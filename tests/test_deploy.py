"""Exercise rollout/rollback without Docker, SSH, provider APIs or a real database."""

import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "deploy.sh"
COMMIT = "a" * 40
STUB = """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
root = Path(os.environ["TOURISM_DEPLOY_ROOT"])
name, args = Path(sys.argv[0]).name, sys.argv[1:]
with (root / "calls.jsonl").open("a") as f:
    f.write(json.dumps([name, args, os.environ.get("RELEASE_TAG")]) + "\\n")
if name == "git" and "worktree" in args:
    release = Path(args[-2])
    (release / "deploy").mkdir(parents=True)
    (release / "deploy/compose.production.yaml").touch()
elif name == "docker":
    if args[0] == "inspect": print("max-local-tourism:previous")
    elif "pg_dump" in args: print("test database backup")
    elif "build" in args and os.environ.get("FAIL_STAGE") == "build": sys.exit(1)
    elif "scripts/check_production.py" in args and os.environ.get("FAIL_STAGE") == "checks": sys.exit(1)
elif name == "readlink": print(Path(args[-1]).resolve())
elif name == "mv": os.replace(args[-2], args[-1])
"""


@pytest.mark.parametrize("failure", [None, "build", "checks"])
def test_rollout_changes_only_app_and_restores_previous_on_failed_checks(
    tmp_path, failure
):
    root = tmp_path / "tourism"
    previous = root / "releases/previous"
    (previous / "deploy").mkdir(parents=True)
    (previous / "deploy/compose.production.yaml").touch()
    (root / "current").symlink_to(previous)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("git", "docker", "curl", "flock", "readlink", "mv"):
        command = bin_dir / name
        command.write_text(STUB)
        command.chmod(0o755)
    env = {
        **os.environ,
        "TOURISM_DEPLOY_ROOT": str(root),
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
    }
    if failure:
        env["FAIL_STAGE"] = failure
    result = subprocess.run(
        ["bash", str(SCRIPT), COMMIT],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    calls = [
        json.loads(line) for line in (root / "calls.jsonl").read_text().splitlines()
    ]
    updates = [call for call in calls if call[0] == "docker" and "up" in call[1]]
    assert all("--no-deps" in call[1] and call[1][-1] == "app" for call in updates)
    assert (
        len([call for call in calls if call[0] == "docker" and "pg_dump" in call[1]])
        == 1
    )
    if failure:
        assert result.returncode != 0
        assert (root / "current").resolve() == previous
        assert len(updates) == (2 if failure == "checks" else 0)
        if updates:
            assert updates[-1][2] == "previous"
    else:
        assert result.returncode == 0, result.stderr
        assert (root / "current").resolve() != previous
        assert len(updates) == 1
        assert (
            next((root / "deployments").glob("*.commit")).read_text().strip() == COMMIT
        )
