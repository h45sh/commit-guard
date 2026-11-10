# Commit Guard: Review Checklist

This checklist details the non-negotiable inspection points across all 6 core pillars. When reviewing diffs, systematically evaluate every modified or added line against these criteria.

---

## Pillar 1: Dead, Bloat & Unnecessary Code (Top Priority)

Nothing lowers codebase velocity and reliability faster than accumulated bloat, speculative code, and forgotten debug artifacts. Treat dead code as a first-class blocker.

### 1.1 Stray Debug & Diagnostic Artifacts
- [ ] **Logging & Print Statements**: Are there leftover `console.log`, `print()`, `printf`, `System.out.println`, `fmt.Println`, `logger.debug` intended only for local troubleshooting?
- [ ] **Debugger Breakpoints**: Look for `debugger;`, `breakpoint()`, `binding.pry`, `import pdb; pdb.set_trace()`.
- [ ] **Dumps & Traces**: Check for `var_dump`, `dd()`, `p!()`, `console.trace()`.
- [ ] **Temporary Revert Markers**: Any `TODO: remove`, `TODO: revert before commit`, `HACK: test only`?
- [ ] **Test Bypass Flags**: Are there test-suite bypasses like `it.only(`, `describe.only(`, `@pytest.mark.skip`, `@Ignore` left enabled?

### 1.2 Dead, Unused & Orphaned Logic
- [ ] **Unused Imports & Dependencies**: Are there newly added imports, modules, or dependencies that are never referenced?
- [ ] **Orphaned Functions & Variables**: Are there helper functions, local variables, or constants declared but never called?
- [ ] **Unreachable Code**: Are there branches after early `return`, `throw`, `exit()`, or impossible conditionals (e.g. `if (false)`)?
- [ ] **Commented-Out Code**: Never keep commented-out code blocks in commits. Git history preserves past code. Delete commented-out blocks immediately.

### 1.3 Over-Engineering & Speculative Generality (YAGNI)
- [ ] **Premature Abstraction**: Has a one-off task been over-engineered into a generic multi-tiered factory, interface, or strategy pattern without immediate need?
- [ ] **Pass-Through Indirection**: Are there functions or classes whose only job is to forward arguments to another function without adding logic, transformation, or invariant checking? Apply the **Deletion Test**: if deleting it removes complexity without moving it elsewhere, delete it.
- [ ] **Speculative Parameters & Configurations**: Are there unused function arguments or configuration options added "just in case we need it later"?
- [ ] **Unnecessary State**: Is mutable state being tracked that could be computed derived state or passed directly?

### 1.4 Code Duplication
- [ ] **Existing Utilities**: Does the change introduce a helper function (e.g., date parsing, string manipulation, deep clone, debounce) that already exists in the project's utility modules or standard libraries?

---

## Pillar 2: Security & Cryptography Hygiene

### 2.1 Secrets & Credential Exposure
- [ ] **Hardcoded Secrets**: Check for API keys, bearer tokens, OAuth client secrets, private RSA/SSH keys, webhook secrets, database passwords.
- [ ] **Environment Leakage**: Are `.env`, `.env.local`, credentials files, or local certificates accidentally staged or untracked?
- [ ] **Client-Side Secret Exposure**: Are backend tokens or sensitive environment variables exposed to frontend bundles (e.g. prefixes like `NEXT_PUBLIC_`, `VITE_` containing non-public keys)?

### 2.2 Cryptographic Standards (NIST SP 800-175B Compliance)
- [ ] **No Weak Hashes for Security**: MD5 and SHA-1 must NEVER be used for security purposes, passwords, digital signatures, or integrity verification. Use SHA-256, SHA-384, SHA-512, or SHA-3.
- [ ] **No Broken Ciphers or Insecure Modes**: DES, 3DES, RC4, and Blowfish are forbidden. AES must NEVER be used in ECB mode (e.g., `AES-ECB`). Always use authenticated encryption (AEAD) like `AES-256-GCM` or `ChaCha20-Poly1305`.
- [ ] **Cryptographically Secure Randomness**: For tokens, session IDs, IVs, and salts, never use pseudo-random generators (e.g., `Math.random()`, Python `random.random()`, C `rand()`). Use CSPRNGs (`crypto.randomBytes()`, `secrets.token_bytes()`, `/dev/urandom`).
- [ ] **Password Storage**: Passwords must never be stored plaintext or hashed with plain SHA/MD5. Use Argon2id (recommended), bcrypt, or scrypt with adequate work factors.
- [ ] **IV & Salt Uniqueness**: Initialization vectors (IVs) for AES-GCM must never be reused with the same key. Generate fresh random 96-bit IVs for each encryption operation.

### 2.3 Injection & Boundary Validation
- [ ] **SQL Injection**: Are database queries constructed using raw string concatenation or template literals rather than parameterized queries / prepared statements?
- [ ] **Command Injection**: Look for `child_process.exec()`, `os.system()`, `subprocess.Popen(..., shell=True)` with untrusted inputs.
- [ ] **Path Traversal**: Are file paths constructed from user input without sanitization against `../` or without resolving against a trusted root directory?
- [ ] **XSS & Template Injection**: Is unescaped user content rendered directly into HTML, DOM elements (`dangerouslySetInnerHTML`), or template engines?
- [ ] **Unsafe Deserialization**: Avoid Python `pickle.loads()`, `yaml.load()` without `SafeLoader`, or Java deserialization on untrusted network payloads.

### 2.4 Authentication & Authorization
- [ ] **Missing Access Controls**: Does the change introduce new routes, endpoints, or RPC handlers without enforcing authentication middleware?
- [ ] **BOLA / IDOR (Broken Object-Level Authorization)**: When accessing records by ID (`/api/documents/:id`), does the code verify that the authenticated user owns or is authorized to view that specific record?
- [ ] **Role Escalation**: Can a user manipulate payload fields (e.g., passing `{ "role": "admin" }` or `{ "is_verified": true }`) in registration or profile updates?

---

## Pillar 3: Architectural & System Integrity

### 3.1 Layer & Boundary Discipline
- [ ] **Dependency Inversion**: Do lower-level layers (domain/core logic) depend on high-level modules (presentation/UI or infrastructure/DB drivers)?
- [ ] **Data Model Encapsulation**: Are internal database models (ORM entities, schema tables) leaking directly into external API responses without a dedicated DTO (Data Transfer Object) or serializer?
- [ ] **Circular Dependencies**: Has the change introduced cross-module imports that form a cycle?

### 3.2 Blast Radius & API Contracts
- [ ] **Scope Containment**: Do the changed files strictly correlate to the user's intended feature/fix, or have unrelated files been modified or formatted?
- [ ] **Breaking Changes to Public APIs**: Have function signatures, parameter orders, or return types of exported APIs changed without backward-compatible defaults or deprecation warnings?
- [ ] **Schema Migrations**: If database models were changed, is there a corresponding migration script included? Is the migration reversible and non-locking?

### 3.3 Concurrency & State Integrity
- [ ] **Race Conditions**: Are shared resources modified concurrently without locks, mutexes, or atomic transactions?
- [ ] **Non-Idempotent Handlers**: Are webhook or payment handlers vulnerable to duplicate deliveries because they lack idempotency keys?

---

## Pillar 4: Efficiency & Performance

### 4.1 Algorithmic Complexity & Loops
- [ ] **Nested Loop Traversal**: Are there $O(N^2)$ lookups (e.g., `array.find()` or `list.contains()` inside a `for` loop over another collection)? Use HashSets, Maps, or dictionaries for $O(1)$ lookups.
- [ ] **Unnecessary Object Duplication**: Are large data structures cloned repeatedly inside tight loops (`[...items]`, `Object.assign()`, `copy.deepcopy()`)?

### 4.2 Database & Network I/O
- [ ] **The N+1 Query Problem**: Are database queries triggered inside an iterative loop over parent records? Use batch fetching, `JOIN`s, or ORM preloading (`include`, `select_related`).
- [ ] **Missing Database Indexes**: Are new queries filtering (`WHERE`) or ordering (`ORDER BY`) on columns that lack database indexes on large tables?
- [ ] **Unbounded Queries**: Are queries missing `LIMIT` or pagination clauses, risking out-of-memory errors on large datasets?

### 4.3 Resource Lifecycle & Async Hygiene
- [ ] **Resource Cleanup**: Are file handles, database connections, streams, or sockets properly closed via `finally`, `using`, or context managers (`with` in Python)?
- [ ] **Sync Calls in Async Contexts**: Are synchronous blocking operations (e.g., `fs.readFileSync`, `time.sleep()`) used inside async event loops or HTTP request threads?
- [ ] **Memory Leaks**: Are event listeners, timers, or subscriptions registered without corresponding cleanup on teardown or unmount?

---

## Pillar 5: Code Design & Robustness

### 5.1 Error Handling Discipline
- [ ] **No Swallowed Exceptions**: Never use silent empty catch blocks (`catch (e) {}` or `except: pass`). Either handle the error, log with context, or re-throw.
- [ ] **Descriptive Errors**: Are custom errors informative? Do they preserve the underlying cause (`throw new CustomError(..., { cause: err })`)?
- [ ] **Fail Fast**: Are input arguments and preconditions validated at the boundary before executing heavy business logic?

### 5.2 Type Safety & Clean Code
- [ ] **Type Precision**: Avoid escaping types with `any`, `Object`, or untyped dictionaries when a structured interface or type is appropriate.
- [ ] **Naming Clarity**: Are variable and function names self-describing, avoiding abbreviations or misleading names?

---

## Pillar 6: Test Coverage & Regression Guard

### 6.1 Test Discipline
- [ ] **Coverage of New Paths**: Are both happy paths and edge/error cases covered with unit or integration tests?
- [ ] **Preservation of Existing Tests**: Were any existing tests deleted, bypassed, or modified to make a broken build pass?
- [ ] **Deterministic Tests**: Do new tests avoid relying on external network calls, system clocks, or race-prone sleep timers?

---

## Pillar 7: Documentation & Contract Completeness

*(See [DOCUMENTATION.md](DOCUMENTATION.md) for full formatting rules and templates)*

### 7.1 In-Code Documentation & Docstrings
- [ ] **Public Interface Commentary**: Are all newly exported functions, methods, classes, and types documented with parameter descriptions, return types, and possible exceptions/errors (following Google Python Style, TSDoc, Rustdoc, or GoDoc)?
- [ ] **Invariants & Edge Cases**: Are non-obvious algorithms, security boundaries, or concurrency locks documented with inline commentary explaining *why* the implementation was chosen?

### 7.2 API Contracts & Schema Synchronization
- [ ] **OpenAPI / Swagger Sync**: If HTTP endpoints or payloads changed, is `openapi.yaml` or Swagger specification updated?
- [ ] **Schema Migrations & Models**: Are GraphQL SDL, Protobuf definitions, or database models synchronized with the code changes?
- [ ] **Deprecation Notices**: Are deprecated functions or fields marked with `@deprecated` tags stating migration alternatives?

### 7.3 System & Architectural Documentation
- [ ] **Architecture Decision Records (ADRs)**: If introducing a new library, persistence layer, or structural pattern, is an ADR included in `docs/adr/`?
- [ ] **README & Configuration Updates**: If new environment variables, configuration flags, or setup prerequisites were introduced, are they documented in `README.md`?
- [ ] **Changelog**: Is `CHANGELOG.md` updated under `## [Unreleased]` using [Keep a Changelog](https://keepachangelog.com/) standards?
