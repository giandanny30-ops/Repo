import { useState, useEffect } from "react";
import { useGetSettings, useUpdateSettings, getGetSettingsQueryKey } from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Save, Eye, EyeOff, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

const S = {
  card: { background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", padding: "24px" },
  label: { fontSize: "11px", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.08em", color: "#6b7280", display: "block", marginBottom: "6px" },
  input: { background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#e2e8f0", fontSize: "14px" },
  section: { fontSize: "11px", fontWeight: 700, textTransform: "uppercase" as const, letterSpacing: "0.1em", color: "#374151", marginBottom: "16px" },
};

export default function Settings() {
  const { data: settings, isLoading } = useGetSettings();
  const updateSettingsMutation = useUpdateSettings();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [botName, setBotName] = useState("");
  const [prefix, setPrefix] = useState("");
  const [officialInvite, setOfficialInvite] = useState("");
  const [colors, setColors] = useState<Record<string, string>>({});

  // Token state
  const [token, setToken] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [tokenStatus, setTokenStatus] = useState<"idle" | "testing" | "ok" | "fail">("idle");
  const [tokenInfo, setTokenInfo] = useState<string | null>(null);
  const [savingToken, setSavingToken] = useState(false);

  useEffect(() => {
    if (settings) {
      setBotName(settings.botName);
      setPrefix(settings.prefix);
      setOfficialInvite(settings.officialInvite);
      setColors(settings.colors as Record<string, string>);
    }
  }, [settings]);

  if (isLoading) return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-48 rounded-lg" style={{ background: "rgba(255,255,255,0.06)" }} />
      <Skeleton className="h-48 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
      <Skeleton className="h-64 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />
    </div>
  );

  const handleSave = () => {
    updateSettingsMutation.mutate({ data: { botName, prefix, officialInvite, colors } }, {
      onSuccess: () => {
        toast({ title: "✅ Podešavanja snimljena" });
        queryClient.invalidateQueries({ queryKey: getGetSettingsQueryKey() });
      },
      onError: () => toast({ title: "❌ Greška pri snimanju", variant: "destructive" }),
    });
  };

  const handleTestToken = async () => {
    if (!token.trim()) return;
    setTokenStatus("testing");
    setTokenInfo(null);
    try {
      const res = await fetch(`${BASE}/api/discord/debug`, {
        headers: { "x-discord-token": token.trim() },
      });
      if (res.ok) {
        const d = await res.json();
        setTokenStatus("ok");
        setTokenInfo(`✅ Povezan kao: ${d.appName ?? "Discord Bot"} · ${d.appEmojisCount ?? 0} emojia · ${d.guildEmojisCount ?? 0} guild emojia`);
      } else {
        setTokenStatus("fail");
        setTokenInfo("❌ Neispravan token — provjeri da je tačan");
      }
    } catch {
      setTokenStatus("fail");
      setTokenInfo("❌ Greška konekcije — pokušaj ponovo");
    }
  };

  const handleSaveToken = async () => {
    if (!token.trim()) return;
    setSavingToken(true);
    try {
      const res = await fetch(`${BASE}/api/settings/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: token.trim() }),
      });
      if (res.ok) {
        toast({ title: "✅ Token snimljen — emojii se osvježavaju" });
        setToken("");
        setTokenStatus("idle");
        setTokenInfo(null);
      } else {
        toast({ title: "❌ Greška pri snimanju tokena", variant: "destructive" });
      }
    } catch {
      toast({ title: "❌ Greška konekcije", variant: "destructive" });
    } finally {
      setSavingToken(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">Podešavanja</h1>
          <p className="text-sm mt-0.5" style={{ color: "#4b5563" }}>Konfiguracija GIANNI bota i panela</p>
        </div>
        <Button
          onClick={handleSave}
          disabled={updateSettingsMutation.isPending}
          data-testid="button-save-settings"
          className="font-bold"
          style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", border: "none", color: "white", boxShadow: "0 4px 15px rgba(99,102,241,0.3)" }}
        >
          {updateSettingsMutation.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
          Snimi promjene
        </Button>
      </div>

      {/* Discord Token */}
      <div style={S.card}>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base" style={{ background: "rgba(99,102,241,0.12)" }}>🔑</div>
          <div>
            <div className="font-bold text-white text-sm">Discord Bot Token</div>
            <div className="text-xs" style={{ color: "#4b5563" }}>Poveži bot direktno unosom tokena</div>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <label style={S.label}>Bot Token</label>
            <div className="relative">
              <Input
                type={showToken ? "text" : "password"}
                value={token}
                onChange={e => { setToken(e.target.value); setTokenStatus("idle"); setTokenInfo(null); }}
                placeholder="MTQ5Njg3..."
                className="pr-10 font-mono text-sm"
                style={S.input}
              />
              <button
                type="button"
                onClick={() => setShowToken(v => !v)}
                className="absolute right-3 top-2.5 transition-colors"
                style={{ color: "#4b5563" }}
              >
                {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Status message */}
          {tokenInfo && (
            <div className="flex items-start gap-2 px-3 py-2 rounded-lg text-xs" style={{
              background: tokenStatus === "ok" ? "rgba(34,197,94,0.08)" : "rgba(239,68,68,0.08)",
              border: `1px solid ${tokenStatus === "ok" ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)"}`,
              color: tokenStatus === "ok" ? "#86efac" : "#fca5a5",
            }}>
              {tokenStatus === "ok" ? <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" /> : <XCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />}
              <span>{tokenInfo}</span>
            </div>
          )}

          <div className="flex gap-2">
            <Button
              onClick={handleTestToken}
              disabled={!token.trim() || tokenStatus === "testing"}
              variant="outline"
              className="text-sm font-semibold"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", color: "#9ca3af" }}
            >
              {tokenStatus === "testing" ? <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />Testira...</> : "🔍 Testiraj konekciju"}
            </Button>
            <Button
              onClick={handleSaveToken}
              disabled={!token.trim() || savingToken || tokenStatus === "fail"}
              className="text-sm font-bold"
              style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", border: "none", color: "white" }}
            >
              {savingToken ? <><Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />Snima...</> : "💾 Snimi token"}
            </Button>
          </div>

          <p className="text-xs leading-relaxed" style={{ color: "#374151" }}>
            Token se čuva na serveru u <code className="px-1 rounded text-xs" style={{ background: "rgba(255,255,255,0.06)", color: "#6366f1" }}>data/settings.json</code> i
            odmah aktivira bez restarta. Dobij ga na <code className="px-1 rounded text-xs" style={{ background: "rgba(255,255,255,0.06)", color: "#6366f1" }}>discord.com/developers</code>.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* General */}
        <div style={S.card}>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base" style={{ background: "rgba(99,102,241,0.12)" }}>⚙️</div>
            <div>
              <div className="font-bold text-white text-sm">Opća podešavanja</div>
              <div className="text-xs" style={{ color: "#4b5563" }}>Identitet i konfiguracija bota</div>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label style={S.label}>Ime bota</label>
              <Input value={botName} onChange={e => setBotName(e.target.value)} style={S.input} data-testid="input-bot-name" />
            </div>
            <div>
              <label style={S.label}>Prefiks komande</label>
              <Input value={prefix} onChange={e => setPrefix(e.target.value)} style={{ ...S.input, fontFamily: "monospace" }} data-testid="input-bot-prefix" />
            </div>
            <div>
              <label style={S.label}>Invite link servera</label>
              <Input value={officialInvite} onChange={e => setOfficialInvite(e.target.value)} style={S.input} data-testid="input-bot-invite" />
            </div>
            {settings?.version && (
              <div className="pt-3 mt-3 flex justify-between items-center" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
                <span className="text-xs" style={{ color: "#4b5563" }}>Verzija</span>
                <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: "rgba(99,102,241,0.1)", color: "#a5b4fc" }}>{settings.version}</span>
              </div>
            )}
          </div>
        </div>

        {/* Colors */}
        <div style={S.card}>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base" style={{ background: "rgba(99,102,241,0.12)" }}>🎨</div>
            <div>
              <div className="font-bold text-white text-sm">Paleta boja</div>
              <div className="text-xs" style={{ color: "#4b5563" }}>Boje korištene u embed porukama</div>
            </div>
          </div>
          <div className="space-y-2 overflow-y-auto" style={{ maxHeight: "280px" }}>
            {Object.entries(colors).map(([key, hex]) => (
              <div key={key} className="flex items-center gap-2 px-2 py-1.5 rounded-lg" style={{ background: "rgba(255,255,255,0.03)" }}>
                <div className="w-6 h-6 rounded-md flex-shrink-0 border" style={{ backgroundColor: hex, borderColor: "rgba(255,255,255,0.1)" }} />
                <span className="flex-1 text-xs font-medium capitalize" style={{ color: "#9ca3af" }}>{key}</span>
                <input type="color" value={hex} onChange={e => setColors(c => ({ ...c, [key]: e.target.value }))} className="w-7 h-7 rounded cursor-pointer border-0 bg-transparent p-0" data-testid={`input-color-${key}-picker`} />
                <Input value={hex} onChange={e => setColors(c => ({ ...c, [key]: e.target.value }))} className="w-20 h-7 text-center font-mono text-xs uppercase" style={{ ...S.input, padding: "0 4px" }} data-testid={`input-color-${key}-text`} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
