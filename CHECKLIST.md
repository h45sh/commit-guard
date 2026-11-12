# Code Guard: Review & Architecture Checklist

This checklist details the non-negotiable inspection points across all 7 core pillars for both **`inspect-commit`** (delta pre-commit audit) and **`inspect-codebase`** (whole-codebase architectural sweep). When reviewing diffs or whole repositories, systematically evaluate every module and changed line against these criteria.

---

## Pillar 1: Dead, Bloat & Shallow Modules (Top Priority)

Nothing lowers codebase velocity and reliability faster than accumulated bloat, speculative code, forgotten debug artifacts, and shallow pass-through abstractions. Treat dead code and shallow modules as first-class blockers.

### 1.1 Stray Debug & Diagnostic Artifacts
- [ ] **Logging & Print Statements**: Leftover `console.log`, `print()`, `printf`, `System.out.println`, `fmt.Println`, `logger.debug` intended only for local troubleshooting.
- [ ] **Debugger Breakpoints**: `debugger;`, `breakpoint()`, `binding.pry`, `import pdb; pdb.set_trace()`.
- [ ] **Dumps & Traces**: `var_dump`, `dd()`, `dump()`, `p!()`, `console.trace()`.
- [ ] **Temporary Revert Markers**: Any `TODO: remove`, `TODO: revert before commit`, `HACK: test only`.
- [ ] **Test Bypass Flags**: Test-suite bypasses like `it.only(`, `describe.only(`, `@pytest.mark.skip`, `@Ignore` left enabled.

### 1.2 Dead, Unused & Orphaned Logic
- [ ] **Unused Imports & Dependencies**: Newly added or lingering imports, modules, or dependencies that are never referenced.
- [ ] **Orphaned Functions & Variables**: Helper functions, local variables, or constants declared but never called.
- [ ] **Unreachable Code**: Branches after early `return`, `throw`, `exit()`, or impossible conditionals (e.g. `if (false)`).
- [ ] **Commented-Out Code**: Never keep commented-out code blocks in commits. Git history preserves past code. Delete commented-out blocks immediately.

### 1.3 Over-Engineering, Shallow Modules & Speculative Generality (YAGNI)
- [ ] **Deep Modules vs. Shallow Wrappers**:
  - *Deep Module (Good)*: A small, simple interface hiding substantial implementation complexity (e.g. `run_tool(adapter, target, params)` hiding subprocess pipes, stream buffering, timeout watchdogs, and sanitization).
  - *Shallow Module (Bad)*: A 50-line class whose interface is nearly as large as its implementation, offering little cognitive leverage to callers.
- [ ] **The Deletion Test**: Apply this test to every intermediate wrapper, helper class, or forwarding layer:
  > *If you delete this class completely, does complexity vanish, or does it scatter across 10 callers?*
  - If complexity **vanishes**: The class was pure pass-through bloat. **Delete it immediately.**
  - If complexity **scatters**: The class earns its keep by encapsulating real complexity. **Keep and deepen it.**
- [ ] **The Two-Adapter Rule (Seams)**:
  - *One adapter means a hypothetical seam; two adapters means a real one.*
  - Do not introduce abstract base classes, interfaces, or protocol seams "just in case" for a single implementation.
  - Require at least two real implementations (e.g. `CloudBackend` + `OllamaBackend`, or `RealSubprocess` + `TestFake`) before extracting an interface, unless explicitly marked as an external plugin seam (`# codeguard: public-seam`).
- [ ] **The Indirection Tax**:
  - Flag any function, class, or method whose body is *only* a single passthrough delegation to an underlying class (`return self._inner.call(*args, **kwargs)`) without adapting an interface, adding caching, managing transactions, or enforcing invariants.
- [ ] **Speculative Parameters & State**:
  - Unused function arguments, speculative flags, or mutable state that could be derived dynamically.

### 1.4 Code Duplication
- [ ] **Existing Utilities**: Does the change introduce a helper function (e.g., date parsing, string manipulation, deep clone, debounce) that already exists in utility modules or standard libraries?

---

## Pillar 2: Security, Cryptography & Trust Boundaries

### 2.1 Secrets & Credential Exposure
- [ ] **Hardcoded Secrets**: API keys, bearer tokens, OAuth client secrets, private RSA/SSH keys, webhook secrets, database passwords.
- [ ] **Environment Leakage**: `.env`, `.env.local`, credentials files, or local certificates accidentally staged or untracked.
- [ ] **Client-Side Secret Exposure**: Backend tokens or sensitive environment variables exposed to frontend bundles (`NEXT_PUBLIC_`, `VITE_` containing non-public keys).

### 2.2 Cryptographic Standards (NIST SP 800-175B Compliance)
- [ ] **No Weak Hashes for Security**: MD5 and SHA-1 must NEVER be used for security purposes, passwords, digital signatures, or integrity verification. Use SHA-256, SHA-384, SHA-512, or SHA-3.
- [ ] **No Broken Ciphers or Insecure Modes**: DES, 3DES, RC4, and Blowfish are forbidden. AES must NEVER be used in ECB mode (e.g., `AES-ECB`). Always use authenticated encryption (AEAD) like `AES-256-GCM` or `ChaCha20-Poly1305`.
- [ ] **Cryptographically Secure Randomness**: For tokens, session IDs, IVs, and salts, never use pseudo-random generators (`Math.random()`, `random.random()`, `rand()`). Use CSPRNGs (`crypto.randomBytes()`, `secrets.token_bytes()`, `/dev/urandom`).
- [ ] **Password Storage**: Passwords must never be stored plaintext or hashed with plain SHA/MD5. Use Argon2id (recommended), bcrypt, or scrypt with adequate work factors.
- [ ] **IV & Salt Uniqueness**: Initialization vectors (IVs) for AES-GCM must never be reused with the same key. Generate fresh random 96-bit IVs for each encryption operation.

### 2.3 Injection & Boundary Validation
- [ ] **SQL Injection**: Raw string concatenation or template literals rather than parameterized queries / prepared statements.
- [ ] **Command Injection**: `child_process.exec()`, `os.system()`, `subprocess.Popen(..., shell=True)` with untrusted inputs.
- [ ] **Path Traversal**: File paths constructed from user input without sanitization against `../` or without resolving against a trusted root directory.
- [ ] **XSS & Template Injection**: Unescaped user content rendered directly into HTML, DOM elements (`dangerouslySetInnerHTML`), or template engines.
- [ ] **Unsafe Deserialization**: Python `pickle.loads()`, `yaml.load()` without `SafeLoader`, or Java deserialization on untrusted payloads.

### 2.4 Authentication & Authorization
- [ ] **Missing Access Controls**: New routes, endpoints, or RPC handlers without enforcing authentication middleware.
- [ ] **BOLA / IDOR (Broken Object-Level Authorization)**: Accessing records by ID (`/api/documents/:id`) without verifying authenticated user ownership/authorization.
- [ ] **Role Escalation**: Client manipulation of protected payload fields (e.g., `{ "role": "admin" }` or `{ "is_verified": true }`).

---

## Pillar 3: Architectural Integrity & System Seams

### 3.1 Strict Layer & Boundary Discipline (Directed Acyclic Graph)
- [ ] **Downwards-Only Layer Hierarchy**:
  - Dependencies must flow strictly in one direction:
    $$\text{UI / Presentation} \longrightarrow \text{Coordination (Facade/Gateway)} \longrightarrow \text{Core Engine} \longrightarrow \text{Domain / Schemas}$$
  - A lower layer must **never** import a higher layer (e.g., `schemas` importing `engine` or `ui`; `engine` importing UI widgets or screens).
- [ ] **Pure Core, Imperative Shell (FC/IS)**:
  - Keep all business logic, validation, parsers, and recommendation rules as **pure functions**: data in $\to$ data out, zero side effects.
  - Push all I/O (file writes, database operations, subprocess execution, network requests) to the very edge of the system (the "Imperative Shell").
  - Flag any validator, parser, or domain rule accepting database connections, active network clients, or file handles when it only operates on raw data.
- [ ] **Clean Seams & Zero Private State Leakage**:
  - Never reach into another module's internal state: `obj._private_dict`, `obj._internal_method()`, `obj._active_jobs`.
  - All communication across seams must pass through explicit public interfaces / facades.
  - Unit tests have scoped white-box exemptions, but cross-module production code must be 100% encapsulated.
- [ ] **Locality of Behavior (LoB) vs. "Layer Soup"**:
  - The behavior of a unit of code should be obvious from reading that unit.
  - Avoid 5-to-7 hop indirection chains (Event $\to$ Handler $\to$ Controller $\to$ Service $\to$ Manager $\to$ Facade $\to$ Adapter). Group code by domain and feature locality, not arbitrary technical layers.
- [ ] **Circular Dependencies & Cycles**:
  - Cross-module or cross-package imports that form dependency cycles are strictly blocked.

### 3.2 Blast Radius, Plugin Isolation & Schema Migrations
- [ ] **Plugin Sandboxing & Blast Radius Isolation**:
  - Third-party tools, integrations, or parser plugins (e.g. `tools/<name>/`) must run behind defensive sandboxes. A failure, crash, or malformed output in one adapter must never crash the main application or corrupt persistence.
- [ ] **Forward-Only Database Migrations**:
  - Never run unversioned `CREATE TABLE` or raw `ALTER TABLE` mutations in production code.
  - All schema mutations must be tracked via reversible, forward-only migration scripts in a dedicated `migrations/` directory.
- [ ] **Breaking Changes to Public APIs**:
  - Function signatures, parameter orders, or return types of exported APIs modified without backward-compatible defaults or deprecation warnings.

### 3.3 Concurrency & State Integrity
- [ ] **Race Conditions & TOCTOU**:
  - Shared resources modified concurrently without locks, mutexes, or atomic transactions.
  - Check-then-act race conditions (e.g. checking file existence before opening rather than using atomic flags `O_CREAT | O_EXCL`).
- [ ] **Non-Idempotent Handlers**:
  - Mutation endpoints, webhook consumers, or payment handlers vulnerable to duplicate deliveries due to missing idempotency keys.

---

## Pillar 4: Efficiency, Concurrency & Performance

### 4.1 Algorithmic Complexity & Loops
- [ ] **Nested Loop Traversal**: $O(N^2)$ lookups (e.g., `array.find()` or `list.contains()` inside a `for` loop over another collection). Use HashSets, Maps, or dictionaries for $O(1)$ lookups.
- [ ] **Unnecessary Object Duplication**: Large data structures cloned repeatedly inside tight loops (`[...items]`, `Object.assign()`, `copy.deepcopy()`).

### 4.2 Database & Network I/O
- [ ] **The N+1 Query Problem**: Database queries triggered inside an iterative loop over parent records. Use batch fetching, `JOIN`s, or ORM preloading (`include`, `select_related`).
- [ ] **Missing Database Indexes**: New queries filtering (`WHERE`) or ordering (`ORDER BY`) on columns that lack database indexes on large tables.
- [ ] **Unbounded Queries**: Missing `LIMIT` or pagination clauses, risking out-of-memory errors on large datasets.

### 4.3 Resource Lifecycle & Async Hygiene
- [ ] **Resource Cleanup**: File handles, database connections, streams, or sockets properly closed via `finally`, `using`, or context managers (`with` in Python).
- [ ] **Sync Calls in Async Contexts**: Synchronous blocking operations (e.g., `fs.readFileSync`, `time.sleep()`) used inside async event loops or HTTP request threads.
- [ ] **Memory Leaks**: Event listeners, timers, or subscriptions registered without corresponding cleanup on teardown or unmount.

---

## Pillar 5: Code Robustness & Error Discipline

### 5.1 Error Handling Discipline
- [ ] **No Swallowed Exceptions**: Never use silent empty catch blocks (`catch (e) {}` or `except: pass`). Either handle the error, log with context, or re-throw.
- [ ] **Descriptive Errors**: Custom errors preserve the underlying cause (`throw new CustomError(..., { cause: err })`).
- [ ] **Fail Fast**: Input arguments and preconditions validated at the boundary before executing heavy business logic.

### 5.2 Type Safety & Clean Code
- [ ] **Type Precision**: Avoid escaping types with `any`, `Object`, or untyped dictionaries when a structured interface or type is appropriate.
- [ ] **Naming Clarity**: Variable and function names are self-describing, avoiding abbreviations or misleading names.

---

## Pillar 6: Test Suite Discipline & Speed Budgets

### 6.1 Speed Budgets & Determinism
- [ ] **Tier 1 Pure Suite Budget (< 2 seconds)**:
  - Tests for parsers, schemas, rules, and validators must run purely in-memory.
  - Zero network calls, zero disk I/O, zero subprocesses, and zero mocks. Runs on every file save.
- [ ] **Tier 2 Integration / TUI Suite Budget (< 60 seconds)**:
  - Tests for SQLite transactions, subprocess streaming, and UI pilots.
  - Guaranteed deterministic fixtures and teardown. Runs before commit.
- [ ] **Zero Flaky Sleep Calls**:
  - Never use `time.sleep()`, `setTimeout()`, or arbitrary sleep timers in unit tests. Use deterministic synchronization, event triggers, or condition polling with timeouts.

### 6.2 Test Coverage & Regression Guard
- [ ] **Coverage of New Paths**: Both happy paths and edge/error cases covered with unit or integration tests.
- [ ] **Preservation of Existing Tests**: No existing tests deleted, bypassed, or modified to make a broken build pass.

---

## Pillar 7: Documentation & Contract Completeness

*(See [DOCUMENTATION.md](DOCUMENTATION.md) for full formatting rules and templates)*

### 7.1 In-Code Documentation & Docstrings
- [ ] **Public Interface Commentary**: All newly exported functions, methods, classes, and types documented with parameter descriptions, return types, and exceptions.
- [ ] **Invariants & Edge Cases**: Non-obvious algorithms, security boundaries, or concurrency locks documented with inline commentary explaining *why*.

### 7.2 API Contracts & Schema Synchronization
- [ ] **OpenAPI / Swagger Sync**: If HTTP endpoints or payloads changed, `openapi.yaml` or Swagger specification updated.
- [ ] **Schema Migrations & Models**: GraphQL SDL, Protobuf definitions, or database models synchronized with the code changes.
- [ ] **Deprecation Notices**: Deprecated functions or fields marked with `@deprecated` tags stating migration alternatives.

### 7.3 System & Architectural Documentation
- [ ] **Architecture Decision Records (ADRs)**: If introducing a new library, persistence layer, or structural pattern, an ADR is included in `docs/adr/`.
- [ ] **README & Configuration Updates**: If new environment variables, configuration flags, or setup prerequisites were introduced, documented in `README.md`.
- [ ] **Changelog**: `CHANGELOG.md` updated under `## [Unreleased]` using [Keep a Changelog](https://keepachangelog.com/) standards.
