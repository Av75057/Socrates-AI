#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FRONTEND_DIR="${REPO_ROOT}/frontend"
TARGET_DIR="/var/www/socrates/dist"

cd "${FRONTEND_DIR}"

if [[ ! -d node_modules ]]; then
  npm ci
fi

npm run build
mkdir -p "${TARGET_DIR}"
rsync -a --delete "${FRONTEND_DIR}/dist/" "${TARGET_DIR}/"
