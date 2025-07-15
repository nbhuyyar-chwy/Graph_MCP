"""
Neo4j database connection management.

This module handles the connection lifecycle and provides methods for
executing queries against the Neo4j database.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

from ..utils.validators import validate_cypher_query

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connections and query execution."""
    
    def __init__(self, uri: str, database: str = "neo4j"):
        """
        Initialize Neo4j connection manager.
        
        Args:
            uri: Neo4j connection URI
            database: Database name to connect to
        """
        self.uri = uri
        self.database = database
        self.driver: Optional[Driver] = None
        self._is_connected = False
    
    async def connect(self, username: str, password: str) -> bool:
        """
        Connect to Neo4j database.
        
        Args:
            username: Neo4j username
            password: Neo4j password
            
        Returns:
            True if connection successful, False otherwise
            
        Raises:
            AuthError: If authentication fails
            ServiceUnavailable: If Neo4j service is not available
        """
        try:
            # Close existing connection if any
            if self.driver:
                await self.disconnect()
            
            # Create new connection
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(username, password)
            )
            
            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self.driver.verify_connectivity
            )
            
            self._is_connected = True
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
            
        except AuthError as e:
            logger.error(f"Authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Neo4j database."""
        if self.driver:
            await asyncio.get_event_loop().run_in_executor(
                None, self.driver.close
            )
            self.driver = None
            self._is_connected = False
            logger.info("Disconnected from Neo4j")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._is_connected and self.driver is not None
    
    async def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute a Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Tuple of (records, summary) where:
            - records: List of query result records
            - summary: Query execution summary with statistics
            
        Raises:
            ValueError: If not connected or query is invalid
            Neo4jError: If query execution fails
        """
        if not self.is_connected:
            raise ValueError("Not connected to Neo4j database")
        
        if not validate_cypher_query(query):
            raise ValueError("Invalid Cypher query")
        
        parameters = parameters or {}
        
        try:
            def execute():
                with self.driver.session(database=self.database) as session:
                    result = session.run(query, parameters)
                    records = [dict(record) for record in result]
                    counters = result.consume().counters
                    
                    summary = {
                        "nodes_created": counters.nodes_created,
                        "nodes_deleted": counters.nodes_deleted,
                        "relationships_created": counters.relationships_created,
                        "relationships_deleted": counters.relationships_deleted,
                        "properties_set": counters.properties_set,
                        "records_returned": len(records)
                    }
                    
                    return records, summary
            
            records, summary = await asyncio.get_event_loop().run_in_executor(
                None, execute
            )
            
            logger.debug(f"Query executed successfully. Records: {len(records)}")
            return records, summary
            
        except Neo4jError as e:
            logger.error(f"Query execution failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise
    
    async def execute_read_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a read-only Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of query result records
        """
        records, _ = await self.execute_query(query, parameters)
        return records
    
    async def execute_write_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute a write Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Tuple of (records, summary)
        """
        return await self.execute_query(query, parameters)
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions.
        
        Usage:
            async with connection.transaction() as tx:
                await tx.run(query, parameters)
        """
        if not self.is_connected:
            raise ValueError("Not connected to Neo4j database")
        
        def get_session():
            return self.driver.session(database=self.database)
        
        session = await asyncio.get_event_loop().run_in_executor(
            None, get_session
        )
        
        try:
            tx = session.begin_transaction()
            yield tx
            await asyncio.get_event_loop().run_in_executor(None, tx.commit)
        except Exception as e:
            await asyncio.get_event_loop().run_in_executor(None, tx.rollback)
            raise e
        finally:
            await asyncio.get_event_loop().run_in_executor(None, session.close)
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get database schema and statistics.
        
        Returns:
            Dictionary containing database information
        """
        if not self.is_connected:
            raise ValueError("Not connected to Neo4j database")
        
        try:
            def get_info():
                with self.driver.session(database=self.database) as session:
                    # Get node labels
                    labels_result = session.run("CALL db.labels()")
                    labels = [record["label"] for record in labels_result]
                    
                    # Get relationship types
                    rels_result = session.run("CALL db.relationshipTypes()")
                    relationships = [record["relationshipType"] for record in rels_result]
                    
                    # Get node counts
                    node_counts = {}
                    for label in labels:
                        count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                        node_counts[label] = count_result.single()["count"]
                    
                    # Get relationship counts
                    rel_counts = {}
                    for rel in relationships:
                        count_result = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) as count")
                        rel_counts[rel] = count_result.single()["count"]
                    
                    return {
                        "node_labels": labels,
                        "relationship_types": relationships,
                        "node_counts": node_counts,
                        "relationship_counts": rel_counts,
                        "database": self.database,
                        "uri": self.uri
                    }
            
            return await asyncio.get_event_loop().run_in_executor(None, get_info)
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            raise 