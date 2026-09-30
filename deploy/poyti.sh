#!/usr/bin/env bash
# Git deployment to poyti.online, including first installation.
set -euo pipefail
umask 077
commit=${1:-}
[[ "$commit" =~ ^[0-9a-f]{40}$ ]]
root=/opt/max-local-tourism
repo="$root/repo.git"
exec 9>"$root/.deploy.lock"
flock -n 9
git --git-dir="$repo" merge-base --is-ancestor "$commit" refs/heads/main
tag="$(date -u +%Y%m%dT%H%M%SZ)-${commit:0:12}"
release="$root/releases/$tag"
backup="$root/backups/$tag"
mkdir -p "$backup" "$root/deployments"
cp /etc/caddy/Caddyfile "$backup/Caddyfile"
previous_release=$(readlink -f "$root/current" || true)
previous_image=$(docker inspect --format '{{.Config.Image}}' max-local-tourism-app-1 2>/dev/null || true)
git --git-dir="$repo" worktree add --detach "$release" "$commit"
compose=(docker compose -f "$release/deploy/compose.poyti.yaml")
RELEASE_TAG="$tag" "${compose[@]}" build app
if docker inspect max-local-tourism-db-1 >/dev/null 2>&1; then
    docker exec max-local-tourism-db-1 pg_dump -U tourism -d tourism -Fc > "$backup/tourism.dump"
    test -s "$backup/tourism.dump"
else
    "${compose[@]}" up -d --no-deps --wait --wait-timeout 90 db
fi
rollback() {
    code=$?
    trap - ERR
    cp "$backup/Caddyfile" /etc/caddy/Caddyfile
    systemctl reload caddy
    if [[ -n "$previous_image" && -f "$previous_release/deploy/compose.poyti.yaml" ]]; then
        RELEASE_TAG="${previous_image#max-local-tourism:}" docker compose -f "$previous_release/deploy/compose.poyti.yaml" up -d --no-deps --wait app
    else
        "${compose[@]}" stop app
    fi
    exit "$code"
}
trap rollback ERR
RELEASE_TAG="$tag" "${compose[@]}" up -d --no-deps --wait --wait-timeout 90 app
docker exec max-local-tourism-app-1 python scripts/check_production.py --base-url http://127.0.0.1:8000
cat > "$backup/Caddyfile.next" <<'CADDY'
poyti.online {
    reverse_proxy 127.0.0.1:18091
}
CADDY
caddy validate --config "$backup/Caddyfile.next" --adapter caddyfile
install -m 644 "$backup/Caddyfile.next" /etc/caddy/Caddyfile
systemctl reload caddy
docker exec max-local-tourism-app-1 python scripts/check_production.py --base-url https://poyti.online
printf '%s\n' "$commit" > "$root/deployments/$tag.commit"
ln -sfn "$release" "$root/current.next"
mv -Tf "$root/current.next" "$root/current"
trap - ERR
printf 'Deployed %s to https://poyti.online\n' "$commit"
