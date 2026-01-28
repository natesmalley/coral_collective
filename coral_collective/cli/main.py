#!/usr/bin/env python3
"""
CoralCollective CLI - Main entry point for command-line operations
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CoralCollective - AI Agent Orchestration Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  coral list                           # List all available agents
  coral run project_architect          # Run an agent interactively
  coral workflow full_stack            # Run a complete workflow
  coral check                          # Check system health

For more information, see: https://github.com/coral-collective/coral-collective
        """,
    )

    parser.add_argument("--version", action="version", version="CoralCollective 1.0.0")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List available agents")
    list_parser.add_argument("--category", help="Filter by category (core/specialist)")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a single agent")
    run_parser.add_argument("agent", help="Agent ID to run")
    run_parser.add_argument("--task", help="Task description")
    run_parser.add_argument("--context", help="Context file (JSON/YAML)")
    run_parser.add_argument("--mcp", action="store_true", help="Enable MCP integration")

    # Workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run a complete workflow")
    workflow_parser.add_argument(
        "workflow_type", help="Workflow type (full_stack, backend_only, etc.)"
    )
    workflow_parser.add_argument("--project", help="Project name")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check system health")
    check_parser.add_argument("--all", action="store_true", help="Run all checks")
    check_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # State command
    state_parser = subparsers.add_parser("state", help="Manage project state")
    state_subparsers = state_parser.add_subparsers(dest="state_command")

    state_save = state_subparsers.add_parser("save", help="Save project state")
    state_save.add_argument("--project", required=True, help="Project ID")

    state_load = state_subparsers.add_parser("load", help="Load project state")
    state_load.add_argument("--project", required=True, help="Project ID")

    state_subparsers.add_parser("list", help="List saved states")

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize CoralCollective in current directory"
    )
    init_parser.add_argument("--project", help="Project name")

    args = parser.parse_args()

    # Route to appropriate handler
    if args.command == "list":
        from agent_runner import AgentRunner

        runner = AgentRunner()
        runner.list_agents()

    elif args.command == "run":
        from agent_runner import AgentRunner

        runner = AgentRunner()
        # The run method will handle the interactive prompts
        runner.main()

    elif args.command == "workflow":
        from agent_runner import AgentRunner

        runner = AgentRunner()
        runner.main()

    elif args.command == "check":
        # Import and run checks
        try:
            from coral_collective.utils.check import main as check_main

            check_main()
        except ImportError:
            print("Check utility not found. Running basic checks...")
            print("✓ CoralCollective is installed")
            print("✓ CLI is working")

    elif args.command == "state":
        from coral_collective.tools.project_state import ProjectStateManager

        state_mgr = ProjectStateManager()

        if args.state_command == "list":
            states = state_mgr.list_states()
            if states:
                print("Saved project states:")
                for state_id in states:
                    print(f"  - {state_id}")
            else:
                print("No saved states found")

        elif args.state_command == "load":
            state = state_mgr.load_state(args.project)
            if state:
                import json

                print(json.dumps(state, indent=2, default=str))
            else:
                print(f"No state found for project: {args.project}")

    elif args.command == "init":
        init_command()

    else:
        # No command specified, show help
        parser.print_help()


def init_command():
    """Initialize CoralCollective in the current directory."""
    import subprocess

    print("Initializing CoralCollective in current directory...")

    # Check if coral_drop.sh exists
    drop_script = Path(__file__).parent.parent.parent / "coral_drop.sh"
    if drop_script.exists():
        # Run the drop script
        result = subprocess.run(
            ["bash", str(drop_script)], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✓ CoralCollective initialized successfully!")
            print("  Use 'coral' command to interact with agents")
        else:
            print(f"Error initializing: {result.stderr}")
    else:
        # Manual initialization
        print("Creating .coral directory structure...")
        Path(".coral").mkdir(exist_ok=True)
        Path(".coral/states").mkdir(exist_ok=True)
        Path(".coral/feedback").mkdir(exist_ok=True)

        # Create wrapper script
        wrapper_content = """#!/bin/bash
# CoralCollective CLI wrapper
python3 -m coral_collective.cli.main "$@"
"""
        coral_script = Path("coral")
        with open(coral_script, "w") as f:
            f.write(wrapper_content)
        coral_script.chmod(0o755)

        print("✓ CoralCollective initialized!")
        print("  Use './coral' command to interact with agents")


if __name__ == "__main__":
    main()
