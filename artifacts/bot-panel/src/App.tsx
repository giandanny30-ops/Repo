import { Switch, Route, Router as WouterRouter, useLocation } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppLayout } from "@/components/layout/AppLayout";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Commands from "@/pages/Commands";
import Embeds from "@/pages/Embeds";
import Members from "@/pages/Members";
import Permissions from "@/pages/Permissions";
import Protection from "@/pages/Protection";
import Games from "@/pages/Games";
import Settings from "@/pages/Settings";
import ServerPage from "@/pages/ServerPage";
import Icons from "@/pages/Icons";
import Emojis from "@/pages/Emojis";
import NotFound from "@/pages/not-found";
import Landing from "@/pages/Landing";
import GamesHub from "@/pages/GamesHub";
import UnoGame from "@/pages/UnoGame";
import LudoGame from "@/pages/LudoGame";

const queryClient = new QueryClient();

function PanelRouter() {
  return (
    <AppLayout>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/commands" component={Commands} />
        <Route path="/embeds" component={Embeds} />
        <Route path="/members" component={Members} />
        <Route path="/server" component={ServerPage} />
        <Route path="/permissions" component={Permissions} />
        <Route path="/protection" component={Protection} />
        <Route path="/games" component={Games} />
        <Route path="/icons" component={Icons} />
        <Route path="/emojis" component={Emojis} />
        <Route path="/settings" component={Settings} />
        <Route component={NotFound} />
      </Switch>
    </AppLayout>
  );
}

function AuthGate() {
  const { isAuthenticated, isLoading } = useAuth();
  const [location] = useLocation();

  // Public routes — accessible without auth
  if (location === "/play" || location.startsWith("/play/")) {
    return (
      <Switch>
        <Route path="/play" component={GamesHub} />
        <Route path="/play/uno" component={UnoGame} />
        <Route path="/play/ludo" component={LudoGame} />
      </Switch>
    );
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: "#080910" }}>
        <div className="flex flex-col items-center gap-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center font-black text-lg"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)", boxShadow: "0 0 24px rgba(99,102,241,0.5)" }}
          >
            G
          </div>
          <div className="flex gap-1">
            {[0, 1, 2].map(i => (
              <div key={i} className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: "#6366f1", animationDelay: `${i * 0.15}s` }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return <Landing />;
  return <PanelRouter />;
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <AuthGate />
          </WouterRouter>
        </AuthProvider>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
