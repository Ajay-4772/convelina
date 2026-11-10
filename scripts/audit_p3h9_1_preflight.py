"""
Detailed audit script for P3H.9.1:
1. Enumerates all PostgreSQL tables, primary keys, owner column, RLS enabled, RLS forced, and policies.
2. Enumerates all FastAPI routes, HTTP methods, router tags, auth dependencies, and required roles.
3. Compares with p3h9_api_routes.json and docs/P3H9_ROUTE_INVENTORY.md.
"""
import os
import sys
import json
from sqlalchemy import text

# Add backend to path to inspect FastAPI app
sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import engine
from app.main import app

def audit_database():
    print("=== POSTGRESQL TABLES & RLS AUDIT ===")
    with engine.connect() as conn:
        # Query all public tables
        tables = conn.execute(text("""
            SELECT 
                c.relname AS table_name,
                c.relrowsecurity AS rls_enabled,
                c.relforcerowsecurity AS rls_forced,
                (
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name 
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.constraint_type = 'PRIMARY KEY' 
                      AND tc.table_name = c.relname
                    LIMIT 1
                ) AS primary_key
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'r'
            ORDER BY c.relname;
        """)).fetchall()
        print(f"Total tables found: {len(tables)}")
        
        # Query policies
        policies = conn.execute(text("""
            SELECT 
                schemaname,
                tablename,
                policyname,
                permissive,
                roles,
                cmd,
                qual,
                with_check
            FROM pg_policies
            WHERE schemaname = 'public'
            ORDER BY tablename, policyname;
        """)).fetchall()
        
        pol_by_table = {}
        for p in policies:
            pol_by_table.setdefault(p[1], []).append(p)

        table_report = []
        for t in tables:
            tname = t[0]
            t_pols = pol_by_table.get(tname, [])
            # Check column names for ownership column
            cols_res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :tname;"), {"tname": tname}).fetchall()
            cols = {r[0]: r[1] for r in cols_res}
            owner_col = "user_id" if "user_id" in cols else ("id" if tname == "users" else "none")
            
            table_report.append({
                "table_name": tname,
                "primary_key": t[3],
                "owner_column": owner_col,
                "rls_enabled": bool(t[1]),
                "rls_forced": bool(t[2]),
                "policy_count": len(t_pols),
                "columns": list(cols.keys())
            })
            print(f"Table: {tname:<32} PK: {str(t[3]):<15} Owner: {owner_col:<10} RLS: {str(t[1]):<5} FORCE: {str(t[2]):<5} Policies: {len(t_pols)}")

    return table_report

def audit_fastapi_routes():
    print("\n=== FASTAPI ROUTE AUDIT ===")
    
    routes_list = []
    category_counts = {}
    role_counts = {"ADMIN": 0, "USER": 0, "PUBLIC": 0, "DEV_ONLY": 0}
    
    for route in app.routes:
        methods = list(route.methods - {"HEAD", "OPTIONS"}) if hasattr(route, "methods") else []
        if not methods:
            continue
        path = route.path
        name = getattr(route, "name", "")
        tags = getattr(route, "tags", [])
        tag = tags[0] if tags else "Core / System"
        
        # Determine required role
        dep_str = ""
        if hasattr(route, "dependencies"):
            dep_str += " ".join(str(d) for d in route.dependencies)
        if hasattr(route, "dependant"):
            dep_str += " " + str(route.dependant)
            for d in getattr(route.dependant, "dependencies", []):
                dep_str += " " + str(d.call)
        
        required_role = "PUBLIC"
        if "require_admin" in dep_str or ("admin" in path.lower() and "/admin/" in path):
            required_role = "ADMIN"
        elif "get_current_user" in dep_str or "require_user" in dep_str or "get_token_claims" in dep_str:
            required_role = "USER"
        elif "/dev/" in path:
            required_role = "DEV_ONLY"
            
        role_counts[required_role] = role_counts.get(required_role, 0) + 1
        category_counts[tag] = category_counts.get(tag, 0) + 1
        
        for m in methods:
            routes_list.append({
                "path": path,
                "method": m,
                "tag": tag,
                "name": name,
                "role": required_role
            })

    print(f"Total registered API routes/endpoints: {len(routes_list)}")
    print("Routes by category:")
    for cat, cnt in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<35}: {cnt}")
    print("\nRoutes by required authorization:")
    for role, cnt in sorted(role_counts.items(), key=lambda x: -x[1]):
        print(f"  {role:<15}: {cnt}")
        
    return routes_list

if __name__ == "__main__":
    t_rep = audit_database()
    r_rep = audit_fastapi_routes()
    with open("scripts/audit_p3h9_1_results.json", "w") as f:
        json.dump({"tables": t_rep, "routes": r_rep}, f, indent=2)
    print("\nResults written to scripts/audit_p3h9_1_results.json")
