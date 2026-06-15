import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import { useToast } from "@/hooks/use-toast";
import {
  Search, X, Plus, Gamepad2, DollarSign, Layers, Bird, Heart,
  Briefcase, Gift, Swords, Star, HelpCircle, Globe, BookOpen,
  Flame, AlertTriangle, Target, Users, ShoppingCart, Sparkles,
  Trophy, TrendingUp, Activity, ClipboardList, Crown, Wallet,
  CheckCircle, Music, Save, Dices,
} from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

interface GamesCfg {
  economy: {
    posao:  { enabled: boolean; cooldown_min: number; reward_min: number; reward_max: number };
    daily:  { enabled: boolean; cooldown_hours: number; reward_min: number; reward_max: number };
    kradi:  { enabled: boolean; cooldown_hours: number; success_rate: number; steal_min: number; steal_max: number };
  };
  gambling: {
    slots:        { enabled: boolean; cooldown_sec: number; max_bet: number; symbols: string[] };
    blackjack:    { enabled: boolean; cooldown_sec: number };
    poker:        { enabled: boolean; min_bet: number; max_bet: number };
    kviz:         { enabled: boolean; min_bet: number };
    geografija:   { enabled: boolean; min_bet: number };
    kpm:          { enabled: boolean };
    vjasala:      { enabled: boolean };
    kaladont:     { enabled: boolean; reward: number };
    toplo_hladno: { enabled: boolean };
    amogus:       { enabled: boolean };
  };
  animals: {
    hunt: { enabled: boolean; cooldown_sec: number };
  };
  social: { enabled: boolean };
  updatedAt: string | null;
}

const DEFAULTS: GamesCfg = {
  economy: {
    posao:  { enabled: true, cooldown_min: 30,  reward_min: 150, reward_max: 600 },
    daily:  { enabled: true, cooldown_hours: 24, reward_min: 300, reward_max: 800 },
    kradi:  { enabled: true, cooldown_hours: 2,  success_rate: 38, steal_min: 50, steal_max: 300 },
  },
  gambling: {
    slots:        { enabled: true, cooldown_sec: 15, max_bet: 1000000000, symbols: ["🍒","🍋","🍇","💎","🔔","⭐","🎰","🍀","👑"] },
    blackjack:    { enabled: true, cooldown_sec: 30 },
    poker:        { enabled: true, min_bet: 50,  max_bet: 50000 },
    kviz:         { enabled: true, min_bet: 10 },
    geografija:   { enabled: true, min_bet: 10 },
    kpm:          { enabled: true },
    vjasala:      { enabled: true },
    kaladont:     { enabled: true, reward: 1500 },
    toplo_hladno: { enabled: true },
    amogus:       { enabled: true },
  },
  animals: {
    hunt: { enabled: true, cooldown_sec: 7 },
  },
  social: { enabled: true },
  updatedAt: null,
};

type Tab = "ekonomija" | "kockanje" | "zivotinje" | "socijalno";

function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!value)}
      className="relative w-11 h-6 rounded-full transition-all flex-shrink-0"
      style={{ background: value ? "linear-gradient(90deg,#6366f1,#8b5cf6)" : "rgba(255,255,255,0.08)" }}
    >
      <div className="absolute top-0.5 w-5 h-5 rounded-full bg-white transition-all" style={{ left: value ? "calc(100% - 22px)" : "2px", boxShadow: "0 1px 4px rgba(0,0,0,0.4)" }} />
    </button>
  );
}

function NumInput({ value, onChange, min, max, suffix }: { value: number; onChange: (v: number) => void; min?: number; max?: number; suffix?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={e => onChange(Number(e.target.value))}
        className="w-24 px-3 py-1.5 rounded-lg text-sm text-white text-right outline-none"
        style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(99,102,241,0.2)" }}
        onFocus={e => e.currentTarget.style.border = "1px solid rgba(99,102,241,0.5)"}
        onBlur={e => e.currentTarget.style.border = "1px solid rgba(99,102,241,0.2)"}
      />
      {suffix && <span className="text-xs" style={{ color: "#6b7280" }}>{suffix}</span>}
    </div>
  );
}

function Card({ title, icon, badge, enabled, onToggle, children }: {
  title: string; icon: React.ReactNode; badge?: string; enabled: boolean;
  onToggle: (v: boolean) => void; children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl p-4" style={{
      background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)",
      opacity: enabled ? 1 : 0.55, transition: "opacity 0.2s"
    }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <span className="flex items-center">{icon}</span>
          <div>
            <span className="text-sm font-semibold text-white">{title}</span>
            {badge && <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded font-mono" style={{ background: "rgba(99,102,241,0.15)", color: "#818cf8" }}>{badge}</span>}
          </div>
        </div>
        <Toggle value={enabled} onChange={onToggle} />
      </div>
      {children && enabled && <div className="space-y-2.5 pt-2 border-t" style={{ borderColor: "rgba(255,255,255,0.05)" }}>{children}</div>}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs" style={{ color: "#9ca3af" }}>{label}</span>
      {children}
    </div>
  );
}

function TabBtn({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all whitespace-nowrap"
      style={{
        background: active ? "rgba(99,102,241,0.2)" : "transparent",
        color: active ? "#a5b4fc" : "#6b7280",
        border: active ? "1px solid rgba(99,102,241,0.3)" : "1px solid transparent",
      }}
    >
      {children}
    </button>
  );
}

// ── Slot Symbol Helpers ───────────────────────────────────────────────────────

function renderSymbol(sym: string, size = 22) {
  const m = sym.match(/^<(a?):([^:]+):(\d+)>$/);
  if (m) {
    const ext = m[1] === "a" ? "gif" : "png";
    return <img src={`https://cdn.discordapp.com/emojis/${m[3]}.${ext}?size=48`} alt={`:${m[2]}:`} title={`:${m[2]}:`} style={{ width: size, height: size }} className="object-contain flex-shrink-0" />;
  }
  return <span style={{ fontSize: size * 0.85, lineHeight: 1 }}>{sym}</span>;
}

interface DiscordEmojiItem { id: string; name: string; animated: boolean; }

function SlotEmojiPicker({ onSelect, onClose }: { onSelect: (md: string) => void; onClose: () => void }) {
  const [emojis, setEmojis] = useState<DiscordEmojiItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch(`${BASE}/api/discord/emojis`)
      .then(r => r.json())
      .then((d: DiscordEmojiItem[]) => { setEmojis(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [onClose]);

  const filtered = useMemo(() =>
    !search ? emojis : emojis.filter(e => e.name.toLowerCase().includes(search.toLowerCase())),
  [emojis, search]);

  return (
    <div ref={ref} className="absolute z-50 bottom-full mb-2 left-0 w-72 rounded-xl shadow-2xl overflow-hidden"
      style={{ background: "#1E1F22", border: "1px solid #2B2D31" }}>
      <div className="p-2 border-b" style={{ borderColor: "#2B2D31" }}>
        <div className="flex items-center gap-2 rounded px-2" style={{ background: "#313338" }}>
          <Search className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "#949BA4" }} />
          <input
            autoFocus
            placeholder="Pretraži emoji..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 bg-transparent text-sm py-1.5 outline-none"
            style={{ color: "#F2F3F5" }}
          />
          {search && <button onClick={() => setSearch("")} style={{ color: "#949BA4" }}><X className="w-3 h-3" /></button>}
        </div>
      </div>
      <div className="overflow-y-auto" style={{ maxHeight: "200px" }}>
        {loading && <div className="flex items-center justify-center h-16 text-sm" style={{ color: "#949BA4" }}>Učitavam...</div>}
        <div className="grid grid-cols-9 gap-0.5 p-2">
          {filtered.map(emoji => {
            const ext = emoji.animated ? "gif" : "png";
            const md = emoji.animated ? `<a:${emoji.name}:${emoji.id}>` : `<:${emoji.name}:${emoji.id}>`;
            return (
              <button key={emoji.id} title={`:${emoji.name}:`} onClick={() => { onSelect(md); onClose(); }}
                className="w-8 h-8 flex items-center justify-center rounded hover:bg-[#313338] transition-colors">
                <img src={`https://cdn.discordapp.com/emojis/${emoji.id}.${ext}?size=32`} alt={emoji.name} className="w-6 h-6 object-contain" loading="lazy" />
              </button>
            );
          })}
        </div>
        {!loading && filtered.length === 0 && (
          <div className="flex items-center justify-center h-12 text-sm" style={{ color: "#949BA4" }}>Nema rezultata</div>
        )}
      </div>
      <div className="px-3 py-1.5 border-t text-[10px]" style={{ borderColor: "#2B2D31", color: "#5C5F66" }}>
        {filtered.length} emoji-ja
      </div>
    </div>
  );
}

function SlotSymbolsEditor({ symbols, onChange }: { symbols: string[]; onChange: (s: string[]) => void }) {
  const [showPicker, setShowPicker] = useState(false);
  const [input, setInput] = useState("");

  const addSymbol = useCallback((md: string) => {
    const val = md.trim();
    if (!val || symbols.includes(val)) return;
    onChange([...symbols, val]);
    setInput("");
  }, [symbols, onChange]);

  const removeSymbol = useCallback((i: number) => onChange(symbols.filter((_, idx) => idx !== i)), [symbols, onChange]);

  return (
    <div className="space-y-2 pt-1">
      <div className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: "#6b7280" }}>
        Simboli na slotovima ({symbols.length})
      </div>
      <div className="flex flex-wrap gap-1.5 p-2.5 rounded-lg min-h-[44px]"
        style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)" }}>
        {symbols.map((sym, i) => (
          <div key={i} className="flex items-center gap-1 px-1.5 py-1 rounded-md group"
            style={{ background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.2)" }}>
            {renderSymbol(sym, 18)}
            <button onClick={() => removeSymbol(i)}
              className="opacity-0 group-hover:opacity-100 transition-opacity w-3.5 h-3.5 flex items-center justify-center rounded"
              style={{ color: "#ef4444" }} title="Ukloni">
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
        {symbols.length === 0 && <span className="text-xs self-center" style={{ color: "#6b7280" }}>Nema simbola — dodaj ispod</span>}
      </div>
      <div className="relative flex gap-1.5">
        <input
          placeholder='<:ime:id> ili 🎰'
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") addSymbol(input); }}
          className="flex-1 px-2.5 py-1.5 rounded-lg text-xs outline-none font-mono"
          style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(99,102,241,0.2)", color: "#F2F3F5" }}
        />
        <button onClick={() => setShowPicker(p => !p)}
          className="px-2.5 py-1.5 rounded-lg text-sm transition-all"
          style={{ background: showPicker ? "rgba(99,102,241,0.25)" : "rgba(99,102,241,0.12)", color: "#a5b4fc", border: "1px solid rgba(99,102,241,0.25)" }}
          title="Odaberi custom emoji">
          😊
        </button>
        <button onClick={() => addSymbol(input)}
          className="px-2 py-1.5 rounded-lg transition-all"
          style={{ background: "rgba(99,102,241,0.2)", color: "#a5b4fc", border: "1px solid rgba(99,102,241,0.3)" }}
          title="Dodaj simbol">
          <Plus className="w-3.5 h-3.5" />
        </button>
        {showPicker && (
          <SlotEmojiPicker
            onSelect={(md) => { addSymbol(md); setShowPicker(false); }}
            onClose={() => setShowPicker(false)}
          />
        )}
      </div>
      <div className="text-[10px]" style={{ color: "#4B5563" }}>
        Upiši emoji (🍒) ili Discord format (<code style={{ color: "#818cf8" }}>&lt;a:ime:id&gt;</code>) i pritisni Enter
      </div>
    </div>
  );
}

function InfoCard({ icon, name, cmd, desc, info }: { icon: React.ReactNode; name: string; cmd?: string; desc: string; info: string }) {
  return (
    <div className="rounded-xl p-4" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
      <div className="flex items-center gap-2.5 mb-2">
        <span className="flex items-center">{icon}</span>
        <div>
          <span className="text-sm font-semibold text-white">{desc}</span>
          <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded font-mono" style={{ background: "rgba(99,102,241,0.15)", color: "#818cf8" }}>{cmd ?? name}</span>
        </div>
      </div>
      <p className="text-xs" style={{ color: "#6b7280" }}>{info}</p>
      <div className="mt-2 text-[10px] px-2 py-1 rounded inline-flex items-center gap-1" style={{ background: "rgba(34,197,94,0.08)", color: "#22c55e", border: "1px solid rgba(34,197,94,0.15)" }}>
        <CheckCircle className="w-3 h-3" /> Uvijek aktivno
      </div>
    </div>
  );
}

export default function Games() {
  const [cfg, setCfg] = useState<GamesCfg>(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetch(`${BASE}/api/games`)
      .then(r => r.json())
      .then(d => setCfg(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const [tab, setTab] = useState<Tab>("ekonomija");

  function setEco<K extends keyof GamesCfg["economy"]>(cmd: K, field: string, val: unknown) {
    setCfg(c => ({ ...c, economy: { ...c.economy, [cmd]: { ...c.economy[cmd], [field]: val } } }));
  }
  function setGamble<K extends keyof GamesCfg["gambling"]>(cmd: K, field: string, val: unknown) {
    setCfg(c => ({ ...c, gambling: { ...c.gambling, [cmd]: { ...c.gambling[cmd], [field]: val } } }));
  }
  function setAnimals(field: string, val: unknown) {
    setCfg(c => ({ ...c, animals: { ...c.animals, hunt: { ...c.animals.hunt, [field]: val } } }));
  }

  async function handleSave() {
    setSaving(true);
    try {
      const r = await fetch(`${BASE}/api/games`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cfg)
      });
      if (!r.ok) throw new Error();
      const updated = await r.json();
      setCfg(updated);
      toast({ title: "Sačuvano!", description: "Bot preuzima promjene za 5 minuta." });
    } catch {
      toast({ title: "Greška!", description: "Nije moguće sačuvati podešavanja.", variant: "destructive" });
    } finally { setSaving(false); }
  }

  function handleReset() {
    setCfg(DEFAULTS);
    toast({ title: "Resetovano", description: "Vraćene su zadane vrijednosti (još nije sačuvano)." });
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="flex gap-1.5">{[0,1,2].map(i => <div key={i} className="w-2 h-2 rounded-full animate-bounce" style={{ background: "#6366f1", animationDelay: `${i*0.15}s` }} />)}</div>
    </div>
  );

  const eco = cfg.economy;
  const gam = cfg.gambling;
  const ani = cfg.animals;

  const gameCmds: { key: string; icon: React.ReactNode; name: string; badge: string }[] = [
    { key: "slots",        icon: <Star         className="w-5 h-5" style={{ color: "#f59e0b" }} />, name: "Slots",              badge: "/slots"         },
    { key: "blackjack",    icon: <Layers       className="w-5 h-5" style={{ color: "#3b82f6" }} />, name: "Blackjack",          badge: "/blackjack"     },
    { key: "poker",        icon: <Trophy       className="w-5 h-5" style={{ color: "#f59e0b" }} />, name: "Poker",              badge: "/poker"         },
    { key: "kviz",         icon: <HelpCircle   className="w-5 h-5" style={{ color: "#8b5cf6" }} />, name: "Kviz",               badge: "/kviz"          },
    { key: "geografija",   icon: <Globe        className="w-5 h-5" style={{ color: "#22c55e" }} />, name: "Geografija",         badge: "/geografija"    },
    { key: "kpm",          icon: <Swords       className="w-5 h-5" style={{ color: "#ef4444" }} />, name: "Kamen-Papir-Makaze", badge: "/kpm"           },
    { key: "vjasala",      icon: <BookOpen     className="w-5 h-5" style={{ color: "#a5b4fc" }} />, name: "Vješala",            badge: "/vjasala"       },
    { key: "kaladont",     icon: <BookOpen     className="w-5 h-5" style={{ color: "#818cf8" }} />, name: "Kaladont",           badge: "/kaladont"      },
    { key: "toplo_hladno", icon: <Flame        className="w-5 h-5" style={{ color: "#f97316" }} />, name: "Toplo-Hladno",       badge: "/toplo-hladno"  },
    { key: "amogus",       icon: <AlertTriangle className="w-5 h-5" style={{ color: "#ef4444" }} />, name: "Among Us",          badge: "/amogus"        },
  ];

  const socialCmds = [
    { icon: <Heart      className="w-5 h-5" style={{ color: "#f472b6" }} />, name: "/zagrljaj", desc: "Zagrli korisnika"          },
    { icon: <Heart      className="w-5 h-5" style={{ color: "#fb7185" }} />, name: "/poljubac", desc: "Poljubi korisnika"          },
    { icon: <Sparkles   className="w-5 h-5" style={{ color: "#c084fc" }} />, name: "/mazi",     desc: "Pogali korisnika"           },
    { icon: <Heart      className="w-5 h-5" style={{ color: "#f9a8d4" }} />, name: "/tapsi",    desc: "Tapni korisnika"            },
    { icon: <Users      className="w-5 h-5" style={{ color: "#60a5fa" }} />, name: "/high5",    desc: "High five!"                 },
    { icon: <AlertTriangle className="w-5 h-5" style={{ color: "#fbbf24" }} />, name: "/cudan", desc: "Diraj korisnika"            },
    { icon: <Heart      className="w-5 h-5" style={{ color: "#ef4444" }} />, name: "/srce",     desc: "Pošalji srce"               },
    { icon: <Sparkles   className="w-5 h-5" style={{ color: "#f59e0b" }} />, name: "/brak",     desc: "Zaprositi korisnika"        },
    { icon: <Star       className="w-5 h-5" style={{ color: "#a78bfa" }} />, name: "/kompli",   desc: "Kompliment"                 },
    { icon: <Music      className="w-5 h-5" style={{ color: "#818cf8" }} />, name: "/fora",     desc: "Ispričaj foru"              },
    { icon: <Heart      className="w-5 h-5" style={{ color: "#f472b6" }} />, name: "/muv",      desc: "Napravi muv"                },
    { icon: <Heart      className="w-5 h-5" style={{ color: "#ec4899" }} />, name: "/crush",    desc: "Nasumičan crush sa servera" },
  ];

  return (
    <div className="space-y-5">
      {/* ── Header ── */}
      <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)" }}>
        {/* Top bar */}
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(99,102,241,0.04)" }}>
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "rgba(99,102,241,0.18)", border: "1px solid rgba(99,102,241,0.3)", boxShadow: "0 0 16px rgba(99,102,241,0.15)" }}>
              <Gamepad2 className="w-6 h-6 text-[#a5b4fc]" />
            </div>
            <div>
              <h1 className="text-lg font-black text-white tracking-tight">Igre & Ekonomija</h1>
              <p className="text-[11px] mt-0.5" style={{ color: "#6b7280" }}>
                Konfiguracija svih igara i ekonomije — bot čita promjene svakih 5 minuta
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-semibold transition-all"
              style={{ background: "rgba(255,255,255,0.05)", color: "#9ca3af", border: "1px solid rgba(255,255,255,0.09)" }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)"; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)"; }}>
              ↺ Resetuj
            </button>
            <button onClick={handleSave} disabled={saving}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
              style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "white", opacity: saving ? 0.7 : 1, boxShadow: "0 2px 12px rgba(99,102,241,0.3)" }}>
              <Save className="w-4 h-4" />
              {saving ? "Čuvanje..." : "Sačuvaj"}
            </button>
          </div>
        </div>

        {/* ── Tabs ── */}
        <div className="flex gap-1 px-3 py-2 overflow-x-auto">
          {([
            { key: "ekonomija", icon: <DollarSign className="w-4 h-4" />, label: "Ekonomija" },
            { key: "kockanje",  icon: <Dices      className="w-4 h-4" />, label: "Kockanje"  },
            { key: "zivotinje", icon: <Bird       className="w-4 h-4" />, label: "Životinje" },
            { key: "socijalno", icon: <Heart      className="w-4 h-4" />, label: "Socijalno" },
          ] as { key: Tab; icon: React.ReactNode; label: string }[]).map(t => (
            <TabBtn key={t.key} active={tab === t.key} onClick={() => setTab(t.key)}>
              {t.icon}
              {t.label}
            </TabBtn>
          ))}
        </div>
      </div>

      {/* ── EKONOMIJA ── */}
      {tab === "ekonomija" && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Card icon={<Briefcase className="w-5 h-5 text-[#a5b4fc]" />} title="Posao" badge="/posao" enabled={eco.posao.enabled} onToggle={v => setEco("posao", "enabled", v)}>
            <Row label="Cooldown"><NumInput value={eco.posao.cooldown_min} onChange={v => setEco("posao","cooldown_min",v)} min={1} max={1440} suffix="min" /></Row>
            <Row label="Min nagrada"><NumInput value={eco.posao.reward_min} onChange={v => setEco("posao","reward_min",v)} min={1} suffix="novca" /></Row>
            <Row label="Max nagrada"><NumInput value={eco.posao.reward_max} onChange={v => setEco("posao","reward_max",v)} min={1} suffix="novca" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              Nagrada: <b>{eco.posao.reward_min}–{eco.posao.reward_max}</b> · CD: <b>{eco.posao.cooldown_min}min</b>
            </div>
          </Card>

          <Card icon={<Gift className="w-5 h-5 text-[#f472b6]" />} title="Daily" badge="/daily" enabled={eco.daily.enabled} onToggle={v => setEco("daily","enabled",v)}>
            <Row label="Cooldown"><NumInput value={eco.daily.cooldown_hours} onChange={v => setEco("daily","cooldown_hours",v)} min={1} max={72} suffix="h" /></Row>
            <Row label="Min nagrada"><NumInput value={eco.daily.reward_min} onChange={v => setEco("daily","reward_min",v)} min={1} suffix="novca" /></Row>
            <Row label="Max nagrada"><NumInput value={eco.daily.reward_max} onChange={v => setEco("daily","reward_max",v)} min={1} suffix="novca" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              Nagrada: <b>{eco.daily.reward_min}–{eco.daily.reward_max}</b> · CD: <b>{eco.daily.cooldown_hours}h</b>
            </div>
          </Card>

          <Card icon={<Swords className="w-5 h-5 text-[#ef4444]" />} title="Kradi" badge="/kradi" enabled={eco.kradi.enabled} onToggle={v => setEco("kradi","enabled",v)}>
            <Row label="Cooldown"><NumInput value={eco.kradi.cooldown_hours} onChange={v => setEco("kradi","cooldown_hours",v)} min={1} max={48} suffix="h" /></Row>
            <Row label="Šansa uspjeha"><NumInput value={eco.kradi.success_rate} onChange={v => setEco("kradi","success_rate",v)} min={1} max={99} suffix="%" /></Row>
            <Row label="Min krađa"><NumInput value={eco.kradi.steal_min} onChange={v => setEco("kradi","steal_min",v)} min={1} suffix="novca" /></Row>
            <Row label="Max krađa"><NumInput value={eco.kradi.steal_max} onChange={v => setEco("kradi","steal_max",v)} min={1} suffix="novca" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              Šansa: <b>{eco.kradi.success_rate}%</b> · Krađa: <b>{eco.kradi.steal_min}–{eco.kradi.steal_max}</b>
            </div>
          </Card>

          {([
            { icon: <Wallet        className="w-5 h-5 text-[#a5b4fc]" />, name: "/baki",        desc: "Provjera balansa",  info: "Prikazuje balans i zadnji rad"       },
            { icon: <Heart         className="w-5 h-5 text-[#f472b6]" />, name: "/daj",         desc: "Transfer para",     info: "Pošalji pare drugaru"                },
            { icon: <TrendingUp    className="w-5 h-5 text-[#22c55e]" />, name: "/rank",        desc: "Level & XP",        info: "Prikazuje tvoj rank i napredak"      },
            { icon: <Activity      className="w-5 h-5 text-[#60a5fa]" />, name: "/aktivnost",   desc: "Aktivnost",         info: "Detaljna statistika aktivnosti"      },
            { icon: <Trophy        className="w-5 h-5 text-[#f59e0b]" />, name: "/leaderboard", desc: "Top lista",         info: "Top 10 po XP-u ili bogatstvu"        },
            { icon: <ShoppingCart  className="w-5 h-5 text-[#c084fc]" />, name: "/shop",        desc: "Shop",              info: "Kupovina boost predmeta"             },
            { icon: <ClipboardList className="w-5 h-5 text-[#818cf8]" />, name: "/quests",      desc: "Zadaci",            info: "3 dnevna zadatka s nagradama"        },
          ].map(c => (
            <InfoCard key={c.name} icon={c.icon} name={c.name} cmd={c.name} desc={c.desc} info={c.info} />
          )))}

        </div>
      )}

      {/* ── KOCKANJE ── */}
      {tab === "kockanje" && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Card icon={<Star className="w-5 h-5 text-[#f59e0b]" />} title="Slots" badge="/slots" enabled={gam.slots.enabled} onToggle={v => setGamble("slots","enabled",v)}>
            <Row label="Cooldown"><NumInput value={gam.slots.cooldown_sec} onChange={v => setGamble("slots","cooldown_sec",v)} min={1} max={3600} suffix="sek" /></Row>
            <Row label="Max opklada"><NumInput value={gam.slots.max_bet} onChange={v => setGamble("slots","max_bet",v)} min={20} suffix="novca" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              CD: <b>{gam.slots.cooldown_sec}s</b> · Max: <b>{gam.slots.max_bet.toLocaleString()}</b>
            </div>
            <SlotSymbolsEditor
              symbols={gam.slots.symbols ?? []}
              onChange={syms => setCfg(c => ({ ...c, gambling: { ...c.gambling, slots: { ...c.gambling.slots, symbols: syms } } }))}
            />
          </Card>

          <Card icon={<Layers className="w-5 h-5 text-[#3b82f6]" />} title="Blackjack" badge="/blackjack" enabled={gam.blackjack.enabled} onToggle={v => setGamble("blackjack","enabled",v)}>
            <Row label="Cooldown"><NumInput value={gam.blackjack.cooldown_sec} onChange={v => setGamble("blackjack","cooldown_sec",v)} min={1} max={3600} suffix="sek" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              CD: <b>{gam.blackjack.cooldown_sec}s</b>
            </div>
          </Card>

          <Card icon={<Trophy className="w-5 h-5 text-[#f59e0b]" />} title="Poker" badge="/poker" enabled={gam.poker.enabled} onToggle={v => setGamble("poker","enabled",v)}>
            <Row label="Min opklada"><NumInput value={gam.poker.min_bet} onChange={v => setGamble("poker","min_bet",v)} min={1} suffix="novca" /></Row>
            <Row label="Max opklada"><NumInput value={gam.poker.max_bet} onChange={v => setGamble("poker","max_bet",v)} min={1} suffix="novca" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              Opklada: <b>{gam.poker.min_bet}–{gam.poker.max_bet.toLocaleString()}</b>
            </div>
          </Card>

          <Card icon={<HelpCircle className="w-5 h-5 text-[#8b5cf6]" />} title="Kviz" badge="/kviz" enabled={gam.kviz.enabled} onToggle={v => setGamble("kviz","enabled",v)}>
            <Row label="Min opklada"><NumInput value={gam.kviz.min_bet} onChange={v => setGamble("kviz","min_bet",v)} min={1} suffix="novca" /></Row>
          </Card>

          <Card icon={<Globe className="w-5 h-5 text-[#22c55e]" />} title="Geografija" badge="/geografija" enabled={gam.geografija.enabled} onToggle={v => setGamble("geografija","enabled",v)}>
            <Row label="Min opklada"><NumInput value={gam.geografija.min_bet} onChange={v => setGamble("geografija","min_bet",v)} min={1} suffix="novca" /></Row>
          </Card>

          <Card icon={<BookOpen className="w-5 h-5 text-[#818cf8]" />} title="Kaladont" badge="/kaladont" enabled={gam.kaladont.enabled} onToggle={v => setGamble("kaladont","enabled",v)}>
            <Row label="Nagrada za pobjedu"><NumInput value={gam.kaladont.reward} onChange={v => setGamble("kaladont","reward",v)} min={0} suffix="novca" /></Row>
            <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
              Pobjednička nagrada: <b>{gam.kaladont.reward} novca + 200 XP</b>
            </div>
          </Card>

          {gameCmds.filter(g => ["kpm","vjasala","toplo_hladno","amogus"].includes(g.key)).map(g => (
            <Card key={g.key} icon={g.icon} title={g.name} badge={g.badge}
              enabled={(gam[g.key as keyof typeof gam] as { enabled: boolean }).enabled}
              onToggle={v => setGamble(g.key as keyof GamesCfg["gambling"], "enabled", v)}
            />
          ))}
        </div>
      )}

      {/* ── ŽIVOTINJE ── */}
      {tab === "zivotinje" && (
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <Card icon={<Target className="w-5 h-5 text-[#22c55e]" />} title="Hunt" badge="/hunt" enabled={ani.hunt.enabled} onToggle={v => setAnimals("enabled",v)}>
              <Row label="Cooldown"><NumInput value={ani.hunt.cooldown_sec} onChange={v => setAnimals("cooldown_sec",v)} min={1} max={600} suffix="sek" /></Row>
              <div className="text-[10px] px-2 py-1.5 rounded" style={{ background: "rgba(99,102,241,0.08)", color: "#818cf8" }}>
                CD: <b>{ani.hunt.cooldown_sec}s</b> · Lovstvo od Common do Mythical
              </div>
            </Card>

            {([
              { icon: <Users        className="w-5 h-5 text-[#22c55e]" />, name: "Zoo",     cmd: "/zoo",     desc: "Prikazuje kolekciju uhvaćenih životinja i ukupnu moć" },
              { icon: <Swords       className="w-5 h-5 text-[#ef4444]" />, name: "Battle",  cmd: "/battle",  desc: "Dvoboj sa drugim korisnikom na osnovu Zoo Power-a"    },
              { icon: <ShoppingCart className="w-5 h-5 text-[#a5b4fc]" />, name: "Sell",    cmd: "/sell",    desc: "Prodaj životinje za novac"                            },
              { icon: <BookOpen     className="w-5 h-5 text-[#818cf8]" />, name: "Animals", cmd: "/animals", desc: "Lista svih životinja s raritetom i vrijednostima"     },
              { icon: <Sparkles     className="w-5 h-5 text-[#f472b6]" />, name: "Pray",    cmd: "/pray",    desc: "Pomoli se za korisnika — nasumičan bonus 20–100"      },
            ]).map(c => (
              <InfoCard key={c.cmd} icon={c.icon} name={c.name} cmd={c.cmd} desc={c.name} info={c.desc} />
            ))}
          </div>

          {/* Rarity table */}
          <div className="rounded-xl p-5" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="flex items-center gap-2 mb-4">
              <Crown className="w-4 h-4 text-[#f59e0b]" />
              <span className="text-sm font-semibold text-white">Raritet životinja</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
              {[
                { r: "Common",    color: "#9ca3af", emoji: "🐇" },
                { r: "Uncommon",  color: "#22c55e", emoji: "🦊" },
                { r: "Rare",      color: "#3b82f6", emoji: "🐺" },
                { r: "Epic",      color: "#8b5cf6", emoji: "🦁" },
                { r: "Legendary", color: "#f59e0b", emoji: "🐉" },
                { r: "Mythical",  color: "#ef4444", emoji: "🔥" },
              ].map(x => (
                <div key={x.r} className="rounded-lg p-3 text-center" style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${x.color}33` }}>
                  <div className="flex justify-center mb-1.5 text-2xl">{x.emoji}</div>
                  <div className="text-xs font-semibold" style={{ color: x.color }}>{x.r}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── SOCIJALNO ── */}
      {tab === "socijalno" && (
        <div className="space-y-4">
          {/* Global toggle */}
          <div className="rounded-xl p-4 flex items-center justify-between" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.2)" }}>
            <div>
              <div className="text-sm font-semibold text-white">Sve socijalne komande</div>
              <div className="text-xs mt-0.5" style={{ color: "#6b7280" }}>Uključi ili isključi cijelu kategoriju odjednom</div>
            </div>
            <Toggle value={cfg.social.enabled} onChange={v => setCfg(c => ({ ...c, social: { enabled: v } }))} />
          </div>

          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4" style={{ opacity: cfg.social.enabled ? 1 : 0.5, transition: "opacity 0.2s" }}>
            {socialCmds.map(c => (
              <div key={c.name} className="rounded-xl p-4" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
                <div className="flex items-center gap-2 mb-1.5">
                  {c.icon}
                  <span className="text-sm font-mono font-semibold" style={{ color: "#a5b4fc" }}>{c.name}</span>
                </div>
                <p className="text-xs" style={{ color: "#6b7280" }}>{c.desc}</p>
              </div>
            ))}
          </div>

          {/* Specijalne komande */}
          <div className="rounded-xl p-5" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="flex items-center gap-2 mb-3">
              <Music className="w-4 h-4 text-[#818cf8]" />
              <span className="text-sm font-semibold text-white">Specijalne komande</span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg p-3" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)" }}>
                <div className="flex items-center gap-2 mb-1">
                  <Music className="w-5 h-5 text-[#818cf8]" />
                  <span className="font-mono text-sm" style={{ color: "#a5b4fc" }}>/vers</span>
                </div>
                <p className="text-xs" style={{ color: "#6b7280" }}>Pošalji hip-hop vers u poseban kanal (VERS_CHANNEL_ID)</p>
              </div>
              <div className="rounded-lg p-3" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)" }}>
                <div className="flex items-center gap-2 mb-1">
                  <Gift className="w-5 h-5 text-[#f472b6]" />
                  <span className="font-mono text-sm" style={{ color: "#a5b4fc" }}>/giveaway</span>
                </div>
                <p className="text-xs" style={{ color: "#6b7280" }}>Pokretanje i završetak nagradnih igara</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Last saved */}
      {cfg.updatedAt && (
        <p className="text-xs text-center" style={{ color: "#374151" }}>
          Zadnje sačuvano: {new Date(cfg.updatedAt).toLocaleString("bs-BA")}
        </p>
      )}
    </div>
  );
}
