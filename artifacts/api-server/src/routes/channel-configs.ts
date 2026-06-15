import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();
const CONFIGS_FILE = path.join(process.cwd(), "data", "channel-configs.json");

interface ChannelConfig {
  embedNames: string[];
  note?: string;
}

function loadConfigs(): Record<string, ChannelConfig> {
  try {
    if (fs.existsSync(CONFIGS_FILE)) {
      return JSON.parse(fs.readFileSync(CONFIGS_FILE, "utf-8"));
    }
  } catch {}
  return {};
}

function saveConfigs(data: Record<string, ChannelConfig>): void {
  const dir = path.dirname(CONFIGS_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(CONFIGS_FILE, JSON.stringify(data, null, 2), "utf-8");
}

// GET all channel configs
router.get("/channel-configs", (req, res) => {
  res.set("Cache-Control", "no-store").json(loadConfigs());
});

// PUT config for a channel
router.put("/channel-configs/:channelId", (req, res) => {
  const { channelId } = req.params;
  const { embedNames, note } = req.body as { embedNames?: string[]; note?: string };
  const configs = loadConfigs();
  if (!embedNames || embedNames.length === 0) {
    delete configs[channelId];
  } else {
    configs[channelId] = { embedNames: embedNames ?? [], note: note ?? "" };
  }
  saveConfigs(configs);
  res.json(configs[channelId] ?? { embedNames: [] });
});

export default router;
