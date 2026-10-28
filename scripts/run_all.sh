#!/usr/bin/env bash
# =====================================================================
# MACSS — Multi-Agent Cooperative Security System
# Automated Launcher & Verification Script (Linux / macOS / WSL)
# =====================================================================

set -e

echo "[1/4] Checking Docker daemon status..."
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker first."
    exit 1
fi

echo "[2/4] Deploying all 10 MACSS containers with Docker Compose..."
docker compose up -d --build

echo "[3/4] Waiting 15 seconds for services to initialize..."
sleep 15

echo "[4/4] Verifying health and system status..."
curl -s http://127.0.0.1:8000/api/health
echo ""
echo "====================================================================="
echo " MACSS System is LIVE!"
echo " - Frontend Research Dashboard : http://localhost:3000"
echo " - Backend REST API & Swagger  : http://localhost:8000/docs"
echo " - Live WebSocket Stream       : ws://localhost:8000/ws"
echo "====================================================================="
