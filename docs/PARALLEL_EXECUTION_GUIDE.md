# Parallel Agent Execution Guide

## Overview

CoralCollective now supports **parallel agent execution** for dramatically improved efficiency. Instead of running agents sequentially (taking 20-30 minutes), we can run independent tasks in parallel (reducing time to 5-10 minutes).

## Key Benefits

### ⚡ Speed Improvements
- **Sequential**: 10 agents × 2 minutes = 20 minutes
- **Parallel**: 3-4 phases × 2 minutes = 6-8 minutes  
- **Efficiency Gain**: 60-70% time reduction

### 🎯 Better Resource Utilization
- Multiple agents work simultaneously
- No waiting for independent tasks
- Optimal use of compute resources

### 🔄 Smart Dependencies
- Respects task dependencies
- Parallel where possible
- Sequential where necessary

## How It Works

### 1. Task Decomposition
Break complex projects into independent subtasks:

```
Traditional (Sequential):
Architect → Writer → Backend → Frontend → QA → DevOps
Total: 6 × 2 min = 12 minutes

Parallel Decomposition:
Phase 1: Architect (2 min)
Phase 2: Writer (2 min)  
Phase 3: Backend + Frontend + Database (parallel - 2 min)
Phase 4: QA + DevOps (parallel - 2 min)
Total: 8 minutes (33% faster!)
```

### 2. Dependency Management
```python
# Tasks that CAN run in parallel (no dependencies)
- Database design + API design + UI mockups
- Backend implementation + Frontend implementation
- Multiple test suites

# Tasks that MUST be sequential (dependencies)
- Architect → Technical Writer (needs architecture)
- Backend → API Integration (needs endpoints)
- Testing → Deployment (needs working code)
```

### 3. Execution Phases
Projects are divided into phases where each phase contains tasks that can run in parallel:

```yaml
Phase 1: Planning
  - Project Architect (solo)
  
Phase 2: Design
  - Database Specialist
  - API Designer
  - UI Designer
  (all run in parallel)
  
Phase 3: Implementation
  - Backend Developer
  - Frontend Developer
  (run in parallel)
  
Phase 4: Integration
  - Full Stack Engineer
  - QA Testing
  (run in parallel)
  
Phase 5: Deployment
  - DevOps (solo)
```

## Usage

### Command Line

```bash
# Run a full stack project with parallel execution
python parallel_agent_runner.py full_stack "Todo app with auth"

# Run API service with max 6 parallel workers
python parallel_agent_runner.py api "Blog REST API" --max-workers 6

# Show execution plan without running
python parallel_agent_runner.py frontend "Dashboard UI" --show-plan
```

### Python API

```python
from parallel_agent_runner import ParallelAgentRunner

runner = ParallelAgentRunner(max_workers=4)

# Create and execute plan
plan = runner.create_parallel_plan("full_stack", "E-commerce site")
summary = runner.execute_plan(plan)

print(f"Completed in {summary['total_time_seconds']} seconds")
print(f"Time saved: {summary['time_saved_seconds']} seconds")
```

### Multi-Agent Orchestrator

```python
from tools.multi_agent_orchestrator import MultiAgentOrchestrator
from tools.multi_agent_orchestrator import ExecutionMode

orchestrator = MultiAgentOrchestrator()

# Execute with dependency-based parallelization
summary = orchestrator.execute_workflow(
    project_type="full_stack_app",
    project_description="Social media platform",
    mode=ExecutionMode.DEPENDENCY_BASED
)
```

## Execution Strategies

### 1. Full Stack Application
```
Phase 1: Architecture (1 agent, 2 min)
Phase 2: Requirements (1 agent, 2 min)  
Phase 3: Design (3 agents parallel, 2 min)
  - Database Schema
  - API Specification
  - UI Mockups
Phase 4: Development (2 agents parallel, 3 min)
  - Backend (APIs, database)
  - Frontend (UI, state)
Phase 5: Integration (2 agents parallel, 2 min)
  - Full Stack Integration
  - QA Testing
Phase 6: Deployment (1 agent, 2 min)

Total: 13 minutes (vs 30+ minutes sequential)
```

### 2. API Service
```
Phase 1: Architecture (1 agent, 2 min)
Phase 2: Specification (2 agents parallel, 2 min)
  - API Design
  - Database Models
Phase 3: Implementation (2 agents parallel, 3 min)
  - Backend Development
  - Security Implementation
Phase 4: Finalization (2 agents parallel, 2 min)
  - Testing
  - Deployment

Total: 9 minutes (vs 20 minutes sequential)
```

### 3. Frontend Application
```
Phase 1: Planning (2 agents parallel, 2 min)
  - UI Designer
  - Frontend Architect
Phase 2: Development (2 agents parallel, 3 min)
  - Component Development
  - Accessibility
Phase 3: Polish (2 agents parallel, 2 min)
  - Integration
  - Testing

Total: 7 minutes (vs 15 minutes sequential)
```

## Implementation Details

### Task Dependencies
Each task declares its dependencies:

```python
ParallelTask(
    agent_id="backend-developer",
    task="Implement REST API",
    depends_on=["api-designer", "database-specialist"]
)
```

### Parallel Groups
Tasks with no mutual dependencies run together:

```python
# These can run in parallel
group = [
    ParallelTask("database-specialist", "Design schema"),
    ParallelTask("api-designer", "Design endpoints"),
    ParallelTask("ui-designer", "Create mockups")
]
```

### Coordination Files
All parallel agents use:
- **scratchpad.md** - Shared working memory
- **activity_tracker.md** - Activity log
- **project_state.yaml** - Machine-readable state

### Non-Interactive Mode
Parallel execution automatically enables non-interactive mode:
```python
os.environ['CORAL_NON_INTERACTIVE'] = '1'
```

## Performance Metrics

### Typical Time Savings

| Project Type | Sequential | Parallel | Savings | Efficiency |
|-------------|------------|----------|---------|------------|
| Full Stack App | 30 min | 12 min | 18 min | 60% |
| API Service | 20 min | 9 min | 11 min | 55% |
| Frontend App | 15 min | 7 min | 8 min | 53% |
| Microservice | 25 min | 10 min | 15 min | 60% |

### Parallelization Factors

| Factor | Impact |
|--------|--------|
| Independent Design Tasks | High (3-4x speedup) |
| Separate Frontend/Backend | High (2x speedup) |
| Multiple Test Suites | Medium (1.5x speedup) |
| Documentation Generation | Low (usually sequential) |

## Best Practices

### ✅ DO
- Identify truly independent tasks
- Use scratchpad.md for coordination
- Set appropriate max_workers (usually 4-6)
- Monitor activity_tracker.md for issues
- Run planning agents first (sequential)

### ❌ DON'T
- Parallelize dependent tasks
- Skip coordination files
- Use too many workers (diminishing returns)
- Ignore failure cascades
- Mix integration before unit work is done

## Advanced Configuration

### Custom Execution Plans

```python
custom_plan = [
    # Phase 1: Research (parallel)
    [
        ParallelTask("ai-ml-specialist", "Research ML options"),
        ParallelTask("security-specialist", "Security assessment"),
    ],
    # Phase 2: Design (parallel)
    [
        ParallelTask("architect", "System design"),
        ParallelTask("database-specialist", "Data architecture"),
    ],
    # Phase 3: Implementation (sequential)
    [
        ParallelTask("backend-developer", "Core implementation"),
    ],
    # Phase 4: Enhancement (parallel)
    [
        ParallelTask("frontend-developer", "UI"),
        ParallelTask("ai-ml-specialist", "ML integration"),
    ]
]

runner.execute_plan(custom_plan)
```

### Execution Modes

```python
# Dependency-based (recommended)
ExecutionMode.DEPENDENCY_BASED  # Respects dependencies, parallel where possible

# Full parallel (aggressive)
ExecutionMode.PARALLEL  # Run everything possible in parallel

# Sequential (safe)
ExecutionMode.SEQUENTIAL  # Traditional one-by-one execution

# Pipeline (streaming)
ExecutionMode.PIPELINE  # Start next phase before previous completes
```

### Resource Limits

```python
# Limit parallel execution
runner = ParallelAgentRunner(
    max_workers=4,  # Maximum parallel agents
    timeout=300,    # Timeout per agent (seconds)
    retry_failed=True  # Retry failed agents
)
```

## Monitoring & Debugging

### Real-time Progress
```
🚀 Starting Parallel Agent Execution

Phase 1/4
Running: project-architect
✅ project-architect completed

Phase 2/4
Running in parallel: database-specialist, api-designer, ui-designer
✅ database-specialist completed
✅ api-designer completed
✅ ui-designer completed

Phase 3/4
Running in parallel: backend-developer, frontend-developer
✅ backend-developer completed
✅ frontend-developer completed
```

### Activity Tracking
Check `activity_tracker.md` for detailed logs:
```markdown
### [2025-01-15 10:30] backend-developer (PARALLEL)
**Task**: Implement REST API
**Group**: Phase 3
**Dependencies**: database-specialist, api-designer
**Status**: ✅ Completed
**Duration**: 2.3 minutes
```

### Performance Summary
```
Execution Summary
─────────────────────────────
Total Agents        : 8
Successful         : 8
Failed            : 0
Success Rate      : 100.0%
Total Time        : 453.2 seconds
Sequential Estimate: 960.0 seconds
Time Saved        : 506.8 seconds
Efficiency Gain   : 52.8%
Phases           : 4
Max Parallel     : 3
```

## Troubleshooting

### Issue: Tasks Running Sequential Despite Parallel Config
**Solution**: Check dependencies - tasks with dependencies cannot run until dependencies complete

### Issue: Too Many Parallel Tasks Overwhelming System
**Solution**: Reduce max_workers to 3-4 for optimal performance

### Issue: Agents Can't Find Previous Agent Output
**Solution**: Ensure all agents update scratchpad.md and activity_tracker.md

### Issue: Parallel Execution Fails
**Solution**: Fall back to sequential mode or check agent non-interactive support

## Future Enhancements

### Planned Features
- 🔮 Automatic dependency detection
- 📊 Real-time execution visualization
- 🔄 Dynamic re-planning on failures
- 🎯 Smart agent selection based on load
- 📈 Historical performance analytics
- 🤖 ML-based execution optimization

### Coming Soon
- WebSocket-based real-time monitoring
- Distributed execution across multiple machines
- Checkpoint and resume capabilities
- Advanced failure recovery strategies

## Conclusion

Parallel agent execution provides:
- **60-70% time savings** on typical projects
- **Better resource utilization**
- **Maintained quality** through smart dependencies
- **Improved developer experience**

Start using parallel execution today:
```bash
python parallel_agent_runner.py full_stack "Your next project"
```

Watch your development time drop from 30 minutes to 10 minutes! 🚀