#!/usr/bin/env node
/**
 * Build / verify catalog.json from models/<id>/{model.json, model.vrm, thumb.jpg}.
 *
 *   node scripts/build-catalog.mjs          # regenerate catalog.json
 *   node scripts/build-catalog.mjs --check  # CI: fail if catalog.json is stale or any rule is broken
 *
 * Rules (also enforced again by the app at runtime):
 *  - license must be an SPDX id from allowed-licenses.json
 *  - id: [a-z0-9-]{2,64}; version: semver x.y.z
 *  - model.vrm must be a GLB with a VRM / VRMC_vrm extension, <= 200 MB
 *  - thumb.jpg|png <= 1 MB
 *  - every URL is https; sha256 + size are mandatory
 */
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const REPO = 'Cookieboty/companion-desk-models';
const MAX_VRM = 200 * 1024 * 1024;
const MAX_THUMB = 1024 * 1024;
const allowed = new Set(JSON.parse(fs.readFileSync(path.join(ROOT, 'allowed-licenses.json'), 'utf8')).allowed);
const check = process.argv.includes('--check');
const errors = [];

const sha256 = (buf) => createHash('sha256').update(buf).digest('hex');

function vrmVersionOf(buf, id) {
  if (buf.readUInt32LE(0) !== 0x46546c67 || buf.readUInt32LE(4) !== 2) {
    errors.push(`${id}: model.vrm is not a glTF 2.0 binary`);
    return null;
  }
  const len = buf.readUInt32LE(12);
  const json = JSON.parse(buf.subarray(20, 20 + len).toString('utf8'));
  const used = json.extensionsUsed ?? [];
  if (used.includes('VRMC_vrm')) return '1.0';
  if (used.includes('VRM')) return '0.x';
  errors.push(`${id}: model.vrm has no VRM / VRMC_vrm extension`);
  return null;
}

const urlsFor = (tag, file) => [
  `https://cdn.jsdelivr.net/gh/${REPO}@${tag}/${file}`,
  `https://raw.githubusercontent.com/${REPO}/${tag}/${file}`,
];

const models = [];
for (const id of fs.readdirSync(path.join(ROOT, 'models')).sort()) {
  const dir = path.join(ROOT, 'models', id);
  if (!fs.statSync(dir).isDirectory()) continue;
  const meta = JSON.parse(fs.readFileSync(path.join(dir, 'model.json'), 'utf8'));
  if (meta.id !== id) errors.push(`${id}: model.json id "${meta.id}" must equal the folder name`);
  if (!/^[a-z0-9-]{2,64}$/.test(id)) errors.push(`${id}: invalid id`);
  if (!/^\d+\.\d+\.\d+$/.test(meta.version ?? '')) errors.push(`${id}: version must be x.y.z`);
  if (!allowed.has(meta.license)) errors.push(`${id}: licence "${meta.license}" is not allowed`);
  for (const k of ['name', 'author', 'source', 'credit']) if (!meta[k]) errors.push(`${id}: missing ${k}`);
  if (meta.source && !meta.source.startsWith('https://')) errors.push(`${id}: source must be https`);

  const vrm = fs.readFileSync(path.join(dir, 'model.vrm'));
  if (vrm.length > MAX_VRM) errors.push(`${id}: model.vrm exceeds 200 MB`);
  const detected = vrmVersionOf(vrm, id);
  if (detected && meta.vrmVersion && meta.vrmVersion !== detected)
    errors.push(`${id}: vrmVersion "${meta.vrmVersion}" but file is ${detected}`);
  const thumbName = ['thumb.jpg', 'thumb.png'].find((f) => fs.existsSync(path.join(dir, f)));
  if (!thumbName) errors.push(`${id}: missing thumb.jpg / thumb.png`);
  const thumb = thumbName ? fs.readFileSync(path.join(dir, thumbName)) : Buffer.alloc(0);
  if (thumb.length > MAX_THUMB) errors.push(`${id}: thumbnail exceeds 1 MB`);

  const tag = `${id}-v${meta.version}`;
  models.push({
    id,
    name: meta.name,
    description: meta.description ?? '',
    author: meta.author,
    license: meta.license,
    source: meta.source,
    version: meta.version,
    vrmVersion: detected ?? meta.vrmVersion,
    tags: meta.tags ?? [],
    credit: meta.credit,
    vrm: {
      // Releases first (no per-file CDN limit), then jsDelivr (<= 20 MB per file) and raw as fallbacks
      urls: [
        `https://github.com/${REPO}/releases/download/${tag}/${id}.vrm`,
        ...(vrm.length <= 20 * 1024 * 1024 ? urlsFor(tag, `models/${id}/model.vrm`) : []),
      ],
      sha256: sha256(vrm),
      size: vrm.length,
    },
    thumbnail: {
      urls: urlsFor(tag, `models/${id}/${thumbName}`),
      sha256: sha256(thumb),
      size: thumb.length,
    },
  });
}

const catalog = { schemaVersion: 1, repository: `https://github.com/${REPO}`, models };
const out = path.join(ROOT, 'catalog.json');
const text = `${JSON.stringify(catalog, null, 2)}\n`;
if (check) {
  const current = fs.existsSync(out) ? fs.readFileSync(out, 'utf8') : '';
  if (current !== text) errors.push('catalog.json is stale — run node scripts/build-catalog.mjs');
} else if (!errors.length) {
  fs.writeFileSync(out, text);
}
if (errors.length) {
  for (const e of errors) console.error(`✖ ${e}`);
  process.exit(1);
}
console.log(`✔ ${models.length} models ${check ? 'verified' : 'written to catalog.json'}`);
