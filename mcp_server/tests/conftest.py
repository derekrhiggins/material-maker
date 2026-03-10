"""Shared fixtures for Material Maker MCP tests."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from material_maker_mcp.connection import MaterialMakerConnection


@pytest.fixture
def mock_reader() -> AsyncMock:
    """Return a mock asyncio.StreamReader."""
    reader = AsyncMock(spec=asyncio.StreamReader)
    return reader


@pytest.fixture
def mock_writer() -> MagicMock:
    """Return a mock asyncio.StreamWriter with async close helpers."""
    writer = MagicMock(spec=asyncio.StreamWriter)
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.fixture
def connection() -> MaterialMakerConnection:
    """Return a fresh, unconnected MaterialMakerConnection."""
    return MaterialMakerConnection(host="localhost", port=9002)


@pytest.fixture
def connected_connection(
    connection: MaterialMakerConnection,
    mock_reader: AsyncMock,
    mock_writer: MagicMock,
) -> MaterialMakerConnection:
    """Return a MaterialMakerConnection with mocked reader/writer already set."""
    connection._reader = mock_reader
    connection._writer = mock_writer
    connection._buffer = b""
    return connection
