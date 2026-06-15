import { ReactNode } from "react";
import { Link, useLocation } from "wouter";
import {
  LayoutDashboard, Terminal, FileText, Users, Globe,
  ShieldCheck, ShieldAlert, Gamepad2, Settings2, LogOut, Sparkles, Smile,
  type LucideIcon,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";

const BASE_URL = import.meta.env.BASE_URL.replace(/\/$/, "");

interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  color: string;      // bg color (hex / oklch / etc.)
  glow: string;       // box-shadow glow color
  textActive: string; // active text color
}

const NAV: NavItem[] = [
  {
    href: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
    color: "#059669",
    glow: "rgba(5,150,105,0.45)",
    textActive: "#34d399",
  },
  {
    href: "/commands",
    label: "Komande",
    icon: Terminal,
    color: "#2563eb",
    glow: "rgba(37,99,235,0.45)",
    textActive: "#60a5fa",
  },
  {
    href: "/embeds",
    label: "Embeds",
    icon: FileText,
    color: "#7c3aed",
    glow: "rgba(124,58,237,0.45)",
    textActive: "#a78bfa",
  },
  {
    href: "/members",
    label: "Članovi",
    icon: Users,
    color: "#db2777",
    glow: "rgba(219,39,119,0.45)",
    textActive: "#f472b6",
  },
  {
    href: "/server",
    label: "Server",
    icon: Globe,
    color: "#d97706",
    glow: "rgba(217,119,6,0.45)",
    textActive: "#fbbf24",
  },
  {
    href: "/permissions",
    label: "Permisije",
    icon: ShieldCheck,
    color: "#0891b2",
    glow: "rgba(8,145,178,0.45)",
    textActive: "#22d3ee",
  },
  {
    href: "/protection",
    label: "Zaštita",
    icon: ShieldAlert,
    color: "#dc2626",
    glow: "rgba(220,38,38,0.45)",
    textActive: "#f87171",
  },
  {
    href: "/games",
    label: "Igre",
    icon: Gamepad2,
    color: "#0d9488",
    glow: "rgba(13,148,136,0.45)",
    textActive: "#2dd4bf",
  },
  {
    href: "/icons",
    label: "Ikone",
    icon: Sparkles,
    color: "#a855f7",
    glow: "rgba(168,85,247,0.45)",
    textActive: "#d8b4fe",
  },
  {
    href: "/emojis",
    label: "Emoji",
    icon: Smile,
    color: "#F59E0B",
    glow: "rgba(245,158,11,0.45)",
    textActive: "#FCD34D",
  },
  {
    href: "/settings",
    label: "Podešavanja",
    icon: Settings2,
    color: "#64748b",
    glow: "rgba(100,116,139,0.45)",
    textActive: "#94a3b8",
  },
];

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
      const res = await fetch(`${BASE_URL}/api/discord/guild`);
      if (!res.ok) throw new Error("Failed to fetch guild");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}

function NavIcon({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <div
      className="flex items-center justify-center rounded-lg flex-shrink-0 transition-all duration-200"
      style={{
        width: 30,
        height: 30,
        background: active ? item.color : `${item.color}22`,
        boxShadow: active ? `0 0 12px ${item.glow}, 0 0 4px ${item.glow}` : "none",
        border: `1px solid ${active ? item.color : `${item.color}44`}`,
      }}
    >
      <Icon
        style={{
          width: 15,
          height: 15,
          color: active ? "#fff" : item.color,
          strokeWidth: 2.2,
        }}
      />
    </div>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const { data: guild } = useGuildInfo();
  const { logout, devMode } = useAuth();

  const activeItem = NAV.find(n => n.href === location);

  return (
    <div
      className="flex h-screen w-full overflow-hidden"
      style={{ background: "#080910", color: "#e2e8f0", fontFamily: "'Segoe UI', system-ui, sans-serif" }}
    >
      {/* Global decorative background */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div style={{ position: "absolute", top: "-120px", left: "-80px", width: "420px", height: "420px", borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%)", filter: "blur(40px)" }} />
        <div style={{ position: "absolute", bottom: "-100px", right: "-60px", width: "350px", height: "350px", borderRadius: "50%", background: "radial-gradient(circle, rgba(139,92,246,0.10) 0%, transparent 70%)", filter: "blur(40px)" }} />
        {activeItem && (
          <div style={{ position: "absolute", top: "20%", left: "0", width: "300px", height: "300px", borderRadius: "50%", background: `radial-gradient(circle, ${activeItem.glow} 0%, transparent 70%)`, filter: "blur(60px)", transition: "all 0.5s ease" }} />
        )}
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(99,102,241,0.12) 1px, transparent 1px)", backgroundSize: "32px 32px", opacity: 0.4 }} />
      </div>

      {/* Sidebar */}
      <aside
        className="w-60 flex-shrink-0 flex flex-col relative z-10 overflow-hidden"
        style={{ background: "rgba(10,11,15,0.97)", borderRight: "1px solid rgba(255,255,255,0.06)" }}
      >
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 50% -5%, rgba(99,102,241,0.18) 0%, transparent 60%)" }} />
        <div className="absolute top-0 right-0 w-px h-full pointer-events-none" style={{ background: "linear-gradient(180deg, transparent, rgba(99,102,241,0.25) 30%, rgba(139,92,246,0.15) 70%, transparent)" }} />

        {/* Brand */}
        <div className="flex items-center gap-3 px-5 py-5 relative z-10">
          {guild?.icon ? (
            <img src={guild.icon} alt={guild.name} className="w-9 h-9 rounded-xl flex-shrink-0 object-cover" style={{ boxShadow: "0 0 24px rgba(99,102,241,0.55)" }} />
          ) : (
            <div className="w-9 h-9 rounded-xl flex items-center justify-center font-black text-sm flex-shrink-0 relative" style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 0 24px rgba(99,102,241,0.55)" }}>
              G
            </div>
          )}
          <div className="min-w-0">
            <div className="font-bold text-white text-sm tracking-tight">GIANNI Panel</div>
            <div className="text-xs font-medium" style={{ color: "#818cf8" }}>Bot v2.0</div>
          </div>
        </div>

        {/* Bot status */}
        <div className="mx-4 mb-4 px-3 py-2.5 rounded-lg relative z-10" style={{ background: "rgba(99,102,241,0.07)", border: "1px solid rgba(99,102,241,0.15)" }}>
          <div className="flex items-center gap-2 mb-1">
            <div className="relative flex-shrink-0">
              <div className="w-2 h-2 rounded-full" style={{ background: "#22c55e" }} />
              <div className="absolute inset-0 w-2 h-2 rounded-full animate-ping" style={{ background: "#22c55e", opacity: 0.5 }} />
            </div>
            <span className="text-xs font-semibold text-white">GIANNI · Online</span>
          </div>
          <div className="flex items-center gap-2">
            {guild?.icon && <img src={guild.icon} alt="" className="w-4 h-4 rounded-full flex-shrink-0" />}
            <div className="text-xs truncate" style={{ color: "#4b5563" }}>{guild?.name ?? "GIAN · Discord"}</div>
          </div>
          {guild?.memberCount && (
            <div className="text-[10px] mt-0.5 font-medium" style={{ color: "#374151" }}>
              {guild.memberCount.toLocaleString()} članova
            </div>
          )}
        </div>

        {/* Section label */}
        <div className="px-5 mb-2 relative z-10">
          <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "#2d3048" }}>Navigacija</span>
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-3 space-y-0.5 relative z-10 overflow-y-auto">
          {NAV.map((item) => {
            const active = location === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                data-testid={`nav-${item.label.toLowerCase()}`}
                className="flex items-center gap-3 px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-150 w-full relative"
                style={{
                  background: active ? `${item.color}14` : "transparent",
                  color: active ? item.textActive : "#6b7280",
                  display: "flex",
                }}
              >
                <NavIcon item={item} active={active} />
                <span className="flex-1 font-medium" style={{ fontSize: "13px" }}>{item.label}</span>
                {active && (
                  <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: item.color, boxShadow: `0 0 6px ${item.color}` }} />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 relative z-10 flex-shrink-0" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <div className="flex items-center gap-2.5">
            {guild?.icon ? (
              <img src={guild.icon} alt="" className="w-8 h-8 rounded-lg flex-shrink-0 object-cover" style={{ boxShadow: "0 0 12px rgba(99,102,241,0.25)" }} />
            ) : (
              <div className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-black flex-shrink-0" style={{ background: "linear-gradient(135deg, #1e1b4b, #312e81)", color: "#a5b4fc" }}>
                G
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="text-xs font-bold text-white truncate">Gianni Bot</div>
              <div className="flex items-center gap-1 text-xs" style={{ color: devMode ? "#f59e0b" : "#22c55e" }}>
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: devMode ? "#f59e0b" : "#22c55e", boxShadow: `0 0 4px ${devMode ? "#f59e0b" : "#22c55e"}` }} />
                {devMode ? "Dev mode" : "Online"}
              </div>
            </div>
            <button
              onClick={logout}
              title="Odjavi se"
              className="flex-shrink-0 p-1.5 rounded-lg transition-all"
              style={{ color: "#4b5563", background: "transparent" }}
              onMouseEnter={e => { e.currentTarget.style.color = "#f87171"; e.currentTarget.style.background = "rgba(239,68,68,0.08)"; }}
              onMouseLeave={e => { e.currentTarget.style.color = "#4b5563"; e.currentTarget.style.background = "transparent"; }}
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative z-10">
        <div
          className="flex-shrink-0 px-6 py-3 flex items-center justify-between"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", background: "rgba(8,9,16,0.6)", backdropFilter: "blur(8px)" }}
        >
          <div className="flex items-center gap-2 text-xs" style={{ color: "#374151" }}>
            <span style={{ color: "#4b5563" }}>gian.today</span>
            <span>/</span>
            {activeItem && (
              <span style={{ color: activeItem.textActive }}>{activeItem.label}</span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {guild?.name && (
              <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)", color: "#818cf8" }}>
                {guild.icon && <img src={guild.icon} alt="" className="w-3.5 h-3.5 rounded-full" />}
                {guild.name}
              </div>
            )}
            <div className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full" style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.16)", color: "#22c55e" }}>
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: "#22c55e", boxShadow: "0 0 4px #22c55e" }} />
              Sistem aktivan
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto" style={{ animation: "fadeSlideUp 0.35s ease both" }}>
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
