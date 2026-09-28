---
name: consolith-db-architect
description: Guides PostgreSQL schema design, migrations, forced RLS policies, role-based scoping, and connection pooling trap mitigation for Consolith.
---

# Consolith Database Architect Skill

## RLS Design Standards
1. Every table with citizen or officer data must have:
   ```sql
   ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
   ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;
   ```
2. Session Settings:
   - Use `app.current_user_id` and `app.current_user_role`.
   - Wrap in `NULLIF(current_setting('app.current_user_id', true), '')::uuid`.
   - Wrap in `NULLIF(current_setting('app.current_user_role', true), '')`.
3. Roles:
   - `citizen`: Can only see and manipulate their own rows.
   - `officer`: Can only see cases assigned to them and documents tied to those cases.
   - `admin`: Can view all records and manage knowledge sources.
4. Non-Superuser Runtime Role:
   - Always run the application with role `consolith_app`.
   - Never run backend under `postgres` (superuser).
