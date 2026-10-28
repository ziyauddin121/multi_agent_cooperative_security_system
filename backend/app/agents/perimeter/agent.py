"""
MACSS — Perimeter Agent
======================
Monitors network-level sensor events from `security:events`.
Detects:
  - Volumetric DDoS & connection floods via sliding-window rate tracking
  - Port & network reconnaissance scanning
Publishes threat alerts to `security:alerts`.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple

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


class PerimeterAgent(BaseAgent):
    """
    Perimeter Defense Agent.
    Specializes in volumetric and scanning network threats.
    """

    def __init__(self):
        super().__init__("perimeter-agent")

        self._traffic_window_seconds = 10.0
        self._ip_packet_windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._target_traffic_windows: Dict[str, Deque[float]] = defaultdict(deque)
        self._port_scan_windows: Dict[str, Deque[Tuple[float, int]]] = defaultdict(deque)

        self.ddos_threshold_pps = 40.0
        self.port_scan_unique_ports = 8
        self._last_alert_timestamps: Dict[str, float] = {}
        self._alert_cooldown_seconds = 4.0

    def _get_consumer_groups(self):
        return [
            (settings.stream_events, settings.group_perimeter),
        ]

    async def setup(self) -> None:
        self.logger.info(
            "perimeter_agent_ready",
            ddos_threshold_pps=self.ddos_threshold_pps,
            port_scan_unique_ports=self.port_scan_unique_ports,
        )

    def _clean_old_windows(self, now: float) -> None:
        cutoff = now - self._traffic_window_seconds

        for ip in list(self._ip_packet_windows.keys()):
            dq = self._ip_packet_windows[ip]
            while dq and dq[0] < cutoff:
                dq.popleft()
            if not dq:
                del self._ip_packet_windows[ip]

        for target in list(self._target_traffic_windows.keys()):
            dq = self._target_traffic_windows[target]
            while dq and dq[0] < cutoff:
                dq.popleft()
            if not dq:
                del self._target_traffic_windows[target]

        for ip in list(self._port_scan_windows.keys()):
            dq = self._port_scan_windows[ip]
            while dq and dq[0][0] < cutoff:
                dq.popleft()
            if not dq:
                del self._port_scan_windows[ip]

    def _should_suppress_alert(self, key: str, now: float) -> bool:
        last_time = self._last_alert_timestamps.get(key, 0.0)
        if now - last_time < self._alert_cooldown_seconds:
            return True
        self._last_alert_timestamps[key] = now
        return False

    async def _handle_sensor_event(self, event: SensorEvent) -> None:
        now = time.time()
        self._clean_old_windows(now)

        src_ip = event.source
        dst_host = event.target or "network"
        dst_port = event.payload.get("dst_port") or event.payload.get("port")
        packet_count = float(event.payload.get("packet_count", 1))

        if src_ip:
            for _ in range(int(min(packet_count, 100))):
                self._ip_packet_windows[src_ip].append(now)

        if dst_host:
            for _ in range(int(min(packet_count, 100))):
                self._target_traffic_windows[dst_host].append(now)

        # ── 1. Check for DDoS Volumetric Flooding ────────────────────────
        target_q = self._target_traffic_windows[dst_host]
        target_rate = len(target_q) / max(self._traffic_window_seconds, 1.0)

        is_ddos_event = event.event_type in (
            EventType.HIGH_TRAFFIC_RATE,
            EventType.CONNECTION_FLOOD,
            EventType.DDOS_SUSPECTED,
        )

        if target_rate >= self.ddos_threshold_pps or is_ddos_event:
            suppress_key = f"ddos:{dst_host}"
            if not self._should_suppress_alert(suppress_key, now):
                severity = Severity.CRITICAL if target_rate >= 80 or is_ddos_event else Severity.HIGH
                alert = AlertMessage(
                    agent_id=self.agent_id,
                    event_type=EventType.DDOS_SUSPECTED,
                    severity=severity,
                    confidence=0.95 if is_ddos_event else 0.85,
                    source=src_ip or "multiple_botnet_nodes",
                    target=dst_host,
                    evidence={
                        "observed_rate_pps": round(target_rate, 2),
                        "threshold_pps": self.ddos_threshold_pps,
                        "attack_vector": event.event_type.value,
                    },
                    recommended_action=ActionType.RATE_LIMIT,
                    affected_hosts=[dst_host],
                )
                msg_id = await self.bb.publish_alert(alert)
                self._alerts_published += 1
                self.logger.info(
                    "ddos_alert_published",
                    alert_id=alert.message_id,
                    stream_id=msg_id,
                    target=dst_host,
                    rate=round(target_rate, 1),
                )

        # ── 2. Check for Port Scanning ──────────────────────────────────
        if src_ip and dst_port:
            try:
                dst_port_int = int(dst_port)
                self._port_scan_windows[src_ip].append((now, dst_port_int))
                unique_ports = {p for _, p in self._port_scan_windows[src_ip]}

                is_scan_event = event.event_type == EventType.SCAN_DETECTED

                if len(unique_ports) >= self.port_scan_unique_ports or is_scan_event:
                    suppress_key = f"scan:{src_ip}"
                    if not self._should_suppress_alert(suppress_key, now):
                        alert = AlertMessage(
                            agent_id=self.agent_id,
                            event_type=EventType.SCAN_DETECTED,
                            severity=Severity.MEDIUM,
                            confidence=0.92,
                            source=src_ip,
                            target=dst_host,
                            evidence={
                                "source_ip": src_ip,
                                "probed_ports_count": len(unique_ports),
                                "probed_ports_sample": list(unique_ports)[:10],
                            },
                            recommended_action=ActionType.BLOCK_SOURCE,
                            affected_hosts=[dst_host],
                        )
                        msg_id = await self.bb.publish_alert(alert)
                        self._alerts_published += 1
                        self.logger.info(
                            "port_scan_alert_published",
                            alert_id=alert.message_id,
                            stream_id=msg_id,
                            src_ip=src_ip,
                            ports=len(unique_ports),
                        )
            except (ValueError, TypeError):
                pass

    async def process_loop(self) -> None:
        self.logger.info("perimeter_agent_consuming", stream=settings.stream_events)

        while self._running:
            try:
                async for stream_id, event in self.bb.read_events(
                    group=settings.group_perimeter,
                    consumer=f"{self.agent_id}-1",
                    block_ms=2000,
                ):
                    if not self._running:
                        break

                    try:
                        await self._handle_sensor_event(event)
                    except Exception as err:
                        self.logger.error("perimeter_event_eval_error", error=str(err))
                    finally:
                        await self.bb.ack_event(stream_id, group=settings.group_perimeter)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("perimeter_loop_error", error=str(exc))
                await asyncio.sleep(1)


if __name__ == "__main__":
    configure_logging()
    run_agent(PerimeterAgent())
