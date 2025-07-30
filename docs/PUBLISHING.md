# Publishing Neo4j MCP Tools

This guide explains how to publish the `neo4j-mcp-tools` package so that users can install it with `pip install neo4j-mcp-tools` and agents can reference it as `@neo4j-tools`.

## Prerequisites

1. **PyPI Account**: Create accounts on [TestPyPI](https://test.pypi.org/) and [PyPI](https://pypi.org/)
2. **API Tokens**: Generate API tokens for secure uploading
3. **Build Tools**: Install required build tools

```bash
pip install build twine
```

## Building the Package

### 1. Update Version (if needed)

Edit `pyproject.toml` and update the version:
```toml
version = "1.0.1"  # Increment as needed
```

Also update `src/__init__.py`:
```python
__version__ = "1.0.1"
```

### 2. Build the Distribution

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build the package
python -m build
```

This creates:
- `dist/neo4j_mcp_tools-1.0.0-py3-none-any.whl` (wheel)
- `dist/neo4j-mcp-tools-1.0.0.tar.gz` (source distribution)

### 3. Test the Build

```bash
# Install locally to test
pip install dist/neo4j_mcp_tools-1.0.0-py3-none-any.whl

# Test the CLI command
neo4j-mcp-server --version
```

## Publishing

### 1. Test on TestPyPI First

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Install from TestPyPI to test
pip install --index-url https://test.pypi.org/simple/ neo4j-mcp-tools
```

### 2. Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
```

### 3. Verify Installation

```bash
# Install from PyPI
pip install neo4j-mcp-tools

# Test CLI
neo4j-mcp-server --help
```

## Making it Available to Agents

### 1. Update Package Name in Configuration

Users will add this to their MCP client configuration:

```json
{
  "mcpServers": {
    "neo4j-tools": {
      "command": "neo4j-mcp-server",
      "args": [],
      "env": {
        "NEO4J_URI": "neo4j+s://your-instance.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your_password_here",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

### 2. Usage by Agents

After installation, agents can reference the tools like:

```python
# Agent can use these tools:
await mcp_client.call_tool("neo4j-tools", "run_cypher_query", {
    "query": "MATCH (p:Pet) RETURN count(p)"
})

await mcp_client.call_tool("neo4j-tools", "search_pets_by_criteria", {
    "species": "dog",
    "limit": 10
})
```

## Distribution Checklist

- [ ] Update version numbers
- [ ] Test build locally
- [ ] Upload to TestPyPI
- [ ] Test installation from TestPyPI
- [ ] Upload to PyPI
- [ ] Test installation from PyPI
- [ ] Update documentation
- [ ] Create GitHub release
- [ ] Announce to users

## Configuration for Different Environments

Users can create environment-specific configurations:

### Production
```json
{
  "mcpServers": {
    "neo4j-production": {
      "command": "neo4j-mcp-server",
      "env": {
        "NEO4J_URI": "neo4j+s://production-instance.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "prod_password"
      }
    }
  }
}
```

### Development
```json
{
  "mcpServers": {
    "neo4j-dev": {
      "command": "neo4j-mcp-server",
      "args": ["--log-level", "DEBUG"],
      "env": {
        "NEO4J_URI": "neo4j+s://dev-instance.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j", 
        "NEO4J_PASSWORD": "dev_password"
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Package not found**: Ensure correct package name `neo4j-mcp-tools`
2. **Command not found**: Check entry points in `pyproject.toml`
3. **Import errors**: Verify package structure and dependencies
4. **Connection issues**: Check environment variables and Neo4j credentials

### Support

- GitHub Issues: https://github.com/nbhuyyar-chwy/Graph_MCP/issues
- Documentation: README.md
- Examples: examples/mcp_tools_demo.py 