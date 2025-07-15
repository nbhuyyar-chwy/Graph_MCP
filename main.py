#!/usr/bin/env python3
"""
Main entry point for the Neo4j MCP Server.

This modular implementation provides a clean, maintainable structure
for interacting with Neo4j databases through the Model Context Protocol.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.server import create_server


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def check_environment():
    """Check if environment is properly configured."""
    if not os.getenv("NEO4J_PASSWORD"):
        print("❌ Missing NEO4J_PASSWORD environment variable")
        print("Please set your Neo4j password:")
        print("export NEO4J_PASSWORD=your_password")
        print("or create a .env file with: NEO4J_PASSWORD=your_password")
        return False
    return True


async def main():
    """Main entry point."""
    print("🚀 Starting Modular Neo4j MCP Server...")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment configured")
    print("🔌 Neo4j URI: neo4j+s://b2f690c8.databases.neo4j.io")
    print("📊 Database: neo4j")
    print("🆔 Instance ID: b2f690c8")
    print()
    
    # Create and run server
    try:
        server = create_server()
        
        print("📡 Starting MCP server on stdio...")
        print("🛠️  Available tools:")
        for tool_name in server.tools.keys():
            print(f"   - {tool_name}")
        print()
        print("Ready to accept MCP tool calls!")
        print("=" * 50)
        
        await server.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        logging.exception("Server error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 