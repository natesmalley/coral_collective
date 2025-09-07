#!/usr/bin/env python3
"""
CoralCollective Integrity Checker
Ensures framework files haven't been modified
"""

import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime

class CoralIntegrityChecker:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.checksums_file = self.base_path / '.coral' / 'checksums.json'
        self.protected_files = self.load_protected_files()
        self.checksums = self.load_checksums()
        
    def load_protected_files(self):
        """Load list of protected files"""
        protected = []
        
        # Core files
        protected.extend([
            'agent_runner.py',
            'agent_prompt_service.py', 
            'project_manager.py',
            'claude_interface.py',
            'subagent_registry.py'
        ])
        
        # All agent definitions
        agents_dir = self.base_path / 'agents'
        if agents_dir.exists():
            protected.extend([
                str(f.relative_to(self.base_path))
                for f in agents_dir.rglob('*.md')
            ])
        
        # MCP files
        mcp_files = [
            'mcp/mcp_client.py',
            'mcp/configs/mcp_config.yaml'
        ]
        protected.extend(mcp_files)
        
        # Memory system
        memory_dir = self.base_path / 'memory'
        if memory_dir.exists():
            protected.extend([
                str(f.relative_to(self.base_path))
                for f in memory_dir.glob('*.py')
            ])
        
        # Scripts
        protected.extend([
            'coral_drop.sh',
            'deploy_coral.sh',
            'coral-init.sh',
            'start.sh'
        ])
        
        return protected
    
    def load_checksums(self):
        """Load existing checksums"""
        if self.checksums_file.exists():
            with open(self.checksums_file, 'r') as f:
                return json.load(f)
        return {}
    
    def calculate_checksum(self, filepath):
        """Calculate SHA256 checksum of a file"""
        file_path = self.base_path / filepath
        if not file_path.exists():
            return None
            
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def check_integrity(self):
        """Check integrity of all protected files"""
        violations = []
        missing = []
        
        for filepath in self.protected_files:
            current_checksum = self.calculate_checksum(filepath)
            
            if current_checksum is None:
                missing.append(filepath)
                continue
                
            if filepath in self.checksums:
                if current_checksum != self.checksums[filepath]:
                    violations.append(filepath)
        
        return violations, missing
    
    def update_checksums(self):
        """Update checksums for all protected files"""
        new_checksums = {}
        
        for filepath in self.protected_files:
            checksum = self.calculate_checksum(filepath)
            if checksum:
                new_checksums[filepath] = checksum
        
        # Save checksums
        self.checksums_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.checksums_file, 'w') as f:
            json.dump(new_checksums, f, indent=2)
        
        return new_checksums
    
    def generate_report(self, violations, missing):
        """Generate integrity report"""
        report = []
        report.append("=" * 60)
        report.append("🪸 CoralCollective Integrity Check")
        report.append("=" * 60)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append("")
        
        if not violations and not missing:
            report.append("✅ All framework files are intact!")
            report.append("No unauthorized modifications detected.")
        else:
            report.append("⚠️  INTEGRITY VIOLATIONS DETECTED!")
            report.append("")
            
            if violations:
                report.append("❌ Modified Files (DO NOT EDIT THESE):")
                for file in violations:
                    report.append(f"   - {file}")
                report.append("")
                report.append("Action Required:")
                report.append("1. Revert these files to original state")
                report.append("2. Use agents via './coral run' instead")
                report.append("")
            
            if missing:
                report.append("⚠️  Missing Files:")
                for file in missing:
                    report.append(f"   - {file}")
                report.append("")
                report.append("Action Required:")
                report.append("1. Reinstall CoralCollective")
                report.append("2. Run: ./coral-init.sh")
        
        report.append("")
        report.append("Remember:")
        report.append("• CoralCollective is a FRAMEWORK to USE")
        report.append("• Never modify framework files")
        report.append("• Use agents through the CLI interface")
        report.append("• Import modules, don't edit them")
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)

def main():
    """Main entry point"""
    checker = CoralIntegrityChecker()
    
    # Parse arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--update':
            print("🔄 Updating checksums...")
            checksums = checker.update_checksums()
            print(f"✅ Updated checksums for {len(checksums)} files")
            return 0
        elif sys.argv[1] == '--help':
            print("Usage:")
            print("  python coral-check.py        # Check integrity")
            print("  python coral-check.py --update # Update checksums")
            return 0
    
    # Check integrity
    violations, missing = checker.check_integrity()
    report = checker.generate_report(violations, missing)
    
    print(report)
    
    # Return error code if violations found
    if violations or missing:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())