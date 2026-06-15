import { useState, FormEvent } from "react";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const err = await login(password);
    setLoading(false);
    if (err) setError(err);
  }

  return (
    <div
      className="fixed inset-0 flex items-center justify-center"
      style={{ background: "#080910", fontFamily: "'Segoe UI', system-ui, sans-serif" }}
    >
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div style={{ position: "absolute", top: "-120px", left: "-80px", width: "500px", height: "500px", borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.14) 0%, transparent 70%)", filter: "blur(60px)" }} />
        <div style={{ position: "absolute", bottom: "-100px", right: "-60px", width: "400px", height: "400px", borderRadius: "50%", background: "radial-gradient(circle, rgba(139,92,246,0.12) 0%, transparent 70%)", filter: "blur(60px)" }} />
        <div style={{ position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(99,102,241,0.10) 1px, transparent 1px)", backgroundSize: "32px 32px", opacity: 0.4 }} />
      </div>

      <div className="relative z-10 w-full max-w-sm mx-4">
        {/* Card */}
        <div
          className="rounded-2xl p-8"
          style={{
            background: "rgba(10,11,15,0.95)",
            border: "1px solid rgba(99,102,241,0.2)",
            boxShadow: "0 0 80px rgba(99,102,241,0.12), 0 24px 48px rgba(0,0,0,0.6)",
          }}
        >
          {/* Logo */}
          <div className="flex flex-col items-center mb-8">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center font-black text-2xl mb-4 relative"
              style={{
                background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                boxShadow: "0 0 32px rgba(99,102,241,0.6), 0 0 80px rgba(99,102,241,0.2)",
              }}
            >
              G
              <div className="absolute inset-0 rounded-2xl" style={{ background: "linear-gradient(135deg, rgba(255,255,255,0.15), transparent)" }} />
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">GIANNI Panel</h1>
            <p className="text-sm mt-1" style={{ color: "#6b7280" }}>Unesi lozinku za pristup</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: "#6366f1" }}>
                Lozinka panela
              </label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••••••"
                autoFocus
                required
                className="w-full px-4 py-3 rounded-xl text-sm text-white outline-none transition-all"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: error ? "1px solid rgba(239,68,68,0.5)" : "1px solid rgba(99,102,241,0.2)",
                  caretColor: "#6366f1",
                }}
                onFocus={e => { e.currentTarget.style.border = "1px solid rgba(99,102,241,0.5)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.1)"; }}
                onBlur={e => { e.currentTarget.style.border = error ? "1px solid rgba(239,68,68,0.5)" : "1px solid rgba(99,102,241,0.2)"; e.currentTarget.style.boxShadow = "none"; }}
              />
              {error && (
                <p className="mt-2 text-xs font-medium" style={{ color: "#f87171" }}>
                  ✖ {error}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !password}
              className="w-full py-3 rounded-xl text-sm font-bold text-white transition-all relative overflow-hidden"
              style={{
                background: loading || !password
                  ? "rgba(99,102,241,0.3)"
                  : "linear-gradient(135deg, #6366f1, #8b5cf6)",
                cursor: loading || !password ? "not-allowed" : "pointer",
                boxShadow: loading || !password ? "none" : "0 0 24px rgba(99,102,241,0.4)",
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Provjera...
                </span>
              ) : "Pristupi panelu"}
            </button>
          </form>

          {/* Footer note */}
          <p className="text-center text-xs mt-6" style={{ color: "#374151" }}>
            🔒 Ova stranica je zaštićena — samo ovlašteni korisnici mogu pristupiti
          </p>
        </div>
      </div>
    </div>
  );
}
