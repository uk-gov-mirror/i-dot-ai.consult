import type { MiddlewareHandler } from "astro";
import {
  configureOtel,
  createLogger,
} from "@i-dot-ai-npm/utilities-observability";

export interface LoggerAdapter {
  middleware: MiddlewareHandler;
}

const SERVICE_NAME = "consult-frontend-service";

const disabledLogger: LoggerAdapter = {
  middleware: async (_, next) => next(),
};

// Prefer the runtime value (server) and fall back to the build-time value,
// matching the env-reading pattern in utils.ts. OTel stays dormant unless the
// flag is on and a collector endpoint is set, mirroring the backend bootstrap.
const readEnv = (
  key: string,
  buildTimeValue: string | undefined,
): string | undefined => {
  if (typeof process !== "undefined" && process.env?.[key]) {
    return process.env[key];
  }
  return buildTimeValue || undefined;
};

const otlpEndpoint = readEnv(
  "OTEL_EXPORTER_OTLP_ENDPOINT",
  import.meta.env.OTEL_EXPORTER_OTLP_ENDPOINT,
);
const otelEnabled =
  readEnv("OTEL_ENABLED", import.meta.env.OTEL_ENABLED) === "true" &&
  Boolean(otlpEndpoint);

const buildLogger = async (): Promise<LoggerAdapter> => {
  const deploymentEnvironment = readEnv(
    "ENVIRONMENT",
    import.meta.env.ENVIRONMENT,
  );

  // Wires the OTLP exporters and patches pino for trace correlation; must run
  // before the first createLogger call.
  await configureOtel({
    serviceName: SERVICE_NAME,
    deploymentEnvironment,
    otlpEndpoint,
  });

  const logger = createLogger({
    serviceName: SERVICE_NAME,
    deploymentEnvironment,
    otlpEndpoint,
    shipLogs: 0,
  });

  return {
    middleware: async ({ locals, request }, next) => {
      const start = performance.now();
      const { method } = request;
      const { pathname } = new URL(request.url);

      const response = await next();

      logger.info(
        {
          contextId: locals.contextId,
          method,
          path: pathname,
          status: response.status,
          durationMs: Math.round(performance.now() - start),
        },
        "request completed",
      );

      return response;
    },
  };
};

const logger: LoggerAdapter = otelEnabled
  ? await buildLogger()
  : disabledLogger;

export default logger;
