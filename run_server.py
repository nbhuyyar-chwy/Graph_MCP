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

def load_environment():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Environment variables loaded from .env file")
        return True
    except ImportError:
        print("⚠️  python-dotenv not found, using system environment variables")
        return True
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def check_environment():
    """Check if environment is properly configured"""
    # First load environment variables from .env
    if not load_environment():
        return False
    
    # Check for required environment variables
    required_vars = [
        "NEO4J_URI",
        "NEO4J_USERNAME", 
        "NEO4J_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these environment variables in your .env file:")
        print("NEO4J_URI=your_neo4j_uri")
        print("NEO4J_USERNAME=your_username")
        print("NEO4J_PASSWORD=your_password")
        print("NEO4J_DATABASE=neo4j")
        return False
    
    # Show loaded configuration (masked)
    print("🔧 Configuration loaded:")
    print(f"   NEO4J_URI: {os.getenv('NEO4J_URI')}")
    print(f"   NEO4J_USERNAME: {os.getenv('NEO4J_USERNAME')}")
    print(f"   NEO4J_PASSWORD: {'*' * len(os.getenv('NEO4J_PASSWORD', ''))}")
    print(f"   NEO4J_DATABASE: {os.getenv('NEO4J_DATABASE', 'neo4j')}")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ["mcp", "neo4j", "dotenv"]
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
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
    
    # Check environment (this will load .env file)
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment checks passed")
    print("✅ Dependencies verified")
    print("\n🔌 Connecting to Neo4j MCP Server...")
    
    # Extract instance ID from URI for display
    neo4j_uri = os.getenv('NEO4J_URI', '')
    if 'databases.neo4j.io' in neo4j_uri:
        instance_id = neo4j_uri.split('://')[1].split('.')[0]
        print(f"Instance ID: {instance_id}")
    
    print(f"URI: {neo4j_uri}")
    print("\n📡 Server starting on stdio...")
    print("🛠️  Available tools include:")
    print("   • get_user_summary - User behavioral analysis")
    print("   • get_user_tags - Semantic behavior labels")
    print("   • get_session_summary - Session insights")
    print("   • Plus 13 other Neo4j tools")
    print("\nReady to accept MCP tool calls!")
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 