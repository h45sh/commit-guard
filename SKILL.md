---
name: commit-guard
description: Comprehensive pre-commit and change auditor. Reviews uncommitted changes, branches, PRs, or full codebases for dead/unnecessary code, architectural integrity, security/crypto hygiene, efficiency, and compliance standards (SemVer, OWASP, NIST, GDPR, SPDX). Use when user asks to review changes, pre-commit audit, check git diff, find dead code, inspect security/architecture of changes, or run /commit-guard.
---

# Commit Guard

`commit-guard` is an uncompromising pre-commit auditor. It enforces system and architectural integrity, security hygiene, cryptographic standards, performance efficiency, and industry compliances—with top priority placed on eliminating dead, bloat, and unnecessary code before it ever enters history.

## Operating Scopes

Inspect changes across 5 flexible scopes:

| Scope | Command / Trigger | Inspection Target |
| :--- | :--- | :--- |
| **`uncommitted`** *(default)* | `"review my changes"`, `"audit diff"` | Staged + unstaged working tree diff (`git diff HEAD`) plus untracked files |
| **`staged`** | `"check staged"`, `"pre-commit check"` | Only changes staged for commit (`git diff --cached`) |
| **`branch` / `pr`** | `"review branch"`, `"audit PR"` | Feature branch changes against base (`git diff main...HEAD`) |
| **`commit`** | `"review commit <sha>"`, `"audit HEAD"` | Specific commit or revision delta (`git show <sha>`) |
| **`full`** | `"audit codebase"`, `"full scan"` | Whole-codebase hygiene, dead code, secrets, and compliance sweep |

## The 3-Phase Review Workflow

```
[ Phase 1: Diff & Scans ] ──> [ Phase 2: Multi-Pillar Audit ] ──> [ Phase 3: Verdict & Report ]
  scripts/inspect_diff.py       Checklist & Compliance Matrix      BLOCK / WARN / PASS Report
```

### Phase 1: Extract & Heuristic Pre-Scan

Run the bundled deterministic extraction script from the repository root:

```bash
python3 /path/to/commit-guard/scripts/inspect_diff.py --scope uncommitted --json
```

Or for branch review:
```bash
python3 /path/to/commit-guard/scripts/inspect_diff.py --scope branch --base main --json
```

This returns:
1. Exact unified diff and list of modified/added/untracked files.
2. Fast regex flags for leftover debug statements (`console.log`, `print()`, `debugger`), credential tokens, and weak crypto primitives.

### Phase 2: Multi-Pillar Deep Inspection

Examine all added and modified lines against the standards defined in:
* **[CHECKLIST.md](CHECKLIST.md)**:
  * **Pillar 1: Dead, Bloat & Unnecessary Code (Top Priority)** — debug statements, unused imports, orphaned helpers, over-engineering/YAGNI, duplicated utilities.
  * **Pillar 2: Security & Cryptography Hygiene** — hardcoded secrets, injection flaws, auth/BOLA bypasses, weak crypto primitives.
  * **Pillar 3: Architectural & System Integrity** — boundary leaks, layer violations, blast radius, circular dependencies.
  * **Pillar 4: Efficiency & Performance** — $O(N^2)$ loops, N+1 queries, unclosed resources, sync calls in async loops.
  * **Pillar 5: Code Design & Error Handling** — swallowed exceptions, fragile typing, bad naming.
  * **Pillar 6: Tests & Regression Guard** — deleted or weakened tests, missing coverage on new paths.
* **[COMPLIANCE.md](COMPLIANCE.md)**:
  * **Versioning & Commits**: Semantic Versioning 2.0.0, Conventional Commits 1.0.0, Keep a Changelog.
  * **Security Standards**: OWASP Top 10 (2021) / API Top 10 (2023), NIST SP 800-175B Cryptography.
  * **Governance & Docs**: ADR requirements, API docs / OpenAPI synchronization.
  * **Privacy & Legal**: GDPR/CCPA PII leaks in logs, SPDX license identifiers.

### Phase 3: Verdict & Structured Report

Generate a clear, actionable review using the template in **[REPORT-FORMAT.md](REPORT-FORMAT.md)**. Always issue an unambiguous verdict:

* **🛑 BLOCK / FAIL**: Critical security vulnerability, hardcoded secret, architectural boundary break, broken migration, or leftover debug/test bypass code. **Do not commit.**
* **⚠️ WARN**: Suboptimal performance, missing test coverage, non-compliant commit/release format, missing documentation, or non-critical bloat. **Should fix before merge.**
* **✅ PASS**: Code is lean, secure, performant, architecturally sound, and compliant. **Ready to commit.**

For every finding, provide:
1. Exact file path and line number with clickable markdown link.
2. Severity and violated pillar/compliance standard.
3. Concrete before/after diff showing the recommended fix.
