# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of CoralCollective seriously. If you have discovered a security vulnerability, we appreciate your help in disclosing it to us responsibly.

### How to Report

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities by emailing:
- **Email**: security@coralcollective.dev (or create a private security advisory on GitHub)
- **Response Time**: We aim to respond within 48 hours
- **Resolution**: We aim to provide a fix within 7-14 days depending on severity

### What to Include

Please provide:
1. Description of the vulnerability
2. Steps to reproduce the issue
3. Potential impact
4. Suggested fix (if any)
5. Your contact information

### Security Vulnerability Response

When we receive a security vulnerability report:
1. **Acknowledge**: We'll confirm receipt within 48 hours
2. **Assess**: We'll investigate and determine the impact
3. **Fix**: We'll develop and test a fix
4. **Release**: We'll release the fix and publish a security advisory
5. **Credit**: We'll credit you for the discovery (unless you prefer to remain anonymous)

## Security Measures

### Code Security
- ✅ Automated security scanning via GitHub Actions
- ✅ Dependency vulnerability scanning (pip-audit, Safety, Dependabot)
- ✅ Static code analysis (Bandit, CodeQL)
- ✅ Secret scanning (Trufflehog)
- ✅ Container scanning (Trivy)
- ✅ OWASP dependency checks

### Development Practices
- ✅ Code review recommended (self-review acceptable for maintainer)
- ✅ Signed commits recommended
- ✅ Protected main branch (maintainer can override when necessary)
- ✅ Automated testing on multiple platforms
- ✅ Regular dependency updates

### Deployment Policy
- ✅ Maintainer (@natesmalley) has deployment authority
- ✅ Self-deployment allowed for bug fixes and minor updates
- ✅ Major changes benefit from peer review but not required
- ✅ Emergency hotfixes can bypass review process

### API Security
- ⚠️ Never commit API keys or secrets
- ⚠️ Use environment variables for sensitive data
- ⚠️ Rotate keys regularly
- ⚠️ Use least-privilege access

## Security Features

### For AI Agent Operations
- **Sandboxed Execution**: Agents operate in isolated environments
- **Permission Management**: Agent-specific tool permissions
- **Input Validation**: All agent inputs are validated
- **Output Sanitization**: Agent outputs are sanitized before use
- **Audit Logging**: All agent actions are logged

### For MCP Integration
- **Server Isolation**: Each MCP server runs in isolation
- **Permission Scoping**: Fine-grained permissions per agent
- **Command Blocking**: Dangerous commands are blocked
- **Path Restrictions**: File system access is restricted

## Security Checklist for Contributors

Before submitting code:
- [ ] No hardcoded secrets or API keys
- [ ] No sensitive data in logs
- [ ] Input validation for user data
- [ ] Error messages don't reveal sensitive info
- [ ] Dependencies are up-to-date
- [ ] Security tests pass

## Security Tools

### Automated Scanning
```bash
# Run security scans locally
pip install bandit safety pip-audit

# Scan for security issues
bandit -r coral_collective/
safety check -r requirements.txt
pip-audit -r requirements.txt
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Security Advisories

Security advisories will be published in:
- GitHub Security Advisories
- CHANGELOG.md
- Release notes

## Contact

- **Security Team**: security@coralcollective.dev
- **General Issues**: Use GitHub Issues (non-security)
- **Private Disclosure**: Use GitHub Security Advisories

## Recognition

We thank the following security researchers for responsibly disclosing vulnerabilities:
- *Your name could be here!*

---

*Last updated: January 2026*