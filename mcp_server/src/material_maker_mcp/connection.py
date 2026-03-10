"""Async TCP client for communicating with the Material Maker GDScript plugin."""

from __future__ import annotations

import asyncio
import json


class MaterialMakerConnection:
    """Manages a TCP connection to the Material Maker MCP plugin.

    Sends newline-delimited JSON commands and reads newline-delimited JSON
    responses over a persistent TCP socket.
    """

    def __init__(self, host: str = "localhost", port: int = 9002) -> None:
        self.host = host
        self.port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._buffer: bytes = b""

    async def connect(self) -> None:
        """Connect to Material Maker with exponential backoff retry.

        Retries up to 5 times, starting with a 1-second delay and doubling
        each attempt. Raises ConnectionError on final failure.
        """
        max_attempts = 5
        delay = 1.0

        for attempt in range(1, max_attempts + 1):
            try:
                self._reader, self._writer = await asyncio.open_connection(self.host, self.port)
                self._buffer = b""
                return
            except (ConnectionRefusedError, OSError, TimeoutError):
                if attempt == max_attempts:
                    raise ConnectionError(
                        "Could not connect to Material Maker. "
                        "Make sure Material Maker is running and the MCP plugin is enabled."
                    )
                await asyncio.sleep(delay)
                delay *= 2

    async def send_command(self, command_type: str, params: dict | None = None) -> dict:
        """Send a command to Material Maker and return the parsed response.

        Args:
            command_type: The command type string (e.g. "create_node").
            params: Optional dict of parameters for the command.

        Returns:
            The parsed JSON response dict.

        Raises:
            ConnectionError: If not connected or connection is lost.
            TimeoutError: If no response is received within 30 seconds.
            RuntimeError: If the server returns an error status.
        """
        if self._writer is None or self._reader is None:
            raise ConnectionError("Not connected to Material Maker. Call connect() first.")

        message: dict = {"type": command_type}
        if params is not None:
            message["params"] = params

        payload = json.dumps(message) + "\n"

        try:
            self._writer.write(payload.encode("utf-8"))
            await self._writer.drain()
        except (ConnectionResetError, BrokenPipeError, OSError) as exc:
            self._writer = None
            self._reader = None
            self._buffer = b""
            raise ConnectionError(f"Lost connection to Material Maker: {exc}") from exc

        # Read response with 30-second timeout, buffering until newline.
        try:
            response_data = await asyncio.wait_for(self._read_line(), timeout=30.0)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(
                f"Timed out waiting for response to '{command_type}' command."
            ) from exc
        except (ConnectionResetError, BrokenPipeError, OSError) as exc:
            self._writer = None
            self._reader = None
            self._buffer = b""
            raise ConnectionError(f"Lost connection to Material Maker: {exc}") from exc

        try:
            result = json.loads(response_data)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Invalid JSON response from Material Maker: {response_data!r}"
            ) from exc

        if result.get("status") == "error":
            raise RuntimeError(f"Material Maker error: {result.get('message', 'Unknown error')}")

        return result.get("result", result)

    async def _read_line(self) -> str:
        """Read from the stream until a newline delimiter is found.

        Handles partial reads by accumulating data in an internal buffer.
        """
        if self._reader is None:
            raise ConnectionError("Not connected to Material Maker.")

        while True:
            # Check if we already have a complete line in the buffer.
            newline_pos = self._buffer.find(b"\n")
            if newline_pos != -1:
                line = self._buffer[:newline_pos]
                self._buffer = self._buffer[newline_pos + 1 :]
                return line.decode("utf-8")

            chunk = await self._reader.read(65536)
            if not chunk:
                # Connection closed by remote side.
                raise ConnectionError("Material Maker closed the connection.")
            self._buffer += chunk

    async def close(self) -> None:
        """Cleanly shut down the TCP connection."""
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass  # Already closed or broken — nothing to do.
            finally:
                self._writer = None
                self._reader = None
                self._buffer = b""
