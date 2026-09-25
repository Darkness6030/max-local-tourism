# Working on this project

- The user wants all future server deployments through Git. Commit the complete intended changes, push to `origin/main`, then run `python3 scripts/deploy.py`. Never upload source snapshots with scp/rsync/tar as the deployment mechanism.
- Repository: `https://github.com/Darkness6030/max-local-tourism`. Default branch: `main`. Do not force-push or rewrite shared history.
- Production: SSH alias `Dental`, project root `/opt/max-local-tourism`, public app `https://kaktut.ru/max/app`. Only update this project's `app` service. Keep PostgreSQL, other containers, nginx and bot identity/settings untouched.
- `deploy/deploy.sh` runs on the server from the selected Git commit. It creates a detached release worktree, backs up PostgreSQL, builds/replaces only the app, checks health/public assets/auth, and atomically switches `current`. On a failed application rollout it restores the previous application image.
- Keep secrets and private materials out of Git: `.env`, `data/`, private keys, database dumps, original PDFs, `docs/PLAN.md`, `docs/RULES.md`, local IDE files and `tmp/`. `.env.example` contains placeholders only. Never print credentials.
- The server uses a repository-specific read-only deploy key stored outside releases. Never copy personal GitHub credentials onto the server.
- `docs/PROGRESS.md` must stay empty. Read local `docs/RULES.md` when available; it is intentionally not published.
- Preserve the user's uncommitted changes. Do not silently omit intended changes from a deployment; the deploy command rejects a dirty worktree.
- Run checks appropriate to the change. Backend: `.venv/bin/ruff check src tests`, `.venv/bin/pytest -q` (PostgreSQL cases need an isolated `TEST_DATABASE_URL`). Frontend: `npm --prefix frontend run build`. Production: `.venv/bin/python scripts/check_production.py`. Browser scripts are documented in README.
