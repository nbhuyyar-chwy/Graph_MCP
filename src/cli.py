#!/usr/bin/env python3
"""
Command Line Interface for Neo4j MCP Server
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from .server import Neo4jMCPServer
from config import Neo4jConfig


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def create_env_file_if_missing():
    """Create a sample .env file if it doesn't exist."""
    env_file = Path(".env")
    if not env_file.exists():
        sample_content = """# Neo4j MCP Server Configuration
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_DATABASE=neo4j
AURA_INSTANCEID=your_instance_id
"""
        env_file.write_text(sample_content)
        print(f"📝 Created sample .env file at {env_file.absolute()}")
        print("🔧 Please edit it with your Neo4j credentials")
        return False
    return True


async def run_server(
    host: str = "localhost", 
    port: int = 8000,
    log_level: str = "INFO"
):
    """Run the Neo4j MCP server."""
    setup_logging(log_level)
    
    print("🚀 Neo4j MCP Server")
    print("=" * 40)
    
    # Check environment
    if not create_env_file_if_missing():
        return 1
    
    if not Neo4jConfig.is_configured():
        print("❌ Neo4j configuration incomplete!")
        print("Please set NEO4J_PASSWORD in your .env file")
        return 1
    
    # Create and start server
    server = Neo4jMCPServer()
    
    try:
        print(f"🔗 Neo4j URI: {Neo4jConfig.URI}")
        print(f"📊 Database: {Neo4jConfig.DATABASE}")
        print(f"🆔 Instance ID: {Neo4jConfig.INSTANCE_ID}")
        print(f"🌐 Server will start on {host}:{port}")
        print("📡 Ready to accept MCP tool calls!")
        print("=" * 40)
        
        # Run the server
        await server.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    finally:
        await server.cleanup()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Neo4j MCP Server - Connect agents to Neo4j databases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  neo4j-mcp-server                    # Run with default settings
  neo4j-mcp-server --port 8001        # Run on custom port
  neo4j-mcp-server --log-level DEBUG  # Enable debug logging
  
For more information, visit: https://github.com/nbhuyyar-chwy/Graph_MCP
        """
    )
    
    parser.add_argument(
        "--host", 
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to run the server on (default: 8000)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="neo4j-mcp-tools 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Run the server
    try:
        exit_code = asyncio.run(run_server(
            host=args.host,
            port=args.port, 
            log_level=args.log_level
        ))
        sys.exit(exit_code or 0)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 