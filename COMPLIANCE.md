# Commit Guard: Comprehensive Industry Compliance Catalog

This catalog outlines standard software industry regulations, frameworks, and engineering standards enforced by `commit-guard`. Code changes should satisfy these specifications across versioning, releases, security, documentation, privacy, accessibility, and supply chain.

---

## 1. Versioning, Tags & Release Standards

### 1.1 Semantic Versioning 2.0.0 (SemVer)
Adhere strictly to [Semantic Versioning 2.0.0](https://semver.org/):
Given a version number `MAJOR.MINOR.PATCH`, increment the:
* **`MAJOR` version** when you make incompatible API changes, breaking schema modifications, or remove deprecated endpoints.
* **`MINOR` version** when you add functionality in a backward-compatible manner.
* **`PATCH` version** when you make backward-compatible bug fixes or security patches.
* **Pre-release identifiers**: Format as `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.1`.
* **Build metadata**: Format as `1.0.0+20261110.build42`.

### 1.2 Git Tagging Conventions
* **Tag Format**: Always prefix release tags with `v` followed by valid SemVer (`v1.2.3`).
* **Annotated Tags**: Production releases must use annotated tags (`git tag -a v1.2.3 -m "Release v1.2.3"`), never lightweight tags, ensuring timestamp, tagger identity, and release notes are recorded in the git object graph.
* **Signed Tags**: Where required by organization policy, sign release tags with cryptographic keys (`git tag -s v1.2.3`).

### 1.3 Conventional Commits 1.0.0
Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```
* **Allowed Types**:
  * `feat`: A new feature (correlates with `MINOR` in SemVer).
  * `fix`: A bug fix (correlates with `PATCH` in SemVer).
  * `docs`: Documentation only changes.
  * `style`: Changes that do not affect the meaning of the code (formatting, white-space).
  * `refactor`: Code change that neither fixes a bug nor adds a feature.
  * `perf`: Code change that improves performance.
  * `test`: Adding missing tests or correcting existing tests.
  * `build`: Changes that affect the build system or external dependencies.
  * `ci`: Changes to CI configuration files and scripts.
  * `chore`: Other changes that don't modify src or test files.
* **Breaking Changes**:
  * Include a `!` before the colon (e.g., `feat(api)!: change user response shape`), OR
  * Include a footer: `BREAKING CHANGE: <explanation of what broke and migration path>`.

### 1.4 Changelog Standard (Keep a Changelog 1.1.0)
Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/):
* Maintain an `## [Unreleased]` section at the top of `CHANGELOG.md`.
* Standard categories per release:
  * `Added` for new features.
  * `Changed` for changes in existing functionality.
  * `Deprecated` for soon-to-be removed features.
  * `Removed` for now removed features.
  * `Fixed` for any bug fixes.
  * `Security` in case of vulnerabilities.

---

## 2. Cryptographic & Security Compliance

### 2.1 NIST SP 800-175B & SP 800-52 (Cryptographic Standards)
* **Approved Encryption Algorithms**:
  * **Symmetric**: AES (Advanced Encryption Standard) with key lengths 128, 192, or 256 bits. Must use authenticated modes: **AES-GCM** or **AES-CCM**. ChaCha20-Poly1305 is also approved for modern transport/storage.
  * **Prohibited Symmetric Ciphers**: DES, 3DES (Triple DES), RC4, Blowfish, and **AES in ECB mode** (`AES-ECB`) under any circumstance.
* **Approved Hash Functions**:
  * SHA-2 family: SHA-256, SHA-384, SHA-512.
  * SHA-3 family: SHA3-256, SHA3-512.
  * **Prohibited**: MD5, SHA-0, SHA-1 (strictly prohibited for digital signatures, certificates, security tokens, or integrity verification).
* **Key Generation & Randomness**:
  * Must utilize Cryptographically Secure Pseudo-Random Number Generators (CSPRNGs) with minimum 128-bit entropy (e.g. `/dev/urandom`, `crypto.getRandomValues()`, Python `secrets`).
* **Transport Security**:
  * **TLS 1.3** preferred, TLS 1.2 minimum. Disable SSLv2, SSLv3, TLS 1.0, and TLS 1.1.
* **Password Hashing**:
  * Argon2id (RFC 9106) with minimum 19 MiB memory, $t=2$ iterations, $p=1$ parallelism.
  * Bcrypt with cost factor $\ge 12$.
  * PBKDF2 with HMAC-SHA256 and $\ge 600,000$ iterations (OWASP recommendation).

### 2.2 OWASP Top 10 (2021) & API Security Top 10 (2023)
Enforce zero presence of OWASP top vulnerability classes:
* **A01: Broken Access Control & API1: BOLA**: Prevent missing authorization checks, parameter tampering on resource IDs, and privilege escalation.
* **A02: Cryptographic Failures**: Zero plaintext sensitive data, zero hardcoded keys.
* **A03: Injection & API8: Security Misconfiguration**: Zero unparameterized SQL/NoSQL queries, command injection, or template injection.
* **A07: Identification and Authentication Failures**: Enforce strong password policies, rate limiting, and secure session token handling.
* **API3: Broken Object Property Level Authorization**: Ensure excessive data exposure (e.g. returning full user DB object containing password hash in response) is blocked.

### 2.3 CWE / SANS Top 25
Explicitly check for the top ranked weaknesses:
* **CWE-787**: Out-of-bounds Write / Buffer Overflow.
* **CWE-79**: Cross-site Scripting (XSS).
* **CWE-89**: SQL Injection.
* **CWE-20**: Improper Input Validation.
* **CWE-22**: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal').
* **CWE-352**: Cross-Site Request Forgery (CSRF).
* **CWE-502**: Deserialization of Untrusted Data.

---

## 3. Regulatory & Enterprise Security Frameworks

### 3.1 SOC 2 Type II Controls (Trust Services Criteria)
* **CC6.1 (Logical Access Security)**: Zero hardcoded credentials, API keys, or master passwords in version control. Access tokens must be injected via secure secret managers at runtime.
* **CC6.6 (Boundary Protection)**: Demarcate internal vs. external service boundaries; internal admin utilities or debug endpoints must not be exposed to the public internet.
* **CC7.2 (Monitoring & Audit Trails)**: Security-relevant events (authentication failures, permission changes, administrative actions, password resets) must emit structured audit logs with timestamp, actor, action, and target.
* **CC8.1 (Change Management)**: All modifications must trace back to an authorized commit/PR with code review and passing automated tests.

### 3.2 PCI-DSS v4.0 (Payment Card Industry Data Security Standard)
* **Requirement 3 (Protect Stored Account Data)**:
  * Primary Account Numbers (PAN) must be rendered unreadable anywhere they are stored (using strong cryptography, truncation, or tokenization).
  * Sensitive Authentication Data (SAD)—including card verification values (CVV/CVC) and PINs—must NEVER be retained after payment authorization.
  * Account data must NEVER be emitted into application logs, error traces, or crash reports.
* **Requirement 6 (Develop and Maintain Secure Systems)**:
  * Address common coding vulnerabilities in software-development processes prior to production release.

### 3.3 HIPAA Security Rule (45 CFR Part 164)
* **§ 164.312(a)(1) Access Control**: Enforce unique user identification and emergency access procedures before accessing Electronic Protected Health Information (ePHI).
* **§ 164.312(c)(1) Integrity**: Protect ePHI from improper alteration or destruction.
* **§ 164.312(e)(1) Transmission Security**: ePHI must be encrypted in transit over public and private networks using strong encryption protocols (TLS 1.2+).
* **Zero ePHI in Logs**: Patient names, medical record numbers, diagnoses, or contact information must never appear in application logs or standard error streams.

---

## 4. Documentation & Governance Standards

*(See [DOCUMENTATION.md](DOCUMENTATION.md) for full implementation specifications and templates)*

### 4.1 The Diátaxis Documentation Framework
Organize project documentation into four quadrants:
* **Tutorials** (learning-oriented lessons for beginners).
* **How-To Guides** (task-oriented recipes for solving specific workflows).
* **Reference** (authoritative technical descriptions, API contracts, CLI flags).
* **Explanation** (architectural concepts, design decisions, trade-offs).

### 4.2 Repository & Module README Standards (Standard Readme)
* Every repo/module must have a `README.md` containing: Pitch/Summary, Architecture Overview, Prerequisites, Installation, Quick Start / Working Example, Configuration Table, CLI/API Reference, Testing commands, Contributing, and License.

### 4.3 In-Code Documentation & Docstrings
* **Python**: PEP 257 & Google Python Style Guide docstrings (`Args:`, `Returns:`, `Raises:`).
* **TypeScript / JavaScript**: TSDoc / JSDoc conventions (`@param`, `@returns`, `@throws`, `@example`).
* **Rust**: Rustdoc RFC 1574 (`///`, `# Examples`, `# Errors`, `# Panics`, `# Safety`).
* **Go**: Effective Go / GoDoc package and symbol commentary.

### 4.4 API & Schema Contracts
* **OpenAPI 3.0 / 3.1**: Complete path schemas, request bodies, error response models, and `@deprecated` annotations.
* **AsyncAPI**: Message channel payload schemas for event queues and WebSockets.
* **GraphQL**: SDL descriptions and `@deprecated` directives on fields.
* **Protocol Buffers**: Proto3 comments and `reserved` field tags for removed fields.

### 4.5 Architectural Decision Records (ADRs - MADR Standard)
* Any major architectural change, persistence modification, or new library must include an ADR in `docs/adr/` capturing Context, Decision Drivers, Considered Options, and Consequences.

### 4.6 Operational Documentation & Runbooks
* Services must maintain `CHANGELOG.md` ([Keep a Changelog](https://keepachangelog.com/)), `SECURITY.md` (vulnerability disclosure policy), and production triage runbooks.

---

## 5. Privacy & Telemetry Compliance (GDPR / CCPA)

### 5.1 Personally Identifiable Information (PII) Protection
* **Log Sanitization**: Logs, error traces, and console outputs must NEVER contain PII:
  * Full names, email addresses, phone numbers.
  * Passwords, PINs, auth tokens, session cookies, API keys.
  * Social security numbers, national ID numbers, tax IDs.
* **Telemetry & Analytics**:
  * Respect user consent flags (opt-in/opt-out).
  * Anonymize or hash IP addresses and device IDs before transmitting to external analytics.
* **Data Minimization (GDPR Art. 5)**: Only collect and store fields strictly necessary for the specified purpose. Avoid collecting broad demographic metadata "just in case."

---

## 6. Web Accessibility Standards (WCAG 2.1 & 2.2 AA)

When code introduces or updates user interfaces:
* **Guideline 1.1 (Text Alternatives)**: All non-text content (`<img>`, `<svg>`, `<canvas>`) has a text alternative (`alt="..."` or `aria-label`).
* **Guideline 1.4 (Distinguishable & Contrast)**: Text has a contrast ratio of at least 4.5:1 against its background (3:1 for large text $\ge 18$pt).
* **Guideline 2.1 (Keyboard Accessible)**: All functionality is operable through a keyboard interface without requiring specific timings.
* **Guideline 2.4 (Navigable)**: Web pages and dialogs have titles, focus order is logical, and focus is never trapped inside non-modal components.
* **Guideline 4.1 (Compatible)**: Valid markup with unique `id` attributes, correct ARIA roles, and state synchronization (`aria-expanded`, `aria-selected`).

---

## 7. Supply Chain & Release Security (SLSA & SPDX)

### 7.1 SLSA (Supply-chain Levels for Software Artifacts v1.0)
* **Build Integrity**: Builds must be automated and defined in code (e.g. GitHub Actions, Cloud Build).
* **Hermetic & Isolated Builds**: Build steps must not download unpinned floating dependencies or execute unverified third-party scripts.
* **Provenance**: Verify software artifacts can be traced back to the exact source commit and build configuration.

### 7.2 SPDX License Identifiers (SPDX 2.3/3.0)
* Every newly introduced source file should declare its license using a standard SPDX identifier at the top:
  ```
  // SPDX-License-Identifier: MIT
  // or
  # SPDX-License-Identifier: Apache-2.0
  ```

### 7.3 License Compatibility & Dependency Hygiene
* **Permissive Licenses** (MIT, Apache-2.0, BSD-2/3-Clause, ISC): Compatible with modern closed-source and open-source applications.
* **Copyleft Licenses** (GPLv2, GPLv3, AGPLv3): Must NOT be silently imported or copied into non-copyleft or proprietary codebases without legal review.
* **Lockfiles**: Any change to package manifests (`package.json`, `pyproject.toml`, `Cargo.toml`) MUST commit the corresponding lockfile (`package-lock.json`, `poetry.lock`, `Cargo.lock`) to ensure deterministic supply chain reproducibility.
* **Version Pinning**: Avoid wildcard versions (`*`, `latest`). Use pinned semantic ranges.
