import { Router } from "express";
import fs from "fs";
import path from "path";
import { ALL_COMMANDS } from "./commands.js";
import { DEFAULT_EMBEDS } from "./embeds.js";

const router = Router();

const SETTINGS_FILE = path.join(process.cwd(), "data", "settings.json");

const DEFAULT_SETTINGS = {
  botName: "GIANNI (Custom)",
  version: "v2.0",
  prefix: ".",
  officialGuildId: "1496860022066385016",
  officialInvite: "gian",
  colors: {
    default: "#2B2D42",
    success: "#43B581",
    error: "#E74C3C",
    warning: "#F39C12",
    info: "#2B2D42",
    gold: "#F1C40F",
    balkan: "#2B2D42",
    purple: "#9B59B6",
    fun: "#2B2D42",
    dark: "#2B2D42",
    teal: "#1ABC9C",
    love: "#FF4D6D",
    pink: "#E91E8C",
    aqua: "#00D4FF",
  },
  updatedAt: null as string | null,
};

function loadSettings(): typeof DEFAULT_SETTINGS {
  try {
    if (fs.existsSync(SETTINGS_FILE)) {
      const raw = fs.readFileSync(SETTINGS_FILE, "utf-8");
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
    }
  } catch {}
  return { ...DEFAULT_SETTINGS };
}

function saveSettings(s: typeof DEFAULT_SETTINGS): void {
  const dir = path.dirname(SETTINGS_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(SETTINGS_FILE, JSON.stringify(s, null, 2), "utf-8");
}

router.get("/settings", (req, res) => {
  res.json(loadSettings());
});

router.put("/settings", (req, res) => {
  const current = loadSettings();
  const updated = {
    ...current,
    ...req.body,
    colors: req.body.colors ? { ...current.colors, ...req.body.colors } : current.colors,
    version: current.version,
    officialGuildId: current.officialGuildId,
    updatedAt: new Date().toISOString(),
  };
  saveSettings(updated);
  res.json(updated);
});

// POST /settings/token — update DISCORD_TOKEN at runtime and persist it
router.post("/settings/token", async (req, res) => {
  const { token } = req.body as { token?: string };
  if (!token || typeof token !== "string" || token.trim().length < 30) {
    res.status(400).json({ error: "Invalid token" });
    return;
  }
  const trimmed = token.trim();
  // Validate token against Discord
  try {
    const r = await fetch("https://discord.com/api/v10/users/@me", {
      headers: { Authorization: `Bot ${trimmed}` },
    });
    if (!r.ok) {
      res.status(400).json({ error: "Token rejected by Discord", status: r.status });
      return;
    }
  } catch (e: any) {
    res.status(502).json({ error: "Could not reach Discord API", detail: e.message });
    return;
  }
  // Update env at runtime
  process.env.DISCORD_TOKEN = trimmed;
  // Persist to settings.json
  const current = loadSettings();
  (current as Record<string, unknown>).discordToken = trimmed;
  saveSettings(current);
  req.log.info("Discord token updated at runtime");
  res.json({ ok: true, message: "Token saved and active" });
});

router.get("/stats", (req, res) => {
  const commandsByCategory: Record<string, number> = {};
  let total = 0;
  for (const cat of ALL_COMMANDS) {
    commandsByCategory[cat.category] = cat.commands.length;
    total += cat.commands.length;
  }

  res.json({
    totalCommands: total,
    totalEmbeds: DEFAULT_EMBEDS.length,
    categories: ALL_COMMANDS.length,
    commandsByCategory,
  });
});

export default router;
