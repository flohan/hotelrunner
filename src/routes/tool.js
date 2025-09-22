import { Router } from "express";
import { requireToolSecret } from "../middleware/auth.js";

export const toolRouter = Router();
toolRouter.use(requireToolSecret);

toolRouter.get("/retell/tool/ping", (_req, res) => {
  res.json({ ok: true, t: Date.now() });
});
