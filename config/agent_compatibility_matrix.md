# Agent Compatibility Matrix

## Overview
This matrix defines which agents work well together, dependencies, conflicts, and optimal sequencing for different project scenarios.

## Agent Compatibility Chart

| Agent | Works Well With | Dependencies | Conflicts | Parallel Safe |
|-------|-----------------|--------------|-----------|---------------|
| **Project Architect** | All agents | None | None | No - Must run first |
| **Technical Writer** | All agents | Project Architect | None | Yes - With development |
| **Backend Developer** | Frontend, Mobile, Data Engineer | Technical Writer, API Designer | None | Yes - With Frontend |
| **Frontend Developer** | Backend, Mobile, Performance | Backend (for API), API Designer | None | Yes - With Backend |
| **Mobile Developer** | Backend, Frontend | Backend (for API), API Designer | None | Yes - After API defined |
| **AI/ML Specialist** | Data Engineer, Backend | Data Engineer, Database Specialist | None | Yes - With Backend |
| **Data Engineer** | Database Specialist, Backend, AI/ML | Database Specialist | None | Yes - With Backend |
| **Database Specialist** | Backend, Data Engineer | Project Architect | None | No - Before data work |
| **API Designer** | Backend, Frontend, Mobile | Project Architect | None | No - Before development |
| **Security Specialist** | All development agents | Some development complete | None | Yes - Continuous |
| **Performance Engineer** | Frontend, Backend, Database | Development complete | None | Yes - After development |
| **QA & Testing** | All agents | Development agents | None | Yes - Continuous |
| **DevOps & Deployment** | All agents | QA & Testing | Active development | No - After testing |

## Project-Specific Combinations

### Web Applications

#### Optimal Sequence
```
1. Project Architect
2. API Designer + Technical Writer (parallel)
3. Database Specialist
4. Backend + Frontend (parallel)
5. Security Specialist
6. Performance Engineer
7. QA & Testing
8. DevOps & Deployment
```

#### Dependencies
- Frontend requires Backend API endpoints
- Performance requires both Backend and Frontend
- DevOps requires successful QA

### Mobile Applications

#### Optimal Sequence
```
1. Project Architect
2. API Designer + Technical Writer (parallel)
3. Backend Developer
4. Mobile Developer + Frontend (for web) (parallel)
5. Performance Engineer
6. QA & Testing
7. DevOps & Deployment
```

#### Dependencies
- Mobile requires Backend API
- Mobile and Frontend can work in parallel
- Performance focuses on API and mobile optimization

### Microservices

#### Optimal Sequence
```
1. Project Architect
2. API Designer
3. Database Specialist + Data Engineer (parallel)
4. Multiple Backend Developers (parallel)
5. API Gateway configuration
6. Security Specialist
7. Performance Engineer
8. QA & Testing
9. DevOps & Deployment
```

#### Dependencies
- Each service can have independent Backend Developer
- API Designer crucial for service contracts
- Performance Engineer essential for distributed systems

### Data Pipelines

#### Optimal Sequence
```
1. Project Architect
2. Database Specialist
3. Data Engineer + Backend (parallel)
4. AI/ML Specialist (if needed)
5. Performance Engineer
6. QA & Testing
7. DevOps & Deployment
```

#### Dependencies
- Data Engineer requires Database design
- AI/ML requires Data Engineer infrastructure
- Performance critical for data processing

### AI/ML Applications

#### Optimal Sequence
```
1. Project Architect
2. Technical Writer Phase 1
3. Data Engineer + Database Specialist (parallel)
4. AI/ML Specialist
5. Backend + Frontend (parallel)
6. Performance Engineer
7. Security Specialist
8. QA & Testing
9. DevOps & Deployment
```

#### Dependencies
- AI/ML requires Data infrastructure
- Frontend requires AI endpoints
- Performance crucial for AI response times

## Parallel Execution Rules

### Safe to Run in Parallel

#### Group 1: Planning Phase
- Technical Writer + API Designer
- Can document while designing APIs

#### Group 2: Infrastructure
- Database Specialist + Data Engineer
- Can design schema while building pipelines

#### Group 3: Development
- Backend + Frontend (after API contracts)
- Multiple Backend (for microservices)
- Backend + Mobile (after API contracts)

#### Group 4: Enhancement
- Security + Performance
- Can optimize while securing

#### Group 5: Continuous
- QA + Technical Writer Phase 2
- Testing while documenting

### Never Run in Parallel

#### Sequential Requirements
1. Project Architect → All others
2. API Designer → Development agents
3. Database Specialist → Data Engineer
4. Development → Performance Engineer
5. QA Testing → DevOps Deployment

## Conditional Agent Selection

### When to Add Agents

| Condition | Add Agent | Reason |
|-----------|-----------|---------|
| User authentication required | Security Specialist | Early in development |
| High traffic expected | Performance Engineer | After development |
| Mobile app needed | Mobile Developer | Instead of/with Frontend |
| AI features required | AI/ML Specialist | After data infrastructure |
| Complex data requirements | Data Engineer | With Database Specialist |
| Microservices architecture | Multiple Backend | Parallel development |
| Compliance requirements | Security Specialist | Throughout development |
| Public API | API Designer | Before any development |

### When to Skip Agents

| Condition | Skip Agent | Alternative |
|-----------|------------|-------------|
| No UI needed | Frontend Developer | Focus on Backend |
| Simple database | Database Specialist | Backend handles it |
| Internal tool only | Performance Engineer | Basic optimization only |
| Proof of concept | Security Specialist | Add later for production |
| Static website | Backend Developer | Frontend only |
| No mobile needed | Mobile Developer | Responsive web design |

## Agent Communication Patterns

### Information Flow

```
Project Architect
    ├→ Technical Writer (requirements)
    ├→ API Designer (structure)
    └→ Database Specialist (data model)
        ├→ Backend Developer (implementation)
        ├→ Frontend Developer (UI)
        └→ Mobile Developer (apps)
            ├→ Security Specialist (hardening)
            ├→ Performance Engineer (optimization)
            └→ QA & Testing (validation)
                └→ DevOps & Deployment (release)
```

### Feedback Loops

```
QA & Testing ←→ All Development Agents
Security Specialist ←→ All Agents
Performance Engineer ←→ Backend + Frontend + Database
Technical Writer ←→ All Agents (documentation)
```

## Conflict Resolution

### Common Conflicts

| Conflict | Resolution |
|----------|------------|
| Backend vs Frontend on API design | API Designer mediates |
| Security vs Performance tradeoffs | Prioritize security, optimize after |
| Mobile vs Web priority | Parallel development when possible |
| Database design disagreements | Database Specialist has authority |
| Testing vs Deployment timeline | Testing must complete first |

### Escalation Path

1. **Agent Level**: Try to resolve within agent scope
2. **Architect Level**: Return to Project Architect for decisions
3. **User Level**: Ask user for business priority
4. **Default**: Follow security > functionality > performance

## Success Patterns

### High Success Combinations

1. **API Designer → Backend → Frontend**
   - Clear contracts prevent integration issues

2. **Database Specialist → Data Engineer → AI/ML**
   - Proper data foundation ensures AI success

3. **Security throughout development**
   - Continuous security prevents late-stage issues

4. **Performance after development**
   - Optimize working code rather than premature optimization

5. **QA parallel with development**
   - Catch issues early, continuous testing

### Anti-Patterns to Avoid

1. **Frontend before Backend**
   - Leads to API mismatches

2. **DevOps before QA**
   - Deploying untested code

3. **Performance before functionality**
   - Premature optimization

4. **Skipping API Designer for complex systems**
   - Integration nightmares

5. **Delaying Security to end**
   - Expensive to fix vulnerabilities

## Optimization Strategies

### For Speed (MVP)
- Minimize agents: Architect → Backend → Frontend → DevOps
- Skip: Performance, extensive QA
- Add later: Security, optimization

### For Quality (Enterprise)
- Use all relevant agents
- Emphasize: Security, QA, Performance
- Multiple iterations: Plan → Build → Test → Refine

### For Scale (High Traffic)
- Essential: Performance Engineer, Database Specialist
- Early: Caching strategy, CDN setup
- Continuous: Load testing, monitoring

### For Compliance (Regulated)
- Early: Security Specialist
- Throughout: Documentation, audit trails
- Extensive: QA & Testing with compliance focus

## Summary

The compatibility matrix ensures:
- ✅ Optimal agent sequencing
- ✅ Efficient parallel execution
- ✅ Clear dependencies
- ✅ Conflict avoidance
- ✅ Project success