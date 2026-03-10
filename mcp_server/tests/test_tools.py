"""Unit tests for Material Maker MCP server tools.

Each tool is tested by mocking ``connection.send_command`` and verifying
that the correct command type / params are forwarded and that the tool
returns what ``send_command`` returns.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

import material_maker_mcp.server as server_module
from material_maker_mcp.server import (
    _cmd,
    _ensure_connected,
    connect_nodes,
    connection,
    create_node,
    delete_node,
    disconnect_nodes,
    execute_mm_script,
    export_for_engine,
    export_material,
    get_3d_preview,
    get_graph_info,
    get_node_parameters,
    get_preview_image,
    get_scene_info,
    list_available_nodes,
    load_project,
    new_project,
    ping,
    save_project,
    set_multiple_parameters,
    set_node_parameter,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_send_command(monkeypatch):
    """Patch ``connection.send_command`` as an AsyncMock for every test.

    Also set ``connection._writer`` to a truthy sentinel so that
    ``_ensure_connected`` does not try to open a real TCP connection.

    Each test can override the return value via
    ``connection.send_command.return_value = ...``.
    """
    mock = AsyncMock(return_value={"status": "ok"})
    monkeypatch.setattr(connection, "send_command", mock)
    # Pretend we are already connected.
    monkeypatch.setattr(connection, "_writer", object())
    yield mock
    # No explicit teardown needed; monkeypatch restores originals.


# ---------------------------------------------------------------------------
# _ensure_connected / auto-connect behaviour
# ---------------------------------------------------------------------------


class TestEnsureConnected:
    """Tests for the lazy-connection helper."""

    async def test_calls_connect_when_writer_is_none(self, monkeypatch):
        """When ``_writer`` is None, ``_ensure_connected`` must call ``connect()``."""
        monkeypatch.setattr(connection, "_writer", None)
        mock_connect = AsyncMock()
        monkeypatch.setattr(connection, "connect", mock_connect)

        await _ensure_connected()

        mock_connect.assert_awaited_once()

    async def test_does_not_call_connect_when_already_connected(self, monkeypatch):
        """When ``_writer`` is not None, ``connect()`` must NOT be called."""
        monkeypatch.setattr(connection, "_writer", object())
        mock_connect = AsyncMock()
        monkeypatch.setattr(connection, "connect", mock_connect)

        await _ensure_connected()

        mock_connect.assert_not_awaited()

    async def test_cmd_auto_connects_on_first_call(self, monkeypatch):
        """``_cmd`` should trigger ``_ensure_connected`` -> ``connect()`` when
        ``_writer`` is None."""
        monkeypatch.setattr(connection, "_writer", None)
        mock_connect = AsyncMock()
        monkeypatch.setattr(connection, "connect", mock_connect)
        # send_command is already mocked by the autouse fixture.

        await _cmd("some_command", {"key": "value"})

        mock_connect.assert_awaited_once()
        connection.send_command.assert_awaited_once_with("some_command", {"key": "value"})


# ---------------------------------------------------------------------------
# 3.1  Graph / Node Tools
# ---------------------------------------------------------------------------


class TestCreateNode:
    async def test_sends_correct_command_with_defaults(self):
        expected = {"status": "ok", "node_id": "n1"}
        connection.send_command.return_value = expected

        result = await create_node(node_type="noise.fbm")

        connection.send_command.assert_awaited_once_with(
            "create_node",
            {"node_type": "noise.fbm", "position_x": 0, "position_y": 0},
        )
        assert result == expected

    async def test_sends_position_and_name(self):
        expected = {"node_id": "n2"}
        connection.send_command.return_value = expected

        result = await create_node(
            node_type="filter.normal_map",
            position_x=100.5,
            position_y=-50,
            node_name="MyNormalMap",
        )

        connection.send_command.assert_awaited_once_with(
            "create_node",
            {
                "node_type": "filter.normal_map",
                "position_x": 100.5,
                "position_y": -50,
                "node_name": "MyNormalMap",
            },
        )
        assert result == expected

    async def test_omits_node_name_when_none(self):
        await create_node(node_type="noise.perlin", node_name=None)

        args = connection.send_command.call_args[0]
        params = args[1]
        assert "node_name" not in params


class TestDeleteNode:
    async def test_sends_correct_command(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await delete_node(node_id="node_42")

        connection.send_command.assert_awaited_once_with("delete_node", {"node_id": "node_42"})
        assert result == expected


class TestConnectNodes:
    async def test_sends_correct_command(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await connect_nodes(from_node_id="a", from_port=0, to_node_id="b", to_port=1)

        connection.send_command.assert_awaited_once_with(
            "connect_nodes",
            {
                "from_node_id": "a",
                "from_port": 0,
                "to_node_id": "b",
                "to_port": 1,
            },
        )
        assert result == expected


class TestDisconnectNodes:
    async def test_sends_correct_command(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await disconnect_nodes(from_node_id="x", from_port=2, to_node_id="y", to_port=3)

        connection.send_command.assert_awaited_once_with(
            "disconnect_nodes",
            {
                "from_node_id": "x",
                "from_port": 2,
                "to_node_id": "y",
                "to_port": 3,
            },
        )
        assert result == expected


class TestGetGraphInfo:
    async def test_sends_correct_command_no_params(self):
        expected = {"nodes": [], "connections": []}
        connection.send_command.return_value = expected

        result = await get_graph_info()

        connection.send_command.assert_awaited_once_with("get_graph_info", None)
        assert result == expected


class TestListAvailableNodes:
    async def test_without_category(self):
        expected = {"nodes": ["noise.fbm", "filter.blur"]}
        connection.send_command.return_value = expected

        result = await list_available_nodes()

        connection.send_command.assert_awaited_once_with("list_available_nodes", None)
        assert result == expected

    async def test_with_category(self):
        expected = {"nodes": ["noise.fbm"]}
        connection.send_command.return_value = expected

        result = await list_available_nodes(category="noise")

        connection.send_command.assert_awaited_once_with(
            "list_available_nodes", {"category": "noise"}
        )
        assert result == expected

    async def test_omits_params_when_category_none(self):
        await list_available_nodes(category=None)

        args = connection.send_command.call_args[0]
        assert args[1] is None


# ---------------------------------------------------------------------------
# 3.2  Parameter Tools
# ---------------------------------------------------------------------------


class TestGetNodeParameters:
    async def test_sends_correct_command(self):
        expected = {"params": {"scale": 2.0}}
        connection.send_command.return_value = expected

        result = await get_node_parameters(node_id="n1")

        connection.send_command.assert_awaited_once_with("get_node_parameters", {"node_id": "n1"})
        assert result == expected


class TestSetNodeParameter:
    async def test_sends_correct_command(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await set_node_parameter(node_id="n1", parameter="scale", value=4.0)

        connection.send_command.assert_awaited_once_with(
            "set_node_parameter",
            {"node_id": "n1", "parameter": "scale", "value": 4.0},
        )
        assert result == expected

    async def test_handles_string_value(self):
        await set_node_parameter(node_id="n2", parameter="label", value="hello")

        connection.send_command.assert_awaited_once_with(
            "set_node_parameter",
            {"node_id": "n2", "parameter": "label", "value": "hello"},
        )


class TestSetMultipleParameters:
    async def test_sends_correct_command(self):
        updates = [
            {"node_id": "n1", "parameter": "scale", "value": 2},
            {"node_id": "n2", "parameter": "seed", "value": 42},
        ]
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await set_multiple_parameters(updates=updates)

        connection.send_command.assert_awaited_once_with(
            "set_multiple_parameters", {"updates": updates}
        )
        assert result == expected


# ---------------------------------------------------------------------------
# 3.3  Export Tools
# ---------------------------------------------------------------------------


class TestExportMaterial:
    async def test_sends_correct_command_defaults(self):
        expected = {"files": ["/out/albedo.png"]}
        connection.send_command.return_value = expected

        result = await export_material(output_path="/out")

        connection.send_command.assert_awaited_once_with(
            "export_material",
            {"output_path": "/out", "format": "png", "resolution": 1024},
        )
        assert result == expected

    async def test_sends_maps_when_provided(self):
        await export_material(
            output_path="/out",
            format="exr",
            resolution=2048,
            maps=["albedo", "normal"],
        )

        connection.send_command.assert_awaited_once_with(
            "export_material",
            {
                "output_path": "/out",
                "format": "exr",
                "resolution": 2048,
                "maps": ["albedo", "normal"],
            },
        )

    async def test_omits_maps_when_none(self):
        await export_material(output_path="/tmp", maps=None)

        args = connection.send_command.call_args[0]
        params = args[1]
        assert "maps" not in params


class TestExportForEngine:
    async def test_sends_correct_command(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await export_for_engine(
            output_path="/game/textures", engine="godot", resolution=512
        )

        connection.send_command.assert_awaited_once_with(
            "export_for_engine",
            {
                "output_path": "/game/textures",
                "engine": "godot",
                "resolution": 512,
            },
        )
        assert result == expected

    async def test_default_resolution(self):
        await export_for_engine(output_path="/out", engine="unity")

        args = connection.send_command.call_args[0]
        assert args[1]["resolution"] == 1024


# ---------------------------------------------------------------------------
# 3.4  Scene / Project Tools
# ---------------------------------------------------------------------------


class TestGetSceneInfo:
    async def test_sends_correct_command_no_params(self):
        expected = {"file_path": "/project.mmg", "node_count": 5}
        connection.send_command.return_value = expected

        result = await get_scene_info()

        connection.send_command.assert_awaited_once_with("get_scene_info", None)
        assert result == expected


class TestSaveProject:
    async def test_without_path(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await save_project()

        connection.send_command.assert_awaited_once_with("save_project", None)
        assert result == expected

    async def test_with_path(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await save_project(path="/home/user/material.mmg")

        connection.send_command.assert_awaited_once_with(
            "save_project", {"path": "/home/user/material.mmg"}
        )
        assert result == expected

    async def test_omits_params_when_path_none(self):
        await save_project(path=None)

        args = connection.send_command.call_args[0]
        assert args[1] is None


class TestLoadProject:
    async def test_sends_correct_command(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await load_project(path="/home/user/project.mmg")

        connection.send_command.assert_awaited_once_with(
            "load_project", {"path": "/home/user/project.mmg"}
        )
        assert result == expected


class TestNewProject:
    async def test_sends_default_material_type(self):
        expected = {"status": "ok"}
        connection.send_command.return_value = expected

        result = await new_project()

        connection.send_command.assert_awaited_once_with("new_project", {"material_type": "pbr"})
        assert result == expected

    async def test_sends_custom_material_type(self):
        await new_project(material_type="unlit")

        connection.send_command.assert_awaited_once_with("new_project", {"material_type": "unlit"})


class TestExecuteMmScript:
    @pytest.fixture(autouse=True)
    def _enable_script(self, monkeypatch):
        monkeypatch.setattr(server_module, "_allow_script", True)

    async def test_sends_correct_command(self):
        expected = {"output": "hello"}
        connection.send_command.return_value = expected

        result = await execute_mm_script(script="print('hello')")

        connection.send_command.assert_awaited_once_with(
            "execute_mm_script", {"script": "print('hello')"}
        )
        assert result == expected

    async def test_sends_context_when_provided(self):
        await execute_mm_script(script="code()", context="editor")

        connection.send_command.assert_awaited_once_with(
            "execute_mm_script",
            {"script": "code()", "context": "editor"},
        )

    async def test_omits_context_when_none(self):
        await execute_mm_script(script="code()", context=None)

        args = connection.send_command.call_args[0]
        params = args[1]
        assert "context" not in params


class TestExecuteMmScriptDisabled:
    async def test_raises_when_disabled(self):
        with pytest.raises(RuntimeError, match="execute_mm_script is disabled"):
            await execute_mm_script(script="print('hello')")


# ---------------------------------------------------------------------------
# 3.x  Preview Tools
# ---------------------------------------------------------------------------


class TestGetPreviewImage:
    async def test_sends_correct_command_with_defaults(self):
        expected = {"image": "base64data", "format": "png", "size": 512, "node_id": "bricks"}
        connection.send_command.return_value = expected

        result = await get_preview_image(node_id="bricks")

        connection.send_command.assert_awaited_once_with(
            "get_preview_image",
            {"node_id": "bricks", "output_index": 0, "size": 512},
        )
        assert result == expected

    async def test_sends_custom_params(self):
        expected = {"image": "data", "format": "png", "size": 1024, "node_id": "noise"}
        connection.send_command.return_value = expected

        result = await get_preview_image(node_id="noise", output_index=1, size=1024)

        connection.send_command.assert_awaited_once_with(
            "get_preview_image",
            {"node_id": "noise", "output_index": 1, "size": 1024},
        )
        assert result == expected

    async def test_clamps_size_to_max(self):
        await get_preview_image(node_id="n1", size=99999)

        args = connection.send_command.call_args[0]
        assert args[1]["size"] == 2048

    async def test_clamps_size_to_min(self):
        await get_preview_image(node_id="n1", size=1)

        args = connection.send_command.call_args[0]
        assert args[1]["size"] == 16


class TestGet3dPreview:
    async def test_sends_correct_command_with_defaults(self):
        expected = {"image": "base64data", "format": "png", "size": 512}
        connection.send_command.return_value = expected

        result = await get_3d_preview()

        connection.send_command.assert_awaited_once_with(
            "get_3d_preview",
            {"size": 512},
        )
        assert result == expected

    async def test_sends_custom_size(self):
        expected = {"image": "data", "format": "png", "size": 256}
        connection.send_command.return_value = expected

        result = await get_3d_preview(size=256)

        connection.send_command.assert_awaited_once_with(
            "get_3d_preview",
            {"size": 256},
        )
        assert result == expected

    async def test_clamps_size_to_max(self):
        await get_3d_preview(size=5000)

        args = connection.send_command.call_args[0]
        assert args[1]["size"] == 2048

    async def test_clamps_size_to_min(self):
        await get_3d_preview(size=0)

        args = connection.send_command.call_args[0]
        assert args[1]["size"] == 16


class TestPing:
    async def test_sends_correct_command(self):
        expected = {"pong": True, "protocol_version": "0.1.0", "port": 9002}
        connection.send_command.return_value = expected

        result = await ping()

        connection.send_command.assert_awaited_once_with("ping", None)
        assert result == expected


# ---------------------------------------------------------------------------
# Return-value passthrough
# ---------------------------------------------------------------------------


class TestReturnValuePassthrough:
    """Verify that every tool faithfully returns whatever ``send_command`` returns."""

    @pytest.fixture(autouse=True)
    def _enable_script(self, monkeypatch):
        monkeypatch.setattr(server_module, "_allow_script", True)

    async def test_arbitrary_dict_returned(self):
        sentinel = {"custom_key": [1, 2, 3], "nested": {"a": True}}
        connection.send_command.return_value = sentinel

        # Spot-check several tools with the same sentinel.
        assert await delete_node(node_id="x") == sentinel
        connection.send_command.return_value = sentinel
        assert await get_graph_info() == sentinel
        connection.send_command.return_value = sentinel
        assert await save_project() == sentinel
        connection.send_command.return_value = sentinel
        assert await execute_mm_script(script="1+1") == sentinel
