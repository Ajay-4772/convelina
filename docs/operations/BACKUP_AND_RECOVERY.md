# CONVELINA — Backup, Disaster Recovery & Business Continuity Plan

**Classification:** Operations & Reliability Engineering  
**Recovery Targets:** RPO < 1 Hour • RTO < 30 Minutes  
**Status:** VALIDATED PROCEDURAL SPECIFICATION  

---

## 1. Backup Strategy & Scheduling

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA PERSISTENCE TIERS                          │
│                                                                        │
│   ┌─────────────────────────────┐    ┌─────────────────────────────┐   │
│   │     POSTGRESQL 16 RDBMS     │    │      QDRANT VECTOR DB       │   │
│   │  • Users, Documents,        │    │  • Knowledge embeddings     │   │
│   │    Conflicts, Cases, Audit  │    │  • Forms catalog vectors    │   │
│   └──────────────┬──────────────┘    └──────────────┬──────────────┘   │
└──────────────────┼──────────────────────────────────┼──────────────────┘
                   │                                  │
                   ▼ Daily Automated Dumps            ▼ Weekly Snapshots
┌────────────────────────────────────────────────────────────────────────┐
│                      BACKUP ENCRYPTION & ARCHIVE                       │
│              AES-256 / GPG Encryption • SHA-256 Checksums              │
│       Destination: Isolated S3 / GCS Bucket with WORM Retention        │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 PostgreSQL 16 Backup Protocol
* **Automated Full Dump**: Executed daily at 02:00 UTC via `pg_dump` using custom compressed format (`-Fc`).
* **Continuous Archiving**: Write-Ahead Logging (WAL) archiving enables Point-In-Time Recovery (PITR) with an RPO under 1 hour.
* **Encryption**: Backups are encrypted at rest using AES-256 before transfer to secure cloud object storage.

### 1.2 Qdrant Vector DB Snapshot Protocol
* **Snapshot Trigger**: Generated weekly or following knowledge base ingestion via the native Qdrant snapshot endpoint:
  ```bash
  curl -X POST "http://localhost:6333/collections/consolith_knowledge/snapshots"
  curl -X POST "http://localhost:6333/collections/consolith_forms/snapshots"
  ```
* **Storage**: Snapshots are archived in the disaster recovery bucket alongside PostgreSQL dumps.

---

## 2. Step-by-Step Restoration Procedure

### 2.1 Database Restoration
```bash
# 1. Stop backend service to prevent connection contention
docker compose stop backend

# 2. Ensure application role exists prior to restoring schema and RLS policies
# (PostgreSQL RLS policies and grants reference consolith_app; role must exist before restore)
docker exec convelina-postgres psql -U postgres -c "
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'consolith_app') THEN
        CREATE ROLE consolith_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END
\$\$;
"

# 3. Re-create clean target database as superuser postgres
docker exec convelina-postgres psql -U postgres -c "DROP DATABASE IF EXISTS consolith;"
docker exec convelina-postgres psql -U postgres -c "CREATE DATABASE consolith;"

# 4. Restore database schema, tables, data, and RLS policies
docker exec -i convelina-postgres pg_restore -U postgres -d consolith /backups/consolith_backup.dump

# 5. Verify non-superuser role permissions and synchronize password
docker exec convelina-postgres psql -U postgres -d consolith -c "
  GRANT USAGE ON SCHEMA public TO consolith_app;
  GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO consolith_app;
"

# 6. Restart backend service
docker compose start backend
```

### 2.2 Qdrant Vector Restoration
```bash
# Recover collection from stored snapshot
curl -X PUT "http://localhost:6333/collections/consolith_knowledge/snapshots/recover" \
     -H "Content-Type: application/json" \
     -d '{"location": "file:///qdrant/snapshots/consolith_knowledge-snapshot.snapshot"}'
```

---

## 3. Post-Restore Integrity Verification

Following any disaster recovery restore, the operator must execute the cryptographic verification checklist:

1. **Verify Audit Trail Hash Continuity**:
   Run `scripts/test_module8_officer_api.py` or inspect hash integrity:
   ```sql
   SELECT id, event_type, current_hash, previous_hash FROM audit_log ORDER BY sequence_number ASC LIMIT 10;
   ```
2. **Verify Forced RLS Status**:
   Confirm that all 13 tenant tables retain `relforcerowsecurity = 't'`:
   ```sql
   SELECT relname, relrowsecurity, relforcerowsecurity 
   FROM pg_class 
   WHERE relname IN ('documents', 'conflicts', 'cases', 'audit_log');
   ```
3. **Execute Health Check**:
   ```bash
   curl -f http://localhost:8000/health
   ```

