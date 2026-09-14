---
name: exempt-skill
description: Verifies the auditignore exemption semantics. Use when testing signature-file exemptions of the auditor.
---

# exempt-skill

This skill ships a signature-definition file (`signatures.txt`) that is
exempted from S-checks via the package-root `auditignore` list.
Everything else about this package is clean and shippable.
