#!/usr/bin/env python3
"""
MCP Metrics Collector for CoralCollective
Comprehensive tracking and analysis of MCP tool usage across agents
"""

import json
import yaml
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class MCPUsageMetrics:
    """Aggregate metrics for MCP usage analysis"""
    total_sessions: int = 0
    total_tool_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    success_rate: float = 0.0
    average_execution_time_ms: float = 0.0
    most_used_servers: List[tuple] = field(default_factory=list)  # (server, count)
    most_used_tools: List[tuple] = field(default_factory=list)   # (tool, count)
    agent_performance: Dict[str, Dict] = field(default_factory=dict)
    server_reliability: Dict[str, Dict] = field(default_factory=dict)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    usage_trends: Dict[str, List] = field(default_factory=dict)  # daily/hourly trends

@dataclass
class AgentMCPPerformance:
    """Performance metrics for a specific agent's MCP usage"""
    agent_id: str
    total_sessions: int = 0
    total_calls: int = 0
    success_rate: float = 0.0
    average_execution_time: float = 0.0
    preferred_servers: List[str] = field(default_factory=list)
    common_errors: List[str] = field(default_factory=list)
    efficiency_score: float = 0.0  # calls per session

class MCPMetricsCollector:
    """
    Collects, aggregates, and analyzes MCP tool usage metrics
    """
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.metrics_dir = self.base_path / "metrics" / "mcp_usage"
        self.reports_dir = self.base_path / "metrics" / "mcp_reports"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self.session_cache: Dict[str, Any] = {}
        self.aggregate_metrics = MCPUsageMetrics()
        
    async def collect_session_data(self, session_data: Dict[str, Any]):
        """Collect metrics from a completed agent session"""
        try:
            session_id = session_data.get('session_id')
            if not session_id:
                logger.warning("Session data missing session_id")
                return
            
            # Save raw session data
            session_file = self.metrics_dir / f"{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            # Update cache
            self.session_cache[session_id] = session_data
            
            # Update aggregate metrics
            await self._update_aggregate_metrics(session_data)
            
            logger.debug(f"Collected session data for {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to collect session data: {e}")
    
    async def _update_aggregate_metrics(self, session_data: Dict[str, Any]):
        """Update aggregate metrics with new session data"""
        tool_usage = session_data.get('tool_usage', [])
        metrics = session_data.get('metrics', {}).get('usage_metrics', {})
        
        # Update totals
        self.aggregate_metrics.total_sessions += 1
        self.aggregate_metrics.total_tool_calls += metrics.get('total_calls', 0)
        self.aggregate_metrics.successful_calls += metrics.get('successful_calls', 0)
        self.aggregate_metrics.failed_calls += metrics.get('failed_calls', 0)
        
        # Recalculate success rate
        if self.aggregate_metrics.total_tool_calls > 0:
            self.aggregate_metrics.success_rate = (
                self.aggregate_metrics.successful_calls / 
                self.aggregate_metrics.total_tool_calls
            )
        
        # Update execution time average
        session_avg_time = session_data.get('metrics', {}).get('average_execution_time_ms', 0)
        if session_avg_time > 0:
            # Weighted average based on number of calls
            total_sessions = self.aggregate_metrics.total_sessions
            current_avg = self.aggregate_metrics.average_execution_time_ms
            
            self.aggregate_metrics.average_execution_time_ms = (
                (current_avg * (total_sessions - 1) + session_avg_time) / total_sessions
            )
        
        # Update server and tool usage counts
        servers_used = metrics.get('servers_used', [])
        tools_used = metrics.get('tools_used', [])
        
        # Update server counts
        server_counter = Counter(dict(self.aggregate_metrics.most_used_servers))
        for server in servers_used:
            server_counter[server] += 1
        self.aggregate_metrics.most_used_servers = server_counter.most_common(10)
        
        # Update tool counts
        tool_counter = Counter(dict(self.aggregate_metrics.most_used_tools))
        for tool in tools_used:
            tool_counter[tool] += 1
        self.aggregate_metrics.most_used_tools = tool_counter.most_common(20)
        
        # Update agent performance
        agent_id = session_data.get('agent_type')
        if agent_id:
            await self._update_agent_performance(agent_id, session_data)
        
        # Update error patterns
        errors = session_data.get('errors', [])
        for error in errors:
            # Extract error type from message
            error_type = self._categorize_error(error)
            self.aggregate_metrics.error_patterns[error_type] = (
                self.aggregate_metrics.error_patterns.get(error_type, 0) + 1
            )
    
    async def _update_agent_performance(self, agent_id: str, session_data: Dict[str, Any]):
        """Update performance metrics for a specific agent"""
        if agent_id not in self.aggregate_metrics.agent_performance:
            self.aggregate_metrics.agent_performance[agent_id] = {
                'total_sessions': 0,
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'success_rate': 0.0,
                'average_execution_time': 0.0,
                'servers_used': Counter(),
                'tools_used': Counter(),
                'common_errors': Counter()
            }
        
        agent_perf = self.aggregate_metrics.agent_performance[agent_id]
        metrics = session_data.get('metrics', {}).get('usage_metrics', {})
        
        # Update counts
        agent_perf['total_sessions'] += 1
        agent_perf['total_calls'] += metrics.get('total_calls', 0)
        agent_perf['successful_calls'] += metrics.get('successful_calls', 0)
        agent_perf['failed_calls'] += metrics.get('failed_calls', 0)
        
        # Update success rate
        if agent_perf['total_calls'] > 0:
            agent_perf['success_rate'] = agent_perf['successful_calls'] / agent_perf['total_calls']
        
        # Update execution time
        session_avg_time = session_data.get('metrics', {}).get('average_execution_time_ms', 0)
        if session_avg_time > 0:
            total_sessions = agent_perf['total_sessions']
            current_avg = agent_perf['average_execution_time']
            
            agent_perf['average_execution_time'] = (
                (current_avg * (total_sessions - 1) + session_avg_time) / total_sessions
            )
        
        # Update servers and tools
        for server in metrics.get('servers_used', []):
            agent_perf['servers_used'][server] += 1
        
        for tool in metrics.get('tools_used', []):
            agent_perf['tools_used'][tool] += 1
        
        # Update errors
        for error in session_data.get('errors', []):
            error_type = self._categorize_error(error)
            agent_perf['common_errors'][error_type] += 1
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorize error message into type"""
        error_lower = error_message.lower()
        
        if 'permission' in error_lower or 'denied' in error_lower:
            return 'Permission Denied'
        elif 'timeout' in error_lower:
            return 'Timeout'
        elif 'connection' in error_lower or 'network' in error_lower:
            return 'Connection Error'
        elif 'not found' in error_lower or '404' in error_lower:
            return 'Resource Not Found'
        elif 'invalid' in error_lower or 'malformed' in error_lower:
            return 'Invalid Request'
        elif 'server error' in error_lower or '500' in error_lower:
            return 'Server Error'
        else:
            return 'Other Error'
    
    async def load_historical_data(self) -> None:
        """Load all historical session data for analysis"""
        try:
            session_files = list(self.metrics_dir.glob("*.json"))
            
            logger.info(f"Loading {len(session_files)} historical session files")
            
            # Reset metrics
            self.aggregate_metrics = MCPUsageMetrics()
            self.session_cache = {}
            
            for session_file in session_files:
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    session_id = session_data.get('session_id')
                    if session_id:
                        self.session_cache[session_id] = session_data
                        await self._update_aggregate_metrics(session_data)
                        
                except Exception as e:
                    logger.warning(f"Failed to load {session_file}: {e}")
            
            logger.info(f"Loaded metrics for {len(self.session_cache)} sessions")
            
        except Exception as e:
            logger.error(f"Failed to load historical data: {e}")
    
    async def generate_usage_report(self) -> Dict[str, Any]:
        """Generate comprehensive usage report"""
        await self.load_historical_data()
        
        # Calculate additional metrics
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_sessions': self.aggregate_metrics.total_sessions,
                'total_tool_calls': self.aggregate_metrics.total_tool_calls,
                'success_rate': f"{self.aggregate_metrics.success_rate:.1%}",
                'average_execution_time_ms': f"{self.aggregate_metrics.average_execution_time_ms:.1f}",
                'most_active_agents': self._get_most_active_agents(),
                'server_reliability': await self._calculate_server_reliability()
            },
            'usage_patterns': {
                'most_used_servers': dict(self.aggregate_metrics.most_used_servers[:10]),
                'most_used_tools': dict(self.aggregate_metrics.most_used_tools[:15]),
                'error_distribution': dict(self.aggregate_metrics.error_patterns),
                'agent_preferences': await self._analyze_agent_preferences()
            },
            'performance_metrics': {
                'top_performing_agents': await self._get_top_performing_agents(),
                'server_response_times': await self._analyze_server_performance(),
                'efficiency_trends': await self._calculate_efficiency_trends()
            },
            'recommendations': await self._generate_recommendations()
        }
        
        return report
    
    def _get_most_active_agents(self) -> List[tuple]:
        """Get agents ordered by total activity"""
        agent_activity = []
        for agent_id, perf in self.aggregate_metrics.agent_performance.items():
            agent_activity.append((agent_id, perf['total_calls']))
        
        return sorted(agent_activity, key=lambda x: x[1], reverse=True)[:10]
    
    async def _calculate_server_reliability(self) -> Dict[str, float]:
        """Calculate reliability score for each server"""
        server_stats = defaultdict(lambda: {'total': 0, 'successful': 0})
        
        for session_data in self.session_cache.values():
            tool_usage = session_data.get('tool_usage', [])
            for usage in tool_usage:
                server = usage.get('server_name')
                if server:
                    server_stats[server]['total'] += 1
                    if usage.get('success'):
                        server_stats[server]['successful'] += 1
        
        reliability = {}
        for server, stats in server_stats.items():
            if stats['total'] > 0:
                reliability[server] = stats['successful'] / stats['total']
        
        return reliability
    
    async def _analyze_agent_preferences(self) -> Dict[str, Dict]:
        """Analyze which servers/tools each agent prefers"""
        preferences = {}
        
        for agent_id, perf in self.aggregate_metrics.agent_performance.items():
            preferences[agent_id] = {
                'preferred_servers': dict(perf['servers_used'].most_common(3)),
                'preferred_tools': dict(perf['tools_used'].most_common(5))
            }
        
        return preferences
    
    async def _get_top_performing_agents(self) -> List[Dict]:
        """Get agents with best performance metrics"""
        performers = []
        
        for agent_id, perf in self.aggregate_metrics.agent_performance.items():
            if perf['total_calls'] >= 5:  # Minimum threshold for consideration
                efficiency = perf['total_calls'] / perf['total_sessions'] if perf['total_sessions'] > 0 else 0
                
                performers.append({
                    'agent_id': agent_id,
                    'success_rate': perf['success_rate'],
                    'efficiency': efficiency,
                    'avg_execution_time': perf['average_execution_time'],
                    'total_calls': perf['total_calls']
                })
        
        # Sort by success rate first, then efficiency
        performers.sort(key=lambda x: (x['success_rate'], x['efficiency']), reverse=True)
        return performers[:10]
    
    async def _analyze_server_performance(self) -> Dict[str, Dict]:
        """Analyze performance metrics for each server"""
        server_perf = defaultdict(lambda: {'response_times': [], 'call_count': 0, 'error_count': 0})
        
        for session_data in self.session_cache.values():
            tool_usage = session_data.get('tool_usage', [])
            for usage in tool_usage:
                server = usage.get('server_name')
                if server:
                    server_perf[server]['call_count'] += 1
                    
                    if usage.get('success'):
                        exec_time = usage.get('execution_time_ms', 0)
                        if exec_time > 0:
                            server_perf[server]['response_times'].append(exec_time)
                    else:
                        server_perf[server]['error_count'] += 1
        
        # Calculate statistics
        performance = {}
        for server, data in server_perf.items():
            response_times = data['response_times']
            performance[server] = {
                'total_calls': data['call_count'],
                'error_count': data['error_count'],
                'avg_response_time': statistics.mean(response_times) if response_times else 0,
                'median_response_time': statistics.median(response_times) if response_times else 0,
                'p95_response_time': (
                    statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0
                )
            }
        
        return dict(performance)
    
    async def _calculate_efficiency_trends(self) -> Dict[str, Any]:
        """Calculate efficiency trends over time"""
        # Group sessions by date
        daily_stats = defaultdict(lambda: {'sessions': 0, 'calls': 0, 'successes': 0})
        
        for session_data in self.session_cache.values():
            # Parse timestamp
            start_time = session_data.get('start_time', '')
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                date_key = dt.date().isoformat()
                
                metrics = session_data.get('metrics', {}).get('usage_metrics', {})
                daily_stats[date_key]['sessions'] += 1
                daily_stats[date_key]['calls'] += metrics.get('total_calls', 0)
                daily_stats[date_key]['successes'] += metrics.get('successful_calls', 0)
                
            except Exception:
                continue
        
        # Calculate trends
        trends = {}
        sorted_dates = sorted(daily_stats.keys())
        
        for date in sorted_dates[-30:]:  # Last 30 days
            stats = daily_stats[date]
            success_rate = stats['successes'] / stats['calls'] if stats['calls'] > 0 else 0
            efficiency = stats['calls'] / stats['sessions'] if stats['sessions'] > 0 else 0
            
            trends[date] = {
                'sessions': stats['sessions'],
                'calls': stats['calls'],
                'success_rate': success_rate,
                'efficiency': efficiency
            }
        
        return trends
    
    async def _generate_recommendations(self) -> List[Dict]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        # Server reliability recommendations
        server_reliability = await self._calculate_server_reliability()
        unreliable_servers = [s for s, r in server_reliability.items() if r < 0.8]
        
        if unreliable_servers:
            recommendations.append({
                'category': 'Reliability',
                'priority': 'High',
                'title': 'Improve Server Reliability',
                'description': f"Servers with <80% success rate: {', '.join(unreliable_servers)}",
                'action': 'Review server configurations, network connectivity, and error handling'
            })
        
        # Performance recommendations
        server_perf = await self._analyze_server_performance()
        slow_servers = [s for s, p in server_perf.items() 
                       if p.get('avg_response_time', 0) > 5000]  # >5s average
        
        if slow_servers:
            recommendations.append({
                'category': 'Performance',
                'priority': 'Medium',
                'title': 'Optimize Slow Servers',
                'description': f"Servers with >5s average response time: {', '.join(slow_servers)}",
                'action': 'Investigate server performance bottlenecks and optimize'
            })
        
        # Usage pattern recommendations
        error_patterns = self.aggregate_metrics.error_patterns
        top_errors = sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
        
        if top_errors:
            recommendations.append({
                'category': 'Error Reduction',
                'priority': 'Medium',
                'title': 'Address Common Errors',
                'description': f"Most common errors: {', '.join([e[0] for e in top_errors])}",
                'action': 'Implement better error handling and user guidance for these scenarios'
            })
        
        return recommendations
    
    async def save_report(self, report: Dict[str, Any], format: str = 'json') -> Path:
        """Save usage report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            report_file = self.reports_dir / f"mcp_usage_report_{timestamp}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        elif format == 'yaml':
            report_file = self.reports_dir / f"mcp_usage_report_{timestamp}.yaml"
            with open(report_file, 'w') as f:
                yaml.dump(report, f, default_flow_style=False)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Usage report saved to {report_file}")
        return report_file
    
    async def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for a dashboard display"""
        await self.load_historical_data()
        
        # Recent activity (last 7 days)
        recent_sessions = []
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        
        for session_data in self.session_cache.values():
            start_time = session_data.get('start_time', '')
            try:
                dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if dt >= week_ago:
                    recent_sessions.append(session_data)
            except:
                continue
        
        dashboard = {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'overview': {
                'total_sessions': self.aggregate_metrics.total_sessions,
                'recent_sessions': len(recent_sessions),
                'success_rate': self.aggregate_metrics.success_rate,
                'avg_execution_time': self.aggregate_metrics.average_execution_time_ms
            },
            'top_agents': self._get_most_active_agents()[:5],
            'top_servers': dict(self.aggregate_metrics.most_used_servers[:5]),
            'recent_errors': list(self.aggregate_metrics.error_patterns.keys())[:5],
            'server_status': await self._get_server_status()
        }
        
        return dashboard
    
    async def _get_server_status(self) -> Dict[str, str]:
        """Get current status of servers based on recent activity"""
        server_reliability = await self._calculate_server_reliability()
        
        status = {}
        for server, reliability in server_reliability.items():
            if reliability >= 0.95:
                status[server] = "Excellent"
            elif reliability >= 0.8:
                status[server] = "Good"
            elif reliability >= 0.6:
                status[server] = "Fair"
            else:
                status[server] = "Poor"
        
        return status