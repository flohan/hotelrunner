import pino from "pino";
import pinoHttp from "pino-http";

const redactPaths = [
  "req.headers.authorization",
  "req.headers.cookie",
  "res.headers['set-cookie']",
  "req.body.password",
  "req.body.token",
  "req.body.secret",
];

export const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  redact: { paths: redactPaths, remove: true },
  base: { service: "retell-agent-optimized" },
  timestamp: pino.stdTimeFunctions.isoTime,
});

export const httpLogger = pinoHttp({
  logger,
  redact: { paths: redactPaths, remove: true },
});
