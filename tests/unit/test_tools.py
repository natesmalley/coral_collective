"""
Unit tests for CoralCollective Utility Tools

Tests cover:
1. FeedbackCollector - Agent feedback and metrics tracking
2. ProjectStateManager - Project state and artifact management
"""

import pytest
import tempfile
import shutil
import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# Import the tools modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.feedback_collector import FeedbackCollector
from tools.project_state import ProjectStateManager


class TestFeedbackCollector:
    """Test FeedbackCollector functionality"""
    
    def setup_method(self):
        """Set up temporary directories for testing"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.feedback_path = self.temp_dir / "feedback" / "agent_feedback.yaml"
        self.metrics_path = self.temp_dir / "metrics" / "agent_metrics.yaml"
        
        self.collector = FeedbackCollector(
            feedback_path=str(self.feedback_path),
            metrics_path=str(self.metrics_path)
        )
    
    def teardown_method(self):
        """Clean up temporary directories"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_collector_initialization(self):
        """Test FeedbackCollector initialization"""
        
        assert self.collector.feedback_path == self.feedback_path
        assert self.collector.metrics_path == self.metrics_path
        
        # Check that directories are created
        assert self.feedback_path.parent.exists()
        assert self.metrics_path.parent.exists()
    
    def test_add_feedback_new_file(self):
        """Test adding feedback when file doesn't exist"""
        
        feedback_entry = self.collector.add_feedback(
            agent="backend_developer",
            issue="API response time is slow",
            suggestion="Implement caching for frequently accessed endpoints",
            priority="high",
            reported_by="qa_team"
        )
        
        # Check return value
        assert feedback_entry["issue"] == "API response time is slow"
        assert feedback_entry["priority"] == "high"
        assert feedback_entry["status"] == "pending"
        assert feedback_entry["reported_by"] == "qa_team"
        assert "date" in feedback_entry
        
        # Check file was created and data stored
        assert self.feedback_path.exists()
        
        with open(self.feedback_path, 'r') as f:
            data = yaml.safe_load(f)
            
        assert "agents" in data
        assert "backend_developer" in data["agents"]
        assert len(data["agents"]["backend_developer"]["feedback"]) == 1
        assert data["agents"]["backend_developer"]["feedback"][0]["issue"] == "API response time is slow"
    
    def test_record_interaction_new_file(self):
        """Test recording interaction when metrics file doesn't exist"""
        
        metrics = self.collector.record_interaction(
            agent="backend_developer",
            success=True,
            satisfaction=8,
            task_type="API Development",
            completion_time=45
        )
        
        # Check returned metrics
        assert metrics["total_uses"] == 1
        assert metrics["successful_tasks"] == 1
        assert metrics["success_rate"] == "100%"
        assert metrics["avg_satisfaction"] == 8
        assert metrics["total_completion_time"] == 45
        assert metrics["avg_completion_time"] == "45min"
        assert "tasks_completed" in metrics
        assert metrics["tasks_completed"]["api_development"] == 1
    
    def test_get_agent_feedback(self):
        """Test retrieving feedback for specific agent"""
        
        # Add feedback
        self.collector.add_feedback("test_agent", "Issue 1", "Suggestion 1")
        self.collector.add_feedback("test_agent", "Issue 2", "Suggestion 2", priority="high")
        self.collector.add_feedback("other_agent", "Other issue", "Other suggestion")
        
        # Get feedback for specific agent
        feedback = self.collector.get_agent_feedback("test_agent")
        
        assert len(feedback) == 2
        assert feedback[0]["issue"] == "Issue 1"
        assert feedback[1]["issue"] == "Issue 2"
        assert feedback[1]["priority"] == "high"
    
    def test_get_agent_metrics(self):
        """Test retrieving metrics for specific agent"""
        
        # Record interactions
        self.collector.record_interaction("test_agent", True, 8, "Testing", 30)
        self.collector.record_interaction("test_agent", True, 9, "Development", 45)
        
        # Get metrics
        metrics = self.collector.get_agent_metrics("test_agent")
        
        assert "current_month" in metrics
        current_metrics = metrics["current_month"]
        assert current_metrics["total_uses"] == 2
        assert current_metrics["success_rate"] == "100%"


class TestProjectStateManager:
    """Test ProjectStateManager functionality"""
    
    def setup_method(self):
        """Set up temporary project directory"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_path = self.temp_dir / "test_project"
        self.project_path.mkdir(parents=True)
        
        self.manager = ProjectStateManager(self.project_path)
    
    def teardown_method(self):
        """Clean up temporary directories"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_manager_initialization(self):
        """Test ProjectStateManager initialization"""
        
        assert self.manager.project_path == self.project_path
        assert self.manager.state_file == self.project_path / '.coral' / 'project_state.yaml'
        assert self.manager.state_file.parent.exists()
        
        # Check default state structure
        state = self.manager.state
        assert state["project"]["name"] == "test_project"
        assert "created_at" in state["project"]
        assert state["project"]["current_phase"] == "planning"
        assert state["project"]["status"] == "active"
        
        assert "agents" in state
        assert "completed" in state["agents"]
        assert "in_progress" in state["agents"]
        assert "pending" in state["agents"]
    
    def test_record_agent_start(self):
        """Test recording agent start"""
        
        context = {"task_type": "architecture", "priority": "high"}
        
        record = self.manager.record_agent_start(
            "project_architect",
            "Design system architecture",
            context
        )
        
        # Check return value
        assert record["agent_id"] == "project_architect"
        assert record["task"] == "Design system architecture"
        assert record["context"] == context
        assert "started_at" in record
        
        # Check state updates
        assert len(self.manager.state["agents"]["in_progress"]) == 1
        assert self.manager.state["agents"]["in_progress"][0]["agent_id"] == "project_architect"
    
    def test_record_agent_completion_success(self):
        """Test recording successful agent completion"""
        
        # Start agent first
        self.manager.record_agent_start("frontend_developer", "Create UI components")
        
        outputs = {"components": ["Header", "Footer", "Sidebar"]}
        artifacts = [
            {"type": "source_code", "path": "src/components/Header.tsx"},
            {"type": "source_code", "path": "src/components/Footer.tsx"}
        ]
        
        # Wait a small amount to have measurable duration
        import time
        time.sleep(0.01)
        
        completion = self.manager.record_agent_completion(
            "frontend_developer",
            success=True,
            outputs=outputs,
            artifacts=artifacts
        )
        
        # Check completion record
        assert completion["agent_id"] == "frontend_developer"
        assert completion["success"] is True
        assert completion["outputs"] == outputs
        assert completion["duration_minutes"] > 0
        assert "completed_at" in completion
        
        # Check state updates
        assert len(self.manager.state["agents"]["completed"]) == 1
        assert len(self.manager.state["agents"]["in_progress"]) == 0
        
        # Check metrics
        assert self.manager.state["metrics"]["total_agents_run"] == 1
        assert self.manager.state["metrics"]["success_rate"] == 1.0
        assert self.manager.state["metrics"]["total_time_minutes"] > 0
        
        # Check artifacts were added
        assert len(self.manager.state["artifacts"]) == 2
    
    def test_add_artifact(self):
        """Test adding artifacts"""
        
        metadata = {"lines_of_code": 250, "language": "TypeScript"}
        
        artifact = self.manager.add_artifact(
            artifact_type="source_code",
            path="src/services/api.ts",
            created_by="backend_developer",
            metadata=metadata
        )
        
        # Check return value
        assert artifact["type"] == "source_code"
        assert artifact["path"] == "src/services/api.ts"
        assert artifact["created_by"] == "backend_developer"
        assert artifact["metadata"] == metadata
        assert "id" in artifact
        assert "created_at" in artifact
        
        # Check state
        assert len(self.manager.state["artifacts"]) == 1
        assert self.manager.state["artifacts"][0]["path"] == "src/services/api.ts"
    
    def test_record_handoff(self):
        """Test recording agent handoff"""
        
        handoff_data = {
            "summary": "Architecture phase completed",
            "artifacts": ["architecture.md", "diagrams/"],
            "next_steps": ["Implement user authentication", "Set up database"],
            "blockers": [],
            "estimated_effort": "2 weeks"
        }
        
        handoff = self.manager.record_handoff(
            "project_architect",
            "backend_developer",
            handoff_data
        )
        
        # Check handoff record
        assert handoff["from_agent"] == "project_architect"
        assert handoff["to_agent"] == "backend_developer"
        assert handoff["data"] == handoff_data
        assert "timestamp" in handoff
        
        # Check state updates
        assert len(self.manager.state["handoffs"]) == 1
        assert len(self.manager.state["agents"]["pending"]) == 1
        assert self.manager.state["agents"]["pending"][0]["agent_id"] == "backend_developer"
    
    def test_get_summary(self):
        """Test getting project summary"""
        
        # Set up some state
        self.manager.record_agent_start("agent1", "Task 1")
        self.manager.record_agent_completion("agent1", True)
        
        self.manager.record_agent_start("agent2", "Task 2") # In progress
        
        self.manager.state["agents"]["pending"].append({"agent_id": "agent3"})
        
        self.manager.add_artifact("documentation", "doc1.md", "agent1")
        self.manager.add_artifact("source_code", "code1.py", "agent1")
        
        self.manager.set_phase("development")
        
        # Get summary
        summary = self.manager.get_summary()
        
        assert summary["project_name"] == "test_project"
        assert summary["current_phase"] == "development"
        assert summary["agents_completed"] == 1
        assert summary["agents_in_progress"] == 1
        assert summary["agents_pending"] == 1
        assert summary["total_artifacts"] == 2
        assert summary["success_rate"] == 1.0
        assert summary["total_time_minutes"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])