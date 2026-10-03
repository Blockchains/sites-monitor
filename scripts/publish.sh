#!/usr/bin/env bash
# Commit + push the gh-pages worktree at ./pages (data JSON + static status site). Retries on races.
set -euo pipefail
msg="${1:-update data}"
mkdir -p pages
cp -r site/. pages/
cp domains.json pages/domains.json
touch pages/.nojekyll
cd pages
git config user.name "sites-monitor[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git commit -q -m "$msg"
for i in 1 2 3 4 5; do
  if git push -q origin HEAD:gh-pages; then echo "pushed"; exit 0; fi
  echo "push race, rebasing (attempt $i)"; sleep $((i * 3))
  git pull -q --rebase -X theirs origin gh-pages || { git rebase --abort || true; git pull -q --no-rebase -X ours origin gh-pages; }
done
echo "push failed"; exit 1
