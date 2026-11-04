#!/bin/bash
# ==============================================================================
# CONVELINA Automated Database & Vector Store Backup Script
# Classification: Disaster Recovery & Operations Protocol
# ==============================================================================

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-convelina-postgres}"
QDRANT_HOST="${QDRANT_HOST:-127.0.0.1}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_DB="${POSTGRES_DB:-consolith}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"

DUMP_FILE="${BACKUP_DIR}/consolith_pg_${TIMESTAMP}.dump"
CHECKSUM_FILE="${BACKUP_DIR}/consolith_pg_${TIMESTAMP}.sha256"

# Cleanup temporary partial files on error
trap 'rm -f "${DUMP_FILE}.tmp" 2>/dev/null || true' ERR

echo "=================================================="
echo " Starting CONVELINA Backup: ${TIMESTAMP}"
echo "=================================================="

# 1. PostgreSQL Custom Compressed Binary Dump (-Fc)
echo "[1/4] Dumping PostgreSQL database '${POSTGRES_DB}' from '${POSTGRES_CONTAINER}'..."
if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -Fc > "${DUMP_FILE}.tmp"
    mv "${DUMP_FILE}.tmp" "${DUMP_FILE}"
    chmod 600 "${DUMP_FILE}" 2>/dev/null || true
    DUMP_SIZE=$(wc -c < "${DUMP_FILE}" | tr -d ' ')
    echo "  [OK] PostgreSQL dump written: ${DUMP_FILE} (${DUMP_SIZE} bytes)"
else
    echo "  [ERROR] PostgreSQL container '${POSTGRES_CONTAINER}' is not running!" >&2
    exit 1
fi

# 2. SHA-256 Checksum Calculation for Audit & Tamper-Evidence
echo "[2/4] Computing SHA-256 integrity checksum..."
if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${DUMP_FILE}" > "${CHECKSUM_FILE}"
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${DUMP_FILE}" > "${CHECKSUM_FILE}"
else
    # Fallback to python
    python3 -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest() + '  ' + sys.argv[1])" "${DUMP_FILE}" > "${CHECKSUM_FILE}"
fi
chmod 600 "${CHECKSUM_FILE}" 2>/dev/null || true
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "  [OK] Checksum recorded: $(cat "${CHECKSUM_FILE}")"
fi

# 3. Qdrant Vector Collection Snapshots
echo "[3/4] Requesting Qdrant collection snapshots..."
for col in "consolith_knowledge" "consolith_forms"; do
    SNAPSHOT_RESP=$(curl -s -w "\n%{http_code}" -X POST "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${col}/snapshots" 2>/dev/null || echo "000")
    HTTP_CODE=$(echo "${SNAPSHOT_RESP}" | tail -n1)
    if [ "${HTTP_CODE}" = "200" ]; then
        echo "  [OK] Snapshot successfully created for collection: ${col}"
    else
        echo "  [WARN] Snapshot returned status ${HTTP_CODE} for collection: ${col} (Qdrant may be remote, empty, or inaccessible at ${QDRANT_HOST}:${QDRANT_PORT})"
    fi
done

# 4. Retention Policy Enforcement
echo "[4/4] Applying retention policy (retaining last ${RETENTION_DAYS} days)..."
if command -v find >/dev/null 2>&1; then
    DELETED_COUNT=$(find "${BACKUP_DIR}" -name "consolith_pg_*.dump" -mtime +"${RETENTION_DAYS}" 2>/dev/null | wc -l || echo "0")
    find "${BACKUP_DIR}" -name "consolith_pg_*.dump" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
    find "${BACKUP_DIR}" -name "consolith_pg_*.sha256" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true
    echo "  [OK] Pruned ${DELETED_COUNT} backups older than ${RETENTION_DAYS} days."
fi

echo "=================================================="
echo " Backup completed successfully at $(date)"
echo "=================================================="
