#!/usr/bin/env python3
"""
Startup script for Neo4j MCP Server

This script provides an easy way to start the Neo4j MCP server with
proper error handling and configuration validation.
"""

import os
import sys
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def check_environment():
    """Check if environment is properly configured"""
    missing_vars = []
    
    # Check for required environment variables
    if not os.getenv("NEO4J_PASSWORD"):
        missing_vars.append("NEO4J_PASSWORD")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables before running the server.")
        print("You can create a .env file with:")
        print("NEO4J_USERNAME=your_username")
        print("NEO4J_PASSWORD=your_password")
        return False
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ["mcp", "neo4j", "dotenv"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install required packages:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Starting Neo4j MCP Server...")
    print("=" * 50)
    
    # Setup logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment checks passed")
    print("✅ Dependencies verified")
    print("\n🔌 Connecting to Neo4j MCP Server...")
    print("Instance ID: b2f690c8")
    print("URI: neo4j+s://b2f690c8.databases.neo4j.io")
    print("\n📡 Server starting on stdio...")
    print("Ready to accept MCP tool calls!")
    print("=" * 50)
    
    # Import and run the server
    try:
        from main import main as run_server
        import asyncio
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 