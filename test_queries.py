#!/usr/bin/env python3
"""
Test queries for the Neo4j Pet Care database

This script contains example Cypher queries that can be used to test
the Neo4j MCP server functionality.
"""

# Sample test queries for the pet care database
TEST_QUERIES = {
    "get_all_users": {
        "description": "Get all users in the database",
        "query": "MATCH (u:User) RETURN u.username as username, u.id as id ORDER BY u.username"
    },
    
    "get_all_pets": {
        "description": "Get all pets with their basic information",
        "query": """
        MATCH (u:User)-[:OWNS]->(p:Pet)
        RETURN u.username as owner, p.name as pet_name, p.species as species, 
               p.breed as breed, p.weight_kg as weight, p.gender as gender
        ORDER BY u.username, p.name
        """
    },
    
    "get_pets_by_species": {
        "description": "Get all pets of a specific species",
        "query": """
        MATCH (u:User)-[:OWNS]->(p:Pet)
        WHERE p.species = $species
        RETURN u.username as owner, p.name as pet_name, p.breed as breed,
               p.weight_kg as weight, p.birth_date as birth_date
        ORDER BY p.name
        """,
        "parameters": {"species": "Dog"}
    },
    
    "get_recent_vet_visits": {
        "description": "Get recent vet visits (last 30 days)",
        "query": """
        MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet),
              (u:User)-[:OWNS]->(p)
        WHERE v.date >= date() - duration({days: 30})
        RETURN v.date as visit_date, p.name as pet_name, u.username as owner,
               v.reason as reason, v.diagnosis as diagnosis, vet.name as vet_name
        ORDER BY v.date DESC
        """
    },
    
    "get_pets_with_medications": {
        "description": "Get pets currently on medication",
        "query": """
        MATCH (u:User)-[:OWNS]->(p:Pet)-[:HAS_MEDICATION]->(m:Medication)
        WHERE m.start_date <= date() AND 
              (m.start_date + duration({days: m.duration_days})) >= date()
        RETURN u.username as owner, p.name as pet_name, 
               m.medication_name as medication, m.dosage as dosage,
               m.frequency as frequency, m.reason as reason
        ORDER BY u.username, p.name
        """
    },
    
    "get_product_ratings": {
        "description": "Get average ratings for products",
        "query": """
        MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product)
        WHERE pi.rating IS NOT NULL
        RETURN prod.product_name as product, prod.brand as brand, 
               prod.category as category,
               avg(pi.rating) as avg_rating, count(pi) as total_interactions
        ORDER BY avg_rating DESC, total_interactions DESC
        """
    },
    
    "get_vet_workload": {
        "description": "Get vet workload statistics",
        "query": """
        MATCH (vet:Vet)<-[:WITH_VET]-(v:VetVisit)
        RETURN vet.name as vet_name, vet.clinic as clinic,
               count(v) as total_visits,
               min(v.date) as first_visit,
               max(v.date) as last_visit
        ORDER BY total_visits DESC
        """
    },
    
    "get_pet_health_overview": {
        "description": "Get health overview for a specific pet",
        "query": """
        MATCH (u:User)-[:OWNS]->(p:Pet {name: $pet_name})
        OPTIONAL MATCH (p)-[:HAS_VISIT]->(v:VetVisit)
        OPTIONAL MATCH (p)-[:HAS_MEDICATION]->(m:Medication)
        RETURN p.name as pet_name, p.species as species, p.breed as breed,
               p.birth_date as birth_date, p.weight_kg as weight,
               u.username as owner,
               count(DISTINCT v) as total_vet_visits,
               count(DISTINCT m) as total_medications,
               max(v.date) as last_vet_visit
        """,
        "parameters": {"pet_name": "Max"}
    },
    
    "get_popular_products": {
        "description": "Get most popular products by interaction count",
        "query": """
        MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product)
        RETURN prod.product_name as product, prod.brand as brand,
               prod.category as category,
               count(pi) as interaction_count,
               avg(pi.rating) as avg_rating,
               collect(DISTINCT pi.interaction_type) as interaction_types
        ORDER BY interaction_count DESC
        LIMIT 10
        """
    },
    
    "get_pets_needing_followup": {
        "description": "Get pets that need follow-up visits",
        "query": """
        MATCH (u:User)-[:OWNS]->(p:Pet)-[:HAS_VISIT]->(v:VetVisit)
        WHERE v.follow_up_date IS NOT NULL AND v.follow_up_date >= date()
        RETURN u.username as owner, p.name as pet_name,
               v.date as visit_date, v.follow_up_date as follow_up_date,
               v.reason as visit_reason, v.diagnosis as diagnosis
        ORDER BY v.follow_up_date ASC
        """
    }
}

def print_query(query_name: str):
    """Print a formatted query"""
    if query_name in TEST_QUERIES:
        query_info = TEST_QUERIES[query_name]
        print(f"\n=== {query_name.upper().replace('_', ' ')} ===")
        print(f"Description: {query_info['description']}")
        print(f"Query:")
        print(query_info['query'])
        if 'parameters' in query_info:
            print(f"Parameters: {query_info['parameters']}")
        print("-" * 50)
    else:
        print(f"Query '{query_name}' not found")

def print_all_queries():
    """Print all available test queries"""
    print("AVAILABLE TEST QUERIES FOR NEO4J PET CARE DATABASE")
    print("=" * 60)
    
    for query_name in TEST_QUERIES.keys():
        print_query(query_name)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        query_name = sys.argv[1]
        print_query(query_name)
    else:
        print_all_queries()
        print("\nUsage: python test_queries.py [query_name]")
        print("Available queries:", ", ".join(TEST_QUERIES.keys())) 