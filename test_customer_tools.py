#!/usr/bin/env python3
"""
Test Client for Customer Management Tools
========================================

This script demonstrates how to call the new customer management MCP tools
from external files. It tests all the tools with Matt's customer ID (6180005).
"""

import asyncio
import json
import logging
import subprocess
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.server import create_server
from src.database import Neo4jConnection
from config import Neo4jConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomerToolsTestClient:
    """Test client for customer management tools."""
    
    def __init__(self):
        """Initialize test client."""
        self.server = None
        self.connection = None
    
    async def setup(self):
        """Setup server and connection."""
        print("🚀 Setting up MCP Server and Database Connection...")
        
        # Create server
        self.server = create_server()
        
        # Connect to database
        username, password = Neo4jConfig.get_credentials()
        await self.server.connection.connect(username, password)
        
        print("✅ Server setup complete!")
        print(f"📊 Available tools: {len(self.server.tools)}")
        print()
    
    async def test_tool(self, tool_name: str, arguments: dict, description: str):
        """Test a specific tool."""
        print(f"🔧 Testing: {description}")
        print(f"   Tool: {tool_name}")
        print(f"   Args: {arguments}")
        
        try:
            if tool_name not in self.server.tools:
                print(f"   ❌ Tool '{tool_name}' not found")
                return None
            
            tool = self.server.tools[tool_name]
            result = await tool.execute(arguments)
            
            if result and len(result) > 0:
                # Parse the result text content
                result_text = result[0].text
                try:
                    result_data = json.loads(result_text)
                    print(f"   ✅ Success!")
                    return result_data
                except json.JSONDecodeError:
                    print(f"   ✅ Success! (Non-JSON result)")
                    print(f"   📄 Result: {result_text[:200]}...")
                    return result_text
            else:
                print(f"   ⚠️  No result returned")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
        
        print()
    
    async def test_all_customer_tools(self, customer_id: str = "6180005"):
        """Test all customer management tools with a specific customer ID."""
        print("=" * 70)
        print(f"🎯 TESTING ALL CUSTOMER TOOLS FOR CUSTOMER ID: {customer_id}")
        print("=" * 70)
        print()
        
        # Test each tool
        test_cases = [
            {
                "tool_name": "get_customer_profile",
                "arguments": {"customer_id": customer_id},
                "description": "Get complete customer profile with AI insights"
            },
            {
                "tool_name": "get_customer_tags",
                "arguments": {"customer_id": customer_id},
                "description": "Get AI-generated user intent tags"
            },
            {
                "tool_name": "get_customer_likes",
                "arguments": {"customer_id": customer_id},
                "description": "Get customer likes and preferences"
            },
            {
                "tool_name": "get_customer_dislikes",
                "arguments": {"customer_id": customer_id},
                "description": "Get customer dislikes"
            },
            {
                "tool_name": "get_customer_products",
                "arguments": {"customer_id": customer_id, "limit_orders": 3},
                "description": "Get customer's products organized by category"
            },
            {
                "tool_name": "get_customer_pets",
                "arguments": {"customer_id": customer_id},
                "description": "Get customer's pets organized by type"
            },
            {
                "tool_name": "get_customer_web_data",
                "arguments": {"customer_id": customer_id, "limit_sessions": 5},
                "description": "Get customer's web session data"
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            result = await self.test_tool(
                test_case["tool_name"],
                test_case["arguments"],
                test_case["description"]
            )
            results[test_case["tool_name"]] = result
            await asyncio.sleep(0.5)  # Small delay between tests
        
        return results
    
    async def display_summary(self, results: dict, customer_id: str):
        """Display a comprehensive summary of all results."""
        print("=" * 70)
        print(f"📊 COMPREHENSIVE CUSTOMER ANALYSIS SUMMARY FOR: {customer_id}")
        print("=" * 70)
        
        # Customer Profile
        profile = results.get("get_customer_profile")
        if profile:
            basic_info = profile.get("basic_info", {})
            ai_insights = profile.get("ai_insights", {})
            
            print(f"👤 CUSTOMER: {basic_info.get('name', 'Unknown')}")
            print(f"📧 EMAIL: {basic_info.get('email', 'Unknown')}")
            print(f"🔄 AUTOSHIP: {'Yes' if basic_info.get('has_autoship') else 'No'}")
            print(f"💰 AVG ORDER VALUE: ${basic_info.get('avg_order_value', 0)}")
            print()
            
            print("🧠 AI INSIGHTS:")
            print(f"   📝 About: {ai_insights.get('about_user', 'No summary')}")
            print()
        
        # Intent Tags
        tags = results.get("get_customer_tags")
        if tags:
            intent_tags = tags.get("intent_tags", [])
            print(f"🏷️ INTENT TAGS ({len(intent_tags)}):")
            for tag in intent_tags:
                print(f"   • {tag}")
            print()
        
        # Likes
        likes = results.get("get_customer_likes")
        if likes:
            likes_list = likes.get("likes", [])
            print(f"👍 LIKES ({len(likes_list)}):")
            for like in likes_list:
                print(f"   • {like}")
            print()
        
        # Products
        products = results.get("get_customer_products")
        if products:
            hub = products.get("products_hub", {})
            categories = products.get("categories", [])
            print(f"🛍️ PRODUCTS ({hub.get('total_categories', 0)} categories):")
            print(f"   💰 Total Spent: ${hub.get('total_spent', 0)}")
            print(f"   📦 Total Orders: {hub.get('total_orders', 0)}")
            for category in categories[:3]:  # Top 3 categories
                print(f"   • {category.get('display_name', 'Unknown')}: ${category.get('category_spent', 0)}")
            print()
        
        # Pets
        pets = results.get("get_customer_pets")
        if pets:
            hub = pets.get("pets_hub", {})
            categories = pets.get("pet_categories", [])
            print(f"🐾 PETS ({hub.get('total_pets', 0)} pets):")
            for category in categories:
                pets_list = category.get("pets", [])
                print(f"   • {category.get('display_name', 'Unknown')}: {len(pets_list)} pets")
                for pet in pets_list[:2]:  # Show first 2 pets per category
                    print(f"     - {pet.get('pet_name', 'Unknown')} ({pet.get('breed', 'Unknown')})")
            print()
        
        # Web Activity
        web_data = results.get("get_customer_web_data")
        if web_data:
            total_sessions = web_data.get("total_sessions", 0)
            sessions = web_data.get("sessions", [])
            print(f"🌐 WEB ACTIVITY ({total_sessions} total sessions):")
            for session in sessions[:3]:  # Show first 3 sessions
                print(f"   • {session.get('session_date', 'Unknown')}: {session.get('event_count', 0)} events")
            print()
        
        print("=" * 70)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.server and self.server.connection:
            await self.server.connection.disconnect()
        print("🧹 Cleanup complete!")


async def main():
    """Main test function."""
    print("🧪 Customer Management Tools Test Suite")
    print("=" * 70)
    print()
    
    client = CustomerToolsTestClient()
    
    try:
        # Setup
        await client.setup()
        
        # Test all tools with Matt's customer ID
        results = await client.test_all_customer_tools("6180005")
        
        # Display comprehensive summary
        await client.display_summary(results, "6180005")
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logging.exception("Test error")
    
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 