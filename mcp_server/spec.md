# Material Maker MCP — Product Requirements Document & Implementation Todo
**Version:** 1.0 — Initial Draft  
**Date:** March 2026  
**License:** MIT (matching Material Maker)  
**Status:** Pre-development

---

## 1. Overview & Vision

Material Maker MCP is an open-source bridge that connects Claude (and any MCP-compatible AI client) directly to Material Maker — the free, MIT-licensed procedural texture authoring tool built on Godot Engine. It is the first MCP server for Material Maker and enables AI-driven texture and material graph creation through natural language.

Inspired by the Blender MCP project (github.com/ahujasid/blender-mcp), this project mirrors the same dual-component pattern: a plugin that runs inside Material Maker exposing a TCP socket server, and a Python MCP server that bridges that socket to the MCP protocol.

### 1.1 Problem Statement

Material Maker is a powerful tool but requires deep knowledge of procedural node graphs and GLSL shaders. AI assistants currently have no way to interact with Material Maker programmatically — there is no API, no plugin system for external control, and no MCP server. Artists and developers must manually wire every node, set every parameter, and export every texture by hand.

### 1.2 Solution

By embedding a lightweight TCP socket server inside Material Maker (as a GDScript plugin) and pairing it with a Python MCP server, Claude can understand a user's natural language description and directly manipulate Material Maker: adding nodes, connecting them, tweaking parameters, and exporting finished textures — all without the user needing to know the node graph in detail.

### 1.3 Reference: How Blender MCP Works (Pattern to Mirror)

| Component | Description |
|---|---|
| Blender Addon | `addon.py` installed in Blender creates a TCP socket server on port 9001. Receives JSON commands, executes `bpy` Python, returns JSON results. |
| Python MCP Server | `server.py` implements the MCP protocol over stdio. Connects to Blender's socket, translates MCP tool calls into JSON commands, returns results to the AI client. |
| Transport | JSON over TCP sockets. Commands: `{ type, params }`. Responses: `{ status: ok|error, result }`. |
| Key Tool | `execute_blender_code` — runs arbitrary Python (bpy) in Blender. Everything else builds on top of this. |

---

## 2. System Architecture

### 2.1 Component Diagram

```
[Claude / AI Client]  <--(MCP/stdio)-->  [Python MCP Server]  <--(TCP :9002)-->  [Material Maker + GDScript Plugin]
  Claude Desktop                           server.py                                 addon.gd
  Cursor, Cline, etc.                      connection.py                             TCPServer on port 9002
```

### 2.2 Repository Structure

```
material-maker-mcp/
├── addon/                          # Material Maker GDScript plugin
│   ├── plugin.cfg                  # MM plugin manifest
│   ├── addon.gd                    # Main plugin: TCP server + command dispatcher
│   └── commands/
│       ├── graph.gd                # Node create/delete/connect commands
│       ├── parameters.gd           # Parameter get/set commands
│       ├── export.gd               # Export texture/material commands
│       ├── scene.gd                # Scene info, save, load commands
│       └── utils.gd                # execute_mm_script escape hatch
├── src/
│   └── material_maker_mcp/
│       ├── __init__.py
│       ├── server.py               # MCP server entry point
│       ├── connection.py           # Async TCP client to MM addon
│       └── tools/
│           ├── graph_tools.py      # Tool schemas: create_node, connect_nodes, etc.
│           ├── parameter_tools.py  # Tool schemas: get/set parameters
│           ├── export_tools.py     # Tool schemas: export_material, export_for_engine
│           └── scene_tools.py      # Tool schemas: get_scene_info, save/load project
├── tests/
│   ├── test_connection.py
│   ├── test_tools.py
│   └── integration/
├── pyproject.toml                  # uvx-installable Python package config
├── README.md
├── TOOLS.md
└── CONTRIBUTING.md
```

### 2.3 Communication Protocol

JSON messages over TCP sockets on port 9002 (configurable). Each message is newline-delimited JSON.

| Field | Format |
|---|---|
| Command | `{ "type": "command_name", "params": { ...args } }` |
| Success response | `{ "status": "ok", "result": { ...data } }` |
| Error response | `{ "status": "error", "message": "human-readable error" }` |
| Default port | `9002` (avoids conflict with Blender MCP on 9001) |
| Encoding | UTF-8 JSON, newline-delimited (one JSON object per line) |
| Timeout | 30 seconds per command (configurable) |

---

## 3. MCP Tools Specification

These are the tools Claude will call. Each maps to one or more GDScript commands sent over TCP.

### 3.1 Graph / Node Tools

**`create_node`**
- Purpose: Create a new node in the current material graph
- Params: `node_type: string` (e.g. `"noise.fbm"`, `"filter.normal_map"`), `position_x: float`, `position_y: float`, `node_name?: string`
- Returns: `{ node_id, node_type, position: {x, y} }`
- MM impl: `mm_graph.create_node(type, position)`

**`delete_node`**
- Purpose: Delete a node by its ID
- Params: `node_id: string`
- Returns: `{ deleted: true, node_id }`
- MM impl: `mm_graph.remove_node(node_id)`

**`connect_nodes`**
- Purpose: Connect the output port of one node to the input port of another
- Params: `from_node_id: string`, `from_port: int`, `to_node_id: string`, `to_port: int`
- Returns: `{ connected: true, from: ..., to: ... }`
- MM impl: `mm_graph.connect_node(from, from_port, to, to_port)`

**`disconnect_nodes`**
- Purpose: Remove a connection between two nodes
- Params: `from_node_id: string`, `from_port: int`, `to_node_id: string`, `to_port: int`
- Returns: `{ disconnected: true }`
- MM impl: `mm_graph.disconnect_node(...)`

**`get_graph_info`**
- Purpose: Get full description of the current material graph (all nodes, connections, parameters)
- Params: none
- Returns: `{ nodes: [...], connections: [...], material_type: string }`
- MM impl: Iterate `mm_graph.get_node_list()`, serialize each node's type, position, params, and ports

**`list_available_nodes`**
- Purpose: Return all node types available in this installation of Material Maker
- Params: `category?: string` (optional filter)
- Returns: `{ categories: { category_name: [node_type_string, ...] } }`
- MM impl: Read Material Maker's node registry / library

### 3.2 Parameter Tools

**`get_node_parameters`**
- Purpose: Get all current parameter values for a specific node
- Params: `node_id: string`
- Returns: `{ node_id, parameters: { param_name: { value, type, min?, max?, options? } } }`
- MM impl: Serialize node's exported properties

**`set_node_parameter`**
- Purpose: Set a single parameter on a node
- Params: `node_id: string`, `parameter: string`, `value: any`
- Returns: `{ node_id, parameter, old_value, new_value }`
- MM impl: `node.set(parameter, value)` then trigger shader recompile

**`set_multiple_parameters`**
- Purpose: Set multiple parameters on one or more nodes in a single call
- Params: `updates: [ { node_id, parameter, value }, ... ]`
- Returns: `{ updated: int, results: [...] }`
- MM impl: Batch the above; defer shader recompile until end

### 3.3 Export Tools

**`export_material`**
- Purpose: Export the current material as texture maps to disk
- Params: `output_path: string`, `format: "png"|"exr"|"jpg"`, `resolution: int` (default 1024), `maps?: ["albedo","roughness","metalness","normal","height","ao"]` (default: all)
- Returns: `{ exported_files: [ { map, path, resolution } ] }`
- MM impl: Trigger Material Maker's export pipeline for each map type

**`export_for_engine`**
- Purpose: Export material in game-engine-ready format
- Params: `output_path: string`, `engine: "godot"|"unity"|"unreal"`, `resolution: int`
- Returns: `{ engine, exported_files: [...], script_path?: string }`
- MM impl: Use MM's built-in engine export targets. For Unreal 5, also generate the Python setup script.

### 3.4 Scene / Project Tools

**`get_scene_info`**
- Purpose: Get metadata about the current open project
- Params: none
- Returns: `{ file_path, material_type, node_count, has_unsaved_changes, mm_version }`
- MM impl: Read global state from `mm_graph` and the editor

**`save_project`**
- Purpose: Save the current project to disk
- Params: `path?: string` (omit to save to current path)
- Returns: `{ saved: true, path }`
- MM impl: `editor.save_current_project(path)`

**`load_project`**
- Purpose: Open a `.mmg` project file
- Params: `path: string`
- Returns: `{ loaded: true, path, node_count }`
- MM impl: `editor.load_project(path)`

**`new_project`**
- Purpose: Create a new empty material project
- Params: `material_type: "pbr"|"dynamic_pbr"|"raymarching"|"unlit"` (default: `"pbr"`)
- Returns: `{ created: true, material_type }`
- MM impl: `editor.new_project(material_type)`

**`execute_mm_script`** *(disabled by default)*
- Purpose: Execute arbitrary GDScript inside Material Maker (power-user escape hatch, mirrors Blender MCP's `execute_blender_code`)
- Params: `script: string` (GDScript code), `context?: string`
- Returns: `{ result: any, output: string }`
- Notes: DANGEROUS — disabled by default via config flag. Sanitize carefully. Do not expose in production.

---

## 4. Material Maker Plugin (GDScript)

### 4.1 Installation

Copy the `addon/` folder into the Material Maker user addons directory. Enable via MM's Plugin Manager. Identical to how existing community plugins work.

### 4.2 Plugin Lifecycle

> **Note:** Material Maker has its own plugin system separate from Godot's `EditorPlugin`. MM plugins extend `Node` (or `MMGenBase` for generator plugins) and are loaded via MM's Plugin Manager. The addon must use MM's plugin conventions, not Godot editor plugin conventions.

1. Plugin registers itself with Material Maker on enable via `plugin.cfg`.
2. `TCPServer` starts listening on port 9002 (configurable via env var `MM_MCP_PORT`).
3. Status indicator appears in the MM UI sidebar: "MCP Server: Running on :9002".
4. On each connection, a new `StreamPeerTCP` is accepted.
5. Incoming newline-delimited JSON commands are dispatched to handler functions by `type` field.
6. Responses are serialized back as JSON and written to the stream.
7. On MM shutdown or plugin disable, the TCP server closes cleanly.
8. On startup, detect Godot engine version (3.x vs 4.x) and select the appropriate TCP/networking API paths.

### 4.3 Key GDScript APIs

| API | Usage |
|---|---|
| Node graph access | `get_tree().get_root().find_node('GraphEdit')` or via `mm_graph` singleton |
| Node creation | `graph.create_node(type, position)` — returns node object with unique ID |
| Node connections | `graph.connect_node(from, from_port, to, to_port)` — Godot GraphEdit API |
| Node parameters | `node.get_parameter_defs()` and `node.set_parameter(name, value)` |
| Export pipeline | `mm_loader.export_textures(path, format, size)` |
| Project I/O | `mm_loader.save_json(path)` / `mm_loader.load_json(path)` |
| TCP server | `TCPServer`, `StreamPeerTCP` — standard Godot networking classes |

### 4.4 Error Handling

- Wrap all node operations in GDScript error code checks.
- Return `{ "status": "error", "message": "..." }` for any failure.
- Log all errors to MM's built-in output panel.
- Never crash MM — all exceptions must be caught at the dispatch level.

---

## 5. Python MCP Server

### 5.1 Dependencies

- `mcp` — Anthropic's official Python MCP SDK
- `asyncio` — standard library, async TCP socket client
- `json` — standard library, message serialization
- Python 3.10+ required

### 5.2 Packaging

uvx-installable via PyPI. Users run:

```bash
uvx material-maker-mcp
```

### 5.3 Claude Desktop Config

```json
{
  "mcpServers": {
    "material-maker": {
      "command": "uvx",
      "args": ["material-maker-mcp"],
      "env": { "MM_PORT": "9002" }
    }
  }
}
```

---

## 6. Requirements

### 6.1 Functional Requirements — MVP

| ID | Requirement |
|---|---|
| FR-01 | Plugin installs and enables without crashing Material Maker |
| FR-02 | TCP server starts on configurable port, status visible in MM UI |
| FR-03 | `create_node` works for all built-in MM node categories |
| FR-04 | `connect_nodes` / `disconnect_nodes` work correctly |
| FR-05 | `get_graph_info` returns accurate graph state |
| FR-06 | `set_node_parameter` / `get_node_parameters` work for all parameter types |
| FR-07 | `export_material` exports PNG texture maps to a specified directory |
| FR-08 | `save_project` and `load_project` work for `.mmg` files |
| FR-09 | Python MCP server connects, runs tools, returns results to Claude |
| FR-10 | Package is uvx-installable from PyPI |

### 6.2 Functional Requirements — v1.1

| ID | Requirement |
|---|---|
| FR-11 | `export_for_engine` with Godot, Unity, Unreal targets |
| FR-12 | `list_available_nodes` returns full node registry |
| FR-13 | `set_multiple_parameters` batched call |
| FR-14 | `execute_mm_script` escape hatch (opt-in) |
| FR-15 | Auto-arrange graph layout helper |
| FR-16 | `get_preview_image` — return base64 PNG of current node preview |
| FR-17 | Undo support — wrap commands in MM's undo history |

### 6.3 Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 Safety | Plugin must never crash or corrupt MM projects. All errors caught and returned gracefully. |
| NFR-02 Performance | Command round-trip < 500ms for non-export operations. |
| NFR-03 Compatibility | Support Material Maker 1.3+ (Godot 3) and 1.4+ (Godot 4). Detect version at runtime. |
| NFR-04 Platform | Windows, macOS, Linux — same as Material Maker itself. |
| NFR-05 Security | `execute_mm_script` disabled by default. No arbitrary filesystem access beyond user-specified paths. |
| NFR-06 Docs | README covers install, setup, all tools with examples. Match Blender MCP documentation quality. |
| NFR-07 Tests | Core tool functions covered by integration tests against a headless MM instance. |

---

## 7. Implementation Todo List

See **[todo.md](todo.md)** for the full phased implementation checklist (60 items across 7 phases).

---

## 8. Example Claude Prompts (Acceptance Criteria)

These prompts should work correctly once the project is complete. Use as validation tests.

1. *"Create a rust metal material in Material Maker with a base color, normal map from noise, and high roughness. Export it as PNG maps."*
2. *"Show me what nodes are currently in my Material Maker graph and what parameters each one has."*
3. *"Add a FBM noise node and connect it to the height input of the normal map node. Set the scale to 4.0 and octaves to 6."*
4. *"Export the current material for Unreal Engine 5 at 2048 resolution to ~/Materials/rust/."*
5. *"Save my current project as crater_rock.mmg and start a new dynamic PBR material."*
6. *"What node types are available for generating patterns in Material Maker?"*

---

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Material Maker API instability | MM is actively developed and internal GDScript APIs may change. Version-detect at startup, maintain compatibility notes, pin to stable MM releases. |
| Godot 3 vs Godot 4 API differences | MM 1.3 uses Godot 3; MM 1.4+ uses Godot 4. `TCPServer` API differs. Write separate addon code paths per Godot major version, detect at runtime. |
| Long export times | Exporting 4K textures may take 30+ seconds, triggering MCP timeout. Make timeout configurable; implement async export with polling. |
| No official MM plugin API | MM lacks a stable plugin extension API. Follow same pattern as existing community plugins; contribute upstream API hooks if needed. |
| Security of execute_mm_script | Arbitrary code execution is dangerous. Disabled by default, guarded by config flag, documented clearly as power-user only. |

---

## 10. Key References

- Blender MCP (pattern to mirror): https://github.com/ahujasid/blender-mcp
- Material Maker repo: https://github.com/RodZill4/material-maker
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP server registry: https://github.com/modelcontextprotocol/servers

---

*Material Maker MCP — PRD v1.0 — March 2026 — MIT License*
