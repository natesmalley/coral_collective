#!/usr/bin/env python3
"""
CoralCollective Universal Installer
Deploy CoralCollective to any project directory with a single command
"""

import os
import sys
import shutil
import json
import yaml
from pathlib import Path
import argparse
import subprocess

class CoralInstaller:
    """Install CoralCollective in any project"""
    
    def __init__(self, source_dir=None):
        """Initialize installer
        
        Args:
            source_dir: Path to coral_collective source (auto-detected if None)
        """
        if source_dir:
            self.source_dir = Path(source_dir)
        else:
            # Auto-detect source directory (where this script lives)
            self.source_dir = Path(__file__).parent.resolve()
        
        if not self.source_dir.exists():
            raise ValueError(f"Source directory not found: {self.source_dir}")
        
        print(f"🪸 CoralCollective Installer v2.1.0")
        print(f"📁 Source: {self.source_dir}")
        print("=" * 50)
    
    def install(self, target_dir, mode='full'):
        """Install CoralCollective to target directory
        
        Args:
            target_dir: Where to install CoralCollective
            mode: Installation mode ('full', 'minimal', 'reference')
        """
        target_path = Path(target_dir).resolve()
        
        # Create target directory if it doesn't exist
        target_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📍 Installing to: {target_path}")
        print(f"📦 Mode: {mode}")
        
        if mode == 'full':
            self._install_full(target_path)
        elif mode == 'minimal':
            self._install_minimal(target_path)
        elif mode == 'reference':
            self._install_reference(target_path)
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
        print("\n✅ Installation complete!")
        self._print_usage(target_path, mode)
    
    def _install_full(self, target_path):
        """Full installation - copies all files to project"""
        print("\n📋 Full Installation - Copying all files...")
        
        # Create .coral directory
        coral_dir = target_path / '.coral'
        coral_dir.mkdir(exist_ok=True)
        
        # Files and directories to copy
        items_to_copy = [
            ('agents', coral_dir / 'agents'),
            ('config', coral_dir / 'config'),
            ('tools', coral_dir / 'tools'),
            ('templates', coral_dir / 'templates'),
            ('providers', coral_dir / 'providers'),
            ('agent_runner.py', coral_dir / 'agent_runner.py'),
            ('parallel_agent_runner.py', coral_dir / 'parallel_agent_runner.py'),
            ('project_manager.py', coral_dir / 'project_manager.py'),
            ('claude_interface.py', coral_dir / 'claude_interface.py'),
            ('subagent_registry.py', coral_dir / 'subagent_registry.py'),
            ('agent_prompt_service.py', coral_dir / 'agent_prompt_service.py'),
            ('claude_code_agents.json', coral_dir / 'claude_code_agents.json'),
            ('requirements.txt', coral_dir / 'requirements.txt'),
        ]
        
        for source_item, dest_item in items_to_copy:
            source_path = self.source_dir / source_item
            
            if source_path.exists():
                if source_path.is_dir():
                    if dest_item.exists():
                        shutil.rmtree(dest_item)
                    shutil.copytree(source_path, dest_item)
                    print(f"  ✓ Copied directory: {source_item}")
                else:
                    shutil.copy2(source_path, dest_item)
                    print(f"  ✓ Copied file: {source_item}")
            else:
                print(f"  ⚠ Skipped (not found): {source_item}")
        
        # Create wrapper script
        self._create_wrapper(target_path, 'full')
        
        # Create project files
        self._create_project_files(target_path)
        
        # Set up Python environment
        self._setup_environment(coral_dir)
    
    def _install_minimal(self, target_path):
        """Minimal installation - essential files only"""
        print("\n📋 Minimal Installation - Essential files only...")
        
        # Create .coral directory
        coral_dir = target_path / '.coral'
        coral_dir.mkdir(exist_ok=True)
        
        # Copy only essential files
        essential_files = [
            'agent_runner.py',
            'claude_code_agents.json',
            'claude_interface.py',
            'subagent_registry.py',
            'requirements.txt'
        ]
        
        for filename in essential_files:
            source_file = self.source_dir / filename
            dest_file = coral_dir / filename
            
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                print(f"  ✓ Copied: {filename}")
        
        # Copy agents directory (required)
        agents_src = self.source_dir / 'agents'
        agents_dst = coral_dir / 'agents'
        if agents_src.exists():
            if agents_dst.exists():
                shutil.rmtree(agents_dst)
            shutil.copytree(agents_src, agents_dst)
            print(f"  ✓ Copied agents directory")
        
        # Copy config directory
        config_src = self.source_dir / 'config'
        config_dst = coral_dir / 'config'
        if config_src.exists():
            if config_dst.exists():
                shutil.rmtree(config_dst)
            shutil.copytree(config_src, config_dst)
            print(f"  ✓ Copied config directory")
        
        # Create wrapper script
        self._create_wrapper(target_path, 'minimal')
        
        # Create project files
        self._create_project_files(target_path)
    
    def _install_reference(self, target_path):
        """Reference installation - links to source without copying"""
        print("\n📋 Reference Installation - Linking to source...")
        
        # Create .coral directory with config only
        coral_dir = target_path / '.coral'
        coral_dir.mkdir(exist_ok=True)
        
        # Create config pointing to source
        config = {
            'mode': 'reference',
            'source_path': str(self.source_dir),
            'version': '2.1.0',
            'features': {
                'parallel_execution': True,
                'non_interactive': True,
                'state_management': True,
                'scratchpad': True,
                'activity_tracker': True
            }
        }
        
        config_file = coral_dir / 'coral_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"  ✓ Created config: {config_file}")
        
        # Create wrapper script for reference mode
        self._create_wrapper(target_path, 'reference')
        
        # Create project files
        self._create_project_files(target_path)
    
    def _create_wrapper(self, target_path, mode):
        """Create the coral wrapper script"""
        
        if mode == 'reference':
            # Reference mode points to source
            wrapper_content = f'''#!/usr/bin/env python3
"""CoralCollective Wrapper - Reference Mode"""
import sys
import os
import json
from pathlib import Path

# Load configuration
config_file = Path(__file__).parent / '.coral' / 'coral_config.json'
with open(config_file) as f:
    config = json.load(f)

# Add source to path
source_path = config['source_path']
sys.path.insert(0, source_path)

# Set environment
os.environ['CORAL_PROJECT_DIR'] = str(Path(__file__).parent)
os.environ['CORAL_SOURCE_DIR'] = source_path

# Import and run
from agent_runner import AgentRunner

if __name__ == "__main__":
    runner = AgentRunner()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            runner.list_agents()
        elif sys.argv[1] == 'agent' and len(sys.argv) >= 4:
            runner.run_agent(sys.argv[2], ' '.join(sys.argv[3:]), non_interactive=True)
        elif sys.argv[1] == 'parallel':
            os.system(f'cd {{source_path}} && python3 parallel_agent_runner.py {{" ".join(sys.argv[2:])}}')
        else:
            print("Usage: coral [list|agent <id> <task>|parallel <type> <desc>]")
    else:
        runner.interactive_menu()
'''
        else:
            # Full/Minimal mode runs from local copy
            wrapper_content = f'''#!/usr/bin/env python3
"""CoralCollective Wrapper - {mode.title()} Mode"""
import sys
import os
from pathlib import Path

# Add .coral to path
coral_dir = Path(__file__).parent / '.coral'
sys.path.insert(0, str(coral_dir))

# Set environment
os.environ['CORAL_PROJECT_DIR'] = str(Path(__file__).parent)

# Import and run
try:
    from agent_runner import AgentRunner
    
    if __name__ == "__main__":
        runner = AgentRunner()
        
        if len(sys.argv) > 1:
            if sys.argv[1] == 'list':
                runner.list_agents()
            elif sys.argv[1] == 'agent' and len(sys.argv) >= 4:
                runner.run_agent(sys.argv[2], ' '.join(sys.argv[3:]), non_interactive=True)
            elif sys.argv[1] == 'parallel':
                from parallel_agent_runner import ParallelAgentRunner
                p_runner = ParallelAgentRunner()
                # Handle parallel execution
            else:
                print("Usage: coral [list|agent <id> <task>|parallel <type> <desc>]")
        else:
            runner.interactive_menu()
except ImportError as e:
    print(f"Error: Missing dependencies - {{e}}")
    print("Run: pip install -r .coral/requirements.txt")
'''
        
        # Write wrapper script
        wrapper_file = target_path / 'coral'
        with open(wrapper_file, 'w') as f:
            f.write(wrapper_content)
        
        # Make executable
        wrapper_file.chmod(0o755)
        print(f"  ✓ Created wrapper: {wrapper_file}")
    
    def _create_project_files(self, target_path):
        """Create scratchpad and activity_tracker files"""
        
        # Create scratchpad.md
        scratchpad = target_path / 'scratchpad.md'
        if not scratchpad.exists():
            with open(scratchpad, 'w') as f:
                f.write("""# Project Scratchpad

## Current Working Notes
- Project initialized with CoralCollective

## Questions & Blockers

## TODOs
- [ ] Define project requirements
- [ ] Choose tech stack

## Notes for Next Agent
- Ready for architecture planning
""")
            print(f"  ✓ Created: scratchpad.md")
        
        # Create activity_tracker.md
        tracker = target_path / 'activity_tracker.md'
        if not tracker.exists():
            with open(tracker, 'w') as f:
                f.write(f"""# Activity Tracker

## Activity Log

### [2025-01-15] Installation
**Task**: Install CoralCollective
**Status**: ✅ Completed
**Actions**:
1. Installed CoralCollective framework
2. Created project structure
3. Set up coordination files

**Notes for Next Agent**:
- Use `./coral` command to run agents
- Project ready for development
""")
            print(f"  ✓ Created: activity_tracker.md")
    
    def _setup_environment(self, coral_dir):
        """Set up Python environment"""
        print("\n🐍 Setting up Python environment...")
        
        # Create virtual environment
        venv_path = coral_dir / 'venv'
        if not venv_path.exists():
            try:
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], 
                             check=True, capture_output=True)
                print(f"  ✓ Created virtual environment")
            except subprocess.CalledProcessError:
                print(f"  ⚠ Could not create virtual environment")
        
        # Install requirements
        req_file = coral_dir / 'requirements.txt'
        if req_file.exists():
            pip_path = venv_path / 'bin' / 'pip' if os.name != 'nt' else venv_path / 'Scripts' / 'pip'
            if pip_path.exists():
                try:
                    subprocess.run([str(pip_path), 'install', '-r', str(req_file), '-q'], 
                                 check=True, capture_output=True)
                    print(f"  ✓ Installed dependencies")
                except subprocess.CalledProcessError:
                    print(f"  ⚠ Could not install all dependencies")
    
    def _print_usage(self, target_path, mode):
        """Print usage instructions"""
        print("\n" + "=" * 50)
        print("🎉 CoralCollective is ready!")
        print("=" * 50)
        print(f"\n📁 Project: {target_path}")
        print(f"📦 Installation: {mode}")
        print("\n🚀 Quick Start:")
        print(f"  cd {target_path}")
        print("  ./coral list              # List agents")
        print("  ./coral agent <id> <task> # Run agent")
        print("\n📚 Documentation:")
        print("  scratchpad.md     - Agent coordination")
        print("  activity_tracker.md - Activity log")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Install CoralCollective in any project')
    parser.add_argument('target', help='Target directory for installation')
    parser.add_argument('--mode', choices=['full', 'minimal', 'reference'],
                       default='minimal', help='Installation mode (default: minimal)')
    parser.add_argument('--source', help='Source directory (auto-detected if not specified)')
    
    args = parser.parse_args()
    
    try:
        installer = CoralInstaller(args.source)
        installer.install(args.target, args.mode)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()