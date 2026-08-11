from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


def _enabled() -> bool:
    return os.getenv("FABERAI_MOLDSIM_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _startup_timeout_seconds() -> float:
    try:
        return max(float(os.getenv("FABERAI_MOLDSIM_STARTUP_TIMEOUT_SECONDS", "15")), 0.1)
    except ValueError:
        return 15.0


class MoldSimMCP:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.tools: list[dict] = []
        self._ready = asyncio.Event()
        self._shutdown = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._failed = False

    async def _run(self):
        """Owns the whole MCP session lifetime in a single task —
        entering and exiting the stdio task group here, never across
        separate lifespan calls, avoids anyio's cross-task cancel-scope error."""
        try:
            params = StdioServerParameters(command="npx", args=["-y", "moldsim-mcp"])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    self.tools = [
                        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                        for t in result.tools
                    ]
                    self.session = session
                    logger.info("moldsim-mcp connected: %d tools", len(self.tools))
                    self._ready.set()

                    await self._shutdown.wait()  # keep session alive until told to stop
        except Exception as exc:
            if hasattr(exc, "exceptions"):  # ExceptionGroup / anyio wrapper
                for sub in exc.exceptions:
                    logger.warning("moldsim-mcp unavailable (sub-exception): %s", sub, exc_info=sub)
            else:
                logger.warning("moldsim-mcp unavailable: %s", exc, exc_info=True)
            self._failed = True
            self._ready.set()  # unblock start() even on failure

    async def start(self):
        self._task = asyncio.create_task(self._run())
        try:
            await asyncio.wait_for(self._ready.wait(), timeout=_startup_timeout_seconds())
        except TimeoutError:
            logger.warning("moldsim-mcp did not become ready before the startup timeout")
            self._failed = True
            await self.stop()

    async def stop(self):
        self._shutdown.set()
        if self._task:
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=5)
            except TimeoutError:
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)

    @property
    def is_available(self) -> bool:
        return self.session is not None and not self._failed


_moldsim: Optional[MoldSimMCP] = None

def get_moldsim() -> Optional[MoldSimMCP]:
    return _moldsim

async def init_moldsim():
    global _moldsim
    if not _enabled():
        logger.info("moldsim-mcp disabled; set FABERAI_MOLDSIM_ENABLED=true to enable it")
        _moldsim = None
        return
    _moldsim = MoldSimMCP()
    await _moldsim.start()
    if _moldsim._failed:
        _moldsim = None

async def shutdown_moldsim():
    if _moldsim:
        await _moldsim.stop()
