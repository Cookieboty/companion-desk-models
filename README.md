# companion-desk-models

Remote model catalog for [Companion Desk](https://github.com/Cookieboty/companion-desk).
The app's **模型商店 / Model store** tab reads [`catalog.json`](catalog.json), shows thumbnails and
licence badges, and downloads the selected VRM into the user's local `userData/models/remote/`
after verifying its **sha256** and size.

- Code & metadata: MIT (see `LICENSE`).
- Models: each model has **its own licence** (see `models/<id>/model.json` and `catalog.json`).
  Only open licences listed in [`allowed-licenses.json`](allowed-licenses.json) are accepted —
  the app re-checks this and silently drops anything else.

## Catalog format (`schemaVersion: 1`)

```jsonc
{
  "schemaVersion": 1,
  "repository": "https://github.com/Cookieboty/companion-desk-models",
  "models": [
    {
      "id": "vita",                 // [a-z0-9-]{2,64}, stable forever (users' selections refer to it)
      "name": "ヴィータ (Vita)",
      "description": "…",
      "author": "pixiv Inc. / VRoid Project",
      "license": "CC0-1.0",         // SPDX id, must be in allowed-licenses.json
      "source": "https://…",        // where the model was originally published (https)
      "version": "1.0.0",           // bump to push an update to users
      "vrmVersion": "0.x",          // "0.x" | "1.0" (detected from the file)
      "tags": ["vroid"],
      "credit": "Text shown on the in-app Credits screen (required for CC-BY)",
      "vrm":       { "urls": ["https://github.com/…/releases/download/vita-v1.0.0/vita.vrm", "jsDelivr…", "raw…"],
                     "sha256": "…", "size": 14198800 },
      "thumbnail": { "urls": ["jsDelivr…", "raw…"], "sha256": "…", "size": 13269 }
    }
  ]
}
```

URLs are tried in order. **GitHub Releases** come first because jsDelivr only serves files up to
20 MB from GitHub repos (larger VRMs simply omit the jsDelivr URL); `raw.githubusercontent.com` is
the last fallback. Every URL must be `https`, and `sha256` + `size` are mandatory: a mismatching
download is discarded.

The app fetches the catalog from (first that works, cached with ETag):

1. `https://raw.githubusercontent.com/Cookieboty/companion-desk-models/main/catalog.json`
2. `https://cdn.jsdelivr.net/gh/Cookieboty/companion-desk-models@main/catalog.json`

Override with the `COMPANION_MODEL_CATALOG_URL` environment variable.

## Adding a model (PR)

1. Make sure the licence allows redistribution and is in `allowed-licenses.json`
   (CC0-1.0, CC-BY-4.0, CC-BY-SA-4.0, …). **No** "personal use only", NC, ND, or VRoid-Hub-only models.
   For CC-BY / CC-BY-SA the `credit` text must name the author and licence.
2. Add `models/<id>/model.vrm` (VRM 0.x or 1.0, ≤ 200 MB), `models/<id>/thumb.jpg` (≤ 1 MB, square-ish)
   and `models/<id>/model.json`:

   ```json
   {
     "id": "<id>",
     "name": "Display name",
     "description": "",
     "author": "Original author",
     "license": "CC-BY-4.0",
     "source": "https://where-it-was-published",
     "version": "1.0.0",
     "vrmVersion": "1.0",
     "tags": [],
     "credit": "\"Display name\" by Author, CC BY 4.0, https://…"
   }
   ```
3. Run `node scripts/build-catalog.mjs` and commit the updated `catalog.json`. CI runs
   `--check` (licence allow-list, VRM header, sizes, https, catalog freshness).
4. After merge a maintainer runs `scripts/release.sh <id>` which tags `<id>-v<version>` and uploads
   the VRM as a release asset (the URLs in `catalog.json` already point there).

To **update** a model, replace the files, bump `version`, rebuild the catalog and release again —
the app shows "update available" for users who installed the old version.

## Current models

| id | name | licence |
| --- | --- | --- |
| default-character | 千駄ヶ谷 渋 (Sendagaya Shibu) | CC0-1.0 |
| sendagaya-shino | 千駄ヶ谷 篠 (Sendagaya Shino) | CC0-1.0 |
| vivi | ビビ (Vivi) | CC0-1.0 |
| vita | ヴィータ (Vita) | CC0-1.0 |
| victoria-rubin | ヴィクトリア・ルービン (Victoria Rubin) | CC0-1.0 |

All five are VRoid sample models by pixiv Inc. / VRoid Project, released under CC0 1.0
(<https://opengameart.org/content/vroid-studio-cc0-models>).
