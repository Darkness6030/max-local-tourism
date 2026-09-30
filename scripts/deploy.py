"""Push the clean main branch and deploy its exact commit through server-side Git."""

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=("dental", "poyti"), default="dental")
    parser.add_argument("--identity-file", type=Path)
    args = parser.parse_args()
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
    ssh_options = []
    if args.identity_file:
        ssh_options = ["-i", str(args.identity_file.expanduser()), "-o", "IdentitiesOnly=yes"]
    bootstrap = BOOTSTRAP
    if args.target == "poyti":
        bootstrap = bootstrap.replace("deploy/deploy.sh", "deploy/poyti.sh")
    subprocess.run(
        [
            "ssh",
            *ssh_options,
            "-o",
            "ConnectTimeout=15",
            "-o",
            "ServerAliveInterval=15",
            "-o",
            "ServerAliveCountMax=3",
            "Dental" if args.target == "dental" else "server@158.160.128.20",
            *([] if args.target == "dental" else ["sudo", "-n"]),
            "bash",
            "-s",
            "--",
            commit,
        ],
        input=bootstrap,
        text=True,
        check=True,
    )
    print(f"Развёрнут коммит {commit}")


if __name__ == "__main__":
    main()
