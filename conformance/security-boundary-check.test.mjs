import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { audit_security_boundaries } from './security-boundary-check.mjs';

const canonical = JSON.parse(readFileSync(new URL('../contracts/ores-platform/v1/schema.json', import.meta.url), 'utf8'));
const copy = () => structuredClone(canonical);

test('canonical identity, telemetry and biometric boundaries emit a safe receipt', () => {
  assert.deepEqual(audit_security_boundaries(canonical), {
    schema: 'ores.security-boundary-receipt/v1',
    safe: true,
    findings: [],
  });
});

test('credential input losing writeOnly protection is denied', () => {
  const mutated = copy();
  delete mutated.$defs.IntrospectionRequest.properties.token.writeOnly;
  assert.deepEqual(audit_security_boundaries(mutated).findings, ['introspection-token-not-write-only']);
});

test('unsafe schema extension and weakened trace correlation are both denied', () => {
  const mutated = copy();
  mutated.$defs.SecurityEvent.additionalProperties = true;
  mutated.$defs.RequestContext.properties.traceId.pattern = '.*';
  assert.deepEqual(audit_security_boundaries(mutated).findings, ['event-open', 'otel-trace-pattern-drift']);
});

test('raw biometric material or bypassed platform verification is denied', () => {
  const mutated = copy();
  mutated.$defs.PlatformBiometricProof.properties.rawBiometricMaterialPresent.const = true;
  mutated.$defs.PlatformBiometricProof.properties.verifiedByPlatformAuthenticator.const = false;
  assert.deepEqual(audit_security_boundaries(mutated).findings, [
    'raw-biometric-material-allowed', 'platform-verification-not-required',
  ]);
});

test('delegation cap drift and absent security definitions fail closed', () => {
  const mutated = copy();
  mutated.$defs.ActorRef.properties.delegationDepth.maximum = 1000;
  assert.deepEqual(audit_security_boundaries(mutated).findings, ['actor-delegation-not-bounded']);
  delete mutated.$defs.RequestContext;
  assert.equal(audit_security_boundaries(mutated).safe, false);
  assert.ok(audit_security_boundaries(mutated).findings.includes('request-context-open'));
});
