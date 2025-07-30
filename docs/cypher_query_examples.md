# 🔍 Custom Cypher Query Guide for Neo4j Pet Care Database

## 📚 Ways to Run Custom Queries

### Method 1: Interactive Query Runner (Recommended)
```bash
NEO4J_PASSWORD=your_password python run_custom_query.py
```

### Method 2: Direct MCP Tool Call
```python
import asyncio
from src.server import Neo4jMCPServer

async def run_query():
    server = Neo4jMCPServer()
    
    # Connect
    await server.tools['connect_neo4j'].execute({
        'username': 'neo4j', 
        'password': 'your_password'
    })
    
    # Run query
    result = await server.tools['run_cypher_query'].execute({
        'query': 'MATCH (p:Pet) RETURN count(p) as total',
        'parameters': {}  # Optional
    })
    
    print(result[0].text)
    
    # Disconnect
    await server.tools['disconnect_neo4j'].execute({})

asyncio.run(run_query())
```

### Method 3: One-liner Script
```bash
NEO4J_PASSWORD=password python -c "
import asyncio, json
from src.server import Neo4jMCPServer

async def query():
    s = Neo4jMCPServer()
    await s.tools['connect_neo4j'].execute({'username': 'neo4j', 'password': 'password'})
    r = await s.tools['run_cypher_query'].execute({'query': 'MATCH (p:Pet) RETURN p.name, p.species LIMIT 5'})
    print(json.loads(r[0].text)['records'])
    await s.tools['disconnect_neo4j'].execute({})

asyncio.run(query())
"
```

## 🎯 Sample Query Categories

### 1. Basic Data Exploration

**Count records by type:**
```cypher
MATCH (p:Pet) RETURN count(p) as total_pets
MATCH (u:User) RETURN count(u) as total_users  
MATCH (v:VetVisit) RETURN count(v) as total_visits
```

**Get all unique values:**
```cypher
MATCH (p:Pet) RETURN DISTINCT p.species as species
MATCH (p:Pet) RETURN DISTINCT p.breed as breed ORDER BY breed
MATCH (vet:Vet) RETURN DISTINCT vet.clinic as clinics
```

### 2. Relationship Queries

**Pets with their owners:**
```cypher
MATCH (u:User)-[:OWNS]->(p:Pet)
RETURN u.username as owner, p.name as pet, p.species, p.breed
ORDER BY owner, pet
```

**Complex relationships:**
```cypher
MATCH (u:User)-[:OWNS]->(p:Pet)-[:HAS_VISIT]->(v:VetVisit)-[:WITH_VET]->(vet:Vet)
RETURN u.username as owner, p.name as pet, v.date as visit_date, 
       v.reason, vet.name as veterinarian
ORDER BY v.date DESC
LIMIT 10
```

### 3. Filtering and Conditions

**Pets by weight range:**
```cypher
MATCH (u:User)-[:OWNS]->(p:Pet)
WHERE p.weight_kg BETWEEN $min_weight AND $max_weight
RETURN u.username as owner, p.name as pet, p.weight_kg as weight
ORDER BY p.weight_kg DESC
```
*Parameters: `{"min_weight": 10, "max_weight": 30}`*

**Recent vet visits:**
```cypher
MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit)
WHERE v.date >= date() - duration({months: $months})
RETURN p.name as pet, v.date, v.reason, v.diagnosis
ORDER BY v.date DESC
```
*Parameters: `{"months": 6}`*

### 4. Aggregation and Analytics

**Pets per owner:**
```cypher
MATCH (u:User)-[:OWNS]->(p:Pet)
RETURN u.username as owner, count(p) as pet_count, 
       collect(p.name) as pet_names
ORDER BY pet_count DESC
```

**Average weight by species:**
```cypher
MATCH (p:Pet)
WHERE p.weight_kg IS NOT NULL
RETURN p.species, 
       avg(p.weight_kg) as avg_weight,
       min(p.weight_kg) as min_weight,
       max(p.weight_kg) as max_weight,
       count(p) as total_pets
ORDER BY avg_weight DESC
```

**Vet workload analysis:**
```cypher
MATCH (vet:Vet)<-[:WITH_VET]-(v:VetVisit)<-[:HAS_VISIT]-(p:Pet)
RETURN vet.name as veterinarian, 
       vet.clinic as clinic,
       count(v) as total_visits,
       count(DISTINCT p) as unique_pets,
       min(v.date) as first_visit,
       max(v.date) as last_visit
ORDER BY total_visits DESC
```

### 5. Product Analysis

**Top-rated products:**
```cypher
MATCH (pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product)
WHERE pi.rating IS NOT NULL
RETURN prod.product_name as product, 
       prod.brand, 
       prod.category,
       avg(pi.rating) as avg_rating,
       count(pi) as total_interactions,
       collect(DISTINCT pi.interaction_type) as interaction_types
ORDER BY avg_rating DESC, total_interactions DESC
LIMIT 10
```

**Product usage by pet species:**
```cypher
MATCH (p:Pet)-[:INTERACTED_WITH]->(pi:ProductInteraction)-[:ABOUT_PRODUCT]->(prod:Product)
RETURN p.species, 
       prod.category, 
       count(pi) as interactions,
       avg(pi.rating) as avg_rating
ORDER BY p.species, interactions DESC
```

### 6. Health and Medical Queries

**Pets with active medications:**
```cypher
MATCH (p:Pet)-[:HAS_MEDICATION]->(m:Medication)
WHERE m.start_date <= date() 
  AND date() <= (m.start_date + duration({days: m.duration_days}))
RETURN p.name as pet, 
       m.medication_name, 
       m.dosage, 
       m.frequency,
       m.start_date,
       (m.start_date + duration({days: m.duration_days})) as end_date
ORDER BY m.start_date DESC
```

**Most common diagnoses:**
```cypher
MATCH (v:VetVisit)
WHERE v.diagnosis IS NOT NULL
RETURN v.diagnosis as diagnosis, 
       count(*) as frequency,
       collect(DISTINCT v.reason) as common_reasons
ORDER BY frequency DESC
LIMIT 10
```

### 7. Advanced Pattern Matching

**Pets with multiple vet visits:**
```cypher
MATCH (p:Pet)-[:HAS_VISIT]->(v:VetVisit)
WITH p, count(v) as visit_count
WHERE visit_count > 1
MATCH (u:User)-[:OWNS]->(p)
RETURN u.username as owner, 
       p.name as pet, 
       visit_count
ORDER BY visit_count DESC
```

**Find pet families (same owner, different pets):**
```cypher
MATCH (u:User)-[:OWNS]->(p:Pet)
WITH u, collect(p) as pets
WHERE size(pets) > 1
RETURN u.username as owner,
       size(pets) as pet_count,
       [p IN pets | p.name + " (" + p.species + ")"] as pet_details
ORDER BY pet_count DESC
```

### 8. Data Quality and Exploration

**Missing or null data:**
```cypher
MATCH (p:Pet)
RETURN 
  count(CASE WHEN p.weight_kg IS NULL THEN 1 END) as missing_weight,
  count(CASE WHEN p.breed IS NULL THEN 1 END) as missing_breed,
  count(CASE WHEN p.birth_date IS NULL THEN 1 END) as missing_birth_date,
  count(p) as total_pets
```

**Schema exploration:**
```cypher
CALL db.labels() YIELD label
RETURN label ORDER BY label
```

```cypher
CALL db.relationshipTypes() YIELD relationshipType
RETURN relationshipType ORDER BY relationshipType
```

## 🚀 Pro Tips

### Using Parameters
Always use parameters for dynamic values:
```cypher
// Good ✅
MATCH (p:Pet) WHERE p.species = $species RETURN p
// Parameters: {"species": "dog"}

// Avoid ❌  
MATCH (p:Pet) WHERE p.species = "dog" RETURN p
```

### Limiting Results
Always limit large result sets:
```cypher
MATCH (p:Pet) RETURN p ORDER BY p.name LIMIT 20
```

### Performance Optimization
Use indexes for common queries:
```cypher
// Check existing indexes
SHOW INDEXES

// Create index if needed (admin operation)
CREATE INDEX pet_species IF NOT EXISTS FOR (p:Pet) ON (p.species)
```

### Complex Conditions
Use CASE statements for complex logic:
```cypher
MATCH (p:Pet)
RETURN p.name,
       CASE 
         WHEN p.weight_kg < 5 THEN "Small"
         WHEN p.weight_kg < 25 THEN "Medium" 
         ELSE "Large"
       END as size_category
```

## 🎯 Quick Start Examples

Run these in your interactive query runner:

1. **Basic exploration:**
   ```
   MATCH (p:Pet) RETURN p.name, p.species, p.breed LIMIT 10
   ```

2. **Find your favorite breed:**
   ```
   MATCH (p:Pet) WHERE p.breed CONTAINS "Labrador" RETURN p.name, p.weight_kg
   ```

3. **Owner with most pets:**
   ```
   MATCH (u:User)-[:OWNS]->(p:Pet) RETURN u.username, count(p) as pets ORDER BY pets DESC LIMIT 1
   ```

Happy querying! 🐾 