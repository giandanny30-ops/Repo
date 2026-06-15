import { useState, useEffect, useCallback } from "react";
import { useLocation } from "wouter";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const API = BASE;

type LudoColor = "red" | "blue" | "green" | "yellow";
interface LudoPiece { pos: number; home: boolean; finished: boolean }
interface LudoPlayer { id: string; name: string; color: LudoColor; pieces: LudoPiece[] }
interface LudoRoom {
  code: string; state: "waiting"|"playing"|"finished";
  players: LudoPlayer[]; currentIdx: number;
  dice: number | null; diceRolled: boolean;
  winner: string | null; lastAction: string;
}

const COLOR_CSS: Record<LudoColor, string> = { red: "#ef4444", blue: "#3b82f6", green: "#22c55e", yellow: "#eab308" };
const COLOR_BG: Record<LudoColor, string> = { red: "linear-gradient(135deg,#ef4444,#dc2626)", blue: "linear-gradient(135deg,#3b82f6,#2563eb)", green: "linear-gradient(135deg,#22c55e,#16a34a)", yellow: "linear-gradient(135deg,#eab308,#ca8a04)" };
const COLOR_LABEL: Record<LudoColor, string> = { red: "Crvena", blue: "Plava", green: "Zelena", yellow: "Žuta" };
const COLORS: LudoColor[] = ["red","blue","green","yellow"];

// Board layout — simplified 11x11 Ludo grid
// Cells are squares on the path. We'll render a visual board.
const BOARD_SIZE = 11;

function Board({ room, playerId, onMove }: { room: LudoRoom; playerId: string; onMove: (pieceIdx: number) => void }) {
  const cellSize = 44;
  const boardPx = BOARD_SIZE * cellSize;
  const player = room.players.find(p => p.id === playerId);
  const isMyTurn = room.players[room.currentIdx]?.id === playerId;

  // Safe squares on the main path
  const SAFE: number[] = [0, 8, 13, 21, 26, 34, 39, 47];

  // Map absolute board positions (0-51) to grid coordinates
  function absToGrid(abs: number): [number, number] {
    // Main path: 52 squares going clockwise
    // Bottom row: 0-5 (col 0..5, row 10)
    // Right column going up: 6..11 (col 6, row 10..5 → but row 9..4)
    // Actually let's do a simpler approach for display
    const path: [number, number][] = [];
    // Bottom: left to right (row 10, col 1..5)
    for (let c = 1; c <= 5; c++) path.push([10, c]);
    // Right bottom corner: col6, row 10..6
    path.push([10, 6]);
    for (let r = 9; r >= 6; r--) path.push([r, 6]);
    path.push([5, 6]);
    // Top: right to left (row 0, col 6..10 going down to row 4)
    for (let r = 4; r >= 1; r--) path.push([r, 6]);
    path.push([0, 6]);
    // Top row: col 5..1
    for (let c = 5; c >= 1; c--) path.push([0, c]);
    // Left top: col0, row 0..4
    path.push([0, 4]);
    for (let r = 1; r <= 4; r++) path.push([r, 4]);
    path.push([5, 4]);
    // Left column going down
    for (let r = 6; r <= 9; r++) path.push([r, 4]);
    path.push([10, 4]);
    for (let c = 3; c >= 1; c--) path.push([10, c]);
    while (path.length < 52) path.push([10, 0]);
    return path[abs % path.length] ?? [5, 5];
  }

  // Render pieces on the board
  const pieces: { color: LudoColor; idx: number; playerId: string; piece: LudoPiece }[] = [];
  for (const p of room.players) {
    for (let i = 0; i < p.pieces.length; i++) {
      pieces.push({ color: p.color, idx: i, playerId: p.id, piece: p.pieces[i] });
    }
  }

  // Home positions for each color
  const homePos: Record<LudoColor, [number,number][]> = {
    red: [[1,1],[1,2],[2,1],[2,2]],
    blue: [[1,8],[1,9],[2,8],[2,9]],
    green: [[8,8],[8,9],[9,8],[9,9]],
    yellow: [[8,1],[8,2],[9,1],[9,2]],
  };

  // Color zones on the board (home columns)
  const colorZone: Record<LudoColor, [number,number][]> = {
    red:    [[6,1],[6,2],[6,3],[6,4],[6,5]],
    blue:   [[1,5],[2,5],[3,5],[4,5],[5,5]],
    green:  [[4,6],[4,7],[4,8],[4,9],[4,10]],
    yellow: [[6,5],[7,5],[8,5],[9,5],[10,5]], // simplified
  };

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      {/* Grid */}
      <svg width={boardPx} height={boardPx} style={{ display: "block" }}>
        {/* Background */}
        <rect width={boardPx} height={boardPx} fill="#0f1117" rx={8} />

        {/* Color home squares */}
        {([["red",0,0],["blue",0,6],["green",6,6],["yellow",6,0]] as [LudoColor,number,number][]).map(([c,r,col]) => (
          <rect key={c} x={col*cellSize+2} y={r*cellSize+2} width={cellSize*5-4} height={cellSize*5-4}
            fill={`${COLOR_CSS[c]}22`} stroke={COLOR_CSS[c]} strokeWidth={1.5} rx={6} />
        ))}

        {/* Grid lines */}
        {Array.from({length: BOARD_SIZE+1},(_,i) => (
          <g key={i}>
            <line x1={0} y1={i*cellSize} x2={boardPx} y2={i*cellSize} stroke="rgba(255,255,255,0.06)" strokeWidth={0.5} />
            <line x1={i*cellSize} y1={0} x2={i*cellSize} y2={boardPx} stroke="rgba(255,255,255,0.06)" strokeWidth={0.5} />
          </g>
        ))}

        {/* Center finish */}
        <polygon points={`${5*cellSize},${5*cellSize} ${6*cellSize},${5*cellSize} ${5.5*cellSize},${5.5*cellSize}`} fill="#ef4444" opacity={0.7} />
        <polygon points={`${5*cellSize},${6*cellSize} ${6*cellSize},${6*cellSize} ${5.5*cellSize},${5.5*cellSize}`} fill="#22c55e" opacity={0.7} />
        <polygon points={`${5*cellSize},${5*cellSize} ${5*cellSize},${6*cellSize} ${5.5*cellSize},${5.5*cellSize}`} fill="#eab308" opacity={0.7} />
        <polygon points={`${6*cellSize},${5*cellSize} ${6*cellSize},${6*cellSize} ${5.5*cellSize},${5.5*cellSize}`} fill="#3b82f6" opacity={0.7} />

        {/* Safe squares markers */}
        {SAFE.map(sq => {
          const [r, c] = absToGrid(sq);
          return <rect key={sq} x={c*cellSize+3} y={r*cellSize+3} width={cellSize-6} height={cellSize-6} fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={1} strokeDasharray="3" rx={3} />;
        })}

        {/* Home area pieces */}
        {room.players.map(p => (
          homePos[p.color].map((hpos, i) => {
            const piece = p.pieces[i];
            if (!piece.home) return null;
            const [r,c] = hpos;
            const canMove2 = isMyTurn && p.id === playerId && piece.home && room.diceRolled && room.dice === 6;
            return (
              <g key={`${p.id}-h${i}`} onClick={() => canMove2 && onMove(i)} style={{ cursor: canMove2 ? "pointer" : "default" }}>
                <circle cx={c*cellSize+cellSize/2} cy={r*cellSize+cellSize/2} r={14} fill={COLOR_CSS[p.color]} opacity={0.9} />
                <circle cx={c*cellSize+cellSize/2} cy={r*cellSize+cellSize/2} r={8} fill="rgba(255,255,255,0.3)" />
                <text x={c*cellSize+cellSize/2} y={r*cellSize+cellSize/2+4} textAnchor="middle" fontSize={9} fill="#fff" fontWeight={700}>{i+1}</text>
                {canMove2 && <circle cx={c*cellSize+cellSize/2} cy={r*cellSize+cellSize/2} r={16} fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth={2} strokeDasharray="4" />}
              </g>
            );
          })
        ))}

        {/* On-track pieces */}
        {pieces.filter(pp => !pp.piece.home && !pp.piece.finished && pp.piece.pos < 52).map((pp) => {
          const startOffsets: Record<LudoColor,number> = { red:0, blue:13, green:26, yellow:39 };
          const abs = (startOffsets[pp.color] + pp.piece.pos) % 52;
          const [r,c] = absToGrid(abs);
          const canMove2 = isMyTurn && pp.playerId === playerId && room.diceRolled && !pp.piece.home;
          return (
            <g key={`${pp.playerId}-t${pp.idx}`} onClick={() => canMove2 && onMove(pp.idx)} style={{ cursor: canMove2 ? "pointer" : "default" }}>
              <circle cx={c*cellSize+cellSize/2} cy={r*cellSize+cellSize/2} r={14} fill={COLOR_CSS[pp.color]} opacity={0.9} />
              <circle cx={c*cellSize+cellSize/2} cy={r*cellSize+cellSize/2} r={8} fill="rgba(255,255,255,0.25)" />
              <text x={c*cellSize+cellSize/2} y={r*cellSize+cellSize/2+4} textAnchor="middle" fontSize={9} fill="#fff" fontWeight={700}>{pp.idx+1}</text>
              {canMove2 && <circle cx={c*cellSize+cellSize/2} cy={r*cellSize+cellSize/2} r={16} fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth={2} strokeDasharray="4" />}
            </g>
          );
        })}
      </svg>

      {/* Player home labels */}
      {room.players.map((p, i) => {
        const positions: Record<string,React.CSSProperties> = {
          "0": { top: 2, left: 2 }, "1": { top: 2, right: 2 }, "2": { bottom: 2, right: 2 }, "3": { bottom: 2, left: 2 }
        };
        return (
          <div key={p.id} style={{ position: "absolute", ...positions[String(i)], background: `${COLOR_CSS[p.color]}33`, border: `1px solid ${COLOR_CSS[p.color]}66`, borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 700, color: COLOR_CSS[p.color] }}>
            {p.name}{p.id === playerId ? " (Ti)" : ""}
          </div>
        );
      })}
    </div>
  );
}

export default function LudoGame() {
  const [, navigate] = useLocation();
  const [screen, setScreen] = useState<"home"|"lobby"|"game">("home");
  const [myName, setMyName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const [playerId, setPlayerId] = useState("");
  const [myColor, setMyColor] = useState<LudoColor>("red");
  const [room, setRoom] = useState<LudoRoom | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);

  const fetchRoom = useCallback(async (code: string) => {
    try {
      const r = await fetch(`${API}/api/play/ludo/${code}`);
      if (r.ok) { const d = await r.json(); setRoom(d); if (d.state === "playing" || d.state === "finished") setScreen("game"); }
    } catch {}
  }, []);

  useEffect(() => {
    if (!roomCode || !polling) return;
    const iv = setInterval(() => fetchRoom(roomCode), 1500);
    return () => clearInterval(iv);
  }, [roomCode, polling, fetchRoom]);

  async function createRoom() {
    if (!myName.trim()) return setError("Unesi ime");
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/api/play/ludo`, { method: "POST", headers: { "Content-Type":"application/json" } });
      const { code } = await r.json();
      const jr = await fetch(`${API}/api/play/ludo/${code}/join`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ name: myName.trim() }) });
      const jd = await jr.json();
      if (!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId); setMyColor(jd.color);
      await fetchRoom(code);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Greška"); } finally { setLoading(false); }
  }

  async function joinRoom() {
    if (!myName.trim() || !joinCode.trim()) return setError("Unesi ime i kod");
    setLoading(true); setError("");
    try {
      const code = joinCode.trim().toUpperCase();
      const jr = await fetch(`${API}/api/play/ludo/${code}/join`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ name: myName.trim() }) });
      const jd = await jr.json();
      if (!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId); setMyColor(jd.color);
      await fetchRoom(code);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Soba ne postoji"); } finally { setLoading(false); }
  }

  async function startGame() {
    await fetch(`${API}/api/play/ludo/${roomCode}/start`, { method: "POST" });
    await fetchRoom(roomCode);
  }

  async function rollDice() {
    setError("");
    const r = await fetch(`${API}/api/play/ludo/${roomCode}/action`, {
      method: "POST", headers: { "Content-Type":"application/json" },
      body: JSON.stringify({ playerId, action: "roll" }),
    });
    const d = await r.json();
    if (!r.ok) setError(d.error);
    await fetchRoom(roomCode);
  }

  async function movePiece(pieceIdx: number) {
    setError("");
    const r = await fetch(`${API}/api/play/ludo/${roomCode}/action`, {
      method: "POST", headers: { "Content-Type":"application/json" },
      body: JSON.stringify({ playerId, action: "move", pieceIdx }),
    });
    const d = await r.json();
    if (!r.ok) setError(d.error);
    await fetchRoom(roomCode);
  }

  const isMyTurn = room?.players[room.currentIdx]?.id === playerId;
  const currentPlayerName = room?.players[room?.currentIdx ?? 0]?.name ?? "";
  const myPlayer = room?.players.find(p => p.id === playerId);

  const Wrap = ({ children }: { children: React.ReactNode }) => (
    <div style={{ minHeight: "100vh", background: "#06070d", color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif", display: "flex", flexDirection: "column" }}>
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: "-100px", left: "-100px", width: "500px", height: "500px", borderRadius: "50%", background: "radial-gradient(circle,rgba(16,185,129,0.08) 0%,transparent 70%)", filter: "blur(60px)" }} />
        <div style={{ position: "absolute", bottom: 0, right: 0, width: "400px", height: "400px", borderRadius: "50%", background: "radial-gradient(circle,rgba(99,102,241,0.08) 0%,transparent 70%)", filter: "blur(60px)" }} />
      </div>
      <nav style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 32px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <button onClick={() => navigate("/play")} style={{ display: "flex", alignItems: "center", gap: "10px", background: "none", border: "none", color: "#fff", cursor: "pointer", fontSize: "16px", fontWeight: 800 }}>
          🎲 <span style={{ color: "#22c55e" }}>Čovječe ne ljuti se</span>
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
          <div style={{ fontSize: 72, marginBottom: 16 }}>🎲</div>
          <h1 style={{ fontSize: 36, fontWeight: 900, margin: "0 0 8px", background: "linear-gradient(135deg,#22c55e,#10b981)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Čovječe ne ljuti se</h1>
          <p style={{ color: "#6b7280", fontSize: 15 }}>Multiplayer • 2–4 igrača</p>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16, padding: 28 }}>
          <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#22c55e", letterSpacing: 1, textTransform: "uppercase", marginBottom: 8 }}>Tvoje ime</label>
          <input value={myName} onChange={e => setMyName(e.target.value)} placeholder="Npr. Ana" maxLength={20}
            style={{ width: "100%", padding: "11px 14px", borderRadius: 10, background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#fff", fontSize: 14, outline: "none", boxSizing: "border-box", marginBottom: 16 }} />
          <button onClick={createRoom} disabled={loading || !myName.trim()}
            style={{ width: "100%", padding: 12, borderRadius: 10, background: loading ? "rgba(34,197,94,0.3)" : "linear-gradient(135deg,#22c55e,#16a34a)", color: "#fff", fontWeight: 700, fontSize: 14, border: "none", cursor: "pointer", marginBottom: 12 }}>
            {loading ? "Kreiranje..." : "🎲 Kreiraj novu sobu"}
          </button>
          <div style={{ display: "flex", gap: 8 }}>
            <input value={joinCode} onChange={e => setJoinCode(e.target.value.toUpperCase())} placeholder="Kod sobe" maxLength={6}
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
          <div style={{ display: "inline-block", background: "rgba(34,197,94,0.15)", border: "1px solid rgba(34,197,94,0.4)", borderRadius: 10, padding: "8px 20px", letterSpacing: 4, fontSize: 22, fontWeight: 900, color: "#86efac" }}>{roomCode}</div>
          <p style={{ color: "#6b7280", fontSize: 13, marginTop: 8 }}>Podijeli kod prijateljima</p>
        </div>
        <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 16, padding: 20, marginBottom: 20 }}>
          <p style={{ fontSize: 11, fontWeight: 700, color: "#6b7280", letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Igrači ({room?.players.length ?? 0}/4)</p>
          {room?.players.map((p, i) => (
            <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < (room.players.length - 1) ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
              <div style={{ width: 32, height: 32, borderRadius: "50%", background: COLOR_BG[p.color], display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700 }}>{p.name[0].toUpperCase()}</div>
              <span style={{ fontSize: 14, fontWeight: 600 }}>{p.name}</span>
              <span style={{ fontSize: 11, color: COLOR_CSS[p.color], marginLeft: 4 }}>({COLOR_LABEL[p.color]})</span>
              {p.id === playerId && <span style={{ fontSize: 11, color: "#a5b4fc", marginLeft: "auto" }}>Ti</span>}
              {i === 0 && <span style={{ fontSize: 11, color: "#f59e0b", marginLeft: "auto" }}>👑 Domaćin</span>}
            </div>
          ))}
        </div>
        {room?.players[0]?.id === playerId && (
          <button onClick={startGame} disabled={(room?.players.length ?? 0) < 2}
            style={{ width: "100%", padding: 14, borderRadius: 12, background: (room?.players.length ?? 0) < 2 ? "rgba(34,197,94,0.3)" : "linear-gradient(135deg,#22c55e,#16a34a)", color: "#fff", fontWeight: 700, fontSize: 15, border: "none", cursor: (room?.players.length ?? 0) < 2 ? "not-allowed" : "pointer" }}>
            {(room?.players.length ?? 0) < 2 ? "Čekanje na igrače..." : "▶ Pokreni igru"}
          </button>
        )}
        {room?.players[0]?.id !== playerId && <p style={{ textAlign: "center", color: "#6b7280", fontSize: 13 }}>Čekaj da domaćin pokrene igru...</p>}
      </div>
    </Wrap>
  );

  return (
    <Wrap>
      {room?.state === "finished" && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center", backdropFilter: "blur(12px)" }}>
          <div style={{ textAlign: "center", background: "rgba(10,11,15,0.95)", border: "1px solid rgba(34,197,94,0.4)", borderRadius: 24, padding: 48, maxWidth: 360 }}>
            <div style={{ fontSize: 72, marginBottom: 16 }}>🏆</div>
            <h2 style={{ fontSize: 32, fontWeight: 900, marginBottom: 8 }}>{room.winner} pobijedio/la!</h2>
            <p style={{ color: "#6b7280", marginBottom: 28 }}>Čestitamo!</p>
            <button onClick={() => { setScreen("home"); setRoom(null); setPolling(false); }}
              style={{ padding: "12px 28px", borderRadius: 10, background: "linear-gradient(135deg,#22c55e,#16a34a)", color: "#fff", fontWeight: 700, border: "none", cursor: "pointer" }}>
              Nova igra
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 20, padding: "16px 20px", maxWidth: 960, margin: "0 auto", flexWrap: "wrap", alignItems: "flex-start" }}>
        {/* Board */}
        <div style={{ flex: "0 0 auto" }}>
          <Board room={room!} playerId={playerId} onMove={movePiece} />
        </div>

        {/* Controls */}
        <div style={{ flex: 1, minWidth: 220 }}>
          {/* Status */}
          <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: 16, marginBottom: 14 }}>
            <p style={{ fontSize: 12, color: "#6b7280", marginBottom: 6 }}>Zadnja akcija</p>
            <p style={{ fontSize: 14, color: "#e5e7eb", fontWeight: 600 }}>{room?.lastAction}</p>
          </div>

          {/* Dice */}
          <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: 20, marginBottom: 14, textAlign: "center" }}>
            {room?.dice && (
              <div style={{ fontSize: 56, marginBottom: 12 }}>
                {["⚀","⚁","⚂","⚃","⚄","⚅"][room.dice - 1]}
              </div>
            )}
            {!room?.diceRolled && isMyTurn && (
              <button onClick={rollDice}
                style={{ width: "100%", padding: "12px", borderRadius: 10, background: "linear-gradient(135deg,#22c55e,#16a34a)", color: "#fff", fontWeight: 700, fontSize: 14, border: "none", cursor: "pointer", boxShadow: "0 0 20px rgba(34,197,94,0.4)" }}>
                🎲 Baci kockicu
              </button>
            )}
            {!isMyTurn && <p style={{ fontSize: 13, color: "#6b7280" }}>Red: <b style={{ color: "#fff" }}>{currentPlayerName}</b></p>}
            {isMyTurn && room?.diceRolled && <p style={{ fontSize: 13, color: "#86efac", fontWeight: 600 }}>Klikni na figuru da se pomjeri</p>}
          </div>

          {error && <p style={{ color: "#f87171", fontSize: 12, marginBottom: 12 }}>⚠ {error}</p>}

          {/* Players */}
          <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 14, padding: 16 }}>
            <p style={{ fontSize: 11, fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Igrači</p>
            {room?.players.map((p, i) => {
              const finCount = p.pieces.filter(pc => pc.finished).length;
              return (
                <div key={p.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 0", borderBottom: i < (room.players.length-1) ? "1px solid rgba(255,255,255,0.05)" : "none" }}>
                  <div style={{ width: 28, height: 28, borderRadius: "50%", background: COLOR_BG[p.color], display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700, flexShrink: 0 }}>{p.name[0]}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: i === room.currentIdx ? 700 : 500 }}>{p.name}{p.id === playerId ? " (Ti)" : ""}</div>
                    <div style={{ fontSize: 11, color: "#6b7280" }}>{finCount}/4 figura doma</div>
                  </div>
                  {i === room.currentIdx && <div style={{ fontSize: 11, color: COLOR_CSS[p.color], fontWeight: 700 }}>▶</div>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Wrap>
  );
}
