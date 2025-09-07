"""
Memory Migration System for CoralCollective

Handles migration from existing YAML-based project state to the new
vector-based memory system while preserving project history and context.
"""

import json
import yaml
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

from .memory_types import (
    MemoryItem, MemoryType, ImportanceLevel, MemoryMetadata, 
    create_memory_from_interaction, generate_memory_id
)
from .memory_system import MemorySystem

logger = logging.getLogger(__name__)


class MemoryMigration:
    """Handles migration from legacy project state to vector memory system"""
    
    def __init__(self, project_path: Path = None, memory_system: MemorySystem = None):
        self.project_path = project_path or Path.cwd()
        self.memory_system = memory_system
        
        # Migration tracking
        self.migration_stats = {
            'total_items_processed': 0,
            'successfully_migrated': 0,
            'failed_migrations': 0,
            'skipped_items': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.migration_log = []
        
    async def migrate_project_state(self, state_file_path: Path = None, 
                                   backup_existing: bool = True) -> Dict[str, Any]:
        """
        Migrate existing project state to memory system
        
        Args:
            state_file_path: Path to existing project state file
            backup_existing: Whether to backup existing state file
            
        Returns:
            Migration results and statistics
        """
        self.migration_stats['start_time'] = datetime.now(timezone.utc)
        
        try:
            # Load existing state
            state_file = state_file_path or self.project_path / '.coral' / 'project_state.yaml'
            
            if not state_file.exists():
                return self._create_migration_result(
                    success=False,
                    message=f"State file not found: {state_file}"
                )
            
            # Backup if requested
            if backup_existing:
                backup_path = state_file.with_suffix('.yaml.backup')
                backup_path.write_text(state_file.read_text())
                logger.info(f"Backed up existing state to: {backup_path}")
            
            # Load state data
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f)
            
            if not state_data:
                return self._create_migration_result(
                    success=False,
                    message="State file is empty or invalid"
                )
            
            # Migrate different components
            await self._migrate_project_info(state_data.get('project', {}))
            await self._migrate_agents(state_data.get('agents', {}))
            await self._migrate_artifacts(state_data.get('artifacts', []))
            await self._migrate_handoffs(state_data.get('handoffs', []))
            await self._migrate_context(state_data.get('context', {}))
            await self._migrate_metrics(state_data.get('metrics', {}))
            
            self.migration_stats['end_time'] = datetime.now(timezone.utc)
            
            return self._create_migration_result(success=True)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.migration_stats['end_time'] = datetime.now(timezone.utc)
            return self._create_migration_result(
                success=False,
                message=f"Migration failed: {str(e)}"
            )
    
    async def _migrate_project_info(self, project_data: Dict[str, Any]):
        """Migrate project information to memory"""
        
        if not project_data:
            return
        
        project_name = project_data.get('name', self.project_path.name)
        created_at = project_data.get('created_at')
        current_phase = project_data.get('current_phase', 'unknown')
        
        # Create project initialization memory
        content = f"""Project '{project_name}' initialized
        
Phase: {current_phase}
Status: {project_data.get('status', 'active')}
Created: {created_at}
        
Project context and configuration established."""
        
        memory = MemoryItem(
            id=generate_memory_id(content, "system"),
            content=content,
            memory_type=MemoryType.PROJECT_CONTEXT,
            timestamp=self._parse_timestamp(created_at) or datetime.now(timezone.utc),
            agent_id="system",
            project_id=project_name,
            importance=ImportanceLevel.HIGH,
            tags=['project', 'initialization', current_phase],
            metadata=MemoryMetadata(
                source="migration",
                workflow_stage="initialization",
                project_phase=current_phase,
                custom={
                    'original_data': project_data,
                    'migration_source': 'project_state'
                }
            )
        )
        
        await self._store_migrated_memory(memory, "project_info")
    
    async def _migrate_agents(self, agents_data: Dict[str, Any]):
        """Migrate agent information to memory"""
        
        if not agents_data:
            return
        
        # Migrate completed agents
        for agent_record in agents_data.get('completed', []):
            await self._migrate_agent_record(agent_record, 'completed')
        
        # Migrate in-progress agents (rare, but handle)
        for agent_record in agents_data.get('in_progress', []):
            await self._migrate_agent_record(agent_record, 'in_progress')
        
        # Migrate pending agents
        for agent_record in agents_data.get('pending', []):
            await self._migrate_agent_record(agent_record, 'pending')
    
    async def _migrate_agent_record(self, agent_record: Dict[str, Any], status: str):
        """Migrate individual agent record"""
        
        agent_id = agent_record.get('agent_id', 'unknown')
        task = agent_record.get('task', 'No task specified')
        
        # Create agent start memory
        if 'started_at' in agent_record:
            start_content = f"Agent {agent_id} started task: {task}"
            
            start_memory = create_memory_from_interaction(
                agent_id=agent_id,
                content=start_content,
                project_id=self.project_path.name,
                interaction_type='start',
                importance=ImportanceLevel.MEDIUM,
                tags=['agent_start', 'workflow', status],
                context={
                    'task': task,
                    'context': agent_record.get('context', {}),
                    'migration_source': 'agent_record',
                    'original_status': status
                }
            )
            
            # Set correct timestamp
            start_memory.timestamp = self._parse_timestamp(
                agent_record['started_at']
            ) or datetime.now(timezone.utc)
            
            await self._store_migrated_memory(start_memory, f"agent_{agent_id}_start")
        
        # Create completion memory if completed
        if status == 'completed' and 'completed_at' in agent_record:
            completion_content = f"Agent {agent_id} completed task: {task}"
            
            success = agent_record.get('success', True)
            if not success:
                completion_content += " (with errors)"
                importance = ImportanceLevel.HIGH  # Errors are important
            else:
                importance = ImportanceLevel.MEDIUM
            
            # Add outputs if available
            if 'outputs' in agent_record:
                outputs = agent_record['outputs']
                completion_content += f"\n\nOutputs:\n{json.dumps(outputs, indent=2)}"
            
            completion_memory = create_memory_from_interaction(
                agent_id=agent_id,
                content=completion_content,
                project_id=self.project_path.name,
                interaction_type='completion',
                importance=importance,
                tags=['agent_completion', 'workflow'] + (['error'] if not success else []),
                context={
                    'task': task,
                    'success': success,
                    'outputs': agent_record.get('outputs', {}),
                    'artifacts': agent_record.get('artifacts', []),
                    'duration_minutes': agent_record.get('duration_minutes', 0),
                    'migration_source': 'agent_record'
                }
            )
            
            completion_memory.timestamp = self._parse_timestamp(
                agent_record['completed_at']
            ) or datetime.now(timezone.utc)
            
            await self._store_migrated_memory(completion_memory, f"agent_{agent_id}_completion")
    
    async def _migrate_artifacts(self, artifacts_data: List[Dict[str, Any]]):
        """Migrate project artifacts to memory"""
        
        for artifact in artifacts_data:
            await self._migrate_single_artifact(artifact)
    
    async def _migrate_single_artifact(self, artifact_data: Dict[str, Any]):
        """Migrate a single artifact record"""
        
        artifact_name = artifact_data.get('name', 'Unnamed Artifact')
        artifact_type = artifact_data.get('type', 'unknown')
        agent_id = artifact_data.get('created_by', 'unknown')
        
        # Determine memory type based on artifact type
        memory_type_mapping = {
            'code': MemoryType.CODE_ARTIFACT,
            'documentation': MemoryType.DOCUMENTATION,
            'config': MemoryType.DEPLOYMENT_CONFIG,
            'test': MemoryType.TEST_CASE,
            'specification': MemoryType.SPECIFICATION,
            'requirement': MemoryType.REQUIREMENT
        }
        
        memory_type = memory_type_mapping.get(artifact_type, MemoryType.CODE_ARTIFACT)
        
        # Create content
        content = f"Artifact '{artifact_name}' created"
        
        if 'description' in artifact_data:
            content += f"\n\nDescription: {artifact_data['description']}"
        
        if 'path' in artifact_data:
            content += f"\nPath: {artifact_data['path']}"
        
        if 'size' in artifact_data:
            content += f"\nSize: {artifact_data['size']} bytes"
        
        # Create memory
        memory = MemoryItem(
            id=generate_memory_id(content, agent_id),
            content=content,
            memory_type=memory_type,
            timestamp=self._parse_timestamp(
                artifact_data.get('created_at')
            ) or datetime.now(timezone.utc),
            agent_id=agent_id,
            project_id=self.project_path.name,
            importance=ImportanceLevel.MEDIUM,
            tags=['artifact', artifact_type, agent_id],
            metadata=MemoryMetadata(
                source="migration",
                custom={
                    'original_artifact': artifact_data,
                    'migration_source': 'artifacts'
                }
            )
        )
        
        await self._store_migrated_memory(memory, f"artifact_{artifact_name}")
    
    async def _migrate_handoffs(self, handoffs_data: List[Dict[str, Any]]):
        """Migrate agent handoffs to memory"""
        
        for handoff in handoffs_data:
            await self._migrate_single_handoff(handoff)
    
    async def _migrate_single_handoff(self, handoff_data: Dict[str, Any]):
        """Migrate a single handoff record"""
        
        from_agent = handoff_data.get('from_agent', 'unknown')
        to_agent = handoff_data.get('to_agent', 'unknown')
        
        content = f"Handoff from {from_agent} to {to_agent}"
        
        if 'summary' in handoff_data:
            content += f"\n\nSummary: {handoff_data['summary']}"
        
        if 'context' in handoff_data:
            content += f"\n\nContext: {json.dumps(handoff_data['context'], indent=2)}"
        
        if 'artifacts' in handoff_data:
            artifacts = handoff_data['artifacts']
            if artifacts:
                content += f"\n\nArtifacts: {', '.join(artifacts)}"
        
        memory = create_memory_from_interaction(
            agent_id=from_agent,
            content=content,
            project_id=self.project_path.name,
            interaction_type='handoff',
            importance=ImportanceLevel.HIGH,  # Handoffs are important
            tags=['handoff', 'agent_transition', from_agent, to_agent],
            context={
                'to_agent': to_agent,
                'handoff_data': handoff_data,
                'migration_source': 'handoffs'
            }
        )
        
        memory.timestamp = self._parse_timestamp(
            handoff_data.get('timestamp')
        ) or datetime.now(timezone.utc)
        
        await self._store_migrated_memory(memory, f"handoff_{from_agent}_{to_agent}")
    
    async def _migrate_context(self, context_data: Dict[str, Any]):
        """Migrate project context to memory"""
        
        if not context_data:
            return
        
        # Create context memory for important context items
        for key, value in context_data.items():
            if self._is_important_context(key, value):
                await self._migrate_context_item(key, value)
    
    async def _migrate_context_item(self, key: str, value: Any):
        """Migrate a single context item"""
        
        content = f"Project context: {key}"
        
        if isinstance(value, str):
            content += f"\n\nValue: {value}"
        else:
            content += f"\n\nValue: {json.dumps(value, indent=2)}"
        
        memory = MemoryItem(
            id=generate_memory_id(content, "system"),
            content=content,
            memory_type=MemoryType.PROJECT_CONTEXT,
            timestamp=datetime.now(timezone.utc),
            agent_id="system",
            project_id=self.project_path.name,
            importance=ImportanceLevel.LOW,
            tags=['context', 'project', key],
            metadata=MemoryMetadata(
                source="migration",
                custom={
                    'context_key': key,
                    'context_value': value,
                    'migration_source': 'context'
                }
            )
        )
        
        await self._store_migrated_memory(memory, f"context_{key}")
    
    async def _migrate_metrics(self, metrics_data: Dict[str, Any]):
        """Migrate project metrics to memory"""
        
        if not metrics_data:
            return
        
        content = "Project metrics summary"
        
        total_agents = metrics_data.get('total_agents_run', 0)
        success_rate = metrics_data.get('success_rate', 0.0)
        total_time = metrics_data.get('total_time_minutes', 0)
        
        content += f"""
        
Total agents run: {total_agents}
Success rate: {success_rate:.1%}
Total time: {total_time} minutes
        """
        
        memory = MemoryItem(
            id=generate_memory_id(content, "system"),
            content=content,
            memory_type=MemoryType.MEMORY_STATS,
            timestamp=datetime.now(timezone.utc),
            agent_id="system",
            project_id=self.project_path.name,
            importance=ImportanceLevel.LOW,
            tags=['metrics', 'statistics', 'project'],
            metadata=MemoryMetadata(
                source="migration",
                custom={
                    'original_metrics': metrics_data,
                    'migration_source': 'metrics'
                }
            )
        )
        
        await self._store_migrated_memory(memory, "project_metrics")
    
    async def _store_migrated_memory(self, memory: MemoryItem, item_name: str):
        """Store a migrated memory item with error handling"""
        
        try:
            self.migration_stats['total_items_processed'] += 1
            
            if self.memory_system:
                await self.memory_system.add_memory(
                    content=memory.content,
                    agent_id=memory.agent_id,
                    project_id=memory.project_id,
                    context=memory.metadata.custom,
                    tags=memory.tags,
                    memory_type=memory.memory_type
                )
            
            self.migration_stats['successfully_migrated'] += 1
            self.migration_log.append(f"✓ Migrated {item_name}")
            logger.debug(f"Successfully migrated: {item_name}")
            
        except Exception as e:
            self.migration_stats['failed_migrations'] += 1
            error_msg = f"✗ Failed to migrate {item_name}: {str(e)}"
            self.migration_log.append(error_msg)
            logger.error(error_msg)
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        
        if not timestamp_str:
            return None
        
        try:
            # Try ISO format first
            if 'T' in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str)
            else:
                # Try common formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(timestamp_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            
            # Ensure timezone info
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            return dt
            
        except Exception as e:
            logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}")
            return None
    
    def _is_important_context(self, key: str, value: Any) -> bool:
        """Determine if context item is important enough to migrate"""
        
        # Skip very common/trivial context
        trivial_keys = {'last_update', 'tmp_', 'cache_', '_internal'}
        
        if any(trivial in key.lower() for trivial in trivial_keys):
            return False
        
        # Skip empty values
        if not value or (isinstance(value, str) and len(value.strip()) < 3):
            return False
        
        return True
    
    def _create_migration_result(self, success: bool, message: str = None) -> Dict[str, Any]:
        """Create migration result dictionary"""
        
        duration = None
        if self.migration_stats['start_time'] and self.migration_stats['end_time']:
            duration = (
                self.migration_stats['end_time'] - self.migration_stats['start_time']
            ).total_seconds()
        
        result = {
            'success': success,
            'message': message or ("Migration completed successfully" if success else "Migration failed"),
            'statistics': self.migration_stats.copy(),
            'duration_seconds': duration,
            'migration_log': self.migration_log.copy()
        }
        
        if success:
            result['summary'] = (
                f"Successfully migrated {self.migration_stats['successfully_migrated']} "
                f"out of {self.migration_stats['total_items_processed']} items"
            )
        
        return result
    
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify migration by checking stored memories"""
        
        if not self.memory_system:
            return {'success': False, 'message': 'No memory system available for verification'}
        
        try:
            # Search for migrated memories
            project_memories = await self.memory_system.search_memories(
                query="",  # Get all memories
                project_id=self.project_path.name,
                limit=1000
            )
            
            # Analyze memories
            by_type = {}
            by_agent = {}
            by_source = {}
            
            for memory in project_memories:
                # Group by memory type
                memory_type = memory.memory_type.value
                by_type[memory_type] = by_type.get(memory_type, 0) + 1
                
                # Group by agent
                agent_id = memory.agent_id
                by_agent[agent_id] = by_agent.get(agent_id, 0) + 1
                
                # Group by migration source
                source = memory.metadata.custom.get('migration_source', 'unknown')
                by_source[source] = by_source.get(source, 0) + 1
            
            verification_result = {
                'success': True,
                'total_memories_found': len(project_memories),
                'breakdown_by_type': by_type,
                'breakdown_by_agent': by_agent,
                'breakdown_by_source': by_source,
                'migration_statistics': self.migration_stats
            }
            
            return verification_result
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Verification failed: {str(e)}"
            }
    
    async def rollback_migration(self, backup_file: Path = None) -> Dict[str, Any]:
        """Rollback migration by restoring from backup"""
        
        try:
            backup_path = backup_file or self.project_path / '.coral' / 'project_state.yaml.backup'
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'message': f'Backup file not found: {backup_path}'
                }
            
            # Restore backup
            original_path = backup_path.with_suffix('')  # Remove .backup
            original_path.write_text(backup_path.read_text())
            
            logger.info(f"Restored backup from {backup_path} to {original_path}")
            
            return {
                'success': True,
                'message': f'Successfully restored from backup: {backup_path}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Rollback failed: {str(e)}'
            }


async def migrate_project_to_memory(
    project_path: Path = None,
    memory_config_path: str = None,
    verify: bool = True,
    backup: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to migrate a project to memory system
    
    Args:
        project_path: Path to project directory
        memory_config_path: Path to memory configuration
        verify: Whether to verify migration results
        backup: Whether to backup existing state
        
    Returns:
        Migration results
    """
    
    project_path = project_path or Path.cwd()
    
    # Initialize memory system for migration
    from .memory_system import MemorySystem
    memory_system = MemorySystem(memory_config_path)
    
    # Initialize migration
    migration = MemoryMigration(project_path, memory_system)
    
    # Perform migration
    result = await migration.migrate_project_state(backup_existing=backup)
    
    # Verify if requested
    if verify and result['success']:
        verification = await migration.verify_migration()
        result['verification'] = verification
    
    return result


if __name__ == "__main__":
    """Command-line interface for migration"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate CoralCollective project state to memory system")
    parser.add_argument("--project", type=Path, help="Project directory path")
    parser.add_argument("--config", help="Memory system configuration path")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--no-verify", action="store_true", help="Skip migration verification")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        result = await migrate_project_to_memory(
            project_path=args.project,
            memory_config_path=args.config,
            backup=not args.no_backup,
            verify=not args.no_verify
        )
        
        print("\nMigration Results:")
        print("=" * 50)
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        
        if 'statistics' in result:
            stats = result['statistics']
            print(f"\nStatistics:")
            print(f"  Total items processed: {stats['total_items_processed']}")
            print(f"  Successfully migrated: {stats['successfully_migrated']}")
            print(f"  Failed migrations: {stats['failed_migrations']}")
            print(f"  Duration: {result.get('duration_seconds', 0):.2f} seconds")
        
        if 'verification' in result:
            verification = result['verification']
            print(f"\nVerification:")
            print(f"  Total memories found: {verification['total_memories_found']}")
            print(f"  Memory types: {list(verification['breakdown_by_type'].keys())}")
        
        if 'migration_log' in result:
            print(f"\nMigration Log:")
            for log_entry in result['migration_log'][-10:]:  # Last 10 entries
                print(f"  {log_entry}")
    
    asyncio.run(main())