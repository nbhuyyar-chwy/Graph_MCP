from neo4j import GraphDatabase

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j+s://b2f690c8.databases.neo4j.io"
AUTH = ("neo4j", "nrxuvCRDnCm5uicdkGmg71DNJFVYxtMfm4gi52I8lWY")

def query_all_pets():
    """Query all pets from the database"""
    
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        # Verify connectivity
        driver.verify_connectivity()
        print("✅ Connected to Neo4j database successfully!")
        print(f"🔗 URI: {URI}")
        
        # Query all pets
        with driver.session() as session:
            # Cypher query to get all pets
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
            
            result = session.run(cypher_query)
            pets = list(result)
            
            print("\n📋 Results:")
            print("=" * 50)
            
            if pets:
                print(f"Found {len(pets)} pets:")
                
                for i, pet in enumerate(pets, 1):
                    print(f"\n{i}. Pet: {pet['pet_name']}")
                    print(f"   Species: {pet['species']}")
                    print(f"   Breed: {pet['breed']}")
                    print(f"   Gender: {pet['gender']}")
                    print(f"   Weight: {pet['weight']} kg")
                    print(f"   Color: {pet['color']}")
                    if pet['birth_date']:
                        print(f"   Birth Date: {pet['birth_date']}")
                    if pet['microchip_id']:
                        print(f"   Microchip: {pet['microchip_id']}")
            else:
                print("No pets found in the database")

if __name__ == "__main__":
    # Instructions for the user
    print("📝 SETUP INSTRUCTIONS:")
    print("1. Edit this file and replace <Username> and <Password> with your actual Neo4j credentials")
    print("2. Run the script: python simple_query_pets.py")
    print("=" * 70)
    
    try:
        query_all_pets()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure to:")
        print("- Replace <Username> and <Password> with your actual credentials")
        print("- Check your internet connection") 
        print("- Verify your Neo4j database is running") 