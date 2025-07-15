#!/bin/bash

# Neo4j MCP Server Setup Script

echo "🚀 Setting up Neo4j MCP Server..."
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Make scripts executable
chmod +x neo4j_mcp_server.py
chmod +x run_server.py
chmod +x test_queries.py

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env template..."
    cat > .env << EOL
# Neo4j Database Configuration
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password_here
EOL
    echo "⚠️  Please edit .env file and add your Neo4j password"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Neo4j credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python run_server.py"
echo ""
echo "Available scripts:"
echo "  - run_server.py      : Start the MCP server"
echo "  - test_queries.py    : View sample queries"
echo "  - neo4j_mcp_server.py: Main server file"
echo ""
echo "Documentation: See README.md for full usage guide" 