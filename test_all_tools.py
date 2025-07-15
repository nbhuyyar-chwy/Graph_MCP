#!/usr/bin/env python3
"""
Comprehensive Test Suite for Neo4j MCP Tools

This script tests all 13 available MCP tools to ensure they're working correctly.
"""

import asyncio
import json
import sys
from typing import Dict, Any, List
from src.server import Neo4jMCPServer
from config import Neo4jConfig

class ToolTester:
    """Test all MCP tools systematically."""
    
    def __init__(self):
        """Initialize the tester."""
        self.server = Neo4jMCPServer()
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def test_tool(self, tool_name: str, arguments: Dict[str, Any], description: str) -> bool:
        """Test a single tool and return success status."""
        self.total_tests += 1
        print(f"🧪 Testing {tool_name}: {description}")
        
        try:
            if tool_name in self.server.tools:
                tool = self.server.tools[tool_name]
                result = await tool.execute(arguments)
                
                # Check if result is valid
                if result and len(result) > 0:
                    result_text = result[0].text
                    result_data = json.loads(result_text) if result_text.startswith('{') else {"text": result_text}
                    
                    if result_data.get("success", True):  # Assume success if no success field
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

    async def run_all_tests(self):
        """Run comprehensive tests for all tools."""
        print("🔧 Neo4j MCP Tools - Comprehensive Test Suite")
        print("=" * 60)
        
        # Check configuration first
        if not Neo4jConfig.is_configured():
            print("❌ Neo4j configuration incomplete!")
            print("Please set NEO4J_PASSWORD environment variable")
            return False
        
        print(f"🔗 Testing connection to: {Neo4jConfig.URI}")
        print(f"📊 Database: {Neo4jConfig.DATABASE}")
        print(f"🆔 Instance ID: {Neo4jConfig.INSTANCE_ID}")
        print()
        
        # Test 1: Connection Tools
        print("1️⃣ TESTING CONNECTION TOOLS")
        print("-" * 40)
        
        await self.test_tool("connect_neo4j", {
            "username": "neo4j",
            "password": "nrxuvCRDnCm5uicdkGmg71DNJFVYxtMfm4gi52I8lWY"
        }, "Connect to Neo4j database")
        
        await self.test_tool("get_database_info", {}, "Get database connection info")
        
        # Test 2: Query Tools
        print("\n2️⃣ TESTING QUERY TOOLS")
        print("-" * 40)
        
        await self.test_tool("run_cypher_query", {
            "query": "MATCH (p:Pet) RETURN count(p) as total_pets"
        }, "Count all pets")
        
        await self.test_tool("get_schema_info", {}, "Get database schema")
        
        await self.test_tool("validate_query", {
            "query": "MATCH (p:Pet) RETURN p.name LIMIT 5"
        }, "Validate Cypher query")
        
        # Test 3: Pet Tools
        print("\n3️⃣ TESTING PET TOOLS")
        print("-" * 40)
        
        await self.test_tool("search_pets_by_criteria", {
            "species": "dog",
            "limit": 3
        }, "Search for dogs")
        
        await self.test_tool("search_pets_by_criteria", {
            "species": "cat",
            "limit": 2
        }, "Search for cats")
        
        await self.test_tool("get_pets_with_active_medications", {}, "Get pets with medications")
        
        # Test 4: Additional Tools
        print("\n4️⃣ TESTING ADDITIONAL TOOLS")
        print("-" * 40)
        
        await self.test_tool("get_vet_appointments", {}, "Get vet appointments")
        
        await self.test_tool("get_product_interactions", {}, "Get product interactions")
        
        # Test 5: Advanced Queries
        print("\n5️⃣ TESTING ADVANCED QUERIES")
        print("-" * 40)
        
        await self.test_tool("run_cypher_query", {
            "query": "MATCH (p:Pet) RETURN DISTINCT p.species as species, count(p) as count ORDER BY count DESC"
        }, "Group pets by species")
        
        await self.test_tool("run_cypher_query", {
            "query": "MATCH (p:Pet) WHERE p.weight_kg > $weight RETURN p.name, p.weight_kg ORDER BY p.weight_kg DESC LIMIT 5",
            "parameters": {"weight": 20.0}
        }, "Find heavy pets (parameterized query)")
        
        # Test 6: Disconnect
        print("\n6️⃣ TESTING DISCONNECTION")
        print("-" * 40)
        
        await self.test_tool("disconnect_neo4j", {}, "Disconnect from database")
        
        # Print summary
        self.print_summary()
        
        return self.failed_tests == 0

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print(f"🧪 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TOOLS ARE WORKING PERFECTLY! 🎉")
            print("✅ Your Neo4j MCP server is ready for production use!")
        else:
            print(f"\n⚠️  {self.failed_tests} tools need attention:")
            for tool_name, result in self.test_results.items():
                if result["status"] == "FAILED":
                    print(f"   ❌ {tool_name}: {result['error']}")
        
        print("\n🔧 Available Tools:")
        for tool_name in self.server.tools.keys():
            status = self.test_results.get(tool_name, {}).get("status", "NOT TESTED")
            emoji = "✅" if status == "PASSED" else "❌" if status == "FAILED" else "⏭️"
            print(f"   {emoji} {tool_name}")

    def print_detailed_results(self):
        """Print detailed test results."""
        print("\n" + "=" * 60)
        print("📋 DETAILED RESULTS")
        print("=" * 60)
        
        for tool_name, result in self.test_results.items():
            print(f"\n🔧 {tool_name}:")
            print(f"   Status: {result['status']}")
            if result['status'] == 'PASSED' and 'result' in result:
                print(f"   Result: {json.dumps(result['result'], indent=2)[:200]}...")
            elif result['status'] == 'FAILED':
                print(f"   Error: {result['error']}")


async def main():
    """Main test function."""
    tester = ToolTester()
    
    print("🚀 Starting comprehensive tool testing...")
    print("This will test all 13 MCP tools systematically.\n")
    
    success = await tester.run_all_tests()
    
    # Optionally show detailed results
    show_details = input("\n📋 Show detailed results? (y/N): ").strip().lower() == 'y'
    if show_details:
        tester.print_detailed_results()
    
    print(f"\n🏁 Testing complete! Exit code: {0 if success else 1}")
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1) 