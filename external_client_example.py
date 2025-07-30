#!/usr/bin/env python3
"""
External Client Example for Customer Management MCP Tools
=========================================================

This example shows how external applications can integrate with the MCP server
to access customer data. This could be used by recommendation systems,
marketing platforms, or customer service applications.
"""

import asyncio
import json
import logging
from typing import Dict, Any

# This would typically be imported from your MCP client library
# For this example, we'll simulate the connection


class CustomerDataClient:
    """External client for accessing customer data via MCP tools."""
    
    def __init__(self, mcp_server_connection):
        """Initialize with MCP server connection."""
        self.connection = mcp_server_connection
    
    async def get_customer_360_view(self, customer_id: str) -> Dict[str, Any]:
        """
        Get a complete 360-degree view of a customer.
        
        This method demonstrates how you would typically call multiple
        MCP tools to build a comprehensive customer profile.
        """
        print(f"🔍 Building 360° view for customer {customer_id}...")
        
        customer_data = {}
        
        try:
            # Get basic profile
            profile_result = await self._call_mcp_tool("get_customer_profile", {
                "customer_id": customer_id
            })
            customer_data["profile"] = profile_result
            
            # Get AI insights
            tags_result = await self._call_mcp_tool("get_customer_tags", {
                "customer_id": customer_id
            })
            customer_data["intent_tags"] = tags_result.get("intent_tags", [])
            
            likes_result = await self._call_mcp_tool("get_customer_likes", {
                "customer_id": customer_id
            })
            customer_data["likes"] = likes_result.get("likes", [])
            
            # Get behavioral data
            products_result = await self._call_mcp_tool("get_customer_products", {
                "customer_id": customer_id,
                "limit_orders": 10
            })
            customer_data["purchase_behavior"] = products_result
            
            pets_result = await self._call_mcp_tool("get_customer_pets", {
                "customer_id": customer_id
            })
            customer_data["pets"] = pets_result
            
            web_result = await self._call_mcp_tool("get_customer_web_data", {
                "customer_id": customer_id,
                "limit_sessions": 20
            })
            customer_data["web_activity"] = web_result
            
            print(f"✅ Successfully built 360° view for {customer_id}")
            return customer_data
            
        except Exception as e:
            print(f"❌ Error building customer view: {e}")
            return {}
    
    async def get_customer_recommendations(self, customer_id: str) -> Dict[str, Any]:
        """Generate product recommendations based on customer data."""
        print(f"🎯 Generating recommendations for customer {customer_id}...")
        
        # Get customer insights
        customer_view = await self.get_customer_360_view(customer_id)
        
        # Extract relevant data for recommendations
        profile = customer_view.get("profile", {})
        likes = customer_view.get("likes", [])
        pets = customer_view.get("pets", {})
        purchase_behavior = customer_view.get("purchase_behavior", {})
        
        # Build recommendation logic (simplified example)
        recommendations = {
            "customer_id": customer_id,
            "customer_name": profile.get("basic_info", {}).get("name", "Unknown"),
            "recommendation_score": 0.85,
            "recommended_products": [],
            "reasoning": []
        }
        
        # Example recommendation logic based on pets
        pet_categories = pets.get("pet_categories", [])
        for category in pet_categories:
            pet_type = category.get("pet_type", "")
            pets_list = category.get("pets", [])
            
            if pet_type.lower() == "dog" and len(pets_list) > 0:
                recommendations["recommended_products"].extend([
                    "Premium Dog Food",
                    "Dog Training Treats",
                    "Interactive Dog Toys"
                ])
                recommendations["reasoning"].append(f"Customer has {len(pets_list)} dog(s)")
        
        # Example recommendation based on likes
        for like in likes:
            if "premium" in like.lower():
                recommendations["recommended_products"].append("Premium Brand Products")
                recommendations["reasoning"].append("Customer prefers premium products")
        
        print(f"✅ Generated {len(recommendations['recommended_products'])} recommendations")
        return recommendations
    
    async def _call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool and return parsed result.
        
        In a real implementation, this would use the MCP protocol
        to communicate with the server over stdio or other transport.
        """
        # For this example, we'll directly call the tool
        # In practice, you'd use the MCP client library
        
        if tool_name not in self.connection.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.connection.tools[tool_name]
        result = await tool.execute(arguments)
        
        if result and len(result) > 0:
            try:
                return json.loads(result[0].text)
            except json.JSONDecodeError:
                return {"raw_result": result[0].text}
        
        return {}


async def demonstrate_external_usage():
    """Demonstrate how an external application would use the customer tools."""
    print("🌟 External Application Integration Example")
    print("=" * 60)
    print()
    
    # Import and setup (this would be done differently in a real external app)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    from src.server import create_server
    from config import Neo4jConfig
    
    # Setup server connection
    server = create_server()
    username, password = Neo4jConfig.get_credentials()
    await server.connection.connect(username, password)
    
    # Create client
    client = CustomerDataClient(server)
    
    try:
        # Example 1: Get 360° customer view
        print("📊 Example 1: Complete Customer Profile")
        print("-" * 40)
        customer_view = await client.get_customer_360_view("6180005")
        
        profile = customer_view.get("profile", {})
        basic_info = profile.get("basic_info", {})
        print(f"Customer: {basic_info.get('name', 'Unknown')}")
        print(f"Email: {basic_info.get('email', 'Unknown')}")
        print(f"Intent Tags: {', '.join(customer_view.get('intent_tags', []))}")
        print()
        
        # Example 2: Generate recommendations
        print("🎯 Example 2: Product Recommendations")
        print("-" * 40)
        recommendations = await client.get_customer_recommendations("6180005")
        print(f"Customer: {recommendations['customer_name']}")
        print(f"Recommendation Score: {recommendations['recommendation_score']}")
        print("Recommended Products:")
        for product in recommendations['recommended_products']:
            print(f"  • {product}")
        print("Reasoning:")
        for reason in recommendations['reasoning']:
            print(f"  • {reason}")
        print()
        
        print("✅ External application integration successful!")
        
    except Exception as e:
        print(f"❌ Error in external application: {e}")
        logging.exception("External app error")
    
    finally:
        await server.connection.disconnect()


if __name__ == "__main__":
    asyncio.run(demonstrate_external_usage()) 