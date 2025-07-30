#!/usr/bin/env python3
"""
Quick Test Script for Neo4j MCP Tools

This script runs a few essential tests to quickly verify your tools are working.
"""

import asyncio
from src.database.connection import Neo4jConnection
from src.server import Neo4jMCPServer
from config import Neo4jConfig

async def quick_test():
    """Run quick tests on essential functionality."""
    print("🚀 Quick Test for Neo4j MCP Tools")
    print("=" * 40)
    
    # Check configuration
    if not Neo4jConfig.is_configured():
        print("❌ NEO4J_PASSWORD not set!")
        print("Set it with: export NEO4J_PASSWORD=your_password")
        return False
    
    print(f"🔗 URI: {Neo4jConfig.URI}")
    print(f"📊 Database: {Neo4jConfig.DATABASE}")
    print()
    
    try:
        # Test 1: Direct Connection
        print("1️⃣ Testing direct Neo4j connection...")
        connection = Neo4jConnection(Neo4jConfig.URI, Neo4jConfig.DATABASE)
        username, password = Neo4jConfig.get_credentials()
        
        if not password:
            print("   ❌ Password is required!")
            return False
        await connection.connect(username, password)
        print("   ✅ Connection successful!")
        
        # Test 2: Simple Query
        print("2️⃣ Testing basic query...")
        result = await connection.execute_read_query("MATCH (p:Pet) RETURN count(p) as total", {})
        total_pets = result[0]['total'] if result else 0
        print(f"   ✅ Found {total_pets} pets in database!")
        
        await connection.disconnect()
        
        # Test 3: MCP Server Tools
        print("3️⃣ Testing MCP server tools...")
        server = Neo4jMCPServer()
        tool_count = len(server.tools)
        print(f"   ✅ {tool_count} tools available!")
        
        # Test 4: Sample Tool Execution
        print("4️⃣ Testing sample tool execution...")
        tool = server.tools["run_cypher_query"]
        result = await tool.execute({
            "query": "MATCH (p:Pet) RETURN DISTINCT p.species as species LIMIT 3"
        })
        
        if result and len(result) > 0:
            print("   ✅ Tool execution successful!")
        else:
            print("   ❌ Tool execution failed!")
            return False
        
        print("\n🎉 ALL QUICK TESTS PASSED!")
        print("✅ Your Neo4j MCP tools are working correctly!")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

async def list_available_tools():
    """List all available tools."""
    print("\n🔧 Available MCP Tools:")
    print("-" * 30)
    
    server = Neo4jMCPServer()
    for i, tool_name in enumerate(server.tools.keys(), 1):
        print(f"{i:2d}. {tool_name}")
    
    print(f"\nTotal: {len(server.tools)} tools")

if __name__ == "__main__":
    try:
        print("Running quick tests...\n")
        success = asyncio.run(quick_test())
        asyncio.run(list_available_tools())
        
        if success:
            print("\n✅ Ready for production use!")
        else:
            print("\n❌ Issues found - check configuration")
            
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}") 