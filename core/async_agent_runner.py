#!/usr/bin/env python3
"""
Async-First Agent Runner for CoralCollective
High-performance agent execution with full async support
"""

import asyncio
import aiofiles
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from functools import lru_cache
import hashlib
from collections import deque
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentRequest:
    """Represents an agent execution request"""
    agent_id: str
    task: str
    context: Optional[Dict] = None
    priority: int = 5
    timeout: int = 300

class AsyncAgentRunner:
    """High-performance async agent runner"""
    
    def __init__(self, cache_size: int = 50, max_concurrent: int = 10):
        self.base_path = Path(__file__).parent.parent
        self.cache_size = cache_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Caching layers
        self.prompt_cache = {}
        self.agent_cache = {}
        self.response_cache = deque(maxlen=100)
        
        # Performance tracking
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'avg_response_time': 0
        }
        
        # Initialize on first use
        self._initialized = False
        
    async def initialize(self):
        """Lazy initialization of runner"""
        if self._initialized:
            return
            
        # Pre-load agent configurations
        await self._load_agents_async()
        
        # Pre-compile common patterns
        self._compile_patterns()
        
        # Initialize connection pool
        await self._init_connection_pool()
        
        self._initialized = True
        logger.info("AsyncAgentRunner initialized successfully")
    
    async def _load_agents_async(self):
        """Load all agent configurations asynchronously"""
        config_path = self.base_path / "claude_code_agents.json"
        
        async with aiofiles.open(config_path, 'r') as f:
            content = await f.read()
            config = json.loads(content)
            
        self.agent_cache = config.get('agents', {})
        logger.info(f"Loaded {len(self.agent_cache)} agents")
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for performance"""
        import re
        self.patterns = {
            'task_extract': re.compile(r'^\d+\.\s+(.+)$'),
            'bullet_point': re.compile(r'^[-*]\s+(.+)$'),
            'header': re.compile(r'^#{1,3}\s+(.+)$'),
            'code_block': re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
        }
    
    async def _init_connection_pool(self):
        """Initialize connection pooling for external services"""
        self.connection_pool = asyncio.Queue(maxsize=10)
        # Pre-create connections if needed
    
    @lru_cache(maxsize=50)
    def _get_prompt_hash(self, agent_id: str) -> str:
        """Get hash of agent prompt file for cache validation"""
        prompt_path = self._get_prompt_path(agent_id)
        if prompt_path.exists():
            return hashlib.md5(prompt_path.read_bytes()).hexdigest()
        return ""
    
    def _get_prompt_path(self, agent_id: str) -> Path:
        """Get the path to an agent's prompt file"""
        agent = self.agent_cache.get(agent_id, {})
        prompt_path = agent.get('prompt_path', f'agents/specialists/{agent_id}.md')
        return self.base_path / prompt_path
    
    async def get_agent_prompt(self, agent_id: str, use_cache: bool = True) -> str:
        """Get agent prompt with intelligent caching"""
        if use_cache and agent_id in self.prompt_cache:
            file_hash = self._get_prompt_hash(agent_id)
            cached_hash, cached_prompt = self.prompt_cache[agent_id]
            if file_hash == cached_hash:
                self.metrics['cache_hits'] += 1
                return cached_prompt
        
        self.metrics['cache_misses'] += 1
        
        # Load prompt asynchronously
        prompt_path = self._get_prompt_path(agent_id)
        
        if not prompt_path.exists():
            # Try alternate paths
            for alt_path in [
                f'agents/core/{agent_id}.md',
                f'agents/specialists/{agent_id}.md',
                f'agents/{agent_id}.md'
            ]:
                full_path = self.base_path / alt_path
                if full_path.exists():
                    prompt_path = full_path
                    break
        
        if prompt_path.exists():
            async with aiofiles.open(prompt_path, 'r') as f:
                prompt = await f.read()
            
            # Update cache
            file_hash = self._get_prompt_hash(agent_id)
            self.prompt_cache[agent_id] = (file_hash, prompt)
            
            return prompt
        
        return ""
    
    async def run_agent(self, request: AgentRequest) -> Dict[str, Any]:
        """Execute agent with full async support"""
        async with self.semaphore:  # Limit concurrent executions
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Initialize if needed
                await self.initialize()
                
                # Get agent configuration
                agent_config = self.agent_cache.get(request.agent_id)
                if not agent_config:
                    return {
                        'status': 'error',
                        'message': f'Agent {request.agent_id} not found'
                    }
                
                # Get prompt (cached)
                prompt = await self.get_agent_prompt(request.agent_id)
                
                # Add task to prompt
                full_prompt = f"{prompt}\n\n## Current Task\n{request.task}"
                
                # Add context if provided
                if request.context:
                    context_str = yaml.dump(request.context, default_flow_style=False)
                    full_prompt += f"\n\n## Context\n```yaml\n{context_str}\n```"
                
                # Execute agent (would integrate with actual execution here)
                result = await self._execute_agent_async(
                    request.agent_id, 
                    full_prompt,
                    request.timeout
                )
                
                # Track metrics
                elapsed = asyncio.get_event_loop().time() - start_time
                self._update_metrics(elapsed)
                
                # Cache successful response
                self.response_cache.append({
                    'agent_id': request.agent_id,
                    'task_hash': hashlib.md5(request.task.encode()).hexdigest(),
                    'result': result,
                    'timestamp': datetime.now()
                })
                
                return {
                    'status': 'success',
                    'agent_id': request.agent_id,
                    'result': result,
                    'execution_time': elapsed,
                    'metrics': self.metrics
                }
                
            except asyncio.TimeoutError:
                return {
                    'status': 'error',
                    'message': f'Agent execution timed out after {request.timeout}s'
                }
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                return {
                    'status': 'error',
                    'message': str(e)
                }
    
    async def _execute_agent_async(self, agent_id: str, prompt: str, timeout: int) -> Any:
        """Execute the actual agent logic asynchronously"""
        # This would integrate with the actual agent execution
        # For now, simulate async execution
        await asyncio.sleep(0.1)  # Simulate work
        return {
            'agent_response': f"Executed {agent_id}",
            'prompt_length': len(prompt)
        }
    
    def _update_metrics(self, elapsed_time: float):
        """Update performance metrics"""
        self.metrics['total_requests'] += 1
        
        # Update rolling average
        current_avg = self.metrics['avg_response_time']
        total = self.metrics['total_requests']
        self.metrics['avg_response_time'] = (
            (current_avg * (total - 1) + elapsed_time) / total
        )
    
    async def run_parallel_agents(self, requests: List[AgentRequest]) -> List[Dict]:
        """Run multiple agents in parallel"""
        tasks = [self.run_agent(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_cached_response(self, agent_id: str, task: str) -> Optional[Dict]:
        """Check if we have a cached response for this request"""
        task_hash = hashlib.md5(task.encode()).hexdigest()
        
        for cached in self.response_cache:
            if (cached['agent_id'] == agent_id and 
                cached['task_hash'] == task_hash):
                age = (datetime.now() - cached['timestamp']).seconds
                if age < 3600:  # 1 hour cache validity
                    self.metrics['cache_hits'] += 1
                    return cached['result']
        
        return None
    
    async def preload_agents(self, agent_ids: List[str]):
        """Preload specific agents for faster access"""
        tasks = [self.get_agent_prompt(aid) for aid in agent_ids]
        await asyncio.gather(*tasks)
        logger.info(f"Preloaded {len(agent_ids)} agents")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_ratio = (
            self.metrics['cache_hits'] / 
            max(1, self.metrics['cache_hits'] + self.metrics['cache_misses'])
        )
        
        return {
            **self.metrics,
            'cache_hit_ratio': cache_ratio,
            'cached_prompts': len(self.prompt_cache),
            'cached_responses': len(self.response_cache)
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        self.prompt_cache.clear()
        self.response_cache.clear()
        logger.info("AsyncAgentRunner cleaned up")


# Convenience functions for standalone usage
async def run_agent_async(agent_id: str, task: str, context: Optional[Dict] = None):
    """Convenience function to run a single agent"""
    runner = AsyncAgentRunner()
    request = AgentRequest(agent_id=agent_id, task=task, context=context)
    return await runner.run_agent(request)


async def run_agents_parallel(agent_tasks: List[Tuple[str, str]]):
    """Run multiple agents in parallel"""
    runner = AsyncAgentRunner()
    requests = [
        AgentRequest(agent_id=aid, task=task) 
        for aid, task in agent_tasks
    ]
    return await runner.run_parallel_agents(requests)


if __name__ == "__main__":
    # Example usage
    async def main():
        runner = AsyncAgentRunner()
        
        # Preload common agents
        await runner.preload_agents(['backend_developer', 'frontend_developer'])
        
        # Run single agent
        result = await runner.run_agent(
            AgentRequest(
                agent_id='backend_developer',
                task='Create a REST API for user management'
            )
        )
        print(f"Result: {result}")
        
        # Run parallel agents
        requests = [
            AgentRequest('database_specialist', 'Design user schema'),
            AgentRequest('api_designer', 'Design REST endpoints'),
            AgentRequest('security_specialist', 'Review security requirements')
        ]
        results = await runner.run_parallel_agents(requests)
        print(f"Parallel results: {len(results)} agents completed")
        
        # Show metrics
        print(f"Metrics: {runner.get_metrics()}")
        
        await runner.cleanup()
    
    asyncio.run(main())