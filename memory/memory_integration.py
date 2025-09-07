#!/usr/bin/env python3
"""
Memory System Integration for CoralCollective

Integrates the three-tier memory system with existing CoralCollective components:
- AgentRunner integration
- ProjectStateManager enhancement
- MCP client memory tools
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from .memory_architecture import MemoryManager, MemoryType, MemoryQuery
from .vector_store import create_memory_store
from .memory_retrieval import MemoryRetriever, MemorySummarizer, MemoryContextInjector

logger = logging.getLogger(__name__)


class CoralMemoryIntegration:
    """Main integration class for CoralCollective memory system"""
    
    def __init__(self, 
                 project_path: Path,
                 config: Dict[str, Any] = None):
        self.project_path = project_path
        self.config = config or self._get_default_config()
        
        # Initialize memory components
        self.memory_store = create_memory_store(
            store_type=self.config.get('store_type', 'chroma'),
            config=self.config.get('store_config', {})
        )
        
        self.memory_manager = MemoryManager(
            long_term_store=self.memory_store,
            project_path=project_path
        )
        
        self.memory_retriever = MemoryRetriever(self.memory_manager)
        self.memory_summarizer = MemorySummarizer(self.memory_manager)
        self.context_injector = MemoryContextInjector(self.memory_retriever)
        
        # Integration state
        self.current_agent_id = None
        self.current_project_id = None
        self.session_start_time = datetime.now(timezone.utc)
        
        logger.info("CoralCollective memory system initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default memory system configuration"""
        return {
            'store_type': 'chroma',
            'store_config': {
                'collection_name': 'coral_collective_memory',
                'persist_directory': 'memory/chroma_db',
                'embedding': {
                    'provider': 'sentence_transformers',
                    'model': 'all-MiniLM-L6-v2'
                }
            },
            'auto_summarization': True,
            'context_injection': True,
            'max_context_length': 2000,
            'memory_retention_days': 30
        }
    
    async def on_agent_start(self, 
                           agent_id: str, 
                           task: str, 
                           project_context: Dict[str, Any] = None) -> str:
        """Handle agent start event - inject context and prepare working memory"""
        self.current_agent_id = agent_id
        self.current_project_id = project_context.get('project', {}).get('name') if project_context else None
        
        # Store agent start interaction
        interaction_id = await self.memory_manager.store_interaction(
            agent_id=agent_id,
            content=f"Started task: {task}",
            memory_type=MemoryType.INTERACTION,
            project_id=self.current_project_id,
            metadata={
                'task': task,
                'project_context': project_context,
                'event_type': 'agent_start'
            },
            tags=['agent_start', agent_id]
        )
        
        # Update working memory
        working_memory = self.memory_manager.get_working_memory()
        working_memory.update_task_state(agent_id, task, 'started')
        working_memory.set_context('current_task', task)
        working_memory.set_context('project_context', project_context)
        
        # Inject relevant context if enabled
        if self.config.get('context_injection', True):
            context = await self.context_injector.inject_memory_context(
                agent_id=agent_id,
                current_task=task,
                project_id=self.current_project_id,
                max_context_length=self.config.get('max_context_length', 2000)
            )
            
            if context:
                working_memory.set_context('injected_context', context)
                logger.info(f"Injected {len(context)} chars of context for {agent_id}")
        
        logger.info(f"Agent {agent_id} started with memory context")
        return interaction_id
    
    async def on_agent_completion(self, 
                                agent_id: str, 
                                success: bool = True,
                                outputs: Dict[str, Any] = None,
                                handoff_data: Dict[str, Any] = None) -> str:
        """Handle agent completion event"""
        outputs = outputs or {}
        
        # Determine completion content
        if handoff_data:
            content = f"Completed task with handoff: {json.dumps(handoff_data, default=str)}"
            memory_type = MemoryType.AGENT_HANDOFF
            tags = ['agent_completion', 'handoff', agent_id]
        else:
            content = f"Completed task - Success: {success}"
            memory_type = MemoryType.INTERACTION
            tags = ['agent_completion', agent_id]
        
        # Store completion interaction
        interaction_id = await self.memory_manager.store_interaction(
            agent_id=agent_id,
            content=content,
            memory_type=memory_type,
            project_id=self.current_project_id,
            metadata={
                'success': success,
                'outputs': outputs,
                'handoff_data': handoff_data,
                'event_type': 'agent_completion'
            },
            tags=tags
        )
        
        # Update working memory
        working_memory = self.memory_manager.get_working_memory()
        working_memory.update_task_state(agent_id, '', 'completed')
        
        # Store working memory summary before clearing for handoffs
        if handoff_data:
            summary = working_memory.get_summary()
            await self.memory_manager.store_interaction(
                agent_id=agent_id,
                content=f"Working memory at handoff: {json.dumps(summary)}",
                memory_type=MemoryType.PROJECT_CONTEXT,
                project_id=self.current_project_id,
                metadata={'working_memory_snapshot': summary},
                tags=['working_memory', 'handoff']
            )
        
        logger.info(f"Agent {agent_id} completion recorded")
        return interaction_id
    
    async def on_file_operation(self, 
                              agent_id: str, 
                              operation: str, 
                              file_path: str, 
                              content_preview: str = None):
        """Handle file operations for memory tracking"""
        # Add to working memory active files
        working_memory = self.memory_manager.get_working_memory()
        working_memory.add_active_file(file_path)
        
        # Store significant file operations
        if operation in ['create', 'major_edit', 'delete']:
            content = f"File {operation}: {file_path}"
            if content_preview:
                content += f"\nPreview: {content_preview[:200]}..."
            
            await self.memory_manager.store_interaction(
                agent_id=agent_id,
                content=content,
                memory_type=MemoryType.CODE_PATTERN,
                project_id=self.current_project_id,
                metadata={
                    'operation': operation,
                    'file_path': file_path,
                    'file_type': Path(file_path).suffix
                },
                tags=['file_operation', operation, Path(file_path).suffix.lstrip('.')]
            )
    
    async def on_error_resolution(self, 
                                agent_id: str, 
                                error_description: str, 
                                solution: str,
                                error_type: str = None):
        """Handle error resolution for learning"""
        content = f"Error Resolution:\nProblem: {error_description}\nSolution: {solution}"
        
        await self.memory_manager.store_interaction(
            agent_id=agent_id,
            content=content,
            memory_type=MemoryType.ERROR_SOLUTION,
            project_id=self.current_project_id,
            metadata={
                'error_description': error_description,
                'solution': solution,
                'error_type': error_type or 'unknown'
            },
            tags=['error_resolution', error_type or 'unknown', agent_id]
        )
        
        logger.info(f"Error resolution recorded for {agent_id}")
    
    async def on_requirement_capture(self, 
                                   agent_id: str, 
                                   requirement: str, 
                                   requirement_type: str = 'functional'):
        """Handle requirement capture"""
        await self.memory_manager.store_interaction(
            agent_id=agent_id,
            content=requirement,
            memory_type=MemoryType.REQUIREMENT,
            project_id=self.current_project_id,
            metadata={
                'requirement_type': requirement_type,
                'captured_by': agent_id
            },
            tags=['requirement', requirement_type, agent_id]
        )
    
    async def on_decision_made(self, 
                             agent_id: str, 
                             decision: str, 
                             rationale: str,
                             decision_type: str = 'technical'):
        """Handle important decisions"""
        content = f"Decision: {decision}\nRationale: {rationale}"
        
        await self.memory_manager.store_interaction(
            agent_id=agent_id,
            content=content,
            memory_type=MemoryType.DECISION,
            project_id=self.current_project_id,
            metadata={
                'decision': decision,
                'rationale': rationale,
                'decision_type': decision_type,
                'decided_by': agent_id
            },
            tags=['decision', decision_type, agent_id]
        )
    
    async def get_agent_context(self, 
                              agent_id: str, 
                              task: str,
                              max_length: int = None) -> str:
        """Get relevant context for agent"""
        max_length = max_length or self.config.get('max_context_length', 2000)
        
        return await self.context_injector.inject_memory_context(
            agent_id=agent_id,
            current_task=task,
            project_id=self.current_project_id,
            max_context_length=max_length
        )
    
    async def search_memories(self, 
                            query: str, 
                            agent_id: str = None, 
                            memory_types: List[str] = None,
                            max_results: int = 10) -> List[Dict[str, Any]]:
        """Search memories and return as serializable dictionaries"""
        # Convert string memory types to enum
        enum_types = []
        if memory_types:
            for mt in memory_types:
                try:
                    enum_types.append(MemoryType(mt))
                except ValueError:
                    logger.warning(f"Unknown memory type: {mt}")
        
        memory_query = MemoryQuery(
            query=query,
            agent_id=agent_id,
            project_id=self.current_project_id,
            memory_types=enum_types,
            max_results=max_results
        )
        
        memories = await self.memory_retriever.retrieve_memories(memory_query)
        
        # Convert to serializable format
        return [
            {
                'id': memory.id,
                'content': memory.content,
                'memory_type': memory.memory_type.value,
                'agent_id': memory.agent_id,
                'project_id': memory.project_id,
                'timestamp': memory.timestamp.isoformat(),
                'importance_score': memory.importance_score,
                'tags': memory.tags,
                'metadata': memory.metadata
            }
            for memory in memories
        ]
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        base_stats = await self.memory_manager.get_memory_stats()
        
        # Add integration-specific stats
        base_stats.update({
            'current_agent': self.current_agent_id,
            'current_project': self.current_project_id,
            'session_duration_minutes': int(
                (datetime.now(timezone.utc) - self.session_start_time).total_seconds() / 60
            ),
            'config': {
                'store_type': self.config.get('store_type'),
                'context_injection_enabled': self.config.get('context_injection', True),
                'auto_summarization_enabled': self.config.get('auto_summarization', True)
            }
        })
        
        return base_stats
    
    async def create_session_summary(self) -> str:
        """Create summary of current session"""
        if self.config.get('auto_summarization', True):
            await self.memory_summarizer.create_periodic_summaries()
        
        # Get session stats
        stats = await self.get_memory_stats()
        summary_id = await self.memory_manager.store_interaction(
            agent_id="system",
            content=f"Session summary: {json.dumps(stats, indent=2)}",
            memory_type=MemoryType.PROJECT_CONTEXT,
            project_id=self.current_project_id,
            metadata={'session_stats': stats, 'summary_type': 'session'},
            tags=['session_summary', 'system']
        )
        
        return summary_id
    
    async def cleanup_session(self):
        """Cleanup session and prepare for shutdown"""
        # Create session summary
        await self.create_session_summary()
        
        # Clear working memory
        await self.memory_manager.clear_working_memory()
        
        # Shutdown memory manager
        await self.memory_manager.shutdown()
        
        logger.info("Memory integration session cleaned up")


class EnhancedProjectStateManager:
    """Enhanced ProjectStateManager with memory integration"""
    
    def __init__(self, 
                 original_manager, 
                 memory_integration: CoralMemoryIntegration):
        self.original = original_manager
        self.memory = memory_integration
    
    async def record_agent_start(self, agent_id: str, task: str, context: Dict = None):
        """Enhanced agent start with memory integration"""
        # Call original method
        result = self.original.record_agent_start(agent_id, task, context)
        
        # Add memory integration
        await self.memory.on_agent_start(agent_id, task, context)
        
        return result
    
    async def record_agent_completion(self, agent_id: str, success: bool = True, 
                                   outputs: Dict = None, artifacts: List[Dict] = None):
        """Enhanced agent completion with memory integration"""
        # Call original method
        result = self.original.record_agent_completion(agent_id, success, outputs, artifacts)
        
        # Extract handoff data from outputs
        handoff_data = outputs.get('handoff') if outputs else None
        
        # Add memory integration
        await self.memory.on_agent_completion(agent_id, success, outputs, handoff_data)
        
        return result
    
    def add_artifact(self, artifact_type: str, path: str, created_by: str, metadata: Dict = None):
        """Enhanced artifact tracking with memory integration"""
        # Call original method
        result = self.original.add_artifact(artifact_type, path, created_by, metadata)
        
        # Add memory integration for significant artifacts
        if artifact_type in ['source_code', 'documentation', 'configuration']:
            asyncio.create_task(
                self.memory.on_file_operation(
                    created_by, 
                    'create', 
                    path,
                    f"Created {artifact_type} artifact"
                )
            )
        
        return result


class MemoryEnhancedAgentRunner:
    """Enhanced AgentRunner with memory integration"""
    
    def __init__(self, original_runner):
        self.original = original_runner
        self.memory_integration = None
        self._initialize_memory()
    
    def _initialize_memory(self):
        """Initialize memory integration"""
        try:
            self.memory_integration = CoralMemoryIntegration(
                project_path=self.original.base_path,
                config=self._load_memory_config()
            )
            logger.info("Memory integration initialized for AgentRunner")
        except Exception as e:
            logger.error(f"Failed to initialize memory integration: {e}")
            self.memory_integration = None
    
    def _load_memory_config(self) -> Dict[str, Any]:
        """Load memory configuration"""
        config_file = self.original.base_path / "memory" / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load memory config: {e}")
        
        return {}
    
    async def run_agent(self, agent_id: str, task: str, project_context: Dict = None, **kwargs):
        """Enhanced run_agent with memory integration"""
        # Initialize memory for this agent run
        if self.memory_integration:
            await self.memory_integration.on_agent_start(agent_id, task, project_context)
            
            # Inject memory context into task if enabled
            if self.memory_integration.config.get('context_injection', True):
                memory_context = await self.memory_integration.get_agent_context(agent_id, task)
                if memory_context:
                    # Enhance task with memory context
                    enhanced_task = f"{task}\n\n{memory_context}"
                    kwargs['enhanced_task'] = enhanced_task
        
        try:
            # Call original run_agent method
            result = await self.original.run_agent(agent_id, task, project_context, **kwargs)
            
            # Record completion
            if self.memory_integration:
                success = result.get('success', True)
                await self.memory_integration.on_agent_completion(
                    agent_id, 
                    success, 
                    result, 
                    result.get('handoff')
                )
            
            return result
            
        except Exception as e:
            # Record error
            if self.memory_integration:
                await self.memory_integration.on_error_resolution(
                    agent_id,
                    f"Agent execution failed: {str(e)}",
                    "Check logs and retry",
                    "execution_error"
                )
            raise
    
    async def shutdown(self):
        """Enhanced shutdown with memory cleanup"""
        if self.memory_integration:
            await self.memory_integration.cleanup_session()
        
        # Call original shutdown if it exists
        if hasattr(self.original, 'shutdown'):
            await self.original.shutdown()


# Utility functions for integration
def enhance_agent_runner(agent_runner):
    """Enhance an existing AgentRunner with memory capabilities"""
    return MemoryEnhancedAgentRunner(agent_runner)

def enhance_project_state_manager(project_state_manager, memory_integration):
    """Enhance an existing ProjectStateManager with memory capabilities"""
    return EnhancedProjectStateManager(project_state_manager, memory_integration)

async def initialize_coral_memory(project_path: Path, config: Dict[str, Any] = None) -> CoralMemoryIntegration:
    """Initialize CoralCollective memory system"""
    memory_integration = CoralMemoryIntegration(project_path, config)
    logger.info("CoralCollective memory system ready")
    return memory_integration