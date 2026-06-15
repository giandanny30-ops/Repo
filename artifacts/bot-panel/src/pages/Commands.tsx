import { useState, useMemo } from "react";
import { useListCommands } from "@workspace/api-client-react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, ShieldAlert, Zap, TerminalSquare } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const CATEGORY_COLORS: Record<string, string> = {
  "Opšte": "#6366f1",
  "Moderacija": "#ef4444",
  "Ekonomija": "#f59e0b",
  "XP i Aktivnost": "#22c55e",
  "Igre": "#3b82f6",
  "Ljubavne": "#ec4899",
  "Fun": "#f97316",
  "Poo": "#a78bfa",
  "Setup / Admin": "#14b8a6",
  "Ostalo": "#6b7280",
};

function getCategoryColor(name: string): string {
  return CATEGORY_COLORS[name] ?? "#6366f1";
}

export default function Commands() {
  const { data: categories, isLoading } = useListCommands();
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  const filteredData = useMemo(() => {
    if (!categories) return [];
    return categories
      .map(cat => ({
        ...cat,
        commands: cat.commands.filter(cmd => {
          const matchSearch = cmd.name.toLowerCase().includes(search.toLowerCase()) ||
            cmd.description.toLowerCase().includes(search.toLowerCase());
          const matchCat = categoryFilter === "all" || cat.name === categoryFilter;
          return matchSearch && matchCat;
        })
      }))
      .filter(cat => cat.commands.length > 0);
  }, [categories, search, categoryFilter]);

  const totalFiltered = filteredData.reduce((acc, cat) => acc + cat.commands.length, 0);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-56 rounded-lg" style={{ background: "rgba(255,255,255,0.06)" }} />
        <div className="flex gap-4">
          <Skeleton className="h-10 w-64" style={{ background: "rgba(255,255,255,0.04)" }} />
          <Skeleton className="h-10 w-48" style={{ background: "rgba(255,255,255,0.04)" }} />
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => <Skeleton key={i} className="h-32 w-full rounded-xl" style={{ background: "rgba(255,255,255,0.04)" }} />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" style={{ animation: "fadeSlideUp 0.35s ease both" }}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <TerminalSquare className="w-4 h-4" style={{ color: "#6366f1" }} />
            <span className="text-xs font-bold uppercase tracking-widest" style={{ color: "#3d3f5c" }}>Bot komande</span>
          </div>
          <h1 className="text-2xl font-black text-white">Command Browser</h1>
          {search || categoryFilter !== "all" ? (
            <p className="text-xs mt-1" style={{ color: "#374151" }}>{totalFiltered} rezultata</p>
          ) : (
            <p className="text-xs mt-1" style={{ color: "#374151" }}>{categories?.reduce((a, c) => a + c.commands.length, 0) ?? 0} ukupno komandi</p>
          )}
        </div>

        {/* Search & filter */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4" style={{ color: "#4b5563" }} />
            <Input
              placeholder="Pretraži komande..."
              className="pl-9 border-0 text-white placeholder:text-gray-600"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }}
              value={search}
              onChange={e => setSearch(e.target.value)}
              data-testid="input-search-commands"
            />
          </div>
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="w-[180px] border-0 text-white" style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.08)" }} data-testid="select-category">
              <SelectValue placeholder="Sve kategorije" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Sve kategorije</SelectItem>
              {categories?.map(c => (
                <SelectItem key={c.name} value={c.name}>
                  <span>{c.icon} {c.name}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Categories */}
      <div className="space-y-8">
        {filteredData.map((category) => {
          const color = getCategoryColor(category.name);
          return (
            <div key={category.name} className="space-y-3" data-testid={`category-${category.name}`}>
              {/* Category header */}
              <div className="flex items-center gap-3 pb-3 relative">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-base flex-shrink-0"
                  style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
                  {category.icon}
                </div>
                <div className="flex items-center gap-2 flex-1">
                  <h2 className="text-base font-black text-white">{category.name}</h2>
                  <div className="px-2 py-0.5 rounded-full text-[11px] font-bold"
                    style={{ background: `${color}15`, color, border: `1px solid ${color}25` }}>
                    {category.commands.length}
                  </div>
                </div>
                {/* Decorative line */}
                <div className="flex-1 h-px" style={{ background: `linear-gradient(90deg, ${color}30, transparent)` }} />
              </div>

              {/* Commands grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                {category.commands.map(cmd => (
                  <div
                    key={cmd.name}
                    className="rounded-xl p-4 relative overflow-hidden group"
                    style={{
                      background: "rgba(255,255,255,0.025)",
                      border: "1px solid rgba(255,255,255,0.07)",
                      transition: "border-color 0.2s, box-shadow 0.2s",
                    }}
                    onMouseEnter={e => {
                      const el = e.currentTarget as HTMLElement;
                      el.style.borderColor = `${color}35`;
                      el.style.boxShadow = `0 0 20px ${color}12`;
                    }}
                    onMouseLeave={e => {
                      const el = e.currentTarget as HTMLElement;
                      el.style.borderColor = "rgba(255,255,255,0.07)";
                      el.style.boxShadow = "none";
                    }}
                    data-testid={`command-${cmd.name}`}
                  >
                    {/* Color accent top line */}
                    <div className="absolute top-0 left-0 right-0 h-0.5 opacity-0 group-hover:opacity-100"
                      style={{ background: `linear-gradient(90deg, ${color}, transparent)`, transition: "opacity 0.2s" }} />

                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-black text-base" style={{ color }}>/{ cmd.name}</h3>
                      {cmd.adminOnly && (
                        <Badge className="h-5 text-[10px] uppercase font-bold flex items-center gap-1 border-0"
                          style={{ background: "rgba(239,68,68,0.15)", color: "#f87171" }}>
                          <ShieldAlert className="w-3 h-3" /><span>Admin</span>
                        </Badge>
                      )}
                    </div>

                    <p className="text-sm mb-3 line-clamp-2" style={{ color: "#9ca3af", minHeight: "40px" }}>{cmd.description}</p>

                    <div className="rounded-lg px-2.5 py-2 font-mono text-xs space-y-1"
                      style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)" }}>
                      <div className="flex items-center gap-2">
                        <span style={{ color: "#4b5563" }}>Usage:</span>
                        <span style={{ color: "#d1d5db" }}>{cmd.usage}</span>
                      </div>
                      {cmd.prefix && (
                        <div className="flex items-center gap-1" style={{ color: "#6366f1" }}>
                          <Zap className="w-3 h-3" /><span>Radi i sa .cmd</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {filteredData.length === 0 && (
          <div className="text-center py-16 rounded-xl" style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="text-4xl mb-3">🔍</div>
            <div className="text-white font-semibold mb-1">Nema rezultata</div>
            <div className="text-sm" style={{ color: "#4b5563" }}>Pokušaj drugačiji pojam za pretragu</div>
          </div>
        )}
      </div>
    </div>
  );
}
