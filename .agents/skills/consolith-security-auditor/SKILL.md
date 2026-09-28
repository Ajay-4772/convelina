---
name: consolith-security-auditor
description: Validates database isolation, RLS enforcement, privilege escalation prevention, append-only audit trail immutability, and zero credential leakage.
---

# Consolith Security Auditor Skill

## Security Invariants to Verify
1. **Isolation Test**:
   - Querying as Citizen A must return 0 rows of Citizen B's documents.
   - Querying as unauthenticated caller (`current_user_id` null/empty) must return 0 rows.
2. **Privilege Escalation Test**:
   - Attempting `UPDATE users SET role = 'admin' WHERE id = current_user_id` as citizen must be rejected by trigger.
3. **Officer Scoping Test**:
   - Officer can only SELECT cases where `assigned_officer_id = current_user_id`. Unassigned cases must return 0 rows.
4. **Audit Trail Immutability**:
   - Attempting `UPDATE audit_log` or `DELETE FROM audit_log` must raise an unhandled exception.
5. **Connection Pooling Safety**:
   - Connections cycled through multiple sessions must not retain previous identity or fail on empty string UUID casts.
