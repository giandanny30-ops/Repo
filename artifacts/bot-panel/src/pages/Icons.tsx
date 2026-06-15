import { useState, useMemo } from "react";
import {
  Search, Download,
  Gamepad2, DollarSign, Layers, Bird, Heart,
  Briefcase, Gift, Swords, Star, HelpCircle, Globe, BookOpen,
  Flame, AlertTriangle, Target, Users, ShoppingCart, Sparkles,
  Trophy, TrendingUp, Activity, ClipboardList, Crown, Wallet,
  CheckCircle, Music, Save, Dices, Shield, Zap, MessageCircle,
  User, ArrowLeftRight, Bell, Settings, LogOut, RefreshCw,
  Eye, Trash2, Info, Lock, Check, ChevronDown, ChevronRight,
  Hash, AtSign, Image, Link, Bold, Italic, List, Code,
  HeartHandshake, Diamond, ShoppingBag, BarChart2, Tag, Archive,
  Wrench, UserPlus, UserMinus, Rocket, Ticket, Mic, Ban,
  VolumeX, Volume2, Clock, ListChecks, Grid3x3, MessageSquare,
  Hand, Play, Pause, Square, Database, FileText, PencilLine,
  UserCheck, ShieldCheck, ShieldX, ScrollText, LayoutTemplate,
  LayoutDashboard, Terminal, Globe2, ShieldAlert, Settings2,
  Plus, X, Unlock, BarChart, Home, Mail, Phone, MapPin,
  Calendar, Camera, Film, Headphones, Cpu, Monitor, Smartphone,
  Wifi, Battery, Zap as ZapIcon, Sun, Moon, Cloud, Wind,
  ThumbsUp, ThumbsDown, Share2, Bookmark, Flag, Tag as TagIcon,
  Filter, SortAsc, SortDesc, RotateCcw, RotateCw, ZoomIn, ZoomOut,
  Maximize, Minimize, ExternalLink, ChevronUp, ChevronLeft,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Move, Crosshair,
  type LucideIcon,
} from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

interface IconEntry {
  name: string;
  component: LucideIcon;
  tags: string[];
}

const ALL_ICONS: IconEntry[] = [
  { name: "Gamepad2",       component: Gamepad2,       tags: ["igra","game","controller"] },
  { name: "DollarSign",     component: DollarSign,     tags: ["novac","money","coin","ekonomija"] },
  { name: "Layers",         component: Layers,         tags: ["slojevi","stack","blackjack"] },
  { name: "Bird",           component: Bird,           tags: ["ptica","zivotinja","animal"] },
  { name: "Heart",          component: Heart,          tags: ["srce","love","like","social"] },
  { name: "Briefcase",      component: Briefcase,      tags: ["torba","posao","work","job"] },
  { name: "Gift",           component: Gift,           tags: ["poklon","gift","daily","present"] },
  { name: "Swords",         component: Swords,         tags: ["mac","battle","kradi","fight"] },
  { name: "Star",           component: Star,           tags: ["zvijezda","star","slots","favorite"] },
  { name: "HelpCircle",     component: HelpCircle,     tags: ["pomoc","help","question","kviz"] },
  { name: "Globe",          component: Globe,          tags: ["globus","world","geografija","earth"] },
  { name: "BookOpen",       component: BookOpen,       tags: ["knjiga","book","kaladont","animals"] },
  { name: "Flame",          component: Flame,          tags: ["vatra","fire","hot","toplo"] },
  { name: "AlertTriangle",  component: AlertTriangle,  tags: ["upozorenje","warning","amogus","alert"] },
  { name: "Target",         component: Target,         tags: ["cilj","hunt","aim","target"] },
  { name: "Users",          component: Users,          tags: ["korisnici","users","zoo","members"] },
  { name: "ShoppingCart",   component: ShoppingCart,   tags: ["korpa","shop","sell","buy"] },
  { name: "Sparkles",       component: Sparkles,       tags: ["sjaj","sparkle","magic","pray"] },
  { name: "Trophy",         component: Trophy,         tags: ["trofej","poker","winner","prize"] },
  { name: "TrendingUp",     component: TrendingUp,     tags: ["rast","rank","stats","trending"] },
  { name: "Activity",       component: Activity,       tags: ["aktivnost","activity","stats","pulse"] },
  { name: "ClipboardList",  component: ClipboardList,  tags: ["lista","quests","tasks","list"] },
  { name: "Crown",          component: Crown,          tags: ["kruna","crown","admin","royal"] },
  { name: "Wallet",         component: Wallet,         tags: ["novcanik","wallet","baki","balance"] },
  { name: "CheckCircle",    component: CheckCircle,    tags: ["check","potvrda","confirm","ok"] },
  { name: "Music",          component: Music,          tags: ["muzika","music","vers","song"] },
  { name: "Save",           component: Save,           tags: ["spremi","save","disk","store"] },
  { name: "Dices",          component: Dices,          tags: ["kocka","dice","gambling","random"] },
  { name: "Search",         component: Search,         tags: ["pretraga","search","find","look"] },
  { name: "X",              component: X,              tags: ["zatvori","close","remove","delete"] },
  { name: "Plus",           component: Plus,           tags: ["dodaj","add","create","new"] },
  { name: "Shield",         component: Shield,         tags: ["stit","shield","protect","security"] },
  { name: "ShieldCheck",    component: ShieldCheck,    tags: ["stit","shield","verified","secure"] },
  { name: "ShieldAlert",    component: ShieldAlert,    tags: ["stit","shield","danger","alert"] },
  { name: "ShieldX",        component: ShieldX,        tags: ["stit","shield","blocked","denied"] },
  { name: "Zap",            component: ZapIcon,        tags: ["munja","zap","fast","electric"] },
  { name: "MessageCircle",  component: MessageCircle,  tags: ["poruka","message","chat","comment"] },
  { name: "MessageSquare",  component: MessageSquare,  tags: ["poruka","message","chat","bubble"] },
  { name: "User",           component: User,           tags: ["korisnik","user","profile","person"] },
  { name: "UserPlus",       component: UserPlus,       tags: ["korisnik","user","add","join"] },
  { name: "UserMinus",      component: UserMinus,      tags: ["korisnik","user","remove","kick"] },
  { name: "UserCheck",      component: UserCheck,      tags: ["korisnik","user","verified","approve"] },
  { name: "ArrowLeftRight", component: ArrowLeftRight, tags: ["strijela","arrow","transfer","swap"] },
  { name: "Bell",           component: Bell,           tags: ["zvono","bell","notification","alert"] },
  { name: "Settings",       component: Settings,       tags: ["podesavanja","settings","gear","config"] },
  { name: "Settings2",      component: Settings2,      tags: ["podesavanja","settings","gear","config"] },
  { name: "LogOut",         component: LogOut,         tags: ["odjava","logout","exit","leave"] },
  { name: "RefreshCw",      component: RefreshCw,      tags: ["refresh","reload","sync","update"] },
  { name: "RotateCcw",      component: RotateCcw,      tags: ["reset","undo","rotate","back"] },
  { name: "RotateCw",       component: RotateCw,       tags: ["redo","rotate","forward","redo"] },
  { name: "Eye",            component: Eye,            tags: ["oko","eye","view","preview","show"] },
  { name: "Trash2",         component: Trash2,         tags: ["brisanje","delete","trash","remove"] },
  { name: "Info",           component: Info,           tags: ["info","information","about","help"] },
  { name: "Lock",           component: Lock,           tags: ["zakljucano","lock","private","secure"] },
  { name: "Unlock",         component: Unlock,         tags: ["otkljucano","unlock","public","open"] },
  { name: "Check",          component: Check,          tags: ["check","potvrda","done","complete"] },
  { name: "ChevronDown",    component: ChevronDown,    tags: ["strijela","arrow","down","dropdown"] },
  { name: "ChevronUp",      component: ChevronUp,      tags: ["strijela","arrow","up","collapse"] },
  { name: "ChevronRight",   component: ChevronRight,   tags: ["strijela","arrow","right","next"] },
  { name: "ChevronLeft",    component: ChevronLeft,    tags: ["strijela","arrow","left","back"] },
  { name: "ArrowUp",        component: ArrowUp,        tags: ["gore","up","increase","asc"] },
  { name: "ArrowDown",      component: ArrowDown,      tags: ["dole","down","decrease","desc"] },
  { name: "ArrowLeft",      component: ArrowLeft,      tags: ["lijevo","left","back","prev"] },
  { name: "ArrowRight",     component: ArrowRight,     tags: ["desno","right","next","forward"] },
  { name: "Hash",           component: Hash,           tags: ["kanal","channel","hashtag","number"] },
  { name: "AtSign",         component: AtSign,         tags: ["mention","at","email","tag"] },
  { name: "Image",          component: Image,          tags: ["slika","image","photo","picture"] },
  { name: "Link",           component: Link,           tags: ["link","url","connect","chain"] },
  { name: "Bold",           component: Bold,           tags: ["podebljano","bold","format","text"] },
  { name: "Italic",         component: Italic,         tags: ["kurziv","italic","format","text"] },
  { name: "List",           component: List,           tags: ["lista","list","items","bullet"] },
  { name: "ListChecks",     component: ListChecks,     tags: ["lista","checklist","tasks","todo"] },
  { name: "Code",           component: Code,           tags: ["kod","code","dev","programming"] },
  { name: "HeartHandshake", component: HeartHandshake, tags: ["ljubav","handshake","partner","deal"] },
  { name: "Diamond",        component: Diamond,        tags: ["dijamant","diamond","premium","gem"] },
  { name: "ShoppingBag",    component: ShoppingBag,    tags: ["korpa","bag","shop","purchase"] },
  { name: "BarChart2",      component: BarChart2,      tags: ["grafikon","chart","stats","data"] },
  { name: "BarChart",       component: BarChart,       tags: ["grafikon","chart","stats","data"] },
  { name: "Tag",            component: TagIcon,        tags: ["tag","label","category","mark"] },
  { name: "Archive",        component: Archive,        tags: ["arhiva","archive","store","box"] },
  { name: "Wrench",         component: Wrench,         tags: ["alat","wrench","tool","fix","repair"] },
  { name: "Rocket",         component: Rocket,         tags: ["raketa","rocket","launch","fast","boost"] },
  { name: "Ticket",         component: Ticket,         tags: ["tiket","ticket","event","entry"] },
  { name: "Mic",            component: Mic,            tags: ["mikrofon","mic","voice","audio"] },
  { name: "Ban",            component: Ban,            tags: ["ban","zabrana","block","stop","not"] },
  { name: "VolumeX",        component: VolumeX,        tags: ["mute","volume","muted","silent"] },
  { name: "Volume2",        component: Volume2,        tags: ["zvuk","volume","sound","audio"] },
  { name: "Clock",          component: Clock,          tags: ["sat","clock","time","timer","cooldown"] },
  { name: "Grid3x3",        component: Grid3x3,        tags: ["grid","mreza","layout","table"] },
  { name: "Hand",           component: Hand,           tags: ["ruka","hand","stop","wait"] },
  { name: "Play",           component: Play,           tags: ["igraj","play","start","run","go"] },
  { name: "Pause",          component: Pause,          tags: ["pauza","pause","stop","hold"] },
  { name: "Square",         component: Square,         tags: ["kvadrat","square","stop","box"] },
  { name: "Database",       component: Database,       tags: ["baza","database","data","storage"] },
  { name: "FileText",       component: FileText,       tags: ["fajl","file","document","text","log"] },
  { name: "ScrollText",     component: ScrollText,     tags: ["scroll","tekst","log","document"] },
  { name: "PencilLine",     component: PencilLine,     tags: ["olovka","edit","pencil","write"] },
  { name: "LayoutDashboard",component: LayoutDashboard,tags: ["dashboard","layout","home","overview"] },
  { name: "LayoutTemplate", component: LayoutTemplate, tags: ["template","layout","design","embed"] },
  { name: "Terminal",       component: Terminal,       tags: ["terminal","cmd","command","code"] },
  { name: "Globe2",         component: Globe2,         tags: ["globus","world","global","internet"] },
  { name: "Move",           component: Move,           tags: ["pomjeri","move","drag","arrows"] },
  { name: "Crosshair",      component: Crosshair,      tags: ["nisan","crosshair","aim","target"] },
  { name: "ZoomIn",         component: ZoomIn,         tags: ["zoom","uvecaj","enlarge","bigger"] },
  { name: "ZoomOut",        component: ZoomOut,        tags: ["zoom","smanji","shrink","smaller"] },
  { name: "Maximize",       component: Maximize,       tags: ["maximiziraj","fullscreen","expand"] },
  { name: "Minimize",       component: Minimize,       tags: ["minimiziraj","minimize","collapse"] },
  { name: "ExternalLink",   component: ExternalLink,   tags: ["vanjski","external","link","open"] },
  { name: "SortAsc",        component: SortAsc,        tags: ["sortiraj","sort","asc","order"] },
  { name: "SortDesc",       component: SortDesc,       tags: ["sortiraj","sort","desc","order"] },
  { name: "Filter",         component: Filter,         tags: ["filter","filtriraj","refine"] },
  { name: "Share2",         component: Share2,         tags: ["dijeli","share","send","social"] },
  { name: "Bookmark",       component: Bookmark,       tags: ["oznaka","bookmark","save","favorite"] },
  { name: "Flag",           component: Flag,           tags: ["zastava","flag","report","mark"] },
  { name: "ThumbsUp",       component: ThumbsUp,       tags: ["lajk","thumbs","like","approve"] },
  { name: "ThumbsDown",     component: ThumbsDown,     tags: ["dislajk","thumbs","dislike","reject"] },
  { name: "Home",           component: Home,           tags: ["dom","home","start","main"] },
  { name: "Mail",           component: Mail,           tags: ["mail","email","poruka","message"] },
  { name: "Phone",          component: Phone,          tags: ["telefon","phone","call","contact"] },
  { name: "MapPin",         component: MapPin,         tags: ["lokacija","map","pin","location"] },
  { name: "Calendar",       component: Calendar,       tags: ["kalendar","calendar","date","event"] },
  { name: "Camera",         component: Camera,         tags: ["kamera","camera","photo","picture"] },
  { name: "Film",           component: Film,           tags: ["film","video","movie","media"] },
  { name: "Headphones",     component: Headphones,     tags: ["slusalice","headphones","audio","music"] },
  { name: "Cpu",            component: Cpu,            tags: ["cpu","processor","tech","hardware"] },
  { name: "Monitor",        component: Monitor,        tags: ["monitor","screen","display","desktop"] },
  { name: "Smartphone",     component: Smartphone,     tags: ["mobilni","phone","smartphone","mobile"] },
  { name: "Wifi",           component: Wifi,           tags: ["wifi","internet","network","connect"] },
  { name: "Battery",        component: Battery,        tags: ["baterija","battery","power","charge"] },
  { name: "Sun",            component: Sun,            tags: ["sunce","sun","light","day","bright"] },
  { name: "Moon",           component: Moon,           tags: ["mjesec","moon","night","dark"] },
  { name: "Cloud",          component: Cloud,          tags: ["oblak","cloud","storage","server"] },
  { name: "Wind",           component: Wind,           tags: ["vjetar","wind","air","speed"] },
];

const ACCENT_COLORS = [
  "#6366f1","#8b5cf6","#a855f7","#ec4899","#ef4444",
  "#f97316","#f59e0b","#22c55e","#14b8a6","#3b82f6",
  "#06b6d4","#84cc16","#e11d48","#0ea5e9","#10b981",
];

function getColor(idx: number) {
  return ACCENT_COLORS[idx % ACCENT_COLORS.length];
}

export default function Icons() {
  const [query, setQuery] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) return ALL_ICONS;
    return ALL_ICONS.filter(i =>
      i.name.toLowerCase().includes(q) ||
      i.tags.some(t => t.includes(q))
    );
  }, [query]);

  function copyName(name: string) {
    navigator.clipboard.writeText(name).catch(() => {});
    setCopied(name);
    setTimeout(() => setCopied(null), 1500);
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "rgba(99,102,241,0.04)" }}>
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "rgba(99,102,241,0.18)", border: "1px solid rgba(99,102,241,0.3)", boxShadow: "0 0 16px rgba(99,102,241,0.15)" }}>
              <Sparkles className="w-6 h-6 text-[#a5b4fc]" />
            </div>
            <div>
              <h1 className="text-lg font-black text-white tracking-tight">Ikone</h1>
              <p className="text-[11px] mt-0.5" style={{ color: "#6b7280" }}>
                {ALL_ICONS.length} Lucide ikona dostupnih u panelu — klikni na ikonu da kopiraš naziv
              </p>
            </div>
          </div>
          <a
            href={`${BASE}/lucide-icons-panel.zip`}
            download="lucide-icons-panel.zip"
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
            style={{ background: "linear-gradient(135deg,#6366f1,#8b5cf6)", color: "white", boxShadow: "0 2px 12px rgba(99,102,241,0.3)", textDecoration: "none" }}
          >
            <Download className="w-4 h-4" />
            Preuzmi SVG zip
          </a>
        </div>

        {/* Search */}
        <div className="px-5 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "#4b5563" }} />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Pretraži ikone (npr. heart, novac, shield...)"
              className="w-full pl-9 pr-4 py-2 rounded-lg text-sm text-white outline-none transition-all"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#e2e8f0" }}
              onFocus={e => (e.target.style.borderColor = "rgba(99,102,241,0.5)")}
              onBlur={e => (e.target.style.borderColor = "rgba(255,255,255,0.08)")}
            />
            {query && (
              <button onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2">
                <X className="w-3.5 h-3.5" style={{ color: "#6b7280" }} />
              </button>
            )}
          </div>
          <p className="text-[11px] mt-2" style={{ color: "#374151" }}>
            {filtered.length} od {ALL_ICONS.length} ikona
          </p>
        </div>
      </div>

      {/* Icons Grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 xl:grid-cols-10 gap-2">
        {filtered.map((entry, idx) => {
          const Icon = entry.component;
          const color = getColor(idx);
          const isCopied = copied === entry.name;
          return (
            <button
              key={entry.name}
              onClick={() => copyName(entry.name)}
              title={entry.name}
              className="flex flex-col items-center gap-2 p-3 rounded-xl transition-all text-center group"
              style={{
                background: isCopied ? `${color}18` : "rgba(255,255,255,0.02)",
                border: `1px solid ${isCopied ? color + "55" : "rgba(255,255,255,0.05)"}`,
              }}
              onMouseEnter={e => {
                if (!isCopied) {
                  e.currentTarget.style.background = `${color}12`;
                  e.currentTarget.style.borderColor = `${color}44`;
                }
              }}
              onMouseLeave={e => {
                if (!isCopied) {
                  e.currentTarget.style.background = "rgba(255,255,255,0.02)";
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.05)";
                }
              }}
            >
              <div
                className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 transition-all"
                style={{
                  background: isCopied ? `${color}30` : `${color}18`,
                  border: `1px solid ${color}33`,
                  boxShadow: isCopied ? `0 0 12px ${color}55` : "none",
                }}
              >
                {isCopied
                  ? <Check className="w-4 h-4" style={{ color }} />
                  : <Icon className="w-4 h-4" style={{ color }} />
                }
              </div>
              <span
                className="text-[9px] font-medium leading-tight break-all"
                style={{ color: isCopied ? color : "#4b5563", maxWidth: "100%" }}
              >
                {isCopied ? "Kopirano!" : entry.name}
              </span>
            </button>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16" style={{ color: "#374151" }}>
          <HelpCircle className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">Nema rezultata za "<span style={{ color: "#6366f1" }}>{query}</span>"</p>
          <button onClick={() => setQuery("")} className="mt-2 text-xs underline" style={{ color: "#4b5563" }}>Poništi pretragu</button>
        </div>
      )}

      {/* Usage hint */}
      <div className="rounded-xl p-4" style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.15)" }}>
        <p className="text-xs" style={{ color: "#6b7280" }}>
          <span className="font-semibold text-[#a5b4fc]">Kako koristiti:</span>{" "}
          Klikni na ikonu da kopiraš naziv · Importuj u React sa{" "}
          <code className="px-1 py-0.5 rounded text-[10px]" style={{ background: "rgba(99,102,241,0.15)", color: "#c7d2fe" }}>
            import {"{ ImeName }"} from "lucide-react"
          </code>
          {" "}· Klikni "Preuzmi SVG zip" da dobiješ sve ikone kao SVG fajlove
        </p>
      </div>
    </div>
  );
}
