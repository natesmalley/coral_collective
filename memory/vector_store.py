#!/usr/bin/env python3
"""
Vector Memory Store Implementation for CoralCollective

Uses ChromaDB for vector storage with semantic search capabilities.
Supports multiple embedding models and hybrid search strategies.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
import hashlib

# Vector database and embeddings
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

# Alternative embedding options
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .memory_architecture import MemoryStore, MemoryItem, MemoryQuery, MemoryType

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """Abstract base for embedding providers"""
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        raise NotImplementedError
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider"""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package required for OpenAI embeddings")
        
        self.model = model
        if api_key:
            openai.api_key = api_key
        
        # Model dimensions mapping
        self.dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate OpenAI embeddings"""
        try:
            response = await openai.Embedding.acreate(
                input=texts,
                model=self.model
            )
            return [item['embedding'] for item in response['data']]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return []
    
    def get_dimensions(self) -> int:
        return self.dimensions.get(self.model, 1536)


class SentenceTransformerProvider(EmbeddingProvider):
    """Sentence Transformers embedding provider"""
    
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers package required")
        
        self.model_name = model
        self.model = SentenceTransformer(model)
        self._dimensions = self.model.get_sentence_embedding_dimension()
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate sentence transformer embeddings"""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                texts
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"SentenceTransformer embedding failed: {e}")
            return []
    
    def get_dimensions(self) -> int:
        return self._dimensions


class ChromaMemoryStore(MemoryStore):
    """ChromaDB-based vector memory store"""
    
    def __init__(self, 
                 collection_name: str = "coral_collective_memory",
                 persist_directory: Optional[Path] = None,
                 embedding_provider: Optional[EmbeddingProvider] = None):
        
        if not CHROMA_AVAILABLE:
            raise ImportError("chromadb package required for vector memory store")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory or Path("memory/chroma_db")
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding provider
        if embedding_provider:
            self.embedding_provider = embedding_provider
        else:
            # Try to use best available option
            if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
                self.embedding_provider = OpenAIEmbeddingProvider()
                logger.info("Using OpenAI embeddings")
            elif SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_provider = SentenceTransformerProvider()
                logger.info("Using SentenceTransformers embeddings")
            else:
                # Fallback to Chroma's default
                self.embedding_provider = None
                logger.info("Using ChromaDB default embeddings")
        
        # Initialize ChromaDB
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create ChromaDB client with persistence
            settings = Settings(
                persist_directory=str(self.persist_directory),
                anonymized_telemetry=False
            )
            self.client = chromadb.Client(settings)
            
            # Set up embedding function
            if self.embedding_provider is None:
                # Use ChromaDB's default embedding function
                embedding_function = embedding_functions.DefaultEmbeddingFunction()
            else:
                # Create custom embedding function
                embedding_function = ChromaEmbeddingFunction(self.embedding_provider)
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function
                )
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=embedding_function,
                    metadata={"description": "CoralCollective Memory Store"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def store(self, item: MemoryItem) -> bool:
        """Store memory item in vector database"""
        try:
            # Prepare document content for embedding
            content_text = self._prepare_content_for_embedding(item)
            
            # Prepare metadata
            metadata = {
                'memory_type': item.memory_type.value,
                'agent_id': item.agent_id,
                'project_id': item.project_id or '',
                'timestamp': item.timestamp.isoformat(),
                'importance_score': item.importance_score,
                'access_count': item.access_count,
                'last_accessed': item.last_accessed.isoformat(),
                'tags': json.dumps(item.tags),
                'metadata': json.dumps(item.metadata)
            }
            
            # Store in ChromaDB
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._sync_add_to_collection,
                item.id,
                content_text,
                metadata
            )
            
            logger.debug(f"Stored memory item {item.id} in vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory item {item.id}: {e}")
            return False
    
    def _sync_add_to_collection(self, item_id: str, content: str, metadata: Dict[str, Any]):
        """Synchronous add to collection (for executor)"""
        self.collection.add(
            ids=[item_id],
            documents=[content],
            metadatas=[metadata]
        )
    
    def _prepare_content_for_embedding(self, item: MemoryItem) -> str:
        """Prepare content text for embedding"""
        # Combine content with relevant metadata for better search
        parts = [item.content]
        
        # Add tags as searchable content
        if item.tags:
            parts.append(f"Tags: {', '.join(item.tags)}")
        
        # Add agent context
        parts.append(f"Agent: {item.agent_id}")
        
        # Add memory type context
        parts.append(f"Type: {item.memory_type.value.replace('_', ' ')}")
        
        # Add important metadata
        if item.metadata:
            important_keys = ['task', 'error_type', 'solution', 'requirement_type']
            metadata_parts = []
            for key in important_keys:
                if key in item.metadata:
                    metadata_parts.append(f"{key}: {item.metadata[key]}")
            if metadata_parts:
                parts.append("Context: " + ", ".join(metadata_parts))
        
        return "\n".join(parts)
    
    async def retrieve(self, query: MemoryQuery) -> List[MemoryItem]:
        """Retrieve memory items using vector search"""
        try:
            # Prepare search query
            search_text = self._prepare_search_query(query)
            
            # Prepare where clause for metadata filtering
            where_clause = self._build_where_clause(query)
            
            # Perform vector search
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self._sync_query_collection,
                search_text,
                where_clause,
                query.max_results
            )
            
            # Convert results to MemoryItem objects
            memory_items = []
            for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0], 
                results['metadatas'][0],
                results['distances'][0]
            )):
                # Filter by similarity threshold
                similarity = 1 - distance  # Convert distance to similarity
                if similarity < query.similarity_threshold:
                    continue
                
                # Reconstruct MemoryItem
                try:
                    item = self._metadata_to_memory_item(doc_id, document, metadata, similarity)
                    if item:
                        memory_items.append(item)
                except Exception as e:
                    logger.error(f"Failed to reconstruct memory item {doc_id}: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(memory_items)} memory items for query: {query.query}")
            return memory_items
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    def _sync_query_collection(self, search_text: str, where_clause: Dict, limit: int):
        """Synchronous query collection (for executor)"""
        return self.collection.query(
            query_texts=[search_text],
            n_results=limit,
            where=where_clause if where_clause else None,
            include=['documents', 'metadatas', 'distances']
        )
    
    def _prepare_search_query(self, query: MemoryQuery) -> str:
        """Prepare search text with context"""
        parts = [query.query]
        
        # Add agent context to search
        if query.agent_id:
            parts.append(f"agent:{query.agent_id}")
        
        # Add memory type context
        if query.memory_types:
            type_names = [mt.value.replace('_', ' ') for mt in query.memory_types]
            parts.append(f"type:{' OR '.join(type_names)}")
        
        # Add tag context
        if query.tags:
            parts.append(f"tags:{' '.join(query.tags)}")
        
        return " ".join(parts)
    
    def _build_where_clause(self, query: MemoryQuery) -> Dict[str, Any]:
        """Build ChromaDB where clause for metadata filtering"""
        conditions = {}
        
        # Agent filter
        if query.agent_id:
            conditions['agent_id'] = {"$eq": query.agent_id}
        
        # Project filter
        if query.project_id:
            conditions['project_id'] = {"$eq": query.project_id}
        
        # Memory type filter
        if query.memory_types:
            type_values = [mt.value for mt in query.memory_types]
            conditions['memory_type'] = {"$in": type_values}
        
        # Importance threshold
        if query.importance_threshold > 0:
            conditions['importance_score'] = {"$gte": query.importance_threshold}
        
        # Time range filter
        if query.time_range:
            start_time, end_time = query.time_range
            conditions['timestamp'] = {
                "$gte": start_time.isoformat(),
                "$lte": end_time.isoformat()
            }
        
        return conditions
    
    def _metadata_to_memory_item(self, 
                                 doc_id: str, 
                                 document: str, 
                                 metadata: Dict[str, Any], 
                                 similarity: float) -> Optional[MemoryItem]:
        """Convert ChromaDB result to MemoryItem"""
        try:
            # Parse stored metadata
            tags = json.loads(metadata.get('tags', '[]'))
            item_metadata = json.loads(metadata.get('metadata', '{}'))
            
            # Add similarity score to metadata
            item_metadata['similarity_score'] = similarity
            
            return MemoryItem(
                id=doc_id,
                content=self._extract_original_content(document),
                memory_type=MemoryType(metadata['memory_type']),
                agent_id=metadata['agent_id'],
                project_id=metadata['project_id'] if metadata['project_id'] else None,
                timestamp=datetime.fromisoformat(metadata['timestamp']),
                metadata=item_metadata,
                importance_score=metadata['importance_score'],
                access_count=metadata['access_count'],
                last_accessed=datetime.fromisoformat(metadata['last_accessed']),
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Failed to parse metadata for {doc_id}: {e}")
            return None
    
    def _extract_original_content(self, enhanced_content: str) -> str:
        """Extract original content from enhanced content used for embedding"""
        # Split by newlines and take everything before metadata additions
        lines = enhanced_content.split('\n')
        
        # Find where we added metadata (lines starting with known prefixes)
        content_lines = []
        for line in lines:
            if line.startswith(('Tags:', 'Agent:', 'Type:', 'Context:')):
                break
            content_lines.append(line)
        
        return '\n'.join(content_lines).strip()
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory item metadata"""
        try:
            # Get existing item
            existing = await self.get_by_id(item_id)
            if not existing:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
                else:
                    existing.metadata[key] = value
            
            # Re-store the updated item
            return await self.store(existing)
            
        except Exception as e:
            logger.error(f"Failed to update memory item {item_id}: {e}")
            return False
    
    async def delete(self, item_id: str) -> bool:
        """Delete memory item from vector store"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._sync_delete_from_collection,
                item_id
            )
            logger.debug(f"Deleted memory item {item_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete memory item {item_id}: {e}")
            return False
    
    def _sync_delete_from_collection(self, item_id: str):
        """Synchronous delete from collection (for executor)"""
        self.collection.delete(ids=[item_id])
    
    async def get_by_id(self, item_id: str) -> Optional[MemoryItem]:
        """Get memory item by ID"""
        try:
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self._sync_get_by_id,
                item_id
            )
            
            if results['ids'] and results['ids'][0]:
                doc_id = results['ids'][0][0]
                document = results['documents'][0][0]
                metadata = results['metadatas'][0][0]
                
                return self._metadata_to_memory_item(doc_id, document, metadata, 1.0)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory item {item_id}: {e}")
            return None
    
    def _sync_get_by_id(self, item_id: str):
        """Synchronous get by ID (for executor)"""
        return self.collection.get(
            ids=[item_id],
            include=['documents', 'metadatas']
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            count = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.count()
            )
            
            return {
                'total_items': count,
                'collection_name': self.collection_name,
                'persist_directory': str(self.persist_directory),
                'embedding_provider': type(self.embedding_provider).__name__ if self.embedding_provider else 'ChromaDB Default'
            }
            
        except Exception as e:
            logger.error(f"Failed to get vector store stats: {e}")
            return {'error': str(e)}


class ChromaEmbeddingFunction:
    """Custom embedding function wrapper for ChromaDB"""
    
    def __init__(self, embedding_provider: EmbeddingProvider):
        self.embedding_provider = embedding_provider
    
    def __call__(self, input_texts: List[str]) -> List[List[float]]:
        """Generate embeddings synchronously for ChromaDB"""
        # Run async embedding in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.embedding_provider.embed(input_texts))
        finally:
            loop.close()


# Alternative vector stores for different deployment scenarios

class SimpleFileMemoryStore(MemoryStore):
    """Simple file-based memory store for development/testing"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory/simple_store")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.items: Dict[str, MemoryItem] = {}
        self._load_from_disk()
    
    def _load_from_disk(self):
        """Load items from disk"""
        for item_file in self.storage_path.glob("*.json"):
            try:
                with open(item_file, 'r') as f:
                    data = json.load(f)
                    item = MemoryItem.from_dict(data)
                    self.items[item.id] = item
            except Exception as e:
                logger.error(f"Failed to load {item_file}: {e}")
    
    def _save_to_disk(self, item: MemoryItem):
        """Save item to disk"""
        item_file = self.storage_path / f"{item.id}.json"
        with open(item_file, 'w') as f:
            json.dump(item.to_dict(), f, indent=2)
    
    async def store(self, item: MemoryItem) -> bool:
        """Store memory item"""
        try:
            self.items[item.id] = item
            self._save_to_disk(item)
            return True
        except Exception as e:
            logger.error(f"Failed to store item {item.id}: {e}")
            return False
    
    async def retrieve(self, query: MemoryQuery) -> List[MemoryItem]:
        """Retrieve items with simple text search"""
        results = []
        query_lower = query.query.lower()
        
        for item in self.items.values():
            # Basic text matching
            if query_lower not in item.content.lower():
                continue
            
            # Apply filters
            if query.agent_id and query.agent_id != item.agent_id:
                continue
            
            if query.project_id and query.project_id != item.project_id:
                continue
            
            if query.memory_types and item.memory_type not in query.memory_types:
                continue
            
            if item.importance_score < query.importance_threshold:
                continue
            
            if query.time_range:
                start, end = query.time_range
                if not (start <= item.timestamp <= end):
                    continue
            
            results.append(item)
        
        # Sort by importance and recency
        results.sort(key=lambda x: (x.importance_score, x.timestamp), reverse=True)
        return results[:query.max_results]
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """Update memory item"""
        if item_id not in self.items:
            return False
        
        item = self.items[item_id]
        for key, value in updates.items():
            if hasattr(item, key):
                setattr(item, key, value)
            else:
                item.metadata[key] = value
        
        self._save_to_disk(item)
        return True
    
    async def delete(self, item_id: str) -> bool:
        """Delete memory item"""
        if item_id not in self.items:
            return False
        
        del self.items[item_id]
        item_file = self.storage_path / f"{item_id}.json"
        if item_file.exists():
            item_file.unlink()
        return True
    
    async def get_by_id(self, item_id: str) -> Optional[MemoryItem]:
        """Get memory item by ID"""
        return self.items.get(item_id)


# Factory function for creating memory stores
def create_memory_store(store_type: str = "chroma", 
                       config: Optional[Dict[str, Any]] = None) -> MemoryStore:
    """Factory function to create memory stores"""
    config = config or {}
    
    if store_type == "chroma":
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB not available, falling back to simple store")
            return SimpleFileMemoryStore()
        
        # Configure embedding provider
        embedding_provider = None
        embedding_config = config.get('embedding', {})
        
        if embedding_config.get('provider') == 'openai':
            if OPENAI_AVAILABLE:
                embedding_provider = OpenAIEmbeddingProvider(
                    model=embedding_config.get('model', 'text-embedding-3-small')
                )
            else:
                logger.warning("OpenAI not available for embeddings")
        
        elif embedding_config.get('provider') == 'sentence_transformers':
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                embedding_provider = SentenceTransformerProvider(
                    model=embedding_config.get('model', 'all-MiniLM-L6-v2')
                )
            else:
                logger.warning("SentenceTransformers not available")
        
        return ChromaMemoryStore(
            collection_name=config.get('collection_name', 'coral_collective_memory'),
            persist_directory=Path(config.get('persist_directory', 'memory/chroma_db')),
            embedding_provider=embedding_provider
        )
    
    elif store_type == "simple":
        return SimpleFileMemoryStore(
            storage_path=Path(config.get('storage_path', 'memory/simple_store'))
        )
    
    else:
        raise ValueError(f"Unknown memory store type: {store_type}")