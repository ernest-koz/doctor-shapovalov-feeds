#!/usr/bin/env bash
# Одноразовый деплой: создать публичный репо, запушить, включить GitHub Pages (/docs).
# Запускать ПОСЛЕ `gh auth refresh`. Requires: gh, git.
set -euo pipefail
cd "$(dirname "$0")"

REPO="ernest-koz/doctor-shapovalov-feeds"

python generator.py

if gh repo view "$REPO" >/dev/null 2>&1; then
  echo "repo exists, pushing..."
  git init -q 2>/dev/null || true
  git remote remove origin 2>/dev/null || true
  git remote add origin "https://github.com/$REPO.git"
  git add -A && git commit -q -m "feed generator: services.yaml, actions, docs" || true
  git branch -M main
  git push -u origin main
else
  gh repo create "$REPO" --public --source . --push --description "Товарные фиды услуг doctor-shapovalov.ru для Яндекс.Вебмастера и VK Рекламы (автогенерация)"
fi

# включить Pages из /docs на main
gh api -X POST "repos/$REPO/pages" \
  -f 'source[branch]=main' -f 'source[path]=/docs' >/dev/null 2>&1 || \
  echo "Pages уже включён (или включи вручную: Settings → Pages → main /docs)"

echo
echo "ГОТОВО. Через ~2 минуты проверь:"
echo "  https://ernest-koz.github.io/doctor-shapovalov-feeds/"
echo "  https://ernest-koz.github.io/doctor-shapovalov-feeds/feed.yml"
