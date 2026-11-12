---
name: code-guard
description: Full-lifecycle codebase and commit integrity auditor. Operates in two modes: inspect-commit (fast delta pre-commit/PR audit for dead code, secrets, regressions, layer leaks) and inspect-codebase (deep whole-codebase architectural sweep for pure core vs imperative shell, layer DAG enforcement, module depth, seam encapsulation, schema migrations, and churn hotspots). Backward compatible with commit-guard. Use when user asks to review changes, pre-commit audit, audit codebase, inspect architecture, check git diff, find dead code, or run /code-guard or /commit-guard.
---

# Code Guard

`code-guard` is an uncompromising full-lifecycle codebase and commit integrity auditor. It prevents software entropy by operating across two complementary scopes:
1. **`inspect-commit` (Delta Mode)**: Lightning-fast (<1.5s) pre-commit and PR gate that inspects modified lines for dead/debug code, exposed secrets, broken crypto, layer inversions, and regression risks.
2. **`inspect-codebase` (Holistic Mode)**: Deep repository-wide audit that enforces architectural layering, module depth, logic purity (pure core vs. imperative shell), seam encapsulation, forward-only migrations, and churn hotspot risk.

---

## Operating Modes & Scopes

| Mode | Command / User Triggers | Inspection Target | Execution Target |
| :--- | :--- | :--- | :--- |
| **`inspect-commit`** *(Default)* | `"review my changes"`, `"audit diff"`, `"pre-commit check"`, `"audit PR"` | Staged or unstaged working tree delta, feature branch against main, or specific commit | Fast delta scan on changed lines + untracked files |
| **`inspect-codebase`** | `"audit codebase"`, `"inspect architecture"`, `"codebase hygiene scan"`, `"find deepening opportunities"` | Full repository tree, subsystem path, or high-churn Git hotspots | Whole AST parse, layer DAG verification, purity audit, churn risk |

---

## The 3-Phase Review Workflow

```
[ Phase 1: Scan & Metrics ] ───► [ Phase 2: Multi-Pillar Audit ] ───► [ Phase 3: Structured Report ]
  scripts/code_guard.py              Checklist, DAG & Principles          Delta or Architecture Report
```

### Phase 1: Deterministic Heuristic Extraction

Run the bundled deterministic extraction script from the repository root:

#### For Delta Commits (`inspect-commit`):
```bash
python3 /path/to/code-guard/scripts/code_guard.py --mode commit --scope uncommitted --json
```
Or for branch / PR review:
```bash
python3 /path/to/code-guard/scripts/code_guard.py --mode commit --scope branch --base main --json
```

#### For Whole-Codebase Architecture (`inspect-codebase`):
```bash
python3 /path/to/code-guard/scripts/code_guard.py --mode codebase --path . --hotspots --json
```

*For legacy codebases adopting Code Guard*: Use `--generate-baseline .codeguard-baseline.json` to capture existing debt, and `--baseline .codeguard-baseline.json` on subsequent runs to ratchet only newly introduced violations.

---

### Phase 2: Multi-Pillar Deep Inspection

Examine the code against the standards defined in:

* **[CHECKLIST.md](CHECKLIST.md)**:
  * **Pillar 1: Dead, Bloat & Shallow Modules (Top Priority)** — leftover debuggers, unused imports, orphaned helpers, shallow wrappers, the **Deletion Test**, the **Two-Adapter Rule**, and the **Indirection Tax**.
  * **Pillar 2: Security, Cryptography & Trust Boundaries** — hardcoded secrets, injection flaws, auth/BOLA bypasses, NIST SP 800-175B crypto primitives, and defensive plugin sandboxing.
  * **Pillar 3: Architectural Integrity & System Seams** — **Downwards-Only Layer Hierarchy** (strict DAG), **Pure Core, Imperative Shell** (zero I/O in rules/parsers), **Clean Seams** (zero external calls to `obj._private`), and **Forward-Only Database Migrations**.
  * **Pillar 4: Efficiency, Concurrency & Performance** — $O(N^2)$ loops, N+1 queries, unclosed resources, sync calls in async loops, TOCTOU, and race conditions.
  * **Pillar 5: Code Robustness & Error Discipline** — swallowed exceptions, fragile typing, and fail-fast validation.
  * **Pillar 6: Test Suite Discipline & Speed Budgets** — Tier 1 Pure Unit Suite ($<2$s in-memory), Tier 2 Integration Suite ($<60$s), and zero flaky sleeps (`time.sleep` banned).
  * **Pillar 7: Documentation & Contract Completeness** — in-code docstrings, OpenAPI/schema synchronization, ADRs, README config updates.

* **[DOMAINS.md](DOMAINS.md)**:
  * **Domain 6: Enterprise Architecture & Scaling** — Layer DAG contracts, schema drift prevention, churn $\times$ complexity hotspot prioritization, and plugin blast radius isolation.
  * **Domain 1–5**: AI/LLM agent safety, container/CI security, API idempotency & SSRF, concurrency TOCTOU, WCAG AA accessibility.

* **[COMPLIANCE.md](COMPLIANCE.md)**:
  * Semantic Versioning 2.0.0, Conventional Commits 1.0.0, Keep a Changelog.
  * OWASP Top 10, NIST SP 800-175B, CWE Top 25, GDPR/CCPA Zero PII in logs, SLSA v1.0, SPDX licensing.

---

### Phase 3: Verdict & Structured Report

Generate a clear, actionable review using the templates in **[REPORT-FORMAT.md](REPORT-FORMAT.md)**:
* Use **Format 1** for `inspect-commit` audits.
* Use **Format 2** for `inspect-codebase` audits.

Always issue an unambiguous verdict:
* **🛑 BLOCK / FAIL**: Critical security vulnerability, hardcoded secret, architectural layer inversion, broken migration, leaked private state, or leftover debug/test bypass code. **Do not commit / merge.**
* **⚠️ WARN**: Suboptimal performance, single-implementation speculative ABC, impure domain rule, missing test coverage, or test sleep. **Fix before merge.**
* **✅ PASS**: Code is lean, secure, performant, architecturally sound, and compliant.

For every finding, provide:
1. Exact file path and line number with clickable markdown link.
2. Severity and violated pillar/compliance standard.
3. Concrete before/after diff showing the recommended fix.

---

### Automated Git Hook Integration

Developers can enforce Code Guard locally on every commit by running:
```bash
python3 /path/to/code-guard/scripts/install_hook.py
```
This installs `.git/hooks/pre-commit`, running `code_guard.py --mode commit --scope staged` before every commit.
