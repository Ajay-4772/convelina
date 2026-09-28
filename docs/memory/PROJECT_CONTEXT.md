# Consolith Project Context

## Overview
**Consolith** is an AI-powered system that detects conflicts across an Indian citizen's identity documents (Aadhaar, PAN, Passport, 10th/12th certificates, EPF records) — such as a name spelled differently across documents, or a genuine mismatch in a parent's name, date of birth, or address — and provides grounded, source-cited government correction guidance using Retrieval-Augmented Generation (RAG).

## Key Constraints
- Tier 1 document scope: Aadhaar, PAN, Passport, 10th/12th certificates, EPF records.
- Tier 2 document scope (future extensible): Voter ID, Driving Licence, Birth Certificate, Transfer Certificate.
- No auto-submission to government portals; guidance and document drafting only.
- No long-term storage of Aadhaar numbers or identity card images.
- System narrative is **tamper-evidence** (cryptographic signing, hash-chained audit logs), not "unhackability".
- Solo academic project with locked 10-module build order.
