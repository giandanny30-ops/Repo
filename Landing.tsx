import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Save, Shield, ShieldAlert, ShieldCheck, RefreshCw, Plus, X, AlertTriangle } from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

interface Protection {
  antiRaid: {
    enabled: boolean;
    windowSeconds: number;
    joinLimit: number;
    suspiciousAgeDays: number;
    lockdownMinutes: number;
    action: "kick" | "ban" | "alert_only";
  };
  antiNsfw: {
    enabled: boolean;
    strikesBeforeTimeout: number;
    timeoutMinutes: number;
    extraBlockedSites: string[];
    extraBlockedKeywords: string[];
  };
  updatedAt: string | null;
}

// ─── Toggle ────────────────────────────────────────────────────────────────
function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="relative inline-flex w-12 h-6 rounded-full transition-all duration-200 flex-shrink-0 focus:outline-none"
      style={{
        background: checked ? "#3ba55c" : "rgba(255,255,255,0.08)",
        border: checked ? "none" : "1px solid rgba(255,255,255,0.12)",
        boxShadow: checked ? "0 0 14px rgba(59,165,92,0.4)" : "none",
      }}
    >
      <span
        className="absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform duration-200"
        style={{ transform: checked ? "translateX(26px)" : "translateX(2px)", boxShadow: "0 1px 4px rgba(0,0,0,0.4)" }}
      />
    </button>
  );
}

// ─── Number Input ──────────────────────────────────────────────────────────
function NumInput({ value, onChange, min, max, suffix }: { value: number; onChange: (v: number) => void; min?: number; max?: number; suffix?: string }) {
  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={e => onChange(Math.max(min ?? 0, Math.min(max ?? 9999, Number(e.target.value))))}
        className="w-20 px-2.5 py-1.5 rounded-lg text-sm text-center focus:outline-none"
        style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", color: "#e2e8f0" }}
      />
      {suffix && <span className="text-xs" style={{ color: "#6b7280" }}>{suffix}</span>}
    </div>
  );
}

// ─── Tag Input ─────────────────────────────────────────────────────────────
function TagInput({ tags, onChange, placeholder }: { tags: string[]; onChange: (t: string[]) => void; placeholder?: string }) {
  const [input, setInput] = useState("");
  const add = () => {
    const v = input.trim().toLowerCase();
    if (v && !tags.includes(v)) onChange([...tags, v]);
    setInput("");
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1.5 min-h-[28px]">
        {tags.map(t => (
          <span key={t} className="flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-mono"
            style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.25)", color: "#a5b4fc" }}>
            {t}
            <button type="button" onClick={() => onChange(tags.filter(x => x !== t))} className="opacity-60 hover:opacity-100">
              <X size={10} />
            </button>
          </span>
        ))}
        {tags.length === 0 && <span className="text-xs" style={{ color: "#4b5563" }}>Nema dodatnih stavki</span>}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder={placeholder}
          className="flex-1 px-2.5 py-1.5 rounded-lg text-xs focus:outline-none"
          style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", color: "#e2e8f0" }}
        />
        <button type="button" onClick={add}
          className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs transition-colors"
          style={{ background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.2)", color: "#a5b4fc" }}>
          <Plus size={11} /> Dodaj
        </button>
      </div>
    </div>
  );
}

// ─── Setting Row ───────────────────────────────────────────────────────────
function SettingRow({ label, desc, children }: { label: string; desc?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between py-3.5" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
      <div className="flex-1 min-w-0 mr-6">
        <div className="text-sm font-medium text-white">{label}</div>
        {desc && <div className="text-xs mt-0.5" style={{ color: "#6b7280" }}>{desc}</div>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

// ─── Section Card ──────────────────────────────────────────────────────────
function SectionCard({ title, icon, enabled, onToggle, children, color }: {
  title: string; icon: React.ReactNode; enabled: boolean;
  onToggle: (v: boolean) => void; children: React.ReactNode; color: string;
}) {
  return (
    <div className="rounded-xl overflow-hidden" style={{ border: `1px solid ${enabled ? color + "30" : "rgba(255,255,255,0.06)"}`, background: "rgba(255,255,255,0.02)" }}>
      <div className="flex items-center justify-between px-5 py-4"
        style={{ background: enabled ? `${color}08` : "rgba(255,255,255,0.015)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: enabled ? `${color}18` : "rgba(255,255,255,0.05)", color: enabled ? color : "#6b7280" }}>
            {icon}
          </div>
          <div>
            <div className="text-sm font-bold text-white flex items-center gap-2">
              {title}
              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold"
                style={{ background: enabled ? `${color}20` : "rgba(255,255,255,0.05)", color: enabled ? color : "#6b7280" }}>
                {enabled ? "AKTIVAN" : "ISKLJUČEN"}
              </span>
            </div>
          </div>
        </div>
        <Toggle checked={enabled} onChange={onToggle} />
      </div>
      {enabled && <div className="px-5 py-1">{children}</div>}
      {!enabled && (
        <div className="px-5 py-4 text-xs" style={{ color: "#4b5563" }}>
          Klikni toggle gore da aktiviraš zaštitu.
        </div>
      )}
    </div>
  );
}

// ─── Main Page ─────────────────────────────────────────────────────────────
export default function Protection() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery<Protection>({
    queryKey: ["protection"],
    queryFn: async () => {
      const r = await fetch(`${BASE}/api/protection`);
      if (!r.ok) throw new Error("Greška pri učitavanju");
      return r.json();
    },
    staleTime: 30_000,
  });

  const [cfg, setCfg] = useState<Protection | null>(null);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (data && !dirty) setCfg(data);
  }, [data, dirty]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${BASE}/api/protection`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cfg),
      });
      if (!r.ok) throw new Error("Greška pri čuvanju");
      return r.json();
    },
    onSuccess: (saved) => {
      toast({ title: "✅ Zaštita sačuvana", description: "Bot će primijeniti nova podešavanja za ~2 min." });
      queryClient.setQueryData(["protection"], saved);
      setDirty(false);
    },
    onError: (e: Error) => toast({ title: "Greška", description: e.message, variant: "destructive" }),
  });

  function patch<K extends keyof Protection>(section: K, updates: Partial<Protection[K]>) {
    setCfg(prev => prev ? { ...prev, [section]: { ...(prev[section] as object), ...updates } } : prev);
    setDirty(true);
  }

  if (isLoading || !cfg) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48 rounded-lg" style={{ background: "rgba(255,255,255,0.06)" }} />
        <Skeleton className="h-64 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
        <Skeleton className="h-64 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
      </div>
    );
  }

  return (
    <div className="space-y-5 max-w-3xl" style={{ animation: "fadeSlideUp 0.35s ease both" }}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldCheck size={20} className="text-green-400" /> Zaštita Servera
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "#6b7280" }}>
            Anti-Raid i Anti-NSFW podešavanja — bot čita promjene automatski
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => { refetch(); setDirty(false); }}
            className="gap-1.5 text-xs" style={{ borderColor: "rgba(255,255,255,0.1)", color: "#9ca3af", background: "transparent" }}>
            <RefreshCw size={11} /> Resetuj
          </Button>
          <Button size="sm" onClick={() => saveMutation.mutate()} disabled={!dirty || saveMutation.isPending}
            className="gap-1.5 text-xs"
            style={{ background: dirty ? "linear-gradient(90deg,#6366f1,#8b5cf6)" : "rgba(99,102,241,0.15)", color: dirty ? "white" : "#6b7280", border: "none" }}>
            <Save size={11} /> {saveMutation.isPending ? "Čuvam..." : "Sačuvaj"}
          </Button>
        </div>
      </div>

      {dirty && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs"
          style={{ background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.15)", color: "#fbbf24" }}>
          <AlertTriangle size={12} /> Imaš nesačuvane promjene — klikni Sačuvaj da se primijene.
        </div>
      )}

      {/* ── Anti-Raid ───────────────────────────────────────────────────── */}
      <SectionCard
        title="Anti-Raid Zaštita"
        icon={<ShieldAlert size={16} />}
        enabled={cfg.antiRaid.enabled}
        onToggle={v => patch("antiRaid", { enabled: v })}
        color="#f87171"
      >
        <SettingRow label="Vremenski prozor" desc="Bot broji joinove unutar ovog perioda">
          <NumInput value={cfg.antiRaid.windowSeconds} onChange={v => patch("antiRaid", { windowSeconds: v })} min={10} max={300} suffix="sekundi" />
        </SettingRow>
        <SettingRow label="Limit sumnjivih joinova" desc="Koliko sumnjivih naloga u prozoru aktivira raid mode">
          <NumInput value={cfg.antiRaid.joinLimit} onChange={v => patch("antiRaid", { joinLimit: v })} min={2} max={50} suffix="naloga" />
        </SettingRow>
        <SettingRow label="Starost sumnjivog naloga" desc="Nalozi mlađi od ovoga se smatraju sumnjivim">
          <NumInput value={cfg.antiRaid.suspiciousAgeDays} onChange={v => patch("antiRaid", { suspiciousAgeDays: v })} min={1} max={90} suffix="dana" />
        </SettingRow>
        <SettingRow label="Trajanje lockdowna" desc="Koliko dugo ostaje raid mode aktivan nakon detekcije">
          <NumInput value={cfg.antiRaid.lockdownMinutes} onChange={v => patch("antiRaid", { lockdownMinutes: v })} min={1} max={60} suffix="minuta" />
        </SettingRow>
        <SettingRow label="Akcija tokom raida" desc="Šta bot radi sa sumnjivim nalozima dok je raid mode aktivan">
          <div className="flex gap-1.5">
            {(["kick", "ban", "alert_only"] as const).map(a => (
              <button key={a} type="button"
                onClick={() => patch("antiRaid", { action: a })}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                style={{
                  background: cfg.antiRaid.action === a
                    ? a === "ban" ? "rgba(248,113,113,0.2)" : a === "kick" ? "rgba(251,191,36,0.2)" : "rgba(99,102,241,0.2)"
                    : "rgba(255,255,255,0.05)",
                  border: cfg.antiRaid.action === a
                    ? a === "ban" ? "1px solid rgba(248,113,113,0.4)" : a === "kick" ? "1px solid rgba(251,191,36,0.4)" : "1px solid rgba(99,102,241,0.4)"
                    : "1px solid rgba(255,255,255,0.08)",
                  color: cfg.antiRaid.action === a
                    ? a === "ban" ? "#f87171" : a === "kick" ? "#fbbf24" : "#818cf8"
                    : "#6b7280",
                }}>
                {a === "kick" ? "⚡ Kick" : a === "ban" ? "🔨 Ban" : "🔔 Samo upozori"}
              </button>
            ))}
          </div>
        </SettingRow>

        <div className="py-3 mt-1">
          <div className="text-xs font-semibold mb-1.5" style={{ color: "#6b7280" }}>TRENUTNA KONFIGURACIJA</div>
          <div className="flex flex-wrap gap-2 text-xs">
            {[
              { label: "Prozor", val: `${cfg.antiRaid.windowSeconds}s` },
              { label: "Limit", val: `${cfg.antiRaid.joinLimit} naloga` },
              { label: "Sumnjiv ako mlađi od", val: `${cfg.antiRaid.suspiciousAgeDays}d` },
              { label: "Lockdown", val: `${cfg.antiRaid.lockdownMinutes} min` },
              { label: "Akcija", val: cfg.antiRaid.action === "kick" ? "Kick" : cfg.antiRaid.action === "ban" ? "Ban" : "Alert" },
            ].map(item => (
              <div key={item.label} className="px-2.5 py-1 rounded-lg" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.15)", color: "#fca5a5" }}>
                <span style={{ color: "#9ca3af" }}>{item.label}: </span>{item.val}
              </div>
            ))}
          </div>
        </div>
      </SectionCard>

      {/* ── Anti-NSFW ───────────────────────────────────────────────────── */}
      <SectionCard
        title="Anti-NSFW Filtar"
        icon={<Shield size={16} />}
        enabled={cfg.antiNsfw.enabled}
        onToggle={v => patch("antiNsfw", { enabled: v })}
        color="#818cf8"
      >
        <SettingRow label="Upozorenja prije timeouta" desc="Koliko NSFW pokušaja prije 1h timeouta korisnika">
          <NumInput value={cfg.antiNsfw.strikesBeforeTimeout} onChange={v => patch("antiNsfw", { strikesBeforeTimeout: v })} min={1} max={10} suffix="strike" />
        </SettingRow>
        <SettingRow label="Trajanje timeouta" desc="Koliko dugo korisnik dobija timeout nakon previše strikea">
          <NumInput value={cfg.antiNsfw.timeoutMinutes} onChange={v => patch("antiNsfw", { timeoutMinutes: v })} min={5} max={1440} suffix="minuta" />
        </SettingRow>

        <div className="py-3.5" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
          <div className="text-sm font-medium text-white mb-1">Dodatni blokirani sajtovi</div>
          <div className="text-xs mb-2.5" style={{ color: "#6b7280" }}>
            Dodaj domene koje bot treba blokirati uz podrazumijevanu listu (pornhub, xvideos, onlyfans...)
          </div>
          <TagInput
            tags={cfg.antiNsfw.extraBlockedSites}
            onChange={v => patch("antiNsfw", { extraBlockedSites: v })}
            placeholder="primjer.com"
          />
        </div>

        <div className="py-3.5">
          <div className="text-sm font-medium text-white mb-1">Dodatne blokirane riječi</div>
          <div className="text-xs mb-2.5" style={{ color: "#6b7280" }}>
            Nazivi fajlova/URL-ovi koji sadrže ove riječi bit će blokirani
          </div>
          <TagInput
            tags={cfg.antiNsfw.extraBlockedKeywords}
            onChange={v => patch("antiNsfw", { extraBlockedKeywords: v })}
            placeholder="keyword"
          />
        </div>

        <div className="pb-3">
          <div className="text-xs font-semibold mb-1.5" style={{ color: "#6b7280" }}>ŠTA JE VEĆ BLOKIRANO (ugrađena lista)</div>
          <div className="flex flex-wrap gap-1">
            {["pornhub", "xvideos", "onlyfans", "xnxx", "rule34", "e-hentai", "chaturbate", "+ 7 sajtova", "dick", "nude", "xxx", "porn", "hentai", "+ 9 riječi"].map(s => (
              <span key={s} className="px-1.5 py-0.5 rounded text-[10px] font-mono"
                style={{ background: "rgba(99,102,241,0.08)", color: "#6366f1", border: "1px solid rgba(99,102,241,0.12)" }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      </SectionCard>

      {/* Info */}
      <div className="flex items-start gap-2.5 px-4 py-3 rounded-xl text-xs"
        style={{ background: "rgba(99,102,241,0.05)", border: "1px solid rgba(99,102,241,0.1)", color: "#818cf8" }}>
        <ShieldCheck size={14} className="mt-0.5 flex-shrink-0" />
        <div>
          <strong>Kako radi:</strong> Bot čita ova podešavanja svakih 5 minuta automatski. Nakon što sačuvaš promjene, bot će ih primijeniti u sljedećem refresh ciklusu. NSFW kanali (age-restricted) su uvijek izuzeti od filtra.
        </div>
      </div>

      {cfg.updatedAt && (
        <div className="text-[10px] text-right" style={{ color: "#374151" }}>
          Zadnje ažuriranje: {new Date(cfg.updatedAt).toLocaleString("bs")}
        </div>
      )}
    </div>
  );
}
