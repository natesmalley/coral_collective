# Agent Orchestrator

## Overview
The Agent Orchestrator manages the complete AI development team workflow, ensuring proper sequencing and handoffs between specialist agents.

## State Management & Coordination
The orchestrator now includes automatic state tracking to prevent work duplication and enable better context sharing:

- **Project State File**: `.coral/project_state.yaml` tracks all agent activities
- **Artifact Tracking**: All files created by agents are recorded
- **Context Sharing**: Agents can access outputs from previous agents
- **Handoff Protocol**: Structured data passing between agents
- **Non-Interactive Mode**: Full automation support for CI/CD environments

## Documentation-First Workflow

```
┌──────────────────────────────────────┐
│     Phase 1: Planning & Foundation   │
├──────────────────────────────────────┤
│  1. PROJECT ARCHITECT                │
│     └─> Creates project structure    │
│     └─> Designs architecture         │
│                                      │
│  2. TECHNICAL WRITER (Phase 1)      │
│     └─> Creates requirements docs    │
│     └─> Defines API specifications   │
│     └─> Establishes standards        │
└──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────┐
│    Phase 2: Development to Spec      │
├──────────────────────────────────────┤
│  3. BACKEND DEVELOPER                │
│     └─> Builds APIs to spec          │
│     └─> Implements data layer        │
│                                      │
│  4. AI/ML SPECIALIST (if needed)    │
│     └─> Integrates AI features       │
│     └─> Sets up vector databases     │
│                                      │
│  5. FRONTEND DEVELOPER               │
│     └─> Builds UI to spec            │
│     └─> Integrates with backend      │
│                                      │
│  6. SECURITY SPECIALIST              │
│     └─> Implements security          │
│     └─> Ensures compliance           │
└──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────┐
│    Phase 3: Quality & Deployment     │
├──────────────────────────────────────┤
│  7. QA & TESTING                     │
│     └─> Tests against requirements   │
│     └─> Validates acceptance criteria│
│                                      │
│  8. DEVOPS & DEPLOYMENT              │
│     └─> Deploys to production        │
│     └─> Sets up monitoring           │
└──────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────┐
│  Phase 4: Documentation Completion   │
├──────────────────────────────────────┤
│  9. TECHNICAL WRITER (Phase 2)      │
│     └─> Creates user documentation   │
│     └─> Finalizes all docs           │
└──────────────────────────────────────┘
```

## Agent Handoff Protocol

Each agent provides structured handoff data to the next agent:

```yaml
handoff:
  from_agent: backend_developer
  to_agent: frontend_developer
  artifacts:
    - type: api_endpoints
      path: /backend/api/
    - type: documentation
      path: /docs/api/
  context:
    api_base_url: http://localhost:3000
    auth_method: JWT
    database: PostgreSQL
  next_task: "Implement frontend UI components that consume the API endpoints"
  notes: "API is fully tested and documented. Auth endpoints ready."
```

## How to Use the Agent Team

### Starting a New Project

1. **Begin with Project Architect**
   ```
   Use this agent prompt from: agents/core/project_architect.md
   Provide your app requirements and answer clarifying questions
   ```

2. **Move to Technical Writer Phase 1**
   ```
   After architect completes, use the handoff instructions provided
   Technical Writer will create all documentation foundation
   ```

3. **Development Phase**
   Follow the recommended sequence from the architect's handoff:
   - Backend Developer
   - AI/ML Specialist (if AI features needed)
   - Frontend Developer
   - Security Specialist

4. **Quality Assurance**
   ```
   Use QA & Testing agent to validate against requirements
   ```

5. **Deployment**
   ```
   DevOps agent handles production deployment
   ```

6. **Final Documentation**
   ```
   Technical Writer Phase 2 creates user-facing documentation
   ```

## Agent Handoff Protocol

Each agent provides structured handoff information:

1. **COMPLETION SUMMARY** - What was delivered
2. **NEXT AGENT RECOMMENDATION** - Which agent should work next
3. **EXACT NEXT PROMPT** - Complete prompt to copy and run
4. **CONTEXT FOR NEXT AGENT** - Critical information to pass along
5. **ADDITIONAL NOTES** - Any special considerations

## Agent Selection Guide

### When to Use Each Agent

| Agent | Use When |
|-------|----------|
| **Project Architect** | Starting any new project or major feature |
| **Technical Writer Phase 1** | After architecture, before development |
| **Full-Stack Engineer** | Need quick solutions, debugging, MVPs, or filling gaps |
| **Backend Developer** | Building APIs, databases, server logic |
| **Frontend Developer** | Creating user interfaces and experiences |
| **AI/ML Specialist** | Adding AI features, LLM integration, ML models |
| **Security Specialist** | Handling sensitive data, compliance requirements |
| **DevOps & Deployment** | Ready to deploy to production |
| **QA & Testing** | Need comprehensive testing coverage |
| **Technical Writer Phase 2** | Finalizing user documentation |

## Project Types and Recommended Sequences

### Full-Stack Web Application
1. Project Architect
2. Technical Writer Phase 1
3. Backend Developer
4. Frontend Developer
5. Security Specialist
6. QA & Testing
7. DevOps & Deployment
8. Technical Writer Phase 2

### AI-Powered Application
1. Project Architect
2. Technical Writer Phase 1
3. Backend Developer
4. AI/ML Specialist
5. Frontend Developer
6. Security Specialist
7. QA & Testing
8. DevOps & Deployment
9. Technical Writer Phase 2

### API-Only Service
1. Project Architect
2. Technical Writer Phase 1
3. Backend Developer
4. Security Specialist
5. QA & Testing
6. DevOps & Deployment
7. Technical Writer Phase 2

### Frontend-Only Application
1. Project Architect
2. Technical Writer Phase 1
3. Frontend Developer
4. QA & Testing
5. DevOps & Deployment
6. Technical Writer Phase 2

### Rapid Prototype/MVP
1. Full-Stack Engineer (can handle entire MVP)
2. QA & Testing (basic validation)
3. DevOps & Deployment (quick deployment)

### Production Debugging
1. Full-Stack Engineer (immediate response)
2. Relevant Specialist (if deep expertise needed)
3. Site Reliability Engineer (for monitoring improvements)

## Best Practices

1. **Always Start with Architecture**
   - Never skip the Project Architect phase
   - Proper planning prevents poor performance

2. **Documentation Before Development**
   - Technical Writer Phase 1 creates specifications
   - Developers build to documented requirements

3. **Follow Handoff Instructions**
   - Each agent provides specific next steps
   - Use the exact prompts provided

4. **Maintain Project Structure**
   - All agents follow the established folder structure
   - Documentation stays in /docs folder

5. **Complete Each Phase**
   - Don't skip agents even if tempting
   - Each specialist adds critical value

## Troubleshooting

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| **Unclear requirements** | Return to Technical Writer Phase 1 |
| **Architecture changes needed** | Consult Project Architect again |
| **Security concerns** | Engage Security Specialist immediately |
| **Failed tests** | Return to relevant developer agent |
| **Deployment issues** | DevOps agent handles infrastructure |
| **Need quick fix** | Use Full-Stack Engineer for immediate solution |
| **Cross-system bug** | Full-Stack Engineer can debug across domains |
| **Missing specialist** | Full-Stack Engineer can fill the gap temporarily |

## Quick Start Example

```bash
# Step 1: Start with architecture
"I want to build a task management app with AI prioritization"
→ Use Project Architect prompt

# Step 2: Follow the handoff
[Architect provides]: "NEXT AGENT: Technical Writer Phase 1..."
→ Copy and use the provided prompt

# Step 3: Continue the chain
[Each agent provides]: "NEXT AGENT: [Name]..."
→ Follow the sequence until project complete
```

## Integration with Claude Code

All agents are optimized for:
- TypeScript support
- Clear code comments
- IDE navigation
- Debugging assistance
- Code review readiness

## Summary

The Agent Orchestrator ensures:
- ✅ Proper workflow sequencing
- ✅ Clear handoffs between specialists
- ✅ Documentation-first approach
- ✅ Comprehensive coverage of all aspects
- ✅ Consistent project structure
- ✅ Quality at every phase