#!/usr/bin/env python3
"""
Comprehensive Test Suite for Neo4j MCP Tools
=============================================

This unified test suite consolidates all testing functionality:
- MCP Tools Testing (all 13 tools)
- Customer Management Tools Testing
- User Session Analysis Testing
- Query Testing
- Session Analysis Models Testing

Run this single file to test all aspects of the system.
"""

import asyncio
import json
import sys
import os
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.server import Neo4jMCPServer, create_server
from src.database import Neo4jConnection
from config import Neo4jConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class ComprehensiveTestSuite:
    """Comprehensive test suite for all Neo4j MCP functionality."""
    
    def __init__(self):
        """Initialize the test suite."""
        self.server = None
        self.connection = None
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def setup(self):
        """Setup server and connection."""
        print("🚀 Setting up MCP Server and Database Connection...")
        
        try:
            # Create server
            self.server = create_server()
            
            # Connect to database
            username, password = Neo4jConfig.get_credentials()
            await self.server.connection.connect(username, password)
            
            print("✅ Server setup complete!")
            print(f"📊 Available tools: {len(self.server.tools)}")
            print()
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    async def test_tool(self, tool_name: str, arguments: Dict[str, Any], description: str) -> bool:
        """Test a single tool and return success status."""
        self.total_tests += 1
        print(f"🧪 Testing {tool_name}: {description}")
        
        try:
            if tool_name in self.server.tools:
                tool = self.server.tools[tool_name]
                result = await tool.execute(arguments)
                
                if result and len(result) > 0:
                    result_text = result[0].text
                    try:
                        result_data = json.loads(result_text) if result_text.startswith('{') else {"text": result_text}
                    except json.JSONDecodeError:
                        result_data = {"text": result_text}
                    
                    if result_data.get("success", True):
                        print(f"   ✅ PASSED: {description}")
                        self.passed_tests += 1
                        self.test_results[tool_name] = {"status": "PASSED", "result": result_data}
                        return True
                    else:
                        print(f"   ❌ FAILED: {result_data.get('error', 'Unknown error')}")
                        self.failed_tests += 1
                        self.test_results[tool_name] = {"status": "FAILED", "error": result_data.get('error')}
                        return False
                else:
                    print(f"   ❌ FAILED: No result returned")
                    self.failed_tests += 1
                    self.test_results[tool_name] = {"status": "FAILED", "error": "No result returned"}
                    return False
            else:
                print(f"   ❌ FAILED: Tool not found")
                self.failed_tests += 1
                self.test_results[tool_name] = {"status": "FAILED", "error": "Tool not found"}
                return False
                
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            self.failed_tests += 1
            self.test_results[tool_name] = {"status": "FAILED", "error": str(e)}
            return False

    async def test_connection_tools(self):
        """Test connection tools."""
        print("1️⃣ TESTING CONNECTION TOOLS")
        print("-" * 40)
        
        await self.test_tool("connect_neo4j", {
            "username": "neo4j",
            "password": os.getenv('NEO4J_PASSWORD')
        }, "Connect to Neo4j database")
        
        await self.test_tool("get_database_info", {}, "Get database connection info")

    async def test_query_tools(self):
        """Test query tools."""
        print("\n2️⃣ TESTING QUERY TOOLS")
        print("-" * 40)
        
        await self.test_tool("run_cypher_query", {
            "query": "MATCH (p:Pet) RETURN count(p) as total_pets"
        }, "Count all pets")
        
        await self.test_tool("get_schema_info", {}, "Get database schema")
        
        await self.test_tool("validate_query", {
            "query": "MATCH (p:Pet) RETURN p.name LIMIT 5"
        }, "Validate Cypher query")

    async def test_pet_tools(self):
        """Test pet management tools."""
        print("\n3️⃣ TESTING PET TOOLS")
        print("-" * 40)
        
        await self.test_tool("search_pets_by_criteria", {
            "species": "dog",
            "limit": 3
        }, "Search for dogs")
        
        await self.test_tool("get_pets_with_active_medications", {}, "Get pets with medications")

    async def test_customer_tools(self):
        """Test customer management tools."""
        print("\n4️⃣ TESTING CUSTOMER MANAGEMENT TOOLS")
        print("-" * 40)
        
        customer_id = "6180005"  # Matt's customer ID
        
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
                "tool_name": "get_customer_products",
                "arguments": {"customer_id": customer_id, "limit_orders": 3},
                "description": "Get customer's products organized by category"
            },
            {
                "tool_name": "get_customer_pets",
                "arguments": {"customer_id": customer_id},
                "description": "Get customer's pets organized by type"
            }
        ]
        
        for test_case in test_cases:
            await self.test_tool(
                test_case["tool_name"],
                test_case["arguments"],
                test_case["description"]
            )

    async def test_session_tools(self):
        """Test user session analysis tools."""
        print("\n5️⃣ TESTING USER SESSION ANALYSIS TOOLS")
        print("-" * 40)
        
        customer_id = "289824860"  # Alexander's customer ID
        
        # Test user summary
        await self.test_tool("get_user_summary", {
            "customer_id": customer_id
        }, "Get user behavioral summary")
        
        # Test user tags
        await self.test_tool("get_user_tags", {
            "user_id": customer_id
        }, "Get semantic user tags")

    async def test_additional_tools(self):
        """Test additional tools."""
        print("\n6️⃣ TESTING ADDITIONAL TOOLS")
        print("-" * 40)
        
        await self.test_tool("get_vet_appointments", {}, "Get vet appointments")
        await self.test_tool("get_product_interactions", {}, "Get product interactions")

    async def test_advanced_queries(self):
        """Test advanced query functionality."""
        print("\n7️⃣ TESTING ADVANCED QUERIES")
        print("-" * 40)
        
        await self.test_tool("run_cypher_query", {
            "query": "MATCH (p:Pet) RETURN DISTINCT p.species as species, count(p) as count ORDER BY count DESC"
        }, "Group pets by species")
        
        await self.test_tool("run_cypher_query", {
            "query": "MATCH (p:Pet) WHERE p.weight_kg > $weight RETURN p.name, p.weight_kg ORDER BY p.weight_kg DESC LIMIT 5",
            "parameters": {"weight": 20.0}
        }, "Find heavy pets (parameterized query)")

    async def test_direct_database_queries(self):
        """Test direct database queries for validation."""
        print("\n8️⃣ TESTING DIRECT DATABASE QUERIES")
        print("-" * 40)
        
        try:
            driver = GraphDatabase.driver(
                os.getenv('NEO4J_URI'),
                auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
            )
            
            with driver.session() as session:
                # Test customer data
                result = session.run("MATCH (c:Customer {customer_id: '6180005'}) RETURN c.customer_full_name as name")
                record = result.single()
                if record:
                    print(f"   ✅ Found customer: {record['name']}")
                else:
                    print("   ❌ Customer not found")
                
                # Test pet count
                result = session.run("MATCH (p:Pet) RETURN count(p) as total")
                record = result.single()
                if record:
                    print(f"   ✅ Total pets in database: {record['total']}")
                
                # Test session data
                result = session.run("MATCH (s:Session) RETURN count(s) as total")
                record = result.single()
                if record:
                    print(f"   ✅ Total sessions in database: {record['total']}")
            
            driver.close()
            print("   ✅ Direct database queries completed")
            
        except Exception as e:
            print(f"   ❌ Direct database query failed: {e}")

    async def test_disconnect(self):
        """Test disconnection."""
        print("\n9️⃣ TESTING DISCONNECTION")
        print("-" * 40)
        
        await self.test_tool("disconnect_neo4j", {}, "Disconnect from database")

    async def run_all_tests(self):
        """Run the comprehensive test suite."""
        print("🔧 Neo4j MCP Tools - Comprehensive Test Suite")
        print("=" * 60)
        
        # Check configuration
        if not Neo4jConfig.is_configured():
            print("❌ Neo4j configuration incomplete!")
            print("Please set NEO4J_PASSWORD environment variable")
            return False
        
        print(f"🔗 Testing connection to: {Neo4jConfig.URI}")
        print(f"📊 Database: {Neo4jConfig.DATABASE}")
        print()
        
        # Setup
        if not await self.setup():
            return False
        
        # Run all test categories
        await self.test_connection_tools()
        await self.test_query_tools()
        await self.test_pet_tools()
        await self.test_customer_tools()
        await self.test_session_tools()
        await self.test_additional_tools()
        await self.test_advanced_queries()
        await self.test_direct_database_queries()
        await self.test_disconnect()
        
        # Print summary
        self.print_summary()
        
        return self.failed_tests == 0

    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        print(f"🧪 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! THE SYSTEM IS READY! 🎉")
            print("✅ Your Neo4j MCP server is fully operational!")
        else:
            print(f"\n⚠️  {self.failed_tests} tests need attention:")
            for tool_name, result in self.test_results.items():
                if result["status"] == "FAILED":
                    print(f"   ❌ {tool_name}: {result['error']}")
        
        print("\n🔧 Test Categories Covered:")
        print("   ✅ Connection Tools")
        print("   ✅ Query Tools") 
        print("   ✅ Pet Management Tools")
        print("   ✅ Customer Management Tools")
        print("   ✅ Session Analysis Tools")
        print("   ✅ Additional Tools")
        print("   ✅ Advanced Queries")
        print("   ✅ Direct Database Validation")

    async def cleanup(self):
        """Cleanup resources."""
        if self.server and self.server.connection:
            await self.server.connection.disconnect()
        print("🧹 Cleanup complete!")


async def main():
    """Main test function."""
    suite = ComprehensiveTestSuite()
    
    print("🚀 Starting Comprehensive Neo4j MCP Test Suite...")
    print("This will test ALL functionality in the system.\n")
    
    try:
        success = await suite.run_all_tests()
        
        print(f"\n🏁 Testing complete! Exit code: {0 if success else 1}")
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        return 1
    finally:
        await suite.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        sys.exit(1) 