"""
MACSS — Database Persistence Service (PostgreSQL)
=================================================
Asynchronously persists Redis stream telemetry (events, alerts, decisions,
actions, verification results, and experiment metrics) to PostgreSQL.
"""
from __future__ import annotations

import asyncio
from typing import Optional, List, Dict, Any
import asyncpg
import orjson

from app.config import settings
from app.logging_config import get_logger

logger = get_logger("database")


class DatabaseService:
    """Async PostgreSQL service using connection pooling."""

    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Initialize asyncpg connection pool."""
        try:
            self._pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_db,
                min_size=2,
                max_size=10,
                timeout=10.0,
            )
            logger.info("postgres_connected", host=settings.postgres_host, db=settings.postgres_db)
        except Exception as exc:
            logger.warning("postgres_connect_deferred", error=str(exc))

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            logger.info("postgres_disconnected")

    async def save_alert(
        self,
        alert_id: str,
        agent_id: str,
        alert_type: str,
        severity: str,
        confidence: float,
        recommended_action: str,
        evidence: dict,
        incident_id: Optional[str] = None,
    ) -> None:
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO alerts (alert_id, agent_id, alert_type, severity, confidence, recommended_action, evidence, incident_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
                    ON CONFLICT (alert_id) DO NOTHING
                    """,
                    alert_id, agent_id, alert_type, severity, confidence,
                    recommended_action, orjson.dumps(evidence).decode(), incident_id
                )
        except Exception as exc:
            logger.warning("db_save_alert_error", error=str(exc))

    async def save_decision(
        self,
        decision_id: str,
        incident_id: str,
        selected_action: str,
        reason: str,
        confidence: float,
        conflicting_actions: List[dict],
        is_multi_agent: bool = True,
    ) -> None:
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                # Ensure incident exists
                await conn.execute(
                    """
                    INSERT INTO incidents (incident_id, attack_type, severity, confidence, affected_hosts, status)
                    VALUES ($1, 'CORRELATED_ATTACK', 'HIGH', $2, '["network"]'::jsonb, 'CONTAINED')
                    ON CONFLICT (incident_id) DO NOTHING
                    """,
                    incident_id, confidence
                )

                await conn.execute(
                    """
                    INSERT INTO decisions (decision_id, incident_id, selected_action, resolution_reason, confidence, conflicting_actions, is_multi_agent)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
                    ON CONFLICT (decision_id) DO NOTHING
                    """,
                    decision_id, incident_id, selected_action, reason, confidence,
                    orjson.dumps(conflicting_actions).decode(), is_multi_agent
                )
        except Exception as exc:
            logger.warning("db_save_decision_error", error=str(exc))

    async def save_action(
        self,
        action_id: str,
        decision_id: str,
        action_type: str,
        target_host: str,
        status: str = "EXECUTED",
    ) -> None:
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO actions (action_id, decision_id, action_type, target_host, status)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (action_id) DO NOTHING
                    """,
                    action_id, decision_id, action_type, target_host, status
                )
        except Exception as exc:
            logger.warning("db_save_action_error", error=str(exc))

    async def save_verification(
        self,
        verification_id: str,
        action_id: str,
        result: str,
        checks: dict,
        notes: str = "",
    ) -> None:
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO verification_results (verification_id, action_id, result, checks, notes)
                    VALUES ($1, $2, $3, $4::jsonb, $5)
                    ON CONFLICT (verification_id) DO NOTHING
                    """,
                    verification_id, action_id, result, orjson.dumps(checks).decode(), notes
                )
        except Exception as exc:
            logger.warning("db_save_verification_error", error=str(exc))

    async def save_experiment_metrics(
        self,
        experiment_id: str,
        detection_time_ms: float,
        containment_time_ms: float,
        blast_radius: int,
        decision_consistency: float,
        total_alerts: int,
        conflicting_decisions: int,
    ) -> None:
        if not self._pool:
            return
        try:
            async with self._pool.acquire() as conn:
                # Insert or get experiment row
                row = await conn.fetchrow(
                    """
                    INSERT INTO experiments (experiment_id, name, status)
                    VALUES ($1, $1, 'COMPLETED')
                    ON CONFLICT (experiment_id) DO UPDATE SET status = 'COMPLETED'
                    RETURNING id
                    """,
                    experiment_id
                )
                exp_pk = row["id"]

                await conn.execute(
                    """
                    INSERT INTO metrics (experiment_id, detection_time_ms, containment_time_ms, blast_radius, decision_consistency, total_alerts, conflicting_decisions)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    exp_pk, detection_time_ms, containment_time_ms, blast_radius,
                    decision_consistency, total_alerts, conflicting_decisions
                )
        except Exception as exc:
            logger.warning("db_save_metrics_error", error=str(exc))

    async def get_history(self) -> Dict[str, Any]:
        """Fetch historical counts and latest records from PostgreSQL."""
        if not self._pool:
            return {"connected": False, "alerts": 0, "decisions": 0, "actions": 0}
        try:
            async with self._pool.acquire() as conn:
                alerts_cnt = await conn.fetchval("SELECT COUNT(*) FROM alerts")
                decisions_cnt = await conn.fetchval("SELECT COUNT(*) FROM decisions")
                actions_cnt = await conn.fetchval("SELECT COUNT(*) FROM actions")
                latest_decisions = await conn.fetch(
                    "SELECT decision_id, selected_action, resolution_reason, created_at FROM decisions ORDER BY id DESC LIMIT 5"
                )
                return {
                    "connected": True,
                    "total_saved_alerts": alerts_cnt,
                    "total_saved_decisions": decisions_cnt,
                    "total_saved_actions": actions_cnt,
                    "recent_decisions": [dict(r) for r in latest_decisions],
                }
        except Exception as exc:
            return {"connected": False, "error": str(exc)}


db_service = DatabaseService()
