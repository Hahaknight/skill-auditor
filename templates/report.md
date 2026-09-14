# Audit Report: {skill-name}

- Verdict: **{verdict}**
- Score: {score}/100
- Scope: {n-files} files, {n-lines} text lines

## Per-check results

| Check | Result | Notes |
|---|---|---|
| S1 Prompt injection | {S1} | |
| S2 Hardcoded secrets | {S2} | |
| S3 Dangerous shell | {S3} | |
| S4 Exfil endpoints | {S4} | |
| S5 Obfuscation | {S5} | |
| Q1 Frontmatter | {Q1} | |
| Q2 Trigger semantics | {Q2} | |
| Q3 Body size | {Q3} | |
| Q4 Local links | {Q4} | |
| Q5 Declared deps | {Q5} | |
| P1 Provenance | {P1} | |
| P2 Filler density | {P2} | |

## Findings

<!-- For every finding: quote the evidence (file:line, matched pattern),
     then state the concrete fix. Kill false positives before reporting. -->

### {finding-1}

- Evidence: `{file}:{line}` — {matched excerpt}
- Why buyers care: {refund/rejection reason}
- Fix: {concrete action}

## Verdict rationale

<!-- One paragraph: why this verdict, what to fix first, what is fine as-is. -->
