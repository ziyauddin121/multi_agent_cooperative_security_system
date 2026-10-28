"""
MACSS — Redis Blackboard
========================
Central shared memory for all agents.
Provides a clean async API over Redis Streams + Redis Hashes.

Usage:
    bb = Blackboard()
    await bb.connect()

    # Publish an alert
    msg_id = await bb.publish_alert(alert_message)

    # Consume events (blocking, for agent loops)
    async for stream_id, event in bb.read_events(group="perimeter_group", consumer="perimeter-1"):
        ...
        await bb.ack_event(stream_id)
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional

import orjson
import redis.asyncio as aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logging_config import get_logger
from app.schemas.messages import (
    AlertMessage, EvidenceMessage, DecisionMessage,
    ActionMessage, VerificationMessage, HeartbeatMessage,
    SensorEvent, BaseMessage,
)

logger = get_logger("blackboard")

# Maximum number of entries to keep per stream (auto-trim)
STREAM_MAX_LEN = 10_000


class Blackboard:
    """
    Async Redis client that wraps all blackboard operations.

    Each agent creates ONE instance of Blackboard and reuses it.
    All methods are async and safe to use in asyncio event loops.
    """

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
        self._connected = False

    # ── Connection ───────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def connect(self) -> None:
        """Connect to Redis. Retries up to 10 times with backoff."""
        password = settings.redis_password or None
        self._client = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=password,
            decode_responses=False,   # we handle encoding ourselves
            max_connections=20,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
        await self._client.ping()
        self._connected = True
        logger.info("blackboard_connected",
                    host=settings.redis_host,
                    port=settings.redis_port)

    async def disconnect(self) -> None:
        if self._client:
            await self._client.aclose()
            self._connected = False
            logger.info("blackboard_disconnected")

    @property
    def client(self) -> aioredis.Redis:
        if not self._client or not self._connected:
            raise RuntimeError("Blackboard not connected. Call await bb.connect() first.")
        return self._client

    # ── Stream Helpers ───────────────────────────────────────────

    async def _publish(self, stream: str, data: dict) -> str:
        """Publish a dict to a Redis Stream, returning the entry ID."""
        # Convert all values to bytes/str
        encoded = {
            (k.encode() if isinstance(k, str) else k):
            (orjson.dumps(v) if not isinstance(v, (str, bytes)) else
             v.encode() if isinstance(v, str) else v)
            for k, v in data.items()
        }
        entry_id = await self.client.xadd(
            stream, encoded, maxlen=STREAM_MAX_LEN, approximate=True
        )
        return entry_id.decode()

    async def ensure_consumer_group(self, stream: str, group: str) -> None:
        """Create stream + consumer group if they don't exist (idempotent)."""
        try:
            await self.client.xgroup_create(
                stream, group, id="0", mkstream=True
            )
            logger.info("consumer_group_created", stream=stream, group=group)
        except aioredis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                pass  # already exists — fine
            else:
                raise

    # ── Publish Methods ──────────────────────────────────────────

    async def publish_event(self, event: SensorEvent) -> str:
        """Simulator publishes raw sensor events here."""
        entry_id = await self._publish(
            settings.stream_events, event.to_redis_dict()
        )
        logger.debug("event_published", event_id=event.event_id,
                     event_type=event.event_type, stream_entry=entry_id)
        return entry_id

    async def publish_alert(self, alert: AlertMessage) -> str:
        """Agents publish threat alerts here."""
        entry_id = await self._publish(
            settings.stream_alerts, alert.to_redis_dict()
        )
        logger.info("alert_published", alert_id=alert.message_id,
                    agent=alert.agent_id, severity=alert.severity,
                    event_type=alert.event_type)
        return entry_id

    async def publish_evidence(self, evidence: EvidenceMessage) -> str:
        """Forensics agent publishes corroborated evidence here."""
        entry_id = await self._publish(
            settings.stream_evidence, evidence.to_redis_dict()
        )
        logger.info("evidence_published", evidence_id=evidence.message_id,
                    incident_id=evidence.incident_id,
                    confidence=evidence.confidence)
        return entry_id

    async def publish_decision(self, decision: DecisionMessage) -> str:
        """Coordinator publishes its final decision here."""
        entry_id = await self._publish(
            settings.stream_decisions, decision.to_redis_dict()
        )
        logger.info("decision_published", decision_id=decision.message_id,
                    action=decision.selected_action,
                    reason=decision.reason)
        return entry_id

    async def publish_action(self, action: ActionMessage) -> str:
        """Records that a simulated containment action was executed."""
        entry_id = await self._publish(
            settings.stream_actions, action.to_redis_dict()
        )
        logger.info("action_published", action_id=action.message_id,
                    action_type=action.action_type, target=action.target_host)
        return entry_id

    async def publish_verification(self, result: VerificationMessage) -> str:
        """Publishes the outcome of a post-action verification check."""
        entry_id = await self._publish(
            settings.stream_verification, result.to_redis_dict()
        )
        logger.info("verification_published",
                    verification_id=result.message_id,
                    result=result.result)
        return entry_id

    async def publish_heartbeat(self, hb: HeartbeatMessage) -> str:
        """Agent liveness heartbeat."""
        entry_id = await self._publish(
            settings.stream_metrics, hb.to_redis_dict()
        )
        return entry_id

    # ── Read Methods ─────────────────────────────────────────────

    async def read_stream(
        self,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 1000,
    ) -> list[tuple[str, dict]]:
        """
        Read new messages from a stream using a consumer group.
        Returns list of (stream_entry_id, field_dict) tuples.
        block_ms: how long to block waiting for new messages (0 = forever).
        """
        try:
            results = await self.client.xreadgroup(
                groupname=group,
                consumername=consumer,
                streams={stream: ">"},  # ">" = only undelivered messages
                count=count,
                block=block_ms,
            )
        except aioredis.ResponseError as e:
            if "NOGROUP" in str(e):
                await self.ensure_consumer_group(stream, group)
                return []
            raise
        entries = []
        if results:
            for _stream, messages in results:
                for entry_id, fields in messages:
                    eid = entry_id.decode() if isinstance(entry_id, bytes) else entry_id
                    # Decode fields
                    decoded = {}
                    for k, v in fields.items():
                        key = k.decode() if isinstance(k, bytes) else k
                        val = v.decode() if isinstance(v, bytes) else v
                        try:
                            decoded[key] = orjson.loads(val)
                        except Exception:
                            decoded[key] = val
                    entries.append((eid, decoded))
        return entries

    async def ack(self, stream: str, group: str, entry_id: str) -> None:
        """Acknowledge a message so it won't be redelivered."""
        await self.client.xack(stream, group, entry_id)

    async def read_events(
        self, group: str, consumer: str, count: int = 10, block_ms: int = 1000
    ) -> AsyncIterator[tuple[str, SensorEvent]]:
        entries = await self.read_stream(settings.stream_events, group, consumer, count, block_ms)
        for entry_id, fields in entries:
            try:
                yield entry_id, SensorEvent.from_redis_dict(fields)
            except Exception as e:
                logger.warning("event_deserialize_error", entry_id=entry_id, error=str(e))

    async def read_alerts(
        self, group: str, consumer: str, count: int = 10, block_ms: int = 1000
    ) -> AsyncIterator[tuple[str, AlertMessage]]:
        entries = await self.read_stream(settings.stream_alerts, group, consumer, count, block_ms)
        for entry_id, fields in entries:
            try:
                yield entry_id, AlertMessage.from_redis_dict(fields)
            except Exception as e:
                logger.warning("alert_deserialize_error", entry_id=entry_id, error=str(e))

    async def read_evidence(
        self, group: str, consumer: str, count: int = 10, block_ms: int = 1000
    ) -> AsyncIterator[tuple[str, EvidenceMessage]]:
        entries = await self.read_stream(settings.stream_evidence, group, consumer, count, block_ms)
        for entry_id, fields in entries:
            try:
                yield entry_id, EvidenceMessage.from_redis_dict(fields)
            except Exception as e:
                logger.warning("evidence_deserialize_error", entry_id=entry_id, error=str(e))

    async def read_decisions(
        self, group: str, consumer: str, count: int = 10, block_ms: int = 1000
    ) -> AsyncIterator[tuple[str, DecisionMessage]]:
        entries = await self.read_stream(settings.stream_decisions, group, consumer, count, block_ms)
        for entry_id, fields in entries:
            try:
                yield entry_id, DecisionMessage.from_redis_dict(fields)
            except Exception as e:
                logger.warning("decision_deserialize_error", entry_id=entry_id, error=str(e))

    async def ack_event(self, entry_id: str, group: str) -> None:
        await self.ack(settings.stream_events, group, entry_id)

    async def ack_alert(self, entry_id: str, group: str) -> None:
        await self.ack(settings.stream_alerts, group, entry_id)

    async def ack_evidence(self, entry_id: str, group: str) -> None:
        await self.ack(settings.stream_evidence, group, entry_id)

    async def ack_decision(self, entry_id: str, group: str) -> None:
        await self.ack(settings.stream_decisions, group, entry_id)

    async def read_events_raw(
        self, group: str, consumer: str, count: int = 20, block_ms: int = 1000
    ) -> list[tuple[str, dict]]:
        return await self.read_stream(
            settings.stream_events, group, consumer, count, block_ms
        )

    async def read_alerts_raw(
        self, group: str, consumer: str, count: int = 20, block_ms: int = 1000
    ) -> list[tuple[str, dict]]:
        return await self.read_stream(
            settings.stream_alerts, group, consumer, count, block_ms
        )

    async def read_evidence_raw(
        self, group: str, consumer: str, count: int = 20, block_ms: int = 1000
    ) -> list[tuple[str, dict]]:
        return await self.read_stream(
            settings.stream_evidence, group, consumer, count, block_ms
        )

    async def read_decisions_raw(
        self, group: str, consumer: str, count: int = 20, block_ms: int = 1000
    ) -> list[tuple[str, dict]]:
        return await self.read_stream(
            settings.stream_decisions, group, consumer, count, block_ms
        )

    # ── Hash State ───────────────────────────────────────────────

    async def set_agent_status(self, agent_id: str, status: dict) -> None:
        """Update an agent's status hash (last-seen, alert count, etc.)."""
        key = f"agent:{agent_id}:status"
        await self.client.hset(key, mapping={
            k: orjson.dumps(v).decode() if not isinstance(v, str) else v
            for k, v in status.items()
        })
        await self.client.expire(key, 60)  # expire after 60 s of no updates

    async def get_agent_status(self, agent_id: str) -> dict:
        """Read an agent's current status from the hash."""
        key = f"agent:{agent_id}:status"
        raw = await self.client.hgetall(key)
        decoded = {}
        for k, v in raw.items():
            key_str = k.decode() if isinstance(k, bytes) else k
            val_str = v.decode() if isinstance(v, bytes) else v
            try:
                decoded[key_str] = orjson.loads(val_str)
            except Exception:
                decoded[key_str] = val_str
        return decoded

    async def get_all_agent_statuses(self) -> dict[str, dict]:
        """Return status of all known agents."""
        agent_ids = [
            "perimeter-agent", "endpoint-agent",
            "forensics-agent", "coordinator-agent", "baseline-agent"
        ]
        result = {}
        for aid in agent_ids:
            result[aid] = await self.get_agent_status(aid)
        return result

    async def set_simulation_state(self, state: dict) -> None:
        """Update the current simulation state hash."""
        key = settings.hash_simulation
        await self.client.hset(key, mapping={
            k: orjson.dumps(v).decode() if not isinstance(v, str) else v
            for k, v in state.items()
        })

    async def get_simulation_state(self) -> dict:
        """Read current simulation state."""
        key = settings.hash_simulation
        raw = await self.client.hgetall(key)
        decoded = {}
        for k, v in raw.items():
            key_str = k.decode() if isinstance(k, bytes) else k
            val_str = v.decode() if isinstance(v, bytes) else v
            try:
                decoded[key_str] = orjson.loads(val_str)
            except Exception:
                decoded[key_str] = val_str
        return decoded

    async def set_incident(self, incident_id: str, data: dict) -> None:
        """Store / update an incident hash."""
        key = f"incident:{incident_id}"
        await self.client.hset(key, mapping={
            k: orjson.dumps(v).decode() if not isinstance(v, str) else v
            for k, v in data.items()
        })

    async def get_incident(self, incident_id: str) -> dict:
        """Read an incident hash."""
        key = f"incident:{incident_id}"
        raw = await self.client.hgetall(key)
        decoded = {}
        for k, v in raw.items():
            key_str = k.decode() if isinstance(k, bytes) else k
            val_str = v.decode() if isinstance(v, bytes) else v
            try:
                decoded[key_str] = orjson.loads(val_str)
            except Exception:
                decoded[key_str] = val_str
        return decoded

    # ── Stream Inspection ────────────────────────────────────────

    async def stream_length(self, stream: str) -> int:
        return await self.client.xlen(stream)

    async def read_stream_range(
        self, stream: str, count: int = 100, reverse: bool = True
    ) -> list[dict]:
        """Read recent entries from a stream (for API / dashboard)."""
        if reverse:
            raw = await self.client.xrevrange(stream, count=count)
        else:
            raw = await self.client.xrange(stream, count=count)

        entries = []
        for entry_id, fields in raw:
            eid = entry_id.decode() if isinstance(entry_id, bytes) else entry_id
            decoded = {"_stream_id": eid}
            for k, v in fields.items():
                key_str = k.decode() if isinstance(k, bytes) else k
                val_str = v.decode() if isinstance(v, bytes) else v
                try:
                    decoded[key_str] = orjson.loads(val_str)
                except Exception:
                    decoded[key_str] = val_str
            entries.append(decoded)
        return entries

    async def flush_all_streams(self) -> None:
        """Delete all security streams (used for experiment reset)."""
        streams = [
            settings.stream_events, settings.stream_alerts,
            settings.stream_evidence, settings.stream_decisions,
            settings.stream_actions, settings.stream_verification,
            settings.stream_metrics,
        ]
        for s in streams:
            await self.client.delete(s)
        # Clear simulation state
        await self.client.delete(settings.hash_simulation)

        # Re-ensure consumer groups so listening agents continue uninterrupted
        groups = [
            (settings.stream_events, settings.group_perimeter),
            (settings.stream_events, settings.group_endpoint),
            (settings.stream_events, settings.group_baseline),
            (settings.stream_alerts, settings.group_forensics),
            (settings.stream_alerts, settings.group_coordinator),
            (settings.stream_evidence, settings.group_coordinator),
            (settings.stream_actions, "verifier_group"),
        ]
        for s, g in groups:
            await self.ensure_consumer_group(s, g)

        logger.info("blackboard_flushed")

    async def health_check(self) -> bool:
        """Return True if Redis is reachable."""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False


# ── Module-level singleton ────────────────────────────────────
# Import this in agents/API to get the shared blackboard instance.
blackboard = Blackboard()
