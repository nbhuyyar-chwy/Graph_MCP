#!/usr/bin/env python3
"""
Simple script to query all pets from the Neo4j database.
"""

import asyncio
import os
from dotenv import load_dotenv
from src.database.connection import Neo4jConnection
from config import Neo4jConfig

# Load environment variables
load_dotenv()

async def query_all_pets():
    """Query all pets in the database."""
    
    # Check if password is configured
    if not Neo4jConfig.is_configured():
        print("❌ Neo4j password not configured!")
        print("Please set NEO4J_PASSWORD environment variable or in .env file")
        return
    
    # Create connection
    connection = Neo4jConnection(
        uri=Neo4jConfig.URI,
        database=Neo4jConfig.DATABASE
    )
    
    try:
        # Connect to database
        username, password = Neo4jConfig.get_credentials()
        if not password:
            print("❌ Neo4j password is required!")
            return
        
        await connection.connect(username, password)
        print("✅ Connected to Neo4j database")
        print(f"🔗 URI: {Neo4jConfig.URI}")
        print(f"📊 Database: {Neo4jConfig.DATABASE}")
        print(f"🆔 Instance ID: {Neo4jConfig.INSTANCE_ID}")
        
        # Query to get all pets
        cypher_query = """
        MATCH (p:Pet)
        RETURN p.name as pet_name, 
               p.species as species, 
               p.breed as breed, 
               p.birth_date as birth_date, 
               p.weight_kg as weight, 
               p.gender as gender,
               p.color as color, 
               p.microchip_id as microchip_id
        ORDER BY p.name
        """
        
        print("\n🔍 Querying all pets...")
        print(f"Query: {cypher_query}")
        
        # Execute the query
        records = await connection.execute_read_query(cypher_query, {})
        
        print("\n📋 Results:")
        print("=" * 50)
        
        if records:
            print(f"Found {len(records)} pets:")
            
            for i, pet in enumerate(records, 1):
                print(f"\n{i}. Pet: {pet.get('pet_name', 'Unknown')}")
                print(f"   Species: {pet.get('species', 'Unknown')}")
                print(f"   Breed: {pet.get('breed', 'Unknown')}")
                print(f"   Gender: {pet.get('gender', 'Unknown')}")
                print(f"   Weight: {pet.get('weight', 'Unknown')} kg")
                print(f"   Color: {pet.get('color', 'Unknown')}")
                if pet.get('birth_date'):
                    print(f"   Birth Date: {pet.get('birth_date')}")
                if pet.get('microchip_id'):
                    print(f"   Microchip: {pet.get('microchip_id')}")
        else:
            print("No pets found in the database")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up connection
        await connection.disconnect()
        print("\n🔌 Disconnected from database")

if __name__ == "__main__":
    asyncio.run(query_all_pets()) 