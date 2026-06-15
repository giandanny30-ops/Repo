import { useState, useMemo, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import {
  Search,
  MoreVertical,
  Edit2,
  Clock,
  Trash2,
  ShieldOff,
  Bot,
  Crown,
  RefreshCw,
  Users,
} from "lucide-react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

interface Member {
  id: string;
  username: string;
  displayName: string;
  nick: string | null;
  avatar: string;
  roles: string[];
  joinedAt: string;
  bot: boolean;
  premiumSince: string | null;
}

interface Role {
  id: string;
  name: string;
  color: string;
  position: number;
  managed: boolean;
}

function useMembers() {
  return useQuery<Member[]>({
    queryKey: ["members"],
    queryFn: async () => {
      const r = await fetch(`${BASE}/api/discord/members?limit=1000`);
      if (!r.ok) throw new Error("Failed to load members");
      return r.json();
    },
    staleTime: 60_000,
    retry: 1,
  });
}

function useRoles() {
  return useQuery<Role[]>({
    queryKey: ["roles"],
    queryFn: async () => {
      const r = await fetch(`${BASE}/api/discord/roles`);
      if (!r.ok) throw new Error("Failed to load roles");
      return r.json();
    },
    staleTime: 300_000,
  });
}

function MemberAvatar({ member }: { member: Member }) {
  return (
    <div className="relative flex-shrink-0">
      <img
        src={member.avatar}
        alt={member.displayName}
        className="w-10 h-10 rounded-full bg-[#36393F]"
        onError={(e) => {
          (e.target as HTMLImageElement).src =
            `https://cdn.discordapp.com/embed/avatars/0.png`;
        }}
      />
      {member.bot && (
        <span className="absolute -bottom-0.5 -right-0.5 bg-[#5865F2] rounded-full p-0.5">
          <Bot className="w-2.5 h-2.5 text-white" />
        </span>
      )}
      {member.premiumSince && !member.bot && (
        <span className="absolute -bottom-0.5 -right-0.5 bg-[#FF73FA] rounded-full p-0.5">
          <Crown className="w-2.5 h-2.5 text-white" />
        </span>
      )}
    </div>
  );
}

function RoleBadge({ roleId, roles }: { roleId: string; roles: Role[] }) {
  const role = roles.find((r) => r.id === roleId);
  if (!role) return null;
  return (
    <span
      className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border"
      style={{
        borderColor: role.color + "60",
        color: role.color,
        backgroundColor: role.color + "18",
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: role.color }}
      />
      {role.name}
    </span>
  );
}

interface EditMemberDialogProps {
  member: Member | null;
  roles: Role[];
  onClose: () => void;
}

function EditMemberDialog({ member, roles, onClose }: EditMemberDialogProps) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [nick, setNick] = useState(member?.nick ?? "");
  const [selectedRoles, setSelectedRoles] = useState<string[]>(member?.roles ?? []);
  const [reason, setReason] = useState("");

  const editMutation = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${BASE}/api/discord/members/${member!.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nick: nick.trim() || null,
          roles: selectedRoles,
          reason: reason.trim() || undefined,
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: r.statusText }));
        throw new Error(err.error ?? "Greška");
      }
      return r.json();
    },
    onSuccess: () => {
      toast({ title: "✅ Sačuvano!", description: `Clan ${member?.displayName} ažuriran.` });
      qc.invalidateQueries({ queryKey: ["members"] });
      onClose();
    },
    onError: (e: Error) => {
      toast({ title: "❌ Greška", description: e.message, variant: "destructive" });
    },
  });

  const toggleRole = (id: string) => {
    setSelectedRoles((prev) =>
      prev.includes(id) ? prev.filter((r) => r !== id) : [...prev, id]
    );
  };

  if (!member) return null;

  return (
    <Dialog open={!!member} onOpenChange={() => onClose()}>
      <DialogContent className="bg-[#2B2D31] border-[#1E1F22] text-[#DBDEE1] max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <img src={member.avatar} className="w-8 h-8 rounded-full" alt="" />
            Uredi — {member.displayName}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Nickname */}
          <div className="space-y-1.5">
            <Label className="text-[#B5BAC1] text-xs uppercase tracking-wider">
              Nickname (ostavi prazno za reset)
            </Label>
            <Input
              value={nick}
              onChange={(e) => setNick(e.target.value)}
              placeholder={member.username}
              className="bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1] focus:border-[#5865F2]"
              maxLength={32}
            />
          </div>

          {/* Roles */}
          <div className="space-y-2">
            <Label className="text-[#B5BAC1] text-xs uppercase tracking-wider">
              Uloge ({selectedRoles.length} odabrano)
            </Label>
            <div className="max-h-52 overflow-y-auto space-y-1 pr-1">
              {roles
                .filter((r) => !r.managed)
                .map((role) => {
                  const active = selectedRoles.includes(role.id);
                  return (
                    <button
                      key={role.id}
                      onClick={() => toggleRole(role.id)}
                      className={`w-full flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors ${
                        active
                          ? "bg-[#404249] text-[#F2F3F5]"
                          : "text-[#949BA4] hover:bg-[#35373C] hover:text-[#DBDEE1]"
                      }`}
                    >
                      <span
                        className="w-3 h-3 rounded-full flex-shrink-0"
                        style={{ backgroundColor: role.color }}
                      />
                      <span className="flex-1 text-left truncate">{role.name}</span>
                      {active && (
                        <span className="text-[#5865F2] text-xs font-bold">✓</span>
                      )}
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Reason */}
          <div className="space-y-1.5">
            <Label className="text-[#B5BAC1] text-xs uppercase tracking-wider">
              Razlog (audit log, opcionalno)
            </Label>
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="npr. Ručno ažuriranje uloga"
              className="bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1] focus:border-[#5865F2]"
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            className="border-[#404249] text-[#B5BAC1] hover:bg-[#35373C]"
          >
            Odustani
          </Button>
          <Button
            onClick={() => editMutation.mutate()}
            disabled={editMutation.isPending}
            className="bg-[#5865F2] hover:bg-[#4752C4] text-white"
          >
            {editMutation.isPending ? "Čuvam..." : "Sačuvaj"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface TimeoutDialogProps {
  member: Member | null;
  onClose: () => void;
}

function TimeoutDialog({ member, onClose }: TimeoutDialogProps) {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [minutes, setMinutes] = useState("10");
  const [reason, setReason] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const r = await fetch(`${BASE}/api/discord/members/${member!.id}/timeout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ minutes: Number(minutes), reason: reason.trim() || undefined }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: r.statusText }));
        throw new Error(err.error ?? "Greška");
      }
      return r.json();
    },
    onSuccess: () => {
      toast({ title: "⏰ Timeout", description: `${member?.displayName} timeout ${minutes} min.` });
      qc.invalidateQueries({ queryKey: ["members"] });
      onClose();
    },
    onError: (e: Error) =>
      toast({ title: "❌ Greška", description: e.message, variant: "destructive" }),
  });

  if (!member) return null;
  return (
    <Dialog open={!!member} onOpenChange={() => onClose()}>
      <DialogContent className="bg-[#2B2D31] border-[#1E1F22] text-[#DBDEE1] max-w-sm">
        <DialogHeader>
          <DialogTitle>⏰ Timeout — {member.displayName}</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 py-2">
          <div className="space-y-1.5">
            <Label className="text-xs text-[#B5BAC1] uppercase tracking-wider">Trajanje (minute)</Label>
            <div className="flex gap-2 flex-wrap">
              {["5", "10", "30", "60", "1440"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMinutes(m)}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    minutes === m
                      ? "bg-[#5865F2] text-white"
                      : "bg-[#1E1F22] text-[#949BA4] hover:text-[#DBDEE1]"
                  }`}
                >
                  {m === "1440" ? "24h" : `${m}min`}
                </button>
              ))}
              <Input
                value={minutes}
                onChange={(e) => setMinutes(e.target.value)}
                className="w-20 bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1] h-8 text-sm"
                type="number"
                min="1"
                max="40320"
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-[#B5BAC1] uppercase tracking-wider">Razlog</Label>
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Razlog timeoutа..."
              className="bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1]"
            />
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} className="border-[#404249] text-[#B5BAC1]">Odustani</Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="bg-[#F39C12] hover:bg-[#D68910] text-white"
          >
            {mutation.isPending ? "..." : "Timeout"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Members() {
  const { data: members, isLoading, refetch, isFetching } = useMembers();
  const { data: roles = [] } = useRoles();
  const { toast } = useToast();
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [editMember, setEditMember] = useState<Member | null>(null);
  const [timeoutMember, setTimeoutMember] = useState<Member | null>(null);
  const [showBots, setShowBots] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: "kick" | "ban";
    member: Member;
  } | null>(null);

  const filtered = useMemo(() => {
    if (!members) return [];
    return members.filter((m) => {
      if (!showBots && m.bot) return false;
      const q = search.toLowerCase();
      return (
        !q ||
        m.displayName.toLowerCase().includes(q) ||
        m.username.toLowerCase().includes(q) ||
        (m.nick ?? "").toLowerCase().includes(q)
      );
    });
  }, [members, search, showBots]);

  const kickMutation = useMutation({
    mutationFn: async (userId: string) => {
      const r = await fetch(`${BASE}/api/discord/members/${userId}/kick`, { method: "DELETE" });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: r.statusText }));
        throw new Error(err.error ?? "Greška");
      }
      return r.json();
    },
    onSuccess: (_, userId) => {
      toast({ title: "👢 Kickovan", description: "Član je uklonjen sa servera." });
      qc.setQueryData<Member[]>(["members"], (old) => old?.filter((m) => m.id !== userId) ?? []);
      setConfirmAction(null);
    },
    onError: (e: Error) =>
      toast({ title: "❌ Greška", description: e.message, variant: "destructive" }),
  });

  const banMutation = useMutation({
    mutationFn: async (userId: string) => {
      const r = await fetch(`${BASE}/api/discord/members/${userId}/ban`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Banned via GIANNI Panel" }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({ error: r.statusText }));
        throw new Error(err.error ?? "Greška");
      }
      return r.json();
    },
    onSuccess: (_, userId) => {
      toast({ title: "🔨 Banovan", description: "Član je banovan sa servera." });
      qc.setQueryData<Member[]>(["members"], (old) => old?.filter((m) => m.id !== userId) ?? []);
      setConfirmAction(null);
    },
    onError: (e: Error) =>
      toast({ title: "❌ Greška", description: e.message, variant: "destructive" }),
  });

  const handleAction = useCallback(
    (type: "kick" | "ban", member: Member) => {
      setConfirmAction({ type, member });
    },
    []
  );

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Users className="w-6 h-6 text-[#5865F2]" />
            Članovi servera
          </h1>
          <p className="text-sm text-[#949BA4] mt-0.5">
            {members ? `${filtered.length} / ${members.filter(m => showBots || !m.bot).length} članova` : "Učitavam..."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowBots((v) => !v)}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors border ${
              showBots
                ? "border-[#5865F2] text-[#5865F2] bg-[#5865F2]/10"
                : "border-[#404249] text-[#949BA4] hover:border-[#5865F2]"
            }`}
          >
            <Bot className="w-3.5 h-3.5 inline mr-1.5" />
            Botovi
          </button>
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

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-[#949BA4]" />
        <Input
          placeholder="Traži po imenu, korisničkom imenu ili nicknamu..."
          className="pl-9 bg-[#1E1F22] border-[#1E1F22] text-[#DBDEE1] placeholder:text-[#949BA4] focus:border-[#5865F2]"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Members table */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg bg-[#2B2D31]" />
          ))}
        </div>
      ) : !members ? (
        <div className="text-center py-16 text-[#949BA4]">
          <p className="text-lg">❌ Nije moguće učitati članove</p>
          <p className="text-sm mt-1">Provjeri Discord token u Settings</p>
        </div>
      ) : (
        <div className="rounded-lg overflow-hidden border border-[#1E1F22]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[#1E1F22] text-[#949BA4] text-xs uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">Korisnik</th>
                <th className="text-left px-4 py-3 font-medium hidden md:table-cell">Uloge</th>
                <th className="text-left px-4 py-3 font-medium hidden lg:table-cell">Pridružio</th>
                <th className="px-4 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E1F22]">
              {filtered.map((member) => (
                <tr
                  key={member.id}
                  className="bg-[#2B2D31] hover:bg-[#35373C] transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <MemberAvatar member={member} />
                      <div className="min-w-0">
                        <p className="font-medium text-[#F2F3F5] truncate">
                          {member.displayName}
                          {member.premiumSince && (
                            <span className="ml-1.5 text-[#FF73FA] text-xs">💜</span>
                          )}
                        </p>
                        <p className="text-[#949BA4] text-xs truncate">
                          @{member.username}
                          {member.nick && member.nick !== member.displayName && (
                            <span className="ml-1 text-[#5865F2]">(nick: {member.nick})</span>
                          )}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {member.roles.slice(0, 4).map((rid) => (
                        <RoleBadge key={rid} roleId={rid} roles={roles} />
                      ))}
                      {member.roles.length > 4 && (
                        <span className="text-[10px] text-[#949BA4] self-center">
                          +{member.roles.length - 4}
                        </span>
                      )}
                      {member.roles.length === 0 && (
                        <span className="text-[#949BA4] text-xs">—</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell text-[#949BA4] text-xs">
                    {member.joinedAt
                      ? new Date(member.joinedAt).toLocaleDateString("bs-BA")
                      : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {!member.bot && (
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-[#949BA4] hover:text-[#DBDEE1] hover:bg-[#404249]"
                          >
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent
                          align="end"
                          className="bg-[#111214] border-[#1E1F22] text-[#DBDEE1] w-44"
                        >
                          <DropdownMenuItem
                            onClick={() => setEditMember(member)}
                            className="hover:bg-[#35373C] cursor-pointer gap-2"
                          >
                            <Edit2 className="h-3.5 w-3.5 text-[#5865F2]" />
                            Uredi nick / uloge
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setTimeoutMember(member)}
                            className="hover:bg-[#35373C] cursor-pointer gap-2"
                          >
                            <Clock className="h-3.5 w-3.5 text-[#F39C12]" />
                            Timeout
                          </DropdownMenuItem>
                          <DropdownMenuSeparator className="bg-[#2B2D31]" />
                          <DropdownMenuItem
                            onClick={() => handleAction("kick", member)}
                            className="hover:bg-[#35373C] cursor-pointer gap-2 text-[#F39C12]"
                          >
                            <ShieldOff className="h-3.5 w-3.5" />
                            Kick
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleAction("ban", member)}
                            className="hover:bg-[#35373C] cursor-pointer gap-2 text-[#E74C3C]"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            Ban
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center py-12 text-[#949BA4]">
                    Nema članova koji odgovaraju pretrazi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit dialog */}
      <EditMemberDialog
        member={editMember}
        roles={roles}
        onClose={() => setEditMember(null)}
      />

      {/* Timeout dialog */}
      <TimeoutDialog
        member={timeoutMember}
        onClose={() => setTimeoutMember(null)}
      />

      {/* Confirm kick/ban dialog */}
      {confirmAction && (
        <Dialog open={!!confirmAction} onOpenChange={() => setConfirmAction(null)}>
          <DialogContent className="bg-[#2B2D31] border-[#1E1F22] text-[#DBDEE1] max-w-sm">
            <DialogHeader>
              <DialogTitle className={confirmAction.type === "ban" ? "text-[#E74C3C]" : "text-[#F39C12]"}>
                {confirmAction.type === "ban" ? "🔨 Ban" : "👢 Kick"} — {confirmAction.member.displayName}
              </DialogTitle>
            </DialogHeader>
            <p className="text-[#949BA4] text-sm py-2">
              Jesi li siguran/na? Ova akcija {confirmAction.type === "ban" ? "banova" : "kickuje"} <strong className="text-[#DBDEE1]">{confirmAction.member.displayName}</strong> sa servera.
            </p>
            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => setConfirmAction(null)}
                className="border-[#404249] text-[#B5BAC1]"
              >
                Odustani
              </Button>
              <Button
                onClick={() => {
                  if (confirmAction.type === "kick") {
                    kickMutation.mutate(confirmAction.member.id);
                  } else {
                    banMutation.mutate(confirmAction.member.id);
                  }
                }}
                disabled={kickMutation.isPending || banMutation.isPending}
                className={
                  confirmAction.type === "ban"
                    ? "bg-[#E74C3C] hover:bg-[#C0392B] text-white"
                    : "bg-[#F39C12] hover:bg-[#D68910] text-white"
                }
              >
                {kickMutation.isPending || banMutation.isPending
                  ? "..."
                  : confirmAction.type === "ban"
                  ? "Banuj"
                  : "Kickuj"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
