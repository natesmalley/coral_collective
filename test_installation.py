#!/usr/bin/env python3
"""
Test script to verify CoralCollective installation and components
"""

import sys
import os
from pathlib import Path

def test_installation():
    """Run installation tests."""
    print("🪸 CoralCollective Installation Test")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check directory structure
    print("\n1. Checking directory structure...")
    required_dirs = ['agents', 'config', 'docs', 'mcp', 'tools', 'coral_collective']
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"  ✓ {dir_name}/ exists")
            tests_passed += 1
        else:
            print(f"  ✗ {dir_name}/ missing")
            tests_failed += 1
    
    # Test 2: Check core files
    print("\n2. Checking core files...")
    core_files = [
        'agent_runner.py',
        'project_manager.py', 
        'agent_prompt_service.py',
        'requirements.txt',
        'setup.py',
        'Dockerfile',
        'docker-compose.yml'
    ]
    for file_name in core_files:
        if Path(file_name).exists():
            print(f"  ✓ {file_name} exists")
            tests_passed += 1
        else:
            print(f"  ✗ {file_name} missing")
            tests_failed += 1
    
    # Test 3: Check configuration files
    print("\n3. Checking configuration files...")
    config_files = [
        'config/agents.yaml',
        'config/model_assignments_2026.yaml',
        '.env.example'
    ]
    for file_name in config_files:
        if Path(file_name).exists():
            print(f"  ✓ {file_name} exists")
            tests_passed += 1
        else:
            print(f"  ✗ {file_name} missing")
            tests_failed += 1
    
    # Test 4: Check agent files
    print("\n4. Checking agent markdown files...")
    try:
        import yaml
        with open('config/agents.yaml', 'r') as f:
            config = yaml.safe_load(f)
            agents = config.get('agents', {})
            
        agents_ok = 0
        agents_missing = 0
        for agent_id, agent_config in agents.items():
            prompt_path = agent_config.get('prompt_path', '')
            if prompt_path and Path(prompt_path).exists():
                agents_ok += 1
            else:
                agents_missing += 1
                
        print(f"  ✓ {agents_ok} agent files found")
        if agents_missing > 0:
            print(f"  ✗ {agents_missing} agent files missing")
            tests_failed += 1
        else:
            tests_passed += 1
            
    except Exception as e:
        print(f"  ✗ Error checking agents: {e}")
        tests_failed += 1
    
    # Test 5: Check deployment scripts
    print("\n5. Checking deployment scripts...")
    scripts = ['start.sh', 'coral_drop.sh', 'deploy_coral.sh']
    for script in scripts:
        if Path(script).exists():
            print(f"  ✓ {script} exists")
            tests_passed += 1
        else:
            print(f"  ✗ {script} missing")
            tests_failed += 1
    
    # Test 6: Check package structure
    print("\n6. Checking Python package structure...")
    package_files = [
        'coral_collective/__init__.py',
        'coral_collective/tools/__init__.py',
        'coral_collective/tools/project_state.py',
        'coral_collective/config/__init__.py',
        'coral_collective/cli/__init__.py',
        'coral_collective/cli/main.py'
    ]
    for file_name in package_files:
        if Path(file_name).exists():
            print(f"  ✓ {file_name} exists")
            tests_passed += 1
        else:
            print(f"  ✗ {file_name} missing")
            tests_failed += 1
    
    # Test 7: Check documentation
    print("\n7. Checking documentation...")
    docs = [
        'README.md',
        'docs/USER_GUIDE.md',
        'docs/ARCHITECTURE.md',
        'docs/API_REFERENCE.md',
        'INTEGRATION.md'
    ]
    for doc in docs:
        if Path(doc).exists():
            print(f"  ✓ {doc} exists")
            tests_passed += 1
        else:
            print(f"  ✗ {doc} missing")
            tests_failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed} passed, {tests_failed} failed")
    
    if tests_failed == 0:
        print("\n✅ All tests passed! CoralCollective is ready for deployment.")
        print("\nNext steps:")
        print("1. Create virtual environment: python3 -m venv venv")
        print("2. Activate it: source venv/bin/activate")
        print("3. Install dependencies: pip install -r requirements.txt")
        print("4. Run: python agent_runner.py")
    else:
        print(f"\n⚠️  {tests_failed} tests failed. Please fix the issues above.")
        
    return tests_failed == 0

if __name__ == '__main__':
    success = test_installation()
    sys.exit(0 if success else 1)