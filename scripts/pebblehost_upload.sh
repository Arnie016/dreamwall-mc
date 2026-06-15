#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE_DIR="${ROOT_DIR}/dist/pebblehost"
HOST="${PEBBLEHOST_SFTP_HOST:-uk144.pebblehost.net}"
PORT="${PEBBLEHOST_SFTP_PORT:-2222}"
USER_NAME="${PEBBLEHOST_SFTP_USER:-itsarnavsalkade@gmail.com.5ea1f567}"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
elif [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: bash scripts/pebblehost_upload.sh [--dry-run]"
  exit 0
elif [[ -n "${1:-}" ]]; then
  echo "Unknown argument: ${1}" >&2
  echo "Usage: bash scripts/pebblehost_upload.sh [--dry-run]" >&2
  exit 1
fi

required_files=(
  "dreamwall-paper-bridge-0.1.0.jar"
  "AfterBlockMuseum.zip"
  "afterblock-demo-world.zip"
  "SHA256SUMS"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "${BUNDLE_DIR}/${file}" ]]; then
    echo "Missing ${BUNDLE_DIR}/${file}" >&2
    echo "Rebuild the local bundle before uploading." >&2
    exit 1
  fi
done

if ! command -v sftp >/dev/null 2>&1; then
  echo "sftp is not available on PATH." >&2
  exit 1
fi

echo "AfterBlock PebbleHost upload"
echo "Host: ${HOST}:${PORT}"
echo "User: ${USER_NAME}"
echo
echo "Local bundle hashes:"
cat "${BUNDLE_DIR}/SHA256SUMS"
echo
echo "You will be prompted for the PebbleHost panel password."
echo "Stop the Minecraft server before replacing plugin/world files."
echo

batch_file="$(mktemp)"
trap 'rm -f "${batch_file}"' EXIT

cat >"${batch_file}" <<SFTP
-mkdir plugins
put "${BUNDLE_DIR}/dreamwall-paper-bridge-0.1.0.jar" plugins/dreamwall-paper-bridge-0.1.0.jar
put "${BUNDLE_DIR}/AfterBlockMuseum.zip" AfterBlockMuseum.zip
put "${BUNDLE_DIR}/afterblock-demo-world.zip" afterblock-demo-world.zip
put "${BUNDLE_DIR}/SHA256SUMS" afterblock-SHA256SUMS.txt
ls -l plugins/dreamwall-paper-bridge-0.1.0.jar
ls -l AfterBlockMuseum.zip
ls -l afterblock-demo-world.zip
bye
SFTP

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "Dry run only. SFTP batch would be:"
  cat "${batch_file}"
  exit 0
fi

sftp -P "${PORT}" -b "${batch_file}" "${USER_NAME}@${HOST}"

echo
echo "Upload finished. Restart the server, then run:"
echo "/dreamwall pack"
echo "/dreamwall museum check"
echo "/dreamwall import"
echo "Only run /dreamwall museum build if you did not install the prebuilt demo world."
