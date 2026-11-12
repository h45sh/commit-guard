# Code Guard 🛡️

An uncompromising full-lifecycle codebase and commit integrity auditor for AI agents and engineering teams.

`code-guard` (formerly `commit-guard`) prevents software entropy and technical rot by operating across two complementary scopes:
1. **`inspect-commit` (Delta Mode)**: Lightning-fast pre-commit and PR gate that inspects modified lines for dead/debug code, exposed secrets, broken crypto, layer inversions, and regression risks.
2. **`inspect-codebase` (Holistic Mode)**: Deep repository-wide audit that enforces architectural layering, module depth, logic purity (pure core vs. imperative shell), seam encapsulation, forward-only migrations, and churn hotspot risk.

---

## Features

- **Dual Operating Modes**:
  - **`inspect-commit`**: Instant (<1.5s) pre-commit/PR check focusing on diffs and staged lines.
  - **`inspect-codebase`**: Whole-system architectural sweep analyzing AST structures, dependency DAGs, and Git churn hotspots.
- **Architectural & System Integrity (Clean Architecture & Deep Modules)**:
  - **Downwards-Only Layer Hierarchy**: Strict Directed Acyclic Graph (DAG) dependency enforcement ($\text{UI} \to \text{Coordination} \to \text{Engine} \to \text{Domain/Schemas}$).
  - **Pure Core, Imperative Shell (FC/IS)**: Keeps business logic, parsers, and recommendation rules 100% pure; pushes DB and network I/O to the shell.
  - **Clean Seams & Zero Private State Leaks**: Enforces encapsulation; forbids external access to `obj._private` attributes/methods.
  - **Deep Modules & The Deletion Test**: Identifies shallow pass-through wrappers and enforces the **Two-Adapter Rule** (1 adapter = hypothetical seam, 2 adapters = real seam).
  - **Forward-Only Migrations**: Prevents untracked DDL mutations and schema drift.
- **Prioritized Dead & Bloat Code Detection**: Catches stray debug statements (`console.log`, `print`, `debugger`), commented-out code, orphaned functions, unused imports, pass-through indirection, and premature over-engineering (YAGNI).
- **Security & Cryptography Hygiene**: Enforces NIST SP 800-175B standards (AES-GCM, SHA-256+, CSPRNGs, no weak ciphers or hashes), secret/credential leak prevention, and OWASP Top 10 / CWE Top 25 defenses.
- **Efficiency & Performance**: Flags $O(N^2)$ lookups, unclosed resources/streams, N+1 query patterns, and synchronous calls in async event loops.
- **Test Suite Speed Budgets**: Enforces Tier 1 Pure In-Memory Unit tests (<2s) vs. Tier 2 Integration tests (<60s), flagging flaky sleeps (`time.sleep` banned).
- **Baseline Ratchet Adoption**: Seamlessly onboard large existing codebases using `--generate-baseline` to capture technical debt and ratchet new changes without stopping development.
- **Automated Local Git Hook**: Easily installs a `.git/hooks/pre-commit` hook to automatically block bad commits before they happen.

---

## Directory Structure

```
code-guard/ (formerly commit-guard)
├── SKILL.md              # Main Agent skill entrypoint
├── CHECKLIST.md          # In-depth inspection criteria across all 7 core pillars
├── DOMAINS.md            # Subsystem deep dives (Architecture, AI/LLM, Docker/CI, APIs, Concurrency, WCAG)
├── DOCUMENTATION.md      # Comprehensive documentation standards (Diátaxis, TSDoc/PEP 257, OpenAPI, ADRs)
├── COMPLIANCE.md         # Industry standards & compliance catalog (SemVer, OWASP, NIST, SOC 2, PCI, HIPAA, SLSA)
├── REPORT-FORMAT.md      # Dual-mode audit report templates (Delta and Architectural Health Scorecards)
├── scripts/
│   ├── code_guard.py     # Deterministic dual-mode scanner (commit + codebase + AST + baseline)
│   ├── inspect_diff.py   # Backward-compatible wrapper forwarding to code_guard.py
│   └── install_hook.py   # One-command git pre-commit hook installer
├── README.md             # Documentation
└── LICENSE               # MIT License
```

---

## Usage

### 1. As an Agent Skill

Invoke directly in your agent conversation:

```text
# Delta / Commit Audits
"Review my uncommitted changes with code-guard."
"Is my code ready to commit?"
"Run a pre-commit audit on branch feature/auth against main."

# Whole-Codebase & Architectural Audits
"Audit the codebase architecture with code-guard."
"Inspect codebase for shallow modules and layer leaks."
"Find deepening opportunities and churn hotspots."
```

### 2. Standalone CLI Usage

#### A. Delta Mode (`inspect-commit`)
```bash
# Check working tree changes
python3 scripts/code_guard.py --mode commit --scope uncommitted

# Check staged files
python3 scripts/code_guard.py --mode commit --scope staged

# Check branch against main
python3 scripts/code_guard.py --mode commit --scope branch --base main

# Output structured JSON
python3 scripts/code_guard.py --mode commit --scope uncommitted --json
```

#### B. Whole-Codebase Mode (`inspect-codebase`)
```bash
# Audit full repository with Git churn hotspot analysis
python3 scripts/code_guard.py --mode codebase --path . --hotspots

# Audit specific subsystem
python3 scripts/code_guard.py --mode codebase --path ./src

# Generate baseline on legacy repository
python3 scripts/code_guard.py --mode codebase --generate-baseline .codeguard-baseline.json

# Audit with baseline ratchet (only reports NEW violations)
python3 scripts/code_guard.py --mode codebase --baseline .codeguard-baseline.json
```

---

## Configuration (`.codeguard.json`)

Customize layers, pure paths, and exclusions for your project:

```json
{
  "layers": {
    "domain": { "can_import": [] },
    "engine": { "can_import": ["domain"] },
    "adapters": { "can_import": ["domain", "engine"] },
    "ui": { "can_import": ["adapters", "domain"] }
  },
  "pure_paths": [
    "src/rules/*",
    "src/schemas/*",
    "src/domain/*"
  ],
  "migrations_dir": "migrations"
}
```

## Inline Suppression

Suppress intentional exceptions using inline comments:

* Python: `# codeguard: ignore[RULE_ID]`
* TypeScript / JavaScript / Go / Rust: `// codeguard-ignore RULE_ID`
* HTML / Markdown: `<!-- codeguard-ignore RULE_ID -->`

---

## License

MIT © 2026
