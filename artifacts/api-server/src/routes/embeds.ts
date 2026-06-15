import { Router } from "express";
import { eq } from "drizzle-orm";

const router = Router();

// Lazy DB — works fine when DATABASE_URL is set, falls back silently when not.
let _db: typeof import("@workspace/db").db | null = null;
let _embedsTable: typeof import("@workspace/db").embedsTable | null = null;
let _dbAvailable: boolean | null = null;

async function getDb() {
  if (_dbAvailable === false) return null;
  if (_db && _embedsTable) return { db: _db, embedsTable: _embedsTable };
  try {
    const mod = await import("@workspace/db");
    _db = mod.db;
    _embedsTable = mod.embedsTable;
    _dbAvailable = true;
    return { db: _db, embedsTable: _embedsTable };
  } catch {
    _dbAvailable = false;
    return null;
  }
}

export const DEFAULT_EMBEDS = [

  //  SISTEM
  {
    name: "welcome",
    title: "",
    description:
      "╭・🌸 Welcome to **GIANNI**\n" +
      "┆\n" +
      "┆ ✦ User: {user}\n" +
      "┆ ✦ Member: `#{memberCount}`\n" +
      "┆ ✦ Account: {accountAge}\n" +
      "┆\n" +
      "╰・Enjoy your stay 💕",
    color: "#ec4899",
    category: "Sistem",
    footer: "✦ GIANNI • WELCOME SYSTEM ✦",
    thumbnail: "{user.avatar}",
    fields: [],
    buttons: [
      { type: "link", label: "Pravila", style: "link" },
      { type: "link", label: "Role",    style: "link" },
      { type: "link", label: "Pozovi",  style: "link" },
      { type: "link", label: "Chat",    style: "link" },
    ],
  },
  {
    name: "leave",
    title: "🚪  {user} je napustio/la server",
    description:
      "😢 Žao nam je što si otišao/la.\n" +
      "💌 Uvijek si dobrodošao/la nazad!",
    color: "#9B59B6",
    category: "Sistem",
    footer: "GIANNI (Custom) • Do viđenja!",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "⏳ Proveo/la na serveru", value: "{timeOnServer}", inline: true },
      { name: "👥 Preostalo članova",    value: "`{memberCount}`", inline: true },
    ],
  },
  {
    name: "dm-welcome",
    title: "💌  Dobrodošao/la na GIAN, {user}!",
    description:
      "🎊 Hvala ti što si se pridružio/la!\n\n" +
      "👑 **discord.gg/gian**\n\n" +
      "📋 Pročitaj pravila u kanalu `#pravila` i uživaj!\n" +
      "💬 Za pomoć, pišite u `#podrška`.",
    color: "#FF85C8",
    category: "Sistem",
    footer: "GIANNI (Custom) • Dobrodošao/la!",
    thumbnail: null,
    fields: [],
  },
  {
    name: "boost",
    title: "🚀  BOOST — Hvala ti, {user}!",
    description:
      "⚡ **{user}** je upravo **boostovao server**!\n" +
      "💜 Hvala ti na podršci — server je sad još jači!",
    color: "#9B59B6",
    category: "Sistem",
    footer: "GIANNI (Custom) • Hvala na podršci",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🚀 Ukupno boostova",   value: "`{boostCount}`",   inline: true },
      { name: "💎 Server Tier",        value: "`Lvl {tier}`",     inline: true },
      { name: "🪙 Nagrada",            value: "`+2.500 🪙`",      inline: true },
    ],
  },
  {
    name: "birthday",
    title: "🎂  Sretan Rođendan, {user}!",
    description:
      "🎉 Danas je poseban dan za **{user}**!\n\n" +
      "🎁 Svi mu/joj čestitajte!\n" +
      "🌟 Neka ti je srećan i blagoslovljen dan!",
    color: "#FF85C8",
    category: "Sistem",
    footer: "GIANNI (Custom) • Sretan Rođendan!",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🎈 Godine", value: "`{age}` godina", inline: true },
      { name: "🪙 Poklon", value: "`+5.000 🪙`",   inline: true },
    ],
  },
  {
    name: "starboard",
    title: "⭐  Zvjezdana poruka!",
    description:
      "✨ Ova poruka je dobila **{stars}** zvjezdica!\n" +
      "📍 Kanal: {channel}\n" +
      "✍️ Autor: {author}",
    color: "#F1C40F",
    category: "Sistem",
    footer: "GIANNI (Custom) • Starboard",
    thumbnail: null,
    fields: [],
  },
  {
    name: "aotw",
    title: "🏆  Aktivni Član Sedmice",
    description:
      "👑 Čestitamo **{user}** na tituli!\n" +
      "🌟 Ova sedmica pripada tebi!\n",
    color: "#F1C40F",
    category: "Sistem",
    footer: "GIANNI (Custom) • Aktivni Član Sedmice",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "💬 Poruka",  value: "`{messageCount}`", inline: true },
      { name: "🪙 Nagrada", value: "`+10.000 🪙`",     inline: true },
    ],
  },

  //  LOG
  {
    name: "log-join",
    title: "📥  Novi Član",
    description:
      "👤 **{user}** se pridružio serveru.\n" +
      "📅 Registracija: {accountAge}",
    color: "#f59e0b",
    category: "Log",
    footer: "GIANNI (Custom) • Log",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🆔 ID",          value: "`{userId}`",   inline: true },
      { name: "👥 Ukupno",      value: "`{memberCount}`", inline: true },
    ],
  },
  {
    name: "log-edit",
    title: "✏️  Poruka Editovana",
    description:
      "👤 **{user}** je izmijenio/la poruku u {channel}.\n\n" +
      "📝 **Stara poruka:**\n`{oldContent}`\n\n" +
      "✅ **Nova poruka:**\n`{newContent}`",
    color: "#f59e0b",
    category: "Log",
    footer: "GIANNI (Custom) • Log Editovanje",
    thumbnail: null,
    fields: [],
  },
  {
    name: "log-delete",
    title: "🗑️  Poruka Obrisana",
    description:
      "👤 **{user}** je obrisao/la poruku u {channel}.\n\n" +
      "📝 **Sadržaj:**\n`{content}`",
    color: "#f59e0b",
    category: "Log",
    footer: "GIANNI (Custom) • Log Brisanje",
    thumbnail: null,
    fields: [],
  },
  {
    name: "report",
    title: "🚨  Prijava člana",
    description:
      "⚠️ **{reporter}** je prijavio/la **{reported}**.\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#f59e0b",
    category: "Log",
    footer: "GIANNI (Custom) • Prijava",
    thumbnail: "{reported.avatar}",
    fields: [
      { name: "🆔 ID prijavljenog",  value: "`{reportedId}`", inline: true },
      { name: "📅 Datum",             value: "{date}",         inline: true },
    ],
  },

  //  MODERACIJA
  {
    name: "warn",
    title: "⚠️  Upozorenje",
    description:
      "🔔 **{user}** je dobio/la upozorenje.\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#ef4444",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Moderacija",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🛡️ Moderator", value: "{mod}",         inline: true },
      { name: "⚠️ Warn #",   value: "`{warnCount}`", inline: true },
    ],
  },
  {
    name: "ban",
    title: "🔨  Član Banovan",
    description:
      "⛔ **{user}** je banovan sa servera.\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#ef4444",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Ban",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🛡️ Moderator", value: "{mod}",      inline: true },
      { name: "⏳ Trajanje",   value: "{duration}", inline: true },
    ],
  },
  {
    name: "mod-kick",
    title: "👢  Član Kickovan",
    description:
      "🚪 **{user}** je izbačen sa servera.\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#ef4444",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Kick",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🛡️ Moderator", value: "{mod}", inline: true },
    ],
  },
  {
    name: "mod-mute",
    title: "🔇  Član Mutovan",
    description:
      "🤐 **{user}** je mutovan.\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#ef4444",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Mute",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🛡️ Moderator", value: "{mod}",      inline: true },
      { name: "⏳ Trajanje",   value: "{duration}", inline: true },
    ],
  },
  {
    name: "mod-unmute",
    title: "🔊  Član Odmutovan",
    description:
      "✅ **{user}** je odmutovan — može opet pisati.",
    color: "#22c55e",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Unmute",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🛡️ Moderator", value: "{mod}", inline: true },
    ],
  },
  {
    name: "mod-timeout",
    title: "⏰  Timeout",
    description:
      "🕐 **{user}** je stavljen u timeout.\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#ef4444",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Timeout",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🛡️ Moderator", value: "{mod}",      inline: true },
      { name: "⏳ Trajanje",   value: "{duration}", inline: true },
    ],
  },
  {
    name: "mod-purge",
    title: "🧹  Poruke Obrisane",
    description:
      "🗑️ **{mod}** je obrisao/la **{count}** poruka u {channel}.",
    color: "#ef4444",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Purge",
    thumbnail: null,
    fields: [],
  },
  {
    name: "mod-unban",
    title: "🔓  Član Odbanovan",
    description:
      "✅ **{user}** je odbanovan sa servera.\n" +
      "🤝 Dobrodošao/la nazad!",
    color: "#22c55e",
    category: "Moderacija",
    footer: "GIANNI (Custom) • Unban",
    thumbnail: null,
    fields: [
      { name: "🛡️ Moderator", value: "{mod}", inline: true },
    ],
  },

  //  XP
  {
    name: "levelup",
    title: "🎉  Level Up, {user}!",
    description:
      "⬆️ Dostigao/la si novi nivo!\n" +
      "🌟 Nastavi tako — odlično!\n",
    color: "#22c55e",
    category: "XP",
    footer: "GIANNI (Custom) • Level Up",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "📊 Novi nivo", value: "`Level {level}`", inline: true },
      { name: "🪙 Nagrada",   value: "`+{reward} 🪙`",  inline: true },
    ],
  },
  {
    name: "vatrica-nova",
    title: "🔥  Nova Vatrica, {user}!",
    description:
      "⭐ **{user}** je zaradio/la novu vatricu!\n" +
      "🏆 Ukupno vatrica: **{count}**",
    color: "#FF6A00",
    category: "XP",
    footer: "GIANNI (Custom) • Vatrica",
    thumbnail: "{user.avatar}",
    fields: [],
  },
  {
    name: "aktivnost",
    title: "📊  Aktivnost",
    description:
      "📈 Pregled aktivnosti za **{user}**:",
    color: "#22c55e",
    category: "XP",
    footer: "GIANNI (Custom) • Aktivnost",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "💬 Poruke",    value: "`{messages}`", inline: true },
      { name: "⏱️ Glasovni", value: "`{voice}`",    inline: true },
      { name: "⭐ XP",        value: "`{xp}`",       inline: true },
    ],
  },
  {
    name: "rank",
    title: "🏅  Rank — {user}",
    description:
      "📊 Tvoj trenutni rank profil:",
    color: "#22c55e",
    category: "XP",
    footer: "GIANNI (Custom) • Rank",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "⭐ XP",        value: "`{xp}`",        inline: true },
      { name: "📊 Level",     value: "`{level}`",     inline: true },
      { name: "🏅 Rank",      value: "`#{rank}`",     inline: true },
      { name: "🔥 Vatrice",   value: "`{vatrice}`",   inline: true },
      { name: "🪙 Novac",     value: "`{balance} 🪙`", inline: true },
    ],
  },
  {
    name: "leaderboard-xp",
    title: "🏆  Top Lista — XP",
    description:
      "🌟 Najaktivniji članovi servera:\n" +
      "{leaderboard}",
    color: "#22c55e",
    category: "XP",
    footer: "GIANNI (Custom) • XP Leaderboard",
    thumbnail: null,
    fields: [],
  },
  {
    name: "leaderboard-novac",
    title: "💰  Top Lista — Novac",
    description:
      "🏦 Najbogatiji članovi servera:\n" +
      "{leaderboard}",
    color: "#f97316",
    category: "XP",
    footer: "GIANNI (Custom) • Novac Leaderboard",
    thumbnail: null,
    fields: [],
  },

  //  EKONOMIJA
  {
    name: "heist",
    title: "🏦  Razboj u pripremi!",
    description:
      "🎯 **{user}** planira pljačku banke!\n" +
      "👥 Pridruži se ekipi — klikni dugme!\n" +
      "⏳ Počinje za: **{countdown}**\n",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Heist",
    thumbnail: null,
    fields: [
      { name: "👥 Učesnici",  value: "`{count}`",   inline: true },
      { name: "💰 Nagradni fond", value: "`{pot} 🪙`", inline: true },
    ],
  },
  {
    name: "lottery",
    title: "🎰  Sedmična Loto!",
    description:
      "🎫 Kupi tiket i osvoji jackpot!\n" +
      "⏳ Žrijeb: **{drawTime}**\n",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Loto",
    thumbnail: null,
    fields: [
      { name: "💰 Jackpot",   value: "`{pot} 🪙`",     inline: true },
      { name: "🎫 Tiketa",    value: "`{tickets}`",    inline: true },
      { name: "🪙 Cijena",    value: "`{price} 🪙`",   inline: true },
    ],
  },
  {
    name: "quests",
    title: "📋  Dnevni Zadaci",
    description:
      "✅ Ispuni zadatke i osvoji nagrade!\n" +
      "{quests}",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Dnevni Zadaci",
    thumbnail: null,
    fields: [],
  },
  {
    name: "giveaway",
    title: "🎁  Nagradna Igra!",
    description:
      "🎉 **{host}** pokreće nagradnu igru!\n" +
      "⏳ Završava: **{endTime}**\n",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Giveaway",
    thumbnail: null,
    fields: [
      { name: "🏆 Nagrada",    value: "{prize}",      inline: true },
      { name: "🎟️ Pobjednika", value: "`{winners}`", inline: true },
    ],
  },
  {
    name: "giveaway-end",
    title: "🏆  Nagradna Igra Završena!",
    description:
      "🎉 Nagradna igra je gotova!\n\n" +
      "🥇 **Pobjednici:**\n{winners}",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Giveaway Kraj",
    thumbnail: null,
    fields: [],
  },
  {
    name: "eco-balance",
    title: "💰  Balans — {user}",
    description:
      "💳 Pregled tvog računa:",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Balans",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🪙 Novčanik", value: "`{wallet} 🪙`", inline: true },
      { name: "🏦 Banka",    value: "`{bank} 🪙`",   inline: true },
      { name: "💰 Ukupno",   value: "`{total} 🪙`",  inline: true },
    ],
  },
  {
    name: "eco-daily",
    title: "📅  Dnevna Nagrada!",
    description:
      "✅ **{user}** je preuzeo/la dnevnu nagradu!\n" +
      "⏰ Sljedeća nagrada za: **24h**",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Daily",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🪙 Nagrada",  value: "`+{amount} 🪙`", inline: true },
      { name: "🔥 Streak",   value: "`{streak} dana`", inline: true },
    ],
  },
  {
    name: "eco-work",
    title: "💼  Posao",
    description:
      "🔧 **{user}** je radio/la kao **{job}** i zaradio/la!",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Posao",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🪙 Zarada",   value: "`+{amount} 🪙`", inline: true },
      { name: "⏰ Sljedeći", value: "`{cooldown}`",    inline: true },
    ],
  },
  {
    name: "eco-shop",
    title: "🛒  Shop",
    description:
      "🏪 Dostupni predmeti:\n" +
      "{items}",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Shop",
    thumbnail: null,
    fields: [],
  },
  {
    name: "eco-buy",
    title: "✅  Kupovina Uspješna!",
    description:
      "🛍️ **{user}** je kupio/la **{item}**!\n" +
      "🪙 Potrošeno: `{price} 🪙`",
    color: "#22c55e",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Kupovina",
    thumbnail: null,
    fields: [],
  },
  {
    name: "eco-transfer",
    title: "💸  Transfer Kovanica",
    description:
      "↔️ **{from}** je poslao/la **{amount} 🪙** korisniku **{to}**!",
    color: "#f97316",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Transfer",
    thumbnail: null,
    fields: [],
  },
  {
    name: "eco-rob",
    title: "🦹  Pljačka!",
    description:
      "💰 **{robber}** je pokušao/la opljačkati **{victim}**!\n\n" +
      "{result}",
    color: "#ef4444",
    category: "Ekonomija",
    footer: "GIANNI (Custom) • Pljačka",
    thumbnail: null,
    fields: [
      { name: "💰 Iznos",    value: "`{amount} 🪙`", inline: true },
      { name: "📊 Rezultat", value: "{status}",      inline: true },
    ],
  },

  //  IGRE
  {
    name: "slots",
    title: "🎰  Slot Mašina",
    description:
      "🎲 **{user}** vrti slotove!\n\n" +
      "[ {r1} | {r2} | {r3} ]\n\n" +
      "{result}\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Slots",
    thumbnail: null,
    fields: [
      { name: "🪙 Ulog",    value: "`{bet} 🪙`",    inline: true },
      { name: "💰 Dobitak", value: "`{winnings} 🪙`", inline: true },
    ],
  },
  {
    name: "blackjack",
    title: "🃏  Blackjack",
    description:
      "🎴 **{user}** igra blackjack!\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Blackjack",
    thumbnail: null,
    fields: [
      { name: "🎴 Tvoje karte",    value: "{playerHand} (`{playerScore}`)", inline: true },
      { name: "🤖 Dealer karte",   value: "{dealerHand} (`{dealerScore}`)", inline: true },
      { name: "🪙 Ulog",           value: "`{bet} 🪙`",                     inline: false },
    ],
  },
  {
    name: "poker-lobby",
    title: "♠️  Poker — Lobby",
    description:
      "🃏 **{host}** otvara poker stol!\n" +
      "👥 Čekamo igrače... ({count}/{max})\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Poker",
    thumbnail: null,
    fields: [
      { name: "🪙 Buy-in",    value: "`{buyin} 🪙`", inline: true },
      { name: "👥 Igrači",    value: "`{players}`",  inline: true },
    ],
  },
  {
    name: "poker-game",
    title: "🎲  Poker — U Toku",
    description:
      "♠️ Runda **{round}** — {phase}\n" +
      "🃏 Stol: {communityCards}",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Poker",
    thumbnail: null,
    fields: [
      { name: "💰 Pot",       value: "`{pot} 🪙`",  inline: true },
      { name: "🎯 Na redu",   value: "{current}",   inline: true },
    ],
  },
  {
    name: "poker-showdown",
    title: "👑  Poker — Showdown!",
    description:
      "🏆 **{winner}** pobijedio/la!\n\n" +
      "🃏 Pobjednička kombinacija: **{hand}**",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Poker Showdown",
    thumbnail: null,
    fields: [
      { name: "🪙 Dobitak", value: "`{pot} 🪙`", inline: true },
    ],
  },
  {
    name: "among-us-lobby",
    title: "🚀  Among Us — Lobby",
    description:
      "👨‍🚀 **{host}** otvara igru!\n" +
      "👥 Igrači: {count}/{max}\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Among Us",
    thumbnail: null,
    fields: [],
  },
  {
    name: "among-us-game",
    title: "🔪  Among Us — U Toku",
    description:
      "👀 Imposter je među nama...\n\n" +
      "👥 Preostalo igrača: **{alive}**\n" +
      "💀 Eliminirani: **{dead}**",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Among Us",
    thumbnail: null,
    fields: [],
  },
  {
    name: "among-us-end",
    title: "🏆  Among Us — Kraj",
    description:
      "🎉 Igra je završena!\n\n" +
      "🥇 **Pobjednici:** {winners}\n" +
      "🔪 **Imposter:** {imposter}",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Among Us",
    thumbnail: null,
    fields: [],
  },
  {
    name: "kaladont-start",
    title: "🔤  Kaladont — Start!",
    description:
      "📝 Igra počinje! Prva riječ:\n" +
      "➜ **{word}**\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Kaladont",
    thumbnail: null,
    fields: [],
  },
  {
    name: "kaladont-active",
    title: "🔤  Kaladont — Na redu: {user}",
    description:
      "⏳ **{user}**, tvoj red!\n\n" +
      "➜ Zadnje slovo: **{letter}**\n" +
      "⌛ Imaš **{seconds}** sekundi!",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Kaladont",
    thumbnail: null,
    fields: [],
  },
  {
    name: "kaladont-word",
    title: "✅  Kaladont — Prihvaćeno!",
    description:
      "👍 **{user}** je rekao/la: **{word}**\n" +
      "➜ Sljedeće slovo: **{nextLetter}**",
    color: "#22c55e",
    category: "Igre",
    footer: "GIANNI (Custom) • Kaladont",
    thumbnail: null,
    fields: [],
  },
  {
    name: "kaladont-win",
    title: "🏆  Kaladont — Pobjeda!",
    description:
      "🎉 **{winner}** pobijedio/la!\n" +
      "🪙 Nagrada: `+{reward} 🪙`",
    color: "#22c55e",
    category: "Igre",
    footer: "GIANNI (Custom) • Kaladont",
    thumbnail: null,
    fields: [],
  },
  {
    name: "bingo",
    title: "🎯  Bingo!",
    description:
      "🎲 Izvučeni brojevi:\n" +
      "{numbers}\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Bingo",
    thumbnail: null,
    fields: [],
  },
  {
    name: "vjasala",
    title: "📝  Vješala",
    description:
      "```{drawing}```\n" +
      "🔤 Riječ: **{display}**\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Vješala",
    thumbnail: null,
    fields: [
      { name: "❌ Greške",   value: "`{wrong}/{max}`",    inline: true },
      { name: "🔤 Pogođeno", value: "`{guessed}`",        inline: true },
    ],
  },
  {
    name: "vjasala-kraj",
    title: "🎉  Vješala — Pogodak!",
    description:
      "✅ **{user}** je pogodio/la: **{word}**!\n" +
      "🪙 Nagrada: `+{reward} 🪙`",
    color: "#22c55e",
    category: "Igre",
    footer: "GIANNI (Custom) • Vješala",
    thumbnail: null,
    fields: [],
  },
  {
    name: "toplo-hladno",
    title: "🌡️  Toplo ili Hladno?",
    description:
      "🎯 **{user}** pokušava pogoditi broj!\n\n" +
      "➜ Pogodak: **{guess}**\n" +
      "📊 **{feedback}**",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Toplo-Hladno",
    thumbnail: null,
    fields: [
      { name: "🔢 Pokušaji", value: "`{attempts}`", inline: true },
    ],
  },
  {
    name: "kviz",
    title: "🧠  Kviz — Balkan Pitanje",
    description:
      "❓ **{question}**\n" +
      "{options}",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Kviz",
    thumbnail: null,
    fields: [
      { name: "⏰ Vrijeme",     value: "`{time}s`",     inline: true },
      { name: "🪙 Nagrada",     value: "`{reward} 🪙`", inline: true },
    ],
  },
  {
    name: "geografija",
    title: "🌍  Geografija Kviz",
    description:
      "🗺️ **{question}**\n" +
      "{options}",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Geografija",
    thumbnail: null,
    fields: [
      { name: "⏰ Vrijeme",  value: "`{time}s`",     inline: true },
      { name: "🪙 Nagrada", value: "`{reward} 🪙`", inline: true },
    ],
  },
  {
    name: "mafia-lobby",
    title: "🕵️  Mafia — Lobby",
    description:
      "🔫 **{host}** pokrenuo/la Mafia igru!\n" +
      "👥 Igrači: {count}/{max}\n",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Mafia",
    thumbnail: null,
    fields: [],
  },
  {
    name: "mafia-end",
    title: "👑  Mafia — Kraj Igre!",
    description:
      "🏆 **{winners}** pobijedio/la!\n\n" +
      "🕵️ Mafia: {mafia}\n" +
      "👮 Grad: {town}",
    color: "#3b82f6",
    category: "Igre",
    footer: "GIANNI (Custom) • Mafia",
    thumbnail: null,
    fields: [],
  },

  //  FUN
  {
    name: "hunt",
    title: "🏹  Lov — Ulovio/la životinju!",
    description:
      "🦌 **{user}** je ulovio/la: **{animal}**!\n" +
      "🪙 Zarada: `+{amount} 🪙`",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Lov",
    thumbnail: null,
    fields: [],
  },
  {
    name: "zoo",
    title: "🦁  Zoo — Tvoja Zbirka",
    description:
      "🐾 **{user}** ima sljedeće životinje:",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Zoo",
    thumbnail: "{user.avatar}",
    fields: [],
  },
  {
    name: "battle",
    title: "⚔️  Bitka!",
    description:
      "🛡️ **{challenger}** vs **{opponent}**!\n" +
      "{result}",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Bitka",
    thumbnail: null,
    fields: [],
  },
  {
    name: "pray",
    title: "🙏  Molitva",
    description:
      "✨ **{user}** se molio/la i...\n\n" +
      "{result}",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Molitva",
    thumbnail: null,
    fields: [],
  },
  {
    name: "vers",
    title: "🎤  Vers — Hip Hop",
    description:
      "🎵 **{user}** baca verse:\n\n" +
      "```{verse}```",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Vers",
    thumbnail: "{user.avatar}",
    fields: [],
  },
  {
    name: "kompli",
    title: "💌  Kompliment",
    description:
      "💕 **{from}** kaže **{to}**:\n\n" +
      "*{compliment}*",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Kompliment",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "fora",
    title: "😂  Fora",
    description:
      "😏 **{from}** je pogledao/la **{to}** i shvatio/la:\n\n" +
      "*{joke}*",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Fora",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "muv",
    title: "💘  Muvanje",
    description:
      "😍 **{from}** → **{to}**:\n\n" +
      "*{pickup}*",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Balkan Muvanje",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "crush",
    title: "💖  Crush",
    description:
      "❤️ **{user}** ima crush na nekoga!\n" +
      "Saznaj koga — svi glasajte!",
    color: "#ec4899",
    category: "Fun",
    footer: "GIANNI (Custom) • Crush",
    thumbnail: "{user.avatar}",
    fields: [],
  },

  //  LJUBAVNE
  {
    name: "zagrljaj",
    title: "🤗  Zagrljaj",
    description:
      "💕 **{from}** grli **{to}**!\n" +
      "Budi slobodan/na primiti ovaj zagrljaj! 🫂",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Zagrljaj",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "poljubac",
    title: "💋  Poljubac",
    description:
      "😘 **{from}** šalje poljubac **{to}**!",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Poljubac",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "mazi",
    title: "🥰  Mazi",
    description:
      "💕 **{from}** mazi **{to}**!",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Mazi",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "tapsi",
    title: "👏  Tapsi",
    description:
      "🫶 **{from}** tapsi **{to}** po glavi!",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Tapsi",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "high5",
    title: "🙌  High Five!",
    description:
      "✋ **{from}** daje high five **{to}**!",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • High Five",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "cudan",
    title: "😅  Ćudan",
    description:
      "👀 **{from}** gleda čudno u **{to}**...\n" +
      "Niko ne zna zašto! 🤔",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Ćudan",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "srce",
    title: "❤️  Srce",
    description:
      "💕 **{from}** šalje srce **{to}**!",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Srce",
    thumbnail: "{to.avatar}",
    fields: [],
  },
  {
    name: "brak",
    title: "💍  Prosidba!",
    description:
      "💒 **{from}** prosi **{to}**!\n" +
      "👑 Hoćeš li prihvatiti?\n",
    color: "#FF85C8",
    category: "Ljubavne",
    footer: "GIANNI (Custom) • Prosidba",
    thumbnail: "{to.avatar}",
    fields: [],
  },

  //  INFO
  {
    name: "spotify",
    title: "🎵  Spotify",
    description:
      "🎶 **{user}** sluša muziku:",
    color: "#1DB954",
    category: "Info",
    footer: "GIANNI (Custom) • Spotify",
    thumbnail: "{albumArt}",
    fields: [
      { name: "🎵 Pjesma",   value: "**{song}**",   inline: true },
      { name: "🎤 Izvođač",  value: "{artist}",     inline: true },
      { name: "💽 Album",    value: "{album}",      inline: true },
    ],
  },
  {
    name: "invite",
    title: "📊  Statistika Pozivnica",
    description:
      "📨 Pregled pozivnica za **{user}**:",
    color: "#14b8a6",
    category: "Info",
    footer: "GIANNI (Custom) • Pozivnice",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "✅ Pozvano",     value: "`{invites}`",    inline: true },
      { name: "🚪 Otišlo",      value: "`{left}`",       inline: true },
      { name: "❌ Lažnih",      value: "`{fake}`",       inline: true },
    ],
  },
  {
    name: "avatar",
    title: "🖼️  Avatar — {user}",
    description:
      "👤 Avatar od **{user}**:",
    color: "#14b8a6",
    category: "Info",
    footer: "GIANNI (Custom) • Avatar",
    thumbnail: null,
    fields: [],
  },
  {
    name: "brojanje-info",
    title: "🔢  Brojanje — Stanje",
    description:
      "📊 Trenutno stanje brojanja na serveru:",
    color: "#14b8a6",
    category: "Info",
    footer: "GIANNI (Custom) • Brojanje",
    thumbnail: null,
    fields: [
      { name: "🔢 Broj",        value: "`{count}`",   inline: true },
      { name: "👤 Zadnji",      value: "{lastUser}",  inline: true },
      { name: "🏆 Rekord",      value: "`{record}`",  inline: true },
    ],
  },

  //  SISTEM PANELI
  {
    name: "ticket",
    title: "🎫  Podrška — Otvori Tiket",
    description:
      "📩 Trebaš pomoć? Klikni dugme ispod!\n" +
      "🛡️ Staff će ti odgovoriti što prije.\n",
    color: "#a78bfa",
    category: "Sistem paneli",
    footer: "GIANNI (Custom) • Support",
    thumbnail: null,
    fields: [],
  },
  {
    name: "ticket-otvoren",
    title: "✅  Tiket Otvoren",
    description:
      "🎫 **{user}**, tiket je otvoren!\n\n" +
      "📝 Opiši problem i staff će ti pomoći.\n" +
      "⏳ Odgovor stiže što prije!",
    color: "#22c55e",
    category: "Sistem paneli",
    footer: "GIANNI (Custom) • Tiket",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🆔 Tiket ID", value: "`#{ticketId}`", inline: true },
      { name: "📅 Otvoren",  value: "{date}",        inline: true },
    ],
  },
  {
    name: "staff-prijava",
    title: "📋  Staff Prijava",
    description:
      "⭐ Želi postati staff?\n" +
      "📝 Ispuni prijavu klikom na dugme!\n",
    color: "#a78bfa",
    category: "Sistem paneli",
    footer: "GIANNI (Custom) • Staff Prijava",
    thumbnail: null,
    fields: [],
  },
  {
    name: "private-vc",
    title: "🎙️  Privatni Voice Kanal",
    description:
      "🔒 Upravljaj privatnim voice kanalom!\n",
    color: "#a78bfa",
    category: "Sistem paneli",
    footer: "GIANNI (Custom) • Privatni VC",
    thumbnail: null,
    fields: [],
  },
  {
    name: "voice-pravila",
    title: "🔊  Voice Pravila",
    description:
      "📋 **Pravila za Voice kanale:**\n\n" +
      "🔇 Ne uznemiravaj ostale\n" +
      "🎵 Muzika samo uz pristanak\n" +
      "🚫 Nema neprimjerenog sadržaja\n",
    color: "#a78bfa",
    category: "Sistem paneli",
    footer: "GIANNI (Custom) • Voice Pravila",
    thumbnail: null,
    fields: [],
  },

  //  VATRICE
  {
    name: "vatrice-pup",
    title: "🔥  Top Lista Vatrica",
    description:
      "⭐ Najtopliji članovi servera:\n" +
      "{leaderboard}",
    color: "#FF6A00",
    category: "Vatrice",
    footer: "GIANNI (Custom) • Vatrice Top",
    thumbnail: null,
    fields: [],
  },
  {
    name: "vatrice-start",
    title: "🔥  Vatrica Sistem — Pokrenut!",
    description:
      "⭐ Vatrica sistem je aktivan!\n" +
      "💬 Prikupljaj vatrice aktivnošću!",
    color: "#FF6A00",
    category: "Vatrice",
    footer: "GIANNI (Custom) • Vatrice",
    thumbnail: null,
    fields: [],
  },
  {
    name: "vatrice-kanal",
    title: "🔥  Vatrica Kanal Postavljen",
    description:
      "📍 Kanal za vatrice: {channel}\n" +
      "✅ Sve vatrice idu u ovaj kanal!",
    color: "#FF6A00",
    category: "Vatrice",
    footer: "GIANNI (Custom) • Vatrice",
    thumbnail: null,
    fields: [],
  },
  {
    name: "vatrice-oblik",
    title: "🔥  Vatrica Emoji Promijenjen",
    description:
      "✏️ Emoji za vatrice promijenjen!\n" +
      "➜ Novi emoji: {emoji}",
    color: "#FF6A00",
    category: "Vatrice",
    footer: "GIANNI (Custom) • Vatrice",
    thumbnail: null,
    fields: [],
  },

  //  POO
  {
    name: "poo",
    title: "💩  Poo — Stanje Kreature",
    description:
      "🐾 Tvoja Poo kreatura!\n",
    color: "#92400e",
    category: "Poo",
    footer: "GIANNI (Custom) • Poo",
    thumbnail: null,
    fields: [
      { name: "❤️ Zdravlje",    value: "`{health}/100`",    inline: true },
      { name: "😄 Sreća",       value: "`{happiness}/100`", inline: true },
      { name: "🍖 Sitost",      value: "`{hunger}/100`",    inline: true },
    ],
  },
  {
    name: "poo-zadaci",
    title: "📋  Poo — Zadaci",
    description:
      "✅ Ispuni zadatke da hraniš svoju Poo!\n\n" +
      "{tasks}",
    color: "#92400e",
    category: "Poo",
    footer: "GIANNI (Custom) • Poo Zadaci",
    thumbnail: null,
    fields: [],
  },
  {
    name: "poo-top",
    title: "🏆  Poo — Top Čuvari",
    description:
      "💩 Najbolji čuvari Poo kreatura:\n" +
      "{leaderboard}",
    color: "#92400e",
    category: "Poo",
    footer: "GIANNI (Custom) • Poo Top",
    thumbnail: null,
    fields: [],
  },
  {
    name: "poo-hrani",
    title: "🍖  Poo — Hranjena!",
    description:
      "✅ **{user}** je hranio/la svoju Poo!\n" +
      "😄 Sreća: +{happiness} | 🍖 Sitost: +{hunger}",
    color: "#22c55e",
    category: "Poo",
    footer: "GIANNI (Custom) • Poo Hrani",
    thumbnail: null,
    fields: [],
  },
  {
    name: "poo-info",
    title: "📊  Poo — Moj Doprinos",
    description:
      "🐾 **{user}** briga o Poo kreaturama:",
    color: "#92400e",
    category: "Poo",
    footer: "GIANNI (Custom) • Poo Info",
    thumbnail: "{user.avatar}",
    fields: [
      { name: "🍖 Hranjenja", value: "`{feedings}`", inline: true },
      { name: "⭐ Doprinos",  value: "`{score}`",    inline: true },
    ],
  },

  //  ADMIN
  {
    name: "backup",
    title: "💾  Backup — Snimljen",
    description:
      "✅ Server backup uspješno snimljen!\n" +
      "📅 Datum: **{datum}**",
    color: "#64748b",
    category: "Admin",
    footer: "GIANNI (Custom) • Backup",
    thumbnail: null,
    fields: [
      { name: "💾 Veličina",   value: "`{size}`",    inline: true },
      { name: "📅 Sljedeći",   value: "{next}",      inline: true },
    ],
  },
  {
    name: "backup-restore",
    title: "♻️  Backup — Vraćen",
    description:
      "✅ Server backup vraćen!\n" +
      "➜ Svi podaci prepisani backupom od **{datum}**.",
    color: "#64748b",
    category: "Admin",
    footer: "GIANNI (Custom) • Backup Restore",
    thumbnail: null,
    fields: [],
  },
  {
    name: "backup-status",
    title: "📊  Backup — Status",
    description:
      "💾 Pregled backup stanja:",
    color: "#64748b",
    category: "Admin",
    footer: "GIANNI (Custom) • Backup Status",
    thumbnail: null,
    fields: [
      { name: "✅ Zadnji backup",  value: "{lastBackup}", inline: true },
      { name: "📁 Ukupno",         value: "`{count}`",    inline: true },
    ],
  },
  {
    name: "report-closed",
    title: "✅  Report Zatvoren",
    description:
      "🔒 Prijava je zatvoren od strane **{mod}**.\n\n" +
      "📋 **Ishod:** {outcome}",
    color: "#64748b",
    category: "Admin",
    footer: "GIANNI (Custom) • Report Zatvoren",
    thumbnail: null,
    fields: [],
  },
  {
    name: "report-nova",
    title: "🚨  Nova Prijava",
    description:
      "⚠️ **{reporter}** prijavio/la **{reported}**!\n\n" +
      "📋 **Razlog:** {reason}",
    color: "#64748b",
    category: "Admin",
    footer: "GIANNI (Custom) • Nova Prijava",
    thumbnail: null,
    fields: [
      { name: "🆔 ID",     value: "`{reportId}`", inline: true },
      { name: "📅 Datum",  value: "{date}",       inline: true },
    ],
  },

  //  MUZIKA
  {
    name: "music-play",
    title: "▶️  Now Playing",
    description:
      "🎵 **{title}**\n" +
      "🎤 Izvođač: **{artist}**\n",
    color: "#8b5cf6",
    category: "Muzika",
    footer: "GIANNI (Custom) • Muzika",
    thumbnail: "{thumbnail}",
    fields: [
      { name: "⏱️ Trajanje",  value: "`{duration}`", inline: true },
      { name: "🔊 Glasnoća",  value: "`{volume}%`",  inline: true },
      { name: "👤 Tražio/la", value: "{requester}",  inline: true },
    ],
  },
  {
    name: "music-queue",
    title: "📜  Red Čekanja",
    description:
      "🎵 **Trenutno:** {current}\n\n" +
      "📋 **Sljedeće:**\n{queue}\n",
    color: "#8b5cf6",
    category: "Muzika",
    footer: "GIANNI (Custom) • Queue",
    thumbnail: null,
    fields: [
      { name: "🎵 Pjesama u redu", value: "`{count}`", inline: true },
    ],
  },
  {
    name: "music-skip",
    title: "⏭️  Preskočeno",
    description:
      "⏭️ **{user}** je preskočio/la: **{title}**\n" +
      "▶️ Sljedeće: **{next}**",
    color: "#8b5cf6",
    category: "Muzika",
    footer: "GIANNI (Custom) • Skip",
    thumbnail: null,
    fields: [],
  },
  {
    name: "music-pause",
    title: "⏸️  Pauzirano",
    description:
      "⏸️ Muzika pauzirana od **{user}**.\n" +
      "▶️ Nastavi sa `/resume`.",
    color: "#8b5cf6",
    category: "Muzika",
    footer: "GIANNI (Custom) • Pauza",
    thumbnail: null,
    fields: [],
  },
  {
    name: "music-stop",
    title: "⏹️  Zaustavljeno",
    description:
      "⏹️ **{user}** je zaustavio/la muziku.\n" +
      "🎵 Red čekanja obrisan.",
    color: "#8b5cf6",
    category: "Muzika",
    footer: "GIANNI (Custom) • Stop",
    thumbnail: null,
    fields: [],
  },
  {
    name: "music-lyrics",
    title: "📝  Tekst Pjesme",
    description:
      "🎵 **{title}** — {artist}\n\n" +
      "{lyrics}\n",
    color: "#8b5cf6",
    category: "Muzika",
    footer: "GIANNI (Custom) • Lyrics",
    thumbnail: null,
    fields: [],
  },

  //  VERIFIKACIJA
  {
    name: "verify-panel",
    title: "🛡️  Verifikacija",
    description:
      "✅ Verificiraj se da pristupiš serveru!\n" +
      "🔒 Klikni dugme ispod.\n",
    color: "#06b6d4",
    category: "Verifikacija",
    footer: "GIANNI (Custom) • Verifikacija",
    thumbnail: null,
    fields: [],
  },
  {
    name: "verify-success",
    title: "✅  Verifikacija Uspješna!",
    description:
      "🎉 **{user}**, uspješno si verificiran/a!\n" +
      "🚀 Dobrodošao/la na server!",
    color: "#22c55e",
    category: "Verifikacija",
    footer: "GIANNI (Custom) • Verifikacija",
    thumbnail: "{user.avatar}",
    fields: [],
  },
  {
    name: "verify-fail",
    title: "❌  Verifikacija Neuspješna",
    description:
      "⚠️ **{user}**, verifikacija nije uspjela.\n" +
      "🔄 Pokušaj ponovo.",
    color: "#ef4444",
    category: "Verifikacija",
    footer: "GIANNI (Custom) • Verifikacija",
    thumbnail: null,
    fields: [],
  },

  //  ANKETE
  {
    name: "poll-create",
    title: "🗳️  Nova Anketa",
    description:
      "❓ **{question}**\n" +
      "{options}",
    color: "#f43f5e",
    category: "Ankete",
    footer: "GIANNI (Custom) • Anketa",
    thumbnail: null,
    fields: [
      { name: "⏰ Završava", value: "{endTime}", inline: true },
    ],
  },
  {
    name: "poll-results",
    title: "📊  Rezultati Ankete",
    description:
      "❓ **{question}**\n" +
      "{results}",
    color: "#f43f5e",
    category: "Ankete",
    footer: "GIANNI (Custom) • Anketa Rezultati",
    thumbnail: null,
    fields: [
      { name: "👥 Ukupno glasova", value: "`{total}`", inline: true },
    ],
  },

  //  REACTION ROLES
  {
    name: "rr-panel",
    title: "🏷️  Reaction Roles",
    description:
      "🎭 Odaberi svoju ulogu klikom na dugme!\n",
    color: "#d946ef",
    category: "Reaction Roles",
    footer: "GIANNI (Custom) • Reaction Roles",
    thumbnail: null,
    fields: [],
  },
  {
    name: "rr-add",
    title: "✅  Uloga Dodana",
    description:
      "🎭 **{user}** dobio/la ulogu **{role}**!",
    color: "#22c55e",
    category: "Reaction Roles",
    footer: "GIANNI (Custom) • Reaction Roles",
    thumbnail: null,
    fields: [],
  },
  {
    name: "rr-remove",
    title: "❌  Uloga Skinuta",
    description:
      "🎭 **{user}** izgubio/la ulogu **{role}**.",
    color: "#d946ef",
    category: "Reaction Roles",
    footer: "GIANNI (Custom) • Reaction Roles",
    thumbnail: null,
    fields: [],
  },
]


async function loadEmbeds(): Promise<typeof DEFAULT_EMBEDS> {
  const conn = await getDb();
  if (!conn) return DEFAULT_EMBEDS;

  const { db, embedsTable } = conn;
  const rows = await db.select().from(embedsTable);
  const savedMap = new Map(rows.map((r) => [r.name, r.data as (typeof DEFAULT_EMBEDS)[number]]));

  // Seed any defaults not yet in DB
  const missing = DEFAULT_EMBEDS.filter((e) => !savedMap.has(e.name));
  if (missing.length > 0) {
    await db.insert(embedsTable)
      .values(missing.map((e) => ({ name: e.name, data: e })))
      .onConflictDoNothing();
    missing.forEach((e) => savedMap.set(e.name, e));
  }

  return DEFAULT_EMBEDS.map((def) => savedMap.get(def.name) ?? def);
}

router.get("/embeds", async (req, res) => {
  try {
    res.json(await loadEmbeds());
  } catch (err) {
    req.log.error(err, "Failed to load embeds");
    res.json(DEFAULT_EMBEDS);
  }
});

router.get("/embeds/:name", async (req, res) => {
  try {
    const conn = await getDb();
    if (conn) {
      const { db, embedsTable } = conn;
      const rows = await db.select().from(embedsTable).where(eq(embedsTable.name, req.params.name));
      if (rows.length > 0) return res.json(rows[0].data);
    }
    const def = DEFAULT_EMBEDS.find((e) => e.name === req.params.name);
    if (!def) return res.status(404).json({ error: "Embed not found" });
    return res.json(def);
  } catch (err) {
    req.log.error(err, "Failed to get embed");
    const def = DEFAULT_EMBEDS.find((e) => e.name === req.params.name);
    return def ? res.json(def) : res.status(404).json({ error: "Embed not found" });
  }
});

router.post("/embeds/reset-all", async (req, res) => {
  try {
    const conn = await getDb();
    if (!conn) return res.status(503).json({ error: "Database not available" });

    const { db, embedsTable } = conn;

    for (const embed of DEFAULT_EMBEDS) {
      await db.insert(embedsTable)
        .values({ name: embed.name, data: embed })
        .onConflictDoUpdate({
          target: embedsTable.name,
          set: { data: embed, updatedAt: new Date() },
        });
    }

    return res.json({ ok: true, updated: DEFAULT_EMBEDS.length });
  } catch (err) {
    req.log.error(err, "Failed to reset all embeds");
    return res.status(500).json({ error: "Database error" });
  }
});

router.put("/embeds/:name", async (req, res) => {
  try {
    const existing = DEFAULT_EMBEDS.find((e) => e.name === req.params.name);
    if (!existing) return res.status(404).json({ error: "Embed not found" });

    const conn = await getDb();
    if (!conn) {
      // No DB — return merged but warn it won't persist
      return res.json({ ...existing, ...req.body });
    }

    const { db, embedsTable } = conn;
    const rows = await db.select().from(embedsTable).where(eq(embedsTable.name, req.params.name));
    const current = rows.length > 0 ? (rows[0].data as (typeof DEFAULT_EMBEDS)[number]) : existing;
    const updated = { ...current, ...req.body };

    await db.insert(embedsTable)
      .values({ name: req.params.name, data: updated })
      .onConflictDoUpdate({ target: embedsTable.name, set: { data: updated, updatedAt: new Date() } });

    return res.json(updated);
  } catch (err) {
    req.log.error(err, "Failed to save embed");
    return res.status(500).json({ error: "Database error" });
  }
});

export default router;
