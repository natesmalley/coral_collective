"""
Test fixtures and data providers for CoralCollective testing

Provides reusable test data, mock objects, and fixtures for:
- Agent configurations
- Project states
- Memory items
- MCP responses
- CLI interactions
"""

import pytest
import tempfile
import shutil
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, MagicMock
from dataclasses import dataclass


@dataclass
class MockAgentConfig:
    """Mock agent configuration for testing"""
    agent_id: str
    role: str
    prompt_path: str
    capabilities: List[str]
    phase: Optional[int] = None


@pytest.fixture
def temp_project_dir():
    """Create temporary project directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_agents_config():
    """Sample agents configuration for testing"""
    return {
        "version": 1,
        "agents": {
            "project_architect": {
                "role": "architect",
                "prompt_path": "agents/core/project_architect.md",
                "capabilities": ["planning", "architecture", "structure", "handoff"]
            },
            "backend_developer": {
                "role": "backend_developer",
                "prompt_path": "agents/specialists/backend_developer.md",
                "capabilities": ["api", "database", "server", "authentication"]
            },
            "frontend_developer": {
                "role": "frontend_developer", 
                "prompt_path": "agents/specialists/frontend_developer.md",
                "capabilities": ["ui", "components", "styling", "state"]
            },
            "qa_testing": {
                "role": "qa_testing",
                "prompt_path": "agents/specialists/qa_testing.md",
                "capabilities": ["testing", "validation", "quality", "automation"]
            },
            "technical_writer_phase1": {
                "role": "technical_writer",
                "phase": 1,
                "prompt_path": "agents/core/technical_writer.md",
                "capabilities": ["requirements", "api_specs", "acceptance_criteria"]
            }
        }
    }


@pytest.fixture
def mock_project_state():
    """Sample project state for testing"""
    return {
        "project": {
            "name": "test_project",
            "id": "test_project_123",
            "created_at": datetime.now().isoformat(),
            "current_phase": "development",
            "status": "active"
        },
        "agents": {
            "completed": [
                {
                    "agent_id": "project_architect",
                    "task": "Design system architecture",
                    "success": True,
                    "started_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "completed_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "duration_minutes": 60,
                    "outputs": {
                        "architecture_doc": "/docs/architecture.md",
                        "requirements": "/docs/requirements.md"
                    }
                },
                {
                    "agent_id": "backend_developer",
                    "task": "Create REST API",
                    "success": True,
                    "started_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "completed_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
                    "duration_minutes": 30,
                    "outputs": {
                        "api_files": ["src/api/routes.py", "src/api/models.py"],
                        "tests": ["tests/test_api.py"]
                    }
                }
            ],
            "active": {
                "agent_id": "frontend_developer",
                "task": "Build user interface",
                "started_at": (datetime.now() - timedelta(minutes=15)).isoformat()
            },
            "queue": ["qa_testing", "devops_deployment"]
        },
        "handoffs": [
            {
                "id": "handoff_001",
                "from_agent": "project_architect",
                "to_agent": "backend_developer",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "data": {
                    "summary": "Architecture complete, ready for backend implementation",
                    "artifacts": ["/docs/architecture.md", "/docs/api_spec.yaml"],
                    "next_steps": ["Implement REST API", "Set up database schema"]
                }
            },
            {
                "id": "handoff_002", 
                "from_agent": "backend_developer",
                "to_agent": "frontend_developer",
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "data": {
                    "summary": "Backend API complete, ready for frontend integration",
                    "artifacts": ["src/api/", "docs/api_documentation.md"],
                    "next_steps": ["Create UI components", "Integrate with API endpoints"]
                }
            }
        ],
        "artifacts": [
            {
                "id": "artifact_001",
                "type": "documentation",
                "path": "/docs/architecture.md",
                "created_by": "project_architect",
                "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                "metadata": {
                    "format": "markdown",
                    "size_bytes": 2048,
                    "checksum": "abc123"
                }
            },
            {
                "id": "artifact_002",
                "type": "code",
                "path": "/src/api/routes.py",
                "created_by": "backend_developer", 
                "created_at": (datetime.now() - timedelta(minutes=45)).isoformat(),
                "metadata": {
                    "language": "python",
                    "lines": 150,
                    "functions": 8
                }
            }
        ],
        "metrics": {
            "total_agents_run": 2,
            "successful_completions": 2,
            "failed_completions": 0,
            "total_handoffs": 2,
            "artifacts_created": 2,
            "estimated_completion": "85%"
        }
    }


@pytest.fixture
def sample_memory_items():
    """Sample memory items for memory system testing"""
    try:
        # Import memory components if available
        from memory.memory_system import MemoryItem, MemoryType, ImportanceLevel
        
        return [
            MemoryItem(
                id="memory_001",
                content="Project architecture designed with microservices pattern",
                memory_type=MemoryType.SEMANTIC,
                timestamp=datetime.now() - timedelta(hours=2),
                agent_id="project_architect",
                project_id="test_project",
                importance=ImportanceLevel.HIGH,
                context={"type": "architecture", "pattern": "microservices"},
                tags=["architecture", "design", "microservices"]
            ),
            MemoryItem(
                id="memory_002",
                content="REST API endpoints created for user management",
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now() - timedelta(hours=1),
                agent_id="backend_developer",
                project_id="test_project",
                importance=ImportanceLevel.MEDIUM,
                context={"type": "implementation", "component": "api"},
                tags=["api", "backend", "users"]
            ),
            MemoryItem(
                id="memory_003",
                content="Agent handoff: Backend → Frontend with API specification",
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now() - timedelta(minutes=30),
                agent_id="system",
                project_id="test_project",
                importance=ImportanceLevel.HIGH,
                context={
                    "type": "handoff",
                    "from_agent": "backend_developer",
                    "to_agent": "frontend_developer",
                    "agent_handoff": True
                },
                tags=["handoff", "backend", "frontend"]
            )
        ]
    except ImportError:
        # Return mock data if memory system not available
        return []


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing MCP integration"""
    client = Mock()
    client.is_connected = True
    client.list_tools = AsyncMock(return_value=[
        {"name": "filesystem_read", "description": "Read files"},
        {"name": "filesystem_write", "description": "Write files"},
        {"name": "github_create_repo", "description": "Create GitHub repository"}
    ])
    client.call_tool = AsyncMock(return_value={
        "success": True,
        "result": "Mock tool execution result"
    })
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_cli_args():
    """Mock command-line arguments for testing CLI interfaces"""
    return {
        "run": Mock(
            command="run",
            agent_id="backend_developer",
            task="Create REST API",
            project_id=None,
            mcp_enabled=False,
            streaming=True,
            model=None,
            validate_tokens=False
        ),
        "workflow": Mock(
            command="workflow", 
            workflow_type="full_stack",
            task="Build web application",
            mcp_enabled=True,
            streaming=False
        ),
        "list": Mock(
            command="list",
            filter_role=None,
            filter_capabilities=None,
            show_paths=False
        ),
        "dashboard": Mock(
            command="dashboard",
            project_id="test_project",
            refresh_interval=5
        )
    }


@pytest.fixture
def agent_prompt_samples():
    """Sample agent prompts for testing"""
    return {
        "project_architect": """
# Project Architect Agent

You are a Senior Project Architect AI agent specializing in system design and project planning.

## Your Role
Design comprehensive project architectures and create development roadmaps.

## Key Responsibilities
- Analyze requirements and constraints
- Design system architecture 
- Create project structure and phases
- Generate technical specifications
- Plan agent workflows and handoffs

## Deliverables
- Architecture documentation
- Project roadmap
- Technical requirements
- Agent workflow plan
""",
        "backend_developer": """
# Backend Developer Agent

You are a Senior Backend Developer AI agent specializing in server-side development.

## Your Role
Develop robust backend systems, APIs, and database solutions.

## Key Responsibilities
- Design and implement REST APIs
- Create database schemas and queries
- Implement authentication and authorization
- Set up server infrastructure
- Write backend tests

## Deliverables
- API implementations
- Database schemas
- Authentication systems
- Backend tests
- API documentation
"""
    }


@pytest.fixture
def mock_feedback_data():
    """Mock feedback data for testing feedback system"""
    return {
        "sessions": [
            {
                "session_id": "session_001",
                "timestamp": datetime.now() - timedelta(hours=2),
                "agent_id": "backend_developer",
                "task": "Create REST API",
                "success": True,
                "duration_minutes": 45,
                "feedback": {
                    "rating": 4,
                    "comments": "Good API structure, clear documentation",
                    "suggestions": ["Add more error handling", "Include rate limiting"]
                }
            },
            {
                "session_id": "session_002",
                "timestamp": datetime.now() - timedelta(hours=1),
                "agent_id": "frontend_developer",
                "task": "Build UI components",
                "success": True,
                "duration_minutes": 30,
                "feedback": {
                    "rating": 5,
                    "comments": "Excellent component design and styling",
                    "suggestions": ["Add accessibility features"]
                }
            }
        ],
        "analytics": {
            "total_sessions": 2,
            "average_rating": 4.5,
            "success_rate": 100,
            "common_issues": [],
            "improvement_areas": ["error_handling", "accessibility"]
        }
    }


@pytest.fixture 
def virtual_env_setup():
    """Ensure tests run in proper virtual environment"""
    import sys
    import os
    
    # Check if we're in a virtual environment
    in_venv = (
        hasattr(sys, 'real_prefix') or  # virtualenv
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or  # venv
        'VIRTUAL_ENV' in os.environ  # explicit environment variable
    )
    
    if not in_venv:
        pytest.skip("Tests require virtual environment")
    
    return {
        "venv_path": os.environ.get('VIRTUAL_ENV', sys.prefix),
        "python_path": sys.executable,
        "site_packages": [p for p in sys.path if 'site-packages' in p]
    }


@pytest.fixture
def performance_thresholds():
    """Performance testing thresholds"""
    return {
        "agent_load_time_ms": 500,      # Max time to load agent prompt
        "memory_add_time_ms": 100,      # Max time to add memory item
        "search_time_ms": 1000,         # Max time for memory search
        "handoff_time_ms": 200,         # Max time to process handoff
        "cli_response_time_ms": 2000,   # Max CLI response time
        "max_memory_usage_mb": 512,     # Max memory usage during test
        "batch_operation_items": 100,   # Number of items for batch tests
        "concurrent_operations": 10      # Number of concurrent operations
    }


class MockProjectSetup:
    """Helper class for setting up mock project environments"""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.coral_dir = temp_dir / '.coral'
        
    def create_coral_structure(self):
        """Create basic .coral directory structure"""
        self.coral_dir.mkdir(exist_ok=True)
        (self.coral_dir / 'memory').mkdir(exist_ok=True)
        (self.coral_dir / 'state').mkdir(exist_ok=True)
        (self.coral_dir / 'logs').mkdir(exist_ok=True)
        
    def create_project_state(self, state_data: Dict[str, Any]):
        """Create project state file"""
        state_file = self.coral_dir / 'project_state.yaml'
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f)
            
    def create_memory_config(self):
        """Create memory configuration"""
        config = {
            "short_term": {"buffer_size": 50, "max_tokens": 10000},
            "long_term": {
                "type": "chroma",
                "collection_name": "test_memory",
                "persist_directory": str(self.coral_dir / "memory" / "chroma_test")
            },
            "orchestrator": {
                "short_term_limit": 50,
                "consolidation_threshold": 0.7,
                "importance_decay_hours": 24
            }
        }
        
        config_file = self.coral_dir / 'memory_config.json'
        with open(config_file, 'w') as f:
            json.dump(config, f)
            
        return str(config_file)
    
    def create_agents_config(self, agents_data: Dict[str, Any]):
        """Create agents configuration file"""
        config_file = self.temp_dir / 'config' / 'agents.yaml'
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(agents_data, f)


@pytest.fixture
def mock_project_setup(temp_project_dir):
    """Create mock project setup helper"""
    return MockProjectSetup(temp_project_dir)


def create_test_environment():
    """Utility function to create complete test environment"""
    import tempfile
    from pathlib import Path
    
    temp_dir = Path(tempfile.mkdtemp())
    setup = MockProjectSetup(temp_dir)
    setup.create_coral_structure()
    
    return temp_dir, setup