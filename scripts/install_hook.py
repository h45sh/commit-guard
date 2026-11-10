#!/usr/bin/env python3
"""
install_hook.py - Install Commit Guard as a Local Git Pre-Commit Hook
Part of the commit-guard skill.

Installs a lightweight pre-commit hook into the target repository's .git/hooks/pre-commit
to automatically audit staged files and block commits containing secrets, debug code,
or critical security violations.
"""

import argparse
import os
import stat
import sys

HOOK_TEMPLATE = """#!/usr/bin/env bash
# Commit Guard Pre-Commit Hook
# Automatically installed by commit-guard

GUARD_SCRIPT="{guard_script}"

if [ ! -f "$GUARD_SCRIPT" ]; then
    echo "⚠️ Commit Guard script not found at $GUARD_SCRIPT. Skipping pre-commit audit."
    exit 0
fi

echo "🛡️ Running Commit Guard pre-commit audit..."
python3 "$GUARD_SCRIPT" --scope staged

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "🛑 Commit Guard blocked this commit due to critical issues."
    echo "   Fix the blockers listed above or run: git diff --cached"
    echo "   To force commit (emergency only): git commit --no-verify"
    exit 1
fi

exit 0
"""


def main():
    parser = argparse.ArgumentParser(description="Install Commit Guard git pre-commit hook")
    parser.add_argument("--repo", default=os.getcwd(), help="Target repository root (default: current directory)")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the pre-commit hook")
    args = parser.parse_args()

    repo_dir = os.path.abspath(args.repo)
    git_dir = os.path.join(repo_dir, ".git")

    if not os.path.isdir(git_dir):
        print(f"❌ Error: {repo_dir} is not a valid git repository (.git folder not found).")
        sys.exit(1)

    hooks_dir = os.path.join(git_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    hook_path = os.path.join(hooks_dir, "pre-commit")

    if args.uninstall:
        if os.path.exists(hook_path):
            os.remove(hook_path)
            print(f"✅ Uninstalled Commit Guard pre-commit hook from {hook_path}")
        else:
            print("ℹ️ No pre-commit hook found to uninstall.")
        return

    # Find the absolute path to inspect_diff.py
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    guard_script = os.path.join(current_script_dir, "inspect_diff.py")

    hook_content = HOOK_TEMPLATE.format(guard_script=guard_script)

    # If hook already exists, backup or confirm
    if os.path.exists(hook_path):
        backup_path = hook_path + ".bak"
        print(f"ℹ️ Existing pre-commit hook found. Backing up to {backup_path}")
        try:
            with open(hook_path, "r", encoding="utf-8") as f_orig:
                existing_content = f_orig.read()
            if "Commit Guard" in existing_content:
                print("ℹ️ Overwriting previous Commit Guard hook.")
            else:
                with open(backup_path, "w", encoding="utf-8") as f_bak:
                    f_bak.write(existing_content)
        except Exception as e:
            print(f"⚠️ Could not backup existing hook: {e}")

    with open(hook_path, "w", encoding="utf-8") as f:
        f.write(hook_content)

    # Make executable (chmod +x)
    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    print(f"✅ Successfully installed Commit Guard hook at: {hook_path}")
    print("   Every 'git commit' in this repo will now automatically be audited before committing!")


if __name__ == "__main__":
    main()
