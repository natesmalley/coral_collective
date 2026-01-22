# Scratchpad & Activity Tracker Guide

## Overview

Every CoralCollective project now includes two critical coordination files that ALL agents must use:

1. **scratchpad.md** - Shared working document
2. **activity_tracker.md** - Complete activity log

These files solve the coordination problems identified in the FinTech Retirement Calculator feedback.

## Why These Files Matter

### Problems They Solve
- ❌ **Before**: Agents duplicated work
- ✅ **After**: Activity tracker shows what's been done

- ❌ **Before**: Lost context between agents
- ✅ **After**: Scratchpad preserves discoveries

- ❌ **Before**: No retry intelligence
- ✅ **After**: Activity log shows what failed and why

- ❌ **Before**: Poor handoffs
- ✅ **After**: Clear notes for next agent

## File Purposes

### 📝 scratchpad.md
**Purpose**: Temporary working space and inter-agent communication

**Contents**:
- Quick notes and observations
- Questions for other agents
- API endpoints discovered
- Database schema decisions
- Environment variables needed
- Integration points
- TODOs
- Draft code snippets

**Lifecycle**:
1. Project Architect creates it
2. Each agent reads it on start
3. Each agent updates during work
4. Each agent cleans before handoff
5. Keeps only relevant info

### 📊 activity_tracker.md
**Purpose**: Complete audit trail of all agent activities

**Contents**:
- Timestamp and agent name
- Task description
- Actions taken (numbered)
- Files created/modified
- Issues encountered
- Resolutions found
- Results (success/failure)
- Notes for next agent

**Lifecycle**:
1. Project Architect creates with first entry
2. Each agent adds entry when starting
3. Updates during work with progress
4. Finalizes entry when complete
5. NEVER delete old entries

## Usage Examples

### Backend Developer Using Scratchpad
```markdown
## API Endpoints Created
- POST /api/auth/login - JWT authentication
- POST /api/auth/register - User registration  
- GET /api/users/:id - Get user profile (requires auth)

## Questions for Frontend
- Using JWT or cookies for auth storage?
- Need refresh token implementation?

## Database Notes
- Users table has email unique index
- Passwords hashed with bcrypt (10 rounds)
```

### Frontend Developer Activity Entry
```markdown
### [2025-01-15 14:30] Frontend Developer
**Task**: Create login and registration UI
**Status**: ✅ Completed
**Actions Taken**:
1. Created LoginForm component with Material-UI
2. Added form validation with react-hook-form
3. Integrated with /api/auth/login endpoint
4. Added JWT token storage in localStorage
5. Created ProtectedRoute component

**Files Created**:
- `/src/components/auth/LoginForm.tsx`
- `/src/components/auth/RegisterForm.tsx`
- `/src/components/routing/ProtectedRoute.tsx`
- `/src/hooks/useAuth.ts`

**Issues Encountered**:
- CORS error with API calls
- Resolution: Added proxy to package.json

**Results**: 
✅ Authentication flow working end-to-end

**Notes for Next Agent**:
- JWT token stored in localStorage
- Auth context provider wraps entire app
- Protected routes redirect to /login
```

## Integration with Project State Manager

The activity_tracker.md complements the programmatic `ProjectStateManager`:

- **activity_tracker.md**: Human-readable log
- **project_state.yaml**: Machine-readable state
- Both updated in parallel
- activity_tracker has more detail
- project_state enables automation

## Best Practices

### DO ✅
- Update in real-time, not just at end
- Be specific about file paths
- Include error messages verbatim
- Add timestamps to entries
- Share insights that help others
- Clean scratchpad before handoff

### DON'T ❌
- Delete activity history
- Leave outdated info in scratchpad
- Skip logging failures
- Assume others know your decisions
- Forget to read on start

## Workflow Integration

### 1. Project Start (Architect)
```markdown
Creates both files with initial content
Logs structure decisions in activity_tracker
Notes tech stack in scratchpad
```

### 2. Backend Development
```markdown
Reads scratchpad for requirements
Logs each API endpoint in activity_tracker
Notes integration points in scratchpad
```

### 3. Frontend Development
```markdown
Reads scratchpad for API endpoints
Logs UI components in activity_tracker
Notes state management in scratchpad
```

### 4. Testing
```markdown
Reads activity_tracker for what to test
Logs test results in activity_tracker
Notes failing tests in scratchpad
```

### 5. Deployment
```markdown
Reads scratchpad for config needs
Logs deployment steps in activity_tracker
Notes URLs and access in scratchpad
```

## Success Metrics

With these files properly used:
- 🎯 **Zero duplicate work** - Check activity first
- 🔄 **Smooth handoffs** - Context preserved
- 🐛 **Faster debugging** - Full history available
- 📈 **Learning system** - Builds on past attempts
- 🤝 **Better coordination** - Clear communication

## Implementation Status

✅ **Project Architect** creates both files
✅ **All agents** have documentation to use them
✅ **Templates** available in `/templates/`
✅ **Non-interactive mode** supports them
✅ **State manager** integrates with them

## Example: Full Workflow

1. **Architect** creates project:
   - ✅ Creates scratchpad.md
   - ✅ Creates activity_tracker.md
   - ✅ Logs first entry

2. **Backend** builds API:
   - ✅ Reads scratchpad
   - ✅ Logs progress
   - ✅ Notes endpoints

3. **Frontend** builds UI:
   - ✅ Finds API in scratchpad
   - ✅ Logs components
   - ✅ Notes auth method

4. **QA** tests:
   - ✅ Sees all changes in activity_tracker
   - ✅ Knows what to test
   - ✅ Logs results

5. **DevOps** deploys:
   - ✅ Gets config from scratchpad
   - ✅ Logs deployment
   - ✅ Documents access

## Result

**Coordination Score: 5/10 → 9/10** 🎉

These simple files create a powerful coordination system that ensures no work is lost and every agent builds on previous work effectively!