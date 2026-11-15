import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFile, mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const valid = {
  schema: 'ores.conformance.case/v1',
  kind: 'behavior',
  id: 'case-shape-negative',
  version: 1,
  input: { signal: 'trace' },
  expected: { accepted: true },
  notes: ['valid freeform explanation']
};

async function verifyCase(overrides) {
  const temp = await mkdtemp(join(tmpdir(), 'ores-conformance-case-'));
  try {
    await mkdir(join(temp, 'conformance', 'cases'), { recursive: true });
    await mkdir(join(temp, 'contracts'), { recursive: true });
    await copyFile(join(root, 'conformance', 'check.mjs'), join(temp, 'conformance', 'check.mjs'));
    await copyFile(join(root, 'conformance', 'case.schema.json'), join(temp, 'conformance', 'case.schema.json'));
    const manifest = JSON.parse(await readFile(join(root, 'conformance', 'manifest.v1.json'), 'utf8'));
    await writeFile(join(temp, 'conformance', 'manifest.v1.json'), JSON.stringify(manifest));
    await writeFile(join(temp, 'contracts', 'authority.json'), '{"type":"object"}');
    await writeFile(join(temp, 'conformance', 'cases', 'case.json'), JSON.stringify({ ...valid, ...overrides }));
    return spawnSync(process.execPath, [join(temp, 'conformance', 'check.mjs')], {
      cwd: temp, encoding: 'utf8',
      env: { ...process.env, GITHUB_REPOSITORY: manifest.repository },
      timeout: 10_000
    });
  } finally {
    await rm(temp, { recursive: true, force: true });
  }
}

test('valid behavioral case with string notes is accepted', async () => {
  const result = await verifyCase({});
  assert.equal(result.status, 0, result.stderr);
  assert.equal(JSON.parse(result.stdout).behaviorCaseCount, 1);
});

test('unrecognized behavioral case fields fail closed', async () => {
  const result = await verifyCase({ secretPayload: 'should-never-be-authority' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /unknown behavior case field/);
});

test('notes must be an array, not a freeform string', async () => {
  const result = await verifyCase({ notes: 'not-an-array' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /notes must be an array of strings/);
});

test('every notes element must be a string', async () => {
  const result = await verifyCase({ notes: ['good', 42] });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /notes must be an array of strings/);
});
