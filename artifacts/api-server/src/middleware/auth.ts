import { Request, Response, NextFunction } from "express";
import { createHash } from "crypto";

export function makeToken(secret: string): string {
  return createHash("sha256").update(secret + ":gianni-panel-v2").digest("hex");
}

export function authMiddleware(req: Request, res: Response, next: NextFunction): void {
  const secret = process.env.PANEL_SECRET;
  // No PANEL_SECRET set → dev mode, allow everything (warn once)
  if (!secret) { next(); return; }
  // Auth endpoints are public (login/verify)
  if (req.path.startsWith("/auth/")) { next(); return; }
  // Health check is public
  if (req.path === "/healthz" || req.path === "/health") { next(); return; }

  const auth = req.headers.authorization ?? "";
  const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
  if (!token || token !== makeToken(secret)) {
    res.status(401).json({ error: "Neautorizovano — prijava obavezna." });
    return;
  }
  next();
}
