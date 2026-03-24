#!/usr/bin/env bash
set -euo pipefail

# Required environment variables:
# - WATER_GCP_HOST
# Optional:
# - WATER_GCP_USER (default: ubuntu)
# - WATER_GCP_KEY_PATH (default: ~/.ssh/gcp-water.pem)

if [[ -z "${WATER_GCP_HOST:-}" ]]; then
  echo "WATER_GCP_HOST is required."
  exit 1
fi

WATER_GCP_USER="${WATER_GCP_USER:-ubuntu}"
WATER_GCP_KEY_PATH="${WATER_GCP_KEY_PATH:-$HOME/.ssh/gcp-water.pem}"
SSH_TARGET="${WATER_GCP_USER}@${WATER_GCP_HOST}"

echo "Bootstrapping remote edge node: ${SSH_TARGET}"

ssh -i "${WATER_GCP_KEY_PATH}" "${SSH_TARGET}" "bash -s" <<'EOF'
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y docker.io
  sudo systemctl enable --now docker
fi

sudo usermod -aG docker "$USER" || true
sudo mkdir -p /data/dicoms/patient_batch_01
sudo chown -R "$USER":"$USER" /data/dicoms

echo "Remote bootstrap complete."
docker --version || true
EOF

echo "Done. Reconnect once to apply docker group membership if needed."
