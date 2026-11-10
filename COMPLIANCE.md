# Commit Guard: Standard Compliance Catalog

This catalog outlines the established software industry standards and compliance frameworks enforced by `commit-guard`. Changes should adhere to these specifications across versioning, releases, security, documentation, privacy, and licensing.

---

## 1. Versioning, Tags & Release Standards

### 1.1 Semantic Versioning 2.0.0 (SemVer)
Adhere strictly to [Semantic Versioning 2.0.0](https://semver.org/):
Given a version number `MAJOR.MINOR.PATCH`, increment the:
* **`MAJOR` version** when you make incompatible API changes or breaking schema modifications.
* **`MINOR` version** when you add functionality in a backward-compatible manner.
* **`PATCH` version** when you make backward-compatible bug fixes or security patches.
* **Pre-release tags**: Format as `1.0.0-alpha.1`, `1.0.0-beta.2`, `1.0.0-rc.1`.
* **Build metadata**: Format as `1.0.0+20261110.build42`.

### 1.2 Git Tagging Conventions
* **Tag Format**: Always prefix release tags with `v` followed by valid SemVer (`v1.2.3`).
* **Annotated Tags**: Production releases must use annotated tags (`git tag -a v1.2.3 -m "Release v1.2.3"`), never lightweight tags, ensuring timestamp, tagger identity, and release summary are captured.
* **Signed Tags**: Where required by organization policy, sign release tags with GPG/SSH keys (`git tag -s v1.2.3`).

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

## 3. Privacy & Telemetry Compliance (GDPR / CCPA)

### 3.1 Personally Identifiable Information (PII) Protection
* **Log Sanitization**: Logs, error traces, and console outputs must NEVER contain PII:
  * Full names, email addresses, phone numbers.
  * Passwords, PINs, auth tokens, session cookies, API keys.
  * Credit card numbers (PCI-DSS compliance requires zero cardholder data in logs).
  * Social security numbers, national ID numbers, health records (HIPAA compliance).
* **Telemetry & Analytics**:
  * Respect user consent flags (opt-in/opt-out).
  * Anonymize or hash IP addresses and device IDs before transmitting to external analytics.

---

## 4. Documentation & Architectural Governance

### 4.1 Architecture Decision Records (ADRs)
* When a commit introduces:
  * A new third-party dependency, framework, or architectural pattern,
  * A change to database technology or persistence model,
  * A major shift in API communication protocols (e.g., REST to gRPC or GraphQL),
  * **Requirement**: An ADR document must accompany the change in `docs/adr/` stating Title, Status, Context, Decision, and Consequences.

### 4.2 API Contract & Interface Documentation
* **OpenAPI / Swagger 3.0+**: Public HTTP endpoints must update their OpenAPI schema specifications.
* **Docstrings & Types**:
  * Python: PEP 257 docstrings and PEP 484 type hints on all public interfaces.
  * TypeScript / JavaScript: TSDoc / JSDoc annotations for exported functions, types, and interfaces.
  * Go: GoDoc comments on all exported types, functions, and packages.
  * Rust: Rustdoc (`///`) on all `pub` structs, traits, and functions.

### 4.3 Deprecation & Migration Notices
* If an existing interface, parameter, or behavior is modified or marked for removal:
  * Mark with explicit `@deprecated` annotation or warning.
  * Document the replacement method and expected version of removal.
  * Provide a clear migration guide in release notes or documentation.

---

## 5. Licensing, Attribution & Supply Chain

### 5.1 SPDX License Identifiers
* Every newly introduced source file should declare its license using a standard SPDX identifier at the top of the file:
  ```
  // SPDX-License-Identifier: MIT
  // or
  # SPDX-License-Identifier: Apache-2.0
  ```

### 5.2 License Compatibility
* **Permissive Licenses** (MIT, Apache-2.0, BSD-2/3-Clause, ISC): Can generally be incorporated into any project.
* **Copyleft Licenses** (GPLv2, GPLv3, AGPLv3): Must NOT be silently imported or copied into non-copyleft or proprietary codebases without legal review.

### 5.3 Supply Chain & Dependency Hygiene
* **Lockfiles**: Any change to dependencies must include the corresponding lockfile update (`package-lock.json`, `poetry.lock`, `Cargo.lock`, `go.sum`).
* **Version Pinning**: Avoid wildcard or open-ended dependency versions (e.g. `*`, `latest`). Pin specific minor/patch ranges (`^1.2.3` or `~1.2.3`).
* **SBOM (Software Bill of Materials)**: Projects adhering to Executive Order 14028 / CycloneDX / SPDX must ensure all new direct dependencies are trackable.
