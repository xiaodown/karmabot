#!/usr/bin/env python3
"""Run the Karmabot test suite.

Usage:
    python3 run_tests.py            # run everything
    python3 run_tests.py test_db    # only test modules matching "test_db"

Prefers the project virtualenv (.venv) if it exists; falls back to the
current interpreter. Prefers pytest if the chosen interpreter has it;
falls back to the standard-library unittest runner. Exits nonzero on
failure.
"""

import os
import subprocess
import sys


def main() -> int:
    repo_root = os.path.dirname(os.path.abspath(__file__))
    filter_arg = sys.argv[1] if len(sys.argv) > 1 else None

    venv_python = os.path.join(repo_root, ".venv", "bin", "python")
    if os.path.exists(venv_python):
        python = venv_python
        env = dict(os.environ)
        env["PYTHONPATH"] = repo_root
    else:
        python = sys.executable
        env = None

    use_pytest = (
        subprocess.run(
            [python, "-c", "import pytest"], capture_output=True, env=env
        ).returncode
        == 0
    )

    if use_pytest:
        cmd = [python, "-m", "pytest", "tests", "-v"]
    else:
        cmd = [python, "-m", "unittest", "discover", "-s", "tests", "-v"]

    if filter_arg:
        if use_pytest:
            cmd += ["-k", filter_arg]
        else:
            cmd += ["-p", f"{filter_arg}.py"]

    result = subprocess.run(cmd, cwd=repo_root, env=env)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
