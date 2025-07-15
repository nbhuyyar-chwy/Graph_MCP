"""
Configuration settings for Neo4j MCP Server
"""

import os
from typing import Optional

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

# Pet Care Database Schema Documentation
SCHEMA_INFO = {
    "nodes": {
        "User": {
            "description": "Pet owner",
            "properties": ["id", "username"]
        },
        "Pet": {
            "description": "Individual pet",
            "properties": ["name", "species", "breed", "birth_date", "weight_kg", "gender", "color", "microchip_id"]
        },
        "VetVisit": {
            "description": "Medical visit for pet", 
            "properties": ["date", "reason", "diagnosis", "treatment", "follow_up_date", "notes"]
        },
        "Vet": {
            "description": "Veterinarian",
            "properties": ["name", "clinic"]
        },
        "Medication": {
            "description": "Prescribed treatment",
            "properties": ["medication_name", "dosage", "frequency", "start_date", "duration_days", "reason", "notes"]
        },
        "ProductInteraction": {
            "description": "Interaction with a product",
            "properties": ["date", "interaction_type", "quantity", "feedback", "rating", "notes"]
        },
        "Product": {
            "description": "Product item itself",
            "properties": ["product_name", "brand", "category", "attributes"]
        }
    },
    "relationships": {
        "OWNS": "User → Pet: A user owns one or more pets",
        "HAS_VISIT": "Pet → VetVisit: A pet has one or more vet visits",
        "WITH_VET": "VetVisit → Vet: Each vet visit is handled by a vet",
        "HAS_MEDICATION": "Pet → Medication: A pet is prescribed one or more medications", 
        "INTERACTED_WITH": "Pet → ProductInteraction: A pet interacts with products",
        "ABOUT_PRODUCT": "ProductInteraction → Product: Product interaction details"
    }
} 