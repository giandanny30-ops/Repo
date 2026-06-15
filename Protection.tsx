import { useGetStats, useListEmbeds } from "@workspace/api-client-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie, Cell as PieCell,
} from "recharts";
import {
  TerminalSquare, LayoutTemplate, Layers, Activity, ArrowRight, Sparkles,
  Users, Zap, Hash, Crown,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { Link } from "wouter";

const BASE_URL = import.meta.env.BASE_URL.replace(/\/$/, "");

const STAT_CARDS = [
  { key: "totalCommands", label: "Ukupno komandi", icon: TerminalSquare, color: "#6366f1", glow: "rgba(99,102,241,0.35)", sub: "Bot komande" },
  { key: "totalEmbeds",   label: "Embed templata", icon: LayoutTemplate, color: "#8b5cf6", glow: "rgba(139,92,246,0.35)", sub: "Poruka templata" },
  { key: "categories",   label: "Kategorija",     icon: Layers,          color: "#a855f7", glow: "rgba(168,85,247,0.35)", sub: "Komandnih grupa" },
  { key: "status",       label: "Status",          icon: Activity,        color: "#22c55e", glow: "rgba(34,197,94,0.35)",  sub: "Sistem zdrav" },
];

const CHART_COLORS = ["#6366f1","#7c3aed","#8b5cf6","#9333ea","#a855f7","#c026d3","#db2777","#e11d48","#f43f5e","#fb7185"];

const EMBED_CAT_COLORS: Record<string, string> = {
  "Sistem":       "#6366f1",
  "Log":          "#f59e0b",
  "Moderacija":   "#ef4444",
  "XP":           "#22c55e",
  "Ekonomija":    "#f97316",
  "Igre":         "#3b82f6",
  "Fun":          "#ec4899",
  "Ljubavne":     "#e879f9",
  "Info":         "#14b8a6",
  "Sistem paneli":"#a78bfa",
};

interface GuildInfo {
  id: string;
  name: string;
  icon: string | null;
  memberCount: number | null;
}

function useGuildInfo() {
  return useQuery<GuildInfo>({
    queryKey: ["guild-info"],
    queryFn: async () => {
      const r = await fetch(`${BASE_URL}/api/discord/guild`);
      if (!r.ok) throw new Error("Failed");
      return r.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

function StatCard({ cardKey, label, icon: Icon, color, glow, sub, value }: {
  cardKey: string; label: string; icon: typeof Activity; color: string;
  glow: string; sub: string; value: string | number;
}) {
  return (
    <div
      className="rounded-xl p-5 relative overflow-hidden group cursor-default"
      style={{
        background: "rgba(255,255,255,0.025)",
        border: "1px solid rgba(255,255,255,0.07)",
        transition: "box-shadow 0.3s, border-color 0.3s, transform 0.2s",
        animation: "fadeSlideUp 0.4s ease both",
      }}
      onMouseEnter={e => {
        const el = e.currentTarget as HTMLElement;
        el.style.boxShadow = `0 0 40px ${glow}`;
        el.style.borderColor = `${color}40`;
        el.style.transform = "translateY(-2px) scale(1.02)";
      }}
      onMouseLeave={e => {
        const el = e.currentTarget as HTMLElement;
        el.style.boxShadow = "none";
        el.style.borderColor = "rgba(255,255,255,0.07)";
        el.style.transform = "none";
      }}
    >
      <div className="absolute top-0 right-0 w-28 h-28 rounded-full -translate-y-12 translate-x-12 opacity-10 group-hover:opacity-25"
        style={{ background: color, filter: "blur(20px)", transition: "opacity 0.3s" }} />
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="p-2 rounded-lg" style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <div className="w-2 h-2 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
      </div>
      <div
        className="text-2xl font-black text-white relative z-10"
        data-testid={`stat-${cardKey === "status" ? "status" : cardKey === "totalCommands" ? "total-commands" : cardKey === "totalEmbeds" ? "total-embeds" : "categories"}`}
      >
        {value}
      </div>
      <div className="text-sm font-semibold mt-0.5 relative z-10" style={{ color: "#9ca3af" }}>{label}</div>
      <div className="text-xs mt-0.5 relative z-10" style={{ color: "#374151" }}>{sub}</div>
      <div className="absolute bottom-0 left-0 right-0 h-0.5"
        style={{ background: `linear-gradient(90deg, ${color}90, ${color}20, transparent)` }} />
    </div>
  );
}

function CustomPieTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: { fill: string } }> }) {
  if (!active || !payload?.length) return null;
  const { name, value, payload: p } = payload[0];
  return (
    <div style={{ background: "#0d0e16", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "10px", padding: "8px 14px", fontSize: "12px", color: "#e2e8f0", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full" style={{ background: p.fill }} />
        <span style={{ color: "#9ca3af" }}>{name}</span>
        <span className="font-bold text-white">{value}</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useGetStats();
  const { data: embeds, isLoading: embedsLoading } = useListEmbeds();
  const { data: guild } = useGuildInfo();

  const isLoading = statsLoading || embedsLoading;

  const chartData = useMemo(() =>
    Object.entries(stats?.commandsByCategory ?? {}).map(([category, count]) => ({ category, count })),
    [stats]
  );

  const embedPieData = useMemo(() => {
    if (!embeds) return [];
    const map = new Map<string, number>();
    for (const e of embeds) {
      const cat = e.category ?? "Ostalo";
      map.set(cat, (map.get(cat) ?? 0) + 1);
    }
    return Array.from(map.entries()).map(([name, value]) => ({
      name,
      value,
      fill: EMBED_CAT_COLORS[name] ?? "#6366f1",
    }));
  }, [embeds]);

  const statValues: Record<string, string | number> = {
    totalCommands: stats?.totalCommands ?? 0,
    totalEmbeds: stats?.totalEmbeds ?? 0,
    categories: stats?.categories ?? 0,
    status: "Healthy",
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-56 rounded-lg" style={{ background: "rgba(255,255,255,0.06)" }} />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-32 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
          <Skeleton className="h-80 rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
        </div>
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6" style={{ animation: "fadeSlideUp 0.35s ease both" }}>
      {/* ── Header ── */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Sparkles className="w-4 h-4" style={{ color: "#6366f1" }} />
            <span className="text-xs font-bold uppercase tracking-widest" style={{ color: "#3d3f5c" }}>Panel v2.0</span>
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight">Dashboard</h1>
          <p className="text-sm mt-1" style={{ color: "#4b5563" }}>Pregled GIANNI Bot panela</p>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          {guild?.memberCount && (
            <div className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.18)", color: "#818cf8" }}>
              <Users className="w-3.5 h-3.5" />
              {guild.memberCount.toLocaleString()} članova
            </div>
          )}
          <div className="text-xs font-mono px-3 py-1.5 rounded-lg" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.18)", color: "#818cf8" }}>
            gian.today
          </div>
        </div>
      </div>

      {/* ── Stat cards ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map(({ key, label, icon, color, glow, sub }) => (
          <StatCard key={key} cardKey={key} label={label} icon={icon} color={color} glow={glow} sub={sub} value={statValues[key]} />
        ))}
      </div>

      {/* ── Charts row ── */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Bar chart — commands by category */}
        <div className="lg:col-span-3 rounded-xl p-6 relative overflow-hidden" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <div className="absolute top-0 right-0 w-64 h-64 pointer-events-none" style={{ background: "radial-gradient(circle at 100% 0%, rgba(99,102,241,0.07) 0%, transparent 60%)" }} />
          <div className="flex items-center justify-between mb-6 relative z-10">
            <div>
              <h2 className="font-black text-white text-lg">Komande po kategoriji</h2>
              <p className="text-xs mt-0.5" style={{ color: "#374151" }}>
                Distribucija {stats.totalCommands} komandi u {stats.categories} kategorija
              </p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.18)" }}>
              <TerminalSquare className="w-4 h-4" style={{ color: "#818cf8" }} />
            </div>
          </div>
          <div style={{ height: 240 }} className="relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} barCategoryGap="35%">
                <XAxis dataKey="category" stroke="#1f2937" fontSize={10} tickLine={false} axisLine={false} tick={{ fill: "#4b5563" }} />
                <YAxis stroke="#1f2937" fontSize={10} tickLine={false} axisLine={false} tick={{ fill: "#374151" }} width={28} />
                <Tooltip
                  cursor={{ fill: "rgba(99,102,241,0.06)" }}
                  contentStyle={{ background: "#0d0e16", border: "1px solid rgba(99,102,241,0.25)", borderRadius: "12px", color: "#e2e8f0", fontSize: "12px", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}
                />
                <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie chart — embeds by category */}
        <div className="lg:col-span-2 rounded-xl p-6 relative overflow-hidden" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
          <div className="absolute bottom-0 left-0 w-48 h-48 pointer-events-none" style={{ background: "radial-gradient(circle at 0% 100%, rgba(139,92,246,0.07) 0%, transparent 60%)" }} />
          <div className="flex items-center justify-between mb-4 relative z-10">
            <div>
              <h2 className="font-black text-white text-lg">Embed kategorije</h2>
              <p className="text-xs mt-0.5" style={{ color: "#374151" }}>{stats.totalEmbeds} templata</p>
            </div>
            <div className="p-2 rounded-lg" style={{ background: "rgba(139,92,246,0.1)", border: "1px solid rgba(139,92,246,0.18)" }}>
              <LayoutTemplate className="w-4 h-4" style={{ color: "#a78bfa" }} />
            </div>
          </div>
          <div style={{ height: 200 }} className="relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={embedPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {embedPieData.map((entry, i) => (
                    <PieCell key={i} fill={entry.fill} stroke="transparent" />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-1 relative z-10">
            {embedPieData.map(entry => (
              <div key={entry.name} className="flex items-center gap-1.5 text-[10px]" style={{ color: "#6b7280" }}>
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: entry.fill }} />
                <span className="truncate">{entry.name}</span>
                <span className="font-bold ml-auto" style={{ color: "#9ca3af" }}>{entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Info strip ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { icon: Zap, label: "Bot status", value: "Online", color: "#22c55e" },
          { icon: Hash, label: "Komandnih kategorija", value: stats.categories, color: "#6366f1" },
          { icon: Crown, label: "Embed kategorija", value: embedPieData.length, color: "#a855f7" },
          { icon: Users, label: "Članova", value: guild?.memberCount ? guild.memberCount.toLocaleString() : "—", color: "#3b82f6" },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="rounded-lg px-4 py-3 flex items-center gap-3"
            style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)" }}>
            <div className="p-1.5 rounded-md flex-shrink-0" style={{ background: `${color}12`, border: `1px solid ${color}22` }}>
              <Icon className="w-3.5 h-3.5" style={{ color }} />
            </div>
            <div className="min-w-0">
              <div className="text-sm font-bold text-white truncate">{value}</div>
              <div className="text-[10px] truncate" style={{ color: "#374151" }}>{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Quick links ── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Pregledaj komande", sub: `${stats.totalCommands} komandi dostupno`, href: "/commands", color: "#6366f1", emoji: "🎮" },
          { label: "Uredi Embeds", sub: `${stats.totalEmbeds} templata`, href: "/embeds", color: "#8b5cf6", emoji: "📋" },
          { label: "Upravljaj članovima", sub: guild?.memberCount ? `${guild.memberCount.toLocaleString()} članova` : "Discord server", href: "/members", color: "#a855f7", emoji: "👥" },
        ].map(link => (
          <Link
            key={link.href}
            href={link.href}
            className="rounded-xl p-4 flex items-center gap-3 group"
            style={{
              background: "rgba(255,255,255,0.025)",
              border: "1px solid rgba(255,255,255,0.07)",
              textDecoration: "none",
              transition: "all 0.2s",
              display: "flex",
            }}
            onMouseEnter={e => {
              const el = e.currentTarget as HTMLElement;
              el.style.borderColor = `${link.color}40`;
              el.style.background = `${link.color}08`;
              el.style.transform = "translateY(-2px)";
            }}
            onMouseLeave={e => {
              const el = e.currentTarget as HTMLElement;
              el.style.borderColor = "rgba(255,255,255,0.07)";
              el.style.background = "rgba(255,255,255,0.025)";
              el.style.transform = "none";
            }}
          >
            <div className="w-10 h-10 rounded-lg flex items-center justify-center text-xl flex-shrink-0"
              style={{ background: `${link.color}15`, border: `1px solid ${link.color}25` }}>
              {link.emoji}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-bold text-white truncate">{link.label}</div>
              <div className="text-xs truncate" style={{ color: "#374151" }}>{link.sub}</div>
            </div>
            <ArrowRight className="w-4 h-4 flex-shrink-0 group-hover:translate-x-1 transition-transform" style={{ color: "#374151" }} />
          </Link>
        ))}
      </div>
    </div>
  );
}
