namespace Ores.Validation.Server;

model TrustedActor {
  @minLength(1) @maxLength(128) userId: string;
  @minLength(1) @maxLength(128) tenantId?: string;
  roles: string[];
}

model ServerRequestContext {
  @minLength(1) @maxLength(128) requestId: string;
  @minLength(1) @maxLength(128) traceId: string;
  @minLength(2) @maxLength(64) locale?: string;
  @minLength(1) @maxLength(128) userId: string;
  @minLength(1) @maxLength(128) tenantId?: string;
  roles: string[];
  @minLength(1) @maxLength(64) sourceIp?: string;
}

model InternalCommand {
  @minLength(1) @maxLength(256) operationId: string;
  @minLength(1) @maxLength(128) idempotencyKey?: string;
  context: ServerRequestContext;
}
