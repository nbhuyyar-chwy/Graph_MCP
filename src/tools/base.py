"""Base classes and utilities for MCP tools."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from mcp.types import TextContent, Tool

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all MCP tools."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize base tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_schema(self) -> Tool:
        """Get the tool schema for MCP registration."""
        pass
    
    @abstractmethod
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute the tool with given arguments."""
        pass
    
    def _format_success_response(self, data: Any) -> List[TextContent]:
        """Format a successful response."""
        try:
            if isinstance(data, (dict, list)):
                content = json.dumps(data, indent=2, default=str)
            else:
                content = str(data)
            
            return [TextContent(type="text", text=content)]
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return [TextContent(type="text", text=f"Response formatting error: {e}")]
    
    def _format_error_response(self, error: str) -> List[TextContent]:
        """Format an error response."""
        return [TextContent(type="text", text=f"Error: {error}")]
    
    def _validate_required_args(self, arguments: Dict[str, Any], required_fields: List[str]) -> Optional[str]:
        """
        Validate required arguments.
        
        Args:
            arguments: Tool arguments
            required_fields: List of required field names
            
        Returns:
            Error message if validation fails, None if successful
        """
        missing_fields = []
        for field in required_fields:
            if field not in arguments or arguments[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            return f"Missing required fields: {', '.join(missing_fields)}"
        
        return None


class ConnectionRequiredTool(BaseTool):
    """Base class for tools that require a database connection."""
    
    def __init__(self, name: str, description: str, connection):
        """
        Initialize connection-required tool.
        
        Args:
            name: Tool name
            description: Tool description
            connection: Neo4j connection instance
        """
        super().__init__(name, description)
        self.connection = connection
    
    async def execute(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute tool with connection validation."""
        # Check connection
        if not self.connection or not self.connection.is_connected:
            return self._format_error_response(
                "Not connected to Neo4j database. Use connect_neo4j tool first."
            )
        
        try:
            return await self._execute_with_connection(arguments)
        except Exception as e:
            logger.error(f"Error executing {self.name}: {e}")
            return self._format_error_response(str(e))
    
    @abstractmethod
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute tool logic with validated connection."""
        pass


def create_tool_schema(
    name: str,
    description: str,
    properties: Dict[str, Any],
    required: Optional[List[str]] = None
) -> Tool:
    """
    Helper function to create tool schema.
    
    Args:
        name: Tool name
        description: Tool description
        properties: Input schema properties
        required: List of required property names
        
    Returns:
        Tool schema object
    """
    return Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required or []
        }
    ) 