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
    GetPetHealthOverviewTool, GetPetsWithActiveMedicationsTool,
    GetProductInteractionsTool, GetVetAppointmentsTool
)
from .tools.user_session_tools import (
    GetUserSummaryTool, GetUserTagsTool, GetSessionSummaryTool
)
from .tools.customer_management_tools import (
    GetCustomerTagsTool, GetCustomerLikesTool, GetCustomerDislikesTool,
    GetCustomerProductsTool, GetCustomerPetsTool, GetCustomerWebDataTool,
    GetCustomerProfileTool, AddCustomerTool, AddCustomerPetTool
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
            
            # Additional tools
            "get_product_interactions": GetProductInteractionsTool(self.connection),
            "get_vet_appointments": GetVetAppointmentsTool(self.connection),
            
            # User session analysis tools
            "get_user_summary": GetUserSummaryTool(self.connection),
            "get_user_tags": GetUserTagsTool(self.connection),
            "get_session_summary": GetSessionSummaryTool(self.connection),
            
            # Customer management tools
            "get_customer_tags": GetCustomerTagsTool(self.connection),
            "get_customer_likes": GetCustomerLikesTool(self.connection),
            "get_customer_dislikes": GetCustomerDislikesTool(self.connection),
            "get_customer_products": GetCustomerProductsTool(self.connection),
            "get_customer_pets": GetCustomerPetsTool(self.connection),
            "get_customer_web_data": GetCustomerWebDataTool(self.connection),
            "get_customer_profile": GetCustomerProfileTool(self.connection),
            "add_customer": AddCustomerTool(self.connection),
            "add_customer_pet": AddCustomerPetTool(self.connection),
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


def create_server() -> Neo4jMCPServer:
    """Factory function to create a configured MCP server."""
    return Neo4jMCPServer()


async def main():
    """Main entry point for the server."""
    logging.basicConfig(level=logging.INFO)
    
    server = create_server()
    
    logger.info("Starting Neo4j MCP Server...")
    logger.info(f"Available tools: {', '.join(server.tools.keys())}")
    
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 