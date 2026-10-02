import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import test from 'node:test';

import {
  SOURCE_LOCK,
  SOURCE_LOCK_PATH,
  SOURCE_PATHS,
  SOURCE_ROOT,
  VALIDATOR_REPOSITORY,
  VALIDATOR_REVISION,
  sha256,
} from './admission.mjs';

const raw = await readFile(join(SOURCE_ROOT, SOURCE_LOCK_PATH), 'utf8');
const parsed = JSON.parse(raw);

test('source lock is closed, immutable, and names the canonical public validator', () => {
  assert.deepEqual(Object.keys(parsed).sort(), ['repository', 'revision', 'schema']);
  assert.equal(parsed.schema, 'ores.tjsv-source-lock/v1');
  assert.equal(parsed.repository, 'ORESoftware/typespec-json-schema-validator');
  assert.match(parsed.revision, /^[0-9a-f]{40}$/);
  assert.deepEqual(SOURCE_LOCK, parsed);
  assert.ok(Object.isFrozen(SOURCE_LOCK));
  assert.equal(VALIDATOR_REPOSITORY, parsed.repository);
  assert.equal(VALIDATOR_REVISION, parsed.revision);
});

test('source lock participates in the admission source-digest closure', () => {
  assert.equal(SOURCE_PATHS.sourceLock, SOURCE_LOCK_PATH);
  assert.match(sha256(raw), /^[0-9a-f]{64}$/);
});
