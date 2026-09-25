#!/usr/bin/env bash
# Run on Dental from Git: see scripts/deploy.py.
set -euo pipefail
umask 077

commit=${1:-}
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]]; then
    printf 'Usage: deploy.sh <full Git commit SHA>\n' >&2
    exit 2
fi
root=${TOURISM_DEPLOY_ROOT:-/opt/max-local-tourism}
repo="$root/repo.git"
exec 9>"$root/.deploy.lock"
flock -n 9 || { printf 'Another deployment is running\n' >&2; exit 1; }

git --git-dir="$repo" cat-file -e "$commit^{commit}"
git --git-dir="$repo" merge-base --is-ancestor "$commit" refs/heads/main
previous_release=$(readlink -f "$root/current")
previous_image=$(docker inspect --format '{{.Config.Image}}' max-local-tourism-app-1)
[[ "$previous_image" == max-local-tourism:* ]]
[[ -f "$previous_release/deploy/compose.production.yaml" ]]

tag="$(date -u +%Y%m%dT%H%M%SZ)-${commit:0:12}"
release="$root/releases/$tag"
git --git-dir="$repo" worktree add --detach "$release" "$commit"
backup="$root/backups/postgres-$tag"
mkdir -p "$backup" "$root/deployments"
docker exec max-local-tourism-db-1 pg_dump -U tourism -d tourism -Fc > "$backup/tourism.dump"
test -s "$backup/tourism.dump"

compose=(docker compose -f "$release/deploy/compose.production.yaml")
RELEASE_TAG="$tag" "${compose[@]}" build app

rollback() {
    local code=$?
    trap - ERR
    printf 'Deployment failed; restoring %s\n' "$previous_image" >&2
    if RELEASE_TAG="${previous_image#max-local-tourism:}" docker compose \
        -f "$previous_release/deploy/compose.production.yaml" \
        up -d --no-deps --wait --wait-timeout 60 app; then
        ln -sfn "$previous_release" "$root/current.next"
        mv -Tf "$root/current.next" "$root/current"
    else
        printf 'Automatic rollback failed; inspect the app container\n' >&2
    fi
    exit "$code"
}
trap rollback ERR
RELEASE_TAG="$tag" "${compose[@]}" up -d --no-deps --wait --wait-timeout 60 app
curl --fail --silent --show-error --max-time 15 http://127.0.0.1:18091/api/v1/health > /dev/null
curl --fail --silent --show-error --max-time 20 https://kaktut.ru/max/app/api/v1/health > /dev/null
# Uses synthetic signed initData from the server environment; never sends messages.
docker exec max-local-tourism-app-1 python scripts/check_production.py
printf '%s\n' "$commit" > "$root/deployments/$tag.commit"
ln -sfn "$release" "$root/current.next"
mv -Tf "$root/current.next" "$root/current"
trap - ERR
printf 'Deployed %s to %s\n' "$commit" "$release"
