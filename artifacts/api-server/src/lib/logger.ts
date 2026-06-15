import pino from "pino";

// Only use pino-pretty when explicitly opted-in (LOG_PRETTY=true).
// In production (Railway) we never use worker-thread transports to avoid
// bundled-path resolution failures.
const usePretty = process.env.LOG_PRETTY === "true";

export const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  redact: [
    "req.headers.authorization",
    "req.headers.cookie",
    "res.headers['set-cookie']",
  ],
  ...(usePretty
    ? {
        transport: {
          target: "pino-pretty",
          options: { colorize: true },
        },
      }
    : {}),
});
