import assert from 'node:assert/strict';
import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdir, mkdtemp, readFile, realpath, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { promisify } from 'node:util';

const exec = promisify(execFile);
export const SOURCE_ROOT = resolve(import.meta.dirname, '../..');
export const SOURCE_LOCK_PATH = 'validation/tjsv/source-lock.json';
const sourceLockDocument = JSON.parse(await readFile(new URL('./source-lock.json', import.meta.url), 'utf8'));
assert.deepEqual(Object.keys(sourceLockDocument).sort(), ['repository', 'revision', 'schema']);
assert.equal(sourceLockDocument.schema, 'ores.tjsv-source-lock/v1');
assert.equal(sourceLockDocument.repository, 'ORESoftware/typespec-json-schema-validator');
assert.match(sourceLockDocument.revision, /^[0-9a-f]{40}$/, 'TJSV revision must be an immutable lowercase Git commit');
export const SOURCE_LOCK = Object.freeze({ ...sourceLockDocument });
export const VALIDATOR_REPOSITORY = SOURCE_LOCK.repository;
export const VALIDATOR_REVISION = SOURCE_LOCK.revision;
export const DECLARATIONS = Object.freeze([
  'Ores.Validation.GitHubActionsBuildLogEvent', 'Ores.Validation.GitHubActionsLogStream',
  'Ores.Validation.PageQuery', 'Ores.Validation.ProblemDetails',
  'Ores.Validation.PublicValidationContract', 'Ores.Validation.RequestMeta',
]);
export const SOURCE_PATHS = Object.freeze({
  typespec: 'validation/typespec/validation.tsp',
  authoredSchema: 'validation/public-contracts.v1.json',
  corpus: 'validation/tjsv/public-corpus.json',
  sourceLock: SOURCE_LOCK_PATH,
});
export const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');

export function validateCorpus(cases) {
  assert.ok(Array.isArray(cases) && cases.length > 0, 'recorded corpus is required');
  const coverage = new Map(DECLARATIONS.map((id) => [id.split('.').at(-1), new Set()]));
  const seen = new Set();
  for (const entry of cases) {
    assert.ok(entry && coverage.has(entry.model), 'unknown corpus declaration');
    assert.match(entry.id, /^[a-z][a-z0-9-]*$/, 'unsafe fixture identity');
    assert.equal(typeof entry.valid, 'boolean', 'explicit expected verdict required');
    assert.ok(Object.hasOwn(entry, 'value'), 'fixture payload is required');
    const key = `${entry.model}/${entry.id}`;
    assert.ok(!seen.has(key), 'duplicate corpus identity');
    seen.add(key);
    coverage.get(entry.model).add(entry.valid);
  }
  for (const verdicts of coverage.values()) assert.equal(verdicts.size, 2, 'every declaration needs positive and negative evidence');
  return cases;
}

export async function assertValidatorPin(validatorRoot) {
  const actual = (await exec('git', ['-C', validatorRoot, 'rev-parse', 'HEAD'])).stdout.trim();
  assert.equal(actual, VALIDATOR_REVISION, 'unexpected TJSV revision');
  await exec('git', ['-C', validatorRoot, 'diff', '--exit-code', 'HEAD']);
}

// Fixed task interface: options are explicit library inputs, never another argv parser.
// Public CLI flags belong solely to TJSV's root .cli-flags.toml / flags-2-env.
async function runValidator(validatorRoot, args) {
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('TSJSV_')));
  return exec(process.execPath, [join(validatorRoot, 'bin/typespec-json-schema-validator.mjs'), ...args],
    { env, cwd: validatorRoot, timeout: 120000, maxBuffer: 2 * 1024 * 1024 });
}

export async function verifyCurrentEvidence(validatorRoot, paths) {
  await runValidator(validatorRoot, ['verify-ir', `--contract-ir=${paths.ir}`,
    `--parity-receipt=${paths.report}`, `--typespec=${paths.typespec}`,
    `--schema=${paths.authoredSchema}`, `--generated-schema=${paths.generatedSchema}`,
    `--expected-declarations=${JSON.stringify(DECLARATIONS)}`, `--verification=${paths.verification}`, '--quiet']);
}

/** Compile actual peer authorities; allow a trusted consumer only while fresh evidence exists. */
export async function withPublicAdmission({ sourceRoot = SOURCE_ROOT,
  validatorRoot = join(SOURCE_ROOT, '.deps/tjsv') } = {}, consume = (evidence) => evidence.summary) {
  sourceRoot = await realpath(sourceRoot);
  validatorRoot = await realpath(validatorRoot);
  await assertValidatorPin(validatorRoot);
  const originals = Object.fromEntries(await Promise.all(Object.entries(SOURCE_PATHS).map(async ([key, path]) =>
    [key, await readFile(join(sourceRoot, path), 'utf8')])));
  const cases = validateCorpus(JSON.parse(originals.corpus));
  const work = await mkdtemp(join(tmpdir(), 'ores-public-admission-'));
  const instances = join(work, 'instances');
  for (const entry of cases) {
    const dir = join(instances, entry.model, entry.valid ? 'valid' : 'invalid');
    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, `${entry.id}.json`), JSON.stringify(entry.value));
  }
  const paths = Object.freeze({ typespec: join(sourceRoot, SOURCE_PATHS.typespec),
    authoredSchema: join(sourceRoot, SOURCE_PATHS.authoredSchema),
    report: join(work, 'report.json'), ir: join(work, 'contract-ir.json'),
    generatedSchema: join(work, 'witness/typespec.generated.schema.json'),
    verification: join(work, 'verification.json') });
  try {
    await runValidator(validatorRoot, ['check', `--typespec=${paths.typespec}`,
      `--schema=${paths.authoredSchema}`, `--instances=${instances}`, '--probes=true', '--max-probes=64',
      '--seal-object-schemas=false', `--output-dir=${join(work, 'witness')}`,
      `--report=${paths.report}`, `--contract-ir=${paths.ir}`, '--quiet']);
  } catch (error) {
    const detail = await readFile(paths.report, 'utf8').catch(() => error.stderr || error.message);
    throw new Error(`public contract admission stopped: ${detail.slice(0, 12000)}`, { cause: error });
  }
  await verifyCurrentEvidence(validatorRoot, paths);
  // Bind the original committed corpus and source lock, not only materialized instance copies.
  for (const [key, path] of Object.entries(SOURCE_PATHS))
    assert.equal(await readFile(join(sourceRoot, path), 'utf8'), originals[key], `source changed during admission: ${path}`);
  const [report, contractIr, verification] = await Promise.all([paths.report, paths.ir, paths.verification]
    .map(async (path) => JSON.parse(await readFile(path, 'utf8'))));
  const summary = Object.freeze({ schema: 'ores.shared-public-admission/v1', status: 'passed',
    validatorRepository: VALIDATOR_REPOSITORY, validatorRevision: VALIDATOR_REVISION,
    irId: contractIr.irId, runId: report.runId,
    declarations: DECLARATIONS, recordedCases: cases.length,
    sourceDigests: Object.fromEntries(Object.entries(originals).map(([key, text]) => [key, sha256(text)])) });
  // The operating system or ephemeral CI runner owns cleanup of this invocation-specific
  // temporary directory. The admission library never recursively deletes filesystem state.
  return await consume(Object.freeze({ summary, paths, report, contractIr, verification,
    sources: Object.freeze(originals), validatorRoot }));
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    assert.equal(process.argv.length, 2, 'this repository task accepts no command-line options');
    console.log(JSON.stringify(await withPublicAdmission()));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 2;
  }
}
