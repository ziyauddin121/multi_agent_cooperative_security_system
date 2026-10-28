"""
MACSS — Single-Agent Baseline (Control Group)
============================================
Academic Comparison Baseline:
A monolithic, single-agent security engine that operates without inter-agent
cooperation, without a distributed blackboard, and without specialized forensic
cross-correlation.
"""
from __future__ import annotations

import asyncio
import time
from typing import Dict

from app.agents.base_agent import BaseAgent, run_agent
from app.config import settings
from app.logging_config import configure_logging
from app.schemas.messages import (
    SensorEvent,
    DecisionMessage,
    ActionMessage,
    ActionType,
    EventType,
    Severity,
)


class BaselineAgent(BaseAgent):
    """
    Monolithic Single-Agent Baseline.
    Processes events in isolation with fixed, rule-based heuristics.
    """

    def __init__(self):
        super().__init__("baseline-agent")
        self._last_action_time: Dict[str, float] = {}

    def _get_consumer_groups(self):
        return [
            (settings.stream_events, settings.group_baseline),
        ]

    async def setup(self) -> None:
        self.logger.info("baseline_agent_ready", mode="monolithic-single-agent")

    async def _handle_sensor_event(self, event: SensorEvent) -> None:
        target = event.target or "host-0"
        now = time.time()

        if now - self._last_action_time.get(target, 0.0) < 3.0:
            return

        selected_action = ActionType.NO_ACTION
        rationale = "Monolithic baseline rule match"
        severity = Severity.MEDIUM

        if event.event_type in (
            EventType.HIGH_TRAFFIC_RATE,
            EventType.CONNECTION_FLOOD,
            EventType.DDOS_SUSPECTED,
        ):
            selected_action = ActionType.RATE_LIMIT
            severity = Severity.HIGH
            rationale = "Volumetric traffic spike detected: Throttling interface."
        elif event.event_type in (
            EventType.FILE_MODIFICATION_SPIKE,
            EventType.FILE_RENAME_SPIKE,
            EventType.MASS_FILE_ACCESS,
            EventType.RANSOMWARE_SUSPECTED,
        ):
            selected_action = ActionType.ISOLATE_ENDPOINT
            severity = Severity.CRITICAL
            rationale = "File encryption event: Host isolation."
        elif event.event_type in (
            EventType.UNUSUAL_AUTH,
            EventType.NEW_REMOTE_CONNECTION,
            EventType.LATERAL_MOVEMENT_SUSPECTED,
            EventType.PRIVILEGE_ESCALATION,
        ):
            selected_action = ActionType.BLOCK_CONNECTION
            severity = Severity.HIGH
            rationale = "Unauthorized remote logon: Connection blocked."
        elif event.event_type == EventType.SCAN_DETECTED:
            selected_action = ActionType.BLOCK_SOURCE
            severity = Severity.MEDIUM
            rationale = "Port reconnaissance: Source IP blocked."

        if selected_action != ActionType.NO_ACTION:
            self._last_action_time[target] = now
            decision = DecisionMessage(
                agent_id=self.agent_id,
                incident_id=f"inc-base-{target}",
                selected_action=selected_action,
                severity=severity,
                confidence=0.75,
                reason=rationale,
                conflicting_recommendations=[],
                affected_hosts=[target],
                is_multi_agent=False,
            )
            await self.bb.publish_decision(decision)

            action_msg = ActionMessage(
                agent_id=self.agent_id,
                decision_id=decision.message_id,
                incident_id=decision.incident_id,
                action_type=selected_action,
                target_host=target,
                action_status="EXECUTED",
                simulation_note=f"Baseline monolithic containment on {target}",
            )
            await self.bb.publish_action(action_msg)
            self._alerts_published += 1

    async def process_loop(self) -> None:
        self.logger.info("baseline_agent_consuming", stream=settings.stream_events)

        while self._running:
            try:
                async for stream_id, event in self.bb.read_events(
                    group=settings.group_baseline,
                    consumer=f"{self.agent_id}-1",
                    block_ms=2000,
                ):
                    if not self._running:
                        break

                    try:
                        await self._handle_sensor_event(event)
                    except Exception as err:
                        self.logger.error("baseline_eval_error", error=str(err))
                    finally:
                        await self.bb.ack_event(stream_id, group=settings.group_baseline)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error("baseline_loop_error", error=str(exc))
                await asyncio.sleep(1)


if __name__ == "__main__":
    configure_logging()
    run_agent(BaselineAgent())
