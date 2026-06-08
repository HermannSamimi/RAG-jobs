#!/usr/bin/env bash
# Transfer JobRAG from this Mac to a remote server and run server-setup.sh.
# Usage: ./scripts/deploy-from-mac.sh [ssh-host] [remote-dir]
# Example: ./scripts/deploy-from-mac.sh hermann@100.64.8.100 apps/RAG-jobs
set -euo pipefail

SERVER="${1:-hermann@100.64.8.100}"
REMOTE_DIR="${2:-apps/RAG-jobs}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE_PATH="~/$REMOTE_DIR"

echo "==> Deploying $LOCAL_DIR to $SERVER:$REMOTE_PATH"

ssh "$SERVER" "mkdir -p $REMOTE_PATH"

rsync -avz --progress \
  --exclude '.git' \
  --exclude '.venv' \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  --exclude '*.pyc' \
  "$LOCAL_DIR/" "$SERVER:$REMOTE_PATH/"

if [[ -f "$LOCAL_DIR/.env" ]]; then
  echo "==> Copying .env (secrets, not in git)..."
  scp "$LOCAL_DIR/.env" "$SERVER:$REMOTE_PATH/.env"
else
  echo "WARNING: No local .env — create one on the server from .env.example"
fi

echo "==> Running server setup on remote..."
ssh "$SERVER" "PROJECT_DIR=$REMOTE_PATH bash -s" < "$LOCAL_DIR/scripts/server-setup.sh"
