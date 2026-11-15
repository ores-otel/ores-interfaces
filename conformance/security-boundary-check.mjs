#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const source = new URL('../contracts/ores-platform/v1/schema.json', import.meta.url);

/**
 * Inspect the canonical authored schema; this is a schema guard, not runtime
 * credential validation or a replacement for full JSON Schema conformance.
 * Missing definitions fail closed and findings contain only stable labels.
 */
export function audit_security_boundaries(schema) {
  const findings = [];
  const get = (...keys) => keys.reduce((value, key) => value?.[key], schema);
  const require_exact = (code, path, expected) => {
    if (get(...path) !== expected) findings.push(code);
  };

  require_exact('root-open', ['additionalProperties'], false);
  require_exact('introspection-open', ['$defs', 'IntrospectionRequest', 'additionalProperties'], false);
  require_exact('introspection-token-not-write-only', ['$defs', 'IntrospectionRequest', 'properties', 'token', 'writeOnly'], true);
  require_exact('token-claims-open', ['$defs', 'TokenClaims', 'additionalProperties'], false);
  require_exact('event-open', ['$defs', 'SecurityEvent', 'additionalProperties'], false);
  require_exact('request-context-open', ['$defs', 'RequestContext', 'additionalProperties'], false);
  require_exact('biometric-proof-open', ['$defs', 'PlatformBiometricProof', 'additionalProperties'], false);
  require_exact('raw-biometric-material-allowed', ['$defs', 'PlatformBiometricProof', 'properties', 'rawBiometricMaterialPresent', 'const'], false);
  require_exact('platform-verification-not-required', ['$defs', 'PlatformBiometricProof', 'properties', 'verifiedByPlatformAuthenticator', 'const'], true);
  require_exact('user-verification-not-required', ['$defs', 'PlatformBiometricProof', 'properties', 'userVerification', 'const'], 'required');
  require_exact('actor-delegation-not-bounded', ['$defs', 'ActorRef', 'properties', 'delegationDepth', 'maximum'], 8);
  require_exact('otel-trace-pattern-drift', ['$defs', 'RequestContext', 'properties', 'traceId', 'pattern'], '^[0-9a-f]{32}$');
  require_exact('otel-span-pattern-drift', ['$defs', 'RequestContext', 'properties', 'spanId', 'pattern'], '^[0-9a-f]{16}$');

  return Object.freeze({
    schema: 'ores.security-boundary-receipt/v1',
    safe: findings.length === 0,
    findings: Object.freeze(findings),
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const data = JSON.parse(await readFile(source, 'utf8'));
    const receipt = audit_security_boundaries(data);
    console.log(JSON.stringify(receipt));
    if (!receipt.safe) process.exitCode = 1;
  } catch {
    console.error('security-boundary: canonical schema unavailable or malformed');
    process.exitCode = 1;
  }
}
