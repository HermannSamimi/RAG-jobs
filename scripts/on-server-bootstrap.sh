#!/usr/bin/env bash
# One-shot server bootstrap: clone repo, require .env, start Docker stack.
# Run ON the server after: ssh hermann@100.64.8.100
set -euo pipefail

APP_DIR="$HOME/apps/RAG-jobs"
REPO="https://github.com/HermannSamimi/RAG-jobs.git"

SUDO=""
[[ "$(id -u)" -ne 0 ]] && SUDO="sudo"

dc() {
  if docker info &>/dev/null 2>&1; then
    docker compose "$@"
  else
    $SUDO docker compose "$@"
  fi
}

echo "==> Installing Docker if needed..."
if ! command -v docker &>/dev/null; then
  export DEBIAN_FRONTEND=noninteractive
  $SUDO apt-get update -qq
  $SUDO apt-get install -y -qq ca-certificates curl git
  curl -fsSL https://get.docker.com | $SUDO sh
  [[ -n "$SUDO" ]] && $SUDO usermod -aG docker "$USER" || true
fi

echo "==> Cloning/updating repo..."
mkdir -p "$(dirname "$APP_DIR")"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo ""
  echo "ERROR: Edit $APP_DIR/.env with your secrets, then re-run:"
  echo "  bash scripts/on-server-bootstrap.sh"
  exit 1
fi

if command -v ufw &>/dev/null; then
  $SUDO ufw allow OpenSSH || true
  $SUDO ufw allow 2312/tcp || true
  $SUDO ufw allow 8080/tcp || true
  $SUDO ufw --force enable || true
fi

echo "==> Starting stack..."
dc up --build -d
dc ps

sleep 15
if docker info &>/dev/null 2>&1; then
  docker exec rag-jobs-airflow-scheduler airflow dags trigger ingest_software_engineer_jobs_berlin || true
else
  $SUDO docker exec rag-jobs-airflow-scheduler airflow dags trigger ingest_software_engineer_jobs_berlin || true
fi

echo ""
echo "Done:"
echo "  Streamlit: http://100.64.8.100:2312"
echo "  Airflow:   http://100.64.8.100:8080"
