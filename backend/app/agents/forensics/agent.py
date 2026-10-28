"""
MACSS — Forensics Agent
=======================
Consumes alerts from `security:alerts`.
Performs:
  - Multi-source alert aggregation and chronological timeline reconstruction
  - Cross-agent correlation (Perimeter + Endpoint)
  - Multi-stage attack chain detection
Publishes structured evidence packages to `security:evidence`.
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Set

from app.agents.base_agent import BaseAgent, run_agent
from app.config import settings
from app.logging_config import configure_logging
from app.schemas.messages import (
    AlertMessage,
    EvidenceMessage,
    EventType,
    Severity,
    ActionType,
)


class ForensicsAgent(BaseAgent):
    """
    Forensics Investigation Agent.
    Synthesizes discrete alerts into cohesive multi-stage incident evidence.
    """

    def __init__(self):
        super().__init__("forensics-agent")
        self._alert_buffer: List[tuple[float, AlertMessage]] = []
        self._correlation_window_seconds = 30.0
        self._host_alerts: Dict[str, List[AlertMessage]] = defaultdict(list)
        self._processed_campaign_keys: Set[str] = set()

    def _get_consumer_groups(self):
        return [
            (settings.stream_alerts, settings.group_forensics),
        ]

    async def setup(self) -> None:
        self.logger.info("forensics_agent_ready", window_seconds=self._correlation_window_seconds)

    def _prune_buffer(self, now: float) -> None:
        cutoff = now - self._correlation_window_seconds
        self._alert_buffer = [(ts, a) for ts, a in self._alert_buffer if ts >= cutoff]

    async def _correlate_and_synthesize(self, new_alert: AlertMessage) -> None:
        now = time.time()
        self._prune_buffer(now)

        self._alert_buffer.append((now, new_alert))
        if new_alert.target:
            self._host_alerts[new_alert.target].append(new_alert)

        recent_alerts = [a for _, a in self._alert_buffer]

        has_ddos = any("ddos" in a.event_type.value.lower() or "flood" in a.event_type.value.lower() for a in recent_alerts)
        has_ransomware = any(a.event_type in (EventType.RANSOMWARE_SUSPECTED, EventType.FILE_RENAME_SPIKE) for a in recent_alerts)
        has_lateral = any("lateral" in a.event_type.value.lower() for a in recent_alerts)
        has_scan = any(a.event_type == EventType.SCAN_DETECTED for a in recent_alerts)

        affected_hosts = list({a.target for a in recent_alerts if a.target})
        alert_ids = [a.message_id for a in recent_alerts]

        # ── Pattern 1: Mixed Campaign (DDoS + Ransomware / Lateral) ────
        if has_ddos and (has_ransomware or has_lateral):
            campaign_key = f"mixed_ddos_ransomware_{len(affected_hosts)}"
            if campaign_key not in self._processed_campaign_keys:
                self._processed_campaign_keys.add(campaign_key)

                timeline = [
                    {
                        "timestamp": a.timestamp.isoformat(),
                        "agent": a.agent_id,
                        "type": a.event_type.value,
                        "host": a.target,
                        "severity": a.severity.value,
                    }
                    for a in recent_alerts
                ]

                evidence = EvidenceMessage(
                    agent_id=self.agent_id,
                    incident_id=f"inc-mixed-{new_alert.target or 'enterprise'}",
                    attack_type=EventType.RANSOMWARE_SUSPECTED,
                    severity=Severity.CRITICAL,
                    confidence=0.98,
                    affected_hosts=affected_hosts,
                    evidence_count=len(alert_ids),
                    correlated_alert_ids=alert_ids,
                    timeline=timeline,
                    recommended_action=ActionType.ISOLATE_ENDPOINT,
                    evidence={
                        "campaign_type": "Mixed Multi-Stage Attack",
                        "primary_threat": "Ransomware with volumetric perimeter distraction",
                        "diversion_detected": True,
                    },
                )
                msg_id = await self.bb.publish_evidence(evidence)
                self.logger.info(
                    "mixed_campaign_evidence_published",
                    evidence_id=evidence.message_id,
                    stream_id=msg_id,
                    confidence=evidence.confidence,
                )
                return

        # ── Pattern 2: Multi-Host Lateral Infiltration ─────────────────
        if has_lateral and len(affected_hosts) >= 2:
            campaign_key = f"lateral_expansion_{len(affected_hosts)}"
            if campaign_key not in self._processed_campaign_keys:
                self._processed_campaign_keys.add(campaign_key)

                evidence = EvidenceMessage(
                    agent_id=self.agent_id,
                    incident_id=f"inc-lateral-{new_alert.target or 'enterprise'}",
                    attack_type=EventType.LATERAL_MOVEMENT_SUSPECTED,
                    severity=Severity.HIGH,
                    confidence=0.94,
                    affected_hosts=affected_hosts,
                    evidence_count=len(alert_ids),
                    correlated_alert_ids=alert_ids,
                    timeline=[{"agent": a.agent_id, "host": a.target} for a in recent_alerts],
                    recommended_action=ActionType.BLOCK_CONNECTION,
                    evidence={
                        "campaign_type": "Lateral Movement & Expansion",
                        "blast_radius_risk": "HIGH",
                    },
                )
                msg_id = await self.bb.publish_evidence(evidence)
                self.logger.info(
                    "lateral_evidence_published",
                    evidence_id=evidence.message_id,
                    stream_id=msg_id,
                    affected=len(affected_hosts),
                )
                return

        # ── Pattern 3: Recon to Attack Transition ──────────────────────
        if has_scan and (has_ddos or has_lateral):
            campaign_key = f"scan_to_attack_{len(affected_hosts)}"
            if campaign_key not in self._processed_campaign_keys:
                self._processed_campaign_keys.add(campaign_key)

                evidence = EvidenceMessage(
                    agent_id=self.agent_id,
                    incident_id=f"inc-recon-{new_alert.target or 'gateway'}",
                    attack_type=EventType.SCAN_DETECTED,
                    severity=Severity.HIGH,
                    confidence=0.91,
                    affected_hosts=affected_hosts,
                    evidence_count=len(alert_ids),
                    correlated_alert_ids=alert_ids,
                    timeline=[{"agent": a.agent_id, "host": a.target} for a in recent_alerts],
                    recommended_action=ActionType.BLOCK_SOURCE,
                    evidence={
                        "campaign_type": "Recon to Exploitation Chain",
                    },
                )
                msg_id = await self.bb.publish_evidence(evidence)
                self.logger.info("recon_evidence_published", evidence_id=evidence.message_id, stream_id=msg_id)

    async def process_loop(self) -> None:
        self.logger.info("forensics_agent_consuming", stream=settings.stream_alerts)

        while self._running:
            try:
                async for stream_id, alert in self.bb.read_alerts(
                    group=settings.group_forensics,
                    consumer=f"{self.agent_id}-1",
                    block_ms=2000,
                ):
                    if not self._running:
                        break

                    try:
                        await self._correlate_and_synthesize(alert)
                    except Exception as err:
                        self.logger.error("forensics_eval_error", error=str(err))
                    finally:
                        await self.bb.ack_alert(stream_id, group=settings.group_forensics)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("forensics_loop_error", error=str(exc))
                await asyncio.sleep(1)


if __name__ == "__main__":
    configure_logging()
    run_agent(ForensicsAgent())
