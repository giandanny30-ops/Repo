import { Router } from "express";
import { randomBytes } from "crypto";

const router = Router();

// ─── UNO ─────────────────────────────────────────────────────────────────────

type UnoColor = "red" | "green" | "blue" | "yellow" | "wild";
type UnoValue = "0"|"1"|"2"|"3"|"4"|"5"|"6"|"7"|"8"|"9"|"skip"|"reverse"|"draw2"|"wild"|"wild4";

interface UnoCard { id: string; color: UnoColor; value: UnoValue }
interface UnoPlayer { id: string; name: string; hand: UnoCard[]; saidUno: boolean; connected: number }

interface UnoRoom {
  code: string;
  players: UnoPlayer[];
  deck: UnoCard[];
  discard: UnoCard[];
  currentIdx: number;
  direction: 1 | -1;
  drawStack: number;
  pendingColor: UnoColor | null;
  state: "waiting" | "playing" | "finished";
  winner: string | null;
  lastAction: string;
  createdAt: number;
}

const unoRooms = new Map<string, UnoRoom>();

function makeUnoDeck(): UnoCard[] {
  const colors: UnoColor[] = ["red","green","blue","yellow"];
  const cards: UnoCard[] = [];
  let id = 0;
  for (const c of colors) {
    cards.push({ id: `${id++}`, color: c, value: "0" });
    for (const v of ["1","2","3","4","5","6","7","8","9","skip","reverse","draw2"] as UnoValue[]) {
      cards.push({ id: `${id++}`, color: c, value: v });
      cards.push({ id: `${id++}`, color: c, value: v });
    }
  }
  for (let i = 0; i < 4; i++) {
    cards.push({ id: `${id++}`, color: "wild", value: "wild" });
    cards.push({ id: `${id++}`, color: "wild", value: "wild4" });
  }
  return shuffle(cards);
}

function shuffle<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function canPlay(card: UnoCard, top: UnoCard, pendingColor: UnoColor | null): boolean {
  const effectiveColor = pendingColor ?? top.color;
  if (card.value === "wild" || card.value === "wild4") return true;
  return card.color === effectiveColor || card.value === top.value;
}

function drawCard(room: UnoRoom): UnoCard {
  if (room.deck.length === 0) {
    const top = room.discard[room.discard.length - 1];
    room.deck = shuffle(room.discard.slice(0, -1));
    room.discard = [top];
  }
  return room.deck.pop()!;
}

function nextIdx(room: UnoRoom, skip = false): number {
  const n = room.players.length;
  let idx = (room.currentIdx + room.direction + n) % n;
  if (skip) idx = (idx + room.direction + n) % n;
  return idx;
}

// POST /api/play/uno  — create room
router.post("/play/uno", (req, res) => {
  const code = randomBytes(3).toString("hex").toUpperCase();
  const room: UnoRoom = {
    code, players: [], deck: makeUnoDeck(), discard: [], currentIdx: 0,
    direction: 1, drawStack: 0, pendingColor: null,
    state: "waiting", winner: null, lastAction: "Soba kreirana",
    createdAt: Date.now(),
  };
  unoRooms.set(code, room);
  res.json({ code });
});

// POST /api/play/uno/:code/join  — join room
router.post("/play/uno/:code/join", (req, res) => {
  const room = unoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  if (room.state !== "waiting") return res.status(400).json({ error: "Igra je već počela" });
  if (room.players.length >= 10) return res.status(400).json({ error: "Soba je puna" });
  const { name } = req.body as { name?: string };
  if (!name?.trim()) return res.status(400).json({ error: "Ime je obavezno" });
  const id = randomBytes(4).toString("hex");
  room.players.push({ id, name: name.trim(), hand: [], saidUno: false, connected: Date.now() });
  room.lastAction = `${name.trim()} se pridružio/la`;
  res.json({ playerId: id, roomCode: room.code });
});

// POST /api/play/uno/:code/start  — start game
router.post("/play/uno/:code/start", (req, res) => {
  const room = unoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  if (room.players.length < 2) return res.status(400).json({ error: "Potrebno min 2 igrača" });
  room.deck = makeUnoDeck();
  for (const p of room.players) {
    p.hand = [];
    for (let i = 0; i < 7; i++) p.hand.push(drawCard(room));
  }
  let first: UnoCard;
  do { first = drawCard(room); } while (first.value === "wild" || first.value === "wild4");
  room.discard = [first];
  room.currentIdx = 0;
  room.state = "playing";
  room.lastAction = "Igra je počela!";
  res.json({ ok: true });
});

// GET /api/play/uno/:code  — get state (player sees own hand)
router.get("/play/uno/:code", (req, res) => {
  const room = unoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  const { playerId } = req.query as { playerId?: string };
  const safeRoom = {
    code: room.code,
    state: room.state,
    currentIdx: room.currentIdx,
    direction: room.direction,
    pendingColor: room.pendingColor,
    drawStack: room.drawStack,
    topCard: room.discard[room.discard.length - 1],
    winner: room.winner,
    lastAction: room.lastAction,
    players: room.players.map(p => ({
      id: p.id, name: p.name,
      handCount: p.hand.length,
      saidUno: p.saidUno,
      hand: p.id === playerId ? p.hand : undefined,
    })),
  };
  res.json(safeRoom);
});

// POST /api/play/uno/:code/action
router.post("/play/uno/:code/action", (req, res) => {
  const room = unoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  if (room.state !== "playing") return res.status(400).json({ error: "Igra nije aktivna" });

  const { playerId, action, cardIdx, chosenColor } = req.body as {
    playerId?: string; action?: string; cardIdx?: number; chosenColor?: UnoColor;
  };

  const pIdx = room.players.findIndex(p => p.id === playerId);
  if (pIdx === -1) return res.status(400).json({ error: "Nisi u sobi" });

  const isCurrentPlayer = pIdx === room.currentIdx;
  const player = room.players[pIdx];

  if (action === "draw") {
    if (!isCurrentPlayer) return res.status(400).json({ error: "Nije tvoj red" });
    const count = room.drawStack > 0 ? room.drawStack : 1;
    for (let i = 0; i < count; i++) player.hand.push(drawCard(room));
    room.drawStack = 0;
    room.currentIdx = nextIdx(room);
    room.pendingColor = null;
    room.lastAction = `${player.name} je uzeo/la ${count} kart${count === 1 ? "u" : "e"}`;
    return res.json({ ok: true });
  }

  if (action === "play") {
    if (!isCurrentPlayer) return res.status(400).json({ error: "Nije tvoj red" });
    if (cardIdx === undefined || cardIdx < 0 || cardIdx >= player.hand.length)
      return res.status(400).json({ error: "Nevalidna karta" });

    const card = player.hand[cardIdx];
    const top = room.discard[room.discard.length - 1];

    if (room.drawStack > 0 && card.value !== "draw2" && card.value !== "wild4")
      return res.status(400).json({ error: "Moraš staviti +2/+4 ili uzeti karte" });

    if (!canPlay(card, top, room.pendingColor))
      return res.status(400).json({ error: "Ne možeš igrati tu kartu" });

    player.hand.splice(cardIdx, 1);
    room.discard.push(card);
    room.pendingColor = null;
    player.saidUno = false;

    if (player.hand.length === 0) {
      room.state = "finished";
      room.winner = player.name;
      room.lastAction = `🏆 ${player.name} je pobijedio/la!`;
      return res.json({ ok: true });
    }

    let skip = false;
    if (card.value === "skip") {
      skip = true;
      room.lastAction = `${player.name} stavio/la Skip`;
    } else if (card.value === "reverse") {
      room.direction = room.direction === 1 ? -1 : 1;
      if (room.players.length === 2) skip = true;
      room.lastAction = `${player.name} promijenio/la smjer`;
    } else if (card.value === "draw2") {
      room.drawStack += 2;
      skip = true;
      room.lastAction = `${player.name} stavio/la +2`;
    } else if (card.value === "wild") {
      if (!chosenColor) return res.status(400).json({ error: "Odaberi boju" });
      room.pendingColor = chosenColor;
      room.lastAction = `${player.name} odabrao/la ${chosenColor}`;
    } else if (card.value === "wild4") {
      if (!chosenColor) return res.status(400).json({ error: "Odaberi boju" });
      room.pendingColor = chosenColor;
      room.drawStack += 4;
      skip = true;
      room.lastAction = `${player.name} stavio/la +4 ${chosenColor}`;
    } else {
      room.lastAction = `${player.name} igrao/la ${card.color} ${card.value}`;
    }

    room.currentIdx = nextIdx(room, skip);
    return res.json({ ok: true });
  }

  if (action === "uno") {
    if (player.hand.length === 1) player.saidUno = true;
    return res.json({ ok: true });
  }

  return res.status(400).json({ error: "Nepoznata akcija" });
});

// ─── LUDO (Čovječe ne ljuti se) ──────────────────────────────────────────────

interface LudoPiece { pos: number; home: boolean; finished: boolean }
interface LudoPlayer { id: string; name: string; color: LudoColor; pieces: LudoPiece[] }

type LudoColor = "red" | "blue" | "green" | "yellow";

interface LudoRoom {
  code: string;
  players: LudoPlayer[];
  state: "waiting" | "playing" | "finished";
  currentIdx: number;
  dice: number | null;
  diceRolled: boolean;
  winner: string | null;
  lastAction: string;
  createdAt: number;
}

const ludoRooms = new Map<string, LudoRoom>();

const LUDO_COLORS: LudoColor[] = ["red", "blue", "green", "yellow"];
const LUDO_START: Record<LudoColor, number> = { red: 0, blue: 13, green: 26, yellow: 39 };
const LUDO_FINISH_ENTRY: Record<LudoColor, number> = { red: 51, blue: 12, green: 25, yellow: 38 };
const SAFE_SQUARES = [0, 8, 13, 21, 26, 34, 39, 47];

function ludoAbsPos(color: LudoColor, relPos: number): number {
  return (LUDO_START[color] + relPos) % 52;
}

// POST /api/play/ludo
router.post("/play/ludo", (req, res) => {
  const code = randomBytes(3).toString("hex").toUpperCase();
  const room: LudoRoom = {
    code, players: [], state: "waiting", currentIdx: 0,
    dice: null, diceRolled: false, winner: null,
    lastAction: "Soba kreirana", createdAt: Date.now(),
  };
  ludoRooms.set(code, room);
  res.json({ code });
});

// POST /api/play/ludo/:code/join
router.post("/play/ludo/:code/join", (req, res) => {
  const room = ludoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  if (room.state !== "waiting") return res.status(400).json({ error: "Igra je već počela" });
  if (room.players.length >= 4) return res.status(400).json({ error: "Soba je puna (max 4)" });
  const { name } = req.body as { name?: string };
  if (!name?.trim()) return res.status(400).json({ error: "Ime je obavezno" });
  const id = randomBytes(4).toString("hex");
  const color = LUDO_COLORS[room.players.length];
  room.players.push({
    id, name: name.trim(), color,
    pieces: [
      { pos: -1, home: true, finished: false },
      { pos: -1, home: true, finished: false },
      { pos: -1, home: true, finished: false },
      { pos: -1, home: true, finished: false },
    ],
  });
  room.lastAction = `${name.trim()} se pridružio/la kao ${color}`;
  res.json({ playerId: id, color, roomCode: room.code });
});

// POST /api/play/ludo/:code/start
router.post("/play/ludo/:code/start", (req, res) => {
  const room = ludoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  if (room.players.length < 2) return res.status(400).json({ error: "Potrebno min 2 igrača" });
  room.state = "playing";
  room.lastAction = "Igra je počela!";
  res.json({ ok: true });
});

// GET /api/play/ludo/:code
router.get("/play/ludo/:code", (req, res) => {
  const room = ludoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  res.json(room);
});

// POST /api/play/ludo/:code/action  — {playerId, action: "roll"|"move", pieceIdx?}
router.post("/play/ludo/:code/action", (req, res) => {
  const room = ludoRooms.get(req.params.code);
  if (!room) return res.status(404).json({ error: "Soba ne postoji" });
  if (room.state !== "playing") return res.status(400).json({ error: "Igra nije aktivna" });

  const { playerId, action, pieceIdx } = req.body as { playerId?: string; action?: string; pieceIdx?: number };
  const pIdx = room.players.findIndex(p => p.id === playerId);
  if (pIdx === -1) return res.status(400).json({ error: "Nisi u sobi" });
  if (pIdx !== room.currentIdx) return res.status(400).json({ error: "Nije tvoj red" });

  const player = room.players[pIdx];

  if (action === "roll") {
    if (room.diceRolled) return res.status(400).json({ error: "Već si bacio kockicu" });
    room.dice = Math.floor(Math.random() * 6) + 1;
    room.diceRolled = true;
    room.lastAction = `${player.name} bacio/la ${room.dice}`;

    // Check if any move is possible
    const canMove = player.pieces.some((p, i) => {
      if (p.finished) return false;
      if (p.home) return room.dice === 6;
      return true;
    });
    if (!canMove) {
      room.diceRolled = false;
      room.dice = null;
      room.currentIdx = (room.currentIdx + 1) % room.players.length;
      room.lastAction += " — nema mogućeg poteza, prelazi se red";
    }
    return res.json({ ok: true, dice: room.dice });
  }

  if (action === "move") {
    if (!room.diceRolled || room.dice === null) return res.status(400).json({ error: "Prvo baci kockicu" });
    if (pieceIdx === undefined || pieceIdx < 0 || pieceIdx > 3) return res.status(400).json({ error: "Nevalidna figura" });
    const piece = player.pieces[pieceIdx];
    if (piece.finished) return res.status(400).json({ error: "Figura je već završila" });

    const dice = room.dice;

    if (piece.home) {
      if (dice !== 6) return res.status(400).json({ error: "Trebaš 6 za izlazak" });
      piece.home = false;
      piece.pos = 0; // start relative position
      room.lastAction = `${player.name} izbacio/la figuru ${pieceIdx + 1}`;
    } else {
      const newRel = piece.pos + dice;
      // Check if entering finish zone (relative pos 51 = finish entry)
      if (newRel > 56) return res.status(400).json({ error: "Ne možeš se pomjeriti" });
      if (newRel === 56) {
        piece.finished = true;
        piece.pos = 56;
        room.lastAction = `${player.name} doveo/la figuru ${pieceIdx + 1} kući! 🏠`;
      } else {
        piece.pos = newRel;
        const absPos = ludoAbsPos(player.color, newRel <= 51 ? newRel : newRel);
        // Check captures (only on main path, pos 0-51)
        if (newRel < 52 && !SAFE_SQUARES.includes(absPos)) {
          for (const other of room.players) {
            if (other.id === player.id) continue;
            for (const op of other.pieces) {
              if (!op.home && !op.finished && op.pos < 52) {
                const otherAbs = ludoAbsPos(other.color, op.pos);
                if (otherAbs === absPos) {
                  op.home = true;
                  op.pos = -1;
                  room.lastAction = `${player.name} srušio/la figuru igrača ${other.name}! 💥`;
                }
              }
            }
          }
        }
        room.lastAction = room.lastAction || `${player.name} pomijerio/la figuru ${pieceIdx + 1}`;
      }
    }

    // Check win
    if (player.pieces.every(p => p.finished)) {
      room.state = "finished";
      room.winner = player.name;
      room.lastAction = `🏆 ${player.name} je pobijedio/la!`;
      room.diceRolled = false;
      return res.json({ ok: true });
    }

    // If rolled 6, player gets another turn
    if (dice === 6) {
      room.diceRolled = false;
      room.dice = null;
      room.lastAction += " (baci ponovo — pao je 6!)";
    } else {
      room.diceRolled = false;
      room.dice = null;
      room.currentIdx = (room.currentIdx + 1) % room.players.length;
    }
    return res.json({ ok: true });
  }

  return res.status(400).json({ error: "Nepoznata akcija" });
});

// Cleanup rooms older than 4h
setInterval(() => {
  const cutoff = Date.now() - 4 * 60 * 60 * 1000;
  for (const [k, v] of unoRooms) if (v.createdAt < cutoff) unoRooms.delete(k);
  for (const [k, v] of ludoRooms) if (v.createdAt < cutoff) ludoRooms.delete(k);
}, 30 * 60 * 1000);

export default router;
