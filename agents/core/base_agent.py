from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
from enum import Enum


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"
    BLOCKED = "blocked"


class AgentRole(Enum):
    ARCHITECT = "architect"
    FRONTEND = "frontend"
    BACKEND = "backend"
    AI_ML = "ai_ml"
    SECURITY = "security"
    DEVOPS = "devops"
    QA = "qa"
    TECHNICAL_WRITER = "technical_writer"
    DATA_ENGINEER = "data_engineer"
    DATABASE_SPECIALIST = "database_specialist"
    MOBILE_DEVELOPER = "mobile_developer"
    API_DESIGNER = "api_designer"
    PERFORMANCE_ENGINEER = "performance_engineer"
    ACCESSIBILITY = "accessibility"
    SRE = "site_reliability_engineer"
    COMPLIANCE = "compliance"
    ANALYTICS_ENGINEER = "analytics_engineer"
    UI_DESIGNER = "ui_designer"


@dataclass
class AgentContext:
    project_path: str
    project_name: str
    tech_stack: Dict[str, List[str]] = field(default_factory=dict)
    requirements: Dict[str, Any] = field(default_factory=dict)
    completed_tasks: List[str] = field(default_factory=list)
    current_phase: str = "planning"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentHandoff:
    from_agent: str
    to_agent: str
    completed_items: List[str]
    context: Dict[str, Any]
    next_prompt: str
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        role: AgentRole,
        description: str,
        capabilities: List[str],
        context: Optional[AgentContext] = None
    ):
        self.name = name
        self.role = role
        self.description = description
        self.capabilities = capabilities
        self.context = context or AgentContext(project_path=".", project_name="unnamed")
        self.status = AgentStatus.IDLE
        self.tasks_completed = []
        self.current_task = None
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"agent.{self.name}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'[%(asctime)s] [{self.name}] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    @abstractmethod
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_prerequisites(self) -> bool:
        pass

    @abstractmethod
    def generate_handoff(self, next_agent: str) -> AgentHandoff:
        pass

    def update_status(self, status: AgentStatus) -> None:
        self.status = status
        self.logger.info(f"Status updated to: {status.value}")

    def add_completed_task(self, task: str) -> None:
        self.tasks_completed.append(task)
        self.context.completed_tasks.append(f"{self.name}: {task}")
        self.logger.info(f"Task completed: {task}")

    def get_prompt(self) -> str:
        return self._load_prompt_template()

    @abstractmethod
    def _load_prompt_template(self) -> str:
        pass

    def can_handle_task(self, task_type: str) -> bool:
        return task_type.lower() in [cap.lower() for cap in self.capabilities]

    def prepare_workspace(self) -> bool:
        self.logger.info(f"Preparing workspace for {self.name}")
        return True

    def cleanup(self) -> None:
        self.logger.info(f"Cleaning up after {self.name}")
        self.status = AgentStatus.IDLE
        self.current_task = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', role={self.role.value}, status={self.status.value})"
