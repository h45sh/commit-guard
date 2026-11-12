# Code Guard: Comprehensive Documentation Standards

Code without documentation is incomplete and creates maintenance debt. `code-guard` (formerly `commit-guard`) enforces documentation standards across the codebase: from in-code docstrings and READMEs to formal Architecture Decision Records (ADRs), API schemas, and operational runbooks.

---

## 1. The Diátaxis Documentation Framework

When writing or reviewing user-facing and technical documentation, follow the [Diátaxis Framework](https://diataxis.fr/) which separates documentation into four distinct quadrants based on user needs:

```
                  PRACTICAL CRAFT
                        ▲
                        │
       How-To Guides    │     Tutorials
     (Task-oriented)    │   (Learning-oriented)
                        │
◄───────────────────────┼───────────────────────►
 THEORETICAL KNOWLEDGE  │   PRACTICAL EXPERIENCE
                        │
       Reference        │    Explanation / Architecture
  (Information-oriented)│   (Understanding-oriented)
                        ▼
```

### 1.1 Tutorials (Learning-Oriented)
* **Goal**: Guide a newcomer through a successful initial learning experience.
* **Format**: Hands-on lesson with concrete steps, predictable results, and immediate gratification.
* **Rules**: Minimal theory, no choices or branching paths, focus on building confidence.

### 1.2 How-To Guides (Task-Oriented)
* **Goal**: Show an experienced user how to solve a specific real-world problem or workflow.
* **Format**: Step-by-step recipes (e.g. *"How to configure Redis caching in production"*).
* **Rules**: Assumes basic knowledge; practical, modular, and outcome-focused.

### 1.3 Reference (Information-Oriented)
* **Goal**: Provide accurate, authoritative, technical descriptions.
* **Format**: API specs, CLI command references, configuration tables, schema definitions.
* **Rules**: Objective, structured, comprehensive, neutral tone, zero fluff. Must match implementation 100%.

### 1.4 Explanation / Architecture (Understanding-Oriented)
* **Goal**: Clarify context, design philosophy, trade-offs, and architecture.
* **Format**: Conceptual deep dives, system design overviews, ADRs.
* **Rules**: Explains *why* the system is designed this way rather than *how* to use it.

---

## 2. README Standard (Standard Readme Specification)

Every repository, module, or package must maintain a top-level `README.md` conforming to the [Standard Readme](https://github.com/RichardLitt/standard-readme) specification.

### 2.1 Required README Sections
1. **Title & Badges**: Project name and relevant status badges (build CI, test coverage, release version, license).
2. **Short Pitch / Summary**: 1–2 sentences explaining what the project does, why it exists, and the problem it solves.
3. **Architecture / Overview**: High-level conceptual diagram (Mermaid.js or visual) or architectural overview.
4. **Table of Contents**: Required if the document exceeds 100 lines.
5. **Prerequisites & Requirements**: Minimum runtime versions (e.g., `Node >= 20`, `Python >= 3.11`, `Rust >= 1.75`), database requirements, and external tools.
6. **Installation**: Exact, copy-pasteable terminal commands to clone and install dependencies.
7. **Quick Start / Usage**: Minimal working example showing how to run the software and produce a verified output.
8. **Configuration & Environment Variables**: Markdown table listing every environment variable, its default, whether it is required, and a description.
9. **API / CLI Reference**: Summary of CLI flags, subcommands, or primary exported APIs.
10. **Development & Testing**: Commands to run the test suite, linting, formatting, and local build.
11. **Contributing & Security**: Links to `CONTRIBUTING.md` and `SECURITY.md`.
12. **License**: Name of license and link to the `LICENSE` file.

---

## 3. In-Code Documentation & Docstrings

Public interfaces, exported types, and complex algorithms must include standardized in-code documentation matching the language's recognized best practice:

### 3.1 Python (PEP 257 & Google Style)
Follow [PEP 257](https://peps.python.org/pep-0257/) and [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):
```python
def calculate_payout(account_id: str, amount_cents: int, currency: str = "USD") -> Dict[str, Any]:
    """Calculates net payout after deducting platform fees and tax withholding.

    Args:
        account_id: The unique identifier of the destination merchant account.
        amount_cents: Gross payout volume in cents (must be positive).
        currency: ISO 4217 currency code (default: 'USD').

    Returns:
        A dictionary containing 'net_cents', 'fee_cents', and 'transaction_id'.

    Raises:
        ValueError: If amount_cents is zero or negative.
        AccountSuspendedError: If destination merchant account is locked.
    """
```

### 3.2 TypeScript / JavaScript (TSDoc & JSDoc)
Follow the [TSDoc](https://tsdoc.org/) specification:
```typescript
/**
 * Renders an accessible modal dialog with backdrop dismissal and keyboard focus trapping.
 *
 * @param props - Configuration properties for modal layout and callbacks.
 * @returns A JSX element rendering the dialog portal.
 *
 * @throws {DOMException} If target portal container node is not present in document.
 * @example
 * ```tsx
 * <Modal isOpen={true} onClose={() => setOpen(false)}>
 *   <p>Modal content</p>
 * </Modal>
 * ```
 */
```

### 3.3 Rust (Rustdoc RFC 1574)
Follow [RFC 1574 Rustdoc Conventions](https://rust-lang.github.io/rfcs/1574-more-api-documentation-conventions.html):
```rust
/// Encrypts plaintext using AES-256-GCM with a freshly generated random 96-bit nonce.
///
/// # Examples
///
/// ```
/// let key = Key::generate();
/// let ciphertext = encrypt(&key, b"secret data")?;
/// ```
///
/// # Errors
///
/// Returns `CryptoError::KeyLengthInvalid` if the key is not exactly 32 bytes.
///
/// # Panics
///
/// Panics if the OS CSPRNG source fails to yield random entropy.
///
/// # Safety
///
/// (Required on any `unsafe fn` documenting caller invariants and memory guarantees)
```

### 3.4 Go (Effective Go / GoDoc)
Follow [Effective Go](https://go.dev/doc/effective_go#commentary):
* Every package comment starts with `// Package <name> ...`
* Every exported function, type, or const comment starts with its name:
```go
// CalculatePayout computes the net distribution after deducting platform fees.
// If amountCents is non-positive, it returns an ErrInvalidAmount.
func CalculatePayout(accountID string, amountCents int64) (*PayoutResult, error) {
    ...
}
```

---

## 4. API & Schema Contracts

When changes introduce or update APIs, corresponding formal contract definitions must be updated in sync:

### 4.1 REST APIs (OpenAPI Specification 3.0 / 3.1)
- [ ] Every new endpoint is documented with path, method, summary, description, and tags.
- [ ] Request body schemas include required fields, data types, and format constraints (`format: email`, `minimum: 1`).
- [ ] Response schemas document all HTTP status codes (`200`, `201`, `400`, `401`, `403`, `404`, `422`, `500`).
- [ ] Deprecated endpoints are explicitly tagged with `deprecated: true` and documented with migration alternatives.

### 4.2 Event-Driven APIs (AsyncAPI 2.x / 3.x)
- [ ] Message queue and event-driven architectures (Kafka, RabbitMQ, WebSockets) document message channels, payload schemas, and serialization formats (JSON, Avro, Protobuf).

### 4.3 GraphQL (Schema Definition Language - SDL)
- [ ] Every query, mutation, and type field includes a markdown description comment (`"""..."""`).
- [ ] Obsolete fields include the `@deprecated(reason: "Use newField instead")` directive.

### 4.4 Protocol Buffers (Proto3 / gRPC)
- [ ] Services, RPC methods, messages, and fields must include comments.
- [ ] Deprecated or deleted field tags are marked with `reserved` to prevent tag collision.

---

## 5. Architectural Decision Records (ADRs)

Any non-trivial architectural change, dependency introduction, or persistent data schema migration must be accompanied by an ADR in `docs/adr/`.

Follow the **MADR (Markdown Any Decision Record)** format:

```markdown
# ADR-0012: Adopt Redis for Session Storage and Rate Limiting

* **Status**: Accepted <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXXX -->
* **Date**: 2026-11-10
* **Deciders**: @h45sh, Core Platform Team

## Context and Problem Statement
Our monolithic PostgreSQL database is experiencing CPU saturation from high-frequency session token validation and API rate-limiting checks (15,000 req/sec). We need a high-throughput, low-latency in-memory store.

## Decision Drivers
* Must handle >= 50,000 ops/sec with < 2ms latency.
* Must support automatic TTL key expiration for transient sessions.
* Must support atomic token bucket or sliding window rate-limiting algorithms.

## Considered Options
1. Redis Cluster (Chosen)
2. Memcached
3. Scaling PostgreSQL with read-replicas

## Decision Outcome
Chosen option: **Redis Cluster**, because it natively provides atomic data structures (`INCR`, `EXPIRE`, sorted sets for sliding windows) and Redis Sentinel failover.

### Positive Consequences
* Offloads 85% of queries from primary PostgreSQL database.
* Rate limiting response latency drops from 8ms to 0.7ms.

### Negative Consequences
* Introduces a new stateful cluster dependency requiring backup and monitoring.
* Potential cache invalidation edge cases if session revocation is delayed.

## Validation & Rollout
* Synthetic benchmark at 50k RPS in staging.
* Feature flag rollout: 5% -> 25% -> 100% traffic over 48 hours.
```

---

## 6. Operational & Governance Documentation

### 6.1 `CHANGELOG.md` (Keep a Changelog 1.1.0)
- [ ] Maintain an active `## [Unreleased]` section.
- [ ] Group entries under semantic headers: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.
- [ ] Link issue or PR numbers to each entry.

### 6.2 `SECURITY.md` (Coordinated Vulnerability Disclosure)
Every production repository must have a `SECURITY.md` detailing:
- [ ] Supported versions receiving security patches.
- [ ] Private vulnerability reporting channel (e.g. security email or GitHub Private Vulnerability Reporting).
- [ ] Disclosure policy and response SLA (e.g. acknowledgment within 48 hours).

### 6.3 Operational Runbooks / Playbooks
When releasing a backend service or critical worker:
- [ ] Document alert triggers (e.g. `HighErrorRateAlert`, `QueueBacklogAlert`).
- [ ] Provide step-by-step triage commands.
- [ ] Document immediate mitigation steps (e.g., fallback flag, rolling restart, scale-out command).
- [ ] Specify escalation contacts.

### 6.4 Deprecation & Migration Guides
- [ ] When breaking changes occur, a migration guide must detail before/after code examples, schema conversion scripts, and backwards-compatibility windows.
