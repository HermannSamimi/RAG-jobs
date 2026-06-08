#!/usr/bin/env bash
# Bootstrap JobRAG on a Linux server (Docker, firewall, compose stack).
# Run on the server: bash scripts/server-setup.sh
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/apps/RAG-jobs}"
PROJECT_DIR="${PROJECT_DIR/#\~/$HOME}"
cd "$PROJECT_DIR"

SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
  SUDO="sudo"
fi

dc() {
  if docker info &>/dev/null; then
    docker compose "$@"
  else
    $SUDO docker compose "$@"
  fi
}

echo "==> JobRAG server setup in $PROJECT_DIR"

if ! command -v docker &>/dev/null; then
  echo "==> Installing Docker..."
  export DEBIAN_FRONTEND=noninteractive
  $SUDO apt-get update -qq
  $SUDO apt-get install -y -qq ca-certificates curl git
  curl -fsSL https://get.docker.com | $SUDO sh
  if [[ -n "$SUDO" ]]; then
    $SUDO usermod -aG docker "$USER" || true
  fi
fi

if ! docker compose version &>/dev/null && ! $SUDO docker compose version &>/dev/null; then
  echo "ERROR: docker compose plugin not found after install"
  exit 1
fi

echo "==> Docker $($SUDO docker --version 2>/dev/null || docker --version)"
echo "==> $($SUDO docker compose version 2>/dev/null || docker compose version)"

if command -v ufw &>/dev/null; then
  echo "==> Configuring firewall (ufw)..."
  $SUDO ufw allow OpenSSH || true
  $SUDO ufw allow 2312/tcp comment 'JobRAG Streamlit' || true
  $SUDO ufw allow 8080/tcp comment 'JobRAG Airflow' || true
  $SUDO ufw --force enable || true
  $SUDO ufw status || true
fi

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found in $PROJECT_DIR"
  echo "Copy .env.example to .env and fill in secrets, or rsync .env from your Mac."
  exit 1
fi

echo "==> Building and starting stack..."
dc up --build -d

echo "==> Container status:"
dc ps

echo "==> Triggering initial ingestion DAG..."
sleep 15
if docker info &>/dev/null; then
  docker exec rag-jobs-airflow-scheduler \
    airflow dags trigger ingest_software_engineer_jobs_berlin || true
else
  $SUDO docker exec rag-jobs-airflow-scheduler \
    airflow dags trigger ingest_software_engineer_jobs_berlin || true
fi

echo ""
echo "Done. Access:"
echo "  Streamlit UI:  http://100.64.8.100:2312"
echo "  Airflow UI:    http://100.64.8.100:8080  (admin / admin)"
echo "  Logs:          docker compose logs -f app"
