#!/usr/bin/env node

/**
 * CoralCollective MCP Server Status Reporter
 * Provides comprehensive status information for all MCP servers
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const colors = {
    RED: '\033[0;31m',
    GREEN: '\033[0;32m',
    YELLOW: '\033[1;33m',
    BLUE: '\033[0;34m',
    MAGENTA: '\033[0;35m',
    CYAN: '\033[0;36m',
    BOLD: '\033[1m',
    NC: '\033[0m'
};

const MCP_DIR = path.dirname(__dirname);
const LOGS_DIR = path.join(MCP_DIR, 'logs');

class MCPStatusReporter {
    constructor() {
        this.servers = [];
        this.config = null;
        this.serverStatus = new Map();
    }
    
    async loadConfig() {
        try {
            const configPath = path.join(MCP_DIR, 'configs', 'mcp_config.yaml');
            const yaml = require('js-yaml');
            const configData = await fs.readFile(configPath, 'utf8');
            this.config = yaml.load(configData);
            
            // Get all servers (enabled and disabled)
            this.servers = Object.entries(this.config.mcp_servers || {})
                .map(([name, config]) => ({ name, ...config }));
            
        } catch (error) {
            console.warn(`Could not load configuration: ${error.message}`);
            this.config = { mcp_servers: {} };
            this.servers = [];
        }
    }
    
    async getServerProcessInfo(serverName) {
        const pidFile = path.join(LOGS_DIR, `${serverName}_server.pid`);
        
        try {
            const pidContent = await fs.readFile(pidFile, 'utf8');
            const pid = parseInt(pidContent.trim());
            
            // Check if process exists and get detailed info
            try {
                process.kill(pid, 0); // Signal 0 just checks existence
                
                // Get process details if available (Unix systems)
                let processDetails = null;
                try {
                    const { stdout } = await execAsync(`ps -p ${pid} -o pid,ppid,etime,pmem,pcpu,command --no-headers`);
                    const parts = stdout.trim().split(/\s+/);
                    if (parts.length >= 6) {
                        processDetails = {
                            pid: parseInt(parts[0]),
                            ppid: parseInt(parts[1]),
                            etime: parts[2],
                            pmem: parseFloat(parts[3]),
                            pcpu: parseFloat(parts[4]),
                            command: parts.slice(5).join(' ')
                        };
                    }
                } catch (psError) {
                    // ps command failed, that's ok
                }
                
                return {
                    running: true,
                    pid,
                    pidFile,
                    processDetails
                };
            } catch (killError) {
                // Process doesn't exist, cleanup stale PID file
                await fs.unlink(pidFile).catch(() => {});
                return {
                    running: false,
                    pidFile: null,
                    stalePidFile: pidFile
                };
            }
        } catch (error) {
            return {
                running: false,
                pidFile: null
            };
        }
    }
    
    async getServerLogInfo(serverName) {
        const logFile = path.join(LOGS_DIR, `${serverName}_server.log`);
        
        try {
            const stats = await fs.stat(logFile);
            
            // Get last few lines and check for recent activity/errors
            let recentLines = '';
            let errorCount = 0;
            try {
                const { stdout } = await execAsync(`tail -n 20 "${logFile}"`);
                recentLines = stdout;
                
                // Count errors in recent logs
                const errorRegex = /(error|exception|fail|crash)/gi;
                errorCount = (recentLines.match(errorRegex) || []).length;
                
            } catch (tailError) {
                // tail command failed
            }
            
            return {
                exists: true,
                size: stats.size,
                modified: stats.mtime,
                recentErrorCount: errorCount,
                recentActivity: recentLines.split('\n').slice(-3).join('\n').trim()
            };
        } catch (error) {
            return {
                exists: false
            };
        }
    }
    
    async checkServerConnectivity(server) {
        // Basic connectivity test - try to run server with --help
        try {
            const cmd = server.command || 'npx';
            const args = [...(server.args || []), '--help'];
            
            const { stdout, stderr } = await execAsync(`${cmd} ${args.join(' ')}`, {
                timeout: 5000,
                env: process.env
            });
            
            return {
                responsive: true,
                response: stdout.substring(0, 100) + '...'
            };
        } catch (error) {
            return {
                responsive: false,
                error: error.message
            };
        }
    }
    
    async gatherServerStatus(server) {
        const processInfo = await this.getServerProcessInfo(server.name);
        const logInfo = await this.getServerLogInfo(server.name);
        
        let connectivityInfo = null;
        if (processInfo.running) {
            connectivityInfo = await this.checkServerConnectivity(server);
        }
        
        return {
            name: server.name,
            enabled: server.enabled || false,
            configured: !!server.command && !!server.args,
            process: processInfo,
            logs: logInfo,
            connectivity: connectivityInfo,
            config: {
                command: server.command,
                args: server.args,
                env: Object.keys(server.env || {})
            }
        };
    }
    
    async generateStatusReport() {
        console.log(`${colors.CYAN}${colors.BOLD}📊 CoralCollective MCP Server Status Report${colors.NC}`);
        console.log('=' * 60);
        console.log(`Generated: ${new Date().toLocaleString()}`);
        console.log();
        
        await this.loadConfig();
        
        // Gather status for all servers
        const statusPromises = this.servers.map(server => this.gatherServerStatus(server));
        const statusResults = await Promise.all(statusPromises);
        
        // Store results
        statusResults.forEach(status => {
            this.serverStatus.set(status.name, status);
        });
        
        // Print overview
        this.printOverview();
        
        // Print detailed status for each server
        console.log(`\n${colors.BOLD}Detailed Server Status:${colors.NC}`);
        console.log('-' * 40);
        
        for (const status of statusResults) {
            this.printServerStatus(status);
        }
        
        // Print summary statistics
        this.printSummaryStatistics();
        
        // Print recommendations
        this.printRecommendations();
        
        // Save detailed report
        await this.saveDetailedReport(statusResults);
        
        return statusResults;
    }
    
    printOverview() {
        const total = this.servers.length;
        const enabled = this.servers.filter(s => s.enabled).length;
        const running = Array.from(this.serverStatus.values()).filter(s => s.process.running).length;
        const healthy = Array.from(this.serverStatus.values()).filter(s => 
            s.process.running && s.connectivity?.responsive
        ).length;
        
        console.log(`${colors.BOLD}Overview:${colors.NC}`);
        console.log(`  Total Servers: ${total}`);
        console.log(`  Enabled: ${colors.BLUE}${enabled}${colors.NC}`);
        console.log(`  Running: ${running > 0 ? colors.GREEN : colors.RED}${running}${colors.NC}`);
        console.log(`  Healthy: ${healthy > 0 ? colors.GREEN : colors.RED}${healthy}${colors.NC}`);
        
        if (enabled > 0) {
            const healthPercentage = Math.round((healthy / enabled) * 100);
            const healthColor = healthPercentage >= 80 ? colors.GREEN :
                               healthPercentage >= 50 ? colors.YELLOW : colors.RED;
            console.log(`  Health: ${healthColor}${healthPercentage}%${colors.NC}`);
        }
    }
    
    printServerStatus(status) {
        console.log(`\n${colors.BOLD}${status.name.toUpperCase()}${colors.NC}`);
        
        // Basic info
        const enabledStatus = status.enabled ? 
            `${colors.GREEN}Enabled${colors.NC}` : 
            `${colors.YELLOW}Disabled${colors.NC}`;
        console.log(`  Status: ${enabledStatus}`);
        
        // Process status
        if (status.process.running) {
            const pid = status.process.pid;
            console.log(`  Process: ${colors.GREEN}Running${colors.NC} (PID: ${pid})`);
            
            if (status.process.processDetails) {
                const details = status.process.processDetails;
                console.log(`    Uptime: ${details.etime}`);
                console.log(`    CPU: ${details.pcpu}%`);
                console.log(`    Memory: ${details.pmem}%`);
            }
        } else {
            console.log(`  Process: ${colors.RED}Stopped${colors.NC}`);
            if (status.process.stalePidFile) {
                console.log(`    ${colors.YELLOW}(Cleaned up stale PID file)${colors.NC}`);
            }
        }
        
        // Connectivity
        if (status.connectivity) {
            if (status.connectivity.responsive) {
                console.log(`  Connectivity: ${colors.GREEN}Responsive${colors.NC}`);
            } else {
                console.log(`  Connectivity: ${colors.RED}Not Responsive${colors.NC}`);
                console.log(`    Error: ${status.connectivity.error}`);
            }
        }
        
        // Logs
        if (status.logs.exists) {
            const size = (status.logs.size / 1024).toFixed(1);
            const modified = status.logs.modified.toLocaleString();
            console.log(`  Logs: ${size}KB (modified: ${modified})`);
            
            if (status.logs.recentErrorCount > 0) {
                console.log(`    ${colors.RED}Recent errors: ${status.logs.recentErrorCount}${colors.NC}`);
            }
        } else {
            console.log(`  Logs: ${colors.YELLOW}No log file${colors.NC}`);
        }
        
        // Configuration
        console.log(`  Config: ${status.configured ? colors.GREEN : colors.RED}${status.configured ? 'Valid' : 'Invalid'}${colors.NC}`);
        if (status.config.command) {
            console.log(`    Command: ${status.config.command} ${status.config.args.join(' ')}`);
        }
        if (status.config.env.length > 0) {
            console.log(`    Environment vars: ${status.config.env.join(', ')}`);
        }
    }
    
    printSummaryStatistics() {
        const statusArray = Array.from(this.serverStatus.values());
        
        console.log(`\n${colors.BOLD}Summary Statistics:${colors.NC}`);
        console.log('-' * 25);
        
        // Server type breakdown
        const serverTypes = {};
        statusArray.forEach(status => {
            const type = status.name.split('-')[0] || status.name;
            serverTypes[type] = (serverTypes[type] || 0) + 1;
        });
        
        console.log('Server Types:');
        Object.entries(serverTypes).forEach(([type, count]) => {
            console.log(`  ${type}: ${count}`);
        });
        
        // Resource usage (if available)
        const processesWithDetails = statusArray.filter(s => s.process.processDetails);
        if (processesWithDetails.length > 0) {
            const totalCpu = processesWithDetails.reduce((sum, s) => sum + s.process.processDetails.pcpu, 0);
            const totalMemory = processesWithDetails.reduce((sum, s) => sum + s.process.processDetails.pmem, 0);
            
            console.log(`\nResource Usage (${processesWithDetails.length} processes):`);
            console.log(`  Total CPU: ${totalCpu.toFixed(1)}%`);
            console.log(`  Total Memory: ${totalMemory.toFixed(1)}%`);
        }
        
        // Log file sizes
        const logsWithSize = statusArray.filter(s => s.logs.exists);
        if (logsWithSize.length > 0) {
            const totalLogSize = logsWithSize.reduce((sum, s) => sum + s.logs.size, 0);
            console.log(`\nLog Files:`);
            console.log(`  Total size: ${(totalLogSize / 1024 / 1024).toFixed(1)}MB`);
            console.log(`  Files: ${logsWithSize.length}`);
        }
    }
    
    printRecommendations() {
        const statusArray = Array.from(this.serverStatus.values());
        const recommendations = [];
        
        // Check for disabled but configured servers
        const disabledConfigured = statusArray.filter(s => !s.enabled && s.configured);
        if (disabledConfigured.length > 0) {
            recommendations.push(`Consider enabling ${disabledConfigured.map(s => s.name).join(', ')} if needed`);
        }
        
        // Check for enabled but not running servers
        const enabledNotRunning = statusArray.filter(s => s.enabled && !s.process.running);
        if (enabledNotRunning.length > 0) {
            recommendations.push(`Start these enabled servers: ${enabledNotRunning.map(s => s.name).join(', ')}`);
        }
        
        // Check for servers with recent errors
        const serversWithErrors = statusArray.filter(s => s.logs.recentErrorCount > 0);
        if (serversWithErrors.length > 0) {
            recommendations.push(`Check logs for these servers with recent errors: ${serversWithErrors.map(s => s.name).join(', ')}`);
        }
        
        // Check for unresponsive servers
        const unresponsive = statusArray.filter(s => s.process.running && s.connectivity && !s.connectivity.responsive);
        if (unresponsive.length > 0) {
            recommendations.push(`Restart these unresponsive servers: ${unresponsive.map(s => s.name).join(', ')}`);
        }
        
        if (recommendations.length > 0) {
            console.log(`\n${colors.YELLOW}${colors.BOLD}Recommendations:${colors.NC}`);
            console.log('-' * 20);
            recommendations.forEach((rec, index) => {
                console.log(`${index + 1}. ${rec}`);
            });
        } else {
            console.log(`\n${colors.GREEN}✓ All systems appear to be operating normally${colors.NC}`);
        }
        
        console.log(`\n${colors.BOLD}Quick Actions:${colors.NC}`);
        console.log('  npm run mcp:start   - Start all enabled servers');
        console.log('  npm run mcp:stop    - Stop all running servers');
        console.log('  npm run mcp:health  - Run comprehensive health check');
        console.log('  npm run mcp:monitor - Start real-time monitoring');
    }
    
    async saveDetailedReport(statusResults) {
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: this.servers.length,
                enabled: this.servers.filter(s => s.enabled).length,
                running: statusResults.filter(s => s.process.running).length,
                healthy: statusResults.filter(s => s.process.running && s.connectivity?.responsive).length
            },
            servers: statusResults.map(status => ({
                ...status,
                // Convert dates to ISO strings for JSON serialization
                logs: status.logs.exists ? {
                    ...status.logs,
                    modified: status.logs.modified.toISOString()
                } : status.logs
            })),
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                projectRoot: process.env.PROJECT_ROOT,
                mcpDir: MCP_DIR
            }
        };
        
        const reportFile = path.join(LOGS_DIR, 'status_report.json');
        try {
            await fs.writeFile(reportFile, JSON.stringify(report, null, 2));
            console.log(`\n${colors.BLUE}Detailed report saved to: ${reportFile}${colors.NC}`);
        } catch (error) {
            console.warn(`Could not save detailed report: ${error.message}`);
        }
    }
}

async function main() {
    const args = process.argv.slice(2);
    const options = {
        json: args.includes('--json'),
        short: args.includes('--short'),
        server: args.find(arg => arg.startsWith('--server=')),
        help: args.includes('--help')
    };
    
    if (options.help) {
        console.log(`
CoralCollective MCP Server Status Reporter

Usage: node server_status.js [options]

Options:
  --json       Output status in JSON format
  --short      Show only summary information
  --server=X   Show status for specific server only
  --help       Show this help message

Examples:
  node server_status.js                    # Full status report
  node server_status.js --short           # Summary only
  node server_status.js --json            # JSON output
  node server_status.js --server=github   # GitHub server only
`);
        process.exit(0);
    }
    
    const reporter = new MCPStatusReporter();
    
    try {
        const results = await reporter.generateStatusReport();
        
        if (options.json) {
            const jsonReport = {
                timestamp: new Date().toISOString(),
                servers: results
            };
            console.log(JSON.stringify(jsonReport, null, 2));
        }
        
        // Exit with appropriate code based on overall health
        const running = results.filter(s => s.process.running).length;
        const enabled = results.filter(s => s.enabled).length;
        
        if (running === enabled && enabled > 0) {
            process.exit(0); // All enabled servers running
        } else if (running > 0) {
            process.exit(1); // Some servers running
        } else {
            process.exit(2); // No servers running
        }
        
    } catch (error) {
        console.error(`${colors.RED}Status reporter failed: ${error.message}${colors.NC}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}