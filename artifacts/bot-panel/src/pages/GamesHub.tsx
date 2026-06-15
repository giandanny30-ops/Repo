import { useLocation } from "wouter";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

const GAMES = [
  {
    id: "uno",
    icon: "🃏",
    title: "UNO",
    desc: "Klasična karta igra. Baci sve karte prije ostalih. Specijalne karte mijenjaju tok igre!",
    players: "2–10 igrača",
    color: "#ef4444",
    grad: "linear-gradient(135deg,#ef4444,#dc2626)",
    glow: "rgba(239,68,68,0.4)",
    rules: ["Igraj kartu koja odgovara boji ili broju gornje karte","Skip preskače red, Reverse mijenja smjer","Draw Two (+2) sljedeći vuče 2 karte","Wild bira novu boju, Wild Draw Four (+4) vuče 4"],
    path: "/play/uno",
  },
  {
    id: "ludo",
    icon: "🎲",
    title: "Čovječe ne ljuti se",
    desc: "Nasadi sve 4 figure u kući. Srušavaj protivnike i budi prvi koji završi!",
    players: "2–4 igrača",
    color: "#22c55e",
    grad: "linear-gradient(135deg,#22c55e,#16a34a)",
    glow: "rgba(34,197,94,0.4)",
    rules: ["Baci 6 da izvučeš figuru iz baze","Pomjeri figuru za broj na kockici","Sruši protivnikovu figuru — idu nazad kući","Dovedi svih 4 figura do centra da pobijediš"],
    path: "/play/ludo",
  },
];

export default function GamesHub() {
  const [, navigate] = useLocation();

  return (
    <div style={{ minHeight: "100vh", background: "#06070d", color: "#fff", fontFamily: "'Segoe UI',system-ui,sans-serif" }}>
      {/* Background */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none" }}>
        <div style={{ position: "absolute", top: "-200px", left: "-100px", width: "700px", height: "700px", borderRadius: "50%", background: "radial-gradient(circle,rgba(99,102,241,0.10) 0%,transparent 70%)", filter: "blur(80px)" }} />
        <div style={{ position: "absolute", bottom: 0, right: "-100px", width: "500px", height: "500px", borderRadius: "50%", background: "radial-gradient(circle,rgba(139,92,246,0.08) 0%,transparent 70%)", filter: "blur(80px)" }} />
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle,rgba(99,102,241,0.06) 1px,transparent 1px)", backgroundSize: "36px 36px", opacity: 0.6 }} />
      </div>

      {/* Nav */}
      <nav style={{ position: "relative", zIndex: 10, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 40px", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <button onClick={() => navigate("/")} style={{ display: "flex", alignItems: "center", gap: 10, background: "none", border: "none", color: "#fff", cursor: "pointer" }}>
          <img src={`${BASE}/gian-bot-penguin.png`} alt="GIAN" style={{ width: 32, height: 32, borderRadius: "50%", objectFit: "cover" }} />
          <span style={{ fontWeight: 800, fontSize: 16 }}><span style={{ color: "#6366f1" }}>GIAN</span> BOT</span>
        </button>
        <span style={{ fontSize: 13, color: "#6b7280" }}>🎮 Igre</span>
      </nav>

      {/* Hero */}
      <div style={{ position: "relative", zIndex: 1, textAlign: "center", padding: "60px 24px 40px" }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>🎮</div>
        <h1 style={{ fontSize: "clamp(32px,5vw,52px)", fontWeight: 900, letterSpacing: "-1px", margin: "0 0 12px", background: "linear-gradient(135deg,#fff,#a5b4fc)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Multiplayer Igre
        </h1>
        <p style={{ color: "#6b7280", fontSize: 16, maxWidth: 480, margin: "0 auto" }}>
          Igraj s prijateljima direktno u browseru. Podijeli kod sobe i krenite!
        </p>
      </div>

      {/* Game cards */}
      <div style={{ position: "relative", zIndex: 1, maxWidth: 880, margin: "0 auto", padding: "0 24px 80px", display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(360px,1fr))", gap: 24 }}>
        {GAMES.map(game => (
          <div key={game.id} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 20, overflow: "hidden", transition: "all .25s", cursor: "pointer" }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.transform = "translateY(-6px)"; (e.currentTarget as HTMLDivElement).style.borderColor = `${game.color}55`; (e.currentTarget as HTMLDivElement).style.boxShadow = `0 20px 60px ${game.glow}`; }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.transform = ""; (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.08)"; (e.currentTarget as HTMLDivElement).style.boxShadow = ""; }}
          >
            {/* Card header */}
            <div style={{ background: game.grad, padding: "32px 28px", display: "flex", alignItems: "center", gap: 16, position: "relative", overflow: "hidden" }}>
              <div style={{ position: "absolute", top: "-30px", right: "-30px", width: 140, height: 140, borderRadius: "50%", background: "rgba(255,255,255,0.1)", filter: "blur(20px)" }} />
              <div style={{ fontSize: 52, flexShrink: 0 }}>{game.icon}</div>
              <div>
                <h2 style={{ fontSize: 28, fontWeight: 900, margin: "0 0 4px", textShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>{game.title}</h2>
                <span style={{ fontSize: 12, background: "rgba(0,0,0,0.25)", borderRadius: 20, padding: "3px 10px", fontWeight: 600 }}>{game.players}</span>
              </div>
            </div>

            {/* Card body */}
            <div style={{ padding: "24px 28px" }}>
              <p style={{ color: "#9ca3af", fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>{game.desc}</p>

              <div style={{ marginBottom: 24 }}>
                <p style={{ fontSize: 11, fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>Pravila</p>
                {game.rules.map((r, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
                    <span style={{ color: game.color, fontSize: 13, flexShrink: 0 }}>▸</span>
                    <span style={{ fontSize: 13, color: "#d1d5db", lineHeight: 1.5 }}>{r}</span>
                  </div>
                ))}
              </div>

              <button onClick={() => navigate(game.path)}
                style={{ width: "100%", padding: "14px", borderRadius: 12, background: game.grad, color: "#fff", fontWeight: 800, fontSize: 15, border: "none", cursor: "pointer", boxShadow: `0 0 24px ${game.glow}`, transition: "all .2s", letterSpacing: "0.5px" }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.transform = "scale(1.02)"; }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = ""; }}
              >
                {game.icon} Igraj {game.title}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{ position: "relative", zIndex: 1, textAlign: "center", padding: "0 24px 40px", color: "#374151", fontSize: 13, borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: 24 }}>
        GIAN BOT • Multiplayer igre za Discord zajednicu
      </div>
    </div>
  );
}
