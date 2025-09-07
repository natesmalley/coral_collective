"""
CoralCollective Memory Integration

Integrates the advanced memory system with CoralCollective's agent workflow.
Provides seamless memory operations for agents and project management.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import yaml
import logging

from .memory_system import MemorySystem, MemoryItem, MemoryType, ImportanceLevel
from ..tools.project_state import ProjectStateManager

logger = logging.getLogger(__name__)

class CoralMemoryIntegration:
    """
    Integration layer between CoralCollective agents and the memory system
    """
    
    def __init__(self, project_path: Path = None, config_path: str = None):
        self.project_path = project_path or Path.cwd()
        self.project_id = self.project_path.name
        
        # Initialize memory system
        self.memory_system = MemorySystem(config_path)
        
        # Initialize project state manager
        self.state_manager = ProjectStateManager(self.project_path)
        
        # Memory-enhanced project state
        self.memory_state = {
            'active_session': str(datetime.now().timestamp()),
            'current_context': {},
            'agent_memory_cache': {}
        }
        
        logger.info(f"CoralCollective memory integration initialized for project: {self.project_id}")
        
    async def record_agent_start(self, agent_id: str, task: str, context: Dict = None) -> str:
        """Record agent start with memory context"""
        
        # Record in project state
        agent_record = self.state_manager.record_agent_start(agent_id, task, context)
        
        # Add to memory system
        memory_content = f"Agent {agent_id} started task: {task}"
        memory_context = {
            'type': 'agent_start',
            'task': task,
            'context': context or {},
            'session_id': self.memory_state['active_session']
        }
        
        memory_id = await self.memory_system.add_memory(
            content=memory_content,
            agent_id=agent_id,
            project_id=self.project_id,
            context=memory_context,
            tags=['agent_start', 'workflow'],
            memory_type=MemoryType.EPISODIC
        )
        
        # Update working memory with current agent
        await self.memory_system.short_term.set_working_memory('current_agent', agent_id)
        await self.memory_system.short_term.set_working_memory('current_task', task)
        
        return memory_id
        
    async def record_agent_output(self, agent_id: str, output: str, 
                                output_type: str = "general", artifacts: List[Dict] = None) -> str:
        """Record agent output in memory"""
        
        # Determine importance based on output type
        importance_map = {
            'error': ImportanceLevel.CRITICAL,
            'completion': ImportanceLevel.HIGH,
            'handoff': ImportanceLevel.HIGH,
            'artifact': ImportanceLevel.MEDIUM,
            'progress': ImportanceLevel.LOW
        }
        
        memory_context = {
            'type': 'agent_output',
            'output_type': output_type,
            'session_id': self.memory_state['active_session'],
            'artifacts': artifacts or []
        }
        
        # Add to memory system
        memory_id = await self.memory_system.add_memory(
            content=output,
            agent_id=agent_id,
            project_id=self.project_id,
            context=memory_context,
            tags=['agent_output', output_type],
            memory_type=MemoryType.SHORT_TERM
        )
        
        return memory_id
        
    async def record_agent_completion(self, agent_id: str, success: bool = True,
                                    outputs: Dict = None, artifacts: List[Dict] = None,
                                    handoff_data: Dict = None) -> str:
        """Record agent completion with memory context"""
        
        # Record in project state
        completion_record = self.state_manager.record_agent_completion(
            agent_id, success, outputs, artifacts
        )
        
        # Prepare memory content
        status = "completed successfully" if success else "completed with errors"
        memory_content = f"Agent {agent_id} {status}"
        
        if outputs:
            memory_content += f"\n\nOutputs: {json.dumps(outputs, indent=2)}"
            
        memory_context = {
            'type': 'agent_completion',
            'success': success,
            'outputs': outputs or {},
            'artifacts': artifacts or [],
            'handoff_data': handoff_data,
            'session_id': self.memory_state['active_session'],
            'duration_minutes': completion_record.get('duration_minutes', 0) if completion_record else 0
        }
        
        # Add to memory system
        memory_id = await self.memory_system.add_memory(
            content=memory_content,
            agent_id=agent_id,
            project_id=self.project_id,
            context=memory_context,
            tags=['agent_completion', 'workflow'],
            memory_type=MemoryType.EPISODIC
        )
        
        # Record handoff if provided
        if handoff_data and 'next_agent' in handoff_data:
            await self.record_agent_handoff(
                from_agent=agent_id,
                to_agent=handoff_data['next_agent'],
                handoff_data=handoff_data
            )
            
        return memory_id
        
    async def record_agent_handoff(self, from_agent: str, to_agent: str, 
                                 handoff_data: Dict) -> str:
        """Record agent handoff in both systems"""
        
        # Record in project state
        self.state_manager.record_handoff(from_agent, to_agent, handoff_data)
        
        # Record in memory system
        await self.memory_system.record_agent_handoff(
            from_agent, to_agent, self.project_id, handoff_data
        )
        
        # Update working memory
        await self.memory_system.short_term.set_working_memory('last_handoff', {
            'from': from_agent,
            'to': to_agent,
            'timestamp': datetime.now().isoformat(),
            'data': handoff_data
        })
        
        return f"handoff_{from_agent}_{to_agent}_{datetime.now().timestamp()}"
        
    async def get_agent_context(self, agent_id: str, include_history: bool = True,
                              context_limit: int = 10) -> Dict[str, Any]:
        """Get comprehensive context for an agent"""
        
        # Get memory-based context
        memory_context = await self.memory_system.get_agent_context(agent_id, self.project_id)
        
        # Get project state context
        state_context = {
            'project_summary': self.state_manager.get_summary(),
            'agent_history': self.state_manager.get_agent_history(agent_id) if include_history else [],
            'recent_handoffs': self.state_manager.state['handoffs'][-5:] if self.state_manager.state['handoffs'] else [],
            'current_phase': self.state_manager.state['project']['current_phase'],
            'project_artifacts': self.state_manager.get_artifacts_by_agent(agent_id)
        }
        
        # Get last handoff to this agent
        last_handoff = self.state_manager.get_last_handoff_for(agent_id)
        if last_handoff:
            state_context['last_handoff'] = last_handoff
            
        # Combine contexts
        combined_context = {
            'memory_context': memory_context,
            'project_state': state_context,
            'session_info': {
                'session_id': self.memory_state['active_session'],
                'project_id': self.project_id,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return combined_context
        
    async def search_project_knowledge(self, query: str, agent_id: str = None,
                                     limit: int = 10) -> List[Dict[str, Any]]:
        """Search project knowledge base"""
        
        memories = await self.memory_system.search_memories(
            query=query,
            agent_id=agent_id,
            project_id=self.project_id,
            limit=limit
        )
        
        # Convert to dict format for easy consumption
        results = []
        for memory in memories:
            results.append({
                'id': memory.id,
                'content': memory.content,
                'agent_id': memory.agent_id,
                'timestamp': memory.timestamp.isoformat(),
                'importance': memory.importance.name,
                'tags': memory.tags,
                'context': memory.context
            })
            
        return results
        
    async def get_project_timeline(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get chronological timeline of project activities"""
        
        # Search for episodic memories
        timeline_memories = await self.memory_system.search_memories(
            query="",  # Empty query to get all
            project_id=self.project_id,
            limit=limit
        )
        
        # Filter for timeline-relevant memories
        timeline_events = []
        for memory in timeline_memories:
            if memory.memory_type in [MemoryType.EPISODIC, MemoryType.SHORT_TERM]:
                timeline_events.append({
                    'timestamp': memory.timestamp.isoformat(),
                    'agent_id': memory.agent_id,
                    'event_type': memory.context.get('type', 'unknown'),
                    'content': memory.content,
                    'importance': memory.importance.name
                })
                
        # Sort by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return timeline_events[:limit]
        
    async def export_project_memory(self, output_path: Path = None) -> Path:
        """Export project memory to file"""
        
        output_path = output_path or self.project_path / 'project_memory_export.json'
        
        # Get all project memories
        all_memories = await self.memory_system.search_memories(
            query="",
            project_id=self.project_id,
            limit=1000  # Large limit to get all
        )
        
        # Prepare export data
        export_data = {
            'project_id': self.project_id,
            'export_timestamp': datetime.now().isoformat(),
            'memory_stats': self.memory_system.get_memory_stats(),
            'memories': []
        }
        
        for memory in all_memories:
            export_data['memories'].append({
                'id': memory.id,
                'content': memory.content,
                'memory_type': memory.memory_type.value,
                'timestamp': memory.timestamp.isoformat(),
                'agent_id': memory.agent_id,
                'importance': memory.importance.value,
                'context': memory.context,
                'tags': memory.tags
            })
            
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Project memory exported to: {output_path}")
        return output_path
        
    async def consolidate_session_memory(self):
        """Consolidate current session memory"""
        
        await self.memory_system.consolidate_memories()
        logger.info("Session memory consolidation completed")
        
    async def cleanup_old_memory(self, days_threshold: int = 90):
        """Clean up old project memory"""
        
        await self.memory_system.cleanup_old_memories(days_threshold)
        logger.info(f"Memory cleanup completed for memories older than {days_threshold} days")
        
    def get_memory_enhanced_prompt(self, agent_id: str, base_prompt: str,
                                 include_recent: bool = True, include_context: bool = True) -> str:
        """Enhance agent prompt with memory context"""
        
        enhanced_parts = [base_prompt]
        
        if include_context or include_recent:
            # This would be called synchronously, so we'll provide a sync wrapper
            context = asyncio.run(self.get_agent_context(agent_id))
            
            if include_recent and context['memory_context']['recent_memories']:
                enhanced_parts.append("\n## Recent Project Context:")
                for memory in context['memory_context']['recent_memories'][:5]:
                    timestamp = memory['timestamp'][:16]  # YYYY-MM-DD HH:MM
                    enhanced_parts.append(f"- [{timestamp}] {memory['agent_id']}: {memory['content'][:200]}...")
                    
            if include_context and context['project_state']['last_handoff']:
                handoff = context['project_state']['last_handoff']
                enhanced_parts.append(f"\n## Previous Agent Context:")
                enhanced_parts.append(f"From {handoff['from_agent']}: {handoff['data'].get('summary', 'No summary provided')}")
                
        return "\n".join(enhanced_parts)

class MemoryEnhancedProjectState(ProjectStateManager):
    """
    Extended ProjectStateManager with memory integration
    """
    
    def __init__(self, project_path: Path = None, memory_integration: CoralMemoryIntegration = None):
        super().__init__(project_path)
        self.memory_integration = memory_integration or CoralMemoryIntegration(project_path)
        
    async def record_agent_start_with_memory(self, agent_id: str, task: str, context: Dict = None):
        """Record agent start with both state and memory tracking"""
        
        # Call parent method
        state_record = self.record_agent_start(agent_id, task, context)
        
        # Add memory tracking
        memory_id = await self.memory_integration.record_agent_start(agent_id, task, context)
        
        return {
            'state_record': state_record,
            'memory_id': memory_id
        }
        
    async def record_agent_completion_with_memory(self, agent_id: str, success: bool = True,
                                                outputs: Dict = None, artifacts: List[Dict] = None):
        """Record agent completion with both state and memory tracking"""
        
        # Call parent method
        completion_record = self.record_agent_completion(agent_id, success, outputs, artifacts)
        
        # Add memory tracking
        memory_id = await self.memory_integration.record_agent_completion(
            agent_id, success, outputs, artifacts
        )
        
        return {
            'completion_record': completion_record,
            'memory_id': memory_id
        }
        
    async def get_enhanced_summary(self) -> Dict[str, Any]:
        """Get project summary enhanced with memory statistics"""
        
        base_summary = self.get_summary()
        memory_stats = self.memory_integration.memory_system.get_memory_stats()
        
        enhanced_summary = {
            **base_summary,
            'memory_statistics': memory_stats,
            'session_id': self.memory_integration.memory_state['active_session']
        }
        
        return enhanced_summary

# Utility functions for easy integration

async def initialize_project_memory(project_path: Path = None, config_path: str = None) -> CoralMemoryIntegration:
    """Initialize memory system for a project"""
    
    memory_integration = CoralMemoryIntegration(project_path, config_path)
    
    # Perform initial setup
    await memory_integration.memory_system.add_memory(
        content="Project memory system initialized",
        agent_id="memory_system",
        project_id=memory_integration.project_id,
        context={'type': 'system_initialization'},
        tags=['system', 'initialization'],
        memory_type=MemoryType.EPISODIC
    )
    
    return memory_integration

def create_memory_config(project_path: Path) -> Path:
    """Create default memory configuration file"""
    
    config_path = project_path / '.coral' / 'memory_config.json'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "short_term": {
            "buffer_size": 25,
            "max_tokens": 10000
        },
        "long_term": {
            "type": "chroma",
            "collection_name": f"coral_memory_{project_path.name}",
            "persist_directory": str(project_path / '.coral' / 'memory' / 'chroma_db')
        },
        "orchestrator": {
            "short_term_limit": 25,
            "consolidation_threshold": 0.6,
            "importance_decay_hours": 48
        },
        "summarizer": {
            "max_summary_length": 500,
            "preserve_critical_info": True
        }
    }
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
        
    return config_path