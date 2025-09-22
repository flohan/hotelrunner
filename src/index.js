import express from "express";
import { config } from "./config.js";
import { httpLogger, logger } from "./logger.js";
import { publicRouter } from "./routes/public.js";
import { toolRouter } from "./routes/tool.js";
import { notFound, errorHandler } from "./middleware/errorHandler.js";
import swaggerUi from "swagger-ui-express";
import { swaggerDefinition } from "./openapi/definition.js";

const app = express();

app.use(express.json({ limit: "200kb", strict: true }));
app.use(httpLogger);

app.get("/healthz", (_req, res) => res.json({ ok: true }));

app.get("/openapi.json", (_req, res) => res.json(swaggerDefinition));
app.use("/docs", swaggerUi.serve, swaggerUi.setup(swaggerDefinition));

app.get("/__routes", (_req, res) => {
  const stack = app._router?.stack ?? [];
  const routes = [];
  stack.forEach((s) => {
    if (s.route && s.route.path) {
      const methods = Object.keys(s.route.methods).filter(Boolean);
      routes.push({ path: s.route.path, methods });
    } else if (s.name === "router" && s.handle && s.handle.stack) {
      s.handle.stack.forEach((r) => {
        if (r.route && r.route.path) {
          const methods = Object.keys(r.route.methods).filter(Boolean);
          routes.push({ path: r.route.path, methods });
        }
      });
    }
  });
  res.json(routes);
});

app.use(publicRouter);
app.use(toolRouter);

app.use(notFound);
app.use(errorHandler);

app.listen(config.port, () => {
  logger.info({ port: config.port }, "Server running");
});
