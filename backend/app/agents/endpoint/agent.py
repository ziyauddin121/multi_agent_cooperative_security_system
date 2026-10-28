"""
MACSS — Endpoint Agent
=====================
Monitors host-level sensor events from `security:events`.
Detects:
  - Ransomware activity (rapid file renames, mass file access, backup tampering)
  - Lateral movement (unusual auth, new remote connections across internal peers)
Publishes threat alerts to `security:alerts`.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Deque

from app.agents.base_agent import BaseAgent, run_agent
from app.config import settings
from app.logging_config import configure_logging
from app.schemas.messages import (
    AlertMessage,
    EventType,
    Severity,
    ActionType,
    SensorEvent,
)

SUSPICIOUS_EXTENSIONS = {
    ".locked", ".crypto", ".enc", ".encrypted", ".wnry",
    ".locky", ".cerber", ".ryuk", ".cui", ".darkside",
}

SHADOW_COPY_COMMANDS = {
    "vssadmin delete shadows",
    "wmic shadowcopy delete",
    "bcdedit /set {default} bootstatuspolicy ignoreallfailures",
    "bcdedit /set {default} recoveryenabled no",
    "wbadmin delete catalog -quiet",
}


class EndpointAgent(BaseAgent):
    """
    Endpoint Security Agent.
    Specializes in host-level behavioral telemetry and host-containment recommendations.
    """

    def __init__(self):
        super().__init__("endpoint-agent")

        self._host_file_writes: Dict[str, Deque[float]] = defaultdict(deque)
        self._host_lateral_probes: Dict[str, Deque[tuple[float, str]]] = defaultdict(deque)

        self._window_seconds = 10.0
        self.ransomware_file_rate_threshold = 15.0
        self.lateral_peer_threshold = 3
        self._alert_cooldown: Dict[str, float] = {}
        self._cooldown_seconds = 4.0

    def _get_consumer_groups(self):
        return [
            (settings.stream_events, settings.group_endpoint),
        ]

    async def setup(self) -> None:
        self.logger.info(
            "endpoint_agent_ready",
            ransomware_file_rate_threshold=self.ransomware_file_rate_threshold,
            lateral_peer_threshold=self.lateral_peer_threshold,
        )

    def _clean_windows(self, now: float) -> None:
        cutoff = now - self._window_seconds

        for host in list(self._host_file_writes.keys()):
            dq = self._host_file_writes[host]
            while dq and dq[0] < cutoff:
                dq.popleft()
            if not dq:
                del self._host_file_writes[host]

        for host in list(self._host_lateral_probes.keys()):
            dq = self._host_lateral_probes[host]
            while dq and dq[0][0] < cutoff:
                dq.popleft()
            if not dq:
                del self._host_lateral_probes[host]

    def _should_suppress(self, key: str, now: float) -> bool:
        last = self._alert_cooldown.get(key, 0.0)
        if now - last < self._cooldown_seconds:
            return True
        self._alert_cooldown[key] = now
        return False

    async def _handle_sensor_event(self, event: SensorEvent) -> None:
        now = time.time()
        self._clean_windows(now)

        host = event.target or event.source or "unknown_endpoint"
        payload = event.payload or {}
        event_type = event.event_type

        # ── 1. Check for Ransomware File Activity ──────────────────────
        is_file_event = event_type in (
            EventType.FILE_MODIFICATION_SPIKE,
            EventType.FILE_RENAME_SPIKE,
            EventType.MASS_FILE_ACCESS,
            EventType.RANSOMWARE_SUSPECTED,
        ) or "file_path" in payload
        file_path = str(payload.get("file_path", "")).lower()
        file_count = int(payload.get("files_affected", 1))

        if is_file_event:
            for _ in range(file_count):
                self._host_file_writes[host].append(now)

            has_suspicious_ext = any(file_path.endswith(ext) for ext in SUSPICIOUS_EXTENSIONS)
            recent_ops = len(self._host_file_writes[host])

            if (
                event_type == EventType.RANSOMWARE_SUSPECTED
                or has_suspicious_ext
                or recent_ops >= self.ransomware_file_rate_threshold
            ):
                suppress_key = f"ransomware:{host}"
                if not self._should_suppress(suppress_key, now):
                    confidence = 0.98 if (has_suspicious_ext or event_type == EventType.RANSOMWARE_SUSPECTED) else 0.88
                    alert = AlertMessage(
                        agent_id=self.agent_id,
                        event_type=EventType.RANSOMWARE_SUSPECTED,
                        severity=Severity.CRITICAL,
                        confidence=confidence,
                        source=event.source or host,
                        target=host,
                        evidence={
                            "rapid_file_operations": recent_ops,
                            "suspicious_extension": has_suspicious_ext,
                            "sample_file": file_path or "bulk_encrypted_files",
                            "process_name": payload.get("process_name", "unknown_encrypter.exe"),
                        },
                        recommended_action=ActionType.ISOLATE_ENDPOINT,
                        affected_hosts=[host],
                    )
                    msg_id = await self.bb.publish_alert(alert)
                    self._alerts_published += 1
                    self.logger.info(
                        "ransomware_alert_published",
                        alert_id=alert.message_id,
                        stream_id=msg_id,
                        host=host,
                        recent_ops=recent_ops,
                    )

        # ── 2. Check for Shadow Copy Deletion ──────────────────────────
        process_cmd = str(payload.get("command_line", "")).lower()
        if any(cmd in process_cmd for cmd in SHADOW_COPY_COMMANDS) or payload.get("shadow_copy_deleted"):
            suppress_key = f"shadow:{host}"
            if not self._should_suppress(suppress_key, now):
                alert = AlertMessage(
                    agent_id=self.agent_id,
                    event_type=EventType.SUSPICIOUS_PROCESS,
                    severity=Severity.HIGH,
                    confidence=0.96,
                    source=event.source or host,
                    target=host,
                    evidence={
                        "executed_command": process_cmd,
                        "backup_tampering": True,
                    },
                    recommended_action=ActionType.BLOCK_CONNECTION,
                    affected_hosts=[host],
                )
                msg_id = await self.bb.publish_alert(alert)
                self._alerts_published += 1
                self.logger.info("shadow_copy_deletion_alert", alert_id=alert.message_id, host=host)

        # ── 3. Check for Lateral Movement ──────────────────────────────
        target_peer = payload.get("destination_host") or payload.get("target_ip")
        is_lateral_event = event_type in (
            EventType.UNUSUAL_AUTH,
            EventType.NEW_REMOTE_CONNECTION,
            EventType.LATERAL_MOVEMENT_SUSPECTED,
            EventType.PRIVILEGE_ESCALATION,
        )

        if is_lateral_event and target_peer:
            self._host_lateral_probes[host].append((now, str(target_peer)))
            unique_peers = {peer for _, peer in self._host_lateral_probes[host]}

            if len(unique_peers) >= self.lateral_peer_threshold or is_lateral_event:
                suppress_key = f"lateral:{host}"
                if not self._should_suppress(suppress_key, now):
                    alert = AlertMessage(
                        agent_id=self.agent_id,
                        event_type=EventType.LATERAL_MOVEMENT_SUSPECTED,
                        severity=Severity.HIGH,
                        confidence=0.91,
                        source=host,
                        target=str(target_peer),
                        evidence={
                            "origin_host": host,
                            "targeted_peers": list(unique_peers)[:5],
                            "peer_count": len(unique_peers),
                            "protocol": payload.get("auth_protocol", "smb/ssh"),
                        },
                        recommended_action=ActionType.BLOCK_CONNECTION,
                        affected_hosts=[host, str(target_peer)],
                    )
                    msg_id = await self.bb.publish_alert(alert)
                    self._alerts_published += 1
                    self.logger.info(
                        "lateral_movement_alert_published",
                        alert_id=alert.message_id,
                        stream_id=msg_id,
                        origin=host,
                        peers=len(unique_peers),
                    )

    async def process_loop(self) -> None:
        self.logger.info("endpoint_agent_consuming", stream=settings.stream_events)

        while self._running:
            try:
                async for stream_id, event in self.bb.read_events(
                    group=settings.group_endpoint,
                    consumer=f"{self.agent_id}-1",
                    block_ms=2000,
                ):
                    if not self._running:
                        break

                    try:
                        await self._handle_sensor_event(event)
                    except Exception as err:
                        self.logger.error("endpoint_event_eval_error", error=str(err))
                    finally:
                        await self.bb.ack_event(stream_id, group=settings.group_endpoint)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("endpoint_loop_error", error=str(exc))
                await asyncio.sleep(1)


if __name__ == "__main__":
    configure_logging()
    run_agent(EndpointAgent())
