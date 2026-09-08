import assert from 'node:assert/strict';
import { cp, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { SOURCE_ROOT, SOURCE_PATHS, validateCorpus, withPublicAdmission, verifyCurrentEvidence } from './admission.mjs';

const corpus = JSON.parse(await readFile(join(SOURCE_ROOT, SOURCE_PATHS.corpus), 'utf8'));
test('recorded corpus covers every declaration in both directions', () => assert.equal(validateCorpus(corpus).length, 31));
for (const [name, mutate] of [
  ['duplicate identities', (c) => c.push(c[0])],
  ['unknown declaration', (c) => { c[0].model = 'TrustedActor'; }],
  ['traversal identity', (c) => { c[0].id = '../escape'; }],
  ['implicit verdict', (c) => { delete c[0].valid; }],
  ['missing payload', (c) => { delete c[0].value; }],
  ['missing positive evidence', (c) => c.splice(0, c.length, ...c.filter((x) => x.model !== 'RequestMeta' || !x.valid))],
]) test(`corpus rejects ${name}`, () => {
  const changed = structuredClone(corpus); mutate(changed);
  assert.throws(() => validateCorpus(changed));
});

test('real compiler and canonical CLI verification fail closed', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'ores-public-test-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  await cp(join(SOURCE_ROOT, 'validation'), join(root, 'validation'), { recursive: true });
  const options = { sourceRoot: root, validatorRoot: join(SOURCE_ROOT, '.deps/tjsv') };
  await withPublicAdmission(options, async (evidence) => {
    await t.test('admits all four real shared declarations', () => {
      assert.equal(evidence.summary.status, 'passed');
      assert.equal(evidence.summary.recordedCases, 31);
      assert.equal(evidence.contractIr.admission.scope.complete, true);
      assert.deepEqual(evidence.contractIr.declarations.map((x) => x.id).sort(), evidence.summary.declarations);
    });
    for (const key of ['typespec', 'authoredSchema', 'generatedSchema']) {
      await t.test(`rejects stale ${key} rather than trusting a copied pass`, async () => {
        const path = evidence.paths[key];
        const old = await readFile(path, 'utf8');
        try {
          await writeFile(path, `${old}\n `);
          await assert.rejects(verifyCurrentEvidence(evidence.validatorRoot, evidence.paths));
        } finally { await writeFile(path, old); }
      });
    }
    await t.test('rejects forged admissible IR bytes', async () => {
      const old = await readFile(evidence.paths.ir, 'utf8');
      try {
        const changed = JSON.parse(old); changed.declarations[0].assertionSchema = { type: 'null' };
        await writeFile(evidence.paths.ir, JSON.stringify(changed));
        await assert.rejects(verifyCurrentEvidence(evidence.validatorRoot, evidence.paths));
      } finally { await writeFile(evidence.paths.ir, old); }
    });
  });
  await t.test('wrong recorded expectation stops new compilation', async () => {
    const path = join(root, SOURCE_PATHS.corpus), old = await readFile(path, 'utf8');
    const changed = JSON.parse(old); changed[0].valid = false;
    try { await writeFile(path, JSON.stringify(changed)); await assert.rejects(withPublicAdmission(options), /admission stopped/); }
    finally { await writeFile(path, old); }
  });
  await t.test('unmapped extra declaration cannot enter a public export', async () => {
    const path = join(root, SOURCE_PATHS.typespec), old = await readFile(path, 'utf8');
    try {
      await writeFile(path, `${old}\nmodel TrustedActor { userId: string; }\n`);
      await assert.rejects(withPublicAdmission(options), /admission stopped/);
    } finally { await writeFile(path, old); }
  });
});
