# Commit Guard: Review Report Template

Every audit executed by `commit-guard` must follow this standardized report structure.

---

# Commit Guard Audit Report

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
| **Compliance Score** | `{{COMPLIANCE_SCORE}} / 100` |

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
| **B3** | `Pillar 3: Architecture` | [`path/to/view.tsx:15`](file:///path/to/view.tsx#L15) | Direct SQL query in frontend component |

### 2.2 Warnings & Improvements (Review before merge)
<!-- Include only if WARNING_COUNT > 0 -->

| # | Pillar / Standard | File & Line | Recommendation |
| :-: | :--- | :--- | :--- |
| **W1** | `Pillar 4: Efficiency` | [`path/to/calc.js:120`](file:///path/to/calc.js#L120) | Nested $O(N^2)$ lookup inside iterative loop; convert to `Set` |
| **W2** | `Pillar 6: Tests` | [`path/to/service.py`](file:///path/to/service.py) | New error branch introduced with no corresponding unit test |
| **W3** | `Compliance: SemVer` | [`CHANGELOG.md`](file:///CHANGELOG.md) | Breaking change introduced but missing SemVer major bump |

---

## 3. Deep Dive Findings & Concrete Fixes

<!-- For each finding above, provide the root cause and the exact remediation code diff -->

### [B1] Stray Debug Print Statement
* **Location**: [`src/services/payment.ts:42`](file:///src/services/payment.ts#L42)
* **Violation**: Pillar 1 (Bloat & Unnecessary Code)
* **Impact**: Pollutes production logs, risks accidental data exposure, decreases performance.
* **Remediation**: Remove the debugging statement:

```diff
- console.log("Received payment payload:", payload);
```

---

### [W1] Algorithmic Complexity: Nested Loop Lookup
* **Location**: [`src/utils/filter.ts:85`](file:///src/utils/filter.ts#L85)
* **Violation**: Pillar 4 (Efficiency & Performance)
* **Impact**: $O(N \times M)$ time complexity slows dramatically as user list scales.
* **Remediation**: Use a `Set` for $O(1)$ lookups:

```diff
- const matching = users.filter(u => allowedIds.includes(u.id));
+ const allowedIdSet = new Set(allowedIds);
+ const matching = users.filter(u => allowedIdSet.has(u.id));
```

---

## 4. Standard Compliance Scorecard

| Domain | Standard | Status | Notes |
| :--- | :--- | :---: | :--- |
| **Versioning** | Semantic Versioning (SemVer 2.0.0) | `PASS` / `FAIL` | Proper Major/Minor/Patch increment |
| **Releases** | Conventional Commits 1.0.0 | `PASS` / `WARN` | Commit message conforms to `feat:`, `fix:`, etc. |
| **Changelog** | Keep a Changelog 1.1.0 | `PASS` / `WARN` | `[Unreleased]` section updated |
| **Cryptography** | NIST SP 800-175B | `PASS` / `FAIL` | AES-GCM / SHA-256 / CSPRNG used |
| **Security** | OWASP Top 10 & CWE Top 25 | `PASS` / `FAIL` | Zero injection, secret leaks, or BOLA flaws |
| **Privacy** | GDPR / CCPA Zero PII in Logs | `PASS` / `FAIL` | No sensitive user data printed to stdout/logs |
| **Docs** | ADR / OpenAPI / Code Comments | `PASS` / `WARN` | Required docs and schemas synced |
| **Licensing** | SPDX Identifiers & Compatibility | `PASS` / `WARN` | Valid license headers present |

---

## 5. Next Steps

<!-- State concrete actions the user or agent should take -->
* If **🛑 BLOCK**: Fix blockers listed in Section 2.1 before proceeding to commit.
* If **⚠️ WARN**: Assess warnings; verify if tests or documentation should be added.
* If **✅ PASS**: Run `git commit` with conventional message format:
  ```bash
  git commit -m "type(scope): concise description of change"
  ```
