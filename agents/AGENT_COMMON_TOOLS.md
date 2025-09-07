# Common Tools for All Agents

## Essential Working Documents

Every agent MUST use these two critical files for coordination and memory:

### 1. 📝 scratchpad.md
**Location**: `/scratchpad.md` (project root)

**Purpose**: 
- Temporary notes and working memory
- Information that doesn't fit elsewhere
- Quick references and reminders
- Draft content before finalizing
- Cross-agent communication notes

**How to Use**:
```markdown
## Current Working Notes

### API Endpoints Discovered
- POST /api/users - Created by backend_developer
- GET /api/users/:id - Needs frontend integration

### Questions for Next Agent
- Should we use JWT or OAuth2?
- Database connection string needed

### TODOs
- [ ] Verify authentication flow
- [ ] Test error handling
```

**When to Update**:
- At the START of your task (read existing notes)
- During work (add discoveries and questions)
- Before handoff (leave notes for next agent)

### 2. 📊 activity_tracker.md
**Location**: `/activity_tracker.md` (project root)

**Purpose**:
- Complete log of all agent activities
- What was attempted, what worked, what failed
- Helps with debugging and retry logic
- Prevents repeating failed approaches
- Knowledge base for future agents

**Format**:
```markdown
## Activity Log

### [2025-01-15 10:30] Backend Developer
**Task**: Create user authentication API
**Actions Taken**:
1. Created /api/auth/login endpoint
2. Implemented JWT token generation
3. Added password hashing with bcrypt

**Results**: 
✅ Authentication working
⚠️ Need to add rate limiting

**Files Modified**:
- /backend/routes/auth.js
- /backend/middleware/auth.js

**Notes for Next Agent**:
- JWT secret in .env file
- Token expiry set to 24h
- Consider adding refresh token

---

### [2025-01-15 11:45] Frontend Developer
**Task**: Create login UI
**Attempted**: Material-UI form
**Issue**: Build failed with TypeScript errors
**Resolution**: Fixed by updating tsconfig.json
**Learning**: Always check TypeScript config first
```

**Required Fields**:
- Timestamp and agent name
- Task description
- Actions taken (numbered list)
- Results (success/failure/partial)
- Files created/modified
- Notes for next agent
- Issues and resolutions

## Usage Protocol

### Starting Your Work
1. **READ** both files first:
   ```bash
   # Check scratchpad for notes from previous agents
   cat scratchpad.md
   
   # Review activity log to understand what's been done
   cat activity_tracker.md
   ```

2. **UPDATE** activity_tracker.md with your start:
   ```markdown
   ### [TIMESTAMP] Your Agent Name
   **Task**: Starting [your task description]
   **Status**: In Progress
   ```

### During Your Work
1. **USE** scratchpad.md for:
   - Quick notes and observations
   - Questions that arise
   - Temporary code snippets
   - Ideas for improvements

2. **DOCUMENT** in activity_tracker.md:
   - Each major action you take
   - Any errors or issues encountered
   - Solutions that worked

### Before Handoff
1. **FINALIZE** activity_tracker.md entry:
   - Mark status as completed
   - List all files created/modified
   - Add clear notes for next agent

2. **CLEAN** scratchpad.md:
   - Move important info to proper documentation
   - Leave only relevant notes for next agent
   - Remove outdated temporary content

## Benefits

### For Individual Agents
- 🧠 **Memory**: Don't lose important discoveries
- 🔄 **Recovery**: Know what to retry after failures
- 📚 **Learning**: Build on previous attempts

### For Team Coordination
- 🤝 **Handoffs**: Clear communication between agents
- 🚫 **No Duplication**: See what's already been tried
- 📈 **Progress Tracking**: Understand project state

### For Debugging
- 🐛 **Error History**: Track what went wrong
- ✅ **Success Patterns**: Identify what works
- 🔍 **Audit Trail**: Complete activity history

## Examples by Agent Type

### Backend Developer
```markdown
<!-- In scratchpad.md -->
## Database Schema Notes
- Users table needs email index for performance
- Consider adding created_at timestamps
- Password reset token expiry: 1 hour

<!-- In activity_tracker.md -->
### [2025-01-15 14:00] Backend Developer
**Task**: Implement password reset flow
**Actions**:
1. Created password reset token generator
2. Added email service integration
3. Created reset endpoints
**Issues**: SMTP credentials missing
**Resolution**: Added to .env.example with instructions
```

### Frontend Developer
```markdown
<!-- In scratchpad.md -->
## UI Component Notes
- Using Material-UI v5
- Theme colors: primary=#1976d2, secondary=#dc004e
- Form validation with react-hook-form

<!-- In activity_tracker.md -->
### [2025-01-15 15:30] Frontend Developer
**Task**: Build responsive navigation
**Actions**:
1. Created AppBar component
2. Added mobile drawer menu
3. Implemented route highlighting
**Learning**: MUI's useMediaQuery hook helpful for responsive design
```

### DevOps Agent
```markdown
<!-- In scratchpad.md -->
## Deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] SSL certificates installed
- [ ] Monitoring alerts set up

<!-- In activity_tracker.md -->
### [2025-01-15 16:45] DevOps Deployment
**Task**: Deploy to AWS
**Actions**:
1. Created Dockerfile
2. Set up GitHub Actions CI/CD
3. Configured AWS ECS
**Blockers**: Need AWS credentials from client
**Workaround**: Created detailed deployment guide for manual setup
```

## Important Rules

1. **ALWAYS** check these files when starting
2. **NEVER** delete historical entries in activity_tracker.md
3. **UPDATE** in real-time, not just at the end
4. **BE SPECIFIC** about file paths and error messages
5. **INCLUDE** timestamps for debugging
6. **SHARE** insights that would help other agents

These tools are MANDATORY for all agents to ensure smooth collaboration and prevent lost work!