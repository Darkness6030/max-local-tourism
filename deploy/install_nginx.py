"""Install only the MAX include in kaktut.ru, with a config-hash guard and rollback.

Run as root on Dental after the isolated upstream has passed its checks.
"""

import argparse
import hashlib
import os
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--backup-dir", required=True)
    args = parser.parse_args()
    target = Path("/etc/nginx/sites-available/kaktut.ru")
    original = target.read_bytes()
    if hashlib.sha256(original).hexdigest() != args.expected_sha256:
        raise SystemExit("nginx config changed since inspection; no changes applied")
    include = "    include /etc/nginx/snippets/max-local-tourism-locations.conf;"
    if include.encode() in original:
        raise SystemExit("MAX include already exists; no changes applied")
    anchor = "    server_name kaktut.ru;"
    if anchor not in original.decode():
        raise SystemExit("Expected server block not found")
    backup = Path(args.backup_dir)
    backup.mkdir(parents=True, exist_ok=False, mode=0o700)
    shutil.copy2(target, backup / "kaktut.ru.before.conf")
    snippets = [
        ("nginx-max-app.conf", "/etc/nginx/snippets/max-local-tourism-locations.conf"),
        ("nginx-proxy.conf", "/etc/nginx/snippets/max-local-tourism-proxy.conf"),
    ]
    for _, dest in snippets:
        if Path(dest).exists():
            raise SystemExit(f"{dest} already exists; no changes applied")
    candidate = target.with_name("kaktut.ru.max-candidate")
    installed = []
    try:
        for source, dest in snippets:
            shutil.copyfile(Path(__file__).parent / source, dest)
            os.chmod(dest, 0o644)
            installed.append(Path(dest))
        candidate.write_text(
            original.decode().replace(anchor, anchor + "\n\n" + include, 1)
        )
        shutil.copystat(target, candidate)
        os.replace(candidate, target)
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
    except BaseException:
        shutil.copy2(backup / "kaktut.ru.before.conf", target)
        for path in installed:
            path.unlink(missing_ok=True)
        candidate.unlink(missing_ok=True)
        subprocess.run(["nginx", "-t"], check=True)
        subprocess.run(["systemctl", "reload", "nginx"], check=True)
        raise
    print(f"MAX locations enabled. Original config saved in {backup}")


if __name__ == "__main__":
    main()
