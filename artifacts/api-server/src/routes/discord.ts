import { Router } from "express";
import fs from "fs";
import path from "path";
import { DEFAULT_EMBEDS } from "./embeds.js";

const router = Router();

const DISCORD_API = "https://discord.com/api/v10";
const PRIMARY_GUILD_ID = "1496860022066385016";
const APPLICATION_ID = "1496871647204999208";   // Gian ( Custom ) — known app ID
const EMOJI_CACHE_FILE = path.join(process.cwd(), "data", "emojis.json");

function botHeaders() {
  const token = process.env.DISCORD_TOKEN;
  if (!token) throw new Error("DISCORD_TOKEN not set");
  return {
    Authorization: `Bot ${token}`,
    "Content-Type": "application/json",
  };
}

// ── In-memory TTL cache for expensive Discord API calls ──────────────────────
interface CacheEntry { data: unknown; expiresAt: number; }
const _cache = new Map<string, CacheEntry>();
function cacheGet(key: string): unknown | null {
  const e = _cache.get(key);
  if (!e) return null;
  if (Date.now() > e.expiresAt) { _cache.delete(key); return null; }
  return e.data;
}
function cacheSet(key: string, data: unknown, ttlMs: number) {
  _cache.set(key, { data, expiresAt: Date.now() + ttlMs });
}

const EMOJI_CACHE_TTL_MS = 60 * 60 * 1000; // 1 sat

function loadEmojiCache() {
  try {
    if (fs.existsSync(EMOJI_CACHE_FILE)) {
      const stat = fs.statSync(EMOJI_CACHE_FILE);
      if (Date.now() - stat.mtimeMs > EMOJI_CACHE_TTL_MS) return null; // isteklo
      const raw = fs.readFileSync(EMOJI_CACHE_FILE, "utf-8");
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch {}
  return null;
}

function saveEmojiCache(emojis: unknown[]) {
  try {
    const dir = path.dirname(EMOJI_CACHE_FILE);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(EMOJI_CACHE_FILE, JSON.stringify(emojis, null, 2), "utf-8");
  } catch {}
}

router.get("/discord/debug", async (req, res) => {
  const token = process.env.DISCORD_TOKEN ?? "";
  const result: Record<string, unknown> = {
    hasToken: !!token,
    tokenLength: token.length,
    tokenPreview: token.length > 10 ? `${token.slice(0, 8)}...${token.slice(-4)}` : "(prazno)",
  };

  if (token) {
    // Test /applications/@me
    try {
      const r = await fetch(`${DISCORD_API}/applications/@me`, { headers: botHeaders() });
      if (r.ok) {
        const app = (await r.json()) as { id: string; name: string };
        result.appId = app.id;
        result.appName = app.name;

        // Test application emojis
        const er = await fetch(`${DISCORD_API}/applications/${app.id}/emojis?limit=200`, { headers: botHeaders() });
        const ebody = await er.text();
        result.appEmojisStatus = er.status;
        try {
          const parsed = JSON.parse(ebody);
          result.appEmojisCount = Array.isArray(parsed.items) ? parsed.items.length : parsed;
        } catch {
          result.appEmojisRaw = ebody.slice(0, 300);
        }
      } else {
        const txt = await r.text();
        result.appError = `${r.status}: ${txt.slice(0, 200)}`;
      }
    } catch (e: any) {
      result.appException = e.message;
    }

    // Test guild emojis
    try {
      const r = await fetch(`${DISCORD_API}/guilds/${PRIMARY_GUILD_ID}/emojis`, { headers: botHeaders() });
      result.guildEmojisStatus = r.status;
      if (r.ok) {
        const emojis = (await r.json()) as unknown[];
        result.guildEmojisCount = emojis.length;
      }
    } catch (e: any) {
      result.guildException = e.message;
    }
  }

  res.json(result);
});

// Fetch emojis: application emojis (Dev Portal) + guild emojis, merged
router.get("/discord/emojis", async (req, res) => {
  const forceRefresh = req.query.refresh === "1";

  // Serve from cache unless forcing a refresh — but only if cache is "full" (app+guild)
  if (!forceRefresh) {
    const cached = loadEmojiCache();
    if (cached && cached.length > 0) {
      res.setHeader("X-From-Cache", "true");
      res.setHeader("X-Emoji-Count", String(cached.length));
      return res.json(cached);
    }
  }

  // Live fetch — inline for reliability (tested working in request-handler context)
  try {
    const headers = botHeaders();
    const seen = new Set<string>();
    const all: Array<{ id: string; name: string; animated: boolean; _source: string }> = [];

    function add(list: Array<{ id: string; name: string; animated?: boolean }>, src: string) {
      for (const e of list) {
        if (e.id && !seen.has(e.id)) {
          seen.add(e.id);
          all.push({ id: e.id, name: e.name, animated: !!e.animated, _source: src });
        }
      }
    }

    // 1. Application emojis — paginate with cursor (after=<last_id>) up to 2000 emojis
    try {
      let after: string | undefined;
      let page = 0;
      const MAX_PAGES = 15; // 15 × 200 = 3000 — well above Discord's 2000 limit

      while (page < MAX_PAGES) {
        const url = `${DISCORD_API}/applications/${APPLICATION_ID}/emojis?limit=200${after ? `&after=${after}` : ""}`;
        let fetched = false;
        for (let attempt = 0; attempt < 3 && !fetched; attempt++) {
          if (attempt > 0) await new Promise(r => setTimeout(r, 1500 * attempt));
          try {
            const r = await fetch(url, { headers });
            if (r.ok) {
              const body = (await r.json()) as { items?: Array<{ id: string; name: string; animated?: boolean }> };
              const items = Array.isArray(body.items) ? body.items : [];
              add(items, "app");
              fetched = true;
              if (items.length < 200) { page = MAX_PAGES; break; } // last page
              after = items[items.length - 1].id;
            } else if (r.status === 429) {
              const retry = r.headers.get("retry-after");
              req.log.warn({ attempt, retryAfter: retry }, "App emoji rate limited");
              await new Promise(r2 => setTimeout(r2, (Number(retry) || 5) * 1000));
            } else {
              req.log.warn({ attempt, status: r.status }, "App emoji fetch failed");
              if (r.status < 500) { page = MAX_PAGES; break; }
            }
          } catch (e: any) {
            req.log.warn({ attempt, err: (e as Error).message }, "App emoji fetch exception");
          }
        }
        page++;
      }
    } catch (e: any) {
      req.log.warn({ err: (e as Error).message }, "App emoji pagination error");
    }

    // 2. Guild emojis (185 custom guild emojis)
    try {
      const r = await fetch(`${DISCORD_API}/guilds/${PRIMARY_GUILD_ID}/emojis`, { headers });
      if (r.ok) {
        const list = (await r.json()) as Array<{ id: string; name: string; animated?: boolean }>;
        add(list, "guild");
      }
    } catch {}

    if (all.length > 0) {
      saveEmojiCache(all);
      req.log.info({ total: all.length, app: all.filter(e => e._source === "app").length, guild: all.filter(e => e._source === "guild").length }, "Emoji cache refreshed");
      res.setHeader("X-Emoji-Count", String(all.length));
      return res.json(all);
    }
  } catch (err: any) {
    req.log.warn({ err }, "Emoji live fetch failed");
  }

  // Final fallback: stale cache
  const cached = loadEmojiCache();
  if (cached) {
    res.setHeader("X-From-Cache", "true");
    return res.json(cached);
  }

  return res.status(503).json({ error: "Emoji nisu dostupni" });
});

// Guild info
router.get("/discord/guild", async (req, res) => {
  try {
    const response = await fetch(
      `${DISCORD_API}/guilds/${PRIMARY_GUILD_ID}?with_counts=true`,
      { headers: botHeaders() }
    );
    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    const guild = await response.json() as any;
    return res.json({
      id: guild.id,
      name: guild.name,
      icon: guild.icon
        ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`
        : null,
      memberCount: guild.approximate_member_count ?? null,
    });
  } catch (err: any) {
    req.log.error({ err }, "Failed to fetch guild");
    return res.status(500).json({ error: err.message });
  }
});

// Guild members list (paginated, up to 1000)
router.get("/discord/members", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const limit = Math.min(Number(req.query.limit) || 100, 1000);
  const after = (req.query.after as string) || "0";
  const cacheKey = `members:${guildId}:${limit}:${after}`;
  const cached = cacheGet(cacheKey);
  if (cached) return res.json(cached);
  try {
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/members?limit=${limit}&after=${after}`,
      { headers: botHeaders() }
    );
    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    const members = await response.json() as any[];
    const mapped = members.map((m: any) => ({
      id: m.user?.id,
      username: m.user?.username,
      displayName: m.nick ?? m.user?.global_name ?? m.user?.username,
      nick: m.nick ?? null,
      avatar: m.user?.avatar
        ? `https://cdn.discordapp.com/avatars/${m.user.id}/${m.user.avatar}.png?size=64`
        : `https://cdn.discordapp.com/embed/avatars/${(Number(m.user?.id ?? 0) >> 22) % 6}.png`,
      roles: m.roles ?? [],
      joinedAt: m.joined_at,
      bot: m.user?.bot ?? false,
      premiumSince: m.premium_since ?? null,
    }));
    cacheSet(cacheKey, mapped, 2 * 60 * 1000); // 2 min
    return res.json(mapped);
  } catch (err: any) {
    req.log.error({ err }, "Failed to fetch members");
    return res.status(500).json({ error: err.message });
  }
});

// Guild roles list
router.get("/discord/roles", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const cacheKey = `roles:${guildId}`;
  const cached = cacheGet(cacheKey);
  if (cached) return res.json(cached);
  try {
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/roles`,
      { headers: botHeaders() }
    );
    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    const roles = await response.json() as any[];
    const mapped = roles
      .sort((a: any, b: any) => b.position - a.position)
      .map((r: any) => ({
        id: r.id,
        name: r.name,
        color: r.color ? `#${r.color.toString(16).padStart(6, "0")}` : "#5865F2",
        position: r.position,
        managed: r.managed,
        permissions: r.permissions as string,
        hoist: r.hoist,
        mentionable: r.mentionable,
      }));
    cacheSet(cacheKey, mapped, 5 * 60 * 1000); // 5 min
    return res.json(mapped);
  } catch (err: any) {
    req.log.error({ err }, "Failed to fetch roles");
    return res.status(500).json({ error: err.message });
  }
});

// PATCH /api/discord/roles/:roleId — update role permissions / color / hoist / mentionable
router.patch("/discord/roles/:roleId", async (req, res) => {
  const { roleId } = req.params;
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const { permissions, color, hoist, mentionable } = req.body as {
    permissions?: string;
    color?: string;
    hoist?: boolean;
    mentionable?: boolean;
  };

  const patch: Record<string, unknown> = {};
  if (permissions !== undefined) patch.permissions = permissions;
  if (hoist !== undefined) patch.hoist = hoist;
  if (mentionable !== undefined) patch.mentionable = mentionable;
  if (color !== undefined) {
    patch.color = color === "transparent" || color === "none"
      ? 0
      : parseInt(color.replace("#", ""), 16);
  }

  try {
    const r = await fetch(`${DISCORD_API}/guilds/${guildId}/roles/${roleId}`, {
      method: "PATCH",
      headers: botHeaders(),
      body: JSON.stringify(patch),
    });
    if (!r.ok) {
      const err = await r.text();
      req.log.warn({ roleId, status: r.status, err }, "Role PATCH failed");
      return res.status(r.status).json({ error: err });
    }
    const updated = await r.json() as any;
    req.log.info({ roleId, permissions }, "Role updated");
    return res.json({
      id: updated.id,
      name: updated.name,
      color: updated.color ? `#${updated.color.toString(16).padStart(6, "0")}` : "#5865F2",
      permissions: updated.permissions as string,
      hoist: updated.hoist,
      mentionable: updated.mentionable,
    });
  } catch (err: any) {
    req.log.error({ err }, "Failed to patch role");
    return res.status(500).json({ error: err.message });
  }
});

// Edit member — nick + roles
router.patch("/discord/members/:userId", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const { userId } = req.params;
  const { nick, roles, reason } = req.body as {
    nick?: string | null;
    roles?: string[];
    reason?: string;
  };

  const body: Record<string, unknown> = {};
  if (nick !== undefined) body.nick = nick;
  if (roles !== undefined) body.roles = roles;

  try {
    const headers: Record<string, string> = {
      ...botHeaders(),
      ...(reason ? { "X-Audit-Log-Reason": encodeURIComponent(reason) } : {}),
    };
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/members/${userId}`,
      { method: "PATCH", headers, body: JSON.stringify(body) }
    );
    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    const updated = await response.json() as any;
    return res.json({
      id: updated.user?.id,
      nick: updated.nick ?? null,
      roles: updated.roles ?? [],
    });
  } catch (err: any) {
    req.log.error({ err }, "Failed to edit member");
    return res.status(500).json({ error: err.message });
  }
});

// Timeout / remove timeout
router.post("/discord/members/:userId/timeout", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const { userId } = req.params;
  const { minutes, reason } = req.body as { minutes?: number; reason?: string };

  let until: string | null = null;
  if (minutes && minutes > 0) {
    until = new Date(Date.now() + minutes * 60 * 1000).toISOString();
  }

  try {
    const headers: Record<string, string> = {
      ...botHeaders(),
      ...(reason ? { "X-Audit-Log-Reason": encodeURIComponent(reason) } : {}),
    };
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/members/${userId}`,
      {
        method: "PATCH",
        headers,
        body: JSON.stringify({ communication_disabled_until: until }),
      }
    );
    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    return res.json({ ok: true, until });
  } catch (err: any) {
    req.log.error({ err }, "Failed to timeout member");
    return res.status(500).json({ error: err.message });
  }
});

// Kick member
router.delete("/discord/members/:userId/kick", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const { userId } = req.params;
  const reason = (req.query.reason as string) || "";

  try {
    const headers: Record<string, string> = {
      ...botHeaders(),
      ...(reason ? { "X-Audit-Log-Reason": encodeURIComponent(reason) } : {}),
    };
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/members/${userId}`,
      { method: "DELETE", headers }
    );
    if (!response.ok && response.status !== 204) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    return res.json({ ok: true });
  } catch (err: any) {
    req.log.error({ err }, "Failed to kick member");
    return res.status(500).json({ error: err.message });
  }
});

// Ban member
router.post("/discord/members/:userId/ban", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const { userId } = req.params;
  const { reason, delete_message_seconds } = req.body as {
    reason?: string;
    delete_message_seconds?: number;
  };

  try {
    const headers: Record<string, string> = {
      ...botHeaders(),
      ...(reason ? { "X-Audit-Log-Reason": encodeURIComponent(reason) } : {}),
    };
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/bans/${userId}`,
      {
        method: "PUT",
        headers,
        body: JSON.stringify({ delete_message_seconds: delete_message_seconds ?? 0 }),
      }
    );
    if (!response.ok && response.status !== 204) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    return res.json({ ok: true });
  } catch (err: any) {
    req.log.error({ err }, "Failed to ban member");
    return res.status(500).json({ error: err.message });
  }
});

// Guild channels — grouped by category
router.get("/discord/channels", async (req, res) => {
  const guildId = (req.query.guild as string) || PRIMARY_GUILD_ID;
  const cacheKey = `channels:${guildId}`;
  const cached = cacheGet(cacheKey);
  if (cached) return res.json(cached);
  try {
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/channels`,
      { headers: botHeaders() }
    );
    if (!response.ok) {
      const err = await response.text();
      return res.status(response.status).json({ error: err });
    }
    const channels = await response.json() as any[];

    // Channel types: 0=text, 2=voice, 4=category, 5=announcement, 13=stage, 15=forum
    const categories = channels
      .filter((c: any) => c.type === 4)
      .sort((a: any, b: any) => a.position - b.position);

    const result = categories.map((cat: any) => ({
      id: cat.id,
      name: cat.name,
      position: cat.position,
      channels: channels
        .filter((c: any) => c.parent_id === cat.id)
        .sort((a: any, b: any) => a.position - b.position)
        .map((c: any) => ({
          id: c.id,
          name: c.name,
          type: c.type,
          position: c.position,
          topic: c.topic ?? null,
          nsfw: c.nsfw ?? false,
        })),
    }));

    // Uncategorized channels
    const uncategorized = channels
      .filter((c: any) => !c.parent_id && c.type !== 4)
      .sort((a: any, b: any) => a.position - b.position)
      .map((c: any) => ({
        id: c.id,
        name: c.name,
        type: c.type,
        position: c.position,
        topic: c.topic ?? null,
        nsfw: c.nsfw ?? false,
      }));

    const payload = { categories: result, uncategorized };
    cacheSet(cacheKey, payload, 5 * 60 * 1000); // 5 min
    return res.json(payload);
  } catch (err: any) {
    req.log.error({ err }, "Failed to fetch channels");
    return res.status(500).json({ error: err.message });
  }
});

// Discord button style int mapping
const DISCORD_BTN_STYLE: Record<string, number> = {
  primary: 1, secondary: 2, success: 3, danger: 4, link: 5,
};

const DEFAULT_BTN_LABELS = ["Pravila", "Role", "Pozovi", "Chat"];

function buildComponents(buttons: any[], guildId = PRIMARY_GUILD_ID): unknown[] {
  if (!buttons || buttons.length === 0) return [];
  const comps = buttons.map((btn: any, idx: number) => {
    const style = btn.type === "link" ? 5 : (DISCORD_BTN_STYLE[btn.style] ?? 1);
    const label = btn.label || DEFAULT_BTN_LABELS[idx] || "Dugme";
    const comp: Record<string, unknown> = { type: 2, style, label };

    // Emoji parsing — supports unicode or <:name:id> / <a:name:id>
    if (btn.emoji) {
      const m = btn.emoji.match(/^<(a?):([^:]+):(\d+)>$/);
      if (m) {
        comp.emoji = { id: m[3], name: m[2], animated: m[1] === "a" };
      } else {
        comp.emoji = { name: btn.emoji };
      }
    }

    // Link button needs url — build from channelId if url not set
    if (btn.type === "link") {
      if (btn.channelId) {
        comp.url = `https://discord.com/channels/${guildId}/${btn.channelId}`;
      } else {
        comp.url = btn.url || "https://discord.gg";
      }
    } else {
      // Determine custom_id from type
      switch (btn.type) {
        case "voice_create":  comp.custom_id = "vc_create_btn"; break;
        case "ticket_open":   comp.custom_id = "ticket_open";   break;
        case "ticket_close":  comp.custom_id = "ticket_close";  break;
        case "role":          comp.custom_id = `panel_role_${btn.roleId}`; break;
        default:              comp.custom_id = btn.customId || `btn_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`; break;
      }
    }
    return comp;
  });

  // Discord requires buttons wrapped in an Action Row (type 1), max 5 per row
  return [{ type: 1, components: comps.slice(0, 5) }];
}

// POST /api/discord/channels/:channelId/send-embed
router.post("/discord/channels/:channelId/send-embed", async (req, res) => {
  const { channelId } = req.params;
  const { embedName } = req.body as { embedName?: string };
  if (!embedName) return res.status(400).json({ error: "embedName required" });

  let embedData: any;
  try {
    const mod = await import("@workspace/db");
    const { eq } = await import("drizzle-orm");
    const rows = await mod.db.select().from(mod.embedsTable).where(eq(mod.embedsTable.name, embedName));
    embedData = rows.length > 0 ? rows[0].data : DEFAULT_EMBEDS.find(e => e.name === embedName);
  } catch {
    embedData = DEFAULT_EMBEDS.find(e => e.name === embedName);
  }

  if (!embedData) return res.status(404).json({ error: "Embed not found" });

  // Demo variable substitution for panel test sends
  const now = new Date();
  const demoVars: Record<string, string> = {
    "{user}":        "@TestUser",
    "{user.name}":   "TestUser",
    "{user.avatar}": "https://cdn.discordapp.com/embed/avatars/0.png",
    "{server}":      "GIANNI",
    "{accountAge}":  "2g 3m",
    "{joinedAt}":    now.toLocaleString("sr-Latn", { month: "short", year: "numeric" }),
    "{count}":       "1.234",
    "{memberCount}": "1.234",
    "{item1}":       "**Pravila**",
    "{item2}":       "**Role**",
    "{item3}":       "**Predstavi se**",
  };
  const applyVars = (s: string): string =>
    Object.entries(demoVars).reduce((acc, [k, v]) => acc.replaceAll(k, v), s);

  const colorHex = (embedData.color ?? "#2B2D3A").replace("#", "");
  const colorInt = parseInt(colorHex, 16) || 0x2B2D3A;

  const discordEmbed: Record<string, unknown> = { color: colorInt };
  if (embedData.title)       discordEmbed.title = applyVars(embedData.title);
  if (embedData.description) discordEmbed.description = applyVars(embedData.description);
  if (embedData.thumbnail)   discordEmbed.thumbnail = { url: applyVars(embedData.thumbnail) };
  if (embedData.footer)      discordEmbed.footer = { text: applyVars(embedData.footer) };
  if (embedData.fields?.length)
    discordEmbed.fields = embedData.fields.map((f: any) => ({
      ...f,
      name:  applyVars(String(f.name  ?? "")),
      value: applyVars(String(f.value ?? "")),
    }));

  const components = buildComponents(embedData.buttons ?? []);

  try {
    // Always send native Discord embed (with variables substituted)
    const body: Record<string, unknown> = { embeds: [discordEmbed] };
    if (components.length > 0) body.components = components;
    const r = await fetch(`${DISCORD_API}/channels/${channelId}/messages`, {
      method: "POST",
      headers: botHeaders(),
      body: JSON.stringify(body),
    });

    if (!r.ok) {
      const err = await r.text();
      req.log.warn({ channelId, embedName, status: r.status, err }, "Discord send failed");
      return res.status(r.status).json({ error: err });
    }
    const msg = await r.json() as { id: string };
    req.log.info({ channelId, embedName, messageId: msg.id, buttons: (embedData.buttons ?? []).length }, "Embed sent to channel");
    return res.json({ ok: true, messageId: msg.id });
  } catch (err: any) {
    req.log.error({ err }, "Failed to send embed to Discord");
    return res.status(500).json({ error: err.message });
  }
});

function clearEmojiCache() {
  try {
    if (fs.existsSync(EMOJI_CACHE_FILE)) fs.unlinkSync(EMOJI_CACHE_FILE);
  } catch {}
}

// ── Upload application emoji ─────────────────────────────────────────────────
router.post("/discord/emojis/upload", async (req, res) => {
  // frontend may send "image" or "imageBase64"
  const body = req.body as { name?: string; image?: string; imageBase64?: string };
  const { name } = body;
  const imageData = body.image ?? body.imageBase64;
  if (!name || !imageData) return res.status(400).json({ error: "name and image required" });

  try {
    const r = await fetch(`${DISCORD_API}/applications/${APPLICATION_ID}/emojis`, {
      method: "POST",
      headers: botHeaders(),
      body: JSON.stringify({ name, image: imageData }),
    });
    const data = await r.json() as Record<string, unknown>;
    if (!r.ok) return res.status(r.status).json({ error: data });
    req.log.info({ name, id: data.id }, "Uploaded app emoji");
    clearEmojiCache();
    return res.json({ id: data.id, name: data.name, animated: data.animated });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
});

// ── Delete application emoji ──────────────────────────────────────────────────
router.delete("/discord/emojis/:emojiId", async (req, res) => {
  const { emojiId } = req.params;
  try {
    const r = await fetch(`${DISCORD_API}/applications/${APPLICATION_ID}/emojis/${emojiId}`, {
      method: "DELETE",
      headers: botHeaders(),
    });
    if (!r.ok) return res.status(r.status).json({ error: "Delete failed" });
    clearEmojiCache();
    return res.json({ ok: true });
  } catch (err: any) {
    return res.status(500).json({ error: err.message });
  }
});

export default router;
