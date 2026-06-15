import { Router } from "express";
import { makeToken } from "../middleware/auth.js";

const router = Router();

// POST /api/auth/login  — { password } → { token }
router.post("/auth/login", (req, res) => {
  const secret = process.env.PANEL_SECRET;
  if (!secret) {
    // Dev mode — no password set
    return res.json({ token: "dev-mode", devMode: true });
  }
  const { password } = req.body as { password?: string };
  if (!password || password !== secret) {
    req.log.warn({ ip: req.ip }, "Failed panel login attempt");
    return res.status(401).json({ error: "Pogrešna lozinka panela." });
  }
  const token = makeToken(secret);
  req.log.info({ ip: req.ip }, "Panel login success");
  return res.json({ token, devMode: false });
});

// GET /api/auth/verify  — validates current Bearer token
router.get("/auth/verify", (req, res) => {
  const secret = process.env.PANEL_SECRET;
  if (!secret) return res.json({ ok: true, devMode: true });
  const auth = req.headers.authorization ?? "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token || token !== makeToken(secret)) {
    return res.status(401).json({ ok: false });
  }
  return res.json({ ok: true, devMode: false });
});

export default router;
