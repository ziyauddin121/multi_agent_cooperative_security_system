"""
MACSS — Coordinator Agent & Conflict Resolution Engine
======================================================
Consumes from:
  - `security:alerts`
  - `security:evidence`

Core responsibilities:
  1. Conflict Detection:
     Detects when multiple agents recommend differing containment actions
     for overlapping hosts/targets (e.g., Perimeter recommends BLOCK_SOURCE
     vs Endpoint recommends ISOLATE_ENDPOINT).
  2. Multi-Criteria Conflict Resolution Scoring:
     Score = (Severity_Weight * 0.40) + (Confidence * 0.30)
             + (Containment_Efficacy * 0.20) - (Disruption_Cost * 0.10)
  3. Executive Decision Making:
     Selects the optimal containment policy, documents the rationale and
     all evaluated options in a DecisionMessage.
  4. Action Dispatch:
     Publishes actionable execution orders to `security:actions`.
"""
from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional

from app.agents.base_agent import BaseAgent, run_agent
from app.config import settings
from app.logging_config import configure_logging
from app.schemas.messages import (
    AlertMessage,
    EvidenceMessage,
    DecisionMessage,
    ActionMessage,
    ConflictEntry,
    ActionType,
    Severity,
)

# ── Multi-Criteria Decision Weights ──────────────────────────────────────────
SEVERITY_WEIGHTS = {
    Severity.CRITICAL: 1.00,
    Severity.HIGH:     0.75,
    Severity.MEDIUM:   0.50,
    Severity.LOW:      0.25,
}

# Containment efficacy in preventing lateral spread or destructive payload
ACTION_EFFICACY = {
    ActionType.ISOLATE_ENDPOINT:  1.00,
    ActionType.QUARANTINE_HOST:   0.90,
    ActionType.BLOCK_CONNECTION:  0.80,
    ActionType.BLOCK_SOURCE:      0.75,
    ActionType.RATE_LIMIT:        0.50,
    ActionType.INVESTIGATE:       0.30,
    ActionType.NOTIFY_ADMIN:      0.20,
    ActionType.NO_ACTION:         0.00,
}

# Operational disruption cost (penalty) to business availability
ACTION_DISRUPTION_PENALTY = {
    ActionType.ISOLATE_ENDPOINT:  0.35,  # high impact: host taken offline
    ActionType.QUARANTINE_HOST:   0.30,  # high impact: subnet quarantined
    ActionType.BLOCK_CONNECTION:  0.20,  # moderate: active session killed
    ActionType.BLOCK_SOURCE:      0.15,  # moderate-low: source IP dropped
    ActionType.RATE_LIMIT:        0.05,  # very low: traffic throttled
    ActionType.INVESTIGATE:       0.05,
    ActionType.NOTIFY_ADMIN:      0.00,
    ActionType.NO_ACTION:         0.00,
}


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent.
    Arbitrates conflicting agent proposals and executes authoritative containment decisions.
    """

    def __init__(self):
        super().__init__("coordinator-agent")
        self._pending_recommendations: Dict[str, List[dict]] = {}
        self._decision_cooldown: Dict[str, float] = {}
        self._cooldown_seconds = 4.0

    def _get_consumer_groups(self):
        return [
            (settings.stream_alerts,   settings.group_coordinator),
            (settings.stream_evidence, settings.group_coordinator),
        ]

    async def setup(self) -> None:
        self.logger.info("coordinator_agent_ready", mode="multi-criteria-conflict-resolution")

    def _compute_action_score(
        self,
        action: ActionType,
        severity: Severity,
        confidence: float,
    ) -> float:
        sev_w = SEVERITY_WEIGHTS.get(severity, 0.50)
        eff_w = ACTION_EFFICACY.get(action, 0.50)
        dis_p = ACTION_DISRUPTION_PENALTY.get(action, 0.10)

        score = (sev_w * 0.40) + (confidence * 0.30) + (eff_w * 0.20) - (dis_p * 0.10)
        return max(0.0, min(1.0, score))

    async def _resolve_and_decide(
        self,
        target_host: str,
        candidates: List[dict],
        context_evidence: Optional[EvidenceMessage] = None,
    ) -> None:
        now = time.time()
        last_decision = self._decision_cooldown.get(target_host, 0.0)
        if now - last_decision < self._cooldown_seconds:
            return
        self._decision_cooldown[target_host] = now

        scored_options = {}
        for c in candidates:
            act = c["action"]
            sev = c.get("severity", Severity.HIGH)
            conf = c.get("confidence", 0.85)

            if context_evidence and context_evidence.attack_type in (
                "DDoS_Diversionary_Ransomware_Campaign",
                "Coordinated_Lateral_Movement",
            ):
                if act == ActionType.ISOLATE_ENDPOINT:
                    conf = min(1.0, conf + 0.15)

            score = self._compute_action_score(act, sev, conf)
            scored_options[act.value] = round(score, 4)

        best_candidate = max(
            candidates,
            key=lambda c: scored_options[c["action"].value]
        )
        selected_action = best_candidate["action"]

        unique_actions = {c["action"] for c in candidates}
        had_conflict = len(unique_actions) > 1

        rationale = (
            f"Multi-agent conflict resolved. Evaluated {len(candidates)} proposals. "
            f"Selected {selected_action.value} with utility score {scored_options[selected_action.value]}. "
            f"Conflict present: {had_conflict}."
        )

        decision = DecisionMessage(
            agent_id=self.agent_id,
            incident_id=f"inc-{target_host}",
            selected_action=selected_action,
            severity=best_candidate.get("severity", Severity.HIGH),
            confidence=round(scored_options[selected_action.value], 4),
            reason=rationale,
            conflicting_recommendations=[
                ConflictEntry(
                    agent_id=c["agent"],
                    recommended_action=c["action"],
                    severity=c.get("severity", Severity.HIGH),
                    confidence=c.get("confidence", 0.85),
                    weight=scored_options.get(c["action"].value, 0.0),
                )
                for c in candidates
            ],
            affected_hosts=[target_host],
            is_multi_agent=True,
        )

        msg_id = await self.bb.publish_decision(decision)
        self.logger.info(
            "decision_published",
            decision_id=decision.message_id,
            stream_id=msg_id,
            target=target_host,
            action=selected_action.value,
            conflict=had_conflict,
        )

        action_msg = ActionMessage(
            agent_id=self.agent_id,
            decision_id=decision.message_id,
            incident_id=decision.incident_id,
            action_type=selected_action,
            target_host=target_host,
            action_status="EXECUTED",
            simulation_note=f"Simulated {selected_action.value} applied to {target_host}",
        )
        action_id = await self.bb.publish_action(action_msg)
        self.logger.info(
            "containment_action_dispatched",
            action_id=action_id,
            target=target_host,
            action=selected_action.value,
        )

    async def _handle_alert(self, alert: AlertMessage) -> None:
        target = alert.target or "global_network"
        candidate = {
            "agent": alert.agent_id,
            "action": alert.recommended_action,
            "severity": alert.severity,
            "confidence": alert.confidence,
        }

        if target not in self._pending_recommendations:
            self._pending_recommendations[target] = []
        self._pending_recommendations[target].append(candidate)

        await self._resolve_and_decide(target, self._pending_recommendations[target])

    async def _handle_evidence(self, evidence: EvidenceMessage) -> None:
        target = evidence.affected_hosts[0] if evidence.affected_hosts else "global_network"
        candidate = {
            "agent": evidence.agent_id,
            "action": evidence.recommended_action,
            "severity": evidence.severity,
            "confidence": evidence.confidence,
        }

        candidates = self._pending_recommendations.get(target, []) + [candidate]
        await self._resolve_and_decide(target, candidates, context_evidence=evidence)

    async def process_loop(self) -> None:
        self.logger.info("coordinator_consuming_streams")

        async def _consume_alerts():
            while self._running:
                try:
                    async for stream_id, alert in self.bb.read_alerts(
                        group=settings.group_coordinator,
                        consumer=f"{self.agent_id}-alerts",
                        block_ms=2000,
                    ):
                        if not self._running:
                            break
                        try:
                            await self._handle_alert(alert)
                        except Exception as err:
                            self.logger.error("coord_alert_eval_error", error=str(err))
                        finally:
                            await self.bb.ack_alert(stream_id, group=settings.group_coordinator)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    self.logger.error("coord_alert_loop_error", error=str(exc))
                    await asyncio.sleep(1)

        async def _consume_evidence():
            while self._running:
                try:
                    async for stream_id, evidence in self.bb.read_evidence(
                        group=settings.group_coordinator,
                        consumer=f"{self.agent_id}-evidence",
                        block_ms=2000,
                    ):
                        if not self._running:
                            break
                        try:
                            await self._handle_evidence(evidence)
                        except Exception as err:
                            self.logger.error("coord_evidence_eval_error", error=str(err))
                        finally:
                            await self.bb.ack_evidence(stream_id, group=settings.group_coordinator)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    self.logger.error("coord_evidence_loop_error", error=str(exc))
                    await asyncio.sleep(1)

        try:
            await asyncio.gather(_consume_alerts(), _consume_evidence())
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    configure_logging()
    run_agent(CoordinatorAgent())
