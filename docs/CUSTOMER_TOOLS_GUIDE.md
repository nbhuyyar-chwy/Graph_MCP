# Customer Management MCP Tools Guide
*Complete guide for accessing customer data via MCP tools*

## 🎯 Overview

The customer management MCP tools provide comprehensive access to customer data including:
- **AI-Generated Insights** (likes, dislikes, intent tags, summaries)
- **Purchase Behavior** (products organized by category)
- **Pet Information** (hierarchical pet structure)
- **Web Activity** (session data and behavior analysis)
- **Customer Management** (add/update customers and pets)

## 📊 Available Tools

### 1. `get_customer_profile`
**Purpose**: Get complete customer profile with AI insights
```json
{
  "customer_id": "6180005"
}
```
**Returns**: Basic info + AI insights (likes, dislikes, tags, summary)

### 2. `get_customer_tags`
**Purpose**: Get AI-generated user intent tags
```json
{
  "customer_id": "6180005"
}
```
**Returns**: Intent tags like "High Spending", "Pet Lover", "Brand Loyal"

### 3. `get_customer_likes`
**Purpose**: Get customer preferences and likes
```json
{
  "customer_id": "6180005"
}
```
**Returns**: AI-analyzed preferences and brand preferences

### 4. `get_customer_dislikes`
**Purpose**: Get customer dislikes
```json
{
  "customer_id": "6180005"
}
```
**Returns**: Things the customer might dislike or avoid

### 5. `get_customer_products`
**Purpose**: Get purchase data organized by category
```json
{
  "customer_id": "6180005",
  "limit_orders": 5
}
```
**Returns**: Hierarchical product structure with spending data

### 6. `get_customer_pets`
**Purpose**: Get pets organized by type
```json
{
  "customer_id": "6180005"
}
```
**Returns**: Hierarchical pet structure with pet details

### 7. `get_customer_web_data`
**Purpose**: Get web session data
```json
{
  "customer_id": "6180005",
  "limit_sessions": 10
}
```
**Returns**: Session data with event counts and importance scores

### 8. `add_customer`
**Purpose**: Add new customer with comprehensive data
```json
{
  "headers": "CUSTOMER_ID\tCUSTOMER_NAME\t...",
  "data": "12345\tJohn Doe\t..."
}
```
**Returns**: Created/updated customer information

### 9. `add_customer_pet`
**Purpose**: Add pet and create hierarchical structure
```json
{
  "headers": "PETPROFILE_ID\tPETNAME\t...",
  "data": "98765\tFluffy\t...",
  "create_hierarchy": true
}
```
**Returns**: Pet creation and hierarchy setup results

## 🚀 Usage Examples

### Matt Osius (Customer ID: 6180005) Test Results

**Profile Summary:**
- **Name**: Matt Osius
- **Email**: chewy.mm@grxme.com  
- **Autoship**: Active
- **Average Order**: $80.62
- **Total Spent**: $19,184.14

**AI Insights:**
- **Intent Tags**: High Spending, Frequent Shopper, Pet Lover, Prefer Autoship, Gift Card Purchaser, High Website Engagement, Brand Loyal
- **Likes**: Nylabone, Fancy Feast, Bones & Chews, Nandi, Feline Natural, Purina Pro Plan, Fussie Cat, Sheba, Farnam and Nutramax brands
- **About**: Loyal customer with preference for Autoship service, wide variety of pets, high website engagement

**Pet Data** (9 pets across 3 categories):
- **Cat Pets**: 3 pets (Rumpel, Mungo, ...)
- **Dog Pets**: 2 pets (Whiskey - English Setter, Gigi - Miniature Poodle)
- **Horse Pets**: 4 pets (Tumelo - Friesian, Adamo - Andalusian, ...)

**Purchase Behavior**:
- **Cat Products**: $9,940.95 (179 orders)
- **Dog Products**: $6,713.41 (87 orders)  
- **Horse Products**: $1,953.53 (21 orders)

**Web Activity**: 11 sessions with 33-260 events per session

## 🔧 How to Call Tools

### Method 1: Direct MCP Server

```bash
# Start the MCP server
cd /Users/nbhuyyar/chewy/mcp_graph
source venv/bin/activate
python main.py
```

Then send MCP tool call messages via stdio.

### Method 2: Direct Integration (Python)

```python
import asyncio
from src.server import create_server
from config import Neo4jConfig

async def use_customer_tools():
    # Setup server
    server = create_server()
    username, password = Neo4jConfig.get_credentials()
    await server.connection.connect(username, password)
    
    # Call tools
    result = await server.tools['get_customer_profile'].execute({
        'customer_id': '6180005'
    })
    
    print(result[0].text)  # JSON response
    
    await server.connection.disconnect()

asyncio.run(use_customer_tools())
```

### Method 3: External Client (Recommended)

```python
# See examples/external_client_example.py for complete implementation
class CustomerDataClient:
    def __init__(self, mcp_server_connection):
        self.connection = mcp_server_connection
    
    async def get_customer_360_view(self, customer_id: str):
        # Calls multiple MCP tools to build comprehensive view
        profile = await self._call_mcp_tool("get_customer_profile", {"customer_id": customer_id})
        pets = await self._call_mcp_tool("get_customer_pets", {"customer_id": customer_id})
        products = await self._call_mcp_tool("get_customer_products", {"customer_id": customer_id})
        # ... etc
        
        return {
            "profile": profile,
            "pets": pets, 
            "products": products
        }
```

## 🌐 Integration Patterns

### For Recommendation Systems
```python
# Get customer preferences and purchase history
likes = await tools['get_customer_likes'].execute({'customer_id': customer_id})
products = await tools['get_customer_products'].execute({'customer_id': customer_id})
pets = await tools['get_customer_pets'].execute({'customer_id': customer_id})

# Use data to generate personalized recommendations
```

### For Marketing Platforms
```python
# Get customer segments and intent tags
tags = await tools['get_customer_tags'].execute({'customer_id': customer_id})
profile = await tools['get_customer_profile'].execute({'customer_id': customer_id})

# Target campaigns based on AI insights
```

### For Customer Service
```python
# Get complete customer context
full_profile = await tools['get_customer_profile'].execute({'customer_id': customer_id})
web_activity = await tools['get_customer_web_data'].execute({'customer_id': customer_id})

# Provide personalized support
```

## 🏗️ Data Architecture

The tools access a hierarchical Neo4j structure:

```
Customer
├── Basic Properties (name, email, autoship, etc.)
├── AI Insights (likes, dislikes, intent_tags, about_user)
├── HIS_PRODUCTS → His Products Hub
│   └── HAS_CATEGORY → Category Products → BOUGHT → Orders
├── HIS_PETS → His Pets Hub  
│   └── HAS_PET_TYPE → Pet Type Categories → HAS_PET → Individual Pets
└── HAS_WEB_DATA → Web Data → HAS_SESSION → Sessions
```

## 🛠️ Server Files

**Main Files:**
- `src/tools/customer_management_tools.py` - All customer MCP tools
- `src/server.py` - MCP server setup with tool registration
- `main.py` - Server entry point
- `test_tools_simple.py` - Testing and demonstration
- `examples/external_client_example.py` - External integration example

**Test & Integration:**
- Run `python test_tools_simple.py` to test all functionality
- Run `python examples/external_client_example.py` for integration demo
- Use `test_customer_tools.py` for comprehensive MCP testing

## ✅ Verification

All tools have been tested and verified with customer ID `6180005` (Matt Osius):
- ✅ Complete customer profile with AI insights
- ✅ 9 pets across 3 categories (Dog, Cat, Horse)
- ✅ $19,184+ in purchases across 7 product categories  
- ✅ 11+ web sessions with behavior analysis
- ✅ Ready for production MCP tool integration

## 🔑 Required Environment

```bash
# .env file required with:
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key  # For AI insights generation
``` 