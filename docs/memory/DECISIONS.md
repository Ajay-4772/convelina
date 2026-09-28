# Architecture Decision Records (ADR)

## ADR-001: Multi-Container Foundation
- **Date**: 2026-09-29
- **Decision**: Use Docker Compose to orchestrate PostgreSQL 16, Qdrant vector DB, FastAPI, and Next.js frontend with isolated internal networking and individual healthchecks.
- **Rationale**: Ensures deterministic, portable runtime across any developer machine without manual setup dependencies.

## ADR-002: PostgreSQL Native Row-Level Security with Dedicated Non-Superuser Role
- **Date**: 2026-09-29
- **Decision**: All tables storing user, document, conflict, case, and audit data will have Row-Level Security explicitly ENABLED and FORCED (`FORCE ROW LEVEL SECURITY`). The application connection pool will connect strictly via `consolith_app`, a non-superuser role with least privileges.
- **Rationale**: Table owners and superusers silently bypass RLS policies in PostgreSQL. By forcing RLS and connecting via a non-superuser role, security is guaranteed at the database engine level, eliminating application-level bypass risks.

## ADR-003: Connection-Pooling Safe Session Variable Casts
- **Date**: 2026-09-29
- **Decision**: All RLS policies referencing session parameters (`app.current_user_id`, `app.current_user_role`) must wrap reads in `NULLIF(current_setting(..., true), '')::uuid`.
- **Rationale**: When pooled database connections are reused, session parameters reset via `SET LOCAL` or connection resets may evaluate to empty string `""` rather than `NULL`. Casting `""` directly to UUID raises an unhandled database exception.
