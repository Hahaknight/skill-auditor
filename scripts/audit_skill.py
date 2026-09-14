# -*- coding: utf-8 -*-
"""skill-auditor: pre-marketplace QA scan for SKILL.md packages.
Every finding carries evidence (file, line, pattern, measured value).
Output: JSON (machine) / stdout summary (human)."""
import argparse, base64, json, os, re, shutil, sys, subprocess

CRIT, WARN, INFO = "CRITICAL", "WARNING", "INFO"

INJECTION = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)", "classic injection phrase"),
    (r"disregard\s+(your|all|the)\s+(rules|instructions|guidelines)", "instruction override"),
    (r"you\s+are\s+now\s+(a|an)\s+(new|different)", "role hijack"),
    (r"system\s*:\s*", "fake system message"),
]
SECRETS = [
    (r"(sk-[A-Za-z0-9]{20,})", "OpenAI-style key"),
    (r"(AKIA[0-9A-Z]{16})", "AWS access key"),
    (r"(ghp_[A-Za-z0-9]{30,})", "GitHub token"),
    (r"(xox[bp]-[A-Za-z0-9-]{10,})", "Slack token"),
    (r"((?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"])", "hardcoded credential"),
]
DANGEROUS = [
    (r"rm\s+-rf?\s+[~/\"]", "recursive force delete"),
    (r"curl[^|]*\|\s*(ba)?sh", "curl pipe shell"),
    (r"wget[^|]*\|\s*(ba)?sh", "wget pipe shell"),
    (r"\bsudo\b", "sudo escalation"),
    (r"chmod\s+777", "world-writable chmod"),
    (r"mkfs|dd\s+if=", "disk-level write"),
    (r"\bkill\s+-9\s+1\b", "init kill"),
]
EXFIL = [
    (r"https?://(?!localhost|127\.0\.0\.1|(?:[a-z0-9-]+\.)*example\.(?:com|org|net)|raw\.githubusercontent|github\.com|npmjs\.org|pypi\.org)[a-z0-9.-]+/(upload|collect|track|webhook|ingest|beacon)", "exfil-style endpoint"),
    (r"(webhook\.site|requestbin|ngrok\.io|burpcollaborator)", "collector service"),
]
OBFUSCATION = [
    (r"eval\s*\(\s*(atob|base64\.decode|buffer\.from)", "base64 eval", INFO),
    (r"exec\s*\(\s*['\"][A-Za-z0-9+/=]{80,}", "exec blob"),
]
GENERIC_FILLER = [
    "lorem ipsum", "todo:", "fixme", "placeholder", "example.com/your",
    "insert your", "your-api-key-here", "tbd", "coming soon", "xxx",
]

def check_frontmatter(md_text):
    issues, meta = [], {}
    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", md_text, re.S)
    if not m:
        return [{"level": CRIT, "check": "Q1", "evidence": "no YAML frontmatter block found"}], meta
    try:
        import yaml
        meta = yaml.safe_load(m.group(1)) or {}
    except Exception:
        for line in m.group(1).splitlines():
            mm = re.match(r"(\w+):\s*(.*)", line)
            if mm: meta[mm.group(1)] = mm.group(2).strip().strip("'\"")
    name = str(meta.get("name", ""))
    desc = str(meta.get("description", ""))
    if not name: issues.append({"level": CRIT, "check": "Q1", "evidence": "frontmatter missing name"})
    if len(name) > 64: issues.append({"level": WARN, "check": "Q1", "evidence": f"name {len(name)} chars > 64 limit"})
    if re.search(r"[A-Z_]|anthropic|claude", name) and not name.islower():
        issues.append({"level": WARN, "check": "Q1", "evidence": f"name '{name}' not lowercase-hyphen or uses reserved word"})
    if not desc: issues.append({"level": CRIT, "check": "Q2", "evidence": "description empty — skill will never trigger"})
    elif len(desc) > 1024: issues.append({"level": WARN, "check": "Q2", "evidence": f"description {len(desc)} chars > 1024 limit"})
    elif not re.search(r"use (when|this skill)", desc, re.I) and not re.search(r"当|触发|时使用|适用于|遇到", desc):
        issues.append({"level": WARN, "check": "Q2",
                       "evidence": "description states what but not WHEN to use — weak trigger semantics",
                       "fix": "append 'Use when ...' clause"})
    return issues, meta

def scan_text_patterns(path, lines, table, check_id):
    findings = []
    for i, line in enumerate(lines, 1):
        for item in table:
            pat, why, sev = (item if len(item) == 3 else (*item, CRIT))
            if re.search(pat, line, re.I if why not in ("AWS access key",) else 0):
                findings.append({"level": sev, "check": check_id, "file": path, "line": i,
                                 "evidence": f"{why}: ...{line.strip()[:100]}"})
    return findings

def filler_density(md_text):
    low = md_text.lower()
    hits = sum(low.count(p) for p in GENERIC_FILLER)
    words = max(len(low.split()), 1)
    return hits, round(hits / words * 1000, 2)  # per-1000-words

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()
    root = args.path
    if not os.path.isdir(root):
        print(f"not a dir: {root}"); sys.exit(2)

    skill_md = os.path.join(root, "SKILL.md")
    report = {"path": root, "checks": {}, "findings": [], "score": 0, "verdict": ""}
    md_text = open(skill_md, encoding="utf-8", errors="replace").read() if os.path.exists(skill_md) else ""
    md_lines = md_text.splitlines()

    # Q1/Q2 frontmatter
    fm_issues, meta = check_frontmatter(md_text)
    report["findings"] += fm_issues
    report["checks"]["Q1_frontmatter"] = "PASS" if not any(f["check"] == "Q1" for f in fm_issues) else "FAIL"
    report["checks"]["Q2_description"] = "PASS" if not any(f["check"] == "Q2" for f in fm_issues) else "FAIL"

    # walk files (a skill may ship signature-definition files it audits with;
    # an auditignore list at package root exempts them from S-checks)
    auditignore = []
    ai_path = os.path.join(root, "auditignore")
    if os.path.exists(ai_path):
        auditignore = [l.strip().replace("\\", "/") for l in open(ai_path, encoding="utf-8", errors="replace") if l.strip() and not l.startswith("#")]
    all_findings, n_files, total_lines, md_refs = [], 0, 0, []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in
                       (".git", "node_modules", "__pycache__",
                        ".pytest_cache", ".mypy_cache", ".ruff_cache",
                        ".tox", ".venv", "venv")]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            n_files += 1
            try:
                if os.path.getsize(fp) > 2_000_000: continue
                lines = open(fp, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            total_lines += len(lines)
            rel = os.path.relpath(fp, root).replace(os.sep, "/")
            exempt = any(rel == pat or rel.startswith(pat + "/") or rel.endswith("/" + pat) for pat in auditignore)
            if not exempt:
                all_findings += scan_text_patterns(rel, lines, INJECTION, "S1")
            if not exempt:
                all_findings += scan_text_patterns(rel, lines, SECRETS, "S2")
                all_findings += scan_text_patterns(rel, lines, DANGEROUS, "S3")
                all_findings += scan_text_patterns(rel, lines, EXFIL, "S4")
                all_findings += scan_text_patterns(rel, lines, OBFUSCATION, "S5")
            if fn.lower().endswith(".md"):
                md_refs += re.findall(r"\]\((?!http)[^)]+\)", "\n".join(lines))

    # dedupe
    seen, dedup = set(), []
    for f in all_findings:
        k = (f["check"], f.get("file"), f.get("line"), f["evidence"][:60])
        if k not in seen: seen.add(k); dedup.append(f)
    report["findings"] += dedup
    for s in ("S1", "S2", "S3", "S4", "S5"):
        report["checks"][s] = "FAIL" if any(f["check"] == s for f in report["findings"]) else "PASS"

    # Q3 body size
    body_lines = len(md_lines)
    report["checks"]["Q3_body_size"] = "WARN" if body_lines > 500 else "PASS"
    if body_lines > 500:
        report["findings"].append({"level": WARN, "check": "Q3",
            "evidence": f"SKILL.md body {body_lines} lines > 500 — split into references/"})

    # Q4 broken local links in SKILL.md
    broken = []
    for ref in re.findall(r"\]\(([^)#?]+?)(?:#[^)]*)?\)", md_text):
        if ref.startswith(("http", "mailto", "data:")) or not ref.strip(): continue
        if not os.path.exists(os.path.normpath(os.path.join(root, ref))):
            broken.append(ref)
    report["checks"]["Q4_links"] = "FAIL" if broken else "PASS"
    for b in broken[:10]:
        report["findings"].append({"level": WARN, "check": "Q4",
            "evidence": f"broken local reference in SKILL.md: {b}"})

    # Q5 declared deps resolvable
    req = (meta.get("metadata") or {}).get("requires", {}).get("bins", []) if isinstance(meta.get("metadata"), dict) else []
    missing = []
    for b in req:
        if shutil.which(str(b)) is None: missing.append(str(b))
    report["checks"]["Q5_deps"] = "FAIL" if missing else ("PASS" if req else "N/A")
    for b in missing:
        report["findings"].append({"level": WARN, "check": "Q5",
            "evidence": f"declared binary '{b}' not found on this machine"})

    # P1 provenance
    has_license = any(os.path.exists(os.path.join(root, f)) for f in ("LICENSE", "LICENSE.md", "LICENSE.txt"))
    report["checks"]["P1_provenance"] = "PASS" if has_license else "WARN"
    if not has_license:
        report["findings"].append({"level": WARN, "check": "P1",
            "evidence": "no LICENSE file — marketplace takedown/IP risk"})

    # P2 filler density
    hits, density = filler_density(md_text)
    report["checks"]["P2_filler"] = "FAIL" if density > 5 else ("WARN" if hits > 0 else "PASS")
    if hits:
        report["findings"].append({"level": INFO, "check": "P2",
            "evidence": f"{hits} filler markers ({density}/1000 words) in SKILL.md"})

    # score (normalize keys: checks store full names like "Q1_frontmatter")
    weights = {"S1": 15, "S2": 15, "S3": 15, "S4": 10, "S5": 10, "Q1": 10, "Q2": 10,
               "Q3": 3, "Q4": 4, "Q5": 4, "P1": 2, "P2": 2}
    short = {k.split("_")[0]: v for k, v in report["checks"].items()}
    score = 0
    for k, w in weights.items():
        v = short.get(k, "N/A")
        score += w if v == "PASS" else (int(w * 0.75) if v == "WARN" else (w // 2 if v == "N/A" else 0))
    crit = [f for f in report["findings"] if f["level"] == CRIT]
    report["score"] = 0 if crit else min(score, 100)
    report["verdict"] = ("DO NOT LIST — critical findings" if crit else
                         "SHIPPABLE" if score >= 85 else "FIX MINOR ISSUES" if score >= 70 else "DO NOT LIST")
    report["stats"] = {"files": n_files, "text_lines": total_lines, "skill_md_lines": body_lines}

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
    print(f"=== skill-auditor: {os.path.basename(root)} ===")
    print(f"score: {report['score']}/100  verdict: {report['verdict']}")
    print(f"stats: {report['stats']}")
    for k in sorted(report["checks"]): print(f"  {k}: {report['checks'][k]}")
    for f in report["findings"][:15]:
        print(f"  [{f['level']}:{f['check']}] {f['evidence'][:110]}")

if __name__ == "__main__":
    main()
