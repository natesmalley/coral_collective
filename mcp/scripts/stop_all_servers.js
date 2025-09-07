#!/usr/bin/env node

/**
 * CoralCollective MCP Server Orchestrator - Stop All Servers
 * Gracefully stops all running MCP servers with proper shutdown handling
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const colors = {
    RED: '\033[0;31m',
    GREEN: '\033[0;32m',
    YELLOW: '\033[1;33m',
    BLUE: '\033[0;34m',
    BOLD: '\033[1m',
    NC: '\033[0m'
};

const MCP_DIR = path.dirname(__dirname);
const SERVERS_DIR = path.join(MCP_DIR, 'servers');
const LOGS_DIR = path.join(MCP_DIR, 'logs');

class MCPServerStopper {
    constructor() {
        this.runningServers = [];
        this.stoppedServers = new Set();
        this.failedServers = new Set();
        this.config = null;
    }
    
    async loadConfig() {
        try {
            const configPath = path.join(MCP_DIR, 'configs', 'mcp_config.yaml');
            const yaml = require('js-yaml');
            const configData = await fs.readFile(configPath, 'utf8');
            this.config = yaml.load(configData);
        } catch (error) {
            this.log('warn', `Could not load configuration: ${error.message}`);
            this.config = { mcp_servers: {} };
        }
    }
    
    log(level, message) {
        const timestamp = new Date().toISOString();
        const levelColors = {
            'info': colors.GREEN,
            'warn': colors.YELLOW,
            'error': colors.RED,
            'debug': colors.BLUE
        };
        
        const color = levelColors[level] || colors.NC;
        console.log(`${color}[${level.toUpperCase()}]${colors.NC} ${message}`);
    }
    
    async discoverRunningServers() {
        this.log('info', 'Discovering running MCP servers...');
        
        try {
            const logFiles = await fs.readdir(LOGS_DIR);
            const pidFiles = logFiles.filter(f => f.endsWith('.pid'));
            
            for (const pidFile of pidFiles) {
                const serverName = pidFile.replace('_server.pid', '');
                const pidPath = path.join(LOGS_DIR, pidFile);
                
                try {
                    const pidContent = await fs.readFile(pidPath, 'utf8');
                    const pid = parseInt(pidContent.trim());
                    
                    // Check if process exists
                    try {
                        process.kill(pid, 0); // Signal 0 just checks existence
                        this.runningServers.push({ name: serverName, pid, pidFile: pidPath });
                        this.log('debug', `Found running server: ${serverName} (PID: ${pid})`);
                    } catch (error) {
                        // Process doesn't exist, cleanup stale PID file
                        await fs.unlink(pidPath).catch(() => {});
                        this.log('debug', `Cleaned up stale PID file: ${pidFile}`);
                    }
                } catch (error) {
                    this.log('warn', `Could not read PID file ${pidFile}: ${error.message}`);
                }
            }
            
            this.log('info', `Found ${this.runningServers.length} running servers`);
            
        } catch (error) {
            this.log('error', `Failed to discover running servers: ${error.message}`);
        }
    }
    
    async stopServer(server) {
        this.log('info', `Stopping ${server.name} server (PID: ${server.pid})...`);
        
        // First, try using the server wrapper script
        const scriptPath = path.join(SERVERS_DIR, `${server.name}_server.sh`);
        const useScript = await fs.access(scriptPath).then(() => true).catch(() => false);
        
        if (useScript) {
            return this.stopServerUsingScript(server, scriptPath);
        } else {
            return this.stopServerDirectly(server);
        }
    }
    
    async stopServerUsingScript(server, scriptPath) {
        return new Promise((resolve) => {
            const stopProcess = spawn(scriptPath, ['stop'], {
                stdio: 'pipe',
                env: process.env,
                cwd: MCP_DIR
            });
            
            let output = '';
            let errorOutput = '';
            
            stopProcess.stdout?.on('data', (data) => {
                output += data.toString();
            });
            
            stopProcess.stderr?.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            const timeout = setTimeout(() => {
                stopProcess.kill('SIGTERM');
                this.log('error', `${server.name} stop script timeout`);
                this.fallbackStopServer(server).then(resolve);
            }, 15000); // 15 second timeout
            
            stopProcess.on('exit', async (code) => {
                clearTimeout(timeout);
                
                if (code === 0) {
                    // Verify server actually stopped
                    const stopped = await this.verifyServerStopped(server);
                    if (stopped) {
                        this.log('info', `✓ ${server.name} server stopped successfully`);
                        this.stoppedServers.add(server.name);
                        resolve(true);
                    } else {
                        this.log('warn', `${server.name} script succeeded but server still running, using fallback`);
                        this.fallbackStopServer(server).then(resolve);
                    }
                } else {
                    this.log('warn', `${server.name} stop script failed (exit code: ${code}), using fallback`);
                    this.fallbackStopServer(server).then(resolve);
                }
            });
            
            stopProcess.on('error', (error) => {
                clearTimeout(timeout);
                this.log('warn', `${server.name} stop script error: ${error.message}, using fallback`);
                this.fallbackStopServer(server).then(resolve);
            });
        });
    }
    
    async stopServerDirectly(server) {
        return this.fallbackStopServer(server);
    }
    
    async fallbackStopServer(server) {
        this.log('info', `Using direct process termination for ${server.name}...`);
        
        try {
            // Try graceful shutdown first (SIGTERM)
            process.kill(server.pid, 'SIGTERM');
            this.log('debug', `Sent SIGTERM to ${server.name} (PID: ${server.pid})`);
            
            // Wait for graceful shutdown
            let attempts = 0;
            const maxAttempts = 10; // 10 seconds
            
            while (attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                attempts++;
                
                const stopped = await this.verifyServerStopped(server);
                if (stopped) {
                    this.log('info', `✓ ${server.name} gracefully stopped`);
                    this.stoppedServers.add(server.name);
                    return true;
                }
            }
            
            // If still running, force kill
            this.log('warn', `${server.name} did not respond to SIGTERM, using SIGKILL`);
            process.kill(server.pid, 'SIGKILL');
            
            // Wait a moment and verify
            await new Promise(resolve => setTimeout(resolve, 2000));
            const stopped = await this.verifyServerStopped(server);
            
            if (stopped) {
                this.log('info', `✓ ${server.name} forcefully stopped`);
                this.stoppedServers.add(server.name);
                return true;
            } else {
                this.log('error', `✗ Failed to stop ${server.name}`);
                this.failedServers.add(server.name);
                return false;
            }
            
        } catch (error) {
            if (error.code === 'ESRCH') {
                // Process doesn't exist (already stopped)
                this.log('info', `${server.name} was already stopped`);
                await this.cleanupServerFiles(server);
                this.stoppedServers.add(server.name);
                return true;
            } else {
                this.log('error', `Failed to stop ${server.name}: ${error.message}`);
                this.failedServers.add(server.name);
                return false;
            }
        }
    }
    
    async verifyServerStopped(server) {
        try {
            process.kill(server.pid, 0);
            return false; // Process still exists
        } catch (error) {
            if (error.code === 'ESRCH') {
                await this.cleanupServerFiles(server);
                return true; // Process doesn't exist (stopped)
            }
            return false; // Other error, assume still running
        }
    }
    
    async cleanupServerFiles(server) {
        try {
            await fs.unlink(server.pidFile);
            this.log('debug', `Cleaned up PID file for ${server.name}`);
        } catch (error) {
            // PID file may already be removed, that's ok
        }
    }
    
    async stopAllServers() {
        console.log(`${colors.BLUE}${colors.BOLD}🛑 CoralCollective MCP Server Stopper${colors.NC}`);
        console.log('=' * 50);
        console.log();
        
        try {
            await this.loadConfig();
            await this.discoverRunningServers();
            
            if (this.runningServers.length === 0) {
                this.log('info', 'No running MCP servers found');
                return 0;
            }
            
            this.log('info', `Stopping ${this.runningServers.length} running servers...`);
            
            // Stop servers in reverse dependency order (reverse of start order)
            const stopOrder = [...this.runningServers].reverse();
            
            for (let i = 0; i < stopOrder.length; i++) {
                const server = stopOrder[i];
                
                await this.stopServer(server);
                
                // Add small delay between stops to avoid race conditions
                if (i < stopOrder.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
            
            // Final status report
            this.printStatusReport();
            
            // Save shutdown report
            await this.saveShutdownReport();
            
            const successCount = this.stoppedServers.size;
            const totalCount = this.runningServers.length;
            
            if (successCount === totalCount) {
                this.log('info', '🎉 All servers stopped successfully!');
                return 0;
            } else if (successCount > 0) {
                this.log('warn', `⚠️  ${successCount}/${totalCount} servers stopped successfully`);
                return 1;
            } else {
                this.log('error', '❌ No servers could be stopped');
                return 2;
            }
            
        } catch (error) {
            this.log('error', `Server stopper failed: ${error.message}`);
            return 1;
        }
    }
    
    printStatusReport() {
        console.log();
        console.log(`${colors.BOLD}Shutdown Status Report${colors.NC}`);
        console.log('-' * 30);
        
        if (this.stoppedServers.size > 0) {
            console.log(`${colors.GREEN}Stopped Successfully (${this.stoppedServers.size}):${colors.NC}`);
            for (const server of this.stoppedServers) {
                console.log(`  ✓ ${server}`);
            }
        }
        
        if (this.failedServers.size > 0) {
            console.log(`${colors.RED}Failed to Stop (${this.failedServers.size}):${colors.NC}`);
            for (const server of this.failedServers) {
                console.log(`  ✗ ${server}`);
            }
            
            console.log();
            console.log(`${colors.YELLOW}Manual Cleanup Required:${colors.NC}`);
            console.log('  Check for remaining processes and PID files');
            console.log('  You may need to manually kill processes or restart your system');
        }
        
        console.log();
        console.log(`${colors.BOLD}Management Commands:${colors.NC}`);
        console.log('  npm run mcp:status  - Check current server status');
        console.log('  npm run mcp:start   - Start all servers');
        console.log('  npm run mcp:health  - Run health checks');
    }
    
    async saveShutdownReport() {
        const report = {
            timestamp: new Date().toISOString(),
            totalServers: this.runningServers.length,
            stoppedSuccessfully: Array.from(this.stoppedServers),
            failedToStop: Array.from(this.failedServers),
            serversFound: this.runningServers.map(s => ({ name: s.name, pid: s.pid })),
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                projectRoot: process.env.PROJECT_ROOT
            }
        };
        
        const reportFile = path.join(LOGS_DIR, 'shutdown_report.json');
        try {
            await fs.writeFile(reportFile, JSON.stringify(report, null, 2));
            this.log('debug', `Shutdown report saved to: ${reportFile}`);
        } catch (error) {
            this.log('warn', `Could not save shutdown report: ${error.message}`);
        }
    }
}

async function main() {
    const args = process.argv.slice(2);
    const options = {
        force: args.includes('--force'),
        help: args.includes('--help')
    };
    
    if (options.help) {
        console.log(`
CoralCollective MCP Server Stopper

Usage: node stop_all_servers.js [options]

Options:
  --force    Force stop servers (use SIGKILL immediately)
  --help     Show this help message

Examples:
  node stop_all_servers.js           # Graceful shutdown
  node stop_all_servers.js --force   # Force shutdown
`);
        process.exit(0);
    }
    
    const stopper = new MCPServerStopper();
    
    try {
        const exitCode = await stopper.stopAllServers();
        process.exit(exitCode);
    } catch (error) {
        console.error(`${colors.RED}Fatal error: ${error.message}${colors.NC}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}