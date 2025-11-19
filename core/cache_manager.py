#!/usr/bin/env python3
"""
Intelligent Cache Manager for CoralCollective
Provides multi-layer caching with TTL, LRU, and invalidation strategies
"""

import asyncio
import hashlib
import json
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
import aiofiles
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    """Represents a single cache entry with metadata"""
    
    def __init__(self, key: str, value: Any, ttl: int = 3600):
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.accessed_at = datetime.now()
        self.access_count = 1
        self.ttl = ttl
        self.size = self._calculate_size(value)
    
    def _calculate_size(self, obj: Any) -> int:
        """Calculate approximate size of object in bytes"""
        try:
            return len(pickle.dumps(obj))
        except:
            return 0
    
    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - self.created_at).seconds
        return age < self.ttl
    
    def access(self) -> Any:
        """Access the cached value and update metadata"""
        self.accessed_at = datetime.now()
        self.access_count += 1
        return self.value

class LRUCache:
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 100, max_memory: int = 100_000_000):
        self.max_size = max_size
        self.max_memory = max_memory  # 100MB default
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory = 0
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self.cache:
            entry = self.cache[key]
            if entry.is_valid():
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return entry.access()
            else:
                # Remove expired entry
                self.remove(key)
        
        self.misses += 1
        return None
    
    def put(self, key: str, value: Any, ttl: int = 3600):
        """Put value in cache"""
        entry = CacheEntry(key, value, ttl)
        
        # Remove old entry if exists
        if key in self.cache:
            self.remove(key)
        
        # Check memory limit
        while self.current_memory + entry.size > self.max_memory and self.cache:
            self._evict_lru()
        
        # Check size limit
        while len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Add new entry
        self.cache[key] = entry
        self.current_memory += entry.size
    
    def remove(self, key: str):
        """Remove entry from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.current_memory -= entry.size
            del self.cache[key]
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if self.cache:
            key, entry = self.cache.popitem(last=False)
            self.current_memory -= entry.size
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.current_memory = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'memory': self.current_memory,
            'hits': self.hits,
            'misses': self.misses,
            'hit_ratio': self.hits / max(1, self.hits + self.misses),
            'max_size': self.max_size,
            'max_memory': self.max_memory
        }

class AsyncCacheManager:
    """Advanced async cache manager with multiple strategies"""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / '.coral_cache'
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Multiple cache layers
        self.memory_cache = LRUCache(max_size=100)
        self.prompt_cache = LRUCache(max_size=50)
        self.response_cache = LRUCache(max_size=200)
        
        # File cache for persistence
        self.file_cache_path = self.base_path / 'cache.json'
        
        # Invalidation callbacks
        self.invalidation_callbacks: Dict[str, Callable] = {}
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str, layer: str = 'memory') -> Optional[Any]:
        """Get value from specified cache layer"""
        async with self.lock:
            if layer == 'memory':
                return self.memory_cache.get(key)
            elif layer == 'prompt':
                return self.prompt_cache.get(key)
            elif layer == 'response':
                return self.response_cache.get(key)
            elif layer == 'file':
                return await self._get_from_file(key)
            else:
                # Try all layers
                for cache_layer in ['memory', 'prompt', 'response', 'file']:
                    value = await self.get(key, cache_layer)
                    if value is not None:
                        return value
        return None
    
    async def put(self, key: str, value: Any, layer: str = 'memory', ttl: int = 3600):
        """Put value in specified cache layer"""
        async with self.lock:
            if layer == 'memory':
                self.memory_cache.put(key, value, ttl)
            elif layer == 'prompt':
                self.prompt_cache.put(key, value, ttl)
            elif layer == 'response':
                self.response_cache.put(key, value, ttl)
            elif layer == 'file':
                await self._put_to_file(key, value, ttl)
            elif layer == 'all':
                # Cache in all layers
                self.memory_cache.put(key, value, ttl)
                await self._put_to_file(key, value, ttl)
    
    async def _get_from_file(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        if self.file_cache_path.exists():
            try:
                async with aiofiles.open(self.file_cache_path, 'r') as f:
                    content = await f.read()
                    cache_data = json.loads(content)
                    
                if key in cache_data:
                    entry = cache_data[key]
                    created_at = datetime.fromisoformat(entry['created_at'])
                    age = (datetime.now() - created_at).seconds
                    
                    if age < entry.get('ttl', 3600):
                        return entry['value']
            except Exception as e:
                logger.error(f"Error reading file cache: {e}")
        return None
    
    async def _put_to_file(self, key: str, value: Any, ttl: int):
        """Put value in file cache"""
        try:
            cache_data = {}
            if self.file_cache_path.exists():
                async with aiofiles.open(self.file_cache_path, 'r') as f:
                    content = await f.read()
                    if content:
                        cache_data = json.loads(content)
            
            cache_data[key] = {
                'value': value,
                'created_at': datetime.now().isoformat(),
                'ttl': ttl
            }
            
            async with aiofiles.open(self.file_cache_path, 'w') as f:
                await f.write(json.dumps(cache_data, default=str))
        except Exception as e:
            logger.error(f"Error writing file cache: {e}")
    
    async def invalidate(self, pattern: str = None, layer: str = 'all'):
        """Invalidate cache entries matching pattern"""
        async with self.lock:
            if layer in ['memory', 'all']:
                self._invalidate_layer(self.memory_cache, pattern)
            if layer in ['prompt', 'all']:
                self._invalidate_layer(self.prompt_cache, pattern)
            if layer in ['response', 'all']:
                self._invalidate_layer(self.response_cache, pattern)
            if layer in ['file', 'all']:
                await self._invalidate_file_cache(pattern)
    
    def _invalidate_layer(self, cache: LRUCache, pattern: Optional[str]):
        """Invalidate entries in a cache layer"""
        if pattern:
            keys_to_remove = [
                k for k in cache.cache.keys() 
                if pattern in k
            ]
            for key in keys_to_remove:
                cache.remove(key)
        else:
            cache.clear()
    
    async def _invalidate_file_cache(self, pattern: Optional[str]):
        """Invalidate file cache entries"""
        if not pattern:
            # Clear entire file cache
            if self.file_cache_path.exists():
                self.file_cache_path.unlink()
        else:
            # Remove specific entries
            if self.file_cache_path.exists():
                async with aiofiles.open(self.file_cache_path, 'r') as f:
                    content = await f.read()
                    cache_data = json.loads(content) if content else {}
                
                keys_to_remove = [k for k in cache_data.keys() if pattern in k]
                for key in keys_to_remove:
                    del cache_data[key]
                
                async with aiofiles.open(self.file_cache_path, 'w') as f:
                    await f.write(json.dumps(cache_data, default=str))
    
    def register_invalidation_callback(self, key: str, callback: Callable):
        """Register callback for cache invalidation"""
        self.invalidation_callbacks[key] = callback
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return {
            'memory': self.memory_cache.get_stats(),
            'prompt': self.prompt_cache.get_stats(),
            'response': self.response_cache.get_stats(),
            'file_cache_size': self.file_cache_path.stat().st_size if self.file_cache_path.exists() else 0
        }
    
    async def cleanup_expired(self):
        """Clean up expired cache entries"""
        async with self.lock:
            # Clean memory caches
            for cache in [self.memory_cache, self.prompt_cache, self.response_cache]:
                expired_keys = [
                    k for k, entry in cache.cache.items()
                    if not entry.is_valid()
                ]
                for key in expired_keys:
                    cache.remove(key)
            
            # Clean file cache
            if self.file_cache_path.exists():
                async with aiofiles.open(self.file_cache_path, 'r') as f:
                    content = await f.read()
                    cache_data = json.loads(content) if content else {}
                
                cleaned_data = {}
                for key, entry in cache_data.items():
                    created_at = datetime.fromisoformat(entry['created_at'])
                    age = (datetime.now() - created_at).seconds
                    if age < entry.get('ttl', 3600):
                        cleaned_data[key] = entry
                
                async with aiofiles.open(self.file_cache_path, 'w') as f:
                    await f.write(json.dumps(cleaned_data, default=str))


def cached(layer: str = 'memory', ttl: int = 3600):
    """Decorator for caching async function results"""
    def decorator(func: Callable):
        cache_manager = AsyncCacheManager()
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_manager.cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache_manager.get(key, layer)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache_manager.put(key, result, layer, ttl)
            
            return result
        
        return wrapper
    return decorator


# Example usage
@cached(layer='prompt', ttl=7200)
async def get_agent_prompt(agent_id: str) -> str:
    """Example cached function"""
    # Expensive operation
    await asyncio.sleep(1)
    return f"Prompt for {agent_id}"


if __name__ == "__main__":
    async def test_cache():
        manager = AsyncCacheManager()
        
        # Test basic operations
        await manager.put('test_key', {'data': 'test'}, layer='all')
        value = await manager.get('test_key')
        print(f"Retrieved: {value}")
        
        # Test decorated function
        prompt = await get_agent_prompt('backend_developer')
        print(f"First call: {prompt}")
        
        prompt = await get_agent_prompt('backend_developer')  # Should be cached
        print(f"Second call (cached): {prompt}")
        
        # Show stats
        stats = await manager.get_stats()
        print(f"Cache stats: {json.dumps(stats, indent=2)}")
        
        # Cleanup
        await manager.cleanup_expired()
    
    asyncio.run(test_cache())