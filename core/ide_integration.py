#!/usr/bin/env python3
"""
IDE Integration Module for CoralCollective
Provides seamless integration with VSCode, Cursor, and other IDEs
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import websockets
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@dataclass
class IDECommand:
    """Represents an IDE command"""
    id: str
    title: str
    command: str
    arguments: List[Any] = None
    when: str = ""  # Context expression for when command is available
    keybinding: str = ""
    category: str = "CoralCollective"

@dataclass 
class CodeLens:
    """Inline code suggestion/action"""
    range: Dict[str, int]  # start/end line/character
    command: IDECommand
    data: Optional[Dict] = None

@dataclass
class InlineCompletion:
    """Inline completion suggestion from agents"""
    text: str
    range: Dict[str, int]
    agent_id: str
    confidence: float = 0.8
    documentation: str = ""

class IDEIntegration:
    """Main IDE integration handler"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.agent_runner = None  # Lazy load
        self.active_sessions = {}
        self.completion_cache = {}
        
        # Command registry
        self.commands = self._register_commands()
        
        # WebSocket server for real-time communication
        self.ws_server = None
        self.clients = set()
        
    def _register_commands(self) -> Dict[str, IDECommand]:
        """Register all IDE commands"""
        return {
            'coral.runAgent': IDECommand(
                id='coral.runAgent',
                title='Run CoralCollective Agent',
                command='coral.runAgent',
                keybinding='ctrl+shift+a'
            ),
            'coral.quickFix': IDECommand(
                id='coral.quickFix',
                title='Quick Fix with Agent',
                command='coral.quickFix',
                when='editorHasCodeActionsProvider'
            ),
            'coral.explainCode': IDECommand(
                id='coral.explainCode',
                title='Explain Code',
                command='coral.explainCode',
                when='editorTextFocus'
            ),
            'coral.generateTests': IDECommand(
                id='coral.generateTests',
                title='Generate Tests',
                command='coral.generateTests',
                category='CoralCollective Testing'
            ),
            'coral.reviewCode': IDECommand(
                id='coral.reviewCode',
                title='Review Code',
                command='coral.reviewCode',
                when='editorTextFocus'
            ),
            'coral.optimizeCode': IDECommand(
                id='coral.optimizeCode',
                title='Optimize Performance',
                command='coral.optimizeCode'
            ),
            'coral.architectureReview': IDECommand(
                id='coral.architectureReview',
                title='Architecture Review',
                command='coral.architectureReview'
            )
        }
    
    async def initialize(self):
        """Initialize IDE integration"""
        # Lazy load agent runner
        if not self.agent_runner:
            from core.async_agent_runner import AsyncAgentRunner
            self.agent_runner = AsyncAgentRunner()
            await self.agent_runner.initialize()
        
        # Start WebSocket server for real-time communication
        await self.start_websocket_server()
        
        # Register with IDE
        await self.register_with_ide()
        
        logger.info("IDE integration initialized")
    
    async def start_websocket_server(self, port: int = 7777):
        """Start WebSocket server for IDE communication"""
        async def handler(websocket, path):
            self.clients.add(websocket)
            try:
                async for message in websocket:
                    await self.handle_ide_message(json.loads(message), websocket)
            finally:
                self.clients.remove(websocket)
        
        self.ws_server = await websockets.serve(handler, 'localhost', port)
        logger.info(f"WebSocket server started on port {port}")
    
    async def handle_ide_message(self, message: Dict, websocket):
        """Handle incoming IDE messages"""
        msg_type = message.get('type')
        
        if msg_type == 'command':
            result = await self.execute_command(message.get('command'), message.get('args'))
            await websocket.send(json.dumps({'type': 'result', 'data': result}))
            
        elif msg_type == 'completion':
            completions = await self.get_completions(message.get('context'))
            await websocket.send(json.dumps({'type': 'completions', 'data': completions}))
            
        elif msg_type == 'codelens':
            lenses = await self.get_code_lenses(message.get('file'), message.get('content'))
            await websocket.send(json.dumps({'type': 'codelenses', 'data': lenses}))
    
    async def execute_command(self, command_id: str, args: List[Any]) -> Dict:
        """Execute an IDE command"""
        if command_id == 'coral.runAgent':
            return await self.run_agent_command(args)
        elif command_id == 'coral.quickFix':
            return await self.quick_fix_command(args)
        elif command_id == 'coral.explainCode':
            return await self.explain_code_command(args)
        elif command_id == 'coral.generateTests':
            return await self.generate_tests_command(args)
        elif command_id == 'coral.reviewCode':
            return await self.review_code_command(args)
        elif command_id == 'coral.optimizeCode':
            return await self.optimize_code_command(args)
        else:
            return {'error': f'Unknown command: {command_id}'}
    
    async def run_agent_command(self, args: List[Any]) -> Dict:
        """Run a specific agent with context"""
        if len(args) < 2:
            return {'error': 'Requires agent_id and task'}
        
        agent_id = args[0]
        task = args[1]
        context = args[2] if len(args) > 2 else {}
        
        from core.async_agent_runner import AgentRequest
        request = AgentRequest(agent_id=agent_id, task=task, context=context)
        
        result = await self.agent_runner.run_agent(request)
        return result
    
    async def quick_fix_command(self, args: List[Any]) -> Dict:
        """Quick fix for code issues"""
        code = args[0] if args else ""
        error = args[1] if len(args) > 1 else ""
        
        # Use backend developer for quick fixes
        from core.async_agent_runner import AgentRequest
        request = AgentRequest(
            agent_id='backend_developer',
            task=f"Fix this error: {error}\n\nCode:\n{code}"
        )
        
        result = await self.agent_runner.run_agent(request)
        return {
            'fixes': [
                {
                    'title': 'Apply CoralCollective Fix',
                    'edit': result.get('result', {}).get('code', code)
                }
            ]
        }
    
    async def explain_code_command(self, args: List[Any]) -> Dict:
        """Explain selected code"""
        code = args[0] if args else ""
        
        from core.async_agent_runner import AgentRequest
        request = AgentRequest(
            agent_id='technical_writer',
            task=f"Explain this code in simple terms:\n\n{code}",
            timeout=30
        )
        
        result = await self.agent_runner.run_agent(request)
        return {
            'explanation': result.get('result', {}).get('explanation', 'No explanation available')
        }
    
    async def generate_tests_command(self, args: List[Any]) -> Dict:
        """Generate tests for code"""
        code = args[0] if args else ""
        framework = args[1] if len(args) > 1 else "pytest"
        
        from core.async_agent_runner import AgentRequest
        request = AgentRequest(
            agent_id='qa_testing',
            task=f"Generate {framework} tests for:\n\n{code}"
        )
        
        result = await self.agent_runner.run_agent(request)
        return {
            'tests': result.get('result', {}).get('tests', '')
        }
    
    async def review_code_command(self, args: List[Any]) -> Dict:
        """Review code for improvements"""
        code = args[0] if args else ""
        
        from core.async_agent_runner import AgentRequest
        
        # Run multiple agents in parallel for comprehensive review
        requests = [
            AgentRequest('security_specialist', f"Review for security issues:\n{code}"),
            AgentRequest('performance_engineer', f"Review for performance:\n{code}"),
            AgentRequest('backend_developer', f"Review code quality:\n{code}")
        ]
        
        results = await self.agent_runner.run_parallel_agents(requests)
        
        return {
            'reviews': [
                {
                    'category': 'Security',
                    'issues': results[0].get('result', {}).get('issues', [])
                },
                {
                    'category': 'Performance',
                    'issues': results[1].get('result', {}).get('issues', [])
                },
                {
                    'category': 'Code Quality',
                    'issues': results[2].get('result', {}).get('issues', [])
                }
            ]
        }
    
    async def optimize_code_command(self, args: List[Any]) -> Dict:
        """Optimize code for performance"""
        code = args[0] if args else ""
        
        from core.async_agent_runner import AgentRequest
        request = AgentRequest(
            agent_id='performance_engineer',
            task=f"Optimize this code for better performance:\n\n{code}"
        )
        
        result = await self.agent_runner.run_agent(request)
        return {
            'optimized_code': result.get('result', {}).get('code', code),
            'improvements': result.get('result', {}).get('improvements', [])
        }
    
    async def get_completions(self, context: Dict) -> List[InlineCompletion]:
        """Get inline completions from agents"""
        file_path = context.get('file')
        line = context.get('line', 0)
        character = context.get('character', 0)
        prefix = context.get('prefix', '')
        
        # Cache key
        cache_key = f"{file_path}:{line}:{character}:{prefix[:20]}"
        
        if cache_key in self.completion_cache:
            cached = self.completion_cache[cache_key]
            if (datetime.now() - cached['time']).seconds < 60:
                return cached['completions']
        
        # Determine appropriate agent based on file type
        agent_id = self._get_agent_for_file(file_path)
        
        from core.async_agent_runner import AgentRequest
        request = AgentRequest(
            agent_id=agent_id,
            task=f"Complete this code:\n{prefix}",
            timeout=5  # Fast timeout for completions
        )
        
        result = await self.agent_runner.run_agent(request)
        
        completions = []
        if result.get('status') == 'success':
            suggestion = result.get('result', {}).get('completion', '')
            if suggestion:
                completions.append(InlineCompletion(
                    text=suggestion,
                    range={'line': line, 'character': character},
                    agent_id=agent_id,
                    confidence=0.85
                ))
        
        # Cache result
        self.completion_cache[cache_key] = {
            'completions': completions,
            'time': datetime.now()
        }
        
        return completions
    
    async def get_code_lenses(self, file_path: str, content: str) -> List[CodeLens]:
        """Get code lenses (inline actions) for file"""
        lenses = []
        
        # Add lenses for functions/classes
        import ast
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Add test generation lens
                    lenses.append(CodeLens(
                        range={
                            'start': {'line': node.lineno - 1, 'character': 0},
                            'end': {'line': node.lineno - 1, 'character': 0}
                        },
                        command=IDECommand(
                            id='coral.generateTests',
                            title=f'Generate tests for {node.name}',
                            command='coral.generateTests',
                            arguments=[ast.unparse(node)]
                        )
                    ))
                    
                    # Add optimization lens
                    if len(node.body) > 20:  # Complex function
                        lenses.append(CodeLens(
                            range={
                                'start': {'line': node.lineno - 1, 'character': 0},
                                'end': {'line': node.lineno - 1, 'character': 0}
                            },
                            command=IDECommand(
                                id='coral.optimizeCode',
                                title='Optimize performance',
                                command='coral.optimizeCode',
                                arguments=[ast.unparse(node)]
                            )
                        ))
        except:
            pass  # Not Python code
        
        return lenses
    
    def _get_agent_for_file(self, file_path: str) -> str:
        """Determine best agent for file type"""
        if not file_path:
            return 'full_stack_engineer'
        
        ext = Path(file_path).suffix.lower()
        
        agent_map = {
            '.py': 'backend_developer',
            '.js': 'frontend_developer',
            '.jsx': 'frontend_developer',
            '.ts': 'frontend_developer',
            '.tsx': 'frontend_developer',
            '.vue': 'frontend_developer',
            '.css': 'ui_designer',
            '.scss': 'ui_designer',
            '.sql': 'database_specialist',
            '.yaml': 'devops_deployment',
            '.yml': 'devops_deployment',
            '.dockerfile': 'devops_deployment',
            '.md': 'technical_writer'
        }
        
        return agent_map.get(ext, 'full_stack_engineer')
    
    async def register_with_ide(self):
        """Register extension with IDE"""
        # Create VS Code extension manifest
        extension_manifest = {
            "name": "coral-collective",
            "displayName": "CoralCollective AI Agents",
            "description": "AI-powered development assistance",
            "version": "2.0.0",
            "engines": {"vscode": "^1.74.0"},
            "categories": ["Programming Languages", "Other"],
            "activationEvents": ["onStartupFinished"],
            "main": "./extension.js",
            "contributes": {
                "commands": [
                    {
                        "command": cmd.command,
                        "title": cmd.title,
                        "category": cmd.category,
                        "when": cmd.when
                    }
                    for cmd in self.commands.values()
                ],
                "keybindings": [
                    {
                        "command": cmd.command,
                        "key": cmd.keybinding,
                        "when": cmd.when or "editorTextFocus"
                    }
                    for cmd in self.commands.values()
                    if cmd.keybinding
                ],
                "configuration": {
                    "title": "CoralCollective",
                    "properties": {
                        "coral.enabled": {
                            "type": "boolean",
                            "default": True,
                            "description": "Enable CoralCollective integration"
                        },
                        "coral.agents.preload": {
                            "type": "array",
                            "default": ["backend_developer", "frontend_developer"],
                            "description": "Agents to preload for faster access"
                        },
                        "coral.cache.enabled": {
                            "type": "boolean",
                            "default": True,
                            "description": "Enable response caching"
                        },
                        "coral.websocket.port": {
                            "type": "number",
                            "default": 7777,
                            "description": "WebSocket server port"
                        }
                    }
                }
            }
        }
        
        # Save manifest
        manifest_path = self.base_path / '.vscode' / 'coral-extension.json'
        manifest_path.parent.mkdir(exist_ok=True)
        
        with open(manifest_path, 'w') as f:
            json.dump(extension_manifest, f, indent=2)
        
        logger.info(f"IDE extension manifest created at {manifest_path}")


# VSCode Extension JavaScript
VSCODE_EXTENSION_JS = '''
const vscode = require('vscode');
const WebSocket = require('ws');

let ws;
let outputChannel;

function activate(context) {
    outputChannel = vscode.window.createOutputChannel('CoralCollective');
    
    // Connect to WebSocket server
    const port = vscode.workspace.getConfiguration('coral').get('websocket.port', 7777);
    ws = new WebSocket(`ws://localhost:${port}`);
    
    ws.on('open', () => {
        outputChannel.appendLine('Connected to CoralCollective');
    });
    
    ws.on('message', (data) => {
        const message = JSON.parse(data);
        handleServerMessage(message);
    });
    
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('coral.runAgent', runAgent),
        vscode.commands.registerCommand('coral.quickFix', quickFix),
        vscode.commands.registerCommand('coral.explainCode', explainCode),
        vscode.commands.registerCommand('coral.generateTests', generateTests),
        vscode.commands.registerCommand('coral.reviewCode', reviewCode),
        vscode.commands.registerCommand('coral.optimizeCode', optimizeCode)
    );
    
    // Register completion provider
    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider(
            { pattern: '**/*' },
            new CoralCompletionProvider(),
            '.'
        )
    );
    
    // Register code lens provider
    context.subscriptions.push(
        vscode.languages.registerCodeLensProvider(
            { pattern: '**/*.{py,js,ts,jsx,tsx}' },
            new CoralCodeLensProvider()
        )
    );
}

async function runAgent() {
    const agents = await getAgentList();
    const agent = await vscode.window.showQuickPick(agents, {
        placeHolder: 'Select an agent'
    });
    
    if (!agent) return;
    
    const task = await vscode.window.showInputBox({
        prompt: 'Enter task for agent'
    });
    
    if (!task) return;
    
    sendCommand('coral.runAgent', [agent, task]);
}

async function quickFix() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    
    const selection = editor.selection;
    const code = editor.document.getText(selection);
    
    sendCommand('coral.quickFix', [code]);
}

async function explainCode() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;
    
    const selection = editor.selection;
    const code = editor.document.getText(selection);
    
    sendCommand('coral.explainCode', [code]);
}

function sendCommand(command, args) {
    ws.send(JSON.stringify({
        type: 'command',
        command: command,
        args: args
    }));
}

function handleServerMessage(message) {
    if (message.type === 'result') {
        outputChannel.appendLine(JSON.stringify(message.data, null, 2));
        outputChannel.show();
    }
}

class CoralCompletionProvider {
    async provideCompletionItems(document, position, token, context) {
        const prefix = document.getText(new vscode.Range(
            new vscode.Position(position.line, 0),
            position
        ));
        
        return new Promise((resolve) => {
            ws.send(JSON.stringify({
                type: 'completion',
                context: {
                    file: document.fileName,
                    line: position.line,
                    character: position.character,
                    prefix: prefix
                }
            }));
            
            const handler = (data) => {
                const message = JSON.parse(data);
                if (message.type === 'completions') {
                    const items = message.data.map(c => {
                        const item = new vscode.CompletionItem(c.text);
                        item.documentation = c.documentation;
                        return item;
                    });
                    resolve(items);
                }
            };
            
            ws.once('message', handler);
        });
    }
}

class CoralCodeLensProvider {
    async provideCodeLenses(document, token) {
        return new Promise((resolve) => {
            ws.send(JSON.stringify({
                type: 'codelens',
                file: document.fileName,
                content: document.getText()
            }));
            
            const handler = (data) => {
                const message = JSON.parse(data);
                if (message.type === 'codelenses') {
                    const lenses = message.data.map(lens => {
                        return new vscode.CodeLens(
                            new vscode.Range(
                                lens.range.start.line,
                                lens.range.start.character,
                                lens.range.end.line,
                                lens.range.end.character
                            ),
                            {
                                title: lens.command.title,
                                command: lens.command.command,
                                arguments: lens.command.arguments
                            }
                        );
                    });
                    resolve(lenses);
                }
            };
            
            ws.once('message', handler);
        });
    }
}

exports.activate = activate;
'''

if __name__ == "__main__":
    async def test_ide():
        ide = IDEIntegration()
        await ide.initialize()
        
        # Test command execution
        result = await ide.execute_command('coral.explainCode', ['print("Hello World")'])
        print(f"Explanation: {result}")
        
        # Test completions
        completions = await ide.get_completions({
            'file': 'test.py',
            'line': 10,
            'character': 5,
            'prefix': 'def calculate_'
        })
        print(f"Completions: {completions}")
    
    asyncio.run(test_ide())