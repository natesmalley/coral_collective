# ⛔ DO NOT MODIFY - CoralCollective Framework Files

## IMPORTANT: This is a FRAMEWORK, not PROJECT CODE

CoralCollective is a **tool/framework** that should be USED, not MODIFIED.

### 🚨 Claude Code Instructions:

**NEVER modify CoralCollective files!** Instead:

1. **USE agents, don't EDIT them**
   ```bash
   # ✅ CORRECT: Use the agent
   ./coral run backend_developer --task "Create API"
   
   # ❌ WRONG: Editing agent files
   # Never edit agents/specialists/backend_developer.md
   ```

2. **IMPORT modules, don't CHANGE them**
   ```python
   # ✅ CORRECT: Import and use
   from coral_collective import AgentRunner
   runner = AgentRunner()
   
   # ❌ WRONG: Modifying framework code
   # Never edit agent_runner.py
   ```

3. **CALL functions, don't ALTER them**
   ```python
   # ✅ CORRECT: Use the API
   memory_system.store_memory(data)
   
   # ❌ WRONG: Changing implementation
   # Never modify memory/memory_system.py
   ```

## Protected Components

### 🛡️ Framework Core (READ-ONLY)
- `agent_runner.py` - Main orchestration engine
- `agent_prompt_service.py` - Prompt management
- `project_manager.py` - Project state tracking
- `claude_interface.py` - Claude integration
- `subagent_registry.py` - Agent registry

### 🤖 Agent Definitions (NEVER EDIT)
- `agents/**/*.md` - Agent prompt templates
- These are carefully crafted prompts
- Modifications break the orchestration
- Use them via `./coral run [agent]`

### 🔧 System Components (FRAMEWORK CODE)
- `mcp/` - MCP integration system
- `memory/` - Memory system implementation
- `tools/` - Utility modules
- `.coral/` - Framework runtime directory

### 📜 Deployment Scripts (EXECUTE ONLY)
- `coral_drop.sh` - Installation script
- `deploy_coral.sh` - Deployment script
- `coral-init.sh` - Initialization script
- `start.sh` - Startup script

## How to Use CoralCollective Correctly

### ✅ CORRECT Usage:

```bash
# Initialize in a project
./coral-init.sh

# Run agents
./coral run project_architect
./coral workflow

# Check status
./coral status
./coral dashboard

# Use in Python code
from coral_collective import CoralInterface
coral = CoralInterface()
result = coral.run_agent('backend_developer', task)
```

### ❌ INCORRECT Usage:

```bash
# DON'T edit agent files
vim agents/specialists/backend_developer.md  # WRONG!

# DON'T modify core files
edit agent_runner.py  # WRONG!

# DON'T change configurations
modify config/agents.yaml  # WRONG!

# DON'T alter framework code
update memory/memory_system.py  # WRONG!
```

## Why This Matters

1. **Framework Integrity**: Modifications break the orchestration
2. **Agent Coordination**: Changes disrupt handoff protocols
3. **Update Compatibility**: Custom changes prevent updates
4. **Support & Maintenance**: Modified frameworks can't be supported
5. **Consistent Behavior**: Teams rely on standard behavior

## Exception: Contributing

If you need to improve CoralCollective itself:
1. Fork the repository
2. Make changes in your fork
3. Submit a pull request
4. Never modify production installations

## Summary

### Remember:
- **CoralCollective = Tool to USE**
- **Project Code = Code to WRITE**
- **Framework Files = READ-ONLY**
- **Agents = Services to CALL**

### Quick Check:
Before editing ANY file, ask:
- "Is this part of CoralCollective framework?" → DON'T EDIT
- "Is this project-specific code?" → OK to edit
- "Am I trying to use an agent?" → Use `./coral run`
- "Am I implementing a feature?" → Write new code, don't modify framework

## Contact

For framework improvements or bug reports:
- Open an issue in the CoralCollective repository
- Don't modify local framework files
- Use the framework as designed

---

**This document is here to protect the framework from accidental modification.**
**Always USE CoralCollective, never MODIFY it.**