#!/usr/bin/env python3
"""
CoralCollective Setup Script

A professional Python packaging setup for CoralCollective - 
an AI agent orchestration framework with 20+ specialized agents.
"""

import os
from setuptools import setup, find_packages

# Read the README file for long description
def read_readme():
    """Read README.md for long description."""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "CoralCollective - AI Agent Orchestration Framework"

# Read version from package
def read_version():
    """Read version from coral_collective/__init__.py."""
    version_path = os.path.join(os.path.dirname(__file__), 'coral_collective', '__init__.py')
    if os.path.exists(version_path):
        with open(version_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "1.0.0"

# Core dependencies
INSTALL_REQUIRES = [
    # Core framework dependencies
    'PyYAML>=6.0',
    'rich>=13.0.0', 
    'pyperclip>=1.8.2',
    'python-dotenv>=1.0.0',
    'click>=8.1.0',
    'pydantic>=2.0.0',
    'python-dateutil>=2.8.0',
    'aiofiles>=23.0.0',
    'httpx>=0.24.0',
]

# Optional feature dependencies
EXTRAS_REQUIRE = {
    'memory': [
        'chromadb>=0.4.15',
        'numpy>=1.24.0',
        'scipy>=1.10.0', 
        'sentence-transformers>=2.2.0',
        'transformers>=4.25.0',
        'torch>=2.0.0',
        'pandas>=2.0.0',
    ],
    'mcp': [
        'mcp>=0.3.0',
    ],
    'dev': [
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'black>=23.0.0',
        'mypy>=1.0.0',
        'ruff>=0.1.0',
    ],
    'all': [
        # Memory dependencies
        'chromadb>=0.4.15',
        'numpy>=1.24.0',
        'scipy>=1.10.0',
        'sentence-transformers>=2.2.0', 
        'transformers>=4.25.0',
        'torch>=2.0.0',
        'pandas>=2.0.0',
        # MCP dependencies
        'mcp>=0.3.0',
        # Dev dependencies
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'black>=23.0.0',
        'mypy>=1.0.0',
        'ruff>=0.1.0',
    ]
}

setup(
    name='coral-collective',
    version=read_version(),
    author='CoralCollective Contributors',
    author_email='noreply@coral-collective.dev',
    description='AI Agent Orchestration Framework with 20+ Specialized Agents',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/coral-collective/coral-collective',
    project_urls={
        'Documentation': 'https://coral-collective.dev/docs',
        'Source': 'https://github.com/coral-collective/coral-collective',
        'Bug Tracker': 'https://github.com/coral-collective/coral-collective/issues',
    },
    
    packages=find_packages(exclude=['tests', 'docs', 'examples']),
    
    # Package data - include all agent markdown files and configs
    package_data={
        'coral_collective': [
            'agents/*.md',
            'agents/**/*.md',
            'config/*.yaml',
            'config/*.json', 
            'templates/*.md',
            'templates/*.json',
            'mcp/configs/*.yaml',
            'memory/*.py',
        ]
    },
    
    # Include additional files via MANIFEST.in
    include_package_data=True,
    
    # Python version requirement
    python_requires='>=3.8',
    
    # Dependencies
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    
    # Console scripts - CLI entry points
    entry_points={
        'console_scripts': [
            'coral=coral_collective.cli.main:main',
            'coral-init=coral_collective.cli.main:init_command',
            'coral-check=coral_collective.utils.check:main',
        ],
    },
    
    # PyPI classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11', 
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Artificial Intelligence',
    ],
    
    # Keywords for PyPI search
    keywords=[
        'ai', 'agents', 'orchestration', 'development', 'automation',
        'claude', 'llm', 'software-engineering', 'project-management'
    ],
    
    # Zip safe
    zip_safe=False,
)