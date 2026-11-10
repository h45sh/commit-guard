# Commit Guard: Subsystem & Domain Guides

When changes touch specific application architectures, frameworks, or deployment infrastructure, apply these specialized domain checks in addition to the core checklist.

---

## 1. AI, LLM & Agent Implementations

When changes involve prompt generation, LLM APIs, agent orchestration, or tool calling:

### 1.1 Prompt Injection & Boundary Security
- [ ] **System vs. User Delimitation**: Are user inputs strictly separated from system instructions using structured formats, role separation (`role: "user"` vs `role: "system"`), or XML/markdown delimiters?
- [ ] **Indirect Prompt Injection**: When fetching web content, emails, user documents, or database records for RAG (Retrieval Augmented Generation), is untrusted content treated as untrusted rather than executable instructions?
- [ ] **Instruction Leakage**: Does the prompt include proprietary business rules or internal credentials that could be extracted via jailbreaks?

### 1.2 Tool Calling & Agentic Safety
- [ ] **Tool Parameter Validation**: Are function-calling arguments treated with the same validation and sanitization rigor as external HTTP requests?
- [ ] **Dangerous Tool Sinks**: Are tools that execute shell commands, file modifications, SQL queries, or financial transactions gated behind explicit authorization and confirmation checks?
- [ ] **Execution Bounds**: Are autonomous loops bounded by strict iteration counters (`max_iterations = 10`), timeout limits, and cumulative spend quotas to prevent runaway cost or infinite loops?

### 1.3 Context & Token Hygiene
- [ ] **Context Window Bloat**: Are full unpruned documents or massive database dumps passed into context when only specific chunks are required?
- [ ] **Secret Scrubbing**: Are logs, error traces, or credentials stripped before data is sent to external LLM provider APIs?

---

## 2. Infrastructure, Containers & CI/CD

When changes touch Dockerfiles, CI workflows, Terraform, Kubernetes, or deployment scripts:

### 2.1 Docker & Container Security
- [ ] **Non-Root Execution**: Does the Dockerfile create and switch to a non-privileged user (`USER appuser`) before the `ENTRYPOINT`/`CMD`?
- [ ] **Base Image Pinning**: Are base images pinned to specific version tags or digests (`node:20.11.0-alpine` or `@sha256:...`) rather than floating `:latest`?
- [ ] **Build Secret Hygiene**: Are API keys or tokens passed using `RUN --mount=type=secret` instead of `ARG` or `ENV` (which leak permanently into image layer history)?
- [ ] **Context Minimization**: Is `.dockerignore` updated to exclude `.git`, `node_modules`, `.env`, tests, and local build artifacts?

### 2.2 CI/CD Pipeline Security (GitHub Actions, GitLab CI)
- [ ] **Unsafe PR Triggers**: Does the workflow use `pull_request_target` alongside checking out untrusted fork code? (This allows untrusted PRs to execute arbitrary commands with access to repository secrets).
- [ ] **Script Injection in Workflows**: Are user-controlled context values (e.g., `${{ github.event.issue.title }}`) interpolated directly into inline `run:` shell scripts instead of passed via environment variables?
- [ ] **Action Pinning**: Are third-party GitHub Actions pinned to immutable full commit SHAs rather than mutable branch/release tags (e.g. `actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11` # v4.1.1)?

### 2.3 Cloud & Infrastructure as Code (Terraform / K8s)
- [ ] **Least Privilege IAM**: Do IAM policies grant wildcard permissions (`"Action": "*"` or `"Resource": "*"`)?
- [ ] **Public Exposure**: Are S3 buckets, GCS buckets, or database instances configured as publicly readable/writable?
- [ ] **Resource Limits**: Do Kubernetes Pod manifests declare explicit `resources.limits` and `resources.requests` for CPU and memory to prevent noisy neighbor exhaustion?

---

## 3. APIs, Microservices & Networking

When changes expose or consume REST, GraphQL, gRPC, or Webhook interfaces:

### 3.1 Idempotency & Mutations
- [ ] **Idempotent Mutations**: Do state-changing endpoints (especially payments, orders, balance transfers) support idempotency keys (`Idempotency-Key` header) to safely handle network retries?
- [ ] **Safe HTTP Verbs**: Are `GET`, `HEAD`, and `OPTIONS` strictly read-only and side-effect free?

### 3.2 Resilience & Network Hygiene
- [ ] **Mandatory Timeouts**: Does every outgoing HTTP request, gRPC call, or socket connection specify explicit connection and read timeouts? Never allow infinite network blocking.
- [ ] **Payload Limits**: Are request body parser limits enforced (e.g. max 1MB JSON body) to prevent memory denial-of-service?
- [ ] **Rate Limiting**: Are public or authenticated endpoints protected by rate limiters to prevent brute-force attacks and resource exhaustion?

### 3.3 Webhooks & Callbacks
- [ ] **Signature Verification**: Does incoming webhook handling verify HMAC signatures (e.g. Stripe, GitHub, Twilio) against the raw payload before parsing JSON?
- [ ] **SSRF Prevention**: If the application fetches URLs provided by users (e.g., custom webhooks, link unfurling), is there validation blocking internal/private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `169.254.169.254`) and DNS rebinding?

---

## 4. Concurrency, State & Memory

When changes involve threads, async tasks, locks, caching, or high-throughput state:

### 4.1 Race Conditions & TOCTOU
- [ ] **Check-Then-Act Flaws**: Are resource availability checks and subsequent modifications performed non-atomically? (e.g., `if (balance >= amount) { balance -= amount; }` without database row locking or atomic increments).
- [ ] **File Operation TOCTOU**: Checking file existence before opening rather than opening with atomic flags (`O_CREAT | O_EXCL`).

### 4.2 Resource Leaks & Deadlocks
- [ ] **Lock Ordering**: If multiple locks or mutexes are acquired, is a consistent global acquisition order enforced to prevent deadlocks?
- [ ] **Async Promise / Goroutine Leaks**: Are asynchronous promises, Go channels, or workers guaranteed to terminate, or can an unhandled error leave them hanging indefinitely?
- [ ] **Unbounded Caches**: Are in-memory caches configured with maximum capacities (LRU/LFU) and TTL expiration to prevent memory ballooning?

---

## 5. Web Frontend, Mobile & Accessibility (WCAG 2.1/2.2)

When changes modify web UI components, HTML templates, or mobile views:

### 5.1 Accessibility (WCAG 2.1 AA)
- [ ] **Alternative Text**: Do all meaningful `<img>` elements include descriptive `alt` attributes (and `alt=""` for purely decorative images)?
- [ ] **Keyboard Navigation**: Can all interactive widgets (dialogs, menus, tabs, accordions) be focused and activated via keyboard alone (`Tab`, `Enter`, `Space`, `Escape`)?
- [ ] **Form Labels**: Does every `<input>`, `<select>`, and `<textarea>` have an associated `<label>` element with a matching `for`/`id` or an explicit `aria-label`?
- [ ] **Accessible Buttons**: Are interactive click handlers placed on semantic `<button>` elements rather than plain `<div>` or `<span>` without keyboard handlers and `role="button"`?

### 5.2 Client-Side Security & State
- [ ] **DOM XSS**: Avoid assigning untrusted data to `innerHTML`, `outerHTML`, `document.write()`, or `href="javascript:..."`.
- [ ] **Third-Party Messaging**: Do `window.postMessage` listeners validate `event.origin` before acting on message payloads?
- [ ] **Open Redirects**: Are client-side redirects (`window.location = redirectUrl`) restricted to relative paths or validated against a domain allowlist?
