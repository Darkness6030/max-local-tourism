"""Push the clean main branch and deploy its exact commit through server-side Git."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = """set -euo pipefail
repo=/opt/max-local-tourism/repo.git
git --git-dir="$repo" fetch --prune origin
git --git-dir="$repo" merge-base --is-ancestor "$1" refs/heads/main
git --git-dir="$repo" show "$1:deploy/deploy.sh" | bash -s -- "$1"
"""


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    if git("status", "--porcelain"):
        raise SystemExit(
            "Сначала закоммитьте изменения: деплой требует чистого рабочего дерева."
        )
    if git("branch", "--show-current") != "main":
        raise SystemExit(
            "Деплой выполняется из main. Сначала завершите слияние изменений."
        )
    commit = git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("Не удалось определить коммит для деплоя")
    subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True)
    subprocess.run(
        [
            "ssh",
            "-o",
            "ConnectTimeout=15",
            "-o",
            "ServerAliveInterval=15",
            "-o",
            "ServerAliveCountMax=3",
            "Dental",
            "bash",
            "-s",
            "--",
            commit,
        ],
        input=BOOTSTRAP,
        text=True,
        check=True,
    )
    print(f"Развёрнут коммит {commit}")


if __name__ == "__main__":
    main()
