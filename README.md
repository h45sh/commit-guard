# Commit Guard 🛡️

An uncompromising pre-commit auditor and change review skill for AI agents and developers.

`commit-guard` enforces system and architectural integrity, security hygiene, cryptographic standards, performance efficiency, and industry compliances—with top priority placed on eliminating dead, bloat, and unnecessary code before it ever enters git history.

---

## Features

- **Prioritized Dead & Bloat Code Detection**: Catches stray debug statements (`console.log`, `print`, `debugger`), commented-out code, orphaned functions, unused imports, pass-through indirection, and premature over-engineering (YAGNI).
- **Security & Cryptography Hygiene**: Enforces NIST SP 800-175B standards (AES-GCM, SHA-256+, CSPRNGs, no weak ciphers or hashes), secret/credential leak prevention, and OWASP Top 10 / CWE Top 25 defenses.
- **Architectural & System Integrity**: Guards layer boundaries, prevents cross-module leakage, checks circular dependencies, and assesses change blast radius.
- **Efficiency & Performance**: Flags $O(N^2)$ lookups, unclosed resources/streams, N+1 query patterns, and synchronous calls in async event loops.
- **Subsystem & Domain Guides**: Specialized checks for AI/LLM systems, Docker & CI/CD workflows, APIs & microservices, concurrency & race conditions, and WCAG accessibility.
- **Comprehensive Industry Compliances**:
  - **Versioning & Releases**: [SemVer 2.0.0](https://semver.org/), [Conventional Commits 1.0.0](https://www.conventionalcommits.org/), [Keep a Changelog 1.1.0](https://keepachangelog.com/).
  - **Security & Cryptography**: OWASP Top 10 (2021), OWASP API Security Top 10 (2023), NIST SP 800-175B / 800-52, CWE / SANS Top 25.
  - **Enterprise Regulations**: SOC 2 Type II, PCI-DSS v4.0, HIPAA Security Rule, GDPR/CCPA zero-PII in logs.
  - **Supply Chain & Governance**: SLSA v1.0, SPDX license identifiers, Architecture Decision Records (ADRs), and OpenAPI sync.
- **Automated Local Git Hook**: Easily installs a `.git/hooks/pre-commit` hook to automatically block bad commits before they happen.
- **Strict Verdicts**: Clear decisions (`🛑 BLOCK / FAIL`, `⚠️ WARN`, `✅ PASS`) with exact file links and before/after remediation diffs.
- **Multi-Scope Flexibility**: Inspect uncommitted working tree changes, staged changes, branches/PRs, specific commits, or full codebases.

---

## Directory Structure

```
commit-guard/
├── SKILL.md              # Main Agent skill entrypoint
├── CHECKLIST.md          # In-depth inspection criteria across all 6 core pillars
├── DOMAINS.md            # Subsystem deep dives (AI/LLM, Docker/CI, APIs, Concurrency, WCAG)
├── COMPLIANCE.md         # Industry standards & compliance catalog (SemVer, OWASP, NIST, SOC 2, PCI, HIPAA, SLSA)
├── REPORT-FORMAT.md      # Standardized audit report template
├── scripts/
│   ├── inspect_diff.py   # Deterministic diff extractor & regex heuristic scanner
│   └── install_hook.py   # One-command git pre-commit hook installer
├── README.md             # Documentation
└── LICENSE               # MIT License
```

---

## Usage

### 1. As an Agent Skill

Invoke directly in your agent conversation:

```text
"Review my uncommitted changes with commit-guard."
"Is my code ready to commit?"
"Run a pre-commit audit on branch feature/auth against main."
"Check for dead code and security flaws in my diff."
```

### 2. Standalone CLI Pre-Scan

You can run the bundled Python scanner directly from the command line:

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

### 3. Automated Git Pre-Commit Hook

Install `commit-guard` as a local git hook in any repository:

```bash
# Install hook in current repository
python3 /path/to/commit-guard/scripts/install_hook.py

# Install hook in a specific repository
python3 /path/to/commit-guard/scripts/install_hook.py --repo /path/to/your/project

# Uninstall hook
python3 /path/to/commit-guard/scripts/install_hook.py --uninstall
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

## Subsystem & Domain Coverage (`DOMAINS.md`)

- **AI & LLM**: Prompt injection prevention, tool calling safety bounds, context bloat minimization.
- **Containers & CI/CD**: Dockerfile non-root execution, base image pinning, GitHub Actions `pull_request_target` security.
- **APIs & Networks**: Mutation idempotency (`Idempotency-Key`), SSRF defense, timeouts, rate limiting.
- **Concurrency**: Race condition prevention, lock acquisition ordering, goroutine/promise leak prevention.
- **Accessibility**: WCAG 2.1/2.2 AA compliant keyboard navigation, form labeling, image alt text.

---

## License

[MIT](LICENSE) © 2026 h45sh
