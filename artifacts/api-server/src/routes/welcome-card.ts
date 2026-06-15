import { Router } from "express";
import { icons } from "lucide";

const router = Router();

type IconNodes = [string, Record<string, string>][];

function esc(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function licon(name: string, x: number, y: number, sz: number, col: string): string {
  const nodes = (icons as Record<string, IconNodes>)[name];
  if (!nodes) return "";
  const sc = sz / 24;
  const sw = (1.8 / sc).toFixed(3);
  const paths = nodes
    .map(([tag, attrs]) => `<${tag} ${Object.entries(attrs).map(([k, v]) => `${k}="${v}"`).join(" ")}/>`)
    .join("");
  return `<g transform="translate(${x},${y}) scale(${sc})" fill="none" stroke="${col}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${paths}</g>`;
}

function starField(n: number, w: number, h: number): string {
  let s = 0xdeadbeef;
  const rng = () => {
    s = Math.imul(s ^ (s >>> 16), 0x45d9f3b);
    s ^= s >>> 16;
    return (s >>> 0) / 0xffffffff;
  };
  return Array.from({ length: n }, () => {
    const x = rng() * w, y = rng() * h;
    const r = rng() * 1.4 + 0.4;
    const o = (rng() * 0.5 + 0.3).toFixed(2);
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${r.toFixed(1)}" fill="white" opacity="${o}"/>`;
  }).join("");
}

function star4(x: number, y: number, sz: number, col = "#ec4899", op = "1"): string {
  const h = sz, q = sz * 0.28;
  return `<path d="M${x},${y - h} L${x + q},${y - q} L${x + h},${y} L${x + q},${y + q} L${x},${y + h} L${x - q},${y + q} L${x - h},${y} L${x - q},${y - q} Z" fill="${col}" opacity="${op}"/>`;
}

async function fetchAsBase64(url: string): Promise<string | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) return null;
    const buf = await res.arrayBuffer();
    const ct = res.headers.get("content-type") ?? "image/png";
    return `data:${ct};base64,${Buffer.from(buf).toString("base64")}`;
  } catch {
    return null;
  }
}

function listItem(x: number, y: number, iconName: string, text: string): string {
  const bx = x, by = y - 17, bw = 23, bh = 23;
  return `
  <rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="5" fill="#1e0530" stroke="#ec4899" stroke-width="1" opacity="0.85"/>
  ${licon(iconName, bx + 2.5, by + 2.5, 18, "#ec4899")}
  <text x="${bx + bw + 9}" y="${y}" font-family="Arial,sans-serif" font-size="13.5" fill="#d4b8cc">${esc(text)}</text>`;
}

function statBlock(x: number, y: number, iconName: string, label: string, value: string): string {
  return `
  ${licon(iconName, x, y - 13, 14, "#8855a0")}
  <text x="${x + 18}" y="${y}" font-family="Arial,sans-serif" font-size="11" fill="#8855a0">${esc(label)}</text>
  <text x="${x}" y="${y + 17}" font-family="Arial,sans-serif" font-weight="bold" font-size="14" fill="white">${esc(value)}</text>`;
}

function infoRow(x: number, y: number, iconName: string, label: string, value: string): string {
  return `
  ${licon(iconName, x, y - 12, 13, "#8855a0")}
  <text x="${x + 18}" y="${y}" font-family="Arial,sans-serif" font-size="11.5" fill="#8855a0">${esc(label)}</text>
  <text x="${x + 80}" y="${y}" font-family="Arial,sans-serif" font-size="12.5" fill="white">${esc(value)}</text>`;
}

function btn(x: number, y: number, w: number, h: number, iconName: string, label: string, filled: boolean): string {
  const bg = filled
    ? `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" fill="#c2185b"/>`
    : `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="9" fill="#1a0528" stroke="#ec4899" stroke-width="1.5" opacity="0.9"/>`;
  const cx = x + (iconName ? 18 : 0);
  const tx = x + w / 2 + (iconName ? 8 : 0);
  return `${bg}
  ${iconName ? licon(iconName, cx - 14, y + (h - 16) / 2, 16, "white") : ""}
  <text x="${tx}" y="${y + h / 2 + 5}" text-anchor="middle" font-family="Arial,sans-serif" font-weight="bold" font-size="13" fill="white">${esc(label)}</text>`;
}

router.get("/api/welcome-card", async (req, res) => {
  const user        = ((req.query.user        as string) ?? "User").slice(0, 20);
  const avatarUrl   =  (req.query.avatarUrl   as string) ?? "";
  const memberCount =  (req.query.memberCount as string) ?? "?";
  const accountAge  =  (req.query.accountAge  as string) ?? "?";
  const joinedAt    =  (req.query.joinedAt    as string) ?? "?";
  const count       =  (req.query.count       as string) ?? "?";
  const cardDesc    =  (req.query.desc        as string) ?? "Drago nam je sto si stigao/la u nasu zajednicu!";
  const cardItem1   =  (req.query.item1       as string) ?? "Procitaj pravila";
  const cardItem2   =  (req.query.item2       as string) ?? "Odaberi role";
  const cardItem3   =  (req.query.item3       as string) ?? "Predstavi se zajednici";
  const cardClosing =  (req.query.closing     as string) ?? "Uzivaj i zabavi se!";
  const cardBtn1    =  (req.query.btn1        as string) ?? "Pravila";
  const cardBtn2    =  (req.query.btn2        as string) ?? "Role";
  const cardBtn3    =  (req.query.btn3        as string) ?? "Pozovi";
  const cardBtn4    =  (req.query.btn4        as string) ?? "Chat";

  const avatarB64 = avatarUrl ? await fetchAsBase64(avatarUrl) : null;

  const W = 900, H = 500;
  const AX = 158, AY = 210, AR = 100;

  const uLen = user.length;
  const uSize = uLen > 17 ? 24 : uLen > 13 ? 29 : 34;

  const svg = `<svg width="${W}" height="${H}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<defs>
  <radialGradient id="bg" cx="35%" cy="45%" r="75%">
    <stop offset="0%"   stop-color="#200930"/>
    <stop offset="100%" stop-color="#0b0413"/>
  </radialGradient>
  <radialGradient id="avatarGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%"   stop-color="#ec4899" stop-opacity="0.4"/>
    <stop offset="100%" stop-color="#ec4899" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="av"><circle cx="${AX}" cy="${AY}" r="${AR}"/></clipPath>
  <filter id="glowF" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="5" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <linearGradient id="panelBg" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%"   stop-color="#1e0830"/>
    <stop offset="100%" stop-color="#130520"/>
  </linearGradient>
</defs>

<!-- Background -->
<rect width="${W}" height="${H}" fill="url(#bg)" rx="18"/>

<!-- Stars -->
${starField(70, W, H)}

<!-- Accent sparkles -->
${star4(340, 78, 6)}
${star4(382, 60, 3.5, "white", "0.8")}
${star4(720, 38, 5)}
${star4(764, 68, 3, "white", "0.7")}
${star4(834, 44, 5.5)}
${star4(858, 178, 3.5, "white", "0.7")}
${star4(877, 355, 4.5, "white", "0.6")}
${star4(60, 80, 4, "white", "0.6")}
${star4(506, 28, 4.5, "white", "0.7")}
${star4(40, 300, 3.5, "white", "0.6")}
${star4(302, 462, 4, "white", "0.5")}
${star4(636, 460, 3.5, "white", "0.5")}

<!-- Small pink heart top-left -->
${licon("Heart", 34, 42, 17, "#ec4899")}

<!-- Moon crescent bottom-left -->
<circle cx="62" cy="420" r="88" fill="#b5436e" opacity="0.5"/>
<circle cx="42" cy="398" r="73" fill="#0b0413" opacity="1"/>

<!-- Clouds -->
<ellipse cx="112" cy="492" rx="88" ry="22" fill="#250838" opacity="0.6"/>
<ellipse cx="52"  cy="484" rx="62" ry="17" fill="#250838" opacity="0.5"/>
<ellipse cx="172" cy="496" rx="62" ry="16" fill="#200730" opacity="0.45"/>

<!-- Left vine decoration -->
<path d="M12,120 Q28,145 18,175 Q8,205 25,225" stroke="#ec4899" stroke-width="1.5" fill="none" opacity="0.25"/>
<path d="M18,175 Q35,168 42,155" stroke="#ec4899" stroke-width="1" fill="none" opacity="0.2"/>
<path d="M22,200 Q40,192 46,180" stroke="#ec4899" stroke-width="1" fill="none" opacity="0.2"/>
<circle cx="43" cy="154" r="3" fill="#ec4899" opacity="0.22"/>
<circle cx="47" cy="179" r="2.5" fill="#ec4899" opacity="0.2"/>

<!-- Avatar glow halo -->
<circle cx="${AX}" cy="${AY}" r="${AR + 28}" fill="url(#avatarGlow)"/>

<!-- Avatar outer glow ring -->
<circle cx="${AX}" cy="${AY}" r="${AR + 13}" fill="none" stroke="#ec4899" stroke-width="2.5" opacity="0.95" filter="url(#glowF)"/>
<!-- Avatar inner subtle ring -->
<circle cx="${AX}" cy="${AY}" r="${AR + 7}"  fill="none" stroke="#ec4899" stroke-width="1" opacity="0.38"/>

<!-- Avatar background fill -->
<circle cx="${AX}" cy="${AY}" r="${AR}" fill="#280840"/>

<!-- Avatar image or placeholder -->
${avatarB64
  ? `<image href="${avatarB64}" x="${AX - AR}" y="${AY - AR}" width="${AR * 2}" height="${AR * 2}" clip-path="url(#av)"/>`
  : `<circle cx="${AX}" cy="${AY}" r="${AR}" fill="#340a50"/>
     <text x="${AX}" y="${AY + 22}" text-anchor="middle" font-family="Arial,sans-serif" font-size="68" fill="#ec4899" font-weight="bold">?</text>`}

<!-- Online green dot -->
<circle cx="${AX + AR - 13}" cy="${AY + AR - 13}" r="12" fill="#0b0413"/>
<circle cx="${AX + AR - 13}" cy="${AY + AR - 13}" r="8.5" fill="#3ba55c"/>

<!-- ─── MIDDLE CONTENT ─── -->

<!-- "hey!" italic -->
<text x="315" y="93" font-family="Georgia,'Times New Roman',serif" font-style="italic" font-size="22" fill="#ec4899" opacity="0.95">hey!</text>
${star4(358, 85, 5)}
${star4(375, 72, 3.5, "white", "0.75")}

<!-- Title row 1 -->
<text x="315" y="143" font-family="Arial,sans-serif" font-weight="bold" font-size="34" fill="white">Dobrodosao/la,</text>

<!-- Title row 2: @user + heart -->
<text x="315" y="${143 + 45}" font-family="Arial,sans-serif" font-weight="bold" font-size="${uSize}" fill="#ec4899">@${esc(user)}</text>
${licon("Heart", 315 + Math.min(uLen, 18) * uSize * 0.56 + 6, 143 + 45 - uSize * 0.8, uSize * 0.7, "#ec4899")}

<!-- Decorative divider: left line, sparkle, member count, sparkle, right line -->
<line x1="315" y1="207" x2="440" y2="207" stroke="#ec4899" stroke-width="0.8" opacity="0.38"/>
${star4(447, 207, 4.5)}
<text x="504" y="211" text-anchor="middle" font-family="Arial,sans-serif" font-weight="bold" font-size="12" fill="#ec4899">Clan #${esc(count)}</text>
${star4(561, 207, 4.5)}
<line x1="568" y1="207" x2="620" y2="207" stroke="#ec4899" stroke-width="0.8" opacity="0.38"/>

<!-- Description -->
<text x="315" y="242" font-family="Arial,sans-serif" font-size="13.5" fill="#dcc4d4">${esc(cardDesc)}</text>
${star4(596, 238, 4, "white", "0.75")}

<!-- List items with icon boxes -->
${listItem(315, 277, "BookOpen",      cardItem1)}
${listItem(315, 312, "Tag",           cardItem2)}
${listItem(315, 347, "MessageCircle", cardItem3)}

<!-- Closing line -->
<text x="315" y="386" font-family="Arial,sans-serif" font-size="13.5" fill="#dcc4d4">${esc(cardClosing)} &#x2665;</text>

<!-- ─── RIGHT PANEL ─── -->
<rect x="648" y="24" width="234" height="438" rx="14" fill="url(#panelBg)"/>
<rect x="648" y="24" width="234" height="438" rx="14" fill="none" stroke="#ec4899" stroke-width="1" opacity="0.32"/>

<!-- Planet top-right of panel -->
<circle cx="852" cy="96" r="14" fill="#26083e" stroke="#ec4899" stroke-width="1.2" opacity="0.65"/>
<ellipse cx="852" cy="96" rx="24" ry="7" fill="none" stroke="#ec4899" stroke-width="1.2" opacity="0.55" transform="rotate(-25 852 96)"/>

<!-- ✦ SERVER STATS ✦ -->
${star4(664, 54, 5)}
<text x="763" y="58" text-anchor="middle" font-family="Arial,sans-serif" font-weight="bold" font-size="11" fill="#ec4899" letter-spacing="2">SERVER STATS</text>
${star4(862, 54, 5)}

<!-- Stat blocks (icon + label + bold value below) -->
${statBlock(664, 87,  "Users",  "Members", memberCount)}
${statBlock(664, 128, "Globe",  "Online",  "24/7")}
${statBlock(664, 169, "Shield", "Secure",  "Always Protected")}
${statBlock(664, 210, "Zap",    "Uptime",  "100%")}

<!-- Panel separator -->
<line x1="664" y1="234" x2="870" y2="234" stroke="#ec4899" stroke-width="0.8" opacity="0.28"/>

<!-- ✦ YOUR INFO ✦ -->
${star4(664, 254, 5)}
<text x="763" y="258" text-anchor="middle" font-family="Arial,sans-serif" font-weight="bold" font-size="11" fill="#ec4899" letter-spacing="2">YOUR INFO</text>
${star4(862, 254, 5)}

<!-- Info rows (icon + label + value same line) -->
${infoRow(664, 293, "User",     "Account",   accountAge)}
${infoRow(664, 328, "Calendar", "Joined",    joinedAt)}
${infoRow(664, 363, "Hash",     "Member ID", "#" + count)}

<!-- ─── BUTTONS ─── -->
${btn(25,  414, 162, 45, "BookOpen",      cardBtn1, true)}
${btn(197, 414, 128, 45, "Tag",           cardBtn2, false)}
${btn(335, 414, 148, 45, "UserPlus",      cardBtn3, false)}
${btn(493, 414, 128, 45, "MessageCircle", cardBtn4, false)}

<!-- ─── FOOTER ─── -->
${star4(316, 488, 4, "#8855a0", "0.85")}
<text x="450" y="492" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#8855a0" letter-spacing="1.5">GIANNI  *  WELCOME SYSTEM</text>
${star4(584, 488, 4, "#8855a0", "0.85")}
</svg>`;

  try {
    const { Resvg } = await import("@resvg/resvg-js");
    const resvg = new Resvg(svg, {
      fitTo: { mode: "original" },
      font: { loadSystemFonts: true },
    });
    const png = Buffer.from(resvg.render().asPng());
    res.set({ "Content-Type": "image/png", "Cache-Control": "no-cache" });
    res.send(png);
  } catch (err: any) {
    if (err?.code === "ERR_MODULE_NOT_FOUND" || err?.message?.includes("resvg")) {
      return res.status(503).json({ error: "Welcome card nije dostupan na ovom serveru (@resvg/resvg-js nije instaliran)" });
    }
    res.status(500).json({ error: "Render failed", detail: String(err) });
  }
});

export default router;
