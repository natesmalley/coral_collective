#!/usr/bin/env node

/**
 * CoralCollective MCP Server Orchestrator - Start All Servers
 * Manages starting multiple MCP servers with proper dependency handling
 */

const fs = require('fs').promises;
const path = require('path');
const { spawn, exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

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

class MCPOrchestrator {
    constructor() {
        this.servers = [];
        this.startOrder = [];
        this.config = null;
        this.startedServers = new Set();
        this.failedServers = new Set();
    }
    
    async loadConfig() {
        try {
            const configPath = path.join(MCP_DIR, 'configs', 'mcp_config.yaml');
            const yaml = require('js-yaml');
            const configData = await fs.readFile(configPath, 'utf8');
            this.config = yaml.load(configData);
            
            // Get enabled servers
            this.servers = Object.entries(this.config.mcp_servers || {})
                .filter(([name, config]) => config.enabled)
                .map(([name, config]) => ({ name, ...config }));
            
            this.log('info', `Found ${this.servers.length} enabled servers to start`);
        } catch (error) {
            this.log('error', `Failed to load configuration: ${error.message}`);
            throw error;
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
    
    async checkPrerequisites() {
        this.log('info', 'Checking prerequisites...');
        
        // Check if server scripts exist
        for (const server of this.servers) {
            const scriptPath = path.join(SERVERS_DIR, `${server.name}_server.sh`);
            try {
                await fs.access(scriptPath);
            } catch (error) {
                throw new Error(`Server script not found: ${scriptPath}`);
            }
        }
        
        // Check environment variables
        const requiredEnvVars = ['PROJECT_ROOT'];
        const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);
        
        if (missingEnvVars.length > 0) {
            throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
        }
        
        // Ensure logs directory exists
        await fs.mkdir(LOGS_DIR, { recursive: true });
        
        this.log('info', 'Prerequisites check passed ✓');
    }
    
    determineDependencyOrder() {
        // Define server dependencies and priority order
        const priorities = {
            'filesystem': 1,  // Filesystem first (needed by others)
            'github': 2,      // GitHub second (source control)
            'postgres': 3,    // Database third
            'docker': 4,      // Docker for containerization
            'e2b': 5,         // E2B for code execution
            'brave-search': 6, // Search capabilities
            'slack': 10,      // Communication (optional)
            'linear': 10,     // Project management (optional)
            'notion': 10      // Documentation (optional)
        };
        
        // Sort servers by priority, then alphabetically
        this.startOrder = this.servers.sort((a, b) => {
            const priorityA = priorities[a.name] || 99;
            const priorityB = priorities[b.name] || 99;
            
            if (priorityA !== priorityB) {
                return priorityA - priorityB;
            }
            return a.name.localeCompare(b.name);
        });
        
        this.log('info', `Server start order: ${this.startOrder.map(s => s.name).join(' → ')}`);
    }
    
    async isServerRunning(serverName) {
        const pidFile = path.join(LOGS_DIR, `${serverName}_server.pid`);
        
        try {
            const pidContent = await fs.readFile(pidFile, 'utf8');
            const pid = parseInt(pidContent.trim());
            
            // Check if process exists
            try {
                process.kill(pid, 0); // Signal 0 just checks if process exists
                return { running: true, pid };
            } catch (error) {
                // Process doesn't exist, cleanup stale PID file
                await fs.unlink(pidFile).catch(() => {});
                return { running: false };
            }
        } catch (error) {
            return { running: false };
        }
    }
    
    async startServer(server) {
        this.log('info', `Starting ${server.name} server...`);
        
        // Check if already running
        const status = await this.isServerRunning(server.name);
        if (status.running) {
            this.log('warn', `${server.name} server is already running (PID: ${status.pid})`);
            this.startedServers.add(server.name);
            return true;
        }
        
        const scriptPath = path.join(SERVERS_DIR, `${server.name}_server.sh`);
        
        return new Promise((resolve) => {
            const startProcess = spawn(scriptPath, ['start'], {
                stdio: 'pipe',
                env: process.env,
                cwd: MCP_DIR
            });
            
            let output = '';
            let errorOutput = '';
            
            startProcess.stdout?.on('data', (data) => {
                output += data.toString();
            });
            
            startProcess.stderr?.on('data', (data) => {
                errorOutput += data.toString();
            });
            
            const timeout = setTimeout(() => {
                startProcess.kill('SIGTERM');
                this.log('error', `${server.name} server start timeout`);
                this.failedServers.add(server.name);
                resolve(false);
            }, 30000); // 30 second timeout
            
            startProcess.on('exit', async (code) => {
                clearTimeout(timeout);
                
                if (code === 0) {
                    // Wait a moment for server to fully initialize
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    // Verify server actually started
                    const verifyStatus = await this.isServerRunning(server.name);
                    if (verifyStatus.running) {
                        this.log('info', `✓ ${server.name} server started successfully (PID: ${verifyStatus.pid})`);
                        this.startedServers.add(server.name);
                        resolve(true);
                    } else {
                        this.log('error', `✗ ${server.name} server failed to start (verification failed)`);
                        this.failedServers.add(server.name);
                        resolve(false);
                    }
                } else {
                    this.log('error', `✗ ${server.name} server failed to start (exit code: ${code})`);
                    if (errorOutput) {
                        this.log('error', `Error output: ${errorOutput.trim()}`);
                    }
                    this.failedServers.add(server.name);
                    resolve(false);
                }
            });
            
            startProcess.on('error', (error) => {
                clearTimeout(timeout);
                this.log('error', `✗ ${server.name} server error: ${error.message}`);
                this.failedServers.add(server.name);
                resolve(false);
            });
        });
    }
    
    async startAllServers() {
        console.log(`${colors.BLUE}${colors.BOLD}🚀 CoralCollective MCP Server Orchestrator${colors.NC}`);
        console.log('=' * 50);
        console.log();
        
        try {
            await this.loadConfig();
            await this.checkPrerequisites();
            this.determineDependencyOrder();
            
            this.log('info', `Starting ${this.servers.length} MCP servers...`);
            
            // Start servers in dependency order with delays
            for (let i = 0; i < this.startOrder.length; i++) {
                const server = this.startOrder[i];
                
                const success = await this.startServer(server);
                
                if (!success) {
                    this.log('warn', `${server.name} failed to start, continuing with remaining servers...`);
                }
                
                // Add delay between server starts to avoid resource conflicts
                if (i < this.startOrder.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }
            }
            
            // Final status report
            this.printStatusReport();
            
            // Save startup report
            await this.saveStartupReport();
            
            const successCount = this.startedServers.size;
            const totalCount = this.servers.length;
            
            if (successCount === totalCount) {
                this.log('info', '🎉 All servers started successfully!');
                return 0;
            } else if (successCount > 0) {
                this.log('warn', `⚠️  ${successCount}/${totalCount} servers started successfully`);
                return 1;
            } else {
                this.log('error', '❌ No servers could be started');
                return 2;
            }
            
        } catch (error) {
            this.log('error', `Orchestrator failed: ${error.message}`);
            return 1;
        }
    }
    
    printStatusReport() {
        console.log();
        console.log(`${colors.BOLD}Startup Status Report${colors.NC}`);
        console.log('-' * 30);
        
        console.log(`${colors.GREEN}Started Successfully (${this.startedServers.size}):${colors.NC}`);
        for (const server of this.startedServers) {
            console.log(`  ✓ ${server}`);
        }
        
        if (this.failedServers.size > 0) {
            console.log(`${colors.RED}Failed to Start (${this.failedServers.size}):${colors.NC}`);
            for (const server of this.failedServers) {
                console.log(`  ✗ ${server}`);
            }
        }
        
        console.log();
        console.log(`${colors.BOLD}Management Commands:${colors.NC}`);
        console.log('  npm run mcp:status  - Check server status');
        console.log('  npm run mcp:health  - Run health checks');
        console.log('  npm run mcp:stop    - Stop all servers');
        console.log('  npm run mcp:monitor - Real-time monitoring');
    }
    
    async saveStartupReport() {
        const report = {
            timestamp: new Date().toISOString(),
            totalServers: this.servers.length,
            startedSuccessfully: Array.from(this.startedServers),
            failedToStart: Array.from(this.failedServers),
            startOrder: this.startOrder.map(s => s.name),
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                projectRoot: process.env.PROJECT_ROOT
            }
        };
        
        const reportFile = path.join(LOGS_DIR, 'startup_report.json');
        try {
            await fs.writeFile(reportFile, JSON.stringify(report, null, 2));
            this.log('debug', `Startup report saved to: ${reportFile}`);
        } catch (error) {
            this.log('warn', `Could not save startup report: ${error.message}`);
        }
    }
}

async function main() {
    const orchestrator = new MCPOrchestrator();
    
    try {
        const exitCode = await orchestrator.startAllServers();
        process.exit(exitCode);
    } catch (error) {
        console.error(`${colors.RED}Fatal error: ${error.message}${colors.NC}`);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}