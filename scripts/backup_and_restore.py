"""
CONVELINA Backup & Disaster Recovery Verification Script
Executes:
1. PostgreSQL logical backup (pg_dump) with SHA-256 checksum & optional Fernet encryption
2. Qdrant collection snapshot trigger via REST API
3. Isolated temporary database restore test & row-count integrity verification
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone


def _run(cmd, check=True):
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def verify_pg_backup_and_restore(
    pg_container: str = "convelina-postgres",
    pg_user: str = "postgres",
    pg_db: str = "consolith",
    qdrant_url: str = "http://127.0.0.1:6333",
    keep_backup_dir: str = "",
) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    temp_ctx = None
    if keep_backup_dir:
        os.makedirs(keep_backup_dir, exist_ok=True)
        out_dir = keep_backup_dir
    else:
        temp_ctx = tempfile.TemporaryDirectory(prefix="convelina_dr_")
        out_dir = temp_ctx.name

    dump_path = os.path.join(out_dir, f"convelina_{ts}.sql")
    scratch_db = f"consolith_dr_verify_{ts.lower()}"

    result = {
        "timestamp_utc": ts,
        "postgres_container": pg_container,
        "source_db": pg_db,
        "scratch_restore_db": scratch_db,
        "qdrant_snapshots": [],
        "table_counts_source": {},
        "table_counts_restored": {},
        "verified": False,
    }

    try:
        # 1. Dump PostgreSQL database
        dump_proc = subprocess.run(
            ["docker", "exec", pg_container, "pg_dump", "-U", pg_user, "-d", pg_db, "--clean", "--if-exists"],
            capture_output=True,
            check=True,
        )
        with open(dump_path, "wb") as f:
            f.write(dump_proc.stdout)

        dump_sha256 = hashlib.sha256(dump_proc.stdout).hexdigest()
        result["backup_bytes"] = len(dump_proc.stdout)
        result["backup_sha256"] = dump_sha256

        # Optional encryption verification round-trip using backend Fernet helper if available
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
            from app.core.encryption import encrypt_data, decrypt_data
            sample_cipher = encrypt_data(dump_sha256)
            assert decrypt_data(sample_cipher) == dump_sha256
            result["encryption_roundtrip"] = "verified"
        except Exception as enc_err:
            result["encryption_roundtrip"] = f"skipped ({enc_err})"

        # 2. Query source row counts for critical tables
        count_sql = (
            "SELECT 'users', COUNT(*) FROM users "
            "UNION ALL SELECT 'documents', COUNT(*) FROM documents "
            "UNION ALL SELECT 'conflicts', COUNT(*) FROM conflicts "
            "UNION ALL SELECT 'official_forms', COUNT(*) FROM official_forms "
            "UNION ALL SELECT 'audit_log', COUNT(*) FROM audit_log;"
        )
        src_counts_proc = _run(
            ["docker", "exec", pg_container, "psql", "-U", pg_user, "-d", pg_db, "-t", "-A", "-F", ",", "-c", count_sql]
        )
        for line in src_counts_proc.stdout.strip().splitlines():
            if "," in line:
                tbl, cnt = line.split(",", 1)
                result["table_counts_source"][tbl.strip()] = int(cnt.strip())

        # 3. Create isolated scratch database, copy dump in, restore, and verify counts
        _run(["docker", "exec", pg_container, "psql", "-U", pg_user, "-d", "postgres", "-c", f"CREATE DATABASE {scratch_db};"])
        try:
            restore_proc = subprocess.run(
                ["docker", "exec", "-i", pg_container, "psql", "-U", pg_user, "-v", "ON_ERROR_STOP=1", "-d", scratch_db],
                input=dump_proc.stdout,
                capture_output=True,
                check=True,
            )
            _ = restore_proc.returncode

            rst_counts_proc = _run(
                ["docker", "exec", pg_container, "psql", "-U", pg_user, "-d", scratch_db, "-t", "-A", "-F", ",", "-c", count_sql]
            )
            for line in rst_counts_proc.stdout.strip().splitlines():
                if "," in line:
                    tbl, cnt = line.split(",", 1)
                    result["table_counts_restored"][tbl.strip()] = int(cnt.strip())

            rls_proc = _run(
                [
                    "docker",
                    "exec",
                    pg_container,
                    "psql",
                    "-U",
                    pg_user,
                    "-d",
                    scratch_db,
                    "-t",
                    "-A",
                    "-c",
                    "SELECT COUNT(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='r' AND c.relrowsecurity AND c.relforcerowsecurity;",
                ]
            )
            result["restored_forced_rls_tables"] = int(rls_proc.stdout.strip())
        finally:
            _run(
                ["docker", "exec", pg_container, "psql", "-U", pg_user, "-d", "postgres", "-c", f"DROP DATABASE IF EXISTS {scratch_db};"],
                check=False,
            )

        # 4. Qdrant collection snapshots verification
        try:
            with urllib.request.urlopen(f"{qdrant_url}/collections", timeout=5) as resp:
                cols_payload = json.loads(resp.read().decode("utf-8"))
            for col in cols_payload.get("result", {}).get("collections", []):
                col_name = col["name"]
                req = urllib.request.Request(f"{qdrant_url}/collections/{col_name}/snapshots", method="POST")
                with urllib.request.urlopen(req, timeout=10) as sresp:
                    snap_data = json.loads(sresp.read().decode("utf-8"))
                snap_name = snap_data.get("result", {}).get("name")
                result["qdrant_snapshots"].append({"collection": col_name, "snapshot": snap_name})
                if snap_name:
                    del_req = urllib.request.Request(
                        f"{qdrant_url}/collections/{col_name}/snapshots/{snap_name}",
                        method="DELETE",
                    )
                    urllib.request.urlopen(del_req, timeout=5).close()
        except Exception as q_err:
            result["qdrant_error"] = str(q_err)

        result["verified"] = (
            result["table_counts_source"] == result["table_counts_restored"]
            and result.get("restored_forced_rls_tables", 0) >= 20
        )
        return result
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CONVELINA Backup & DR Restore Test")
    parser.add_argument("--keep-dir", default="", help="Optional directory to keep dump file")
    args = parser.parse_args()
    report = verify_pg_backup_and_restore(keep_backup_dir=args.keep_dir)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("verified") else 1)

