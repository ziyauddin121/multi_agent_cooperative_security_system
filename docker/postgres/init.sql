-- ============================================================
-- MACSS — PostgreSQL Initialization Script
-- Run automatically when the postgres container first starts.
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── Agents ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agents (
    id              SERIAL PRIMARY KEY,
    agent_id        VARCHAR(50) UNIQUE NOT NULL,
    agent_type      VARCHAR(50),
    is_multi_agent  BOOLEAN DEFAULT TRUE,
    registered_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Seed known agents
INSERT INTO agents (agent_id, agent_type, is_multi_agent) VALUES
    ('perimeter-agent',   'perimeter',   TRUE),
    ('endpoint-agent',    'endpoint',    TRUE),
    ('forensics-agent',   'forensics',   TRUE),
    ('coordinator-agent', 'coordinator', TRUE),
    ('baseline-agent',    'baseline',    FALSE)
ON CONFLICT (agent_id) DO NOTHING;

-- ── Experiments ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS experiments (
    id               SERIAL PRIMARY KEY,
    experiment_id    VARCHAR(50) UNIQUE NOT NULL,
    name             VARCHAR(200),
    scenario         VARCHAR(100),
    attack_intensity VARCHAR(20),
    number_of_hosts  INTEGER DEFAULT 4,
    random_seed      INTEGER DEFAULT 42,
    is_multi_agent   BOOLEAN DEFAULT TRUE,
    config           JSONB,
    start_time       TIMESTAMPTZ,
    end_time         TIMESTAMPTZ,
    status           VARCHAR(50) DEFAULT 'pending'
);

-- ── Events ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id            SERIAL PRIMARY KEY,
    event_id      VARCHAR(50) UNIQUE NOT NULL,
    event_type    VARCHAR(100),
    source        VARCHAR(100),
    target        VARCHAR(100),
    severity      VARCHAR(20),
    payload       JSONB,
    is_attack     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    experiment_id INTEGER REFERENCES experiments(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_events_experiment ON events(experiment_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);

-- ── Alerts ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id                  SERIAL PRIMARY KEY,
    alert_id            VARCHAR(50) UNIQUE NOT NULL,
    agent_id            VARCHAR(50) REFERENCES agents(agent_id),
    event_id            VARCHAR(50) REFERENCES events(event_id) ON DELETE SET NULL,
    incident_id         VARCHAR(50),
    alert_type          VARCHAR(100),
    severity            VARCHAR(20),
    confidence          FLOAT,
    recommended_action  VARCHAR(50),
    evidence            JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alerts_incident ON alerts(incident_id);
CREATE INDEX IF NOT EXISTS idx_alerts_agent ON alerts(agent_id);

-- ── Incidents ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS incidents (
    id             SERIAL PRIMARY KEY,
    incident_id    VARCHAR(50) UNIQUE NOT NULL,
    attack_type    VARCHAR(100),
    severity       VARCHAR(20),
    confidence     FLOAT,
    affected_hosts JSONB,
    evidence_count INTEGER DEFAULT 0,
    status         VARCHAR(50) DEFAULT 'OPEN',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    resolved_at    TIMESTAMPTZ,
    experiment_id  INTEGER REFERENCES experiments(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);

-- ── Evidence ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
    id            SERIAL PRIMARY KEY,
    evidence_id   VARCHAR(50) UNIQUE NOT NULL,
    incident_id   VARCHAR(50) REFERENCES incidents(incident_id) ON DELETE CASCADE,
    source_agent  VARCHAR(50),
    evidence_type VARCHAR(100),
    evidence_data JSONB,
    confidence    FLOAT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_evidence_incident ON evidence(incident_id);

-- ── Decisions ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS decisions (
    id                       SERIAL PRIMARY KEY,
    decision_id              VARCHAR(50) UNIQUE NOT NULL,
    incident_id              VARCHAR(50) REFERENCES incidents(incident_id),
    selected_action          VARCHAR(50),
    conflicting_actions      JSONB,
    resolution_reason        TEXT,
    confidence               FLOAT,
    is_multi_agent           BOOLEAN DEFAULT TRUE,
    created_at               TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_decisions_incident ON decisions(incident_id);

-- ── Actions ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS actions (
    id            SERIAL PRIMARY KEY,
    action_id     VARCHAR(50) UNIQUE NOT NULL,
    decision_id   VARCHAR(50) REFERENCES decisions(decision_id),
    action_type   VARCHAR(50),
    target_host   VARCHAR(100),
    status        VARCHAR(50) DEFAULT 'EXECUTED',
    executed_at   TIMESTAMPTZ DEFAULT NOW(),
    experiment_id INTEGER REFERENCES experiments(id) ON DELETE SET NULL
);

-- ── Verification Results ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS verification_results (
    id               SERIAL PRIMARY KEY,
    verification_id  VARCHAR(50) UNIQUE NOT NULL,
    action_id        VARCHAR(50) REFERENCES actions(action_id),
    result           VARCHAR(50),
    checks           JSONB,
    notes            TEXT,
    verified_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Metrics ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metrics (
    id                       SERIAL PRIMARY KEY,
    experiment_id            INTEGER REFERENCES experiments(id) ON DELETE CASCADE,
    detection_time_ms        FLOAT,
    containment_time_ms      FLOAT,
    decision_time_ms         FLOAT,
    blast_radius             INTEGER,
    blast_radius_reduction   INTEGER,
    decision_consistency     FLOAT,
    false_positive_rate      FLOAT,
    false_negative_rate      FLOAT,
    total_alerts             INTEGER DEFAULT 0,
    conflicting_decisions    INTEGER DEFAULT 0,
    successful_containments  INTEGER DEFAULT 0,
    computed_at              TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_metrics_experiment ON metrics(experiment_id);

-- Done
SELECT 'MACSS database initialized.' AS message;
