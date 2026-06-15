import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Skeleton } from "@/components/ui/skeleton";
import { Hash, Volume2, Megaphone, HelpCircle, ChevronDown, ChevronRight, Server, Layers, X, Save, Plus, Trash2, Send } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const BASE_URL = import.meta.env.BASE_URL.replace(/\/$/, "");

// ── Types ────────────────────────────────────────────────────────────────────

interface Channel {
  id: string;
  name: string;
  type: number;
  position: number;
  topic: string | null;
  nsfw: boolean;
}

interface ChannelCategory {
  id: string;
  name: string;
  position: number;
  channels: Channel[];
}

interface ChannelsData {
  categories: ChannelCategory[];
  uncategorized: Channel[];
}

interface GuildInfo {
  id: string;
  name: string;
  icon: string | null;
  memberCount: number | null;
}

interface EmbedTemplate {
  name: string;
  title: string;
  category: string;
  color: string;
}

interface ChannelConfig {
  embedNames: string[];
  note?: string;
}

// ── Data hooks ───────────────────────────────────────────────────────────────

function useChannels() {
  return useQuery<ChannelsData>({
    queryKey: ["discord-channels"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/discord/channels`);
      if (!res.ok) throw new Error("Failed to fetch channels");
      return res.json();
    },
    staleTime: 2 * 60 * 1000,
  });
}

function useGuildInfo() {
  return useQuery<GuildInfo>({
    queryKey: ["guild-info"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/discord/guild`);
      if (!res.ok) throw new Error("Failed to fetch guild");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

function useEmbeds() {
  return useQuery<EmbedTemplate[]>({
    queryKey: ["embeds"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/embeds`);
      if (!res.ok) throw new Error("Failed to fetch embeds");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

function useChannelConfigs() {
  return useQuery<Record<string, ChannelConfig>>({
    queryKey: ["channel-configs"],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/channel-configs`);
      if (!res.ok) throw new Error("Failed to fetch channel configs");
      return res.json();
    },
  });
}

function useSaveChannelConfig() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ channelId, embedNames, note }: { channelId: string; embedNames: string[]; note?: string }) => {
      const res = await fetch(`${BASE_URL}/api/channel-configs/${channelId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embedNames, note }),
      });
      if (!res.ok) throw new Error("Failed to save");
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["channel-configs"] }),
  });
}

function useSendEmbed() {
  return useMutation({
    mutationFn: async ({ channelId, embedName }: { channelId: string; embedName: string }) => {
      const res = await fetch(`${BASE_URL}/api/discord/channels/${channelId}/send-embed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embedName }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Greška pri slanju" }));
        throw new Error(err.error ?? "Greška pri slanju");
      }
      return res.json();
    },
  });
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const EMBED_DISPLAY_NAMES: Record<string, string> = {
  welcome: "Dobrodošao na server",
  leave: "Clan je napustio server",
  "dm-welcome": "DM Dobrodošlica",
  boost: "Novi Boost! 💜",
  birthday: "Sretan Rodjendan! 🎂",
  starboard: "Zvjezdana poruka ⭐",
  aotw: "Aktivni Član Sedmice 👑",
  "log-join": "Novi Član (Log) 📥",
  "log-edit": "Poruka Editovana ✏️",
  "log-delete": "Poruka Obrisana 🗑️",
  report: "Prijava člana 🚨",
  warn: "Upozorenje ⚠️",
  ban: "Član Banovan 🔨",
  levelup: "Level Up! 🌟",
  "vatrica-nova": "Nova Vatrica! 🔥",
  aktivnost: "Aktivnost 📊",
  rank: "Rank Profil 📈",
  "leaderboard-xp": "Top Lista — XP 🏅",
  "leaderboard-novac": "Top Lista — Novac 💰",
  heist: "Razboj u pripremi 💰",
  lottery: "Sedmična Loto 🎰",
  quests: "Dnevni Zadaci 📋",
  giveaway: "Nagradna Igra 🎉",
  slots: "Slot Mašina 🎰",
  blackjack: "Blackjack 🃏",
  "poker-lobby": "Poker — Lobby 🃏",
  "poker-game": "Poker — Igra 🃏",
  "poker-showdown": "Poker — Showdown 🏆",
  "among-us-lobby": "Among Us — Lobby 🚀",
  "among-us-game": "Among Us — U Toku 🚀",
  "among-us-end": "Among Us — Kraj 🏁",
  "kaladont-start": "Kaladont — Start 🔤",
  "kaladont-active": "Kaladont — Aktivna igra 🔤",
  "kaladont-word": "Kaladont — Word Card 🔤",
  "kaladont-win": "Kaladont — Pobjeda 👑",
  bingo: "Bingo 🎱",
  hunt: "Lov — Ulovio životinju 🏹",
  zoo: "Zoo — Zbirka 🦁",
  battle: "Bitka ⚔️",
  pray: "Molitva 🙏",
  vers: "Vers — Hip Hop 🎤",
  kompli: "Kompliment 🌹",
  fora: "Fora 😂",
  muv: "Muv 😏",
  crush: "Crush 💘",
  zagrljaj: "Zagrljaj 🤗",
  poljubac: "Poljubac 💋",
  mazi: "Mazi 🥰",
  tapsi: "Tapsi 👋",
  high5: "High Five 🙌",
  cudan: "Ćudan 😠",
  srce: "Srce ❤️",
  brak: "Brak / Prosidba 💍",
  spotify: "Spotify 🎵",
  invite: "Statistika 📊",
  avatar: "Avatar 🖼️",
  "brojanje-info": "Brojanje — stanje 🔢",
  ticket: "Tiket — Panel 🎫",
  "ticket-otvoren": "Tiket — Otvoren ✅",
  "staff-prijava": "Staff Prijava 📋",
  "private-vc":    "Privatni Voice Kanal 🔊",
  "voice-pravila": "Voice Pravila — Panel 🔊",
};

const EMBED_CATEGORY_COLORS: Record<string, string> = {
  Sistem: "#6366f1",
  Log: "#f59e0b",
  Moderacija: "#ef4444",
  XP: "#22c55e",
  Ekonomija: "#f97316",
  Igre: "#3b82f6",
  Fun: "#ec4899",
  Ljubavne: "#e879f9",
  Info: "#14b8a6",
  "Sistem paneli": "#a78bfa",
};

const CATEGORY_PALETTE = [
  "#6366f1","#ef4444","#f59e0b","#22c55e",
  "#3b82f6","#ec4899","#f97316","#14b8a6",
  "#a78bfa","#e879f9","#84cc16","#06b6d4",
];

function channelIcon(type: number) {
  switch (type) {
    case 2:  return <Volume2 className="w-3.5 h-3.5 flex-shrink-0" />;
    case 5:  return <Megaphone className="w-3.5 h-3.5 flex-shrink-0" />;
    case 13: return <Volume2 className="w-3.5 h-3.5 flex-shrink-0" />;
    case 15: return <HelpCircle className="w-3.5 h-3.5 flex-shrink-0" />;
    default: return <Hash className="w-3.5 h-3.5 flex-shrink-0" />;
  }
}

function channelColor(type: number) {
  switch (type) {
    case 2:  return "#22c55e";
    case 5:  return "#f59e0b";
    case 13: return "#14b8a6";
    case 15: return "#6366f1";
    default: return "#6b7280";
  }
}

// ── Channel side panel ───────────────────────────────────────────────────────

function ChannelPanel({
  channel,
  config,
  embeds,
  onClose,
  onSave,
  saving,
}: {
  channel: Channel;
  config: ChannelConfig | undefined;
  embeds: EmbedTemplate[] | undefined;
  onClose: () => void;
  onSave: (embedNames: string[], note: string) => void;
  saving: boolean;
}) {
  const [selected, setSelected] = useState<string[]>(config?.embedNames ?? []);
  const [note, setNote] = useState(config?.note ?? "");
  const [search, setSearch] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const [sendingEmbed, setSendingEmbed] = useState<string | null>(null);
  const sendEmbed = useSendEmbed();
  const { toast } = useToast();

  const handleSend = async (embedName: string) => {
    setSendingEmbed(embedName);
    try {
      await sendEmbed.mutateAsync({ channelId: channel.id, embedName });
      toast({ title: "Embed poslan!", description: `"${EMBED_DISPLAY_NAMES[embedName] ?? embedName}" je poslan u #${channel.name}` });
    } catch (err: any) {
      toast({ title: "Greška", description: err.message ?? "Slanje nije uspjelo", variant: "destructive" });
    } finally {
      setSendingEmbed(null);
    }
  };

  const color = channelColor(channel.type);

  const grouped = embeds
    ? embeds.reduce((acc, e) => {
        const cat = e.category ?? "Ostalo";
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(e);
        return acc;
      }, {} as Record<string, EmbedTemplate[]>)
    : {};

  const filteredGrouped = Object.entries(grouped).reduce((acc, [cat, items]) => {
    const filtered = items.filter(e =>
      !search || (EMBED_DISPLAY_NAMES[e.name] ?? e.name).toLowerCase().includes(search.toLowerCase())
    );
    if (filtered.length) acc[cat] = filtered;
    return acc;
  }, {} as Record<string, EmbedTemplate[]>);

  const toggle = (name: string) => {
    setSelected(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name]
    );
  };

  return (
    <div className="flex flex-col h-full" style={{ background: "#0d0e14", borderLeft: "1px solid rgba(255,255,255,0.06)" }}>
      {/* Panel header */}
      <div className="flex items-center gap-3 px-5 py-4 flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.02)" }}>
        <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: `${color}15`, border: `1px solid ${color}30` }}>
          <span style={{ color }}>{channelIcon(channel.type)}</span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-black text-white text-sm">#{channel.name}</div>
          <div className="text-[10px] mt-0.5" style={{ color: "#4b5563" }}>
            {selected.length > 0 ? `${selected.length} embed${selected.length !== 1 ? "a" : ""} dodijeljen` : "Nema dodijeljenih embeda"}
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 rounded-lg transition-colors" style={{ color: "#4b5563" }}
          onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,0.06)") }
          onMouseLeave={e => (e.currentTarget.style.background = "transparent")}>
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Assigned embeds */}
      <div className="px-5 py-4 flex-shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="text-[10px] font-bold uppercase tracking-widest mb-2.5" style={{ color: "#374151" }}>
          Dodijeljeni embedovi
        </div>
        {selected.length === 0 ? (
          <div className="text-xs py-3 text-center rounded-lg" style={{ color: "#374151", background: "rgba(255,255,255,0.02)", border: "1px dashed rgba(255,255,255,0.06)" }}>
            Nijedan embed nije dodijeljen
          </div>
        ) : (
          <div className="space-y-1.5">
            {selected.map(name => {
              const embed = embeds?.find(e => e.name === name);
              const catColor = EMBED_CATEGORY_COLORS[embed?.category ?? ""] ?? "#6366f1";
              return (
                <div key={name} className="flex items-center gap-2 px-3 py-2 rounded-lg"
                  style={{ background: `${catColor}10`, border: `1px solid ${catColor}20` }}>
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: embed?.color ?? catColor }} />
                  <span className="flex-1 text-xs font-medium text-white truncate">
                    {EMBED_DISPLAY_NAMES[name] ?? name}
                  </span>
                  <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded flex-shrink-0"
                    style={{ background: `${catColor}20`, color: catColor }}>
                    {embed?.category}
                  </span>
                  <button
                    onClick={() => handleSend(name)}
                    disabled={sendingEmbed === name}
                    title="Pošalji u Discord kanal"
                    className="flex-shrink-0 transition-colors disabled:opacity-50"
                    style={{ color: "#22c55e" }}
                    onMouseEnter={e => { if (sendingEmbed !== name) (e.currentTarget as HTMLElement).style.color = "#4ade80"; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = "#22c55e"; }}>
                    {sendingEmbed === name
                      ? <span className="text-[10px] animate-pulse">⏳</span>
                      : <Send className="w-3.5 h-3.5" />}
                  </button>
                  <button onClick={() => toggle(name)} className="flex-shrink-0 transition-colors"
                    style={{ color: "#4b5563" }}
                    onMouseEnter={e => (e.currentTarget.style.color = "#ef4444")}
                    onMouseLeave={e => (e.currentTarget.style.color = "#4b5563")}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Add embed button */}
        <button
          className="mt-2.5 w-full flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-semibold transition-all"
          style={{ background: "rgba(99,102,241,0.08)", border: "1px dashed rgba(99,102,241,0.25)", color: "#6366f1" }}
          onClick={() => setShowPicker(p => !p)}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(99,102,241,0.15)"; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(99,102,241,0.08)"; }}
        >
          <Plus className="w-3.5 h-3.5" />
          {showPicker ? "Zatvori listu" : "Dodaj embed"}
        </button>
      </div>

      {/* Embed picker */}
      {showPicker && (
        <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <div className="px-5 py-2 flex-shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
            <input
              autoFocus
              placeholder="Pretraži embede..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full px-3 py-1.5 rounded-lg text-xs text-white placeholder:text-gray-600 outline-none"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
            />
          </div>
          <div className="flex-1 overflow-y-auto px-5 py-3 space-y-3">
            {Object.entries(filteredGrouped).map(([cat, items]) => {
              const catColor = EMBED_CATEGORY_COLORS[cat] ?? "#6366f1";
              return (
                <div key={cat}>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-[9px] font-black uppercase tracking-widest" style={{ color: catColor }}>{cat}</span>
                    <div className="flex-1 h-px" style={{ background: `linear-gradient(90deg, ${catColor}30, transparent)` }} />
                  </div>
                  <div className="space-y-1">
                    {items.map(embed => {
                      const isSelected = selected.includes(embed.name);
                      return (
                        <button
                          key={embed.name}
                          onClick={() => toggle(embed.name)}
                          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left transition-all text-xs"
                          style={{
                            background: isSelected ? `${catColor}15` : "rgba(255,255,255,0.02)",
                            border: isSelected ? `1px solid ${catColor}30` : "1px solid rgba(255,255,255,0.04)",
                            color: isSelected ? "#F2F3F5" : "#6b7280",
                          }}
                        >
                          <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: embed.color ?? catColor }} />
                          <span className="flex-1 truncate font-medium">{EMBED_DISPLAY_NAMES[embed.name] ?? embed.name}</span>
                          {isSelected && (
                            <div className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 text-white text-[10px]"
                              style={{ background: catColor }}>✓</div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Note + save */}
      {!showPicker && (
        <div className="px-5 py-4 flex-shrink-0 mt-auto" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <div className="text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: "#374151" }}>Bilješka</div>
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Napomena za ovaj kanal..."
            rows={2}
            className="w-full px-3 py-2 rounded-lg text-xs resize-none outline-none mb-3 text-white placeholder:text-gray-700"
            style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}
          />
          <button
            onClick={() => onSave(selected, note)}
            disabled={saving}
            className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-lg text-sm font-bold transition-all text-white"
            style={{ background: "linear-gradient(90deg, #6366f1, #8b5cf6)", opacity: saving ? 0.7 : 1 }}
          >
            <Save className="w-4 h-4" />
            {saving ? "Čuvanje..." : "Sačuvaj konfiguraciju"}
          </button>
        </div>
      )}
    </div>
  );
}

// ── Channel row ──────────────────────────────────────────────────────────────

function ChannelRow({
  ch,
  configs,
  onClick,
  isSelected,
}: {
  ch: Channel;
  configs: Record<string, ChannelConfig> | undefined;
  onClick: () => void;
  isSelected: boolean;
}) {
  const color = channelColor(ch.type);
  const cfg = configs?.[ch.id];
  const hasEmbeds = cfg && cfg.embedNames.length > 0;

  return (
    <button
      className="w-full flex items-center gap-2 px-2 py-1.5 rounded-lg transition-all text-left"
      style={{
        background: isSelected ? "rgba(99,102,241,0.12)" : "transparent",
        border: isSelected ? "1px solid rgba(99,102,241,0.25)" : "1px solid transparent",
        color: isSelected ? "#d1d5db" : "#6b7280",
      }}
      onClick={onClick}
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
      <span style={{ color, opacity: 0.8 }}>{channelIcon(ch.type)}</span>
      <span className="text-xs font-medium truncate flex-1">{ch.name}</span>
      {ch.nsfw && (
        <span className="text-[9px] px-1 py-0.5 rounded font-bold uppercase flex-shrink-0"
          style={{ background: "rgba(239,68,68,0.15)", color: "#f87171" }}>18+</span>
      )}
      {hasEmbeds && (
        <div className="flex items-center gap-0.5 flex-shrink-0">
          {cfg.embedNames.slice(0, 3).map((name, i) => {
            const embed = { category: "" } as EmbedTemplate;
            const catColor = "#6366f1";
            return (
              <div key={i} className="w-3 h-3 rounded-full border border-black/30"
                style={{ background: catColor, marginLeft: i > 0 ? "-4px" : 0 }} />
            );
          })}
          <span className="text-[9px] ml-1 font-bold" style={{ color: "#6366f1" }}>
            {cfg.embedNames.length}
          </span>
        </div>
      )}
    </button>
  );
}

// ── Category block ───────────────────────────────────────────────────────────

function CategoryBlock({
  cat,
  color,
  index,
  configs,
  selectedChannel,
  onSelectChannel,
}: {
  cat: ChannelCategory;
  color: string;
  index: number;
  configs: Record<string, ChannelConfig> | undefined;
  selectedChannel: Channel | null;
  onSelectChannel: (ch: Channel) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const textCount = cat.channels.filter(c => c.type === 0 || c.type === 5 || c.type === 15).length;
  const voiceCount = cat.channels.filter(c => c.type === 2 || c.type === 13).length;
  const configuredCount = cat.channels.filter(c => configs?.[c.id]?.embedNames.length).length;

  return (
    <div className="rounded-xl overflow-hidden" style={{ border: `1px solid rgba(255,255,255,0.06)`, background: "rgba(255,255,255,0.02)" }}>
      <button
        className="w-full flex items-center gap-3 px-4 py-3 transition-all"
        style={{ background: `${color}08`, borderBottom: collapsed ? "none" : `1px solid rgba(255,255,255,0.05)` }}
        onClick={() => setCollapsed(p => !p)}
      >
        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs flex-shrink-0 font-bold"
          style={{ background: `${color}15`, border: `1px solid ${color}30`, color }}>
          {index + 1}
        </div>
        <div className="flex-1 text-left">
          <div className="font-black text-white text-sm uppercase tracking-wide">{cat.name}</div>
          <div className="flex items-center gap-3 mt-0.5">
            {textCount > 0 && (
              <span className="text-[10px] flex items-center gap-1" style={{ color: "#6b7280" }}>
                <Hash className="w-3 h-3" />{textCount}
              </span>
            )}
            {voiceCount > 0 && (
              <span className="text-[10px] flex items-center gap-1" style={{ color: "#6b7280" }}>
                <Volume2 className="w-3 h-3" />{voiceCount}
              </span>
            )}
            {configuredCount > 0 && (
              <span className="text-[10px] flex items-center gap-1" style={{ color: "#6366f1" }}>
                📋 {configuredCount} embed
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="px-2 py-0.5 rounded-full text-[10px] font-bold"
            style={{ background: `${color}15`, color, border: `1px solid ${color}25` }}>
            {cat.channels.length}
          </div>
          {collapsed
            ? <ChevronRight className="w-4 h-4" style={{ color: "#4b5563" }} />
            : <ChevronDown className="w-4 h-4" style={{ color: "#4b5563" }} />
          }
        </div>
      </button>

      {!collapsed && (
        <div className="p-2 space-y-0.5">
          {cat.channels.length === 0 ? (
            <div className="text-center py-4 text-xs" style={{ color: "#374151" }}>Nema kanala</div>
          ) : (
            cat.channels.map(ch => (
              <ChannelRow
                key={ch.id}
                ch={ch}
                configs={configs}
                isSelected={selectedChannel?.id === ch.id}
                onClick={() => onSelectChannel(ch)}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function ServerPage() {
  const { data: channelData, isLoading: chLoading, isError: chError } = useChannels();
  const { data: guild } = useGuildInfo();
  const { data: embeds } = useEmbeds();
  const { data: configs } = useChannelConfigs();
  const saveConfig = useSaveChannelConfig();
  const { toast } = useToast();

  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);

  const handleSelectChannel = useCallback((ch: Channel) => {
    setSelectedChannel(prev => prev?.id === ch.id ? null : ch);
  }, []);

  const handleSave = useCallback((embedNames: string[], note: string) => {
    if (!selectedChannel) return;
    saveConfig.mutate(
      { channelId: selectedChannel.id, embedNames, note },
      {
        onSuccess: () => toast({ title: "Konfiguracija sačuvana" }),
        onError: () => toast({ title: "Greška pri čuvanju", variant: "destructive" }),
      }
    );
  }, [selectedChannel, saveConfig, toast]);

  const totalChannels = channelData
    ? channelData.categories.reduce((a, c) => a + c.channels.length, 0) + channelData.uncategorized.length
    : 0;

  const totalConfigured = configs ? Object.keys(configs).length : 0;

  if (chLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64 rounded-xl" style={{ background: "rgba(255,255,255,0.06)" }} />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-40 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />)}
        </div>
      </div>
    );
  }

  if (chError) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="text-4xl">⚠️</div>
        <div className="text-white font-bold">Greška pri učitavanju kanala</div>
        <div className="text-sm" style={{ color: "#6b7280" }}>Provjeri da li je DISCORD_TOKEN postavljen</div>
      </div>
    );
  }

  return (
    <div className="flex gap-0 -m-6 h-[calc(100vh-56px)]">
      {/* ── Left: channel browser ── */}
      <div className="flex-1 min-w-0 overflow-y-auto p-6">
        <div className="space-y-6 max-w-4xl">
          {/* Header */}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Server className="w-4 h-4" style={{ color: "#6366f1" }} />
                <span className="text-xs font-bold uppercase tracking-widest" style={{ color: "#3d3f5c" }}>Discord Server</span>
              </div>
              <div className="flex items-center gap-3">
                {guild?.icon && (
                  <img src={guild.icon} alt={guild.name}
                    className="w-12 h-12 rounded-2xl object-cover flex-shrink-0"
                    style={{ boxShadow: "0 0 24px rgba(99,102,241,0.4)" }} />
                )}
                <div>
                  <h1 className="text-3xl font-black text-white">{guild?.name ?? "GIAN Server"}</h1>
                  <p className="text-xs mt-0.5" style={{ color: "#374151" }}>
                    {guild?.memberCount?.toLocaleString()} članova · {channelData?.categories.length} kategorija · {totalChannels} kanala
                  </p>
                </div>
              </div>
            </div>
            <div className="flex gap-3 flex-wrap">
              {[
                { label: "Kategorije", value: channelData?.categories.length ?? 0, color: "#6366f1" },
                { label: "Kanali", value: totalChannels, color: "#22c55e" },
                { label: "Konfig.", value: totalConfigured, color: "#f59e0b" },
              ].map(s => (
                <div key={s.label} className="rounded-xl px-4 py-3 text-center"
                  style={{ background: `${s.color}08`, border: `1px solid ${s.color}20`, minWidth: "80px" }}>
                  <div className="text-xl font-black" style={{ color: s.color }}>{s.value}</div>
                  <div className="text-[10px] font-bold uppercase tracking-wide mt-0.5" style={{ color: "#4b5563" }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Hint */}
          <div className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg"
            style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.12)", color: "#6366f1" }}>
            💡 Klikni na kanal da vidiš ili dodaš embed konfiguraciju
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#2d3048" }}>Tip:</span>
            {[
              { icon: <Hash className="w-3 h-3" />, label: "Tekst", color: "#6b7280" },
              { icon: <Volume2 className="w-3 h-3" />, label: "Voice", color: "#22c55e" },
              { icon: <Megaphone className="w-3 h-3" />, label: "Announcement", color: "#f59e0b" },
              { icon: <HelpCircle className="w-3 h-3" />, label: "Forum", color: "#6366f1" },
            ].map(l => (
              <div key={l.label} className="flex items-center gap-1.5 text-[11px]" style={{ color: l.color }}>
                {l.icon} {l.label}
              </div>
            ))}
          </div>

          {/* Uncategorized */}
          {channelData && channelData.uncategorized.length > 0 && (
            <div className="rounded-xl overflow-hidden"
              style={{ border: "1px solid rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.02)" }}>
              <div className="flex items-center gap-3 px-4 py-3"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(255,255,255,0.01)" }}>
                <Layers className="w-4 h-4" style={{ color: "#4b5563" }} />
                <span className="font-black text-white text-sm uppercase tracking-wide">Nekategorizovani</span>
                <div className="px-2 py-0.5 rounded-full text-[10px] font-bold ml-auto"
                  style={{ background: "rgba(255,255,255,0.06)", color: "#6b7280" }}>
                  {channelData.uncategorized.length}
                </div>
              </div>
              <div className="p-2 space-y-0.5">
                {channelData.uncategorized.map(ch => (
                  <ChannelRow
                    key={ch.id}
                    ch={ch}
                    configs={configs}
                    isSelected={selectedChannel?.id === ch.id}
                    onClick={() => handleSelectChannel(ch)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Category grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {channelData?.categories.map((cat, i) => (
              <CategoryBlock
                key={cat.id}
                cat={cat}
                color={CATEGORY_PALETTE[i % CATEGORY_PALETTE.length]}
                index={i}
                configs={configs}
                selectedChannel={selectedChannel}
                onSelectChannel={handleSelectChannel}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ── Right: channel config panel ── */}
      {selectedChannel && (
        <div className="w-80 flex-shrink-0 flex flex-col overflow-hidden"
          style={{ borderLeft: "1px solid rgba(255,255,255,0.06)" }}>
          <ChannelPanel
            channel={selectedChannel}
            config={configs?.[selectedChannel.id]}
            embeds={embeds}
            onClose={() => setSelectedChannel(null)}
            onSave={handleSave}
            saving={saveConfig.isPending}
          />
        </div>
      )}
    </div>
  );
}
