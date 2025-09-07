#!/usr/bin/env python3
"""
Claude Interface for CoralCollective
This module provides direct integration points for Claude to interact with CoralCollective agents.
"""

import json
import sys
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agent_runner import AgentRunner
except ImportError:
    # Fallback for when rich is not installed
    class AgentRunner:
        def __init__(self):
            self.agents_config = self.load_config()
            self.base_path = Path(__file__).parent
            
        def load_config(self):
            config_path = Path(__file__).parent / "claude_code_agents.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            return {"agents": {}, "workflows": {}}


class ClaudeInterface:
    """Interface for Claude to interact with CoralCollective"""
    
    def __init__(self):
        """Initialize the Claude interface"""
        self.runner = AgentRunner()
        self.base_path = Path(__file__).parent
        self.config = self._load_config()
        
    def list_agents(self) -> Dict[str, Any]:
        """Return a structured list of all available agents"""
        agents = {}
        for agent_id, agent_info in self.runner.agents_config.get('agents', {}).items():
            agents[agent_id] = {
                'name': agent_info.get('name', agent_id),
                'category': agent_info.get('category', 'unknown'),
                'description': agent_info.get('description', ''),
                'capabilities': agent_info.get('capabilities', []),
                'prompt_path': agent_info.get('prompt_path', '')
            }
        return agents
    
    def get_agent_prompt(self, agent_id: str, task: str = "") -> Dict[str, str]:
        """Get the full prompt for a specific agent"""
        if agent_id not in self.runner.agents_config.get('agents', {}):
            return {
                'status': 'error',
                'message': f'Agent {agent_id} not found',
                'available_agents': list(self.runner.agents_config.get('agents', {}).keys())
            }
        
        agent = self.runner.agents_config['agents'][agent_id]
        prompt_path = self.base_path / agent.get('prompt_path', f'agents/specialists/{agent_id}.md')
        
        if not prompt_path.exists():
            # Try alternate paths
            alt_paths = [
                self.base_path / f'agents/core/{agent_id}.md',
                self.base_path / f'agents/specialists/{agent_id}.md',
                self.base_path / f'agents/{agent_id}.md'
            ]
            for alt_path in alt_paths:
                if alt_path.exists():
                    prompt_path = alt_path
                    break
        
        if not prompt_path.exists():
            return {
                'status': 'error',
                'message': f'Prompt file not found for {agent_id}',
                'tried_paths': [str(prompt_path)] + [str(p) for p in alt_paths]
            }
        
        with open(prompt_path, 'r') as f:
            prompt_content = f.read()
        
        # If task is provided, append it to the prompt
        if task:
            prompt_content += f"\n\n## Current Task\n{task}"
        
        return {
            'status': 'success',
            'agent_id': agent_id,
            'agent_name': agent.get('name', agent_id),
            'prompt': prompt_content,
            'task': task,
            'next_agents': self.get_recommended_next_agents(agent_id)
        }
    
    def get_recommended_next_agents(self, current_agent: str) -> List[str]:
        """Get recommended next agents based on current agent"""
        recommendations = {
            'project_architect': ['technical_writer_phase1', 'api_designer', 'database_specialist'],
            'technical_writer_phase1': ['backend_developer', 'frontend_developer', 'api_designer'],
            'backend_developer': ['frontend_developer', 'database_specialist', 'qa_testing'],
            'frontend_developer': ['qa_testing', 'accessibility_specialist', 'performance_engineer'],
            'api_designer': ['backend_developer', 'frontend_developer'],
            'database_specialist': ['backend_developer', 'data_engineer'],
            'qa_testing': ['devops_deployment', 'performance_engineer'],
            'devops_deployment': ['site_reliability_engineer', 'technical_writer_phase2'],
            'technical_writer_phase2': [],  # Final agent
        }
        return recommendations.get(current_agent, ['qa_testing', 'devops_deployment'])
    
    def get_workflow(self, workflow_type: str = 'full_stack_web') -> Dict[str, Any]:
        """Get a complete workflow sequence"""
        workflows = self.runner.agents_config.get('workflows', {})
        
        if workflow_type not in workflows:
            return {
                'status': 'error',
                'message': f'Workflow {workflow_type} not found',
                'available_workflows': list(workflows.keys())
            }
        
        workflow = workflows[workflow_type]
        return {
            'status': 'success',
            'workflow_type': workflow_type,
            'name': workflow.get('name', workflow_type),
            'description': workflow.get('description', ''),
            'phases': workflow.get('phases', []),
            'total_agents': sum(len(phase.get('agents', [])) for phase in workflow.get('phases', []))
        }
    
    def get_project_template(self, template_name: str = 'full_stack_web') -> Dict[str, Any]:
        """Get a project template with agent sequence"""
        templates = self.runner.agents_config.get('project_templates', {})
        
        if template_name not in templates:
            return {
                'status': 'error',
                'message': f'Template {template_name} not found',
                'available_templates': list(templates.keys())
            }
        
        template = templates[template_name]
        sequence = template.get('sequence', [])
        
        # Build detailed sequence with agent info
        detailed_sequence = []
        for agent_id in sequence:
            if agent_id in self.runner.agents_config.get('agents', {}):
                agent_info = self.runner.agents_config['agents'][agent_id]
                detailed_sequence.append({
                    'id': agent_id,
                    'name': agent_info.get('name', agent_id),
                    'category': agent_info.get('category', ''),
                    'description': agent_info.get('description', '')
                })
        
        return {
            'status': 'success',
            'template_name': template_name,
            'name': template.get('name', template_name),
            'description': template.get('description', ''),
            'sequence': detailed_sequence,
            'total_agents': len(detailed_sequence)
        }
    
    def execute_agent_sequence(self, agent_ids: List[str], task: str) -> List[Dict[str, Any]]:
        """Execute a sequence of agents with a given task"""
        results = []
        context = task
        
        for agent_id in agent_ids:
            result = self.get_agent_prompt(agent_id, context)
            results.append(result)
            
            # Update context for next agent (this is simplified)
            if result['status'] == 'success':
                context = f"Previous agent ({agent_id}) completed. Continue with: {task}"
        
        return results
    
    def get_agent_by_capability(self, capability: str) -> List[Dict[str, str]]:
        """Find agents with a specific capability"""
        matching_agents = []
        
        for agent_id, agent_info in self.runner.agents_config.get('agents', {}).items():
            capabilities = agent_info.get('capabilities', [])
            if capability.lower() in [cap.lower() for cap in capabilities]:
                matching_agents.append({
                    'id': agent_id,
                    'name': agent_info.get('name', agent_id),
                    'category': agent_info.get('category', ''),
                    'description': agent_info.get('description', ''),
                    'all_capabilities': capabilities
                })
        
        return matching_agents
    
    def get_category_agents(self, category: str) -> List[Dict[str, str]]:
        """Get all agents in a specific category"""
        category_agents = []
        
        for agent_id, agent_info in self.runner.agents_config.get('agents', {}).items():
            if agent_info.get('category', '').lower() == category.lower():
                category_agents.append({
                    'id': agent_id,
                    'name': agent_info.get('name', agent_id),
                    'description': agent_info.get('description', ''),
                    'capabilities': agent_info.get('capabilities', [])
                })
        
        return category_agents
    
    def _load_config(self) -> Dict:
        """Load agent configurations from YAML"""
        config_file = self.base_path / "config" / "agents.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return {'agents': {}}
    
    def create_claude_code_agents(self) -> bool:
        """Create agent definitions for Claude Code discovery"""
        agents = []
        
        # Core agents that appear in Claude Code's /agents
        core_agents = {
            'project_architect': {
                'name': 'CoralCollective Architect',
                'description': 'System design and architecture planning specialist with 20+ years experience',
                'type': 'general-purpose',
                'category': 'Architecture & Design'
            },
            'backend_developer': {
                'name': 'CoralCollective Backend',
                'description': 'Server-side development specialist with API design and database expertise',
                'type': 'general-purpose', 
                'category': 'Development'
            },
            'frontend_developer': {
                'name': 'CoralCollective Frontend',
                'description': 'UI/UX implementation specialist with modern framework expertise',
                'type': 'general-purpose',
                'category': 'Development'
            },
            'full_stack_engineer': {
                'name': 'CoralCollective FullStack',
                'description': 'End-to-end development specialist handling both frontend and backend',
                'type': 'general-purpose',
                'category': 'Development'
            },
            'qa_testing': {
                'name': 'CoralCollective QA',
                'description': 'Quality assurance specialist with comprehensive testing strategies',
                'type': 'general-purpose',
                'category': 'Quality & Testing'
            },
            'devops_deployment': {
                'name': 'CoralCollective DevOps',
                'description': 'Infrastructure and deployment specialist with CI/CD expertise',
                'type': 'general-purpose',
                'category': 'DevOps & Infrastructure'
            },
            'security_specialist': {
                'name': 'CoralCollective Security',
                'description': 'Application security specialist focused on defensive measures',
                'type': 'general-purpose',
                'category': 'Security & Compliance'
            },
            'database_specialist': {
                'name': 'CoralCollective Database',
                'description': 'Database design and optimization specialist',
                'type': 'general-purpose',
                'category': 'Data & Storage'
            },
            'ai_ml_specialist': {
                'name': 'CoralCollective AI/ML',
                'description': 'AI integration and machine learning implementation specialist',
                'type': 'general-purpose',
                'category': 'AI & Machine Learning'
            }
        }
        
        for agent_id, agent_info in core_agents.items():
            if agent_id in self.config.get('agents', {}):
                agent_config = self.config['agents'][agent_id]
                
                # Read the agent prompt
                prompt_path = self.base_path / agent_config['prompt_path']
                agent_prompt = ""
                if prompt_path.exists():
                    with open(prompt_path, 'r') as f:
                        agent_prompt = f.read()
                
                # Create the agent definition for Claude Code
                agent_def = {
                    "name": agent_info['name'],
                    "description": agent_info['description'],
                    "type": agent_info['type'],
                    "category": agent_info['category'],
                    "instructions": f"""You are a {agent_config.get('role', agent_id)} from CoralCollective, the AI development team framework.

{agent_prompt}

## CoralCollective Context
You are part of a 20+ agent development team. Follow CoralCollective's structured approach:
1. Always provide clear deliverables and next steps
2. Create handoff summaries for other agents
3. Use appropriate tools for file operations and code execution
4. Focus on your specialized expertise while being collaborative

## Available Tools
You have access to all Claude Code tools including Read, Write, Edit, Bash, Grep, Glob, LS, Task, and more.""",
                    "tools": ["*"]
                }
                
                agents.append(agent_def)
        
        # Save agent definitions in format Claude Code expects
        agents_file = self.base_path / "coral_agents_claude_code.json"
        with open(agents_file, 'w') as f:
            json.dump({
                "version": "1.0",
                "provider": "CoralCollective",
                "agents": agents
            }, f, indent=2)
        
        print(f"✅ Created {len(agents)} CoralCollective agents for Claude Code")
        print(f"📄 Agent definitions saved to: {agents_file}")
        
        # Also create individual agent files that Claude Code might look for
        agents_dir = self.base_path / "agents_claude_code"
        agents_dir.mkdir(exist_ok=True)
        
        for i, agent in enumerate(agents):
            agent_file = agents_dir / f"coral_agent_{i+1}.json"
            with open(agent_file, 'w') as f:
                json.dump(agent, f, indent=2)
        
        print(f"📁 Individual agent files created in: {agents_dir}")
        
        return True
    
    def create_claude_agent_files(self) -> bool:
        """Create CoralCollective agents as Markdown files for Claude Code discovery"""
        
        # Create both user-level and project-level agent directories
        user_claude_dir = Path.home() / ".claude"
        user_agents_dir = user_claude_dir / "agents"
        user_agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Project-level agents (takes precedence)
        project_claude_dir = Path.cwd() / ".claude"
        project_agents_dir = project_claude_dir / "agents"
        project_agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Core agents to create
        core_agents = {
            'project_architect': {
                'name': 'CoralCollective Architect',
                'description': 'System design and architecture planning specialist for creating technical specifications and project structure'
            },
            'backend_developer': {
                'name': 'CoralCollective Backend',
                'description': 'Server-side development specialist for building APIs, databases, and backend services'
            },
            'frontend_developer': {
                'name': 'CoralCollective Frontend', 
                'description': 'UI/UX implementation specialist for building responsive web interfaces'
            },
            'full_stack_engineer': {
                'name': 'CoralCollective FullStack',
                'description': 'End-to-end development specialist for complete application development'
            },
            'qa_testing': {
                'name': 'CoralCollective QA',
                'description': 'Quality assurance specialist for comprehensive testing strategies'
            },
            'devops_deployment': {
                'name': 'CoralCollective DevOps',
                'description': 'Infrastructure and deployment specialist for CI/CD and production systems'
            },
            'security_specialist': {
                'name': 'CoralCollective Security',
                'description': 'Application security specialist focused on defensive security measures'
            },
            'database_specialist': {
                'name': 'CoralCollective Database',
                'description': 'Database design and optimization specialist'
            },
            'ai_ml_specialist': {
                'name': 'CoralCollective AI/ML',
                'description': 'AI integration and machine learning implementation specialist'
            }
        }
        
        created_count = 0
        
        for agent_id, agent_info in core_agents.items():
            if agent_id in self.config.get('agents', {}):
                agent_config = self.config['agents'][agent_id]
                
                # Read the agent prompt
                prompt_path = self.base_path / agent_config['prompt_path']
                agent_prompt = ""
                if prompt_path.exists():
                    with open(prompt_path, 'r') as f:
                        agent_prompt = f.read()
                
                # Create the Markdown agent file
                agent_content = f"""---
name: {agent_info['name']}
description: {agent_info['description']}
---

# {agent_info['name']}

You are a {agent_config.get('role', agent_id)} from **CoralCollective**, the AI development team framework with 20+ specialized agents.

{agent_prompt}

## CoralCollective Integration

You are part of a structured development team. Your role includes:

1. **Follow CoralCollective Workflow**: Use the established documentation patterns and handoff protocols
2. **Structured Deliverables**: Always provide clear completion summaries and next steps
3. **Agent Handoffs**: Recommend the next specialist agent and provide context for them
4. **Documentation Standards**: Follow the project's established folder structure and documentation patterns
5. **Collaborative Approach**: Build on work from previous agents and set up the next agent for success

## Key Capabilities

- Access to all Claude Code tools for file operations, terminal commands, and project management
- Deep understanding of modern development practices and frameworks
- Integration with project architecture and established patterns
- Clear communication and detailed documentation
- Handoff protocols for seamless team collaboration

## Project Structure Compliance

Always follow the established folder structure:
- Documentation goes in `/docs/` with proper organization
- Source code follows established patterns in `/src/`
- Tests are properly organized in `/tests/`
- Configuration files are correctly placed
- README.md files explain each directory's purpose

## Next Steps Protocol

After completing your work, always provide:
1. **Completion Summary**: What you delivered
2. **Next Agent Recommendation**: Which CoralCollective agent should work next
3. **Context Handoff**: Essential information for the next agent
4. **Integration Notes**: How your work connects to the broader system

Use your specialized expertise while maintaining the collaborative CoralCollective approach for optimal development results."""
                
                # Write the agent file to both locations
                agent_filename = f"{agent_id.replace('_', '-')}.md"
                
                # User-level agent
                user_agent_file = user_agents_dir / agent_filename
                with open(user_agent_file, 'w') as f:
                    f.write(agent_content)
                
                # Project-level agent (takes precedence)
                project_agent_file = project_agents_dir / agent_filename
                with open(project_agent_file, 'w') as f:
                    f.write(agent_content)
                
                created_count += 1
                print(f"✅ Created {agent_info['name']}")
        
        print(f"\n🎉 Successfully created {created_count} CoralCollective agents!")
        print(f"📍 User-level: {user_agents_dir}")
        print(f"📍 Project-level: {project_agents_dir}")
        print(f"\n🚀 How to use:")
        print("1. Type /agents in Claude Code")
        print("2. Look for CoralCollective agents in the list")
        print("3. Select any CoralCollective agent to use specialized expertise")
        print("\n💡 CoralCollective agents provide structured development workflows")
        print("   with clear handoffs between specialists for complete project delivery.")
        
        return True
    
    def register_agents_with_claude(self) -> bool:
        """Register CoralCollective agents with Claude's ~/.config/claude/agents directory"""
        
        # Define all CoralCollective agents with proper format
        agents = {
            "coral-architect": {
                "name": "Coral Architect",
                "description": "System design and architecture planning specialist from CoralCollective",
                "instructions": "You are the Project Architect from CoralCollective. Focus on system design, architecture planning, and creating technical blueprints.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-backend": {
                "name": "Coral Backend Developer",
                "description": "Server-side and database specialist from CoralCollective",
                "instructions": "You are the Backend Developer from CoralCollective. Build scalable APIs, implement authentication, and manage databases.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-frontend": {
                "name": "Coral Frontend Developer",
                "description": "UI/UX implementation specialist from CoralCollective",
                "instructions": "You are the Frontend Developer from CoralCollective. Create responsive UIs, implement user interactions, and ensure accessibility.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-fullstack": {
                "name": "Coral Full Stack Engineer",
                "description": "End-to-end development specialist from CoralCollective",
                "instructions": "You are the Full Stack Engineer from CoralCollective. Handle both frontend and backend development with a holistic approach.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-qa": {
                "name": "Coral QA Testing",
                "description": "Quality assurance and testing specialist from CoralCollective",
                "instructions": "You are the QA Testing specialist from CoralCollective. Write comprehensive tests, ensure code quality, and validate functionality.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-devops": {
                "name": "Coral DevOps",
                "description": "Infrastructure and deployment specialist from CoralCollective",
                "instructions": "You are the DevOps specialist from CoralCollective. Handle CI/CD, deployment, monitoring, and infrastructure.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-security": {
                "name": "Coral Security",
                "description": "Application security specialist from CoralCollective",
                "instructions": "You are the Security Specialist from CoralCollective. Audit code for vulnerabilities, implement security best practices.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-ai": {
                "name": "Coral AI/ML",
                "description": "AI and machine learning specialist from CoralCollective",
                "instructions": "You are the AI/ML Specialist from CoralCollective. Integrate AI features, implement ML models, and optimize performance.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-database": {
                "name": "Coral Database",
                "description": "Database design specialist from CoralCollective",
                "instructions": "You are the Database Specialist from CoralCollective. Design schemas, optimize queries, and manage data migrations.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            },
            "coral-api": {
                "name": "Coral API Designer",
                "description": "API design specialist from CoralCollective",
                "instructions": "You are the API Designer from CoralCollective. Design RESTful and GraphQL APIs with clear contracts.",
                "tools": ["*"],
                "model": "claude-3-5-sonnet-20241022"
            }
        }
        
        # Create agents directory if it doesn't exist
        agents_dir = Path.home() / ".config" / "claude" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        # Write each agent definition
        for agent_id, agent_config in agents.items():
            agent_file = agents_dir / f"{agent_id}.json"
            with open(agent_file, 'w') as f:
                json.dump(agent_config, f, indent=2)
            print(f"✅ Registered {agent_config['name']} at {agent_file}")
        
        print(f"\n✨ Successfully registered {len(agents)} CoralCollective agents!")
        print("\nTo use them in Claude:")
        print("1. Type /agents to see the list")
        print("2. Select any Coral agent")
        print("3. The agent will use CoralCollective's specialized expertise")
        
        return True
    
    def install_for_claude_code(self) -> bool:
        """Install CoralCollective agents for Claude Code discovery"""
        
        print("🪸 Installing CoralCollective Agents for Claude Code")
        print("=" * 55)
        
        if self.create_claude_code_agents():
            print("\n✅ Installation successful!")
            print("\n🚀 Next steps:")
            print("1. Restart Claude Code if it's running")
            print("2. Run /agents command to see CoralCollective agents")
            print("3. Select any CoralCollective agent to use specialized expertise")
            print("\n💡 CoralCollective agents provide:")
            print("  • Specialized domain expertise")
            print("  • Structured development workflows") 
            print("  • Clear handoff protocols between agents")
            print("  • Integration with MCP tools and services")
            
            return True
        else:
            print("\n❌ Installation failed")
            return False


def main():
    """Main entry point for command-line usage"""
    parser = argparse.ArgumentParser(description='Claude Interface for CoralCollective')
    parser.add_argument('command', choices=['list', 'get-prompt', 'workflow', 'template', 'capability', 'category', 'install-claude-code', 'install-markdown', 'register-claude'],
                        help='Command to execute')
    parser.add_argument('--agent', help='Agent ID for get-prompt command')
    parser.add_argument('--task', help='Task description for the agent')
    parser.add_argument('--workflow', default='full_stack_web', help='Workflow type')
    parser.add_argument('--template', default='full_stack_web', help='Project template')
    parser.add_argument('--capability', help='Capability to search for')
    parser.add_argument('--category', help='Category to list agents from')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    interface = ClaudeInterface()
    
    result = None
    
    if args.command == 'list':
        result = interface.list_agents()
    elif args.command == 'get-prompt':
        if not args.agent:
            print("Error: --agent is required for get-prompt command")
            sys.exit(1)
        result = interface.get_agent_prompt(args.agent, args.task or "")
    elif args.command == 'workflow':
        result = interface.get_workflow(args.workflow)
    elif args.command == 'template':
        result = interface.get_project_template(args.template)
    elif args.command == 'capability':
        if not args.capability:
            print("Error: --capability is required for capability command")
            sys.exit(1)
        result = interface.get_agent_by_capability(args.capability)
    elif args.command == 'category':
        if not args.category:
            print("Error: --category is required for category command")
            sys.exit(1)
        result = interface.get_category_agents(args.category)
    elif args.command == 'install-claude-code':
        result = {"success": interface.install_for_claude_code()}
    elif args.command == 'install-markdown':
        result = {"success": interface.create_claude_agent_files()}
    elif args.command == 'register-claude':
        result = {"success": interface.register_agents_with_claude()}
    
    if result:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            # Pretty print for human reading
            if isinstance(result, dict):
                for key, value in result.items():
                    if key == 'prompt':
                        print(f"\n=== PROMPT ===\n{value}\n")
                    else:
                        print(f"{key}: {value}")
            elif isinstance(result, list):
                for item in result:
                    print(f"- {item}")
            else:
                print(result)


if __name__ == '__main__':
    main()