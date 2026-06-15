import { useState, useMemo, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Search,
  RefreshCw,
  Smile,
  Upload,
  Trash2,
  Copy,
  Check,
} from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

interface Emoji {
  id: string;
  name: string;
  animated: boolean;
  _source: "app" | "guild";
}

function useEmojis() {
  return useQuery<Emoji[]>({
    queryKey: ["emojis"],
    queryFn: async () => {
      const r = await fetch(`${BASE}/api/discord/emojis`);
      if (!r.ok) throw new Error("Nije moguće učitati emoji");
      return r.json();
    },
    staleTime: 120_000,
    retry: 1,
  });
}

function emojiUrl(e: Emoji) {
  return `https://cdn.discordapp.com/emojis/${e.id}.${e.animated ? "gif" : "png"}?size=64&quality=lossless`;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={(ev) => {
        ev.stopPropagation();
        navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
      className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 p-1 rounded bg-[#111214]/80 hover:bg-[#5865F2]/80 transition-all"
      title="Kopiraj"
    >
      {copied ? (
        <Check className="w-3 h-3 text-green-400" />
      ) : (
        <Copy className="w-3 h-3 text-[#949BA4]" />
      )}
    </button>
  );
}

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
}

function UploadDialog({ open, onClose }: UploadDialogProps) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [preview, setPreview] = useState<string | null>(null);
  const [b64, setB64] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setName("");
    setPreview(null);
    setB64(null);
  };

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setPreview(result);
      setB64(result);
      if (!name) setName(file.name.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9_]/g, "_"));
    };
    reader.readAsDataURL(file);
  };

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!name.trim() || !b64) throw new Error("Nedostaje ime ili slika");
      const r = await fetch(`${BASE}/api/discord/emojis/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), image: b64 }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: r.statusText }));
        throw new Error(err.error ?? "Greška pri uploadu");
      }
      return r.json();
    },
    onSuccess: () => {
      toast({ title: "✅ Emoji dodan!", description: `<:${name}:...> je spreman.` });
      qc.invalidateQueries({ queryKey: ["emojis"] });
      reset();
      onClose();
    },
    onError: (e: Error) => {
      toast({ title: "❌ Greška", description: e.message, variant: "destructive" });
    },
  });

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) { reset(); onClose(); } }}>
      <DialogContent className="bg-[#2B2D31] border-[#1E1F22] text-[#DBDEE1] max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-4 h-4 text-[#F59E0B]" />
            Dodaj Application Emoji
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-1">
          <div className="space-y-1.5">
            <Label className="text-[#B5BAC1] text-xs uppercase tracking-wider">Ime emoji-ja</Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value.replace(/[^a-zA-Z0-9_]/g, "_"))}
              placeholder="npr. custom_emoji"
              className="bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1] focus:border-[#F59E0B]"
              maxLength={32}
            />
            <p className="text-[10px] text-[#949BA4]">Samo slova, brojevi i underscore (2–32 znakova)</p>
          </div>

          <div className="space-y-1.5">
            <Label className="text-[#B5BAC1] text-xs uppercase tracking-wider">Slika (PNG, JPG, GIF)</Label>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/gif,image/webp"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
            />
            <button
              onClick={() => fileRef.current?.click()}
              className="w-full border-2 border-dashed border-[#404249] rounded-lg py-6 flex flex-col items-center gap-2 hover:border-[#F59E0B]/60 transition-colors"
            >
              {preview ? (
                <img src={preview} alt="preview" className="h-14 w-14 object-contain rounded" />
              ) : (
                <>
                  <Upload className="w-6 h-6 text-[#949BA4]" />
                  <span className="text-sm text-[#949BA4]">Klikni za odabir slike</span>
                </>
              )}
            </button>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => { reset(); onClose(); }} className="border-[#404249] text-[#B5BAC1] hover:bg-[#35373C]">
            Odustani
          </Button>
          <Button
            onClick={() => uploadMutation.mutate()}
            disabled={uploadMutation.isPending || !b64 || name.length < 2}
            className="bg-[#F59E0B] hover:bg-[#D97706] text-black font-semibold"
          >
            {uploadMutation.isPending ? "Uploadujem..." : "Dodaj emoji"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface DeleteDialogProps {
  emoji: Emoji | null;
  onClose: () => void;
}

function DeleteDialog({ emoji, onClose }: DeleteDialogProps) {
  const { toast } = useToast();
  const qc = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${BASE}/api/discord/emojis/${emoji!.id}`, { method: "DELETE" });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: r.statusText }));
        throw new Error(err.error ?? "Greška");
      }
    },
    onSuccess: () => {
      toast({ title: "🗑️ Obrisano", description: `Emoji :${emoji?.name}: je uklonjen.` });
      qc.setQueryData<Emoji[]>(["emojis"], (old) => old?.filter((e) => e.id !== emoji!.id) ?? []);
      onClose();
    },
    onError: (e: Error) =>
      toast({ title: "❌ Greška", description: e.message, variant: "destructive" }),
  });

  if (!emoji) return null;
  return (
    <Dialog open={!!emoji} onOpenChange={() => onClose()}>
      <DialogContent className="bg-[#2B2D31] border-[#1E1F22] text-[#DBDEE1] max-w-xs">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-[#E74C3C]">
            <Trash2 className="w-4 h-4" />
            Obriši emoji
          </DialogTitle>
        </DialogHeader>
        <div className="py-2 flex items-center gap-3">
          <img src={emojiUrl(emoji)} alt={emoji.name} className="w-10 h-10 object-contain" />
          <div>
            <p className="font-medium">:{emoji.name}:</p>
            <p className="text-[#949BA4] text-xs">Ova akcija je trajna.</p>
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} className="border-[#404249] text-[#B5BAC1]">Odustani</Button>
          <Button
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
            className="bg-[#E74C3C] hover:bg-[#C0392B] text-white"
          >
            {deleteMutation.isPending ? "Brišem..." : "Obriši"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Emojis() {
  const { data: emojis, isLoading, refetch, isFetching } = useEmojis();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all" | "app" | "guild">("all");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [deleteEmoji, setDeleteEmoji] = useState<Emoji | null>(null);

  const filtered = useMemo(() => {
    if (!emojis) return [];
    return emojis.filter((e) => {
      if (filter !== "all" && e._source !== filter) return false;
      return !search || e.name.toLowerCase().includes(search.toLowerCase());
    });
  }, [emojis, search, filter]);

  const appCount = emojis?.filter((e) => e._source === "app").length ?? 0;
  const guildCount = emojis?.filter((e) => e._source === "guild").length ?? 0;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Smile className="w-6 h-6 text-[#F59E0B]" />
            Emoji
          </h1>
          <p className="text-sm text-[#949BA4] mt-0.5">
            {emojis
              ? `${filtered.length} prikazano · ${appCount} app · ${guildCount} guild`
              : "Učitavam..."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setUploadOpen(true)}
            size="sm"
            className="bg-[#F59E0B] hover:bg-[#D97706] text-black font-semibold"
          >
            <Upload className="w-3.5 h-3.5 mr-1.5" />
            Dodaj
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isFetching}
            className="border-[#404249] text-[#949BA4] hover:bg-[#35373C]"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isFetching ? "animate-spin" : ""}`} />
            Osvježi
          </Button>
        </div>
      </div>

      {/* Filters + Search */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#949BA4]" />
          <Input
            placeholder="Traži emoji po imenu..."
            className="pl-9 bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1] placeholder:text-[#949BA4] focus:border-[#F59E0B]"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex gap-1.5">
          {(["all", "app", "guild"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors border ${
                filter === f
                  ? "border-[#F59E0B] text-[#F59E0B] bg-[#F59E0B]/10"
                  : "border-[#404249] text-[#949BA4] hover:border-[#F59E0B]/60"
              }`}
            >
              {f === "all" ? "Svi" : f === "app" ? `App (${appCount})` : `Guild (${guildCount})`}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2">
          {Array.from({ length: 40 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg bg-[#2B2D31]" />
          ))}
        </div>
      ) : !emojis ? (
        <div className="text-center py-16 text-[#949BA4]">
          <Smile className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-lg">❌ Nije moguće učitati emoji</p>
          <p className="text-sm mt-1">Provjeri Discord token u Podešavanjima</p>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-[#949BA4]">
          <p>Nema emoji koji odgovaraju pretrazi</p>
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(88px,1fr))] gap-2">
          {filtered.map((e) => (
            <div
              key={e.id}
              className="group relative bg-[#2B2D31] hover:bg-[#35373C] rounded-lg p-2.5 flex flex-col items-center gap-2 transition-colors border border-transparent hover:border-[#404249]"
            >
              <img
                src={emojiUrl(e)}
                alt={e.name}
                className="w-10 h-10 object-contain"
                loading="lazy"
                onError={(ev) => { (ev.target as HTMLImageElement).style.opacity = "0.2"; }}
              />
              <p className="text-[10px] text-[#B5BAC1] text-center leading-tight break-all line-clamp-2">
                :{e.name}:
              </p>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
                  e._source === "app"
                    ? "bg-[#F59E0B]/15 text-[#F59E0B]"
                    : "bg-[#5865F2]/15 text-[#818CF8]"
                }`}
              >
                {e._source === "app" ? "App" : "Guild"}
              </span>

              <CopyButton text={e.animated ? `<a:${e.name}:${e.id}>` : `<:${e.name}:${e.id}>`} />

              {e._source === "app" && (
                <button
                  onClick={() => setDeleteEmoji(e)}
                  className="absolute bottom-1 left-1 opacity-0 group-hover:opacity-100 p-1 rounded bg-[#111214]/80 hover:bg-[#E74C3C]/80 transition-all"
                  title="Obriši"
                >
                  <Trash2 className="w-3 h-3 text-[#949BA4]" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} />
      <DeleteDialog emoji={deleteEmoji} onClose={() => setDeleteEmoji(null)} />
    </div>
  );
}
