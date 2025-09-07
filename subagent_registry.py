#!/usr/bin/env python3
"""
Subagent Registry for Claude
This module registers CoralCollective agents as Claude subagents that can be invoked directly.
"""

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import re

class SubagentRegistry:
    """Registry for Claude to access CoralCollective agents as subagents"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.agents = self._load_agents()
        self.subagents = {}
        self._register_all_subagents()
    
    def _load_agents(self) -> Dict:
        """Load agent configuration"""
        config_path = self.base_path / "claude_code_agents.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f).get('agents', {})
        
        # Fallback to YAML config
        yaml_config_path = self.base_path / "config" / "agents.yaml"
        if yaml_config_path.exists():
            with open(yaml_config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('agents', {})
        
        return {}
    
    def _register_all_subagents(self):
        """Register all agents as Claude subagents"""
        for agent_id, agent_info in self.agents.items():
            self.register_subagent(agent_id, agent_info)
    
    def register_subagent(self, agent_id: str, agent_info: Dict):
        """Register a single agent as a Claude subagent"""
        
        # Create subagent function
        def subagent_function(task: str, context: Optional[Dict] = None) -> Dict:
            """Subagent execution function"""
            return self.invoke_subagent(agent_id, task, context)
        
        # Register with metadata
        self.subagents[agent_id] = {
            'function': subagent_function,
            'metadata': {
                'name': agent_info.get('name', agent_id),
                'description': agent_info.get('description', ''),
                'category': agent_info.get('category', ''),
                'capabilities': agent_info.get('capabilities', []),
                'prompt_path': agent_info.get('prompt_path', ''),
                'invocation_pattern': f"@{agent_id}",
                'aliases': self._generate_aliases(agent_id, agent_info)
            }
        }
    
    def _generate_aliases(self, agent_id: str, agent_info: Dict) -> List[str]:
        """Generate alternative invocation patterns for an agent"""
        aliases = [
            f"@{agent_id}",
            f"@{agent_id.replace('_', '-')}",
            f"@{agent_info.get('category', '')}/{agent_id}" if agent_info.get('category') else None,
        ]
        
        # Add capability-based aliases
        for capability in agent_info.get('capabilities', []):
            aliases.append(f"@do/{capability}")
        
        # Add role-based alias
        name = agent_info.get('name', '').lower().replace(' ', '_')
        if name:
            aliases.append(f"@role/{name}")
        
        return [a for a in aliases if a]
    
    def invoke_subagent(self, agent_id: str, task: str, context: Optional[Dict] = None) -> Dict:
        """Invoke a subagent with a task"""
        
        if agent_id not in self.agents:
            return {
                'status': 'error',
                'message': f'Subagent {agent_id} not found',
                'available_subagents': list(self.agents.keys())
            }
        
        agent_info = self.agents[agent_id]
        prompt_path = self.base_path / agent_info.get('prompt_path', f'agents/specialists/{agent_id}.md')
        
        # Try alternate paths if primary doesn't exist
        if not prompt_path.exists():
            alt_paths = [
                self.base_path / f'agents/core/{agent_id}.md',
                self.base_path / f'agents/specialists/{agent_id}.md'
            ]
            for path in alt_paths:
                if path.exists():
                    prompt_path = path
                    break
        
        if not prompt_path.exists():
            return {
                'status': 'error',
                'message': f'Prompt file not found for subagent {agent_id}'
            }
        
        # Load the prompt
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
        
        # Build the subagent response
        response = {
            'status': 'success',
            'subagent': agent_id,
            'name': agent_info.get('name', agent_id),
            'task': task,
            'context': context or {},
            'prompt': prompt_content,
            'instructions': self._extract_instructions(prompt_content),
            'next_subagents': self._get_next_subagents(agent_id),
            'capabilities': agent_info.get('capabilities', [])
        }
        
        # Add task to prompt if specified
        if task:
            response['full_prompt'] = f"{prompt_content}\n\n## Current Task\n{task}"
        
        return response
    
    def _extract_instructions(self, prompt_content: str) -> List[str]:
        """Extract key instructions from agent prompt"""
        instructions = []
        
        # Look for numbered lists or bullet points
        patterns = [
            r'^\d+\.\s+(.+)$',  # Numbered lists
            r'^[-*]\s+(.+)$',   # Bullet points
            r'^###\s+(.+)$',    # Subsections
        ]
        
        lines = prompt_content.split('\n')
        for line in lines[:50]:  # Check first 50 lines for instructions
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    instructions.append(match.group(1))
                    if len(instructions) >= 10:  # Limit to 10 instructions
                        return instructions
        
        return instructions
    
    def _get_next_subagents(self, current_agent: str) -> List[str]:
        """Get recommended next subagents"""
        recommendations = {
            'project_architect': ['@technical_writer_phase1', '@api_designer', '@database_specialist'],
            'technical_writer_phase1': ['@backend_developer', '@frontend_developer'],
            'backend_developer': ['@frontend_developer', '@database_specialist', '@qa_testing'],
            'frontend_developer': ['@qa_testing', '@accessibility_specialist'],
            'api_designer': ['@backend_developer', '@frontend_developer'],
            'database_specialist': ['@backend_developer', '@data_engineer'],
            'qa_testing': ['@devops_deployment', '@performance_engineer'],
            'devops_deployment': ['@site_reliability_engineer', '@technical_writer_phase2'],
        }
        return recommendations.get(current_agent, ['@qa_testing', '@devops_deployment'])
    
    def find_subagent_by_alias(self, alias: str) -> Optional[str]:
        """Find subagent by any of its aliases"""
        for agent_id, subagent_info in self.subagents.items():
            if alias in subagent_info['metadata']['aliases']:
                return agent_id
        return None
    
    def get_subagent_help(self, agent_id: str) -> str:
        """Get help text for a subagent"""
        if agent_id not in self.subagents:
            return f"Subagent {agent_id} not found"
        
        metadata = self.subagents[agent_id]['metadata']
        help_text = f"""
Subagent: {metadata['name']}
ID: @{agent_id}
Category: {metadata['category']}
Description: {metadata['description']}

Capabilities:
{chr(10).join('  - ' + cap for cap in metadata['capabilities'])}

Invocation patterns:
{chr(10).join('  ' + alias for alias in metadata['aliases'])}

Example usage:
  @{agent_id} "Your task here"
  @{agent_id} {{
    "task": "Your task",
    "context": {{"previous_work": "..."}}
  }}
"""
        return help_text
    
    def list_subagents_by_category(self) -> Dict[str, List[Dict]]:
        """List all subagents organized by category"""
        categories = {}
        
        for agent_id, subagent_info in self.subagents.items():
            category = subagent_info['metadata']['category'] or 'uncategorized'
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'id': f"@{agent_id}",
                'name': subagent_info['metadata']['name'],
                'description': subagent_info['metadata']['description'],
                'capabilities': subagent_info['metadata']['capabilities']
            })
        
        return categories
    
    def get_workflow_subagents(self, workflow_type: str = 'full_stack_web') -> List[str]:
        """Get subagents for a specific workflow"""
        workflows = {
            'full_stack_web': [
                '@project_architect',
                '@technical_writer_phase1',
                '@backend_developer',
                '@frontend_developer',
                '@database_specialist',
                '@qa_testing',
                '@security_specialist',
                '@devops_deployment',
                '@technical_writer_phase2'
            ],
            'api_service': [
                '@project_architect',
                '@api_designer',
                '@backend_developer',
                '@database_specialist',
                '@qa_testing',
                '@devops_deployment'
            ],
            'ai_application': [
                '@project_architect',
                '@technical_writer_phase1',
                '@ai_ml_specialist',
                '@backend_developer',
                '@frontend_developer',
                '@devops_deployment',
                '@site_reliability_engineer'
            ]
        }
        return workflows.get(workflow_type, [])
    
    def create_subagent_chain(self, agent_ids: List[str]) -> Callable:
        """Create a chain of subagents that execute in sequence"""
        def chain_executor(initial_task: str) -> List[Dict]:
            results = []
            context = {'task': initial_task, 'results': []}
            
            for agent_id in agent_ids:
                # Remove @ prefix if present
                clean_id = agent_id.replace('@', '')
                
                # Invoke subagent with accumulated context
                result = self.invoke_subagent(clean_id, initial_task, context)
                results.append(result)
                
                # Update context for next agent
                context['results'].append({
                    'agent': clean_id,
                    'status': result.get('status'),
                    'output': result.get('prompt', '')[:500]  # First 500 chars
                })
            
            return results
        
        return chain_executor
    
    def register_with_claude(self) -> bool:
        """Register CoralCollective agents with Claude Code"""
        try:
            # Create subagent definitions
            subagents = self.create_subagent_definitions()
            
            # Save to a format Claude Code can discover
            output_file = self.base_path / "coral_subagents.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "version": "1.0",
                    "provider": "CoralCollective",
                    "subagents": subagents
                }, f, indent=2)
            
            print(f"✅ Registered {len(subagents)} CoralCollective agents")
            print(f"📄 Subagent definitions saved to: {output_file}")
            
            # Also create individual agent files for Task tool
            for agent in subagents:
                agent_file = self.base_path / f"agents_claude/{agent['id']}.json"
                agent_file.parent.mkdir(exist_ok=True)
                with open(agent_file, 'w') as f:
                    json.dump(agent, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to register agents: {e}")
            return False
    
    def create_subagent_definitions(self) -> List[Dict[str, Any]]:
        """Create subagent definitions for Claude Code's Task tool"""
        subagents = []
        
        for agent_id, agent in self.agents.items():
            # Get agent details
            agent_name = agent.get('role', agent_id.replace('_', ' ').title())
            agent_desc = agent.get('capabilities', [])
            if isinstance(agent_desc, list):
                agent_desc = agent_desc[0] if agent_desc else f"{agent_name} specialist"
            
            # Create a subagent definition that Claude Code can use
            subagent = {
                "type": "general-purpose",  # Use general-purpose type for all agents
                "id": f"coral-{agent_id.replace('_', '-')}",
                "name": f"Coral {agent_name}",
                "description": f"{agent_desc} (CoralCollective)",
                "prompt_template": self._get_full_agent_prompt(agent_id, "{task}"),
                "tools": ["*"]  # All tools available
            }
            subagents.append(subagent)
        
        return subagents
    
    def _get_full_agent_prompt(self, agent_id: str, task: str) -> str:
        """Get the full prompt for an agent"""
        if agent_id not in self.agents:
            return f"Unknown agent: {agent_id}"
        
        agent = self.agents[agent_id]
        prompt_path = self.base_path / agent.get('prompt_path', f'agents/specialists/{agent_id}.md')
        
        # Try alternate paths if primary doesn't exist
        if not prompt_path.exists():
            alt_paths = [
                self.base_path / f'agents/core/{agent_id}.md',
                self.base_path / f'agents/specialists/{agent_id}.md'
            ]
            for path in alt_paths:
                if path.exists():
                    prompt_path = path
                    break
        
        if not prompt_path.exists():
            return f"Agent prompt file not found: {prompt_path}"
        
        with open(prompt_path, 'r') as f:
            base_prompt = f.read()
        
        # Format the prompt with the task
        agent_name = agent.get('role', agent_id.replace('_', ' ').title())
        full_prompt = f"""# CoralCollective Agent: {agent_name}

{base_prompt}

## Current Task
{task}

## Instructions
Please complete the task above following the guidelines and best practices in your agent definition.
Use all available tools to accomplish the task effectively.
"""
        
        return full_prompt
    
    def get_task_invocation(self, agent_id: str, task: str) -> Dict[str, Any]:
        """Get the Task tool invocation for a CoralCollective agent"""
        agent = self.agents.get(agent_id, {})
        agent_name = agent.get('role', agent_id.replace('_', ' ').title())
        
        return {
            "subagent_type": "general-purpose",
            "description": f"Run Coral {agent_name}",
            "prompt": self._get_full_agent_prompt(agent_id, task)
        }


class ClaudeSubagentInterface:
    """Interface for Claude to use subagents directly"""
    
    def __init__(self):
        self.registry = SubagentRegistry()
    
    def __call__(self, invocation: str) -> Dict:
        """Allow Claude to invoke subagents with @ notation
        
        Examples:
            @backend_developer "Create REST API"
            @role/frontend_developer "Build React UI"
            @do/api "Design GraphQL schema"
            @category/security "Audit authentication"
        """
        
        # Parse invocation
        parts = invocation.split(' ', 1)
        if len(parts) < 2:
            return {'error': 'Invalid invocation. Use: @agent_id "task"'}
        
        agent_ref = parts[0]
        task = parts[1].strip('"\'')
        
        # Find agent by reference
        if agent_ref.startswith('@'):
            agent_id = self.registry.find_subagent_by_alias(agent_ref)
            if not agent_id:
                # Try direct ID
                agent_id = agent_ref.replace('@', '').replace('-', '_')
        else:
            agent_id = agent_ref
        
        # Invoke the subagent
        return self.registry.invoke_subagent(agent_id, task)
    
    def help(self, agent_id: str = None) -> str:
        """Get help for subagents"""
        if agent_id:
            return self.registry.get_subagent_help(agent_id.replace('@', ''))
        
        # General help
        categories = self.registry.list_subagents_by_category()
        help_text = "Available CoralCollective Subagents:\n\n"
        
        for category, agents in categories.items():
            help_text += f"{category.upper()}:\n"
            for agent in agents:
                help_text += f"  {agent['id']}: {agent['name']}\n"
            help_text += "\n"
        
        help_text += """
Usage Examples:
  @backend_developer "Create user authentication API"
  @project_architect "Design e-commerce platform"
  @qa_testing "Write unit tests for payment module"
  
Get help for specific agent:
  help('@backend_developer')
"""
        return help_text
    
    def workflow(self, workflow_type: str, task: str) -> List[Dict]:
        """Execute a complete workflow"""
        agent_ids = self.registry.get_workflow_subagents(workflow_type)
        chain = self.registry.create_subagent_chain(agent_ids)
        return chain(task)


# Global instance for Claude to use
coral_subagents = ClaudeSubagentInterface()


def main():
    """Command-line interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CoralCollective Subagent Registry')
    parser.add_argument('command', choices=['list', 'invoke', 'help', 'workflow', 'register'])
    parser.add_argument('--agent', help='Agent ID')
    parser.add_argument('--task', help='Task for the agent')
    parser.add_argument('--workflow', help='Workflow type')
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    
    registry = SubagentRegistry()
    
    if args.command == 'list':
        categories = registry.list_subagents_by_category()
        if args.json:
            print(json.dumps(categories, indent=2))
        else:
            for category, agents in categories.items():
                print(f"\n{category.upper()}:")
                for agent in agents:
                    print(f"  {agent['id']}: {agent['name']}")
    
    elif args.command == 'invoke':
        if not args.agent or not args.task:
            print("Error: --agent and --task required")
            sys.exit(1)
        result = registry.invoke_subagent(args.agent, args.task)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Status: {result['status']}")
            if result['status'] == 'success':
                print(f"Subagent: {result['name']}")
                print(f"Task: {result['task']}")
    
    elif args.command == 'help':
        if args.agent:
            print(registry.get_subagent_help(args.agent))
        else:
            interface = ClaudeSubagentInterface()
            print(interface.help())
    
    elif args.command == 'workflow':
        if not args.workflow or not args.task:
            print("Error: --workflow and --task required")
            sys.exit(1)
        interface = ClaudeSubagentInterface()
        results = interface.workflow(args.workflow, args.task)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            for i, result in enumerate(results):
                print(f"\nStep {i+1}: {result.get('name', 'Unknown')}")
                print(f"Status: {result.get('status', 'Unknown')}")
    
    elif args.command == 'register':
        success = registry.register_with_claude()
        if args.json:
            print(json.dumps({"success": success}, indent=2))
        elif success:
            print("✅ Successfully registered agents with Claude Code")
        else:
            print("❌ Failed to register agents")


if __name__ == '__main__':
    main()