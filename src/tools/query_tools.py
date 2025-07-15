"""General query tools for Neo4j database operations."""

import json
from typing import Any, Dict, List

from mcp.types import TextContent, Tool

from .base import ConnectionRequiredTool, create_tool_schema
from ..utils.validators import validate_cypher_query, validate_parameters


class RunCypherQueryTool(ConnectionRequiredTool):
    """Tool for executing custom Cypher queries."""
    
    def __init__(self, connection):
        """
        Initialize query tool.
        
        Args:
            connection: Neo4j connection instance
        """
        super().__init__(
            name="run_cypher_query",
            description="Execute a Cypher query on the Neo4j database",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "query": {
                    "type": "string",
                    "description": "The Cypher query to execute"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the query (optional)",
                    "additionalProperties": True
                }
            },
            required=["query"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute Cypher query."""
        query = arguments["query"]
        parameters = arguments.get("parameters", {})
        
        # Validate query
        if not validate_cypher_query(query):
            return self._format_error_response("Invalid Cypher query")
        
        # Validate parameters
        if not validate_parameters(parameters):
            return self._format_error_response("Invalid query parameters")
        
        try:
            records, summary = await self.connection.execute_query(query, parameters)
            
            response = {
                "query": query,
                "parameters": parameters,
                "records": records,
                "summary": summary
            }
            
            return self._format_success_response(response)
            
        except Exception as e:
            return self._format_error_response(f"Query execution error: {str(e)}")


class GetSchemaInfoTool(ConnectionRequiredTool):
    """Tool for getting detailed schema information."""
    
    def __init__(self, connection):
        """
        Initialize schema info tool.
        
        Args:
            connection: Neo4j connection instance
        """
        super().__init__(
            name="get_schema_info",
            description="Get detailed schema information including constraints and indexes",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={}
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get schema information."""
        try:
            # Get basic schema info
            basic_info = await self.connection.get_database_info()
            
            # Get constraints
            constraints_query = "SHOW CONSTRAINTS"
            constraints, _ = await self.connection.execute_query(constraints_query)
            
            # Get indexes
            indexes_query = "SHOW INDEXES"
            indexes, _ = await self.connection.execute_query(indexes_query)
            
            schema_info = {
                **basic_info,
                "constraints": constraints,
                "indexes": indexes
            }
            
            return self._format_success_response(schema_info)
            
        except Exception as e:
            return self._format_error_response(f"Error getting schema info: {str(e)}")


class ValidateQueryTool(ConnectionRequiredTool):
    """Tool for validating Cypher queries without executing them."""
    
    def __init__(self, connection):
        """
        Initialize query validation tool.
        
        Args:
            connection: Neo4j connection instance
        """
        super().__init__(
            name="validate_query",
            description="Validate a Cypher query without executing it",
            connection=connection
        )
    
    def get_schema(self) -> Tool:
        """Get the tool schema."""
        return create_tool_schema(
            name=self.name,
            description=self.description,
            properties={
                "query": {
                    "type": "string",
                    "description": "The Cypher query to validate"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the query (optional)",
                    "additionalProperties": True
                }
            },
            required=["query"]
        )
    
    async def _execute_with_connection(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Validate Cypher query."""
        query = arguments["query"]
        parameters = arguments.get("parameters", {})
        
        try:
            # Basic validation
            if not validate_cypher_query(query):
                return self._format_error_response("Query failed basic validation")
            
            if not validate_parameters(parameters):
                return self._format_error_response("Invalid query parameters")
            
            # Try to explain the query (this validates syntax without executing)
            explain_query = f"EXPLAIN {query}"
            result, _ = await self.connection.execute_query(explain_query, parameters)
            
            validation_result = {
                "query": query,
                "parameters": parameters,
                "is_valid": True,
                "explanation": result,
                "message": "Query is valid"
            }
            
            return self._format_success_response(validation_result)
            
        except Exception as e:
            validation_result = {
                "query": query,
                "parameters": parameters,
                "is_valid": False,
                "error": str(e),
                "message": "Query validation failed"
            }
            
            return self._format_success_response(validation_result) 