import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();
const DATA_FILE = path.join(process.cwd(), "data", "games.json");

const DEFAULTS = {
  economy: {
    posao:  { enabled: true, cooldown_min: 30,  reward_min: 150, reward_max: 600 },
    daily:  { enabled: true, cooldown_hours: 24, reward_min: 300, reward_max: 800 },
    kradi:  { enabled: true, cooldown_hours: 2,  success_rate: 38, steal_min: 50, steal_max: 300 },
  },
  gambling: {
    slots:       { enabled: true, cooldown_sec: 15, max_bet: 1000000000, symbols: ["🍒","🍋","🍇","💎","🔔","⭐","🎰","🍀","👑"] },
    blackjack:   { enabled: true, cooldown_sec: 30 },
    poker:       { enabled: true, min_bet: 50,  max_bet: 50000 },
    kviz:        { enabled: true, min_bet: 10 },
    geografija:  { enabled: true, min_bet: 10 },
    kpm:         { enabled: true },
    vjasala:     { enabled: true },
    kaladont:    { enabled: true, reward: 1500 },
    toplo_hladno:{ enabled: true },
    amogus:      { enabled: true },
  },
  animals: {
    hunt: { enabled: true, cooldown_sec: 7 },
  },
  social: {
    enabled: true,
  },
  updatedAt: null as string | null,
};

function load() {
  try {
    if (fs.existsSync(DATA_FILE)) {
      return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(DATA_FILE, "utf8")) };
    }
  } catch {}
  return { ...DEFAULTS };
}

function save(cfg: typeof DEFAULTS) {
  fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
  fs.writeFileSync(DATA_FILE, JSON.stringify(cfg, null, 2));
}

router.get("/games", (_req, res) => {
  res.json(load());
});

router.put("/games", (req, res) => {
  const current = load();
  const updated = {
    ...current,
    ...req.body,
    updatedAt: new Date().toISOString(),
  };
  save(updated);
  res.json(updated);
});

export default router;
