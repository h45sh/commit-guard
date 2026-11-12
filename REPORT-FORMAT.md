# Code Guard: Report Formats

`code-guard` uses standardized reporting structures for its two operating modes:
1. **Mode 1: `inspect-commit`** (Fast Delta / Pre-Commit Gate)
2. **Mode 2: `inspect-codebase`** (Holistic Architectural & Entropy Audit)

---

# Format 1: `inspect-commit` Audit Report

```markdown
# Code Guard: Commit Audit Report

**Target Scope**: `{{SCOPE}}` (`{{TARGET_REF}}`)  
**Timestamp**: `{{TIMESTAMP}}`  
**Verdict**: **`{{VERDICT_BADGE}}`** <!-- One of: 🛑 BLOCK / FAIL | ⚠️ WARN | ✅ PASS -->

---

## 1. Executive Summary & Metrics

| Metric | Value |
| :--- | :--- |
| **Files Evaluated** | `{{TOTAL_FILES}}` (`+{{ADDED_FILES}}` / `~{{MODIFIED_FILES}}` / `-{{DELETED_FILES}}`) |
| **Lines Changed** | `+{{INSERTIONS}}` / `-{{DELETIONS}}` |
| **Untracked Files** | `{{UNTRACKED_COUNT}}` |
| **Critical Blockers** | `{{BLOCKER_COUNT}}` |
| **Warnings** | `{{WARNING_COUNT}}` |
| **Execution Time** | `{{EXEC_TIME_SEC}}s` |

> **Verdict Rationale**:  
> {{A 2-3 sentence clear summary explaining why this diff passed, received warnings, or was blocked.}}

---

## 2. Findings Matrix

### 2.1 Critical Blockers (Must fix before committing)
<!-- Include only if BLOCKER_COUNT > 0 -->

| # | Pillar / Standard | File & Line | Summary of Violation |
| :-: | :--- | :--- | :--- |
| **B1** | `Pillar 1: Bloat/Debug` | [`path/to/file.ts:42`](file:///path/to/file.ts#L42) | Leftover `console.log` debug statement |
| **B2** | `Pillar 2: Security` | [`path/to/auth.py:88`](file:///path/to/auth.py#L88) | Hardcoded API secret key detected |
| **B3** | `Pillar 3: Architecture` | [`src/schemas/job.py:12`](file:///src/schemas/job.py#L12) | Upward layer import: `schemas` importing `engine` |
| **B4** | `Pillar 3: Seams` | [`src/ui/screen.py:64`](file:///src/ui/screen.py#L64) | Leaked private state: calling `engine._active_jobs` |

### 2.2 Warnings & Improvements (Review before merge)
<!-- Include only if WARNING_COUNT > 0 -->

| # | Pillar / Standard | File & Line | Recommendation |
| :-: | :--- | :--- | :--- |
| **W1** | `Pillar 1: YAGNI` | [`src/adapters/email.py:15`](file:///src/adapters/email.py#L15) | Single-implementation ABC (Two-Adapter Rule) |
| **W2** | `Pillar 3: Pure Core` | [`src/rules/port_rule.py:30`](file:///src/rules/port_rule.py#L30) | Impure rule: accepts DB connection instead of raw finding |
| **W3** | `Pillar 6: Tests` | [`tests/unit/test_rule.py:45`](file:///tests/unit/test_rule.py#L45) | Flaky `time.sleep()` in unit test |

---

## 3. Deep Dive Findings & Concrete Fixes

### [B3] Upward Layer Dependency Violation
* **Location**: [`src/schemas/job.py:12`](file:///src/schemas/job.py#L12)
* **Violation**: Pillar 3.1 (Downwards-Only Layer Hierarchy)
* **Impact**: Creates cyclical coupling between domain models and runtime execution engine.
* **Remediation**: Invert the dependency or pass the needed data as a pure primitive:

```diff
- from app.engine.executor import JobRunner
+ from typing import Optional
```

---

## 4. Standard Compliance Scorecard

| Domain | Standard | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Layer Discipline** | Downwards-Only Flow | `PASS` / `FAIL` | Zero upward layer imports |
| **Seam Encapsulation** | Zero Private State Leaks | `PASS` / `FAIL` | No external `obj._private` references |
| **Cryptography** | NIST SP 800-175B | `PASS` / `FAIL` | AES-GCM / SHA-256 / CSPRNG used |
| **Security** | OWASP Top 10 & CWE Top 25 | `PASS` / `FAIL` | Zero injection, secret leaks, or BOLA flaws |
| **Test Health** | Deterministic Tests | `PASS` / `WARN` | Zero sleep calls in unit tests |
| **Releases & SemVer** | Conventional Commits & SemVer | `PASS` / `WARN` | Correct format and version bump |

---

## 5. Next Steps
* If **🛑 BLOCK**: Fix blockers listed in Section 2.1 before committing.
* If **✅ PASS**: Ready to commit.
```

---

# Format 2: `inspect-codebase` Audit Report

```markdown
# Code Guard: Whole-Codebase & Architecture Health Report

**Target Path**: `{{TARGET_PATH}}`  
**Repository Branch**: `{{BRANCH}}` (`{{COMMIT_SHA}}`)  
**Scan Scope**: `{{TOTAL_FILES}}` source files (`{{TOTAL_LOC}}` lines of code)  
**Architectural Health Score**: **`{{HEALTH_SCORE}} / 100`**  
**Verdict**: **`{{VERDICT_BADGE}}`** <!-- 🟢 HEALTHY | 🟡 ATTENTION NEEDED | 🔴 CRITICAL DEBT -->

---

## 1. Architectural Health & Entropy Scorecard

| Domain | Standard / Metric | Target | Status | Observations |
| :--- | :--- | :---: | :---: | :--- |
| **Layer Hierarchy (DAG)** | Zero Upward Imports | 0 | `PASS` / `FAIL` | {{Layer leak count and offending modules}} |
| **Dependency Cycles** | Strongly Connected Components | 0 | `PASS` / `FAIL` | {{Cycle count between packages}} |
| **Seam Encapsulation** | Zero External `_private` Access | 0 | `PASS` / `WARN` | {{Count of private attribute leaks}} |
| **Pure Core Integrity** | Pure Rules, Parsers, Schemas | 100% | `PASS` / `WARN` | {{Impure domain files accepting DB/net}} |
| **Module Depth** | Deep vs. Shallow Ratio | > 80% | `PASS` / `WARN` | {{Shallow pass-through classes found}} |
| **Seam Generality** | Two-Adapter Rule | Clean | `PASS` / `WARN` | {{Single-implementation ABCs}} |
| **Database Migrations** | Forward-Only & Drift-Free | 100% | `PASS` / `WARN` | {{Untracked DDL or raw ALTER TABLE}} |
| **Test Speed Budgets** | Tier 1 (<2s) / Tier 2 (<60s) | In-Budget | `PASS` / `WARN` | {{Test duration and sleep count}} |

---

## 2. High-Risk Hotspots (Churn × Complexity)

Modules that change frequently and have high complexity represent the greatest architectural risk. Prioritize refactoring and deepening here:

| Module / File | 90-Day Churn (Commits) | Complexity / LOC | Hotspot Risk Score | Recommended Action |
| :--- | :---: | :---: | :---: | :--- |
| [`src/engine/executor.py`](file:///src/engine/executor.py) | 42 | 480 LOC | 🔴 HIGH (88) | Deepen facade; encapsulate process watchdogs |
| [`src/ui/dashboard.py`](file:///src/ui/dashboard.py) | 35 | 620 LOC | 🟡 MEDIUM (65) | Move business rules out of UI callbacks |
| [`src/rules/network.py`](file:///src/rules/network.py) | 18 | 150 LOC | 🟢 LOW (22) | Healthy pure core |

---

## 3. Deepening Opportunities (The Deletion & Seam Test)

For each shallow module identified, evaluate whether deleting the intermediate layer reduces overall friction:

### Opportunity 1: Consolidate Shallow Pass-Through Facade
* **Involved Files**: [`path/to/wrapper.py`](file:///path/to/wrapper.py), [`path/to/actual_service.py`](file:///path/to/actual_service.py)
* **Problem**: `Wrapper` provides a 6-method interface where every method simply forwards arguments directly to `ActualService` with zero invariant checking or transformation.
* **Deletion Test Result**: Deleting `Wrapper` completely eliminates 50 lines of cognitive overhead without moving complexity elsewhere.
* **Remediation**: Callers should import `ActualService` directly, or `Wrapper` must be deepened to handle lifecycle, timeouts, and state caching.

---

## 4. Layer & Cycle Violations

<!-- Include exact import paths that violate the DAG -->
```
[LAYER VIOLATION] src/schemas/models.py:8
  imports: app.engine.executor (Engine layer cannot be imported by Schemas)
  fix: pass raw parameters or define an abstract schema contract.
```

---

## 5. Strategic Architectural Roadmap

1. **Immediate (Blockers)**: Break circular package dependencies and eliminate external private state calls.
2. **Near-Term (Next Sprint)**: Make domain rules pure ($data_{in} \to data_{out}$); migrate SQLite `CREATE TABLE` to forward-only migration files.
3. **Continuous Maintenance**: Maintain the Two-Adapter rule and enforce Tier 1 test speed budgets ($<2$ seconds).
```
