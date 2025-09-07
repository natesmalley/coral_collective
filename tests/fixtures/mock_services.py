"""
Mock Services for CoralCollective Testing

Provides comprehensive mock implementations for:
1. Agent execution services
2. Memory system services  
3. MCP client services
4. Project state management
5. External API services
6. File system operations
"""

import asyncio
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, AsyncMock, MagicMock
from dataclasses import dataclass, asdict
import tempfile


@dataclass
class MockAgentResult:
    """Mock result from agent execution"""
    success: bool
    agent_id: str
    task: str
    duration: float
    outputs: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    handoff_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass  
class MockMemoryItem:
    """Mock memory item"""
    id: str
    content: str
    agent_id: str
    project_id: str
    timestamp: str
    memory_type: str = "episodic"
    importance: str = "medium"
    tags: Optional[List[str]] = None
    context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.context is None:
            self.context = {}


class MockAgentRunner:
    """Mock implementation of AgentRunner"""
    
    def __init__(self, agents_config: Optional[Dict] = None):
        self.agents_config = agents_config or self._default_agents_config()
        self.execution_history = []
        self.execution_delay = 0.1  # Simulate execution time
        self.failure_rate = 0.0  # Configurable failure rate for testing
        
    def _default_agents_config(self) -> Dict:
        """Default agents configuration for testing"""
        return {
            "version": 1,
            "agents": {
                "project_architect": {
                    "role": "architect",
                    "prompt_path": "agents/core/project_architect.md",
                    "capabilities": ["planning", "architecture", "structure"]
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
                "devops_deployment": {
                    "role": "devops_deployment",
                    "prompt_path": "agents/specialists/devops_deployment.md",
                    "capabilities": ["deployment", "infrastructure", "monitoring"]
                }
            }
        }
    
    async def run_agent(self, agent_id: str, task: str, options: Optional[Dict] = None) -> MockAgentResult:
        """Mock agent execution"""
        
        # Simulate execution delay
        await asyncio.sleep(self.execution_delay)
        
        # Simulate failure based on failure rate
        import random
        if random.random() < self.failure_rate:
            result = MockAgentResult(
                success=False,
                agent_id=agent_id,
                task=task,
                duration=self.execution_delay * 1000,
                outputs={},
                artifacts=[],
                error=f"Simulated failure for {agent_id}"
            )
        else:
            result = self._generate_successful_result(agent_id, task, options or {})
        
        self.execution_history.append(result)
        return result
    
    def _generate_successful_result(self, agent_id: str, task: str, options: Dict) -> MockAgentResult:
        """Generate successful agent execution result"""
        
        base_outputs = {
            "task_completed": task,
            "execution_context": options,
            "agent_insights": [f"Insight from {agent_id}", "Task completed successfully"]
        }
        
        base_artifacts = [
            {
                "type": "log",
                "path": f"/logs/{agent_id}_execution.log",
                "description": f"Execution log for {agent_id}"
            }
        ]
        
        # Agent-specific outputs and artifacts
        if agent_id == "project_architect":
            base_outputs.update({
                "architecture_document": "/docs/architecture.md",
                "project_structure": "/docs/project_structure.md", 
                "technology_decisions": ["React", "Node.js", "PostgreSQL", "Docker"]
            })
            base_artifacts.extend([
                {"type": "documentation", "path": "/docs/architecture.md"},
                {"type": "diagram", "path": "/docs/architecture_diagram.png"}
            ])
            
        elif agent_id == "backend_developer":
            base_outputs.update({
                "api_endpoints": ["POST /api/users", "GET /api/users", "PUT /api/users/:id"],
                "database_schema": "/src/db/schema.sql",
                "authentication_system": "JWT with refresh tokens"
            })
            base_artifacts.extend([
                {"type": "code", "path": "/src/api/routes.py", "language": "python"},
                {"type": "code", "path": "/src/models/user.py", "language": "python"},
                {"type": "sql", "path": "/src/db/schema.sql"}
            ])
            
        elif agent_id == "frontend_developer":
            base_outputs.update({
                "components_created": ["UserDashboard", "LoginForm", "NavigationBar"],
                "pages_implemented": ["Home", "Profile", "Settings"],
                "styling_framework": "Tailwind CSS"
            })
            base_artifacts.extend([
                {"type": "code", "path": "/src/components/UserDashboard.jsx", "language": "javascript"},
                {"type": "code", "path": "/src/pages/Home.jsx", "language": "javascript"},
                {"type": "css", "path": "/src/styles/main.css"}
            ])
            
        elif agent_id == "qa_testing":
            base_outputs.update({
                "test_coverage": {"unit": 87.5, "integration": 78.2, "e2e": 65.3},
                "tests_created": 156,
                "bugs_found": 3,
                "performance_metrics": {"response_time_p95": 245, "throughput_rps": 450}
            })
            base_artifacts.extend([
                {"type": "test", "path": "/tests/unit/test_api.py", "framework": "pytest"},
                {"type": "test", "path": "/tests/integration/test_workflow.py", "framework": "pytest"},
                {"type": "report", "path": "/tests/coverage_report.html"}
            ])
            
        elif agent_id == "devops_deployment":
            base_outputs.update({
                "deployment_environment": "Kubernetes",
                "ci_cd_pipeline": "GitHub Actions",
                "monitoring_setup": "Prometheus + Grafana",
                "deployment_url": "https://staging.example.com"
            })
            base_artifacts.extend([
                {"type": "config", "path": "/k8s/deployment.yaml"},
                {"type": "config", "path": "/.github/workflows/deploy.yml"},
                {"type": "config", "path": "/monitoring/prometheus.yml"}
            ])
        
        # Generate handoff data for workflow transitions
        handoff_data = None
        if agent_id == "project_architect":
            handoff_data = {
                "summary": "Architecture designed, ready for development",
                "next_agent": "backend_developer",
                "key_decisions": base_outputs.get("technology_decisions", []),
                "next_steps": ["Implement backend API", "Set up database schema"]
            }
        elif agent_id == "backend_developer":
            handoff_data = {
                "summary": "Backend implementation complete, API ready",
                "next_agent": "frontend_developer", 
                "api_endpoints": base_outputs.get("api_endpoints", []),
                "next_steps": ["Implement frontend UI", "Connect to API"]
            }
        elif agent_id == "frontend_developer":
            handoff_data = {
                "summary": "Frontend implementation complete",
                "next_agent": "qa_testing",
                "components": base_outputs.get("components_created", []),
                "next_steps": ["Run comprehensive tests", "Validate user workflows"]
            }
        elif agent_id == "qa_testing":
            handoff_data = {
                "summary": "Testing complete, ready for deployment",
                "next_agent": "devops_deployment",
                "test_results": base_outputs.get("test_coverage", {}),
                "next_steps": ["Deploy to staging", "Set up monitoring"]
            }
        
        return MockAgentResult(
            success=True,
            agent_id=agent_id,
            task=task,
            duration=self.execution_delay * 1000 + (hash(agent_id) % 500),  # Variable duration
            outputs=base_outputs,
            artifacts=base_artifacts,
            handoff_data=handoff_data
        )
    
    def get_available_agents(self, filter_role: Optional[str] = None) -> List[Dict]:
        """Get list of available agents"""
        agents = []
        for agent_id, config in self.agents_config["agents"].items():
            agent_info = {
                "id": agent_id,
                "role": config["role"], 
                "capabilities": config["capabilities"],
                "prompt_path": config["prompt_path"]
            }
            
            if filter_role is None or config["role"] == filter_role:
                agents.append(agent_info)
                
        return agents
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict]:
        """Get specific agent information"""
        if agent_id in self.agents_config["agents"]:
            config = self.agents_config["agents"][agent_id]
            return {
                "id": agent_id,
                "role": config["role"],
                "capabilities": config["capabilities"],
                "prompt_path": config["prompt_path"]
            }
        return None
    
    def set_failure_rate(self, rate: float):
        """Set failure rate for testing error scenarios"""
        self.failure_rate = max(0.0, min(1.0, rate))
    
    def set_execution_delay(self, delay_seconds: float):
        """Set execution delay for performance testing"""
        self.execution_delay = max(0.0, delay_seconds)
    
    def get_execution_history(self) -> List[MockAgentResult]:
        """Get history of agent executions"""
        return self.execution_history.copy()
    
    def clear_history(self):
        """Clear execution history"""
        self.execution_history.clear()


class MockMemorySystem:
    """Mock implementation of Memory System"""
    
    def __init__(self):
        self.memories = []
        self.working_memory = {}
        self.session_context = {}
        self.consolidation_history = []
        self.search_delay = 0.05  # 50ms search delay
        
    async def add_memory(self, content: str, agent_id: str, project_id: str, 
                        memory_type: str = "episodic", importance: str = "medium",
                        context: Optional[Dict] = None, tags: Optional[List[str]] = None) -> str:
        """Add memory item"""
        
        memory_id = f"mem_{len(self.memories):04d}_{hash(content) % 1000:03d}"
        
        memory_item = MockMemoryItem(
            id=memory_id,
            content=content,
            agent_id=agent_id,
            project_id=project_id,
            timestamp=datetime.now().isoformat(),
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            context=context or {}
        )
        
        self.memories.append(memory_item)
        return memory_id
    
    async def search_memories(self, query: str, limit: int = 10, 
                            agent_id: Optional[str] = None,
                            project_id: Optional[str] = None,
                            memory_type: Optional[str] = None) -> List[Dict]:
        """Search memories"""
        
        await asyncio.sleep(self.search_delay)
        
        # Filter memories based on criteria
        filtered_memories = []
        query_terms = query.lower().split()
        
        for memory in self.memories:
            # Apply filters
            if agent_id and memory.agent_id != agent_id:
                continue
            if project_id and memory.project_id != project_id:
                continue
            if memory_type and memory.memory_type != memory_type:
                continue
            
            # Calculate relevance score
            relevance = 0.0
            content_lower = memory.content.lower()
            
            # Check for query terms in content
            for term in query_terms:
                if term in content_lower:
                    relevance += 1.0
                if term in memory.tags:
                    relevance += 0.5
                if any(term in str(value).lower() for value in memory.context.values()):
                    relevance += 0.3
            
            if relevance > 0:
                memory_dict = asdict(memory)
                memory_dict['relevance'] = relevance
                filtered_memories.append(memory_dict)
        
        # Sort by relevance and return limited results
        filtered_memories.sort(key=lambda x: x['relevance'], reverse=True)
        return filtered_memories[:limit]
    
    async def get_agent_context(self, agent_id: str, project_id: str) -> Dict:
        """Get agent context with memories"""
        
        # Get recent memories for agent
        recent_memories = await self.search_memories(
            query="",
            limit=10,
            agent_id=agent_id,
            project_id=project_id
        )
        
        # Get relevant memories based on current working memory
        relevant_query = " ".join(self.working_memory.values()) if self.working_memory else "general"
        relevant_memories = await self.search_memories(
            query=str(relevant_query),
            limit=5,
            project_id=project_id
        )
        
        return {
            "recent_memories": recent_memories,
            "relevant_memories": relevant_memories,
            "working_memory": self.working_memory.copy(),
            "session_context": self.session_context.copy()
        }
    
    async def record_agent_handoff(self, from_agent: str, to_agent: str,
                                 project_id: str, handoff_data: Dict) -> str:
        """Record agent handoff"""
        
        handoff_content = f"Agent handoff: {from_agent} → {to_agent}"
        return await self.add_memory(
            content=handoff_content,
            agent_id="system",
            project_id=project_id,
            memory_type="episodic",
            importance="high",
            context={
                "type": "agent_handoff",
                "from_agent": from_agent,
                "to_agent": to_agent,
                "handoff_data": handoff_data
            },
            tags=["handoff", from_agent, to_agent]
        )
    
    def set_working_memory(self, key: str, value: Any):
        """Set working memory item"""
        self.working_memory[key] = value
    
    def get_working_memory(self) -> Dict:
        """Get working memory"""
        return self.working_memory.copy()
    
    def set_session_context(self, context: Dict):
        """Set session context"""
        self.session_context.update(context)
    
    def get_session_context(self) -> Dict:
        """Get session context"""
        return self.session_context.copy()
    
    def get_memory_stats(self) -> Dict:
        """Get memory system statistics"""
        return {
            "total_memories": len(self.memories),
            "short_term_memories": len([m for m in self.memories if m.memory_type == "short_term"]),
            "long_term_memories": len([m for m in self.memories if m.memory_type == "long_term"]),
            "working_memory_keys": len(self.working_memory),
            "session_context_keys": len(self.session_context)
        }
    
    async def consolidate_memories(self, memories: List[Dict], 
                                 strategy: str = "importance_based") -> Dict:
        """Mock memory consolidation"""
        
        await asyncio.sleep(0.1 * len(memories))  # Simulate processing time
        
        consolidation_result = {
            "success": True,
            "memories_processed": len(memories),
            "consolidation_strategy": strategy,
            "consolidation_summary": f"Consolidated {len(memories)} memories using {strategy} strategy",
            "processing_time": 0.1 * len(memories)
        }
        
        self.consolidation_history.append(consolidation_result)
        return consolidation_result


class MockMCPClient:
    """Mock implementation of MCP Client"""
    
    def __init__(self):
        self.connected = False
        self.available_tools = {
            "filesystem_read": {
                "name": "filesystem_read",
                "description": "Read files from filesystem",
                "parameters": {"path": "string", "encoding": "string"}
            },
            "filesystem_write": {
                "name": "filesystem_write", 
                "description": "Write files to filesystem",
                "parameters": {"path": "string", "content": "string", "encoding": "string"}
            },
            "github_create_repo": {
                "name": "github_create_repo",
                "description": "Create GitHub repository",
                "parameters": {"name": "string", "description": "string", "private": "boolean"}
            },
            "github_create_issue": {
                "name": "github_create_issue",
                "description": "Create GitHub issue",
                "parameters": {"repo": "string", "title": "string", "body": "string"}
            },
            "postgres_execute": {
                "name": "postgres_execute",
                "description": "Execute PostgreSQL query",
                "parameters": {"query": "string", "params": "array"}
            }
        }
        self.tool_call_history = []
        self.tool_latency = 0.1  # 100ms default latency
        
    async def connect(self) -> bool:
        """Mock connection to MCP servers"""
        await asyncio.sleep(0.1)  # Simulate connection time
        self.connected = True
        return True
    
    async def disconnect(self):
        """Mock disconnection from MCP servers"""
        await asyncio.sleep(0.05)
        self.connected = False
    
    async def list_tools(self) -> List[Dict]:
        """List available tools"""
        if not self.connected:
            raise RuntimeError("MCP client not connected")
        
        return list(self.available_tools.values())
    
    async def call_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Mock tool execution"""
        
        if not self.connected:
            raise RuntimeError("MCP client not connected")
        
        if tool_name not in self.available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        # Simulate tool execution delay
        await asyncio.sleep(self.tool_latency)
        
        # Generate mock response based on tool
        result = self._generate_tool_result(tool_name, parameters)
        
        # Record tool call
        call_record = {
            "tool_name": tool_name,
            "parameters": parameters,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.tool_call_history.append(call_record)
        
        return result
    
    def _generate_tool_result(self, tool_name: str, parameters: Dict) -> Dict:
        """Generate mock tool execution result"""
        
        base_result = {
            "success": True,
            "tool": tool_name,
            "execution_time": self.tool_latency,
            "timestamp": datetime.now().isoformat()
        }
        
        if tool_name == "filesystem_read":
            path = parameters.get("path", "/unknown")
            base_result.update({
                "content": f"Mock file content from {path}",
                "size_bytes": 1024,
                "encoding": parameters.get("encoding", "utf-8")
            })
            
        elif tool_name == "filesystem_write":
            path = parameters.get("path", "/unknown")
            content = parameters.get("content", "")
            base_result.update({
                "path": path,
                "bytes_written": len(content),
                "encoding": parameters.get("encoding", "utf-8")
            })
            
        elif tool_name == "github_create_repo":
            repo_name = parameters.get("name", "test-repo")
            base_result.update({
                "repository": {
                    "name": repo_name,
                    "full_name": f"testuser/{repo_name}",
                    "url": f"https://github.com/testuser/{repo_name}",
                    "private": parameters.get("private", False)
                }
            })
            
        elif tool_name == "github_create_issue":
            base_result.update({
                "issue": {
                    "id": 12345,
                    "number": 1,
                    "title": parameters.get("title", "Test Issue"),
                    "state": "open",
                    "url": f"https://github.com/{parameters.get('repo', 'test/repo')}/issues/1"
                }
            })
            
        elif tool_name == "postgres_execute":
            query = parameters.get("query", "SELECT 1")
            if query.strip().upper().startswith("SELECT"):
                base_result.update({
                    "rows": [{"id": 1, "name": "test_data"}],
                    "row_count": 1,
                    "columns": ["id", "name"]
                })
            else:
                base_result.update({
                    "rows_affected": 1,
                    "message": "Query executed successfully"
                })
        
        return base_result
    
    def get_tool_history(self) -> List[Dict]:
        """Get tool call history"""
        return self.tool_call_history.copy()
    
    def clear_history(self):
        """Clear tool call history"""
        self.tool_call_history.clear()
    
    def set_tool_latency(self, latency_seconds: float):
        """Set tool execution latency for testing"""
        self.tool_latency = max(0.0, latency_seconds)


class MockProjectStateManager:
    """Mock implementation of Project State Manager"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.project_state = self._initialize_project_state()
        self.state_history = []
        
    def _initialize_project_state(self) -> Dict:
        """Initialize default project state"""
        return {
            "project": {
                "id": self.project_id,
                "name": self.project_id.replace("_", " ").title(),
                "created_at": datetime.now().isoformat(),
                "current_phase": "planning",
                "status": "active",
                "description": f"Mock project {self.project_id} for testing"
            },
            "agents": {
                "completed": [],
                "active": None,
                "queue": ["project_architect", "technical_writer"]
            },
            "handoffs": [],
            "artifacts": [],
            "metrics": {
                "total_agents_run": 0,
                "successful_completions": 0,
                "failed_completions": 0,
                "total_handoffs": 0,
                "artifacts_created": 0,
                "estimated_completion": "0%"
            }
        }
    
    def get_current_state(self) -> Dict:
        """Get current project state"""
        return self.project_state.copy()
    
    def update_agent_status(self, agent_id: str, status: str, 
                          result: Optional[Dict] = None) -> bool:
        """Update agent status"""
        
        # Save state to history
        self.state_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "update_agent_status",
            "agent_id": agent_id,
            "status": status,
            "previous_state": self.project_state.copy()
        })
        
        if status == "active":
            self.project_state["agents"]["active"] = agent_id
            # Remove from queue if present
            if agent_id in self.project_state["agents"]["queue"]:
                self.project_state["agents"]["queue"].remove(agent_id)
                
        elif status == "completed":
            # Move from active to completed
            if self.project_state["agents"]["active"] == agent_id:
                self.project_state["agents"]["active"] = None
            
            completion_record = {
                "agent_id": agent_id,
                "completed_at": datetime.now().isoformat(),
                "success": True
            }
            
            if result:
                completion_record.update({
                    "task": result.get("task", ""),
                    "duration_minutes": result.get("duration", 0) / 60,
                    "outputs": result.get("outputs", {}),
                    "artifacts": result.get("artifacts", [])
                })
            
            self.project_state["agents"]["completed"].append(completion_record)
            
            # Update metrics
            self.project_state["metrics"]["total_agents_run"] += 1
            self.project_state["metrics"]["successful_completions"] += 1
            
        elif status == "failed":
            if self.project_state["agents"]["active"] == agent_id:
                self.project_state["agents"]["active"] = None
            
            # Update metrics
            self.project_state["metrics"]["total_agents_run"] += 1
            self.project_state["metrics"]["failed_completions"] += 1
        
        return True
    
    def add_artifact(self, artifact_data: Dict) -> str:
        """Add project artifact"""
        
        artifact_id = f"artifact_{len(self.project_state['artifacts']):03d}"
        
        artifact = {
            "id": artifact_id,
            "created_at": datetime.now().isoformat(),
            **artifact_data
        }
        
        self.project_state["artifacts"].append(artifact)
        self.project_state["metrics"]["artifacts_created"] += 1
        
        return artifact_id
    
    def add_handoff(self, from_agent: str, to_agent: str, handoff_data: Dict) -> str:
        """Add agent handoff record"""
        
        handoff_id = f"handoff_{len(self.project_state['handoffs']):03d}"
        
        handoff = {
            "id": handoff_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now().isoformat(),
            "data": handoff_data
        }
        
        self.project_state["handoffs"].append(handoff)
        self.project_state["metrics"]["total_handoffs"] += 1
        
        return handoff_id
    
    def update_project_phase(self, phase: str):
        """Update project phase"""
        self.project_state["project"]["current_phase"] = phase
        
    def get_project_metrics(self) -> Dict:
        """Get project metrics"""
        return self.project_state["metrics"].copy()
    
    def get_state_history(self) -> List[Dict]:
        """Get state change history"""
        return self.state_history.copy()


class MockServiceFactory:
    """Factory for creating mock services with consistent configuration"""
    
    @staticmethod
    def create_agent_runner(**kwargs) -> MockAgentRunner:
        """Create mock agent runner"""
        return MockAgentRunner(**kwargs)
    
    @staticmethod
    def create_memory_system() -> MockMemorySystem:
        """Create mock memory system"""
        return MockMemorySystem()
    
    @staticmethod
    def create_mcp_client(**kwargs) -> MockMCPClient:
        """Create mock MCP client"""
        return MockMCPClient(**kwargs)
    
    @staticmethod
    def create_project_state_manager(project_id: str) -> MockProjectStateManager:
        """Create mock project state manager"""
        return MockProjectStateManager(project_id)
    
    @staticmethod
    def create_integrated_test_environment(project_id: str = "test_project") -> Dict:
        """Create complete integrated test environment"""
        
        return {
            "agent_runner": MockServiceFactory.create_agent_runner(),
            "memory_system": MockServiceFactory.create_memory_system(),
            "mcp_client": MockServiceFactory.create_mcp_client(),
            "state_manager": MockServiceFactory.create_project_state_manager(project_id),
            "project_id": project_id,
            "temp_dir": Path(tempfile.mkdtemp())
        }


# Utility functions for test setup
def create_sample_project_structure(base_path: Path) -> Dict[str, Path]:
    """Create sample project directory structure"""
    
    structure = {
        "root": base_path,
        "src": base_path / "src",
        "tests": base_path / "tests", 
        "docs": base_path / "docs",
        "config": base_path / "config",
        "coral": base_path / ".coral",
        "coral_state": base_path / ".coral" / "state",
        "coral_memory": base_path / ".coral" / "memory",
        "coral_logs": base_path / ".coral" / "logs"
    }
    
    # Create directories
    for path in structure.values():
        path.mkdir(parents=True, exist_ok=True)
    
    # Create sample files
    (structure["src"] / "main.py").write_text('print("Hello, CoralCollective!")')
    (structure["docs"] / "README.md").write_text("# Test Project\nSample project for testing")
    (structure["config"] / "settings.yaml").write_text("environment: test\ndebug: true")
    
    return structure


def generate_sample_memories(count: int = 10, project_id: str = "test_project") -> List[MockMemoryItem]:
    """Generate sample memory items for testing"""
    
    memories = []
    agents = ["project_architect", "backend_developer", "frontend_developer", "qa_testing"]
    memory_types = ["episodic", "semantic", "short_term"]
    importance_levels = ["low", "medium", "high", "critical"]
    
    for i in range(count):
        memory = MockMemoryItem(
            id=f"sample_mem_{i:03d}",
            content=f"Sample memory content {i}: Agent completed task with various outcomes",
            agent_id=agents[i % len(agents)],
            project_id=project_id,
            timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
            memory_type=memory_types[i % len(memory_types)],
            importance=importance_levels[i % len(importance_levels)],
            tags=[f"tag_{i % 3}", f"sample_{i}", "generated"],
            context={
                "iteration": i,
                "phase": "development" if i < count // 2 else "testing",
                "sample": True
            }
        )
        memories.append(memory)
    
    return memories