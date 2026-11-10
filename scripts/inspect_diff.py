#!/usr/bin/env python3
"""
inspect_diff.py - Deterministic Git Diff Extractor and Heuristic Scanner
Part of the commit-guard skill.

Extracts diffs across multiple scopes (uncommitted, staged, branch, commit, full)
and runs high-speed heuristic scans for debug artifacts, secrets, and weak crypto.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Any, Optional, Tuple

# Patterns to scan on added lines (lines starting with +)
HEURISTIC_RULES = [
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
        "description": "print() call detected (verify if intended for CLI or leftover debug)",
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
        "regex": re.compile(r"\b(var_dump|dd|dump|p!)\s*\("),
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

    # 2. Hardcoded Secrets & Credentials (scanned in all files including docs)
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
        "description": "Potential GitHub personal access or OAuth token",
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
        "description": "Insecure or deprecated cipher mode (DES, RC4, or AES-ECB)",
        "code_only": True,
        "regex": re.compile(r"['\"](des|3des|rc4|blowfish|aes-[0-9]{3}-ecb)['\"]", re.IGNORECASE),
    },
    {
        "id": "CRYPTO_INSECURE_JWT",
        "category": "Pillar 2: Security & Crypto",
        "severity": "BLOCK",
        "description": "Unverified JWT signature or 'none' algorithm",
        "code_only": True,
        "regex": re.compile(r"(jwt\.decode\s*\(.*verify\s*=\s*False|algorithm\s*=\s*['\"]none['\"])", re.IGNORECASE),
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

    # 4. System Integrity & Git Hygiene
    {
        "id": "GIT_CONFLICT_MARKER",
        "category": "Pillar 3: System Integrity",
        "severity": "BLOCK",
        "description": "Unresolved Git merge conflict marker",
        "code_only": False,
        "regex": re.compile(r"^(<{7}|={7}|>{7})(\s|$)"),
    },
    {
        "id": "LEFTOVER_LOCALHOST_URL",
        "category": "Pillar 3: System Integrity",
        "severity": "WARN",
        "description": "Hardcoded localhost or loopback URL (verify environment configurability)",
        "code_only": True,
        "regex": re.compile(r"https?://(localhost|127\.0\.0\.1):[0-9]{2,5}"),
    },

    # 5. Infrastructure & Container Hygiene
    {
        "id": "DOCKER_UNPINNED_LATEST",
        "category": "Compliance: Supply Chain & Infra",
        "severity": "WARN",
        "description": "Docker base image using unpinned floating :latest tag",
        "code_only": True,
        "regex": re.compile(r"^FROM\s+[a-zA-Z0-9_\-\./]+:latest\b"),
    },
    {
        "id": "CI_UNSAFE_PR_TRIGGER",
        "category": "Compliance: Supply Chain & CI",
        "severity": "WARN",
        "description": "GitHub Actions pull_request_target trigger (verify fork checkout security)",
        "code_only": False,
        "regex": re.compile(r"^\s*pull_request_target\s*:"),
    },

    # 6. Robustness & Anti-Patterns
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


def get_default_branch(cwd: str) -> str:
    # Try symbolic-ref first
    code, stdout, _ = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"], cwd)
    if code == 0 and stdout.strip():
        return stdout.strip().split("/")[-1]
    # Check if main exists
    code, _, _ = run_git(["rev-parse", "--verify", "main"], cwd)
    if code == 0:
        return "main"
    # Fallback to master
    return "master"


def get_untracked_files(cwd: str) -> List[str]:
    code, stdout, _ = run_git(["status", "--porcelain"], cwd)
    if code != 0:
        return []
    untracked = []
    for line in stdout.splitlines():
        if line.startswith("?? "):
            untracked.append(line[3:].strip())
    return untracked


def extract_diff(scope: str, base_branch: Optional[str], commit_sha: Optional[str], cwd: str) -> Tuple[str, List[str]]:
    untracked_files = []
    diff_text = ""

    if scope == "staged":
        _, diff_text, _ = run_git(["diff", "--cached"], cwd)
    elif scope == "branch":
        base = base_branch or get_default_branch(cwd)
        _, diff_text, _ = run_git(["diff", f"{base}...HEAD"], cwd)
    elif scope == "commit":
        target = commit_sha or "HEAD"
        _, diff_text, _ = run_git(["show", target], cwd)
    elif scope == "full":
        # Full scan: generate diff against empty tree
        code, empty_tree, _ = run_git(["hash-object", "-t", "tree", "/dev/null"], cwd)
        if code == 0 and empty_tree.strip():
            _, diff_text, _ = run_git(["diff", empty_tree.strip(), "HEAD"], cwd)
        else:
            _, diff_text, _ = run_git(["diff", "HEAD~1..HEAD"], cwd)
    else:  # uncommitted (staged + unstaged + untracked)
        _, diff_text, _ = run_git(["diff", "HEAD"], cwd)
        # If HEAD doesn't exist (initial commit), fallback to cached
        if not diff_text:
            _, diff_cached, _ = run_git(["diff", "--cached"], cwd)
            _, diff_unstaged, _ = run_git(["diff"], cwd)
            diff_text = diff_cached + ("\n" if diff_cached and diff_unstaged else "") + diff_unstaged

        # Include untracked files
        untracked = get_untracked_files(cwd)
        untracked_files = untracked
        for uf in untracked:
            full_path = os.path.join(cwd, uf)
            if os.path.isfile(full_path) and os.path.getsize(full_path) < 500 * 1024:
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    lines = content.splitlines()
                    diff_text += f"\n--- /dev/null\n+++ b/{uf}\n@@ -0,0 +1,{len(lines)} @@\n"
                    for l in lines:
                        diff_text += f"+{l}\n"
                except Exception:
                    pass

    return diff_text, untracked_files


def scan_diff_heuristics(diff_text: str) -> List[Dict[str, Any]]:
    findings = []
    current_file = None
    line_number = 0

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:].strip()
            line_number = 0
            continue
        elif raw_line.startswith("@@"):
            # Extract starting line number in new file
            m = re.search(r"\+([0-9]+)", raw_line)
            if m:
                line_number = int(m.group(1)) - 1
            continue

        if not current_file:
            continue

        # If it's an added line in the diff
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            line_number += 1
            added_content = raw_line[1:]
            _, ext = os.path.splitext(current_file)

            # Skip self-referential scanner regex definitions
            if "re.compile(" in added_content or '"regex":' in added_content or '"description":' in added_content:
                continue

            for rule in HEURISTIC_RULES:
                # If rule is code_only, skip markdown, txt, and documentation files
                if rule.get("code_only") and ext.lower() in [".md", ".markdown", ".txt", ".rst", ".adoc"]:
                    continue

                # Don't flag print() if it's clearly inside a CLI script's main/CLI output
                if rule["id"] == "DEBUG_PYTHON_PRINT":
                    if "def main" in diff_text or 'if __name__ == "__main__"' in diff_text:
                        # Only flag if not in a file clearly functioning as a CLI tool
                        if current_file.startswith("scripts/") or current_file.endswith("cli.py"):
                            continue

                # Check extension filter if present
                if "file_ext" in rule and ext not in rule["file_ext"]:
                    continue

                if rule["regex"].search(added_content):
                    findings.append({
                        "rule_id": rule["id"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "file": current_file,
                        "line": line_number,
                        "snippet": added_content.strip()[:160],
                    })
        elif not raw_line.startswith("-"):
            # Context line
            line_number += 1

    return findings


def calculate_metrics(diff_text: str, untracked: List[str]) -> Dict[str, Any]:
    added_files = set()
    modified_files = set()
    deleted_files = set()
    insertions = 0
    deletions = 0

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            f = line[6:].strip()
            modified_files.add(f)
        elif line.startswith("--- a/"):
            f = line[6:].strip()
        elif line.startswith("+") and not line.startswith("+++"):
            insertions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return {
        "files_changed_count": len(modified_files),
        "files_changed": sorted(list(modified_files)),
        "insertions": insertions,
        "deletions": deletions,
        "untracked_count": len(untracked),
        "untracked_files": untracked,
    }


def main():
    parser = argparse.ArgumentParser(description="Commit Guard Diff Extractor and Heuristic Scanner")
    parser.add_argument("--scope", choices=["uncommitted", "staged", "branch", "commit", "full"], default="uncommitted")
    parser.add_argument("--base", default=None, help="Base branch for branch scope (default: main/master)")
    parser.add_argument("--commit", default=None, help="Commit hash for commit scope")
    parser.add_argument("--cwd", default=os.getcwd(), help="Target repository directory")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--max-diff-lines", type=int, default=2000, help="Maximum diff lines to include in output")

    args = parser.parse_args()
    cwd = os.path.abspath(args.cwd)

    diff_text, untracked = extract_diff(args.scope, args.base, args.commit, cwd)
    heuristics = scan_diff_heuristics(diff_text)
    metrics = calculate_metrics(diff_text, untracked)

    blocker_count = sum(1 for h in heuristics if h["severity"] == "BLOCK")
    warning_count = sum(1 for h in heuristics if h["severity"] == "WARN")

    if blocker_count > 0:
        preliminary_verdict = "BLOCK"
    elif warning_count > 0:
        preliminary_verdict = "WARN"
    else:
        preliminary_verdict = "PASS"

    truncated_diff = "\n".join(diff_text.splitlines()[: args.max_diff_lines])

    result = {
        "scope": args.scope,
        "cwd": cwd,
        "preliminary_verdict": preliminary_verdict,
        "blockers": blocker_count,
        "warnings": warning_count,
        "metrics": metrics,
        "heuristic_findings": heuristics,
        "diff_preview": truncated_diff,
        "diff_total_lines": len(diff_text.splitlines()),
        "truncated": len(diff_text.splitlines()) > args.max_diff_lines,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"=== Commit Guard Pre-Scan: {args.scope.upper()} ===")
        print(f"Verdict: {preliminary_verdict}")
        print(f"Files Changed: {metrics['files_changed_count']} (+{metrics['insertions']} / -{metrics['deletions']})")
        print(f"Untracked Files: {metrics['untracked_count']}")
        print(f"Findings: {len(heuristics)} ({blocker_count} Blockers, {warning_count} Warnings)\n")

        if heuristics:
            print("--- Heuristic Flags ---")
            for h in heuristics:
                print(f"[{h['severity']}] {h['file']}:{h['line']} - {h['description']}")
                print(f"    > {h['snippet']}")


if __name__ == "__main__":
    main()
