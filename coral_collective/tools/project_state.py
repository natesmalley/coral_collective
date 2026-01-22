"""
Project State Management

Handles project state persistence and context management for CoralCollective.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import yaml


@dataclass
class ProjectState:
    """Represents the state of a project."""

    project_id: str
    name: str
    phase: str
    status: str
    agents_completed: List[str]
    current_agent: Optional[str]
    context: Dict[str, Any]
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class ProjectStateManager:
    """Manages project state persistence and retrieval."""

    def __init__(self, state_dir: Optional[str] = None):
        """
        Initialize the project state manager.

        Args:
            state_dir: Directory to store state files. Defaults to .coral/states
        """
        if state_dir:
            self.state_dir = Path(state_dir)
        else:
            self.state_dir = Path.cwd() / ".coral" / "states"

        # Create state directory if it doesn't exist
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_file(self, project_id: str) -> Path:
        """Get the state file path for a project."""
        return self.state_dir / f"{project_id}_state.yaml"

    def save_state(self, project_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Save project state to file.

        Args:
            project_id: Unique identifier for the project
            state_data: Dictionary containing project state information

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add timestamps
            if "created_at" not in state_data:
                state_data["created_at"] = datetime.now().isoformat()
            state_data["updated_at"] = datetime.now().isoformat()

            # Ensure project_id is in state data
            state_data["project_id"] = project_id

            # Save to YAML file
            state_file = self._get_state_file(project_id)
            with open(state_file, "w") as f:
                yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)

            return True

        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def load_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load project state from file.

        Args:
            project_id: Unique identifier for the project

        Returns:
            Dictionary containing project state, or None if not found
        """
        try:
            state_file = self._get_state_file(project_id)

            if not state_file.exists():
                return None

            with open(state_file, "r") as f:
                state_data = yaml.safe_load(f)

            return state_data

        except Exception as e:
            print(f"Error loading state: {e}")
            return None

    def update_state(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing project state.

        Args:
            project_id: Unique identifier for the project
            updates: Dictionary of updates to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing state
            current_state = self.load_state(project_id)

            if not current_state:
                # If no existing state, create new one
                current_state = {"project_id": project_id}

            # Apply updates
            current_state.update(updates)

            # Save updated state
            return self.save_state(project_id, current_state)

        except Exception as e:
            print(f"Error updating state: {e}")
            return False

    def delete_state(self, project_id: str) -> bool:
        """
        Delete project state file.

        Args:
            project_id: Unique identifier for the project

        Returns:
            True if successful, False otherwise
        """
        try:
            state_file = self._get_state_file(project_id)

            if state_file.exists():
                state_file.unlink()

            return True

        except Exception as e:
            print(f"Error deleting state: {e}")
            return False

    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """
        Get accumulated context for a project.

        Args:
            project_id: Unique identifier for the project

        Returns:
            Dictionary containing project context
        """
        state = self.load_state(project_id)

        if not state:
            return {}

        return state.get("context", {})

    def clear_project_context(self, project_id: str) -> bool:
        """
        Clear all state for a project.

        Args:
            project_id: Unique identifier for the project

        Returns:
            True if successful, False otherwise
        """
        return self.delete_state(project_id)

    def list_states(self) -> List[str]:
        """
        List all saved project states.

        Returns:
            List of project IDs with saved states
        """
        try:
            state_files = self.state_dir.glob("*_state.yaml")
            project_ids = []

            for file in state_files:
                # Extract project ID from filename
                project_id = file.stem.replace("_state", "")
                project_ids.append(project_id)

            return project_ids

        except Exception as e:
            print(f"Error listing states: {e}")
            return []

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all project states.

        Returns:
            Dictionary mapping project IDs to their states
        """
        states = {}

        for project_id in self.list_states():
            state = self.load_state(project_id)
            if state:
                states[project_id] = state

        return states

    def export_state(self, project_id: str, format: str = "json") -> Optional[str]:
        """
        Export project state in specified format.

        Args:
            project_id: Unique identifier for the project
            format: Export format ('json' or 'yaml')

        Returns:
            Exported state as string, or None if not found
        """
        state = self.load_state(project_id)

        if not state:
            return None

        try:
            if format == "json":
                return json.dumps(state, indent=2, default=str)
            elif format == "yaml":
                return yaml.safe_dump(state, default_flow_style=False, sort_keys=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            print(f"Error exporting state: {e}")
            return None


# Convenience functions
def save_project_state(project_id: str, state_data: Dict[str, Any]) -> bool:
    """Save project state using default manager."""
    manager = ProjectStateManager()
    return manager.save_state(project_id, state_data)


def load_project_state(project_id: str) -> Optional[Dict[str, Any]]:
    """Load project state using default manager."""
    manager = ProjectStateManager()
    return manager.load_state(project_id)


def list_project_states() -> List[str]:
    """List all project states using default manager."""
    manager = ProjectStateManager()
    return manager.list_states()
