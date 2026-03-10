# Material Maker MCP -- Tools Reference

This document is a complete reference for every MCP tool exposed by the Material Maker MCP server. Tools are listed by category. For installation and setup, see [README.md](README.md). For the underlying specification, see [spec.md](spec.md).

---

## Summary

| Tool | Category | Description |
|---|---|---|
| `create_node` | Graph / Node | Create a new node in the current material graph |
| `delete_node` | Graph / Node | Delete a node by its ID |
| `connect_nodes` | Graph / Node | Connect an output port of one node to an input port of another |
| `disconnect_nodes` | Graph / Node | Remove a connection between two nodes |
| `get_graph_info` | Graph / Node | Get all nodes, connections, and parameters in the active graph |
| `list_available_nodes` | Graph / Node | List all node types available in Material Maker |
| `get_node_parameters` | Parameter | Get all current parameter values for a node |
| `set_node_parameter` | Parameter | Set a single parameter on a node |
| `set_multiple_parameters` | Parameter | Set multiple parameters across one or more nodes in one call |
| `export_material` | Export | Export the current material as texture maps to disk |
| `export_for_engine` | Export | Export material in a game-engine-ready format |
| `list_export_profiles` | Export | List all available export profiles from the current material |
| `get_preview_image` | Preview | Get a base64-encoded PNG preview of a node's rendered output |
| `get_3d_preview` | Preview | Get a base64-encoded PNG screenshot of the 3D material preview |
| `get_scene_info` | Scene / Project | Get metadata about the currently open project |
| `save_project` | Scene / Project | Save the current project to disk |
| `load_project` | Scene / Project | Open a `.mmg` project file |
| `new_project` | Scene / Project | Create a new empty material project |
| `ping` | Utility | Check if Material Maker is running and the MCP addon is responding |
| `execute_mm_script` | Utility | Execute arbitrary GDScript inside Material Maker |

---

## 1. Graph / Node Tools

### `create_node`

Create a new node in the current Material Maker graph.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `node_type` | `string` | Yes | -- | Node type identifier (e.g. `"noise.fbm"`, `"filter.normal_map"`). |
| `position_x` | `float` | No | `0` | Horizontal position in the graph canvas. |
| `position_y` | `float` | No | `0` | Vertical position in the graph canvas. |
| `node_name` | `string` | No | `null` | Optional human-readable name for the node. |

#### Return Value

```json
{
  "node_id": "string",
  "node_type": "string",
  "position": { "x": 0.0, "y": 0.0 }
}
```

#### Example Prompt

> "Add an FBM noise node at position (200, 100) in Material Maker."

---

### `delete_node`

Delete a node from the current graph by its ID.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `node_id` | `string` | Yes | -- | The unique identifier of the node to delete. |

#### Return Value

```json
{
  "deleted": true,
  "node_id": "string"
}
```

#### Example Prompt

> "Remove the node with ID 'node_3' from my Material Maker graph."

---

### `connect_nodes`

Connect an output port of one node to an input port of another.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `from_node_id` | `string` | Yes | -- | Source node ID. |
| `from_port` | `int` | Yes | -- | Output port index on the source node. |
| `to_node_id` | `string` | Yes | -- | Destination node ID. |
| `to_port` | `int` | Yes | -- | Input port index on the destination node. |

#### Return Value

```json
{
  "connected": true,
  "from": { "node_id": "string", "port": 0 },
  "to": { "node_id": "string", "port": 0 }
}
```

#### Example Prompt

> "Connect the output of the noise node to input 0 of the normal map node."

---

### `disconnect_nodes`

Remove a connection between two nodes.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `from_node_id` | `string` | Yes | -- | Source node ID. |
| `from_port` | `int` | Yes | -- | Output port index on the source node. |
| `to_node_id` | `string` | Yes | -- | Destination node ID. |
| `to_port` | `int` | Yes | -- | Input port index on the destination node. |

#### Return Value

```json
{
  "disconnected": true
}
```

#### Example Prompt

> "Disconnect the noise node's output 0 from the normal map node's input 0."

---

### `get_graph_info`

Get a full description of the current material graph, including all nodes, connections, and parameters.

#### Parameters

None.

#### Return Value

```json
{
  "nodes": [
    {
      "node_id": "string",
      "node_type": "string",
      "position": { "x": 0.0, "y": 0.0 },
      "parameters": { "...": "..." }
    }
  ],
  "connections": [
    {
      "from_node_id": "string",
      "from_port": 0,
      "to_node_id": "string",
      "to_port": 0
    }
  ],
  "material_type": "string"
}
```

#### Example Prompt

> "Show me what nodes are currently in my Material Maker graph and how they are connected."

---

### `list_available_nodes`

List all node types available in the current installation of Material Maker, optionally filtered by category.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `category` | `string` | No | `null` | Category name to filter results (e.g. `"noise"`, `"filter"`). Returns all categories if omitted. |

#### Return Value

```json
{
  "categories": {
    "category_name": ["node_type_string", "..."]
  }
}
```

#### Example Prompt

> "What node types are available for generating patterns in Material Maker?"

---

## 2. Parameter Tools

### `get_node_parameters`

Get all current parameter values for a specific node.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `node_id` | `string` | Yes | -- | The unique identifier of the node. |

#### Return Value

```json
{
  "node_id": "string",
  "parameters": {
    "param_name": {
      "value": "any",
      "type": "string",
      "min": 0.0,
      "max": 1.0,
      "options": ["..."]
    }
  }
}
```

The `min`, `max`, and `options` fields are present only when applicable to the parameter type.

#### Example Prompt

> "What are the current parameters on the FBM noise node?"

---

### `set_node_parameter`

Set a single parameter on a node. Triggers a shader recompile in Material Maker.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `node_id` | `string` | Yes | -- | The unique identifier of the node. |
| `parameter` | `string` | Yes | -- | The parameter name to set. |
| `value` | `any` | Yes | -- | The new value for the parameter. Type must match the parameter definition. |

#### Return Value

```json
{
  "node_id": "string",
  "parameter": "string",
  "old_value": "any",
  "new_value": "any"
}
```

#### Example Prompt

> "Set the scale parameter on the noise node to 4.0."

---

### `set_multiple_parameters`

Set multiple parameters on one or more nodes in a single call. Shader recompilation is deferred until all updates are applied.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `updates` | `list[dict]` | Yes | -- | A list of objects, each containing `node_id` (string), `parameter` (string), and `value` (any). |

Each entry in `updates` has the following shape:

```json
{ "node_id": "string", "parameter": "string", "value": "any" }
```

#### Return Value

```json
{
  "updated": 3,
  "results": [
    { "node_id": "string", "parameter": "string", "old_value": "any", "new_value": "any" }
  ]
}
```

#### Example Prompt

> "On the FBM noise node, set scale to 4.0 and octaves to 6. Also set the normal map node's strength to 1.5."

---

## 3. Export Tools

### `export_material`

Export the current material as texture maps to disk.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `output_path` | `string` | Yes | -- | Directory path where texture files will be saved. |
| `format` | `string` | No | `"png"` | Image format. One of `"png"`, `"exr"`, or `"jpg"`. |
| `resolution` | `int` | No | `1024` | Texture resolution in pixels (width and height). |
| `maps` | `list[string]` | No | `null` (all maps) | Specific maps to export. Valid values: `"albedo"`, `"roughness"`, `"metalness"`, `"normal"`, `"height"`, `"ao"`. Exports all maps if omitted. |

#### Return Value

```json
{
  "exported_files": [
    { "map": "albedo", "path": "/path/to/albedo.png", "resolution": 1024 },
    { "map": "normal", "path": "/path/to/normal.png", "resolution": 1024 }
  ]
}
```

#### Example Prompt

> "Export my material as PNG texture maps at 2048 resolution to ~/Materials/rust/."

---

### `export_for_engine`

Export material in a game-engine-ready format. For Unreal Engine, this also generates a Python setup script.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `output_path` | `string` | Yes | -- | Directory path where exported files will be saved. |
| `engine` | `string` | Yes | -- | Target engine. One of `"godot"`, `"unity"`, or `"unreal"`. |
| `resolution` | `int` | No | `1024` | Texture resolution in pixels (width and height). |

#### Return Value

```json
{
  "engine": "unreal",
  "exported_files": [
    { "map": "albedo", "path": "/path/to/albedo.png", "resolution": 1024 }
  ],
  "script_path": "/path/to/setup_material.py"
}
```

The `script_path` field is present only for engine targets that generate a companion script (e.g. Unreal).

#### Example Prompt

> "Export the current material for Unreal Engine 5 at 2048 resolution to ~/Materials/rust/."

---

### `list_export_profiles`

List all available export profiles from the current material.

#### Parameters

None.

#### Return Value

```json
{
  "profiles": ["Godot/Godot 4 ORM", "Unity/3D", "Unreal/Unreal"]
}
```

#### Example Prompt

> "What export profiles are available for my current material?"

---

## 4. Preview Tools

### `get_preview_image`

Get a base64-encoded PNG preview of a node's rendered output texture.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `node_id` | `string` | Yes | -- | The unique identifier of the node to preview. |
| `output_index` | `int` | No | `0` | Which output port to render. |
| `size` | `int` | No | `512` | Preview image size in pixels (max 2048). |

#### Return Value

```json
{
  "image": "base64-encoded PNG data",
  "format": "png",
  "size": 512,
  "node_id": "bricks"
}
```

#### Example Prompt

> "Show me a preview of the bricks node output."

---

### `get_3d_preview`

Get a base64-encoded PNG screenshot of the 3D material preview viewport (the sphere/cube showing the applied material).

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `size` | `int` | No | `512` | Preview image size in pixels (max 2048). |

#### Return Value

```json
{
  "image": "base64-encoded PNG data",
  "format": "png",
  "size": 512
}
```

#### Example Prompt

> "Show me how the material looks on the 3D preview sphere."

---

## 5. Scene / Project Tools

### `get_scene_info`

Get metadata about the currently open Material Maker project.

#### Parameters

None.

#### Return Value

```json
{
  "file_path": "/path/to/project.mmg",
  "material_type": "pbr",
  "node_count": 12,
  "has_unsaved_changes": false,
  "mm_version": "1.4"
}
```

#### Example Prompt

> "What project do I have open in Material Maker right now?"

---

### `save_project`

Save the current project to disk.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | `string` | No | `null` | File path to save to. Omit to save to the current file path (overwrite). |

#### Return Value

```json
{
  "saved": true,
  "path": "/path/to/project.mmg"
}
```

#### Example Prompt

> "Save my current Material Maker project as crater_rock.mmg."

---

### `load_project`

Open a Material Maker project file (`.mmg`).

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | `string` | Yes | -- | Path to the `.mmg` file to open. |

#### Return Value

```json
{
  "loaded": true,
  "path": "/path/to/project.mmg",
  "node_count": 8
}
```

#### Example Prompt

> "Open the project file at ~/Materials/brick_wall.mmg in Material Maker."

---

### `new_project`

Create a new empty material project.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `material_type` | `string` | No | `"pbr"` | The material type. One of `"pbr"`, `"dynamic_pbr"`, `"raymarching"`, or `"unlit"`. |

#### Return Value

```json
{
  "created": true,
  "material_type": "pbr"
}
```

#### Example Prompt

> "Start a new dynamic PBR material in Material Maker."

---

## 6. Utility Tools

### `ping`

Check if Material Maker is running and the MCP addon is responding.

#### Parameters

None.

#### Return Value

```json
{
  "pong": true,
  "protocol_version": "0.1.0",
  "port": 9002
}
```

#### Example Prompt

> "Is Material Maker connected?"

---

### `execute_mm_script`

Execute arbitrary GDScript inside Material Maker. This is a power-user escape hatch, analogous to Blender MCP's `execute_blender_code`.

**Security note:** This tool is disabled by default. It must be explicitly enabled in the server configuration. Do not enable in production environments.

#### Parameters

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `script` | `string` | Yes | -- | GDScript code to execute inside Material Maker. |
| `context` | `string` | No | `null` | Optional execution context identifier. |

#### Return Value

```json
{
  "result": "any",
  "output": "string"
}
```

#### Example Prompt

> "Run this GDScript in Material Maker to list all node names: `for n in mm_graph.get_children(): print(n.name)`"

---

## Protocol Details

All tools communicate with the Material Maker GDScript plugin over TCP (default port 9002). The wire format is newline-delimited JSON:

- **Command:** `{ "type": "tool_name", "params": { ... } }`
- **Success:** `{ "status": "ok", "result": { ... } }`
- **Error:** `{ "status": "error", "message": "human-readable error" }`

The default timeout is 30 seconds per command. Export operations on large resolutions may take longer. The port is configurable via the `MM_PORT` environment variable (default 9002). The timeout is currently hardcoded in `connection.py`.
