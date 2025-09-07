"""
Migration Strategy for CoralCollective Memory System

Migrates existing project state data to the new advanced memory system
while preserving all historical information and maintaining compatibility.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

from .memory_system import MemorySystem, MemoryItem, MemoryType, ImportanceLevel
from .coral_memory_integration import CoralMemoryIntegration, initialize_project_memory, create_memory_config
from ..tools.project_state import ProjectStateManager

logger = logging.getLogger(__name__)

class MemoryMigrationStrategy:
    """Handles migration from existing project state to memory system"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.coral_path = project_path / '.coral'
        self.backup_path = self.coral_path / 'migration_backup'
        
        # Initialize managers
        self.state_manager = ProjectStateManager(project_path)
        self.memory_integration: Optional[CoralMemoryIntegration] = None
        
    async def migrate_project(self, preserve_existing: bool = True) -> Dict[str, Any]:
        """
        Migrate existing project state to memory system
        
        Args:
            preserve_existing: Keep existing project_state.yaml for compatibility
            
        Returns:
            Migration report
        """
        
        logger.info(f"Starting memory migration for project: {self.project_path.name}")
        
        # Create backup
        if preserve_existing:
            await self._create_backup()
            
        # Initialize memory system
        config_path = create_memory_config(self.project_path)
        self.memory_integration = await initialize_project_memory(
            self.project_path, str(config_path)
        )
        
        migration_report = {
            'project_name': self.project_path.name,
            'migration_timestamp': datetime.now().isoformat(),
            'migrated_items': {},
            'errors': [],
            'statistics': {}
        }
        
        try:
            # Migrate different types of data
            await self._migrate_agent_activities(migration_report)
            await self._migrate_handoffs(migration_report)
            await self._migrate_artifacts(migration_report)
            await self._migrate_context(migration_report)
            
            # Generate statistics
            migration_report['statistics'] = await self._generate_migration_stats()
            
            # Create migration log
            await self._create_migration_log(migration_report)
            
            logger.info("Memory migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration error: {e}")
            migration_report['errors'].append({
                'type': 'migration_failure',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
        return migration_report
        
    async def _create_backup(self):
        """Create backup of existing state"""
        
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Backup project state
        state_file = self.coral_path / 'project_state.yaml'
        if state_file.exists():
            backup_state = self.backup_path / f'project_state_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
            backup_state.write_text(state_file.read_text())
            
        logger.info(f"Backup created at: {self.backup_path}")
        
    async def _migrate_agent_activities(self, report: Dict[str, Any]):
        """Migrate agent activities to memory system"""
        
        migrated_count = 0
        errors = []
        
        # Migrate completed agents
        for agent_record in self.state_manager.state['agents']['completed']:
            try:
                # Create start memory
                start_content = f"Agent {agent_record['agent_id']} started task: {agent_record.get('task', 'Unknown task')}"
                start_context = {
                    'type': 'agent_start',
                    'task': agent_record.get('task', ''),
                    'original_context': agent_record.get('context', {}),
                    'migrated_from': 'project_state'
                }
                
                await self.memory_integration.memory_system.add_memory(
                    content=start_content,
                    agent_id=agent_record['agent_id'],
                    project_id=self.memory_integration.project_id,
                    context=start_context,
                    tags=['agent_start', 'migrated', 'workflow'],
                    memory_type=MemoryType.EPISODIC
                )
                
                # Create completion memory
                status = "completed successfully" if agent_record.get('success', True) else "completed with errors"
                completion_content = f"Agent {agent_record['agent_id']} {status}"
                
                if agent_record.get('outputs'):
                    completion_content += f"\n\nOutputs: {json.dumps(agent_record['outputs'], indent=2)}"
                    
                completion_context = {
                    'type': 'agent_completion',
                    'success': agent_record.get('success', True),
                    'duration_minutes': agent_record.get('duration_minutes', 0),
                    'outputs': agent_record.get('outputs', {}),
                    'migrated_from': 'project_state'
                }
                
                await self.memory_integration.memory_system.add_memory(
                    content=completion_content,
                    agent_id=agent_record['agent_id'],
                    project_id=self.memory_integration.project_id,
                    context=completion_context,
                    tags=['agent_completion', 'migrated', 'workflow'],
                    memory_type=MemoryType.EPISODIC
                )
                
                migrated_count += 2  # Start and completion
                
            except Exception as e:
                error_msg = f"Failed to migrate agent {agent_record.get('agent_id', 'unknown')}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
        report['migrated_items']['agent_activities'] = migrated_count
        report['errors'].extend(errors)
        
        logger.info(f"Migrated {migrated_count} agent activity records")
        
    async def _migrate_handoffs(self, report: Dict[str, Any]):
        """Migrate agent handoffs to memory system"""
        
        migrated_count = 0
        errors = []
        
        for handoff in self.state_manager.state['handoffs']:
            try:
                content = f"Handoff from {handoff['from_agent']} to {handoff['to_agent']}"
                if 'data' in handoff and handoff['data'].get('summary'):
                    content += f": {handoff['data']['summary']}"
                    
                context = {
                    'type': 'handoff',
                    'from_agent': handoff['from_agent'],
                    'to_agent': handoff['to_agent'],
                    'handoff_data': handoff.get('data', {}),
                    'migrated_from': 'project_state'
                }
                
                await self.memory_integration.memory_system.add_memory(
                    content=content,
                    agent_id=handoff['from_agent'],
                    project_id=self.memory_integration.project_id,
                    context=context,
                    tags=['handoff', 'migrated', 'agent_transition'],
                    memory_type=MemoryType.EPISODIC
                )
                
                migrated_count += 1
                
            except Exception as e:
                error_msg = f"Failed to migrate handoff {handoff.get('from_agent', 'unknown')} -> {handoff.get('to_agent', 'unknown')}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
        report['migrated_items']['handoffs'] = migrated_count
        report['errors'].extend(errors)
        
        logger.info(f"Migrated {migrated_count} handoff records")
        
    async def _migrate_artifacts(self, report: Dict[str, Any]):
        """Migrate project artifacts to memory system"""
        
        migrated_count = 0
        errors = []
        
        for artifact in self.state_manager.state['artifacts']:
            try:
                content = f"Artifact created: {artifact['type']} at {artifact['path']}"
                if artifact.get('metadata'):
                    content += f"\nMetadata: {json.dumps(artifact['metadata'], indent=2)}"
                    
                context = {
                    'type': 'artifact_creation',
                    'artifact_type': artifact['type'],
                    'artifact_path': artifact['path'],
                    'metadata': artifact.get('metadata', {}),
                    'migrated_from': 'project_state'
                }
                
                # Artifacts are important for project continuity
                importance = ImportanceLevel.MEDIUM
                if artifact['type'] in ['documentation', 'architecture', 'api_spec']:
                    importance = ImportanceLevel.HIGH
                    
                await self.memory_integration.memory_system.add_memory(
                    content=content,
                    agent_id=artifact['created_by'],
                    project_id=self.memory_integration.project_id,
                    context=context,
                    tags=['artifact', 'migrated', artifact['type']],
                    memory_type=MemoryType.SEMANTIC
                )
                
                migrated_count += 1
                
            except Exception as e:
                error_msg = f"Failed to migrate artifact {artifact.get('path', 'unknown')}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
        report['migrated_items']['artifacts'] = migrated_count
        report['errors'].extend(errors)
        
        logger.info(f"Migrated {migrated_count} artifact records")
        
    async def _migrate_context(self, report: Dict[str, Any]):
        """Migrate shared context to memory system"""
        
        migrated_count = 0
        errors = []
        
        shared_context = self.state_manager.get_context()
        
        if shared_context:
            try:
                content = f"Project shared context:\n{json.dumps(shared_context, indent=2)}"
                
                context = {
                    'type': 'shared_context',
                    'context_data': shared_context,
                    'migrated_from': 'project_state'
                }
                
                await self.memory_integration.memory_system.add_memory(
                    content=content,
                    agent_id="project_system",
                    project_id=self.memory_integration.project_id,
                    context=context,
                    tags=['context', 'migrated', 'project_state'],
                    memory_type=MemoryType.SEMANTIC
                )
                
                migrated_count = 1
                
            except Exception as e:
                error_msg = f"Failed to migrate shared context: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
        report['migrated_items']['shared_context'] = migrated_count
        report['errors'].extend(errors)
        
        logger.info(f"Migrated shared context")
        
    async def _generate_migration_stats(self) -> Dict[str, Any]:
        """Generate migration statistics"""
        
        memory_stats = self.memory_integration.memory_system.get_memory_stats()
        project_summary = self.state_manager.get_summary()
        
        return {
            'original_project_stats': project_summary,
            'new_memory_stats': memory_stats,
            'migration_efficiency': {
                'total_original_items': (
                    len(self.state_manager.state['agents']['completed']) +
                    len(self.state_manager.state['handoffs']) +
                    len(self.state_manager.state['artifacts'])
                ),
                'total_migrated_memories': memory_stats['short_term_memories'] + memory_stats['long_term_memories']
            }
        }
        
    async def _create_migration_log(self, report: Dict[str, Any]):
        """Create detailed migration log"""
        
        log_path = self.coral_path / 'memory_migration_log.json'
        
        with open(log_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        logger.info(f"Migration log created at: {log_path}")
        
    async def rollback_migration(self) -> bool:
        """Rollback migration if needed"""
        
        try:
            # Remove memory data
            memory_dir = self.coral_path / 'memory'
            if memory_dir.exists():
                import shutil
                shutil.rmtree(memory_dir)
                
            # Restore backup
            backup_files = list(self.backup_path.glob('project_state_backup_*.yaml'))
            if backup_files:
                latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
                state_file = self.coral_path / 'project_state.yaml'
                state_file.write_text(latest_backup.read_text())
                
            logger.info("Migration rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

class MemorySystemValidator:
    """Validates memory system integrity after migration"""
    
    def __init__(self, memory_integration: CoralMemoryIntegration):
        self.memory_integration = memory_integration
        
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate migration integrity"""
        
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'passed',
            'recommendations': []
        }
        
        # Test memory storage
        validation_report['tests']['memory_storage'] = await self._test_memory_storage()
        
        # Test search functionality
        validation_report['tests']['search_functionality'] = await self._test_search()
        
        # Test agent context retrieval
        validation_report['tests']['context_retrieval'] = await self._test_context_retrieval()
        
        # Test memory consolidation
        validation_report['tests']['consolidation'] = await self._test_consolidation()
        
        # Check for any failed tests
        failed_tests = [name for name, result in validation_report['tests'].items() if not result['passed']]
        if failed_tests:
            validation_report['overall_status'] = 'failed'
            validation_report['recommendations'].append(f"Failed tests: {', '.join(failed_tests)}")
            
        return validation_report
        
    async def _test_memory_storage(self) -> Dict[str, Any]:
        """Test memory storage functionality"""
        
        try:
            test_memory_id = await self.memory_integration.memory_system.add_memory(
                content="Migration validation test",
                agent_id="validator",
                project_id=self.memory_integration.project_id,
                context={'type': 'validation_test'},
                tags=['validation', 'test']
            )
            
            return {
                'passed': bool(test_memory_id),
                'memory_id': test_memory_id,
                'message': 'Memory storage test passed'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'message': 'Memory storage test failed'
            }
            
    async def _test_search(self) -> Dict[str, Any]:
        """Test search functionality"""
        
        try:
            results = await self.memory_integration.search_project_knowledge(
                query="validation test",
                limit=5
            )
            
            return {
                'passed': True,
                'results_count': len(results),
                'message': 'Search functionality test passed'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'message': 'Search functionality test failed'
            }
            
    async def _test_context_retrieval(self) -> Dict[str, Any]:
        """Test agent context retrieval"""
        
        try:
            context = await self.memory_integration.get_agent_context("validator")
            
            return {
                'passed': bool(context),
                'context_keys': list(context.keys()) if context else [],
                'message': 'Context retrieval test passed'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'message': 'Context retrieval test failed'
            }
            
    async def _test_consolidation(self) -> Dict[str, Any]:
        """Test memory consolidation"""
        
        try:
            await self.memory_integration.consolidate_session_memory()
            
            return {
                'passed': True,
                'message': 'Memory consolidation test passed'
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'message': 'Memory consolidation test failed'
            }

# CLI interface for migration
async def run_migration(project_path: str, preserve_existing: bool = True) -> Dict[str, Any]:
    """Run memory migration for a project"""
    
    path = Path(project_path)
    migration = MemoryMigrationStrategy(path)
    
    # Run migration
    report = await migration.migrate_project(preserve_existing)
    
    # Validate migration
    if migration.memory_integration:
        validator = MemorySystemValidator(migration.memory_integration)
        validation = await validator.validate_migration()
        report['validation'] = validation
        
    return report

if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description="CoralCollective Memory Migration")
    parser.add_argument("project_path", help="Path to project directory")
    parser.add_argument("--no-preserve", action="store_true", help="Don't preserve existing project state")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation")
    
    args = parser.parse_args()
    
    async def main():
        if args.validate_only:
            # Initialize memory system and validate
            memory_integration = await initialize_project_memory(Path(args.project_path))
            validator = MemorySystemValidator(memory_integration)
            validation = await validator.validate_migration()
            print(json.dumps(validation, indent=2))
        else:
            # Run full migration
            report = await run_migration(args.project_path, not args.no_preserve)
            print(json.dumps(report, indent=2))
            
    asyncio.run(main())