# 🚀 Agent Force Quick Start Guide

## Setup in 30 Seconds

### Step 1: Enable Agent Force in Claude Code
1. Copy everything from `AGENT_FORCE_MASTER_PROMPT.md`
2. Paste it at the start of your Claude Code conversation
3. Claude Code now has access to all 8 specialist agents!

### Step 2: Start Building
Simply say:
- **"Start a new project"** - Activates Project Architect
- **"Use the Backend Developer agent"** - Activates specific agent  
- **"Help me build a todo app"** - Claude suggests the right agents
- **"Continue with the agent workflow"** - Follows the handoff chain

## 🎯 Quick Commands

| What You Say | What Happens |
|--------------|--------------|
| "Start a new project" | Project Architect creates structure |
| "Use the [name] agent" | Activates that specific specialist |
| "What agent should I use for..." | Claude recommends the right agent |
| "Continue with next agent" | Follows handoff instructions |
| "Build me a [type] app" | Starts complete workflow |

## 📋 Example Conversation Flow

```
You: "I want to build a task management app with AI prioritization"

Claude: "I'll help you build this using our Agent Force system. Let me activate 
the Project Architect agent to create the technical plan and project structure.

*[Activates Project Architect]*

As your Project Architect, I need to understand your requirements..."

[... Project Architect completes ...]

Claude: "=== PROJECT ARCHITECT HANDOFF ===
NEXT AGENT: Technical Writer Phase 1
Shall I continue with the Technical Writer to create the documentation foundation?"

You: "Yes, continue"

Claude: "*[Activates Technical Writer Phase 1]*
As your Technical Writer, I'll now create the requirements documentation..."
```

## 🔄 The Complete Workflow

```
1. Project Architect (Planning)
   ↓
2. Technical Writer Phase 1 (Documentation)
   ↓
3. Backend Developer (APIs)
   ↓
4. AI/ML Specialist (If needed)
   ↓
5. Frontend Developer (UI)
   ↓
6. Security Specialist (Security)
   ↓
7. QA & Testing (Quality)
   ↓
8. DevOps & Deployment (Production)
   ↓
9. Technical Writer Phase 2 (User Docs)
```

## 💡 Pro Tips

### Let Claude Code Guide You
- Claude knows the optimal agent sequence
- Just follow the handoff recommendations
- Each agent provides exact next steps

### Jump to Specific Agents
```
"Use the Security Specialist agent to review my authentication"
"Switch to the Frontend Developer agent"  
"Activate the AI/ML Specialist for this feature"
```

### Work on Existing Projects
```
"Use the Backend Developer agent to add a new API endpoint"
"Use the QA Testing agent to test this feature"
"Use DevOps agent to deploy this update"
```

## 🎯 Common Scenarios

### Scenario 1: Brand New Project
```
You: "Start a new SaaS application"
Claude: [Activates Project Architect] → [Guides through entire workflow]
```

### Scenario 2: Add Feature to Existing Project  
```
You: "Add user authentication to my app"
Claude: [Activates Backend Developer] → [Then Security Specialist]
```

### Scenario 3: Fix and Deploy
```
You: "Fix the bugs and deploy to production"
Claude: [Activates QA & Testing] → [Then DevOps & Deployment]
```

### Scenario 4: AI Enhancement
```
You: "Add AI chat support to my app"
Claude: [Activates AI/ML Specialist] → [Coordinates with Frontend]
```

## 🚦 Visual Status Indicators

Claude will clearly indicate:
- 🤖 **Active Agent**: "As your [Agent Name]..."
- ✅ **Completed Tasks**: "COMPLETED: ✓ Task done"
- ➡️ **Next Steps**: "NEXT AGENT: [Name]"
- 📋 **Handoff Ready**: "=== HANDOFF ==="

## ⚡ Speed Run Commands

For experienced users:
- **"Run the full agent workflow"** - Executes all agents in sequence
- **"Skip to deployment"** - Jumps to DevOps agent
- **"Documentation only"** - Just Technical Writer phases
- **"Backend and frontend only"** - Skips auxiliary agents

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Claude doesn't recognize agents" | Paste the master prompt first |
| "Wrong agent activated" | Say "Switch to [correct agent] agent" |
| "Lost in workflow" | Say "Show me the agent workflow status" |
| "Need to go back" | Say "Return to [previous agent] agent" |

## 🎉 Ready to Build?

1. Copy the master prompt
2. Start Claude Code
3. Paste the prompt
4. Say "Start a new project"
5. Follow the guided workflow!

**Remember**: The agents work best when you follow the complete workflow, but you can always jump to specific agents when needed!