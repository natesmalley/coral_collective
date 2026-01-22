# Security Checklist for CoralCollective

## Repository Settings (GitHub UI)

### ✅ General Settings
- [ ] Repository is PUBLIC (for full security features)
- [ ] Issues are enabled
- [ ] Wiki is disabled (unless needed)
- [ ] Projects are enabled
- [ ] Preserve this repository is enabled
- [ ] Include all branches for preservation

### 🔒 Code Security and Analysis
Navigate to: Settings → Code security and analysis

#### Dependency Management
- [ ] **Dependency graph** - ENABLED
- [ ] **Dependabot alerts** - ENABLED
- [ ] **Dependabot security updates** - ENABLED
- [ ] **Grouped security updates** - ENABLED

#### Code Scanning
- [ ] **Code scanning** - SET UP
  - [ ] CodeQL analysis configured
  - [ ] Upload to GitHub Security tab enabled
  - [ ] Scheduled scans enabled (weekly)

#### Secret Scanning
- [ ] **Secret scanning** - ENABLED
- [ ] **Push protection** - ENABLED
- [ ] **Validity checks** - ENABLED

#### Security Advisories
- [ ] **Private vulnerability reporting** - ENABLED

### 🛡️ Branch Protection Rules
Navigate to: Settings → Branches

#### Main Branch
- [ ] **Require pull request before merging**
  - [ ] Required approvals: 1
  - [ ] Dismiss stale reviews
  - [ ] Require review from CODEOWNERS
  - [ ] Require approval of most recent reviewable push
- [ ] **Require status checks**
  - [ ] Require branches up to date
  - [ ] Required checks:
    - [ ] Code Quality Checks
    - [ ] Test Python 3.10 on ubuntu-latest
    - [ ] Dependency Vulnerability Scan
    - [ ] Bandit Security Linter
    - [ ] Safety Vulnerability Check
- [ ] **Require conversation resolution**
- [ ] **Require signed commits** (optional but recommended)
- [ ] **Include administrators**
- [ ] **Restrict force pushes**
- [ ] **Restrict deletions**

### 📋 GitHub Actions Settings
Navigate to: Settings → Actions → General

- [ ] **Actions permissions**: Allow all actions
- [ ] **Workflow permissions**: Read and write
- [ ] **Pull requests from forks**: Require approval
- [ ] **GitHub Actions cache**: Enabled

## Security Workflows

### ✅ Automated Security Scanning
File: `.github/workflows/security.yml`

- [ ] **Dependency scanning**
  - [ ] pip-audit
  - [ ] Safety
  - [ ] OWASP Dependency Check
- [ ] **Code security**
  - [ ] Bandit
  - [ ] CodeQL
- [ ] **Container security**
  - [ ] Trivy
- [ ] **Secret detection**
  - [ ] Trufflehog
- [ ] **Supply chain**
  - [ ] Dependabot

### ✅ CI/CD Security
File: `.github/workflows/ci.yml`

- [ ] Tests run on multiple OS (Ubuntu, Windows, macOS)
- [ ] Tests run on multiple Python versions
- [ ] Code formatting checks (Black)
- [ ] Linting checks (Ruff)
- [ ] Type checking (MyPy)
- [ ] Coverage reporting

## Local Development Security

### 🔐 Pre-commit Hooks
File: `.pre-commit-config.yaml`

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

- [ ] Secret detection
- [ ] Security scanning (Bandit)
- [ ] Code formatting
- [ ] Type checking
- [ ] YAML/JSON validation
- [ ] Shell script validation

### 🔑 Environment Variables
File: `.env.example`

- [ ] Never commit `.env` files
- [ ] Use `.env.example` as template
- [ ] Rotate API keys regularly
- [ ] Use least-privilege access

## Documentation

### 📚 Security Documentation
- [ ] **SECURITY.md** - Security policy and vulnerability reporting
- [ ] **CODEOWNERS** - Code ownership for reviews
- [ ] **LICENSE** - Open source license
- [ ] **CONTRIBUTING.md** - Contribution guidelines
- [ ] **README.md** - Security badges and info

## Monitoring and Alerts

### 📊 GitHub Security Dashboard
Navigate to: Security tab

- [ ] Review security overview regularly
- [ ] Monitor vulnerability alerts
- [ ] Check code scanning alerts
- [ ] Review secret scanning alerts
- [ ] Track dependency updates

### 🔔 Notifications
Navigate to: Settings → Notifications

- [ ] Security alerts: Email + Web
- [ ] Vulnerability alerts: Email + Web
- [ ] Code scanning alerts: Email + Web

## Regular Maintenance

### Weekly
- [ ] Review Dependabot PRs
- [ ] Check security alerts
- [ ] Update dependencies

### Monthly
- [ ] Review security policy
- [ ] Audit access permissions
- [ ] Review branch protection rules
- [ ] Check for outdated actions

### Quarterly
- [ ] Security audit
- [ ] Rotate API keys
- [ ] Review CODEOWNERS
- [ ] Update security documentation

## Emergency Response

### 🚨 If Security Incident Occurs
1. [ ] Assess the impact
2. [ ] Revoke compromised credentials
3. [ ] Fix the vulnerability
4. [ ] Release security patch
5. [ ] Publish security advisory
6. [ ] Notify affected users
7. [ ] Document lessons learned

## Quick Setup Script

After making repository public, run:
```bash
# Apply branch protection and security settings
.github/scripts/setup-branch-protection.sh
```

## Security Contacts

- **Security Team**: security@coralcollective.dev
- **GitHub Security Advisories**: [Create Advisory](https://github.com/natesmalley/coral_collective/security/advisories/new)
- **Issues (non-security)**: [GitHub Issues](https://github.com/natesmalley/coral_collective/issues)

---

*Last updated: January 2026*
*Review frequency: Monthly*