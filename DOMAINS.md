# Code Guard: Subsystem & Domain Guides

When changes or codebase audits touch specific application architectures, frameworks, scaling tiers, or deployment infrastructure, apply these specialized domain checks in addition to the core checklist.

---

## 1. AI, LLM & Agent Implementations

When changes involve prompt generation, LLM APIs, agent orchestration, or tool calling:

### 1.1 Prompt Injection & Boundary Security
- [ ] **System vs. User Delimitation**: User inputs strictly separated from system instructions using structured formats, role separation (`role: "user"` vs `role: "system"`), or XML/markdown delimiters.
- [ ] **Indirect Prompt Injection**: When fetching web content, emails, user documents, or database records for RAG (Retrieval Augmented Generation), untrusted content is treated as untrusted rather than executable instructions.
- [ ] **Instruction Leakage**: Prompts do not leak proprietary business rules or internal credentials that could be extracted via jailbreaks.

### 1.2 Tool Calling & Agentic Safety
- [ ] **Tool Parameter Validation**: Function-calling arguments validated and sanitized with the same rigor as external HTTP requests.
- [ ] **Dangerous Tool Sinks**: Tools that execute shell commands, file modifications, SQL queries, or financial transactions gated behind explicit authorization and confirmation checks.
- [ ] **Execution Bounds**: Autonomous loops bounded by strict iteration counters (`max_iterations = 10`), timeout limits, and cumulative spend quotas to prevent runaway cost or infinite loops.

### 1.3 Context & Token Hygiene
- [ ] **Context Window Bloat**: Full unpruned documents or massive database dumps avoided when only specific chunks are required.
- [ ] **Secret Scrubbing**: Logs, error traces, or credentials stripped before data is sent to external LLM provider APIs.

---

## 2. Infrastructure, Containers & CI/CD

When changes touch Dockerfiles, CI workflows, Terraform, Kubernetes, or deployment scripts:

### 2.1 Docker & Container Security
- [ ] **Non-Root Execution**: Dockerfile creates and switches to a non-privileged user (`USER appuser`) before the `ENTRYPOINT`/`CMD`.
- [ ] **Base Image Pinning**: Base images pinned to specific version tags or digests (`node:20.11.0-alpine` or `@sha256:...`) rather than floating `:latest`.
- [ ] **Build Secret Hygiene**: API keys or tokens passed using `RUN --mount=type=secret` instead of `ARG` or `ENV` (which leak permanently into image layer history).
- [ ] **Context Minimization**: `.dockerignore` updated to exclude `.git`, `node_modules`, `.env`, tests, and local build artifacts.

### 2.2 CI/CD Pipeline Security (GitHub Actions, GitLab CI)
- [ ] **Unsafe PR Triggers**: Workflows do not use `pull_request_target` alongside checking out untrusted fork code (which allows arbitrary command execution with access to repository secrets).
- [ ] **Script Injection in Workflows**: User-controlled context values (e.g., `${{ github.event.issue.title }}`) passed via environment variables, never interpolated directly into inline `run:` shell scripts.
- [ ] **Action Pinning**: Third-party GitHub Actions pinned to immutable full commit SHAs rather than mutable branch/release tags.

### 2.3 Cloud & Infrastructure as Code (Terraform / K8s)
- [ ] **Least Privilege IAM**: IAM policies do not grant wildcard permissions (`"Action": "*"` or `"Resource": "*"`).
- [ ] **Public Exposure**: S3 buckets, GCS buckets, or database instances configured as private.
- [ ] **Resource Limits**: Kubernetes Pod manifests declare explicit `resources.limits` and `resources.requests` for CPU and memory.

---

## 3. APIs, Microservices & Networking

When changes expose or consume REST, GraphQL, gRPC, or Webhook interfaces:

### 3.1 Idempotency & Mutations
- [ ] **Idempotent Mutations**: State-changing endpoints (especially payments, orders, balance transfers) support idempotency keys (`Idempotency-Key` header) to safely handle network retries.
- [ ] **Safe HTTP Verbs**: `GET`, `HEAD`, and `OPTIONS` strictly read-only and side-effect free.

### 3.2 Resilience & Network Hygiene
- [ ] **Mandatory Timeouts**: Every outgoing HTTP request, gRPC call, or socket connection specifies explicit connection and read timeouts. Never allow infinite network blocking.
- [ ] **Payload Limits**: Request body parser limits enforced (e.g. max 1MB JSON body) to prevent memory denial-of-service.
- [ ] **Rate Limiting**: Public or authenticated endpoints protected by rate limiters to prevent brute-force attacks and resource exhaustion.

### 3.3 Webhooks & Callbacks
- [ ] **Signature Verification**: Incoming webhook handling verifies HMAC signatures (e.g. Stripe, GitHub, Twilio) against the raw payload before parsing JSON.
- [ ] **SSRF Prevention**: URL fetching (custom webhooks, link unfurling) validates and blocks internal/private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.169.254`) and DNS rebinding.

---

## 4. Concurrency, State & Memory

When changes involve threads, async tasks, locks, caching, or high-throughput state:

### 4.1 Race Conditions & TOCTOU
- [ ] **Check-Then-Act Flaws**: Resource availability checks and subsequent modifications performed atomically (using database row locking, mutexes, or atomic increments).
- [ ] **File Operation TOCTOU**: Checking file existence before opening rather than opening with atomic flags (`O_CREAT | O_EXCL`).

### 4.2 Resource Leaks & Deadlocks
- [ ] **Lock Ordering**: Multiple locks or mutexes acquired in a consistent global acquisition order to prevent deadlocks.
- [ ] **Async Promise / Goroutine Leaks**: Asynchronous promises, Go channels, or worker routines guaranteed to terminate on error.
- [ ] **Unbounded Caches**: In-memory caches configured with maximum capacities (LRU/LFU) and TTL expiration to prevent memory ballooning.

---

## 5. Web Frontend, Mobile & Accessibility (WCAG 2.1/2.2)

When changes modify web UI components, HTML templates, or mobile views:

### 5.1 Accessibility (WCAG 2.1 AA)
- [ ] **Alternative Text**: Meaningful `<img>` elements include descriptive `alt` attributes (`alt=""` for purely decorative images).
- [ ] **Keyboard Navigation**: Interactive widgets (dialogs, menus, tabs, accordions) focusable and operable via keyboard alone (`Tab`, `Enter`, `Space`, `Escape`).
- [ ] **Form Labels**: Every `<input>`, `<select>`, and `<textarea>` has an associated `<label>` element with a matching `for`/`id` or an explicit `aria-label`.
- [ ] **Accessible Buttons**: Interactive click handlers placed on semantic `<button>` elements rather than plain `<div>` or `<span>` without keyboard handlers and `role="button"`.

### 5.2 Client-Side Security & State
- [ ] **DOM XSS**: Avoid assigning untrusted data to `innerHTML`, `outerHTML`, `document.write()`, or `href="javascript:..."`.
- [ ] **Third-Party Messaging**: `window.postMessage` listeners validate `event.origin` before acting on message payloads.
- [ ] **Open Redirects**: Client-side redirects restricted to relative paths or validated against a domain allowlist.

---

## 6. Enterprise Architecture, Codebase Scaling & Seams (50k - 500k+ Lines)

When inspecting whole repositories or scaling modular architectures past 50,000 lines:

### 6.1 Architectural Boundary & DAG Layer Enforcement
- [ ] **Directed Acyclic Graph (DAG) Layering**:
  - Configure `.codeguard.json` with explicit layer import permissions (e.g., `schemas` cannot import `engine`, `engine` cannot import `ui`).
  - No upward layer imports: enforce in CI and local audits.
- [ ] **Zero Circular Package Dependencies**:
  - Module import graphs must contain zero cycles. If package A imports B, B cannot directly or indirectly import A.
- [ ] **Clean Seam Facades**:
  - Complex subsystems (e.g. execution engines, graph databases, auth managers) expose a single, high-leverage facade. Callers do not bypass the facade to touch internal classes.

### 6.2 Pure Domain Core vs. Imperative Shell
- [ ] **Purity Isolation**:
  - All parsing, business decision logic, security scoring, and recommendation rules placed in pure modules (`rules/`, `domain/`, `parsers/`).
  - Pure modules accept raw data and return structured values. They must never import database drivers, socket clients, or invoke `subprocess.run()`.
- [ ] **Defensive Plugin Sandboxes**:
  - Tools, adapters, or integration scripts run in isolated sub-processes or sandboxes. A failure, timeout, or invalid output in one tool must never crash the host application.

### 6.3 Forward-Only Database Migrations & Schema Drift
- [ ] **Zero Untracked Mutations**:
  - Production schemas must never be altered via raw `ALTER TABLE` or ad-hoc SQL executions.
  - Every schema change must have a corresponding, numbered, forward-only migration file (e.g., `migrations/001_initial.sql`, `migrations/002_add_index.sql`).
- [ ] **Backwards Compatibility**:
  - Migrations must be non-locking and backwards-compatible with active application instances (e.g. add columns as nullable; deprecate before dropping).

### 6.4 Test Suite Speed Budgets
- [ ] **Two-Tier Test Partitioning**:
  - **Tier 1 (Pure Unit Suite)**: Must complete in $<2$ seconds total. Covers schemas, parsers, and rules purely in-memory. Zero network, zero disk I/O, zero mocks.
  - **Tier 2 (Integration Suite)**: Subprocess execution, database persistence, and UI pilot flows must complete in $<60$ seconds with deterministic teardown.
- [ ] **Zero Sleep Pollution**:
  - No `time.sleep()`, `setTimeout()`, or `sleep()` calls in test suites. All waits must be event-driven or timeout-bounded pollers.

### 6.5 Churn & Hotspot Risk Prioritization
- [ ] **Hotspot Risk Scoring**:
  - Prioritize architectural deepening on modules with high churn and high complexity ($Risk = Churn \times Complexity$). Deepening stable, low-churn files is low ROI; deepening high-churn hotspot files pays immediate compound returns.
