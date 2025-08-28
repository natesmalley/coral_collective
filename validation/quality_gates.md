# Agent Force - Quality Gates & Validation Protocols

## Overview
Quality gates ensure each agent delivers expected outputs and maintains project integrity across handoffs.

## Universal Validation Rules

### 1. Output Completeness
Every agent must produce:
- ✅ All required deliverables listed in their specification
- ✅ Proper documentation in designated folders
- ✅ Handoff information for next agent
- ✅ Updated project context

### 2. Structural Compliance
All agents must:
- ✅ Follow established project structure
- ✅ Place files in correct directories
- ✅ Create README files for new folders
- ✅ Update main project documentation

### 3. Code Quality Standards
Development agents must ensure:
- ✅ TypeScript types properly defined
- ✅ No TypeScript errors
- ✅ ESLint rules pass
- ✅ Code is properly formatted
- ✅ Tests are included where applicable

## Agent-Specific Quality Gates

### Project Architect
**Must Deliver:**
- [ ] Complete project structure created
- [ ] Technical specification in /docs/architecture/
- [ ] Database schema if applicable
- [ ] Technology stack decisions documented
- [ ] README.md in every folder

**Validation Checks:**
```javascript
{
  "structure_complete": true,
  "documentation_exists": true,
  "tech_stack_defined": true,
  "handoff_ready": true
}
```

### Technical Writer (Phase 1)
**Must Deliver:**
- [ ] Requirements documentation complete
- [ ] API specifications defined
- [ ] Acceptance criteria documented
- [ ] Documentation templates created
- [ ] Standards established

**Validation Checks:**
```javascript
{
  "requirements_documented": true,
  "api_specs_complete": true,
  "templates_created": true,
  "standards_defined": true
}
```

### Backend Developer
**Must Deliver:**
- [ ] All API endpoints functional
- [ ] Database models implemented
- [ ] Authentication working
- [ ] Error handling complete
- [ ] API documentation updated

**Validation Checks:**
```javascript
{
  "endpoints_tested": true,
  "database_connected": true,
  "auth_implemented": true,
  "errors_handled": true,
  "docs_updated": true
}
```

### Frontend Developer
**Must Deliver:**
- [ ] UI components created
- [ ] Responsive design implemented
- [ ] API integration complete
- [ ] Accessibility standards met
- [ ] User flows working

**Validation Checks:**
```javascript
{
  "components_rendered": true,
  "responsive_design": true,
  "api_connected": true,
  "accessibility_checked": true,
  "user_flows_tested": true
}
```

### Mobile Developer
**Must Deliver:**
- [ ] Mobile app builds successfully
- [ ] Platform-specific features work
- [ ] Responsive to different screens
- [ ] Offline functionality if required
- [ ] App store ready if applicable

**Validation Checks:**
```javascript
{
  "ios_builds": true,
  "android_builds": true,
  "responsive_ui": true,
  "offline_capable": true,
  "store_requirements": true
}
```

### AI/ML Specialist
**Must Deliver:**
- [ ] AI models integrated
- [ ] Vector database configured
- [ ] API endpoints for AI features
- [ ] Error handling for AI failures
- [ ] Performance benchmarks met

**Validation Checks:**
```javascript
{
  "models_loaded": true,
  "vectordb_connected": true,
  "ai_endpoints_working": true,
  "fallbacks_implemented": true,
  "performance_acceptable": true
}
```

### Data Engineer
**Must Deliver:**
- [ ] Data pipelines operational
- [ ] ETL processes tested
- [ ] Data quality checks in place
- [ ] Monitoring configured
- [ ] Documentation complete

**Validation Checks:**
```javascript
{
  "pipelines_running": true,
  "etl_tested": true,
  "data_quality_verified": true,
  "monitoring_active": true,
  "docs_complete": true
}
```

### Database Specialist
**Must Deliver:**
- [ ] Schema optimized
- [ ] Indexes created
- [ ] Migrations ready
- [ ] Backup strategy defined
- [ ] Performance tuned

**Validation Checks:**
```javascript
{
  "schema_optimized": true,
  "indexes_appropriate": true,
  "migrations_tested": true,
  "backups_configured": true,
  "performance_validated": true
}
```

### Security Specialist
**Must Deliver:**
- [ ] Authentication secure
- [ ] Authorization implemented
- [ ] Data encryption active
- [ ] Security headers configured
- [ ] Vulnerability scan passed

**Validation Checks:**
```javascript
{
  "auth_secure": true,
  "rbac_implemented": true,
  "encryption_enabled": true,
  "headers_configured": true,
  "vulnerabilities_addressed": true
}
```

### Performance Engineer
**Must Deliver:**
- [ ] Performance benchmarks met
- [ ] Optimization implemented
- [ ] Load testing complete
- [ ] Monitoring configured
- [ ] CDN/caching setup

**Validation Checks:**
```javascript
{
  "benchmarks_met": true,
  "optimizations_applied": true,
  "load_tests_passed": true,
  "monitoring_active": true,
  "caching_configured": true
}
```

### API Designer
**Must Deliver:**
- [ ] API specification complete
- [ ] OpenAPI/GraphQL schema
- [ ] Authentication documented
- [ ] Rate limiting defined
- [ ] Client SDKs generated

**Validation Checks:**
```javascript
{
  "spec_complete": true,
  "schema_valid": true,
  "auth_documented": true,
  "rate_limits_defined": true,
  "sdks_generated": true
}
```

### QA & Testing
**Must Deliver:**
- [ ] Test suites complete
- [ ] Coverage targets met
- [ ] Bug reports filed
- [ ] Performance validated
- [ ] Accessibility tested

**Validation Checks:**
```javascript
{
  "unit_tests_pass": true,
  "integration_tests_pass": true,
  "coverage_adequate": true,
  "bugs_documented": true,
  "accessibility_verified": true
}
```

### DevOps & Deployment
**Must Deliver:**
- [ ] Application deployed
- [ ] CI/CD configured
- [ ] Monitoring active
- [ ] Backups configured
- [ ] Documentation updated

**Validation Checks:**
```javascript
{
  "deployment_successful": true,
  "cicd_working": true,
  "monitoring_active": true,
  "backups_verified": true,
  "docs_complete": true
}
```

## Validation Workflow

### Pre-Agent Validation
Before starting an agent:
1. Check prerequisites met
2. Verify dependencies available
3. Confirm previous phase complete
4. Validate project context

### During Agent Execution
While agent is working:
1. Monitor progress indicators
2. Check intermediate outputs
3. Validate against requirements
4. Track blockers and issues

### Post-Agent Validation
After agent completes:
1. Run quality gate checks
2. Validate all deliverables
3. Verify handoff information
4. Update project context
5. Clear for next agent

## Error Recovery Protocols

### Validation Failure Types

#### 1. Missing Prerequisites
**Error**: "Previous agent outputs not found"
**Recovery**:
- Return to previous agent
- Complete missing deliverables
- Re-run validation

#### 2. Incomplete Outputs
**Error**: "Required deliverables missing"
**Recovery**:
- Continue with current agent
- Complete missing items
- Re-validate

#### 3. Quality Standards Not Met
**Error**: "Code quality checks failed"
**Recovery**:
- Fix identified issues
- Run quality tools
- Re-validate

#### 4. Integration Failures
**Error**: "Components not integrating properly"
**Recovery**:
- Review integration points
- Fix compatibility issues
- Test integration again

### Recovery Decision Tree
```
Validation Failed?
├── Missing Prerequisites?
│   └── Return to Previous Agent
├── Incomplete Outputs?
│   └── Continue Current Agent
├── Quality Issues?
│   └── Fix and Re-validate
└── Integration Issues?
    └── Debug and Fix Integration
```

## Automated Validation Commands

### Check Current Phase
```bash
@validate current
# Returns: Current phase validation status
```

### Validate Specific Agent
```bash
@validate agent backend_developer
# Returns: Validation results for backend developer outputs
```

### Run Full Validation
```bash
@validate all
# Returns: Complete project validation report
```

### Check Dependencies
```bash
@validate dependencies frontend_developer
# Returns: Whether prerequisites for frontend are met
```

## Validation Report Format

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "project_phase": "development",
  "agent": "backend_developer",
  "validation_status": "passed",
  "checks": {
    "endpoints_tested": true,
    "database_connected": true,
    "auth_implemented": true,
    "errors_handled": true,
    "docs_updated": true
  },
  "warnings": [],
  "errors": [],
  "next_agent_ready": true,
  "handoff_complete": true
}
```

## Quality Metrics

### Success Indicators
- ✅ 100% required deliverables complete
- ✅ No blocking errors
- ✅ Handoff information provided
- ✅ Next agent prerequisites met
- ✅ Documentation updated

### Warning Indicators
- ⚠️ Optional deliverables incomplete
- ⚠️ Performance below optimal
- ⚠️ Test coverage below target
- ⚠️ Minor quality issues

### Failure Indicators
- ❌ Required deliverables missing
- ❌ Blocking errors present
- ❌ Integration broken
- ❌ Security vulnerabilities
- ❌ No handoff information

## Continuous Improvement

### Validation Feedback Loop
1. Track validation failures
2. Identify common patterns
3. Update agent prompts
4. Improve quality gates
5. Refine recovery protocols

### Metrics to Track
- Agent success rate
- Common failure points
- Recovery success rate
- Time to resolution
- User satisfaction

## Summary

Quality gates ensure:
- ✅ Consistent deliverables
- ✅ Smooth handoffs
- ✅ Early error detection
- ✅ Maintained standards
- ✅ Project success