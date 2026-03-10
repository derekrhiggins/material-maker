# Material Maker (MCP Fork)

Fork of [Material Maker](https://github.com/RodZill4/material-maker) with an integrated MCP server for AI-driven procedural texture creation.

## Architecture

```
[AI Client] <--MCP/stdio--> [Python MCP Server]  <--TCP:9002--> [GDScript Addon]
                              mcp_server/                         addons/material_maker_mcp/
```

Both components live in this repo. The GDScript addon is an autoload registered in `project.godot` — it starts automatically with MM.

## Project Structure

```
addons/material_maker_mcp/      # GDScript TCP server + command handlers (autoload)
  addon.gd                      # TCP server, JSON dispatch, command routing
  commands/                     # Command handler modules
    graph.gd                    # create_node, delete_node, connect/disconnect, get_graph_info
    parameters.gd               # get/set node parameters
    export.gd                   # export_material, export_for_engine, list_export_profiles
    scene.gd                    # get_scene_info, save/load/new project
    preview.gd                  # get_preview_image, get_3d_preview
    utils.gd                    # execute_mm_script (opt-in)
    validation.gd               # shared path/node_id validation

mcp_server/                     # Python MCP server (pip/uvx installable)
  src/material_maker_mcp/
    server.py                   # FastMCP server, tool definitions, entry point
    connection.py               # Async TCP client with retry/backoff
  tests/                        # Unit tests (pytest)
  pyproject.toml                # Python package config
  TOOLS.md                      # Full tool reference
  todo.md                       # Implementation checklist
  spec.md                       # Original PRD

addons/material_maker/          # Upstream Material Maker engine (do not modify)
material_maker/                 # Upstream Material Maker UI (do not modify)
```

## Key Commands

```bash
# Run MCP server (from mcp_server/)
cd mcp_server && pip install -e ".[dev]" && python -m material_maker_mcp.server

# Run tests
cd mcp_server && pytest tests/ -v

# Lint
cd mcp_server && ruff check src/ tests/ && mypy src/ --ignore-missing-imports
```

## MCP Tool Categories

| Category | Tools |
|---|---|
| Graph | `create_node`, `delete_node`, `connect_nodes`, `disconnect_nodes`, `get_graph_info`, `list_available_nodes` |
| Parameters | `get_node_parameters`, `set_node_parameter`, `set_multiple_parameters` |
| Export | `export_material`, `export_for_engine`, `list_export_profiles` |
| Preview | `get_preview_image`, `get_3d_preview` |
| Scene | `get_scene_info`, `save_project`, `load_project`, `new_project` |
| Utility | `execute_mm_script` (disabled by default), `ping` |

## Key Design Decisions

- **Port 9002** (9001 is Blender MCP). Override: `MM_MCP_PORT` (GDScript), `MM_PORT` (Python)
- **Host** defaults to `localhost`. Override: `MM_HOST` (Python, needed for WSL2)
- Addon binds to `0.0.0.0` for WSL2 cross-stack connectivity
- TCP poll throttled to 50ms intervals to avoid rendering overhead
- `execute_mm_script` disabled by default — opt in via `MM_MCP_ALLOW_SCRIPT=1`
- All GDScript errors caught at dispatch level and returned as JSON — never crash MM

## Code Conventions

- **Python**: Type hints, `from __future__ import annotations`, async/await, modern union syntax
- **GDScript**: Godot 4 typed syntax, `##` doc comments, shared validation via `validation.gd`
- **Protocol**: Newline-delimited JSON over TCP. Commands: `{"type": "...", "params": {...}}`. Responses: `{"status": "ok"|"error", ...}`

## Important Notes

- The GDScript addon extends `Node` (MM autoload convention), NOT Godot's `EditorPlugin`
- MM has no external plugin system — this fork is required for MCP support
- Export operations can be slow (30s+ for 4K) — the 30s TCP timeout may need extending
- `mm_globals.main_window` is polled for up to 600 frames at startup (autoload starts before main window)
