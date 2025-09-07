#!/usr/bin/env python3
"""
CoralCollective MCP Server Monitor
Real-time monitoring and alerting for MCP servers
"""

import os
import sys
import json
import time
import yaml
import signal
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psutil
except ImportError:
    print("⚠️  psutil not found. Install with: pip install psutil")
    psutil = None


@dataclass
class ServerMetrics:
    """Server performance metrics"""
    timestamp: datetime
    pid: Optional[int]
    cpu_percent: float
    memory_mb: float
    status: str  # 'running', 'stopped', 'error'
    uptime_seconds: float
    error_count: int
    response_time_ms: Optional[float] = None


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str  # 'cpu_percent', 'memory_mb', 'error_count', etc.
    operator: str  # '>', '<', '>=', '<=', '=='
    threshold: float
    duration_seconds: int  # How long condition must persist
    enabled: bool = True


class Colors:
    """Terminal color codes"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class MCPServerMonitor:
    """Real-time MCP server monitoring system"""
    
    def __init__(self, mcp_dir: Optional[Path] = None, update_interval: int = 5):
        self.mcp_dir = mcp_dir or Path(__file__).parent.parent
        self.update_interval = update_interval
        self.config_file = self.mcp_dir / "configs" / "mcp_config.yaml"
        self.log_dir = self.mcp_dir / "logs"
        self.monitoring_dir = self.mcp_dir / "monitoring"
        self.monitoring_dir.mkdir(exist_ok=True)
        
        # Monitoring state
        self.server_metrics: Dict[str, deque] = {}
        self.server_processes: Dict[str, Optional[psutil.Process]] = {}
        self.alert_states: Dict[str, Dict[str, datetime]] = {}
        self.running = False
        
        # Load configuration
        self.config = self._load_config()
        self.servers = self._get_enabled_servers()
        self.alert_rules = self._load_alert_rules()
        
        # Initialize metrics storage
        for server_name in self.servers:
            self.server_metrics[server_name] = deque(maxlen=720)  # Store last 1 hour at 5s intervals
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP configuration"""
        try:
            if not self.config_file.exists():
                return {"mcp_servers": {}}
                
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.NC} Failed to load config: {e}")
            return {"mcp_servers": {}}
    
    def _get_enabled_servers(self) -> List[str]:
        """Get list of enabled servers"""
        enabled = []
        for name, config in self.config.get("mcp_servers", {}).items():
            if config.get("enabled", False):
                enabled.append(name)
        return enabled
    
    def _load_alert_rules(self) -> List[AlertRule]:
        """Load alert rules from configuration"""
        # Default alert rules
        default_rules = [
            AlertRule("High CPU Usage", "cpu_percent", ">", 80.0, 30, True),
            AlertRule("High Memory Usage", "memory_mb", ">", 500.0, 60, True),
            AlertRule("Server Down", "status", "==", "stopped", 10, True),
            AlertRule("Error Spike", "error_count", ">", 5, 30, True),
            AlertRule("Slow Response", "response_time_ms", ">", 5000, 60, True),
        ]
        
        # Load custom rules from monitoring config if exists
        monitor_config_file = self.monitoring_dir / "alert_rules.yaml"
        if monitor_config_file.exists():
            try:
                with open(monitor_config_file, 'r') as f:
                    custom_config = yaml.safe_load(f)
                    custom_rules = [
                        AlertRule(**rule) for rule in custom_config.get("alert_rules", [])
                    ]
                    return custom_rules
            except Exception as e:
                print(f"{Colors.YELLOW}[WARN]{Colors.NC} Failed to load custom alert rules: {e}")
        
        return default_rules
    
    def _get_server_process(self, server_name: str) -> Optional[psutil.Process]:
        """Find server process by PID file"""
        if not psutil:
            return None
            
        pid_file = self.log_dir / f"{server_name}_server.pid"
        if not pid_file.exists():
            return None
        
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                # Verify it's actually our server process
                if any(server_name in arg for arg in proc.cmdline()):
                    return proc
        except Exception:
            pass
        
        return None
    
    def _collect_server_metrics(self, server_name: str) -> ServerMetrics:
        """Collect metrics for a specific server"""
        timestamp = datetime.now(timezone.utc)
        
        # Get process handle
        proc = self._get_server_process(server_name)
        self.server_processes[server_name] = proc
        
        if not proc:
            return ServerMetrics(
                timestamp=timestamp,
                pid=None,
                cpu_percent=0.0,
                memory_mb=0.0,
                status='stopped',
                uptime_seconds=0.0,
                error_count=0
            )
        
        try:
            # Collect process metrics
            cpu_percent = proc.cpu_percent()
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            
            # Calculate uptime
            create_time = proc.create_time()
            uptime_seconds = time.time() - create_time
            
            # Count recent errors from log file
            error_count = self._count_recent_errors(server_name)
            
            # Measure response time (simple TCP check if applicable)
            response_time_ms = self._measure_response_time(server_name)
            
            return ServerMetrics(
                timestamp=timestamp,
                pid=proc.pid,
                cpu_percent=cpu_percent,
                memory_mb=memory_mb,
                status='running',
                uptime_seconds=uptime_seconds,
                error_count=error_count,
                response_time_ms=response_time_ms
            )
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            return ServerMetrics(
                timestamp=timestamp,
                pid=None,
                cpu_percent=0.0,
                memory_mb=0.0,
                status='error',
                uptime_seconds=0.0,
                error_count=0
            )
    
    def _count_recent_errors(self, server_name: str, minutes: int = 5) -> int:
        """Count errors in server log from last N minutes"""
        log_file = self.log_dir / f"{server_name}_server.log"
        if not log_file.exists():
            return 0
        
        try:
            cutoff_time = time.time() - (minutes * 60)
            error_count = 0
            
            # Read last 1000 lines to avoid processing huge files
            with open(log_file, 'r') as f:
                lines = deque(f, maxlen=1000)
            
            for line in lines:
                if 'error' in line.lower() or 'exception' in line.lower():
                    # Try to extract timestamp and check if recent
                    # This is a simple heuristic - adjust based on actual log format
                    error_count += 1
            
            return error_count
            
        except Exception:
            return 0
    
    def _measure_response_time(self, server_name: str) -> Optional[float]:
        """Measure server response time (basic health check)"""
        # For now, just return None as MCP servers don't have standard health endpoints
        # This could be enhanced to test actual MCP protocol connectivity
        return None
    
    def _check_alerts(self, server_name: str, metrics: ServerMetrics):
        """Check alert rules against current metrics"""
        current_time = datetime.now(timezone.utc)
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # Get metric value
            metric_value = getattr(metrics, rule.metric, None)
            if metric_value is None:
                continue
            
            # Check threshold
            triggered = False
            if rule.operator == '>':
                triggered = metric_value > rule.threshold
            elif rule.operator == '<':
                triggered = metric_value < rule.threshold
            elif rule.operator == '>=':
                triggered = metric_value >= rule.threshold
            elif rule.operator == '<=':
                triggered = metric_value <= rule.threshold
            elif rule.operator == '==':
                triggered = str(metric_value) == str(rule.threshold)
            
            alert_key = f"{server_name}:{rule.name}"
            
            if triggered:
                # Track when alert first triggered
                if alert_key not in self.alert_states:
                    self.alert_states[alert_key] = current_time
                
                # Check if alert has been triggered long enough
                trigger_duration = (current_time - self.alert_states[alert_key]).total_seconds()
                if trigger_duration >= rule.duration_seconds:
                    self._fire_alert(server_name, rule, metrics, trigger_duration)
            else:
                # Clear alert state if condition no longer met
                if alert_key in self.alert_states:
                    del self.alert_states[alert_key]
    
    def _fire_alert(self, server_name: str, rule: AlertRule, metrics: ServerMetrics, duration: float):
        """Fire an alert"""
        alert_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'server': server_name,
            'rule': rule.name,
            'metric': rule.metric,
            'threshold': rule.threshold,
            'current_value': getattr(metrics, rule.metric),
            'duration_seconds': duration,
            'severity': self._get_alert_severity(rule),
            'metrics': asdict(metrics)
        }
        
        # Log alert
        alert_file = self.monitoring_dir / "alerts.jsonl"
        with open(alert_file, 'a') as f:
            json.dump(alert_data, f)
            f.write('\n')
        
        # Print to console
        severity_color = {
            'critical': Colors.RED,
            'warning': Colors.YELLOW,
            'info': Colors.BLUE
        }.get(alert_data['severity'], Colors.NC)
        
        print(f"\n{severity_color}🚨 ALERT: {rule.name}{Colors.NC}")
        print(f"  Server: {server_name}")
        print(f"  {rule.metric}: {alert_data['current_value']} (threshold: {rule.threshold})")
        print(f"  Duration: {duration:.1f}s")
    
    def _get_alert_severity(self, rule: AlertRule) -> str:
        """Determine alert severity"""
        if 'down' in rule.name.lower() or 'stopped' in rule.name.lower():
            return 'critical'
        elif 'high' in rule.name.lower() or 'error' in rule.name.lower():
            return 'warning'
        else:
            return 'info'
    
    def _display_dashboard(self):
        """Display real-time monitoring dashboard"""
        # Clear screen
        os.system('clear')
        
        print(f"{Colors.CYAN}{Colors.BOLD}🪸 CoralCollective MCP Server Monitor{Colors.NC}")
        print(f"{'=' * 60}")
        print(f"Update Interval: {self.update_interval}s | Press Ctrl+C to exit")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Server status table
        print(f"{Colors.BOLD}Server Status:{Colors.NC}")
        print(f"{'Server':<15} {'Status':<10} {'PID':<8} {'CPU%':<8} {'Memory':<10} {'Uptime':<10} {'Errors':<8}")
        print("-" * 80)
        
        for server_name in self.servers:
            metrics_queue = self.server_metrics.get(server_name, deque())
            if not metrics_queue:
                print(f"{server_name:<15} {'NO DATA':<10} {'-':<8} {'-':<8} {'-':<10} {'-':<10} {'-':<8}")
                continue
            
            latest = metrics_queue[-1]
            
            # Status color
            status_color = {
                'running': Colors.GREEN,
                'stopped': Colors.RED,
                'error': Colors.YELLOW
            }.get(latest.status, Colors.NC)
            
            # Format values
            pid_str = str(latest.pid) if latest.pid else '-'
            cpu_str = f"{latest.cpu_percent:.1f}" if latest.status == 'running' else '-'
            memory_str = f"{latest.memory_mb:.1f}MB" if latest.status == 'running' else '-'
            uptime_str = self._format_uptime(latest.uptime_seconds) if latest.status == 'running' else '-'
            error_str = str(latest.error_count) if latest.error_count > 0 else '-'
            
            print(f"{server_name:<15} {status_color}{latest.status.upper():<10}{Colors.NC} "
                  f"{pid_str:<8} {cpu_str:<8} {memory_str:<10} {uptime_str:<10} {error_str:<8}")
        
        # Active alerts
        if self.alert_states:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}Active Alerts:{Colors.NC}")
            for alert_key in self.alert_states:
                server, rule_name = alert_key.split(':', 1)
                duration = (datetime.now(timezone.utc) - self.alert_states[alert_key]).total_seconds()
                print(f"  🚨 {server}: {rule_name} (for {duration:.0f}s)")
        
        # Recent metrics (mini graph)
        print(f"\n{Colors.BOLD}Recent CPU Usage (last 10 samples):{Colors.NC}")
        for server_name in self.servers[:5]:  # Show first 5 servers
            metrics_queue = self.server_metrics.get(server_name, deque())
            if len(metrics_queue) < 2:
                continue
            
            recent_cpu = [m.cpu_percent for m in list(metrics_queue)[-10:]]
            graph = self._create_mini_graph(recent_cpu, max_value=100.0)
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            print(f"  {server_name:<15} {graph} (avg: {avg_cpu:.1f}%)")
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.0f}m"
        else:
            return f"{seconds/3600:.1f}h"
    
    def _create_mini_graph(self, values: List[float], max_value: float, width: int = 20) -> str:
        """Create a mini ASCII graph"""
        if not values:
            return " " * width
        
        normalized = [min(v / max_value, 1.0) for v in values]
        
        # Create graph with different characters for different ranges
        graph = ""
        for val in normalized[-width:]:  # Take last 'width' values
            if val > 0.8:
                graph += "█"
            elif val > 0.6:
                graph += "▆"
            elif val > 0.4:
                graph += "▄"
            elif val > 0.2:
                graph += "▂"
            elif val > 0:
                graph += "▁"
            else:
                graph += " "
        
        # Pad to width
        return graph.ljust(width)
    
    def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print(f"{Colors.GREEN}Starting MCP server monitoring...{Colors.NC}")
        print(f"Monitoring {len(self.servers)} servers: {', '.join(self.servers)}")
        print(f"Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                # Collect metrics for all servers
                for server_name in self.servers:
                    metrics = self._collect_server_metrics(server_name)
                    self.server_metrics[server_name].append(metrics)
                    
                    # Check alerts
                    self._check_alerts(server_name, metrics)
                
                # Display dashboard
                self._display_dashboard()
                
                # Save metrics snapshot
                self._save_metrics_snapshot()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()
    
    def _save_metrics_snapshot(self):
        """Save current metrics to file"""
        snapshot = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'servers': {}
        }
        
        for server_name, metrics_queue in self.server_metrics.items():
            if metrics_queue:
                latest = metrics_queue[-1]
                snapshot['servers'][server_name] = asdict(latest)
                # Convert datetime to ISO string
                snapshot['servers'][server_name]['timestamp'] = latest.timestamp.isoformat()
        
        snapshot_file = self.monitoring_dir / "current_metrics.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n{Colors.YELLOW}Shutting down monitor...{Colors.NC}")
        self.running = False
    
    def _cleanup(self):
        """Cleanup on exit"""
        print(f"{Colors.GREEN}Monitor stopped.{Colors.NC}")
        
        # Save final metrics
        self._save_metrics_snapshot()
        
        # Save historical data
        history_file = self.monitoring_dir / f"metrics_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        historical_data = {}
        for server_name, metrics_queue in self.server_metrics.items():
            historical_data[server_name] = [
                {**asdict(m), 'timestamp': m.timestamp.isoformat()}
                for m in metrics_queue
            ]
        
        with open(history_file, 'w') as f:
            json.dump(historical_data, f, indent=2)
        
        print(f"Historical data saved to: {history_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CoralCollective MCP Server Monitor')
    parser.add_argument('--interval', type=int, default=5, help='Update interval in seconds (default: 5)')
    parser.add_argument('--mcp-dir', type=str, help='MCP directory path')
    parser.add_argument('--once', action='store_true', help='Run once and exit (no dashboard)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    # Initialize monitor
    mcp_dir = Path(args.mcp_dir) if args.mcp_dir else None
    monitor = MCPServerMonitor(mcp_dir, args.interval)
    
    if args.once:
        # Single monitoring run
        metrics_data = {}
        for server_name in monitor.servers:
            metrics = monitor._collect_server_metrics(server_name)
            metrics_data[server_name] = {
                **asdict(metrics),
                'timestamp': metrics.timestamp.isoformat()
            }
        
        if args.json:
            print(json.dumps(metrics_data, indent=2))
        else:
            print(f"MCP Server Metrics - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 50)
            for server_name, data in metrics_data.items():
                print(f"{server_name}: {data['status']} (PID: {data['pid']}, CPU: {data['cpu_percent']:.1f}%)")
    else:
        # Start continuous monitoring
        monitor.start_monitoring()


if __name__ == '__main__':
    main()