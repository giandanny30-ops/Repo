import { useState, useEffect, useCallback } from "react";
import { useLocation } from "wouter";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const API = BASE;

type UnoColor = "red" | "green" | "blue" | "yellow" | "wild";
type UnoValue = string;
interface UnoCard { id: string; color: UnoColor; value: UnoValue }
interface UnoPlayer { id: string; name: string; handCount: number; saidUno: boolean; hand?: UnoCard[] }
interface RoomState {
  code: string; state: "waiting"|"playing"|"finished";
  players: UnoPlayer[]; currentIdx: number; direction: number;
  pendingColor: UnoColor | null; drawStack: number;
  topCard: UnoCard; winner: string | null; lastAction: string;
}

const COLOR_BG: Record<string, string> = {
  red: "linear-gradient(135deg,#ef4444,#dc2626)",
  green: "linear-gradient(135deg,#22c55e,#16a34a)",
  blue: "linear-gradient(135deg,#3b82f6,#2563eb)",
  yellow: "linear-gradient(135deg,#eab308,#ca8a04)",
  wild: "linear-gradient(135deg,#1f2937,#111827)",
};
const COLOR_LABEL: Record<string, string> = { red:"Crvena", green:"Zelena", blue:"Plava", yellow:"Žuta" };
const COLOR_HEX: Record<string, string> = { red:"#ef4444", green:"#22c55e", blue:"#3b82f6", yellow:"#eab308" };

function CardView({ card, playable, onClick, small }: { card: UnoCard; playable?: boolean; onClick?: () => void; small?: boolean }) {
  const size = small ? { width: 36, height: 54, fontSize: 9 } : { width: 64, height: 96, fontSize: 13 };
  const label = card.value === "wild" ? "W" : card.value === "wild4" ? "+4" : card.value === "draw2" ? "+2" : card.value === "skip" ? "⊘" : card.value === "reverse" ? "↺" : card.value;
  return (
    <div
      onClick={playable ? onClick : undefined}
      style={{
        ...size, borderRadius: small ? 6 : 10, background: COLOR_BG[card.color] || COLOR_BG.wild,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontWeight: 900, color: "#fff", cursor: playable ? "pointer" : "default",
        border: playable ? "2px solid rgba(255,255,255,0.8)" : "2px solid rgba(255,255,255,0.15)",
        boxShadow: playable ? "0 0 16px rgba(255,255,255,0.4), 0 4px 12px rgba(0,0,0,0.5)" : "0 2px 8px rgba(0,0,0,0.4)",
        transform: playable ? "translateY(-4px) scale(1.05)" : "none",
        transition: "all .15s", flexShrink: 0, textShadow: "0 1px 2px rgba(0,0,0,0.5)",
        position: "relative",
      }}
    >
      <span style={{ fontSize: size.fontSize * 1.4 }}>{label}</span>
      {small && <span style={{ position: "absolute", top: 2, left: 3, fontSize: 7, opacity: .7 }}>{card.color === "wild" ? "🌈" : ""}</span>}
    </div>
  );
}

export default function UnoGame() {
  const [, navigate] = useLocation();
  const [screen, setScreen] = useState<"home"|"lobby"|"game">("home");
  const [myName, setMyName] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [playerId, setPlayerId] = useState("");
  const [room, setRoom] = useState<RoomState | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [colorPicker, setColorPicker] = useState<number | null>(null);
  const [polling, setPolling] = useState(false);

  const fetchRoom = useCallback(async (code: string, pid: string) => {
    try {
      const r = await fetch(`${API}/api/play/uno/${code}?playerId=${pid}`);
      if (r.ok) { const d = await r.json(); setRoom(d); if (d.state === "playing" || d.state === "finished") setScreen("game"); }
    } catch {}
  }, []);

  useEffect(() => {
    if (!roomCode || !playerId || !polling) return;
    const iv = setInterval(() => fetchRoom(roomCode, playerId), 1500);
    return () => clearInterval(iv);
  }, [roomCode, playerId, polling, fetchRoom]);

  async function createRoom() {
    if (!myName.trim()) return setError("Unesi ime");
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/api/play/uno`, { method: "POST", headers: { "Content-Type":"application/json" } });
      const { code } = await r.json();
      const jr = await fetch(`${API}/api/play/uno/${code}/join`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ name: myName.trim() }) });
      const jd = await jr.json();
      if (!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId);
      await fetchRoom(code, jd.playerId);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Greška pri kreaciji sobe"); } finally { setLoading(false); }
  }

  async function joinRoom() {
    if (!myName.trim() || !joinCode.trim()) return setError("Unesi ime i kod sobe");
    setLoading(true); setError("");
    try {
      const code = joinCode.trim().toUpperCase();
      const jr = await fetch(`${API}/api/play/uno/${code}/join`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ name: myName.trim() }) });
      const jd = await jr.json();
      if (!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId);
      await fetchRoom(code, jd.playerId);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Soba ne postoji"); } finally { setLoading(false); }
  }

  async function startGame() {
    await fetch(`${API}/api/play/uno/${roomCode}/start`, { method: "POST" });
    await fetchRoom(roomCode, playerId);
  }

  async function action(payload: object) {
    setError("");
    const r = await fetch(`${API}/api/play/uno/${roomCode}/action`, {
      method: "POST", headers: { "Content-Type":"application/json" },
      body: JSON.stringify({ playerId, ...payload }),
    });
    const d = await r.json();
    if (!r.ok) { setError(d.error); return; }
    await fetchRoom(roomCode, playerId);
  }

  function handlePlayCard(idx: number, card: UnoCard) {
    if (card.value === "wild" || card.value === "wild4") { setColorPicker(idx); return; }
    action({ action: "play", cardIdx: idx });
  }

  const myPlayer = room?.players.find(p => p.id === playerId);
  const myHand = myPlayer?.hand ?? [];
  const isMyTurn = room?.players[room.currentIdx]?.id === playerId;
  const topCard = room?.topCard;
  const canPlayCard = (card: UnoCard): boolean => {
    if (!room || !isMyTurn) return false;
    if (room.drawStack > 0) return card.value === "draw2" || card.value === "wild4";
    if (card.value === "wild" || card.value === "wild4") return true;
    const eff = room.pendingColor ?? topCard?.color ?? "red";
    return card.color === eff || card.value === topCard?.value;
  };

  const Wrap = ({ children }: { children: React.ReactNode }) => (
    <div style={{ minHeight: "100vh", background: "#06070d", color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif", display: "flex", flexDirection: "column" }}>
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: "-200px", left: "-100px", width: "600px", height: "600px", borderRadius: "50%", background: "radial-gradient(circle,rgba(239,68,68,0.08) 0%,transparent 70%)", filter: "blur(80px)" }} />
        <div style={{ position: "absolute", bottom: 0, right: "-100px", width: "500px", height: "500px", borderRadius: "50%", background: "radial-gradient(circle,rgba(99,102,241,0.08) 0%,transparent 70%)", filter: "blur(80px)" }} />
      </div>
      <nav style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 32px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <button onClick={() => navigate("/play")} style={{ display: "flex", alignItems: "center", gap: "10px", background: "none", border: "none", color: "#fff", cursor: "pointer", fontSize: "16px", fontWeight: 800 }}>
          🃏 <span style={{ color: "#ef4444" }}>UNO</span>
        </button>
        {roomCode && <span style={{ fontSize: "13px", color: "#6b7280" }}>Soba: <b style={{ color: "#a5b4fc", letterSpacing: "2px" }}>{roomCode}</b></span>}
      </nav>
      <div style={{ flex: 1, position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );

  if (screen === "home") return (
    <Wrap>
      <div style={{ maxWidth: 480, margin: "0 auto", padding: "60px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 72, marginBottom: 16 }}>🃏</div>
          <h1 style={{ fontSize: 40, fontWeight: 900, margin: "0 0 8px", background: "linear-gradient(135deg,#ef4444,#f97316)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>UNO</h1>
          <p style={{ color: "#6b7280", fontSize: 15 }}>Multiplayer • 2–10 igrača</p>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16, padding: 28 }}>
          <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#6366f1", letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>Tvoje ime</label>
          <input value={myName} onChange={e => setMyName(e.target.value)} placeholder="Npr. Marko" maxLength={20}
            style={{ width: "100%", padding: "11px 14px", borderRadius: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: 14, outline: "none", boxSizing: "border-box", marginBottom: 16 }} />
          <button onClick={createRoom} disabled={loading || !myName.trim()}
            style={{ width: "100%", padding: "12px", borderRadius: 10, background: loading ? "rgba(239,68,68,0.3)" : "linear-gradient(135deg,#ef4444,#dc2626)", color: "#fff", fontWeight: 700, fontSize: 14, border: "none", cursor: "pointer", marginBottom: 12 }}>
            {loading ? "Kreiranje..." : "🃏 Kreiraj novu sobu"}
          </button>
          <div style={{ display: "flex", gap: 8 }}>
            <input value={joinCode} onChange={e => setJoinCode(e.target.value.toUpperCase())} placeholder="Kod sobe (npr. A3F2C1)" maxLength={6}
              style={{ flex: 1, padding: "11px 14px", borderRadius: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: 14, outline: "none", letterSpacing: 2 }} />
            <button onClick={joinRoom} disabled={loading || !myName.trim() || !joinCode.trim()}
              style={{ padding: "11px 20px", borderRadius: 10, background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.15)", color: "#fff", fontWeight: 600, fontSize: 14, cursor: "pointer" }}>
              Pridruži se
            </button>
          </div>
          {error && <p style={{ color: "#f87171", fontSize: 12, marginTop: 10 }}>⚠ {error}</p>}
        </div>
      </div>
    </Wrap>
  );

  if (screen === "lobby") return (
    <Wrap>
      <div style={{ maxWidth: 480, margin: "0 auto", padding: "60px 24px" }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8 }}>Čekaonica</h2>
          <div style={{ display: "inline-block", background: "rgba(99,102,241,0.15)", border: "1px solid rgba(99,102,241,0.4)", borderRadius: 10, padding: "8px 20px", letterSpacing: 4, fontSize: 22, fontWeight: 900, color: "#a5b4fc" }}>{roomCode}</div>
          <p style={{ color: "#6b7280", fontSize: 13, marginTop: 8 }}>Podijeli kod prijateljima</p>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16, padding: 20, marginBottom: 20 }}>
          <p style={{ fontSize: 11, fontWeight: 700, color: "#6b7280", letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Igrači ({room?.players.length ?? 0}/10)</p>
          {room?.players.map((p, i) => (
            <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < (room.players.length - 1) ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: "linear-gradient(135deg,#6366f1,#8b5cf6)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700 }}>{p.name[0].toUpperCase()}</div>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{p.name}</span>
              {p.id === playerId && <span style={{ fontSize: 11, color: "#a5b4fc", marginLeft: "auto" }}>Ti</span>}
              {i === 0 && <span style={{ fontSize: 11, color: "#f59e0b", marginLeft: "auto" }}>👑 Domaćin</span>}
            </div>
          ))}
        </div>
        {room?.players[0]?.id === playerId && (
          <button onClick={startGame} disabled={(room?.players.length ?? 0) < 2}
            style={{ width: "100%", padding: 14, borderRadius: 12, background: (room?.players.length ?? 0) < 2 ? "rgba(239,68,68,0.3)" : "linear-gradient(135deg,#ef4444,#dc2626)", color: "#fff", fontWeight: 700, fontSize: 15, border: "none", cursor: (room?.players.length ?? 0) < 2 ? "not-allowed" : "pointer", boxShadow: "0 0 20px rgba(239,68,68,0.3)" }}>
            {(room?.players.length ?? 0) < 2 ? "Čekanje na igrače..." : "▶ Pokreni igru"}
          </button>
        )}
        {room?.players[0]?.id !== playerId && <p style={{ textAlign: "center", color: "#6b7280", fontSize: 13 }}>Čekaj da domaćin pokrene igru...</p>}
      </div>
    </Wrap>
  );

  // Game screen
  const currentPlayerName = room?.players[room.currentIdx]?.name ?? "";
  return (
    <Wrap>
      {room?.state === "finished" && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", backdropFilter: "blur(12px)" }}>
          <div style={{ textAlign: "center", background: "rgba(10,11,15,0.95)", border: "1px solid rgba(99,102,241,0.4)", borderRadius: 24, padding: 48, maxWidth: 360 }}>
            <div style={{ fontSize: 72, marginBottom: 16 }}>🏆</div>
            <h2 style={{ fontSize: 32, fontWeight: 900, marginBottom: 8 }}>{room.winner} pobijedio/la!</h2>
            <p style={{ color: "#6b7280", marginBottom: 28 }}>Čestitamo na pobjedi!</p>
            <button onClick={() => { setScreen("home"); setRoom(null); setPolling(false); }}
              style={{ padding: "12px 28px", borderRadius: 10, background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "#fff", fontWeight: 700, border: "none", cursor: "pointer" }}>
              Nova igra
            </button>
          </div>
        </div>
      )}

      {colorPicker !== null && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", backdropFilter: "blur(8px)" }}>
          <div style={{ background: "rgba(10,11,15,0.98)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 20, padding: 32, textAlign: "center" }}>
            <h3 style={{ marginBottom: 20, fontSize: 18, fontWeight: 700 }}>Odaberi boju</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {(["red","green","blue","yellow"] as const).map(c => (
                <button key={c} onClick={() => { action({ action: "play", cardIdx: colorPicker, chosenColor: c }); setColorPicker(null); }}
                  style={{ padding: "16px 28px", borderRadius: 12, background: COLOR_BG[c], color: "#fff", fontWeight: 700, border: "none", cursor: "pointer", fontSize: 15, boxShadow: `0 0 16px ${COLOR_HEX[c]}66` }}>
                  {COLOR_LABEL[c]}
                </button>
              ))}
            </div>
            <button onClick={() => setColorPicker(null)} style={{ marginTop: 16, background: "none", border: "none", color: "#6b7280", cursor: "pointer", fontSize: 13 }}>Odustani</button>
          </div>
        </div>
      )}

      <div style={{ padding: "16px 20px", maxWidth: 800, margin: "0 auto" }}>
        {/* Status bar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {room?.players.map((p, i) => (
              <div key={p.id} style={{ padding: "4px 12px", borderRadius: 20, background: i === room.currentIdx ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.05)", border: i === room.currentIdx ? "1px solid rgba(239,68,68,0.6)" : "1px solid rgba(255,255,255,0.08)", fontSize: 12, fontWeight: i === room.currentIdx ? 700 : 400 }}>
                {i === room.currentIdx ? "▶ " : ""}{p.name} {p.id === playerId ? "(Ti)" : ""} <span style={{ color: "#6b7280" }}>[{p.handCount}]</span>
                {p.saidUno && <span style={{ color: "#ef4444", marginLeft: 4 }}>UNO!</span>}
              </div>
            ))}
          </div>
          <div style={{ fontSize: 12, color: "#6b7280" }}>{room?.direction === 1 ? "→" : "←"} {room?.lastAction}</div>
        </div>

        {/* Game area */}
        <div style={{ display: "flex", gap: 20, alignItems: "flex-start", flexWrap: "wrap" }}>
          {/* Center area */}
          <div style={{ flex: "0 0 auto", display: "flex", flexDirection: "column", alignItems: "center", gap: 16, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16, padding: 24, minWidth: 200 }}>
            <div>
              <p style={{ fontSize: 11, color: "#6b7280", marginBottom: 8, textAlign: "center", textTransform: "uppercase", letterSpacing: 1 }}>Gornja karta</p>
              {topCard && <CardView card={topCard} />}
              {room?.pendingColor && <p style={{ fontSize: 11, color: COLOR_HEX[room.pendingColor], textAlign: "center", marginTop: 6, fontWeight: 700 }}>Boja: {COLOR_LABEL[room.pendingColor]}</p>}
              {(room?.drawStack ?? 0) > 0 && <p style={{ fontSize: 13, color: "#f97316", textAlign: "center", marginTop: 4, fontWeight: 700 }}>Naredni vuče +{room!.drawStack}</p>}
            </div>
            {isMyTurn && (
              <div style={{ display: "flex", gap: 8, flexDirection: "column", width: "100%" }}>
                <button onClick={() => action({ action: "draw" })}
                  style={{ width: "100%", padding: "10px", borderRadius: 10, background: "rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.4)", color: "#a5b4fc", fontWeight: 700, fontSize: 13, cursor: "pointer" }}>
                  {room?.drawStack > 0 ? `Uzmi +${room.drawStack}` : "Vuci kartu"}
                </button>
                {myPlayer && myPlayer.handCount <= 2 && (
                  <button onClick={() => action({ action: "uno" })}
                    style={{ width: "100%", padding: "10px", borderRadius: 10, background: "rgba(239,68,68,0.2)", border: "1px solid rgba(239,68,68,0.4)", color: "#fca5a5", fontWeight: 700, fontSize: 13, cursor: "pointer" }}>
                    🗣 UNO!
                  </button>
                )}
              </div>
            )}
            {!isMyTurn && <p style={{ fontSize: 12, color: "#6b7280", textAlign: "center" }}>Red: <b style={{ color: "#fff" }}>{currentPlayerName}</b></p>}
          </div>

          {/* My hand */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 11, color: "#6b7280", marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 }}>Tvoje karte ({myHand.length})</p>
            {myHand.length === 0 && room?.state === "playing" && <p style={{ color: "#6b7280", fontSize: 14 }}>Nema karata</p>}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {myHand.map((card, i) => {
                const playable = canPlayCard(card);
                return <CardView key={card.id} card={card} playable={playable} onClick={() => handlePlayCard(i, card)} />;
              })}
            </div>
            {error && <p style={{ color: "#f87171", fontSize: 12, marginTop: 10 }}>⚠ {error}</p>}
          </div>
        </div>
      </div>
    </Wrap>
  );
}
