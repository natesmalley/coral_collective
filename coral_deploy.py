#!/usr/bin/env python3
"""
CoralCollective Smart Deployment System
Intelligent deployment with minimal footprint and automatic optimization
"""

import os
import sys
import json
import shutil
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import hashlib
import zipfile
import tempfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentStrategy:
    """Deployment strategy configurations"""
    
    MINIMAL = {
        'name': 'minimal',
        'description': 'Core agents only, minimal footprint (~5MB)',
        'includes': ['core/', 'config/agents.yaml', 'claude_interface.py'],
        'agents': ['project_architect', 'backend_developer', 'frontend_developer']
    }
    
    STANDARD = {
        'name': 'standard',
        'description': 'Common agents and tools (~15MB)',
        'includes': ['core/', 'agents/', 'config/', 'tools/', '*.py'],
        'agents': 'all',
        'excludes': ['tests/', 'examples/', 'docs/']
    }
    
    FULL = {
        'name': 'full',
        'description': 'Complete framework with all features (~30MB)',
        'includes': ['*'],
        'excludes': ['venv/', '__pycache__/', '*.pyc', '.git/']
    }
    
    IDE_OPTIMIZED = {
        'name': 'ide_optimized',
        'description': 'Optimized for IDE integration with caching',
        'includes': ['core/', 'agents/', 'config/', 'mcp/'],
        'features': ['async', 'cache', 'parallel'],
        'minified': True
    }

class CoralDeployer:
    """Smart deployment system for CoralCollective"""
    
    def __init__(self):
        self.source_path = Path(__file__).parent
        self.deployment_cache = {}
        
    async def analyze_project(self, target_path: Path) -> Dict:
        """Analyze target project to determine best deployment strategy"""
        analysis = {
            'project_type': 'unknown',
            'size': 'small',
            'frameworks': [],
            'existing_coral': False,
            'recommended_strategy': 'minimal'
        }
        
        if not target_path.exists():
            return analysis
        
        # Check for existing Coral
        if (target_path / '.coral').exists() or (target_path / 'coral_collective').exists():
            analysis['existing_coral'] = True
        
        # Detect project type
        if (target_path / 'package.json').exists():
            with open(target_path / 'package.json') as f:
                pkg = json.load(f)
                if 'react' in str(pkg):
                    analysis['frameworks'].append('react')
                if 'vue' in str(pkg):
                    analysis['frameworks'].append('vue')
                analysis['project_type'] = 'javascript'
        
        if (target_path / 'requirements.txt').exists():
            analysis['project_type'] = 'python'
            with open(target_path / 'requirements.txt') as f:
                reqs = f.read()
                if 'django' in reqs:
                    analysis['frameworks'].append('django')
                if 'flask' in reqs:
                    analysis['frameworks'].append('flask')
                if 'fastapi' in reqs:
                    analysis['frameworks'].append('fastapi')
        
        # Determine project size
        total_files = sum(1 for _ in target_path.rglob('*') if _.is_file())
        if total_files > 1000:
            analysis['size'] = 'large'
        elif total_files > 100:
            analysis['size'] = 'medium'
        
        # Recommend strategy
        if analysis['size'] == 'large':
            analysis['recommended_strategy'] = 'ide_optimized'
        elif analysis['frameworks']:
            analysis['recommended_strategy'] = 'standard'
        else:
            analysis['recommended_strategy'] = 'minimal'
        
        return analysis
    
    async def deploy(
        self,
        target_path: Path,
        strategy: str = 'auto',
        force: bool = False,
        upgrade: bool = False
    ) -> Dict:
        """Deploy CoralCollective to target project"""
        
        target_path = Path(target_path).resolve()
        
        # Analyze project
        analysis = await self.analyze_project(target_path)
        
        # Determine strategy
        if strategy == 'auto':
            strategy = analysis['recommended_strategy']
        
        strategy_config = getattr(DeploymentStrategy, strategy.upper(), DeploymentStrategy.MINIMAL)
        
        logger.info(f"Deploying with strategy: {strategy_config['name']}")
        logger.info(f"Target: {target_path}")
        
        # Check for existing installation
        if analysis['existing_coral'] and not (force or upgrade):
            return {
                'status': 'error',
                'message': 'CoralCollective already exists. Use --force to overwrite or --upgrade to update'
            }
        
        # Create deployment package
        package_path = await self._create_package(strategy_config, analysis)
        
        # Deploy to target
        result = await self._deploy_package(package_path, target_path, upgrade)
        
        # Post-deployment setup
        if result['status'] == 'success':
            await self._post_deployment_setup(target_path, analysis)
        
        return result
    
    async def _create_package(self, strategy: Dict, analysis: Dict) -> Path:
        """Create optimized deployment package"""
        
        # Check cache
        cache_key = hashlib.md5(
            f"{strategy['name']}_{analysis['project_type']}".encode()
        ).hexdigest()
        
        if cache_key in self.deployment_cache:
            logger.info("Using cached deployment package")
            return self.deployment_cache[cache_key]
        
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix='coral_deploy_'))
        package_dir = temp_dir / 'coral_collective'
        package_dir.mkdir()
        
        # Copy files based on strategy
        if strategy.get('minified'):
            await self._copy_minified(package_dir, strategy)
        else:
            await self._copy_standard(package_dir, strategy)
        
        # Add project-specific optimizations
        await self._add_project_optimizations(package_dir, analysis)
        
        # Create deployment info
        info = {
            'version': '2.0.0',
            'strategy': strategy['name'],
            'deployed_at': datetime.now().isoformat(),
            'project_analysis': analysis,
            'features': strategy.get('features', [])
        }
        
        with open(package_dir / '.coral_info.json', 'w') as f:
            json.dump(info, f, indent=2)
        
        # Cache the package
        self.deployment_cache[cache_key] = package_dir
        
        return package_dir
    
    async def _copy_minified(self, package_dir: Path, strategy: Dict):
        """Copy minified version of files"""
        
        # Core optimized modules
        core_files = [
            'core/async_agent_runner.py',
            'core/cache_manager.py',
            'core/parallel_executor.py'
        ]
        
        for file_path in core_files:
            src = self.source_path / file_path
            if src.exists():
                dst = package_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Minify Python (remove comments, docstrings)
                content = await self._minify_python(src)
                dst.write_text(content)
        
        # Copy essential agents
        agents_dir = package_dir / 'agents'
        agents_dir.mkdir(exist_ok=True)
        
        essential_agents = [
            'agents/core/project_architect.md',
            'agents/specialists/backend_developer.md',
            'agents/specialists/frontend_developer.md'
        ]
        
        for agent_path in essential_agents:
            src = self.source_path / agent_path
            if src.exists():
                dst = package_dir / agent_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    
    async def _copy_standard(self, package_dir: Path, strategy: Dict):
        """Copy standard files based on strategy"""
        
        includes = strategy.get('includes', [])
        excludes = strategy.get('excludes', [])
        
        for include_pattern in includes:
            if include_pattern == '*':
                # Copy everything except excludes
                for item in self.source_path.iterdir():
                    if not any(exc in str(item) for exc in excludes):
                        if item.is_dir():
                            shutil.copytree(
                                item, 
                                package_dir / item.name,
                                ignore=shutil.ignore_patterns(*excludes)
                            )
                        else:
                            shutil.copy2(item, package_dir)
            else:
                src = self.source_path / include_pattern
                if src.exists():
                    dst = package_dir / include_pattern
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
    
    async def _minify_python(self, file_path: Path) -> str:
        """Minify Python code by removing comments and docstrings"""
        import ast
        import astor
        
        with open(file_path, 'r') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
            
            # Remove docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if (node.body and 
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant)):
                        node.body.pop(0)
            
            # Convert back to source
            return astor.to_source(tree)
        except:
            # If minification fails, return original
            return source
    
    async def _add_project_optimizations(self, package_dir: Path, analysis: Dict):
        """Add project-specific optimizations"""
        
        # Create project-specific config
        config = {
            'project_type': analysis['project_type'],
            'frameworks': analysis['frameworks'],
            'optimizations': []
        }
        
        # Add framework-specific agents
        if 'react' in analysis['frameworks']:
            config['recommended_agents'] = ['frontend_developer', 'ui_designer']
        elif 'django' in analysis['frameworks']:
            config['recommended_agents'] = ['backend_developer', 'database_specialist']
        
        # Add size-based optimizations
        if analysis['size'] == 'large':
            config['optimizations'].extend(['parallel_execution', 'aggressive_caching'])
        
        with open(package_dir / '.coral_project.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    async def _deploy_package(self, package_path: Path, target_path: Path, upgrade: bool) -> Dict:
        """Deploy package to target location"""
        
        try:
            # Determine deployment location
            if target_path.name == '.coral':
                deploy_path = target_path
            else:
                deploy_path = target_path / '.coral'
            
            # Backup existing if upgrading
            if upgrade and deploy_path.exists():
                backup_path = deploy_path.parent / f'.coral_backup_{datetime.now():%Y%m%d_%H%M%S}'
                shutil.move(deploy_path, backup_path)
                logger.info(f"Backed up existing installation to {backup_path}")
            
            # Copy package
            if deploy_path.exists():
                shutil.rmtree(deploy_path)
            
            shutil.copytree(package_path, deploy_path)
            
            # Create wrapper script
            wrapper_script = target_path / 'coral'
            wrapper_content = f'''#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / '.coral'))

from core.async_agent_runner import AsyncAgentRunner
from claude_interface import ClaudeInterface
import asyncio

async def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'run' and len(sys.argv) > 2:
            runner = AsyncAgentRunner()
            agent_id = sys.argv[2]
            task = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else ''
            result = await runner.run_agent(agent_id, task)
            print(result)
        elif command == 'list':
            interface = ClaudeInterface()
            agents = interface.list_agents()
            for agent_id, info in agents.items():
                print(f"{{agent_id}}: {{info['name']}}")
        else:
            print("Usage: coral [run AGENT_ID TASK | list]")
    else:
        print("CoralCollective - Use 'coral run AGENT_ID TASK' or 'coral list'")

if __name__ == "__main__":
    asyncio.run(main())
'''
            wrapper_script.write_text(wrapper_content)
            wrapper_script.chmod(0o755)
            
            return {
                'status': 'success',
                'deploy_path': str(deploy_path),
                'wrapper_script': str(wrapper_script),
                'message': f'Successfully deployed to {deploy_path}'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Deployment failed: {e}'
            }
    
    async def _post_deployment_setup(self, target_path: Path, analysis: Dict):
        """Perform post-deployment setup"""
        
        # Initialize cache
        cache_dir = target_path / '.coral' / '.cache'
        cache_dir.mkdir(exist_ok=True)
        
        # Create IDE config if needed
        if analysis['project_type'] == 'javascript':
            vscode_dir = target_path / '.vscode'
            vscode_dir.mkdir(exist_ok=True)
            
            settings = {
                "coral.enabled": True,
                "coral.cachePath": str(cache_dir),
                "coral.agents.preload": analysis.get('recommended_agents', [])
            }
            
            settings_file = vscode_dir / 'coral.json'
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        
        logger.info("Post-deployment setup complete")


async def main():
    """CLI interface for deployment"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy CoralCollective')
    parser.add_argument('target', help='Target project directory')
    parser.add_argument('--strategy', choices=['minimal', 'standard', 'full', 'ide_optimized', 'auto'],
                       default='auto', help='Deployment strategy')
    parser.add_argument('--force', action='store_true', help='Force overwrite existing')
    parser.add_argument('--upgrade', action='store_true', help='Upgrade existing installation')
    parser.add_argument('--analyze', action='store_true', help='Only analyze, don\'t deploy')
    
    args = parser.parse_args()
    
    deployer = CoralDeployer()
    target = Path(args.target)
    
    if args.analyze:
        analysis = await deployer.analyze_project(target)
        print(json.dumps(analysis, indent=2))
    else:
        result = await deployer.deploy(
            target,
            strategy=args.strategy,
            force=args.force,
            upgrade=args.upgrade
        )
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())