import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@/context/AuthContext";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const API = BASE;

// ─── Types ────────────────────────────────────────────────────────────────────
type UnoColor = "red" | "green" | "blue" | "yellow" | "wild";
interface UnoCard { id: string; color: UnoColor; value: string }
interface UnoPlayer { id: string; name: string; handCount: number; saidUno: boolean; hand?: UnoCard[] }
interface UnoRoom {
  code: string; state: "waiting"|"playing"|"finished";
  players: UnoPlayer[]; currentIdx: number; direction: number;
  pendingColor: UnoColor|null; drawStack: number;
  topCard: UnoCard; winner: string|null; lastAction: string;
}
type LudoColor = "red"|"blue"|"green"|"yellow";
interface LudoPiece { pos: number; home: boolean; finished: boolean }
interface LudoPlayer { id: string; name: string; color: LudoColor; pieces: LudoPiece[] }
interface LudoRoom {
  code: string; state: "waiting"|"playing"|"finished";
  players: LudoPlayer[]; currentIdx: number;
  dice: number|null; diceRolled: boolean;
  winner: string|null; lastAction: string;
}

// ─── UNO helpers ──────────────────────────────────────────────────────────────
const UNO_COLOR_BG: Record<string,string> = {
  red:"linear-gradient(135deg,#ef4444,#dc2626)",
  green:"linear-gradient(135deg,#22c55e,#16a34a)",
  blue:"linear-gradient(135deg,#3b82f6,#2563eb)",
  yellow:"linear-gradient(135deg,#eab308,#ca8a04)",
  wild:"linear-gradient(135deg,#1f2937,#111827)",
};
const UNO_COLOR_LABEL: Record<string,string> = { red:"Crvena",green:"Zelena",blue:"Plava",yellow:"Žuta" };
const UNO_COLOR_HEX: Record<string,string> = { red:"#ef4444",green:"#22c55e",blue:"#3b82f6",yellow:"#eab308" };

function UnoCardView({ card, playable, onClick, small }: { card: UnoCard; playable?: boolean; onClick?: () => void; small?: boolean }) {
  const sz = small ? { w:40,h:58,fs:10 } : { w:62,h:92,fs:13 };
  const lbl = card.value==="wild"?"W":card.value==="wild4"?"+4":card.value==="draw2"?"+2":card.value==="skip"?"⊘":card.value==="reverse"?"↺":card.value;
  return (
    <div onClick={playable?onClick:undefined} style={{
      width:sz.w,height:sz.h,borderRadius:8,background:UNO_COLOR_BG[card.color]||UNO_COLOR_BG.wild,
      display:"flex",alignItems:"center",justifyContent:"center",fontWeight:900,color:"#fff",
      cursor:playable?"pointer":"default",flexShrink:0,
      border:playable?"2px solid rgba(255,255,255,0.85)":"2px solid rgba(255,255,255,0.15)",
      boxShadow:playable?"0 0 14px rgba(255,255,255,0.35),0 4px 10px rgba(0,0,0,0.5)":"0 2px 6px rgba(0,0,0,0.4)",
      transform:playable?"translateY(-6px) scale(1.06)":"none",transition:"all .15s",
      fontSize:sz.fs*1.4,textShadow:"0 1px 2px rgba(0,0,0,0.5)",position:"relative",
    }}>{lbl}</div>
  );
}

// ─── LUDO helpers ─────────────────────────────────────────────────────────────
const LUDO_COLOR: Record<LudoColor,string> = { red:"#ef4444",blue:"#3b82f6",green:"#22c55e",yellow:"#eab308" };
const LUDO_COLOR_BG: Record<LudoColor,string> = { red:"linear-gradient(135deg,#ef4444,#dc2626)",blue:"linear-gradient(135deg,#3b82f6,#2563eb)",green:"linear-gradient(135deg,#22c55e,#16a34a)",yellow:"linear-gradient(135deg,#eab308,#ca8a04)" };
const LUDO_LABEL: Record<LudoColor,string> = { red:"Crvena",blue:"Plava",green:"Zelena",yellow:"Žuta" };

// ─── Main component ───────────────────────────────────────────────────────────
export default function Landing() {
  const { isAuthenticated, login } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [loginPwd, setLoginPwd] = useState("");
  const [loginErr, setLoginErr] = useState<string|null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  // Active game panel: null = landing, "uno" = UNO, "ludo" = Ludo
  const [activeGame, setActiveGame] = useState<null|"uno"|"ludo">(null);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoginErr(null); setLoginLoading(true);
    const err = await login(loginPwd);
    setLoginLoading(false);
    if (err) setLoginErr(err);
    else { setShowLogin(false); window.location.reload(); }
  }

  if (activeGame === "uno") return <UnoPanel onBack={() => setActiveGame(null)} />;
  if (activeGame === "ludo") return <LudoPanel onBack={() => setActiveGame(null)} />;

  return (
    <div style={{ background:"#06070d",minHeight:"100vh",fontFamily:"'Segoe UI',system-ui,sans-serif",color:"#fff",overflowX:"hidden" }}>
      {/* BG */}
      <div style={{ position:"fixed",inset:0,pointerEvents:"none",zIndex:0 }}>
        <div style={{ position:"absolute",top:"-200px",left:"-100px",width:"700px",height:"700px",borderRadius:"50%",background:"radial-gradient(circle,rgba(99,102,241,0.12) 0%,transparent 70%)",filter:"blur(80px)" }} />
        <div style={{ position:"absolute",bottom:0,right:"-100px",width:"600px",height:"600px",borderRadius:"50%",background:"radial-gradient(circle,rgba(139,92,246,0.10) 0%,transparent 70%)",filter:"blur(80px)" }} />
        <div style={{ position:"absolute",inset:0,backgroundImage:"radial-gradient(circle,rgba(99,102,241,0.07) 1px,transparent 1px)",backgroundSize:"40px 40px",opacity:0.5 }} />
      </div>

      {/* Nav */}
      <nav style={{ position:"relative",zIndex:10,display:"flex",alignItems:"center",justifyContent:"space-between",padding:"18px 40px",borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ display:"flex",alignItems:"center",gap:12 }}>
          <img src={`${BASE}/gian-bot-penguin.png`} alt="GIAN BOT" style={{ width:38,height:38,borderRadius:"50%",objectFit:"cover" }} />
          <span style={{ fontWeight:800,fontSize:17 }}><span style={{ color:"#6366f1" }}>GIAN</span> BOT</span>
        </div>
        <div style={{ display:"flex",gap:10 }}>
          {isAuthenticated ? (
            <a href={BASE+"/"} style={{ padding:"8px 18px",borderRadius:8,background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:600,textDecoration:"none" }}>Panel →</a>
          ) : (
            <button onClick={() => setShowLogin(true)} style={{ padding:"8px 18px",borderRadius:8,background:"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontSize:13,fontWeight:700,border:"none",cursor:"pointer" }}>🔐 Prijavi se</button>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section style={{ position:"relative",zIndex:1,display:"flex",alignItems:"center",justifyContent:"center",gap:70,padding:"64px 40px 48px",maxWidth:1060,margin:"0 auto",flexWrap:"wrap" }}>
        <div style={{ position:"relative",flexShrink:0 }}>
          <div style={{ position:"absolute",inset:"-20px",borderRadius:"50%",background:"radial-gradient(circle,rgba(99,102,241,0.22) 0%,transparent 70%)",filter:"blur(28px)" }} />
          <div style={{ width:210,height:210,borderRadius:"50%",background:"linear-gradient(135deg,rgba(99,102,241,0.18),rgba(139,92,246,0.18))",border:"2px solid rgba(99,102,241,0.35)",display:"flex",alignItems:"center",justifyContent:"center",boxShadow:"0 0 56px rgba(99,102,241,0.28),0 0 110px rgba(99,102,241,0.12)",position:"relative" }}>
            <img src={`${BASE}/gian-bot-penguin.png`} alt="GIAN BOT" style={{ width:170,height:170,objectFit:"contain",borderRadius:"50%",filter:"drop-shadow(0 0 18px rgba(99,102,241,0.45))" }} />
          </div>
          <div style={{ position:"absolute",top:"-8px",right:"-28px",background:"rgba(16,185,129,0.9)",color:"#fff",padding:"4px 10px",borderRadius:20,fontSize:11,fontWeight:700,whiteSpace:"nowrap" }}>● Online</div>
          <div style={{ position:"absolute",bottom:18,left:"-38px",background:"rgba(99,102,241,0.9)",color:"#fff",padding:"4px 10px",borderRadius:20,fontSize:11,fontWeight:700,whiteSpace:"nowrap" }}>Bot v2.0</div>
        </div>
        <div style={{ maxWidth:460 }}>
          <div style={{ display:"inline-flex",alignItems:"center",gap:8,background:"rgba(99,102,241,0.14)",border:"1px solid rgba(99,102,241,0.3)",borderRadius:20,padding:"5px 13px",marginBottom:18 }}>
            <span style={{ fontSize:11,color:"#a5b4fc",fontWeight:600,letterSpacing:1,textTransform:"uppercase" }}>🤖 Discord Bot</span>
          </div>
          <h1 style={{ fontSize:"clamp(40px,6vw,62px)",fontWeight:900,letterSpacing:"-2px",lineHeight:1.1,margin:"0 0 14px" }}>
            <span style={{ background:"linear-gradient(135deg,#fff,#a5b4fc)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent" }}>GIAN</span>
            <span style={{ background:"linear-gradient(135deg,#6366f1,#8b5cf6)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent" }}> BOT</span>
          </h1>
          <p style={{ fontSize:16,color:"#9ca3af",lineHeight:1.7,marginBottom:28 }}>
            Moćan Discord bot za upravljanje serverom — zaštita, igre, ekonomija, welcome sistem i još mnogo toga.
          </p>
          <a
            href="https://discord.com/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=8&scope=bot+applications.commands"
            target="_blank" rel="noopener noreferrer"
            style={{ display:"inline-flex",alignItems:"center",gap:8,padding:"13px 26px",borderRadius:12,background:"linear-gradient(135deg,#5865F2,#7c3aed)",color:"#fff",fontWeight:700,fontSize:15,textDecoration:"none",boxShadow:"0 0 28px rgba(88,101,242,0.45)" }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 00-.031-.03z"/></svg>
            Dodaj na server
          </a>
        </div>
      </section>

      {/* ── GAMES SECTION ── */}
      <section style={{ position:"relative",zIndex:1,maxWidth:1060,margin:"0 auto",padding:"0 40px 60px" }}>
        <div style={{ textAlign:"center",marginBottom:36 }}>
          <h2 style={{ fontSize:32,fontWeight:900,margin:"0 0 10px" }}>🎮 Igraj direktno ovdje</h2>
          <p style={{ color:"#6b7280",fontSize:15,margin:0 }}>Bez registracije, bez prijave — samo kreiraj sobu i pozovi prijatelje!</p>
        </div>

        <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))",gap:20 }}>
          {/* UNO Card */}
          <div style={{ borderRadius:20,overflow:"hidden",border:"1px solid rgba(239,68,68,0.25)",background:"rgba(239,68,68,0.05)",transition:"all .2s",cursor:"pointer" }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.transform="translateY(-6px)"; (e.currentTarget as HTMLDivElement).style.boxShadow="0 20px 60px rgba(239,68,68,0.3)"; (e.currentTarget as HTMLDivElement).style.borderColor="rgba(239,68,68,0.5)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.transform=""; (e.currentTarget as HTMLDivElement).style.boxShadow=""; (e.currentTarget as HTMLDivElement).style.borderColor="rgba(239,68,68,0.25)"; }}
          >
            <div style={{ background:"linear-gradient(135deg,#ef4444,#dc2626)",padding:"28px 24px",display:"flex",alignItems:"center",gap:16 }}>
              <span style={{ fontSize:48 }}>🃏</span>
              <div>
                <h3 style={{ fontSize:26,fontWeight:900,margin:"0 0 4px" }}>UNO</h3>
                <span style={{ fontSize:12,background:"rgba(0,0,0,0.25)",borderRadius:20,padding:"3px 10px",fontWeight:600 }}>2–10 igrača</span>
              </div>
            </div>
            <div style={{ padding:"20px 24px 24px" }}>
              <p style={{ color:"#9ca3af",fontSize:13,lineHeight:1.6,marginBottom:16 }}>Klasična karta igra. Baci sve karte prije ostalih! Specijalne karte (Skip, +2, Wild, +4) mijenjaju tok igre.</p>
              <div style={{ display:"flex",gap:6,flexWrap:"wrap",marginBottom:18 }}>
                {["Skip ⊘","Reverse ↺","+2 Draw","Wild 🌈","+4 Draw"].map(t => (
                  <span key={t} style={{ fontSize:11,padding:"3px 8px",borderRadius:6,background:"rgba(239,68,68,0.15)",color:"#fca5a5",fontWeight:600 }}>{t}</span>
                ))}
              </div>
              <button onClick={() => setActiveGame("uno")}
                style={{ width:"100%",padding:"13px",borderRadius:12,background:"linear-gradient(135deg,#ef4444,#dc2626)",color:"#fff",fontWeight:800,fontSize:15,border:"none",cursor:"pointer",boxShadow:"0 0 20px rgba(239,68,68,0.4)" }}>
                🃏 Igraj UNO
              </button>
            </div>
          </div>

          {/* Ludo Card */}
          <div style={{ borderRadius:20,overflow:"hidden",border:"1px solid rgba(34,197,94,0.25)",background:"rgba(34,197,94,0.05)",transition:"all .2s",cursor:"pointer" }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.transform="translateY(-6px)"; (e.currentTarget as HTMLDivElement).style.boxShadow="0 20px 60px rgba(34,197,94,0.3)"; (e.currentTarget as HTMLDivElement).style.borderColor="rgba(34,197,94,0.5)"; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.transform=""; (e.currentTarget as HTMLDivElement).style.boxShadow=""; (e.currentTarget as HTMLDivElement).style.borderColor="rgba(34,197,94,0.25)"; }}
          >
            <div style={{ background:"linear-gradient(135deg,#22c55e,#16a34a)",padding:"28px 24px",display:"flex",alignItems:"center",gap:16 }}>
              <span style={{ fontSize:48 }}>🎲</span>
              <div>
                <h3 style={{ fontSize:26,fontWeight:900,margin:"0 0 4px" }}>Čovječe ne ljuti se</h3>
                <span style={{ fontSize:12,background:"rgba(0,0,0,0.25)",borderRadius:20,padding:"3px 10px",fontWeight:600 }}>2–4 igrača</span>
              </div>
            </div>
            <div style={{ padding:"20px 24px 24px" }}>
              <p style={{ color:"#9ca3af",fontSize:13,lineHeight:1.6,marginBottom:16 }}>Nasadi sve 4 figure u kući! Baci 6 da izvučeš figuru, srušavaj protivnike i budi prvi koji završi.</p>
              <div style={{ display:"flex",gap:6,flexWrap:"wrap",marginBottom:18 }}>
                {["Kockica 🎲","4 boje","Rušanje 💥","Sigurna polja","Baci ponovo (6)"].map(t => (
                  <span key={t} style={{ fontSize:11,padding:"3px 8px",borderRadius:6,background:"rgba(34,197,94,0.15)",color:"#86efac",fontWeight:600 }}>{t}</span>
                ))}
              </div>
              <button onClick={() => setActiveGame("ludo")}
                style={{ width:"100%",padding:"13px",borderRadius:12,background:"linear-gradient(135deg,#22c55e,#16a34a)",color:"#fff",fontWeight:800,fontSize:15,border:"none",cursor:"pointer",boxShadow:"0 0 20px rgba(34,197,94,0.4)" }}>
                🎲 Igraj Čovječe
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ position:"relative",zIndex:1,padding:"0 40px 72px",maxWidth:1060,margin:"0 auto" }}>
        <h2 style={{ textAlign:"center",fontSize:26,fontWeight:800,marginBottom:28,color:"#e5e7eb" }}>Šta sve <span style={{ color:"#6366f1" }}>GIAN BOT</span> nudi?</h2>
        <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(260px,1fr))",gap:14 }}>
          {[
            { icon:"🛡️",title:"Zaštita servera",desc:"Anti-spam, anti-raid, auto-mod, filteri" },
            { icon:"📋",title:"Embeds editor",desc:"Prilagodi poruke bota vizuelnim editorom" },
            { icon:"⭐",title:"Zvjezdana tabla",desc:"Sistem glasanja i nagrađivanja" },
            { icon:"👥",title:"Upravljanje članovima",desc:"Banovi, kickovi, upozorenja, logovi" },
            { icon:"🎵",title:"Welcome sistem",desc:"Personalizovane welcome kartice i DM" },
            { icon:"💰",title:"Ekonomija",desc:"Dnevne nagrade, kockanje, posao, krađa" },
          ].map((f,i) => (
            <div key={i} style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:14,padding:"20px",transition:"all .2s" }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background="rgba(99,102,241,0.07)"; (e.currentTarget as HTMLDivElement).style.borderColor="rgba(99,102,241,0.25)"; }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background="rgba(255,255,255,0.03)"; (e.currentTarget as HTMLDivElement).style.borderColor="rgba(255,255,255,0.07)"; }}
            >
              <div style={{ fontSize:26,marginBottom:10 }}>{f.icon}</div>
              <h3 style={{ fontSize:14,fontWeight:700,marginBottom:6,color:"#e5e7eb" }}>{f.title}</h3>
              <p style={{ fontSize:12,color:"#6b7280",lineHeight:1.5,margin:0 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer style={{ position:"relative",zIndex:1,textAlign:"center",padding:"20px 24px",borderTop:"1px solid rgba(255,255,255,0.05)",color:"#374151",fontSize:13 }}>
        GIAN BOT © 2025 — Napravljen s ❤️ za Discord zajednicu
      </footer>

      {/* Login Modal */}
      {showLogin && (
        <div style={{ position:"fixed",inset:0,background:"rgba(0,0,0,0.8)",zIndex:100,display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(8px)" }}
          onClick={e => { if(e.target===e.currentTarget) setShowLogin(false); }}>
          <div style={{ width:"100%",maxWidth:380,margin:20,background:"rgba(10,11,15,0.98)",border:"1px solid rgba(99,102,241,0.3)",borderRadius:20,padding:36,boxShadow:"0 0 80px rgba(99,102,241,0.2)" }}>
            <div style={{ textAlign:"center",marginBottom:28 }}>
              <img src={`${BASE}/gian-bot-penguin.png`} alt="GIAN" style={{ width:54,height:54,borderRadius:"50%",marginBottom:12 }} />
              <h2 style={{ fontSize:20,fontWeight:800,margin:"0 0 6px" }}>Prijava u panel</h2>
              <p style={{ color:"#6b7280",fontSize:13,margin:0 }}>Unesi lozinku za pristup</p>
            </div>
            <form onSubmit={handleLogin}>
              <label style={{ display:"block",fontSize:11,fontWeight:700,color:"#6366f1",letterSpacing:1,textTransform:"uppercase",marginBottom:8 }}>Lozinka</label>
              <input type="password" value={loginPwd} onChange={e=>setLoginPwd(e.target.value)} placeholder="••••••••••••" autoFocus required
                style={{ width:"100%",padding:"12px 16px",borderRadius:10,background:"rgba(255,255,255,0.04)",border:loginErr?"1px solid rgba(239,68,68,0.5)":"1px solid rgba(99,102,241,0.2)",color:"#fff",fontSize:14,outline:"none",boxSizing:"border-box" }} />
              {loginErr && <p style={{ color:"#f87171",fontSize:12,marginTop:8 }}>✖ {loginErr}</p>}
              <button type="submit" disabled={loginLoading||!loginPwd}
                style={{ width:"100%",marginTop:16,padding:12,borderRadius:10,background:loginLoading||!loginPwd?"rgba(99,102,241,0.3)":"linear-gradient(135deg,#6366f1,#8b5cf6)",color:"#fff",fontWeight:700,fontSize:14,border:"none",cursor:loginLoading||!loginPwd?"not-allowed":"pointer" }}>
                {loginLoading?"Provjera...":"Pristupi panelu"}
              </button>
            </form>
            <button onClick={() => setShowLogin(false)} style={{ display:"block",margin:"14px auto 0",background:"none",border:"none",color:"#6b7280",fontSize:13,cursor:"pointer" }}>Zatvori</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── UNO Panel (inline) ───────────────────────────────────────────────────────
function UnoPanel({ onBack }: { onBack: () => void }) {
  const [screen, setScreen] = useState<"home"|"lobby"|"game">("home");
  const [myName, setMyName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const [playerId, setPlayerId] = useState("");
  const [room, setRoom] = useState<UnoRoom|null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [colorPicker, setColorPicker] = useState<number|null>(null);
  const [polling, setPolling] = useState(false);

  const fetchRoom = useCallback(async (code: string, pid: string) => {
    try {
      const r = await fetch(`${API}/api/play/uno/${code}?playerId=${pid}`);
      if (r.ok) { const d = await r.json(); setRoom(d); if(d.state!=="waiting") setScreen("game"); }
    } catch {}
  }, []);

  useEffect(() => {
    if (!roomCode||!playerId||!polling) return;
    const iv = setInterval(()=>fetchRoom(roomCode,playerId),1500);
    return ()=>clearInterval(iv);
  }, [roomCode,playerId,polling,fetchRoom]);

  async function createRoom() {
    if(!myName.trim()) return setError("Unesi ime");
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/api/play/uno`,{method:"POST",headers:{"Content-Type":"application/json"}});
      const {code} = await r.json();
      const jr = await fetch(`${API}/api/play/uno/${code}/join`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:myName.trim()})});
      const jd = await jr.json();
      if(!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId);
      await fetchRoom(code,jd.playerId);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Greška"); } finally { setLoading(false); }
  }

  async function joinRoom() {
    if(!myName.trim()||!joinCode.trim()) return setError("Unesi ime i kod");
    setLoading(true); setError("");
    try {
      const code = joinCode.trim().toUpperCase();
      const jr = await fetch(`${API}/api/play/uno/${code}/join`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:myName.trim()})});
      const jd = await jr.json();
      if(!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId);
      await fetchRoom(code,jd.playerId);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Soba ne postoji"); } finally { setLoading(false); }
  }

  async function startGame() {
    await fetch(`${API}/api/play/uno/${roomCode}/start`,{method:"POST"});
    await fetchRoom(roomCode,playerId);
  }

  async function action(payload: object) {
    setError("");
    const r = await fetch(`${API}/api/play/uno/${roomCode}/action`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({playerId,...payload})});
    const d = await r.json();
    if(!r.ok) setError(d.error);
    await fetchRoom(roomCode,playerId);
  }

  function playCard(idx: number, card: UnoCard) {
    if(card.value==="wild"||card.value==="wild4") { setColorPicker(idx); return; }
    action({action:"play",cardIdx:idx});
  }

  const myPlayer = room?.players.find(p=>p.id===playerId);
  const myHand = myPlayer?.hand ?? [];
  const isMyTurn = room?.players[room.currentIdx]?.id === playerId;
  const topCard = room?.topCard;
  const canPlay = (card: UnoCard): boolean => {
    if(!room||!isMyTurn) return false;
    if(room.drawStack>0) return card.value==="draw2"||card.value==="wild4";
    if(card.value==="wild"||card.value==="wild4") return true;
    const eff = room.pendingColor ?? topCard?.color ?? "red";
    return card.color===eff || card.value===topCard?.value;
  };

  const wrapper = (children: React.ReactNode) => (
    <div style={{ background:"#06070d",minHeight:"100vh",fontFamily:"'Segoe UI',system-ui,sans-serif",color:"#fff" }}>
      <div style={{ position:"fixed",inset:0,pointerEvents:"none" }}>
        <div style={{ position:"absolute",top:"-100px",left:"-100px",width:"500px",height:"500px",borderRadius:"50%",background:"radial-gradient(circle,rgba(239,68,68,0.08) 0%,transparent 70%)",filter:"blur(70px)" }} />
        <div style={{ position:"absolute",bottom:0,right:0,width:"400px",height:"400px",borderRadius:"50%",background:"radial-gradient(circle,rgba(99,102,241,0.07) 0%,transparent 70%)",filter:"blur(60px)" }} />
      </div>
      <nav style={{ position:"relative",zIndex:10,display:"flex",alignItems:"center",gap:12,padding:"14px 28px",borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
        <button onClick={onBack} style={{ background:"none",border:"none",color:"#9ca3af",cursor:"pointer",fontSize:20,padding:"4px 8px",borderRadius:8,display:"flex",alignItems:"center" }}>←</button>
        <span style={{ fontSize:18,fontWeight:800 }}>🃏 <span style={{ color:"#ef4444" }}>UNO</span></span>
        {roomCode && <span style={{ marginLeft:"auto",fontSize:12,color:"#6b7280" }}>Soba: <b style={{ color:"#a5b4fc",letterSpacing:2 }}>{roomCode}</b></span>}
      </nav>
      <div style={{ position:"relative",zIndex:1 }}>{children}</div>
    </div>
  );

  if (screen==="home") return wrapper(
    <div style={{ maxWidth:440,margin:"0 auto",padding:"50px 20px" }}>
      <div style={{ textAlign:"center",marginBottom:32 }}>
        <div style={{ fontSize:64,marginBottom:12 }}>🃏</div>
        <h1 style={{ fontSize:38,fontWeight:900,margin:"0 0 6px",background:"linear-gradient(135deg,#ef4444,#f97316)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent" }}>UNO</h1>
        <p style={{ color:"#6b7280",fontSize:14 }}>Multiplayer • 2–10 igrača</p>
      </div>
      <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:16,padding:26 }}>
        <label style={{ display:"block",fontSize:11,fontWeight:700,color:"#ef4444",letterSpacing:1,textTransform:"uppercase",marginBottom:8 }}>Tvoje ime</label>
        <input value={myName} onChange={e=>setMyName(e.target.value)} placeholder="Npr. Marko" maxLength={20}
          style={{ width:"100%",padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"#fff",fontSize:14,outline:"none",boxSizing:"border-box",marginBottom:14 }} />
        <button onClick={createRoom} disabled={loading||!myName.trim()}
          style={{ width:"100%",padding:12,borderRadius:10,background:loading?"rgba(239,68,68,0.3)":"linear-gradient(135deg,#ef4444,#dc2626)",color:"#fff",fontWeight:700,fontSize:14,border:"none",cursor:"pointer",marginBottom:10 }}>
          {loading?"Kreiranje...":"🃏 Kreiraj novu sobu"}
        </button>
        <div style={{ display:"flex",gap:8 }}>
          <input value={joinCode} onChange={e=>setJoinCode(e.target.value.toUpperCase())} placeholder="Kod sobe (npr. A3F2C1)" maxLength={6}
            style={{ flex:1,padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"#fff",fontSize:14,outline:"none",letterSpacing:2 }} />
          <button onClick={joinRoom} disabled={loading||!myName.trim()||!joinCode.trim()}
            style={{ padding:"11px 18px",borderRadius:10,background:"rgba(255,255,255,0.08)",border:"1px solid rgba(255,255,255,0.15)",color:"#fff",fontWeight:600,fontSize:14,cursor:"pointer" }}>
            Pridruži se
          </button>
        </div>
        {error && <p style={{ color:"#f87171",fontSize:12,marginTop:10 }}>⚠ {error}</p>}
      </div>
    </div>
  );

  if (screen==="lobby") return wrapper(
    <div style={{ maxWidth:440,margin:"0 auto",padding:"50px 20px" }}>
      <div style={{ textAlign:"center",marginBottom:28 }}>
        <h2 style={{ fontSize:22,fontWeight:800,marginBottom:8 }}>Čekaonica</h2>
        <div style={{ display:"inline-block",background:"rgba(239,68,68,0.15)",border:"1px solid rgba(239,68,68,0.4)",borderRadius:10,padding:"8px 20px",letterSpacing:4,fontSize:22,fontWeight:900,color:"#fca5a5" }}>{roomCode}</div>
        <p style={{ color:"#6b7280",fontSize:12,marginTop:6 }}>Podijeli kod prijateljima</p>
      </div>
      <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:16,padding:18,marginBottom:16 }}>
        <p style={{ fontSize:11,fontWeight:700,color:"#6b7280",letterSpacing:1,textTransform:"uppercase",marginBottom:10 }}>Igrači ({room?.players.length??0}/10)</p>
        {room?.players.map((p,i)=>(
          <div key={p.id} style={{ display:"flex",alignItems:"center",gap:10,padding:"7px 0",borderBottom:i<(room.players.length-1)?"1px solid rgba(255,255,255,0.05)":"none" }}>
            <div style={{ width:30,height:30,borderRadius:"50%",background:"linear-gradient(135deg,#ef4444,#dc2626)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,fontWeight:700 }}>{p.name[0].toUpperCase()}</div>
            <span style={{ fontSize:14,fontWeight:600 }}>{p.name}</span>
            {p.id===playerId && <span style={{ fontSize:11,color:"#a5b4fc",marginLeft:"auto" }}>Ti</span>}
            {i===0 && <span style={{ fontSize:11,color:"#f59e0b",marginLeft:"auto" }}>👑</span>}
          </div>
        ))}
      </div>
      {room?.players[0]?.id===playerId ? (
        <button onClick={startGame} disabled={(room?.players.length??0)<2}
          style={{ width:"100%",padding:13,borderRadius:12,background:(room?.players.length??0)<2?"rgba(239,68,68,0.3)":"linear-gradient(135deg,#ef4444,#dc2626)",color:"#fff",fontWeight:700,fontSize:15,border:"none",cursor:(room?.players.length??0)<2?"not-allowed":"pointer" }}>
          {(room?.players.length??0)<2?"Čekanje na igrače...":"▶ Pokreni igru"}
        </button>
      ) : <p style={{ textAlign:"center",color:"#6b7280",fontSize:13 }}>Čekaj da domaćin pokrene igru...</p>}
    </div>
  );

  // Game screen
  const currentName = room?.players[room.currentIdx]?.name??"";
  return wrapper(
    <>
      {room?.state==="finished" && (
        <div style={{ position:"fixed",inset:0,background:"rgba(0,0,0,0.85)",zIndex:50,display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(12px)" }}>
          <div style={{ textAlign:"center",background:"rgba(10,11,15,0.95)",border:"1px solid rgba(239,68,68,0.4)",borderRadius:24,padding:48,maxWidth:340 }}>
            <div style={{ fontSize:72,marginBottom:16 }}>🏆</div>
            <h2 style={{ fontSize:30,fontWeight:900,marginBottom:8 }}>{room.winner} pobijedio/la!</h2>
            <div style={{ display:"flex",gap:10,justifyContent:"center",marginTop:24 }}>
              <button onClick={()=>{setScreen("home");setRoom(null);setPolling(false);}}
                style={{ padding:"11px 24px",borderRadius:10,background:"linear-gradient(135deg,#ef4444,#dc2626)",color:"#fff",fontWeight:700,border:"none",cursor:"pointer" }}>Nova igra</button>
              <button onClick={onBack}
                style={{ padding:"11px 24px",borderRadius:10,background:"rgba(255,255,255,0.08)",border:"1px solid rgba(255,255,255,0.15)",color:"#fff",fontWeight:700,cursor:"pointer" }}>Nazad</button>
            </div>
          </div>
        </div>
      )}
      {colorPicker!==null && (
        <div style={{ position:"fixed",inset:0,background:"rgba(0,0,0,0.7)",zIndex:50,display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(8px)" }}>
          <div style={{ background:"rgba(10,11,15,0.98)",border:"1px solid rgba(255,255,255,0.1)",borderRadius:20,padding:32,textAlign:"center" }}>
            <h3 style={{ marginBottom:20,fontSize:18,fontWeight:700 }}>Odaberi boju</h3>
            <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:12 }}>
              {(["red","green","blue","yellow"] as const).map(c=>(
                <button key={c} onClick={()=>{action({action:"play",cardIdx:colorPicker,chosenColor:c});setColorPicker(null);}}
                  style={{ padding:"15px 26px",borderRadius:12,background:UNO_COLOR_BG[c],color:"#fff",fontWeight:700,border:"none",cursor:"pointer",fontSize:14,boxShadow:`0 0 14px ${UNO_COLOR_HEX[c]}66` }}>
                  {UNO_COLOR_LABEL[c]}
                </button>
              ))}
            </div>
            <button onClick={()=>setColorPicker(null)} style={{ marginTop:14,background:"none",border:"none",color:"#6b7280",cursor:"pointer",fontSize:12 }}>Odustani</button>
          </div>
        </div>
      )}
      <div style={{ padding:"14px 18px",maxWidth:780,margin:"0 auto" }}>
        {/* Status */}
        <div style={{ display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:14,flexWrap:"wrap",gap:8 }}>
          <div style={{ display:"flex",gap:6,flexWrap:"wrap" }}>
            {room?.players.map((p,i)=>(
              <div key={p.id} style={{ padding:"3px 10px",borderRadius:20,background:i===room.currentIdx?"rgba(239,68,68,0.28)":"rgba(255,255,255,0.05)",border:i===room.currentIdx?"1px solid rgba(239,68,68,0.55)":"1px solid rgba(255,255,255,0.07)",fontSize:12,fontWeight:i===room.currentIdx?700:400 }}>
                {i===room.currentIdx?"▶ ":""}{p.name}{p.id===playerId?" (Ti)":""} <span style={{ color:"#6b7280" }}>[{p.handCount}]</span>
                {p.saidUno && <span style={{ color:"#ef4444",marginLeft:4 }}>UNO!</span>}
              </div>
            ))}
          </div>
          <span style={{ fontSize:11,color:"#6b7280" }}>{room?.lastAction}</span>
        </div>
        <div style={{ display:"flex",gap:16,flexWrap:"wrap",alignItems:"flex-start" }}>
          {/* Center */}
          <div style={{ flex:"0 0 auto",background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:14,padding:20,minWidth:180,display:"flex",flexDirection:"column",alignItems:"center",gap:14 }}>
            <div>
              <p style={{ fontSize:10,color:"#6b7280",marginBottom:7,textAlign:"center",textTransform:"uppercase",letterSpacing:1 }}>Gornja karta</p>
              {topCard && <UnoCardView card={topCard} />}
              {room?.pendingColor && <p style={{ fontSize:11,color:UNO_COLOR_HEX[room.pendingColor],textAlign:"center",marginTop:5,fontWeight:700 }}>Boja: {UNO_COLOR_LABEL[room.pendingColor]}</p>}
              {(room?.drawStack??0)>0 && <p style={{ fontSize:12,color:"#f97316",textAlign:"center",marginTop:3,fontWeight:700 }}>Naredni vuče +{room!.drawStack}</p>}
            </div>
            {isMyTurn ? (
              <div style={{ display:"flex",flexDirection:"column",gap:8,width:"100%" }}>
                <button onClick={()=>action({action:"draw"})}
                  style={{ width:"100%",padding:"9px",borderRadius:9,background:"rgba(99,102,241,0.2)",border:"1px solid rgba(99,102,241,0.4)",color:"#a5b4fc",fontWeight:700,fontSize:12,cursor:"pointer" }}>
                  {(room?.drawStack??0)>0?`Uzmi +${room!.drawStack}`:"Vuci kartu"}
                </button>
                {myPlayer && myPlayer.handCount<=2 && (
                  <button onClick={()=>action({action:"uno"})}
                    style={{ width:"100%",padding:"9px",borderRadius:9,background:"rgba(239,68,68,0.2)",border:"1px solid rgba(239,68,68,0.4)",color:"#fca5a5",fontWeight:700,fontSize:12,cursor:"pointer" }}>
                    🗣 UNO!
                  </button>
                )}
              </div>
            ) : <p style={{ fontSize:12,color:"#6b7280",textAlign:"center" }}>Red: <b style={{ color:"#fff" }}>{currentName}</b></p>}
          </div>
          {/* Hand */}
          <div style={{ flex:1,minWidth:0 }}>
            <p style={{ fontSize:11,color:"#6b7280",marginBottom:10,textTransform:"uppercase",letterSpacing:1 }}>Tvoje karte ({myHand.length})</p>
            <div style={{ display:"flex",flexWrap:"wrap",gap:7 }}>
              {myHand.map((card,i)=><UnoCardView key={card.id} card={card} playable={canPlay(card)} onClick={()=>playCard(i,card)} />)}
            </div>
            {error && <p style={{ color:"#f87171",fontSize:12,marginTop:10 }}>⚠ {error}</p>}
          </div>
        </div>
      </div>
    </>
  );
}

// ─── LUDO Panel (inline) ──────────────────────────────────────────────────────
function LudoPanel({ onBack }: { onBack: () => void }) {
  const [screen, setScreen] = useState<"home"|"lobby"|"game">("home");
  const [myName, setMyName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const [playerId, setPlayerId] = useState("");
  const [myColor, setMyColor] = useState<LudoColor>("red");
  const [room, setRoom] = useState<LudoRoom|null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);

  const fetchRoom = useCallback(async (code: string) => {
    try {
      const r = await fetch(`${API}/api/play/ludo/${code}`);
      if(r.ok) { const d = await r.json(); setRoom(d); if(d.state!=="waiting") setScreen("game"); }
    } catch {}
  }, []);

  useEffect(() => {
    if(!roomCode||!polling) return;
    const iv = setInterval(()=>fetchRoom(roomCode),1500);
    return ()=>clearInterval(iv);
  }, [roomCode,polling,fetchRoom]);

  async function createRoom() {
    if(!myName.trim()) return setError("Unesi ime");
    setLoading(true); setError("");
    try {
      const r = await fetch(`${API}/api/play/ludo`,{method:"POST",headers:{"Content-Type":"application/json"}});
      const {code} = await r.json();
      const jr = await fetch(`${API}/api/play/ludo/${code}/join`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:myName.trim()})});
      const jd = await jr.json();
      if(!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId); setMyColor(jd.color);
      await fetchRoom(code);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Greška"); } finally { setLoading(false); }
  }

  async function joinRoom() {
    if(!myName.trim()||!joinCode.trim()) return setError("Unesi ime i kod");
    setLoading(true); setError("");
    try {
      const code = joinCode.trim().toUpperCase();
      const jr = await fetch(`${API}/api/play/ludo/${code}/join`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:myName.trim()})});
      const jd = await jr.json();
      if(!jr.ok) return setError(jd.error);
      setRoomCode(code); setPlayerId(jd.playerId); setMyColor(jd.color);
      await fetchRoom(code);
      setScreen("lobby"); setPolling(true);
    } catch { setError("Soba ne postoji"); } finally { setLoading(false); }
  }

  async function startGame() {
    await fetch(`${API}/api/play/ludo/${roomCode}/start`,{method:"POST"});
    await fetchRoom(roomCode);
  }

  async function doAction(payload: object) {
    setError("");
    const r = await fetch(`${API}/api/play/ludo/${roomCode}/action`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({playerId,...payload})});
    const d = await r.json();
    if(!r.ok) setError(d.error);
    await fetchRoom(roomCode);
  }

  const isMyTurn = room?.players[room.currentIdx]?.id===playerId;
  const currentName = room?.players[room?.currentIdx??0]?.name??"";

  // Simple Ludo board path helper
  function pathToGrid(abs: number): [number,number] {
    const path: [number,number][] = [];
    for(let c=1;c<=5;c++) path.push([10,c]);
    path.push([10,6]);
    for(let r=9;r>=6;r--) path.push([r,6]);
    path.push([5,6]);
    for(let r=4;r>=1;r--) path.push([r,6]);
    path.push([0,6]);
    for(let c=5;c>=1;c--) path.push([0,c]);
    path.push([0,4]);
    for(let r=1;r<=4;r++) path.push([r,4]);
    path.push([5,4]);
    for(let r=6;r<=9;r++) path.push([r,4]);
    path.push([10,4]);
    for(let c=3;c>=1;c--) path.push([10,c]);
    while(path.length<52) path.push([5,5]);
    return path[abs%52]??[5,5];
  }

  const homePos: Record<LudoColor,[number,number][]> = {
    red:[[1,1],[1,2],[2,1],[2,2]],
    blue:[[1,8],[1,9],[2,8],[2,9]],
    green:[[8,8],[8,9],[9,8],[9,9]],
    yellow:[[8,1],[8,2],[9,1],[9,2]],
  };
  const startOff: Record<LudoColor,number> = {red:0,blue:13,green:26,yellow:39};
  const SAFE = [0,8,13,21,26,34,39,47];
  const cs = 40; // cell size
  const boardPx = 11*cs;

  const wrapper = (children: React.ReactNode) => (
    <div style={{ background:"#06070d",minHeight:"100vh",fontFamily:"'Segoe UI',system-ui,sans-serif",color:"#fff" }}>
      <div style={{ position:"fixed",inset:0,pointerEvents:"none" }}>
        <div style={{ position:"absolute",top:"-100px",left:"-100px",width:"500px",height:"500px",borderRadius:"50%",background:"radial-gradient(circle,rgba(34,197,94,0.07) 0%,transparent 70%)",filter:"blur(60px)" }} />
      </div>
      <nav style={{ position:"relative",zIndex:10,display:"flex",alignItems:"center",gap:12,padding:"14px 28px",borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
        <button onClick={onBack} style={{ background:"none",border:"none",color:"#9ca3af",cursor:"pointer",fontSize:20,padding:"4px 8px",borderRadius:8 }}>←</button>
        <span style={{ fontSize:18,fontWeight:800 }}>🎲 <span style={{ color:"#22c55e" }}>Čovječe ne ljuti se</span></span>
        {roomCode && <span style={{ marginLeft:"auto",fontSize:12,color:"#6b7280" }}>Soba: <b style={{ color:"#a5b4fc",letterSpacing:2 }}>{roomCode}</b></span>}
      </nav>
      <div style={{ position:"relative",zIndex:1 }}>{children}</div>
    </div>
  );

  if(screen==="home") return wrapper(
    <div style={{ maxWidth:440,margin:"0 auto",padding:"50px 20px" }}>
      <div style={{ textAlign:"center",marginBottom:32 }}>
        <div style={{ fontSize:64,marginBottom:12 }}>🎲</div>
        <h1 style={{ fontSize:34,fontWeight:900,margin:"0 0 6px",background:"linear-gradient(135deg,#22c55e,#10b981)",WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent" }}>Čovječe ne ljuti se</h1>
        <p style={{ color:"#6b7280",fontSize:14 }}>Multiplayer • 2–4 igrača</p>
      </div>
      <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:16,padding:26 }}>
        <label style={{ display:"block",fontSize:11,fontWeight:700,color:"#22c55e",letterSpacing:1,textTransform:"uppercase",marginBottom:8 }}>Tvoje ime</label>
        <input value={myName} onChange={e=>setMyName(e.target.value)} placeholder="Npr. Ana" maxLength={20}
          style={{ width:"100%",padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"#fff",fontSize:14,outline:"none",boxSizing:"border-box",marginBottom:14 }} />
        <button onClick={createRoom} disabled={loading||!myName.trim()}
          style={{ width:"100%",padding:12,borderRadius:10,background:loading?"rgba(34,197,94,0.3)":"linear-gradient(135deg,#22c55e,#16a34a)",color:"#fff",fontWeight:700,fontSize:14,border:"none",cursor:"pointer",marginBottom:10 }}>
          {loading?"Kreiranje...":"🎲 Kreiraj novu sobu"}
        </button>
        <div style={{ display:"flex",gap:8 }}>
          <input value={joinCode} onChange={e=>setJoinCode(e.target.value.toUpperCase())} placeholder="Kod sobe" maxLength={6}
            style={{ flex:1,padding:"11px 14px",borderRadius:10,background:"rgba(255,255,255,0.05)",border:"1px solid rgba(255,255,255,0.1)",color:"#fff",fontSize:14,outline:"none",letterSpacing:2 }} />
          <button onClick={joinRoom} disabled={loading||!myName.trim()||!joinCode.trim()}
            style={{ padding:"11px 18px",borderRadius:10,background:"rgba(255,255,255,0.08)",border:"1px solid rgba(255,255,255,0.15)",color:"#fff",fontWeight:600,fontSize:14,cursor:"pointer" }}>
            Pridruži se
          </button>
        </div>
        {error && <p style={{ color:"#f87171",fontSize:12,marginTop:10 }}>⚠ {error}</p>}
      </div>
    </div>
  );

  if(screen==="lobby") return wrapper(
    <div style={{ maxWidth:440,margin:"0 auto",padding:"50px 20px" }}>
      <div style={{ textAlign:"center",marginBottom:26 }}>
        <h2 style={{ fontSize:22,fontWeight:800,marginBottom:8 }}>Čekaonica</h2>
        <div style={{ display:"inline-block",background:"rgba(34,197,94,0.15)",border:"1px solid rgba(34,197,94,0.4)",borderRadius:10,padding:"8px 20px",letterSpacing:4,fontSize:22,fontWeight:900,color:"#86efac" }}>{roomCode}</div>
        <p style={{ color:"#6b7280",fontSize:12,marginTop:6 }}>Podijeli kod prijateljima</p>
      </div>
      <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:16,padding:18,marginBottom:14 }}>
        <p style={{ fontSize:11,fontWeight:700,color:"#6b7280",textTransform:"uppercase",letterSpacing:1,marginBottom:10 }}>Igrači ({room?.players.length??0}/4)</p>
        {room?.players.map((p,i)=>(
          <div key={p.id} style={{ display:"flex",alignItems:"center",gap:10,padding:"7px 0",borderBottom:i<(room.players.length-1)?"1px solid rgba(255,255,255,0.05)":"none" }}>
            <div style={{ width:30,height:30,borderRadius:"50%",background:LUDO_COLOR_BG[p.color],display:"flex",alignItems:"center",justifyContent:"center",fontSize:13,fontWeight:700 }}>{p.name[0]}</div>
            <span style={{ fontSize:14,fontWeight:600 }}>{p.name}</span>
            <span style={{ fontSize:11,color:LUDO_COLOR[p.color],marginLeft:4 }}>({LUDO_LABEL[p.color]})</span>
            {p.id===playerId && <span style={{ fontSize:11,color:"#a5b4fc",marginLeft:"auto" }}>Ti</span>}
          </div>
        ))}
      </div>
      {room?.players[0]?.id===playerId ? (
        <button onClick={startGame} disabled={(room?.players.length??0)<2}
          style={{ width:"100%",padding:13,borderRadius:12,background:(room?.players.length??0)<2?"rgba(34,197,94,0.3)":"linear-gradient(135deg,#22c55e,#16a34a)",color:"#fff",fontWeight:700,fontSize:15,border:"none",cursor:(room?.players.length??0)<2?"not-allowed":"pointer" }}>
          {(room?.players.length??0)<2?"Čekanje na igrače...":"▶ Pokreni igru"}
        </button>
      ) : <p style={{ textAlign:"center",color:"#6b7280",fontSize:13 }}>Čekaj da domaćin pokrene igru...</p>}
    </div>
  );

  return wrapper(
    <>
      {room?.state==="finished" && (
        <div style={{ position:"fixed",inset:0,background:"rgba(0,0,0,0.85)",zIndex:50,display:"flex",alignItems:"center",justifyContent:"center",backdropFilter:"blur(12px)" }}>
          <div style={{ textAlign:"center",background:"rgba(10,11,15,0.95)",border:"1px solid rgba(34,197,94,0.4)",borderRadius:24,padding:48,maxWidth:340 }}>
            <div style={{ fontSize:72,marginBottom:16 }}>🏆</div>
            <h2 style={{ fontSize:30,fontWeight:900,marginBottom:8 }}>{room.winner} pobijedio/la!</h2>
            <div style={{ display:"flex",gap:10,justifyContent:"center",marginTop:24 }}>
              <button onClick={()=>{setScreen("home");setRoom(null);setPolling(false);}}
                style={{ padding:"11px 24px",borderRadius:10,background:"linear-gradient(135deg,#22c55e,#16a34a)",color:"#fff",fontWeight:700,border:"none",cursor:"pointer" }}>Nova igra</button>
              <button onClick={onBack}
                style={{ padding:"11px 24px",borderRadius:10,background:"rgba(255,255,255,0.08)",border:"1px solid rgba(255,255,255,0.15)",color:"#fff",fontWeight:700,cursor:"pointer" }}>Nazad</button>
            </div>
          </div>
        </div>
      )}
      <div style={{ display:"flex",gap:18,padding:"14px 18px",maxWidth:900,margin:"0 auto",flexWrap:"wrap",alignItems:"flex-start" }}>
        {/* Board */}
        <div style={{ flex:"0 0 auto",position:"relative" }}>
          <svg width={boardPx} height={boardPx} style={{ display:"block",borderRadius:10 }}>
            <rect width={boardPx} height={boardPx} fill="#0f1117" rx={8} />
            {([["red",0,0],["blue",0,6],["green",6,6],["yellow",6,0]] as [LudoColor,number,number][]).map(([c,row,col])=>(
              <rect key={c} x={col*cs+2} y={row*cs+2} width={cs*5-4} height={cs*5-4} fill={`${LUDO_COLOR[c]}1a`} stroke={LUDO_COLOR[c]} strokeWidth={1.5} rx={5} />
            ))}
            {Array.from({length:12},(_,i)=>(
              <g key={i}>
                <line x1={0} y1={i*cs} x2={boardPx} y2={i*cs} stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} />
                <line x1={i*cs} y1={0} x2={i*cs} y2={boardPx} stroke="rgba(255,255,255,0.05)" strokeWidth={0.5} />
              </g>
            ))}
            <polygon points={`${5*cs},${5*cs} ${6*cs},${5*cs} ${5.5*cs},${5.5*cs}`} fill="#ef4444" opacity={0.8} />
            <polygon points={`${5*cs},${6*cs} ${6*cs},${6*cs} ${5.5*cs},${5.5*cs}`} fill="#22c55e" opacity={0.8} />
            <polygon points={`${5*cs},${5*cs} ${5*cs},${6*cs} ${5.5*cs},${5.5*cs}`} fill="#eab308" opacity={0.8} />
            <polygon points={`${6*cs},${5*cs} ${6*cs},${6*cs} ${5.5*cs},${5.5*cs}`} fill="#3b82f6" opacity={0.8} />
            {SAFE.map(sq=>{ const [r,c]=pathToGrid(sq); return <rect key={sq} x={c*cs+4} y={r*cs+4} width={cs-8} height={cs-8} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={1} strokeDasharray="3" rx={3} />; })}
            {/* Home pieces */}
            {room?.players.map(p=>homePos[p.color].map(([hr,hc],i)=>{
              const piece=p.pieces[i];
              if(!piece.home) return null;
              const canMv = isMyTurn&&p.id===playerId&&piece.home&&(room?.diceRolled??false)&&room?.dice===6;
              return (
                <g key={`${p.id}-h${i}`} onClick={()=>canMv&&doAction({action:"move",pieceIdx:i})} style={{ cursor:canMv?"pointer":"default" }}>
                  <circle cx={hc*cs+cs/2} cy={hr*cs+cs/2} r={12} fill={LUDO_COLOR[p.color]} opacity={0.85} />
                  <circle cx={hc*cs+cs/2} cy={hr*cs+cs/2} r={7} fill="rgba(255,255,255,0.28)" />
                  <text x={hc*cs+cs/2} y={hr*cs+cs/2+4} textAnchor="middle" fontSize={9} fill="#fff" fontWeight={700}>{i+1}</text>
                  {canMv && <circle cx={hc*cs+cs/2} cy={hr*cs+cs/2} r={14} fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth={2} strokeDasharray="4" />}
                </g>
              );
            }))}
            {/* On-track pieces */}
            {room?.players.flatMap(p=>p.pieces.map((piece,i)=>{
              if(piece.home||piece.finished||piece.pos>=52) return null;
              const abs=(startOff[p.color]+piece.pos)%52;
              const [pr,pc]=pathToGrid(abs);
              const canMv=isMyTurn&&p.id===playerId&&(room?.diceRolled??false)&&!piece.home;
              return (
                <g key={`${p.id}-t${i}`} onClick={()=>canMv&&doAction({action:"move",pieceIdx:i})} style={{ cursor:canMv?"pointer":"default" }}>
                  <circle cx={pc*cs+cs/2} cy={pr*cs+cs/2} r={12} fill={LUDO_COLOR[p.color]} opacity={0.85} />
                  <circle cx={pc*cs+cs/2} cy={pr*cs+cs/2} r={7} fill="rgba(255,255,255,0.22)" />
                  <text x={pc*cs+cs/2} y={pr*cs+cs/2+4} textAnchor="middle" fontSize={9} fill="#fff" fontWeight={700}>{i+1}</text>
                  {canMv && <circle cx={pc*cs+cs/2} cy={pr*cs+cs/2} r={14} fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth={2} strokeDasharray="4" />}
                </g>
              );
            }))}
          </svg>
          {/* Player labels */}
          {room?.players.map((p,i)=>{
            const pos: React.CSSProperties[] = [
              {position:"absolute",top:2,left:2},{position:"absolute",top:2,right:2},
              {position:"absolute",bottom:2,right:2},{position:"absolute",bottom:2,left:2}
            ];
            return (
              <div key={p.id} style={{ ...pos[i],background:`${LUDO_COLOR[p.color]}33`,border:`1px solid ${LUDO_COLOR[p.color]}66`,borderRadius:5,padding:"2px 7px",fontSize:10,fontWeight:700,color:LUDO_COLOR[p.color] }}>
                {p.name}{p.id===playerId?" (Ti)":""}
              </div>
            );
          })}
        </div>

        {/* Controls */}
        <div style={{ flex:1,minWidth:200 }}>
          <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:13,padding:14,marginBottom:12 }}>
            <p style={{ fontSize:11,color:"#6b7280",marginBottom:5 }}>Zadnja akcija</p>
            <p style={{ fontSize:13,color:"#e5e7eb",fontWeight:600 }}>{room?.lastAction}</p>
          </div>
          <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:13,padding:18,marginBottom:12,textAlign:"center" }}>
            {room?.dice && <div style={{ fontSize:52,marginBottom:10 }}>{["⚀","⚁","⚂","⚃","⚄","⚅"][room.dice-1]}</div>}
            {!room?.diceRolled && isMyTurn ? (
              <button onClick={()=>doAction({action:"roll"})}
                style={{ width:"100%",padding:"11px",borderRadius:10,background:"linear-gradient(135deg,#22c55e,#16a34a)",color:"#fff",fontWeight:700,fontSize:13,border:"none",cursor:"pointer",boxShadow:"0 0 18px rgba(34,197,94,0.35)" }}>
                🎲 Baci kockicu
              </button>
            ) : !isMyTurn ? (
              <p style={{ fontSize:12,color:"#6b7280" }}>Red: <b style={{ color:"#fff" }}>{currentName}</b></p>
            ) : (
              <p style={{ fontSize:12,color:"#86efac",fontWeight:600 }}>Klikni na figuru da je pomjeriš</p>
            )}
          </div>
          {error && <p style={{ color:"#f87171",fontSize:12,marginBottom:10 }}>⚠ {error}</p>}
          <div style={{ background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.07)",borderRadius:13,padding:14 }}>
            <p style={{ fontSize:10,fontWeight:700,color:"#6b7280",textTransform:"uppercase",letterSpacing:1,marginBottom:8 }}>Igrači</p>
            {room?.players.map((p,i)=>{
              const done=p.pieces.filter(pc=>pc.finished).length;
              return (
                <div key={p.id} style={{ display:"flex",alignItems:"center",gap:8,padding:"5px 0",borderBottom:i<(room.players.length-1)?"1px solid rgba(255,255,255,0.04)":"none" }}>
                  <div style={{ width:26,height:26,borderRadius:"50%",background:LUDO_COLOR_BG[p.color],display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,flexShrink:0 }}>{p.name[0]}</div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:12,fontWeight:i===room.currentIdx?700:500 }}>{p.name}{p.id===playerId?" (Ti)":""}</div>
                    <div style={{ fontSize:10,color:"#6b7280" }}>{done}/4 figura doma</div>
                  </div>
                  {i===room.currentIdx && <span style={{ fontSize:11,color:LUDO_COLOR[p.color],fontWeight:700 }}>▶</span>}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </>
  );
}
