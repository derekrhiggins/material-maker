"""Unit tests for MaterialMakerConnection."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from material_maker_mcp.connection import MaterialMakerConnection

# ---------------------------------------------------------------------------
# 1. Successful connection
# ---------------------------------------------------------------------------


async def test_connect_success(
    connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
    mock_writer: MagicMock,
) -> None:
    """connect() should store reader/writer returned by open_connection."""
    with patch(
        "material_maker_mcp.connection.asyncio.open_connection",
        new_callable=AsyncMock,
        return_value=(mock_reader, mock_writer),
    ):
        await connection.connect()

    assert connection._reader is mock_reader
    assert connection._writer is mock_writer
    assert connection._buffer == b""


# ---------------------------------------------------------------------------
# 2. Exponential backoff retry
# ---------------------------------------------------------------------------


async def test_connect_exponential_backoff(
    connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
    mock_writer: MagicMock,
) -> None:
    """connect() should sleep with doubling delays (1, 2, 4) on transient failures."""
    failures = 3
    side_effects: list = [ConnectionRefusedError("refused") for _ in range(failures)]
    side_effects.append((mock_reader, mock_writer))

    with (
        patch(
            "material_maker_mcp.connection.asyncio.open_connection",
            new_callable=AsyncMock,
            side_effect=side_effects,
        ),
        patch(
            "material_maker_mcp.connection.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep,
    ):
        await connection.connect()

    # Delays: 1s after attempt 1, 2s after attempt 2, 4s after attempt 3.
    assert mock_sleep.call_count == failures
    assert mock_sleep.call_args_list[0].args == (1.0,)
    assert mock_sleep.call_args_list[1].args == (2.0,)
    assert mock_sleep.call_args_list[2].args == (4.0,)

    assert connection._reader is mock_reader
    assert connection._writer is mock_writer


# ---------------------------------------------------------------------------
# 3. Connection failure after max retries
# ---------------------------------------------------------------------------


async def test_connect_max_retries_raises(
    connection: MaterialMakerConnection,
) -> None:
    """connect() should raise ConnectionError after 5 failed attempts."""
    with (
        patch(
            "material_maker_mcp.connection.asyncio.open_connection",
            new_callable=AsyncMock,
            side_effect=ConnectionRefusedError("refused"),
        ),
        patch(
            "material_maker_mcp.connection.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep,
    ):
        with pytest.raises(ConnectionError, match="Could not connect to Material Maker"):
            await connection.connect()

    # 4 sleeps between 5 attempts (no sleep after the final failed attempt).
    assert mock_sleep.call_count == 4
    assert connection._reader is None
    assert connection._writer is None


# ---------------------------------------------------------------------------
# 4. send_command success
# ---------------------------------------------------------------------------


async def test_send_command_success(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
    mock_writer: MagicMock,
) -> None:
    """send_command() should encode the command, write it, and parse the response."""
    response_payload = {"status": "ok", "result": {"node_id": 42}}
    response_bytes = json.dumps(response_payload).encode("utf-8") + b"\n"
    mock_reader.read = AsyncMock(return_value=response_bytes)

    result = await connected_connection.send_command("create_node", {"type": "noise"})

    # Verify the written payload.
    expected_message = json.dumps({"type": "create_node", "params": {"type": "noise"}}) + "\n"
    mock_writer.write.assert_called_once_with(expected_message.encode("utf-8"))
    mock_writer.drain.assert_awaited_once()

    # Verify the returned value is the "result" field.
    assert result == {"node_id": 42}


async def test_send_command_no_params(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
    mock_writer: MagicMock,
) -> None:
    """send_command() without params should omit 'params' key in payload."""
    response_payload = {"status": "ok", "result": {"nodes": []}}
    response_bytes = json.dumps(response_payload).encode("utf-8") + b"\n"
    mock_reader.read = AsyncMock(return_value=response_bytes)

    await connected_connection.send_command("list_nodes")

    expected_message = json.dumps({"type": "list_nodes"}) + "\n"
    mock_writer.write.assert_called_once_with(expected_message.encode("utf-8"))


# ---------------------------------------------------------------------------
# 5. send_command timeout
# ---------------------------------------------------------------------------


async def test_send_command_timeout(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """send_command() should raise TimeoutError when response takes too long."""

    async def stall_forever(*_args, **_kwargs):
        await asyncio.sleep(9999)

    mock_reader.read = stall_forever

    with patch(
        "material_maker_mcp.connection.asyncio.wait_for",
        new_callable=AsyncMock,
        side_effect=asyncio.TimeoutError,
    ):
        with pytest.raises(TimeoutError, match="Timed out waiting for response"):
            await connected_connection.send_command("ping")


# ---------------------------------------------------------------------------
# 6. send_command connection lost (write phase)
# ---------------------------------------------------------------------------


async def test_send_command_connection_lost_on_write(
    connected_connection: MaterialMakerConnection,
    mock_writer: MagicMock,
) -> None:
    """send_command() should raise ConnectionError when write fails."""
    mock_writer.write.side_effect = ConnectionResetError("reset")

    with pytest.raises(ConnectionError, match="Lost connection to Material Maker"):
        await connected_connection.send_command("ping")

    # Reader and writer should be cleared after connection loss.
    assert connected_connection._reader is None
    assert connected_connection._writer is None


async def test_send_command_connection_lost_on_drain(
    connected_connection: MaterialMakerConnection,
    mock_writer: MagicMock,
) -> None:
    """send_command() should raise ConnectionError when drain fails."""
    mock_writer.drain = AsyncMock(side_effect=BrokenPipeError("pipe"))

    with pytest.raises(ConnectionError, match="Lost connection to Material Maker"):
        await connected_connection.send_command("ping")

    assert connected_connection._reader is None
    assert connected_connection._writer is None


# ---------------------------------------------------------------------------
# 7. send_command error response
# ---------------------------------------------------------------------------


async def test_send_command_error_response(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """send_command() should raise RuntimeError on an error status response."""
    error_response = {"status": "error", "message": "Node not found"}
    response_bytes = json.dumps(error_response).encode("utf-8") + b"\n"
    mock_reader.read = AsyncMock(return_value=response_bytes)

    with pytest.raises(RuntimeError, match="Material Maker error: Node not found"):
        await connected_connection.send_command("delete_node", {"id": 999})


async def test_send_command_error_response_no_message(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """send_command() should use 'Unknown error' when error response has no message."""
    error_response = {"status": "error"}
    response_bytes = json.dumps(error_response).encode("utf-8") + b"\n"
    mock_reader.read = AsyncMock(return_value=response_bytes)

    with pytest.raises(RuntimeError, match="Unknown error"):
        await connected_connection.send_command("bad_command")


# ---------------------------------------------------------------------------
# 8. send_command invalid JSON response
# ---------------------------------------------------------------------------


async def test_send_command_invalid_json(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """send_command() should raise RuntimeError on malformed JSON."""
    mock_reader.read = AsyncMock(return_value=b"this is not json\n")

    with pytest.raises(RuntimeError, match="Invalid JSON response from Material Maker"):
        await connected_connection.send_command("ping")


# ---------------------------------------------------------------------------
# 9. Partial read buffering
# ---------------------------------------------------------------------------


async def test_partial_read_buffering(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """_read_line() should assemble a complete line from multiple read() chunks."""
    full_response = json.dumps({"status": "ok", "result": {"value": 123}})
    encoded = full_response.encode("utf-8") + b"\n"
    # Split the payload in the middle.
    mid = len(encoded) // 2
    chunk1 = encoded[:mid]
    chunk2 = encoded[mid:]

    mock_reader.read = AsyncMock(side_effect=[chunk1, chunk2])

    result = await connected_connection.send_command("get_value")

    assert result == {"value": 123}
    assert mock_reader.read.call_count == 2


async def test_buffer_carries_over(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """Data after the first newline should stay in the buffer for the next read."""
    first_response = json.dumps({"status": "ok", "result": {"a": 1}})
    second_response = json.dumps({"status": "ok", "result": {"b": 2}})
    # Deliver both responses in a single chunk.
    combined = (first_response + "\n" + second_response + "\n").encode("utf-8")
    mock_reader.read = AsyncMock(return_value=combined)

    result1 = await connected_connection.send_command("cmd1")
    assert result1 == {"a": 1}

    result2 = await connected_connection.send_command("cmd2")
    assert result2 == {"b": 2}


async def test_remote_close_during_read(
    connected_connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
) -> None:
    """_read_line() should raise ConnectionError when the remote side closes."""
    mock_reader.read = AsyncMock(return_value=b"")

    with pytest.raises(ConnectionError, match="Material Maker closed the connection"):
        await connected_connection.send_command("ping")


# ---------------------------------------------------------------------------
# 10. close()
# ---------------------------------------------------------------------------


async def test_close(
    connected_connection: MaterialMakerConnection,
    mock_writer: MagicMock,
) -> None:
    """close() should call writer.close() and wait_closed(), then clear state."""
    await connected_connection.close()

    mock_writer.close.assert_called_once()
    mock_writer.wait_closed.assert_awaited_once()
    assert connected_connection._reader is None
    assert connected_connection._writer is None
    assert connected_connection._buffer == b""


# ---------------------------------------------------------------------------
# 11. close() when not connected
# ---------------------------------------------------------------------------


async def test_close_when_not_connected(
    connection: MaterialMakerConnection,
) -> None:
    """close() should not raise when there is no active connection."""
    await connection.close()  # Should complete without error.
    assert connection._reader is None
    assert connection._writer is None


# ---------------------------------------------------------------------------
# 12. send_command when not connected
# ---------------------------------------------------------------------------


async def test_send_command_not_connected(
    connection: MaterialMakerConnection,
) -> None:
    """send_command() should raise ConnectionError before any I/O."""
    with pytest.raises(ConnectionError, match="Not connected to Material Maker"):
        await connection.send_command("ping")
