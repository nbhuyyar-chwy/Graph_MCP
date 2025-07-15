# Neo4j MCP Server for Pet Care Database

A **modular** Model Context Protocol (MCP) server that provides tools to interact with a Neo4j database containing pet care information including users, pets, vet visits, medications, and product interactions.

## 🏗️ Modular Architecture

This implementation follows a clean, modular architecture for maintainability and extensibility:

```
mcp_graph/
├── src/                          # Main source code
│   ├── database/                 # Database layer
│   │   ├── connection.py         # Neo4j connection management
│   │   └── queries.py            # Cypher query builders
│   ├── models/                   # Data models
│   │   ├── base.py              # Base model classes
│   │   ├── users.py             # User models
│   │   ├── pets.py              # Pet models
│   │   ├── vets.py              # Vet and medical models
│   │   └── products.py          # Product models
│   ├── tools/                    # MCP tools
│   │   ├── base.py              # Base tool classes
│   │   ├── connection_tools.py   # Connection tools
│   │   ├── query_tools.py        # Query tools
│   │   └── pet_tools.py          # Pet-specific tools
│   ├── utils/                    # Utilities
│   │   └── validators.py         # Input validation
│   └── server.py                 # Main server orchestration
├── main.py                       # Entry point
├── config.py                     # Configuration
└── requirements.txt              # Dependencies
```

## Features

This MCP server provides the following tools:

- **connect_neo4j**: Connect to the Neo4j database
- **run_cypher_query**: Execute custom Cypher queries
- **get_database_info**: Get schema and statistics information
- **get_user_pets**: Get all pets owned by a specific user
- **get_pet_medical_history**: Get complete medical history for a pet
- **get_vet_appointments**: Get vet appointments with optional filters
- **get_product_interactions**: Get product interaction data for analysis
- **search_pets_by_criteria**: Search pets by species, breed, weight, gender, etc.

## Database Schema

The Neo4j database contains the following node types and relationships:

### Nodes
- **User**: Pet owners (id, username)
- **Pet**: Individual pets (name, species, breed, birth_date, weight_kg, gender, color, microchip_id)
- **VetVisit**: Medical visits (date, reason, diagnosis, treatment, follow_up_date, notes)
- **Vet**: Veterinarians (name, clinic)
- **Medication**: Prescribed treatments (medication_name, dosage, frequency, start_date, duration_days, reason, notes)
- **ProductInteraction**: Product interactions (date, interaction_type, quantity, feedback, rating, notes)
- **Product**: Products (product_name, brand, category, attributes)

### Relationships
- `(:User)-[:OWNS]->(:Pet)`: User owns pets
- `(:Pet)-[:HAS_VISIT]->(:VetVisit)`: Pet has vet visits
- `(:VetVisit)-[:WITH_VET]->(:Vet)`: Vet visit with veterinarian
- `(:Pet)-[:HAS_MEDICATION]->(:Medication)`: Pet has medications
- `(:Pet)-[:INTERACTED_WITH]->(:ProductInteraction)`: Pet interacts with products
- `(:ProductInteraction)-[:ABOUT_PRODUCT]->(:Product)`: Product interaction details

## Connection Details

- **Neo4j URI**: `neo4j+s://b2f690c8.databases.neo4j.io`
- **Query API URL**: `https://b2f690c8.databases.neo4j.io/db/neo4j/query/v2`
- **Instance ID**: `b2f690c8`
- **Database**: `neo4j`

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file with your Neo4j credentials:
   ```
   NEO4J_USERNAME=your_username
   NEO4J_PASSWORD=your_password
   ```

3. **Run the server**:
   ```bash
   python main.py
   ```
   
   Or use the startup script:
   ```bash
   python run_server.py
   ```

## Usage Examples

### Connect to Database
```python
# Tool: connect_neo4j
{
  "username": "neo4j",
  "password": "your_password"
}
```

### Get User's Pets
```python
# Tool: get_user_pets
{
  "username": "sarah"
}
```

### Get Pet Medical History
```python
# Tool: get_pet_medical_history
{
  "pet_name": "Max",
  "owner_username": "sarah"
}
```

### Search Pets by Criteria
```python
# Tool: search_pets_by_criteria
{
  "species": "Dog",
  "min_weight": 5,
  "max_weight": 30,
  "gender": "Male"
}
```

### Custom Cypher Query
```python
# Tool: run_cypher_query
{
  "query": "MATCH (u:User)-[:OWNS]->(p:Pet) WHERE p.species = $species RETURN u.username, p.name",
  "parameters": {"species": "Cat"}
}
```

### Get Vet Appointments
```python
# Tool: get_vet_appointments
{
  "vet_name": "Dr. Chen",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### Get Product Interactions
```python
# Tool: get_product_interactions
{
  "product_name": "Blue Buffalo",
  "min_rating": 4
}
```

## Security Notes

- Store credentials in environment variables, not in code
- The server connects using encrypted connection (neo4j+s://)
- All queries are parameterized to prevent injection attacks

## Dependencies

- `mcp>=1.0.0`: Model Context Protocol framework
- `neo4j>=5.15.0`: Neo4j Python driver
- `python-dotenv>=1.0.0`: Environment variable management
- `typing-extensions>=4.8.0`: Type hints support
- `asyncio-throttle>=1.0.2`: Async rate limiting

## Error Handling

The server includes comprehensive error handling for:
- Connection failures
- Authentication errors
- Invalid queries
- Missing parameters
- Network timeouts

All errors are returned as descriptive text messages to help with debugging.