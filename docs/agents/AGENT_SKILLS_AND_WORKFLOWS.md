# CONVELINA — Agent Skills, Rules & DevSecOps Workflows Specification

```
+---------------------------------------------------------------------------------------------------------+
| AI AGENT DEVSECOPS: Custom Domain Skills | AGENTS.md Operating Rules | OpenQodex AST Code Reviewer       |
+---------------------------------------------------------------------------------------------------------+
```

**Classification:** Developer & Agent Tooling Specification  
**Component:** `.agents/skills`, `.cursor/rules`, `AGENTS.md`, `.openqodex`  
**Status:** Active Production Tooling  

---

## 1. Executive Overview

CONVELINA uses an **agent-assisted engineering workflow** governed by strict operating invariants. Autonomous AI pairing tools follow locked architectural rules to ensure that every change maintains database isolation, cryptographic audit trails, and strict Aadhaar Act compliance.

---

## 2. Agent Skills Inventory (`.agents/skills/`)

| Skill Directory | Skill Name | Core Capability & Role |
| :--- | :--- | :--- |
| `.agents/skills/consolith-db-architect/` | `consolith-db-architect` | Guides PostgreSQL schema design, migrations, forced RLS policies, role-based scoping (`consolith_app`), and connection pooling trap mitigation (`NULLIF(..., '')::uuid`). |
| `.agents/skills/consolith-security-auditor/` | `consolith-security-auditor` | Validates database isolation, RLS enforcement, privilege escalation prevention, append-only audit trail immutability, and zero credential leakage. |

---

## 3. Mandatory Agent Operating Rules (`AGENTS.md`)

All AI agents working on CONVELINA must adhere to the 9 core rules defined in [`AGENTS.md`](file:///c:/Users/ajaya/Desktop/consolin/AGENTS.md):
1. **Inspect Before Coding**: Always read `PROJECT.md`, `CURRENT_STATE.md`, and relevant module files before planning code.
2. **Follow Approved Architecture & Locked Build Order**: Modules 1 through 10 must be completed in order.
3. **Fail-Safe, Never Silently Wrong**: Ambiguous names or low OCR confidence must be flagged as "needs manual review". Never report false "no conflict" matches.
4. **Row-Level Security Enforcement**: RLS must be enabled and forced on every table holding user data. Runtime connections must use `consolith_app`. Session settings must use `NULLIF(current_setting(...), '')::uuid`.
5. **Aadhaar Act Compliance**: Zero long-term storage of Aadhaar numbers or raw images. First 8 digits masked in UI and logs. Sensitive fields encrypted with Fernet AES-256. Ephemeral files unlinked in `finally` blocks.
6. **Append-Only Tamper-Evident Audit Log**: Triggers block `UPDATE` and `DELETE` on `audit_log`. Each entry links to the previous entry via SHA-256.
7. **RAG Grounding & Zero Hallucination**: Enforce relevance score floor ($\ge 0.55$). Validate citations against retrieved context.
8. **Credential & Secret Protection**: Never commit `.env`, private keys, or Firebase JSON files to version control.
9. **Test Rigor**: Tests must have real failure modes. Always run tests against live containers before declaring work complete.

---

## 4. OpenQodex Pre-Push Code Reviewer

Before any `git push`, the developer runs:
```bash
npx -y openqodex@0.16.0 review
```
OpenQodex orchestrates static scanners (Semgrep, Gitleaks, Ruff, Bandit, Hadolint, Oxlint, Squawk, SQLFluff, and OSV-Scanner) to ensure zero security regressions before code is pushed to remote repositories.

