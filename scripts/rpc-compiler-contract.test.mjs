import assert from 'node:assert/strict';
import {
  lstatSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { basename, join, relative } from 'node:path';
import { spawnSync } from 'node:child_process';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const repositoryRoot = fileURLToPath(new URL('../', import.meta.url));
const contractRoot = join(repositoryRoot, 'contracts/rpc-retry/v1');
const contractRequire = createRequire(join(contractRoot, 'package.json'));
const Ajv2020 = contractRequire('ajv/dist/2020').default;
const executable = (name) => join(
  contractRoot,
  'node_modules',
  '.bin',
  process.platform === 'win32' ? `${name}.cmd` : name,
);

function run(label, command, args, cwd = contractRoot) {
  const completed = spawnSync(command, args, {
    cwd,
    encoding: 'utf8',
    env: { ...process.env, NO_COLOR: '1' },
  });
  assert.equal(
    completed.status,
    0,
    `${label} failed\nstdout:\n${completed.stdout}\nstderr:\n${completed.stderr}`,
  );
}

function regularFiles(root, current = root) {
  return readdirSync(current, { withFileTypes: true }).flatMap((entry) => {
    const path = join(current, entry.name);
    const stat = lstatSync(path);
    assert.equal(stat.isSymbolicLink(), false, `generated output must not be a symlink: ${path}`);
    if (stat.isDirectory()) return regularFiles(root, path);
    assert.equal(stat.isFile(), true, `generated output must be a regular file: ${path}`);
    return [relative(root, path)];
  }).sort();
}

function compile(label) {
  const temporaryRoot = mkdtempSync(join(tmpdir(), `ores-rpc-${label}-`));
  const output = join(temporaryRoot, 'generated');
  run(
    `TypeSpec ${label}`,
    executable('tsp'),
    ['compile', '.', '--warn-as-error', '--output-dir', output],
  );
  return { output, temporaryRoot };
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function writeBufConfig(temporaryRoot) {
  writeFileSync(join(temporaryRoot, 'buf.yaml'), `version: v2
modules:
  - path: generated/protobuf
lint:
  use:
    - STANDARD
  except:
    - PACKAGE_DIRECTORY_MATCH
`);
}

test('TypeSpec generation is deterministic and matches committed artifacts', () => {
  const first = compile('first');
  const second = compile('second');
  const committed = join(contractRoot, 'generated');
  const expectedFiles = [
    'json-schema/RetryAttempt.json',
    'json-schema/RetryDecision.json',
    'json-schema/RetryInput.json',
    'json-schema/RetryPolicy.json',
    'protobuf/ores/rpc/v1.proto',
  ];

  assert.deepEqual(regularFiles(first.output), expectedFiles);
  assert.deepEqual(regularFiles(second.output), expectedFiles);
  assert.deepEqual(regularFiles(committed), expectedFiles);

  for (const path of expectedFiles) {
    const generatedOnce = readFileSync(join(first.output, path));
    const generatedTwice = readFileSync(join(second.output, path));
    const reviewedArtifact = readFileSync(join(committed, path));
    assert.deepEqual(generatedOnce, generatedTwice, `${path} is nondeterministic`);
    assert.deepEqual(generatedOnce, reviewedArtifact, `${path} is stale`);
  }

  for (const result of [first, second]) {
    writeBufConfig(result.temporaryRoot);
    run(
      `Buf lint ${basename(result.temporaryRoot)}`,
      executable('buf'),
      ['lint', '--config', 'buf.yaml'],
      result.temporaryRoot,
    );
    run(
      `Buf descriptor ${basename(result.temporaryRoot)}`,
      executable('buf'),
      [
        'build',
        '--config',
        'buf.yaml',
        '--as-file-descriptor-set',
        '-o',
        join(result.temporaryRoot, 'retry-descriptor.binpb'),
      ],
      result.temporaryRoot,
    );
  }
  assert.deepEqual(
    readFileSync(join(first.temporaryRoot, 'retry-descriptor.binpb')),
    readFileSync(join(second.temporaryRoot, 'retry-descriptor.binpb')),
    'Protobuf descriptor set is nondeterministic',
  );
});

test('generated JSON Schemas accept and reject reviewed boundary instances', () => {
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  for (const name of ['RetryPolicy', 'RetryAttempt', 'RetryInput', 'RetryDecision']) {
    ajv.addSchema(readJson(join(contractRoot, `generated/json-schema/${name}.json`)));
  }
  const instances = readJson(join(contractRoot, 'instances.json'));

  for (const [name, cases] of Object.entries(instances)) {
    const validate = ajv.getSchema(`${name}.json`);
    assert.ok(validate, `validator exists for ${name}`);
    for (const value of cases.valid) {
      assert.equal(validate(value), true, `${name} valid fixture: ${ajv.errorsText(validate.errors)}`);
    }
    for (const fixture of cases.invalid) {
      assert.equal(validate(fixture.value), false, `${name} accepted invalid fixture: ${fixture.name}`);
    }
  }
});
