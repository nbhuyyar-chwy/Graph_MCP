"""
Main MCP server module for Neo4j Pet Care Database.

This module orchestrates all the components to create a fully functional
MCP server for interacting with Neo4j databases.
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent

from .database import Neo4jConnection, QueryBuilder
from .tools.connection_tools import ConnectNeo4jTool, GetDatabaseInfoTool, DisconnectNeo4jTool
from .tools.query_tools import RunCypherQueryTool, GetSchemaInfoTool, ValidateQueryTool
from .tools.pet_tools import (
    GetUserPetsTool, GetPetMedicalHistoryTool, SearchPetsByCriteriaTool,
    GetPetHealthOverviewTool, GetPetsWithActiveMedicationsTool
)
from config import Neo4jConfig

logger = logging.getLogger(__name__)


class Neo4jMCPServer:
    """Main MCP server for Neo4j database operations."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("neo4j-mcp")
        
        # Initialize database connection
        self.connection = Neo4jConnection(
            uri=Neo4jConfig.URI,
            database=Neo4jConfig.DATABASE
        )
        
        # Initialize tools
        self._initialize_tools()
        
        # Register handlers
        self._register_handlers()
    
    def _initialize_tools(self):
        """Initialize all MCP tools."""
        self.tools = {
            # Connection tools
            "connect_neo4j": ConnectNeo4jTool(self.connection),
            "get_database_info": GetDatabaseInfoTool(self.connection),
            "disconnect_neo4j": DisconnectNeo4jTool(self.connection),
            
            # Query tools
            "run_cypher_query": RunCypherQueryTool(self.connection),
            "get_schema_info": GetSchemaInfoTool(self.connection),
            "validate_query": ValidateQueryTool(self.connection),
            
            # Pet tools
            "get_user_pets": GetUserPetsTool(self.connection),
            "get_pet_medical_history": GetPetMedicalHistoryTool(self.connection),
            "search_pets_by_criteria": SearchPetsByCriteriaTool(self.connection),
            "get_pet_health_overview": GetPetHealthOverviewTool(self.connection),
            "get_pets_with_active_medications": GetPetsWithActiveMedicationsTool(self.connection),
        }
    
    def _register_handlers(self):
        """Register MCP handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [tool.get_schema() for tool in self.tools.values()]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name not in self.tools:
                    return [TextContent(
                        type="text", 
                        text=f"Error: Unknown tool '{name}'. Available tools: {', '.join(self.tools.keys())}"
                    )]
                
                tool = self.tools[name]
                return await tool.execute(arguments)
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.connection:
            await self.connection.disconnect()
    
    async def run(self):
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="neo4j-mcp",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={},
                        ),
                    ),
                )
        finally:
            await self.cleanup()


# Additional simplified tools for common operations
class VetAppointmentsTool:
    """Simplified tool for vet appointments that can be added to the server."""
    
    def __init__(self, connection):
        self.connection = connection
        self.name = "get_vet_appointments"
        self.description = "Get vet appointments with optional filters"
    
    def get_schema(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "vet_name": {
                        "type": "string",
                        "description": "Name of the veterinarian (optional)"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format (optional)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format (optional)"
                    }
                }
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute vet appointments query."""
        if not self.connection.is_connected:
            return [TextContent(type="text", text="Error: Not connected to database")]
        
        try:
            query, params = QueryBuilder.get_vet_appointments(
                vet_name=arguments.get("vet_name"),
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date")
            )
            
            records = await self.connection.execute_read_query(query, params)
            
            import json
            return [TextContent(type="text", text=json.dumps({
                "total_appointments": len(records),
                "appointments": records
            }, indent=2, default=str))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


class ProductInteractionsTool:
    """Simplified tool for product interactions."""
    
    def __init__(self, connection):
        self.connection = connection
        self.name = "get_product_interactions"
        self.description = "Get product interaction data for analysis"
    
    def get_schema(self) -> Tool:
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema={
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Specific product name (optional)"
                    },
                    "interaction_type": {
                        "type": "string",
                        "description": "Type of interaction (optional)"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum rating filter (optional)"
                    }
                }
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute product interactions query."""
        if not self.connection.is_connected:
            return [TextContent(type="text", text="Error: Not connected to database")]
        
        try:
            query, params = QueryBuilder.get_product_interactions(
                product_name=arguments.get("product_name"),
                interaction_type=arguments.get("interaction_type"),
                min_rating=arguments.get("min_rating")
            )
            
            records = await self.connection.execute_read_query(query, params)
            
            import json
            return [TextContent(type="text", text=json.dumps({
                "total_interactions": len(records),
                "interactions": records
            }, indent=2, default=str))]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]


def create_server() -> Neo4jMCPServer:
    """Factory function to create a configured MCP server."""
    server = Neo4jMCPServer()
    
    # Add additional tools
    server.tools["get_vet_appointments"] = VetAppointmentsTool(server.connection)
    server.tools["get_product_interactions"] = ProductInteractionsTool(server.connection)
    
    return server


async def main():
    """Main entry point for the server."""
    logging.basicConfig(level=logging.INFO)
    
    server = create_server()
    
    logger.info("Starting Neo4j MCP Server...")
    logger.info(f"Available tools: {', '.join(server.tools.keys())}")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 