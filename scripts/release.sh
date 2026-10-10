#!/usr/bin/env bash
# Publish one model version as a GitHub Release (tag <id>-v<version>, asset <id>.vrm).
# Usage: scripts/release.sh <id>     (run after the PR adding/updating the model is merged)
set -euo pipefail
id="$1"
version=$(node -p "require('./models/$id/model.json').version")
tag="$id-v$version"
tmp=$(mktemp -d)
cp "models/$id/model.vrm" "$tmp/$id.vrm"
git tag "$tag" 2>/dev/null || true
git push origin "$tag"
gh release create "$tag" "$tmp/$id.vrm" --title "$tag" \
  --notes "$(node -p "const m=require('./models/$id/model.json');m.credit+'\n\nLicence: '+m.license+'\nSource: '+m.source")"
rm -rf "$tmp"
