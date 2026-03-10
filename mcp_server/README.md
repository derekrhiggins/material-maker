# Material Maker MCP Server

**Python MCP server for AI-driven procedural texture creation in Material Maker.**

This is the Python side of the Material Maker MCP integration. It bridges MCP clients (Claude Desktop, Claude Code, Cursor, etc.) to Material Maker's built-in GDScript TCP addon via the Model Context Protocol.

## Architecture

```
[AI Client] <--MCP/stdio--> [Python MCP Server] <--TCP:9002--> [MM GDScript Addon]
                              mcp_server/                        addons/material_maker_mcp/
```

Both components live in this repository. The GDScript addon starts automatically as an autoload when Material Maker launches. The Python server connects to it over TCP.

## Installation

```bash
# From this directory
pip install -e ".[dev]"

# Or run directly
python -m material_maker_mcp.server

# Or via uvx (once published to PyPI)
uvx material-maker-mcp
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "material-maker": {
      "command": "uvx",
      "args": ["material-maker-mcp"],
      "env": {
        "MM_PORT": "9002"
      }
    }
  }
}
```

### WSL2 users

Find your Windows host IP:
```bash
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
```

Then use it in the config (replace the IP with yours):
```json
{
  "mcpServers": {
    "material-maker": {
      "command": "wsl",
      "args": ["-e", "bash", "-lc", "MM_HOST=172.28.224.1 python3 -m material_maker_mcp.server"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MM_HOST` | `localhost` | Host where Material Maker is running |
| `MM_PORT` | `9002` | TCP port for the connection |
| `MM_MCP_ALLOW_SCRIPT` | (unset) | Set to `1` to enable `execute_mm_script` |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format --check src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

See [TOOLS.md](TOOLS.md) for the full tool reference.
