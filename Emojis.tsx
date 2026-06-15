import { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Shield, ShieldAlert, Save, RefreshCw, Search, ChevronDown, ChevronRight,
  Lock, MessageSquare, Mic, Users, Settings2, Star, Eye,
} from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

// ─── Discord permission definitions ───────────────────────────────────────────
type Safety = "safe" | "moderate" | "danger";

interface PermDef {
  bit: bigint;
  label: string;
  description: string;
  danger?: boolean;
  safety: Safety;
}

type Category = { label: string; icon: React.ReactNode; perms: PermDef[] };

const SAFETY_BADGE: Record<Safety, { label: string; bg: string; color: string }> = {
  safe:     { label: "Bezbjedno", bg: "rgba(59,165,92,0.12)",   color: "#3ba55c" },
  moderate: { label: "Umjereno",  bg: "rgba(251,191,36,0.12)",  color: "#fbbf24" },
  danger:   { label: "Opasno",    bg: "rgba(248,113,113,0.12)", color: "#f87171" },
};

const CATEGORIES: Category[] = [
  {
    label: "Generalno",
    icon: <Settings2 size={14} />,
    perms: [
      { bit: 1n << 3n,  label: "Administrator",           description: "Sve permisije — nikad davati normalnim korisnicima!", danger: true, safety: "danger" },
      { bit: 1n << 5n,  label: "Upravljaj serverom",      description: "Mijenja ime, region, ikonu servera", safety: "danger" },
      { bit: 1n << 7n,  label: "Vidi audit log",          description: "Pristup historiji akcija na serveru", safety: "moderate" },
      { bit: 1n << 19n, label: "Vidi statistike servera", description: "Discord Insights analitika", safety: "safe" },
      { bit: 1n << 30n, label: "Upravljaj webhookovima",  description: "Kreira, uređuje i briše webhookove", safety: "moderate" },
      { bit: 1n << 29n, label: "Upravljaj emojima",       description: "Dodaje i briše serverske emojije", safety: "moderate" },
    ],
  },
  {
    label: "Kanali i uloge",
    icon: <Lock size={14} />,
    perms: [
      { bit: 1n << 4n,  label: "Upravljaj kanalima",   description: "Kreira, briše i uređuje kanale", safety: "danger" },
      { bit: 1n << 28n, label: "Upravljaj ulogama",     description: "Kreira i uređuje uloge ispod ove — može eskalirati permisije!", danger: true, safety: "danger" },
      { bit: 1n << 0n,  label: "Kreira pozivnice",      description: "Generiše invite linkove", safety: "safe" },
      { bit: 1n << 10n, label: "Vidi kanale",           description: "Vidi tekstualne i voice kanale", safety: "safe" },
    ],
  },
  {
    label: "Tekst",
    icon: <MessageSquare size={14} />,
    perms: [
      { bit: 1n << 11n, label: "Šalje poruke",         description: "Piše u tekstualnim kanalima", safety: "safe" },
      { bit: 1n << 16n, label: "Čita historiju",        description: "Vidi starije poruke u kanalima", safety: "safe" },
      { bit: 1n << 13n, label: "Upravlja porukama",     description: "Briše i pini poruke drugih korisnika", danger: true, safety: "moderate" },
      { bit: 1n << 12n, label: "TTS poruke",            description: "Šalje text-to-speech poruke — može biti dosadno", safety: "moderate" },
      { bit: 1n << 14n, label: "Embed linkove",         description: "Linkovi generišu pregled", safety: "safe" },
      { bit: 1n << 15n, label: "Priloži fajlove",       description: "Upload fajlova i slika", safety: "safe" },
      { bit: 1n << 6n,  label: "Dodaje reakcije",       description: "Reaguje na poruke emoji-jem", safety: "safe" },
      { bit: 1n << 17n, label: "Taguje @everyone",      description: "Može tagovati cio server — nikad davati normalnim korisnicima!", danger: true, safety: "danger" },
      { bit: 1n << 18n, label: "Eksterni emoji",        description: "Koristi emojije s drugih servera", safety: "safe" },
      { bit: 1n << 38n, label: "Eksterni stikeri",      description: "Koristi stikere s drugih servera", safety: "safe" },
      { bit: 1n << 32n, label: "Šalje ankete",          description: "Kreira Discord ankete", safety: "safe" },
      { bit: 1n << 34n, label: "Koristi aplikacije",    description: "Slash komande i aplikacije u kanalu", safety: "safe" },
    ],
  },
  {
    label: "Voice",
    icon: <Mic size={14} />,
    perms: [
      { bit: 1n << 20n, label: "Spoji se",             description: "Ulazi u voice kanale", safety: "safe" },
      { bit: 1n << 21n, label: "Govori",                description: "Govori u voice kanalima", safety: "safe" },
      { bit: 1n << 25n, label: "Voice aktivacija",      description: "Govori bez push-to-talk", safety: "safe" },
      { bit: 1n << 8n,  label: "Prioritetni govor",     description: "Smanjuje glasnoću ostalih dok govori", safety: "moderate" },
      { bit: 1n << 9n,  label: "Video streaming",       description: "Dijeli ekran/kameru u voice", safety: "safe" },
      { bit: 1n << 22n, label: "Utišaj članove",        description: "Mute server-wide za druge", danger: true, safety: "danger" },
      { bit: 1n << 23n, label: "Zaguši članove",        description: "Deafen server-wide za druge", danger: true, safety: "danger" },
      { bit: 1n << 24n, label: "Premjesti članove",     description: "Prebacuje korisnike između kanala", safety: "moderate" },
    ],
  },
  {
    label: "Članovi",
    icon: <Users size={14} />,
    perms: [
      { bit: 1n << 1n,  label: "Kickuj članove",        description: "Izbacuje korisnike sa servera — samo za modove/admne", danger: true, safety: "danger" },
      { bit: 1n << 2n,  label: "Banuj članove",         description: "Trajno ili privremeno bani korisnike — samo za admne", danger: true, safety: "danger" },
      { bit: 1n << 40n, label: "Timeout članove",       description: "Stavlja korisnike u timeout — samo za modove", danger: true, safety: "moderate" },
      { bit: 1n << 26n, label: "Mijenja vlastiti nick",  description: "Može promijeniti vlastiti nadimak", safety: "safe" },
      { bit: 1n << 27n, label: "Upravljaj nickovima",   description: "Mijenja nadimke drugima", safety: "moderate" },
    ],
  },
];

// ─── Types ────────────────────────────────────────────────────────────────────
interface Role {
  id: string;
  name: string;
  color: string;
  position: number;
  managed: boolean;
  permissions: string;
  hoist: boolean;
  mentionable: boolean;
}

// ─── Utilities ────────────────────────────────────────────────────────────────
function hasPermission(permBigInt: bigint, bit: bigint): boolean {
  if (permBigInt & (1n << 3n)) return true; // admin = all
  return !!(permBigInt & bit);
}

function safeBigInt(val: string | undefined | null): bigint {
  try { return BigInt(val ?? "0"); } catch { return 0n; }
}

// ─── Role Color Dot ───────────────────────────────────────────────────────────
function RoleDot({ color }: { color: string }) {
  return (
    <span
      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
      style={{ background: color === "#5865F2" ? "#6b7280" : color, boxShadow: `0 0 6px ${color}44` }}
    />
  );
}

// ─── Toggle Switch ────────────────────────────────────────────────────────────
function Toggle({ checked, onChange, disabled, danger }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean; danger?: boolean }) {
  const activeColor = danger ? "#f87171" : "#3ba55c";
  const activeGlow  = danger ? "rgba(248,113,113,0.35)" : "rgba(59,165,92,0.35)";
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className="relative inline-flex w-11 h-6 rounded-full transition-all duration-200 flex-shrink-0 focus:outline-none"
      style={{
        background: checked ? activeColor : "rgba(255,255,255,0.07)",
        border: checked ? "none" : "1px solid rgba(255,255,255,0.12)",
        boxShadow: checked ? `0 0 14px ${activeGlow}` : "none",
        opacity: disabled ? 0.45 : 1,
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      <span
        className="absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform duration-200"
        style={{ transform: checked ? "translateX(22px)" : "translateX(2px)", boxShadow: "0 1px 4px rgba(0,0,0,0.45)" }}
      />
    </button>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function Permissions() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [localPerms, setLocalPerms] = useState<bigint>(0n);
  const [localHoist, setLocalHoist] = useState(false);
  const [localMentionable, setLocalMentionable] = useState(false);
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [dirty, setDirty] = useState(false);

  const { data: roles = [], isLoading, refetch } = useQuery<Role[]>({
    queryKey: ["discord-roles"],
    queryFn: async () => {
      const r = await fetch(`${BASE}/api/discord/roles`);
      if (!r.ok) throw new Error("Greška pri učitavanju uloga");
      return r.json();
    },
    staleTime: 30_000,
  });

  const selected = useMemo(() => roles.find(r => r.id === selectedId) ?? null, [roles, selectedId]);

  // Sync local state when selection changes
  useEffect(() => {
    if (!selected) return;
    setLocalPerms(safeBigInt(selected.permissions));
    setLocalHoist(selected.hoist);
    setLocalMentionable(selected.mentionable);
    setDirty(false);
  }, [selected]);

  const patchMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${BASE}/api/discord/roles/${selectedId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          permissions: localPerms.toString(),
          hoist: localHoist,
          mentionable: localMentionable,
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: "Greška" }));
        throw new Error(err.error ?? "Greška pri čuvanju");
      }
      return r.json();
    },
    onSuccess: () => {
      toast({ title: "Sačuvano", description: `Permisije za @${selected?.name} ažurirane.` });
      queryClient.invalidateQueries({ queryKey: ["discord-roles"] });
      setDirty(false);
    },
    onError: (err: Error) => {
      toast({ title: "Greška", description: err.message, variant: "destructive" });
    },
  });

  function togglePerm(bit: bigint) {
    const isAdmin = bit === (1n << 3n);
    setLocalPerms(prev => {
      const next = prev ^ bit;
      return isAdmin ? (next & (1n << 3n) ? next : next) : next;
    });
    setDirty(true);
  }

  const filteredRoles = useMemo(
    () => roles.filter(r => r.name.toLowerCase().includes(search.toLowerCase())),
    [roles, search],
  );

  const adminOn = !!(localPerms & (1n << 3n));

  return (
    <div className="flex flex-col gap-0 h-[calc(100vh-96px)]" style={{ animation: "fadeSlideUp 0.35s ease both" }}>
      {/* Header */}
      <div className="mb-5 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Shield size={20} className="text-indigo-400" /> Permisije Uloga
          </h1>
          <p className="text-xs mt-0.5" style={{ color: "#6b7280" }}>
            Odaberi ulogu i konfigurišu Discord permisije direktno iz panela
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => refetch()}
          disabled={isLoading}
          className="gap-2 text-xs"
          style={{ borderColor: "rgba(255,255,255,0.1)", color: "#9ca3af", background: "transparent" }}
        >
          <RefreshCw size={12} className={isLoading ? "animate-spin" : ""} /> Osvježi
        </Button>
      </div>

      {/* Two-column layout */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* ── Left: Role List ───────────────────────────────────────── */}
        <div
          className="w-56 flex-shrink-0 flex flex-col rounded-xl overflow-hidden"
          style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}
        >
          {/* Search */}
          <div className="p-3 flex-shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2" style={{ color: "#6b7280" }} />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Pretraži uloge..."
                className="w-full pl-7 pr-2 py-1.5 rounded-md text-xs bg-transparent border outline-none focus:ring-0"
                style={{
                  border: "1px solid rgba(255,255,255,0.08)",
                  color: "#d1d5db",
                  background: "rgba(255,255,255,0.03)",
                }}
              />
            </div>
          </div>

          {/* Role list */}
          <div className="flex-1 overflow-y-auto py-1">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="flex items-center gap-2 px-3 py-2">
                  <Skeleton className="w-2.5 h-2.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }} />
                  <Skeleton className="h-3 flex-1 rounded" style={{ background: "rgba(255,255,255,0.06)" }} />
                </div>
              ))
            ) : filteredRoles.length === 0 ? (
              <div className="text-xs text-center py-8" style={{ color: "#6b7280" }}>Nema rezultata</div>
            ) : (
              filteredRoles.map(role => {
                const active = role.id === selectedId;
                return (
                  <button
                    key={role.id}
                    onClick={() => setSelectedId(role.id)}
                    className="w-full flex items-center gap-2 px-3 py-2 text-left transition-all duration-150 relative"
                    style={{
                      background: active ? "rgba(99,102,241,0.12)" : "transparent",
                      borderLeft: active ? "2px solid #6366f1" : "2px solid transparent",
                      color: active ? "#e2e8f0" : "#9ca3af",
                    }}
                  >
                    <RoleDot color={role.color} />
                    <span className="text-xs font-medium truncate flex-1">{role.name}</span>
                    {role.managed && (
                      <span className="text-[9px] px-1 py-0.5 rounded" style={{ background: "rgba(99,102,241,0.15)", color: "#818cf8" }}>BOT</span>
                    )}
                    {!!(safeBigInt(role.permissions) & (1n << 3n)) && (
                      <ShieldAlert size={10} style={{ color: "#f87171", flexShrink: 0 }} />
                    )}
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* ── Right: Permission Editor ──────────────────────────────── */}
        <div className="flex-1 flex flex-col min-h-0 rounded-xl overflow-hidden"
          style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>

          {!selected ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3" style={{ color: "#4b5563" }}>
              <Shield size={40} className="opacity-20" />
              <p className="text-sm">Odaberi ulogu s liste</p>
            </div>
          ) : (
            <>
              {/* Role header */}
              <div
                className="flex items-center justify-between px-5 py-3.5 flex-shrink-0"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(255,255,255,0.015)" }}
              >
                <div className="flex items-center gap-3">
                  <RoleDot color={selected.color} />
                  <div>
                    <div className="text-sm font-bold text-white flex items-center gap-2">
                      @{selected.name}
                      {selected.managed && <Badge className="text-[9px] px-1.5 py-0" style={{ background: "rgba(99,102,241,0.2)", color: "#818cf8", border: "none" }}>BOT ULOGA</Badge>}
                    </div>
                    <div className="text-xs flex items-center gap-2 mt-0.5" style={{ color: "#6b7280" }}>
                      <span>Pozicija: #{selected.position}</span>
                      <span>·</span>
                      <span>ID: {selected.id}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {dirty && (
                    <span className="text-xs px-2 py-0.5 rounded-full" style={{ background: "rgba(251,191,36,0.12)", color: "#fbbf24", border: "1px solid rgba(251,191,36,0.2)" }}>
                      Nesačuvane promjene
                    </span>
                  )}
                  <Button
                    size="sm"
                    onClick={() => patchMutation.mutate()}
                    disabled={!dirty || patchMutation.isPending || selected.managed}
                    className="gap-2 text-xs"
                    style={{ background: dirty ? "linear-gradient(90deg,#6366f1,#8b5cf6)" : "rgba(99,102,241,0.15)", color: dirty ? "white" : "#6b7280", border: "none" }}
                  >
                    <Save size={12} /> {patchMutation.isPending ? "Čuvam..." : "Sačuvaj"}
                  </Button>
                </div>
              </div>

              {selected.managed && (
                <div className="mx-5 mt-3 px-3 py-2 rounded-lg text-xs flex items-center gap-2" style={{ background: "rgba(251,191,36,0.06)", border: "1px solid rgba(251,191,36,0.15)", color: "#fbbf24" }}>
                  <ShieldAlert size={12} /> Bot uloge (managed) ne mogu se uređivati.
                </div>
              )}

              {/* Role flags */}
              <div className="px-5 py-3 flex items-center gap-6 flex-shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                <div className="flex items-center gap-2">
                  <Toggle
                    checked={localHoist}
                    onChange={v => { setLocalHoist(v); setDirty(true); }}
                    disabled={selected.managed}
                  />
                  <div>
                    <div className="text-xs font-medium text-white">Prikaži odvojeno</div>
                    <div className="text-[10px]" style={{ color: "#6b7280" }}>Hoist — vidljiva u sidebar listi</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Toggle
                    checked={localMentionable}
                    onChange={v => { setLocalMentionable(v); setDirty(true); }}
                    disabled={selected.managed}
                  />
                  <div>
                    <div className="text-xs font-medium text-white">Mention-able</div>
                    <div className="text-[10px]" style={{ color: "#6b7280" }}>Svi mogu tagovati @{selected.name}</div>
                  </div>
                </div>
                {adminOn && (
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs" style={{ background: "rgba(248,113,113,0.08)", border: "1px solid rgba(248,113,113,0.2)", color: "#f87171" }}>
                    <ShieldAlert size={11} /> Administrator uključen — sve permisije aktivne
                  </div>
                )}
              </div>

              {/* Scrollable perm list */}
              <div className="flex-1 overflow-y-auto px-5 py-3 space-y-2">
                {CATEGORIES.map(cat => {
                  const open = !collapsed[cat.label];
                  return (
                    <div key={cat.label} className="rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.05)" }}>
                      {/* Category header */}
                      <button
                        type="button"
                        onClick={() => setCollapsed(prev => ({ ...prev, [cat.label]: !prev[cat.label] }))}
                        className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-semibold transition-colors"
                        style={{ background: "rgba(255,255,255,0.025)", color: "#9ca3af" }}
                      >
                        <div className="flex items-center gap-2">
                          <span style={{ color: "#6366f1" }}>{cat.icon}</span>
                          {cat.label}
                          <span className="font-normal opacity-50">
                            ({cat.perms.filter(p => hasPermission(localPerms, p.bit)).length}/{cat.perms.length})
                          </span>
                        </div>
                        {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                      </button>

                      {/* Perms */}
                      {open && (
                        <div className="divide-y divide-white/5" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
                          {cat.perms.map(perm => {
                            const on = hasPermission(localPerms, perm.bit);
                            const isAdminBit = perm.bit === (1n << 3n);
                            const forcedByAdmin = !isAdminBit && adminOn;
                            const rowColor = on
                              ? perm.danger ? "rgba(248,113,113,0.07)" : "rgba(59,165,92,0.07)"
                              : "transparent";
                            const labelColor = on
                              ? perm.danger ? "#fca5a5" : "#86efac"
                              : "#9ca3af";
                            return (
                              <div
                                key={String(perm.bit)}
                                className="flex items-center justify-between px-4 py-2.5 transition-colors duration-150"
                                style={{ background: rowColor }}
                              >
                                <div className="flex-1 min-w-0 mr-4">
                                  <div className="flex items-center gap-1.5 text-xs font-medium" style={{ color: labelColor }}>
                                    {on && !perm.danger && (
                                      <span style={{ color: "#3ba55c", fontSize: 11 }}>✓</span>
                                    )}
                                    {perm.label}
                                    {perm.danger && on && (
                                      <span style={{ color: "#f87171" }}><ShieldAlert size={10} /></span>
                                    )}
                                    {forcedByAdmin && (
                                      <span className="text-[9px] px-1 py-0.5 rounded" style={{ background: "rgba(248,113,113,0.12)", color: "#f87171" }}>Admin</span>
                                    )}
                                    {!forcedByAdmin && (() => {
                                      const b = SAFETY_BADGE[perm.safety];
                                      return (
                                        <span className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold" style={{ background: b.bg, color: b.color }}>
                                          {b.label}
                                        </span>
                                      );
                                    })()}
                                  </div>
                                  <div className="text-[10px] mt-0.5 truncate" style={{ color: on ? "#4b5563" : "#374151" }}>{perm.description}</div>
                                </div>
                                <Toggle
                                  checked={on}
                                  onChange={() => togglePerm(perm.bit)}
                                  disabled={selected.managed || forcedByAdmin}
                                  danger={perm.danger}
                                />
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
