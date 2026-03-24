#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${WATER_GCP_HOST:-}" ]]; then
  echo "WATER_GCP_HOST is required."
  exit 1
fi

WATER_GCP_USER="${WATER_GCP_USER:-ubuntu}"
WATER_GCP_KEY_PATH="${WATER_GCP_KEY_PATH:-$HOME/.ssh/gcp-water.pem}"
LOCAL_INPUT_PATH="${1:-/data/dicoms/patient_batch_01}"
REMOTE_INPUT_PATH="${2:-/data/dicoms/patient_batch_01}"
SSH_TARGET="${WATER_GCP_USER}@${WATER_GCP_HOST}"

if [[ ! -d "${LOCAL_INPUT_PATH}" ]]; then
  echo "Local input directory not found: ${LOCAL_INPUT_PATH}"
  exit 1
fi

ssh -i "${WATER_GCP_KEY_PATH}" "${SSH_TARGET}" "mkdir -p \"${REMOTE_INPUT_PATH}\""
rsync -az --delete -e "ssh -i ${WATER_GCP_KEY_PATH}" "${LOCAL_INPUT_PATH%/}/" "${SSH_TARGET}:${REMOTE_INPUT_PATH%/}/"
echo "Data synced to ${SSH_TARGET}:${REMOTE_INPUT_PATH}"
