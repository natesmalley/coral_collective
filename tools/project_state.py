"""
Project State Management System for CoralCollective

Tracks agent activities, artifacts, and project progress to enable
better coordination between agents and maintain context across sessions.
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib


class ProjectStateManager:
    """Manages project state across agent interactions"""
    
    def __init__(self, project_path: Path = None):
        """Initialize state manager
        
        Args:
            project_path: Path to project directory (defaults to current)
        """
        self.project_path = project_path or Path.cwd()
        self.state_file = self.project_path / '.coral' / 'project_state.yaml'
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing state or create new
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load existing state or create default"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return yaml.safe_load(f) or self._default_state()
        return self._default_state()
    
    def _default_state(self) -> Dict:
        """Create default state structure"""
        return {
            'project': {
                'name': self.project_path.name,
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'current_phase': 'planning',
                'status': 'active'
            },
            'agents': {
                'completed': [],
                'in_progress': [],
                'pending': []
            },
            'artifacts': [],
            'context': {},
            'handoffs': [],
            'metrics': {
                'total_agents_run': 0,
                'success_rate': 0.0,
                'total_time_minutes': 0
            }
        }
    
    def save_state(self):
        """Persist state to disk"""
        self.state['project']['last_modified'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            yaml.dump(self.state, f, default_flow_style=False, sort_keys=False)
    
    def record_agent_start(self, agent_id: str, task: str, context: Dict = None):
        """Record when an agent starts working
        
        Args:
            agent_id: ID of the agent
            task: Task description
            context: Optional context data
        """
        agent_record = {
            'agent_id': agent_id,
            'task': task,
            'started_at': datetime.now().isoformat(),
            'context': context or {}
        }
        
        # Move from pending to in_progress
        self.state['agents']['in_progress'].append(agent_record)
        
        # Remove from pending if exists
        self.state['agents']['pending'] = [
            a for a in self.state['agents']['pending'] 
            if a.get('agent_id') != agent_id
        ]
        
        self.save_state()
        return agent_record
    
    def record_agent_completion(self, agent_id: str, success: bool = True, 
                               outputs: Dict = None, artifacts: List[Dict] = None):
        """Record when an agent completes
        
        Args:
            agent_id: ID of the agent
            success: Whether task was successful
            outputs: Agent outputs/results
            artifacts: List of created artifacts
        """
        # Find the in-progress record
        in_progress = None
        for record in self.state['agents']['in_progress']:
            if record['agent_id'] == agent_id:
                in_progress = record
                break
        
        if in_progress:
            # Calculate duration
            started = datetime.fromisoformat(in_progress['started_at'])
            duration_minutes = (datetime.now() - started).total_seconds() / 60
            
            # Create completion record
            completion = {
                **in_progress,
                'completed_at': datetime.now().isoformat(),
                'duration_minutes': round(duration_minutes, 2),
                'success': success,
                'outputs': outputs or {}
            }
            
            # Move to completed
            self.state['agents']['completed'].append(completion)
            self.state['agents']['in_progress'] = [
                r for r in self.state['agents']['in_progress']
                if r['agent_id'] != agent_id
            ]
            
            # Update metrics
            self.state['metrics']['total_agents_run'] += 1
            self.state['metrics']['total_time_minutes'] += duration_minutes
            
            # Calculate success rate
            completed = self.state['agents']['completed']
            successful = sum(1 for a in completed if a.get('success', True))
            self.state['metrics']['success_rate'] = successful / len(completed)
            
            # Record artifacts
            if artifacts:
                for artifact in artifacts:
                    self.add_artifact(artifact['type'], artifact['path'], agent_id)
            
            self.save_state()
            return completion
        
        return None
    
    def add_artifact(self, artifact_type: str, path: str, created_by: str, 
                    metadata: Dict = None):
        """Record an artifact created by an agent
        
        Args:
            artifact_type: Type of artifact (documentation, source_code, etc)
            path: Path to the artifact
            created_by: Agent that created it
            metadata: Optional metadata
        """
        artifact = {
            'id': self._generate_id(f"{artifact_type}:{path}"),
            'type': artifact_type,
            'path': path,
            'created_by': created_by,
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Check if artifact already exists
        existing = [a for a in self.state['artifacts'] if a['path'] == path]
        if existing:
            # Update existing artifact
            idx = self.state['artifacts'].index(existing[0])
            self.state['artifacts'][idx] = artifact
        else:
            self.state['artifacts'].append(artifact)
        
        self.save_state()
        return artifact
    
    def record_handoff(self, from_agent: str, to_agent: str, 
                      handoff_data: Dict):
        """Record a handoff between agents
        
        Args:
            from_agent: Agent handing off
            to_agent: Agent receiving
            handoff_data: Data being passed
        """
        handoff = {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'timestamp': datetime.now().isoformat(),
            'data': handoff_data
        }
        
        self.state['handoffs'].append(handoff)
        
        # Add to pending if not already processed
        if not any(a['agent_id'] == to_agent for a in 
                  self.state['agents']['completed'] + 
                  self.state['agents']['in_progress']):
            self.state['agents']['pending'].append({
                'agent_id': to_agent,
                'added_at': datetime.now().isoformat(),
                'added_by': from_agent,
                'reason': handoff_data.get('reason', 'Agent handoff')
            })
        
        self.save_state()
        return handoff
    
    def get_agent_history(self, agent_id: str) -> List[Dict]:
        """Get all historical runs of an agent
        
        Args:
            agent_id: Agent to look up
            
        Returns:
            List of all runs for this agent
        """
        return [
            record for record in self.state['agents']['completed']
            if record['agent_id'] == agent_id
        ]
    
    def get_artifacts_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all artifacts created by an agent
        
        Args:
            agent_id: Agent to look up
            
        Returns:
            List of artifacts
        """
        return [
            artifact for artifact in self.state['artifacts']
            if artifact['created_by'] == agent_id
        ]
    
    def get_artifacts_by_type(self, artifact_type: str) -> List[Dict]:
        """Get all artifacts of a specific type
        
        Args:
            artifact_type: Type to filter by
            
        Returns:
            List of artifacts
        """
        return [
            artifact for artifact in self.state['artifacts']
            if artifact['type'] == artifact_type
        ]
    
    def get_last_handoff_for(self, agent_id: str) -> Optional[Dict]:
        """Get the last handoff directed to an agent
        
        Args:
            agent_id: Agent to look up
            
        Returns:
            Last handoff data or None
        """
        handoffs = [
            h for h in self.state['handoffs']
            if h['to_agent'] == agent_id
        ]
        return handoffs[-1] if handoffs else None
    
    def update_context(self, key: str, value: Any):
        """Update shared context
        
        Args:
            key: Context key
            value: Context value
        """
        self.state['context'][key] = value
        self.save_state()
    
    def get_context(self, key: str = None) -> Any:
        """Get shared context
        
        Args:
            key: Specific key to retrieve (None for all)
            
        Returns:
            Context value or full context dict
        """
        if key:
            return self.state['context'].get(key)
        return self.state['context']
    
    def set_phase(self, phase: str):
        """Update project phase
        
        Args:
            phase: New phase (planning, development, testing, deployment, etc)
        """
        self.state['project']['current_phase'] = phase
        self.save_state()
    
    def get_summary(self) -> Dict:
        """Get project summary
        
        Returns:
            Summary statistics
        """
        return {
            'project_name': self.state['project']['name'],
            'current_phase': self.state['project']['current_phase'],
            'agents_completed': len(self.state['agents']['completed']),
            'agents_in_progress': len(self.state['agents']['in_progress']),
            'agents_pending': len(self.state['agents']['pending']),
            'total_artifacts': len(self.state['artifacts']),
            'success_rate': self.state['metrics']['success_rate'],
            'total_time_minutes': self.state['metrics']['total_time_minutes']
        }
    
    def _generate_id(self, seed: str) -> str:
        """Generate a unique ID
        
        Args:
            seed: Seed string for ID generation
            
        Returns:
            8-character hex ID
        """
        return hashlib.sha256(seed.encode()).hexdigest()[:8]
    
    def export_state(self, output_path: Path = None) -> Path:
        """Export state to JSON
        
        Args:
            output_path: Optional output path
            
        Returns:
            Path to exported file
        """
        output_path = output_path or self.project_path / 'project_state_export.json'
        with open(output_path, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
        return output_path


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Project State Manager")
    parser.add_argument('command', choices=['summary', 'export', 'agents', 'artifacts'])
    parser.add_argument('--project-path', type=Path, default=Path.cwd())
    
    args = parser.parse_args()
    
    manager = ProjectStateManager(args.project_path)
    
    if args.command == 'summary':
        summary = manager.get_summary()
        print(yaml.dump(summary, default_flow_style=False))
    
    elif args.command == 'export':
        path = manager.export_state()
        print(f"State exported to: {path}")
    
    elif args.command == 'agents':
        print("Completed agents:")
        for agent in manager.state['agents']['completed']:
            print(f"  - {agent['agent_id']}: {agent.get('success', True)}")
    
    elif args.command == 'artifacts':
        print("Project artifacts:")
        for artifact in manager.state['artifacts']:
            print(f"  - {artifact['type']}: {artifact['path']}")