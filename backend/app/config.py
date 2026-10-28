"""
MACSS — Application Settings
Loaded from environment variables / .env file.
All agents and the API import this module for shared config.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — reads from environment / .env"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Redis ────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # ── PostgreSQL ───────────────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "macss_db"
    postgres_user: str = "macss_user"
    postgres_password: str = "macss_pass"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── API ──────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # ── Agent ────────────────────────────────────────────────────
    agent_heartbeat_interval: int = 5       # seconds
    agent_poll_interval: float = 1.0        # seconds
    agent_max_retries: int = 3
    agent_name: str = "unknown-agent"       # overridden per container

    # ── Simulation ───────────────────────────────────────────────
    default_random_seed: int = 42
    simulation_speed_multiplier: float = 1.0

    # ── Redis Stream Keys ─────────────────────────────────────────
    stream_events: str = "security:events"
    stream_alerts: str = "security:alerts"
    stream_evidence: str = "security:evidence"
    stream_decisions: str = "security:decisions"
    stream_actions: str = "security:actions"
    stream_verification: str = "security:verification"
    stream_metrics: str = "security:metrics"

    # ── Consumer Group Names ──────────────────────────────────────
    group_perimeter: str = "perimeter_group"
    group_endpoint: str = "endpoint_group"
    group_forensics: str = "forensics_group"
    group_coordinator: str = "coordinator_group"
    group_baseline: str = "baseline_group"

    # ── Hash Key Prefixes ─────────────────────────────────────────
    hash_agent_status: str = "agent:{agent_id}:status"
    hash_incident: str = "incident:{incident_id}"
    hash_simulation: str = "simulation:current"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton)."""
    return Settings()


# Convenience alias
settings = get_settings()
