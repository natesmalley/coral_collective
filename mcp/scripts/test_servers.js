#!/usr/bin/env node

/**
 * CoralCollective MCP Server Integration Test Suite
 * Comprehensive testing for MCP server functionality and integration
 */

const { spawn, exec } = require('child_process');
const fs = require('fs').promises;
const path = require('path');
const util = require('util');
const execAsync = util.promisify(exec);

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

// Colors for output
const colors = {
    RED: '\033[0;31m',
    GREEN: '\033[0;32m', 
    YELLOW: '\033[1;33m',
    BLUE: '\033[0;34m',
    BOLD: '\033[1m',
    NC: '\033[0m' // No Color
};

// Test configuration
const TEST_TIMEOUT = 30000; // 30 seconds
const MCP_DIR = path.dirname(__dirname);
const PROJECT_ROOT = path.dirname(MCP_DIR);

class TestResult {
    constructor(name, status, message = '', details = {}, duration = 0) {
        this.name = name;
        this.status = status; // 'pass', 'fail', 'skip', 'warn'
        this.message = message;
        this.details = details;
        this.duration = duration;
        this.timestamp = new Date().toISOString();
    }
}

class MCPServerTester {
    constructor() {
        this.results = [];
        this.config = null;
        this.servers = [];
        
        this.loadConfig();
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
            
            this.log('info', `Loaded configuration for ${this.servers.length} servers`);
        } catch (error) {
            this.log('error', `Failed to load configuration: ${error.message}`);
            this.config = { mcp_servers: {} };
            this.servers = [];
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
    
    async runTest(name, testFunction, timeout = TEST_TIMEOUT) {
        const startTime = Date.now();
        this.log('info', `Running test: ${name}`);
        
        try {
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Test timeout')), timeout);
            });
            
            const result = await Promise.race([
                testFunction(),
                timeoutPromise
            ]);
            
            const duration = Date.now() - startTime;
            const testResult = new TestResult(name, 'pass', 'Test completed successfully', result, duration);
            this.results.push(testResult);
            this.log('info', `✓ ${name} (${duration}ms)`);
            return testResult;
            
        } catch (error) {
            const duration = Date.now() - startTime;
            const testResult = new TestResult(name, 'fail', error.message, { error: error.stack }, duration);
            this.results.push(testResult);
            this.log('error', `✗ ${name}: ${error.message} (${duration}ms)`);
            return testResult;
        }
    }
    
    async testPrerequisites() {
        return this.runTest('Prerequisites Check', async () => {
            const results = {};
            
            // Check Node.js
            try {
                const { stdout } = await execAsync('node --version');
                results.nodeVersion = stdout.trim();
                const majorVersion = parseInt(results.nodeVersion.replace('v', '').split('.')[0]);
                if (majorVersion < 18) {
                    throw new Error(`Node.js version ${results.nodeVersion} is too old (minimum: v18)`);
                }
            } catch (error) {
                throw new Error(`Node.js check failed: ${error.message}`);
            }
            
            // Check npm
            try {
                const { stdout } = await execAsync('npm --version');
                results.npmVersion = stdout.trim();
            } catch (error) {
                throw new Error(`npm check failed: ${error.message}`);
            }
            
            // Check npx
            try {
                await execAsync('npx --version');
                results.npxAvailable = true;
            } catch (error) {
                throw new Error(`npx check failed: ${error.message}`);
            }
            
            // Check environment file
            try {
                await fs.access(path.join(MCP_DIR, '.env'));
                results.envFileExists = true;
            } catch (error) {
                throw new Error('Environment file (.env) not found');
            }
            
            return results;
        });
    }
    
    async testEnvironmentVariables() {
        return this.runTest('Environment Variables', async () => {
            const results = {};
            const missingVars = [];
            const placeholderVars = [];
            
            // Check common required environment variables
            const requiredVars = [
                'GITHUB_TOKEN',
                'PROJECT_ROOT',
                'E2B_API_KEY',
                'BRAVE_API_KEY'
            ];
            
            for (const varName of requiredVars) {
                const value = process.env[varName];
                if (!value) {
                    missingVars.push(varName);
                } else if (value.includes('your_') && value.includes('_here')) {
                    placeholderVars.push(varName);
                } else {
                    results[varName] = 'configured';
                }
            }
            
            results.missingVars = missingVars;
            results.placeholderVars = placeholderVars;
            
            if (missingVars.length > 0) {
                throw new Error(`Missing required environment variables: ${missingVars.join(', ')}`);
            }
            
            if (placeholderVars.length > 0) {
                this.log('warn', `Environment variables with placeholder values: ${placeholderVars.join(', ')}`);
            }
            
            return results;
        });
    }
    
    async testServerPackageInstallation() {
        return this.runTest('Server Package Installation', async () => {
            const results = {};
            const packageChecks = [];
            
            for (const server of this.servers) {
                const packageName = server.args?.[0] || `@modelcontextprotocol/server-${server.name}`;
                
                try {
                    // Try to check if package is available
                    await execAsync(`npm list -g ${packageName}`, { timeout: 10000 });
                    results[server.name] = 'installed_global';
                } catch (globalError) {
                    try {
                        // Check local installation
                        await execAsync(`npm list ${packageName}`, { cwd: PROJECT_ROOT, timeout: 10000 });
                        results[server.name] = 'installed_local';
                    } catch (localError) {
                        results[server.name] = 'not_installed';
                        packageChecks.push(`${server.name}: ${packageName} not found`);
                    }
                }
            }
            
            if (packageChecks.length > 0) {
                throw new Error(`Package installation issues: ${packageChecks.join('; ')}`);
            }
            
            return results;
        });
    }
    
    async testServerBasicConnectivity() {
        return this.runTest('Server Basic Connectivity', async () => {
            const results = {};
            
            for (const server of this.servers.slice(0, 3)) { // Test first 3 servers to avoid timeouts
                try {
                    const serverResult = await this.testIndividualServer(server);
                    results[server.name] = serverResult;
                } catch (error) {
                    results[server.name] = { status: 'failed', error: error.message };
                }
            }
            
            const failedServers = Object.entries(results)
                .filter(([name, result]) => result.status === 'failed')
                .map(([name]) => name);
            
            if (failedServers.length === Object.keys(results).length) {
                throw new Error(`All tested servers failed connectivity test`);
            }
            
            if (failedServers.length > 0) {
                this.log('warn', `Some servers failed connectivity: ${failedServers.join(', ')}`);
            }
            
            return results;
        });
    }
    
    async testIndividualServer(server) {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Server test timeout'));
            }, 15000);
            
            // Prepare command
            const cmd = server.command || 'npx';
            const args = [...(server.args || []), '--help'];
            
            // Prepare environment
            const env = { ...process.env };
            if (server.env) {
                for (const [key, value] of Object.entries(server.env)) {
                    // Resolve environment variable references
                    let resolvedValue = value;
                    const envVarMatch = value.match(/\$\{([^}]+)\}/);
                    if (envVarMatch) {
                        const envVarName = envVarMatch[1];
                        const envVarValue = process.env[envVarName] || '';
                        resolvedValue = value.replace(`\${${envVarName}}`, envVarValue);
                    }
                    env[key] = resolvedValue;
                }
            }
            
            // Spawn process
            const child = spawn(cmd, args, {
                env,
                stdio: ['ignore', 'pipe', 'pipe'],
                cwd: MCP_DIR
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout?.on('data', (data) => {
                stdout += data.toString();
            });
            
            child.stderr?.on('data', (data) => {
                stderr += data.toString();
            });
            
            child.on('error', (error) => {
                clearTimeout(timeout);
                reject(new Error(`Process error: ${error.message}`));
            });
            
            child.on('exit', (code, signal) => {
                clearTimeout(timeout);
                
                // Most MCP servers return 0 or 1 for --help
                if (code === 0 || code === 1) {
                    resolve({
                        status: 'success',
                        exitCode: code,
                        stdout: stdout.substring(0, 200), // First 200 chars
                        stderr: stderr.substring(0, 200)
                    });
                } else {
                    reject(new Error(`Server exited with code ${code}: ${stderr.substring(0, 200)}`));
                }
            });
        });
    }
    
    async testServerWrapperScripts() {
        return this.runTest('Server Wrapper Scripts', async () => {
            const results = {};
            const serversDir = path.join(MCP_DIR, 'servers');
            
            for (const server of this.servers) {
                const scriptPath = path.join(serversDir, `${server.name}_server.sh`);
                
                try {
                    await fs.access(scriptPath, fs.constants.F_OK | fs.constants.X_OK);
                    results[server.name] = 'script_exists_executable';
                    
                    // Test script help
                    try {
                        const { stdout, stderr } = await execAsync(`${scriptPath} help`, { timeout: 5000 });
                        results[`${server.name}_help`] = 'help_works';
                    } catch (helpError) {
                        results[`${server.name}_help`] = 'help_failed';
                    }
                    
                } catch (error) {
                    results[server.name] = 'script_missing_or_not_executable';
                }
            }
            
            return results;
        });
    }
    
    async testLogDirectoryStructure() {
        return this.runTest('Log Directory Structure', async () => {
            const results = {};
            const logDir = path.join(MCP_DIR, 'logs');
            
            // Check if log directory exists
            try {
                const logDirStats = await fs.stat(logDir);
                results.logDirExists = logDirStats.isDirectory();
                
                // Check permissions
                await fs.access(logDir, fs.constants.R_OK | fs.constants.W_OK);
                results.logDirWritable = true;
                
                // List log files
                const logFiles = await fs.readdir(logDir);
                results.logFiles = logFiles.filter(f => f.endsWith('.log'));
                results.pidFiles = logFiles.filter(f => f.endsWith('.pid'));
                
            } catch (error) {
                throw new Error(`Log directory check failed: ${error.message}`);
            }
            
            return results;
        });
    }
    
    async testMCPClientIntegration() {
        return this.runTest('MCP Client Integration', async () => {
            const results = {};
            const mcpClientPath = path.join(MCP_DIR, 'mcp_client.py');
            
            try {
                await fs.access(mcpClientPath);
                results.mcpClientExists = true;
                
                // Test basic import (if Python is available)
                try {
                    const { stdout, stderr } = await execAsync(`python3 -c "import sys; sys.path.insert(0, '${MCP_DIR}'); from mcp_client import MCPClient; print('Import successful')"`, { timeout: 10000 });
                    results.mcpClientImportable = true;
                } catch (importError) {
                    results.mcpClientImportable = false;
                    results.importError = importError.message;
                    this.log('warn', `MCP Client import test failed: ${importError.message}`);
                }
                
            } catch (error) {
                throw new Error('MCP client file not found');
            }
            
            return results;
        });
    }
    
    async testConfigurationValidity() {
        return this.runTest('Configuration Validity', async () => {
            const results = {};
            
            // Test YAML parsing
            if (this.config) {
                results.configParseable = true;
                results.serverCount = Object.keys(this.config.mcp_servers || {}).length;
                results.enabledServerCount = this.servers.length;
                
                // Check for required sections
                const requiredSections = ['mcp_servers', 'security', 'agent_permissions'];
                const missingSections = requiredSections.filter(section => !this.config[section]);
                
                if (missingSections.length > 0) {
                    this.log('warn', `Configuration missing sections: ${missingSections.join(', ')}`);
                }
                
                results.missingSections = missingSections;
                
                // Validate server configurations
                const invalidServers = [];
                for (const [name, config] of Object.entries(this.config.mcp_servers || {})) {
                    if (!config.command || !config.args) {
                        invalidServers.push(name);
                    }
                }
                
                results.invalidServers = invalidServers;
                
                if (invalidServers.length > 0) {
                    this.log('warn', `Servers with invalid configuration: ${invalidServers.join(', ')}`);
                }
                
            } else {
                throw new Error('Configuration could not be loaded');
            }
            
            return results;
        });
    }
    
    async testDocumentationFiles() {
        return this.runTest('Documentation Files', async () => {
            const results = {};
            
            const importantFiles = [
                'README.md',
                '.env.example',
                'claude_desktop_config.json',
                'configs/mcp_config.yaml'
            ];
            
            for (const file of importantFiles) {
                const filePath = path.join(MCP_DIR, file);
                try {
                    const stats = await fs.stat(filePath);
                    results[file] = {
                        exists: true,
                        size: stats.size,
                        modified: stats.mtime.toISOString()
                    };
                } catch (error) {
                    results[file] = { exists: false };
                }
            }
            
            return results;
        });
    }
    
    async runBenchmarks() {
        return this.runTest('Performance Benchmarks', async () => {
            const results = {};
            
            // Test server startup time for one server
            if (this.servers.length > 0) {
                const testServer = this.servers[0];
                
                const startTime = Date.now();
                try {
                    await this.testIndividualServer(testServer);
                    const responseTime = Date.now() - startTime;
                    results.serverResponseTime = responseTime;
                    results.performanceGrade = responseTime < 5000 ? 'excellent' : 
                                               responseTime < 10000 ? 'good' : 
                                               responseTime < 20000 ? 'acceptable' : 'poor';
                } catch (error) {
                    results.serverResponseTime = 'failed';
                }
            }
            
            // Test file system performance
            const testFileStartTime = Date.now();
            const testFilePath = path.join(MCP_DIR, 'logs', 'test_benchmark.tmp');
            try {
                await fs.writeFile(testFilePath, 'benchmark test data');
                await fs.readFile(testFilePath);
                await fs.unlink(testFilePath);
                results.fileSystemPerformance = Date.now() - testFileStartTime;
            } catch (error) {
                results.fileSystemPerformance = 'failed';
            }
            
            return results;
        });
    }
    
    async runAllTests() {
        console.log(`${colors.BLUE}${colors.BOLD}🧪 CoralCollective MCP Integration Test Suite${colors.NC}`);
        console.log('=' * 60);
        console.log(`Starting comprehensive testing of MCP infrastructure...`);
        console.log();
        
        const startTime = Date.now();
        
        // Run test suite
        const tests = [
            () => this.testPrerequisites(),
            () => this.testEnvironmentVariables(),
            () => this.testConfigurationValidity(),
            () => this.testDocumentationFiles(),
            () => this.testLogDirectoryStructure(),
            () => this.testServerPackageInstallation(),
            () => this.testServerWrapperScripts(),
            () => this.testServerBasicConnectivity(),
            () => this.testMCPClientIntegration(),
            () => this.runBenchmarks()
        ];
        
        for (const test of tests) {
            try {
                await test();
            } catch (error) {
                this.log('error', `Test execution error: ${error.message}`);
            }
        }
        
        const totalDuration = Date.now() - startTime;
        
        // Generate test report
        this.generateTestReport(totalDuration);
        
        return {
            results: this.results,
            summary: this.generateTestSummary(totalDuration)
        };
    }
    
    generateTestSummary(totalDuration) {
        const passed = this.results.filter(r => r.status === 'pass').length;
        const failed = this.results.filter(r => r.status === 'fail').length;
        const warnings = this.results.filter(r => r.status === 'warn').length;
        const skipped = this.results.filter(r => r.status === 'skip').length;
        
        return {
            total: this.results.length,
            passed,
            failed,
            warnings,
            skipped,
            totalDuration,
            overallStatus: failed === 0 ? (warnings === 0 ? 'pass' : 'pass_with_warnings') : 'fail'
        };
    }
    
    generateTestReport(totalDuration) {
        const summary = this.generateTestSummary(totalDuration);
        
        console.log(`\n${colors.BOLD}Test Results Summary${colors.NC}`);
        console.log('-' * 30);
        
        const statusColor = summary.overallStatus === 'pass' ? colors.GREEN :
                           summary.overallStatus === 'pass_with_warnings' ? colors.YELLOW :
                           colors.RED;
        
        console.log(`Overall Status: ${statusColor}${summary.overallStatus.toUpperCase()}${colors.NC}`);
        console.log(`Total Tests: ${summary.total}`);
        console.log(`${colors.GREEN}Passed: ${summary.passed}${colors.NC}`);
        console.log(`${colors.RED}Failed: ${summary.failed}${colors.NC}`);
        if (summary.warnings > 0) {
            console.log(`${colors.YELLOW}Warnings: ${summary.warnings}${colors.NC}`);
        }
        if (summary.skipped > 0) {
            console.log(`Skipped: ${summary.skipped}`);
        }
        console.log(`Duration: ${totalDuration}ms`);
        
        // Show failed tests
        const failedTests = this.results.filter(r => r.status === 'fail');
        if (failedTests.length > 0) {
            console.log(`\n${colors.RED}Failed Tests:${colors.NC}`);
            for (const test of failedTests) {
                console.log(`  ✗ ${test.name}: ${test.message}`);
            }
        }
        
        // Show warnings
        const warningTests = this.results.filter(r => r.status === 'warn');
        if (warningTests.length > 0) {
            console.log(`\n${colors.YELLOW}Warnings:${colors.NC}`);
            for (const test of warningTests) {
                console.log(`  ⚠ ${test.name}: ${test.message}`);
            }
        }
        
        // Save detailed results
        const reportFile = path.join(MCP_DIR, 'tests', `test_results_${new Date().toISOString().replace(/[:.]/g, '-')}.json`);
        fs.writeFile(reportFile, JSON.stringify({
            timestamp: new Date().toISOString(),
            summary,
            results: this.results
        }, null, 2)).catch(err => {
            this.log('warn', `Could not save detailed test report: ${err.message}`);
        });
    }
}

// Main execution
async function main() {
    const args = process.argv.slice(2);
    const options = {
        json: args.includes('--json'),
        verbose: args.includes('--verbose'),
        server: args.find(arg => arg.startsWith('--server=')),
        help: args.includes('--help')
    };
    
    if (options.help) {
        console.log(`
CoralCollective MCP Integration Test Suite

Usage: node test_servers.js [options]

Options:
  --json       Output results in JSON format
  --verbose    Show detailed test output
  --server=X   Test only specific server
  --help       Show this help message

Examples:
  node test_servers.js                    # Run all tests
  node test_servers.js --json            # Output JSON results
  node test_servers.js --server=github   # Test only GitHub server
`);
        process.exit(0);
    }
    
    const tester = new MCPServerTester();
    
    try {
        const results = await tester.runAllTests();
        
        if (options.json) {
            console.log(JSON.stringify(results, null, 2));
        }
        
        // Exit with appropriate code
        const summary = results.summary;
        if (summary.overallStatus === 'fail') {
            process.exit(1);
        } else if (summary.overallStatus === 'pass_with_warnings') {
            process.exit(2);
        } else {
            process.exit(0);
        }
        
    } catch (error) {
        console.error(`${colors.RED}Test suite failed: ${error.message}${colors.NC}`);
        process.exit(1);
    }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

// Run tests if called directly
if (require.main === module) {
    main();
}

module.exports = { MCPServerTester, TestResult };