#!/usr/bin/env python3
"""
CoralCollective MCP Health Check System
Comprehensive health monitoring and diagnostics for MCP servers
"""

import os
import sys
import json
import time
import yaml
import subprocess
import tempfile
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import dotenv
    from dotenv import load_dotenv
except ImportError:
    print("⚠️  python-dotenv not found. Install with: pip install python-dotenv")
    dotenv = None


@dataclass
class HealthCheckResult:
    """Result of a health check operation"""
    server_name: str
    status: str  # 'healthy', 'unhealthy', 'warning', 'unknown'
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration_ms: float


@dataclass
class ServerConfig:
    """MCP Server configuration"""
    name: str
    enabled: bool
    command: str
    args: List[str]
    env_vars: Dict[str, str]
    required_env: List[str]
    permissions: List[str]


class Colors:
    """Terminal color codes"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class MCPHealthChecker:
    """Comprehensive MCP server health checker"""
    
    def __init__(self, mcp_dir: Optional[Path] = None):
        self.mcp_dir = mcp_dir or Path(__file__).parent.parent
        self.config_file = self.mcp_dir / "configs" / "mcp_config.yaml"
        self.env_file = self.mcp_dir / ".env"
        self.log_dir = self.mcp_dir / "logs"
        self.results: List[HealthCheckResult] = []
        
        # Load environment variables
        if dotenv and self.env_file.exists():
            load_dotenv(self.env_file)
        
        # Load MCP configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP configuration from YAML file"""
        try:
            if not self.config_file.exists():
                return {"mcp_servers": {}}
                
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.NC} Failed to load config: {e}")
            return {"mcp_servers": {}}
    
    def _get_server_config(self, server_name: str) -> Optional[ServerConfig]:
        """Extract server configuration"""
        server_conf = self.config.get("mcp_servers", {}).get(server_name)
        if not server_conf:
            return None
            
        return ServerConfig(
            name=server_name,
            enabled=server_conf.get("enabled", False),
            command=server_conf.get("command", "npx"),
            args=server_conf.get("args", []),
            env_vars=server_conf.get("env", {}),
            required_env=self._extract_env_vars(server_conf.get("env", {})),
            permissions=server_conf.get("permissions", [])
        )
    
    def _extract_env_vars(self, env_dict: Dict[str, str]) -> List[str]:
        """Extract required environment variable names from config"""
        env_vars = []
        for value in env_dict.values():
            if isinstance(value, str) and "${" in value and "}" in value:
                # Extract variable name from ${VAR_NAME} format
                start = value.find("${") + 2
                end = value.find("}", start)
                if end > start:
                    env_vars.append(value[start:end])
        return env_vars
    
    def check_prerequisites(self) -> HealthCheckResult:
        """Check system prerequisites"""
        start_time = time.time()
        details = {}
        issues = []
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
            node_version = result.stdout.strip()
            details['node_version'] = node_version
            
            # Check minimum version (18+)
            version_num = int(node_version.lstrip('v').split('.')[0])
            if version_num < 18:
                issues.append(f"Node.js version too old: {node_version} (minimum: v18)")
        except Exception as e:
            issues.append(f"Node.js not found: {e}")
        
        # Check npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True, timeout=5)
            details['npm_version'] = result.stdout.strip()
        except Exception as e:
            issues.append(f"npm not found: {e}")
        
        # Check npx
        try:
            subprocess.run(['npx', '--version'], capture_output=True, timeout=5, check=True)
            details['npx_available'] = True
        except Exception:
            issues.append("npx not available")
            details['npx_available'] = False
        
        # Check Python (for this script)
        details['python_version'] = sys.version
        details['python_path'] = sys.executable
        
        # Check environment file
        if self.env_file.exists():
            details['env_file'] = str(self.env_file)
            details['env_file_exists'] = True
        else:
            issues.append(f"Environment file not found: {self.env_file}")
            details['env_file_exists'] = False
        
        # Check config file
        if self.config_file.exists():
            details['config_file'] = str(self.config_file)
            details['config_file_exists'] = True
        else:
            issues.append(f"Config file not found: {self.config_file}")
            details['config_file_exists'] = False
        
        duration_ms = (time.time() - start_time) * 1000
        
        if issues:
            status = 'unhealthy'
            message = f"Prerequisites check failed: {'; '.join(issues)}"
        else:
            status = 'healthy'
            message = "All prerequisites satisfied"
        
        return HealthCheckResult(
            server_name='prerequisites',
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms
        )
    
    def check_environment(self) -> HealthCheckResult:
        """Check environment variables"""
        start_time = time.time()
        details = {}
        issues = []
        warnings = []
        
        # Get all server configs and required env vars
        all_required_env = set()
        for server_name in self.config.get("mcp_servers", {}):
            server_conf = self._get_server_config(server_name)
            if server_conf and server_conf.enabled:
                all_required_env.update(server_conf.required_env)
        
        # Check each required environment variable
        for env_var in all_required_env:
            value = os.getenv(env_var)
            if not value:
                issues.append(f"Missing required environment variable: {env_var}")
                details[f'{env_var}_status'] = 'missing'
            elif 'your_' in value.lower() and '_here' in value.lower():
                warnings.append(f"Environment variable has placeholder value: {env_var}")
                details[f'{env_var}_status'] = 'placeholder'
            else:
                details[f'{env_var}_status'] = 'configured'
        
        # Check specific configurations
        project_root = os.getenv('PROJECT_ROOT')
        if project_root:
            if not Path(project_root).exists():
                issues.append(f"PROJECT_ROOT path does not exist: {project_root}")
            details['project_root'] = project_root
            details['project_root_exists'] = Path(project_root).exists()
        
        duration_ms = (time.time() - start_time) * 1000
        
        if issues:
            status = 'unhealthy'
            message = f"Environment issues: {'; '.join(issues)}"
        elif warnings:
            status = 'warning'
            message = f"Environment warnings: {'; '.join(warnings)}"
        else:
            status = 'healthy'
            message = "Environment configuration is valid"
        
        return HealthCheckResult(
            server_name='environment',
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms
        )
    
    def check_server(self, server_name: str) -> HealthCheckResult:
        """Check individual MCP server"""
        start_time = time.time()
        details = {}
        
        server_conf = self._get_server_config(server_name)
        if not server_conf:
            return HealthCheckResult(
                server_name=server_name,
                status='unknown',
                message=f"Server configuration not found",
                details={'configured': False},
                timestamp=datetime.now(timezone.utc),
                duration_ms=(time.time() - start_time) * 1000
            )
        
        details['enabled'] = server_conf.enabled
        details['command'] = server_conf.command
        details['args'] = server_conf.args
        details['required_env'] = server_conf.required_env
        
        if not server_conf.enabled:
            return HealthCheckResult(
                server_name=server_name,
                status='warning',
                message="Server is disabled in configuration",
                details=details,
                timestamp=datetime.now(timezone.utc),
                duration_ms=(time.time() - start_time) * 1000
            )
        
        # Check if server package is installed
        package_name = server_conf.args[0] if server_conf.args else f"@modelcontextprotocol/server-{server_name}"
        
        try:
            # Try to run the server with --help to check availability
            cmd = [server_conf.command] + server_conf.args + ['--help']
            
            # Prepare environment
            env = os.environ.copy()
            for key, value in server_conf.env_vars.items():
                # Resolve environment variable references
                if "${" in value and "}" in value:
                    start_idx = value.find("${") + 2
                    end_idx = value.find("}", start_idx)
                    if end_idx > start_idx:
                        env_var_name = value[start_idx:end_idx]
                        env_value = os.getenv(env_var_name, "")
                        env[key] = value.replace(f"${{{env_var_name}}}", env_value)
                else:
                    env[key] = value
            
            # Run the command with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            
            details['exit_code'] = result.returncode
            details['stdout_preview'] = result.stdout[:200] + '...' if len(result.stdout) > 200 else result.stdout
            details['stderr_preview'] = result.stderr[:200] + '...' if len(result.stderr) > 200 else result.stderr
            
            # Most MCP servers return 0 or 1 when run with --help
            if result.returncode in [0, 1]:
                status = 'healthy'
                message = f"Server is available and responsive"
            else:
                status = 'warning'
                message = f"Server responded but with unexpected exit code: {result.returncode}"
            
        except subprocess.TimeoutExpired:
            status = 'unhealthy'
            message = "Server check timed out"
            details['timeout'] = True
            
        except FileNotFoundError:
            status = 'unhealthy'
            message = f"Server package not found: {package_name}"
            details['package_found'] = False
            
        except Exception as e:
            status = 'unhealthy'
            message = f"Server check failed: {str(e)}"
            details['error'] = str(e)
        
        # Check log files
        log_file = self.log_dir / f"{server_name}_server.log"
        pid_file = self.log_dir / f"{server_name}_server.pid"
        
        details['log_file_exists'] = log_file.exists()
        details['pid_file_exists'] = pid_file.exists()
        
        if log_file.exists():
            try:
                stat = log_file.stat()
                details['log_file_size'] = stat.st_size
                details['log_file_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                pass
        
        duration_ms = (time.time() - start_time) * 1000
        
        return HealthCheckResult(
            server_name=server_name,
            status=status,
            message=message,
            details=details,
            timestamp=datetime.now(timezone.utc),
            duration_ms=duration_ms
        )
    
    def check_all_servers(self) -> List[HealthCheckResult]:
        """Check all configured MCP servers"""
        server_names = list(self.config.get("mcp_servers", {}).keys())
        
        # Use thread pool for concurrent checking
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_server = {
                executor.submit(self.check_server, server_name): server_name
                for server_name in server_names
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_server):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    server_name = future_to_server[future]
                    results.append(HealthCheckResult(
                        server_name=server_name,
                        status='unhealthy',
                        message=f"Health check failed: {str(e)}",
                        details={'error': str(e)},
                        timestamp=datetime.now(timezone.utc),
                        duration_ms=0
                    ))
            
            return results
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run comprehensive health check of entire MCP infrastructure"""
        print(f"{Colors.BLUE}{Colors.BOLD}🔍 CoralCollective MCP Health Check{Colors.NC}")
        print("=" * 50)
        print()
        
        start_time = time.time()
        all_results = []
        
        # Check prerequisites
        print(f"{Colors.BLUE}[1/3]{Colors.NC} Checking system prerequisites...")
        prereq_result = self.check_prerequisites()
        all_results.append(prereq_result)
        self._print_result(prereq_result)
        
        # Check environment
        print(f"\n{Colors.BLUE}[2/3]{Colors.NC} Checking environment configuration...")
        env_result = self.check_environment()
        all_results.append(env_result)
        self._print_result(env_result)
        
        # Check servers
        print(f"\n{Colors.BLUE}[3/3]{Colors.NC} Checking MCP servers...")
        server_results = self.check_all_servers()
        all_results.extend(server_results)
        
        for result in server_results:
            self._print_result(result)
        
        total_duration = (time.time() - start_time) * 1000
        
        # Generate summary
        summary = self._generate_summary(all_results, total_duration)
        
        print(f"\n{Colors.BOLD}Health Check Summary{Colors.NC}")
        print("-" * 30)
        self._print_summary(summary)
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'duration_ms': total_duration,
            'results': [
                {
                    'server_name': r.server_name,
                    'status': r.status,
                    'message': r.message,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat(),
                    'duration_ms': r.duration_ms
                }
                for r in all_results
            ],
            'summary': summary
        }
    
    def _print_result(self, result: HealthCheckResult):
        """Print a single health check result"""
        status_colors = {
            'healthy': Colors.GREEN,
            'warning': Colors.YELLOW,
            'unhealthy': Colors.RED,
            'unknown': Colors.BLUE
        }
        
        status_icons = {
            'healthy': '✓',
            'warning': '⚠',
            'unhealthy': '✗',
            'unknown': '?'
        }
        
        color = status_colors.get(result.status, Colors.NC)
        icon = status_icons.get(result.status, '?')
        
        duration_str = f"({result.duration_ms:.1f}ms)"
        
        print(f"  {color}{icon} {result.server_name.upper()}{Colors.NC}: {result.message} {duration_str}")
        
        # Print key details for unhealthy servers
        if result.status == 'unhealthy' and result.details:
            for key, value in result.details.items():
                if key in ['error', 'stderr_preview'] and value:
                    print(f"    {Colors.RED}└─{Colors.NC} {key}: {value}")
    
    def _generate_summary(self, results: List[HealthCheckResult], total_duration: float) -> Dict[str, Any]:
        """Generate health check summary"""
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        total_servers = len([r for r in results if r.server_name not in ['prerequisites', 'environment']])
        healthy_servers = len([r for r in results if r.status == 'healthy' and r.server_name not in ['prerequisites', 'environment']])
        
        return {
            'total_checks': len(results),
            'total_duration_ms': total_duration,
            'status_counts': status_counts,
            'total_servers': total_servers,
            'healthy_servers': healthy_servers,
            'health_percentage': (healthy_servers / total_servers * 100) if total_servers > 0 else 0,
            'overall_status': self._determine_overall_status(results)
        }
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> str:
        """Determine overall health status"""
        if any(r.status == 'unhealthy' for r in results if r.server_name in ['prerequisites', 'environment']):
            return 'unhealthy'
        
        server_results = [r for r in results if r.server_name not in ['prerequisites', 'environment']]
        if not server_results:
            return 'unknown'
        
        unhealthy_count = sum(1 for r in server_results if r.status == 'unhealthy')
        warning_count = sum(1 for r in server_results if r.status == 'warning')
        
        if unhealthy_count > len(server_results) * 0.5:  # More than 50% unhealthy
            return 'unhealthy'
        elif unhealthy_count > 0 or warning_count > len(server_results) * 0.3:  # Any unhealthy or >30% warnings
            return 'warning'
        else:
            return 'healthy'
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print health check summary"""
        overall_color = {
            'healthy': Colors.GREEN,
            'warning': Colors.YELLOW,
            'unhealthy': Colors.RED,
            'unknown': Colors.BLUE
        }.get(summary['overall_status'], Colors.NC)
        
        print(f"Overall Status: {overall_color}{summary['overall_status'].upper()}{Colors.NC}")
        print(f"Total Duration: {summary['total_duration_ms']:.1f}ms")
        print(f"Servers Health: {summary['healthy_servers']}/{summary['total_servers']} ({summary['health_percentage']:.1f}%)")
        
        print("\nStatus Breakdown:")
        for status, count in summary['status_counts'].items():
            color = {
                'healthy': Colors.GREEN,
                'warning': Colors.YELLOW,
                'unhealthy': Colors.RED,
                'unknown': Colors.BLUE
            }.get(status, Colors.NC)
            print(f"  {color}● {status.title()}: {count}{Colors.NC}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CoralCollective MCP Health Check')
    parser.add_argument('--json', action='store_true', help='Output results in JSON format')
    parser.add_argument('--server', type=str, help='Check specific server only')
    parser.add_argument('--save', type=str, help='Save results to file')
    parser.add_argument('--mcp-dir', type=str, help='MCP directory path')
    
    args = parser.parse_args()
    
    # Initialize health checker
    mcp_dir = Path(args.mcp_dir) if args.mcp_dir else None
    checker = MCPHealthChecker(mcp_dir)
    
    if args.server:
        # Check specific server
        result = checker.check_server(args.server)
        if args.json:
            print(json.dumps({
                'server_name': result.server_name,
                'status': result.status,
                'message': result.message,
                'details': result.details,
                'timestamp': result.timestamp.isoformat(),
                'duration_ms': result.duration_ms
            }, indent=2))
        else:
            checker._print_result(result)
    else:
        # Run comprehensive check
        results = checker.run_comprehensive_check()
        
        if args.json:
            print(json.dumps(results, indent=2))
        
        if args.save:
            with open(args.save, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.save}")
    
    # Exit with appropriate code based on overall status
    if not args.server and results['summary']['overall_status'] in ['unhealthy']:
        sys.exit(1)
    elif not args.server and results['summary']['overall_status'] in ['warning']:
        sys.exit(2)


if __name__ == '__main__':
    main()