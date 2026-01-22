#!/bin/bash
# Script to set up branch protection rules for CoralCollective
# Run this after making the repository public

set -e

REPO="natesmalley/coral_collective"
echo "🔒 Setting up branch protection for $REPO"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it first."
    echo "   Visit: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI. Run: gh auth login"
    exit 1
fi

echo "📋 Setting up main branch protection..."

# Main branch protection
gh api -X PUT "repos/$REPO/branches/main/protection" \
  --input - << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Code Quality Checks",
      "Test Python 3.10 on ubuntu-latest", 
      "Test Python 3.10 on windows-latest",
      "Test Python 3.10 on macos-latest",
      "Dependency Vulnerability Scan",
      "Bandit Security Linter",
      "Safety Vulnerability Check"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "require_last_push_approval": false,
    "bypass_pull_request_allowances": {
      "users": [],
      "teams": [],
      "apps": []
    }
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": true,
  "required_linear_history": false
}
EOF

echo "✅ Main branch protection enabled"

# Enable security features
echo "🛡️ Enabling security features..."

# Enable vulnerability alerts
gh api -X PUT "repos/$REPO/vulnerability-alerts" 2>/dev/null || echo "⚠️ Vulnerability alerts may already be enabled"

# Enable automated security fixes
gh api -X PUT "repos/$REPO/automated-security-fixes" 2>/dev/null || echo "⚠️ Automated security fixes may already be enabled"

# Enable GitHub Advanced Security features (if available)
echo "🔍 Attempting to enable advanced security features..."
gh api -X PATCH "repos/$REPO" \
  --field security_and_analysis='{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}' \
  2>/dev/null || echo "⚠️ Some security features require GitHub Advanced Security license"

echo ""
echo "📊 Repository Security Summary:"
echo "================================"
gh api "repos/$REPO" --jq '.name, "Private: " + (.private|tostring), "Security Policy: " + (.security_and_analysis.secret_scanning.status // "unknown")'

echo ""
echo "🎯 Next Steps:"
echo "1. Go to Settings > Code security and analysis"
echo "2. Enable 'Dependency graph' if not already enabled"
echo "3. Enable 'Dependabot alerts'"
echo "4. Enable 'Dependabot security updates'"
echo "5. Enable 'Code scanning' with CodeQL"
echo "6. Review and merge the security PR"

echo ""
echo "✅ Branch protection setup complete!"