"""
Neo4j MCP Tools - Connect agents to Neo4j databases with powerful query capabilities.

This package provides a Model Context Protocol (MCP) server for Neo4j databases,
allowing AI agents to interact with graph databases through standardized tools.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .server import Neo4jMCPServer, create_server
from .database import Neo4jConnection, QueryBuilder
from .models import Pet, User, Vet, Product, PetHealthSummary, MedicalHistory

__all__ = [
    "Neo4jMCPServer",
    "create_server", 
    "Neo4jConnection",
    "QueryBuilder",
    "Pet",
    "User", 
    "Vet",
    "Product",
    "PetHealthSummary",
    "MedicalHistory",
] 