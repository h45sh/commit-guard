#!/usr/bin/env python3
"""
code_guard.py - Full-Lifecycle Codebase & Commit Integrity Auditor
Part of the code-guard skill (formerly commit-guard).

Operates in two modes:
  1. inspect-commit (mode=commit): Fast pre-commit/PR gate auditing git diffs.
  2. inspect-codebase (mode=codebase): Deep whole-codebase architectural & entropy audit.
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Universal Heuristic Rules (scanned on added lines in diffs or source files)
UNIVERSAL_RULES = [
    # 1. Debug Statements & Artifacts
    {
        "id": "DEBUG_CONSOLE_LOG",
        "category": "Pillar 1: Dead/Debug Code",
        "severity": "BLOCK",
        "description": "Leftover console.log statement",
        "code_only": True,
        "regex": re.compile(r"console\.(log|debug|info|trace|dir)\s*\("),
    },
    {
        "id": "DEBUG_PYTHON_PRINT",
        "category": "Pillar 1: Dead/Debug Code",
        "severity": "WARN",
        "description": "print() call detected (verify if intended for CLI output or leftover debug)",
        "file_ext": [".py"],
        "code_only": True,
        "regex": re.compile(r"^\s*print\s*\("),
    },
    {
        "id": "DEBUGGER_BREAKPOINT",
        "category": "Pillar 1: Dead/Debug Code",
        "severity": "BLOCK",
        "description": "Debugger breakpoint left in code",
        "code_only": True,
        "regex": re.compile(r"\b(debugger;|breakpoint\(\)|binding\.pry|import pdb; pdb\.set_trace\(\))"),
    },
    {
        "id": "DEBUG_DUMP_CALL",
        "category": "Pillar 1: Dead/Debug Code",
        "severity": "BLOCK",
        "description": "Leftover diagnostic dump function",
        "code_only": True,
        "regex": re.compile(r"\b(var_dump|dd|p!)\s*\(|(?<!\.)\bdump\s*\("),
    },
    {
        "id": "TEST_BYPASS_FLAG",
        "category": "Pillar 1: Dead/Debug Code",
        "severity": "BLOCK",
        "description": "Focused test runner bypass flag (skips other tests)",
        "code_only": True,
        "regex": re.compile(r"\b(it\.only|describe\.only|test\.only|fit\(|fdescribe\()\b"),
    },
    {
        "id": "TODO_REVERT_MARKER",
        "category": "Pillar 1: Dead/Debug Code",
        "severity": "BLOCK",
        "description": "Temporary revert or removal marker",
        "code_only": True,
        "regex": re.compile(r"TODO\s*:\s*(revert|remove|temporary|hack before commit)", re.IGNORECASE),
    },

    # 2. Hardcoded Secrets & Credentials
    {
        "id": "SECRET_PRIVATE_KEY",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Exposed private key",
        "regex": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    },
    {
        "id": "SECRET_AWS_KEY",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Potential AWS Access Key ID",
        "regex": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    },
    {
        "id": "SECRET_GITHUB_TOKEN",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Potential GitHub token",
        "regex": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"),
    },
    {
        "id": "SECRET_GOOGLE_KEY",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Potential Google API Key",
        "regex": re.compile(r"\bAIza[0-9A-Za-z\\-_]{35}\b"),
    },
    {
        "id": "SECRET_STRIPE_KEY",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Live Stripe Secret or Restricted API Key",
        "regex": re.compile(r"\b(sk_live|rk_live)_[0-9a-zA-Z]{24,}\b"),
    },
    {
        "id": "SECRET_SLACK_TOKEN",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Slack API / Bot Token",
        "regex": re.compile(r"\bxox[baprs]-[0-9a-zA-Z]{10,}\b"),
    },
    {
        "id": "SECRET_GENERIC_KEY",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Hardcoded secret, password, or bearer token assignment",
        "regex": re.compile(r"(password|passwd|secret|api_key|apikey|bearer)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]", re.IGNORECASE),
    },

    # 3. Cryptography & Injection Hygiene
    {
        "id": "CRYPTO_WEAK_HASH",
        "category": "Pillar 2: Security & Crypto",
        "severity": "BLOCK",
        "description": "Insecure hash function (MD5/SHA-1) in cryptographic context",
        "code_only": True,
        "regex": re.compile(r"(createHash|hashlib\.)\s*\(?['\"](md5|sha1)['\"]", re.IGNORECASE),
    },
    {
        "id": "CRYPTO_INSECURE_CIPHER",
        "category": "Pillar 2: Security & Crypto",
        "severity": "BLOCK",
        "description": "Insecure cipher mode (DES, RC4, or AES-ECB)",
        "code_only": True,
        "regex": re.compile(r"['\"](des|3des|rc4|blowfish|aes-[0-9]{3}-ecb)['\"]", re.IGNORECASE),
    },
    {
        "id": "INJECTION_RAW_SQL",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Potential raw SQL string concatenation or unescaped interpolation",
        "code_only": True,
        "regex": re.compile(r"(f['\"]SELECT\s+.*\{|['\"]SELECT\s+.*['\"]\s*\+\s*|query\s*=\s*['\"]SELECT\s+.*['\"]\s*%)", re.IGNORECASE),
    },
    {
        "id": "INJECTION_COMMAND_SHELL",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Dangerous shell execution invocation",
        "code_only": True,
        "regex": re.compile(r"(os\.system\s*\(|subprocess\.(Popen|run|call)\s*\(.*shell\s*=\s*True|child_process\.exec\s*\()"),
    },
    {
        "id": "UNSAFE_DESERIALIZATION",
        "category": "Pillar 2: Security",
        "severity": "BLOCK",
        "description": "Unsafe payload deserialization (pickle, un-safe yaml, or Marshal)",
        "code_only": True,
        "regex": re.compile(r"(pickle\.loads?\s*\(|yaml\.load\s*\([^,)]*\)|Marshal\.load\s*\()"),
    },

    # 4. Architectural & System Integrity
    {
        "id": "GIT_CONFLICT_MARKER",
        "category": "Pillar 3: System Integrity",
        "severity": "BLOCK",
        "description": "Unresolved Git merge conflict marker",
        "code_only": False,
        "regex": re.compile(r"^(<{7}|={7}|>{7})(\s|$)"),
    },
    {
        "id": "PRIVATE_STATE_LEAK_REGEX",
        "category": "Pillar 3: Architecture & Seams",
        "severity": "BLOCK",
        "description": "External access to private attribute/method (violates clean seams)",
        "code_only": True,
        "regex": re.compile(r"\b(?!(?:self|cls)\b)[a-zA-Z0-9_]+\._(?!_)[a-zA-Z0-9_]+\b"),
    },
    {
        "id": "TEST_FLAKY_SLEEP",
        "category": "Pillar 6: Tests & Speed Budget",
        "severity": "WARN",
        "description": "Arbitrary sleep call in test (violates test speed budget & causes flakiness)",
        "code_only": True,
        "regex": re.compile(r"\b(time\.sleep|asyncio\.sleep|sleep|setTimeout)\s*\(\s*[0-9]+"),
    },
    {
        "id": "UNTRACKED_SCHEMA_MUTATION",
        "category": "Pillar 3: Architecture & Migrations",
        "severity": "WARN",
        "description": "Direct DDL schema mutation detected (verify if versioned migration is included)",
        "code_only": True,
        "regex": re.compile(r"\b(ALTER\s+TABLE|CREATE\s+TABLE(?!\s+IF\s+NOT\s+EXISTS)|DROP\s+TABLE)\b", re.IGNORECASE),
    },

    # 5. Robustness & Anti-Patterns
    {
        "id": "SWALLOWED_EXCEPTION_PY",
        "category": "Pillar 5: Robustness",
        "severity": "WARN",
        "description": "Silent swallowed exception (except: pass)",
        "file_ext": [".py"],
        "code_only": True,
        "regex": re.compile(r"except(\s+\w+)?\s*:\s*pass\b"),
    },
    {
        "id": "SWALLOWED_EXCEPTION_JS",
        "category": "Pillar 5: Robustness",
        "severity": "WARN",
        "description": "Empty catch block silently swallowing error",
        "file_ext": [".js", ".ts", ".jsx", ".tsx"],
        "code_only": True,
        "regex": re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}"),
    },
]

# Suppression comment regexes (line and file level)
SUPPRESSION_PATTERNS = [
    re.compile(r"#\s*codeguard\s*:\s*(?:ignore|disable)\[([a-zA-Z0-9_,\s]+)\]"),
    re.compile(r"//\s*codeguard-(?:ignore|disable)\s+([a-zA-Z0-9_,\s]+)"),
    re.compile(r"<!--\s*codeguard-(?:ignore|disable)\s+([a-zA-Z0-9_,\s]+)\s*-->"),
]

FILE_SUPPRESSION_PATTERNS = [
    re.compile(r"#\s*codeguard\s*:\s*(?:ignore-file|disable-file|disable)[=\[]\s*([a-zA-Z0-9_,\s]+)\]?"),
    re.compile(r"//\s*codeguard-(?:ignore-file|disable-file|disable)\s+([a-zA-Z0-9_,\s]+)"),
    re.compile(r"<!--\s*codeguard-(?:ignore-file|disable-file|disable)\s+([a-zA-Z0-9_,\s]+)\s*-->"),
]

CODE_EXTENSIONS = {
    ".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".cpp",
    ".h", ".hpp", ".rb", ".php", ".cs", ".swift", ".kt", ".scala", ".sh", ".bash"
}

TEST_DIR_PATTERNS = [
    "/test/", "/tests/", "/spec/", "/specs/", "/fixtures/", "/mocks/",
    "test_", "_test.", ".spec.", "fixture_", "mock_"
]

COMPAT_FILE_PATTERNS = [
    "compat.py", "_compat.py", "/compat/",
    "shim.py", "_shim.py", "shims.py", "/shims/",
    "patch.py", "_patch.py", "patches.py", "/patches/",
    "polyfill.py", "polyfills.py", "/polyfills/",
    "/vendor/", "vendor.py"
]

STDLIB_AND_FRAMEWORK_WHITELIST_NAMES = {
    "argparse", "sys", "os", "typing", "dataclasses", "inspect", "unittest",
    "mock", "ctypes", "threading", "multiprocessing", "importlib", "asyncio", "_ast"
}

STDLIB_PROTECTED_ATTRS = {
    "_SubParsersAction", "_ActionsContainer", "_ArgumentGroup", "_MutuallyExclusiveGroup",
    "_actions", "_option_string_actions", "_defaults", "_negative_number_matcher",
    "_getframe", "_current_frames", "_exit",
    "_GenericAlias", "_SpecialForm", "_MISSING_TYPE",
    "_mock_return_value", "_mock_self", "_WritelnDecorator",
    "_fields", "_asdict", "_replace", "_source",  # namedtuple protected methods
}

EXCLUDED_ATTRIBUTES = {
    "__name__", "__class__", "__doc__", "__dict__", "__module__", "__mro__",
    "__qualname__", "__file__", "__path__", "__package__", "__wrapped__"
}


def is_compat_file(file_path: str) -> bool:
    normalized = (file_path or "").lower().replace("\\", "/")
    return any(p in normalized for p in COMPAT_FILE_PATTERNS)


def is_test_file(file_path: str) -> bool:
    normalized = (file_path or "").lower().replace("\\", "/")
    return any(p in normalized for p in TEST_DIR_PATTERNS)


def run_git(args: List[str], cwd: str) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 1, "", "git executable not found in PATH."


def is_suppressed(line: str, rule_id: str) -> bool:
    for pattern in SUPPRESSION_PATTERNS:
        match = pattern.search(line)
        if match:
            ignored_rules = [r.strip() for r in match.group(1).split(",")]
            if rule_id in ignored_rules or "all" in ignored_rules:
                return True
    return False


def extract_file_suppressed_rules(content_or_lines: Union[str, List[str]]) -> Set[str]:
    lines = content_or_lines if isinstance(content_or_lines, list) else content_or_lines.splitlines()[:25]
    suppressed = set()
    for line in lines[:25]:
        for pattern in FILE_SUPPRESSION_PATTERNS:
            match = pattern.search(line)
            if match:
                for r in match.group(1).split(","):
                    suppressed.add(r.strip())
    return suppressed


def is_file_suppressed(content: str, rule_id: str) -> bool:
    suppressed = extract_file_suppressed_rules(content)
    return rule_id in suppressed or "all" in suppressed


def is_config_ignored(config: Dict[str, Any], file_path: str, rule_id: str) -> bool:
    ignores = config.get("ignore", {})
    normalized = file_path.replace("\\", "/")
    for pattern, rules in ignores.items():
        if pattern == normalized or (pattern.endswith("/") and normalized.startswith(pattern)) or (pattern in normalized):
            if isinstance(rules, list):
                if rule_id in rules or "all" in rules:
                    return True
            elif isinstance(rules, str):
                if rule_id == rules or rules == "all":
                    return True
    return False


def load_codeguard_config(cwd: str) -> Dict[str, Any]:
    config_paths = [Path(cwd) / ".codeguard.json", Path(cwd) / "codeguard.json"]
    for path in config_paths:
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not parse {path}: {e}", file=sys.stderr)
    return {}


def load_baseline(baseline_file: str) -> Set[str]:
    if not os.path.isfile(baseline_file):
        return set()
    try:
        with open(baseline_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("fingerprints", []))
    except Exception:
        return set()


def compute_violation_fingerprint(v: Dict[str, Any]) -> str:
    # Stable fingerprint based on file, rule, and snippet (without line number)
    return f"{v.get('file')}:{v.get('rule_id')}:{v.get('line_content', '').strip()}"


# ==============================================================================
# AST & Deep Architectural Verification (Python)
# ==============================================================================

def verify_python_ast(file_path: str, content: str, pure_paths: List[str], layer_rules: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    violations = []
    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        return violations

    cfg = config or {}
    lines = content.splitlines()

    is_test = is_test_file(file_path)
    is_compat = is_compat_file(file_path)
    is_pure_path = any(pure_path in file_path for pure_path in pure_paths) or any(
        kw in file_path.lower() for kw in ["/rules/", "/validators/", "/parsers/"]
    )

    BANNED_PURE_IMPORTS = {"sqlite3", "psycopg2", "sqlalchemy", "requests", "httpx", "aiohttp", "subprocess", "socket"}

    # Find linenos inside `if TYPE_CHECKING:` blocks to avoid flagging static type annotations
    type_checking_linenos = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.If):
            test_id = ""
            if isinstance(n.test, ast.Name):
                test_id = n.test.id
            elif isinstance(n.test, ast.Attribute):
                test_id = n.test.attr
            if test_id == "TYPE_CHECKING":
                for child in ast.walk(n):
                    if hasattr(child, "lineno"):
                        type_checking_linenos.add(child.lineno)

    # Collect symbols defined locally in this file (intra-module exemption)
    locally_defined_symbols = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            locally_defined_symbols.add(n.name)

    for node in ast.walk(tree):
        # 1. Check for impure imports inside designated pure domains (skip if in TYPE_CHECKING)
        if is_pure_path and getattr(node, "lineno", 0) not in type_checking_linenos:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    is_impure = root_mod in BANNED_PURE_IMPORTS or alias.name == "urllib.request"
                    if is_impure:
                        line_str = lines[node.lineno - 1] if 0 < node.lineno <= len(lines) else ""
                        if is_suppressed(line_str, "IMPURE_DOMAIN_LOGIC") or is_file_suppressed(content, "IMPURE_DOMAIN_LOGIC") or is_config_ignored(cfg, file_path, "IMPURE_DOMAIN_LOGIC"):
                            continue
                        violations.append({
                            "rule_id": "IMPURE_DOMAIN_LOGIC",
                            "category": "Pillar 3: Pure Core",
                            "severity": "WARN",
                            "file": file_path,
                            "line": node.lineno,
                            "line_content": f"import {alias.name}",
                            "description": f"Impure dependency '{alias.name}' imported in pure domain file (violates Pure Core, Imperative Shell).",
                        })
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    is_impure = root_mod in BANNED_PURE_IMPORTS or node.module == "urllib.request"
                    if is_impure:
                        line_str = lines[node.lineno - 1] if 0 < node.lineno <= len(lines) else ""
                        if is_suppressed(line_str, "IMPURE_DOMAIN_LOGIC") or is_file_suppressed(content, "IMPURE_DOMAIN_LOGIC") or is_config_ignored(cfg, file_path, "IMPURE_DOMAIN_LOGIC"):
                            continue
                        violations.append({
                            "rule_id": "IMPURE_DOMAIN_LOGIC",
                            "category": "Pillar 3: Pure Core",
                            "severity": "WARN",
                            "file": file_path,
                            "line": node.lineno,
                            "line_content": f"from {node.module} import ...",
                            "description": f"Impure dependency '{node.module}' imported in pure domain file (violates Pure Core, Imperative Shell).",
                        })

        # 2. Check for private attribute access across boundaries
        # Automatically exempt test suites and dedicated compat/shim layers
        if not is_test and not is_compat and isinstance(node, ast.Attribute):
            attr_name = node.attr
            if attr_name.startswith("_") and not attr_name.startswith("__"):
                # Ignore self._* and cls._*
                is_internal = False
                if isinstance(node.value, ast.Name):
                    if node.value.id in ("self", "cls"):
                        is_internal = True
                    elif node.value.id in STDLIB_AND_FRAMEWORK_WHITELIST_NAMES:
                        is_internal = True
                elif isinstance(node.value, ast.Attribute):
                    if node.value.attr in STDLIB_AND_FRAMEWORK_WHITELIST_NAMES:
                        is_internal = True

                # Check if attribute is in stdlib protected attributes or dunders
                if attr_name in STDLIB_PROTECTED_ATTRS or attr_name in EXCLUDED_ATTRIBUTES:
                    is_internal = True

                # Check if symbol is defined locally in the same file
                if attr_name in locally_defined_symbols:
                    is_internal = True

                if not is_internal:
                    line_str = lines[node.lineno - 1] if 0 < node.lineno <= len(lines) else ""
                    if is_suppressed(line_str, "PRIVATE_STATE_LEAK") or is_file_suppressed(content, "PRIVATE_STATE_LEAK") or is_config_ignored(cfg, file_path, "PRIVATE_STATE_LEAK"):
                        continue
                    violations.append({
                        "rule_id": "PRIVATE_STATE_LEAK",
                        "category": "Pillar 3: Architecture & Seams",
                        "severity": "WARN",
                        "file": file_path,
                        "line": node.lineno,
                        "line_content": f".{attr_name}",
                        "description": f"Accessing private member '{attr_name}' across module boundary (violates Clean Seams).",
                    })

    return violations


# ==============================================================================
# MODE 1: INSPECT-COMMIT (Fast Delta Scanner)
# ==============================================================================

def extract_git_diff(scope: str, base_branch: str, commit_ref: str, cwd: str) -> Dict[str, Any]:
    if scope == "staged":
        diff_cmd = ["diff", "--cached", "-U3"]
    elif scope == "uncommitted":
        diff_cmd = ["diff", "HEAD", "-U3"]
    elif scope == "branch":
        diff_cmd = ["diff", f"{base_branch}...HEAD", "-U3"]
    elif scope == "commit":
        target = commit_ref or "HEAD"
        diff_cmd = ["show", "--format=", "-U3", target]
    else:
        diff_cmd = ["diff", "HEAD", "-U3"]

    code, diff_output, err = run_git(diff_cmd, cwd)
    if code != 0:
        return {"error": f"Git diff failed: {err}"}

    # Extract untracked files
    untracked_files = []
    if scope in ("uncommitted", "staged"):
        c_untrack, out_untrack, _ = run_git(["status", "--porcelain"], cwd)
        if c_untrack == 0:
            for line in out_untrack.splitlines():
                if line.startswith("?? "):
                    untracked_files.append(line[3:].strip())

    return {
        "diff": diff_output,
        "untracked_files": untracked_files,
        "scope": scope,
    }


def audit_diff(diff_text: str, untracked_files: List[str], cwd: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    violations = []
    current_file = None
    line_num = 0
    current_file_suppressions: Set[str] = set()

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            current_file = parts[-1].lstrip("b/")
            ext = os.path.splitext(current_file)[1].lower()
            is_code = ext in CODE_EXTENSIONS
            line_num = 0
            full_p = Path(cwd) / current_file
            if full_p.is_file():
                try:
                    file_head = full_p.read_text(encoding="utf-8", errors="replace")[:1000]
                    current_file_suppressions = extract_file_suppressed_rules(file_head)
                except Exception:
                    current_file_suppressions = set()
            else:
                current_file_suppressions = set()
            continue
        elif raw_line.startswith("@@"):
            match = re.search(r"\+(\d+)", raw_line)
            if match:
                line_num = int(match.group(1)) - 1
            continue
        elif raw_line.startswith("+") and not raw_line.startswith("+++"):
            line_num += 1
            added_line = raw_line[1:]

            # Check Universal Heuristic Rules
            for rule in UNIVERSAL_RULES:
                rule_id = rule["id"]
                if rule_id in current_file_suppressions or "all" in current_file_suppressions:
                    continue
                if is_suppressed(added_line, rule_id):
                    continue
                if current_file and is_config_ignored(config, current_file, rule_id):
                    continue
                if rule.get("code_only") and not is_code:
                    continue
                if "file_ext" in rule:
                    ext = os.path.splitext(current_file or "")[1].lower()
                # Skip rule definitions, regex tables, and metadata
                if "re.compile(" in added_line or '"regex":' in added_line or '"description":' in added_line:
                    continue

                # Context check for migrations
                if rule_id == "UNTRACKED_SCHEMA_MUTATION":
                    if "migration" in (current_file or "").lower() or "schema" in (current_file or "").lower():
                        continue
                if rule_id == "TEST_FLAKY_SLEEP":
                    if not is_test_file(current_file or ""):
                        continue
                if rule_id == "PRIVATE_STATE_LEAK_REGEX":
                    if is_test_file(current_file or "") or is_compat_file(current_file or ""):
                        continue
                    if any(attr in added_line for attr in STDLIB_PROTECTED_ATTRS):
                        continue
                    if any(f"{mod}._" in added_line for mod in STDLIB_AND_FRAMEWORK_WHITELIST_NAMES):
                        continue
                if rule_id.startswith("SECRET_"):
                    if is_test_file(current_file or "") or "test-fixture" in added_line.lower():
                        continue
                if rule_id == "DEBUG_PYTHON_PRINT":
                    if "file=sys.std" in added_line or (current_file and ("code_guard.py" in current_file or "install_hook.py" in current_file)):
                        continue

                if rule["regex"].search(added_line):
                    violations.append({
                        "rule_id": rule_id,
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "file": current_file,
                        "line": line_num,
                        "line_content": added_line.strip(),
                        "description": rule["description"],
                    })

    # Scan untracked files for secrets
    for ufile in untracked_files:
        u_path = Path(cwd) / ufile
        if u_path.is_file() and u_path.stat().st_size < 1_000_000:
            try:
                content = u_path.read_text(encoding="utf-8", errors="replace")
                for idx, line in enumerate(content.splitlines(), start=1):
                    for rule in UNIVERSAL_RULES:
                        if rule["category"].startswith("Pillar 2: Security") and rule["regex"].search(line):
                            violations.append({
                                "rule_id": rule["id"],
                                "category": rule["category"],
                                "severity": rule["severity"],
                                "file": ufile,
                                "line": idx,
                                "line_content": line.strip()[:100],
                                "description": f"[Untracked File] {rule['description']}",
                            })
            except Exception:
                pass

    return violations


# ==============================================================================
# MODE 2: INSPECT-CODEBASE (Holistic Architectural & Churn Audit)
# ==============================================================================

def analyze_git_hotspots(cwd: str, limit: int = 20) -> List[Dict[str, Any]]:
    # Run git log --format=oneline --name-only for last 90 days
    code, stdout, _ = run_git(["log", "--since=90.days", "--name-only", "--pretty=format:"], cwd)
    if code != 0:
        return []

    churn_counts: Dict[str, int] = {}
    IGNORED_HOTSPOT_EXT = {".md", ".json", ".lock", ".yaml", ".yml", ".txt", ".png", ".svg", ".toml"}

    for line in stdout.splitlines():
        fname = line.strip()
        if not fname:
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext in IGNORED_HOTSPOT_EXT or "package-lock" in fname or "pnpm-lock" in fname:
            continue
        f_path = Path(cwd) / fname
        if f_path.is_file():
            churn_counts[fname] = churn_counts.get(fname, 0) + 1

    results = []
    for fname, churn in sorted(churn_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
        f_path = Path(cwd) / fname
        try:
            loc = sum(1 for _ in open(f_path, "r", encoding="utf-8", errors="replace"))
        except Exception:
            loc = 100
        # Hotspot Risk Score = Churn * log(LOC)
        risk = int(churn * (loc ** 0.5) / 2)
        results.append({
            "file": fname,
            "churn_commits": churn,
            "loc": loc,
            "risk_score": risk,
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results


def audit_whole_codebase(target_dir: str, cwd: str, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    violations = []
    root_path = Path(target_dir).resolve()
    pure_paths = config.get("pure_paths", ["rules/", "validators/", "parsers/", "schemas/"])
    layer_rules = config.get("layers", {})

    total_files = 0
    total_loc = 0

    IGNORED_DIRS = {
        ".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build",
        ".next", ".tox", "assets", "reports", "exports", "site-packages",
        "coverage", ".pytest_cache", ".ruff_cache", ".mypy_cache"
    }

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRS
            and not d.startswith(".")
            and not d.endswith(".egg-info")
            and not d.endswith(".dist-info")
        ]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in CODE_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, root_path)
            total_files += 1

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    lines = content.splitlines()
                    total_loc += len(lines)
            except Exception:
                continue

            # 1. Check Python AST for pure domain and private state leaks
            if ext == ".py":
                ast_violations = verify_python_ast(rel_path, content, pure_paths, layer_rules, config)
                violations.extend(ast_violations)

            # 2. Universal Heuristic Check
            file_suppressed = extract_file_suppressed_rules(lines)
            for idx, line in enumerate(lines, start=1):
                for rule in UNIVERSAL_RULES:
                    rule_id = rule["id"]
                    if rule_id in file_suppressed or "all" in file_suppressed:
                        continue
                    if is_suppressed(line, rule_id) or is_config_ignored(config, rel_path, rule_id):
                        continue
                    if rule.get("code_only") and ext not in CODE_EXTENSIONS:
                        continue
                    if "file_ext" in rule and ext not in rule["file_ext"]:
                        continue

                    # Skip rule definitions, regex tables, and metadata
                    if "re.compile(" in line or '"regex":' in line or '"description":' in line:
                        continue

                    # Skip secrets in test files or mock data
                    if rule_id.startswith("SECRET_") and (is_test_file(rel_path) or "test-fixture" in line.lower()):
                        continue

                    # If file is Python, verify_python_ast already handles private attribute checking with full AST semantics;
                    # skip regex check on Python files to avoid duplicate reporting.
                    if rule_id == "PRIVATE_STATE_LEAK_REGEX" and ext == ".py":
                        continue

                    if rule_id == "TEST_FLAKY_SLEEP" and not is_test_file(rel_path):
                        continue
                    if rule_id == "PRIVATE_STATE_LEAK_REGEX":
                        if is_test_file(rel_path) or is_compat_file(rel_path):
                            continue
                        if any(attr in line for attr in STDLIB_PROTECTED_ATTRS):
                            continue
                        if any(f"{mod}._" in line for mod in STDLIB_AND_FRAMEWORK_WHITELIST_NAMES):
                            continue
                    if rule_id == "DEBUG_PYTHON_PRINT":
                        if "file=sys.std" in line or "code_guard.py" in rel_path or "install_hook.py" in rel_path:
                            continue

                    if rule["regex"].search(line):
                        violations.append({
                            "rule_id": rule_id,
                            "category": rule["category"],
                            "severity": rule["severity"],
                            "file": rel_path,
                            "line": idx,
                            "line_content": line.strip()[:100],
                            "description": rule["description"],
                        })

    metrics = {
        "total_files": total_files,
        "total_loc": total_loc,
    }
    return violations, metrics


# ==============================================================================
# MAIN CLI DRIVER
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="code-guard: Full-Lifecycle Codebase & Commit Integrity Auditor")
    parser.add_argument("--mode", choices=["commit", "codebase"], default="commit", help="Audit mode: commit (delta) or codebase (full)")
    parser.add_argument("--scope", choices=["uncommitted", "staged", "branch", "commit", "full"], default="uncommitted", help="Delta git scope")
    parser.add_argument("--base", default="main", help="Base branch for branch/PR diff comparison")
    parser.add_argument("--commit", default="", help="Commit SHA to inspect")
    parser.add_argument("--path", default=".", help="Target directory for codebase audit")
    parser.add_argument("--json", action="store_true", help="Output audit report as structured JSON")
    parser.add_argument("--hotspots", action="store_true", help="Include churn hotspot analysis in codebase mode")
    parser.add_argument("--baseline", default="", help="Path to .codeguard-baseline.json to ratchet violations")
    parser.add_argument("--generate-baseline", default="", help="Save current violations to baseline JSON and exit 0")

    args = parser.parse_args()
    cwd = os.getcwd()

    # If --scope full is requested, route to codebase mode
    if args.scope == "full":
        args.mode = "codebase"

    target_path = Path(args.path).resolve() if args.mode == "codebase" else Path(cwd).resolve()
    config = load_codeguard_config(str(target_path))
    if not config and str(target_path) != str(cwd):
        config = load_codeguard_config(cwd)

    violations: List[Dict[str, Any]] = []
    summary_metrics: Dict[str, Any] = {}

    if args.mode == "commit":
        diff_info = extract_git_diff(args.scope, args.base, args.commit, cwd)
        if "error" in diff_info:
            print(f"Error: {diff_info['error']}", file=sys.stderr)
            sys.exit(1)
        violations = audit_diff(diff_info["diff"], diff_info["untracked_files"], cwd, config)
        summary_metrics = {
            "mode": "commit",
            "scope": args.scope,
            "untracked_count": len(diff_info["untracked_files"]),
        }
    else:
        violations, codebase_metrics = audit_whole_codebase(str(target_path), cwd, config)
        hotspots = analyze_git_hotspots(str(target_path)) if args.hotspots else []
        summary_metrics = {
            "mode": "codebase",
            "path": str(target_path),
            **codebase_metrics,
            "hotspots": hotspots,
        }

    # Handle Baseline Ratchet
    if args.generate_baseline:
        fingerprints = [compute_violation_fingerprint(v) for v in violations]
        baseline_data = {
            "version": "1.0",
            "total_violations": len(violations),
            "fingerprints": sorted(list(set(fingerprints))),
        }
        with open(args.generate_baseline, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2)
        print(f"✅ Generated baseline file with {len(baseline_data['fingerprints'])} entries: {args.generate_baseline}")
        sys.exit(0)

    if args.baseline:
        baseline_set = load_baseline(args.baseline)
        if baseline_set:
            violations = [v for v in violations if compute_violation_fingerprint(v) not in baseline_set]

    blocker_count = sum(1 for v in violations if v["severity"] == "BLOCK")
    warning_count = sum(1 for v in violations if v["severity"] == "WARN")

    # Normalized Architectural Health Score (0 - 100)
    # Deduct per offending file to prevent a single file from collapsing the score
    blocker_files = len(set(v["file"] for v in violations if v["severity"] == "BLOCK"))
    warning_files = len(set(v["file"] for v in violations if v["severity"] == "WARN"))
    total_penalty = min(blocker_files * 10, 50) + min(warning_files * 2, 25)
    health_score = max(100 - total_penalty, 0)
    summary_metrics["health_score"] = health_score

    if blocker_count > 0:
        verdict = "BLOCK"
    elif warning_count > 0:
        verdict = "WARN"
    else:
        verdict = "PASS"

    output_payload = {
        "verdict": verdict,
        "health_score": health_score,
        "blockers": blocker_count,
        "warnings": warning_count,
        "metrics": summary_metrics,
        "violations": violations,
    }

    if args.json:
        print(json.dumps(output_payload, indent=2))
    else:
        print("=" * 70)
        print(f"CODE GUARD AUDIT REPORT [{args.mode.upper()} MODE] - Verdict: {verdict}")
        print(f"Architectural Health Score: {health_score} / 100")
        print("=" * 70)
        print(f"Critical Blockers: {blocker_count} | Warnings: {warning_count}")
        if violations:
            print("\nFindings:")
            for idx, v in enumerate(violations, start=1):
                badge = "🛑 BLOCK" if v["severity"] == "BLOCK" else "⚠️ WARN"
                print(f"  {idx}. [{badge}] {v['rule_id']} in {v['file']}:{v['line']}")
                print(f"     {v['description']}")
                print(f"     > {v.get('line_content', '')}\n")
        else:
            print("\n✅ Zero violations detected. Codebase is clean, secure, and architecturally sound.")

    sys.exit(1 if blocker_count > 0 else 0)


if __name__ == "__main__":
    main()
