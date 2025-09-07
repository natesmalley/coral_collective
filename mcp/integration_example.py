#!/usr/bin/env python3
"""
Integration example showing how to use the MCP client with CoralCollective agents.
This demonstrates the complete workflow from agent creation to tool execution.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.mcp_client import MCPClient, AgentMCPInterface


async def backend_developer_workflow():
    """Example workflow for a backend developer agent using MCP tools"""
    
    print("🚀 Starting Backend Developer Workflow")
    print("=" * 50)
    
    # Create agent interface
    agent = AgentMCPInterface('backend_developer')
    
    try:
        print("\n1. 📋 Getting available tools...")
        available_tools = await agent.get_available_tools()
        for server_name, tools in available_tools.items():
            print(f"   {server_name}: {len(tools)} tools available")
        
        print("\n2. 📁 Reading project files...")
        # Try to read package.json or README.md
        for file_path in ['package.json', 'README.md', 'pyproject.toml']:
            content = await agent.filesystem_read(file_path)
            if content:
                print(f"   ✅ Read {file_path} ({len(content)} characters)")
                break
        else:
            print("   ⚠️  No common project files found")
        
        print("\n3. 📂 Listing project structure...")
        files = await agent.filesystem_list('.')
        if files:
            print(f"   Found {len(files)} items in root directory")
            # Show first few files
            for file in files[:5]:
                print(f"   - {file}")
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more")
        
        print("\n4. 🌐 Searching for documentation...")
        search_results = await agent.search_web("Python asyncio best practices", max_results=3)
        if search_results:
            print(f"   Found {len(search_results)} search results")
            for i, result in enumerate(search_results[:2], 1):
                title = result.get('title', 'No title')[:60]
                print(f"   {i}. {title}...")
        
        print("\n5. 🐳 Testing Docker functionality...")
        docker_output = await agent.docker_run('python:3.11-alpine', 'python --version')
        if docker_output:
            print(f"   Docker test: {docker_output.strip()}")
        else:
            print("   ⚠️  Docker not available or not configured")
        
        print("\n6. 💻 Testing code execution sandbox...")
        code_result = await agent.e2b_execute("""
import sys
import datetime
print(f"Hello from E2B sandbox!")
print(f"Python version: {sys.version}")
print(f"Current time: {datetime.datetime.now()}")
result = sum(range(100))
print(f"Sum of 0-99: {result}")
""", language='python')
        
        if code_result:
            print("   ✅ Code execution successful:")
            if 'output' in code_result:
                for line in code_result['output'].split('\n')[:3]:
                    if line.strip():
                        print(f"      {line}")
        else:
            print("   ⚠️  E2B sandbox not available or not configured")
        
        print("\n✅ Backend Developer Workflow Complete!")
        
    except Exception as e:
        print(f"\n❌ Workflow error: {e}")
    
    finally:
        await agent.close()


async def frontend_developer_workflow():
    """Example workflow for a frontend developer agent"""
    
    print("\n🎨 Starting Frontend Developer Workflow")
    print("=" * 50)
    
    agent = AgentMCPInterface('frontend_developer')
    
    try:
        print("\n1. 📋 Checking available tools...")
        available_tools = await agent.get_available_tools()
        print(f"   Frontend developer has access to {len(available_tools)} server types")
        
        print("\n2. 🔍 Searching for React documentation...")
        react_results = await agent.search_web("React 18 new features hooks", max_results=2)
        if react_results:
            for i, result in enumerate(react_results, 1):
                title = result.get('title', 'No title')[:50]
                print(f"   {i}. {title}...")
        
        print("\n3. 📁 Looking for frontend files...")
        frontend_files = []
        for pattern in ['src/', 'components/', 'pages/', 'app/']:
            files = await agent.filesystem_list(pattern)
            if files:
                frontend_files.extend([f"{pattern}{f}" for f in files[:3]])
        
        if frontend_files:
            print(f"   Found {len(frontend_files)} frontend files:")
            for file in frontend_files[:5]:
                print(f"   - {file}")
        
        print("\n4. 💻 Testing component code...")
        component_code = """
import React, { useState, useEffect } from 'react';

const MCPTestComponent = () => {
    const [data, setData] = useState(null);
    
    useEffect(() => {
        // Simulate MCP data fetch
        setTimeout(() => {
            setData({ message: 'MCP integration working!', timestamp: Date.now() });
        }, 1000);
    }, []);
    
    return (
        <div>
            <h2>MCP Test Component</h2>
            {data ? (
                <p>{data.message} at {new Date(data.timestamp).toLocaleString()}</p>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    );
};

export default MCPTestComponent;
"""
        
        result = await agent.e2b_execute(component_code, language='javascript')
        if result:
            print("   ✅ Component code syntax validated")
        
        print("\n✅ Frontend Developer Workflow Complete!")
        
    except Exception as e:
        print(f"\n❌ Frontend workflow error: {e}")
    
    finally:
        await agent.close()


async def demonstrate_client_features():
    """Demonstrate core MCP client features"""
    
    print("\n🔧 Demonstrating MCP Client Features")
    print("=" * 50)
    
    # Create direct client
    client = MCPClient('mcp/configs/mcp_config.yaml')
    
    try:
        print("\n1. 🖥️  Server Information:")
        servers = client.get_available_servers()
        for server_name in servers:
            info = client.get_server_info(server_name)
            if info:
                features = info.get('features', [])
                agents = info.get('agents', [])
                print(f"   {server_name}:")
                print(f"     Features: {', '.join(features[:3])}")
                print(f"     Agents: {', '.join(agents[:3])}")
        
        print("\n2. 🔐 Permission Testing:")
        test_agents = ['backend_developer', 'frontend_developer', 'qa_testing']
        test_servers = ['github', 'filesystem', 'postgres', 'docker']
        
        for agent in test_agents:
            permissions = []
            for server in test_servers:
                if client.check_agent_permissions(agent, server):
                    permissions.append(server)
            print(f"   {agent}: {', '.join(permissions)}")
        
        print("\n3. 📊 Client Metrics:")
        metrics = client.get_metrics()
        if metrics:
            for key, value in list(metrics.items())[:5]:
                print(f"   {key}: {value}")
        else:
            print("   No metrics available yet (servers not connected)")
        
    finally:
        await client.shutdown()


async def main():
    """Main integration demonstration"""
    
    print("🪸 CoralCollective MCP Client Integration Demo")
    print("=" * 60)
    print("This demo shows how MCP tools integrate with CoralCollective agents.")
    print("Note: Some operations may fail if MCP servers are not configured.")
    
    # Run demonstrations
    await demonstrate_client_features()
    await backend_developer_workflow()
    await frontend_developer_workflow()
    
    print("\n🎉 Integration Demo Complete!")
    print("\nNext Steps:")
    print("1. Configure MCP servers in mcp/configs/mcp_config.yaml")
    print("2. Set up environment variables in mcp/.env") 
    print("3. Run the full test suite: python3 mcp/test_mcp_client.py")
    print("4. Integrate with your CoralCollective agents")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚡ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()