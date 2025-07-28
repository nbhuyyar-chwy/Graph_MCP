#!/usr/bin/env python3
"""
Demo of User Session Analysis MCP Tools

This demonstrates how to use the three new MCP tools:
1. GetUserSummaryTool - Behavioral summary from WebData node
2. GetUserTagsTool - Semantic tags from session patterns
3. GetSessionSummaryTool - Detailed session analysis
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Import the MCP tools and database connection
from src.database import Neo4jConnection
from src.tools.user_session_tools import (
    GetUserSummaryTool, 
    GetUserTagsTool, 
    GetSessionSummaryTool
)

async def demo_mcp_tools_usage():
    """Demo how to use the actual MCP tools."""
    
    print("🎯 MCP User Session Analysis Tools Usage Demo")
    print("=" * 55)
    print("This shows how to call the actual MCP tool classes")
    print()
    
    # Test data
    customer_id = "289824860"  # Alexander's customer ID
    session_id = "f0b1755b-55b0-423c-b0e7-199ae8a75f27-1752206335415"  # User-provided session
    
    # Initialize Neo4j connection
    connection = Neo4jConnection(
        uri=os.getenv('NEO4J_URI'),
        database=os.getenv('NEO4J_DATABASE', 'neo4j')
    )
    
    try:
        # Connect to database
        await connection.connect(
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        print("✅ Connected to Neo4j")
        
        # Demo 1: GetUserSummaryTool
        print("\n🧠 MCP TOOL 1: GetUserSummaryTool")
        print("=" * 42)
        print("📋 How to use:")
        print("   tool = GetUserSummaryTool(connection)")
        print(f"   result = await tool.execute({{'customer_id': '{customer_id}'}})")
        print()
        
        user_summary_tool = GetUserSummaryTool(connection)
        result = await user_summary_tool.execute({"customer_id": customer_id})
        
        print("✅ MCP Tool Response:")
        if result and result[0].text:
            print(result[0].text)
        else:
            print("❌ No result returned")
        
        # Demo 2: GetUserTagsTool  
        print("\n\n🏷️ MCP TOOL 2: GetUserTagsTool")
        print("=" * 37)
        print("📋 How to use:")
        print("   tool = GetUserTagsTool(connection)")
        print(f"   result = await tool.execute({{'user_id': '{customer_id}'}})")
        print()
        
        user_tags_tool = GetUserTagsTool(connection)
        result = await user_tags_tool.execute({"user_id": customer_id})
        
        print("✅ MCP Tool Response:")
        if result and result[0].text:
            print(result[0].text)
        else:
            print("❌ No result returned")
        
        # Demo 3: GetSessionSummaryTool
        print("\n\n📱 MCP TOOL 3: GetSessionSummaryTool")
        print("=" * 44)
        print("📋 How to use:")
        print("   tool = GetSessionSummaryTool(connection)")
        print(f"   result = await tool.execute({{'session_id': '{session_id[:30]}...'}})")
        print()
        
        session_summary_tool = GetSessionSummaryTool(connection)
        result = await session_summary_tool.execute({"session_id": session_id})
        
        print("✅ MCP Tool Response:")
        if result and result[0].text:
            print(result[0].text)
        else:
            print("❌ No result returned")
        
        # Demo 4: Error Handling
        print("\n\n⚠️ ERROR HANDLING DEMO")
        print("=" * 25)
        print("📋 Testing with invalid inputs:")
        
        # Test with non-existent customer
        print("\n🔍 Testing non-existent customer:")
        result = await user_summary_tool.execute({"customer_id": "999999"})
        print(f"Result: {result[0].text}")
        
        # Test with non-existent session
        print("\n🔍 Testing non-existent session:")
        result = await session_summary_tool.execute({"session_id": "invalid-session-id"})
        print(f"Result: {result[0].text}")
        
        # Test with missing parameters
        print("\n🔍 Testing missing parameters:")
        result = await user_summary_tool.execute({})
        print(f"Result: {result[0].text}")
        
        print("\n\n🎉 MCP Tools Usage Demo Complete!")
        print("=" * 45)
        print("💡 Integration Tips:")
        print("   • Tools are async and return List[TextContent]")
        print("   • Each tool validates input parameters")
        print("   • Error handling is built-in")
        print("   • Tools work with the existing MCP server framework")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        await connection.disconnect()
        print("🔌 Disconnected from Neo4j")


async def demo_tool_schemas():
    """Demo the tool schemas (what the MCP server exposes)."""
    
    print("\n\n📋 MCP TOOL SCHEMAS")
    print("=" * 25)
    print("These are the schemas exposed by the MCP server:")
    
    # Create dummy connection for schema demo
    connection = Neo4jConnection(uri="bolt://localhost:7687", database="neo4j")
    
    tools = [
        GetUserSummaryTool(connection),
        GetUserTagsTool(connection), 
        GetSessionSummaryTool(connection)
    ]
    
    for i, tool in enumerate(tools, 1):
        schema = tool.get_schema()
        print(f"\n🔧 Tool {i}: {schema.name}")
        print(f"   Description: {schema.description}")
        print(f"   Input Schema: {schema.inputSchema}")


if __name__ == "__main__":
    print("🚀 User Session Analysis MCP Tools Demo")
    print("=" * 45)
    print("This demo shows how to use the actual MCP tool classes")
    print("instead of raw Neo4j queries.")
    print()
    
    asyncio.run(demo_mcp_tools_usage())
    asyncio.run(demo_tool_schemas()) 