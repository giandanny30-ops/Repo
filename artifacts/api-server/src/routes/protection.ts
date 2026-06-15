import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();

const PROTECTION_FILE = path.join(process.cwd(), "data", "protection.json");

const DEFAULT_PROTECTION = {
  antiRaid: {
    enabled: true,
    windowSeconds: 30,
    joinLimit: 5,
    suspiciousAgeDays: 7,
    lockdownMinutes: 5,
    action: "kick" as "kick" | "ban" | "alert_only",
  },
  antiNsfw: {
    enabled: true,
    strikesBeforeTimeout: 3,
    timeoutMinutes: 60,
    extraBlockedSites: [] as string[],
    extraBlockedKeywords: [] as string[],
  },
  updatedAt: null as string | null,
};

function load(): typeof DEFAULT_PROTECTION {
  try {
    if (fs.existsSync(PROTECTION_FILE)) {
      const raw = fs.readFileSync(PROTECTION_FILE, "utf-8");
      const parsed = JSON.parse(raw);
      return {
        ...DEFAULT_PROTECTION,
        ...parsed,
        antiRaid: { ...DEFAULT_PROTECTION.antiRaid, ...parsed.antiRaid },
        antiNsfw: { ...DEFAULT_PROTECTION.antiNsfw, ...parsed.antiNsfw },
      };
    }
  } catch {}
  return { ...DEFAULT_PROTECTION };
}

function save(cfg: typeof DEFAULT_PROTECTION): void {
  const dir = path.dirname(PROTECTION_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(PROTECTION_FILE, JSON.stringify(cfg, null, 2), "utf-8");
}

router.get("/protection", (_req, res) => {
  res.json(load());
});

router.put("/protection", (req, res) => {
  const current = load();
  const body = req.body as Partial<typeof DEFAULT_PROTECTION>;
  const updated = {
    ...current,
    ...body,
    antiRaid: body.antiRaid ? { ...current.antiRaid, ...body.antiRaid } : current.antiRaid,
    antiNsfw: body.antiNsfw ? { ...current.antiNsfw, ...body.antiNsfw } : current.antiNsfw,
    updatedAt: new Date().toISOString(),
  };
  save(updated);
  req.log.info(
    { antiRaidEnabled: updated.antiRaid.enabled, antiNsfwEnabled: updated.antiNsfw.enabled },
    "Protection config updated",
  );
  res.json(updated);
});

export default router;
