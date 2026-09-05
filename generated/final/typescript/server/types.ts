// Generated only after independent JSON Schema and TypeSpec agreement. DO NOT EDIT.

export const contractVersion="ores.validation.v2" as const;
export const contractScope="server" as const;

export interface InternalCommand {
  readonly context: ServerRequestContext;
  readonly idempotencyKey?: string;
  readonly operationId: string;
}

export interface ServerRequestContext {
  readonly locale?: string;
  readonly requestId: string;
  readonly roles: ReadonlyArray<string>;
  readonly sourceIp?: string;
  readonly tenantId?: string;
  readonly traceId: string;
  readonly userId: string;
}

export interface TrustedActor {
  readonly roles: ReadonlyArray<string>;
  readonly tenantId?: string;
  readonly userId: string;
}
