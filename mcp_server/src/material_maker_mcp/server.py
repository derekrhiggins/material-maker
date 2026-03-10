"""MCP server for Material Maker — bridges Claude to Material Maker over TCP."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from material_maker_mcp.connection import MaterialMakerConnection

mcp = FastMCP("material-maker")

_host = os.environ.get("MM_HOST", "localhost")
_port = int(os.environ.get("MM_PORT", "9002"))
_allow_script = os.environ.get("MM_MCP_ALLOW_SCRIPT", "").strip().lower() in ("1", "true", "yes")
connection = MaterialMakerConnection(host=_host, port=_port)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _ensure_connected() -> None:
    """Lazily connect to Material Maker on first tool call."""
    if connection._writer is None:
        await connection.connect()


async def _cmd(command_type: str, params: dict | None = None) -> dict:
    """Send a command, auto-connecting if necessary."""
    await _ensure_connected()
    return await connection.send_command(command_type, params)


# ---------------------------------------------------------------------------
# 3.1  Graph / Node Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_node(
    node_type: str,
    position_x: float = 0,
    position_y: float = 0,
    node_name: str | None = None,
) -> dict:
    """Create a new node in the current Material Maker graph.

    Args:
        node_type: The node type identifier (e.g. "noise.fbm", "filter.normal_map").
        position_x: Horizontal position in the graph.
        position_y: Vertical position in the graph.
        node_name: Optional human-readable name for the node.
    """
    params: dict[str, Any] = {
        "node_type": node_type,
        "position_x": position_x,
        "position_y": position_y,
    }
    if node_name is not None:
        params["node_name"] = node_name
    return await _cmd("create_node", params)


@mcp.tool()
async def delete_node(node_id: str) -> dict:
    """Delete a node from the current graph by its ID.

    Args:
        node_id: The unique identifier of the node to delete.
    """
    return await _cmd("delete_node", {"node_id": node_id})


@mcp.tool()
async def connect_nodes(
    from_node_id: str,
    from_port: int,
    to_node_id: str,
    to_port: int,
) -> dict:
    """Connect an output port of one node to an input port of another.

    Args:
        from_node_id: Source node ID.
        from_port: Output port index on the source node.
        to_node_id: Destination node ID.
        to_port: Input port index on the destination node.
    """
    return await _cmd(
        "connect_nodes",
        {
            "from_node_id": from_node_id,
            "from_port": from_port,
            "to_node_id": to_node_id,
            "to_port": to_port,
        },
    )


@mcp.tool()
async def disconnect_nodes(
    from_node_id: str,
    from_port: int,
    to_node_id: str,
    to_port: int,
) -> dict:
    """Remove a connection between two nodes.

    Args:
        from_node_id: Source node ID.
        from_port: Output port index on the source node.
        to_node_id: Destination node ID.
        to_port: Input port index on the destination node.
    """
    return await _cmd(
        "disconnect_nodes",
        {
            "from_node_id": from_node_id,
            "from_port": from_port,
            "to_node_id": to_node_id,
            "to_port": to_port,
        },
    )


@mcp.tool()
async def get_graph_info() -> dict:
    """Get a full description of the current material graph.

    Returns all nodes, connections, and parameters in the active graph.
    """
    return await _cmd("get_graph_info")


@mcp.tool()
async def list_available_nodes(category: str | None = None) -> dict:
    """List all node types available in Material Maker.

    Args:
        category: Optional category name to filter results.
    """
    params: dict[str, Any] | None = None
    if category is not None:
        params = {"category": category}
    return await _cmd("list_available_nodes", params)


# ---------------------------------------------------------------------------
# 3.2  Parameter Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_node_parameters(node_id: str) -> dict:
    """Get all current parameter values for a specific node.

    Args:
        node_id: The unique identifier of the node.
    """
    return await _cmd("get_node_parameters", {"node_id": node_id})


@mcp.tool()
async def set_node_parameter(node_id: str, parameter: str, value: Any) -> dict:
    """Set a single parameter on a node.

    Args:
        node_id: The unique identifier of the node.
        parameter: The parameter name to set.
        value: The new value for the parameter.
    """
    return await _cmd(
        "set_node_parameter",
        {
            "node_id": node_id,
            "parameter": parameter,
            "value": value,
        },
    )


@mcp.tool()
async def set_multiple_parameters(updates: list[dict]) -> dict:
    """Set multiple parameters on one or more nodes in a single call.

    Args:
        updates: A list of dicts, each with keys "node_id", "parameter", and "value".
    """
    return await _cmd("set_multiple_parameters", {"updates": updates})


# ---------------------------------------------------------------------------
# 3.3  Export Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def export_material(
    output_path: str,
    format: str = "png",
    resolution: int = 1024,
    maps: list[str] | None = None,
) -> dict:
    """Export the current material as texture maps to disk.

    Args:
        output_path: Directory path where texture files will be saved.
        format: Image format — "png", "exr", or "jpg".
        resolution: Texture resolution in pixels (default 1024).
        maps: Specific maps to export (e.g. ["albedo", "normal"]). Exports all if omitted.
    """
    params: dict[str, Any] = {
        "output_path": output_path,
        "format": format,
        "resolution": resolution,
    }
    if maps is not None:
        params["maps"] = maps
    return await _cmd("export_material", params)


@mcp.tool()
async def export_for_engine(
    output_path: str,
    engine: str,
    resolution: int = 1024,
) -> dict:
    """Export material in a game-engine-ready format.

    Args:
        output_path: Directory path where exported files will be saved.
        engine: Target engine — "godot", "unity", "unreal", or "blender".
        resolution: Texture resolution in pixels (default 1024).
    """
    return await _cmd(
        "export_for_engine",
        {
            "output_path": output_path,
            "engine": engine,
            "resolution": resolution,
        },
    )


@mcp.tool()
async def list_export_profiles() -> dict:
    """List all available export profiles from the current material.

    Returns profile names like "Godot/Godot 4 ORM", "Unity/3D", etc.
    """
    return await _cmd("list_export_profiles")


# ---------------------------------------------------------------------------
# 3.x  Preview Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_preview_image(
    node_id: str,
    output_index: int = 0,
    size: int = 512,
) -> dict:
    """Get a base64-encoded PNG preview of a node's rendered output texture.

    Args:
        node_id: The unique identifier of the node to preview.
        output_index: Which output port to render (default 0).
        size: Preview image size in pixels (default 512, clamped to 16–2048).
    """
    size = max(16, min(size, 2048))
    return await _cmd(
        "get_preview_image",
        {
            "node_id": node_id,
            "output_index": output_index,
            "size": size,
        },
    )


@mcp.tool()
async def get_3d_preview(size: int = 512) -> dict:
    """Get a base64-encoded PNG screenshot of the 3D material preview viewport.

    Args:
        size: Preview image size in pixels (default 512, clamped to 16–2048).
    """
    size = max(16, min(size, 2048))
    return await _cmd("get_3d_preview", {"size": size})


# ---------------------------------------------------------------------------
# 3.4  Scene / Project Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_scene_info() -> dict:
    """Get metadata about the currently open Material Maker project.

    Returns file path, material type, node count, unsaved-changes flag, and MM version.
    """
    return await _cmd("get_scene_info")


@mcp.tool()
async def save_project(path: str | None = None) -> dict:
    """Save the current project to disk.

    Args:
        path: File path to save to. Omit to save to the current path.
    """
    params: dict[str, Any] | None = None
    if path is not None:
        params = {"path": path}
    return await _cmd("save_project", params)


@mcp.tool()
async def load_project(path: str) -> dict:
    """Open a Material Maker project file (.mmg).

    Args:
        path: Path to the .mmg file to open.
    """
    return await _cmd("load_project", {"path": path})


@mcp.tool()
async def new_project(material_type: str = "pbr") -> dict:
    """Create a new empty material project.

    Args:
        material_type: The material type — "pbr", "dynamic_pbr", "raymarching", or "unlit".
    """
    return await _cmd("new_project", {"material_type": material_type})


@mcp.tool()
async def execute_mm_script(script: str, context: str | None = None) -> dict:
    """Execute arbitrary GDScript inside Material Maker.

    This is a power-user escape hatch, similar to Blender MCP's execute_blender_code.
    Disabled by default — enable by setting the MM_MCP_ALLOW_SCRIPT=1 environment variable.

    Args:
        script: GDScript code to execute.
        context: Optional execution context identifier.
    """
    if not _allow_script:
        raise RuntimeError(
            "execute_mm_script is disabled. "
            "Set the MM_MCP_ALLOW_SCRIPT=1 environment variable to enable it."
        )
    params: dict[str, Any] = {"script": script}
    if context is not None:
        params["context"] = context
    return await _cmd("execute_mm_script", params)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@mcp.tool()
async def ping() -> dict:
    """Check if Material Maker is running and the MCP plugin is responding.

    Returns protocol version, port, and a pong flag.
    """
    return await _cmd("ping")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the Material Maker MCP server over stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
