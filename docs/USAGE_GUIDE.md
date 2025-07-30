# Neo4j MCP Tools - Usage Guide

## 🚀 Running the MCP Server

### Method 1: Quick Start (Recommended)

1. **Set your Neo4j password:**
   ```bash
   export NEO4J_PASSWORD=nrxuvCRDnCm5uicdkGmg71DNJFVYxtMfm4gi52I8lWY
   ```

2. **Start the server:**
   ```bash
   python main.py
   ```

### Method 2: Using Environment File

1. **Create/update .env file:**
   ```bash
   echo "NEO4J_PASSWORD=nrxuvCRDnCm5uicdkGmg71DNJFVYxtMfm4gi52I8lWY" >> .env
   ```

2. **Start the server:**
   ```bash
   python run_server.py
   ```

### Method 3: Direct Python Script

```bash
python simple_query_pets.py  # Test basic connection and query
```

---

## 🔧 Available Tools

Your server exposes **11 MCP tools** organized in 3 categories:

### Connection Tools (3)
- `connect_neo4j` - Connect to database
- `get_database_info` - Get connection info  
- `disconnect_neo4j` - Disconnect from database

### Query Tools (3)
- `run_cypher_query` - Execute any Cypher query
- `get_schema_info` - Get database schema
- `validate_query` - Validate query syntax

### Pet Tools (5)
- `get_user_pets` - Get pets owned by a user
- `search_pets_by_criteria` - Search pets by filters
- `get_pet_medical_history` - Get medical records
- `get_pet_health_overview` - Get health summary
- `get_pets_with_active_medications` - Find pets on medication

---

## 👥 How Others Can Use Your Tools

### Option 1: For AI Agents (MCP Client)

**Step 1:** Install the package
```bash
pip install neo4j-mcp-tools
```

**Step 2:** Add to MCP client configuration:
```json
{
  "mcpServers": {
    "neo4j-tools": {
      "command": "neo4j-mcp-server",
      "args": [],
      "env": {
        "NEO4J_URI": "neo4j+s://b2f690c8.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "nrxuvCRDnCm5uicdkGmg71DNJFVYxtMfm4gi52I8lWY",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

**Step 3:** Use tools in agent:
```python
# Agent can now use:
await mcp_client.call_tool("neo4j-tools", "run_cypher_query", {
    "query": "MATCH (p:Pet) RETURN count(p)"
})
```

### Option 2: Direct Local Usage

**Step 1:** Clone your repository
```bash
git clone https://github.com/nbhuyyar-chwy/Graph_MCP.git
cd Graph_MCP
```

**Step 2:** Setup environment
```bash
pip install -r requirements.txt
cp .env.example .env  # Edit with credentials
```

**Step 3:** Run tools directly
```bash
python simple_query_pets.py                # Query all pets
python examples/mcp_tools_demo.py          # See all tools
python query_all_pets.py                   # Advanced queries
```

### Option 3: Using as Python Library

```python
from neo4j_mcp_tools import Neo4jMCPServer, Neo4jConnection

# Create connection
connection = Neo4jConnection(
    uri="neo4j+s://b2f690c8.databases.neo4j.io",
    database="neo4j"
)

# Connect and query
await connection.connect("neo4j", "password")
results = await connection.execute_read_query(
    "MATCH (p:Pet) RETURN p.name, p.species LIMIT 5", {}
)
```

---

## 🌐 Server Deployment Options

### Local Development
```bash
python main.py  # Runs on stdio for MCP clients
```

### Production Deployment
```bash
# Docker deployment (create Dockerfile)
docker build -t neo4j-mcp-server .
docker run -e NEO4J_PASSWORD=password neo4j-mcp-server

# Or systemd service
sudo systemctl enable neo4j-mcp-server
sudo systemctl start neo4j-mcp-server
```

---

## 📋 Common Usage Examples

### 1. Count All Pets
```json
{
  "tool": "run_cypher_query",
  "arguments": {
    "query": "MATCH (p:Pet) RETURN count(p) as total_pets"
  }
}
```

### 2. Find Dogs
```json
{
  "tool": "search_pets_by_criteria", 
  "arguments": {
    "species": "dog",
    "limit": 10
  }
}
```

### 3. Get Medical History
```json
{
  "tool": "get_pet_medical_history",
  "arguments": {
    "pet_name": "Max"
  }
}
```

### 4. Database Schema
```json
{
  "tool": "get_schema_info",
  "arguments": {}
}
```

---

## 🔒 Security & Configuration

### Environment Variables
```bash
NEO4J_URI=neo4j+s://b2f690c8.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_DATABASE=neo4j
AURA_INSTANCEID=b2f690c8
```

### Connection Details (Read-Only)
- **URI**: `neo4j+s://b2f690c8.databases.neo4j.io`
- **Database**: `neo4j`
- **Instance ID**: `b2f690c8`
- **Contains**: 28 pets with complete medical/interaction data

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check environment
python -c "from config import Neo4jConfig; print(Neo4jConfig.is_configured())"

# Test connection
python simple_query_pets.py
```

### Tools Not Available
```bash
# List all tools
echo "1" | python examples/mcp_tools_demo.py

# Test specific tool
python -c "
import asyncio
from src.server import Neo4jMCPServer
server = Neo4jMCPServer()
print(list(server.tools.keys()))
"
```

### Connection Issues
- Verify Neo4j credentials
- Check network connectivity
- Ensure database is running

---

## 📞 Support

- **Repository**: https://github.com/nbhuyyar-chwy/Graph_MCP
- **Issues**: https://github.com/nbhuyyar-chwy/Graph_MCP/issues
- **Examples**: See `examples/mcp_tools_demo.py` and `tests/test_queries.py`

---

## 🚀 Quick Commands Reference

```bash
# List tools
echo "1" | python examples/mcp_tools_demo.py

# Test connection  
python simple_query_pets.py

# Start server
python main.py

# Run with debug
NEO4J_PASSWORD=password python main.py

# Install as package
pip install neo4j-mcp-tools
``` 