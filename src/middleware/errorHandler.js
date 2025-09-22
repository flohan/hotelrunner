import { logger } from "../logger.js";

export function notFound(_req, res, _next) {
  res.status(404).json({ error: "Not Found" });
}

export function errorHandler(err, _req, res, _next) {
  const status = err.status || err.statusCode || 500;
  if (status >= 500) {
    logger.error({ err }, "Unhandled error");
  } else {
    logger.warn({ err }, "Handled error");
  }
  res.status(status).json({ error: err.message || "Internal Server Error" });
}
