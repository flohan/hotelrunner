export function requireToolSecret(req, res, next) {
  const secret = process.env.TOOL_SECRET || "";
  const header = req.headers["x-tool-secret"];
  if (!secret || header !== secret) {
    return res.status(401).json({ error: "Unauthorized" });
  }
  next();
}
