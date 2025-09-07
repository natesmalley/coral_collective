#!/usr/bin/env python3
"""
Memory Retrieval System for CoralCollective

Implements hybrid search combining vector similarity, keyword matching,
and contextual relevance scoring for optimal memory retrieval.
"""

import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
import logging
import math

from .memory_architecture import MemoryItem, MemoryQuery, MemoryType, MemoryManager
from .vector_store import MemoryStore

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """Advanced memory retrieval system with hybrid search capabilities"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.search_strategies = {
            'semantic': self._semantic_search,
            'keyword': self._keyword_search,
            'temporal': self._temporal_search,
            'contextual': self._contextual_search,
            'agent_specific': self._agent_specific_search
        }
    
    async def retrieve_memories(self, 
                              query: MemoryQuery, 
                              strategies: List[str] = None,
                              hybrid_weights: Dict[str, float] = None) -> List[MemoryItem]:
        """
        Retrieve memories using hybrid search approach
        
        Args:
            query: Memory retrieval query
            strategies: List of search strategies to use
            hybrid_weights: Weights for combining different search results
        """
        strategies = strategies or ['semantic', 'keyword', 'contextual']
        hybrid_weights = hybrid_weights or {
            'semantic': 0.4,
            'keyword': 0.3,
            'contextual': 0.2,
            'temporal': 0.1
        }
        
        # Execute different search strategies in parallel
        search_tasks = []
        for strategy in strategies:
            if strategy in self.search_strategies:
                task = asyncio.create_task(
                    self.search_strategies[strategy](query),
                    name=f"search_{strategy}"
                )
                search_tasks.append((strategy, task))
        
        # Wait for all searches to complete
        strategy_results = {}
        for strategy, task in search_tasks:
            try:
                results = await task
                strategy_results[strategy] = results
                logger.debug(f"{strategy} search returned {len(results)} results")
            except Exception as e:
                logger.error(f"Search strategy {strategy} failed: {e}")
                strategy_results[strategy] = []
        
        # Combine results using hybrid scoring
        combined_results = self._combine_search_results(
            strategy_results, 
            hybrid_weights, 
            query
        )
        
        # Apply post-processing filters
        filtered_results = self._apply_post_filters(combined_results, query)
        
        # Sort by final relevance score
        filtered_results.sort(
            key=lambda x: x.metadata.get('final_relevance_score', 0), 
            reverse=True
        )
        
        # Return top results
        return filtered_results[:query.max_results]
    
    async def _semantic_search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Semantic vector search using embeddings"""
        return await self.memory_manager.retrieve_memories(query)
    
    async def _keyword_search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Keyword-based search with TF-IDF scoring"""
        # Get all relevant memories from short-term
        all_memories = self.memory_manager.short_term_memory.get_recent_interactions(
            agent_id=query.agent_id,
            limit=500  # Larger set for keyword search
        )
        
        # Extract keywords from query
        keywords = self._extract_keywords(query.query)
        
        # Score memories based on keyword matches
        scored_memories = []
        for memory in all_memories:
            score = self._calculate_keyword_score(memory.content, keywords, query)
            if score > 0:
                memory_copy = memory
                memory_copy.metadata = memory_copy.metadata.copy()
                memory_copy.metadata['keyword_score'] = score
                scored_memories.append(memory_copy)
        
        # Sort by keyword score
        scored_memories.sort(key=lambda x: x.metadata['keyword_score'], reverse=True)
        return scored_memories[:query.max_results * 2]  # Return more for hybrid combination
    
    async def _temporal_search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Time-based search focusing on recent and relevant memories"""
        # Create temporal query
        temporal_query = MemoryQuery(
            query=query.query,
            agent_id=query.agent_id,
            project_id=query.project_id,
            memory_types=query.memory_types,
            max_results=query.max_results * 2,
            time_range=(
                datetime.now(timezone.utc) - timedelta(days=7),  # Last week
                datetime.now(timezone.utc)
            )
        )
        
        results = await self.memory_manager.retrieve_memories(temporal_query)
        
        # Score based on temporal relevance
        now = datetime.now(timezone.utc)
        for result in results:
            age_hours = (now - result.timestamp).total_seconds() / 3600
            # Exponential decay with half-life of 24 hours
            temporal_score = math.exp(-age_hours / 24)
            result.metadata = result.metadata.copy()
            result.metadata['temporal_score'] = temporal_score
        
        return results
    
    async def _contextual_search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Context-aware search based on current working memory and project state"""
        working_memory = self.memory_manager.get_working_memory()
        context_boost_keywords = []
        
        # Extract context from working memory
        if working_memory.task_context:
            task = working_memory.task_context.get('task', '')
            context_boost_keywords.extend(self._extract_keywords(task))
        
        # Add active files as context
        for file_path in working_memory.active_files[-5:]:  # Recent files
            filename = file_path.split('/')[-1]
            context_boost_keywords.extend(self._extract_keywords(filename))
        
        # Get project-specific memories
        project_query = MemoryQuery(
            query=query.query,
            project_id=query.project_id,
            max_results=query.max_results * 2,
            memory_types=[MemoryType.PROJECT_CONTEXT, MemoryType.REQUIREMENT, MemoryType.DECISION]
        )
        
        results = await self.memory_manager.retrieve_memories(project_query)
        
        # Score based on contextual relevance
        for result in results:
            context_score = self._calculate_context_score(
                result.content, 
                context_boost_keywords,
                working_memory.current_phase
            )
            result.metadata = result.metadata.copy()
            result.metadata['context_score'] = context_score
        
        return results
    
    async def _agent_specific_search(self, query: MemoryQuery) -> List[MemoryItem]:
        """Search for agent-specific patterns and learnings"""
        if not query.agent_id:
            return []
        
        # Get agent's historical interactions
        agent_memories = []
        
        # Short-term memories from this agent
        short_term = self.memory_manager.short_term_memory.get_recent_interactions(
            agent_id=query.agent_id,
            limit=100
        )
        agent_memories.extend(short_term)
        
        # Look for similar tasks this agent has handled
        similar_task_query = MemoryQuery(
            query=query.query,
            agent_id=query.agent_id,
            memory_types=[MemoryType.AGENT_HANDOFF, MemoryType.ERROR_SOLUTION, MemoryType.CODE_PATTERN],
            max_results=50
        )
        
        long_term_agent_memories = await self.memory_manager.retrieve_memories(similar_task_query)
        agent_memories.extend(long_term_agent_memories)
        
        # Score based on agent expertise and success patterns
        for memory in agent_memories:
            agent_score = self._calculate_agent_expertise_score(memory, query.agent_id)
            memory.metadata = memory.metadata.copy()
            memory.metadata['agent_score'] = agent_score
        
        return agent_memories
    
    def _extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'this', 'that', 'these', 'those', 'is', 'are', 
            'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract words, normalize case
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Filter by length and stop words
        keywords = [
            word for word in words 
            if len(word) >= min_length and word not in stop_words
        ]
        
        # Return most common keywords
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _calculate_keyword_score(self, content: str, keywords: List[str], query: MemoryQuery) -> float:
        """Calculate keyword relevance score using TF-IDF-like approach"""
        if not keywords:
            return 0.0
        
        content_lower = content.lower()
        content_words = content_lower.split()
        
        # Calculate term frequency for each keyword
        total_score = 0.0
        for keyword in keywords:
            # Count occurrences
            count = content_lower.count(keyword)
            if count > 0:
                # TF component (log normalization)
                tf = 1 + math.log(count)
                
                # Simple IDF approximation (boost rare terms)
                idf = 1 + (len(keyword) / 10)  # Longer terms get slight boost
                
                total_score += tf * idf
        
        # Normalize by content length
        normalized_score = total_score / max(1, len(content_words) / 100)
        return min(1.0, normalized_score)
    
    def _calculate_context_score(self, content: str, context_keywords: List[str], current_phase: str) -> float:
        """Calculate contextual relevance score"""
        base_score = 0.0
        
        # Context keyword boost
        if context_keywords:
            context_matches = sum(
                1 for keyword in context_keywords 
                if keyword.lower() in content.lower()
            )
            base_score += (context_matches / len(context_keywords)) * 0.5
        
        # Phase relevance boost
        phase_keywords = {
            'planning': ['requirement', 'design', 'architecture', 'plan'],
            'development': ['code', 'implement', 'function', 'class', 'api'],
            'testing': ['test', 'bug', 'error', 'debug', 'fix'],
            'deployment': ['deploy', 'build', 'production', 'release']
        }
        
        if current_phase in phase_keywords:
            phase_matches = sum(
                1 for keyword in phase_keywords[current_phase]
                if keyword in content.lower()
            )
            base_score += (phase_matches / len(phase_keywords[current_phase])) * 0.3
        
        return min(1.0, base_score)
    
    def _calculate_agent_expertise_score(self, memory: MemoryItem, agent_id: str) -> float:
        """Calculate agent expertise score based on historical success"""
        base_score = 0.5
        
        # Boost for successful interactions
        if memory.metadata.get('success') is True:
            base_score += 0.3
        elif memory.metadata.get('success') is False:
            base_score -= 0.1
        
        # Boost for frequently accessed memories
        access_boost = min(0.2, memory.access_count * 0.02)
        base_score += access_boost
        
        # Boost for agent handoffs (indicates good completion)
        if memory.memory_type == MemoryType.AGENT_HANDOFF:
            base_score += 0.2
        
        # Boost for error solutions (valuable learning)
        if memory.memory_type == MemoryType.ERROR_SOLUTION:
            base_score += 0.25
        
        return min(1.0, max(0.0, base_score))
    
    def _combine_search_results(self, 
                              strategy_results: Dict[str, List[MemoryItem]], 
                              weights: Dict[str, float], 
                              query: MemoryQuery) -> List[MemoryItem]:
        """Combine results from different search strategies"""
        # Collect all unique memories
        all_memories = {}
        
        for strategy, results in strategy_results.items():
            strategy_weight = weights.get(strategy, 0.1)
            
            for i, memory in enumerate(results):
                memory_id = memory.id
                
                if memory_id not in all_memories:
                    all_memories[memory_id] = memory
                    all_memories[memory_id].metadata = memory.metadata.copy()
                    all_memories[memory_id].metadata['strategy_scores'] = {}
                    all_memories[memory_id].metadata['final_relevance_score'] = 0.0
                
                # Calculate position-based score for this strategy
                position_score = max(0, 1 - (i / len(results)))
                
                # Get strategy-specific score
                strategy_score_key = f"{strategy}_score"
                strategy_score = memory.metadata.get(strategy_score_key, 0.5)
                
                # Combined score for this strategy
                combined_strategy_score = position_score * 0.5 + strategy_score * 0.5
                
                # Store strategy score
                all_memories[memory_id].metadata['strategy_scores'][strategy] = combined_strategy_score
                
                # Add to final score with weight
                all_memories[memory_id].metadata['final_relevance_score'] += (
                    combined_strategy_score * strategy_weight
                )
        
        return list(all_memories.values())
    
    def _apply_post_filters(self, memories: List[MemoryItem], query: MemoryQuery) -> List[MemoryItem]:
        """Apply post-processing filters to refine results"""
        filtered = []
        
        for memory in memories:
            # Skip low-relevance items
            relevance = memory.metadata.get('final_relevance_score', 0)
            if relevance < 0.1:
                continue
            
            # Apply diversity filter to avoid too many similar results
            if self._is_diverse_enough(memory, filtered):
                filtered.append(memory)
            
            # Limit results
            if len(filtered) >= query.max_results * 2:  # Extra buffer for final ranking
                break
        
        return filtered
    
    def _is_diverse_enough(self, memory: MemoryItem, existing: List[MemoryItem], 
                          similarity_threshold: float = 0.8) -> bool:
        """Check if memory is diverse enough from existing results"""
        if not existing:
            return True
        
        memory_keywords = set(self._extract_keywords(memory.content))
        
        for existing_memory in existing:
            existing_keywords = set(self._extract_keywords(existing_memory.content))
            
            # Calculate Jaccard similarity
            if memory_keywords and existing_keywords:
                intersection = memory_keywords & existing_keywords
                union = memory_keywords | existing_keywords
                similarity = len(intersection) / len(union)
                
                if similarity > similarity_threshold:
                    return False
        
        return True


class MemorySummarizer:
    """Intelligent memory summarization for efficient storage and retrieval"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def summarize_interaction_sequence(self, 
                                           interactions: List[MemoryItem],
                                           summary_type: str = "conversation") -> MemoryItem:
        """Summarize a sequence of related interactions"""
        if not interactions:
            return None
        
        # Group interactions by type and agent
        grouped = defaultdict(list)
        for interaction in interactions:
            key = f"{interaction.agent_id}_{interaction.memory_type.value}"
            grouped[key].append(interaction)
        
        # Create summary content
        summary_parts = []
        all_agents = set()
        all_tags = set()
        total_importance = 0.0
        earliest_time = min(i.timestamp for i in interactions)
        latest_time = max(i.timestamp for i in interactions)
        
        for group_key, group_items in grouped.items():
            agent_id, memory_type = group_key.split('_', 1)
            all_agents.add(agent_id)
            
            # Summarize this group
            group_summary = self._summarize_group(group_items)
            summary_parts.append(f"**{agent_id}** ({memory_type}): {group_summary}")
            
            # Collect metadata
            for item in group_items:
                all_tags.update(item.tags)
                total_importance += item.importance_score
        
        # Create summary content
        summary_content = f"""
# {summary_type.title()} Summary ({earliest_time.strftime('%Y-%m-%d %H:%M')} - {latest_time.strftime('%Y-%m-%d %H:%M')})

**Participants**: {', '.join(sorted(all_agents))}
**Duration**: {int((latest_time - earliest_time).total_seconds() / 60)} minutes
**Interactions**: {len(interactions)}

## Key Activities:
{chr(10).join(summary_parts)}

## Context:
- **Tags**: {', '.join(sorted(all_tags))}
- **Avg Importance**: {total_importance / len(interactions):.2f}
""".strip()
        
        # Create summary memory item
        summary_id = str(uuid.uuid4())
        summary_item = MemoryItem(
            id=summary_id,
            content=summary_content,
            memory_type=MemoryType.PROJECT_CONTEXT,
            agent_id="system",
            project_id=interactions[0].project_id,
            importance_score=min(0.9, total_importance / len(interactions) + 0.3),  # Summaries are important
            metadata={
                'summary_type': summary_type,
                'summarized_count': len(interactions),
                'summarized_agents': list(all_agents),
                'time_span_minutes': int((latest_time - earliest_time).total_seconds() / 60),
                'original_interaction_ids': [i.id for i in interactions]
            },
            tags=list(all_tags) + ['summary', summary_type]
        )
        
        return summary_item
    
    def _summarize_group(self, items: List[MemoryItem]) -> str:
        """Summarize a group of related memory items"""
        if not items:
            return "No activities"
        
        if len(items) == 1:
            return self._truncate_content(items[0].content, 100)
        
        # Extract key themes
        all_content = " ".join(item.content for item in items)
        keywords = self._extract_themes(all_content)
        
        # Count successful vs failed items
        successes = sum(1 for item in items if item.metadata.get('success') is True)
        failures = sum(1 for item in items if item.metadata.get('success') is False)
        
        # Create summary
        theme_text = f"Worked on {', '.join(keywords[:3])}" if keywords else "Various activities"
        
        result_text = ""
        if successes > 0 and failures > 0:
            result_text = f" ({successes} successful, {failures} failed)"
        elif successes > 0:
            result_text = f" ({successes} successful)"
        elif failures > 0:
            result_text = f" ({failures} failed)"
        
        return f"{theme_text}{result_text}"
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from text content"""
        # Simple theme extraction based on important technical terms
        theme_patterns = {
            'api': r'\b(?:api|endpoint|rest|graphql)\b',
            'database': r'\b(?:database|db|sql|query|table)\b',
            'frontend': r'\b(?:frontend|ui|component|react|vue)\b',
            'backend': r'\b(?:backend|server|service|microservice)\b',
            'testing': r'\b(?:test|testing|unittest|integration)\b',
            'deployment': r'\b(?:deploy|deployment|docker|kubernetes)\b',
            'authentication': r'\b(?:auth|authentication|login|jwt)\b',
            'error handling': r'\b(?:error|exception|bug|debug)\b'
        }
        
        found_themes = []
        text_lower = text.lower()
        
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, text_lower):
                found_themes.append(theme)
        
        return found_themes
    
    def _truncate_content(self, content: str, max_length: int = 150) -> str:
        """Truncate content to specified length"""
        if len(content) <= max_length:
            return content
        
        # Try to cut at sentence boundary
        truncated = content[:max_length]
        last_period = truncated.rfind('.')
        last_space = truncated.rfind(' ')
        
        cut_point = max(last_period, last_space) if last_period > 0 or last_space > 0 else max_length
        
        return content[:cut_point] + "..."
    
    async def create_periodic_summaries(self):
        """Create periodic summaries of recent activity"""
        # Get recent interactions from short-term memory
        recent_interactions = self.memory_manager.short_term_memory.get_recent_interactions(
            limit=100
        )
        
        if len(recent_interactions) < 5:  # Need minimum interactions
            return
        
        # Group by time windows (e.g., last hour, last 4 hours, last day)
        time_windows = [
            (timedelta(hours=1), "hourly"),
            (timedelta(hours=4), "session"),
            (timedelta(days=1), "daily")
        ]
        
        for window_size, summary_type in time_windows:
            window_start = datetime.now(timezone.utc) - window_size
            window_interactions = [
                i for i in recent_interactions 
                if i.timestamp >= window_start
            ]
            
            if len(window_interactions) >= 3:  # Minimum for summary
                summary = await self.summarize_interaction_sequence(
                    window_interactions, 
                    summary_type
                )
                
                if summary:
                    # Store the summary
                    await self.memory_manager.store_interaction(
                        agent_id="system",
                        content=summary.content,
                        memory_type=summary.memory_type,
                        project_id=summary.project_id,
                        metadata=summary.metadata,
                        tags=summary.tags
                    )


# Context injection for agent prompts
class MemoryContextInjector:
    """Injects relevant memory context into agent prompts"""
    
    def __init__(self, memory_retriever: MemoryRetriever):
        self.memory_retriever = memory_retriever
    
    async def inject_memory_context(self, 
                                   agent_id: str,
                                   current_task: str,
                                   project_id: Optional[str] = None,
                                   max_context_length: int = 2000) -> str:
        """Inject relevant memory context for an agent task"""
        
        # Create memory query
        query = MemoryQuery(
            query=current_task,
            agent_id=agent_id,
            project_id=project_id,
            max_results=10,
            importance_threshold=0.4
        )
        
        # Retrieve relevant memories
        memories = await self.memory_retriever.retrieve_memories(
            query, 
            strategies=['semantic', 'contextual', 'agent_specific']
        )
        
        if not memories:
            return ""
        
        # Format context
        context_parts = ["## Relevant Context from Memory\n"]
        current_length = len(context_parts[0])
        
        for memory in memories:
            # Format memory entry
            timestamp_str = memory.timestamp.strftime("%Y-%m-%d %H:%M")
            memory_entry = f"""
### {memory.memory_type.value.replace('_', ' ').title()} ({timestamp_str})
**Agent**: {memory.agent_id}
**Content**: {self._truncate_for_context(memory.content, 300)}
**Tags**: {', '.join(memory.tags[:5])}
---
"""
            
            # Check length limit
            if current_length + len(memory_entry) > max_context_length:
                break
            
            context_parts.append(memory_entry)
            current_length += len(memory_entry)
        
        return "\n".join(context_parts)
    
    def _truncate_for_context(self, content: str, max_length: int) -> str:
        """Truncate content for context injection"""
        if len(content) <= max_length:
            return content
        
        # Cut at word boundary
        truncated = content[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length - 50:  # Don't cut too short
            truncated = truncated[:last_space]
        
        return truncated + "..."