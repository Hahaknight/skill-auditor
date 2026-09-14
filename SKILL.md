---
name: skill-auditor
description: Pre-marketplace quality and security audit for AI agent skills. Use when you plan to publish or sell a skill on Agensi, Fleece AI, ClaudeSkills, or any SKILL.md marketplace and want to catch the issues that get submissions rejected or refunded — security patterns, structure defects, fake-content filler, missing provenance. Produces a scored report with pass/fail per check and fix instructions.
---

# Skill Auditor — Pre-Marketplace QA

You are auditing a skill package before it is submitted to a paid marketplace.
Marketplaces reject or refund for exactly these classes of defects. Your job:
produce evidence-backed verdicts, not template text.

## Core rule
Every finding MUST cite evidence from the actual skill files (file path, line,
matched pattern, measured number). If a check produces the same text regardless
of input, the check is broken — say so instead of filling in boilerplate.

## Workflow

1. Run the scanner:
   `python scripts/audit_skill.py --path <skill-dir> --json out.json`
2. Read the JSON. For every flagged check, open the cited file/line and verify
   the finding is real (kill false positives before reporting).
3. Write the report with `templates/report.md`: score, per-check verdict,
   evidence, and a concrete fix for every failed check.
4. Re-run after fixes. Ship only at score >= 85 with zero CRITICAL findings.

## What the scanner checks (and why buyers care)

| # | Check | Marketplace reason |
|---|---|---|
| S1 | Prompt injection patterns | Agensi 8-point scan rejects |
| S2 | Hardcoded secrets / keys | Rejected + account risk |
| S3 | Dangerous shell patterns (recursive force-delete, remote-script piping, privilege escalation) | Rejected |
| S4 | Suspicious exfiltration endpoints | Rejected |
| S5 | Obfuscation (base64 blobs, eval) | Rejected |
| Q1 | Frontmatter validity (name/description rules: length, reserved words) | Install breaks |
| Q2 | Description quality: does it state WHAT + WHEN, or generic filler | Trigger fails → refunds |
| Q3 | Body-to-reference balance (>500 line body = bloat) | Token cost complaints |
| Q4 | Referenced files exist (broken links) | Support tickets |
| Q5 | Declared deps (`metadata.requires.bins`) resolvable | "Doesn't run" refunds |
| P1 | Provenance: LICENSE/NOTICE/author present | Takedown risk |
| P2 | Template-filler risk: generic filler text density | The #1 refund cause |

## Scoring
- CRITICAL (S1-S5, P1) = auto-fail, fix first
- Score = weighted pass rate. 85+ = shippable, 70-84 = fix minor, <70 = do not list
