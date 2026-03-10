# Implementation Todo List

> Complete phases in order. Check boxes as you go.
> Split from [spec.md](spec.md) § 7.
>
> **Architecture update:** The GDScript addon is now integrated via a
> [fork of Material Maker](https://github.com/derekrhiggins/material-maker)
> rather than a standalone plugin (MM has no external plugin loading system).
> The addon is registered as an autoload in `project.godot` and starts
> automatically with MM. See `TODO_MCP.md` in the fork repo for fork-specific tasks.

---

### Phase 1 — Repo & Scaffolding

- [x] **1.** Create GitHub repo `material-maker-mcp` with MIT license and `.gitignore` (Python + GDScript) — `GitHub`  🔴 HIGH
- [x] **2.** Create top-level directory structure: `addon/`, `src/`, `tests/`, `docs/` — `repo root`  🔴 HIGH
- [x] **3.** Write `pyproject.toml` with package name `material-maker-mcp`, version, entry point `material_maker_mcp.server:main`, and `mcp` dependency — `pyproject.toml`  🔴 HIGH
- [x] **4.** Write initial `README.md` with project description, install instructions placeholder, and badges — `README.md`  🔴 HIGH
- [x] **5.** Create `addon/plugin.cfg` — Material Maker plugin manifest with name, description, version, author — `addon/plugin.cfg`  🔴 HIGH
- [x] **6.** Create `src/material_maker_mcp/__init__.py` package init — `src/.../__init__.py`  🔴 HIGH

---

### Phase 2 — GDScript TCP Server (addon.gd)

- [x] **7.** Create `addon/addon.gd`: extend `Node` (MM plugin convention, NOT Godot `EditorPlugin`), implement `_ready()` and `_exit_tree()` lifecycle — `addon/addon.gd`  🔴 HIGH
- [ ] **8.** In `addon.gd`: detect Godot engine version (3.x vs 4.x) at startup and select correct TCP/networking API — `addon/addon.gd`  🔴 HIGH
- [x] **9.** In `addon.gd`: initialize `TCPServer` and start listening on port 9002 in `_ready()` — `addon/addon.gd`  🔴 HIGH
- [x] **10.** In `addon.gd`: implement `_process()` loop to poll for new connections and read incoming data — `addon/addon.gd`  🔴 HIGH
- [x] **11.** In `addon.gd`: implement JSON parse/dispatch — route `type` field to the correct handler function — `addon/addon.gd`  🔴 HIGH
- [x] **12.** In `addon.gd`: implement `send_response(peer, status, result)` helper to write newline-delimited JSON — `addon/addon.gd`  🔴 HIGH
- [ ] **13.** In `addon.gd`: add configuration panel to MM sidebar showing server port and status (Running/Stopped) — `addon/addon.gd`  🟡 MED
- [x] **14.** In `addon.gd`: add port override via environment variable `MM_MCP_PORT` — `addon/addon.gd`  🟡 MED
- [x] **15.** In `addon.gd`: handle TCP client disconnection cleanly without crashing — `addon/addon.gd`  🔴 HIGH

---

### Phase 3 — GDScript Command Handlers

- [x] **16.** Create `addon/commands/scene.gd`: implement `get_scene_info` command — `commands/scene.gd`  🔴 HIGH
- [x] **17.** In `scene.gd`: implement `save_project` command using MM's file I/O API — `commands/scene.gd`  🔴 HIGH
- [x] **18.** In `scene.gd`: implement `load_project` command — `commands/scene.gd`  🔴 HIGH
- [x] **19.** In `scene.gd`: implement `new_project` command with `material_type` param — `commands/scene.gd`  🟡 MED
- [x] **20.** Create `addon/commands/graph.gd`: implement `create_node` command — `commands/graph.gd`  🔴 HIGH
- [x] **21.** In `graph.gd`: implement `delete_node` command — `commands/graph.gd`  🔴 HIGH
- [x] **22.** In `graph.gd`: implement `connect_nodes` command — `commands/graph.gd`  🔴 HIGH
- [x] **23.** In `graph.gd`: implement `disconnect_nodes` command — `commands/graph.gd`  🔴 HIGH
- [x] **24.** In `graph.gd`: implement `get_graph_info` command (serialize all nodes + connections) — `commands/graph.gd`  🔴 HIGH
- [x] **25.** In `graph.gd`: implement `list_available_nodes` command (read MM node registry) — `commands/graph.gd`  🟡 MED
- [x] **26.** Create `addon/commands/parameters.gd`: implement `get_node_parameters` command — `commands/parameters.gd`  🔴 HIGH
- [x] **27.** In `parameters.gd`: implement `set_node_parameter` for all MM param types (float, int, color, bool, enum) — `commands/parameters.gd`  🔴 HIGH
- [x] **28.** In `parameters.gd`: implement `set_multiple_parameters` batched command — `commands/parameters.gd`  🟡 MED
- [x] **29.** Create `addon/commands/export.gd`: implement `export_material` command — `commands/export.gd`  🔴 HIGH
- [x] **30.** In `export.gd`: implement `export_for_engine` command for Godot, Unity, Unreal targets — `commands/export.gd`  🟡 MED
- [x] **31.** Create `addon/commands/utils.gd`: implement `execute_mm_script` (disabled by default via config flag) — `commands/utils.gd`  🟢 LOW

---

### Phase 4 — Python MCP Server

- [x] **32.** Create `src/material_maker_mcp/connection.py`: async TCP client class with `connect()`, `send_command()`, `close()` — `connection.py`  🔴 HIGH
- [x] **33.** In `connection.py`: implement reconnection with exponential backoff (retry up to 5x), 30s command timeout, and friendly error when MM is not running (`"Material Maker is not running. Start MM and enable the MCP plugin."`) — `connection.py`  🔴 HIGH
- [x] **34.** Create `src/material_maker_mcp/server.py`: initialize MCP server with `mcp.Server("material-maker")` — `server.py`  🔴 HIGH
- [x] **35.** In `server.py`: implement `@server.list_tools()` handler returning all tool definitions with JSON schemas — `server.py`  🔴 HIGH
- [x] **36.** In `server.py`: implement `@server.call_tool()` handler dispatching to `connection.send_command()` — `server.py`  🔴 HIGH
- [x] **37.** In `server.py`: implement `main()` entrypoint using `mcp.run()` with stdio transport — `server.py`  🔴 HIGH
- [x] **38.** Create `tools/graph_tools.py`: define tool schemas for `create_node`, `delete_node`, `connect_nodes`, `disconnect_nodes`, `get_graph_info`, `list_available_nodes` — `tools/graph_tools.py`  🔴 HIGH
- [x] **39.** Create `tools/parameter_tools.py`: define tool schemas for `get_node_parameters`, `set_node_parameter`, `set_multiple_parameters` — `tools/parameter_tools.py`  🔴 HIGH
- [x] **40.** Create `tools/export_tools.py`: define tool schemas for `export_material`, `export_for_engine` — `tools/export_tools.py`  🔴 HIGH
- [x] **41.** Create `tools/scene_tools.py`: define tool schemas for `get_scene_info`, `save_project`, `load_project`, `new_project` — `tools/scene_tools.py`  🔴 HIGH
- [ ] **42.** Implement input validation in each tool handler — reject bad types and out-of-range values with helpful messages — `server.py`  🔴 HIGH

---

### Phase 5 — Testing

- [x] **43.** Create `tests/test_connection.py`: unit test TCP connection, reconnection logic, timeout handling — `tests/`  🔴 HIGH
- [x] **44.** Create `tests/test_tools.py`: mock MM socket responses and verify each tool produces correct MCP output — `tests/`  🔴 HIGH
- [ ] **45.** Create `tests/integration/`: integration tests that launch MM headlessly and run full command round-trips — `tests/integration/`  🟡 MED
- [ ] **46.** Test `create_node` for the top 10 most common MM node types — `tests/`  🔴 HIGH
- [ ] **47.** Test `connect_nodes` and verify graph structure with `get_graph_info` — `tests/`  🔴 HIGH
- [ ] **48.** Test `set_node_parameter` with float, int, color, bool, and enum types — `tests/`  🔴 HIGH
- [ ] **49.** Test `export_material` — verify output files exist at specified path with correct dimensions — `tests/`  🔴 HIGH
- [x] **50.** Add CI via GitHub Actions: lint (ruff), type check (mypy), unit tests on push — `.github/workflows/`  🟡 MED

---

### Phase 6 — Documentation & Release

- [x] **51.** Write full `README.md`: what is this, prerequisites, install addon steps, configure Claude Desktop JSON, usage examples — `README.md`  🔴 HIGH
- [x] **52.** Write `TOOLS.md`: table of every MCP tool, params, return type, and example Claude prompts — `TOOLS.md`  🟡 MED
- [ ] **53.** Write `CONTRIBUTING.md`: how to add new commands, coding style, how to run tests — `CONTRIBUTING.md`  🟢 LOW
- [ ] **54.** Publish to PyPI as `material-maker-mcp` so `uvx` installation works — `PyPI`  🔴 HIGH
- [ ] **55.** Submit to Anthropic's MCP server registry (`modelcontextprotocol/servers`) — `GitHub PR`  🟡 MED
- [ ] **56.** Post to Material Maker Discord and Reddit (r/godot, r/gamedev) — `Community`  🟢 LOW
- [ ] **57.** Create a short demo video/gif showing Claude creating a brick material from scratch in MM — `README.md`  🟢 LOW

---

### Phase 7 — v1.1 Features (post-MVP)

> Tracks FR-15 through FR-17 from [spec.md](spec.md) § 6.2 that were missing from the original checklist.
> GDScript-side work now lives in the [MM fork](https://github.com/derekrhiggins/material-maker) — see `TODO_MCP.md` there.

- [x] **58.** Implement `get_preview_image` tool — return base64 PNG of a node's 2D texture preview — fork `TODO_MCP.md` F14–F16  🔴 HIGH
- [x] **59.** Implement `get_3d_preview` tool — capture 3D material preview viewport as PNG — fork `TODO_MCP.md` F17  🟡 MED
- [ ] **60.** Implement `auto_arrange_graph` tool — automatically layout nodes for readability — `commands/graph.gd`, `tools/graph_tools.py`  🟡 MED
- [ ] **61.** Wrap all mutating commands in MM's undo history so Ctrl+Z works after AI edits — `addon/addon.gd`  🟡 MED
