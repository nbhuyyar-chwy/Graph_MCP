#!/usr/bin/env python3
"""
Graph Database Population Script

This script connects to Neo4j database and populates it with customer and pet data.
It performs the following operations:
1. Connects to Neo4j using configuration from .env file
2. Deletes all existing nodes and relationships
3. Creates Customer nodes from customers.csv (ALL columns as properties)
4. Creates Pet nodes from pet_profile.csv (ALL columns as properties)  
5. Creates :OWNS_PET relationships between customers and pets

Usage:
    python populate_graph.py [--dry-run] [--batch-size SIZE]
"""

import asyncio
import csv
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import argparse
from contextlib import asynccontextmanager
import re

# Import Neo4j libraries
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Configuration (inline since we can't import config easily)
class Neo4jConfig:
    """Neo4j database configuration"""
    
    # Neo4j connection details
    URI = "neo4j+s://b2f690c8.databases.neo4j.io"
    DATABASE = "neo4j"
    INSTANCE_ID = "b2f690c8"
    QUERY_API_URL = "https://b2f690c8.databases.neo4j.io/db/neo4j/query/v2"
    
    # Authentication (can be overridden by environment variables)
    USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    
    @classmethod
    def get_credentials(cls) -> tuple[str, Optional[str]]:
        """Get Neo4j credentials"""
        return cls.USERNAME, cls.PASSWORD
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if Neo4j is properly configured"""
        return bool(cls.PASSWORD)


# Simple Cypher query validator
def validate_cypher_query(query: str) -> bool:
    """Basic validation for Cypher queries."""
    if not query or not isinstance(query, str):
        return False
    
    query = query.strip()
    if not query:
        return False
    
    # Check for obvious dangerous patterns
    import re
    dangerous_patterns = [
        r';\s*DROP\s+',
        r';\s*DELETE\s+',
        r';\s*ALTER\s+',
        r'--',
        r'/\*.*\*/',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return False
    
    return True


# Custom Neo4j Connection class (inline to avoid import issues)
class Neo4jConnection:
    """Manages Neo4j database connections and query execution."""
    
    def __init__(self, uri: str, database: str = "neo4j"):
        """Initialize Neo4j connection manager."""
        self.uri = uri
        self.database = database
        self.driver: Optional[Driver] = None
        self._is_connected = False
    
    async def connect(self, username: str, password: str) -> bool:
        """Connect to Neo4j database."""
        try:
            if self.driver:
                await self.disconnect()
            
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(username, password)
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None, self.driver.verify_connectivity
            )
            
            self._is_connected = True
            logging.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
            
        except AuthError as e:
            logging.error(f"Authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logging.error(f"Neo4j service unavailable: {e}")
            raise
        except Exception as e:
            logging.error(f"Connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Neo4j database."""
        if self.driver:
            await asyncio.get_event_loop().run_in_executor(
                None, self.driver.close
            )
            self.driver = None
            self._is_connected = False
            logging.info("Disconnected from Neo4j")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to database."""
        return self._is_connected and self.driver is not None
    
    async def execute_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Execute a Cypher query."""
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
            
            logging.debug(f"Query executed successfully. Records: {len(records)}")
            return records, summary
            
        except Neo4jError as e:
            logging.error(f"Query execution failed: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error during query execution: {e}")
            raise
    
    async def execute_write_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Execute a write Cypher query."""
        return await self.execute_query(query, parameters)
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get database schema and statistics."""
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
                        # Skip labels with special characters that cause syntax errors
                        if ' ' in label or '-' in label:
                            continue
                        try:
                            count_result = session.run(f"MATCH (n:`{label}`) RETURN count(n) as count")
                            node_counts[label] = count_result.single()["count"]
                        except:
                            continue
                    
                    # Get relationship counts
                    rel_counts = {}
                    for rel in relationships:
                        try:
                            count_result = session.run(f"MATCH ()-[r:`{rel}`]->() RETURN count(r) as count")
                            rel_counts[rel] = count_result.single()["count"]
                        except:
                            continue
                    
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
            logging.error(f"Error getting database info: {e}")
            raise


def sanitize_property_name(name: str) -> str:
    """Convert CSV column name to valid Neo4j property name."""
    # Convert to lowercase and replace non-alphanumeric chars with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'prop_' + sanitized
    return sanitized


def infer_data_type_and_convert(value: str, column_name: str) -> tuple[str, Any]:
    """
    Infer data type from column name and value, return (cypher_conversion, processed_value).
    """
    if value is None or value == '':
        return 'null', None
    
    value_str = str(value).strip()
    column_lower = column_name.lower()
    
    # Date/DateTime fields
    if any(keyword in column_lower for keyword in ['dttm', 'date', 'birthday']):
        if value_str and value_str != 'null':
            try:
                # Try parsing various date formats
                if len(value_str) >= 19:  # Full datetime
                    dt = datetime.strptime(value_str[:19], '%Y-%m-%d %H:%M:%S')
                    return 'datetime(item.{column})', dt.isoformat()
                elif len(value_str) >= 10:  # Date only
                    return 'date(item.{column})', value_str[:10]
            except:
                pass
    
    # Boolean fields
    if any(keyword in column_lower for keyword in ['flag', 'active']):
        if value_str.lower() in ['true', 'false']:
            return 'item.{column} = "true"', value_str.lower()
    
    # Numeric fields
    if any(keyword in column_lower for keyword in ['count', 'id', 'key', 'value', 'weight', 'score', 'nps']):
        try:
            if '.' in value_str:
                float(value_str)
                return 'toFloat(item.{column})', value_str
            else:
                int(value_str)
                return 'toInteger(item.{column})', value_str
        except ValueError:
            pass
    
    # Default to string
    return 'item.{column}', value_str


def generate_property_mappings(columns: List[str]) -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Generate property mappings for all columns.
    Returns (property_to_column_map, cypher_conversion_map)
    """
    property_to_column = {}
    cypher_conversions = {}
    
    for column in columns:
        prop_name = sanitize_property_name(column)
        property_to_column[prop_name] = column
        
        # Get appropriate cypher conversion based on column name
        conversion_template, _ = infer_data_type_and_convert("sample", column)
        cypher_conversions[prop_name] = conversion_template.replace('item.{column}', f'item.{column}')
    
    return property_to_column, cypher_conversions


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('populate_graph.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class GraphPopulator:
    """Handles population of Neo4j graph database with customer and pet data."""
    
    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        """Initialize the graph populator."""
        self.connection = Neo4jConnection(
            uri=Neo4jConfig.URI,
            database=Neo4jConfig.DATABASE
        )
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            'customers_created': 0,
            'pets_created': 0,
            'relationships_created': 0,
            'nodes_deleted': 0
        }
    
    async def connect(self) -> bool:
        """Connect to Neo4j database."""
        try:
            username, password = Neo4jConfig.get_credentials()
            if not password:
                logger.error("❌ NEO4J_PASSWORD not set in environment variables")
                return False
                
            logger.info(f"🔗 Connecting to Neo4j at {Neo4jConfig.URI}")
            await self.connection.connect(username, password)
            logger.info("✅ Successfully connected to Neo4j")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Neo4j database."""
        await self.connection.disconnect()
        logger.info("🔌 Disconnected from Neo4j")
    
    async def clear_database(self):
        """Delete all existing nodes and relationships."""
        logger.info("🗑️  Clearing existing data from database...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would delete all nodes and relationships")
            return
        
        try:
            # Delete all relationships first
            delete_rels_query = "MATCH ()-[r]-() DELETE r"
            _, summary = await self.connection.execute_write_query(delete_rels_query)
            relationships_deleted = summary.get('relationships_deleted', 0)
            logger.info(f"🔗 Deleted {relationships_deleted} relationships")
            
            # Delete all nodes
            delete_nodes_query = "MATCH (n) DELETE n"
            _, summary = await self.connection.execute_write_query(delete_nodes_query)
            nodes_deleted = summary.get('nodes_deleted', 0)
            logger.info(f"🗂️  Deleted {nodes_deleted} nodes")
            
            self.stats['nodes_deleted'] = nodes_deleted
            logger.info("✅ Database cleared successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear database: {e}")
            raise
    
    def load_csv_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from CSV file, preserving ALL columns including null values."""
        logger.info(f"📄 Loading data from {file_path}")
        
        # Adjust path to be relative to parent directory
        full_path = Path(__file__).parent.parent / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"CSV file not found: {full_path}")
        
        data = []
        with open(full_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Keep ALL values, convert empty strings to None
                cleaned_row = {k: (v if v.strip() else None) if v else None for k, v in row.items()}
                data.append(cleaned_row)
        
        logger.info(f"📊 Loaded {len(data)} records from {file_path}")
        if data:
            logger.info(f"📝 Columns found: {len(data[0])} total columns")
        return data
    
    def process_data_for_neo4j(self, data: List[Dict[str, Any]], columns: List[str]) -> List[Dict[str, Any]]:
        """Process data with proper type conversion for Neo4j."""
        processed_data = []
        
        for row in data:
            processed_row = {}
            for column in columns:
                value = row.get(column)
                _, processed_value = infer_data_type_and_convert(value, column)
                processed_row[column] = processed_value
            processed_data.append(processed_row)
        
        return processed_data
    
    async def create_customers(self, customers_data: List[Dict[str, Any]]):
        """Create Customer nodes from customers data with ALL columns as properties."""
        logger.info(f"👥 Creating {len(customers_data)} customer nodes with ALL columns...")
        
        if not customers_data:
            logger.warning("No customer data to process")
            return
        
        # Get all columns from the data
        all_columns = list(customers_data[0].keys())
        logger.info(f"📋 Processing {len(all_columns)} customer columns")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would create customer nodes with columns:")
            for i, col in enumerate(all_columns):
                if i < 10:  # Show first 10 columns
                    logger.info(f"   - {col}")
            if len(all_columns) > 10:
                logger.info(f"   ... and {len(all_columns) - 10} more columns")
            return
        
        # Generate property mappings
        prop_to_col, cypher_conversions = generate_property_mappings(all_columns)
        
        # Build dynamic property assignment string
        property_assignments = []
        for prop_name, column in prop_to_col.items():
            conversion = cypher_conversions[prop_name].replace(f'item.{column}', f'item.{column}')
            property_assignments.append(f"{prop_name}: {conversion}")
        
        # Process in batches
        for i in range(0, len(customers_data), self.batch_size):
            batch = customers_data[i:i + self.batch_size]
            logger.info(f"📦 Processing customer batch {i//self.batch_size + 1} ({len(batch)} customers)")
            
            # Create dynamic batch insert query
            query = f"""
            UNWIND $customers AS item
            CREATE (c:Customer {{
                {',\n                '.join(property_assignments)}
            }})
            """
            
            try:
                # Process data for Neo4j
                processed_batch = self.process_data_for_neo4j(batch, all_columns)
                
                _, summary = await self.connection.execute_write_query(
                    query, {"customers": processed_batch}
                )
                batch_created = summary.get('nodes_created', 0)
                self.stats['customers_created'] += batch_created
                logger.info(f"✅ Created {batch_created} customer nodes in batch")
                
            except Exception as e:
                logger.error(f"❌ Failed to create customer batch: {e}")
                logger.error(f"Query was: {query[:500]}...")
                raise
        
        logger.info(f"👥 Successfully created {self.stats['customers_created']} customer nodes")
    
    async def create_pets(self, pets_data: List[Dict[str, Any]]):
        """Create Pet nodes from pet profile data with ALL columns as properties."""
        logger.info(f"🐕 Creating {len(pets_data)} pet nodes with ALL columns...")
        
        if not pets_data:
            logger.warning("No pet data to process")
            return
        
        # Get all columns from the data
        all_columns = list(pets_data[0].keys())
        logger.info(f"📋 Processing {len(all_columns)} pet profile columns")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would create pet nodes with columns:")
            for i, col in enumerate(all_columns):
                if i < 10:  # Show first 10 columns
                    logger.info(f"   - {col}")
            if len(all_columns) > 10:
                logger.info(f"   ... and {len(all_columns) - 10} more columns")
            return
        
        # Generate property mappings
        prop_to_col, cypher_conversions = generate_property_mappings(all_columns)
        
        # Build dynamic property assignment string
        property_assignments = []
        for prop_name, column in prop_to_col.items():
            conversion = cypher_conversions[prop_name].replace(f'item.{column}', f'item.{column}')
            property_assignments.append(f"{prop_name}: {conversion}")
        
        # Process in batches
        for i in range(0, len(pets_data), self.batch_size):
            batch = pets_data[i:i + self.batch_size]
            logger.info(f"📦 Processing pet batch {i//self.batch_size + 1} ({len(batch)} pets)")
            
            # Create dynamic batch insert query
            query = f"""
            UNWIND $pets AS item
            CREATE (p:Pet {{
                {',\n                '.join(property_assignments)}
            }})
            """
            
            try:
                # Process data for Neo4j
                processed_batch = self.process_data_for_neo4j(batch, all_columns)
                
                _, summary = await self.connection.execute_write_query(
                    query, {"pets": processed_batch}
                )
                batch_created = summary.get('nodes_created', 0)
                self.stats['pets_created'] += batch_created
                logger.info(f"✅ Created {batch_created} pet nodes in batch")
                
            except Exception as e:
                logger.error(f"❌ Failed to create pet batch: {e}")
                logger.error(f"Query was: {query[:500]}...")
                raise
        
        logger.info(f"🐕 Successfully created {self.stats['pets_created']} pet nodes")
    
    async def create_relationships(self):
        """Create :OWNS_PET relationships between customers and pets."""
        logger.info("🔗 Creating relationships between customers and pets...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would create customer-pet relationships")
            return
        
        # Use sanitized property names for the relationship query
        customer_id_prop = sanitize_property_name('CUSTOMER_ID')
        pet_customer_id_prop = sanitize_property_name('PETPROFILE_CUSTOMER_ID')
        
        query = f"""
        MATCH (c:Customer), (p:Pet)
        WHERE c.{customer_id_prop} = p.{pet_customer_id_prop}
        CREATE (c)-[:OWNS_PET]->(p)
        """
        
        try:
            _, summary = await self.connection.execute_write_query(query)
            relationships_created = summary.get('relationships_created', 0)
            self.stats['relationships_created'] = relationships_created
            logger.info(f"✅ Created {relationships_created} :OWNS_PET relationships")
            
        except Exception as e:
            logger.error(f"❌ Failed to create relationships: {e}")
            raise
    
    async def create_indexes(self):
        """Create database indexes for better query performance."""
        logger.info("📈 Creating database indexes...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN: Would create database indexes")
            return
        
        # Use sanitized property names for indexes
        customer_id_prop = sanitize_property_name('CUSTOMER_ID')
        pet_id_prop = sanitize_property_name('PETPROFILE_ID')
        pet_customer_id_prop = sanitize_property_name('PETPROFILE_CUSTOMER_ID')
        
        indexes = [
            f"CREATE INDEX customer_id_index IF NOT EXISTS FOR (c:Customer) ON (c.{customer_id_prop})",
            f"CREATE INDEX pet_id_index IF NOT EXISTS FOR (p:Pet) ON (p.{pet_id_prop})",
            f"CREATE INDEX pet_customer_id_index IF NOT EXISTS FOR (p:Pet) ON (p.{pet_customer_id_prop})",
        ]
        
        for index_query in indexes:
            try:
                await self.connection.execute_write_query(index_query)
                prop_name = index_query.split('ON (')[1].split(')')[0]
                logger.info(f"✅ Created index on: {prop_name}")
            except Exception as e:
                logger.warning(f"⚠️  Index creation failed (may already exist): {e}")
    
    async def get_final_stats(self):
        """Get final database statistics."""
        logger.info("📊 Getting final database statistics...")
        
        try:
            db_info = await self.connection.get_database_info()
            logger.info("🎯 Final Database Statistics:")
            logger.info(f"   📝 Node Labels: {db_info.get('node_labels', [])}")
            logger.info(f"   📈 Node Counts: {db_info.get('node_counts', {})}")
            logger.info(f"   🔗 Relationship Types: {db_info.get('relationship_types', [])}")
            logger.info(f"   📊 Relationship Counts: {db_info.get('relationship_counts', {})}")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not retrieve final statistics: {e}")
    
    def print_summary(self):
        """Print operation summary."""
        logger.info("=" * 60)
        logger.info("📋 OPERATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"🗑️  Nodes deleted: {self.stats['nodes_deleted']}")
        logger.info(f"👥 Customers created: {self.stats['customers_created']}")
        logger.info(f"🐕 Pets created: {self.stats['pets_created']}")
        logger.info(f"🔗 Relationships created: {self.stats['relationships_created']}")
        logger.info("=" * 60)


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Populate Neo4j graph database with customer and pet data')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing records (reduced for large number of properties)')
    args = parser.parse_args()
    
    logger.info("🚀 Starting Graph Database Population (ALL COLUMNS)")
    logger.info("=" * 60)
    
    # Initialize populator
    populator = GraphPopulator(dry_run=args.dry_run, batch_size=args.batch_size)
    
    try:
        # Connect to database
        if not await populator.connect():
            return 1
        
        # Load CSV data
        customers_data = populator.load_csv_data("data/graph/customers.csv")
        pets_data = populator.load_csv_data("data/graph/pet_profile.csv")
        
        # Clear existing data
        await populator.clear_database()
        
        # Create nodes
        await populator.create_customers(customers_data)
        await populator.create_pets(pets_data)
        
        # Create relationships
        await populator.create_relationships()
        
        # Create indexes
        await populator.create_indexes()
        
        # Get final statistics
        await populator.get_final_stats()
        
        # Print summary
        populator.print_summary()
        
        logger.info("🎉 Graph database population completed successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"💥 Population failed: {e}")
        return 1
        
    finally:
        await populator.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 