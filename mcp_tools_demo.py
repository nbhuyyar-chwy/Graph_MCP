#!/usr/bin/env python3
"""
MCP Tools Demonstration

This script shows all available MCP tools and how to call them.
"""

import json

def show_available_tools():
    """Show all available MCP tools."""
    print("🔧 Neo4j MCP Server - Available Tools")
    print("=" * 50)
    
    tools = [
        # Connection Tools
        {
            "name": "connect_neo4j",
            "description": "Connect to Neo4j database",
            "category": "Connection",
            "parameters": ["username", "password"]
        },
        {
            "name": "get_database_info", 
            "description": "Get database connection info",
            "category": "Connection",
            "parameters": []
        },
        {
            "name": "disconnect_neo4j",
            "description": "Disconnect from Neo4j",
            "category": "Connection", 
            "parameters": []
        },
        
        # Query Tools
        {
            "name": "run_cypher_query",
            "description": "Execute any Cypher query",
            "category": "Query",
            "parameters": ["query", "parameters (optional)"]
        },
        {
            "name": "get_schema_info",
            "description": "Get database schema information", 
            "category": "Query",
            "parameters": []
        },
        {
            "name": "validate_query",
            "description": "Validate a Cypher query syntax",
            "category": "Query",
            "parameters": ["query"]
        },
        
        # Pet Tools
        {
            "name": "get_user_pets",
            "description": "Get all pets owned by a user",
            "category": "Pet",
            "parameters": ["username"]
        },
        {
            "name": "get_pet_medical_history", 
            "description": "Get medical history for a specific pet",
            "category": "Pet",
            "parameters": ["pet_name", "owner_username (optional)"]
        },
        {
            "name": "search_pets_by_criteria",
            "description": "Search pets by various criteria",
            "category": "Pet", 
            "parameters": ["species (optional)", "breed (optional)", "min_weight (optional)", "max_weight (optional)", "gender (optional)", "limit (optional)"]
        },
        {
            "name": "get_pet_health_overview",
            "description": "Get health overview for a pet",
            "category": "Pet",
            "parameters": ["pet_name"]
        },
        {
            "name": "get_pets_with_active_medications",
            "description": "Get pets currently on medication", 
            "category": "Pet",
            "parameters": []
        }
    ]
    
    print(f"📋 Total Tools Available: {len(tools)}")
    
    # Group by category
    categories = {}
    for tool in tools:
        cat = tool["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)
    
    for category, cat_tools in categories.items():
        print(f"\n🔧 {category.upper()} TOOLS ({len(cat_tools)} tools)")
        print("-" * 40)
        
        for tool in cat_tools:
            print(f"   • {tool['name']}")
            print(f"     {tool['description']}")
            if tool['parameters']:
                print(f"     Parameters: {', '.join(tool['parameters'])}")
            else:
                print(f"     Parameters: None")
            print()

# Usage examples for each tool  
TOOL_USAGE_EXAMPLES = {
    "connect_neo4j": {
        "description": "Connect to Neo4j database",
        "parameters": {
            "username": "neo4j", 
            "password": "nrxuvCRDnCm5uicdkGmg71DNJFVYxtMfm4gi52I8lWY"
        },
        "example_call": """
# How to call in MCP client:
{
    "tool": "connect_neo4j",
    "arguments": {
        "username": "neo4j",
        "password": "your_password"
    }
}"""
    },
    
    "get_database_info": {
        "description": "Get database connection info",
        "parameters": {},
        "example_call": """
# How to call in MCP client:
{
    "tool": "get_database_info",
    "arguments": {}
}"""
    },
    
    "run_cypher_query": {
        "description": "Execute any Cypher query",
        "parameters": {
            "query": "MATCH (p:Pet) RETURN p.name, p.species LIMIT 5",
            "parameters": {}  # optional
        },
        "example_call": """
# How to call in MCP client:
{
    "tool": "run_cypher_query", 
    "arguments": {
        "query": "MATCH (p:Pet) WHERE p.species = $species RETURN p.name",
        "parameters": {"species": "dog"}
    }
}"""
    },
    
    "get_user_pets": {
        "description": "Get all pets owned by a user",
        "parameters": {
            "username": "user123"
        },
        "example_call": """
# How to call in MCP client:
{
    "tool": "get_user_pets",
    "arguments": {
        "username": "sarah"
    }
}"""
    },
    
    "search_pets_by_criteria": {
        "description": "Search pets by various criteria",
        "parameters": {
            "species": "dog",        # optional
            "breed": "Labrador",     # optional  
            "min_weight": 10.0,      # optional
            "max_weight": 30.0,      # optional
            "gender": "male",        # optional
            "limit": 10              # optional
        },
        "example_call": """
# How to call in MCP client:
{
    "tool": "search_pets_by_criteria",
    "arguments": {
        "species": "cat",
        "min_weight": 5.0,
        "limit": 5
    }
}"""
    },
    
    "get_pet_medical_history": {
        "description": "Get medical history for a specific pet",
        "parameters": {
            "pet_name": "Max",
            "owner_username": "user123"  # optional
        },
        "example_call": """
# How to call in MCP client:
{
    "tool": "get_pet_medical_history",
    "arguments": {
        "pet_name": "Max"
    }
}"""
    },
    
    "get_pets_with_active_medications": {
        "description": "Get pets currently on medication",
        "parameters": {},
        "example_call": """
# How to call in MCP client:
{
    "tool": "get_pets_with_active_medications",
    "arguments": {}
}"""
    }
}

def show_usage_examples():
    """Show usage examples for all tools."""
    print("\n📖 MCP TOOLS USAGE EXAMPLES")
    print("=" * 60)
    
    for tool_name, example in TOOL_USAGE_EXAMPLES.items():
        print(f"\n🔧 {tool_name}")
        print(f"   {example['description']}")
        print(f"   Parameters: {json.dumps(example['parameters'], indent=15)}")
        print(f"   {example['example_call']}")
        print("-" * 50)

def show_quick_start():
    """Show quick start guide."""
    print("\n🚀 QUICK START GUIDE")
    print("=" * 60)
    print("""
1. Start the MCP Server:
   python run_server.py

2. Connect your MCP client to the server

3. Use tools in this order:
   
   Step 1: Connect to database
   -> connect_neo4j
   
   Step 2: Explore the data  
   -> get_database_info
   -> get_schema_info
   -> run_cypher_query (MATCH (p:Pet) RETURN count(p))
   
   Step 3: Use specialized pet tools
   -> get_pets_with_active_medications
   -> search_pets_by_criteria
   -> get_user_pets (if you know a username)

4. Common Cypher queries you can run:
   - Count all pets: "MATCH (p:Pet) RETURN count(p)"
   - List pet species: "MATCH (p:Pet) RETURN DISTINCT p.species"
   - Get first 5 pets: "MATCH (p:Pet) RETURN p.name, p.species LIMIT 5"
   - Find dogs: "MATCH (p:Pet) WHERE p.species = 'dog' RETURN p.name"
""")

if __name__ == "__main__":
    print("🎯 Choose what you want to see:")
    print("1. List all available tools")
    print("2. Show detailed usage examples") 
    print("3. Show quick start guide")
    print("4. Show everything")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        show_available_tools()
    elif choice == "2":
        show_usage_examples()
    elif choice == "3":
        show_quick_start()
    else:
        show_available_tools()
        show_usage_examples() 
        show_quick_start() 