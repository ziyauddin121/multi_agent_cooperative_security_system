"""
MACSS — Base Agent
==================
All four agents (Perimeter, Endpoint, Forensics, Coordinator)
and the Baseline agent inherit from BaseAgent.

Provides:
  - Redis blackboard connection
  - Consumer group setup
  - Heartbeat loop
  - Graceful shutdown
  - Structured logging
"""
from __future__ import annotations

import asyncio
import signal
import time
from abc import ABC, abstractmethod
from typing import Optional

from app.blackboard import Blackboard
from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.schemas.messages import HeartbeatMessage


class BaseAgent(ABC):
    """
    Abstract base class for every MACSS agent.

    Subclass and implement:
        async def setup(self) -> None          — one-time setup
        async def process_loop(self) -> None   — main agent loop
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.bb = Blackboard()
        self.logger = get_logger(agent_id)
        self._running = False
        self._start_time: float = 0.0
        self._alerts_published: int = 0
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None

    # ── Lifecycle ────────────────────────────────────────────────

    async def start(self) -> None:
        """Connect, setup, then run the agent loops."""
        configure_logging()
        self.logger.info("agent_starting", agent_id=self.agent_id)

        # Connect to Redis with retry
        await self.bb.connect()
        await self._create_consumer_groups()

        # Agent-specific one-time setup
        await self.setup()

        self._running = True
        self._start_time = time.monotonic()

        # Update status
        await self._update_status("running")

        # Launch the heartbeat + processing loops concurrently
        self._heartbeat_task = asyncio.create_task(
            self._heartbeat_loop(), name=f"{self.agent_id}-heartbeat"
        )
        self._process_task = asyncio.create_task(
            self.process_loop(), name=f"{self.agent_id}-process"
        )

        self.logger.info("agent_started", agent_id=self.agent_id)

        try:
            await asyncio.gather(self._heartbeat_task, self._process_task)
        except asyncio.CancelledError:
            self.logger.info("agent_cancelled", agent_id=self.agent_id)
        except Exception as exc:
            self.logger.error("agent_error", agent_id=self.agent_id, error=str(exc))
            raise

    async def stop(self) -> None:
        """Gracefully shut down the agent."""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._process_task:
            self._process_task.cancel()
        await self._update_status("stopped")
        await self.bb.disconnect()
        self.logger.info("agent_stopped", agent_id=self.agent_id)

    # ── Abstract Interface ────────────────────────────────────────

    @abstractmethod
    async def setup(self) -> None:
        """One-time initialization (consumer groups, DB connections, etc.)."""

    @abstractmethod
    async def process_loop(self) -> None:
        """Main agent loop — reads from blackboard, processes, publishes."""

    # ── Consumer Groups ───────────────────────────────────────────

    async def _create_consumer_groups(self) -> None:
        """Create all consumer groups this agent needs."""
        for stream, group in self._get_consumer_groups():
            await self.bb.ensure_consumer_group(stream, group)

    def _get_consumer_groups(self) -> list[tuple[str, str]]:
        """
        Override in subclasses to declare which streams + groups this agent uses.
        Returns list of (stream_key, group_name) tuples.
        """
        return []

    # ── Heartbeat ─────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Publish a liveness heartbeat every N seconds."""
        while self._running:
            try:
                uptime = time.monotonic() - self._start_time
                hb = HeartbeatMessage(
                    agent_id=self.agent_id,
                    status="running",
                    alerts_published=self._alerts_published,
                    uptime_seconds=round(uptime, 1),
                )
                await self.bb.publish_heartbeat(hb)
                await self._update_status("running")
            except Exception as exc:
                self.logger.warning("heartbeat_error", error=str(exc))
            await asyncio.sleep(settings.agent_heartbeat_interval)

    async def _update_status(self, status: str) -> None:
        """Push current agent status to the blackboard hash."""
        try:
            uptime = round(time.monotonic() - self._start_time, 1) \
                if self._start_time else 0.0
            await self.bb.set_agent_status(self.agent_id, {
                "agent_id": self.agent_id,
                "status": status,
                "last_seen": str(time.time()),
                "alerts_published": self._alerts_published,
                "uptime_seconds": uptime,
            })
        except Exception as exc:
            self.logger.warning("status_update_error", error=str(exc))


def run_agent(agent: BaseAgent) -> None:
    """
    Entry-point helper — sets up signal handlers and runs the agent.
    Call from __main__ in each agent module:

        if __name__ == "__main__":
            run_agent(PerimeterAgent())
    """
    loop = asyncio.get_event_loop()

    def _shutdown(sig_name):
        configure_logging()
        log = get_logger("run_agent")
        log.info("shutdown_signal_received", signal=sig_name)
        asyncio.ensure_future(agent.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown, sig.name)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler for all signals
            pass

    try:
        loop.run_until_complete(agent.start())
    finally:
        loop.close()
