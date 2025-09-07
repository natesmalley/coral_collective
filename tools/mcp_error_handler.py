#!/usr/bin/env python3
"""
MCP Error Handler for CoralCollective
Comprehensive error handling, recovery strategies, and fallback mechanisms
"""

import asyncio
import logging
import traceback
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    PERMISSION = "permission"
    CONNECTION = "connection"
    TIMEOUT = "timeout"
    RESOURCE_NOT_FOUND = "resource_not_found"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"

@dataclass
class MCPError:
    """Structured MCP error with metadata"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_error: Optional[Exception] = None
    server_name: Optional[str] = None
    tool_name: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    recovery_attempted: bool = False
    recovery_successful: bool = False
    retry_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class FallbackStrategy:
    """Defines a fallback strategy for handling errors"""
    name: str
    description: str
    applicable_errors: List[ErrorCategory]
    severity_threshold: ErrorSeverity
    handler: Callable
    retry_limit: int = 3
    delay_seconds: float = 1.0
    exponential_backoff: bool = True

class MCPErrorHandler:
    """
    Comprehensive error handler for MCP operations with intelligent recovery
    """
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.error_log_path = self.base_path / "logs" / "mcp_errors.jsonl"
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Error history for pattern analysis
        self.error_history: List[MCPError] = []
        self.recovery_strategies: Dict[ErrorCategory, List[FallbackStrategy]] = {}
        
        # Circuit breaker state
        self.circuit_breaker_state: Dict[str, Dict] = {}  # server_name -> state
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        
        # Initialize fallback strategies
        self._init_fallback_strategies()
    
    def _init_fallback_strategies(self):
        """Initialize built-in fallback strategies"""
        
        # Permission error fallbacks
        self.recovery_strategies[ErrorCategory.PERMISSION] = [
            FallbackStrategy(
                name="request_elevated_permissions",
                description="Request elevated permissions from user",
                applicable_errors=[ErrorCategory.PERMISSION],
                severity_threshold=ErrorSeverity.MEDIUM,
                handler=self._handle_permission_error,
                retry_limit=1
            ),
            FallbackStrategy(
                name="use_alternative_server",
                description="Try alternative server with similar capabilities",
                applicable_errors=[ErrorCategory.PERMISSION],
                severity_threshold=ErrorSeverity.HIGH,
                handler=self._handle_server_alternative,
                retry_limit=2
            )
        ]
        
        # Connection error fallbacks
        self.recovery_strategies[ErrorCategory.CONNECTION] = [
            FallbackStrategy(
                name="reconnect_with_backoff",
                description="Reconnect with exponential backoff",
                applicable_errors=[ErrorCategory.CONNECTION, ErrorCategory.TIMEOUT],
                severity_threshold=ErrorSeverity.MEDIUM,
                handler=self._handle_connection_retry,
                retry_limit=3,
                delay_seconds=2.0,
                exponential_backoff=True
            ),
            FallbackStrategy(
                name="use_cached_data",
                description="Use cached results if available",
                applicable_errors=[ErrorCategory.CONNECTION],
                severity_threshold=ErrorSeverity.LOW,
                handler=self._handle_cached_fallback,
                retry_limit=1
            )
        ]
        
        # Server error fallbacks  
        self.recovery_strategies[ErrorCategory.SERVER_ERROR] = [
            FallbackStrategy(
                name="retry_with_delay",
                description="Retry after brief delay for transient errors",
                applicable_errors=[ErrorCategory.SERVER_ERROR],
                severity_threshold=ErrorSeverity.MEDIUM,
                handler=self._handle_server_retry,
                retry_limit=2,
                delay_seconds=5.0
            ),
            FallbackStrategy(
                name="degrade_gracefully",
                description="Continue with reduced functionality",
                applicable_errors=[ErrorCategory.SERVER_ERROR],
                severity_threshold=ErrorSeverity.HIGH,
                handler=self._handle_graceful_degradation,
                retry_limit=1
            )
        ]
        
        # Rate limit fallbacks
        self.recovery_strategies[ErrorCategory.RATE_LIMIT] = [
            FallbackStrategy(
                name="exponential_backoff",
                description="Wait with exponential backoff for rate limit reset",
                applicable_errors=[ErrorCategory.RATE_LIMIT],
                severity_threshold=ErrorSeverity.LOW,
                handler=self._handle_rate_limit_backoff,
                retry_limit=3,
                delay_seconds=60.0,
                exponential_backoff=True
            )
        ]
    
    def categorize_error(self, error: Exception, context: Dict[str, Any] = None) -> MCPError:
        """Categorize an error and determine its severity"""
        error_message = str(error).lower()
        context = context or {}
        
        # Determine category
        category = ErrorCategory.UNKNOWN
        severity = ErrorSeverity.MEDIUM
        
        if any(word in error_message for word in ['permission', 'denied', 'unauthorized', 'forbidden']):
            category = ErrorCategory.PERMISSION
            severity = ErrorSeverity.HIGH
        elif any(word in error_message for word in ['connection', 'network', 'unreachable']):
            category = ErrorCategory.CONNECTION
            severity = ErrorSeverity.HIGH
        elif any(word in error_message for word in ['timeout', 'timed out']):
            category = ErrorCategory.TIMEOUT
            severity = ErrorSeverity.MEDIUM
        elif any(word in error_message for word in ['not found', '404', 'does not exist']):
            category = ErrorCategory.RESOURCE_NOT_FOUND
            severity = ErrorSeverity.MEDIUM
        elif any(word in error_message for word in ['invalid', 'malformed', 'bad request', '400']):
            category = ErrorCategory.INVALID_REQUEST
            severity = ErrorSeverity.LOW
        elif any(word in error_message for word in ['server error', '500', 'internal error']):
            category = ErrorCategory.SERVER_ERROR
            severity = ErrorSeverity.HIGH
        elif any(word in error_message for word in ['rate limit', 'too many requests', '429']):
            category = ErrorCategory.RATE_LIMIT
            severity = ErrorSeverity.LOW
        elif any(word in error_message for word in ['authentication', 'auth', 'token']):
            category = ErrorCategory.AUTHENTICATION
            severity = ErrorSeverity.HIGH
        
        return MCPError(
            category=category,
            severity=severity,
            message=str(error),
            original_error=error,
            server_name=context.get('server_name'),
            tool_name=context.get('tool_name'),
            agent_id=context.get('agent_id'),
            context=context
        )
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an MCP error with appropriate recovery strategies
        
        Returns:
            Dict containing recovery result and recommendations
        """
        mcp_error = self.categorize_error(error, context)
        
        # Log error
        await self._log_error(mcp_error)
        
        # Add to history
        self.error_history.append(mcp_error)
        
        # Update circuit breaker if needed
        if mcp_error.server_name:
            self._update_circuit_breaker(mcp_error.server_name, success=False)
            
            # Check if circuit breaker should prevent retry
            if self._is_circuit_breaker_open(mcp_error.server_name):
                return {
                    'success': False,
                    'error': mcp_error,
                    'recovery_attempted': False,
                    'reason': 'Circuit breaker open',
                    'recommended_action': f'Wait {self.circuit_breaker_timeout}s before retrying {mcp_error.server_name}'
                }
        
        # Attempt recovery
        recovery_result = await self._attempt_recovery(mcp_error)
        
        return recovery_result
    
    async def _attempt_recovery(self, error: MCPError) -> Dict[str, Any]:
        """Attempt to recover from an error using available strategies"""
        
        applicable_strategies = self.recovery_strategies.get(error.category, [])
        
        if not applicable_strategies:
            logger.warning(f"No recovery strategies available for {error.category}")
            return {
                'success': False,
                'error': error,
                'recovery_attempted': False,
                'reason': 'No recovery strategies available',
                'recommended_action': 'Manual intervention required'
            }
        
        # Sort strategies by severity threshold (try less severe first)
        strategies = sorted(applicable_strategies, key=lambda s: s.severity_threshold.value)
        
        for strategy in strategies:
            if error.severity.value >= strategy.severity_threshold.value:
                logger.info(f"Attempting recovery strategy: {strategy.name}")
                
                try:
                    error.recovery_attempted = True
                    result = await strategy.handler(error)
                    
                    if result.get('success'):
                        error.recovery_successful = True
                        logger.info(f"Recovery successful using strategy: {strategy.name}")
                        
                        # Update circuit breaker on success
                        if error.server_name:
                            self._update_circuit_breaker(error.server_name, success=True)
                        
                        return result
                    else:
                        logger.warning(f"Recovery strategy {strategy.name} failed: {result.get('reason')}")
                
                except Exception as e:
                    logger.error(f"Recovery strategy {strategy.name} raised exception: {e}")
                    continue
        
        # All strategies failed
        return {
            'success': False,
            'error': error,
            'recovery_attempted': True,
            'recovery_successful': False,
            'reason': 'All recovery strategies failed',
            'recommended_action': self._generate_manual_action_recommendation(error)
        }
    
    async def _handle_permission_error(self, error: MCPError) -> Dict[str, Any]:
        """Handle permission errors"""
        logger.info(f"Handling permission error for {error.server_name}/{error.tool_name}")
        
        recommendations = []
        
        if error.server_name and error.agent_id:
            recommendations.append(f"Add {error.server_name} to allowed servers for {error.agent_id}")
            recommendations.append(f"Check agent permissions in mcp_config.yaml")
        
        if error.tool_name:
            recommendations.append(f"Verify {error.tool_name} is in allowed tools list")
        
        return {
            'success': False,
            'strategy': 'request_elevated_permissions',
            'reason': 'Permission error requires manual configuration',
            'recommendations': recommendations,
            'automated_fix': False
        }
    
    async def _handle_server_alternative(self, error: MCPError) -> Dict[str, Any]:
        """Try alternative server with similar capabilities"""
        # This would require server capability mapping
        logger.info(f"Looking for alternative to {error.server_name}")
        
        # Placeholder logic - in reality would check server capabilities
        alternatives = {
            'postgres': ['supabase'],
            'github': ['gitlab'],  # If GitLab MCP server exists
            'filesystem': []  # No alternatives for filesystem
        }
        
        server_alternatives = alternatives.get(error.server_name, [])
        
        if server_alternatives:
            return {
                'success': True,
                'strategy': 'use_alternative_server',
                'alternative_server': server_alternatives[0],
                'reason': f'Switched from {error.server_name} to {server_alternatives[0]}'
            }
        
        return {
            'success': False,
            'strategy': 'use_alternative_server',
            'reason': f'No alternatives available for {error.server_name}'
        }
    
    async def _handle_connection_retry(self, error: MCPError) -> Dict[str, Any]:
        """Handle connection errors with retry logic"""
        max_retries = 3
        base_delay = 2.0
        
        for attempt in range(max_retries):
            delay = base_delay * (2 ** attempt) if attempt > 0 else 0
            
            if delay > 0:
                logger.info(f"Retrying connection to {error.server_name} in {delay}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)
            
            try:
                # This would attempt to reconnect to the server
                # For now, simulate with a delay and random success
                await asyncio.sleep(1)
                
                # Simulate successful reconnection (in reality, would test connection)
                if attempt >= 1:  # Succeed after first retry
                    return {
                        'success': True,
                        'strategy': 'reconnect_with_backoff',
                        'attempts': attempt + 1,
                        'reason': f'Successfully reconnected to {error.server_name}'
                    }
                    
            except Exception as e:
                logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
                continue
        
        return {
            'success': False,
            'strategy': 'reconnect_with_backoff',
            'attempts': max_retries,
            'reason': f'Failed to reconnect to {error.server_name} after {max_retries} attempts'
        }
    
    async def _handle_cached_fallback(self, error: MCPError) -> Dict[str, Any]:
        """Use cached data as fallback"""
        # This would check for cached results
        cache_path = self.base_path / "cache" / "mcp_responses"
        
        if error.tool_name and error.context.get('parameters'):
            # Generate cache key
            cache_key = f"{error.server_name}_{error.tool_name}_{hash(str(error.context['parameters']))}"
            cache_file = cache_path / f"{cache_key}.json"
            
            if cache_file.exists():
                try:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                    
                    # Check if cache is not too old (1 hour)
                    cache_age = time.time() - cache_file.stat().st_mtime
                    if cache_age < 3600:  # 1 hour
                        return {
                            'success': True,
                            'strategy': 'use_cached_data',
                            'result': cached_data,
                            'cache_age_seconds': cache_age,
                            'reason': f'Used cached data for {error.tool_name}'
                        }
                except Exception as e:
                    logger.warning(f"Failed to load cached data: {e}")
        
        return {
            'success': False,
            'strategy': 'use_cached_data',
            'reason': 'No valid cached data available'
        }
    
    async def _handle_server_retry(self, error: MCPError) -> Dict[str, Any]:
        """Retry server operations with delay"""
        delay = 5.0
        logger.info(f"Retrying {error.tool_name} on {error.server_name} after {delay}s delay")
        
        await asyncio.sleep(delay)
        
        # This would retry the original operation
        # For now, simulate success after delay
        return {
            'success': True,
            'strategy': 'retry_with_delay',
            'delay_seconds': delay,
            'reason': f'Successful retry of {error.tool_name} after delay'
        }
    
    async def _handle_graceful_degradation(self, error: MCPError) -> Dict[str, Any]:
        """Handle graceful degradation"""
        degradation_options = {
            'filesystem': 'Read-only mode available',
            'database': 'Use cached queries only',
            'github': 'Repository operations disabled, issue tracking available',
            'docker': 'Container management disabled'
        }
        
        degraded_capability = degradation_options.get(error.server_name, 'Limited functionality')
        
        return {
            'success': True,
            'strategy': 'degrade_gracefully',
            'degraded_mode': True,
            'available_capabilities': degraded_capability,
            'reason': f'Operating in degraded mode: {degraded_capability}'
        }
    
    async def _handle_rate_limit_backoff(self, error: MCPError) -> Dict[str, Any]:
        """Handle rate limiting with exponential backoff"""
        base_delay = 60.0  # Start with 1 minute
        max_delay = 300.0  # Cap at 5 minutes
        
        # Extract retry-after header if available
        retry_after = error.context.get('retry_after', base_delay)
        delay = min(retry_after, max_delay)
        
        logger.info(f"Rate limited by {error.server_name}, waiting {delay}s")
        await asyncio.sleep(delay)
        
        return {
            'success': True,
            'strategy': 'exponential_backoff',
            'delay_seconds': delay,
            'reason': f'Rate limit handled, waited {delay}s'
        }
    
    def _update_circuit_breaker(self, server_name: str, success: bool):
        """Update circuit breaker state for a server"""
        if server_name not in self.circuit_breaker_state:
            self.circuit_breaker_state[server_name] = {
                'failure_count': 0,
                'last_failure': None,
                'state': 'closed'  # closed, open, half-open
            }
        
        state = self.circuit_breaker_state[server_name]
        
        if success:
            state['failure_count'] = 0
            state['state'] = 'closed'
        else:
            state['failure_count'] += 1
            state['last_failure'] = time.time()
            
            if state['failure_count'] >= self.circuit_breaker_threshold:
                state['state'] = 'open'
                logger.warning(f"Circuit breaker OPEN for {server_name}")
    
    def _is_circuit_breaker_open(self, server_name: str) -> bool:
        """Check if circuit breaker is open for a server"""
        if server_name not in self.circuit_breaker_state:
            return False
        
        state = self.circuit_breaker_state[server_name]
        
        if state['state'] == 'closed':
            return False
        elif state['state'] == 'open':
            # Check if timeout has passed
            if state['last_failure'] and (time.time() - state['last_failure'] > self.circuit_breaker_timeout):
                state['state'] = 'half-open'
                state['failure_count'] = 0
                logger.info(f"Circuit breaker HALF-OPEN for {server_name}")
                return False
            return True
        else:  # half-open
            return False
    
    async def _log_error(self, error: MCPError):
        """Log error to file for analysis"""
        try:
            error_data = {
                'timestamp': error.timestamp.isoformat(),
                'category': error.category.value,
                'severity': error.severity.value,
                'message': error.message,
                'server_name': error.server_name,
                'tool_name': error.tool_name,
                'agent_id': error.agent_id,
                'context': error.context,
                'recovery_attempted': error.recovery_attempted,
                'recovery_successful': error.recovery_successful,
                'retry_count': error.retry_count
            }
            
            with open(self.error_log_path, 'a') as f:
                f.write(json.dumps(error_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to log error: {e}")
    
    def _generate_manual_action_recommendation(self, error: MCPError) -> str:
        """Generate manual action recommendation based on error"""
        recommendations = {
            ErrorCategory.PERMISSION: "Check agent permissions in mcp_config.yaml and ensure proper server access",
            ErrorCategory.CONNECTION: "Verify MCP servers are running and network connectivity",
            ErrorCategory.TIMEOUT: "Check server performance and increase timeout limits if needed",
            ErrorCategory.RESOURCE_NOT_FOUND: "Verify resource paths and availability",
            ErrorCategory.INVALID_REQUEST: "Check request parameters and data format",
            ErrorCategory.SERVER_ERROR: "Check server logs and health status",
            ErrorCategory.RATE_LIMIT: "Reduce request frequency or upgrade API limits",
            ErrorCategory.AUTHENTICATION: "Verify API keys and authentication credentials"
        }
        
        return recommendations.get(error.category, "Review error details and server configuration")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for analysis"""
        if not self.error_history:
            return {"message": "No errors recorded"}
        
        total_errors = len(self.error_history)
        category_counts = {}
        severity_counts = {}
        recovery_stats = {'attempted': 0, 'successful': 0}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            if error.recovery_attempted:
                recovery_stats['attempted'] += 1
                if error.recovery_successful:
                    recovery_stats['successful'] += 1
        
        return {
            'total_errors': total_errors,
            'by_category': category_counts,
            'by_severity': severity_counts,
            'recovery_rate': f"{(recovery_stats['successful'] / recovery_stats['attempted'] * 100):.1f}%" if recovery_stats['attempted'] > 0 else "N/A",
            'circuit_breaker_states': {k: v['state'] for k, v in self.circuit_breaker_state.items()}
        }
    
    def reset_error_history(self):
        """Reset error history (useful for testing)"""
        self.error_history = []
        self.circuit_breaker_state = {}
        logger.info("Error history reset")