#!/usr/bin/env bash
set -euo pipefail

# Required environment variables:
# - WATER_GCP_HOST
# Optional:
# - WATER_GCP_USER (default: ubuntu)
# - WATER_GCP_KEY_PATH (default: ~/.ssh/gcp-water.pem)
# - WATER_IMAGE (default: water/opencv-infer:latest)

if [[ -z "${WATER_GCP_HOST:-}" ]]; then
  echo "WATER_GCP_HOST is required."
  exit 1
fi

WATER_GCP_USER="${WATER_GCP_USER:-ubuntu}"
WATER_GCP_KEY_PATH="${WATER_GCP_KEY_PATH:-$HOME/.ssh/gcp-water1.pem}"
WATER_IMAGE="${WATER_IMAGE:-water/opencv-infer:latest}"
SSH_TARGET="${WATER_GCP_USER}@${WATER_GCP_HOST}"

echo "Building local image: ${WATER_IMAGE}"
docker build -t "${WATER_IMAGE}" examples/opencv_infer

if [[ ! -f "${WATER_GCP_KEY_PATH}" ]]; then
  echo "SSH key not found: ${WATER_GCP_KEY_PATH}"
  exit 1
fi

IMAGE_SIZE_BYTES="$(docker image inspect "${WATER_IMAGE}" --format '{{.Size}}')"
echo "Image size: ${IMAGE_SIZE_BYTES} bytes"

echo "Streaming image to remote node: ${SSH_TARGET}"
START_TS="$(date +%s)"
if command -v pv >/dev/null 2>&1; then
  docker save "${WATER_IMAGE}" | pv -s "${IMAGE_SIZE_BYTES}" | ssh -i "${WATER_GCP_KEY_PATH}" "${SSH_TARGET}" "docker load"
else
  echo "Tip: install 'pv' for live ETA/progress (sudo apt-get install -y pv)."
  docker save "${WATER_IMAGE}" | ssh -i "${WATER_GCP_KEY_PATH}" "${SSH_TARGET}" "docker load"
fi
END_TS="$(date +%s)"
ELAPSED="$((END_TS - START_TS))"
echo "Image transfer + load completed in ${ELAPSED}s"

echo "Verifying image on remote node"
ssh -i "${WATER_GCP_KEY_PATH}" "${SSH_TARGET}" "docker image inspect ${WATER_IMAGE} >/dev/null && echo 'Image ready on remote'"
