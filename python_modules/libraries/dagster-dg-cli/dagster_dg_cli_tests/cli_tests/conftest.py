from contextlib import asynccontextmanager
from typing import Iterator
import pytest
import rich

# Prevent rich from thinking it's in a legacy Windows terminal, which can cause problems matching
# test output in CI.
rich.reconfigure(legacy_windows=False)


@pytest.fixture(autouse=True)
def clear_defined_commands():
    """Reset the _commands_defined flag on scaffold_group between tests,
    to ensure the cache of scaffold subcommands is cleared. This isn't an issue outside
    of tests because we're not reusing a Python process between different dg venvs.
    """
    from dagster_dg_cli.cli.scaffold import scaffold_defs_group

    scaffold_defs_group._commands_defined = False  # noqa: SLF001  # type: ignore


try:
    import mcp

    mcp_exists = True
except ImportError:
    mcp_exists = False

if mcp_exists:
    import asyncio
    import sys
    from contextlib import asynccontextmanager
    from typing import Tuple, Callable

    import mcp.client.stdio as _mcp_stdio

    _original_stdio_client = _mcp_stdio.stdio_client  # keep a reference

    # Helper: forward every line from a StreamReader to stderr so pytest captures it
    async def _dump_stream(prefix: str, stream: asyncio.StreamReader) -> None:
        try:
            async for line in stream:
                sys.stderr.write(f"{prefix}{line.decode(errors='replace')}")
        except asyncio.CancelledError:
            pass


    @asynccontextmanager
    async def _verbose_stdio_client(params) -> Iterator[Tuple[asyncio.StreamReader, Callable[[bytes], None]]]:
        """
        Wrap the real stdio_client:
          * start background tasks that drain both stdout and stderr
          * yield the same (reader, writer) tuple the real context manager yields
        """
        async with _original_stdio_client(params) as (reader, writer):
            # The original context manager attaches .process to itself so we can
            # reach the child; if that ever changes you can inspect dir(reader)
            # once to find the right attribute name.
            proc = _verbose_stdio_client.process  # type: ignore[attr-defined]

            # Start background readers; they keep the OS pipes empty.
            stdout_drain = asyncio.create_task(_dump_stream("[MCP-stdout] ", reader))

            # Windows dead-locks most often on *stderr*, so make sure we drain that
            # one too.  If the real stdio_client used stderr=STDOUT you won’t
            # reach this branch, which is still fine.
            if proc.stderr is not None:
                stderr_reader = asyncio.StreamReader()
                stderr_protocol = asyncio.StreamReaderProtocol(stderr_reader)
                await asyncio.get_running_loop().connect_read_pipe(
                    lambda: stderr_protocol, proc.stderr
                )
                stderr_drain = asyncio.create_task(_dump_stream("[MCP-stderr] ", stderr_reader))
            else:
                stderr_drain = None

            try:
                yield reader, writer
            finally:
                stdout_drain.cancel()
                if stderr_drain:
                    stderr_drain.cancel()

    # Monkey-patch for the duration of the test session
    _mcp_stdio.stdio_client = _verbose_stdio_client
