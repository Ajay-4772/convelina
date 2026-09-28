# Known Issues & Traps

## 1. Connection-Pooling Trap with Session Variables
- **Problem**: When a pooled connection is returned to the pool after `SET LOCAL app.current_user_id = '...'`, the parameter might revert to `""` (empty string) instead of `NULL`.
- **Trap**: `current_setting('app.current_user_id', true)::uuid` fails with `invalid input syntax for type uuid: ""` on subsequent queries.
- **Fix**: Always use `NULLIF(current_setting('app.current_user_id', true), '')::uuid`.

## 2. RLS Silent Bypass by Superusers
- **Problem**: In PostgreSQL, the table owner and the `postgres` superuser bypass Row-Level Security by default unless forced, and superusers bypass RLS unconditionally.
- **Fix**: Application runtime connection must use `consolith_app`, a non-superuser role with explicitly granted DML permissions only.

## 3. Windows Terminal Unicode Encoding
- **Problem**: Scripts printing unicode checkmarks (`\u2713`) fail on Windows terminals running under `cp1252` encoding.
- **Fix**: Use ASCII status indicators `[OK]` and `[FAIL]` in CLI test scripts.
