#!/usr/bin/env python3
"""
Interactive Custom Cypher Query Runner
Run any Cypher query against the Neo4j pet care database.
"""

import asyncio
import json
import sys
from src.server import Neo4jMCPServer
from config import Neo4jConfig

class CustomQueryRunner:
    def __init__(self):
        self.server = Neo4jMCPServer()
        self.connected = False
    
    async def connect(self):
        """Connect to the database."""
        if not self.connected:
            print("🔌 Connecting to Neo4j database...")
            try:
                result = await self.server.tools['connect_neo4j'].execute({
                    'username': Neo4jConfig.USERNAME,
                    'password': Neo4jConfig.PASSWORD
                })
                if "Successfully connected" in result[0].text:
                    self.connected = True
                    print("✅ Connected successfully!")
                    return True
                else:
                    print("❌ Connection failed!")
                    return False
            except Exception as e:
                print(f"❌ Connection error: {e}")
                return False
        return True
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connected:
            await self.server.tools['disconnect_neo4j'].execute({})
            self.connected = False
            print("🔌 Disconnected from database")
    
    async def run_query(self, query, parameters=None):
        """Run a custom Cypher query."""
        if not self.connected:
            await self.connect()
        
        if not self.connected:
            return None
        
        try:
            args = {'query': query}
            if parameters:
                args['parameters'] = parameters
            
            result = await self.server.tools['run_cypher_query'].execute(args)
            data = json.loads(result[0].text)
            return data
        except Exception as e:
            print(f"❌ Query error: {e}")
            return None
    
    def format_results(self, data):
        """Format query results for display."""
        if not data or 'records' not in data:
            return "No results"
        
        records = data['records']
        if not records:
            return "Query executed successfully - no records returned"
        
        # Get column headers
        if records:
            headers = list(records[0].keys())
            
            # Print headers
            output = []
            output.append("=" * 80)
            output.append(" | ".join(f"{h:<15}" for h in headers))
            output.append("=" * 80)
            
            # Print rows
            for record in records[:20]:  # Limit to first 20 rows
                row = " | ".join(f"{str(record.get(h, '')):<15}" for h in headers)
                output.append(row)
            
            if len(records) > 20:
                output.append(f"... and {len(records) - 20} more rows")
            
            output.append("=" * 80)
            output.append(f"Total records: {len(records)}")
            
            return "\n".join(output)
        
        return str(data)

async def main():
    runner = CustomQueryRunner()
    
    print("🐾 Neo4j Pet Care Database - Custom Query Runner")
    print("=" * 60)
    print("Enter 'help' for sample queries, 'quit' to exit")
    print("=" * 60)
    
    # Connect to database
    connected = await runner.connect()
    if not connected:
        print("Failed to connect to database. Exiting.")
        return
    
    # Sample queries for help
    sample_queries = {
        "1": {
            "name": "Count all pets",
            "query": "MATCH (p:Pet) RETURN count(p) as total_pets"
        },
        "2": {
            "name": "List all pets with owners",
            "query": "MATCH (u:User)-[:OWNS]->(p:Pet) RETURN u.username as owner, p.name as pet_name, p.species, p.breed ORDER BY owner, pet_name"
        },
        "3": {
            "name": "Find pets by species",
            "query": "MATCH (p:Pet) WHERE p.species = $species RETURN p.name, p.breed, p.weight_kg ORDER BY p.name",
            "parameters": {"species": "dog"}
        },
        "4": {
            "name": "Recent vet visits",
            "query": "MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet), (u:User)-[:OWNS]->(p) RETURN p.name as pet, u.username as owner, v.date, v.reason, vet.name as vet ORDER BY v.date DESC LIMIT 10"
        },
        "5": {
            "name": "Product interactions with ratings",
            "query": "MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product) WHERE pi.rating IS NOT NULL RETURN p.name as pet, prod.product_name as product, pi.rating, pi.feedback ORDER BY pi.rating DESC LIMIT 10"
        },
        "6": {
            "name": "Database schema info",
            "query": "CALL db.schema.visualization() YIELD nodes, relationships RETURN nodes, relationships"
        },
        "7": {
            "name": "Pets needing follow-up",
            "query": "MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit) WHERE v.follow_up_date >= date() RETURN p.name as pet, v.follow_up_date, v.reason, v.diagnosis ORDER BY v.follow_up_date"
        },
        "8": {
            "name": "Top-rated products",
            "query": "MATCH (pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product) WHERE pi.rating IS NOT NULL RETURN prod.product_name, prod.brand, avg(pi.rating) as avg_rating, count(pi) as interactions ORDER BY avg_rating DESC, interactions DESC LIMIT 10"
        }
    }
    
    try:
        while True:
            print("\n" + "="*60)
            query_input = input("\n💬 Enter your Cypher query (or 'help', 'quit'): ").strip()
            
            if query_input.lower() in ['quit', 'exit', 'q']:
                break
            elif query_input.lower() in ['help', 'h']:
                print("\n📚 Sample Queries:")
                print("-" * 40)
                for num, info in sample_queries.items():
                    print(f"{num}. {info['name']}")
                print("\nType a number (1-8) to run a sample query, or enter your own Cypher query.")
                continue
            elif query_input in sample_queries:
                # Run sample query
                sample = sample_queries[query_input]
                print(f"\n🔍 Running: {sample['name']}")
                print(f"Query: {sample['query']}")
                if 'parameters' in sample:
                    print(f"Parameters: {sample['parameters']}")
                    data = await runner.run_query(sample['query'], sample['parameters'])
                else:
                    data = await runner.run_query(sample['query'])
            else:
                # Run custom query
                print(f"\n🔍 Running your query...")
                
                # Check if user wants to add parameters
                if '$' in query_input:
                    param_input = input("💬 Enter parameters as JSON (or press Enter for none): ").strip()
                    parameters = None
                    if param_input:
                        try:
                            parameters = json.loads(param_input)
                        except json.JSONDecodeError:
                            print("❌ Invalid JSON parameters. Running without parameters.")
                    data = await runner.run_query(query_input, parameters)
                else:
                    data = await runner.run_query(query_input)
            
            # Display results
            if data:
                print("\n📊 Results:")
                print(runner.format_results(data))
            else:
                print("❌ Query failed or returned no data")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        await runner.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 