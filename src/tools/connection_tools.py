"""Connection tools for Neo4j database operations."""

import os
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from .base import BaseTool, create_tool_schema


class ConnectNeo4jTool(BaseTool):
    """Tool for connecting to Neo4j database."""
    
    def __init__(self, connection):
        """
        Initialize connection tool.
        
        Args:
            connection: Neo4j connection instance
        """
        super().__init__(
            name="connect_neo4j",
            description="Connect to the Neo4j database"
        )
        self.connection = connection
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "username": {
                    "type": "string",
                    "description": "Neo4j username (optional if set in env)"
                },
                "password": {
                    "type": "string",
                    "description": "Neo4j password (optional if set in env)"
                }
            }
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute connection to Neo4j."""
        try:
            username = arguments.get("username") or os.getenv("NEO4J_USERNAME", "neo4j")
            password = arguments.get("password") or os.getenv("NEO4J_PASSWORD")
            
            if not password:
                return self._format_error_response(
                    "Neo4j password is required. Set NEO4J_PASSWORD environment variable or provide it as parameter."
                )
            
            # Attempt connection
            success = await self.connection.connect(username, password)
            
            if success:
                return self._format_success_response({
                    "status": "connected",
                    "message": f"Successfully connected to Neo4j database at {self.connection.uri}",
                    "database": self.connection.database
                })
            else:
                return self._format_error_response("Failed to connect to Neo4j database")
                
        except Exception as e:
            return self._format_error_response(f"Connection error: {str(e)}")


class GetDatabaseInfoTool(BaseTool):
    """Tool for getting database schema and statistics."""
    
    def __init__(self, connection):
        """
        Initialize database info tool.
        
        Args:
            connection: Neo4j connection instance
        """
        super().__init__(
            name="get_database_info",
            description="Get general information about the Neo4j database schema and statistics"
        )
        self.connection = connection
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={}
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute database info retrieval."""
        if not self.connection or not self.connection.is_connected:
            return self._format_error_response(
                "Not connected to Neo4j database. Use connect_neo4j tool first."
            )
        
        try:
            info = await self.connection.get_database_info()
            return self._format_success_response(info)
            
        except Exception as e:
            return self._format_error_response(f"Error getting database info: {str(e)}")


class DisconnectNeo4jTool(BaseTool):
    """Tool for disconnecting from Neo4j database."""
    
    def __init__(self, connection):
        """
        Initialize disconnect tool.
        
        Args:
            connection: Neo4j connection instance
        """
        super().__init__(
            name="disconnect_neo4j",
            description="Disconnect from the Neo4j database"
        )
        self.connection = connection
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={}
        )
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute disconnection from Neo4j."""
        try:
            if self.connection:
                await self.connection.disconnect()
                return self._format_success_response({
                    "status": "disconnected",
                    "message": "Successfully disconnected from Neo4j database"
                })
            else:
                return self._format_success_response({
                    "status": "not_connected",
                    "message": "No active connection to disconnect"
                })
                
        except Exception as e:
            return self._format_error_response(f"Disconnect error: {str(e)}") 