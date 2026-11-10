# Commit Guard 🛡️

An uncompromising pre-commit auditor and change review skill for AI agents and developers.

`commit-guard` enforces system and architectural integrity, security hygiene, cryptographic standards, performance efficiency, and industry compliances—with top priority placed on eliminating dead, bloat, and unnecessary code before it ever enters git history.

---

## Features

- **Prioritized Dead & Bloat Code Detection**: Catches stray debug statements (`console.log`, `print`, `debugger`), commented-out code, orphaned functions, unused imports, pass-through indirection, and premature over-engineering (YAGNI).
- **Security & Cryptography Hygiene**: Enforces NIST SP 800-175B standards (AES-GCM, SHA-256+, CSPRNGs, no weak ciphers or hashes), secret/credential leak prevention, and OWASP Top 10 defenses.
- **Architectural & System Integrity**: Guards layer boundaries, prevents cross-module leakage, checks circular dependencies, and assesses change blast radius.
- **Efficiency & Performance**: Flags $O(N^2)$ lookups, unclosed resources/streams, N+1 query patterns, and synchronous calls in async event loops.
- **Industry Standard Compliances**:
  - **Versioning & Releases**: [SemVer 2.0.0](https://semver.org/), [Conventional Commits 1.0.0](https://www.conventionalcommits.org/), [Keep a Changelog 1.1.0](https://keepachangelog.com/).
  - **Security Frameworks**: OWASP Top 10 (2021), OWASP API Security Top 10 (2023), NIST SP 800-175B / 800-52, CWE Top 25.
  - **Privacy & Governance**: GDPR/CCPA zero-PII in logs, Architecture Decision Records (ADRs), OpenAPI sync, and SPDX licensing.
- **Strict Verdicts**: Clear decisions (`🛑 BLOCK / FAIL`, `⚠️ WARN`, `✅ PASS`) with exact file links and before/after remediation diffs.
- **Multi-Scope Flexibility**: Inspect uncommitted working tree changes, staged changes, branches/PRs, specific commits, or full codebases.

---

## Directory Structure

```
commit-guard/
├── SKILL.md              # Main Agent skill entrypoint
├── CHECKLIST.md          # In-depth inspection criteria across all 6 pillars
├── COMPLIANCE.md         # Industry standards & compliance catalog
├── REPORT-FORMAT.md      # Standardized audit report template
├── scripts/
│   └── inspect_diff.py   # Deterministic diff extractor & regex heuristic scanner
├── README.md             # Documentation
└── LICENSE               # MIT License
```

---

## Usage

### As an Agent Skill

Invoke directly in your agent conversation:

```text
"Review my uncommitted changes with commit-guard."
"Is my code ready to commit?"
"Run a pre-commit audit on branch feature/auth against main."
"Check for dead code and security flaws in my diff."
```

### Standalone CLI Pre-Scan

You can also run the bundled Python scanner directly from the command line:

```bash
# Scan uncommitted changes (staged + unstaged + untracked)
python3 scripts/inspect_diff.py --scope uncommitted

# Scan only staged changes
python3 scripts/inspect_diff.py --scope staged

# Scan branch changes against main
python3 scripts/inspect_diff.py --scope branch --base main

# Output structured JSON for automation or CI pipelines
python3 scripts/inspect_diff.py --scope uncommitted --json
```

---

## The 6 Core Pillars

1. **Dead, Bloat & Unnecessary Code (Top Priority)**: Debug artifacts, orphaned logic, YAGNI over-engineering, code duplication.
2. **Security & Cryptography Hygiene**: Zero hardcoded secrets, authenticated encryption (AES-GCM/ChaCha20), no MD5/SHA1/DES, injection prevention.
3. **Architectural & System Integrity**: Boundary integrity, data encapsulation, blast radius control, schema migrations.
4. **Efficiency & Performance**: Algorithmic complexity, resource lifecycle management, unclosed streams, N+1 queries.
5. **Code Design & Robustness**: Robust error handling (no swallowed exceptions), fail-fast validation, clean types.
6. **Test Coverage & Regression Guard**: Test coverage on new branches, preservation of existing test suites.

---

## License

[MIT](LICENSE) © 2026 h45sh
