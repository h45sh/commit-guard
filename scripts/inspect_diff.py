#!/usr/bin/env python3
"""
inspect_diff.py - Backward Compatibility Wrapper for code-guard.
Delegates to scripts/code_guard.py with --mode commit.
"""
import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    code_guard_bin = os.path.join(script_dir, "code_guard.py")
    cmd = [sys.executable, code_guard_bin, "--mode", "commit"] + sys.argv[1:]
    try:
        proc = subprocess.run(cmd)
        sys.exit(proc.returncode)
    except Exception as e:
        print(f"Error invoking code_guard.py: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
