import React, { useState, useRef, useEffect, useCallback, useMemo } from "react";
import emojiRegex from "emoji-regex";
import { useListEmbeds, useUpdateEmbed, getListEmbedsQueryKey } from "@workspace/api-client-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Save, Smile, X, Search, RefreshCw, LayoutTemplate, Maximize2, Minimize2, AtSign, Send, ChevronDown,
  Settings, ScrollText, Shield, Zap, DollarSign, Gamepad2, Sparkles, Heart,
  Info, Music, BadgeCheck, BarChart2, Tag, Flame, Star, Archive, Wrench, Leaf,
  UserPlus, UserMinus, LogOut, MessageCircle, Rocket, Gift, Crown, Ticket,
  CheckCircle, ClipboardList, Mic, AlertTriangle, Ban, UserX, VolumeX, Volume2,
  Clock, TrendingUp, Activity, Trophy, Target, ListChecks, Layers, Users, BookOpen,
  Grid3x3, Hash, HelpCircle, Globe, Bird, Swords, MessageSquare, HeartHandshake,
  Hand, Diamond, User, Wallet, Briefcase, ShoppingCart, ShoppingBag, ArrowLeftRight,
  AlertOctagon, Play, ListMusic, SkipForward, Pause, Square, ShieldCheck, ShieldX,
  Plus, Minus, RotateCcw, Database, FileText, PencilLine, Trash2, UserCheck,
  type LucideIcon,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import type { EmbedTemplate, EmbedField } from "@workspace/api-client-react";

const EMBED_DISPLAY_NAMES: Record<string, string> = {
  // Sistem
  welcome:          "Dobrodošao na server",
  leave:            "Clan je napustio server",
  "dm-welcome":     "DM Dobrodošlica",
  boost:            "Novi Boost!",
  birthday:         "Sretan Rođendan!",
  starboard:        "Zvjezdana poruka",
  aotw:             "Aktivni Član Sedmice",
  // Log
  "log-join":       "Novi Član (Log)",
  "log-edit":       "Poruka Editovana",
  "log-delete":     "Poruka Obrisana",
  report:           "Prijava člana",
  // Moderacija
  warn:             "Upozorenje",
  ban:              "Član Banovan",
  // XP
  levelup:          "Level Up!",
  "vatrica-nova":   "Nova Vatrica!",
  aktivnost:        "Aktivnost",
  rank:             "Rank Profil",
  "leaderboard-xp":     "Top Lista — XP",
  "leaderboard-novac":  "Top Lista — Novac",
  // Ekonomija
  heist:            "Razboj u pripremi",
  lottery:          "Sedmična Loto",
  quests:           "Dnevni Zadaci",
  giveaway:         "Nagradna Igra",
  // Igre
  slots:            "Slot Mašina",
  blackjack:        "Blackjack",
  "poker-lobby":    "Poker — Lobby",
  "poker-game":     "Poker — Igra",
  "poker-showdown": "Poker — Showdown",
  "among-us-lobby": "Among Us — Lobby",
  "among-us-game":  "Among Us — U Toku",
  "among-us-end":   "Among Us — Kraj",
  "kaladont-start":  "Kaladont — Start",
  "kaladont-active": "Kaladont — Aktivan",
  "kaladont-word":   "Kaladont — Riječ",
  "kaladont-win":    "Kaladont — Pobjeda",
  bingo:            "Bingo",
  // Fun
  hunt:             "Lov — Ulovio životinju",
  zoo:              "Zoo — Zbirka",
  battle:           "Bitka",
  pray:             "Molitva",
  vers:             "Vers — Hip Hop",
  kompli:           "Kompliment",
  fora:             "Fora",
  muv:              "Muv",
  crush:            "Crush",
  // Ljubavne
  zagrljaj:         "Zagrljaj",
  poljubac:         "Poljubac",
  mazi:             "Mazi",
  tapsi:            "Tapsi",
  high5:            "High Five",
  cudan:            "Ćudan",
  srce:             "Srce",
  brak:             "Brak / Prosidba",
  // Info
  spotify:          "Spotify",
  invite:           "Statistika",
  avatar:           "Avatar",
  "brojanje-info":  "Brojanje — stanje",
  // Sistem paneli
  ticket:           "Tiket — Panel",
  "ticket-otvoren": "Tiket — Otvoren",
  "staff-prijava":  "Staff Prijava",
  "private-vc":     "Privatni Voice Kanal",
  "voice-pravila":  "Voice Pravila — Panel",
  // Vatrice
  "vatrice-pup":    "Top Lista Vatrica",
  "vatrice-start":  "Vatrica Sistem — Start",
  "vatrice-kanal":  "Vatrica Kanal Postavljen",
  "vatrice-oblik":  "Vatrica Emoji Promijenjen",
  // Ekonomija (dopune)
  "giveaway-end":   "Nagradna Igra — Završena",
  // Igre (dopune)
  "vjasala":        "Vješala — Igra",
  "vjasala-kraj":   "Vješala — Pogodak!",
  "toplo-hladno":   "Toplo ili Hladno",
  "kviz":           "Kviz — Balkan Pitanje",
  "geografija":     "Geografija Kviz",
  "mafia-lobby":    "Mafia — Lobby",
  "mafia-end":      "Mafia — Kraj Igre",
  // Poo
  "poo":            "Poo — Stanje Kreature 💩",
  "poo-zadaci":     "Poo — Zadaci 📋",
  "poo-top":        "Poo — Top Čuvari 🏆",
  "poo-hrani":      "Poo — Hranjen! 🍖",
  "poo-info":       "Poo — Moj Doprinos 📊",
  // Admin
  "backup":         "Backup — Snimljen 💾",
  "backup-restore": "Backup — Vraćen ♻️",
  "backup-status":  "Backup — Status 📊",
  "report-closed":  "Report Zatvoren",
  "report-nova":    "Nova Prijava — Report",
  // Moderacija (kompletno)
  "mod-kick":       "Član Kickovan",
  "mod-mute":       "Član Mutovan",
  "mod-unmute":     "Član Odmutovan",
  "mod-timeout":    "Timeout",
  "mod-purge":      "Poruke Obrisane (Purge)",
  "mod-unban":      "Član Odbanovan",
  // Ekonomija (kompletno)
  "eco-balance":    "Balans",
  "eco-daily":      "Dnevna Nagrada",
  "eco-work":       "Posao",
  "eco-shop":       "Shop",
  "eco-buy":        "Kupovina Uspješna",
  "eco-transfer":   "Transfer Kovanica",
  "eco-rob":        "Pljačka",
  // Muzika
  "music-play":     "Reprodukcija — Now Playing",
  "music-queue":    "Red Čekanja",
  "music-skip":     "Preskočeno",
  "music-pause":    "Pauzirano",
  "music-stop":     "Zaustavljeno",
  "music-lyrics":   "Tekst Pjesme",
  // Verifikacija
  "verify-panel":   "Verifikacija — Panel",
  "verify-success": "Verifikacija — Uspješna",
  "verify-fail":    "Verifikacija — Neuspješna",
  // Ankete
  "poll-create":    "Anketa — Nova",
  "poll-results":   "Anketa — Rezultati",
  // Reaction Roles
  "rr-panel":       "Reaction Roles — Panel",
  "rr-add":         "Reaction Roles — Uloga Dodana",
  "rr-remove":      "Reaction Roles — Uloga Skinuta",
};

/** Lucide icon per embed name */
const EMBED_ICONS: Record<string, LucideIcon> = {
  // Sistem
  welcome:            UserPlus,
  leave:              LogOut,
  "dm-welcome":       MessageCircle,
  boost:              Rocket,
  birthday:           Gift,
  starboard:          Star,
  aotw:               Crown,
  ticket:             Ticket,
  "ticket-otvoren":   CheckCircle,
  "staff-prijava":    ClipboardList,
  "private-vc":       Mic,
  "voice-pravila":    ScrollText,
  // Log
  "log-join":         UserPlus,
  "log-edit":         PencilLine,
  "log-delete":       Trash2,
  report:             AlertTriangle,
  "report-closed":    CheckCircle,
  "report-nova":      AlertTriangle,
  // Moderacija
  warn:               AlertTriangle,
  ban:                Ban,
  "mod-kick":         UserX,
  "mod-mute":         VolumeX,
  "mod-unmute":       Volume2,
  "mod-timeout":      Clock,
  "mod-purge":        Trash2,
  "mod-unban":        UserCheck,
  // XP
  levelup:            TrendingUp,
  "vatrica-nova":     Flame,
  aktivnost:          Activity,
  rank:               BarChart2,
  "leaderboard-xp":   Trophy,
  "leaderboard-novac": DollarSign,
  // Ekonomija
  heist:              Target,
  lottery:            Ticket,
  quests:             ListChecks,
  giveaway:           Gift,
  "giveaway-end":     Trophy,
  "eco-balance":      Wallet,
  "eco-daily":        Star,
  "eco-work":         Briefcase,
  "eco-shop":         ShoppingCart,
  "eco-buy":          ShoppingBag,
  "eco-transfer":     ArrowLeftRight,
  "eco-rob":          AlertOctagon,
  // Igre
  slots:              Layers,
  blackjack:          Layers,
  "poker-lobby":      Layers,
  "poker-game":       Layers,
  "poker-showdown":   Crown,
  "among-us-lobby":   Users,
  "among-us-game":    Users,
  "among-us-end":     CheckCircle,
  "kaladont-start":   BookOpen,
  "kaladont-active":  BookOpen,
  "kaladont-word":    BookOpen,
  "kaladont-win":     Trophy,
  bingo:              Grid3x3,
  "vjasala":          Hash,
  "vjasala-kraj":     CheckCircle,
  "toplo-hladno":     HelpCircle,
  kviz:               HelpCircle,
  geografija:         Globe,
  "mafia-lobby":      Users,
  "mafia-end":        Crown,
  // Fun
  hunt:               Target,
  zoo:                Bird,
  battle:             Swords,
  pray:               Star,
  vers:               Music,
  kompli:             MessageSquare,
  fora:               Smile,
  muv:                Heart,
  crush:              HeartHandshake,
  // Ljubavne
  zagrljaj:           HeartHandshake,
  poljubac:           Heart,
  mazi:               Smile,
  tapsi:              Hand,
  high5:              Star,
  cudan:              HelpCircle,
  srce:               Heart,
  brak:               Diamond,
  // Info
  spotify:            Music,
  invite:             BarChart2,
  avatar:             User,
  "brojanje-info":    Hash,
  // Vatrice
  "vatrice-pup":      Trophy,
  "vatrice-start":    Flame,
  "vatrice-kanal":    Flame,
  "vatrice-oblik":    Flame,
  // Poo
  poo:                Leaf,
  "poo-zadaci":       ListChecks,
  "poo-top":          Trophy,
  "poo-hrani":        Heart,
  "poo-info":         BarChart2,
  // Admin
  backup:             Archive,
  "backup-restore":   RotateCcw,
  "backup-status":    Database,
  // Muzika
  "music-play":       Play,
  "music-queue":      ListMusic,
  "music-skip":       SkipForward,
  "music-pause":      Pause,
  "music-stop":       Square,
  "music-lyrics":     FileText,
  // Verifikacija
  "verify-panel":     ShieldCheck,
  "verify-success":   BadgeCheck,
  "verify-fail":      ShieldX,
  // Ankete
  "poll-create":      BarChart2,
  "poll-results":     Trophy,
  // Reaction Roles
  "rr-panel":         Tag,
  "rr-add":           Plus,
  "rr-remove":        Minus,
};

/** Lucide icon per category */
const EMBED_CAT_ICONS: Record<string, LucideIcon> = {
  "Sistem":          Settings,
  "Log":             ScrollText,
  "Moderacija":      Shield,
  "XP":              Zap,
  "Ekonomija":       DollarSign,
  "Igre":            Gamepad2,
  "Fun":             Sparkles,
  "Ljubavne":        Heart,
  "Info":            Info,
  "Muzika":          Music,
  "Verifikacija":    BadgeCheck,
  "Ankete":          BarChart2,
  "Reaction Roles":  Tag,
  "Admin":           Wrench,
  "Vatrice":         Flame,
  "Poo":             Leaf,
  "Sistem paneli":   LayoutTemplate,
};

interface DiscordEmoji {
  id: string;
  name: string;
  animated: boolean;
}

const EMBED_CATEGORY_COLORS: Record<string, string> = {
  "Sistem":          "#6366f1",
  "Log":             "#f59e0b",
  "Moderacija":      "#ef4444",
  "XP":              "#22c55e",
  "Ekonomija":       "#f97316",
  "Igre":            "#3b82f6",
  "Fun":             "#ec4899",
  "Ljubavne":        "#e879f9",
  "Info":            "#14b8a6",
  "Sistem paneli":   "#a78bfa",
  "Vatrice":         "#FF6A00",
  "Poo":             "#92400e",
  "Admin":           "#64748b",
  "Muzika":          "#8b5cf6",
  "Verifikacija":    "#06b6d4",
  "Ankete":          "#f43f5e",
  "Reaction Roles":  "#d946ef",
};

function getCategoryColor(cat: string) {
  return EMBED_CATEGORY_COLORS[cat] ?? "#6366f1";
}

const BASE_URL = import.meta.env.BASE_URL.replace(/\/$/, "");

function useDiscordEmojis() {
  return useQuery<DiscordEmoji[]>({
    queryKey: ["discord-emojis"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/discord/emojis`);
      if (!res.ok) throw new Error("Failed to fetch emojis");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

async function forceRefreshEmojis(): Promise<number> {
  const res = await fetch(`${BASE_URL}/api/discord/emojis?refresh=1`);
  if (!res.ok) throw new Error("Refresh failed");
  const data = await res.json();
  return Array.isArray(data) ? data.length : 0;
}

function emojiUrl(emoji: DiscordEmoji) {
  const ext = emoji.animated ? "gif" : "png";
  return `https://cdn.discordapp.com/emojis/${emoji.id}.${ext}?size=32`;
}

function emojiMarkdown(emoji: DiscordEmoji) {
  return emoji.animated ? `<a:${emoji.name}:${emoji.id}>` : `<:${emoji.name}:${emoji.id}>`;
}

interface EmojiPickerProps {
  onSelect: (markdown: string) => void;
  onClose: () => void;
}

function EmojiPicker({ onSelect, onClose }: EmojiPickerProps) {
  const { data: emojis, isLoading, isError } = useDiscordEmojis();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [onClose]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const count = await forceRefreshEmojis();
      setRefreshMsg(`✅ ${count} emojia učitano`);
      qc.invalidateQueries({ queryKey: ["discord-emojis"] });
    } catch {
      setRefreshMsg("❌ Greška — pokušaj ponovo");
    } finally {
      setRefreshing(false);
    }
  };

  // Split animated vs static for display
  const animated = emojis?.filter(e => e.animated) ?? [];
  const staticEmojis = emojis?.filter(e => !e.animated) ?? [];

  const filterFn = (e: DiscordEmoji) =>
    !search || e.name.toLowerCase().includes(search.toLowerCase());

  const filteredAnimated = animated.filter(filterFn);
  const filteredStatic = staticEmojis.filter(filterFn);
  const filtered = [...filteredAnimated, ...filteredStatic];

  return (
    <div
      ref={ref}
      className="absolute z-50 bottom-full mb-2 left-0 w-80 bg-[#1E1F22] border border-[#2B2D31] rounded-lg shadow-2xl overflow-hidden"
      data-testid="emoji-picker"
    >
      {/* Search row */}
      <div className="p-2 border-b border-[#2B2D31] flex items-center gap-1">
        <div className="flex items-center gap-2 bg-[#313338] rounded px-2 flex-1">
          <Search className="w-3.5 h-3.5 text-[#949BA4] flex-shrink-0" />
          <input
            autoFocus
            placeholder="Pretraži emoji..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm text-[#F2F3F5] placeholder:text-[#949BA4] py-1.5 outline-none"
            data-testid="input-emoji-search"
          />
          {search && (
            <button onClick={() => setSearch("")} className="text-[#949BA4] hover:text-[#F2F3F5]">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          title="Osvježi emojie (učitaj sve sa Dev Portala)"
          className="p-1.5 rounded text-[#949BA4] hover:text-[#F1C40F] hover:bg-[#313338] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Refresh message */}
      {refreshMsg && (
        <div className="px-3 py-1.5 text-[11px] text-center border-b border-[#2B2D31]"
          style={{ color: refreshMsg.startsWith("✅") ? "#43B581" : "#E74C3C" }}>
          {refreshMsg}
        </div>
      )}

      <div className="overflow-y-auto" style={{ maxHeight: "240px" }}>
        {isLoading && (
          <div className="flex items-center justify-center h-24 text-[#949BA4] text-sm">
            Učitavam emoji-je...
          </div>
        )}
        {isError && (
          <div className="flex items-center justify-center h-24 text-red-400 text-sm text-center px-4">
            Greška — klikni ↺ za ponovni pokušaj
          </div>
        )}

        {/* Animated GIF section */}
        {filteredAnimated.length > 0 && (
          <div className="p-2">
            <div className="text-[10px] text-[#949BA4] uppercase tracking-wider mb-1 px-1">
              GIF Emojii ({filteredAnimated.length})
            </div>
            <div className="grid grid-cols-9 gap-0.5">
              {filteredAnimated.map(emoji => (
                <button
                  key={emoji.id}
                  title={`:${emoji.name}:`}
                  data-testid={`emoji-${emoji.name}`}
                  onClick={() => { onSelect(emojiMarkdown(emoji)); onClose(); }}
                  className="w-8 h-8 flex items-center justify-center rounded hover:bg-[#313338] transition-colors"
                >
                  <img src={emojiUrl(emoji)} alt={emoji.name} className="w-6 h-6 object-contain" loading="lazy" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Static section */}
        {filteredStatic.length > 0 && (
          <div className="p-2 border-t border-[#2B2D31]">
            <div className="text-[10px] text-[#949BA4] uppercase tracking-wider mb-1 px-1">
              Statični ({filteredStatic.length})
            </div>
            <div className="grid grid-cols-9 gap-0.5">
              {filteredStatic.map(emoji => (
                <button
                  key={emoji.id}
                  title={`:${emoji.name}:`}
                  data-testid={`emoji-${emoji.name}`}
                  onClick={() => { onSelect(emojiMarkdown(emoji)); onClose(); }}
                  className="w-8 h-8 flex items-center justify-center rounded hover:bg-[#313338] transition-colors"
                >
                  <img src={emojiUrl(emoji)} alt={emoji.name} className="w-6 h-6 object-contain" loading="lazy" />
                </button>
              ))}
            </div>
          </div>
        )}

        {!isLoading && !isError && filtered.length === 0 && (
          <div className="flex items-center justify-center h-20 text-[#949BA4] text-sm">
            Nema rezultata
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-1.5 border-t border-[#2B2D31] text-[10px] text-[#949BA4] flex items-center justify-between">
        <span>{filtered.length}{emojis ? ` / ${emojis.length}` : ""} emoji-ja</span>
        {emojis && emojis.length < 500 && (
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="text-[#5865F2] hover:underline disabled:opacity-50"
          >
            {refreshing ? "Osvježavam..." : "↺ Učitaj sve"}
          </button>
        )}
      </div>
    </div>
  );
}

// ── Mention Picker ───────────────────────────────────────────────────────────

const CHANNEL_TYPE_ICON: Record<number, string> = {
  0: "#",   // text
  2: "🔊",  // voice
  5: "📢",  // announcement
  15: "📋", // forum
  13: "🎙️", // stage
};

interface MentionPickerProps {
  onSelect: (markdown: string) => void;
  onClose: () => void;
}

function MentionPicker({ onSelect, onClose }: MentionPickerProps) {
  const { data: channelData, isLoading: chLoading } = useDiscordChannels();
  const { data: roles, isLoading: rLoading } = useDiscordRoles();
  const [tab, setTab] = useState<"channels" | "roles">("channels");
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [onClose]);

  const allChannels = useMemo(() => [
    ...(channelData?.categories?.flatMap(c => c.channels) ?? []),
    ...(channelData?.uncategorized ?? []),
  ].filter(c => [0, 2, 5, 15, 13].includes(c.type)), [channelData]);

  const filteredChannels = useMemo(() =>
    !search ? allChannels : allChannels.filter(c => c.name.toLowerCase().includes(search.toLowerCase())),
  [allChannels, search]);

  const filteredRoles = useMemo(() =>
    !search ? (roles ?? []) : (roles ?? []).filter(r => r.name.toLowerCase().includes(search.toLowerCase())),
  [roles, search]);

  const tabBtn = (active: boolean) =>
    `flex-1 py-2 text-xs font-semibold transition-colors ${
      active
        ? "text-[#F2F3F5] border-b-2 border-[#5865F2]"
        : "text-[#949BA4] hover:text-[#DBDEE1] border-b-2 border-transparent"
    }`;

  return (
    <div
      ref={ref}
      className="absolute z-50 bottom-full mb-2 left-0 w-72 bg-[#1E1F22] border border-[#2B2D31] rounded-lg shadow-2xl overflow-hidden"
    >
      {/* Tabs */}
      <div className="flex border-b border-[#2B2D31]">
        <button className={tabBtn(tab === "channels")} onClick={() => setTab("channels")}>
          # Kanali
        </button>
        <button className={tabBtn(tab === "roles")} onClick={() => setTab("roles")}>
          @ Uloge
        </button>
      </div>

      {/* Search */}
      <div className="p-2 border-b border-[#2B2D31]">
        <div className="flex items-center gap-2 bg-[#313338] rounded px-2">
          <Search className="w-3.5 h-3.5 text-[#949BA4] flex-shrink-0" />
          <input
            autoFocus
            placeholder={tab === "channels" ? "Pretraži kanale..." : "Pretraži uloge..."}
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm text-[#F2F3F5] placeholder:text-[#949BA4] py-1.5 outline-none"
          />
          {search && (
            <button onClick={() => setSearch("")} className="text-[#949BA4] hover:text-[#F2F3F5]">
              <X className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="overflow-y-auto" style={{ maxHeight: "220px" }}>
        {tab === "channels" && (
          <>
            {chLoading && (
              <div className="flex items-center justify-center h-16 text-[#949BA4] text-sm">Učitavam kanale...</div>
            )}
            {!chLoading && filteredChannels.length === 0 && (
              <div className="flex items-center justify-center h-16 text-[#949BA4] text-sm">Nema kanala</div>
            )}
            {filteredChannels.map(ch => (
              <button
                key={ch.id}
                onClick={() => { onSelect(`<#${ch.id}>`); onClose(); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-[#313338] text-left transition-colors"
              >
                <span className="text-[#949BA4] text-sm w-4 flex-shrink-0 text-center">
                  {CHANNEL_TYPE_ICON[ch.type] ?? "#"}
                </span>
                <span className="text-sm text-[#DBDEE1] truncate">{ch.name}</span>
                <span className="ml-auto text-[10px] text-[#5C5F66] flex-shrink-0">{ch.id.slice(-4)}</span>
              </button>
            ))}
          </>
        )}

        {tab === "roles" && (
          <>
            {/* Special mentions */}
            <div className="px-3 py-1 text-[10px] text-[#5C5F66] uppercase tracking-wider font-semibold">Posebno</div>
            {["@everyone", "@here"].map(m => (
              <button
                key={m}
                onClick={() => { onSelect(m); onClose(); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-[#313338] text-left transition-colors"
              >
                <div className="w-2.5 h-2.5 rounded-full bg-[#5865F2] flex-shrink-0" />
                <span className="text-sm text-[#DBDEE1]">{m}</span>
              </button>
            ))}
            {(roles ?? []).length > 0 && (
              <div className="px-3 py-1 mt-1 text-[10px] text-[#5C5F66] uppercase tracking-wider font-semibold border-t border-[#2B2D31]">
                Uloge ({filteredRoles.length})
              </div>
            )}
            {rLoading && (
              <div className="flex items-center justify-center h-16 text-[#949BA4] text-sm">Učitavam uloge...</div>
            )}
            {filteredRoles.map(role => (
              <button
                key={role.id}
                onClick={() => { onSelect(`<@&${role.id}>`); onClose(); }}
                className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-[#313338] text-left transition-colors"
              >
                <div
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ background: role.color && role.color !== "#000000" ? role.color : "#99AAB5" }}
                />
                <span className="text-sm text-[#DBDEE1] truncate">@{role.name}</span>
                <span className="ml-auto text-[10px] text-[#5C5F66] flex-shrink-0">{role.id.slice(-4)}</span>
              </button>
            ))}
          </>
        )}
      </div>

      <div className="px-3 py-1.5 border-t border-[#2B2D31] text-[10px] text-[#5C5F66]">
        {tab === "channels" ? `${filteredChannels.length} kanala` : `${filteredRoles.length} uloga`}
      </div>
    </div>
  );
}

// ── Emoji token detection ────────────────────────────────────────────────────

interface EmojiToken {
  raw: string;       // original text matched
  index: number;     // start position in string
  isCustom: boolean;
  isAnimated: boolean;
  id?: string;
  name?: string;
}

/** Find all emojis (Unicode + custom Discord) in a string with their positions */
function findEmojisInText(text: string): EmojiToken[] {
  const results: EmojiToken[] = [];

  // 1. Discord custom emoji: <:name:id>  or  <a:name:id>
  const customRe = /<(a?):([^:>\s]+):(\d+)>/g;
  let m: RegExpExecArray | null;
  while ((m = customRe.exec(text)) !== null) {
    results.push({
      raw: m[0],
      index: m.index,
      isCustom: true,
      isAnimated: m[1] === "a",
      id: m[3],
      name: m[2],
    });
  }

  // 2. Unicode emoji — use \p{Emoji_Presentation} (u flag, supported in modern browsers)
  try {
    const unicodeRe = /\p{Emoji_Presentation}(?:\uFE0F|\u20E3)?(?:\u200D\p{Emoji_Presentation}(?:\uFE0F|\u20E3)?)*/gu;
    while ((m = unicodeRe.exec(text)) !== null) {
      const idx = m.index;
      // Skip if this position falls inside a custom emoji token already found
      const inCustom = results.some(
        r => r.isCustom && idx >= r.index && idx < r.index + r.raw.length
      );
      if (!inCustom) {
        results.push({
          raw: m[0],
          index: idx,
          isCustom: false,
          isAnimated: false,
        });
      }
    }
  } catch {}

  return results.sort((a, b) => a.index - b.index);
}

/** Replace one token in the text with new markdown */
function replaceToken(text: string, token: EmojiToken, replacement: string): string {
  return text.slice(0, token.index) + replacement + text.slice(token.index + token.raw.length);
}

// ── Inline emoji rendering helper (standalone, no component state needed) ───

function renderInlineEmojis(text: string): React.JSX.Element[] {
  if (!text) return [];
  const parts = text.split(/(<a?:[^:]+:\d+>)/g);
  return parts.flatMap((part, i): React.JSX.Element[] => {
    const m = part.match(/^<(a?):([^:]+):(\d+)>$/);
    if (m) {
      const animated = m[1] === "a";
      const name = m[2];
      const id = m[3];
      return [
        <img
          key={i}
          src={`https://cdn.discordapp.com/emojis/${id}.${animated ? "gif" : "png"}?size=32`}
          alt={`:${name}:`}
          title={`:${name}:`}
          className="inline-block w-5 h-5 object-contain align-middle"
        />,
      ];
    }
    if (!part) return [];
    return [<span key={i} className="align-middle">{part}</span>];
  });
}

// ── Inline emoji chip + mini-picker ─────────────────────────────────────────

interface EmojiChipProps {
  token: EmojiToken;
  onReplace: (newMarkdown: string) => void;
}

function EmojiChip({ token, onReplace }: EmojiChipProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const display = token.isCustom && token.id ? (
    <img
      src={`https://cdn.discordapp.com/emojis/${token.id}.${token.isAnimated ? "gif" : "png"}?size=32`}
      alt={token.name}
      className="w-5 h-5 object-contain"
    />
  ) : (
    <span className="text-base leading-none">{token.raw}</span>
  );

  return (
    <div ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen(p => !p)}
        title="Zamijeni emoji"
        className={`flex items-center gap-1 px-1.5 py-0.5 rounded border text-[10px] font-medium transition-colors ${
          open
            ? "border-[#5865F2] bg-[#5865F2]/20 text-[#5865F2]"
            : "border-[#404249] bg-[#1E1F22] text-[#949BA4] hover:border-[#5865F2] hover:text-[#5865F2]"
        }`}
      >
        {display}
        <RefreshCw className="w-2.5 h-2.5 flex-shrink-0" />
      </button>
      {open && (
        <EmojiPicker
          onSelect={(md) => { onReplace(md); setOpen(false); }}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}

// ── TextFieldWithEmoji ───────────────────────────────────────────────────────

interface TextFieldWithEmojiProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  multiline?: boolean;
  testId: string;
}

function TextFieldWithEmoji({ label, value, onChange, multiline, testId }: TextFieldWithEmojiProps) {
  const [showPicker, setShowPicker] = useState(false);
  const [showMentionPicker, setShowMentionPicker] = useState(false);
  const inputRef = useRef<HTMLInputElement & HTMLTextAreaElement>(null);

  const tokens = useMemo(() => findEmojisInText(value ?? ""), [value]);

  const insertAtCursor = useCallback((markdown: string) => {
    const el = inputRef.current;
    if (!el) { onChange(value + markdown); return; }
    const start = el.selectionStart ?? value.length;
    const end = el.selectionEnd ?? value.length;
    const next = value.slice(0, start) + markdown + value.slice(end);
    onChange(next);
    requestAnimationFrame(() => {
      el.focus();
      const pos = start + markdown.length;
      el.setSelectionRange(pos, pos);
    });
  }, [value, onChange]);

  const replaceEmoji = useCallback((token: EmojiToken, newMarkdown: string) => {
    onChange(replaceToken(value ?? "", token, newMarkdown));
  }, [value, onChange]);

  const commonClass = "bg-[#1E1F22] border border-[#2B2D31] text-[#F2F3F5] placeholder:text-[#949BA4] focus:border-[#5865F2] focus:ring-0 rounded-md text-sm";

  const hasEmojis = tokens.length > 0;

  return (
    <div className="space-y-1.5">
      <Label className="text-[#B5BAC1] text-xs font-semibold uppercase tracking-wide">{label}</Label>

      {/* Inline rendered preview — shows emoji images mixed with text */}
      {hasEmojis && (
        <div className="bg-[#111214] border border-[#2B2D31] rounded-md px-3 py-2 text-sm text-[#F2F3F5] leading-6 min-h-[2rem] flex flex-wrap items-center gap-x-0 gap-y-1 break-words">
          {renderInlineEmojis(value ?? "")}
        </div>
      )}

      <div className="relative">
        {multiline ? (
          <Textarea
            ref={inputRef as React.Ref<HTMLTextAreaElement>}
            value={value ?? ""}
            onChange={e => onChange(e.target.value)}
            className={`${commonClass} h-28 resize-none pr-16`}
            data-testid={testId}
          />
        ) : (
          <Input
            ref={inputRef as React.Ref<HTMLInputElement>}
            value={value ?? ""}
            onChange={e => onChange(e.target.value)}
            className={`${commonClass} pr-16`}
            data-testid={testId}
          />
        )}
        <div className="absolute right-2 bottom-2 flex items-center gap-1">
          <button
            type="button"
            onClick={() => { setShowMentionPicker(p => !p); setShowPicker(false); }}
            className={`transition-colors ${showMentionPicker ? "text-[#5865F2]" : "text-[#949BA4] hover:text-[#5865F2]"}`}
            data-testid={`button-mention-${testId}`}
            title="Umetni tag (kanal/uloga)"
          >
            <AtSign className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => { setShowPicker(p => !p); setShowMentionPicker(false); }}
            className={`transition-colors ${showPicker ? "text-[#F1C40F]" : "text-[#949BA4] hover:text-[#F1C40F]"}`}
            data-testid={`button-emoji-${testId}`}
            title="Umetni emoji"
          >
            <Smile className="w-4 h-4" />
          </button>
        </div>

        {showPicker && (
          <EmojiPicker
            onSelect={insertAtCursor}
            onClose={() => setShowPicker(false)}
          />
        )}
        {showMentionPicker && (
          <MentionPicker
            onSelect={insertAtCursor}
            onClose={() => setShowMentionPicker(false)}
          />
        )}
      </div>

      {/* Emoji replace chips */}
      {hasEmojis && (
        <div className="flex flex-wrap gap-1 pt-0.5">
          <span className="text-[10px] text-[#5C5F66] self-center">zamijeni:</span>
          {tokens.map((token, i) => (
            <EmojiChip
              key={`${token.index}-${i}`}
              token={token}
              onReplace={(md) => replaceEmoji(token, md)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

type ButtonType = "voice_create" | "ticket_open" | "ticket_close" | "role" | "link" | "custom";

interface EmbedButton {
  type?: ButtonType;
  label: string;
  style: "primary" | "secondary" | "success" | "danger" | "link";
  emoji?: string;
  url?: string;
  channelId?: string;
  roleId?: string;
  customId?: string;
}

const BUTTON_TYPE_DEFAULTS: Record<ButtonType, Partial<EmbedButton>> = {
  voice_create:  { label: "🔊 Kreiraj svoj voice", style: "success",   customId: "vc_create_btn" },
  ticket_open:   { label: "🎫 Otvori Ticket",      style: "primary",   customId: "ticket_open" },
  ticket_close:  { label: "🔒 Zatvori Ticket",     style: "danger",    customId: "ticket_close" },
  role:          { label: "Uzmi ulogu",             style: "secondary"  },
  link:          { label: "Otvori link",            style: "link"       },
  custom:        { label: "Dugme",                  style: "primary"    },
};

const BUTTON_TYPE_LABELS: Record<ButtonType, string> = {
  voice_create: "🔊 Voice",
  ticket_open:  "🎫 Otvori Tiket",
  ticket_close: "🔒 Zatvori Tiket",
  role:         "🏷️ Uloga",
  link:         "🔗 Link",
  custom:       "⚙️ Custom",
};

const BUTTON_STYLE_COLORS: Record<string, string> = {
  primary:   "#5865F2",
  secondary: "#4E5058",
  success:   "#248046",
  danger:    "#DA373C",
  link:      "#4E5058",
};

interface DiscordRole { id: string; name: string; color: string; }

function useDiscordRoles() {
  return useQuery<DiscordRole[]>({
    queryKey: ["discord-roles"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/discord/roles`);
      if (!res.ok) throw new Error("Failed to fetch roles");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

interface DiscordChannel { id: string; name: string; type: number; }
interface DiscordChannelCategory { id: string; name: string; channels: DiscordChannel[]; }

function useDiscordChannels() {
  return useQuery<{ categories: DiscordChannelCategory[]; uncategorized: DiscordChannel[] }>({
    queryKey: ["discord-channels"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/discord/channels`);
      if (!res.ok) throw new Error("Failed to fetch channels");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}


function DiscordEmbedPreview({ embed, title, description, color, bgColor, previewMode, fields: fieldsProp, buttons: buttonsProp }: {
  embed: EmbedTemplate;
  title: string;
  description: string;
  color: string;
  bgColor?: string;
  previewMode?: "desktop" | "mobile";
  fields?: EmbedTemplate["fields"];
  buttons?: EmbedButton[];
}) {
  const { data: roles } = useDiscordRoles();
  const { data: channelData } = useDiscordChannels();

  const roleMap = useMemo(() => {
    const m: Record<string, DiscordRole> = {};
    for (const r of roles ?? []) m[r.id] = r;
    return m;
  }, [roles]);

  const channelMap = useMemo(() => {
    const m: Record<string, DiscordChannel> = {};
    for (const cat of channelData?.categories ?? []) for (const ch of cat.channels) m[ch.id] = ch;
    for (const ch of channelData?.uncategorized ?? []) m[ch.id] = ch;
    return m;
  }, [channelData]);

  function emojiToTwemojiUrl(emoji: string): string {
    const cps: string[] = [];
    let i = 0;
    while (i < emoji.length) {
      const cp = emoji.codePointAt(i)!;
      if (cp !== 0xfe0f) cps.push(cp.toString(16));
      i += cp > 0xffff ? 2 : 1;
    }
    return `https://cdn.jsdelivr.net/gh/jdecked/twemoji@15/assets/72x72/${cps.join("-")}.png`;
  }

  function renderMarkdownAndEmoji(text: string, keyPfx: string): React.JSX.Element[] {
    if (!text) return [];
    const mdPatterns: [RegExp, string][] = [
      [/\*\*(.+?)\*\*/s, "bold"],
      [/__(.+?)__/s, "underline"],
      [/~~(.+?)~~/s, "strike"],
      [/\*(.+?)\*/s, "italic"],
      [/_(.+?)_/s, "italic"],
      [/`([^`]+)`/, "code"],
      [/\|\|(.+?)\|\|/s, "spoiler"],
    ];
    let earliest: RegExpExecArray | null = null;
    let earliestType = "";
    for (const [pattern, type] of mdPatterns) {
      const m = pattern.exec(text);
      if (m && (earliest === null || m.index < earliest.index!)) {
        earliest = m;
        earliestType = type;
      }
    }
    if (earliest) {
      const before = text.slice(0, earliest.index!);
      const inner = earliest[1];
      const after = text.slice(earliest.index! + earliest[0].length);
      const result: React.JSX.Element[] = [];
      if (before) result.push(...renderMarkdownAndEmoji(before, keyPfx + "b"));
      const innerNodes = renderMarkdownAndEmoji(inner, keyPfx + "m");
      const innerEl: React.ReactNode = innerNodes.length === 1 ? innerNodes[0] : <React.Fragment key={keyPfx + "mf"}>{innerNodes}</React.Fragment>;
      if (earliestType === "bold") result.push(<strong key={keyPfx + "bd"}>{innerEl}</strong>);
      else if (earliestType === "underline") result.push(<u key={keyPfx + "u"}>{innerEl}</u>);
      else if (earliestType === "italic") result.push(<em key={keyPfx + "em"}>{innerEl}</em>);
      else if (earliestType === "strike") result.push(<del key={keyPfx + "del"}>{innerEl}</del>);
      else if (earliestType === "code") result.push(<code key={keyPfx + "code"} className="bg-[#2B2D31] px-1 rounded text-[#E3E5E8] font-mono text-[0.875em]">{inner}</code>);
      else if (earliestType === "spoiler") result.push(<span key={keyPfx + "sp"} className="bg-[#202225] text-[#202225] rounded px-0.5 select-none cursor-pointer hover:text-[#DBDEE1] hover:bg-[#2B2D31] transition-colors">{innerEl}</span>);
      if (after) result.push(...renderMarkdownAndEmoji(after, keyPfx + "a"));
      return result;
    }
    const emojiRe = emojiRegex();
    const nodes: React.JSX.Element[] = [];
    let last = 0;
    let idx = 0;
    let em: RegExpExecArray | null;
    emojiRe.lastIndex = 0;
    while ((em = emojiRe.exec(text)) !== null) {
      if (em.index > last) nodes.push(<span key={`${keyPfx}-t${idx++}`}>{text.slice(last, em.index)}</span>);
      const url = emojiToTwemojiUrl(em[0]);
      nodes.push(<img key={`${keyPfx}-e${idx++}`} src={url} alt={em[0]} title={em[0]} className="inline-block w-5 h-5 object-contain align-middle mx-px" />);
      last = em.index + em[0].length;
    }
    if (last < text.length) nodes.push(<span key={`${keyPfx}-t${idx++}`}>{text.slice(last)}</span>);
    return nodes.length ? nodes : [<span key={keyPfx}>{text}</span>];
  }

  function renderText(text: string): React.JSX.Element[] {
    const parts = text.split(/(<a?:[^:]+:\d+>|<#\d+>|<@&\d+>|<@!?\d+>|@everyone|@here)/g);
    return parts.flatMap((part, i): React.JSX.Element[] => {
      // Custom emoji
      const emojiMatch = part.match(/^<(a?):([^:]+):(\d+)>$/);
      if (emojiMatch) {
        const animated = emojiMatch[1] === "a";
        const name = emojiMatch[2];
        const id = emojiMatch[3];
        const ext = animated ? "gif" : "png";
        return [
          <img
            key={i}
            src={`https://cdn.discordapp.com/emojis/${id}.${ext}?size=32`}
            alt={`:${name}:`}
            title={`:${name}:`}
            className="inline-block w-5 h-5 object-contain align-middle mx-0.5"
          />,
        ];
      }
      // Channel mention <#id>
      const chMatch = part.match(/^<#(\d+)>$/);
      if (chMatch) {
        const ch = channelMap[chMatch[1]];
        return [
          <span key={i} className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-[#5865F2]/20 text-[#5865F2] font-medium text-[0.85em] cursor-default hover:bg-[#5865F2]/30 transition-colors">
            <span className="text-[#7289DA]">#</span>{ch ? ch.name : chMatch[1]}
          </span>,
        ];
      }
      // Role mention <@&id>
      const roleMatch = part.match(/^<@&(\d+)>$/);
      if (roleMatch) {
        const role = roleMap[roleMatch[1]];
        const roleColor = role?.color && role.color !== "#000000" ? role.color : "#99AAB5";
        return [
          <span
            key={i}
            className="inline-flex items-center px-1 py-0.5 rounded font-medium text-[0.85em] cursor-default transition-colors"
            style={{ background: roleColor + "33", color: roleColor }}
            title={role ? `@${role.name}` : roleMatch[1]}
          >
            @{role ? role.name : roleMatch[1]}
          </span>,
        ];
      }
      // User mention <@id> or <@!id>
      const userMatch = part.match(/^<@!?(\d+)>$/);
      if (userMatch) {
        return [
          <span key={i} className="inline-flex items-center px-1 py-0.5 rounded bg-[#5865F2]/20 text-[#5865F2] font-medium text-[0.85em] cursor-default hover:bg-[#5865F2]/30 transition-colors">
            @{userMatch[1]}
          </span>,
        ];
      }
      // @everyone / @here
      if (part === "@everyone" || part === "@here") {
        return [
          <span key={i} className="inline-flex items-center px-1 py-0.5 rounded bg-[#F0B132]/20 text-[#F0B132] font-medium text-[0.85em] cursor-default">
            {part}
          </span>,
        ];
      }
      return renderMarkdownAndEmoji(part, String(i));
    });
  }

  const isMobile = previewMode === "mobile";

  return (
    <div
      className="bg-[#313338] rounded-lg p-4 transition-all duration-300"
      style={{ maxWidth: isMobile ? 340 : "100%" }}
    >
      {/* Device label */}
      {isMobile && (
        <div className="flex justify-center mb-2">
          <span className="text-[10px] text-[#949BA4] bg-[#1E1F22] px-2 py-0.5 rounded-full tracking-wider">
            📱 Mobile prikaz
          </span>
        </div>
      )}

      {/* Message row */}
      <div className="flex gap-3">
        <div className={`${isMobile ? "w-8 h-8 text-xs" : "w-10 h-10 text-sm"} rounded-full bg-[#F1C40F] flex-shrink-0 flex items-center justify-center font-bold text-black select-none`}>
          G
        </div>
        <div className="flex-1 min-w-0">
          <div className={`flex ${isMobile ? "flex-col gap-0" : "items-baseline gap-2"} mb-1`}>
            <div className="flex items-center gap-1.5">
              <span className={`font-medium text-[#F2F3F5] ${isMobile ? "text-[13px]" : "text-sm"}`}>GIANNI (Custom)</span>
              <span className="bg-[#5865F2] text-white text-[9px] px-1 py-px rounded font-bold uppercase leading-none tracking-wide">
                BOT
              </span>
            </div>
            <span className={`${isMobile ? "text-[10px]" : "text-[11px]"} text-[#949BA4]`}>Danas u 12:00</span>
          </div>

          {/* Embed card — matches Discord layout exactly */}
          {(() => {
            const thumb = embed.thumbnail ?? null;
            let thumbnailEl: React.ReactNode = null;
            if (thumb) {
              if (thumb.startsWith("http")) {
                const resolvedSrc = thumb.replace(
                  /^https?:\/\/gian\.today\//,
                  `${window.location.origin}/`
                );
                thumbnailEl = (
                  <img
                    src={resolvedSrc}
                    alt="thumbnail"
                    className="rounded object-cover flex-shrink-0"
                    style={{ width: 56, height: 56 }}
                    onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
                  />
                );
              } else {
                thumbnailEl = (
                  <div
                    className="rounded-full bg-[#4E5058] flex items-center justify-center flex-shrink-0 overflow-hidden"
                    style={{ width: 56, height: 56 }}
                    title={thumb}
                  >
                    <svg width={26} height={26} viewBox="0 0 24 24" fill="#B5BAC1">
                      <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
                    </svg>
                  </div>
                );
              }
            }

            return (
              <div
                className="rounded overflow-hidden inline-flex w-full mt-0.5"
                style={{
                  borderLeft: `4px solid ${color}`,
                  backgroundColor: bgColor ?? "#2B2D31",
                  maxWidth: isMobile ? 260 : 480,
                }}
              >
                <div className="p-3 flex-1 min-w-0 overflow-hidden">
                  <div className="flex gap-2">
                    <div className="flex-1 min-w-0 overflow-hidden">
                      {/* Title */}
                      {title && (
                        <div className="font-semibold text-[#F2F3F5] text-sm leading-snug mb-1 break-words">
                          {renderText(title)}
                        </div>
                      )}

                      {/* Description */}
                      {description && (
                        <div className="text-[#DBDEE1] text-sm leading-relaxed whitespace-pre-wrap mb-2 break-words overflow-hidden">
                          {renderText(description)}
                        </div>
                      )}

                      {/* Fields */}
                      {(() => {
                        const displayFields = (fieldsProp ?? embed.fields) ?? [];
                        return displayFields.length > 0 && (
                          <div className="grid gap-x-4 gap-y-2 mt-2" style={{
                            gridTemplateColumns: displayFields.every(f => f.inline)
                              ? "repeat(3, 1fr)"
                              : "1fr"
                          }}>
                            {displayFields.map((f, i) => (
                              <div key={i} className={f.inline ? "" : "col-span-full"}>
                                <div className="text-[12px] font-bold text-[#F2F3F5] mb-0.5">{renderText(f.name)}</div>
                                <div className="text-[12px] text-[#DBDEE1]">{renderText(f.value)}</div>
                              </div>
                            ))}
                          </div>
                        );
                      })()}
                    </div>

                    {/* Thumbnail — top right */}
                    {thumbnailEl && (
                      <div className="flex-shrink-0 pt-0.5">
                        {thumbnailEl}
                      </div>
                    )}
                  </div>

                  {/* Footer */}
                  {embed.footer && (
                    <div className="mt-3 pt-2 border-t border-white/5 text-[11px] text-[#949BA4] flex items-center gap-1.5 flex-wrap">
                      {renderText(embed.footer)}
                    </div>
                  )}
                </div>
              </div>
            );
          })()}

          {/* Buttons row — below embed card like Discord */}
          {buttonsProp && buttonsProp.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2" style={{ maxWidth: isMobile ? 260 : 480 }}>
              {buttonsProp.map((btn, i) => (
                <button
                  key={i}
                  type="button"
                  className="flex items-center gap-1.5 px-4 py-1.5 rounded text-white text-[13px] font-medium select-none cursor-default"
                  style={{ background: BUTTON_STYLE_COLORS[btn.style] ?? "#4E5058" }}
                >
                  {btn.emoji && <span>{btn.emoji}</span>}
                  {btn.style === "link" && (
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" className="opacity-70">
                      <path d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z"/>
                    </svg>
                  )}
                  <span>{btn.label || "Dugme"}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ButtonEditor({ buttons, onChange }: { buttons: EmbedButton[]; onChange: (b: EmbedButton[]) => void }) {
  const { data: roles } = useDiscordRoles();

  const add = () => {
    if (buttons.length >= 5) return;
    onChange([...buttons, { type: "custom", label: "Dugme", style: "primary" }]);
  };

  const remove = (i: number) => onChange(buttons.filter((_, idx) => idx !== i));

  const update = (i: number, patch: Partial<EmbedButton>) =>
    onChange(buttons.map((b, idx) => idx === i ? { ...b, ...patch } : b));

  const changeType = (i: number, type: ButtonType) => {
    const defaults = BUTTON_TYPE_DEFAULTS[type];
    onChange(buttons.map((b, idx) =>
      idx === i ? { ...b, type, ...defaults } : b
    ));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-[#B5BAC1] text-xs font-semibold uppercase tracking-wide">
          Dugmad
          <span className="ml-1.5 text-[10px] font-normal normal-case text-[#6b7280]">({buttons.length}/5)</span>
        </Label>
        {buttons.length < 5 && (
          <button
            type="button"
            onClick={add}
            className="flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-bold transition-all"
            style={{ background: "rgba(88,101,242,0.15)", border: "1px solid rgba(88,101,242,0.3)", color: "#a5b4fc" }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(88,101,242,0.25)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(88,101,242,0.15)"; }}
          >
            + Dodaj dugme
          </button>
        )}
      </div>

      {buttons.length === 0 && (
        <div className="text-[11px] text-[#4E5058] italic text-center py-3 rounded-md border border-dashed border-[#2B2D31]">
          Nema dugmadi — klikni + Dodaj dugme
        </div>
      )}

      {buttons.map((btn, i) => (
        <div key={i} className="bg-[#1E1F22] rounded-md p-3 space-y-2.5 border border-[#2B2D31]">
          {/* Header row */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-[#6b7280] uppercase tracking-wide">Dugme {i + 1}</span>
            <button
              type="button"
              onClick={() => remove(i)}
              className="text-[#6b7280] hover:text-[#ef4444] transition-colors p-0.5 rounded"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Type selector */}
          <div className="space-y-1">
            <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">Tip akcije</Label>
            <div className="grid grid-cols-3 gap-1">
              {(Object.keys(BUTTON_TYPE_LABELS) as ButtonType[]).map(t => {
                const sel = (btn.type ?? "custom") === t;
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => changeType(i, t)}
                    className="px-2 py-1.5 rounded text-[10px] font-bold transition-all text-center leading-tight"
                    style={{
                      background: sel ? "rgba(88,101,242,0.2)" : "rgba(255,255,255,0.04)",
                      border: `1px solid ${sel ? "#5865F2" : "rgba(255,255,255,0.08)"}`,
                      color: sel ? "#a5b4fc" : "#6b7280",
                    }}
                  >
                    {BUTTON_TYPE_LABELS[t]}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Label */}
          <div className="space-y-1">
            <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">Label</Label>
            <Input
              value={btn.label}
              onChange={e => update(i, { label: e.target.value })}
              placeholder="Tekst na dugmetu..."
              className="bg-[#2B2D31] border-[#404249] text-[#F2F3F5] text-sm h-8"
            />
          </div>

          {/* Emoji */}
          <div className="space-y-1">
            <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">Emoji (opcionalno)</Label>
            <Input
              value={btn.emoji ?? ""}
              onChange={e => update(i, { emoji: e.target.value || undefined })}
              placeholder="🔊 ili <:ime:id>"
              className="bg-[#2B2D31] border-[#404249] text-[#F2F3F5] text-sm h-8 font-mono"
            />
          </div>

          {/* Role picker — only for "role" type */}
          {btn.type === "role" && (
            <div className="space-y-1">
              <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">Uloga</Label>
              <select
                value={btn.roleId ?? ""}
                onChange={e => update(i, { roleId: e.target.value || undefined })}
                className="w-full bg-[#2B2D31] border border-[#404249] text-[#F2F3F5] text-sm rounded-md px-2 h-8"
              >
                <option value="">— Odaberi ulogu —</option>
                {(roles ?? []).filter(r => !r.name.startsWith("@")).map(r => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
              {btn.roleId && (
                <p className="text-[10px] text-[#4E5058]">
                  custom_id: <code className="text-[#F1C40F]">panel_role_{btn.roleId}</code>
                </p>
              )}
            </div>
          )}

          {/* URL — only for "link" type */}
          {btn.type === "link" && (
            <div className="space-y-1">
              <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">URL</Label>
              <Input
                value={btn.url ?? ""}
                onChange={e => update(i, { url: e.target.value || undefined })}
                placeholder="https://..."
                className="bg-[#2B2D31] border-[#404249] text-[#F2F3F5] text-sm h-8 font-mono"
              />
            </div>
          )}

          {/* Custom ID — only for "custom" type */}
          {btn.type === "custom" && (
            <div className="space-y-1">
              <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">Custom ID</Label>
              <Input
                value={btn.customId ?? ""}
                onChange={e => update(i, { customId: e.target.value || undefined })}
                placeholder="moj_custom_btn"
                className="bg-[#2B2D31] border-[#404249] text-[#F2F3F5] text-sm h-8 font-mono"
              />
            </div>
          )}

          {/* Style override */}
          {btn.type !== "link" && (
            <div className="space-y-1">
              <Label className="text-[#B5BAC1] text-[10px] font-semibold uppercase tracking-wide">Boja</Label>
              <div className="grid grid-cols-4 gap-1">
                {(["success", "primary", "secondary", "danger"] as const).map(style => {
                  const styleLabels: Record<string, string> = {
                    success: "🟢", primary: "🔵", secondary: "⚫", danger: "🔴",
                  };
                  const sel = btn.style === style;
                  return (
                    <button
                      key={style}
                      type="button"
                      onClick={() => update(i, { style })}
                      className="px-2 py-1.5 rounded text-[11px] font-bold transition-all"
                      title={style}
                      style={{
                        background: sel ? `${BUTTON_STYLE_COLORS[style]}33` : "rgba(255,255,255,0.04)",
                        border: `1px solid ${sel ? BUTTON_STYLE_COLORS[style] : "rgba(255,255,255,0.08)"}`,
                        color: sel ? "#fff" : "#6b7280",
                      }}
                    >
                      {styleLabels[style]}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Preview chip */}
          <button
            type="button"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-white text-[12px] font-medium select-none cursor-default"
            style={{ background: BUTTON_STYLE_COLORS[btn.style] ?? "#4E5058" }}
          >
            {btn.emoji && <span>{btn.emoji}</span>}
            <span>{btn.label || "Dugme"}</span>
          </button>
        </div>
      ))}
    </div>
  );
}

function EmbedEditor({ embed, isFullscreen, onToggleFullscreen }: {
  embed: EmbedTemplate;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const updateEmbedMutation = useUpdateEmbed();
  const { data: channelData } = useDiscordChannels();

  const [sendOpen, setSendOpen] = useState(false);
  const [sendChannelId, setSendChannelId] = useState("");
  const [sendSearch, setSendSearch] = useState("");
  const [sending, setSending] = useState(false);
  const sendRef = useRef<HTMLDivElement>(null);

  const allTextChannels = useMemo(() => [
    ...(channelData?.categories?.flatMap(c => c.channels) ?? []),
    ...(channelData?.uncategorized ?? []),
  ].filter(c => c.type === 0), [channelData]);

  const filteredSendChannels = useMemo(() =>
    !sendSearch ? allTextChannels : allTextChannels.filter(c => c.name.toLowerCase().includes(sendSearch.toLowerCase())),
  [allTextChannels, sendSearch]);

  useEffect(() => {
    if (!sendOpen) return;
    const handler = (e: MouseEvent) => {
      if (sendRef.current && !sendRef.current.contains(e.target as Node)) setSendOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [sendOpen]);

  const handleSend = async () => {
    if (!sendChannelId) return;
    setSending(true);
    try {
      const res = await fetch(`${BASE_URL}/api/discord/channels/${sendChannelId}/send-embed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embedName: embed.name }),
      });
      if (res.ok) {
        const chName = allTextChannels.find(c => c.id === sendChannelId)?.name ?? sendChannelId;
        toast({ title: `✅ Embed poslan u #${chName}` });
        setSendOpen(false);
      } else {
        const err = await res.json().catch(() => ({}));
        toast({ title: `❌ Greška: ${err.error ?? res.status}`, variant: "destructive" });
      }
    } catch {
      toast({ title: "❌ Greška pri slanju", variant: "destructive" });
    } finally {
      setSending(false);
    }
  };

  const [title, setTitle] = useState(embed.title ?? "");
  const [description, setDescription] = useState(embed.description ?? "");
  const [color, setColor] = useState(embed.color ?? "#2B2D42");
  const [bgColor, setBgColor] = useState<string>((embed as any).bgColor ?? "#2B2D31");
  const [fields, setFields] = useState<EmbedField[]>(embed.fields ?? []);
  const [buttons, setButtons] = useState<EmbedButton[]>((embed as any).buttons ?? []);
  const [previewMode, setPreviewMode] = useState<"desktop" | "mobile">("desktop");

  // Welcome card specific state
  const [cardDesc,       setCardDesc]       = useState<string>((embed as any).cardDesc       ?? "Drago nam je sto si stigao/la u nasu zajednicu!");
  const [cardItem1,      setCardItem1]      = useState<string>((embed as any).cardItem1      ?? "Procitaj pravila");
  const [cardItem2,      setCardItem2]      = useState<string>((embed as any).cardItem2      ?? "Odaberi role");
  const [cardItem3,      setCardItem3]      = useState<string>((embed as any).cardItem3      ?? "Predstavi se zajednici");
  const [cardClosing,    setCardClosing]    = useState<string>((embed as any).cardClosing    ?? "Uzivaj i zabavi se!");
  const [item1ChannelId, setItem1ChannelId] = useState<string>((embed as any).item1ChannelId ?? "");
  const [item2ChannelId, setItem2ChannelId] = useState<string>((embed as any).item2ChannelId ?? "");
  const [item3ChannelId, setItem3ChannelId] = useState<string>((embed as any).item3ChannelId ?? "");
  const [cardPreviewUrl, setCardPreviewUrl] = useState<string>("");

  // Resizable panel state
  const [formWidth, setFormWidth] = useState(280);
  const isResizing = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const onResizeStart = (e: React.MouseEvent) => {
    isResizing.current = true;
    startX.current = e.clientX;
    startWidth.current = formWidth;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!isResizing.current) return;
      const delta = e.clientX - startX.current;
      setFormWidth(Math.max(200, Math.min(480, startWidth.current + delta)));
    };
    const onUp = () => {
      isResizing.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  useEffect(() => {
    setTitle(embed.title ?? "");
    setDescription(embed.description ?? "");
    setColor(embed.color ?? "#2B2D42");
    setBgColor((embed as any).bgColor ?? "#2B2D31");
    setFields(embed.fields ?? []);
    setButtons((embed as any).buttons ?? []);
    setCardDesc((embed as any).cardDesc ?? "Drago nam je sto si stigao/la u nasu zajednicu!");
    setCardItem1((embed as any).cardItem1 ?? "Procitaj pravila");
    setCardItem2((embed as any).cardItem2 ?? "Odaberi role");
    setCardItem3((embed as any).cardItem3 ?? "Predstavi se zajednici");
    setCardClosing((embed as any).cardClosing ?? "Uzivaj i zabavi se!");
    setItem1ChannelId((embed as any).item1ChannelId ?? "");
    setItem2ChannelId((embed as any).item2ChannelId ?? "");
    setItem3ChannelId((embed as any).item3ChannelId ?? "");
  }, [embed.name]);

  // Debounced card preview URL — rebuild 500ms after any card field changes
  useEffect(() => {
    if (embed.name !== "welcome") return;
    const btns = buttons as EmbedButton[];
    const build = () =>
      `${window.location.origin}/api/welcome-card` +
      `?user=Testko&memberCount=1.250.000%2B&accountAge=2g+3m&joinedAt=Maj+2024&count=4521` +
      `&desc=${encodeURIComponent(cardDesc)}` +
      `&item1=${encodeURIComponent(cardItem1)}` +
      `&item2=${encodeURIComponent(cardItem2)}` +
      `&item3=${encodeURIComponent(cardItem3)}` +
      `&closing=${encodeURIComponent(cardClosing)}` +
      `&btn1=${encodeURIComponent(btns[0]?.label ?? "Pravila")}` +
      `&btn2=${encodeURIComponent(btns[1]?.label ?? "Role")}` +
      `&btn3=${encodeURIComponent(btns[2]?.label ?? "Pozovi")}` +
      `&btn4=${encodeURIComponent(btns[3]?.label ?? "Chat")}`;
    setCardPreviewUrl(build());
    const t = setTimeout(() => setCardPreviewUrl(build()), 500);
    return () => clearTimeout(t);
  }, [embed.name, cardDesc, cardItem1, cardItem2, cardItem3, cardClosing, buttons]);

  const updateField = (i: number, key: "name" | "value", val: string) => {
    setFields((fs: EmbedField[]) => fs.map((f: EmbedField, idx: number) => idx === i ? { ...f, [key]: val } : f));
  };

  const handleSave = () => {
    updateEmbedMutation.mutate(
      { name: embed.name, data: { title, description, color, bgColor, fields, buttons, cardDesc, cardItem1, cardItem2, cardItem3, cardClosing, item1ChannelId, item2ChannelId, item3ChannelId } as any },
      {
        onSuccess: () => {
          toast({ title: "Embed sacuvan" });
          queryClient.invalidateQueries({ queryKey: getListEmbedsQueryKey() });
        },
        onError: () => toast({ title: "Greska pri cuvanju", variant: "destructive" }),
      }
    );
  };

  const catColor = getCategoryColor(embed.category ?? "");

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3.5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.015)" }}>
        <div className="flex items-center gap-3">
          {(() => {
            const EmbedIcon = EMBED_ICONS[embed.name] ?? EMBED_CAT_ICONS[embed.category ?? ""];
            return (
              <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{
                  background: `${catColor}20`,
                  border: `1.5px solid ${catColor}50`,
                  boxShadow: `0 0 10px ${catColor}25`,
                }}>
                {EmbedIcon
                  ? <EmbedIcon style={{ width: 18, height: 18, color: catColor, strokeWidth: 2 }} />
                  : <span style={{ fontSize: 16 }}>📝</span>
                }
              </div>
            );
          })()}
          <div>
            <span className="font-black text-white text-sm">
              {EMBED_DISPLAY_NAMES[embed.name] ?? embed.title ?? embed.name}
            </span>
            <div className="flex items-center gap-1.5 mt-0.5">
              {(() => {
                const CatIcon = EMBED_CAT_ICONS[embed.category ?? ""];
                return CatIcon
                  ? <CatIcon style={{ width: 10, height: 10, color: catColor, strokeWidth: 2.5 }} />
                  : <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: catColor }} />;
              })()}
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: catColor }}>
                {embed.category}
              </span>
              <span className="text-[10px]" style={{ color: `${catColor}60` }}>·</span>
              <span className="text-[10px] font-mono" style={{ color: "#4b5563" }}>{embed.name}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onToggleFullscreen && (
            <button
              onClick={onToggleFullscreen}
              title={isFullscreen ? "Izlaz iz fullscreen (Esc)" : "Fullscreen editor"}
              className="p-2 rounded-lg transition-all"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", color: "#6b7280" }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = "#a5b4fc"; (e.currentTarget as HTMLElement).style.background = "rgba(99,102,241,0.12)"; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#6b7280"; (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
          )}

          {/* Send to Discord dropdown */}
          <div ref={sendRef} className="relative">
            <button
              onClick={() => setSendOpen(o => !o)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all"
              style={{
                background: sendOpen ? "rgba(88,101,242,0.2)" : "rgba(88,101,242,0.1)",
                border: "1px solid rgba(88,101,242,0.35)",
                color: "#818cf8",
              }}
            >
              <Send className="w-3.5 h-3.5" />
              Pošalji
              <ChevronDown className="w-3 h-3 opacity-60" />
            </button>

            {sendOpen && (
              <div
                className="absolute right-0 top-full mt-1 z-50 rounded-xl overflow-hidden"
                style={{
                  width: 260,
                  background: "#1a1b1e",
                  border: "1px solid rgba(255,255,255,0.1)",
                  boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
                }}
              >
                <div className="p-3 border-b border-white/5">
                  <p className="text-xs font-bold text-white/60 mb-2">Odaberi kanal</p>
                  <div className="relative">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" />
                    <input
                      autoFocus
                      value={sendSearch}
                      onChange={e => setSendSearch(e.target.value)}
                      placeholder="Pretraži kanale..."
                      className="w-full bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-white/30 outline-none focus:border-indigo-500/50"
                    />
                  </div>
                </div>
                <div className="max-h-48 overflow-y-auto p-1">
                  {filteredSendChannels.length === 0 && (
                    <p className="text-xs text-white/30 text-center py-4">Nema kanala</p>
                  )}
                  {filteredSendChannels.map(ch => (
                    <button
                      key={ch.id}
                      onClick={() => setSendChannelId(ch.id)}
                      className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs transition-all text-left"
                      style={{
                        background: sendChannelId === ch.id ? "rgba(88,101,242,0.2)" : "transparent",
                        color: sendChannelId === ch.id ? "#a5b4fc" : "#9ca3af",
                      }}
                    >
                      <Hash className="w-3 h-3 flex-shrink-0 opacity-50" />
                      <span className="truncate">{ch.name}</span>
                      {sendChannelId === ch.id && <CheckCircle className="w-3 h-3 ml-auto text-indigo-400 flex-shrink-0" />}
                    </button>
                  ))}
                </div>
                <div className="p-2 border-t border-white/5">
                  <button
                    onClick={handleSend}
                    disabled={!sendChannelId || sending}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{
                      background: sendChannelId && !sending ? "rgba(88,101,242,0.8)" : "rgba(88,101,242,0.2)",
                      color: "#fff",
                    }}
                  >
                    <Send className="w-3.5 h-3.5" />
                    {sending ? "Slanje..." : sendChannelId ? `Pošalji u #${allTextChannels.find(c => c.id === sendChannelId)?.name ?? "..."}` : "Odaberi kanal prvo"}
                  </button>
                </div>
              </div>
            )}
          </div>

          <Button
            size="sm"
            onClick={handleSave}
            disabled={updateEmbedMutation.isPending}
            data-testid="button-save-embed"
            className="border-0 font-bold"
            style={{ background: catColor, color: "#fff" }}
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            {updateEmbedMutation.isPending ? "Čuvanje..." : "Sačuvaj"}
          </Button>
        </div>
      </div>

      <div className="flex flex-row flex-1 overflow-hidden">
        {/* Form */}
        <div className="flex-shrink-0 p-5 space-y-5 border-r border-[#1E1F22] overflow-y-auto" style={{ width: formWidth }}>
          <TextFieldWithEmoji
            label="Naslov"
            value={title}
            onChange={setTitle}
            testId="input-embed-title"
          />
          <TextFieldWithEmoji
            label="Opis"
            value={description}
            onChange={setDescription}
            multiline
            testId="input-embed-description"
          />
          {embed.name === "welcome" && (
            <div className="space-y-4">
              <div className="space-y-3">
                <Label className="text-[#B5BAC1] text-xs font-semibold uppercase tracking-wide block">Dugmad</Label>
                {([
                  { label: buttons[0]?.label ?? "Pravila", channelId: buttons[0]?.channelId ?? "", idx: 0 },
                  { label: buttons[1]?.label ?? "Role",    channelId: buttons[1]?.channelId ?? "", idx: 1 },
                  { label: buttons[2]?.label ?? "Pozovi",  channelId: buttons[2]?.channelId ?? "", idx: 2 },
                  { label: buttons[3]?.label ?? "Chat",    channelId: buttons[3]?.channelId ?? "", idx: 3 },
                ]).map(({ label, channelId, idx }) => {
                  const allChannels: DiscordChannel[] = [
                    ...(channelData?.categories.flatMap(c => c.channels) ?? []),
                    ...(channelData?.uncategorized ?? []),
                  ];
                  const linked = allChannels.find(c => c.id === channelId);
                  return (
                    <div key={idx} className="bg-[#1E1F22] rounded-md p-2.5 space-y-2 border border-[#2B2D31]">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-bold text-[#5865F2] uppercase tracking-wide w-16 flex-shrink-0">Dugme {idx + 1}</span>
                        <Input
                          value={label}
                          onChange={e => {
                            const v = e.target.value;
                            setButtons(b => {
                              const next = [...b];
                              while (next.length <= idx) next.push({ label: "", style: "link", type: "link" });
                              next[idx] = { ...next[idx], label: v };
                              return next;
                            });
                          }}
                          className="bg-[#2B2D31] border-[#404249] text-[#F2F3F5] text-sm h-7"
                          placeholder="Naziv dugmeta"
                        />
                      </div>
                      <div>
                        <select
                          value={channelId}
                          onChange={e => {
                            const v = e.target.value;
                            setButtons(b => {
                              const next = [...b];
                              while (next.length <= idx) next.push({ label: "", style: "link", type: "link" });
                              next[idx] = { ...next[idx], channelId: v || undefined, type: "link", style: "link" };
                              return next;
                            });
                          }}
                          className="w-full bg-[#2B2D31] border border-[#404249] text-[#F2F3F5] text-sm rounded-md px-2 h-8"
                        >
                          <option value="">— Poveži kanal —</option>
                          {(channelData?.categories ?? []).map(cat => (
                            <optgroup key={cat.id} label={cat.name}>
                              {cat.channels.filter(c => c.type === 0).map(c => (
                                <option key={c.id} value={c.id}>#{c.name}</option>
                              ))}
                            </optgroup>
                          ))}
                          {(channelData?.uncategorized ?? []).filter(c => c.type === 0).map(c => (
                            <option key={c.id} value={c.id}>#{c.name}</option>
                          ))}
                        </select>
                        {linked && (
                          <p className="text-[10px] text-[#57F287] mt-1 flex items-center gap-1">
                            <span>✓</span> #{linked.name}
                          </p>
                        )}
                        {!linked && channelId && (
                          <p className="text-[10px] text-[#ED4245] mt-1">ID: {channelId}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          <div className="space-y-2">
            <Label className="text-[#B5BAC1] text-xs font-semibold uppercase tracking-wide">Boja embeda</Label>
            {/* Preset palette */}
            <div className="grid grid-cols-10 gap-1.5">
              {[
                "#5865F2","#57F287","#FEE75C","#ED4245","#EB459E",
                "#F1C40F","#F97316","#E67E22","#9B59B6","#3498DB",
                "#2ECC71","#1ABC9C","#E74C3C","#2C3E50","#FF6A00",
                "#FF4D6D","#00BCD4","#8E44AD","#27AE60","#2B2D42",
              ].map(preset => (
                <button
                  key={preset}
                  type="button"
                  title={preset}
                  onClick={() => setColor(preset)}
                  className="w-6 h-6 rounded-full border-2 transition-all hover:scale-110 focus:outline-none"
                  style={{
                    backgroundColor: preset,
                    borderColor: color.toLowerCase() === preset.toLowerCase() ? "#fff" : "transparent",
                    boxShadow: color.toLowerCase() === preset.toLowerCase() ? `0 0 0 1px ${preset}` : "none",
                  }}
                />
              ))}
            </div>
            {/* Custom picker + hex input */}
            <div className="flex gap-2 items-center">
              <div className="relative w-9 h-9 flex-shrink-0">
                <div
                  className="w-9 h-9 rounded-lg border-2 border-[#404249] cursor-pointer overflow-hidden"
                  style={{ backgroundColor: color }}
                />
                <input
                  type="color"
                  value={color}
                  onChange={e => setColor(e.target.value)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  data-testid="input-embed-color-picker"
                  title="Odaberi prilagođenu boju"
                />
              </div>
              <Input
                value={color}
                onChange={e => setColor(e.target.value)}
                className="flex-1 bg-[#1E1F22] border-[#2B2D31] text-[#F2F3F5] font-mono text-sm uppercase"
                data-testid="input-embed-color-text"
                placeholder="#2B2D42"
              />
              <div
                className="w-9 h-9 rounded-lg flex-shrink-0 border border-white/10"
                style={{ backgroundColor: color }}
                title="Pregled boje"
              />
            </div>
          </div>

          {/* Background colour picker */}
          <div className="space-y-2">
            <div>
              <Label className="text-[#B5BAC1] text-xs font-semibold uppercase tracking-wide">Pozadina embeda</Label>
              <p className="text-[10px] mt-0.5" style={{ color: "#F1C40F" }}>
                ⚠ Samo za pregled u panelu — Discord ne podržava prilagođenu pozadinu embeda. Na Discordu pozadina ovisi o temi korisnika (dark/light mode).
              </p>
            </div>
            <div className="grid grid-cols-10 gap-1.5">
              {[
                "#2B2D31","#1E1F22","#313338","#111214","#0d0d0d",
                "#1a1a2e","#16213e","#0f3460","#1b1b2f","#2d1b33",
                "#1f2d1f","#1a2a1a","#2d1a1a","#2a1f0f","#1e2a2a",
                "#ffffff","#f0f0f0","#e0e0e0","#c0c0c0","#808080",
              ].map(preset => (
                <button
                  key={preset}
                  type="button"
                  title={preset}
                  onClick={() => setBgColor(preset)}
                  className="w-6 h-6 rounded-full border-2 transition-all hover:scale-110 focus:outline-none"
                  style={{
                    backgroundColor: preset,
                    borderColor: bgColor.toLowerCase() === preset.toLowerCase() ? "#fff" : preset === "#ffffff" ? "#555" : "transparent",
                    boxShadow: bgColor.toLowerCase() === preset.toLowerCase() ? `0 0 0 1px ${preset === "#ffffff" ? "#aaa" : preset}` : "none",
                  }}
                />
              ))}
            </div>
            <div className="flex gap-2 items-center">
              <div className="relative w-9 h-9 flex-shrink-0">
                <div
                  className="w-9 h-9 rounded-lg border-2 border-[#404249] cursor-pointer overflow-hidden"
                  style={{ backgroundColor: bgColor }}
                />
                <input
                  type="color"
                  value={bgColor}
                  onChange={e => setBgColor(e.target.value)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  title="Odaberi prilagođenu pozadinu"
                />
              </div>
              <Input
                value={bgColor}
                onChange={e => setBgColor(e.target.value)}
                className="flex-1 bg-[#1E1F22] border-[#2B2D31] text-[#F2F3F5] font-mono text-sm uppercase"
                placeholder="#2B2D31"
              />
              <div
                className="w-9 h-9 rounded-lg flex-shrink-0 border border-white/10"
                style={{ backgroundColor: bgColor }}
                title="Pregled pozadine"
              />
            </div>
          </div>

          {fields.length > 0 && (
            <div className="space-y-3">
              <Label className="text-[#B5BAC1] text-xs font-semibold uppercase tracking-wide">Polja</Label>
              {fields.map((f, i) => (
                <div key={i} className="bg-[#1E1F22] rounded-md p-2.5 space-y-2 border border-[#2B2D31]">
                  <TextFieldWithEmoji
                    label={`Naslov polja ${i + 1}`}
                    value={f.name}
                    onChange={v => updateField(i, "name", v)}
                    testId={`input-field-name-${i}`}
                  />
                  <TextFieldWithEmoji
                    label="Vrijednost"
                    value={f.value}
                    onChange={v => updateField(i, "value", v)}
                    multiline
                    testId={`input-field-value-${i}`}
                  />
                </div>
              ))}
            </div>
          )}

          {/* ── Dugmad editor ────────────────────────────────────── */}
          {embed.name !== "welcome" && (
            <ButtonEditor buttons={buttons} onChange={setButtons} />
          )}
        </div>

        {/* Resize handle */}
        <div
          onMouseDown={onResizeStart}
          className="w-1 flex-shrink-0 relative group cursor-col-resize"
          style={{ background: "#1E1F22" }}
        >
          <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-[#5865F2]/30 transition-colors" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-8 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: "#5865F2" }} />
        </div>

        {/* Preview */}
        <div className="flex-1 p-5 overflow-y-auto bg-[#2B2D31]">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs text-[#949BA4] font-semibold uppercase tracking-wider">Pregled — Discord izgled</div>
            <div className="flex items-center gap-1 bg-[#1E1F22] rounded-md p-0.5 border border-[#2B2D31]">
              <button
                type="button"
                onClick={() => setPreviewMode("desktop")}
                title="Desktop prikaz"
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                  previewMode === "desktop"
                    ? "bg-[#5865F2] text-white"
                    : "text-[#949BA4] hover:text-[#B5BAC1]"
                }`}
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M21 2H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h7l-2 3v1h8v-1l-2-3h7c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 12H3V4h18v10z"/>
                </svg>
                Desktop
              </button>
              <button
                type="button"
                onClick={() => setPreviewMode("mobile")}
                title="Mobile prikaz"
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                  previewMode === "mobile"
                    ? "bg-[#5865F2] text-white"
                    : "text-[#949BA4] hover:text-[#B5BAC1]"
                }`}
              >
                <svg width="10" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17 1.01L7 1c-1.1 0-2 .9-2 2v18c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V3c0-1.1-.9-1.99-2-1.99zM17 19H7V5h10v14z"/>
                </svg>
                Mobile
              </button>
            </div>
          </div>
          {(() => {
            // Apply demo variable substitution for preview
            const demoMap: Record<string, string> = {
              "{user}": "@TestUser",
              "{user.name}": "TestUser",
              "{user.avatar}": "https://cdn.discordapp.com/embed/avatars/0.png",
              "{server}": "GIANNI",
              "{accountAge}": "2g 3m",
              "{joinedAt}": "Maj 2026.",
              "{count}": "1.234",
              "{memberCount}": "1.234",
            };
            const applyDemo = (s: string) =>
              Object.entries(demoMap).reduce((a, [k, v]) => a.replaceAll(k, v), s);
            const previewTitle = applyDemo(title);
            const previewDesc = applyDemo(description);
            const previewFields = fields.map(f => ({
              ...f,
              name: applyDemo(String(f.name ?? "")),
              value: applyDemo(String(f.value ?? "")),
            }));
            const previewEmbed = {
              ...embed,
              thumbnail: embed.thumbnail ? applyDemo(embed.thumbnail) : embed.thumbnail,
            };
            return (
              <DiscordEmbedPreview
                embed={previewEmbed}
                title={previewTitle}
                description={previewDesc}
                color={color}
                bgColor={bgColor}
                previewMode={previewMode}
                fields={previewFields}
                buttons={buttons}
              />
            );
          })()}

          <div className="mt-4 text-[11px] text-[#949BA4] space-y-1">
            <div>Varijable poput <code className="bg-[#1E1F22] px-1 rounded text-[#F1C40F]">{"{user}"}</code> zamjenjuje bot pri slanju.</div>
            <div>Emoji format: <code className="bg-[#1E1F22] px-1 rounded text-[#F1C40F]">{"<:ime:id>"}</code> — koristi pikač desno od polja.</div>
            <div>Tag format: <code className="bg-[#1E1F22] px-1 rounded text-[#5865F2]">{"<#kanal-id>"}</code> <code className="bg-[#1E1F22] px-1 rounded text-[#5865F2]">{"<@&uloga-id>"}</code> — koristi <code className="bg-[#1E1F22] px-1 rounded">@</code> pikač desno od polja.</div>
            <div className="mt-2 pt-2 border-t border-[#2B2D31] space-y-2">
              <div className="text-[#949BA4] mb-1">Markdown formatiranje teksta:</div>
              <div className="flex flex-wrap gap-x-4 gap-y-1">
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"**tekst**"}</code> → <strong>podebljano</strong></div>
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"*tekst*"}</code> → <em>kurziv</em></div>
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"__tekst__"}</code> → <span className="underline">podvučeno</span></div>
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"~~tekst~~"}</code> → <span className="line-through">precrtano</span></div>
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"`tekst`"}</code> → <code className="bg-[#1E1F22] px-1 rounded">kod box</code></div>
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"||tekst||"}</code> → spoiler</div>
                <div><code className="bg-[#1E1F22] px-1 rounded text-white">{"> tekst"}</code> → blockquote</div>
              </div>

              <div className="pt-1">
                <div className="text-[#949BA4] mb-1">Dekorativne linije (copy-paste):</div>
                <div className="flex flex-wrap gap-x-3 gap-y-1">
                  {[
                    "─────────────",
                    "━━━━━━━━━━━",
                    "═════════════",
                    "· · · · · · · · ·",
                    "⊱ ────── ⊰",
                  ].map((line) => (
                    <code
                      key={line}
                      className="bg-[#1E1F22] px-1 rounded text-[#949BA4] cursor-pointer hover:text-white transition-colors select-all"
                      title="Klikni da selektuješ"
                    >{line}</code>
                  ))}
                </div>
              </div>

              <div className="pt-1">
                <div className="text-[#949BA4] mb-1">Unicode dekoracije (copy-paste):</div>
                <div className="flex flex-wrap gap-x-2 gap-y-1">
                  {["•","◆","◇","▸","►","→","✦","✧","★","☆","〔〕","【】","《》","╭","╰","│","✨","🌸","💫"].map((ch) => (
                    <code
                      key={ch}
                      className="bg-[#1E1F22] px-1 rounded text-[#949BA4] cursor-pointer hover:text-white transition-colors select-all"
                      title="Klikni da selektuješ"
                    >{ch}</code>
                  ))}
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Embeds() {
  const { data: embeds, isLoading } = useListEmbeds();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [selectedEmbed, setSelectedEmbed] = useState<EmbedTemplate | null>(null);
  const [sidebarSearch, setSidebarSearch] = useState("");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  const handleResetAll = async () => {
    if (!confirm("Resetovati SVE embede na podrazumijevane vrijednosti? Sve promjene bit će izgubljene.")) return;
    setIsResetting(true);
    try {
      const res = await fetch(`${BASE_URL}/api/embeds/reset-all`, { method: "POST" });
      if (!res.ok) throw new Error("Reset failed");
      const json = await res.json();
      await queryClient.invalidateQueries({ queryKey: getListEmbedsQueryKey() });
      toast({ title: `✅ ${json.updated ?? "Svi"} embeda resetovano na defaults` });
    } catch {
      toast({ title: "❌ Greška pri resetu", variant: "destructive" });
    } finally {
      setIsResetting(false);
    }
  };

  // Escape to exit fullscreen
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") setIsFullscreen(false); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  // Resizable sidebar
  const [sidebarWidth, setSidebarWidth] = useState(240);
  const sidebarResizing = useRef(false);
  const sidebarStartX = useRef(0);
  const sidebarStartW = useRef(0);

  const onSidebarResizeStart = (e: React.MouseEvent) => {
    sidebarResizing.current = true;
    sidebarStartX.current = e.clientX;
    sidebarStartW.current = sidebarWidth;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!sidebarResizing.current) return;
      const delta = e.clientX - sidebarStartX.current;
      setSidebarWidth(Math.max(180, Math.min(380, sidebarStartW.current + delta)));
    };
    const onUp = () => {
      sidebarResizing.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  // Auto-select first embed once loaded; re-sync selected embed when data refreshes (e.g. after reset)
  useEffect(() => {
    if (!embeds || embeds.length === 0) return;
    if (!selectedEmbed) {
      setSelectedEmbed(embeds[0]);
    } else {
      // Keep selected embed in sync with freshly fetched data
      const fresh = embeds.find(e => e.name === selectedEmbed.name);
      if (fresh) setSelectedEmbed(fresh);
    }
  }, [embeds]);

  // Group embeds by category
  const grouped = useMemo(() => {
    if (!embeds) return [];
    const map = new Map<string, EmbedTemplate[]>();
    for (const embed of embeds) {
      const cat = embed.category ?? "Ostalo";
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(embed);
    }
    return Array.from(map.entries()).map(([cat, items]) => ({ cat, items }));
  }, [embeds]);

  const filteredGrouped = useMemo(() => {
    const q = sidebarSearch.toLowerCase();
    if (!q) return grouped;
    return grouped.map(({ cat, items }) => ({
      cat,
      items: items.filter(e =>
        (EMBED_DISPLAY_NAMES[e.name] ?? e.title ?? e.name).toLowerCase().includes(q)
      ),
    })).filter(g => g.items.length > 0);
  }, [grouped, sidebarSearch]);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" style={{ background: "rgba(255,255,255,0.06)" }} />
        <div className="flex gap-4">
          <Skeleton className="h-[500px] w-56 flex-shrink-0" style={{ background: "rgba(255,255,255,0.04)" }} />
          <Skeleton className="h-[500px] flex-1" style={{ background: "rgba(255,255,255,0.04)" }} />
        </div>
      </div>
    );
  }

  const containerClass = isFullscreen
    ? "fixed inset-0 z-50 flex flex-col"
    : "flex flex-col h-full -m-6";

  return (
    <div className={containerClass} style={{ background: isFullscreen ? "#0a0b0f" : undefined }}>
      <div className="flex h-full min-h-0">
        {/* ── Sidebar ── */}
        <div
          className="flex-shrink-0 flex flex-col overflow-hidden"
          style={{
            width: sidebarWidth,
            background: "rgba(255,255,255,0.02)",
            borderRight: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          {/* Sidebar header */}
          <div className="px-3 pt-4 pb-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <div className="flex items-center gap-2 mb-3">
              <LayoutTemplate className="w-4 h-4" style={{ color: "#6366f1" }} />
              <span className="text-xs font-bold uppercase tracking-widest" style={{ color: "#6366f1" }}>
                Embed Templates
              </span>
              <div className="px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                style={{ background: "rgba(99,102,241,0.15)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.2)" }}>
                {embeds?.length ?? 0}
              </div>
              <button
                onClick={handleResetAll}
                disabled={isResetting}
                title="Učitaj sve embede — Reset na podrazumijevane vrijednosti"
                className="ml-auto p-1.5 rounded-md transition-all disabled:opacity-50"
                style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171" }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.2)"; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.1)"; }}
              >
                <RotateCcw className={`w-3 h-3 ${isResetting ? "animate-spin" : ""}`} />
              </button>
            </div>
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 w-3.5 h-3.5" style={{ color: "#4b5563" }} />
              <input
                placeholder="Pretraži..."
                value={sidebarSearch}
                onChange={e => setSidebarSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg text-xs text-white placeholder:text-gray-600 outline-none"
                style={{
                  background: "rgba(255,255,255,0.05)",
                  border: "1px solid rgba(255,255,255,0.08)",
                }}
              />
            </div>
          </div>

          {/* Grouped list */}
          <div className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
            {filteredGrouped.map(({ cat, items }) => {
              const color = getCategoryColor(cat);
              return (
                <div key={cat}>
                  {/* Category header */}
                  <div className="flex items-center gap-2 px-1 mb-1.5">
                    <div className="w-5 h-5 rounded flex items-center justify-center flex-shrink-0"
                      style={{ background: `${color}20`, border: `1px solid ${color}40` }}>
                      {(() => { const CatIcon = EMBED_CAT_ICONS[cat]; return CatIcon ? <CatIcon style={{ width: 11, height: 11, color, strokeWidth: 2.5 }} /> : null; })()}
                    </div>
                    <span className="text-[10px] font-black uppercase tracking-wider" style={{ color }}>{cat}</span>
                    <div className="flex-1 h-px" style={{ background: `linear-gradient(90deg, ${color}30, transparent)` }} />
                    <span className="text-[9px] font-bold" style={{ color: `${color}80` }}>{items.length}</span>
                  </div>

                  {/* Embed buttons */}
                  <div className="space-y-0.5 pl-1">
                    {items.map(embed => {
                      const isSelected = selectedEmbed?.name === embed.name;
                      return (
                        <button
                          key={embed.name}
                          onClick={() => setSelectedEmbed(embed)}
                          data-testid={`select-embed-${embed.name}`}
                          className="w-full text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2 transition-all text-xs group"
                          style={{
                            background: isSelected ? `${color}15` : "transparent",
                            border: isSelected ? `1px solid ${color}30` : "1px solid transparent",
                            color: isSelected ? "#F2F3F5" : "#6b7280",
                          }}
                          onMouseEnter={e => {
                            if (!isSelected) {
                              (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
                              (e.currentTarget as HTMLElement).style.color = "#d1d5db";
                            }
                          }}
                          onMouseLeave={e => {
                            if (!isSelected) {
                              (e.currentTarget as HTMLElement).style.background = "transparent";
                              (e.currentTarget as HTMLElement).style.color = "#6b7280";
                            }
                          }}
                        >
                          {(() => {
                            const EmbedIcon = EMBED_ICONS[embed.name] ?? EMBED_CAT_ICONS[cat];
                            return EmbedIcon ? (
                              <div
                                className="flex items-center justify-center rounded-md flex-shrink-0 transition-all"
                                style={{
                                  width: 22, height: 22,
                                  background: isSelected ? `${color}30` : `${color}15`,
                                  border: `1px solid ${isSelected ? color + "60" : color + "30"}`,
                                }}
                              >
                                <EmbedIcon style={{ width: 12, height: 12, color: isSelected ? color : color + "cc", strokeWidth: 2.2 }} />
                              </div>
                            ) : (
                              <div className="w-2 h-2 rounded-full flex-shrink-0"
                                style={{ backgroundColor: color, opacity: isSelected ? 1 : 0.5 }} />
                            );
                          })()}
                          <span className="truncate font-medium">
                            {EMBED_DISPLAY_NAMES[embed.name] ?? embed.title ?? embed.name}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Sidebar resize handle ── */}
        <div
          onMouseDown={onSidebarResizeStart}
          className="w-1 flex-shrink-0 relative group cursor-col-resize"
          style={{ background: "rgba(255,255,255,0.03)" }}
        >
          <div className="absolute inset-y-0 -left-1 -right-1 group-hover:bg-indigo-500/20 transition-colors" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-10 rounded-full opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: "#6366f1" }} />
        </div>

        {/* ── Main editor ── */}
        <div className="flex-1 min-w-0 flex flex-col overflow-hidden" style={{ background: "#1a1b1e" }}>
          {selectedEmbed ? (
            <EmbedEditor
              key={selectedEmbed.name}
              embed={selectedEmbed}
              isFullscreen={isFullscreen}
              onToggleFullscreen={() => setIsFullscreen(f => !f)}
            />
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl"
                style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" }}>
                📝
              </div>
              <div className="text-white font-semibold">Odaberi embed template</div>
              <div className="text-xs" style={{ color: "#4b5563" }}>Klikni na template s lijeve strane</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
