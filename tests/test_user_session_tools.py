#!/usr/bin/env python3
"""
Test script for User Session Analysis MCP Tools

This script tests the three new MCP tools:
1. get_user_summary - Get behavioral summary for a customer
2. get_user_tags - Get semantic tags for a user
3. get_session_summary - Get summary for a specific session
"""

import asyncio
import logging
from dotenv import load_dotenv
import os

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Import the tools directly
from src.database import Neo4jConnection
from src.tools.user_session_tools import (
    GetUserSummaryTool, GetUserTagsTool, GetSessionSummaryTool
)

async def test_user_session_tools():
    """Test all user session analysis tools."""
    
    print("🧪 Testing User Session Analysis MCP Tools")
    print("=" * 50)
    
    # Initialize connection
    connection = Neo4jConnection(
        uri=os.getenv('NEO4J_URI'),
        database=os.getenv('NEO4J_DATABASE', 'neo4j')
    )
    
    # Connect to database
    try:
        await connection.connect(
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j: {e}")
        return
    
    # Test data
    customer_id = "289824860"  # Alexander's customer ID
    sample_session_id = "2d5ae2e4-86b5-443d-aa3e-5560ec02adde-1749658730684"
    
    try:
        # Test 1: Get User Summary
        print("\n🧠 TEST 1: Get User Summary")
        print("-" * 30)
        
        user_summary_tool = GetUserSummaryTool(connection)
        result = await user_summary_tool.execute({"customer_id": customer_id})
        
        if result and result[0].text:
            print("✅ User Summary Retrieved:")
            print(result[0].text)
        else:
            print("❌ Failed to get user summary")
        
        # Test 2: Get User Tags
        print("\n🏷️ TEST 2: Get User Tags")
        print("-" * 25)
        
        user_tags_tool = GetUserTagsTool(connection)
        result = await user_tags_tool.execute({"user_id": customer_id})
        
        if result and result[0].text:
            print("✅ User Tags Retrieved:")
            print(result[0].text)
        else:
            print("❌ Failed to get user tags")
        
        # Test 3: Get Session Summary
        print("\n📱 TEST 3: Get Session Summary")
        print("-" * 30)
        
        session_summary_tool = GetSessionSummaryTool(connection)
        result = await session_summary_tool.execute({"session_id": sample_session_id})
        
        if result and result[0].text:
            print("✅ Session Summary Retrieved:")
            print(result[0].text)
        else:
            print("❌ Failed to get session summary")
        
        # Test 4: Error Handling
        print("\n⚠️ TEST 4: Error Handling")
        print("-" * 25)
        
        # Test with non-existent customer
        result = await user_summary_tool.execute({"customer_id": "999999"})
        print(f"Non-existent customer result: {result[0].text[:100]}...")
        
        # Test with non-existent session
        result = await session_summary_tool.execute({"session_id": "non-existent-session"})
        print(f"Non-existent session result: {result[0].text[:100]}...")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        
    finally:
        # Cleanup
        await connection.disconnect()
        print("🔌 Disconnected from Neo4j")


async def show_available_data():
    """Show what data is available for testing."""
    
    print("\n📊 Available Test Data")
    print("=" * 25)
    
    connection = Neo4jConnection(
        uri=os.getenv('NEO4J_URI'),
        database=os.getenv('NEO4J_DATABASE', 'neo4j')
    )
    
    try:
        await connection.connect(
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        
        # Check customers with WebData
        query = """
        MATCH (c:Customer)-[:HAS_WEB_DATA]->(w:WebData)-[:HAS_SESSION]->(s:Session)
        RETURN c.customer_id as customer,
               count(s) as session_count,
               min(s.session_id) as sample_session
        """
        
        result = await connection.execute_read_query(query, {})
        
        if result:
            for record in result:
                customer = record.get("customer", "Unknown")
                session_count = record.get("session_count", 0)
                sample_session = record.get("sample_session", "None")
                
                print(f"👤 Customer: {customer}")
                print(f"   📝 Sessions: {session_count}")
                print(f"   🆔 Sample Session: {sample_session[:50]}...")
                print()
        else:
            print("❌ No customer data found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await connection.disconnect()


if __name__ == "__main__":
    print("🚀 User Session Analysis MCP Tools Test")
    print("=" * 40)
    
    asyncio.run(show_available_data())
    asyncio.run(test_user_session_tools()) 