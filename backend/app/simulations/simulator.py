"""
MACSS — Attack Simulator & Campaign Orchestrator
===============================================
Orchestrates realistic, multi-stage cyber attack scenarios:
  1. Mixed Campaign (DDoS + Ransomware + Lateral Movement)
  2. Volumetric Flooding
  3. Ransomware Outbreak
  4. Internal Lateral Movement
"""
from __future__ import annotations

import asyncio
import random
import time
from typing import Dict, Any

from app.blackboard import blackboard
from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.schemas.messages import SensorEvent, EventType

logger = get_logger("simulator")


class AttackCampaignOrchestrator:
    """Simulates realistic cyber attack campaigns by pushing events to Redis."""

    def __init__(self):
        self.running = False
        self.current_scenario = "none"
        self.events_emitted = 0
        self.start_time = 0.0

    async def emit_sensor_event(
        self,
        event_type: EventType,
        source_ip: str,
        target_host: str,
        payload: dict,
    ) -> str:
        """Helper to create and publish a SensorEvent."""
        event = SensorEvent(
            event_type=event_type,
            source=source_ip,
            target=target_host,
            payload=payload,
            simulation_phase="attack",
            is_attack=True,
        )
        msg_id = await blackboard.publish_event(event)
        self.events_emitted += 1
        return msg_id

    async def run_mixed_campaign(self, intensity: str = "high") -> None:
        """
        Mixed Campaign:
        Stage 1 (0-3s): Reconnaissance Port Scan
        Stage 2 (3-8s): Volumetric DDoS Flooding (Perimeter Distraction)
        Stage 3 (8-14s): Covert Ransomware Encryption on Internal DB Server
        Stage 4 (14-20s): Lateral Movement to Active Directory / Domain Controller
        """
        self.running = True
        self.current_scenario = "mixed_campaign"
        self.events_emitted = 0
        self.start_time = time.time()

        logger.info("mixed_campaign_started", intensity=intensity)
        await blackboard.set_simulation_state({
            "active": True,
            "scenario": "mixed_campaign",
            "stage": "Stage 1: Reconnaissance Port Scanning",
            "progress_percent": 15,
            "events_emitted": 0,
            "start_time": self.start_time,
        })

        # ── Stage 1: Reconnaissance ──────────────────────────────────────
        logger.info("simulating_stage_1_recon")
        attacker_ip = "198.51.100.42"
        target_web = "srv-web-01"

        for port in [21, 22, 25, 80, 443, 8080, 3306, 3389, 5432, 8443]:
            await self.emit_sensor_event(
                event_type=EventType.SCAN_DETECTED,
                source_ip=attacker_ip,
                target_host=target_web,
                payload={"dst_port": port, "tcp_flags": "SYN", "scan_type": "stealth_syn"},
            )
            await asyncio.sleep(0.12)

        # ── Stage 2: Volumetric DDoS Distraction ─────────────────────────
        logger.info("simulating_stage_2_ddos_flood")
        await blackboard.set_simulation_state({
            "active": True,
            "scenario": "mixed_campaign",
            "stage": "Stage 2: Volumetric DDoS Distraction (HTTP + SYN Flood)",
            "progress_percent": 40,
            "events_emitted": self.events_emitted,
            "start_time": self.start_time,
        })

        botnet_ips = [f"203.0.113.{i}" for i in range(10, 40)]
        for _ in range(40):
            bot_ip = random.choice(botnet_ips)
            await self.emit_sensor_event(
                event_type=EventType.CONNECTION_FLOOD,
                source_ip=bot_ip,
                target_host=target_web,
                payload={"packet_count": 65, "pps": 650, "dst_port": 80},
            )
            await asyncio.sleep(0.06)

        # ── Stage 3: Covert Ransomware Encryption ─────────────────────────
        logger.info("simulating_stage_3_ransomware")
        target_db = "db-prod-01"
        await blackboard.set_simulation_state({
            "active": True,
            "scenario": "mixed_campaign",
            "stage": "Stage 3: Ransomware Infiltration & Shadow Copy Deletion",
            "progress_percent": 70,
            "events_emitted": self.events_emitted,
            "start_time": self.start_time,
        })

        await self.emit_sensor_event(
            event_type=EventType.SUSPICIOUS_PROCESS,
            source_ip="10.0.0.15",
            target_host=target_db,
            payload={
                "command_line": "vssadmin delete shadows /all /quiet",
                "process_name": "cmd.exe",
                "shadow_copy_deleted": True,
            },
        )
        await asyncio.sleep(0.4)

        critical_files = [
            "/var/lib/postgresql/data/base_01.dat.locked",
            "/srv/backups/corporate_finance_2026.xlsx.locked",
            "/srv/backups/client_contracts.tar.gz.locked",
        ]
        for fpath in critical_files:
            await self.emit_sensor_event(
                event_type=EventType.RANSOMWARE_SUSPECTED,
                source_ip="10.0.0.15",
                target_host=target_db,
                payload={
                    "file_path": fpath,
                    "files_affected": 20,
                    "process_name": "encrypter.bin",
                },
            )
            await asyncio.sleep(0.3)

        # ── Stage 4: Lateral Movement ────────────────────────────────────
        logger.info("simulating_stage_4_lateral_movement")
        target_dc = "dc-core-01"
        await blackboard.set_simulation_state({
            "active": True,
            "scenario": "mixed_campaign",
            "stage": "Stage 4: Lateral Movement to Domain Controller",
            "progress_percent": 90,
            "events_emitted": self.events_emitted,
            "start_time": self.start_time,
        })

        for peer in ["srv-app-02", "srv-app-03", target_dc]:
            await self.emit_sensor_event(
                event_type=EventType.LATERAL_MOVEMENT_SUSPECTED,
                source_ip="10.0.0.15",
                target_host=peer,
                payload={
                    "origin_host": target_db,
                    "destination_host": peer,
                    "auth_protocol": "smb",
                    "admin_share": "ADMIN$",
                },
            )
            await asyncio.sleep(0.4)

        # ── Campaign Completion ──────────────────────────────────────────
        total_time = round(time.time() - self.start_time, 2)
        await blackboard.set_simulation_state({
            "active": False,
            "scenario": "mixed_campaign",
            "stage": f"Completed ({total_time}s, {self.events_emitted} events)",
            "progress_percent": 100,
            "events_emitted": self.events_emitted,
            "start_time": self.start_time,
        })
        self.running = False
        logger.info("mixed_campaign_completed", total_time=total_time, events=self.events_emitted)


orchestrator = AttackCampaignOrchestrator()


async def main():
    configure_logging()
    logger.info("simulator_service_started")

    await blackboard.connect()

    await blackboard.set_simulation_state({
        "active": False,
        "scenario": "none",
        "stage": "Ready for experiment trigger",
        "progress_percent": 0,
        "events_emitted": 0,
        "start_time": 0.0,
    })

    while True:
        try:
            state = await blackboard.get_simulation_state()
            if state.get("trigger_requested") in (True, "true", "True", 1, "1"):
                scenario = state.get("scenario", "mixed_campaign")
                intensity = state.get("intensity", "high")
                await blackboard.set_simulation_state({"trigger_requested": False})
                if scenario == "mixed_campaign":
                    await orchestrator.run_mixed_campaign(intensity=intensity)
            await asyncio.sleep(1.0)
        except Exception as exc:
            logger.error("simulator_loop_error", error=str(exc))
            await asyncio.sleep(2.0)


if __name__ == "__main__":
    asyncio.run(main())
