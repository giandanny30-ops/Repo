import discord, random, asyncio, json, os, time, aiohttp, re
from itertools import combinations as _pk_comb
from collections import defaultdict, deque, Counter
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timezone, timedelta

# ═══════════════════════════════════════════
#           KONFIGURACIJA
# ═══════════════════════════════════════════
BOT_NAME = "GIANNI (Custom)"
VERSION  = "v3.0"
TOKEN    = os.environ.get("DISCORD_TOKEN")

# ═══════════════════════════════════════════
#    🔐 LICENCA — Jedini originalni bot
# ═══════════════════════════════════════════
# Bot radi SAMO ako je član zvaničnog GIAN servera (GIAN).
# Ako je neko klonirao kod i pokrenuo svoju kopiju — bot napušta sve servere
# i gasi se automatski.
OFFICIAL_INVITE   = "gian"               # GIAN
OFFICIAL_GUILD_ID = 1494043955980140754  # ID zvaničnog GIAN servera

COLORS = {
    "default": 0x2B2D42, "success": 0x43B581, "error":   0xE74C3C,
    "warning": 0xF39C12, "info":    0x2B2D42, "gold":    0xF1C40F,
    "balkan":  0x2B2D42, "purple":  0x2B2D42, "fun":     0x2B2D42,
    "dark":    0x2B2D42, "teal":    0x2B2D42, "love":    0xFF4D6D,
    "pink":    0x2B2D42,
    "aqua":    0x2B2D42,
}

# ── Custom animirani emoji (već postoje na serveru) — za ljepši izgled igara ──
E_FIRE1 = "<a:vatrice1:1500466044429664256>"
E_FIRE2 = "<a:vatrice2:1500466048418185246>"
E_FIRE3 = "<a:vatrice3:1500466039782113352>"
E_FIRE4 = "<a:vatrice4:1500466061970247741>"
E_GAME  = "<a:game1:1500459114931949568>"
E_MUSIC = "<a:music2:1500459145382592602>"

# Akcentne boje po igri (premium izgled)
GAME_COLORS = {
    "kaladont": 0xF1C40F,  # aqua
    "wordle":   0x6AAA64,  # zelena (wordle)
    "kviz":     0x9B59B6,  # ljubičasta
    "geo":      0x3498DB,  # plava
}
# ═══════════════════════════════════════════
#    PANEL API — Live embed integracija
# ═══════════════════════════════════════════
PANEL_API_URL = os.environ.get("PANEL_API_URL", "https://giann.uk")

async def get_panel_embed(name: str) -> dict | None:
    """Fetch embed data from GIAN panel API (fallback to hardcoded on error)."""
    try:
        async with aiohttp.ClientSession() as _s:
            async with _s.get(f"{PANEL_API_URL}/api/embeds/{name}",
                              timeout=aiohttp.ClientTimeout(total=3)) as _r:
                if _r.status == 200:
                    return await _r.json()
    except Exception as _pe:
        print(f"[panel-embed] Cannot fetch '{name}': {_pe}")
    return None

# ── Panel protection config (anti-raid + anti-nsfw settings) ─────────────────
_prot_cfg: dict = {}

# ── Games config (panel → bot) ───────────────────────────
_games_cfg: dict = {}

async def get_panel_games() -> dict:
    """Fetch games/economy settings from panel API. Falls back to defaults on error."""
    global _games_cfg
    try:
        async with aiohttp.ClientSession() as _s:
            async with _s.get(f"{PANEL_API_URL}/api/games",
                              timeout=aiohttp.ClientTimeout(total=3)) as _r:
                if _r.status == 200:
                    _games_cfg = await _r.json()
                    print(f"[panel-games] Config refreshed OK")
    except Exception as _ge:
        print(f"[panel-games] Fetch error (using last/defaults): {_ge}")
    return _games_cfg

def _g_eco(cmd: str) -> dict:
    """Vrati economy config za datu komandu."""
    defaults = {
        "posao": {"enabled": True, "cooldown_min": 30,  "reward_min": 150, "reward_max": 600},
        "daily": {"enabled": True, "cooldown_hours": 24, "reward_min": 300, "reward_max": 800},
        "kradi": {"enabled": True, "cooldown_hours": 2,  "success_rate": 38, "steal_min": 50, "steal_max": 300},
    }
    eco = _games_cfg.get("economy", {})
    return {**defaults.get(cmd, {}), **eco.get(cmd, {})}

def _g_gamble(cmd: str) -> dict:
    """Vrati gambling config za datu komandu."""
    defaults = {
        "slots":     {"enabled": True, "cooldown_sec": 15, "max_bet": 1_000_000_000},
        "blackjack": {"enabled": True, "cooldown_sec": 30},
        "poker":     {"enabled": True, "min_bet": 50,  "max_bet": 50_000},
        "kviz":      {"enabled": True, "min_bet": 10},
        "geografija":{"enabled": True, "min_bet": 10},
        "kpm":       {"enabled": True},
        "vjasala":   {"enabled": True},
        "kaladont":  {"enabled": True, "reward": 1500},
        "wordle":    {"enabled": True, "reward": 1200},
        "toplo_hladno":{"enabled": True},
        "amogus":    {"enabled": True},
    }
    gam = _games_cfg.get("gambling", {})
    return {**defaults.get(cmd, {}), **gam.get(cmd, {})}

def _g_social() -> bool:
    return _games_cfg.get("social", {}).get("enabled", True)

def _g_hunt() -> dict:
    defaults = {"enabled": True, "cooldown_sec": 7}
    return {**defaults, **_games_cfg.get("animals", {}).get("hunt", {})}

async def _games_refresh_loop():
    """Osvježava games config svakih 5 minuta."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await asyncio.sleep(300)
        await get_panel_games()

# ── Protection config (panel → bot) ──────────────────────
async def get_panel_protection() -> dict:
    """Fetch protection settings from panel API. Falls back to defaults on error."""
    global _prot_cfg
    try:
        async with aiohttp.ClientSession() as _s:
            async with _s.get(f"{PANEL_API_URL}/api/protection",
                              timeout=aiohttp.ClientTimeout(total=3)) as _r:
                if _r.status == 200:
                    _prot_cfg = await _r.json()
                    print(f"[panel-protection] Config refreshed — antiRaid={_prot_cfg.get('antiRaid',{}).get('enabled')}, antiNsfw={_prot_cfg.get('antiNsfw',{}).get('enabled')}")
    except Exception as _pe:
        print(f"[panel-protection] Fetch error (using last/defaults): {_pe}")
    return _prot_cfg

def _prot_raid() -> dict:
    ar = _prot_cfg.get("antiRaid", {})
    return {
        "enabled":      ar.get("enabled", True),
        "window":       ar.get("windowSeconds", 30),
        "limit":        ar.get("joinLimit", 5),
        "age_days":     ar.get("suspiciousAgeDays", 7),
        "lockdown_min": ar.get("lockdownMinutes", 5),
        "action":       ar.get("action", "kick"),
    }

def _prot_nsfw() -> dict:
    an = _prot_cfg.get("antiNsfw", {})
    return {
        "enabled":       an.get("enabled", True),
        "strikes":       an.get("strikesBeforeTimeout", 3),
        "timeout_min":   an.get("timeoutMinutes", 60),
        "extra_sites":   [s.lower() for s in an.get("extraBlockedSites", [])],
        "extra_keywords": [k.lower() for k in an.get("extraBlockedKeywords", [])],
    }

async def _protection_refresh_loop():
    """Osvježava protection config svakih 5 minuta."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await get_panel_protection()
        await asyncio.sleep(300)

def _ev(text: str, member, count: int) -> str:
    """Replace panel template variables in embed text."""
    if not text: return text
    return (text
        .replace("{user}", member.mention)
        .replace("{memberCount}", str(count))
        .replace("{user.name}", member.display_name)
        .replace("{server}", member.guild.name if member.guild else "")
    )



JOBS = [
    "Radio si kao konobar 🍺", "Čuvao si baku 🧓", "Prodavao ćevape 🥙",
    "Vozio si taksi 🚕", "Radio si na građevini 🏗️", "Popravljao auta 🔧",
    "Čuvao parking 🚗", "Nosio poštu 📬", "Prodavao lubenicu 🍉",
    "Brao paprike u polju 🌶️", "Radio u pekari 🥖", "Čuvao ovce 🐑",
    "Prodavao karte na stanici 🚌", "Radio kao zaštitar 💪", "Prao automobile 🚿",
]

EIGHTBALL_REPLIES = [
    "🟢 Definitivno da!", "🟢 Sve znakovi govore — DA.",
    "🟢 Bez ikakve sumnje, majstore!", "🟢 Računaj na to, brate.",
    "🟡 Pitaj ponovo malo kasnije.", "🟡 Nisam baš siguran, brate.",
    "🟡 Teško reći u ovom trenutku.", "🟡 Magla mi zaklanja odgovor.",
    "🔴 Ne računaj na to.", "🔴 Odgovor je jasno — NE.",
    "🔴 Izgledi su jako loši.", "🔴 Zaboravi na to, majstore.",
]

# ═══════════════════════════════════════════
#    MEMOVI (veliki bazen sa rotacijom)
# ═══════════════════════════════════════════
MEMES = [
    "Kad kažeš 'samo još 5 minuta' a prođe 3 sata. 😴📱",
    "Baka: 'Jesi li jeo?' Ti: 'Jesam.' Baka: 'A jesi li gladan?' 🍽️👵",
    "Kad upališ klimu na 16°C a napolju je 40°C. ❄️🥵",
    "Turbofolk u 3 ujutru, sutra na posao u 7. 🎶😵",
    "Kad kažeš 'idemo na kafu' a završiš na roštilju do zore. 🥩🍻",
    "Svaki Balkanac ima ujaka koji sve zna popraviti. 🔧😂",
    "'Sačekaj 5 minuta' — Balkan vreme: 45 minuta minimum. ⏰🤌",
    "Kad pitaš baku za recept: 'Malo ovog, malo onog, dok ne bude dobro.' 📏👵",
    "Kad kaže 'idem odmah' a gleda TV već sat vremena. 📺🛋️",
    "Ništa me ne boli više nego kad mi telefon padne na lice u krevetu. 📱😩",
    "Balkan dijetа: ne jedeš između obroka. Obroci su svaki sat. 🍴⏱️",
    "Komšija u 11 noću: buši zidove. Normalnost. 🔨🏠",
    "Kad mama kaže 'pričekaj dok dođemo kući' — Bog te čuvaj. 😰🏡",
    "'Idemo samo na malo' — 6 sati kasnije. 😂⌛",
    "Kad vidiš stranca u selu svi izlaze da gledaju. 👀🏡",
    "Balkan autopilot: čim sjedneš — telefon u ruci. 📱🧠",
    "Svaka baka misli da je njeno dijete premršavo. Vaga se ne slaže. ⚖️👵",
    "Na Balkanu se ne kaže 'hvala' u kafani. Prstom se kuca po stolu. 🫵☕",
    "Kad kažeš da si sit a vidiš čevape. 🥙😤",
    "Balkanska logika: ne možeš biti bolestan ljeti, samo zimi. ☀️🤧",
    "Baka čuva svaku vrećicu od kupovine već 30 godina. 🛍️♻️",
    "Kad ti kaže 'nisam ljuta' — bježi. 😬💨",
    "Balkanska dijalektika: svaka rasprava završi pričom o ratu. ⚔️🗣️",
    "Pranje auta = kiša za 2 sata garantovana. 🚗🌧️",
    "Kada slušaš muziku na slušalicama a mama govori s tobom. 🎧😤",
    "Spavanje na plaži sa šeširom na licu. Balkanski ljetni odmor. 🏖️👒",
    "Na Balkanu svadbena muzika mora biti glasnija od aviona. ✈️🎵",
    "'Ajde brzo' — 20 minuta čekanja. 🏃⏳",
    "Kad dobiješ viber poruku od mame u 2 noću: 'Jesi li stigao?' 📲😅",
    "Piknik bez kajmaka — nije piknik. 🧀🌿",
    "Svaki kvar na autu Balkanac može dijagnosticirati zvukom. 🚗👂",
    "Kad ti komšija javi vijest koja nije tvoja stvar. 📰🙄",
    "Ljeto = hvatanje klime ispod jorgana. 🛏️❄️",
    "Balkan parking: dvije linije? Staju četiri auta. 🚙😂",
    "Fritula je rješenje za sve životne probleme. 🍩🫶",
    "Kad dođe familija iznenada a kuća nije čista. 😱🧹",
    "Svako putovanje počinje sa 'imaš li pare za autoput?'. 🛣️💶",
    "Baka na kafi: zna sve o svima u gradu. 👵☕📰",
    "Balkanska statistika: 9 od 10 problema se rješava uz kafu. ☕📊",
    "'Otišao sam samo po hleb' — vratio se sa pola marketa. 🛒😅",
    "Kad igraš fudbal na ulici i lopta ode kod ljutog komšije. ⚽😰",
    "Svaki razgovor na Balkanu počne sa: 'Brate, slušaj ovo...' 🗣️👂",
    "Dnevna soba samo za goste. Gosti nikad ne dolaze. 🛋️🔒",
    "Šalter na pošti: radi jedan, čekaju trideset. 🏢😑",
    "Kad se probudi baka u 5 ujutru i odmah počne pjevati. 🌅🎵👵",
    "Balkanski sat: 'Dođi u 7' znači dođi u 8:30. 🕖😄",
    "Svaka kuća ima baku koja čuva bombone od 1998. 🍬👵",
    "Na Balkanu, ako ne jedeš treću porciju, nisi počašćen. 🍽️😅",
    "Kad završiš posao i nema struje za punjač. 🔌😩",
    "Balkanac na moru: čeka red u restoranu, naruči duplo, pojede četvoro. 🍴🌊",
    "Usred filma: 'Koliko još traje?' — Baš na napetom dijelu. 🎬😤",
    "Kad kaže 'jesi li gladan?' a hrana je već na stolu. 🍲🏃",
    "Svaka balkanska mama je doktor, kuhar i psiholog u jednom. 👩‍⚕️👩‍🍳🧠",
    "Kad ideš kod zubara a zub prestane boljeti čim sjedneš u čekaonicu. 🦷😤",
    "Balkan net: radi samo kad ne trebaš. 📶🙃",
    "Djeca na Balkanu idu van da se igraju — mama zna sve što su radila. 🏃👁️",
    "Kad vidiš kišu a majka te pita jesi li ponio kapu. 🌧️🧢",
    "Jedina stvar brža od vijesti na Balkanu — trač. 👄⚡",
    "Svaki rodjak želi znati kada se ženiš. Svake godine. 💍😭",
    "Na ljetovanju: sunce, more i debata gdje ćemo ručati 2 sata. 🌞🍽️",
    "Balkanac u inostranstvu: pronađe Balkanca u roku 10 minuta. 🌍🤝",
    "Kad čistiš sobu a mama kaže 'baciš li to, ubijam te'. 🗑️😅",
    "Fijaker sa konjima sporiji od balkanskog interneta. 🐴📶",
    "Svaka baka krije novac u džepu kecelje. 💸👵",
    "Domaći sok od šljive — lijek za sve. 🍑💊",
    "Balkan dijalog: 'Jesi jeo?' 'Jesam.' 'Jedi još.' 🍽️🔄",
    "Kad nema struje — svi izađu napolje i postanu filozofi. 🕯️🧠",
    "Majka ne razumije 'meni ništa ne treba za rodjendan'. 🎁👩‍👦",
    "Na Balkanu kafu piješ u svakoj kući čak i ako si 'samo svrnuo'. ☕🏠",
    "Djeca na Balkanu nemaju 'slobodnog vremena' — ima posla uvijek. 🧹⏰",
    "Balkan parking 2: dvostruki parking je tradicija, ne greška. 🚗🚗",
    "Svako selo ima svog vračara i svi tvrde da ne vjeruju. 🔮😏",
    "Kad mama pita 'gdje si bio?' a ti bio u WC-u. 🚽😤",
    "Balkan zimovanje: pečenje kestena i debata o politici. 🌰🗳️",
    "Sendvič koji je spakovao ko znaš uvijek je bolji. 🥪❤️",
    "Svaki kafić ima isti TV kanal i uvijek su vijesti. 📺☕",
    "Balkanski wifi lozinka: nešto poput 'qwerty1234'. 📶😂",
    "Kad igraš tablić i gledaš protivnikove karte u odrazu prozora. 🃏👁️",
    "Balkan letovanje: čekaš godinu dana, provedeš 7 dana, žališ se pola godine. 🌊😤",
    "Svaka balkanska mama reciklira plastične flaše u vazi. 🌺♻️",
    "Kad rjeknete 'ajde' a niko se ne miče. 🚶🗿",
    "Balkan shopping: ideš po jedno, vratiš se sa svime osim tog jednog. 🛍️😅",
]

MEME_STATE: dict = {}  # guild_id -> shuffled list of remaining indices

def get_next_meme(guild_id: int) -> str:
    key = str(guild_id)
    if key not in MEME_STATE or not MEME_STATE[key]:
        idxs = list(range(len(MEMES)))
        random.shuffle(idxs)
        MEME_STATE[key] = idxs
    return MEMES[MEME_STATE[key].pop()]

# ═══════════════════════════════════════════
#    VJEŠALA — rječnik
# ═══════════════════════════════════════════
VJASALA_RJECNIK = [
    "RAKIJA","CEVAPI","BALKON","KAFANA","MARKET","TRAKTOR","KOMSIJA","BONTON",
    "FUDBAL","PAPRIKA","BUREK","KAJMAK","SARMA","KIFLA","PEKARA","BAKLAVA",
    "KOMPJUTER","INTERNET","MOBITEL","PUNJAC","SLUSALICE","TASTATURA","MIŠKA",
    "PLANINA","JEZERO","RIJEKA","SUMSKA","LIVADA","VRELO","KLISURA","BRDOVIT",
    "LIJENOST","MUDROST","HRABROST","ZIVAHNA","BRZINA","TOPLINA","VESELJE",
    "BAKA","DJED","STRIC","UJNA","BRAT","SESTRA","MAJKA","OTAC","DIJETE",
    "KREVET","STOLICA","ORMAR","ZAVJESA","TEPIH","OGLEDALO","PROZOR","VRATA",
    "KOKOSOVO","JAGODA","MALINA","BOROVNICA","SMOKVA","SLJIVA","TRESNJA",
    "AUTOMOBIL","MOTOCIKL","BICIKL","AVION","BROD","VAGON","TRAMVAJ","METRO",
    "GITARA","VIOLINA","BUBNJEVI","FLAUTA","KLAVIR","HARMONIKA","SAKSOFON",
    "POLICAJAC","VATROGASAC","LJEKAR","UCITELJ","NOVINAR","ARHITEKT","INZENJER",
    "SUNCOKREO","RUZA","LAVANDA","KAKTUS","TULIPAN","JORGOVANA","MASLACAK",
    "OBLAK","MUNJA","GROM","SNIJEG","ROSA","MAGLA","VJETAR","OLUJA","DUGA",
    "LEPTIR","PCELICA","BUBAMARA","VJEVERICA","JELEN","LISICA","MEDVJED","VUK",
    "TORTA","KOLAC","KROFNA","PALACINKA","WAFFLE","BROWNIE","TIRAMISU","MACARON",
    "KUHINJA","KUPATILO","HODNIK","PODRUM","TAVAN","GARAZ","BALKON","TERASA",
    "SLOBODA","JEDNAKOST","LJUBAV","NADA","VJERA","SREĆA","ISTINA","PRAVDA",
    "GIMNASTIKA","PLIVANJE","ATLETIKA","KOSARKA","ODBOJKA","TENIS","SAHI","BOKS",
    "JANUAR","FEBRUAR","OKTOBAR","NOVEMBAR","DECEMBAR","SUBOTA","NEDJELJA",
    "DUGACAK","KRATAK","VISOK","NIZAK","DEBEO","MRSAV","BRZO","POLAKO","GLASNO",
]

VJASALA_FAZE = [
    "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```",
]

# ═══════════════════════════════════════════
#    KALADONT — RJEČNIK VALIDNIH RIJEČI (BHS)
#    Velika baza: imenice, glagoli, pridjevi, pojmovi.
#    Sve riječi u UPPERCASE bez dijakritika dvojnih (Š→S, Č→C, Ž→Z, Đ→DJ, Ć→C)
#    NORMALIZACIJA: korisničku riječ prebacujemo u UPPERCASE i mapiramo dijakritike.
# ═══════════════════════════════════════════
def _kaladont_normalize(w: str) -> str:
    """Normalizuj riječ: uppercase + skidanje dijakritika (Š→S, Č→C, Ž→Z, Đ→DJ, Ć→C)."""
    w = (w or "").upper().strip()
    repl = {"Š":"S","Č":"C","Ž":"Z","Đ":"DJ","Ć":"C","Ä":"A","Ö":"O","Ü":"U","Ñ":"N"}
    out = []
    for ch in w:
        out.append(repl.get(ch, ch))
    return "".join(out)

KALADONT_DICT = set([
    # === Hrana, piće, kuhinja ===
    "RAKIJA","CEVAPI","BUREK","KAJMAK","SARMA","KIFLA","PEKARA","BAKLAVA","PALACINKA",
    "TORTA","KOLAC","KROFNA","SLADOLED","KESTEN","ORAH","BADEM","LJESNJAK","KIKIRIKI",
    "JAGODA","MALINA","BOROVNICA","SMOKVA","SLJIVA","TRESNJA","JABUKA","KRUSKA","BANANA",
    "LIMUN","NARANCA","GROZDJE","LUBENICA","DINJA","BRESKVA","KAJSIJA","ANANAS","KIVI",
    "KRASTAVAC","PARADAJZ","KROMPIR","LUK","BIJELILUK","PAPRIKA","TIKVA","SPINAT","SALATA",
    "KARFIOL","BROKULA","KUPUS","REPA","ROTKVA","KELERABA","CESNJAK","GRAH","MAHUNE",
    "PASULJ","RIZA","TJESTENINA","HLEB","KRUH","LEPINJA","SOMUN","POGACA","PROJA",
    "KUKURUZ","PSENICA","JECAM","ZOB","RAZ","BRASNO","SECER","SOL","BIBER","VANILA",
    "CIMET","KAFA","CAJ","MLIJEKO","JOGURT","SIR","MASLAC","JAJE","MEDU","MED",
    "VINO","PIVO","SOK","VODA","LIMUNADA","KAKAO","COKOLADA","BOMBONA","DZEM","MARMELADA",
    "KOBASICA","SUNKA","SLANINA","BIFTEK","ROSTILJ","RIBA","TUNJEVINA","SARDINE","SKAMPI",
    "JUHA","COPRA","SUPA","CORBA","GULAS","PILAV","RIZOTO","LAZANJE","PIZZA","PASTA",
    # === Životinje ===
    "MACKA","PAS","KONJ","KRAVA","OVCA","KOZA","SVINJA","KOKOSKA","PETAO","PILE",
    "PATKA","GUSKA","CURKA","PURAN","ZEC","KUNIC","STAKOR","MIS","HRCAK","JEZ",
    "VJEVERICA","JELEN","SRNA","LISICA","VUK","MEDVJED","RIS","DABAR","JAZAVAC","TVOR",
    "LASICA","KUNA","NERC","TIGAR","LAV","LEOPARD","GEPARD","PANTER","PUMA","JAGUAR",
    "SLON","NOSOROG","NILSKI","ZIRAFA","ZEBRA","KAMILA","LAMA","ALPAKA","BIVOL","BIK",
    "MAJMUN","GORILA","SIMPANZA","ORANGUTAN","KENGUR","KOALA","PANDA","DELFIN","KIT",
    "MORSKIPAS","LOSOS","PASTRMKA","KARP","SARAN","SOM","STUKA","HARINGA","BAKALAR",
    "ORAO","SOKO","JASTREB","SOVA","GAVRAN","VRANA","SVRAKA","GOLUB","VRABAC","LASTAVICA",
    "PJEVAC","KOLIBRI","PINGVIN","NOJ","FLAMINGO","KOKOS","PAUN","TUKAN","PAPIGA",
    "ZMIJA","GUSTER","KORNJACA","KROKODIL","ALIGATOR","ZABA","PUNOGLAVAC","SALAMANDER",
    "PCELA","OSA","STRSLJEN","MRAV","BUBA","BUBAMARA","LEPTIR","MOLJAC","MUHA","KOMARAC",
    "PAUK","SKORPION","RAK","ROKER","OKTOPOD","LIGNJA","MEDUZA","KORAL","SKOLJKA","PUZ",
    # === Priroda ===
    "PLANINA","JEZERO","RIJEKA","POTOK","IZVOR","VRELO","KLISURA","KANJON","DOLINA",
    "POLJE","LIVADA","SUMA","SUMICA","GAJ","PARK","BAZEN","MORE","OCEAN","VAL",
    "PIJESAK","SLJUNAK","KAMEN","STIJENA","BRDO","HUM","POLUOTOK","OTOK","ATOL","UVALA",
    "OBALA","PLAZA","LAGUNA","MOCVARA","PUSTINJA","TUNDRA","GLECER","VULKAN","GEJZIR",
    "CVIJET","RUZA","TULIPAN","LJILJAN","KARANFIL","BOZUR","JORGOVAN","LAVANDA","KAKTUS",
    "MASLACAK","NEVEN","SUNCOKRET","PERUNIKA","VISIBABA","KAMILICA","METVICA","MAJCINA",
    "STABLO","DRVO","HRAST","BUKVA","JAVOR","BREZA","TOPOLA","JELA","BOR","SMRECA",
    "MASLINA","LIPA","KESTEN","BAGREM","PALMA","BAMBUS","PAPRAT","MAHOVINA","TRAVA",
    "SUNCE","MJESEC","ZVIJEZDA","PLANETA","KOMETA","METEOR","NEBO","OBLAK","KISA",
    "SNIJEG","LED","MAGLA","ROSA","INJE","MUNJA","GROM","OLUJA","DUGA","VJETAR",
    "PROLJECE","LJETO","JESEN","ZIMA","JUTRO","PODNE","VECE","NOC","PONOC","ZORA",
    # === Tijelo, ljudi ===
    "GLAVA","KOSA","CELO","OKO","NOS","USTA","JEZIK","ZUB","USNA","UHO",
    "VRAT","RAME","RUKA","SAKA","PRST","NOKAT","LAKAT","LEDJA","GRUDI","TRBUH",
    "NOGA","BUTINA","KOLJENO","STOPALO","PETA","KUK","KICMA","REBRO","SRCE","PLUCA",
    "ZELUDAC","JETRA","BUBREG","CRIJEVO","MOZAK","KOST","KOZA","KRV","ZIVAC","MISIC",
    "BAKA","DJED","STRIC","UJAK","TETKA","UJNA","BRAT","SESTRA","MAJKA","OTAC",
    "DIJETE","SIN","KCERKA","ROD","FAMILIJA","KOMSIJA","PRIJATELJ","DRUGAR","KOLEGA",
    "DJEVOJKA","MOMAK","ZENA","COVJEK","STARAC","BABA","BEBA","KLINAC","DJEVOJCICA","DJECAK",
    # === Profesije ===
    "POLICAJAC","VATROGASAC","LJEKAR","DOKTOR","UCITELJ","PROFESOR","NOVINAR","ARHITEKT",
    "INZENJER","PROGRAMER","PISAC","PJESNIK","SLIKAR","KIPAR","MUZICAR","GLUMAC","REZISER",
    "PJEVAC","PLESAC","FOTOGRAF","KUVAR","KONOBAR","PEKAR","MESAR","KROJAC","FRIZER",
    "ZUBAR","VETERINAR","FARMER","RIBAR","LOVAC","MORNAR","PILOT","VOZAC","SOFER","STUDENT",
    "GLUMICA","SUDIJA","ADVOKAT","TUZILAC","NOTAR","BANKAR","TRGOVAC","PRODAVAC","KASIRKA",
    # === Kuća, predmeti ===
    "KUHINJA","KUPATILO","HODNIK","PODRUM","TAVAN","GARAZA","BALKON","TERASA","DVORISTE",
    "VRATA","PROZOR","KROV","ZID","POD","STROP","STEPENICE","LIFT","HODNJAK","SOBA",
    "KREVET","STOLICA","STOL","ORMAR","KOMODA","FOTELJA","KAUC","ZAVJESA","TEPIH","SAG",
    "OGLEDALO","SLIKA","UKRAS","VAZA","SVIJECA","LAMPA","LUSTER","SAT","BUDILNIK","KALENDAR",
    "PEC","STEDNJAK","RERNA","FRIZIDER","ZAMRZIVAC","PERILICA","SUSILICA","TOSTER","BLENDER",
    "TANJUR","SOLJA","CASA","BOCA","TAVA","LONAC","NOZ","VILJUSKA","KASIKA","ZLICA",
    "TORBA","RANAC","KOFER","NOVCANIK","NAOCALE","KISOBRAN","KAPA","SAL","RUKAVICE","CARAPE",
    "MAJICA","KOSULJA","SAKO","JAKNA","KAPUT","HLACE","TRENERKA","SUKNJA","HALJINA","CIPELE",
    "PATIKE","CIZME","SANDALE","PAPUCE","KORZET","KAIS","KRAVATA","PIDZAMA","KUPACI","BIKINI",
    # === Tehnika ===
    "KOMPJUTER","RACUNAR","LAPTOP","TABLET","MOBITEL","TELEFON","INTERNET","WIFI","KABL","MODEM",
    "PUNJAC","BATERIJA","SLUSALICE","TASTATURA","MIS","KAMERA","FOTOAPARAT","TELEVIZOR","RADIO",
    "ZVUCNIK","MIKROFON","KONZOLA","DZOJSTIK","DRON","ROBOT","SERVER","DISPLEJ","EKRAN","MONITOR",
    # === Vozila ===
    "AUTOMOBIL","AUTO","KAMION","MOTOCIKL","BICIKL","ROMOBIL","SKUTER","TRAKTOR","BAGER","KOMBI",
    "AUTOBUS","TRAMVAJ","TROLEJBUS","METRO","VOZ","VLAK","BRZIVOZ","BROD","JAHTA","JEDRILICA",
    "CAMAC","KAJAK","KANU","SPLAV","PODMORNICA","AVION","HELIKOPTER","RAKETA","BALON","ZEPELIN",
    # === Geografija ===
    "DRZAVA","REPUBLIKA","GRAD","SELO","NASELJE","ULICA","TRG","PARK","MOST","TUNEL",
    "AUTOPUT","CESTA","PUT","STAZA","ZELJEZNICA","ASTANA","BEOGRAD","SARAJEVO","ZAGREB",
    "MOSTAR","SPLIT","RIJEKA","ZADAR","DUBROVNIK","PULA","NIS","SUBOTICA","TIRANA","SKOPLJE",
    "BANJALUKA","TUZLA","ZENICA","BIHAC","TREBINJE","JAJCE","BUGOJNO","TRAVNIK","KISELJAK","BREZA",
    "FRANCUSKA","NJEMACKA","ITALIJA","SPANIJA","ENGLESKA","RUSIJA","KINA","JAPAN","INDIJA","BRAZIL",
    "AMERIKA","MEKSIKO","KANADA","TURSKA","GRCKA","BUGARSKA","RUMUNIJA","MADJARSKA","POLJSKA","CESKA",
    "EUROPA","AZIJA","AFRIKA","AUSTRALIJA","ANTARKTIK","BALKAN","SREDOZEMLJE","JADRAN","DANUBIJ",
    # === Sport ===
    "FUDBAL","NOGOMET","KOSARKA","ODBOJKA","RUKOMET","TENIS","STOLNI","BOKS","KARATE","DZUDO",
    "HOKEJ","RAGBI","BEJZBOL","KRIKET","PLIVANJE","RONJENJE","JEDRENJE","VESLANJE","SKIJANJE",
    "SNOWBOARD","KLIZANJE","BICIKLIZAM","GIMNASTIKA","ATLETIKA","TRCANJE","SAH","DAMA","BILIJAR",
    "PIKADO","KUGLANJE","GOLF","JAHANJE","STRIJELJASTVO","PIANISTIKA","JOGGING","FITNESS",
    # === Muzika, umjetnost ===
    "GITARA","VIOLINA","BUBNJEVI","FLAUTA","KLAVIR","HARMONIKA","SAKSOFON","TRUBA","SAZ",
    "TAMBURA","MANDOLINA","UKULELE","KSILOFON","ORGULJE","SINTISAJZER","KLARINET","OBOJA",
    "FAGOT","CELO","KONTRABAS","HARFA","NOTA","PJESMA","STIH","AKORD","RIFF","RITAM","MELODIJA",
    "ROCK","POP","JAZZ","BLUES","FOLK","TURBOFOLK","NARODNJACI","RAP","HIPHOP","REGGAE","TECHNO",
    "OPERA","BALET","KAZALISTE","POZORISTE","KONCERT","FESTIVAL","SCENA","BINA","MIKROFON",
    # === Apstraktno, osjećanja ===
    "SLOBODA","JEDNAKOST","LJUBAV","NADA","VJERA","SRECA","TUGA","RADOST","STRAH","BIJES",
    "LJUTNJA","MIR","RAT","BORBA","POBJEDA","PORAZ","PRIJATELJSTVO","NEPRIJATELJ","ISTINA",
    "LAZ","PRAVDA","NEPRAVDA","HRABROST","KUKAVICA","MUDROST","GLUPOST","ZNANJE","UMIJECE",
    "TALENT","DAR","SUDBINA","SREĆA","PROBLEM","RJESENJE","ODGOVOR","PITANJE","IDEJA","PLAN",
    "SAN","SNOVI","MASTA","REALNOST","ZIVOT","SMRT","RODJENJE","PROSLOST","BUDUCNOST","SADASNJOST",
    # === Vrijeme ===
    "JANUAR","FEBRUAR","MART","APRIL","MAJ","JUNI","JULI","AVGUST","SEPTEMBAR","OKTOBAR",
    "NOVEMBAR","DECEMBAR","PONEDJELJAK","UTORAK","SRIJEDA","CETVRTAK","PETAK","SUBOTA","NEDJELJA",
    "DAN","SEDMICA","MJESEC","GODINA","DECENIJA","STOLJECE","MILENIJ","SAT","MINUTA","SEKUNDA",
    # === Boje ===
    "CRVENA","ZUTA","ZELENA","PLAVA","BIJELA","CRNA","SIVA","ROZE","NARANCASTA","LJUBICASTA",
    "BRAON","BORDO","BEZ","ZLATNA","SREBRNA","TIRKIZNA","TURKIZ","KAKI","INDIGO","KORALNA",
    # === Pridjevi (osnovni oblik) ===
    "DUGACAK","KRATAK","VISOK","NIZAK","DEBEO","MRSAV","BRZ","SPOR","JAK","SLAB",
    "TVRD","MEK","TOPAO","HLADAN","VRUC","LEDEN","SVIJETAO","TAMAN","PUN","PRAZAN",
    "STAR","MLAD","NOV","TEZAK","LAGAN","SKUP","JEFTIN","DOBAR","LOS","LIJEP",
    "RUZAN","PAMETAN","GLUP","HRABAR","STRASLJIV","BOGAT","SIROMAH","SRECAN","TUZAN","UMORAN",
    "BIJESAN","SMIJEAN","OZBILJAN","TIH","GLASAN","MIRAN","DIVLJI","PITOM","OPASAN","SIGURAN",
    # === Glagoli (infinitiv, kratki oblici) ===
    "RADITI","UCITI","CITATI","PISATI","CRTATI","SLIKATI","KUVATI","PECI","PRZITI","KUHATI",
    "JESTI","PITI","SPATI","BUDITI","TRCATI","HODATI","SETATI","PLIVATI","RONITI","LETJETI",
    "VOZITI","JAHATI","TRAZITI","GUBITI","NACI","DOBITI","DATI","UZETI","KUPITI","PRODATI",
    "PLATITI","ZARADITI","RACUNATI","BROJATI","MJERITI","VAGATI","PUSITI","GLEDATI","SLUSATI",
    "GOVORITI","SAPUTATI","VIKATI","PJEVATI","PLESATI","SVIRATI","POMOCI","VOLJETI","MRZJETI",
    "SMIJATI","PLAKATI","SPAVATI","SANJATI","RAZMISLJATI","OBJASNJAVATI","RAZUMJETI","ZNATI","UMJETI",
    # === Razni pojmovi ===
    "KARTA","NOVAC","BANKA","KASA","KREDIT","ZAJAM","KAMATA","POREZ","RACUN","FAKTURA",
    "UGOVOR","DOKUMENT","PEČAT","POTPIS","PISMO","KOVERTA","PAKET","POSILJKA","POSTA","KURIR",
    "SKOLA","FAKULTET","UCIONICA","TABLA","KREDA","SVESKA","KNJIGA","UDZBENIK","RJECNIK","ATLAS",
    "ZADATAK","TEST","ISPIT","DIPLOMA","OCJENA","ODGOJ","PRAVILO","ZAKON","KAZNA","NAGRADA",
    "BOLNICA","KLINIKA","AMBULANTA","HITNA","APOTEKA","LIJEK","TABLETA","INJEKCIJA","ZAVOJ","VAKCINA",
    "TRZNICA","PIJACA","DUCAN","PRODAVNICA","MARKET","CENTAR","TRZNI","BUTIK","KIOSK","BAZAR",
    "POZORNICA","SALA","KINO","BIOSKOP","MUZEJ","GALERIJA","BIBLIOTEKA","ARHIV","KATEDRALA","CRKVA",
    "DZAMIJA","SINAGOGA","HRAM","SAMOSTAN","MANASTIR","ZVONIK","MUNARA","OLTAR","IKONA","KRST",
    "GRAD","TVRDJAVA","KULA","DVORAC","PALACA","VILA","KOLIBA","CATRJA","STAN","KUCA",
    "FARMA","RANC","MLINI","STAJA","STAJSKA","KOKOSARNIK","KOSNICA","VOCNJAK","VINOGRAD","BASTA",
    # === Tehnologija, online ===
    "EMAIL","FORUM","BLOG","STRANICA","SAJT","LINK","KLIK","DOWNLOAD","UPLOAD","FAJL",
    "FOLDER","DATOTEKA","BACKUP","SOFTVER","PROGRAM","APLIKACIJA","KORISNIK","LOZINKA","PROFIL",
    "NALOG","RACUN","KOMENTAR","LAJK","DISLAJK","SHARE","POST","STORY","REELS","TIKTOK",
    # === Igre, zabava ===
    "IGRA","IGRACKA","LUTKA","KOCKA","PUZZLE","KARTA","TABLA","FIGURA","TOPIC","KONJ",
    "LOVAC","KRALJ","KRALJICA","PJEŠAK","TURNIR","LIGA","KUP","FINALE","POBJEDNIK","GUBITNIK",
    # === Specifične BHS riječi ===
    "MERAK","BERICET","INSAN","SEVDAH","SEVDALINKA","CARSIJA","BAHAR","BAHCIVAN","TESPIH","HAMAM",
    "KALDRMA","SOKAK","AVLIJA","CARDAK","CESMA","BUNAR","SOFRA","DZEZVA","FILDZAN","RAHAT",
    "BAKLAVA","TUFAHIJA","HURMASICE","REVANIJA","HALVA","SUDZUK","PASTRMA","CICVARA","UJSCAK",
    # === Nastavak — više riječi za bolju igrivost ===
    "ANANAS","ABDIJA","AUTOR","ATOM","ANTENA","ASPIRIN","ANGINA","ARMIJA","ARMATURA","AKCIJA",
    "ATLAS","ATOMSKI","ADRESA","AGENT","AHOJ","AKADEMIJA","AKORD","AKVARIJ","ALARM","ALGEBRA",
    "ALEJA","AMETIST","ANALIZA","ANGEO","ANJON","ANSAMBL","APARAT","APETIT","ARENA","ARHIV",
    "ATOMSKI","AUDIO","AURA","AVET","AVION","AVIS","AZBUKA","AZUR","ASOVAN","ATEIST",
    "BABILON","BACVA","BADANJ","BADEM","BAJONET","BAKAR","BALADA","BALAST","BALKON","BALOTA",
    "BAMBUS","BANANE","BARABA","BARAKA","BARJAK","BAROKNI","BARUT","BASIST","BATALJON","BATERIJA",
    "BELI","BENZIN","BICIKL","BIDE","BIFTEK","BIGAMIJA","BIKINI","BILBORD","BIMBAS","BIRO",
    "BISER","BISTRO","BITKA","BJEKSTVO","BLAGAJNA","BLAGOSLOV","BLATO","BLISTAV","BLITVA","BOLEST",
    "BOSANAC","BOTANIKA","BOTOX","BRADAVICA","BRAJIN","BRANIK","BRAVAR","BREZA","BRITVA","BROD",
    "BUBANJ","BUDISTA","BUDZET","BUKVAR","BUMERANG","BUSEN","BUVA",
    "CASTITI","CEDAR","CEDULJA","CENTAR","CESTAR","CIGLA","CILJ","CIMET","CINIK","CISTA",
    "CITRUS","COLA","CRTA","CRTEZ","CUNJ","CUPAVAC","CARLI","COKLA","CUREVI","CIRIL",
    "CADA","CALMA","CARAPA","CARDA","CESALJ","CIGRA","CILIM","CINEMA","CIPELE","CIVIJA",
    "DAJ","DALEKO","DARDA","DARILO","DASKA","DAVID","DEBELA","DEFTER","DELFIN","DESET",
    "DIJAGONALA","DIPLOMA","DIVAN","DIVAS","DIVOT","DJEVOJKA","DOBOS","DODIR","DOJAVA","DOLAR",
    "DOMAR","DOMETI","DRAMA","DRENA","DRSKO","DRVO","DUGA","DUKAT","DUVAR","DZIN",
    "EBOLA","EDEN","EGIPAT","EHO","EKIPA","EKLER","EKRAN","ELASTIK","ELEMENT","EMAJL",
    "EPIZODA","ERA","ESEJ","ESKIM","ETAPA","ETIKETA","EVROPA",
    "FAJL","FAKIR","FALANGA","FARMA","FAUNA","FAZA","FAZON","FELERAN","FESTIVAL","FIGURA",
    "FIJASKO","FILDZAN","FILM","FILTER","FINALE","FIRMA","FISKAL","FLOKA","FLOTA","FOAJE",
    "FOKA","FOND","FORUM","FREJM","FUGA",
    "GALEB","GALIJA","GAMA","GARDA","GARNIR","GASTRO","GAZAP","GAZDA","GENIJ","GIBAK",
    "GIROS","GLAS","GLAVA","GLINA","GLODAR","GLUMAC","GMAZ","GOLOB","GORAN","GORJE",
    "GRABLJE","GRAD","GRAH","GRANA","GREDA","GROB","GROZD","GRUDI","GUSTERA","GUMA",
    "HALDA","HALJINA","HARFA","HARING","HEROJ","HIDRA","HIDROAVION","HILJADA","HIPNOZA","HISTORIJA",
    "HLAD","HOBI","HODAC","HORIZONT","HORMON","HRAM","HRAST","HRPA","HUMOR","HVALA",
    "IGLA","IGRA","ILUZIJA","IMITATOR","INGOT","INJE","INKA","INSEKT","INTERVJU","ISKRA",
    "ISTOK","IZLAZ","IZMET","IZVAN","IZVOR",
    "JAGNJE","JAJE","JANJE","JARAC","JARAK","JARGON","JASIKA","JAVNOST","JEDAN","JEDINKA",
    "JELEN","JEZIK","JOGA","JOGURT","JORGAN","JUG","JUHA","JUNAK","JURNJAVA",
    "KABAO","KADET","KAFANA","KAJAK","KAKAO","KALAJ","KALDRMA","KALORIJA","KAMEN","KAMPER",
    "KAPETAN","KARMIN","KARNEVAL","KARTA","KASA","KASETA","KASKO","KESTEN","KEVA","KIFLA",
    "KILIM","KINEZ","KIPAR","KIRO","KISELO","KIT","KLATNO","KLAVIR","KLIN","KLISURA",
    "KLOPKA","KLUB","KNEZ","KNJIGA","KOBASICA","KOFER","KOKA","KOKOS","KOLAC","KOLIBA",
    "KOMAR","KOMODA","KONJUSAR","KONOP","KORAK","KORAL","KORICE","KORPA","KOSA","KOSNICA",
    "KOST","KOSTIM","KOSULJA","KOTAR","KRAJ","KRALJ","KRASTAVAC","KRATER","KRESIVO","KRIZA",
    "KROV","KRPA","KRUH","KRUNA","KRZNO","KUFER","KUGLA","KUMA","KUPA","KUPATILO",
    "LAJAVAC","LAKAT","LAMPA","LANAC","LATICA","LAVOR","LEDENJAK","LEGENDA","LEPTIR","LIBELA",
    "LIDER","LIFER","LIK","LILJAN","LIMUN","LIPA","LISICA","LJEKARNA","LJEPILO","LJESA",
    "LJESNJAK","LJULJASKA","LOGOR","LOKVA","LONAC","LOPATA","LOPOV","LOZA","LUBENICA","LUDARA",
    "LULA","LUNA","LUPA","LUSTER",
    "MACETA","MAFIN","MAGIJA","MAGLA","MAJKA","MAKARONI","MALINA","MAMA","MAMUT","MARAMA",
    "MARATON","MARGARIN","MARKA","MARMELADA","MARTINI","MASAZA","MASKA","MASLINA","MATERIJA","MEDIJ",
    "MEDONOSA","MEDUZA","MELEM","MEN","MERAK","METAR","METLA","MIRIS","MISLI","MITRALJEZ",
    "MJERA","MOC","MODA","MOJA","MOLBA","MORE","MOST","MOTAR","MOTIV","MOZAIK",
    "MUFLON","MUKA","MUMIJA","MUNJA","MUTA","MUZEJ",
    "NABOJ","NACRT","NAFTA","NAJLON","NAKIT","NAOCALE","NAPAD","NAPOJ","NAPOR","NARAVAN",
    "NAREDBA","NAROD","NASLJEDNIK","NAUKA","NEBO","NEDA","NEMIR","NERAST","NESTASIK","NEUTRON",
    "NEVRIJEME","NIDAS","NIKAD","NIMFA","NIVO","NOC","NOGA","NOTA","NOVAC","NOVCANIK",
    "OAZA","OBALA","OBARAC","OBLAK","OBLIK","OBROK","OBRT","OCJENA","ODGOJ","ODOBOR",
    "ODORA","OGANJ","OGRADA","OKO","OKLOP","OLIMP","OLOVKA","OPATICA","OPTIKA","ORAH",
    "ORAO","ORBIT","ORDEN","ORGAN","ORLOVI","ORMAN","OROMIR","OSAM","OSIGURAC","OSJET",
    "OSMIJEH","OTAC","OTOK","OZIBAC",
    "PAJAC","PAKET","PALAC","PALACA","PALACINKA","PALETA","PAMUK","PAPIR","PAPUC","PARTIJA",
    "PASKVIL","PASOS","PASTA","PASTIR","PAUK","PAUZA","PCELA","PECINA","PEHAR","PERIVOJ",
    "PERLA","PERSPEKTIVA","PESMA","PIANIST","PICA","PIDZAMA","PIJUK","PILA","PILOT","PIPA",
    "PISMO","PJEGA","PLAFON","PLAKAT","PLAN","PLATA","PLATFORMA","PLAVUSA","PLEMSTVO","PLIN",
    "PLOCA","PODNOZJE","POEZIJA","POJAS","POKER","POLE","POLITIKA","POLJANA","POMOC","PONOC",
    "POROD","POSAO","POSLOVI","POSTUDA","POVRCE","POZIV","PRASAK","PRAVDA","PREDAK","PREDSJEDNIK",
    "PREGRADA","PREPAD","PREPRJEK","PRES","PRIBOR","PRIVOZNIK","PROGRAM","PROLOM","PROSAC","PRSTEN",
    "PSALAM","PUDING","PUNJAC",
    "RACA","RACUN","RADIJA","RAJ","RAKIJA","RAKOVI","RAMA","RANAC","RAT","RATAR",
    "RAVAN","RAZBORIT","RAZUM","REKA","REPLIKA","REZIJA","RIBA","RIJEC","RIKVERC","RIMA",
    "RISTO","RIZA","ROBA","ROBOT","RODA","RODBINA","RODOSLOV","ROK","ROMOR","ROVAS",
    "RUPA","RUTINA","RUZA",
    "SABOR","SAJAM","SAKO","SALATA","SALON","SAMAC","SAMUR","SAN","SANJAR","SANJKE",
    "SAPUN","SARAJ","SARGO","SARMA","SAT","SAVA","SAVJET","SAVRSEN","SCENA","SCIT",
    "SECER","SEDLO","SELO","SEMAFOR","SEPTUNA","SESTRA","SEVDAH","SEZONA","SIDRO","SIJALICA",
    "SIJEDA","SIKIRA","SILAZAK","SIMFONIJA","SIMPATIJA","SINOC","SIROMAH","SIROVI","SISTEM","SITAN",
    "SITNICA","SJAJ","SJEME","SJENA","SKALA","SKICA","SKLAP","SKOLA","SKULPTURA","SLATKO",
    "SLIKAR","SLOBODA","SLON","SLUSALICE","SMOKVA","SNAJPER","SOFER","SOK","SOL","SOLI",
    "SOMUN","SOSO","SPARTA","SPEKTAR","SPLAV","SPOMENIK","SPORT","SPREJ","SREDISTE","STADION",
    "STAJA","STAKA","STALAK","STAN","STAPSKI","STARAC","STARINA","STAZA","STEPENICE","STIH",
    "STOKA","STOL","STOLAR","STRAH","STRELA","STRIJELA","STROJ","STUDENT","SUDIJA","SUMA",
    "SUNCE","SVIJET","SVJETLO",
    "TABLA","TANJUR","TARAKAN","TARABA","TASNA","TAVA","TEKO","TELEFON","TELEVIZOR","TEMA",
    "TENISER","TEORIJA","TEPIH","TEREN","TERMIT","TIGAR","TIKVA","TINEJDZER","TIPKA","TIRKIZ",
    "TKANINA","TLOCRT","TOCAK","TOPLOMJER","TOPOR","TORBA","TORTA","TORZO","TRAGAC","TRAKA",
    "TRAKTOR","TRAVA","TREN","TRENER","TRG","TRGOVAC","TRIBUNA","TRKA","TROFEJ","TRUBA",
    "TRUP","TUFNA","TUGA","TULIPAN","TUNA","TURPIJA",
    "UDOVAC","UJAK","UJEDINJENA","UKRAS","ULICA","ULOVAR","UMOR","UMOR","UPALA","URAGAN",
    "URAR","UROK","USPJEH","USPON","USTAJANJE","UTOR","UZBUNA",
    "VAGA","VAGON","VAKCINA","VALOVI","VANJA","VARNICA","VARTILO","VATRA","VEKER","VENTIL",
    "VESELJE","VIDIK","VIGOR","VIJORI","VIKTORIJA","VILA","VILJUSKA","VINO","VIORI","VITAMIN",
    "VITEZ","VITRINA","VJEDRO","VJENCANJE","VJESTAK","VJEVERICA","VLAK","VOCNJAK","VODA","VOJNIK",
    "VOLAN","VRABAC","VRH","VRHUNAC","VRT","VUCJAK","VULKAN",
    "ZADATAK","ZADNJAK","ZAGRLJAJ","ZAJC","ZAKLON","ZAKON","ZAMOR","ZANIMANJE","ZAOBILAZAK","ZAPIS",
    "ZAPLET","ZARADA","ZASEDA","ZASIK","ZASLON","ZAVISA","ZAVOJ","ZBIRKA","ZDRAVO","ZEC",
    "ZELENI","ZEMLJA","ZGRADA","ZID","ZIMA","ZIVOT","ZLATO","ZMAJ","ZMIJA","ZNAK",
    "ZOLJA","ZORA","ZRAK","ZRNO","ZUB","ZVUK",
    # === Dodatne kratke 3-4 slovne riječi ===
    "BOG","DOM","DAR","SAN","JAJ","RAJ","ČAJ","ROJ","BOJ","BOJA","BOL","BOLI","BOR","BUS",
    "CAR","CIK","DAH","DAB","DAR","DJED","FEN","GAS","GRB","GRM","HOR","HUM","IGO","ILI",
    "JAJE","JAK","JAR","KAD","KAJ","KAP","KIT","KOM","KOS","KOZA","LAV","LEK","LET","LED",
    "LIK","LIM","LIN","LOM","LOV","LUK","MAH","MAK","MAJ","MIR","MOR","MOST","NEK","NIT",
    "NOC","NOJ","NOS","ORO","OBL","OKO","OPA","OSA","PAS","PAR","PAT","PIR","POD","POJ",
    "POP","POT","PUH","PUT","RAD","RAJ","RAP","RAT","RED","REP","REZ","RIM","ROD","ROK",
    "ROM","ROZ","RUB","RUC","SAJ","SAN","SAP","SAT","SLON","SOK","SON","SOR","STO","SUD",
    "SUH","SUR","SVE","TAJ","TAN","TAS","TIH","TIK","TIM","TIP","TON","TUR","UAL","UKA",
    "ULJ","UMI","UVA","VAL","VAR","VAS","VEC","VEK","VID","VIK","VIR","VOD","VOL","VOZ",
    "VRH","VUK","ZID","ZIK","ZIM","ZNA","ZOR","ZUB","ZUM","ZID","ZIV",
    # === Magicna rijec ===
    "KALADONT",
])

# ── KALADONT — laka pravila: BLOKIRAMO SAMO IMENA i nemoguće završetke ──
# Korisnik je tražio: NEMA strogog rječnika.
#   • blokiraj imena (lista najčešćih balkanskih imena)
#   • blokiraj završetke koji nemaju nastavak (KT, QU, MK, NJ, GH, ZH, MJ, NJ, BJ)
#   • SVE OSTALO PROLAZI (nema više "nije u rječniku" greške)
KALADONT_NAMES = set([
    # muška
    "MARKO","IVAN","STEFAN","NIKOLA","PETAR","LUKA","FILIP","DUSAN","MIHAJLO","MILOS",
    "ALEKSA","LAZAR","DJORDJE","BORIS","DAVID","DANIEL","NEMANJA","UROS","STRAHINJA",
    "VUK","RADOMIR","BRANIMIR","MILAN","BOJAN","ZORAN","DRAGAN","GORAN","SLAVKO",
    "MILOVAN","RANKO","ZELJKO","MLADEN","NENAD","SASA","PREDRAG","DRAGOMIR","NEBOJSA",
    "EMIR","HARIS","FARUK","ADNAN","KENAN","TARIK","AMAR","DENIS","ARMIN","HAMZA",
    "MUHAMED","MUHAMMAD","ALMIR","ELVIS","EDIN","ENES","SEMIR","SENAD","DAMIR","NEDIM",
    "SAMIR","MIRZA","MIRSAD","FUAD","DZENAN","HARUN","BAKIR","SULEJMAN","IBRAHIM",
    "AMER","JASMIN","SEAD","KEMAL","DARKO","DALIBOR","DRAZEN","NIKOLINA","TIN","IVO",
    "IGOR","TOMA","MATE","MATEJ","MATEO","ANTE","JOSIP","ANDRIJA","HRVOJE","MISLAV",
    "DOMAGOJ","ZVONIMIR","BORNA","LOVRO","KRESIMIR","SINISA","RAJKO",
    # ženska
    "ANA","MARIJA","JELENA","MILICA","TIJANA","TAMARA","SANJA","JOVANA","KATARINA",
    "ANDJELA","ANDREJA","ANDREA","SARA","NADJA","SELMA","HANA","MELISA","AMINA",
    "LEJLA","EMINA","ALMA","MEDINA","ELMA","LAMIJA","DZENANA","MERIMA","IVANA",
    "MARIJANA","BILJANA","SNEZANA","DANIJELA","DRAGANA","GORDANA","SLOBODANKA",
    "DJURDJA","DJURDJICA","SLAVICA","MILENA","NEVENA","DUNJA","TEODORA","ELENA",
    "VESNA","JASMINA","JADRANKA","BOSILJKA","MARTA","NIKA","LANA","MIA","NORA",
    "EMA","DORA","PETRA","IVA","MAJA","LUCIJA","KARMELA","KLARA","MATEJA","ROZA",
    "TINA","ANJA","KIKO","DANNY","ALEKSA","YUGO","GIAN",
])

KALADONT_BAD_END = ("KT","QU","MK","NJ","GH","ZH","MJ","BJ","CJ","FJ","HJ","KJ","LJ","NJ","PJ","SJ","TJ","VJ","ZJ")

# ── 50/50 sistem — poruke kada sudbina odbije valjanu riječ ──────────────
KALADONT_50_FAIL = [
    "😈 Sudbina je rekla **NE**! Pokušaj ponovo.",
    "💀 Sreća te napustila ovaj put! Pokušaj drugu.",
    "🎲 Kocka nije bila na tvojoj strani! (50% šansa te ubila)",
    "🌪️ Vjetar sudbine te odnio! Probaj opet.",
    "⚡ Grom te udario! Tvoja riječ propala zbog nesreće.",
    "🃏 Džoker je rekao NE! Sudbina odlučuje ovdje.",
    "🌑 Crna mačka prešla put! Probaj drugu riječ.",
    "☠️ Loša energija! Tvoja riječ bila je ispravna, ali sreća te izdala.",
    "🎭 Drama sudbine — ispravna riječ, ali nemaš sreće danas!",
    "🔮 Kristalna kugla je rekla NE! (50/50 sistem udario)",
]

def kaladont_word_valid(word: str):
    """Vraća (ok, razlog). NE provjeravamo rječnik — samo imena i nemoguće završetke."""
    nw = _kaladont_normalize(word)
    if nw == "KALADONT":
        return True, ""
    if nw in KALADONT_NAMES:
        return False, "ime"
    # provjera završetka — uzima zadnja 2 slova
    if len(nw) >= 2 and nw[-2:] in KALADONT_BAD_END:
        return False, "kraj"
    return True, ""

def get_kaladont_hint(req: str, used: set) -> list:
    """Vrati do 4 primjera riječi iz baze koje počinju sa req i nisu još korištene."""
    req_up = req.upper()
    candidates = [w for w in KALADONT_DICT if w.startswith(req_up) and w not in used and w != "KALADONT"]
    random.shuffle(candidates)
    return candidates[:4]

# ═══════════════════════════════════════════
#    INTENTS & BOT
# ═══════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True  # potrebno za /vanity (čitanje custom statusa)
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ═══════════════════════════════════════════
#    PREFIX BRIDGE — .kpm radi kao /kpm
# ═══════════════════════════════════════════
class _FakeResponse:
    def __init__(self, fake): self.fake = fake; self._sent = False
    async def send_message(self, content=None, *, embed=None, embeds=None, view=None, ephemeral=False, **kw):
        kwargs = {}
        if content is not None: kwargs["content"] = content
        if embed is not None: kwargs["embed"] = embed
        if embeds is not None: kwargs["embeds"] = embeds
        if view is not None: kwargs["view"] = view
        cmd_name = (self.fake.message.content[1:].split(maxsplit=1)[0].lower() if self.fake.message.content.startswith(".") else "")
        if ephemeral and cmd_name == "help":
            try:
                msg = await self.fake.user.send(**kwargs)
                try: await self.fake.message.add_reaction("📬")
                except: pass
                self.fake._original = msg; self._sent = True
                return msg
            except: pass
        if ephemeral:
            kwargs["delete_after"] = 10
        msg = await self.fake.channel.send(**kwargs)
        self.fake._original = msg; self._sent = True
        return msg
    async def defer(self, ephemeral=False, thinking=False): self._sent = True
    async def edit_message(self, **kw):
        try: await self.fake._original.edit(**{k:v for k,v in kw.items() if v is not None})
        except: pass
    def is_done(self): return self._sent

class _FakeFollowup:
    def __init__(self, fake): self.fake = fake
    async def send(self, content=None, *, embed=None, embeds=None, view=None, ephemeral=False, **kw):
        kwargs = {}
        if content is not None: kwargs["content"] = content
        if embed is not None: kwargs["embed"] = embed
        if embeds is not None: kwargs["embeds"] = embeds
        if view is not None: kwargs["view"] = view
        cmd_name = (self.fake.message.content[1:].split(maxsplit=1)[0].lower() if self.fake.message.content.startswith(".") else "")
        if ephemeral and cmd_name == "help":
            try: return await self.fake.user.send(**kwargs)
            except: pass
        if ephemeral:
            kwargs["delete_after"] = 10
        return await self.fake.channel.send(**kwargs)

class FakeInteraction:
    def __init__(self, message):
        self.user = message.author
        self.channel = message.channel
        self.guild = message.guild
        self.message = message
        self.client = bot
        self.command = None
        self._original = None
        self._response = _FakeResponse(self)
        self._followup = _FakeFollowup(self)
    @property
    def response(self): return self._response
    @property
    def followup(self): return self._followup
    @property
    def channel_id(self): return self.channel.id
    @property
    def guild_id(self): return self.guild.id if self.guild else None
    async def original_response(self): return self._original

def _parse_member(text, guild):
    text = text.strip()
    if not text: return None
    m = re.match(r"<@!?(\d+)>", text)
    if m:
        return guild.get_member(int(m.group(1)))
    if text.isdigit():
        return guild.get_member(int(text))
    text_low = text.lower()
    for mem in guild.members:
        if mem.name.lower() == text_low or mem.display_name.lower() == text_low:
            return mem
    for mem in guild.members:
        if text_low in mem.name.lower() or text_low in mem.display_name.lower():
            return mem
    return None

def _parse_role(text, guild):
    text = text.strip()
    m = re.match(r"<@&(\d+)>", text)
    if m: return guild.get_role(int(m.group(1)))
    if text.isdigit(): return guild.get_role(int(text))
    for r in guild.roles:
        if r.name.lower() == text.lower(): return r
    return None

def _parse_channel(text, guild):
    text = text.strip()
    m = re.match(r"<#(\d+)>", text)
    if m: return guild.get_channel(int(m.group(1)))
    if text.isdigit(): return guild.get_channel(int(text))
    for c in guild.channels:
        if c.name.lower() == text.lower(): return c
    return None

# ═══════════════════════════════════════════
#    KANAL PRAVILA — gdje koja igra/komanda smije
# ═══════════════════════════════════════════
# Format: "ime_komande": "dio_imena_kanala_gdje_smije"
CHANNEL_RULES = {
    # Igre
    "kaladont": "kaladont", "kaladont-stop": "kaladont",
    "vjasala": "vješalo",  # ili "vjesalo"
    "kpm": "kamen-papir",
    "kviz": "kviz",
    "geografija": "geografija",
    "toplo-hladno": "geografija",
    "amogus": "among-us", "amogus-stop": "among-us",
    # Casino
    "blackjack": "casino", "slots": "casino", "rulet": "casino",
    "kocka": "casino", "kradi": "casino",
    "bingo": "casino",
    # Ekonomija
    "baki": "economics", "posao": "economics", "daily": "economics",
    "daj": "economics", "shop": "economics", "kupi": "economics",
    "bank": "economics", "lottery": "economics", "heist": "economics",
    "quests": "economics", "rank": "economics", "leaderboard": "economics",
    # Brojanje
    # (auto, brojanje ima svoj kanal kroz cnt_cfg)
    # Ljubavne
    "zagrljaj": "zagrljaji", "poljubac": "zagrljaji", "mazi": "zagrljaji",
    "srce": "zagrljaji", "high5": "zagrljaji", "tapsi": "zagrljaji",
    "cudan": "zagrljaji", "pocetkaj": "zagrljaji", "curse": "zagrljaji",
    # Fun
    "meme": "zabava",
}
# Ove komande RADE SVUDA (ne ograničavamo)
CMDS_ANYWHERE = {
    "ping", "help", "serverinfo", "userinfo", "avatar", "invite", "spotify",
    "qr", "remind", "birthday", "afk", "topchatters",
    "say", "poll", "confess", "report", "tiketstaff", "tiket", "pravila", "warn", "warnings",
    "clearwarnings", "ban", "kick", "timeout", "clear",
    # setup
    "setup", "setup-roles", "setup-welcome", "setup-leave", "setup-autorole",
    "setup-log", "setup-starboard", "setup-levelrole", "setup-birthday",
    "setup-panels", "ticket-setup", "brojanje-postavi", "brojanje-info",
    "brojanje-reset", "setname", "setavatar", "setchannel", "sort-roles",
    "server-config", "vatrice", "tiketstaff",
}

# Kanali u kojima SVE komande rade (slobodne zone)
FREE_CHANNELS = ["comanda", "komanda", "komande", "giveaways", "events", "bot-spam", "bot-commands"]

def check_channel_rule(channel, cmd_name: str):
    """Vrati None ako smije, ili ime potrebnog kanala ako ne smije."""
    ch_name = (channel.name or "").lower()
    # Slobodne zone — sve smije
    if any(fc in ch_name for fc in FREE_CHANNELS): return None
    if cmd_name in CMDS_ANYWHERE: return None
    needed = CHANNEL_RULES.get(cmd_name)
    if not needed: return None  # nije ograničena
    if needed.lower() in ch_name: return None  # OK
    return needed

def _extract_string_options(options: list) -> list[str]:
    """Rekurzivno izvuci sve string vrijednosti iz slash komande opcija."""
    result = []
    for opt in options or []:
        if not isinstance(opt, dict): continue
        if opt.get("type") == 3:  # type 3 = STRING u Discord API
            result.append(str(opt.get("value", "")))
        result.extend(_extract_string_options(opt.get("options", [])))
    return result

async def _global_channel_check(interaction: discord.Interaction) -> bool:
    if not interaction.guild or not interaction.command: return True

    # ── Anti-Invite u slash komandama (PRIJE admin bypass-a — vrijedi za sve osim OWNERa) ──
    # Provjeri sve string parametre koje korisnik upiše u komandu
    try:
        if interaction.user.id not in OWNER_IDS:
            opts = _extract_string_options((interaction.data or {}).get("options", []))
            for val in opts:
                if INVITE_REGEX.search(val):
                    await interaction.response.send_message(
                        embed=em("🚫 Reklama zabranjena",
                                 f"{interaction.user.mention} — invite linkovi nisu dozvoljeni ni u komandama!",
                                 color=COLORS["error"]),
                        ephemeral=True
                    )
                    return False
    except: pass

    # admini i vlasnik smiju svuda (channel rule bypass)
    try:
        if interaction.user.guild_permissions.administrator: return True
    except: return True

    needed = check_channel_rule(interaction.channel, interaction.command.name)
    if needed is None: return True
    target = discord.utils.find(lambda c: needed.lower() in c.name.lower(), interaction.guild.text_channels)
    msg = f"❌ **Ova komanda nije za ovaj kanal!**\n➡️ Koristi je u {target.mention if target else f'#{needed}'}"
    try:
        await interaction.response.send_message(embed=em("🚫 Pogrešan kanal", msg, color=COLORS["warning"]), ephemeral=True)
    except: pass
    return False

bot.tree.interaction_check = _global_channel_check

async def try_prefix_command(message):
    """Returns True if a .command was found and executed."""
    content = message.content.strip()
    if not content.startswith("."): return False
    if len(content) < 2 or content[1] in (" ", ".", "/"): return False
    parts = content[1:].split(maxsplit=1)
    cmd_name = parts[0].lower()
    args_text = parts[1] if len(parts) > 1 else ""
    PREFIX_ALIASES = {"i": "invite", "inv": "invite", "h": "help", "p": "ping", "lb": "leaderboard", "np": "spotify", "sp": "spotify",  "tc": "topchatters", "top": "topchatters", "b": "bank", "lot": "lottery", "r": "remind", "qrcode": "qr"}
    cmd_name = PREFIX_ALIASES.get(cmd_name, cmd_name)
    cmd = bot.tree.get_command(cmd_name)
    if cmd is None: return False
    # Kanal pravila
    if not message.author.guild_permissions.administrator:
        needed = check_channel_rule(message.channel, cmd_name)
        if needed:
            target = discord.utils.find(lambda c: needed.lower() in c.name.lower(), message.guild.text_channels)
            await message.channel.send(
                embed=em("🚫 Pogrešan kanal", f"❌ {message.author.mention} — **ova komanda nije za ovaj kanal!**\n➡️ Idi u {target.mention if target else f'#{needed}'}", color=COLORS["warning"]),
                delete_after=10
            )
            try: await message.delete()
            except: pass
            return True
    # ── Anti-Invite u prefix komandama (.poll, .say, ...) ──
    if message.author.id not in OWNER_IDS and INVITE_REGEX.search(args_text or ""):
        try:
            await message.delete()
        except: pass
        await message.channel.send(
            embed=em("🚫 Reklama zabranjena",
                     f"{message.author.mention} — invite linkovi nisu dozvoljeni ni u komandama!",
                     color=COLORS["error"]),
            delete_after=8
        )
        return True

    fake = FakeInteraction(message)
    kwargs = {}
    try:
        params = list(cmd.parameters) if hasattr(cmd, "parameters") else []
        remaining = args_text
        for idx, p in enumerate(params):
            ptype = getattr(p.type, "name", str(p.type)).lower()
            is_last = (idx == len(params) - 1)
            if not remaining and not p.required:
                continue
            if not remaining and p.required:
                await message.channel.send(embed=em("❌", f"Fali argument: `{p.name}`. Probaj sa `/` umjesto `.` za pomoć.", color=COLORS["error"]), delete_after=8)
                return True
            if "user" in ptype or "member" in ptype:
                token, _, rest = remaining.partition(" ")
                mem = _parse_member(token, message.guild)
                if mem is None:
                    await message.channel.send(embed=em("❌", f"Korisnik nije pronađen: `{token}`", color=COLORS["error"]), delete_after=6)
                    return True
                kwargs[p.name] = mem
                remaining = rest.strip()
            elif "role" in ptype:
                token, _, rest = remaining.partition(" ")
                r = _parse_role(token, message.guild)
                if r is None:
                    await message.channel.send(embed=em("❌", f"Uloga nije pronađena: `{token}`", color=COLORS["error"]), delete_after=6)
                    return True
                kwargs[p.name] = r
                remaining = rest.strip()
            elif "channel" in ptype:
                token, _, rest = remaining.partition(" ")
                ch = _parse_channel(token, message.guild)
                if ch is None:
                    await message.channel.send(embed=em("❌", f"Kanal nije pronađen: `{token}`", color=COLORS["error"]), delete_after=6)
                    return True
                kwargs[p.name] = ch
                remaining = rest.strip()
            elif "integer" in ptype or "int" in ptype:
                token, _, rest = remaining.partition(" ")
                try: kwargs[p.name] = int(token)
                except ValueError:
                    await message.channel.send(embed=em("❌", f"`{p.name}` mora biti broj. Dao si: `{token}`", color=COLORS["error"]), delete_after=6)
                    return True
                remaining = rest.strip()
            elif "number" in ptype or "float" in ptype:
                token, _, rest = remaining.partition(" ")
                try: kwargs[p.name] = float(token)
                except ValueError:
                    await message.channel.send(embed=em("❌", f"`{p.name}` mora biti broj.", color=COLORS["error"]), delete_after=6)
                    return True
                remaining = rest.strip()
            elif "boolean" in ptype or "bool" in ptype:
                token, _, rest = remaining.partition(" ")
                kwargs[p.name] = token.lower() in ("da","yes","true","1","on")
                remaining = rest.strip()
            else:  # string
                if is_last:
                    kwargs[p.name] = remaining
                    remaining = ""
                else:
                    token, _, rest = remaining.partition(" ")
                    kwargs[p.name] = token
                    remaining = rest.strip()
        await cmd.callback(fake, **kwargs)
    except app_commands.CommandOnCooldown as e:
        await message.channel.send(embed=em("⏱️ Cooldown", f"Probaj ponovo za `{int(e.retry_after)}s`", color=COLORS["warning"]), delete_after=6)
    except Exception as e:
        await message.channel.send(embed=em("❌ Greška", f"`{type(e).__name__}`: {str(e)[:200]}\n\n💡 Probaj sa `/{cmd_name}` umjesto `.{cmd_name}`", color=COLORS["error"]), delete_after=10)
        print(f"[prefix bridge] {cmd_name}: {e}")
    return True

# ═══════════════════════════════════════════
#    PODACI
# ═══════════════════════════════════════════
import os as _os
_DATA_DIR = "/app/data" if _os.path.isdir("/app/data") else "."
try: _os.makedirs(_DATA_DIR, exist_ok=True)
except: _DATA_DIR = "."
DATA_FILE = _os.path.join(_DATA_DIR, "oleun_data.json")
if not _os.path.exists(DATA_FILE) and _os.path.exists("oleun_data.json"):
    try:
        import shutil as _sh
        _sh.copy("oleun_data.json", DATA_FILE)
        print(f"[migracija] Kopiran oleun_data.json → {DATA_FILE}")
    except Exception as _e: print(f"[migracija] {_e}")
print(f"[storage] DATA_FILE = {DATA_FILE}")
data = {"economy": {}, "xp": {}, "warnings": {}, "zoo": {}, "quests": {}, "selfroles": {},
        "guild_config": {}, "afk": {}, "birthdays": {}, "starboard_done": {}, "counting": {},
        "msg_count": {}, "invites": {}, "invite_uses": {},
        "money": {}, "bank": {}, "lottery": {"pot": 0, "tickets": {}, "last_draw": 0},
        "heist_cooldown": {}, "reminders": [], "confess_count": 0,
        "cmd_uses": {}, "private_voices": {}, "pvc_info_posted": False,
        "msg_count_week": {}, "aotw_last": None,
        "ban_allowed_ids": [],
        "poo": {},
        "poo_tasks": {}}

def load_data():
    global data
    try:
      if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            data["economy"]        = loaded.get("economy", {})
            data["xp"]             = loaded.get("xp", {})
            data["warnings"]       = loaded.get("warnings", {})
            data["zoo"]            = loaded.get("zoo", {})
            data["quests"]         = loaded.get("quests", {})
            data["selfroles"]      = loaded.get("selfroles", {})
            data["guild_config"]   = loaded.get("guild_config", {})
            data["afk"]            = loaded.get("afk", {})
            data["birthdays"]      = loaded.get("birthdays", {})
            data["starboard_done"] = loaded.get("starboard_done", {})
            data["msg_count"]      = loaded.get("msg_count", {})
            data["invites"]        = loaded.get("invites", {})
            data["invite_uses"]    = loaded.get("invite_uses", {})
            data["money"]          = loaded.get("money", {})
            data["bank"]           = loaded.get("bank", {})
            data["lottery"]        = loaded.get("lottery", {"pot": 0, "tickets": {}, "last_draw": 0})
            data["heist_cooldown"] = loaded.get("heist_cooldown", {})
            data["reminders"]      = loaded.get("reminders", [])
            data["confess_count"]  = loaded.get("confess_count", 0)
            data["cmd_uses"]       = loaded.get("cmd_uses", {})
            data["private_voices"] = loaded.get("private_voices", {})
            data["pvc_info_posted"]= loaded.get("pvc_info_posted", False)
            data["msg_count_week"] = loaded.get("msg_count_week", {})
            data["aotw_last"]      = loaded.get("aotw_last", None)
            data["nsfw_strikes"]   = loaded.get("nsfw_strikes", {})
            data["ban_allowed_ids"]= loaded.get("ban_allowed_ids", [])
            data["poo"]            = loaded.get("poo", {})
            data["poo_tasks"]       = loaded.get("poo_tasks", {})
            data["vatrice"]        = loaded.get("vatrice", {})
            data["vatrice_cd"]     = loaded.get("vatrice_cd", {})
            data["vatrice_threshold"] = loaded.get("vatrice_threshold", {})
            for k, v in loaded.items():
                if k not in data:
                    data[k] = v
    except Exception as e:
        print(f"[load_data] WARN: {e} — koristim default")

def save_data():
    """Atomski save — temp fajl + rename, sa backupom. Nikad ne gubi vatrice."""
    try:
        tmp = DATA_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            try: os.fsync(f.fileno())
            except Exception: pass
        if os.path.exists(DATA_FILE):
            try:
                bak = DATA_FILE + ".bak"
                if os.path.exists(bak): os.remove(bak)
                os.replace(DATA_FILE, bak)
            except Exception: pass
        os.replace(tmp, DATA_FILE)
        # 🔁 OBILJEŽI da treba poslati backup na Discord (radi auto petlja)
        try: _DBACKUP_STATE["pending"] = True
        except Exception: pass
    except Exception as e:
        print(f"[save_data] ERROR: {e}")

# ═══════════════════════════════════════════
#    💾 DISCORD CLOUD BACKUP — vatrice/tiketstaff/brojanje uvijek online
#    Bot uploaduje oleun_data.json u privatni Discord kanal i restoruje
#    ga automatski kad se redeploy desi (nema vanjske baze ni servisa).
#    PODESI ENV VAR:  BACKUP_CHANNEL_ID = ID kanala (broj)
#    Bot mora imati pristup tom kanalu i dozvolu Send + Attach Files.
# ═══════════════════════════════════════════
BACKUP_CHANNEL_ID = int(os.environ.get("BACKUP_CHANNEL_ID", "0") or "0")
DBACKUP_INTERVAL  = 90   # min sekundi između dva uploada (anti-spam)
_DBACKUP_STATE    = {"pending": False, "last": 0.0, "restored": False}

async def _discord_backup_upload():
    """Pošalji oleun_data.json kao attachment u backup kanal (throttled)."""
    if not BACKUP_CHANNEL_ID:
        return
    if not os.path.exists(DATA_FILE):
        return
    ch = bot.get_channel(BACKUP_CHANNEL_ID)
    if ch is None:
        try: ch = await bot.fetch_channel(BACKUP_CHANNEL_ID)
        except Exception as e:
            print(f"[cloud-backup] kanal {BACKUP_CHANNEL_ID} nedostupan: {e}")
            return
    try:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        with open(DATA_FILE, "rb") as f:
            await ch.send(
                content=f"💾 **Auto-backup** · `{ts}`",
                file=discord.File(f, filename="oleun_data.json"),
            )
        _DBACKUP_STATE["last"] = time.time()
        _DBACKUP_STATE["pending"] = False
        print(f"[cloud-backup] OK ({ts})")
    except Exception as e:
        print(f"[cloud-backup] upload fail: {e}")

async def _discord_backup_restore() -> bool:
    """Ako je oleun_data.json prazan/nepostojeći — povuci posljednji backup sa Discorda."""
    if not BACKUP_CHANNEL_ID:
        print("[cloud-restore] BACKUP_CHANNEL_ID nije postavljen — preskačem")
        return False
    # Ne restoruj ako već imamo pun fajl sa vatricama/podacima
    try:
        if os.path.exists(DATA_FILE) and os.path.getsize(DATA_FILE) > 50:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                tmp = json.load(f)
            if tmp.get("vatrice") or tmp.get("counting") or tmp.get("economy") or tmp.get("xp"):
                print("[cloud-restore] lokalni fajl ima podatke — preskačem restore")
                return False
    except Exception:
        pass
    ch = bot.get_channel(BACKUP_CHANNEL_ID)
    if ch is None:
        try: ch = await bot.fetch_channel(BACKUP_CHANNEL_ID)
        except Exception as e:
            print(f"[cloud-restore] kanal nedostupan: {e}")
            return False
    try:
        async for msg in ch.history(limit=50):
            for att in msg.attachments:
                if att.filename == "oleun_data.json":
                    raw = await att.read()
                    # validacija — mora biti validan JSON
                    try:
                        json.loads(raw.decode("utf-8"))
                    except Exception:
                        continue
                    with open(DATA_FILE, "wb") as f:
                        f.write(raw)
                    print(f"[cloud-restore] vraćen backup od {msg.created_at.strftime('%Y-%m-%d %H:%M UTC')}")
                    load_data()
                    _DBACKUP_STATE["restored"] = True
                    return True
        print("[cloud-restore] nema backupa u zadnjih 50 poruka")
    except Exception as e:
        print(f"[cloud-restore] error: {e}")
    return False

@tasks.loop(seconds=30)
async def _cloud_backup_loop():
    try:
        if not BACKUP_CHANNEL_ID:
            return
        if _DBACKUP_STATE.get("pending") and (time.time() - _DBACKUP_STATE.get("last", 0)) >= DBACKUP_INTERVAL:
            await _discord_backup_upload()
    except Exception as e:
        print(f"[cloud-backup loop] {e}")

def get_guild_config(guild_id) -> dict:
    key = str(guild_id)
    if key not in data["guild_config"]:
        data["guild_config"][key] = {}
    return data["guild_config"][key]

load_data()

def get_economy(uid):
    key = str(uid)
    if key not in data["economy"]:
        data["economy"][key] = {"balance": 500, "last_work": 0, "last_daily": 0}
    d = data["economy"][key]
    d.setdefault("last_daily", 0)
    return d

def get_xp(uid):
    key = str(uid)
    if key not in data["xp"]:
        data["xp"][key] = {"xp": 0, "level": 1}
    return data["xp"][key]

def add_xp(uid, amount):
    d = get_xp(uid)
    d["xp"] += amount
    needed = d["level"] * 75
    if d["xp"] >= needed:
        d["xp"] -= needed
        d["level"] += 1
        return True
    return False

def get_zoo(uid):
    key = str(uid)
    if key not in data["zoo"]:
        data["zoo"][key] = {}
    return data["zoo"][key]

def get_warnings(guild_id, uid):
    gk, uk = str(guild_id), str(uid)
    data["warnings"].setdefault(gk, {})
    data["warnings"][gk].setdefault(uk, [])
    return data["warnings"][gk][uk]

# ═══════════════════════════════════════════
#    EMBED HELPER
# ═══════════════════════════════════════════
def em(title, desc="", color=COLORS["balkan"], fields=None, footer=None, thumb=None, image=None):
    e = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.now(timezone.utc))
    if fields:
        for n, v, inline in fields:
            e.add_field(name=n, value=v or "\u200b", inline=inline)
    e.set_footer(text=footer or f"{BOT_NAME} {VERSION}")
    if thumb:  e.set_thumbnail(url=thumb)
    if image:  e.set_image(url=image)
    return e

# ═══════════════════════════════════════════
#    🎨 AUTO-EMBED MONKEYPATCH
#    Sve poruke koje bot pošalje kao plain tekst se automatski
#    pretvaraju u lijepi embed — NIŠTA NE OSTAJE PROVIDNO.
#    (Originalni embed/file/view/content pozivi se NE diraju.)
# ═══════════════════════════════════════════
def _autoembed_color_for(text: str) -> int:
    t = (text or "").lstrip()
    if t.startswith(("❌", "🚫", "⛔", "💀")):       return COLORS["error"]
    if t.startswith(("⚠️", "⚠")):                   return COLORS["warning"]
    if t.startswith(("✅", "🎉", "🏆", "💚")):       return COLORS["success"]
    if t.startswith(("🔒", "🔐", "🔑")):             return COLORS["purple"]
    if t.startswith(("💶", "💰", "🏦", "💸")):       return COLORS["gold"]
    return COLORS["info"]

def _wrap_to_embed(content):
    if content is None: return None
    s = str(content)
    if not s.strip(): return None
    return em(None, s, color=_autoembed_color_for(s))

def _aembed_should_wrap(content, args, kwargs, extra_skip=()):
    """Vrati True samo ako poruka NEMA embed/file/view/modal i NIJE prazna."""
    if content is None or args:
        return False
    skip_keys = ("embed", "embeds", "file", "files", "view", "modal", "stickers")
    for k in skip_keys + tuple(extra_skip):
        if k in kwargs:
            return False
    s = str(content)
    return bool(s.strip())

_orig_iresp_send       = discord.InteractionResponse.send_message
_orig_iresp_edit       = discord.InteractionResponse.edit_message
_orig_inter_edit_orig  = discord.Interaction.edit_original_response
_orig_webhook_send     = discord.Webhook.send
_orig_messageable_send = discord.abc.Messageable.send
_orig_message_edit     = discord.Message.edit
_orig_message_reply    = discord.Message.reply

async def _patched_iresp_send(self, content=None, *args, **kwargs):
    if _aembed_should_wrap(content, args, kwargs):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            content = None
    return await _orig_iresp_send(self, content, *args, **kwargs)

async def _patched_iresp_edit(self, *args, **kwargs):
    # InteractionResponse.edit_message — content kroz kwargs
    content = kwargs.get("content")
    if _aembed_should_wrap(content, args, kwargs):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            kwargs["content"] = None
    return await _orig_iresp_edit(self, *args, **kwargs)

async def _patched_inter_edit_orig(self, **kwargs):
    content = kwargs.get("content")
    if _aembed_should_wrap(content, (), kwargs):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            kwargs["content"] = None
    return await _orig_inter_edit_orig(self, **kwargs)

async def _patched_webhook_send(self, content=None, *args, **kwargs):
    if _aembed_should_wrap(content, args, kwargs):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            content = None
    return await _orig_webhook_send(self, content, *args, **kwargs)

async def _patched_messageable_send(self, content=None, *args, **kwargs):
    # Ne diraj poruke koje već imaju embed/file/view/sticker/reference
    if _aembed_should_wrap(content, args, kwargs, extra_skip=("reference",)):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            content = None
    return await _orig_messageable_send(self, content, *args, **kwargs)

async def _patched_message_edit(self, **kwargs):
    content = kwargs.get("content")
    if _aembed_should_wrap(content, (), kwargs):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            kwargs["content"] = None
    return await _orig_message_edit(self, **kwargs)

async def _patched_message_reply(self, content=None, **kwargs):
    if _aembed_should_wrap(content, (), kwargs, extra_skip=("reference",)):
        emb = _wrap_to_embed(content)
        if emb is not None:
            kwargs["embed"] = emb
            content = None
    return await _orig_message_reply(self, content, **kwargs)

discord.InteractionResponse.send_message       = _patched_iresp_send
discord.InteractionResponse.edit_message       = _patched_iresp_edit
discord.Interaction.edit_original_response     = _patched_inter_edit_orig
discord.Webhook.send                           = _patched_webhook_send
discord.abc.Messageable.send                   = _patched_messageable_send
discord.Message.edit                           = _patched_message_edit
discord.Message.reply                          = _patched_message_reply
print("[auto-embed] aktivan — sve plain poruke (send/edit/reply/followup) automatski idu kao embed")

# Premium embed za važne ekrane (profil, daily, level-up, pobjede, shop)
def em_pro(title, desc="", color=COLORS["gold"], fields=None, footer=None, thumb=None, image=None, author=None, accent=True):
    sep = "˚｡⋆୨୧˚ ───────────── ˚୨୧⋆｡˚"
    if accent and desc:
        desc = f"{sep}\n{desc}\n{sep}"
    elif accent:
        desc = sep
    e = discord.Embed(title=f"✦ {title} ✦", description=desc, color=color, timestamp=datetime.now(timezone.utc))
    if fields:
        for n, v, inline in fields:
            e.add_field(name=f"⟢ {n}", value=v or "\u200b", inline=inline)
    if author:
        e.set_author(name=author.display_name, icon_url=author.display_avatar.url)
    e.set_footer(text=footer or f"⚡ {BOT_NAME} {VERSION}")
    if thumb:  e.set_thumbnail(url=thumb)
    if image:  e.set_image(url=image)
    return e

# ═══════════════════════════════════════════
#    GIF HELPER (nekos.best)
# ═══════════════════════════════════════════
async def get_gif(action: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://nekos.best/api/v2/{action}", timeout=aiohttp.ClientTimeout(total=5)) as r:
                if r.status == 200:
                    j = await r.json()
                    return j["results"][0]["url"]
    except:
        pass
    return None

# ═══════════════════════════════════════════
#    EVENTI
# ═══════════════════════════════════════════
async def _license_check_and_shutdown_if_clone():
    """Provjerava da je bot na zvaničnom GIAN serveru. Ako nije — gasi se.
    Aktivira se SAMO ako je env var LICENSE_GUARD=1 (sigurnosni opt-in).
    """
    if os.environ.get("LICENSE_GUARD") != "1":
        print(f"  🔓 Licenca: guard isključen (postavi LICENSE_GUARD=1 da uključiš)")
        return True
    if bot.get_guild(OFFICIAL_GUILD_ID) is not None:
        print(f"  🔐 Licenca: ✓ ovo je ZVANIČNI bot (GIAN)")
        return True
    # Bot nije na zvaničnom serveru — ovo je klonirana kopija
    print(f"\n{'═'*60}")
    print(f"  ⛔ NEDOZVOLJENA KOPIJA BOTA")
    print(f"  Ovaj bot nije član zvaničnog GIAN servera.")
    print(f"  Jedini originalni bot: GIAN")
    print(f"  Napuštam sve servere i gasim se za 5s...")
    print(f"{'═'*60}\n")
    # Pokušaj poslati poruku u svaki guild prije izlaska
    for g in list(bot.guilds):
        try:
            ch = next((c for c in g.text_channels if c.permissions_for(g.me).send_messages), None)
            if ch:
                e = discord.Embed(
                    title="⛔ Nedozvoljena kopija bota",
                    description=(
                        f"Ovaj bot je **neovlaštena kopija** originalnog **{BOT_NAME}** bota.\n\n"
                        f"🔗 **Jedini originalni bot:** GIAN\n\n"
                        f"Bot će se sada automatski isključiti i napustiti server."
                    ),
                    color=0xE74C3C
                )
                await ch.send(embed=e)
        except Exception:
            pass
        try:
            await g.leave()
            print(f"  ↩  Napustio: {g.name} ({g.id})")
        except Exception as _e:
            print(f"  ✘ Ne mogu napustiti {g.name}: {_e}")
    await asyncio.sleep(5)
    await bot.close()
    return False


@bot.event
async def on_ready():
    print(f"\n{'═'*45}\n  {BOT_NAME} {VERSION} — ONLINE\n{'═'*45}")
    # ── 🔐 Licencna provjera — gasi se ako je kopija ──
    if not await _license_check_and_shutdown_if_clone():
        return
    # ── 💾 CLOUD RESTORE — ako je oleun_data.json nestao poslije uploada ──
    try:
        restored = await _discord_backup_restore()
        if restored:
            print("  ✔ Cloud restore uspio — vatrice/tiket/brojanje vraćeni!")
    except Exception as _e:
        print(f"[cloud-restore on_ready] {_e}")
    # ── Persistent views (preživljavaju restart) ──
    try:
        bot.add_view(GiveawayView())
        bot.add_view(TicketOpenView())
        bot.add_view(TicketCloseView())
        bot.add_view(PrivateVCPanel())
        bot.add_view(StaffVoteView())
        bot.add_view(VoiceCreateButton())
        print("  ✔ Persistent views aktivni (giveaway / ticket / staff-vote / privatni VC / panel-role)")
    except Exception as e:
        print(f"  ✘ Persistent views: {e}")
    # ── Protection config (anti-raid + anti-nsfw) ──
    try:
        await get_panel_protection()
        bot.loop.create_task(_protection_refresh_loop())
        print("  ✔ Protection config učitan — refresh loop aktivan (svakih 5 min)")
    except Exception as e:
        print(f"  ✘ Protection config: {e}")
    # ── Games config (ekonomija, kockanje, životinje) ──
    try:
        await get_panel_games()
        bot.loop.create_task(_games_refresh_loop())
        print("  ✔ Games config učitan — refresh loop aktivan (svakih 5 min)")
    except Exception as e:
        print(f"  ✘ Games config: {e}")
    # ── Sync komandi na svaki restart (guild-only, bez duplikata) ──
    synced_count = 0
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            synced_count = len(synced)
            print(f"  ✔ {guild.name} ({guild.member_count} članova) — {synced_count} komandi")
        except Exception as e:
            print(f"  ✘ {guild.name}: {e}")
    # Obriši globalne komande da nema duplikata
    try:
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print(f"  ✔ Globalne komande obrisane — nema duplikata")
    except Exception as e:
        print(f"  ✘ Clear global error: {e}")
    print(f"  ✔ Sync završen: {synced_count} komandi")
    print(f"{'═'*45}\n")
    # Cache invites
    for guild in bot.guilds:
        try:
            invs = await guild.invites()
            data["invite_uses"][str(guild.id)] = {inv.code: inv.uses for inv in invs}
        except Exception as _e: print(f"[invite cache] {guild.name}: {_e}")
    save_data()
    if not change_status.is_running(): change_status.start()
    if not birthday_check.is_running(): birthday_check.start()
    if not auto_backup.is_running(): auto_backup.start()
    if not _cloud_backup_loop.is_running(): _cloud_backup_loop.start()
    # forsiraj prvi backup ubrzo nakon pokretanja (ako je kanal podešen)
    try:
        if BACKUP_CHANNEL_ID:
            _DBACKUP_STATE["pending"] = True
            _DBACKUP_STATE["last"]    = 0.0
    except Exception: pass
    # vanity_loop uklonjen — zamijenjen sa /vatrice sistemom
    if not auto_game_loop.is_running(): auto_game_loop.start()
    if not active_member_week.is_running(): active_member_week.start()
    try: await post_pvc_info()
    except Exception as _e: print(f"[pvc-info init] {_e}")
    print(f"  🛡️ Sigurnost: Anti-Nuke ✓ • Anti-Invite ✓ • Auto-Backup ✓ • Owner whitelist: {len(OWNER_IDS)}")
    for key, panel in data.get("selfroles", {}).items():
        if not panel.get("message_id"):
            continue
        try:
            view = _build_selfrole_view(key)
            bot.add_view(view, message_id=panel["message_id"])
        except Exception as e:
            print(f"  ✘ selfroles restore [{key}]: {e}")

    # ── 🎉 RECOVERY: nastavi aktivne giveaway-ove poslije restarta ──
    saved_gws = data.get("active_giveaways", {})
    if saved_gws:
        print(f"  🎉 Recovery {len(saved_gws)} aktivnih giveaway-ova...")
        now_ts = datetime.now(timezone.utc).timestamp()
        for mid_str, gd in list(saved_gws.items()):
            try:
                mid = int(mid_str)
                ga = {
                    "entrants": set(gd.get("entrants", [])),
                    "prize": gd["prize"],
                    "channel_id": gd["channel_id"],
                    "msg_id": mid,
                    "end_at": gd.get("end_at"),
                    "guild_id": gd.get("guild_id"),
                }
                active_giveaways[mid] = ga
                ch = bot.get_channel(gd["channel_id"])
                if not ch:
                    print(f"  ✘ giveaway {mid}: kanal {gd['channel_id']} ne postoji, brišem")
                    _remove_giveaway(mid); active_giveaways.pop(mid, None)
                    continue
                end_at = gd.get("end_at") or now_ts
                remaining = max(0, end_at - now_ts)
                if remaining <= 0:
                    asyncio.create_task(_end_giveaway(mid, ch))
                    print(f"  ✔ giveaway {mid}: istekao → završavam")
                else:
                    async def _resume(mid=mid, ch=ch, sec=remaining):
                        await asyncio.sleep(sec)
                        await _end_giveaway(mid, ch)
                    asyncio.create_task(_resume())
                    print(f"  ✔ giveaway {mid}: nastavlja se ({int(remaining)}s preostalo)")
            except Exception as e:
                print(f"  ✘ giveaway recovery [{mid_str}]: {e}")

    # ── 🔊 CLEANUP: orphaned privatni VC-ovi ──
    pvs = dict(data.get("private_voices", {}))
    cleaned = 0
    for ch_id_str in list(pvs.keys()):
        try:
            ch = bot.get_channel(int(ch_id_str))
            if ch is None:
                # Kanal ne postoji više
                data["private_voices"].pop(ch_id_str, None); cleaned += 1
            elif len([m for m in ch.members if not m.bot]) == 0:
                # Prazan — obriši
                try: await ch.delete(reason="Cleanup orphaned PVC na startup")
                except: pass
                data["private_voices"].pop(ch_id_str, None); cleaned += 1
        except Exception as e:
            print(f"  ✘ pvc cleanup [{ch_id_str}]: {e}")
    if cleaned:
        save_data()
        print(f"  🧹 Očišćeno {cleaned} praznih/nepostojećih privatnih VC-ova")

@bot.event
async def on_guild_join(guild):
    print(f"  ➕ Pridružen server: {guild.name} ({guild.member_count} članova)")
    # ── 🔐 Licencna provjera za novi server (samo ako je guard aktivan) ──
    if os.environ.get("LICENSE_GUARD") == "1" and bot.get_guild(OFFICIAL_GUILD_ID) is None:
        # Ovo je klonirani bot — ne dozvoli mu rad na novom serveru
        try:
            ch = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if ch:
                e = discord.Embed(
                    title="⛔ Nedozvoljena kopija bota",
                    description=(
                        f"Ovaj bot je **neovlaštena kopija** originalnog **{BOT_NAME}** bota.\n\n"
                        f"🔗 **Jedini originalni bot:** GIAN\n\n"
                        f"Bot napušta server."
                    ),
                    color=0xE74C3C
                )
                await ch.send(embed=e)
        except Exception:
            pass
        try:
            await guild.leave()
            print(f"  🔐 Licenca: napustio nedozvoljeni server {guild.name}")
        except Exception as _e:
            print(f"  ✘ Ne mogu napustiti {guild.name}: {_e}")
        return
    try:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"  ✔ Komande sync-ane za {guild.name}")
    except Exception as e:
        print(f"  ✘ Sync error za {guild.name}: {e}")
    chan = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
    if chan:
        try:
            e = discord.Embed(
                title=f"👋 Zdravo, {guild.name}!",
                description=(
                    f"Ja sam **{BOT_NAME}** — Balkan Discord bot!\n\n"
                    f"📖 Ukucaj `/help` da vidiš sve komande.\n"
                    f"🎮 Igraj igre, skupljaj životinje, zarađuj pare!\n\n"
                    f"*Verzija: {VERSION}*"
                ),
                color=COLORS["balkan"],
                timestamp=datetime.now(timezone.utc)
            )
            e.set_thumbnail(url=bot.user.display_avatar.url)
            e.set_footer(text=f"{BOT_NAME} {VERSION}")
            await chan.send(embed=e)
        except Exception:
            pass

@bot.event
async def on_member_join(member):
    cfg = get_guild_config(member.guild.id)

    # ── Anti-Raid (PAMETNI: ne lockuje, samo kickuje sumnjive) ──
    try:
        if await antiraid_check(member):
            return  # Kickovan, ne radi welcome
    except Exception as _e: print(f"[anti-raid] {_e}")

    # ── 🔥 VATRICE — novi član dobija 1 auto vatricu pri ulasku + ažurira nick ──
    try:
        cfg_vj = get_guild_config(member.guild.id)
        vemoji = cfg_vj.get("vatrice_emoji", "🔥")
        novi_v = _add_vatrica(member.guild.id, member.id, 1)
        save_data()
        # ⬇️ Odmah ažuriraj nick da član dobije varicu pored nicka
        try:
            await _update_vatrice_nick(member, novi_v, vemoji)
        except Exception:
            pass
        if vch_id := cfg_vj.get("vatrice_channel"):
            if vch := member.guild.get_channel(vch_id):
                vj_e = discord.Embed(
                    description=(
                        f"🎁 {member.mention} dobio/la **1 {vemoji} vatricu** kao poklon dobrodošlice!\n"
                        f"{vemoji} Ukupno: **{novi_v}**  ·  Još vatrica zarađuješ svakih **150 poruka!**"
                    ),
                    color=0xFF4500,
                    timestamp=datetime.now(timezone.utc)
                )
                vj_e.set_author(name=f"{member.display_name} se pridružio/la!", icon_url=member.display_avatar.url)
                vj_e.set_footer(text=f"GIAN (Custom) • Vatrice sistem")
                await vch.send(embed=vj_e)
    except Exception as _e:
        print(f"[vatrica-join] {_e}")

    # ── Invite Tracking ────────────────────────────────
    try:
        gkey = str(member.guild.id)
        old = data["invite_uses"].get(gkey, {})
        new_invites = await member.guild.invites()
        new_uses = {inv.code: inv.uses for inv in new_invites}
        used_code = None
        for code, uses in new_uses.items():
            if uses > old.get(code, 0):
                used_code = code
                break
        if used_code:
            inviter = next((inv.inviter for inv in new_invites if inv.code == used_code), None)
            if inviter and not inviter.bot:
                ikey = f"{member.guild.id}:{inviter.id}"
                rec = data["invites"].setdefault(ikey, {"count": 0, "code": used_code})
                rec["count"] += 1
                rec["code"] = used_code
        data["invite_uses"][gkey] = new_uses
        save_data()
    except Exception as _e: print(f"[invite-track join] {_e}")

    # ── Sumnjivi nalozi (mlađi od 7 dana) — upozorenje u log ──
    try:
        if is_suspicious_account(member):
            age_days = (datetime.now(timezone.utc) - member.created_at).days
            await audit_log(member.guild, "⚠️ Sumnjiv nalog se pridružio",
                f"{member.mention} (`{member}`) — nalog je star samo **{age_days} dan/a**.\n"
                f"Mogući fake/spam nalog. Provjeriti aktivnost.",
                color=COLORS.get("warning", 0xFFA500))
    except Exception as _e: print(f"[suspicious] {_e}")

    # ── Server Milestones (50, 100, 200, 500, 1000…) ──
    try:
        cnt = sum(1 for m in member.guild.members if not m.bot)
        milestones = [25, 50, 100, 150, 200, 300, 500, 750, 1000, 1500, 2000, 5000]
        if cnt in milestones:
            ms_ch = member.guild.get_channel(cfg.get("welcome_channel") or 1494687347558715543) or member.guild.system_channel
            if ms_ch:
                ms_e = discord.Embed(
                    title=f"🎊 MILESTONE — {cnt} ČLANOVA! 🎊",
                    description=(
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🏆 Upravo smo dostigli **{cnt}** članova!\n"
                        f"💜 Hvala svima koji su dio **× GIAN** porodice!\n"
                        f"🚀 Nastavljamo dalje — sljedeća stanica još veća!\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━"
                    ),
                    color=0xFFD700, timestamp=datetime.now(timezone.utc)
                )
                ms_e.set_image(url="https://media.tenor.com/M0vSf9CGHoEAAAAC/celebration.gif")
                ms_e.set_footer(text=f"{BOT_NAME} • Server raste! 📈")
                await ms_ch.send(content="@everyone", embed=ms_e,
                    allowed_mentions=discord.AllowedMentions(everyone=True))
    except Exception as _e: print(f"[milestone] {_e}")

    # ── Auto-Role ──────────────────────────────────────
    if auto_role_id := cfg.get("auto_role"):
        role = member.guild.get_role(auto_role_id)
        if role:
            try: await member.add_roles(role)
            except: pass

    # ── Log ────────────────────────────────────────────
    if log_ch := member.guild.get_channel(cfg.get("log_channel", 0)):
        le = discord.Embed(title="📥 Novi Član", color=COLORS["success"], timestamp=datetime.now(timezone.utc))
        le.set_author(name=str(member), icon_url=member.display_avatar.url)
        le.add_field(name="ID", value=f"`{member.id}`", inline=True)
        le.add_field(name="Nalog kreiran", value=member.created_at.strftime("%d.%m.%Y."), inline=True)
        le.add_field(name="Ukupno članova", value=f"`{member.guild.member_count}`", inline=True)
        await log_ch.send(embed=le)


    # ── Welcome ────────────────────────────────────────
    ch_id = cfg.get("welcome_channel")
    chan = member.guild.get_channel(ch_id) if ch_id else discord.utils.get(member.guild.text_channels, name="welcome")
    if not chan: return

    # ── Animirani vatrice emojiji ──
    VE = [
        "<a:vatrice1:1500466044429664256>",
        "<a:vatrice2:1500466048418185246>",
        "<a:vatrice3:1500466039782113352>",
        "<a:vatrice4:1500466061970247741>",
    ]

    # ── Kanali ──
    ch_chat = member.guild.get_channel(cfg.get("chat_channel",  1496860023706488884))
    ch_info = member.guild.get_channel(cfg.get("info_channel",  1496860023093989475))
    ch_news = member.guild.get_channel(cfg.get("news_channel",  1501973333195882696))
    ch_gws  = member.guild.get_channel(cfg.get("gws_channel",   1496860023480127505))
    ch_game = member.guild.get_channel(cfg.get("game_channel",  1496860023706488890))
    ch_mus  = member.guild.get_channel(cfg.get("music_channel", 1496860024121852088))

    chat_lnk = ch_chat.mention if ch_chat else "#chat"
    info_lnk = ch_info.mention if ch_info else "#info"
    news_lnk = ch_news.mention if ch_news else "#news"
    gws_lnk  = ch_gws.mention  if ch_gws  else "#gws"

    member_count = sum(1 for m in member.guild.members if not m.bot)

    # ── Welcome Embed (Panel API → fallback hardkod) ──
    _pw = await get_panel_embed("welcome")

    # Welcome-specific variable resolver — handles {accountAge}, {joinedAt}, {count} etc.
    _now_utc = datetime.now(timezone.utc)
    _created  = member.created_at if member.created_at.tzinfo else member.created_at.replace(tzinfo=timezone.utc)
    _delta    = _now_utc - _created
    _yrs, _rem = divmod(_delta.days, 365)
    _mos = _rem // 30
    _age_str = (f"{_yrs}g {_mos}m" if _yrs and _mos else
                f"{_yrs}g"         if _yrs           else
                f"{_mos}m"         if _mos           else "< 1m")
    _joined_str = (member.joined_at or _now_utc).strftime("%b %Y")

    def _wev(text: str) -> str:
        """Welcome embed variable expander — superset of _ev."""
        if not text: return text
        return (_ev(text, member, member_count)
                .replace("{accountAge}", _age_str)
                .replace("{joinedAt}",   _joined_str)
                .replace("{count}",      str(member_count))
                .replace("{user.avatar}", str(member.display_avatar.url))
                .replace("{memberCount}", str(member_count)))

    def _fmt_item(label: str, ch_id: str) -> str:
        return f"<#{ch_id}>" if ch_id else f"**{label}**"

    if _pw:
        _wc = int((_pw.get("color") or "#ec4899").lstrip("#") or "ec4899", 16)

        # Card list items (with optional channel links)
        _item1 = _pw.get("cardItem1") or "Procitaj pravila"
        _item2 = _pw.get("cardItem2") or "Odaberi role"
        _item3 = _pw.get("cardItem3") or "Predstavi se zajednici"
        _ch1   = _pw.get("item1ChannelId") or ""
        _ch2   = _pw.get("item2ChannelId") or ""
        _ch3   = _pw.get("item3ChannelId") or ""

        # Build description
        _desc_base = _pw.get("description") or ""
        if not _desc_base:
            _desc_base = (f"{_fmt_item(_item1, _ch1)}\n"
                          f"{_fmt_item(_item2, _ch2)}\n"
                          f"{_fmt_item(_item3, _ch3)}")
        else:
            _desc_base = (_desc_base
                .replace("{item1}", _fmt_item(_item1, _ch1))
                .replace("{item2}", _fmt_item(_item2, _ch2))
                .replace("{item3}", _fmt_item(_item3, _ch3)))

        e = discord.Embed(description=_wev(_desc_base), color=_wc, timestamp=_now_utc)

        if _pw.get("title"):
            e.title = _wev(_pw["title"])

        # Fields — with full variable substitution
        for _f in (_pw.get("fields") or []):
            _fn = _wev(str(_f.get("name") or ""))
            _fv = _wev(str(_f.get("value") or ""))
            if _fn or _fv:
                e.add_field(
                    name=_fn   or "\u200b",
                    value=_fv  or "\u200b",
                    inline=bool(_f.get("inline", True))
                )

        # Thumbnail
        _thumb_raw = _pw.get("thumbnail") or ""
        _thumb_url = _wev(_thumb_raw) if _thumb_raw else str(member.display_avatar.url)
        if _thumb_url and _thumb_url.startswith("http"):
            e.set_thumbnail(url=_thumb_url)

        # Footer
        _footer_text = _wev(_pw.get("footer") or f"{BOT_NAME} • Welcome")
        e.set_footer(text=_footer_text, icon_url=member.guild.icon.url if member.guild.icon else None)

    else:
        e = discord.Embed(
            description=(
                f"**wlcm {member.mention}!**\n\n"
                f"{VE[0]} {chat_lnk} **·** {VE[1]} {info_lnk} **·** {VE[2]} {news_lnk} **·** {VE[3]} {gws_lnk}\n"
                f"🪶 **{member_count} member**"
            ),
            color=0x2B2D3A,
            timestamp=_now_utc
        )
        e.set_thumbnail(url=member.display_avatar.url)
        e.set_footer(text=f"{BOT_NAME} • Welcome",
                     icon_url=member.guild.icon.url if member.guild.icon else None)

    # ── Dugmadi ──
    wv = discord.ui.View()
    pw_buttons = (_pw or {}).get("buttons") or []
    _has_linked = any(pb.get("channelId") or pb.get("url") for pb in pw_buttons)
    if pw_buttons and _has_linked:
        for pb in pw_buttons:
            if not pb.get("label"):
                continue
            ch_id  = pb.get("channelId") or pb.get("channel_id")
            direct = pb.get("url")
            if ch_id:
                btn_url = f"https://discord.com/channels/{member.guild.id}/{ch_id}"
            elif direct:
                btn_url = direct
            else:
                continue
            wv.add_item(discord.ui.Button(
                label=pb["label"],
                emoji=pb.get("emoji") or None,
                url=btn_url,
                style=discord.ButtonStyle.link,
            ))
    else:
        # Fallback — hardkodovani game/music kanali
        if ch_game:
            wv.add_item(discord.ui.Button(
                label="game",
                emoji="<a:game1:1500459114931949568>",
                url=f"https://discord.com/channels/{member.guild.id}/{ch_game.id}",
                style=discord.ButtonStyle.link
            ))
        if ch_mus:
            wv.add_item(discord.ui.Button(
                label="music",
                emoji="<a:music2:1500459145382592602>",
                url=f"https://discord.com/channels/{member.guild.id}/{ch_mus.id}",
                style=discord.ButtonStyle.link
            ))

    await chan.send(content=member.mention, embed=e, view=wv)

def _find_boost_channel(guild: discord.Guild):
    """Vraća prvi tekstualni kanal koji u imenu sadrži 'boost' (case-insensitive),
    a u koji bot ima dozvolu da šalje poruke. Fallback: system_channel."""
    for c in guild.text_channels:
        if "boost" in c.name.lower() and c.permissions_for(guild.me).send_messages:
            return c
    sc = guild.system_channel
    if sc and sc.permissions_for(guild.me).send_messages:
        return sc
    return next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)

@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        guild  = after.guild
        boosts = guild.premium_subscription_count or 0
        tier   = guild.premium_tier

        BOOST_REWARD = 2500
        get_economy(after.id)["balance"] += BOOST_REWARD
        save_data()

        chan = _find_boost_channel(guild)
        if not chan:
            return

        # ── MALI, ČIST EMBED ──
        e = discord.Embed(
            title="💜 Novi Boost!",
            description=(
                f"{after.mention} je upravo **boostovao server**! 🚀\n"
                f"Hvala ti na podršci — server je sad još jači! 💪"
            ),
            color=0xF47FFF,
            timestamp=datetime.now(timezone.utc)
        )
        e.add_field(name="🚀 Boostova", value=f"`{boosts}`",        inline=True)
        e.add_field(name="🏅 Tier",     value=f"`Lvl {tier}`",      inline=True)
        e.add_field(name="🎁 Nagrada",  value=f"`+{BOOST_REWARD:,} 💶`", inline=True)
        e.set_thumbnail(url=after.display_avatar.url)
        e.set_footer(text=f"{BOT_NAME} • Hvala na podršci 💜")
        await chan.send(content=after.mention, embed=e)

@bot.event
async def on_message(message):
    if message.author.bot: return
    if not message.guild: return

    # ── Prefix bridge (.kpm radi kao /kpm) ──
    if message.content.startswith("."):
        if await try_prefix_command(message):
            return

    # ── WLCM auto-reakcije (svako ko napiše "wlcm" dobije 🇼🇱🇨🇲) ──
    if message.content.lower().strip() in ("wlcm", "wlcm all"):
        for emj in ["🇼", "🇱", "🇨", "🇲"]:
            try: await message.add_reaction(emj)
            except: pass
        return

    # ── Brojanje handler (PRIJE auto-mod-a, da se uvijek reaguje) ──
    cnt_cfg = data.get("counting", {}).get(str(message.guild.id))
    if cnt_cfg and message.channel.id == cnt_cfg.get("channel_id"):
        content = message.content.strip()
        try:
            num = int(content)
        except ValueError:
            try: await message.delete()
            except: pass
            return
        expected = cnt_cfg.get("current", 0) + 1
        last_user = cnt_cfg.get("last_user")
        if last_user == message.author.id:
            try: await message.add_reaction("⛔")
            except Exception as e: print(f"[brojanje] reaction fail: {e}")
            warn_e = discord.Embed(
                title="⛔ OPOMENA — Ne možeš brojati iza sebe!",
                description=(
                    f"{message.author.mention}, **mora neko drugi nastaviti** prije nego što ti opet brojiš.\n\n"
                    f"➡️ Sljedeći broj je i dalje: **{expected}**"
                ),
                color=COLORS["warning"]
            )
            warn_e.set_footer(text=f"Pravilo: izmjenjivanje korisnika obavezno")
            await message.channel.send(content=message.author.mention, embed=warn_e, delete_after=8)
            try: await message.delete()
            except: pass
            return
        if num != expected:
            try: await message.add_reaction("❌")
            except Exception as e: print(f"[brojanje] reaction fail: {e}")
            try: await message.delete()
            except: pass
            # broji greške po korisniku (NE resetujemo brojanje!)
            mistakes = cnt_cfg.setdefault("mistakes", {})
            uid_str = str(message.author.id)
            mistakes[uid_str] = mistakes.get(uid_str, 0) + 1
            user_total = mistakes[uid_str]
            save_data()
            err_e = discord.Embed(
                title="💥 OPOMENA — Pogrešan broj!",
                description=(
                    f"{message.author.mention}, **pogriješio/la** si!\n\n"
                    f"❌ Tvoj odgovor: **{num}**\n"
                    f"✅ Trebalo je: **{expected}**\n\n"
                    f"⚠️ Tvojih grešaka ukupno: **{user_total}**\n"
                    f"➡️ Brojanje **se nastavlja** — sljedeći broj je i dalje: **{expected}**"
                ),
                color=COLORS["error"], timestamp=datetime.now(timezone.utc)
            )
            err_e.set_footer(text=f"Pazi sljedeći put, {message.author.display_name}!")
            await message.channel.send(content=message.author.mention, embed=err_e, delete_after=10)
            return
        # tačan broj
        cnt_cfg["current"] = num
        cnt_cfg["last_user"] = message.author.id
        if num > cnt_cfg.get("high_score", 0):
            cnt_cfg["high_score"] = num
        save_data()
        try:
            await message.add_reaction("✅")
        except Exception as e:
            print(f"[brojanje] reaction fail: {e}")
        # uokvireni label ispod broja
        try:
            label = discord.Embed(
                description=f"✅  **#{num}**  ·  sljedeći: **{num+1}**",
                color=COLORS["success"]
            )
            label.set_footer(text=f"Brojao/la: {message.author.display_name}")
            await message.reply(embed=label, mention_author=False, silent=True)
        except Exception as e:
            print(f"[brojanje] reply fail: {e}")
        if num % 50 == 0:
            eco = get_economy(message.author.id)
            eco["balance"] += 100
            add_xp(message.author.id, 50); save_data()
            await message.channel.send(
                embed=em(f"🎯 Milestone {num}!",
                         f"{message.author.mention} dostigao broj **{num}**!\n`+100 💶` `+50 XP`",
                         color=COLORS["gold"]),
                delete_after=10
            )
        return

    # ── Auto-Mod ──────────────────────────────────────
    if await check_nsfw(message):
        return
    if await check_automod(message):
        return

    # ── AFK: clear if author was AFK ──────────────────
    uid_str = str(message.author.id)
    if uid_str in data["afk"]:
        afk_info = data["afk"].pop(uid_str)
        save_data()
        since = datetime.fromtimestamp(afk_info["since"], tz=timezone.utc)
        elapsed = datetime.now(timezone.utc) - since
        mins = int(elapsed.total_seconds() // 60)
        await message.channel.send(
            embed=em("👋 Dobro došao/la nazad!", f"Skinut AFK status. Bio/la si odsutan/na **{mins} min**.", color=COLORS["info"]),
            delete_after=8
        )

    # ── AFK: notify if mentioning AFK user ────────────
    for mentioned in message.mentions:
        m_str = str(mentioned.id)
        if m_str in data["afk"]:
            afk_r = data["afk"][m_str]
            await message.channel.send(
                embed=em(f"😴 {mentioned.display_name} je AFK",
                         f"Razlog: *{afk_r.get('reason', 'nema razloga')}*",
                         color=COLORS["warning"]),
                delete_after=10
            )

    # ── Quest: msgs20 ─────────────────────────────────
    if not message.content.startswith("/") and not message.content.startswith("!"):
        completed = quest_progress(message.author.id, "msgs20")
        if completed:
            await message.channel.send(
                embed=em(f"✅ Quest završen! {completed['name']}", f"+**{completed['reward']} 💶**!", color=COLORS["gold"]),
                delete_after=8
            )

    # ── Kaladont handler ──────────────────────────────
    if message.channel.id in kaladont_games and not message.content.startswith("/"):
        game = kaladont_games[message.channel.id]
        # NORMALIZACIJA: uppercase + skidanje dijakritika (Š→S, Č→C, Ž→Z, Đ→DJ, Ć→C)
        word = _kaladont_normalize(message.content)
        letters = game["letters"]
        req = game["word"][-letters:]

        async def reject(reason: str, hint: str = ""):
            desc = hint or f"Sljedeća mora početi sa **`{req}`**"
            try:
                await message.reply(
                    embed=em("❌  " + reason, desc, color=COLORS["error"]),
                    mention_author=False, delete_after=7
                )
            except Exception: pass

        # Mora biti čista riječ (samo slova, bez razmaka)
        if not word or not word.isalpha() or " " in message.content.strip():
            pass  # ignoriši poruke koje nisu čiste riječi (ili imaju više riječi)
        elif len(word) < 3:
            await reject("Prekratka!", "Minimalno **3 slova**.")
        elif message.author.id == game.get("last_uid"):
            await reject("Ne možeš igrati iza sebe!", "Čekaj da drugi odigra pa onda ti.")
        elif word[:letters] != req:
            await reject(f"Mora početi sa `{req}`!", f"Tvoja: `{word}` — sljedeća mora početi sa **`{req}`**")
        elif word in game["used"]:
            await reject(f"`{word}` je već bila!", "Pokušaj drugu riječ.")
        else:
            ok, why = kaladont_word_valid(word)
            if not ok:
                if why == "ime":
                    await reject(f"`{word}` je ime!", "Imena (osoba) nisu dozvoljena u kaladontu. Pokušaj imenicu, glagol ili pridjev.")
                    return
                elif why == "kraj":
                    await reject(
                        f"`{word}` ima nemoguć završetak!",
                        f"Niko ne može nastaviti sa **`{word[-2:]}`**. Probaj drugu riječ koja počinje sa **`{req}`**."
                    )
                    return
            # ── Validna riječ — uvijek se prihvata ───────────────────
            game["word"]             = word
            game["last_uid"]         = message.author.id
            game["last_player_name"] = message.author.display_name
            game["used"].add(word)
            game["chain"].append((word, message.author.display_name))
            count   = len(game["chain"])
            new_req = word[-letters:]
            try: await message.add_reaction("✅")
            except: pass
            # ── POBJEDA: magična riječ "KALADONT" ─────────────
            if word == "KALADONT":
                try: await message.add_reaction("👑")
                except: pass
                eco = get_economy(message.author.id)
                nagrada = 1500
                eco["balance"] = eco.get("balance", 0) + nagrada
                add_xp(message.author.id, 200)
                save_data()
                win_e = discord.Embed(
                    title=f"👑  K A L A D O N T  —  P O B J E D A !  {E_FIRE4}",
                    description=f"{E_FIRE1}{E_FIRE2}{E_FIRE3}  {message.author.mention} je izrekao/la magičnu riječ!  {E_FIRE3}{E_FIRE2}{E_FIRE1}",
                    color=0xFFD700,
                    timestamp=datetime.now(timezone.utc)
                )
                win_e.add_field(name="🏆  Pobjednik/ca",  value=f"**{message.author.display_name}**", inline=True)
                win_e.add_field(name="📊  Riječi u nizu", value=f"**{count}**",                       inline=True)
                win_e.add_field(name="💰  Nagrada",       value=f"**+{nagrada:,} 💶**",               inline=True)
                win_e.add_field(name="⭐  XP",            value=f"**+200**",                          inline=True)
                win_e.set_thumbnail(url=message.author.display_avatar.url)
                win_e.set_footer(text=f"{BOT_NAME} • Kaladont pobjeda")
                await message.channel.send(content=message.author.mention, embed=win_e)
                del kaladont_games[message.channel.id]
                return
            await message.channel.send(embed=kaladont_word_card(word, message.author.display_name, new_req, count), view=KaladontWordView(message.channel.id))
            if game["msg"]:
                try: await game["msg"].edit(embed=kaladont_active_embed(game))
                except: pass
        return  # ne procesuj XP za kaladont poruke

    # ── Wordle handler ────────────────────────────────
    if message.channel.id in wordle_games:
        wgame = wordle_games[message.channel.id]
        wcontent = message.content.strip()
        if message.author.id == wgame["uid"] and not wcontent.startswith("/"):
            guess = _kaladont_normalize(wcontent)
            if guess.isalpha() and len(guess) == 5:
                wgame["guesses"].append(guess)
                won  = (guess == wgame["word"])
                used = len(wgame["guesses"])
                try: await message.add_reaction("🟩" if won else "✅")
                except: pass
                if won:
                    wcfg   = _g_gamble("wordle")
                    reward = int(wcfg.get("reward", 1200))
                    xp     = 150
                    eco    = get_economy(message.author.id)
                    eco["balance"] = eco.get("balance", 0) + reward
                    add_xp(message.author.id, xp)
                    save_data()
                    win_e = _wordle_embed(wgame, message.author, finished=True, won=True, reward=reward, xp=xp)
                    if wgame.get("msg"):
                        try: await wgame["msg"].edit(embed=win_e)
                        except: pass
                    await message.channel.send(content=message.author.mention, embed=win_e)
                    del wordle_games[message.channel.id]
                    return
                if used >= wgame["max"]:
                    lose_e = _wordle_embed(wgame, message.author, finished=True, won=False)
                    if wgame.get("msg"):
                        try: await wgame["msg"].edit(embed=lose_e)
                        except: pass
                    await message.channel.send(embed=lose_e)
                    del wordle_games[message.channel.id]
                    return
                upd_e = _wordle_embed(wgame, message.author)
                if wgame.get("msg"):
                    try: await wgame["msg"].edit(embed=upd_e)
                    except: pass
                else:
                    try:
                        sent = await message.channel.send(embed=upd_e)
                        wgame["msg"] = sent
                    except: pass
                return  # ne procesuj XP za wordle pogodak

    # ── Msg Counter ───────────────────────────────────
    mkey = f"{message.guild.id}:{message.author.id}"
    data["msg_count"][mkey] = data["msg_count"].get(mkey, 0) + 1
    # Poo task: chat messages
    if message.guild:
        _poo_task_progress(message.guild.id, message.author.id, "chat")
    data.setdefault("msg_count_week", {})
    data["msg_count_week"][mkey] = data["msg_count_week"].get(mkey, 0) + 1

    # ── 🔥 VATRICE — auto +1 svakih 100 poruka (threshold-based, otporno na restart/upload) ────────
    try:
        VATRICA_PRAG = 100
        ukupno_msgs = data["msg_count"][mkey]
        # threshold-based: koristimo "last_vatrica_msg" tracker u data["vatrice_threshold"]
        data.setdefault("vatrice_threshold", {})
        last_v_msg = int(data["vatrice_threshold"].get(mkey, 0))
        # auto-init: ako je threshold 0 a već ima >150 poruka, postavi na najbliži milestone ispod
        if last_v_msg == 0 and ukupno_msgs >= VATRICA_PRAG:
            last_v_msg = (ukupno_msgs // VATRICA_PRAG) * VATRICA_PRAG
            data["vatrice_threshold"][mkey] = last_v_msg
        # award svaku vatricu koja je dosegnuta od zadnjeg threshold-a (može biti više ako je preskočeno)
        awarded = 0
        while ukupno_msgs - last_v_msg >= VATRICA_PRAG:
            last_v_msg += VATRICA_PRAG
            awarded += 1
        if awarded > 0:
            data["vatrice_threshold"][mkey] = last_v_msg
            cfg_v = get_guild_config(message.guild.id)
            vemoji = cfg_v.get("vatrice_emoji", "🔥")
            novi_v = _add_vatrica(message.guild.id, message.author.id, awarded)

            # ── XP / LEVEL — sve zaključano na 100 poruka ──
            # Svakih 100 poruka = +1 vatrica + +1 LEVEL + +100 XP
            xp_d = get_xp(message.author.id)
            xp_d["level"] = xp_d.get("level", 1) + awarded
            xp_d["xp"]    = xp_d.get("xp", 0) + (awarded * 100)
            novi_lvl = xp_d["level"]
            save_data()

            try: await _update_vatrice_nick(message.author, novi_v, vemoji)
            except Exception: pass
            try: await _post_vatrice_objava(message.guild, None, message.author, novi_v, vemoji)
            except Exception: pass

            # ── Level-up notifikacija (uloge + embed) ──
            try:
                lr = cfg_v.get("level_roles", {})
                new_role = None
                if str(novi_lvl) in lr:
                    lvl_role = message.guild.get_role(lr[str(novi_lvl)])
                    if lvl_role:
                        try:
                            await message.author.add_roles(lvl_role)
                            new_role = lvl_role
                        except: pass
                lvl_ch_id = cfg_v.get("levelup_channel") or cfg_v.get("aktivnost_channel") or 1494043957242495107
                lvl_ch = message.guild.get_channel(lvl_ch_id) or message.channel
                sep = "━━━━━━━━━━━━━━━━━━━━━━"
                desc = (
                    f"{sep}\n"
                    f"🎉 Čestitamo {message.author.mention}!\n"
                    f"Dostigao/la si **`★ LEVEL {novi_lvl} ★`**\n"
                    f"{sep}\n"
                    f"💬 **+100 XP** • {vemoji} **+{awarded} vatrica**\n"
                    f"📨 Sljedeći level: još `100` poruka!\n"
                )
                if new_role:
                    desc += f"🏷️ **Otključana uloga:** {new_role.mention}\n"
                desc += f"\n📊 Provjeri statistiku sa `/aktivnost` ili `/rank`"
                lv_em = discord.Embed(
                    title="🌟 ʟᴇᴠᴇʟ ᴜᴘ! 🌟",
                    description=desc,
                    color=0xFFD700,
                    timestamp=datetime.now(timezone.utc)
                )
                lv_em.set_thumbnail(url=message.author.display_avatar.url)
                lv_em.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
                lv_em.set_footer(text=f"⚡ {BOT_NAME} • XP Sistem (svakih 100 poruka)")
                if lvl_ch.id == message.channel.id:
                    await lvl_ch.send(content=message.author.mention, embed=lv_em, delete_after=15)
                else:
                    await lvl_ch.send(content=message.author.mention, embed=lv_em)
            except Exception as _e:
                print(f"[level-up] {_e}")
    except Exception as _e: print(f"[vatrica-500] {_e}")

    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    if not before.guild: return
    cfg = get_guild_config(before.guild.id)
    log_ch = before.guild.get_channel(cfg.get("log_channel", 0))
    if not log_ch: return
    e = discord.Embed(title="✏️ Poruka Editovana", color=COLORS["warning"], timestamp=datetime.now(timezone.utc))
    e.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
    e.add_field(name="Kanal",   value=before.channel.mention,           inline=True)
    e.add_field(name="📍 Link", value=f"[Idi na poruku]({after.jump_url})", inline=True)
    e.add_field(name="Prije",   value=(before.content[:1000] or "*prazno*"), inline=False)
    e.add_field(name="Poslije", value=(after.content[:1000]  or "*prazno*"), inline=False)
    await log_ch.send(embed=e)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild: return
    cfg = get_guild_config(message.guild.id)
    log_ch = message.guild.get_channel(cfg.get("log_channel", 0))
    if not log_ch: return
    e = discord.Embed(title="🗑️ Poruka Obrisana", color=COLORS["error"], timestamp=datetime.now(timezone.utc))
    e.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
    e.add_field(name="Kanal",    value=message.channel.mention,                         inline=True)
    e.add_field(name="Sadržaj",  value=(message.content[:1000] or "*prilog/prazno*"),   inline=False)
    await log_ch.send(embed=e)

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) != "⭐" or not payload.guild_id: return
    cfg = get_guild_config(payload.guild_id)
    sb_ch_id = cfg.get("starboard_channel")
    if not sb_ch_id: return
    if payload.channel_id == sb_ch_id: return
    threshold = cfg.get("starboard_threshold", 3)
    guild   = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    try:
        message = await channel.fetch_message(payload.message_id)
    except: return
    star_r = discord.utils.get(message.reactions, emoji="⭐")
    count  = star_r.count if star_r else 0
    if count < threshold: return
    sb_channel = guild.get_channel(sb_ch_id)
    if not sb_channel: return
    gkey   = str(payload.guild_id)
    mkey   = str(payload.message_id)
    done   = data["starboard_done"].setdefault(gkey, {})
    if mkey in done:
        try:
            sb_msg = await sb_channel.fetch_message(done[mkey])
            ne = sb_msg.embeds[0]
            ne.set_footer(text=f"⭐ {count} | #{channel.name}")
            await sb_msg.edit(embed=ne)
        except: pass
        return
    e = discord.Embed(description=message.content or "", color=COLORS["gold"], timestamp=message.created_at)
    e.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    e.add_field(name="📍 Original", value=f"[Idi na poruku]({message.jump_url})", inline=False)
    if message.attachments: e.set_image(url=message.attachments[0].url)
    e.set_footer(text=f"⭐ {count} | #{channel.name}")
    sb_msg = await sb_channel.send(f"⭐ **{count}** | {channel.mention}", embed=e)
    done[mkey] = sb_msg.id
    save_data()

@tasks.loop(hours=1)
async def birthday_check():
    today = datetime.now(timezone.utc).strftime("%d-%m")
    for uid, bday in list(data.get("birthdays", {}).items()):
        if bday != today: continue
        for guild in bot.guilds:
            member = guild.get_member(int(uid))
            if not member: continue
            cfg   = get_guild_config(guild.id)
            ch_id = cfg.get("birthday_channel")
            if not ch_id: continue
            chan = guild.get_channel(ch_id)
            if not chan: continue
            e = discord.Embed(
                title="🎂 Sretan Rođendan!",
                description=f"Danas je rođendan od {member.mention}! 🎉\nSvi mu/joj čestitajte! 🥳",
                color=COLORS["fun"], timestamp=datetime.now(timezone.utc)
            )
            e.set_thumbnail(url=member.display_avatar.url)
            e.set_footer(text=f"{BOT_NAME} • Rođendani")
            try: await chan.send(content=member.mention, embed=e)
            except: pass

@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def sync_cmd(ctx):
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(embed=em("✅ Sinhronizovano!", f"`{len(synced)}` komandi registrovano.", color=COLORS["success"]))
    except Exception as e:
        await ctx.send(embed=em("❌ Greška", str(e), color=COLORS["error"]))

# ═══════════════════════════════════════════
#    🛡️ SIGURNOST: Anti-Nuke / Audit / Backup / Whitelist
# ═══════════════════════════════════════════
OWNER_IDS: set = {829552737322270731}  # Discord ID-evi koji su 100% sigurni (anti-nuke whitelist)
NUKE_WINDOW = 30        # sekundi
NUKE_BAN_LIMIT = 3      # max banova/kickova/brisanja u prozoru
nuke_tracker: dict = defaultdict(lambda: defaultdict(deque))

# ── PAMETNI Anti-Raid (NE LOCKUJE server, samo kickuje sumnjive) ───
RAID_WINDOW = 30            # sekundi (5+ joinova u 30s = raid lockdown 5 min)
RAID_JOIN_LIMIT = 5         # 5+ NOVIH naloga u 30s = raid
SUSPICIOUS_AGE_DAYS = 7     # nalozi mlađi od ovoliko dana = sumnjivi
join_tracker: dict = defaultdict(deque)   # guild_id -> deque[(timestamp, member_id, account_age_days)]
raid_mode: dict = {}        # guild_id -> until_timestamp (period gdje se sumnjivi auto-kickaju)

def is_suspicious_account(member) -> bool:
    """Nalog je sumnjiv ako je mlađi od konfiguriranog praga."""
    age_days = (datetime.now(timezone.utc) - member.created_at).days
    return age_days < _prot_raid().get("age_days", SUSPICIOUS_AGE_DAYS)

async def antiraid_check(member):
    """Prati joinove. Ako je raid, ulazi u raid mod. Koristi live panel config."""
    r = _prot_raid()
    if not r["enabled"]:
        return False
    now = time.time()
    gid = member.guild.id
    age_days = (datetime.now(timezone.utc) - member.created_at).days
    dq = join_tracker[gid]
    dq.append((now, member.id, age_days))
    while dq and dq[0][0] < now - r["window"]:
        dq.popleft()
    suspicious_recent = sum(1 for _, _, ad in dq if ad < r["age_days"])
    if suspicious_recent >= r["limit"]:
        lockdown_secs = r["lockdown_min"] * 60
        raid_mode[gid] = now + lockdown_secs
        await audit_log(member.guild, "🚨 RAID DETEKTOVAN!",
            f"**{suspicious_recent}** sumnjivih naloga (mlađih od {r['age_days']} dana) u zadnjih {r['window']}s!\n"
            f"⚙️ **Raid mode AKTIVAN {r['lockdown_min']}min** — sumnjivi nalozi će biti automatski kickovani.\n"
            f"✅ Stari/legitimni nalozi prolaze normalno.")
    if gid in raid_mode and now < raid_mode[gid] and is_suspicious_account(member):
        try:
            await member.send(embed=em("🛡️ Raid Zaštita", f"Server **{member.guild.name}** je trenutno pod raid zaštitom. Tvoj nalog je premlad ({age_days}d). Pokušaj ponovo kasnije.", color=COLORS["warning"]))
        except: pass
        action = r["action"]
        if action == "ban":
            try:
                await member.ban(reason="🛡️ Anti-Raid: sumnjiv nalog tokom raida")
                await audit_log(member.guild, "🛡️ Anti-Raid Ban", f"Banovan: `{member}` (`{member.id}`) — nalog star {age_days}d")
                return True
            except: pass
        elif action == "kick":
            try:
                await member.kick(reason="🛡️ Anti-Raid: sumnjiv nalog tokom raida")
                await audit_log(member.guild, "🛡️ Anti-Raid Kick", f"Kickovan: `{member}` (`{member.id}`) — nalog star {age_days}d")
                return True
            except: pass
        else:  # alert_only
            await audit_log(member.guild, "🛡️ Anti-Raid Upozorenje", f"Sumnjiv nalog: `{member}` (`{member.id}`) — nalog star {age_days}d (akcija: samo upozori)")
    return False

async def audit_log(guild, title, desc):
    """Šalje sigurnosni log u log_channel + DM-uje OWNER_IDS."""
    try:
        cfg = get_guild_config(guild.id)
        if log_ch := guild.get_channel(cfg.get("log_channel", 0)):
            await log_ch.send(embed=em(title, desc, color=COLORS["error"]))
    except: pass
    for oid in OWNER_IDS:
        try:
            owner = await bot.fetch_user(oid)
            await owner.send(embed=em(f"🔔 [{guild.name}] {title}", desc, color=COLORS["warning"]))
        except: pass

async def antinuke_check(guild, mod, action: str):
    """Vrati True ako moderator prelazi limit. Skida mu admin uloge i obavještava."""
    if mod.id in OWNER_IDS or mod.bot:
        return False
    now = time.time()
    dq = nuke_tracker[guild.id][mod.id]
    dq.append(now)
    while dq and dq[0] < now - NUKE_WINDOW:
        dq.popleft()
    if len(dq) >= NUKE_BAN_LIMIT:
        dq.clear()
        # Skini sve admin uloge
        try:
            removed = []
            for r in list(mod.roles):
                if r.permissions.administrator or r.permissions.ban_members or r.permissions.kick_members or r.permissions.manage_roles:
                    try:
                        await mod.remove_roles(r, reason="🛡️ Anti-Nuke: prelazak limita")
                        removed.append(r.name)
                    except: pass
            await audit_log(guild, "🚨 ANTI-NUKE AKTIVAN!",
                f"**Moderator:** {mod.mention} (`{mod}`)\n**Akcija:** {action}\n**Limit:** {NUKE_BAN_LIMIT} u {NUKE_WINDOW}s\n**Skinute uloge:** {', '.join(removed) if removed else 'nijedna'}")
        except Exception as _e: print(f"[anti-nuke] {_e}")
        return True
    return False

@bot.event
async def on_member_ban(guild, user):
    # ── Log u log_channel ───────────────────────────────
    try:
        cfg = get_guild_config(guild.id)
        if log_ch := guild.get_channel(cfg.get("log_channel", 0)):
            e = discord.Embed(title="🔨 Član Banovan", color=COLORS["error"], timestamp=datetime.now(timezone.utc))
            e.set_author(name=str(user), icon_url=user.display_avatar.url)
            e.add_field(name="ID", value=f"`{user.id}`", inline=True)
            await log_ch.send(embed=e)
    except Exception as _e: print(f"[on_member_ban log] {_e}")
    # ── Anti-Nuke provjera ──────────────────────────────
    try:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                await antinuke_check(guild, entry.user, f"BAN korisnika `{user}`")
                await audit_log(guild, "🔨 BAN", f"**Moderator:** {entry.user.mention}\n**Korisnik:** `{user}` (`{user.id}`)\n**Razlog:** {entry.reason or '—'}")
                break
    except Exception as _e: print(f"[on_member_ban nuke] {_e}")

@bot.event
async def on_member_remove(member):
    # ── Sanity guards ───────────────────────────────────
    # Ako je guild nedostupan (bot je izbačen/napustio server) — izlaz
    if member.guild is None or bot.get_guild(member.guild.id) is None:
        return
    # Ako je član koji odlazi sam bot — izlaz
    if bot.user is not None and member.id == bot.user.id:
        return

    cfg = get_guild_config(member.guild.id)
    # ── Log ────────────────────────────────────────────
    try:
        if log_ch := member.guild.get_channel(cfg.get("log_channel", 0)):
            le = discord.Embed(title="📤 Član Otišao", color=COLORS["warning"], timestamp=datetime.now(timezone.utc))
            le.set_author(name=str(member), icon_url=member.display_avatar.url)
            le.add_field(name="ID", value=f"`{member.id}`", inline=True)
            le.add_field(name="Pridružio se", value=member.joined_at.strftime("%d.%m.%Y.") if member.joined_at else "?", inline=True)
            await log_ch.send(embed=le)
    except (discord.NotFound, discord.Forbidden):
        pass
    except Exception as _e: print(f"[on_member_remove log] {_e}")
    # ── Leave message ───────────────────────────────────
    try:
        ch_id = cfg.get("leave_channel") or cfg.get("welcome_channel")
        chan = member.guild.get_channel(ch_id) if ch_id else discord.utils.get(member.guild.text_channels, name="welcome")
        if chan:
            VE_L = [
                "<a:vatrice1:1500466044429664256>",
                "<a:vatrice2:1500466048418185246>",
                "<a:vatrice3:1500466039782113352>",
                "<a:vatrice4:1500466061970247741>",
            ]
            member_count_l = sum(1 for m in member.guild.members if not m.bot)
            _pl = await get_panel_embed("leave")
            if _pl:
                _ld = _ev(_pl.get("description") or "", member, member_count_l)
                _lc = int(_pl.get("color", "#2B2D3A").lstrip("#") or "2B2D3A", 16)
                e = discord.Embed(description=_ld, color=_lc, timestamp=datetime.now(timezone.utc))
                if _pl.get("title"): e.title = _ev(_pl["title"], member, member_count_l)
            else:
                e = discord.Embed(
                    description=(
                        f"**bye {member.mention}** 👋\n\n"
                        f"{VE_L[0]} {member.display_name} **je napustio/la server**\n"
                        f"🪶 **{member_count_l} member**"
                    ),
                    color=0x2B2D3A,
                    timestamp=datetime.now(timezone.utc)
                )
            e.set_thumbnail(url=member.display_avatar.url)
            e.set_footer(
                text=f"{BOT_NAME} • Leave",
                icon_url=member.guild.icon.url if member.guild.icon else None
            )
            await chan.send(embed=e)
    except (discord.NotFound, discord.Forbidden):
        pass
    except Exception as _e: print(f"[on_member_remove leave] {_e}")
    # ── Anti-Nuke kick provjera ─────────────────────────
    try:
        # Provjeri ponovo prije API poziva (guild je možda nestao u međuvremenu)
        if bot.get_guild(member.guild.id) is None:
            return
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (time.time() - entry.created_at.timestamp()) < 5:
                await antinuke_check(member.guild, entry.user, f"KICK korisnika `{member}`")
                await audit_log(member.guild, "👢 KICK", f"**Moderator:** {entry.user.mention}\n**Korisnik:** `{member}` (`{member.id}`)")
                break
    except (discord.NotFound, discord.Forbidden):
        # Guild ne postoji više ili nemamo View Audit Log permisiju — tiho ignoriši
        pass
    except Exception as _e: print(f"[on_member_remove nuke] {_e}")

@bot.event
async def on_guild_channel_delete(channel):
    try:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                await antinuke_check(channel.guild, entry.user, f"BRISANJE kanala #{channel.name}")
                await audit_log(channel.guild, "🗑️ KANAL OBRISAN", f"**Moderator:** {entry.user.mention}\n**Kanal:** `#{channel.name}`")
                break
    except Exception as _e: print(f"[on_channel_delete] {_e}")

@bot.event
async def on_guild_role_delete(role):
    try:
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role.id:
                await antinuke_check(role.guild, entry.user, f"BRISANJE uloge {role.name}")
                await audit_log(role.guild, "🏷️ ULOGA OBRISANA", f"**Moderator:** {entry.user.mention}\n**Uloga:** `{role.name}`")
                break
    except Exception as _e: print(f"[on_role_delete] {_e}")

# ── Auto-backup svakih 6 sati ────────────────────────
@tasks.loop(hours=6)
async def auto_backup():
    try:
        import shutil as _sh
        backup_dir = _os.path.join(_DATA_DIR, "backups")
        _os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dst = _os.path.join(backup_dir, f"oleun_data_{ts}.json")
        _sh.copy(DATA_FILE, dst)
        # Drži maksimum 20 backupa
        backups = sorted(_os.listdir(backup_dir))
        for old in backups[:-20]:
            try: _os.remove(_os.path.join(backup_dir, old))
            except: pass
        print(f"[backup] {dst}")
    except Exception as _e: print(f"[backup] {_e}")

@tasks.loop(seconds=30)
async def change_status():
    statuses = [
        discord.Activity(type=discord.ActivityType.playing,   name=f"/help | {BOT_NAME}"),
        discord.Activity(type=discord.ActivityType.watching,  name="Balkanske drame 🎭"),
        discord.Activity(type=discord.ActivityType.competing, name="kocki i rakiji 🍻"),
        discord.Activity(type=discord.ActivityType.playing,   name="Balkan igre 🎮"),
        discord.Activity(type=discord.ActivityType.watching,  name="tvojim /hunt resultatima 🏹"),
        discord.Activity(type=discord.ActivityType.playing,   name="sa životinjama u zoo-u 🦁"),
        discord.Activity(type=discord.ActivityType.competing, name="battle turniru ⚔️"),
        discord.CustomActivity(name="💰 Ekonomija • 🎮 Igre • 🐾 OWO"),
        discord.CustomActivity(name=f"🟣 {BOT_NAME}"),
        discord.Activity(type=discord.ActivityType.listening, name="/help za sve komande"),
    ]
    await bot.change_presence(activity=random.choice(statuses))

# ═══════════════════════════════════════════
#    INFO & UTILS
# ═══════════════════════════════════════════
@bot.tree.command(name="ping", description="🏓 Provjeri brzinu bota")
async def ping(i: discord.Interaction):
    ms = round(bot.latency * 1000)
    status, color = ("🟢 Odlično", COLORS["success"]) if ms < 80 else ("🟡 Dobro", COLORS["warning"]) if ms < 180 else ("🔴 Sporo", COLORS["error"])
    await i.response.send_message(embed=em("🏓 Pong!", color=color, fields=[
        ("📡 Latency", f"`{ms}ms`", True), ("📊 Status", status, True), ("🤖 Bot", f"`{bot.user}`", True)
    ]))

@bot.tree.command(name="serverinfo", description="📊 Informacije o serveru")
async def serverinfo(i: discord.Interaction):
    g = i.guild
    bots, humans = sum(1 for m in g.members if m.bot), g.member_count - sum(1 for m in g.members if m.bot)
    await i.response.send_message(embed=em(f"🏰 {g.name}", color=COLORS["purple"], thumb=g.icon.url if g.icon else None, fields=[
        ("👑 Vlasnik",   g.owner.mention,                                        True),
        ("👥 Članovi",   f"`{humans}` ljudi • `{bots}` botova",                 True),
        ("📅 Kreiran",   g.created_at.strftime("%d.%m.%Y."),                    True),
        ("💬 Kanali",    f"`{len(g.text_channels)}` tekst • `{len(g.voice_channels)}` voice", True),
        ("🏷️ Uloge",    f"`{len(g.roles)-1}`",                                  True),
        ("🚀 Boostovi",  f"`{g.premium_subscription_count or 0}`",              True),
    ]))

@bot.tree.command(name="userinfo", description="👤 Informacije o korisniku")
async def userinfo(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    eco, xpd = get_economy(u.id), get_xp(u.id)
    warns = len(get_warnings(i.guild.id, u.id))
    await i.response.send_message(embed=em(f"👤 {u.display_name}", color=u.accent_color or COLORS["default"], thumb=u.display_avatar.url, fields=[
        ("🆔 ID",          f"`{u.id}`",                                            True),
        ("📅 Pridružio",   u.joined_at.strftime("%d.%m.%Y.") if u.joined_at else "N/A", True),
        ("🏷️ Top uloga",  u.top_role.mention,                                    True),
        ("💰 Balans",      f"`{eco['balance']:,} 💶`",                            True),
        ("📈 Level",       f"`{xpd['level']}`",                                   True),
        ("⚠️ Upozorenja",  f"`{warns}`",                                           True),
    ]))

@bot.tree.command(name="spotify", description="🎵 Pogledaj šta korisnik trenutno sluša na Spotifyu")
async def spotify_cmd(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    spotify = next((a for a in u.activities if isinstance(a, discord.Spotify)), None)
    if not spotify:
        return await i.response.send_message(
            embed=em("🎵 Spotify", f"{u.mention} trenutno **ne sluša ništa** na Spotifyu.\n\n💡 *Mora imati Spotify povezan sa Discord nalogom i pustiti pjesmu.*", color=COLORS["warning"]),
            ephemeral=False
        )
    duration = spotify.duration
    elapsed = datetime.now(timezone.utc) - spotify.start
    progress = min(elapsed.total_seconds() / duration.total_seconds(), 1.0)
    bar_len = 20
    filled = int(progress * bar_len)
    bar = "▰" * filled + "▱" * (bar_len - filled)
    def fmt_t(td):
        s = int(td.total_seconds()); return f"{s//60}:{s%60:02d}"
    e = discord.Embed(
        title=f"🎵 {spotify.title}",
        url=f"https://open.spotify.com/track/{spotify.track_id}",
        description=f"**Izvođač:** {spotify.artist}\n**Album:** {spotify.album}\n\n`{fmt_t(elapsed)}` {bar} `{fmt_t(duration)}`",
        color=0x1DB954,  # Spotify zelena
        timestamp=datetime.now(timezone.utc)
    )
    e.set_author(name=f"{u.display_name} sluša", icon_url=u.display_avatar.url)
    if spotify.album_cover_url: e.set_thumbnail(url=spotify.album_cover_url)
    e.set_footer(text=f"Spotify • {BOT_NAME}")
    await i.response.send_message(embed=e)

@bot.tree.command(name="invite", description="📊 Statistika — poruke + invite-ovi")
async def invite_cmd(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    mkey = f"{i.guild.id}:{u.id}"
    msg_n = data["msg_count"].get(mkey, 0)
    ikey = f"{i.guild.id}:{u.id}"
    inv_rec = data["invites"].get(ikey, {})
    inv_count = inv_rec.get("count", 0)
    invite_url = None
    invite_uses = 0
    try:
        invs = await i.guild.invites()
        user_invs = [inv for inv in invs if inv.inviter and inv.inviter.id == u.id]
        if user_invs:
            best = max(user_invs, key=lambda x: x.uses)
            invite_url = f"https://discord.gg/{best.code}"
            invite_uses = best.uses
            if not inv_rec:
                inv_count = best.uses
    except Exception as _e: print(f"[pump] {_e}")
    e = em(f"📊 Statistika — {u.display_name}",
        color=u.accent_color or COLORS["balkan"], thumb=u.display_avatar.url, fields=[
        ("✍️ Poruke poslato", f"`{msg_n:,}`", True),
        ("👥 Doveo članova",   f"`{inv_count}`", True),
        ("📅 Pridružio",       u.joined_at.strftime("%d.%m.%Y.") if u.joined_at else "N/A", True),
        ("🔗 Tvoj invite",     f"`{invite_uses}` korišćenja" if invite_url else "*nemaš svoj invite link*", False),
    ])
    e.set_footer(text=f"Korisnik: {u} • ID: {u.id}")
    view = None
    if invite_url:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Otvori invite", emoji="🔗", url=invite_url, style=discord.ButtonStyle.link))
    await i.response.send_message(embed=e, view=view) if view else await i.response.send_message(embed=e)


@bot.tree.command(name="avatar", description="🖼️ Prikaži avatar korisnika")
async def avatar(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    await i.response.send_message(embed=em(f"🖼️ {u.display_name}",
        f"[PNG]({u.display_avatar.with_format('png').url}) • [JPG]({u.display_avatar.with_format('jpg').url}) • [WEBP]({u.display_avatar.with_format('webp').url})",
        color=COLORS["info"], image=u.display_avatar.url))

# /say uklonjeno (v2.1) — rizik impersonacije/uznemiravanja kroz bota.

@bot.tree.command(name="brojanje-postavi", description="🔢 Postavi kanal za brojanje [ADMIN]")
@app_commands.describe(kanal="Kanal u kojem će se brojati", pocetak="Od kog broja krenuti (default 0 → sljedeći je 1)")
@app_commands.checks.has_permissions(administrator=True)
async def brojanje_postavi(i: discord.Interaction, kanal: discord.TextChannel, pocetak: int = 0):
    data["counting"][str(i.guild.id)] = {
        "channel_id": kanal.id,
        "current": max(0, pocetak),
        "last_user": None,
        "high_score": data.get("counting", {}).get(str(i.guild.id), {}).get("high_score", 0)
    }
    save_data()
    nxt = max(0, pocetak) + 1
    e = em("✅ Kanal za brojanje postavljen!",
           f"Kanal: {kanal.mention}\n"
           f"Trenutno: **{max(0, pocetak)}**\n"
           f"Sljedeći broj: **{nxt}**\n\n"
           f"📜 **Pravila:**\n"
           f"• Pišite brojeve redom (1, 2, 3, …)\n"
           f"• Ne smiješ brojati dvaput zaredom\n"
           f"• Ko pogriješi → reset na 0\n"
           f"• Svaki **50.** broj = `+100 💶` `+50 XP` 🎯",
           color=COLORS["success"])
    await i.response.send_message(embed=e)

@bot.tree.command(name="brojanje-info", description="🔢 Pokaži stanje brojanja")
async def brojanje_info(i: discord.Interaction):
    cfg = data.get("counting", {}).get(str(i.guild.id))
    if not cfg:
        return await i.response.send_message(
            embed=em("❌", "Brojanje nije postavljeno! Admin može sa `/brojanje-postavi`.", color=COLORS["error"]),
            ephemeral=True
        )
    ch = i.guild.get_channel(cfg["channel_id"])
    nxt = cfg.get("current", 0) + 1
    last = cfg.get("last_user")
    last_txt = f"<@{last}>" if last else "—"
    e = discord.Embed(
        title="🔢 Brojanje — stanje",
        description=(
            f"📍 **Kanal:** {ch.mention if ch else '*(obrisan)*'}\n"
            f"🔢 **Trenutno:** `{cfg.get('current', 0)}`\n"
            f"➡️ **Sljedeći broj:** `{nxt}`\n"
            f"👤 **Zadnji brojao:** {last_txt}\n"
            f"🏆 **Rekord:** `{cfg.get('high_score', 0)}`"
        ),
        color=COLORS["info"], timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.response.send_message(embed=e)

@bot.tree.command(name="brojanje-reset", description="🔢 Resetuj brojanje na 0 [ADMIN]")
@app_commands.checks.has_permissions(administrator=True)
async def brojanje_reset(i: discord.Interaction):
    cfg = data.get("counting", {}).get(str(i.guild.id))
    if not cfg:
        return await i.response.send_message(
            embed=em("❌", "Brojanje nije postavljeno!", color=COLORS["error"]),
            ephemeral=True
        )
    cfg["current"] = 0
    cfg["last_user"] = None
    save_data()
    await i.response.send_message(embed=em("✅ Resetovano!", "Brojanje krene od **1**.", color=COLORS["success"]))

# /setname i /setavatar — uklonjeni (oslobađa slotove za 100-command limit)
# Bot ime/avatar mijenjaj ručno preko Discord Developer Portal-a.

# ═══════════════════════════════════════════
#    MODERACIJA
# ═══════════════════════════════════════════
def _find_role_by_names(guild: discord.Guild, names: list):
    """Pronađi ulogu po nazivu (case-insensitive, zanemari razmake i dekorativne separatore).
    Tolerira: 〢 ║ ┃ │ ┊ ╏ ▎ ▏ ▌ ▍ ︙ ⫶ • · ・ ｜ | ‖ ╎ ┋ ┆ ┇ ┈ ┉ ─ ━ ═ ▪ ▫ ◆ ◇ ★ ☆"""
    SEP_CHARS = "〢║┃│┊╏▎▏▌▍︙⫶•·・｜|‖╎┋┆┇┈┉─━═▪▫◆◇★☆◈◉○●◎◍◌«»‹›„""''‚‛*=+~-_."
    def norm(s: str) -> str:
        s = s.lower()
        # Skini sve dekorativne separatore i razmake
        s = "".join(ch for ch in s if ch not in SEP_CHARS)
        s = re.sub(r"\s+", "", s)
        return s
    targets = [norm(n) for n in names]
    for r in guild.roles:
        if norm(r.name) in targets:
            return r
    return None

@bot.tree.command(name="ban", description="🔨 [VLASNIK / 〢 /GIAN] Ban korisnika")
async def ban(i: discord.Interaction, korisnik: discord.Member, razlog: str = "Bez razloga"):
    # ── Provjera pristupa: samo OWNER ili 〢 /GIAN član kojeg je vlasnik odobrio ──
    if i.user.id not in OWNER_IDS:
        gianni_ban_role = _find_role_by_names(i.guild, ["〢 /GIAN", "/GIAN", "〢/GIAN", "〢 /GIANNI", "/GIANNI", "〢/GIANNI"])
        has_gianni = gianni_ban_role is not None and gianni_ban_role in i.user.roles
        if not has_gianni:
            return await i.response.send_message(
                embed=em("❌ Pristup odbijen",
                         "Samo korisnici sa ulogom `〢 /GIAN` smiju koristiti `/ban`!",
                         color=COLORS["error"]),
                ephemeral=True)
        ban_allowed = str(i.user.id) in data.get("ban_allowed_ids", [])
        if not ban_allowed:
            return await i.response.send_message(
                embed=em("❌ Pristup odbijen",
                         "Vlasnik te još **nije odobrio** za korištenje `/ban`.\n"
                         "Kontaktiraj vlasnika — on koristi `/ban-dozvola add @ti` da te odobri.",
                         color=COLORS["error"]),
                ephemeral=True)

    if korisnik.top_role >= i.user.top_role:
        return await i.response.send_message(embed=em("❌ Greška", "Ne možeš ovo nekome sa višom ili istom ulogom!", color=COLORS["error"]), ephemeral=True)

    # ── VLASNIK → pravi Discord ban ──
    if i.user.id in OWNER_IDS:
        await korisnik.ban(reason=f"[VLASNIK BAN] {razlog}")
        return await i.response.send_message(embed=em("🔨 Banovan (Vlasnik)", color=COLORS["error"], thumb=korisnik.display_avatar.url, fields=[
            ("👤 Korisnik", f"{korisnik} (`{korisnik.id}`)", False),
            ("📝 Razlog", razlog, False), ("👑 Vlasnik", i.user.mention, False),
        ]))

    # ── STAFF → soft-ban: dodaj ulogu "Banned Permisson" ──
    banned_role = _find_role_by_names(i.guild, ["Banned Permisson", "Banned Permission", "Banned"])
    if not banned_role:
        return await i.response.send_message(embed=em("❌ Greška", "Uloga `Banned Permisson` ne postoji na serveru!\nKreiraj je ili javi vlasniku.", color=COLORS["error"]), ephemeral=True)
    if banned_role >= i.guild.me.top_role:
        return await i.response.send_message(embed=em("❌ Greška", f"Bot ne može dodijeliti `{banned_role.name}` jer je iznad njegove uloge!\nPomakni GIAN bot ulogu iznad nje.", color=COLORS["error"]), ephemeral=True)

    # Sačuvaj sve njegove uloge (osim @everyone) za moguće vraćanje
    saved_roles = [r.id for r in korisnik.roles if r != i.guild.default_role and r != banned_role]
    data.setdefault("soft_bans", {})[str(korisnik.id)] = {
        "guild_id": i.guild.id, "roles": saved_roles,
        "razlog": razlog, "moderator": i.user.id,
        "vreme": datetime.now(timezone.utc).strftime("%d.%m.%Y. %H:%M")
    }
    save_data()

    try:
        # Skini sve uloge i dodaj banned
        roles_to_remove = [r for r in korisnik.roles if r != i.guild.default_role and r < i.guild.me.top_role]
        if roles_to_remove:
            await korisnik.remove_roles(*roles_to_remove, reason=f"Soft-ban od {i.user}: {razlog}")
        await korisnik.add_roles(banned_role, reason=f"Soft-ban od {i.user}: {razlog}")
    except discord.Forbidden:
        return await i.response.send_message(embed=em("❌ Greška", "Bot nema permisiju da mijenja uloge ovom korisniku!", color=COLORS["error"]), ephemeral=True)

    # View sa dugmadima za vlasnika (Vrati uloge / Pravi Ban)
    class SoftBanView(discord.ui.View):
        def __init__(self, target_id: int, banned_role_id: int):
            super().__init__(timeout=None)
            self.target_id = target_id
            self.banned_role_id = banned_role_id

        @discord.ui.button(label="✅ Vrati Uloge", style=discord.ButtonStyle.success, custom_id=f"softban_restore_{korisnik.id}")
        async def restore(self, ii: discord.Interaction, btn: discord.ui.Button):
            if ii.user.id not in OWNER_IDS:
                return await ii.response.send_message("❌ Samo vlasnik može vratiti uloge.", ephemeral=True)
            target = ii.guild.get_member(self.target_id)
            if not target:
                return await ii.response.send_message("❌ Korisnik više nije na serveru.", ephemeral=True)
            sb = data.get("soft_bans", {}).get(str(self.target_id))
            if not sb:
                return await ii.response.send_message("❌ Nema sačuvanih uloga.", ephemeral=True)
            br = ii.guild.get_role(self.banned_role_id)
            try:
                if br and br in target.roles:
                    await target.remove_roles(br, reason=f"Restore od {ii.user}")
                roles_to_add = [ii.guild.get_role(rid) for rid in sb.get("roles", [])]
                roles_to_add = [r for r in roles_to_add if r and r < ii.guild.me.top_role]
                if roles_to_add:
                    await target.add_roles(*roles_to_add, reason=f"Restore od {ii.user}")
                data["soft_bans"].pop(str(self.target_id), None); save_data()
                await ii.response.send_message(f"✅ Vraćene uloge za {target.mention}", ephemeral=True)
            except Exception as e:
                await ii.response.send_message(f"❌ Greška: `{e}`", ephemeral=True)

        @discord.ui.button(label="🔨 Pravi Ban", style=discord.ButtonStyle.danger, custom_id=f"softban_hardban_{korisnik.id}")
        async def hardban(self, ii: discord.Interaction, btn: discord.ui.Button):
            if ii.user.id not in OWNER_IDS:
                return await ii.response.send_message("❌ Samo vlasnik može banovati.", ephemeral=True)
            target = ii.guild.get_member(self.target_id)
            if not target:
                return await ii.response.send_message("❌ Korisnik više nije na serveru.", ephemeral=True)
            try:
                await target.ban(reason=f"[VLASNIK] Pravi ban iz soft-ban panela ({ii.user})")
                data.get("soft_bans", {}).pop(str(self.target_id), None); save_data()
                await ii.response.send_message(f"🔨 {target} pravi banovan.", ephemeral=True)
            except Exception as e:
                await ii.response.send_message(f"❌ Greška: `{e}`", ephemeral=True)

    await i.response.send_message(embed=em("⛔ Soft-Ban (uloga Banned Permisson)", color=COLORS["error"], thumb=korisnik.display_avatar.url, fields=[
        ("👤 Korisnik", f"{korisnik.mention} (`{korisnik.id}`)", False),
        ("📝 Razlog", razlog, False),
        ("🛡️ Moderator", i.user.mention, True),
        ("ℹ️ Info", "Pravi Discord ban može uraditi **samo vlasnik** (dugmad ispod).", False),
    ]), view=SoftBanView(korisnik.id, banned_role.id))
    # DM vlasniku za odobrenje pravog bana
    for oid in OWNER_IDS:
        try:
            owner = await bot.fetch_user(oid)
            await owner.send(embed=em("🔔 Soft-Ban zahtijeva pažnju", color=COLORS["warning"], fields=[
                ("👤 Korisnik", f"{korisnik} (`{korisnik.id}`)", False),
                ("📝 Razlog", razlog, False),
                ("🛡️ Moderator", f"{i.user} (`{i.user.id}`)", False),
                ("🏠 Server", i.guild.name, True),
                ("⚖️ Akcija", "Vrati uloge ili pravi ban — kroz panel u serveru.", False),
            ]))
        except: pass

@bot.tree.command(name="ban-dozvola", description="👑 [VLASNIK] Dozvoli/oduzmi pravo na /ban za 〢 /GIAN člana")
async def ban_dozvola(i: discord.Interaction, akcija: str, korisnik: discord.Member):
    """
    akcija: "add" (dodaj dozvolu) ili "remove" (ukloni dozvolu)
    Samo vlasnici iz OWNER_IDS smiju koristiti ovu komandu.
    """
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("❌ Pristup odbijen", "Samo vlasnik može koristiti `/ban-dozvola`!", color=COLORS["error"]),
            ephemeral=True)
    akcija_norm = akcija.lower().strip()
    if akcija_norm not in ("add", "remove", "dodaj", "ukloni"):
        return await i.response.send_message(
            embed=em("❌ Greška", "Akcija mora biti `add` ili `remove`.\nPrimjer: `/ban-dozvola add @korisnik`", color=COLORS["error"]),
            ephemeral=True)
    allowed: list = data.setdefault("ban_allowed_ids", [])
    uid = str(korisnik.id)
    if akcija_norm in ("add", "dodaj"):
        if uid not in allowed:
            allowed.append(uid)
            save_data()
        return await i.response.send_message(
            embed=em("✅ Dozvola dodana",
                     f"{korisnik.mention} (`{korisnik}`) sada **može koristiti `/ban`**.\n"
                     f"⚠️ Mora imati ulogu `〢 /GIAN` da bi komanda radila.",
                     color=COLORS["success"]),
            ephemeral=True)
    else:
        if uid in allowed:
            allowed.remove(uid)
            save_data()
        return await i.response.send_message(
            embed=em("✅ Dozvola uklonjena",
                     f"{korisnik.mention} (`{korisnik}`) više **ne može koristiti `/ban`**.",
                     color=COLORS["warning"]),
            ephemeral=True)

@bot.tree.command(name="kick", description="👢 [VLASNIK] Pravi kick / [STAFF] dodjela /GIAN oznake")
@app_commands.default_permissions(kick_members=True)
@app_commands.checks.has_permissions(kick_members=True)
async def kick(i: discord.Interaction, korisnik: discord.Member, razlog: str = "Bez razloga"):
    if korisnik.top_role >= i.user.top_role:
        return await i.response.send_message(embed=em("❌ Greška", "Ne možeš ovo nekome sa višom ili istom ulogom!", color=COLORS["error"]), ephemeral=True)

    # ── VLASNIK → pravi kick ──
    if i.user.id in OWNER_IDS:
        await korisnik.kick(reason=f"[VLASNIK KICK] {razlog}")
        return await i.response.send_message(embed=em("👢 Izbačen (Vlasnik)", color=COLORS["warning"], thumb=korisnik.display_avatar.url, fields=[
            ("👤 Korisnik", f"{korisnik} (`{korisnik.id}`)", False),
            ("📝 Razlog", razlog, False), ("👑 Vlasnik", i.user.mention, False),
        ]))

    # ── STAFF → dodaj /GIAN ulogu kao oznaku upozorenja ──
    gianni_role = _find_role_by_names(i.guild, ["/GIAN", "/Gianni", "GIAN", "/GIANNI", "GIANNI"])
    if not gianni_role:
        return await i.response.send_message(embed=em("❌ Greška", "Uloga `/GIAN` ne postoji na serveru!\nKreiraj je ili javi vlasniku.", color=COLORS["error"]), ephemeral=True)
    if gianni_role >= i.guild.me.top_role:
        return await i.response.send_message(embed=em("❌ Greška", f"Bot ne može dodijeliti `{gianni_role.name}` jer je iznad njegove uloge!", color=COLORS["error"]), ephemeral=True)

    try:
        await korisnik.add_roles(gianni_role, reason=f"Soft-kick (oznaka) od {i.user}: {razlog}")
    except discord.Forbidden:
        return await i.response.send_message(embed=em("❌ Greška", "Bot nema permisiju!", color=COLORS["error"]), ephemeral=True)

    await i.response.send_message(embed=em("⚠️ Soft-Kick (oznaka /GIAN)", color=COLORS["warning"], thumb=korisnik.display_avatar.url, fields=[
        ("👤 Korisnik", f"{korisnik.mention} (`{korisnik.id}`)", False),
        ("📝 Razlog", razlog, False),
        ("🛡️ Moderator", i.user.mention, True),
        ("ℹ️ Info", "Pravi Discord kick može uraditi **samo vlasnik**. Dodijeljena oznaka `/GIAN`.", False),
    ]))
    for oid in OWNER_IDS:
        try:
            owner = await bot.fetch_user(oid)
            await owner.send(embed=em("🔔 Soft-Kick (oznaka /GIAN)", color=COLORS["warning"], fields=[
                ("👤 Korisnik", f"{korisnik} (`{korisnik.id}`)", False),
                ("📝 Razlog", razlog, False),
                ("🛡️ Moderator", f"{i.user} (`{i.user.id}`)", False),
                ("🏠 Server", i.guild.name, True),
            ]))
        except: pass

@bot.tree.command(name="timeout", description="⏱️ Ućutkaj korisnika")
@app_commands.default_permissions(moderate_members=True)
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout_cmd(i: discord.Interaction, korisnik: discord.Member, minuta: int = 10, razlog: str = "Bez razloga"):
    if not 1 <= minuta <= 1440:
        return await i.response.send_message(embed=em("❌ Greška", "Između 1 i 1440 minuta!", color=COLORS["error"]), ephemeral=True)
    await korisnik.timeout(discord.utils.utcnow() + timedelta(minutes=minuta), reason=razlog)
    await i.response.send_message(embed=em("⏱️ Ućutkan", color=COLORS["warning"], thumb=korisnik.display_avatar.url, fields=[
        ("👤 Korisnik", korisnik.mention, True), ("⏳ Trajanje", f"`{minuta}` min", True),
        ("📝 Razlog", razlog, False), ("🛡️ Moderator", i.user.mention, True),
    ]))

@bot.tree.command(name="warn", description="⚠️ Upozori korisnika")
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(i: discord.Interaction, korisnik: discord.Member, razlog: str = "Kršenje pravila"):
    warns = get_warnings(i.guild.id, korisnik.id)
    warns.append({"razlog": razlog, "moderator": str(i.user), "vreme": datetime.now(timezone.utc).strftime("%d.%m.%Y. %H:%M")})
    save_data()
    await i.response.send_message(embed=em("⚠️ Upozorenje", color=COLORS["warning"], thumb=korisnik.display_avatar.url, fields=[
        ("👤 Korisnik", korisnik.mention, True), ("📊 Ukupno", f"`{len(warns)}`", True),
        ("📝 Razlog", razlog, False), ("🛡️ Moderator", i.user.mention, True),
    ]))

@bot.tree.command(name="warnings", description="📋 Upozorenja korisnika")
@app_commands.checks.has_permissions(manage_messages=True)
async def warnings_cmd(i: discord.Interaction, korisnik: discord.Member):
    warns = get_warnings(i.guild.id, korisnik.id)
    if not warns:
        return await i.response.send_message(embed=em(f"📋 {korisnik.display_name}", "Nema upozorenja! ✅", color=COLORS["success"]), ephemeral=True)
    desc = "\n".join([f"`{n+1}.` **{w['razlog']}** — {w['vreme']}" for n, w in enumerate(warns)])
    await i.response.send_message(embed=em(f"📋 {korisnik.display_name} — Upozorenja", desc, color=COLORS["warning"], thumb=korisnik.display_avatar.url), ephemeral=True)

@bot.tree.command(name="clearwarnings", description="🗑️ Obriši upozorenja")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def clearwarnings(i: discord.Interaction, korisnik: discord.Member):
    data["warnings"].get(str(i.guild.id), {}).pop(str(korisnik.id), None)
    save_data()
    await i.response.send_message(embed=em("✅ Obrisano", f"Sva upozorenja za {korisnik.mention} su uklonjena.", color=COLORS["success"]), ephemeral=True)

@bot.tree.command(name="clear", description="🧹 Obriši poruke")
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(i: discord.Interaction, kolicina: int = 10):
    await i.response.defer(ephemeral=True)
    deleted = await i.channel.purge(limit=max(1, min(kolicina, 100)))
    await i.followup.send(embed=em("🧹 Čišćenje završeno", color=COLORS["success"], fields=[
        ("🗑️ Obrisano", f"`{len(deleted)}` poruka", True), ("📌 Kanal", i.channel.mention, True),
    ]), ephemeral=True)

# ═══════════════════════════════════════════
#    EKONOMIJA & LEVEL
# ═══════════════════════════════════════════
@bot.tree.command(name="baki", description="💰 Provjeri stanje novca")
async def baki(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    d = get_economy(u.id)
    last = time.strftime("%H:%M", time.localtime(d["last_work"])) if d["last_work"] else "Nikad"
    await i.response.send_message(embed=em_pro(f"💰 Novčanik", f"💎 Stanje računa za {u.mention}", color=COLORS["gold"], thumb=u.display_avatar.url, author=u, fields=[
        ("💶 Balans", f"```yaml\n{d['balance']:,} 💶\n```", True), ("💼 Poslednji posao", f"`{last}`", True),
    ]))

@bot.tree.command(name="posao", description="💼 Radi i zaradi (svakih 30 min)")
@app_commands.checks.cooldown(1, 1800, key=lambda i: i.user.id)
async def posao(i: discord.Interaction):
    cfg_p = _g_eco("posao")
    if not cfg_p.get("enabled", True):
        return await i.response.send_message(embed=em("⏸️ Isključeno", "Komanda `/posao` je trenutno isključena.", color=COLORS["warning"]), ephemeral=True)
    d = get_economy(i.user.id)
    earn = random.randint(int(cfg_p.get("reward_min", 150)), int(cfg_p.get("reward_max", 600)))
    d["balance"] += earn; d["last_work"] = time.time(); save_data()
    quest_progress(i.user.id, "work3")
    _poo_task_progress(i.guild.id if i.guild else 0, i.user.id, "work")
    await i.response.send_message(embed=em("💼 Posao završen!", f"*{random.choice(JOBS)}*", color=COLORS["success"], fields=[
        ("💶 Zarada", f"`+{earn} 💶`", True), ("🏦 Balans", f"`{d['balance']:,} 💶`", True), ("⏰ Sledeći", "za 30 min", True),
    ]))

@bot.tree.command(name="daily", description="🎁 Dnevna nagrada")
async def daily(i: discord.Interaction):
    cfg_d = _g_eco("daily")
    if not cfg_d.get("enabled", True):
        return await i.response.send_message(embed=em("⏸️ Isključeno", "Komanda `/daily` je trenutno isključena.", color=COLORS["warning"]), ephemeral=True)
    # 🔒 PERZISTENTNI cooldown — preživljava restart bota
    cooldown_secs = int(cfg_d.get("cooldown_hours", 24)) * 3600
    d = get_economy(i.user.id)
    now = time.time()
    last = float(d.get("last_daily", 0) or 0)
    elapsed = now - last
    if elapsed < cooldown_secs:
        remaining = int(cooldown_secs - elapsed)
        hours, rem = divmod(remaining, 3600)
        mins, secs = divmod(rem, 60)
        if hours:   wait_text = f"{hours}h {mins}min"
        elif mins:  wait_text = f"{mins}min {secs}s"
        else:       wait_text = f"{secs}s"
        return await i.response.send_message(
            embed=em("⏳ Cooldown!", f"Već si uzeo daily!\n\n⏰ Sačekaj još **{wait_text}**.", color=COLORS["warning"]),
            ephemeral=True
        )
    reward = random.randint(int(cfg_d.get("reward_min", 300)), int(cfg_d.get("reward_max", 800)))
    d["balance"] += reward
    d["last_daily"] = now
    save_data()
    quest_progress(i.user.id, "daily1")
    _poo_task_progress(i.guild.id if i.guild else 0, i.user.id, "daily")
    cd_label = f"za {cfg_d.get('cooldown_hours', 24)}h"
    await i.response.send_message(embed=em_pro("🎁 Daily Nagrada", "🌟 Tvoj poklon je stigao!", color=COLORS["gold"], author=i.user, thumb=i.user.display_avatar.url, fields=[
        ("💶 Nagrada", f"```diff\n+ {reward} 💶\n```", True), ("🏦 Balans", f"```yaml\n{d['balance']:,} 💶\n```", True), ("⏰ Sljedeći", cd_label, True),
    ]))

@bot.tree.command(name="daj", description="🤝 Pošalji pare drugaru")
async def daj(i: discord.Interaction, korisnik: discord.Member, iznos: int):
    if iznos <= 0: return await i.response.send_message(embed=em("❌ Greška", "Iznos mora biti pozitivan!", color=COLORS["error"]), ephemeral=True)
    if korisnik.id == i.user.id: return await i.response.send_message(embed=em("❌ Greška", "Ne možeš sebi slati!", color=COLORS["error"]), ephemeral=True)
    s, r = get_economy(i.user.id), get_economy(korisnik.id)
    if s["balance"] < iznos: return await i.response.send_message(embed=em("❌ Nemaš dovoljno", f"Imaš samo `{s['balance']:,} 💶`!", color=COLORS["error"]), ephemeral=True)
    s["balance"] -= iznos; r["balance"] += iznos; save_data()
    await i.response.send_message(embed=em("🤝 Transakcija uspešna", color=COLORS["success"], fields=[
        ("📤 Od", i.user.mention, True), ("📥 Za", korisnik.mention, True), ("💶 Iznos", f"`{iznos:,} 💶`", True),
    ]))

@bot.tree.command(name="kradi", description="🕵️ Pokušaj ukrasti (rizično!)")
@app_commands.checks.cooldown(1, 7200, key=lambda i: i.user.id)
async def kradi(i: discord.Interaction, korisnik: discord.Member):
    cfg_k = _g_eco("kradi")
    if not cfg_k.get("enabled", True):
        return await i.response.send_message(embed=em("⏸️ Isključeno", "Komanda `/kradi` je trenutno isključena.", color=COLORS["warning"]), ephemeral=True)
    if korisnik.id == i.user.id: return await i.response.send_message(embed=em("❌", "Ne možeš krasti sam sebe!", color=COLORS["error"]), ephemeral=True)
    if korisnik.bot: return await i.response.send_message(embed=em("❌", "Botovi nemaju para!", color=COLORS["error"]), ephemeral=True)
    s, r = get_economy(i.user.id), get_economy(korisnik.id)
    if r["balance"] < 100: return await i.response.send_message(embed=em("❌", "Siromašna žrtva, nema šta ukrasti.", color=COLORS["error"]), ephemeral=True)
    await i.response.defer()
    await asyncio.sleep(2)
    steal_max = int(cfg_k.get("steal_max", 300))
    steal_min = int(cfg_k.get("steal_min", 50))
    success_rate = float(cfg_k.get("success_rate", 38)) / 100.0
    amount = random.randint(steal_min, min(steal_max, r["balance"]))
    if random.random() < success_rate:
        r["balance"] -= amount; s["balance"] += amount
        e = em("🕵️ Krađa uspješna!", "Niko te nije video. Za sad... 👀", color=COLORS["gold"], fields=[
            ("💰 Ukradeno", f"`{amount:,} 💶`", True), ("👤 Žrtva", korisnik.mention, True), ("🏦 Balans", f"`{s['balance']:,} 💶`", True),
        ])
    else:
        fine = random.randint(100, 350)
        s["balance"] = max(0, s["balance"] - fine)
        e = em("🚔 Uhvaćen si!", f"{korisnik.mention} te je prijavio policiji! 🤡", color=COLORS["error"], fields=[
            ("💸 Kazna", f"`{fine:,} 💶`", True), ("🏦 Balans", f"`{s['balance']:,} 💶`", True),
        ])
    save_data(); await i.followup.send(embed=e)

@bot.tree.command(name="rank", description="📈 Level i XP")
async def rank(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    d = get_xp(u.id)
    needed = d["level"] * 75
    filled = min(d["xp"] * 10 // needed, 10)
    bar = "🟪" * filled + "⬛" * (10 - filled)
    pct = round(d["xp"] / needed * 100)
    await i.response.send_message(embed=em_pro(f"📈 Rank Profil", f"{bar}\n`{'▰'*filled}{'▱'*(10-filled)}` **{pct}%**", color=COLORS["purple"], thumb=u.display_avatar.url, author=u, fields=[
        ("🏆 Level", f"```fix\n{d['level']}\n```", True), ("⭐ XP", f"```py\n{d['xp']}/{needed}\n```", True), ("📊 Progres", f"```css\n[{pct}%]\n```", True),
    ]))

# ═══════════════════════════════════════════
#    /aktivnost — prikaz LVL / XP / poruke
# ═══════════════════════════════════════════
@bot.tree.command(name="aktivnost", description="📊 Tvoja aktivnost: level, XP i broj poruka")
@discord.app_commands.describe(korisnik="Čija statistika? (default: ti)")
async def aktivnost(i: discord.Interaction, korisnik: discord.Member = None):
    u = korisnik or i.user
    gid = i.guild.id if i.guild else 0
    mkey = f"{gid}:{u.id}"
    msgs = int(data.get("msg_count", {}).get(mkey, 0))
    xp_d = get_xp(u.id)
    lvl  = int(xp_d.get("level", 1))
    xp   = int(xp_d.get("xp", 0))
    vat  = _get_vatrice(gid, u.id) if gid else 0

    # Napredak do sljedećeg levela (svakih 100 poruka)
    do_sljedeceg = 100 - (msgs % 100) if msgs % 100 != 0 else 100
    proslo = msgs % 100
    filled = min(proslo // 10, 10)
    bar = "🟧" * filled + "⬛" * (10 - filled)

    sep = "━━━━━━━━━━━━━━━━━━━━"
    desc = (
        f"{sep}\n"
        f"👤 **{u.display_name}**\n"
        f"{sep}\n"
        f"{bar}  `{proslo}/100`\n"
        f"⏳ Još **`{do_sljedeceg}`** poruka do sljedećeg levela!\n"
    )
    e = discord.Embed(
        title="📊 ᴀᴋᴛɪᴠɴᴏsᴛ",
        description=desc,
        color=0xFFA500,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_thumbnail(url=u.display_avatar.url)
    e.add_field(name="🏆 Level",    value=f"```fix\n★ {lvl} ★\n```", inline=True)
    e.add_field(name="⭐ XP",       value=f"```py\n{xp:,}\n```",      inline=True)
    e.add_field(name="💬 Poruke",   value=f"```css\n{msgs:,}\n```",   inline=True)
    e.add_field(name="🔥 Vatrice",  value=f"```yaml\n{vat}\n```",     inline=True)
    e.add_field(name="📈 Sistem",   value="```ini\n[100 poruka = 1 LVL + 1 vatrica + 100 XP]\n```", inline=False)
    e.set_footer(text=f"⚡ {BOT_NAME} • Aktivnost • Svakih 100 poruka novi level!")
    await i.response.send_message(embed=e)

# ═══════════════════════════════════════════
#    /vers — hip-hop rima u stylish embedu
# ═══════════════════════════════════════════
VERS_CHANNEL_ID = 1498983966005268520

@bot.tree.command(name="vers", description="🎤 Pošalji rimu / vers u hip-hop stylish embedu")
@discord.app_commands.describe(text="Tvoj vers / rima / lyrics — može i u navodnicima")
async def vers(i: discord.Interaction, text: str):
    text = (text or "").strip().strip('"').strip("'").strip("-").strip()
    if not text:
        return await i.response.send_message(
            embed=em("❌ Prazan vers", "Napiši tekst rime, npr:\n`.vers \"lolo ako odem odavde...\"`", color=COLORS["error"]),
            ephemeral=True
        )
    # razlomi po zarezima/tačkama u stihove
    raw_lines = []
    cur = ""
    for ch in text:
        cur += ch
        if ch in ",.!?":
            raw_lines.append(cur.strip(" ,.!?").strip())
            cur = ""
    if cur.strip():
        raw_lines.append(cur.strip(" ,.!?").strip())
    raw_lines = [l for l in raw_lines if l]
    if not raw_lines:
        raw_lines = [text]

    # mali, čist hip-hop card — bez ogromnih bannera
    stihovi = "\n".join(f"*{ln}*" for ln in raw_lines)
    desc = f"> 🎙️\n> {stihovi}\n> 🎤"

    e = discord.Embed(
        description=desc,
        color=0x9B30FF,
    )
    e.set_author(name=f"{i.user.display_name}", icon_url=i.user.display_avatar.url)
    e.set_footer(text="🎧 vers • drop the mic")

    target_ch = i.guild.get_channel(VERS_CHANNEL_ID) if i.guild else None
    if target_ch is None:
        target_ch = i.channel
    try:
        await target_ch.send(embed=e)
    except Exception as _e:
        return await i.response.send_message(
            embed=em("❌ Greška", f"Ne mogu slati u <#{VERS_CHANNEL_ID}>.\n`{_e}`", color=COLORS["error"]),
            ephemeral=True
        )
    if target_ch.id != (i.channel.id if i.channel else 0):
        await i.response.send_message(
            embed=em("✅ Vers objavljen!", f"Tvoja rima je otišla u {target_ch.mention} 🎤🔥", color=COLORS["success"]),
            ephemeral=True
        )
    else:
        await i.response.send_message(
            embed=em("🎤 Drop the mic!", "Vers postavljen iznad 🔥", color=COLORS["success"]),
            ephemeral=True
        )

@bot.tree.command(name="leaderboard", description="🏅 Top lista servera")
@app_commands.choices(tip=[app_commands.Choice(name="XP & Leveli", value="xp"), app_commands.Choice(name="Novac 💶", value="novac")])
async def leaderboard(i: discord.Interaction, tip: str = "xp"):
    await i.response.defer()
    medals = ["🥇", "🥈", "🥉"]
    if tip == "xp":
        srt = sorted(data["xp"].items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]
        lines = []
        for n, (uid, d) in enumerate(srt):
            try: user = await bot.fetch_user(int(uid)); name = user.display_name
            except: name = f"#{uid[:4]}"
            lines.append(f"{medals[n] if n<3 else f'`{n+1}.`'} **{name}** — Level `{d['level']}` • `{d['xp']} XP`")
        e = em("🏅 Top Lista — XP", "\n".join(lines) or "Nema podataka.", color=COLORS["purple"])
    else:
        srt = sorted(data["economy"].items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
        lines = []
        for n, (uid, d) in enumerate(srt):
            try: user = await bot.fetch_user(int(uid)); name = user.display_name
            except: name = f"#{uid[:4]}"
            lines.append(f"{medals[n] if n<3 else f'`{n+1}.`'} **{name}** — `{d['balance']:,} 💶`")
        e = em("🏅 Top Lista — Bogatstvo", "\n".join(lines) or "Nema podataka.", color=COLORS["gold"])
    await i.followup.send(embed=e)

# ═══════════════════════════════════════════
#    IGRE
# ═══════════════════════════════════════════
class KPM(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30); self.user = user; self.msg = None

    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if self.msg: await self.msg.edit(embed=em("⏱️ Vreme isteklo!", "Igra otkazana.", color=COLORS["error"]), view=self)

    async def play(self, i, choice):
        if i.user != self.user: return await i.response.send_message(embed=em("❌", "Nije tvoja igra!", color=COLORS["error"]), ephemeral=True)
        bot_c = random.choice(["🪨 Kamen", "📄 Papir", "✂️ Makaze"])
        win_map = {("Kamen","Makaze"),("Papir","Kamen"),("Makaze","Papir")}
        cw, bw = choice.split()[1], bot_c.split()[1]
        if choice == bot_c: res, color = "🤝 Nerešeno!", COLORS["warning"]
        elif (cw, bw) in win_map: res, color = "🏆 Pobedio si!", COLORS["success"]
        else: res, color = "💀 Izgubio si!", COLORS["error"]
        for c in self.children: c.disabled = True
        await i.response.edit_message(embed=em(f"🎮 KPM — {res}", color=color, fields=[
            ("👤 Ti", choice, True), ("🤖 Bot", bot_c, True), ("📊 Rezultat", res, False),
        ]), view=self); self.stop()

    @discord.ui.button(label="Kamen",  emoji="🪨", style=discord.ButtonStyle.primary)
    async def r(self, i, b): await self.play(i, "🪨 Kamen")
    @discord.ui.button(label="Papir",  emoji="📄", style=discord.ButtonStyle.success)
    async def p(self, i, b): await self.play(i, "📄 Papir")
    @discord.ui.button(label="Makaze", emoji="✂️", style=discord.ButtonStyle.danger)
    async def s(self, i, b): await self.play(i, "✂️ Makaze")

@bot.tree.command(name="kpm", description="🎮 Kamen-Papir-Makaze")
async def kpm(i: discord.Interaction):
    v = KPM(i.user)
    await i.response.send_message(embed=em("🎮 Kamen-Papir-Makaze", f"{i.user.mention}, odaberi potez! ⏱️ 30s", color=COLORS["balkan"]), view=v)
    v.msg = await i.original_response()

@bot.tree.command(name="slots", description="🎰 Slot mašina — uloži od 20 do 1.000.000.000 💶")
@app_commands.describe(ulog="Iznos uloga (min 20 — max 1.000.000.000)")
@app_commands.checks.cooldown(1, 15, key=lambda i: i.user.id)
async def slots(i: discord.Interaction, ulog: int = 100):
    _poo_task_progress(i.guild.id if i.guild else 0, i.user.id, "slots")
    SLOTS_MIN = 20
    SLOTS_MAX = 1_000_000_000

    if ulog < SLOTS_MIN:
        return await i.response.send_message(
            embed=em("❌ Premali ulog", f"Minimalan ulog je **{SLOTS_MIN:,} 💶**.", color=COLORS["error"]),
            ephemeral=True
        )
    if ulog > SLOTS_MAX:
        return await i.response.send_message(
            embed=em("❌ Preveliki ulog", f"Maksimalan ulog je **{SLOTS_MAX:,} 💶**.", color=COLORS["error"]),
            ephemeral=True
        )

    d = get_economy(i.user.id)
    if d["balance"] < ulog:
        return await i.response.send_message(
            embed=em(
                "❌ Nemaš dovoljno",
                f"Trebaš **{ulog:,} 💶** a imaš samo **{d['balance']:,} 💶**.",
                color=COLORS["error"]
            ),
            ephemeral=True
        )

    await i.response.defer()

    # ─── Simboli i težine ───────────────────────────────────────────────
    SLOT_DATA = [
        ("🍒", 22, 3.0,  0.5),
        ("🍋", 20, 3.5,  0.6),
        ("🍊", 18, 4.0,  0.7),
        ("🍇", 15, 5.0,  0.8),
        ("🔔", 12, 6.0,  0.9),
        ("⭐",  8, 8.0,  1.2),
        ("💎",  4, 15.0, 1.8),
        ("7️⃣",  1, 50.0, 2.5),
    ]
    symbols_list  = [s[0] for s in SLOT_DATA]
    weights       = [s[1] for s in SLOT_DATA]
    jackpot_multi = {s[0]: s[2] for s in SLOT_DATA}
    pair_multi    = {s[0]: s[3] for s in SLOT_DATA}

    # Unaprijed izaberi krajnji rezultat
    reels = random.choices(symbols_list, weights=weights, k=3)
    sym   = reels[0]

    # ─── Animacija ──────────────────────────────────────────────────────
    SPIN = "🎰"  # simbol vrtnje
    def _sr(): return random.choice(symbols_list)  # random simbol za vrtnju

    def _spin_embed(r1, r2, r3, subtitle="🎰  Vrte se..."):
        desc = f"𓉘  {r1}  │  {r2}  │  {r3}  𓉝"
        e = discord.Embed(
            title=f"🎰  S L O T  M A Š I N A",
            description=desc,
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc)
        )
        e.add_field(name="💰 Ulog", value=f"`{ulog:,} 💶`", inline=True)
        e.add_field(name="⏳ Status", value=subtitle, inline=True)
        e.set_footer(text=f"{i.user.display_name} • {BOT_NAME}")
        return e

    # Frame 0 — sve se vrte
    msg = await i.followup.send(embed=_spin_embed(_sr(), _sr(), _sr()), wait=True)

    # Frame 1-2 — sve se vrte (random)
    for _ in range(2):
        await asyncio.sleep(0.55)
        try: await msg.edit(embed=_spin_embed(_sr(), _sr(), _sr()))
        except: pass

    # Frame 3 — prvi valjak staje
    await asyncio.sleep(0.65)
    try: await msg.edit(embed=_spin_embed(reels[0], _sr(), _sr(), f"🔒 Stao: {reels[0]}"))
    except: pass

    # Frame 4 — drugi valjak staje
    await asyncio.sleep(0.7)
    try: await msg.edit(embed=_spin_embed(reels[0], reels[1], _sr(), f"🔒 Stao: {reels[0]} {reels[1]}"))
    except: pass

    # Frame 5 — treći valjak staje (kratka pauza za dramski efekat)
    await asyncio.sleep(0.75)

    # ─── Odluka ─────────────────────────────────────────────────────────
    if reels[0] == reels[1] == reels[2]:
        multiplier = jackpot_multi[sym]
        win        = int(ulog * multiplier)
        net        = win - ulog
        d["balance"] += net
        color = COLORS["gold"]
        if sym in ("💎", "7️⃣"):
            title  = "💎  M E G A  J A C K P O T  💎"
            result = f"🤑 **+{win:,} 💶** *(×{multiplier:.0f})*"
            footer_extra = "🏆 NEVJEROVATAN POGODAK!"
        else:
            title  = "🎉  J A C K P O T  🎉"
            result = f"🎊 **+{win:,} 💶** *(×{multiplier:.1f})*"
            footer_extra = "Sva tri ista!"
        outcome = "jackpot"

    elif reels[0] == reels[1] or reels[1] == reels[2]:
        mid        = reels[1]
        multiplier = pair_multi[mid]
        win        = int(ulog * multiplier)
        net        = win - ulog
        if net >= 0:
            d["balance"] += net
            color  = COLORS["success"]
            title  = "✨  D O B I T A K  ✨"
            result = f"💚 **+{win:,} 💶** *(×{multiplier:.1f})*"
        else:
            d["balance"] = max(0, d["balance"] + net)
            color  = COLORS["warning"]
            title  = "😬  M A L I  G U B I T A K"
            result = f"🟡 **{net:,} 💶** *(×{multiplier:.1f})*"
        footer_extra = "Dva ista simbola — par!"
        outcome = "pair"

    else:
        d["balance"] = max(0, d["balance"] - ulog)
        color  = COLORS["error"]
        title  = "💸  N I Š T A . . ."
        result = f"❌ **−{ulog:,} 💶**"
        footer_extra = "Nema sreće ovaj put"
        outcome = "loss"

    save_data()

    # ─── Finalni embed ────────────────────────────────────────────────────
    slot_line = f"𓉘  {reels[0]}  │  {reels[1]}  │  {reels[2]}  𓉝"
    if outcome == "jackpot":
        final_desc = f"{slot_line}\n\n🎰 Sva tri ista — **JACKPOT!**"
    elif outcome == "pair":
        final_desc = f"{slot_line}\n\n🎯 Dva ista simbola — **par!**"
    else:
        final_desc = f"{slot_line}\n\n😢 Nema kombinacije. Pokušaj ponovo!"

    final_e = discord.Embed(
        title=f"🎰  {title}",
        description=final_desc,
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    final_e.add_field(name="💰 Ulog",     value=f"`{ulog:,} 💶`",         inline=True)
    final_e.add_field(name="🎯 Rezultat", value=result,                   inline=True)
    final_e.add_field(name="🏦 Balans",   value=f"`{d['balance']:,} 💶`", inline=True)
    final_e.set_footer(text=f"{BOT_NAME} • {footer_extra} • 🍒×3 🍋×3.5 🍊×4 🍇×5 🔔×6 ⭐×8 💎×15 7️⃣×50")

    try:
        await msg.edit(embed=final_e)
    except Exception:
        await i.followup.send(embed=final_e)

# /rulet uklonjeno (na zahtjev) — /flip i /8ball uklonjeni (v2.2) — pravimo mjesto za /mafia igru.
# /meme uklonjeno (v2.1) — vanjski sadržaj može vratiti NSFW u SFW kanal.

# ═══════════════════════════════════════════
#    VJEŠALA (Hangman)
# ═══════════════════════════════════════════
class VjesalaModal(discord.ui.Modal, title="Unesi slovo"):
    slovo = discord.ui.TextInput(label="Slovo (jedno)", min_length=1, max_length=1, placeholder="Npr: A")

    def __init__(self, hangman_view):
        super().__init__()
        self.hv = hangman_view

    async def on_submit(self, i: discord.Interaction):
        await self.hv.guess(i, self.slovo.value.upper().strip())

class VjesalaView(discord.ui.View):
    def __init__(self, user: discord.Member, word: str):
        super().__init__(timeout=300)
        self.user    = user
        self.word    = word.upper()
        self.guessed: set = set()
        self.wrong   = 0
        self.max_w   = 6
        self.over    = False

    def display_word(self):
        return " ".join(c if c in self.guessed else "\\_ " for c in self.word)

    def make_embed(self, title=None, color=None):
        wrong_letters = [l for l in sorted(self.guessed) if l not in self.word]
        right_letters = [l for l in sorted(self.guessed) if l in self.word]
        t = title or "🎮 Vješala"
        c = color or COLORS["balkan"]
        e = discord.Embed(title=t, color=c, timestamp=datetime.now(timezone.utc))
        e.add_field(name="🔤 Riječ", value=f"`{self.display_word()}`", inline=False)
        e.add_field(name="💀 Vješalo", value=VJASALA_FAZE[self.wrong], inline=True)
        e.add_field(name="❌ Pogrešna", value=" ".join(wrong_letters) or "—", inline=True)
        e.add_field(name="✅ Tačna", value=" ".join(right_letters) or "—", inline=True)
        e.add_field(name="❤️ Životi", value=f"`{self.max_w - self.wrong}/{self.max_w}`", inline=True)
        e.set_footer(text=f"{BOT_NAME} {VERSION} • Pogodi slovo klikom!")
        return e

    async def guess(self, i: discord.Interaction, letter: str):
        if i.user != self.user:
            return await i.response.send_message(embed=em("❌", "Nije tvoja igra!", color=COLORS["error"]), ephemeral=True)
        if not letter.isalpha():
            return await i.response.send_message(embed=em("❌", "Unesi samo slovo!", color=COLORS["error"]), ephemeral=True)
        if letter in self.guessed:
            return await i.response.send_message(embed=em("⚠️", f"Slovo **{letter}** si već pokušao!", color=COLORS["warning"]), ephemeral=True)
        self.guessed.add(letter)
        if letter not in self.word:
            self.wrong += 1
        won  = all(c in self.guessed for c in self.word)
        lost = self.wrong >= self.max_w
        if won:
            self.over = True; self.children[0].disabled = True
            await i.response.edit_message(embed=self.make_embed(f"🏆 Pobijedio si! Riječ: **{self.word}**", COLORS["success"]), view=self)
            self.stop()
        elif lost:
            self.over = True; self.children[0].disabled = True
            await i.response.edit_message(embed=self.make_embed(f"💀 Izgubio si! Bila je: **{self.word}**", COLORS["error"]), view=self)
            self.stop()
        else:
            await i.response.edit_message(embed=self.make_embed(), view=self)

    async def on_timeout(self):
        if not self.over:
            self.children[0].disabled = True
            try:
                await self.message.edit(embed=self.make_embed(f"⏱️ Vreme isteklo! Bila je: **{self.word}**", COLORS["error"]), view=self)
            except: pass

    @discord.ui.button(label="Unesi slovo", style=discord.ButtonStyle.primary, emoji="✏️")
    async def enter(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user != self.user:
            return await i.response.send_message(embed=em("❌", "Nije tvoja igra!", color=COLORS["error"]), ephemeral=True)
        await i.response.send_modal(VjesalaModal(self))

    @discord.ui.button(label="Predaj se", emoji="🏳️", style=discord.ButtonStyle.danger)
    async def give_up(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user != self.user:
            return await i.response.send_message(embed=em("❌", "Nije tvoja igra!", color=COLORS["error"]), ephemeral=True)
        self.over = True
        for c in self.children: c.disabled = True
        await i.response.edit_message(embed=self.make_embed(f"🏳️ Predao si! Bila je: **{self.word}**", COLORS["warning"]), view=self)
        self.stop()

@bot.tree.command(name="vjasala", description="🎮 Igra Vješala — pogodi skrivenu riječ!")
async def vjasala(i: discord.Interaction):
    _poo_task_progress(i.guild.id if i.guild else 0, i.user.id, "vjasala")
    word = random.choice(VJASALA_RJECNIK)
    v    = VjesalaView(i.user, word)
    await i.response.send_message(embed=v.make_embed(), view=v)
    v.message = await i.original_response()

# ═══════════════════════════════════════════
#    KALADONT
# ═══════════════════════════════════════════
_KALADONT_START_RAW = [
    "BALKON","RAKIJA","KAFANA","FUDBAL","TANJIR","SUNCE","ZIVOT","RIJEKA",
    "PLANINA","DRVO","KAMEN","VATRA","ZEMLJA","VJETAR","OBLAK","JEZERO",
    "MOST","GRAD","SELO","POLJE","BRDO","DOLINA","SPILJA","OCEAN",
    "MAJKA","OTAC","BRAT","SESTRA","BAKA","DJED","PRIJATELJ","KOMŠIJA",
    "GITARA","MUZIKA","PJESMA","PLES","RADIO","POZORIŠTE","BIOSKOP",
    "AUTOMOBIL","AVION","BROD","VAGON","BICIKL","MOTOCIKL","TRAKTOR",
    "JABUKA","KRUŠKA","ŠLJIVA","TREŠNJA","BANANA","NARANDZA","GROŽĐE",
    "CEVAPI","BUREK","SARMA","KAJMAK","PITA","PALAČINKA","KOLAC",
    "ŠKOLA","BOLNICA","CRKVA","DŽAMIJA","STADION","BIBLIOTEKA","MUZEJ",
]
# Normaliziraj sve start-words (skidanje dijakritika) i osiguraj da su u rječniku
KALADONT_START_WORDS = [_kaladont_normalize(w) for w in _KALADONT_START_RAW]
for _w in KALADONT_START_WORDS:
    KALADONT_DICT.add(_w)

kaladont_games: dict = {}  # channel_id -> {word, used, starter, letters, chain, msg}

KALADONT_ICONS = ["✨","⚡","🔥","💫","🌊","🍀","🎯","💥","🌟","🎪","💎","🎭","🚀","🦋","🐉","🎶"]
KALADONT_COLOR = 0xF1C40F   # aqua — konzistentno s ostatkom bota

def kaladont_start_embed(game: dict, mention: str):
    word    = game["word"]
    letters = game["letters"]
    req     = word[-letters:]
    tezina_map = {1: "🟢 Lako · 1 slovo", 2: "🟡 Normalno · 2 slova", 3: "🔴 Teško · 3 slova"}
    tezina = tezina_map.get(letters, f"⚙️ {letters} slova")
    e = discord.Embed(
        title="🔤  K A L A D O N T",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ Igra je počela! Prva riječ:\n"
            f"## 💬  **{word}**\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=KALADONT_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="➡️  Sljedeća počinje sa", value=f"## **`{req}`**",   inline=True)
    e.add_field(name="⚙️  Težina",              value=tezina,              inline=True)
    e.add_field(name="🔗  Niz",                 value="**#1**",            inline=True)
    e.add_field(
        name="📖  Pravila igre",
        value=(
            "✅  Svaka riječ počinje traženim slovima\n"
            "🚫  Ista osoba **ne može** igrati iza sebe\n"
            "🔁  Ponavljanje iste riječi nije dozvoljeno\n"
            "✍️  Minimalno **3 slova** po riječi\n"
            "🆘  Pritisni **Pomoć** za primjer riječi\n"
            "🏆  Upiši **`KALADONT`** i osvoji **1500** 🪙 + **200** ✨ XP!"
        ),
        inline=False
    )
    e.set_footer(text=f"🔤 Pokrenuo/la: {mention}  •  🏁 Pritisni dugme za kraj")
    return e

def kaladont_active_embed(game: dict):
    word    = game["word"]
    letters = game["letters"]
    req     = word[-letters:]
    count   = len(game["chain"])
    last_player = game.get("last_player_name", "—")
    icon    = KALADONT_ICONS[(count - 1) % len(KALADONT_ICONS)]
    streak_fx = E_FIRE1 if count < 5 else (E_FIRE2 if count < 10 else (E_FIRE3 if count < 20 else E_FIRE4))
    e = discord.Embed(
        title=f"{E_GAME}  K A L A D O N T  {E_GAME}",
        description=f"{E_FIRE1}{E_FIRE2}{E_FIRE3}{E_FIRE4}  **aktivna igra**  {E_FIRE4}{E_FIRE3}{E_FIRE2}{E_FIRE1}",
        color=KALADONT_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name=f"{icon}  Zadnja riječ",    value=f"**`{word}`**",     inline=True)
    e.add_field(name="🗣️  Odigrao/la",           value=last_player,         inline=True)
    e.add_field(name=f"{streak_fx}  Niz",        value=f"**#{count}**",     inline=True)
    e.add_field(name="➡️  Sljedeća počinje sa",  value=f"## **`{req}`**",   inline=False)
    e.set_footer(text="🏁 Pritisni dugme za kraj igre")
    return e

def kaladont_word_card(word: str, player: str, req: str, count: int):
    icon = KALADONT_ICONS[(count - 1) % len(KALADONT_ICONS)]
    streak_fx = E_FIRE1 if count < 5 else (E_FIRE2 if count < 10 else (E_FIRE3 if count < 20 else E_FIRE4))
    e = discord.Embed(
        description=(
            f"## {icon}  **{word}**\n"
            f"*🗣️ {player}*  ·  {streak_fx} **niz #{count}**"
        ),
        color=KALADONT_COLOR,
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="➡️  Sljedeća počinje sa",  value=f"## **`{req}`**",   inline=True)
    e.add_field(name=f"{streak_fx}  Niz",        value=f"**#{count}**",     inline=True)
    e.set_footer(text=f"GIAN Kaladont  •  #{count}")
    return e

# ── Kaladont pomoć cooldown: uid -> timestamp zadnjeg klika ──
_kaladont_help_cd: dict = {}
KALADONT_HELP_CD = 15 * 60  # 15 minuta u sekundama

async def _send_kaladont_help(i: discord.Interaction, channel_id: int):
    """Zajednička logika za Pomoć dugme — koristi se i u KaladontView i KaladontWordView."""
    # ── 15-minuta cooldown po korisniku ──
    now = time.time()
    last = _kaladont_help_cd.get(i.user.id, 0)
    remaining = KALADONT_HELP_CD - (now - last)
    if remaining > 0 and i.user.id not in OWNER_IDS:
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        wait = f"{mins}m {secs}s" if mins else f"{secs}s"
        return await i.response.send_message(
            embed=em("⏳ Cooldown", f"Možeš ponovo kliknuti Pomoć za **{wait}**.", color=COLORS["warning"]),
            ephemeral=True
        )
    _kaladont_help_cd[i.user.id] = now

    game = kaladont_games.get(channel_id)
    if not game:
        return await i.response.send_message(
            embed=em("❌", "Nema aktivne igre.", color=COLORS["error"]), ephemeral=True
        )
    req   = game["word"][-game["letters"]:]
    used  = game.get("used", set())
    hints = get_kaladont_hint(req, used)
    if hints:
        hint_text = "  ·  ".join(f"`{w}`" for w in hints)
        desc = (
            f"Sljedeća mora početi sa **`{req}`**\n\n"
            f"💡 **Primjeri iz baze:**\n{hint_text}\n\n"
            f"*Možeš koristiti i bilo koju drugu imenicu/glagol/pridjev!*"
        )
    else:
        desc = (
            f"Sljedeća mora početi sa **`{req}`**\n\n"
            f"💡 Nema primjera u bazi za **`{req}`**, ali probaj:\n"
            f"Imenice, glagoli, pridjevi koji počinju sa `{req}`.\n"
            f"*(Npr. ako je `{req}` → razmisli o riječima koje počinju tim slovima)*"
        )
    e = discord.Embed(
        title=f"🆘 Pomoć — počni sa `{req}`",
        description=desc,
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text="🔤 Kaladont Pomoć • samo ti vidiš ovo • cooldown 15 min")
    await i.response.send_message(embed=e, ephemeral=True)


class KaladontView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="Pomoć", emoji="🆘", style=discord.ButtonStyle.secondary, row=0)
    async def pomoc(self, i: discord.Interaction, b: discord.ui.Button):
        await _send_kaladont_help(i, self.channel_id)

    @discord.ui.button(label="Završi igru", emoji="🏁", style=discord.ButtonStyle.danger, row=0)
    async def zavrsi(self, i: discord.Interaction, b: discord.ui.Button):  # type: ignore
        game = kaladont_games.get(self.channel_id)
        if not game:
            return await i.response.send_message(embed=em("❌", "Nema aktivne igre.", color=COLORS["error"]), ephemeral=True)
        if i.user.id != game["starter"] and not i.user.guild_permissions.manage_messages:
            return await i.response.send_message(embed=em("❌", "Samo pokretač ili mod može završiti igru!", color=COLORS["error"]), ephemeral=True)
        count = len(game["chain"])
        del kaladont_games[self.channel_id]
        b.disabled = True
        e = discord.Embed(
            title="🏁 Kaladont završen!",
            description=f"Igra gotova! Ukupno izgovoreno **{count}** rijeci. 🎉",
            color=COLORS["gold"], timestamp=datetime.now(timezone.utc)
        )
        e.set_footer(text=f"{BOT_NAME} {VERSION}")
        await i.response.edit_message(embed=e, view=self)
        self.stop()


class KaladontWordView(discord.ui.View):
    """Mala view ispod svakog word-card embeda — samo dugme Pomoć sa 15-min cooldownom."""
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @discord.ui.button(label="Pomoć", emoji="🆘", style=discord.ButtonStyle.secondary)
    async def pomoc(self, i: discord.Interaction, b: discord.ui.Button):
        await _send_kaladont_help(i, self.channel_id)


@bot.tree.command(name="kaladont", description="🔤 Pokretanje igre Kaladont — ulančaj riječi!")
@app_commands.describe(slova="Koliko zadnjih slova mora nova rijec početi (1, 2 ili 3)")
@app_commands.choices(slova=[
    app_commands.Choice(name="1 slovo (lakše)", value=1),
    app_commands.Choice(name="2 slova (normalno)", value=2),
    app_commands.Choice(name="3 slova (teže)", value=3),
])
async def kaladont(i: discord.Interaction, slova: int = 2):
    if i.channel.id in kaladont_games:
        return await i.response.send_message(
            embed=em("⚠️ Igra već teče!", "U ovom kanalu je već aktivan Kaladont. Završi prvu!", color=COLORS["warning"]), ephemeral=True)
    start_word = random.choice(KALADONT_START_WORDS)
    game = {
        "word":             start_word,
        "used":             {start_word},
        "starter":          i.user.id,
        "letters":          slova,
        "chain":            [(start_word, "🤖 Bot")],
        "msg":              None,
        "last_uid":         None,        # ko je zadnji odigrao (None = bot, svi mogu)
        "last_player_name": "🤖 Bot",
    }
    kaladont_games[i.channel.id] = game
    v = KaladontView(i.channel.id)
    await i.response.send_message(embed=kaladont_start_embed(game, i.user.display_name), view=v)
    resp = await i.original_response()
    game["msg"] = resp

@bot.tree.command(name="kaladont-stop", description="🔤 Zaustavi trenutnu Kaladont igru u ovom kanalu")
async def kaladont_stop(i: discord.Interaction):
    game = kaladont_games.get(i.channel.id)
    if not game:
        return await i.response.send_message(
            embed=em("ℹ️", "Nema aktivne Kaladont igre u ovom kanalu.", color=COLORS["info"]),
            ephemeral=True
        )
    is_admin = i.user.guild_permissions.administrator
    if i.user.id != game["starter"] and not is_admin:
        return await i.response.send_message(
            embed=em("🚫", "Samo onaj ko je pokrenuo igru ili admin može zaustaviti!", color=COLORS["error"]),
            ephemeral=True
        )
    chain = game.get("chain", [])
    count = len(chain)
    last_word = game.get("word", "—")
    del kaladont_games[i.channel.id]
    e = discord.Embed(
        title="🛑 Kaladont zaustavljen",
        description=(
            f"Igru zaustavio: {i.user.mention}\n\n"
            f"📊 **Riječi u nizu:** `{count}`\n"
            f"🔤 **Zadnja riječ:** `{last_word}`"
        ),
        color=COLORS["warning"], timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.response.send_message(embed=e)

# ═══════════════════════════════════════════
#    WORDLE — pogodi skrivenu riječ od 5 slova
#    Riječi: UPPERCASE, bez dijakritika (ista normalizacija kao kaladont)
# ═══════════════════════════════════════════
WORDLE_WORDS = [
    # Ljudi / porodica / profesije
    "MAJKA","TETKA","STRIC","KUHAR","PEKAR","RIBAR","LOVAC","ZUBAR",
    # Hrana / piće
    "LIMUN","DINJA","KUPUS","SECER","BIBER","MLEKO",
    # Životinje
    "KAJAK","JELEN","MACKA","KRAVA","PETAO","PATKA","GUSKA","HRCAK",
    "ZMIJA","PCELA","MRAVI","VRANA","GOLUB",
    # Priroda
    "POTOK","IZVOR","VRELO","POLJE","OKEAN","KAMEN","OBALA","PLAZA",
    "MAGLA","MUNJA","OLUJA","HRAST","BUKVA","JAVOR","BREZA","PALMA",
    "TRAVA","SUNCE","OBLAK","LJETO","JESEN","JUTRO","PODNE","VECER",
    # Tijelo
    "GLAVA","JEZIK","VRATA","PRSTI","NOKAT","LAKAT","GRUDI","TRBUH",
    "KICMA","REBRO","PLUCA","MOZAK","KOSTI","MISIC",
    # Kuća / predmeti / odjeća
    "ORMAR","TEPIH","SLIKA","LAMPA","SOLJA","LONAC","TORBA","RANAC",
    "KOFER","JAKNA","KAPUT","HLACE","CIZME",
    # Tehnika / vozila
    "MODEM","EKRAN","RADIO","ROBOT","KOMBI","JAHTA","CAMAC","SPLAV","BALON",
    # Geografija
    "ULICA","TUNEL","CESTA","STAZA","SPLIT","ZADAR","TUZLA","BIHAC",
    "JAJCE","JAPAN","GRCKA","AZIJA",
    # Pojmovi
    "VJERA",
]

wordle_games: dict = {}  # channel_id -> {word, guesses, uid, max, starter_name, msg}

def _wordle_feedback(secret: str, guess: str) -> str:
    """Vrati niz 🟩/🟨/⬛ za pogodak (ispravno rješava duple slova)."""
    res = ["⬛"] * 5
    rest = list(secret)
    # prvo zelena polja (tačno mjesto)
    for idx in range(5):
        if guess[idx] == rest[idx]:
            res[idx] = "🟩"
            rest[idx] = None
    # zatim žuta polja (slovo u riječi, pogrešno mjesto)
    for idx in range(5):
        if res[idx] == "🟩":
            continue
        ch = guess[idx]
        if ch in rest:
            res[idx] = "🟨"
            rest[rest.index(ch)] = None
    return "".join(res)

def _wordle_embed(game: dict, user, *, finished: bool = False, won: bool = False,
                  reward: int = 0, xp: int = 0):
    used = len(game["guesses"])
    maxg = game["max"]
    rows = []
    for g in game["guesses"]:
        fb = _wordle_feedback(game["word"], g)
        letters = "  ".join(g)
        rows.append(f"{fb}\n`  {letters}  `")
    board = "\n\n".join(rows) if rows else "*Upiši riječ od **5 slova** u chat!*"
    legend = "🟩 tačno mjesto  •  🟨 pogrešno mjesto  •  ⬛ nema slova"
    if finished and won:
        color = GAME_COLORS["wordle"]
        title = f"{E_GAME}  W O R D L E  —  P O B J E D A !  {E_FIRE4}"
        footer = f"🏆 Pogodio/la {user.display_name} • {used}/{maxg} pokušaja"
        extra = (f"\n\n{E_FIRE1}{E_FIRE2}{E_FIRE3} Riječ je bila **{game['word']}**!\n"
                 f"💰 Nagrada: **+{reward:,} 💶**   •   ⭐ XP: **+{xp}**")
    elif finished:
        color = COLORS["error"]
        title = "🟥  W O R D L E  —  K R A J"
        footer = "Pokušaj ponovo sa /wordle"
        extra = (f"\n\n💀 Iskoristio/la si svih **{maxg}** pokušaja!\n"
                 f"🔑 Skrivena riječ je bila **{game['word']}**")
    else:
        color = GAME_COLORS["wordle"]
        title = f"{E_GAME}  W O R D L E"
        footer = f"Pokušaj {used}/{maxg} • upiši riječ od 5 slova"
        extra = ""
    e = discord.Embed(
        title=title,
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{board}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"{legend}{extra}"
        ),
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=footer)
    return e

@bot.tree.command(name="wordle", description="🟩 Pogodi skrivenu riječ od 5 slova u 6 pokušaja!")
async def wordle(i: discord.Interaction):
    cfg = _g_gamble("wordle")
    if not cfg.get("enabled", True):
        return await i.response.send_message(
            embed=em("🚫 Wordle je isključen", "Administrator je privremeno onemogućio ovu igru.", color=COLORS["error"]),
            ephemeral=True
        )
    if i.channel.id in wordle_games:
        return await i.response.send_message(
            embed=em("⚠️ Igra već teče!", "U ovom kanalu je već aktivan Wordle. Završi prvi!", color=COLORS["warning"]),
            ephemeral=True
        )
    secret = random.choice(WORDLE_WORDS)
    game = {
        "word":         secret,
        "guesses":      [],
        "uid":          i.user.id,
        "max":          6,
        "starter_name": i.user.display_name,
        "msg":          None,
    }
    wordle_games[i.channel.id] = game
    await i.response.send_message(embed=_wordle_embed(game, i.user))
    try:
        resp = await i.original_response()
        game["msg"] = resp
    except Exception:
        pass

@bot.tree.command(name="wordle-stop", description="🟩 Zaustavi trenutnu Wordle igru u ovom kanalu")
async def wordle_stop(i: discord.Interaction):
    game = wordle_games.get(i.channel.id)
    if not game:
        return await i.response.send_message(
            embed=em("ℹ️", "Nema aktivne Wordle igre u ovom kanalu.", color=COLORS["info"]),
            ephemeral=True
        )
    is_admin = i.user.guild_permissions.administrator
    if i.user.id != game["uid"] and not is_admin:
        return await i.response.send_message(
            embed=em("🚫", "Samo onaj ko je pokrenuo igru ili admin može zaustaviti!", color=COLORS["error"]),
            ephemeral=True
        )
    secret = game["word"]
    del wordle_games[i.channel.id]
    await i.response.send_message(
        embed=em("🛑 Wordle zaustavljen", f"Igra je prekinuta.\n🔑 Skrivena riječ je bila **{secret}**", color=COLORS["warning"])
    )

# ═══════════════════════════════════════════
#    TOPLO-HLADNO
# ═══════════════════════════════════════════
toplo_games: dict = {}  # channel_id -> {"secret": int, "guesses": int, "starter": int, "min": int, "max": int}

TEMPERATURE = [
    (0,  0,   "🎯 TAČNO!",       COLORS["gold"]),
    (1,  5,   "🔥 VRELO je!",    0xFF4500),
    (6,  15,  "♨️ Jako toplo!",  COLORS["error"]),
    (16, 30,  "🌡️ Toplo...",     COLORS["warning"]),
    (31, 60,  "😐 Mlako...",     COLORS["info"]),
    (61, 120, "❄️ Hladno!",      0x87CEEB),
    (121,999, "🥶 Ledeno!",      0x4169E1),
]

def get_temperature(diff: int):
    for lo, hi, label, color in TEMPERATURE:
        if lo <= diff <= hi:
            return label, color
    return "🥶 Ledeno!", 0x4169E1

class ToploModal(discord.ui.Modal, title="Toplo-Hladno — Pogodi broj!"):
    broj = discord.ui.TextInput(label="Tvoj broj", min_length=1, max_length=5, placeholder="Unesi broj...")

    def __init__(self, view):
        super().__init__(); self.tv = view

    async def on_submit(self, i: discord.Interaction):
        try:
            guess = int(self.broj.value.strip())
        except ValueError:
            return await i.response.send_message(embed=em("❌", "Unesi cijeli broj!", color=COLORS["error"]), ephemeral=True)
        await self.tv.process_guess(i, guess)

class ToploView(discord.ui.View):
    def __init__(self, channel_id: int, starter: discord.Member, secret: int, max_num: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.max_num    = max_num
        toplo_games[channel_id] = {"secret": secret, "guesses": 0, "starter": starter.id, "history": []}

    def make_embed(self, result: str = "", color=None, solved=False):
        game = toplo_games.get(self.channel_id, {})
        guesses = game.get("guesses", 0)
        history = game.get("history", [])[-5:]
        c = color or COLORS["info"]
        e = discord.Embed(title="🌡️ Toplo-Hladno", color=c, timestamp=datetime.now(timezone.utc))
        e.add_field(name="🎯 Raspon", value=f"`1 — {self.max_num}`", inline=True)
        e.add_field(name="🔢 Pokušaji", value=f"`{guesses}`", inline=True)
        if result: e.add_field(name="📡 Signal", value=result, inline=False)
        if history and not solved:
            e.add_field(name="📜 Zadnji pokušaji", value="\n".join(history), inline=False)
        e.set_footer(text=f"{BOT_NAME} {VERSION} • Klikni i pogodi broj!")
        return e

    async def process_guess(self, i: discord.Interaction, guess: int):
        game = toplo_games.get(self.channel_id)
        if not game:
            return await i.response.send_message(embed=em("❌", "Igra nije aktivna!", color=COLORS["error"]), ephemeral=True)
        if not 1 <= guess <= self.max_num:
            return await i.response.send_message(
                embed=em("❌ Van raspona!", f"Unesi broj između `1` i `{self.max_num}`!", color=COLORS["error"]), ephemeral=True)
        game["guesses"] += 1
        secret = game["secret"]
        diff   = abs(guess - secret)
        label, color = get_temperature(diff)
        direction = "⬆️ više" if guess < secret else "⬇️ manje" if guess > secret else ""
        hint = f"`{guess}` → {label}" + (f" ({direction})" if direction else "")
        game["history"].append(hint)
        if diff == 0:
            for c in self.children: c.disabled = True
            del toplo_games[self.channel_id]
            e = discord.Embed(
                title=f"🎯 {i.user.mention} pogodio/la!",
                description=f"Tajna je bila **`{secret}`**!\n🏆 Pogođeno za **{game['guesses']}** pokušaja!",
                color=COLORS["gold"], timestamp=datetime.now(timezone.utc)
            )
            e.set_footer(text=f"{BOT_NAME} {VERSION}")
            await i.response.edit_message(embed=e, view=self)
            self.stop()
        else:
            await i.response.edit_message(embed=self.make_embed(hint, color), view=self)

    @discord.ui.button(label="Pogodi broj", emoji="🌡️", style=discord.ButtonStyle.primary)
    async def guess_btn(self, i: discord.Interaction, b: discord.ui.Button):
        if self.channel_id not in toplo_games:
            return await i.response.send_message(embed=em("❌", "Igra nije aktivna.", color=COLORS["error"]), ephemeral=True)
        await i.response.send_modal(ToploModal(self))

    @discord.ui.button(label="Završi igru", emoji="🏁", style=discord.ButtonStyle.danger)
    async def zavrsi(self, i: discord.Interaction, b: discord.ui.Button):
        game = toplo_games.get(self.channel_id)
        if not game:
            return await i.response.send_message(embed=em("❌", "Nema aktivne igre.", color=COLORS["error"]), ephemeral=True)
        if i.user.id != game["starter"] and not i.user.guild_permissions.manage_messages:
            return await i.response.send_message(embed=em("❌", "Samo pokretač ili mod može završiti igru!", color=COLORS["error"]), ephemeral=True)
        secret = game["secret"]
        del toplo_games[self.channel_id]
        for c in self.children: c.disabled = True
        e = discord.Embed(title="🏁 Igra završena!",
            description=f"Tajna je bila **`{secret}`**!\nNiko nije pogodio ovaj put. 😅",
            color=COLORS["warning"], timestamp=datetime.now(timezone.utc))
        e.set_footer(text=f"{BOT_NAME} {VERSION}")
        await i.response.edit_message(embed=e, view=self)
        self.stop()

@bot.tree.command(name="toplo-hladno", description="🌡️ Pogodi tajni broj — Toplo ili Hladno!")
@app_commands.describe(maksimum="Maksimalni broj (default 100, max 1000)")
async def toplo_hladno(i: discord.Interaction, maksimum: int = 100):
    if i.channel.id in toplo_games:
        return await i.response.send_message(
            embed=em("⚠️ Igra već teče!", "U ovom kanalu je već aktivna igra. Završi prvu!", color=COLORS["warning"]), ephemeral=True)
    maksimum = max(10, min(maksimum, 1000))
    secret = random.randint(1, maksimum)
    v = ToploView(i.channel.id, i.user, secret, maksimum)
    await i.response.send_message(
        embed=v.make_embed(f"🎮 {i.user.mention} pokrenuo igru!\nPogodi broj od `1` do `{maksimum}`!", COLORS["info"]),
        view=v
    )

# ═══════════════════════════════════════════
#    🎮 PER-USER COOLDOWN za GAME komande
#    Regularan član može pokrenuti svaku igru jednom u 30 minuta.
#    Owner i admin (manage_messages) zaobilaze cooldown.
# ═══════════════════════════════════════════
GAME_USER_COOLDOWN_SEC = 30 * 60  # 30 minuta
_game_user_cooldowns: dict = {}   # (gid, uid, cmd) -> last_use_ts

def _is_game_admin(member) -> bool:
    """Owner ili korisnik s manage_messages zaobilazi cooldown."""
    try:
        if int(getattr(member, "id", 0)) in OWNER_IDS:
            return True
    except Exception:
        pass
    try:
        return bool(member.guild_permissions.manage_messages)
    except Exception:
        return False

def _check_game_cooldown(member, gid: int, cmd: str):
    """Vrati (ok: bool, sec_left: int). Owner/admin = uvijek ok."""
    if _is_game_admin(member):
        return True, 0
    key  = (gid or 0, getattr(member, "id", 0), cmd)
    last = _game_user_cooldowns.get(key, 0.0)
    now  = time.time()
    diff = now - last
    if diff < GAME_USER_COOLDOWN_SEC:
        return False, int(GAME_USER_COOLDOWN_SEC - diff)
    return True, 0

def _set_game_cooldown(member, gid: int, cmd: str):
    if _is_game_admin(member):
        return
    _game_user_cooldowns[((gid or 0), getattr(member, "id", 0), cmd)] = time.time()

async def _send_cooldown_msg(i: discord.Interaction, cmd: str, secs_left: int):
    mins, secs = divmod(secs_left, 60)
    e = em(
        "⏳ Cooldown — sačekaj!",
        f"Možeš ponovo pokrenuti **/{cmd}** za **{mins}m {secs}s**.\n"
        f"*(Cooldown za regularne članove: 30 min — admin/owner zaobilazi.)*",
        color=COLORS["warning"]
    )
    return await i.response.send_message(embed=e, ephemeral=True)

# ═══════════════════════════════════════════
#    AMONG US — AMOGUS
# ═══════════════════════════════════════════
PLAYER_COLORS   = ["🔴","🟠","🟡","🟢","🔵","🟣","⚫","⚪","🟤","🩷"]
IMPOSTOR_COUNTS = {4:1, 5:1, 6:1, 7:2, 8:2, 9:2, 10:3}
TASKS_PER_PLAYER = 3
KILL_COOLDOWN_SEC = 30

#  ── DINAMIČKI GENERATOR ZADATAKA (6 kategorija) ──
#  Tipovi: math / typing / logic / memory / speed / repair
#  Svaki zadatak je dict: {q, a, type, fake}
#   - real (crewmate)  → uvećava done_tasks pri tačnom odgovoru
#   - fake (impostor)  → izgleda isto, ali NE broji se u napredak

AMOGUS_TASK_TYPES = ["math", "typing", "logic", "memory", "speed", "repair"]

_AG_LOGIC_TEMPLATES = [
    # (formula, opis za prikaz)
    (lambda x: x*x,         "n²",        "Niz kvadrata: {a}, {b}, {c}, __?"),
    (lambda x: x*2,         "n·2",       "Niz duplih: {a}, {b}, {c}, __?"),
    (lambda x: x*3,         "n·3",       "Niz: {a}, {b}, {c}, __?"),
    (lambda x: x+x*2,       "n + 2n",    "Niz: {a}, {b}, {c}, __?"),
    (lambda x: x*x - 1,     "n²-1",      "Niz: {a}, {b}, {c}, __?"),
]
_AG_TYPE_WORDS  = ["REACTOR","ENGINE","SHIELD","SCAN","UPLOAD","O2","COMMS","ADMIN",
                   "MEDBAY","CAFE","NAV","WEAPONS","STORAGE","ELECTRIC","CAMS"]
_AG_TYPE_SUFFIX = ["ON","OFF","OK","CORE","BAY","ROOM","42","X9","BETA","ZONE"]
_AG_REPAIR_WORDS = ["KABEL","REAKTOR","KAMERE","O2VENT","NAVIGAT","STITOVI"]
_AG_SPEED_WORDS  = ["GO","NOW","FAST","HIT","TAP","RUN","CLICK","ZAP"]

def generate_amogus_task(fake: bool = False) -> dict:
    """Generiše random zadatak iz jedne od 6 kategorija."""
    ttype = random.choice(AMOGUS_TASK_TYPES)

    if ttype == "math":
        op = random.choice(["+","-","×","÷"])
        if op == "+":
            a, b = random.randint(15, 99), random.randint(15, 99)
            q, ans = f"📐 Koliko je {a} + {b}?", str(a+b)
        elif op == "-":
            a = random.randint(50, 199); b = random.randint(10, a-1)
            q, ans = f"📐 Koliko je {a} − {b}?", str(a-b)
        elif op == "×":
            a, b = random.randint(6, 19), random.randint(3, 12)
            q, ans = f"📐 Koliko je {a} × {b}?", str(a*b)
        else:
            b = random.randint(2, 12); ans_v = random.randint(3, 25); a = b * ans_v
            q, ans = f"📐 Koliko je {a} ÷ {b}?", str(ans_v)

    elif ttype == "typing":
        word = f"{random.choice(_AG_TYPE_WORDS)}_{random.choice(_AG_TYPE_SUFFIX)}_{random.randint(10,99)}"
        q, ans = f"⌨️ Upiši TAČNO: `{word}`", word

    elif ttype == "logic":
        fn, label, desc_tpl = random.choice(_AG_LOGIC_TEMPLATES)
        start = random.randint(2, 7)
        seq = [fn(start), fn(start+1), fn(start+2)]
        nxt = fn(start+3)
        q   = f"🧩 {desc_tpl.format(a=seq[0], b=seq[1], c=seq[2])}  *(formula: {label})*"
        ans = str(nxt)

    elif ttype == "memory":
        num = "".join(str(random.randint(0,9)) for _ in range(random.choice([4,5,6])))
        q   = f"🧠 Zapamti i upiši: **{num}**"
        ans = num

    elif ttype == "speed":
        word = random.choice(_AG_SPEED_WORDS)
        q    = f"⚡ BRZINA! Upiši **{word}** što prije!"
        ans  = word

    else:  # repair
        word = random.choice(_AG_REPAIR_WORDS)
        scrambled = list(word); random.shuffle(scrambled)
        q   = f"🔧 POPRAVKA — sastavi riječ iz: `{'-'.join(scrambled)}`"
        ans = word

    return {"q": q, "a": ans, "type": ttype, "fake": bool(fake), "done": False}

# Zadržano za kompatibilnost (nije korišteno aktivno)
AMOGUS_TASKS = [generate_amogus_task() for _ in range(15)]

amogus_games: dict = {}  # channel_id -> state

def _ag(cid):
    return amogus_games.get(cid)

def _task_bar(done, total):
    filled = int((done / total) * 10) if total else 0
    return "🟩"*filled + "⬜"*(10-filled) + f" `{done}/{total}`"

def _ag_player_list(players, show_roles=False):
    lines = []
    for uid, p in players.items():
        dead = "💀 ~~" if not p["alive"] else ""
        end  = "~~" if not p["alive"] else ""
        role = f" — **{'🔴 IMP' if p['role']=='impostor' else '🔵 CREW'}**" if show_roles else ""
        td   = f" [{p['tasks_done']}/{TASKS_PER_PLAYER}]" if p["alive"] and not show_roles else ""
        lines.append(f"{dead}{p['color']} {p['name']}{td}{role}{end}")
    return "\n".join(lines) or "*Nema igrača*"

def _ag_lobby_embed(state):
    players = state["players"]
    e = discord.Embed(title="🚀 Among Us — Lobby", color=0x1B1B2F,
                      description="Pridruži se i čekaj da host pokrene igru!\n**Min 4 • Max 10 igrača**",
                      timestamp=datetime.now(timezone.utc))
    e.add_field(name=f"👥 Igrači ({len(players)}/10)",
                value="\n".join(f"{p['color']} {p['name']}" for p in players.values()) or "*Čekamo...*",
                inline=False)
    e.set_footer(text="Host: klikni ▶️ Pokreni igru kad ste svi tu!")
    return e

def _ag_game_embed(state):
    alive = [p for p in state["players"].values() if p["alive"]]
    ac = sum(1 for p in alive if p["role"]=="crewmate")
    ai = sum(1 for p in alive if p["role"]=="impostor")
    e = discord.Embed(title="🚀 Among Us — U Toku", color=0x1B1B2F, timestamp=datetime.now(timezone.utc))
    e.add_field(name="👥 Igrači", value=_ag_player_list(state["players"]), inline=False)
    e.add_field(name="📋 Zadaci", value=_task_bar(state["done_tasks"], state["total_tasks"]), inline=True)
    e.add_field(name="🎭 Živi", value=f"🔵 {ac} crew | 🔴 {ai} imp", inline=True)
    if state.get("reactor"):
        n_fix = len(state["reactor"]["fixers"])
        e.add_field(name="💥 SABOTAŽA AKTIVNA!", value=f"Reaktor — `{n_fix}/{REACTOR_FIXES_NEEDED}` popravača! ⏱️", inline=False)
    e.set_footer(text="📋 Zadatak • 🚨 Alarm • 🔪 Akcija • 🛑 Sabotiraj • 🎭 Lažni alarm • 🔫 Šerif • 👻 Ghost")
    return e

async def _ag_check_win(state, channel) -> bool:
    alive = [p for p in state["players"].values() if p["alive"]]
    ac = [p for p in alive if p["role"]=="crewmate"]
    ai = [p for p in alive if p["role"]=="impostor"]
    if not ai:
        await _ag_end(state, channel, "🔵 CREWMATI POBIJEDE!", "Svi impostori eliminirani! ✅", COLORS["success"])
        return True
    if len(ai) >= len(ac):
        await _ag_end(state, channel, "🔴 IMPOSTORI POBIJEDE!", "Impostori preuzeli brod! ☠️", COLORS["error"])
        return True
    if state["done_tasks"] >= state["total_tasks"] > 0:
        await _ag_end(state, channel, "🔵 CREWMATI POBIJEDE!", "Svi zadaci završeni! 🎉", COLORS["success"])
        return True
    return False

async def _ag_end(state, channel, title, desc, color):
    state["phase"] = "ended"
    reveal = "\n".join(
        f"{'🔴' if p['role']=='impostor' else '🔵'} {p['color']} **{p['name']}** — {p['role'].upper()}"
        for p in state["players"].values()
    )
    e = discord.Embed(title=f"🏁 {title}", description=desc, color=color, timestamp=datetime.now(timezone.utc))
    e.add_field(name="🎭 Otkrivene uloge", value=reveal, inline=False)
    e.set_footer(text=f"{BOT_NAME} • Among Us")
    await channel.send(embed=e)
    amogus_games.pop(channel.id, None)

async def _ag_tally(channel, state):
    tally = Counter(v for v in state["votes"].values() if v is not None)
    if not tally:
        state["phase"] = "playing"; state["votes"] = {}
        await channel.send(embed=em("⏭️ Niko nije eliminisan", "Svi su preskočili — igra se nastavlja!", color=COLORS["warning"]))
        gv = state.get("game_view")
        if gv: await channel.send(embed=_ag_game_embed(state), view=gv)
        return
    max_v   = max(tally.values())
    winners = [uid for uid, c in tally.items() if c == max_v]
    if len(winners) > 1:
        state["phase"] = "playing"; state["votes"] = {}
        await channel.send(embed=em("⚖️ Izjednačeno!", "Glasanje neodlučeno — niko nije eliminisan!", color=COLORS["warning"]))
        gv = state.get("game_view")
        if gv: await channel.send(embed=_ag_game_embed(state), view=gv)
        return
    ejected_id = winners[0]
    ejected_p  = state["players"][ejected_id]
    ejected_p["alive"] = False
    role_txt = "🔴 **IMPOSTOR**" if ejected_p["role"] == "impostor" else "🔵 **CREWMATE**"
    e = discord.Embed(
        title=f"🚀 {ejected_p['name']} je izbačen/a!",
        description=f"{ejected_p['color']} **{ejected_p['name']}** eliminisan/a sa **{max_v}** glasova.\nBio/la je: {role_txt}",
        color=COLORS["error"] if ejected_p["role"]=="impostor" else COLORS["warning"],
        timestamp=datetime.now(timezone.utc)
    )
    await channel.send(embed=e)
    if not await _ag_check_win(state, channel):
        state["phase"] = "playing"; state["votes"] = {}
        gv = state.get("game_view")
        if gv: await channel.send(embed=_ag_game_embed(state), view=gv)

# ── Views ──────────────────────────────────────────────────

class AmogusLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid

    @discord.ui.button(label="Pridruži se", emoji="🚀", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "lobby":
            return await i.response.send_message(embed=em("❌","Lobby je zatvoren!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        if uid in state["players"]:
            return await i.response.send_message(embed=em("✅","Već si tu!",color=COLORS["warning"]),ephemeral=True)
        if len(state["players"]) >= 10:
            return await i.response.send_message(embed=em("❌","Lobby pun (10/10)!",color=COLORS["error"]),ephemeral=True)
        idx = len(state["players"]) % len(PLAYER_COLORS)
        state["players"][uid] = {"name":i.user.display_name,"alive":True,"role":None,
                                  "color":PLAYER_COLORS[idx],"tasks":[],"tasks_done":0,"kill_cd":0}
        await i.response.edit_message(embed=_ag_lobby_embed(state), view=self)

    @discord.ui.button(label="Napusti", emoji="🚪", style=discord.ButtonStyle.secondary)
    async def leave(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "lobby":
            return await i.response.send_message(embed=em("❌","Lobby zatvoren!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        if uid not in state["players"]:
            return await i.response.send_message(embed=em("❌","Nisi u lobby-u!",color=COLORS["error"]),ephemeral=True)
        del state["players"][uid]
        if not state["players"]:
            amogus_games.pop(self.cid, None)
            return await i.response.edit_message(embed=em("🚪","Lobby zatvoren.",color=COLORS["error"]),view=None)
        if state["host"] == i.user.id:
            state["host"] = int(next(iter(state["players"])))
        await i.response.edit_message(embed=_ag_lobby_embed(state), view=self)

    @discord.ui.button(label="Pokreni igru", emoji="▶️", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state:
            return await i.response.send_message(embed=em("❌","Nema lobby-a!",color=COLORS["error"]),ephemeral=True)
        if i.user.id != state["host"]:
            return await i.response.send_message(embed=em("❌","Samo host može pokrenuti!",color=COLORS["error"]),ephemeral=True)
        if len(state["players"]) < 4:
            return await i.response.send_message(embed=em("❌",f"Treba min **4 igrača**! Sad: `{len(state['players'])}`",color=COLORS["error"]),ephemeral=True)
        await i.response.defer()
        n     = len(state["players"])
        n_imp = IMPOSTOR_COUNTS.get(n, 1)
        ids   = list(state["players"].keys())
        random.shuffle(ids)
        for idx, uid in enumerate(ids):
            role = "impostor" if idx < n_imp else "crewmate"
            state["players"][uid]["role"] = role
            state["players"][uid]["is_sheriff"] = False
            state["players"][uid]["shot_used"]  = False
            # Crewmate dobija prave zadatke; impostor dobija LAŽNE (da glumi rad)
            is_imp = (role == "impostor")
            state["players"][uid]["tasks"] = [generate_amogus_task(fake=is_imp) for _ in range(TASKS_PER_PLAYER)]
        # Jedan random crewmate postaje 👮 ŠERIF
        crew_uids = [uid for uid in ids if state["players"][uid]["role"] == "crewmate"]
        if crew_uids:
            sheriff_uid = random.choice(crew_uids)
            state["players"][sheriff_uid]["is_sheriff"] = True
        state["total_tasks"]         = (n - n_imp) * TASKS_PER_PLAYER
        state["done_tasks"]          = 0
        state["phase"]               = "playing"
        state["sabotage_cd"]         = 0
        state["reactor"]             = None
        state["last_alarm_was_fake"] = False
        # DMs
        bad_dm = []
        for uid, p in state["players"].items():
            member = i.guild.get_member(int(uid))
            if not member: continue
            is_imp = p["role"] == "impostor"
            dm_e = discord.Embed(
                title=f"{'🔴 IMPOSTOR' if is_imp else '🔵 CREWMATE'} — Tvoja uloga!",
                description=("🔴 **Eliminiši crewmate-e, ne budi uhvaćen!**\nKoristi dugme 🔪 **Akcija** za ubijanje."
                             if is_imp else
                             "🔵 **Završi zadatke, pronađi impostora!**\nKoristi dugme 📋 **Zadatak** za rad."),
                color=COLORS["error"] if is_imp else COLORS["info"]
            )
            if is_imp:
                partners = [state["players"][x]["name"] for x in ids[:n_imp] if x != uid]
                if partners: dm_e.add_field(name="🔴 Saimpostori", value="\n".join(partners))
                dm_e.add_field(name="🛑 Sabotaža",  value=f"Klikni **🛑 Sabotiraj** u kanalu — reaktor će eksplodirati za `{REACTOR_TIME_SEC}s` ako ga ne stabilizuju!", inline=False)
                dm_e.add_field(name="🎭 Lažni alarm", value="Klikni **🎭 Lažni alarm** da sazoveš FAKE meeting i zbunjš ekipu.", inline=False)
            if p.get("is_sheriff"):
                dm_e.add_field(name="👮 SPECIJALNA ULOGA: ŠERIF",
                               value="Imaš **1 hitac** za cijelu igru!\n• Pogodi **impostora** → on/ona umire\n• Pogodi **civila** → TI umireš (kazna)\n→ Dugme: **🔫 Šerif Pucaj**",
                               inline=False)
            dm_e.add_field(name="👻 Ghost Chat", value="Kad umreš, klikni **👻 Ghost Chat** u kanalu da pišeš drugim duhovima.", inline=False)
            dm_e.set_footer(text=f"{BOT_NAME} • Samo ti vidiš ovo!")
            try: await member.send(embed=dm_e)
            except: bad_dm.append(p["name"])
        gv = AmogusGameView(self.cid)
        state["game_view"] = gv
        extra = f"\n⚠️ Nije mogao primiti DM: {', '.join(bad_dm)}" if bad_dm else ""
        start_e = discord.Embed(title="🚀 Igra počinje!", description=f"Uloge podijeljene! Provjeri **DM** za svoju ulogu.{extra}",
                                color=0x1B1B2F, timestamp=datetime.now(timezone.utc))
        await i.edit_original_response(embed=start_e, view=None)
        await i.channel.send(embed=_ag_game_embed(state), view=gv)

class AmogusTaskModal(discord.ui.Modal, title="📋 Zadatak"):
    odgovor = discord.ui.TextInput(label="Odgovor:", placeholder="Upiši odgovor...", max_length=60)
    def __init__(self, cid, uid, tidx):
        super().__init__()
        self.cid  = cid
        self.uid  = uid
        self.tidx = tidx
        state = _ag(cid)
        if state and uid in state["players"]:
            q = state["players"][uid]["tasks"][tidx]["q"]
            self.odgovor.label = q[:45]
    async def on_submit(self, i: discord.Interaction):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        p    = state["players"][self.uid]
        task = p["tasks"][self.tidx]
        if self.odgovor.value.strip().lower() == task["a"].strip().lower():
            task["done"] = True
            p["tasks_done"] += 1
            is_fake = task.get("fake", False)
            # Lažni zadaci NE povećavaju globalni napredak
            if not is_fake:
                state["done_tasks"] += 1
            rem = TASKS_PER_PLAYER - p["tasks_done"]
            msg = f"✅ Tačno! Ostalo zadataka: **{rem}**" if rem else "✅ Svi zadaci završeni! 🎉"
            # Igraču NE govorimo da je task fake (zato impostor i može da glumi)
            await i.response.send_message(embed=em("📋 Zadatak završen!", msg, color=COLORS["success"]), ephemeral=True)
            gv = state.get("game_view")
            try: await i.message.edit(embed=_ag_game_embed(state), view=gv)
            except: pass
            if not is_fake:
                await _ag_check_win(state, i.channel)
        else:
            await i.response.send_message(embed=em("❌ Pogrešno!","Pokušaj ponovo!", color=COLORS["error"]), ephemeral=True)

class AmogusKillSelect(discord.ui.View):
    def __init__(self, cid, killer_id):
        super().__init__(timeout=20)
        self.cid       = cid
        self.killer_id = killer_id
        state = _ag(cid)
        if not state: return
        opts = [discord.SelectOption(label=p["name"], value=uid, emoji=p["color"])
                for uid, p in state["players"].items()
                if p["alive"] and uid != str(killer_id) and p["role"] == "crewmate"]
        if opts:
            s = discord.ui.Select(placeholder="Odaberi žrtvu...", options=opts[:25])
            s.callback = self.do_kill
            self.add_item(s)
    async def do_kill(self, i: discord.Interaction):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        ks  = str(self.killer_id)
        kp  = state["players"].get(ks)
        if not kp or not kp["alive"]:
            return await i.response.send_message(embed=em("❌","Ne možeš ubijati!",color=COLORS["error"]),ephemeral=True)
        now = time.time()
        if now - kp.get("kill_cd",0) < KILL_COOLDOWN_SEC:
            left = int(KILL_COOLDOWN_SEC-(now-kp["kill_cd"]))
            return await i.response.send_message(embed=em("⏳",f"Cooldown! Čekaj još `{left}s`",color=COLORS["warning"]),ephemeral=True)
        vid = i.data["values"][0]
        vp  = state["players"].get(vid)
        if not vp or not vp["alive"]:
            return await i.response.send_message(embed=em("❌","Taj igrač nije dostupan!",color=COLORS["error"]),ephemeral=True)
        vp["alive"] = False
        kp["kill_cd"] = now
        # reduce total tasks
        state["total_tasks"] = max(0, state["total_tasks"] - (TASKS_PER_PLAYER - vp["tasks_done"]))
        await i.response.send_message(embed=em("🔪 Eliminirano!",f"**{vp['name']}** je eliminisan/a! Niko ne zna...",color=COLORS["error"]),ephemeral=True)
        vm = i.guild.get_member(int(vid))
        if vm:
            try: await vm.send(embed=em("💀 Eliminisan/a si!",f"**{kp['name']}** te je eliminisao/la. Možeš promatrati igru.",color=COLORS["error"]))
            except: pass
        gv = state.get("game_view")
        try: await i.message.edit(embed=_ag_game_embed(state), view=gv)
        except: pass
        await _ag_check_win(state, i.channel)
        self.stop()

# ── REAKTOR (sabotaža mini-igra) ──
SABOTAGE_COOLDOWN_SEC = 60
REACTOR_TIME_SEC      = 30
REACTOR_FIXES_NEEDED  = 2

class AmogusReactorView(discord.ui.View):
    """Crewmate-i moraju 2x kliknuti '🔧 Stabilizuj' u 30s ili impostori pobjeđuju."""
    def __init__(self, cid):
        super().__init__(timeout=REACTOR_TIME_SEC)
        self.cid = cid

    @discord.ui.button(label="🔧 Stabilizuj reaktor", style=discord.ButtonStyle.success)
    async def fix(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or not state.get("reactor"):
            return await i.response.send_message(embed=em("❌","Nema aktivne sabotaže!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        p   = state["players"].get(uid)
        if not p or not p["alive"]:
            return await i.response.send_message(embed=em("❌","Mrtvi ne mogu popravljati!",color=COLORS["error"]),ephemeral=True)
        if p["role"] == "impostor":
            return await i.response.send_message(embed=em("🚫","Impostori NE mogu popravljati! 😈",color=COLORS["error"]),ephemeral=True)
        state["reactor"]["fixers"].add(uid)
        n = len(state["reactor"]["fixers"])
        await i.response.send_message(embed=em("🔧 Popravljaš!", f"Klik registrovan: **{n}/{REACTOR_FIXES_NEEDED}** popravača.", color=COLORS["success"]), ephemeral=True)
        if n >= REACTOR_FIXES_NEEDED:
            state["reactor"] = None
            self.stop()
            try: await i.message.edit(view=None)
            except: pass
            await i.channel.send(embed=em("✅ REAKTOR STABILIZOVAN!", "Crewmate-i su uspjeli popraviti reaktor na vrijeme! 🛡️", color=COLORS["success"]))

    async def on_timeout(self):
        state = _ag(self.cid)
        if not state or not state.get("reactor"):
            return  # već je popravljen
        state["reactor"] = None
        ch = bot.get_channel(self.cid)
        if ch and state["phase"] == "playing":
            await ch.send(embed=em("💥 REAKTOR EKSPLODIRAO!","Crewmate-i nisu uspjeli popraviti reaktor! 💀", color=COLORS["error"]))
            await _ag_end(state, ch, "🔴 IMPOSTORI POBJEDJUJU!", "Reaktor eksplodirao zbog sabotaže 💥", COLORS["error"])

# ── ŠERIF SELECT (specijalna crewmate uloga, 1 hitac) ──
class AmogusSheriffSelect(discord.ui.View):
    def __init__(self, cid, sheriff_id):
        super().__init__(timeout=20)
        self.cid        = cid
        self.sheriff_id = sheriff_id
        state = _ag(cid)
        if not state: return
        opts = [discord.SelectOption(label=p["name"], value=uid, emoji=p["color"])
                for uid, p in state["players"].items()
                if p["alive"] and uid != str(sheriff_id)]
        if opts:
            s = discord.ui.Select(placeholder="🔫 Pucaj na...", options=opts[:25])
            s.callback = self.do_shot
            self.add_item(s)

    async def do_shot(self, i: discord.Interaction):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        ss = str(self.sheriff_id)
        sp = state["players"].get(ss)
        if not sp or not sp.get("is_sheriff") or sp.get("shot_used") or not sp["alive"]:
            return await i.response.send_message(embed=em("❌","Ne možeš sad pucati!",color=COLORS["error"]),ephemeral=True)
        tid = i.data["values"][0]
        tp  = state["players"].get(tid)
        if not tp or not tp["alive"]:
            return await i.response.send_message(embed=em("❌","Meta nije dostupna!",color=COLORS["error"]),ephemeral=True)
        sp["shot_used"] = True
        if tp["role"] == "impostor":
            tp["alive"] = False
            state["total_tasks"] = max(0, state["total_tasks"])  # impostor nema realne zadatke
            await i.response.send_message(embed=em("🎯 POGODAK!", f"Eliminisao/la si **IMPOSTORA** {tp['name']}!", color=COLORS["success"]), ephemeral=True)
            await i.channel.send(embed=em("👮 ŠERIF DJELUJE!", f"💥 **{tp['name']}** je upucan/a — bio/la je **IMPOSTOR**! 🎉", color=COLORS["success"]))
        else:
            sp["alive"] = False
            state["total_tasks"] = max(0, state["total_tasks"] - (TASKS_PER_PLAYER - sp["tasks_done"]))
            await i.response.send_message(embed=em("💀 Pogriješio si!", f"**{tp['name']}** nije bio impostor — UMIREŠ od kazne!", color=COLORS["error"]), ephemeral=True)
            await i.channel.send(embed=em("👮 ŠERIF PROMAŠIO!", f"⚖️ Šerif **{sp['name']}** pucao u civila — sam je pao! 💀", color=COLORS["error"]))
        gv = state.get("game_view")
        try: await i.message.edit(view=None)
        except: pass
        await _ag_check_win(state, i.channel)
        self.stop()

# ── GHOST CHAT (mrtvi pričaju u DM-u) ──
class AmogusGhostModal(discord.ui.Modal, title="👻 Ghost Chat"):
    poruka = discord.ui.TextInput(label="Poruka ostalim duhovima:", placeholder="Pisi ovde...", max_length=200, style=discord.TextStyle.paragraph)
    def __init__(self, cid, uid):
        super().__init__()
        self.cid = cid
        self.uid = uid

    async def on_submit(self, i: discord.Interaction):
        state = _ag(self.cid)
        if not state:
            return await i.response.send_message(embed=em("❌","Nema igre!",color=COLORS["error"]),ephemeral=True)
        sender = state["players"].get(self.uid)
        if not sender:
            return await i.response.send_message(embed=em("❌","Nisi u igri!",color=COLORS["error"]),ephemeral=True)
        text = self.poruka.value.strip()
        if not text:
            return await i.response.send_message(embed=em("❌","Prazna poruka!",color=COLORS["error"]),ephemeral=True)
        e = em(f"👻 {sender['name']} (DUH)", text, color=COLORS["purple"])
        e.set_footer(text="🤫 Samo mrtvi vide ovo (Ghost Chat)")
        sent = 0
        for puid, p in state["players"].items():
            if not p["alive"]:
                try:
                    m = i.guild.get_member(int(puid))
                    if m:
                        await m.send(embed=e)
                        sent += 1
                except: pass
        await i.response.send_message(embed=em("👻 Poslato!", f"Vidjelo te je **{sent}** duhova.", color=COLORS["success"]), ephemeral=True)

class AmogusGameView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=None)
        self.cid = cid

    @discord.ui.button(label="Zadatak", emoji="📋", style=discord.ButtonStyle.primary)
    async def task_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        if uid not in state["players"]:
            return await i.response.send_message(embed=em("❌","Nisi u igri!",color=COLORS["error"]),ephemeral=True)
        p = state["players"][uid]
        if not p["alive"]:
            return await i.response.send_message(embed=em("💀","Mrtvi ne mogu raditi zadatke!",color=COLORS["error"]),ephemeral=True)
        tidx = next((idx for idx,t in enumerate(p["tasks"]) if not t["done"]), None)
        if tidx is None:
            return await i.response.send_message(embed=em("✅ Sve završeno!","Čekaj ostatak tima! 🎉",color=COLORS["success"]),ephemeral=True)
        await i.response.send_modal(AmogusTaskModal(self.cid, uid, tidx))

    @discord.ui.button(label="Alarm!", emoji="🚨", style=discord.ButtonStyle.danger)
    async def alarm_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        if uid not in state["players"] or not state["players"][uid]["alive"]:
            return await i.response.send_message(embed=em("❌","Ne možeš sazvati meeting!",color=COLORS["error"]),ephemeral=True)
        state["phase"]      = "meeting"
        state["votes"]      = {}
        state["meeting_by"] = i.user.id
        alive_pl = [(k, v["name"]) for k,v in state["players"].items() if v["alive"]]
        mv = AmogusMeetingView(self.cid, alive_pl)
        state["meeting_view"] = mv
        me = _ag_meeting_embed(state, state["players"][uid]["name"], "Emergency Meeting 🚨")
        await i.response.send_message(embed=me, view=mv)

    @discord.ui.button(label="Akcija", emoji="🔪", style=discord.ButtonStyle.secondary)
    async def action_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        if uid not in state["players"]:
            return await i.response.send_message(embed=em("❌","Nisi u igri!",color=COLORS["error"]),ephemeral=True)
        p = state["players"][uid]
        if not p["alive"]:
            return await i.response.send_message(embed=em("💀","Mrtvi ništa ne mogu!",color=COLORS["error"]),ephemeral=True)
        if p["role"] != "impostor":
            return await i.response.send_message(embed=em("🔵 Ti si Crewmate!","Samo impostori mogu koristiti Akciju.",color=COLORS["info"]),ephemeral=True)
        kv = AmogusKillSelect(self.cid, i.user.id)
        if not kv.children:
            return await i.response.send_message(embed=em("❌","Nema živih crewmate-a!",color=COLORS["error"]),ephemeral=True)
        await i.response.send_message(embed=em("🔪 Odaberi žrtvu","Samo ti vidiš ovo!",color=COLORS["error"]),view=kv,ephemeral=True)

    # ── 🛑 SABOTAŽA (samo impostor) ──
    @discord.ui.button(label="Sabotiraj", emoji="🛑", style=discord.ButtonStyle.danger, row=1)
    async def sabotage_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        p   = state["players"].get(uid)
        if not p or not p["alive"] or p["role"] != "impostor":
            return await i.response.send_message(embed=em("🚫","Samo živi impostori sabotiraju!",color=COLORS["error"]),ephemeral=True)
        if state.get("reactor"):
            return await i.response.send_message(embed=em("⚠️","Sabotaža je već aktivna!",color=COLORS["warning"]),ephemeral=True)
        now = time.time()
        last = state.get("sabotage_cd", 0)
        if now - last < SABOTAGE_COOLDOWN_SEC:
            left = int(SABOTAGE_COOLDOWN_SEC - (now - last))
            return await i.response.send_message(embed=em("⏳ Cooldown",f"Sačekaj još `{left}s` da opet sabotiraš.",color=COLORS["warning"]),ephemeral=True)
        state["sabotage_cd"] = now
        state["reactor"]     = {"started": now, "fixers": set()}
        rv = AmogusReactorView(self.cid)
        await i.response.send_message(embed=em("🛑 Sabotaža pokrenuta!","Reaktor će eksplodirati za 30s ako ga ne stabilizuju!",color=COLORS["error"]),ephemeral=True)
        await i.channel.send(embed=em("💥 ALARM — REAKTOR SE TOPI!",
            f"⚠️ Sabotirano!\n**Treba `{REACTOR_FIXES_NEEDED}` različita crewmate-a da kliknu '🔧 Stabilizuj' u **`{REACTOR_TIME_SEC}s`!**",
            color=COLORS["error"]), view=rv)

    # ── 🎭 LAŽNI ALARM (samo impostor) ──
    @discord.ui.button(label="Lažni alarm", emoji="🎭", style=discord.ButtonStyle.secondary, row=1)
    async def fake_alarm_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        p   = state["players"].get(uid)
        if not p or not p["alive"] or p["role"] != "impostor":
            return await i.response.send_message(embed=em("🚫","Samo živi impostori!",color=COLORS["error"]),ephemeral=True)
        state["phase"]              = "meeting"
        state["votes"]              = {}
        state["meeting_by"]         = i.user.id
        state["last_alarm_was_fake"] = True
        alive_pl = [(k, v["name"]) for k,v in state["players"].items() if v["alive"]]
        mv = AmogusMeetingView(self.cid, alive_pl)
        state["meeting_view"] = mv
        me = _ag_meeting_embed(state, p["name"], "🎭 Lažna prijava — neko je 'navodno' vidio tijelo (ali da li je istina?)")
        await i.response.send_message(embed=em("🎭 Lažni alarm postavljen!","Niko ne zna da si TI to lažirao/la! 😈",color=COLORS["error"]),ephemeral=True)
        await i.channel.send(embed=me, view=mv)

    # ── 🔫 ŠERIF (specijalna crewmate uloga, 1 hitac) ──
    @discord.ui.button(label="Šerif Pucaj", emoji="🔫", style=discord.ButtonStyle.danger, row=2)
    async def sheriff_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state or state["phase"] != "playing":
            return await i.response.send_message(embed=em("❌","Igra nije aktivna!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        p   = state["players"].get(uid)
        if not p or not p["alive"]:
            return await i.response.send_message(embed=em("💀","Mrtvi ne pucaju!",color=COLORS["error"]),ephemeral=True)
        if not p.get("is_sheriff"):
            return await i.response.send_message(embed=em("❌","Nisi šerif!","Samo jedan crewmate ima ovu sposobnost.",color=COLORS["error"]),ephemeral=True)
        if p.get("shot_used"):
            return await i.response.send_message(embed=em("❌","Već si potrošio svoj hitac!",color=COLORS["error"]),ephemeral=True)
        sv = AmogusSheriffSelect(self.cid, i.user.id)
        if not sv.children:
            return await i.response.send_message(embed=em("❌","Nema dostupnih meta!",color=COLORS["error"]),ephemeral=True)
        await i.response.send_message(embed=em("🔫 Šerif — biraj metu","⚠️ Pažljivo! Ako pogriješiš — UMIREŠ od kazne!",color=COLORS["gold"]),view=sv,ephemeral=True)

    # ── 👻 GHOST CHAT (samo mrtvi) ──
    @discord.ui.button(label="Ghost Chat", emoji="👻", style=discord.ButtonStyle.secondary, row=2)
    async def ghost_btn(self, i: discord.Interaction, b):
        state = _ag(self.cid)
        if not state:
            return await i.response.send_message(embed=em("❌","Nema aktivne igre!",color=COLORS["error"]),ephemeral=True)
        uid = str(i.user.id)
        p   = state["players"].get(uid)
        if not p:
            return await i.response.send_message(embed=em("❌","Nisi u igri!",color=COLORS["error"]),ephemeral=True)
        if p["alive"]:
            return await i.response.send_message(embed=em("👻","Ghost Chat je SAMO za mrtve!",color=COLORS["error"]),ephemeral=True)
        await i.response.send_modal(AmogusGhostModal(self.cid, uid))

def _ag_meeting_embed(state, caller, reason):
    e = discord.Embed(title="🚨 EMERGENCY MEETING!", color=0xFF0000,
                      description=f"**{caller}** je sazvao/la meeting!\n*{reason}*\n\n**Glasajte koga eliminišete!**",
                      timestamp=datetime.now(timezone.utc))
    alive = {k:v for k,v in state["players"].items() if v["alive"]}
    e.add_field(name="👥 Živi igrači", value=_ag_player_list(alive), inline=False)
    total_alive = len(alive)
    e.add_field(name="🗳️ Glasanje", value=f"`0` od `{total_alive}` glasalo", inline=True)
    e.set_footer(text="Glasajte mudro! Eliminisani igrač otkrije svoju ulogu.")
    return e

class AmogusMeetingView(discord.ui.View):
    def __init__(self, cid, alive_players):
        super().__init__(timeout=90)
        self.cid           = cid
        self.alive_players = alive_players
        for uid, name in alive_players:
            btn = discord.ui.Button(label=name[:20], custom_id=f"agv_{uid}", style=discord.ButtonStyle.secondary)
            btn.callback = self._vote_cb(uid, name)
            self.add_item(btn)
        skip = discord.ui.Button(label="Preskoči", emoji="⏭️", custom_id="agv_skip", style=discord.ButtonStyle.secondary)
        skip.callback = self._vote_cb(None, "Preskoči")
        self.add_item(skip)

    def _vote_cb(self, tid, tname):
        async def cb(i: discord.Interaction):
            state = _ag(self.cid)
            if not state or state["phase"] != "meeting":
                return await i.response.send_message(embed=em("❌","Meeting završen!",color=COLORS["error"]),ephemeral=True)
            uid = str(i.user.id)
            if uid not in state["players"] or not state["players"][uid]["alive"]:
                return await i.response.send_message(embed=em("❌","Ne možeš glasati!",color=COLORS["error"]),ephemeral=True)
            if uid in state["votes"]:
                return await i.response.send_message(embed=em("⚠️","Već si glasao/la!",color=COLORS["warning"]),ephemeral=True)
            state["votes"][uid] = tid
            label = f"**{tname}**" if tid else "Preskoči"
            await i.response.send_message(embed=em("🗳️ Glas zabilježen!",f"Glasao/la si za: {label}",color=COLORS["success"]),ephemeral=True)
            alive_cnt = sum(1 for p in state["players"].values() if p["alive"])
            # Update meeting embed vote count
            try:
                me = i.message.embeds[0]
                me.set_field_at(1, name="🗳️ Glasanje", value=f"`{len(state['votes'])}` od `{alive_cnt}` glasalo", inline=True)
                await i.message.edit(embed=me)
            except: pass
            if len(state["votes"]) >= alive_cnt:
                self.stop()
                await _ag_tally(i.channel, state)
        return cb

    async def on_timeout(self):
        state = _ag(self.cid)
        if not state or state["phase"] != "meeting": return
        for guild in bot.guilds:
            chan = guild.get_channel(self.cid)
            if chan:
                await chan.send(embed=em("⏱️ Glasanje isteklo!","Premalo glasova — niko nije eliminisan.", color=COLORS["warning"]))
                await _ag_tally(chan, state)
                break

@bot.tree.command(name="amogus", description="🚀 Pokreni Among Us igru!")
async def amogus_cmd(i: discord.Interaction):
    ok, left = _check_game_cooldown(i.user, i.guild_id, "amogus")
    if not ok:
        return await _send_cooldown_msg(i, "amogus", left)
    if i.channel.id in amogus_games:
        return await i.response.send_message(embed=em("❌","Igra je već aktivna! Koristi `/amogus-stop` za kraj.",color=COLORS["error"]),ephemeral=True)
    _set_game_cooldown(i.user, i.guild_id, "amogus")
    state = {"phase":"lobby","host":i.user.id,"channel_id":i.channel.id,
             "players":{},"total_tasks":0,"done_tasks":0,"votes":{},"game_view":None,"meeting_view":None}
    state["players"][str(i.user.id)] = {
        "name":i.user.display_name,"alive":True,"role":None,
        "color":PLAYER_COLORS[0],"tasks":[],"tasks_done":0,"kill_cd":0
    }
    amogus_games[i.channel.id] = state
    await i.response.send_message(embed=_ag_lobby_embed(state), view=AmogusLobbyView(i.channel.id))

@bot.tree.command(name="amogus-stop", description="🚀 Zaustavi Among Us igru [HOST/ADMIN]")
async def amogus_stop(i: discord.Interaction):
    state = _ag(i.channel.id)
    if not state:
        return await i.response.send_message(embed=em("❌","Nema aktivne igre!",color=COLORS["error"]),ephemeral=True)
    if i.user.id != state["host"] and not i.user.guild_permissions.manage_messages:
        return await i.response.send_message(embed=em("❌","Samo host ili admin može zaustaviti igru!",color=COLORS["error"]),ephemeral=True)
    amogus_games.pop(i.channel.id, None)
    await i.response.send_message(embed=em("🚀 Igra zaustavljena","Among Us igra je prekinuta.", color=COLORS["warning"]))

# ═══════════════════════════════════════════
#    🃏 POKER — Texas Hold'em za pravi novac
# ═══════════════════════════════════════════

_PK_RANKS  = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]
_PK_SUITS  = ["♠","♥","♦","♣"]
_PK_SE     = {"♠":"♠️","♥":"♥️","♦":"♦️","♣":"♣️"}
_PK_RV     = {r: i+2 for i, r in enumerate(_PK_RANKS)}
_PK_HNAMES = [
    "Visoka karta","Par","Dva para","Tri iste","Strit",
    "Flush","Full house","Četiri iste","Strit flush","Rojal flush"
]

def _pk_deck():
    d = [(r, s) for s in _PK_SUITS for r in _PK_RANKS]
    random.shuffle(d)
    return d

def _pk_card(c):
    return f"`{c[0]}{_PK_SE[c[1]]}`"

def _pk_cards(cards):
    return " ".join(_pk_card(c) for c in cards) if cards else "`?` `?`"

def _pk_hand_rank(five):
    vals  = sorted([_PK_RV[c[0]] for c in five], reverse=True)
    suits = [c[1] for c in five]
    flush = len(set(suits)) == 1
    straight = (vals == list(range(vals[0], vals[0]-5, -1)))
    if not straight and sorted(vals) == [2, 3, 4, 5, 14]:
        straight = True; vals = [5, 4, 3, 2, 1]
    cnt = Counter(vals)
    grp = sorted(cnt.items(), key=lambda x: (x[1], x[0]), reverse=True)
    gc  = [g[1] for g in grp]
    gv  = [g[0] for g in grp]
    if flush and straight:
        return (9 if vals[0] == 14 and vals[1] == 13 else 8, vals)
    if gc[0] == 4:                return (7, gv)
    if gc[:2] == [3, 2]:          return (6, gv)
    if flush:                     return (5, vals)
    if straight:                  return (4, vals)
    if gc[0] == 3:                return (3, gv)
    if gc[:2] == [2, 2]:          return (2, gv)
    if gc[0] == 2:                return (1, gv)
    return (0, vals)

def _pk_best(hole, community):
    all7 = hole + community
    if len(all7) < 5:
        return (_pk_hand_rank(all7), all7)
    return max(((_pk_hand_rank(list(c)), list(c)) for c in _pk_comb(all7, 5)), key=lambda x: x[0])

poker_games: dict = {}  # channel_id -> game dict

def _pk_get_bal(guild_id, user_id):
    mkey = f"{guild_id}:{user_id}"
    return data["money"].get(mkey, data["economy"].get(str(user_id), {}).get("balance", 0))

def _pk_set_bal(guild_id, user_id, amount):
    data["money"][f"{guild_id}:{user_id}"] = max(0, int(amount))

def _pk_lobby_embed(g):
    plist = "\n".join(f"▸ **{p['name']}**" for p in g["players"].values()) or "_Niko još nije ušao_"
    e = discord.Embed(
        title="🃏 POKER — Texas Hold'em",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 **Ulog po igraču:** `{g['ulog']:,} 💶`\n"
            f"🏆 **Trenutni pot:** `{g['pot']:,} 💶`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Igrači ({len(g['players'])}/9):**\n{plist}\n\n"
            f"▸ Klikni **Ulazi u igru** da se pridružiš\n"
            f"▸ Domaćin klika **Počni igru** kad je spreman\n"
            f"▸ Igra automatski kreće za **60 sekundi**"
        ),
        color=0x2ECC71,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f"🃏 {BOT_NAME} • Poker • Min 2, Max 9 igrača")
    return e

def _pk_game_embed(g):
    phase_titles = {
        "preflop": "🃏 Pre-Flop — Kartice podijeljene",
        "flop":    "🌊 Flop — 3 zajedničke kartice",
        "turn":    "🔄 Turn — 4. zajednička kartica",
        "river":   "🌊 River — 5. zajednička kartica",
    }
    community_str = _pk_cards(g["community"]) if g["community"] else "`?` `?` `?` `?` `?`"
    active = [(uid, p) for uid, p in g["players"].items() if not p["folded"]]
    folded = [(uid, p) for uid, p in g["players"].items() if p["folded"]]
    act_str  = "\n".join(f"✅ **{p['name']}**" for _, p in active) or "_nema_"
    fold_str = "\n".join(f"❌ ~~{p['name']}~~" for _, p in folded)
    needs = g.get("needs_action", set())
    wait_str = "\n".join(f"⏳ {g['players'][uid]['name']}" for uid in needs if uid in g["players"]) or "_Svi su djelovali_"
    desc = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🃏 **Zajedničke kartice:**\n{community_str}\n"
        f"💰 **Pot:** `{g['pot']:,} 💶`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Aktivni:**\n{act_str}\n"
    )
    if fold_str:
        desc += f"❌ **Foldali:**\n{fold_str}\n"
    desc += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n⏳ **Čekamo potez:**\n{wait_str}"
    e = discord.Embed(
        title=phase_titles.get(g["phase"], "🃏 POKER"),
        description=desc,
        color=0xE74C3C if g["phase"] == "river" else 0xF39C12,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f"🃏 {BOT_NAME} • Klikni 'Vidi kartice' za svoju ruku • Pot: {g['pot']:,} 💶")
    return e

class PokerLobbyView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=60)
        self.channel_id = channel_id
        self._started   = False

    @discord.ui.button(label="Ulazi u igru 🎴", style=discord.ButtonStyle.success, row=0)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g or g["phase"] != "join":
            return await interaction.response.send_message("❌ Prijava je zatvorena.", ephemeral=True)
        uid = interaction.user.id
        if uid in g["players"]:
            return await interaction.response.send_message("Već si u igri!", ephemeral=True)
        if len(g["players"]) >= 9:
            return await interaction.response.send_message("❌ Igra je puna (max 9)!", ephemeral=True)
        ulog = g["ulog"]
        bal  = _pk_get_bal(g["guild_id"], uid)
        if bal < ulog:
            return await interaction.response.send_message(
                f"❌ Nemaš dovoljno! Trebaš `{ulog:,} 💶`, a imaš `{bal:,} 💶`.", ephemeral=True)
        _pk_set_bal(g["guild_id"], uid, bal - ulog)
        save_data()
        g["players"][uid] = {"name": interaction.user.display_name, "hole": [], "folded": False}
        g["pot"] += ulog
        try:
            await interaction.message.edit(embed=_pk_lobby_embed(g))
        except Exception:
            pass
        await interaction.response.send_message(
            f"✅ Ušao/la si u igru! Skinuto `{ulog:,} 💶`. Pot: `{g['pot']:,} 💶`", ephemeral=True)

    @discord.ui.button(label="Počni igru ▶️", style=discord.ButtonStyle.primary, row=0)
    async def start_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g:
            return await interaction.response.send_message("Nema aktivne igre.", ephemeral=True)
        if interaction.user.id != g["host_id"] and interaction.user.id not in OWNER_IDS:
            return await interaction.response.send_message("❌ Samo domaćin može pokrenuti igru!", ephemeral=True)
        if len(g["players"]) < 2:
            return await interaction.response.send_message("❌ Trebaju minimalno **2 igrača**!", ephemeral=True)
        if self._started:
            return await interaction.response.send_message("Igra već počinje...", ephemeral=True)
        self._started = True
        await interaction.response.defer()
        await _pk_begin(self.channel_id)

    async def on_timeout(self):
        g = poker_games.get(self.channel_id)
        if not g or g["phase"] != "join":
            return
        if len(g["players"]) >= 2:
            await _pk_begin(self.channel_id)
        else:
            for uid in g["players"]:
                _pk_set_bal(g["guild_id"], uid, _pk_get_bal(g["guild_id"], uid) + g["ulog"])
            save_data()
            del poker_games[self.channel_id]
            ch = bot.get_channel(self.channel_id)
            if ch:
                try:
                    msg = g.get("msg")
                    if msg:
                        await msg.edit(embed=discord.Embed(
                            title="❌ Poker otkazan",
                            description="Nema dovoljno igrača (min 2). Ulozi vraćeni.",
                            color=COLORS["error"]
                        ), view=None)
                except Exception:
                    pass

class PokerRaiseModal(discord.ui.Modal, title="💰 Raise / Podigni ulog"):
    iznos = discord.ui.TextInput(label="Koliko podižeš (💶)?", placeholder="npr. 100", max_length=10)

    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        g = poker_games.get(self.channel_id)
        if not g or g["phase"] in ("join", "showdown"):
            return await interaction.response.send_message(
                embed=em("❌","Igra nije aktivna!", color=COLORS["error"]), ephemeral=True)
        uid = interaction.user.id
        if uid not in g["players"] or g["players"][uid]["folded"]:
            return await interaction.response.send_message(
                embed=em("❌","Nisi u igri ili si foldo!", color=COLORS["error"]), ephemeral=True)
        if uid not in g.get("needs_action", set()):
            return await interaction.response.send_message(
                embed=em("⏳","Već si djelovao/la!", color=COLORS["warning"]), ephemeral=True)
        try:
            amt = int(self.iznos.value.strip())
        except Exception:
            return await interaction.response.send_message(
                embed=em("❌","Mora biti broj!", color=COLORS["error"]), ephemeral=True)
        if amt < 10:
            return await interaction.response.send_message(
                embed=em("❌","Min raise je `10 💶`!", color=COLORS["error"]), ephemeral=True)
        bal = _pk_get_bal(g["guild_id"], uid)
        if bal < amt:
            return await interaction.response.send_message(
                embed=em("❌","Nemaš dovoljno!", f"Imaš `{bal:,} 💶`, treba `{amt:,} 💶`.", color=COLORS["error"]),
                ephemeral=True)
        _pk_set_bal(g["guild_id"], uid, bal - amt)
        g["pot"] += amt
        save_data()
        # Resetuj needs_action: svi ostali aktivni MORAJU reagovati
        active = [u for u, p in g["players"].items() if not p["folded"] and u != uid]
        g["needs_action"] = set(active)
        await interaction.response.send_message(
            embed=em("💰 Raise!", f"Podigao/la si **`{amt:,} 💶`**!\n🏆 Novi pot: **`{g['pot']:,} 💶`**\n⏳ Ostali igrači moraju reagovati.",
                     color=COLORS.get("gold", 0xFFD700)),
            ephemeral=False
        )
        # Update embed
        try:
            msg = g.get("msg")
            if msg:
                await msg.edit(embed=_pk_game_embed(g), view=PokerActionView(self.channel_id))
        except Exception:
            pass

class PokerActionView(discord.ui.View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=120)
        self.channel_id = channel_id

    @discord.ui.button(label="🃏 Vidi kartice", style=discord.ButtonStyle.secondary, row=0)
    async def see_cards(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g:
            return await interaction.response.send_message("Nema aktivne igre.", ephemeral=True)
        uid = interaction.user.id
        if uid not in g["players"]:
            return await interaction.response.send_message("Nisi u ovoj igri!", ephemeral=True)
        p      = g["players"][uid]
        hole   = p["hole"]
        status = "❌ **FOLDO si**" if p["folded"] else "✅ **Aktivno igraš**"
        community = g.get("community", [])
        if community and len(hole) == 2:
            rank_t, best5 = _pk_best(hole, community)
            best_str = f"\n🏆 Tvoja trenutna ruka: **{_PK_HNAMES[rank_t[0]]}**\n→ {_pk_cards(best5)}"
        else:
            best_str = ""
        await interaction.response.send_message(
            f"🃏 **Tvoje kartice:** {_pk_cards(hole)}\n{status}{best_str}", ephemeral=True)

    @discord.ui.button(label="✅ Prati", style=discord.ButtonStyle.success, row=1)
    async def check_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g:
            return await interaction.response.send_message("Nema igre.", ephemeral=True)
        uid = interaction.user.id
        if uid not in g["players"]:
            return await interaction.response.send_message("Nisi u igri!", ephemeral=True)
        if g["players"][uid]["folded"]:
            return await interaction.response.send_message("Već si foldo!", ephemeral=True)
        if uid not in g.get("needs_action", set()):
            return await interaction.response.send_message("Već si djelovao/la u ovoj rundi.", ephemeral=True)
        g["needs_action"].discard(uid)
        await interaction.response.send_message(
            embed=em("✅ Pratiš!", "Tvoja akcija je registrovana.", color=COLORS["success"]),
            ephemeral=True
        )
        await _pk_check_advance(self.channel_id)

    @discord.ui.button(label="❌ Fold", style=discord.ButtonStyle.danger, row=1)
    async def fold_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g:
            return await interaction.response.send_message("Nema igre.", ephemeral=True)
        uid = interaction.user.id
        if uid not in g["players"]:
            return await interaction.response.send_message("Nisi u igri!", ephemeral=True)
        if g["players"][uid]["folded"]:
            return await interaction.response.send_message("Već si foldo!", ephemeral=True)
        if uid not in g.get("needs_action", set()):
            return await interaction.response.send_message("Već si djelovao/la u ovoj rundi.", ephemeral=True)
        g["players"][uid]["folded"] = True
        g["needs_action"].discard(uid)
        active_left = [u for u, p in g["players"].items() if not p["folded"]]
        await interaction.response.send_message(
            f"❌ Foldo/la si! Ostalo **{len(active_left)}** aktivnih igrača.", ephemeral=True)
        await _pk_check_advance(self.channel_id)

    @discord.ui.button(label="💰 Raise", style=discord.ButtonStyle.primary, row=1)
    async def raise_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g or g["phase"] in ("join", "showdown"):
            return await interaction.response.send_message(
                embed=em("❌","Igra nije aktivna!", color=COLORS["error"]), ephemeral=True)
        uid = interaction.user.id
        if uid not in g["players"] or g["players"][uid]["folded"]:
            return await interaction.response.send_message(
                embed=em("❌","Nisi u igri ili si foldo!", color=COLORS["error"]), ephemeral=True)
        if uid not in g.get("needs_action", set()):
            return await interaction.response.send_message(
                embed=em("⏳","Već si djelovao/la!", color=COLORS["warning"]), ephemeral=True)
        await interaction.response.send_modal(PokerRaiseModal(self.channel_id))

    @discord.ui.button(label="🔥 ALL-IN", style=discord.ButtonStyle.danger, row=2)
    async def allin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        g = poker_games.get(self.channel_id)
        if not g or g["phase"] in ("join", "showdown"):
            return await interaction.response.send_message(
                embed=em("❌","Igra nije aktivna!", color=COLORS["error"]), ephemeral=True)
        uid = interaction.user.id
        if uid not in g["players"] or g["players"][uid]["folded"]:
            return await interaction.response.send_message(
                embed=em("❌","Nisi u igri ili si foldo!", color=COLORS["error"]), ephemeral=True)
        if uid not in g.get("needs_action", set()):
            return await interaction.response.send_message(
                embed=em("⏳","Već si djelovao/la!", color=COLORS["warning"]), ephemeral=True)
        bal = _pk_get_bal(g["guild_id"], uid)
        if bal <= 0:
            return await interaction.response.send_message(
                embed=em("❌","Nemaš novca za all-in!", color=COLORS["error"]), ephemeral=True)
        _pk_set_bal(g["guild_id"], uid, 0)
        g["pot"] += bal
        save_data()
        active = [u for u, p in g["players"].items() if not p["folded"] and u != uid]
        g["needs_action"] = set(active)
        await interaction.response.send_message(
            embed=em("🔥 ALL-IN!", f"**{interaction.user.display_name}** ide ALL-IN sa **`{bal:,} 💶`**!\n🏆 Pot: **`{g['pot']:,} 💶`**",
                     color=COLORS["error"]),
            ephemeral=False
        )
        try:
            msg = g.get("msg")
            if msg:
                await msg.edit(embed=_pk_game_embed(g), view=PokerActionView(self.channel_id))
        except Exception:
            pass

    async def on_timeout(self):
        g = poker_games.get(self.channel_id)
        if not g or g["phase"] in ("join", "showdown"):
            return
        for uid in list(g.get("needs_action", set())):
            if uid in g["players"] and not g["players"][uid]["folded"]:
                g["players"][uid]["folded"] = True
        g["needs_action"] = set()
        await _pk_check_advance(self.channel_id)

async def _pk_begin(channel_id: int):
    g = poker_games.get(channel_id)
    if not g:
        return
    g["phase"]     = "preflop"
    deck           = _pk_deck()
    g["deck"]      = deck
    g["community"] = []
    for uid in g["players"]:
        g["players"][uid]["hole"]   = [deck.pop(), deck.pop()]
        g["players"][uid]["folded"] = False
    g["needs_action"] = set(g["players"].keys())
    ch = bot.get_channel(channel_id)
    if not ch:
        return
    e    = _pk_game_embed(g)
    view = PokerActionView(channel_id)
    try:
        msg = g.get("msg")
        if msg:
            await msg.edit(embed=e, view=view)
        else:
            msg = await ch.send(embed=e, view=view)
            g["msg"] = msg
    except Exception:
        msg = await ch.send(embed=e, view=view)
        g["msg"] = msg
    await ch.send(
        "🃏 **Kartice su podijeljene!**\n"
        "▸ Klikni **Vidi kartice** da vidiš svoju ruku (samo ti vidiš)\n"
        "▸ Klikni **Prati** da ostaneš u igri ili **Fold** da odustaneš."
    )

async def _pk_check_advance(channel_id: int):
    g = poker_games.get(channel_id)
    if not g:
        return
    active = [uid for uid, p in g["players"].items() if not p["folded"]]
    if len(active) <= 1:
        await _pk_end_game(channel_id, active)
        return
    if not g.get("needs_action"):
        await _pk_next_phase(channel_id)

async def _pk_next_phase(channel_id: int):
    g = poker_games.get(channel_id)
    if not g:
        return
    ch = bot.get_channel(channel_id)
    if not ch:
        return
    active = [uid for uid, p in g["players"].items() if not p["folded"]]
    phase  = g["phase"]
    if phase == "preflop":
        g["community"] = [g["deck"].pop(), g["deck"].pop(), g["deck"].pop()]
        g["phase"]     = "flop"
        ann_title = "🌊 FLOP"
        ann_desc  = f"Zajedničke kartice:\n{_pk_cards(g['community'])}"
        ann_color = COLORS["info"]
    elif phase == "flop":
        g["community"].append(g["deck"].pop())
        g["phase"] = "turn"
        ann_title = "🔄 TURN"
        ann_desc  = f"Kartice:\n{_pk_cards(g['community'])}"
        ann_color = COLORS["purple"]
    elif phase == "turn":
        g["community"].append(g["deck"].pop())
        g["phase"] = "river"
        ann_title = "🌊 RIVER"
        ann_desc  = f"Kartice:\n{_pk_cards(g['community'])}"
        ann_color = COLORS["gold"]
    elif phase == "river":
        await _pk_showdown(channel_id)
        return
    else:
        return
    g["needs_action"] = set(active)
    e    = _pk_game_embed(g)
    view = PokerActionView(channel_id)
    try:
        msg = g.get("msg")
        if msg:
            await msg.edit(embed=e, view=view)
    except Exception:
        pass
    await ch.send(embed=em(ann_title, ann_desc, color=ann_color))

async def _pk_showdown(channel_id: int):
    g = poker_games.get(channel_id)
    if not g:
        return
    g["phase"] = "showdown"
    ch = bot.get_channel(channel_id)
    if not ch:
        return
    active = [(uid, p) for uid, p in g["players"].items() if not p["folded"]]
    if not active:
        del poker_games[channel_id]
        return
    if len(active) == 1:
        await _pk_end_game(channel_id, [active[0][0]])
        return
    community = g["community"]
    results   = []
    for uid, p in active:
        rank_t, best5 = _pk_best(p["hole"], community)
        results.append((uid, p["name"], rank_t, best5, p["hole"]))
    results.sort(key=lambda x: x[2], reverse=True)
    best_rank  = results[0][2]
    winners    = [r for r in results if r[2] == best_rank]
    winner_ids = [r[0] for r in winners]
    pot        = g["pot"]
    split      = pot // len(winners)
    lines = []
    for uid, name, rank_t, best5, hole in results:
        crown = "🏆" if uid in winner_ids else "  "
        lines.append(
            f"{crown} **{name}**\n"
            f"   Ruka: {_pk_cards(hole)}\n"
            f"   → **{_PK_HNAMES[rank_t[0]]}** | {_pk_cards(best5)}"
        )
    winner_str = " & ".join(r[1] for r in winners)
    tie_note   = " *(Split pot)*" if len(winners) > 1 else ""
    e = discord.Embed(
        title="🏆 SHOWDOWN — Poker",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🃏 **Zajedničke kartice:**\n{_pk_cards(community)}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            + "\n\n".join(lines) +
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 **Pobjednik:** {winner_str}{tie_note}\n"
            f"💰 **Dobitak:** `{split:,} 💶` po pobjedniku"
        ),
        color=COLORS.get("gold", 0xFFD700),
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f"🃏 {BOT_NAME} • Poker završen • Ukupni pot: {pot:,} 💶")
    try:
        msg = g.get("msg")
        if msg:
            await msg.edit(embed=e, view=None)
        else:
            await ch.send(embed=e)
    except Exception:
        await ch.send(embed=e)
    await _pk_end_game(channel_id, winner_ids, skip_embed=True)

async def _pk_end_game(channel_id: int, winner_ids: list, skip_embed: bool = False):
    g = poker_games.get(channel_id)
    if not g:
        return
    pot      = g["pot"]
    guild_id = g["guild_id"]
    ch       = bot.get_channel(channel_id)
    if winner_ids:
        split     = pot // len(winner_ids)
        remainder = pot % len(winner_ids)
        for idx, uid in enumerate(winner_ids):
            amt = split + (remainder if idx == 0 else 0)
            _pk_set_bal(guild_id, uid, _pk_get_bal(guild_id, uid) + amt)
        save_data()
        if not skip_embed and ch:
            name = g["players"].get(winner_ids[0], {}).get("name", "Pobjednik")
            e = discord.Embed(
                title="🏆 Poker — Pobjednik!",
                description=(
                    f"🏆 **{name}** pobijedio/la jer su svi ostali foldali!\n"
                    f"💰 **Dobitak:** `{pot:,} 💶`"
                ),
                color=COLORS.get("gold", 0xFFD700),
                timestamp=datetime.now(timezone.utc)
            )
            try:
                msg = g.get("msg")
                if msg:
                    await msg.edit(embed=e, view=None)
                else:
                    await ch.send(embed=e)
            except Exception:
                await ch.send(embed=e)
    poker_games.pop(channel_id, None)

@bot.tree.command(name="poker", description="🃏 Pokreni Texas Hold'em Poker za pravi novac (2–9 igrača)")
@app_commands.describe(ulog="Iznos uloga po igraču u 💶 (default: 200, min: 50, max: 50000)")
async def poker_cmd(i: discord.Interaction, ulog: int = 200):
    ok, left = _check_game_cooldown(i.user, i.guild_id, "poker")
    if not ok:
        return await _send_cooldown_msg(i, "poker", left)
    if poker_games.get(i.channel_id):
        return await i.response.send_message(
            embed=em("❌", "Poker igra je već aktivna u ovom kanalu!", color=COLORS["error"]), ephemeral=True)
    if ulog < 50:
        return await i.response.send_message(
            embed=em("❌", "Minimalni ulog je `50 💶`.", color=COLORS["error"]), ephemeral=True)
    if ulog > 50000:
        return await i.response.send_message(
            embed=em("❌", "Maksimalni ulog je `50,000 💶`.", color=COLORS["error"]), ephemeral=True)
    uid = i.user.id
    bal = _pk_get_bal(i.guild.id, uid)
    if bal < ulog:
        return await i.response.send_message(
            embed=em("❌", f"Nemaš dovoljno! Trebaš `{ulog:,} 💶`, a imaš `{bal:,} 💶`.", color=COLORS["error"]),
            ephemeral=True)
    _pk_set_bal(i.guild.id, uid, bal - ulog)
    save_data()
    _set_game_cooldown(i.user, i.guild_id, "poker")
    g = {
        "guild_id":    i.guild.id,
        "channel_id":  i.channel_id,
        "host_id":     uid,
        "ulog":        ulog,
        "pot":         ulog,
        "phase":       "join",
        "players":     {uid: {"name": i.user.display_name, "hole": [], "folded": False}},
        "deck":        [],
        "community":   [],
        "needs_action": set(),
        "msg":         None,
    }
    poker_games[i.channel_id] = g
    view = PokerLobbyView(i.channel_id)
    e    = _pk_lobby_embed(g)
    await i.response.send_message(embed=e, view=view)
    msg  = await i.original_response()
    g["msg"] = msg

# ═══════════════════════════════════════════
#    LJUBAVNE / SOCIJALNE KOMANDE
# ═══════════════════════════════════════════
async def social_cmd(i: discord.Interaction, target: discord.Member, action: str, txt: str, color_key: str = "love"):
    await i.response.defer()
    gif = await get_gif(action)
    opis = txt.replace("{from}", i.user.mention).replace("{to}", target.mention)
    e = discord.Embed(description=opis, color=COLORS[color_key], timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    if gif: e.set_image(url=gif)
    await i.followup.send(embed=e)

@bot.tree.command(name="zagrljaj", description="🤗 Zagrli nekog na serveru")
async def zagrljaj(i: discord.Interaction, korisnik: discord.Member):
    await social_cmd(i, korisnik, "hug", "🤗 {from} grli {to}! Aww, tako slatko! 💕", "love")

@bot.tree.command(name="poljubac", description="💋 Pošalji poljubac nekome")
async def poljubac(i: discord.Interaction, korisnik: discord.Member):
    await social_cmd(i, korisnik, "kiss", "💋 {from} šalje poljubac {to}! 😘", "pink")

@bot.tree.command(name="mazi", description="🥰 Pomazi nekoga nježno")
async def mazi(i: discord.Interaction, korisnik: discord.Member):
    await social_cmd(i, korisnik, "pat", "🥰 {from} mazi {to} po glavi! Predobro! ✨", "love")

@bot.tree.command(name="tapsi", description="👋 Tapši nekoga prijateljski")
async def tapsi(i: discord.Interaction, korisnik: discord.Member):
    await social_cmd(i, korisnik, "handshake", "👋 {from} tapše {to}! Aj, brate! 🤝", "teal")

@bot.tree.command(name="high5", description="🙌 Daj peticu nekome")
async def high5(i: discord.Interaction, korisnik: discord.Member):
    await social_cmd(i, korisnik, "highfive", "🙌 {from} daje peticu {to}! Dobra ekipa! ⚡", "success")

@bot.tree.command(name="cudan", description="😠 Budi ćudan prema nekome")
async def cudan(i: discord.Interaction, korisnik: discord.Member):
    await social_cmd(i, korisnik, "poke", "😠 {from} je ćudan prema {to}! Ajde, brate... 😤", "warning")

@bot.tree.command(name="srce", description="❤️ Pošalji srce nekome")
async def srce(i: discord.Interaction, korisnik: discord.Member):
    poruke = [
        "❤️ {from} šalje srce {to}! Aww! 🥺",
        "💖 {from} voli {to}! Toliko slatko! 💕",
        "🌹 {from} poklanja ruže {to}! Romantično! 🌹",
        "💝 {from} šalje ljubav {to}! Neka traje! 💝",
    ]
    e = discord.Embed(description=random.choice(poruke).replace("{from}", i.user.mention).replace("{to}", korisnik.mention), color=COLORS["love"], timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.response.send_message(embed=e)

@bot.tree.command(name="brak", description="💍 Zaprosio nekoga (za fun)")
async def brak(i: discord.Interaction, korisnik: discord.Member):
    if korisnik.id == i.user.id:
        return await i.response.send_message(embed=em("❌", "Ne možeš se zarositi sam sebi!", color=COLORS["error"]), ephemeral=True)
    odgovori = [
        f"💍 {i.user.mention} zaprosio {korisnik.mention}! 😍 Hoćeš li? 🥂",
        f"💒 {i.user.mention} klekne pred {korisnik.mention} i kaže: 'Hoćeš li biti moj/moja?' 💍",
        f"🌹 {i.user.mention} donosi ruže i prsten {korisnik.mention}! Romantika! 😘",
    ]
    e = discord.Embed(description=random.choice(odgovori), color=COLORS["love"], timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.response.send_message(embed=e)

# ═══════════════════════════════════════════
#    POZDRAVI & MUVANJE
# ═══════════════════════════════════════════
_fun_cd: dict = {}  # (user_id, cmd) -> expires_at

async def fun_cooldown(i: discord.Interaction, cmd: str) -> bool:
    """Vrati True (i pošalji grešku) ako je korisnik na cooldownu."""
    key = (i.user.id, cmd)
    now = time.time()
    if key in _fun_cd and now < _fun_cd[key]:
        left = round(_fun_cd[key] - now, 1)
        await i.response.send_message(
            embed=em("⏳ Polako!", f"Čekaj još `{left}s` pa pošalji ponovo! 😅", color=COLORS["warning"]),
            ephemeral=True
        )
        return True
    _fun_cd[key] = now + random.randint(5, 7)
    return False

POZZ_PORUKE = [
    "{user} je toliko nesretan/nesretna da bi kiša padala samo na njega/nju! ☔😂",
    "{user} se pojavio/la! Svima odmah postalo malo bolje. Ili gore. Još ne znamo. 🤔",
    "{user} je stigao/la! Server je upravo dobio +1 na kaos. 🎲",
    "Oh, {user} je tu! Čak i WiFi malo usporio od uzbuđenja. 📶😂",
    "{user} je ušao/la kao da nosi sav teret Balkana na leđima. Budi jači/a, brate/sestro! 💪",
    "{user} se pojavio/la, oblaci su se razišli... al samo da ga/je bolje vide. ☁️👀",
    "{user} je stigao/la! Temperatura u sobi pala za 2 stepena. Brrr. 🥶",
    "{user} je tu! Neko je trebao doći kasno, i evo ga/je. ⏰😂",
    "{user} je ušao/la onako kako ulaze heroji — tiho, neopaženo, i malo zbunjeno. 🦸",
    "{user} se pojavio/la! Baba bi rekla: 'Ajde sine/ćeri, jesil jeo/jela?' 👵🍽️",
    "{user} je stigao/la! Google Maps kaže da si trebao/la biti tu prije 45 minuta. 🗺️😅",
    "{user} se prijavio/la na server! Anđeli plaču, a đavoli aplaudiraju. 😈😇",
    "{user} je tu! Čak i mačke na ulici znale da nešto nije u redu. 🐱",
    "Alarm! {user} je online! Sklanjajte sve vrijedno! 🚨😂",
    "{user} je ušao/la onako tiho kao slon u prodavnici porculana. 🐘",
]

KOMPLI_PORUKE = [
    "🌹 {from} kaže {to}: 'Ti si razlog zašto dan počinje sa osmijehom. 😍'",
    "💫 {from} za {to}: 'Tvoje oči sjaje više nego moj monitor u 3 ujutru. 😘'",
    "🌸 {from} {to}: 'Kad se smiješiš, čak i bots-ovi izgube koncentraciju. 💕'",
    "🎇 {from} kaže {to}: 'Ti si jedina osoba zbog koje bih zatvorio YouTube. I to je PUNO. 😅💖'",
    "🦋 {from} za {to}: 'Pored tebe, sve ostale zvezde izgledaju kao noćne lampice. ✨'",
    "🍀 {from} {to}: 'Ako si ti greška, onda je svemir trebao praviti više grešaka. 💝'",
    "🌙 {from} kaže {to}: 'Ti si razlog zašto pjesnici još uvijek pišu stihove. 📜💕'",
    "🔥 {from} za {to}: 'Toliko si cool da ni klima u mom sobi ne može da te dostigne. ❄️😍'",
    "🎀 {from} {to}: 'Kad si ti tu, cio server osjeti razliku. Kao sunce posle kiše. 🌈'",
    "💌 {from} kaže {to}: 'Nisi savršen/na, ali si savršen/na za mene. I to je sve što treba. 😘'",
    "🌺 {from} za {to}: 'Tvoj smijeh zvuči kao melodija koje bi slušao/la cio dan. 🎵💕'",
    "⭐ {from} {to}: 'Ti si dokaz da Bog ponekad ima dobrog dana. 😇✨'",
]

FORA_PORUKE = [
    "😂 {from} je pogledao/la {to} i shvatio/la: 'Brate/sestro, ti si dokaz da evolucija nije uvijek napredak.' 🐒",
    "🎭 {from} za {to}: 'Tražiš razlog da se smiješ? Pogledaj se u ogledalo!' 😭😂",
    "💀 {from} {to}: 'Toliko si prosječan/na da Google ne zna ni da te indexuje.' 🔍",
    "😤 {from} za {to}: 'Tvoja ex je bila u pravu za jedno — čekanje nije uvijek vrijedno.' 💔😂",
    "🧠 {from} {to}: 'Mislio/la sam da si pametan/na... al to bi mi bila prva greška.' 🤓",
    "🎪 {from} za {to}: 'Jedina stvar koja radi brže od tebe je moj internet kad ga fakturiram.' 📡😂",
    "😅 {from} {to}: 'Rekli su mi da budem ljubazan/na... al ni ja ne znam kako.' 💀",
    "👀 {from} za {to}: 'Svaki put kad pišeš, autocorrect se zapita je li vredno popraviti.' 📱😂",
    "🤦 {from} {to}: 'IQ ti je manji od temp u frižideru. I to zimski frižider.' ❄️",
    "🏆 {from} za {to}: 'Nagradu za originalnost si propustio/la zajedno sa svakom drugom nagradom.' 😂",
]

# /pozz uklonjeno (v2.2) — pravimo mjesto za /mafia igru.

@bot.tree.command(name="kompli", description="🌹 Pošalji slatki kompliment nekome")
@discord.app_commands.describe(korisnik="Kome šalješ kompliment")
async def kompli(i: discord.Interaction, korisnik: discord.Member):
    if await fun_cooldown(i, "kompli"): return
    if korisnik.id == i.user.id:
        poruka = "🤡 Hm, komplimentiraš samog/samu sebe? Ajde, prihvatamo to!"
    else:
        poruka = random.choice(KOMPLI_PORUKE).replace("{from}", i.user.mention).replace("{to}", korisnik.mention)
    e = discord.Embed(description=poruka, color=COLORS["pink"], timestamp=datetime.now(timezone.utc))
    e.set_thumbnail(url=korisnik.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} • Muvanje 101 💕")
    await i.response.send_message(embed=e)

@bot.tree.command(name="fora", description="😂 Ubaci foru na račun nekoga (sve u šali!)")
@discord.app_commands.describe(korisnik="Ko prima foru")
async def fora(i: discord.Interaction, korisnik: discord.Member):
    if await fun_cooldown(i, "fora"): return
    if korisnik.id == i.user.id:
        poruka = "😂 Fora na vlastiti račun? Poštujemo samokritiku!"
    else:
        poruka = random.choice(FORA_PORUKE).replace("{from}", i.user.mention).replace("{to}", korisnik.mention)
    e = discord.Embed(description=poruka, color=COLORS["fun"], timestamp=datetime.now(timezone.utc))
    e.set_thumbnail(url=korisnik.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} • Sve u šali! 😂")
    await i.response.send_message(embed=e)

@bot.tree.command(name="muv", description="😏 Muvaj nekoga Balkan stilom")
@discord.app_commands.describe(korisnik="Ko je sretan/na da ga/ju muvaš")
async def muv(i: discord.Interaction, korisnik: discord.Member):
    if await fun_cooldown(i, "muv"): return
    if korisnik.id == i.user.id:
        return await i.response.send_message(embed=em("😅", "Ne možeš muvati samog/samu sebe, brate/sestro!", color=COLORS["error"]), ephemeral=True)
    muv_poruke = [
        f"😏 {i.user.mention} {korisnik.mention}: 'Jesi li ti WiFi? Jer osjećam konekciju između nas.' 📶💕",
        f"🌹 {i.user.mention} {korisnik.mention}: 'Daj mi broj, hoću te zvati svaki dan... osim kad nemam kredit.' 😂💖",
        f"🔥 {i.user.mention} {korisnik.mention}: 'Ti si kao kebab u 3 ujutru — ne znam zašto, ali baš te trebam.' 🌯😍",
        f"💫 {i.user.mention} kaže {korisnik.mention}: 'Slika ti se hvata svuda — čak i u mojim snovima. 📸💕'",
        f"😘 {i.user.mention} {korisnik.mention}: 'Da sam Google, stavil/la bih te na prvu stranicu. 🔍💝'",
        f"🎯 {i.user.mention} {korisnik.mention}: 'Znaš šta te razlikuje od ostalih? Sve. 😍✨'",
        f"🏹 {i.user.mention} {korisnik.mention}: 'Cupid me pogodio strelicom, ali mislim da si ti sljedeća meta. 😳💘'",
        f"🌙 {i.user.mention} {korisnik.mention}: 'Astronomija je dokazala da zvijezde padaju. Ali ti... ti nikad ne padaš s mog uma. 🌟'",
        f"☕ {i.user.mention} {korisnik.mention}: 'Ti si mi kao kafa ujutru — ne mogu bez tebe ni dan. 😏☕'",
        f"🎵 {i.user.mention} {korisnik.mention}: 'Svaka pjesma koju čujem podsjeti me na tebe. Čak i folk. 🎶💕'",
    ]
    e = discord.Embed(description=random.choice(muv_poruke), color=COLORS["love"], timestamp=datetime.now(timezone.utc))
    e.set_thumbnail(url=korisnik.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} • Balkan Muvanje™ 😏")
    await i.response.send_message(embed=e)

@bot.tree.command(name="crush", description="💘 Otkrij ko je tvoj tajni crush na serveru!")
async def crush(i: discord.Interaction):
    if await fun_cooldown(i, "crush"): return
    members = [m for m in i.guild.members if not m.bot and m.id != i.user.id]
    if not members:
        return await i.response.send_message(embed=em("❌", "Nema dovoljno članova!", color=COLORS["error"]), ephemeral=True)
    random.seed(i.user.id + i.guild.id)
    picked = random.choice(members)
    random.seed()
    poruke = [
        f"💘 Po zvijezdama i kafanskim računima, tvoj tajni crush je... **{picked.display_name}**! 😳",
        f"🔮 Kristalna kugla kaže: **{picked.display_name}** ti se sviđa više nego što priznaješ! 💕",
        f"💌 Baka bi rekla: 'Idi, pitaj ga/je na kafu!' — tvoj crush: **{picked.display_name}** ☕😍",
    ]
    e = discord.Embed(description=random.choice(poruke), color=COLORS["love"], timestamp=datetime.now(timezone.utc))
    e.set_thumbnail(url=picked.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} • Crush Otkrivač™ | Samo za zabavu!")
    await i.response.send_message(embed=e)

# ═══════════════════════════════════════════
#    OWO — ŽIVOTINJE SISTEM
# ═══════════════════════════════════════════
ANIMALS = {
    # ime: (emoji, rarity, power, value)
    "Riba":            ("🐟", "common",    1,   5),
    "Ptica":           ("🐦", "common",    1,   5),
    "Patka":           ("🦆", "common",    1,   6),
    "Kokoška":         ("🐔", "common",    1,   6),
    "Zec":             ("🐇", "common",    2,   8),
    "Vjeverica":       ("🐿️","common",    2,   8),
    "Gušter":          ("🦎", "common",    2,   8),
    "Puž":             ("🐌", "common",    1,   5),
    "Miš":             ("🐭", "common",    2,   7),
    "Lisica":          ("🦊", "uncommon",  5,  25),
    "Jazavac":         ("🦡", "uncommon",  4,  22),
    "Vuk":             ("🐺", "uncommon",  7,  40),
    "Rakun":           ("🦝", "uncommon",  5,  30),
    "Kornjača":        ("🐢", "uncommon",  3,  28),
    "Majmun":          ("🐒", "uncommon",  5,  32),
    "Medvjed":         ("🐻", "rare",     12,  90),
    "Lav":             ("🦁", "rare",     14, 110),
    "Tigar":           ("🐯", "rare",     13, 105),
    "Orao":            ("🦅", "rare",     10, 100),
    "Ajkula":          ("🦈", "rare",     13, 115),
    "Nilski konj":     ("🦛", "rare",     11,  95),
    "Zmaj":            ("🐉", "epic",     28, 320),
    "Jednorog":        ("🦄", "epic",     22, 270),
    "Krokodil":        ("🐊", "epic",     25, 290),
    "Gorila":          ("🦍", "epic",     20, 260),
    "Feniks":          ("🔥", "legendary",55, 900),
    "Morski Lav":      ("🌊", "legendary",50, 820),
    "Noćni Zmaj":      ("🐲", "legendary",60, 980),
    "Kristalni Jednorog":("💎","mythical",110,5000),
    "Dugin Feniks":    ("🌈", "mythical", 130,7000),
    "Nebeski Zmaj":    ("✨", "mythical", 150,9999),
}

RARITY_ORDER  = ["common","uncommon","rare","epic","legendary","mythical"]
RARITY_EMOJI  = {"common":"⚪","uncommon":"🟢","rare":"🔵","epic":"🟣","legendary":"🟡","mythical":"🌸"}
RARITY_COLORS = {"common":0x9B9B9B,"uncommon":0x2ECC71,"rare":0x3498DB,"epic":0x9B59B6,"legendary":0xF1C40F,"mythical":0xFF69B4}
RARITY_WEIGHTS= {"common":50,"uncommon":26,"rare":15,"epic":7,"legendary":2,"mythical":0.3}

HUNT_MISS = [
    "Ništa nisi uhvatio... životinja je pobjegla! 💨",
    "Prazne ruke! Vrati se kad si odmorniji. 😴",
    "Tišina u šumi... nema ničega danas. 🌲",
    "Promašio si! Trebao si ići lijevo. ⬅️",
    "Životinja te vidjela prije nego ti nju. 👀",
]

def pick_animal() -> str | None:
    if random.random() < 0.12:
        return None  # miss
    rarities = list(RARITY_WEIGHTS.keys())
    weights  = [RARITY_WEIGHTS[r] for r in rarities]
    chosen   = random.choices(rarities, weights=weights, k=1)[0]
    pool     = [n for n, (_, r, _, _) in ANIMALS.items() if r == chosen]
    return random.choice(pool) if pool else None

def zoo_power(uid) -> int:
    zoo  = get_zoo(uid)
    total = 0
    for name, cnt in zoo.items():
        if name in ANIMALS and cnt > 0:
            total += ANIMALS[name][2] * cnt
    return total

HUNT_COOLDOWNS: dict = {}

@bot.tree.command(name="hunt", description="🏹 Idi u lov na životinje! (kao owo hunt)")
async def hunt(i: discord.Interaction):
    now = time.time()
    last = HUNT_COOLDOWNS.get(i.user.id, 0)
    remaining = 7 - (now - last)
    if remaining > 0:
        return await i.response.send_message(
            embed=em("⏳ Previše si lovio!", f"Čekaj još `{remaining:.1f}s`", color=COLORS["warning"]),
            ephemeral=True
        )
    HUNT_COOLDOWNS[i.user.id] = now
    await i.response.defer()
    await asyncio.sleep(1.2)

    animal = pick_animal()
    if not animal:
        e = discord.Embed(description=f"🏹  {random.choice(HUNT_MISS)}", color=0x555555, timestamp=datetime.now(timezone.utc))
        e.set_footer(text=f"{BOT_NAME} {VERSION} • Pokušaj ponovo za 7s")
        return await i.followup.send(embed=e)

    emoji, rarity, power, value = ANIMALS[animal]
    zoo = get_zoo(i.user.id)
    zoo[animal] = zoo.get(animal, 0) + 1
    save_data()
    quest_progress(i.user.id, "hunt5")
    quest_progress(i.user.id, "hunt10")

    color = RARITY_COLORS[rarity]
    ri    = RARITY_EMOJI[rarity]
    e = discord.Embed(
        title=f"🏹  Uhvatio si životinje!",
        description=f"## {emoji}  {animal}\n{ri} **{rarity.capitalize()}**  ·  ⚔️ Snaga `{power}`",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="🔢 Imaš ukupno", value=f"`{zoo[animal]}x {emoji} {animal}`", inline=True)
    e.add_field(name="💶 Vrijednost",   value=f"`{value} 💶`",                       inline=True)
    e.set_footer(text=f"{i.user.display_name} • {BOT_NAME} {VERSION}")
    await i.followup.send(embed=e)

@bot.tree.command(name="zoo", description="🦁 Pogledaj svoju zbirku životinja (kao owo zoo)")
async def zoo_cmd(i: discord.Interaction, korisnik: discord.Member = None):
    u   = korisnik or i.user
    zoo = get_zoo(u.id)
    if not zoo or all(v == 0 for v in zoo.values()):
        return await i.response.send_message(
            embed=em(f"🦁 {u.display_name} — Zoo", "Prazno! Idi u `/hunt` i uhvati neku životinje. 🏹", color=COLORS["info"]), ephemeral=True
        )

    sections = []
    for rarity in RARITY_ORDER:
        animals = [(n, cnt) for n, cnt in zoo.items() if n in ANIMALS and ANIMALS[n][1] == rarity and cnt > 0]
        if not animals:
            continue
        ri   = RARITY_EMOJI[rarity]
        rows = [f"{ANIMALS[n][0]} **{n}** `×{cnt}`" for n, cnt in sorted(animals)]
        sections.append(f"{ri} **{rarity.capitalize()}**\n" + "  ".join(rows))

    total   = sum(zoo.values())
    power   = zoo_power(u.id)
    e = discord.Embed(
        title=f"🦁 {u.display_name} — Zoo",
        description="\n\n".join(sections),
        color=COLORS["purple"],
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="📦 Ukupno",   value=f"`{total}` životinja", inline=True)
    e.add_field(name="⚔️ Snaga",    value=f"`{power}`",           inline=True)
    e.set_thumbnail(url=u.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.response.send_message(embed=e)

@bot.tree.command(name="battle", description="⚔️ Bori se sa nekim (kao owo battle)")
async def battle(i: discord.Interaction, korisnik: discord.Member):
    if korisnik.id == i.user.id:
        return await i.response.send_message(embed=em("❌", "Ne možeš se boriti sam sa sobom!", color=COLORS["error"]), ephemeral=True)
    if korisnik.bot:
        return await i.response.send_message(embed=em("❌", "Botovi ne znaju se boriti!", color=COLORS["error"]), ephemeral=True)

    await i.response.defer()
    await asyncio.sleep(2)

    p1 = zoo_power(i.user.id) + random.randint(1, 30)
    p2 = zoo_power(korisnik.id) + random.randint(1, 30)

    if p1 == p2:
        p1 += 1

    winner = i.user if p1 > p2 else korisnik
    loser  = korisnik if p1 > p2 else i.user
    wp, lp = (p1, p2) if p1 > p2 else (p2, p1)

    reward = random.randint(80, 300)
    get_economy(winner.id)["balance"] += reward
    save_data()

    bar_total = 20
    p1_fill = round((p1 / (p1 + p2)) * bar_total)
    p2_fill = bar_total - p1_fill
    bar = f"`{'█' * p1_fill}{'░' * p2_fill}`"

    e = discord.Embed(
        title="⚔️  BITKA!",
        description=(
            f"**{i.user.display_name}** vs **{korisnik.display_name}**\n"
            f"{bar}\n"
            f"⚔️ `{p1}` vs `{p2}` ⚔️"
        ),
        color=COLORS["gold"],
        timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="🏆 Pobjednik",  value=f"**{winner.mention}**",      inline=True)
    e.add_field(name="💀 Poražen",    value=f"{loser.mention}",           inline=True)
    e.add_field(name="💶 Nagrada",    value=f"`+{reward} 💶`",            inline=False)
    e.set_thumbnail(url=winner.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.followup.send(embed=e)

@bot.tree.command(name="sell", description="💰 Prodaj životinje iz zoo-a (kao owo sell)")
@app_commands.describe(zivotinja="Ime životinje (npr. Riba)", kolicina="Koliko prodaješ (default 1)")
async def sell(i: discord.Interaction, zivotinja: str, kolicina: int = 1):
    name = zivotinja.strip().capitalize()
    if name not in ANIMALS:
        names = ", ".join(f"`{n}`" for n in list(ANIMALS.keys())[:15])
        return await i.response.send_message(
            embed=em("❌ Nepoznata životinja", f"Provjeri `/zoo` za listu svojih životinja.\nPrimjeri: {names}", color=COLORS["error"]), ephemeral=True
        )
    zoo = get_zoo(i.user.id)
    owned = zoo.get(name, 0)
    if owned < kolicina or kolicina < 1:
        return await i.response.send_message(
            embed=em("❌ Nemaš dovoljno", f"Imaš samo `{owned}x {ANIMALS[name][0]} {name}`.", color=COLORS["error"]), ephemeral=True
        )
    emoji, rarity, power, value = ANIMALS[name]
    total_earn = value * kolicina
    zoo[name]  = owned - kolicina
    get_economy(i.user.id)["balance"] += total_earn
    save_data()
    await i.response.send_message(embed=em(
        f"💰 Prodato!",
        f"Prodao si `{kolicina}x {emoji} {name}` za **{total_earn} 💶**!",
        color=COLORS["success"],
        fields=[("🏦 Balans", f"`{get_economy(i.user.id)['balance']:,} 💶`", True)]
    ))

@bot.tree.command(name="animals", description="📋 Listu svih životinja i raritet (kao owo animals)")
async def animals_cmd(i: discord.Interaction):
    e = discord.Embed(title="📋 Sve životinje — Raritetna lista", color=COLORS["purple"], timestamp=datetime.now(timezone.utc))
    for rarity in RARITY_ORDER:
        ri    = RARITY_EMOJI[rarity]
        pool  = [(n, d[0], d[2], d[3]) for n, d in ANIMALS.items() if d[1] == rarity]
        lines = [f"{em2} **{n}** — ⚔️`{pw}` 💶`{val}`" for n, em2, pw, val in pool]
        e.add_field(name=f"{ri} {rarity.capitalize()}", value="\n".join(lines), inline=True)
    e.set_footer(text=f"{BOT_NAME} {VERSION} • /hunt za loviti!")
    await i.response.send_message(embed=e)

@bot.tree.command(name="pray", description="🙏 Pomoli se za nekoga (kao owo pray)")
async def pray(i: discord.Interaction, korisnik: discord.Member):
    if korisnik.id == i.user.id:
        return await i.response.send_message(embed=em("❌", "Ne možeš moliti za sebe!", color=COLORS["error"]), ephemeral=True)
    bonus = random.randint(20, 100)
    get_economy(korisnik.id)["balance"] += bonus
    save_data()
    msgs = [
        f"🙏 {i.user.mention} moli se za {korisnik.mention}! Nebo čuje — `+{bonus} 💶` palo s neba!",
        f"✨ {i.user.mention} šalje dobre vibracije {korisnik.mention}! `+{bonus} 💶` u džep!",
        f"🕊️ Zbog molitve {i.user.mention}, {korisnik.mention} je blagosloven sa `{bonus} 💶`!",
    ]
    e = discord.Embed(description=random.choice(msgs), color=0xFFD700, timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"{BOT_NAME} {VERSION}")
    await i.response.send_message(embed=e)

# /curse uklonjeno (v2.1) — semantika "prokletstva" rizična za content moderaciju.

# ═══════════════════════════════════════════
#    AUTO-MOD (Anti-Spam + Bad Words)
# ═══════════════════════════════════════════
SPAM_WINDOW = 5
SPAM_LIMIT  = 7
BAD_WORDS: set = set()  # add bad words here: BAD_WORDS = {"rijec1", "rijec2"}
user_msg_times: dict = defaultdict(deque)

# ── Anti-NSFW (pornografija, slike) ─────────────────────
# ⚠️  Psovke u tekstu su DOZVOLJENE — filtriramo samo NSFW linkove i slike

# Pornografski sajtovi — blokirani kao linkovi/embeds
NSFW_SITES = [
    "pornhub", "xvideos", "xnxx", "redtube", "youporn", "onlyfans",
    "rule34", "e-hentai", "xhamster", "spankbang", "chaturbate",
    "pornpics", "porn.com", "xtube", "4tube", "tube8", "sex.com",
]

# Eksplicitni nazivi fajlova (slike kurca/picke) — blokirani u uploadima
NSFW_FILENAMES = [
    "dick", "cock", "penis", "pussy", "vagina", "kurac", "picka", "pička",
    "pizda", "nude", "nudes", "naked", "cumshot", "blowjob", "anal",
    "hentai", "xxx", "porn", "nsfw", "boobs", "tits",
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi", ".webm"}

# Sigurni domeni — GIF-ovi s ovih servisa su uvijek OK (Discord GIF picker, Tenor, Giphy)
SAFE_DOMAINS = (
    "tenor.com", "media.tenor.com", "tenor.googleapis.com",
    "giphy.com", "media.giphy.com", "media0.giphy.com",
    "media1.giphy.com", "media2.giphy.com",
    "cdn.discordapp.com", "media.discordapp.net",
    "discord.com/channels",
)

def _contains_nsfw_site(text: str) -> str | None:
    if not text: return None
    t = text.lower()
    for w in NSFW_SITES:
        if w in t:
            return w
    return None

def _contains_nsfw_filename(text: str) -> str | None:
    if not text: return None
    t = text.lower()
    for w in NSFW_FILENAMES:
        if w in t:
            return w
    return None

async def check_nsfw(message) -> bool:
    """Briše NSFW sadržaj (slike/linkovi). Vraća True ako je obrisao.
    NAPOMENA: Psovke u tekstu su DOZVOLJENE — ne filtriramo tekst poruke."""
    n = _prot_nsfw()
    if not n["enabled"]:
        return False
    if message.channel.is_nsfw():  # NSFW kanal je dozvoljen
        return False
    # Merge ugrađene + panel extra liste
    all_sites    = list(NSFW_SITES)    + n["extra_sites"]
    all_keywords = list(NSFW_FILENAMES) + n["extra_keywords"]

    def _site_hit(text: str) -> str | None:
        if not text: return None
        t = text.lower()
        for w in all_sites:
            if w in t: return w
        return None

    def _kw_hit(text: str) -> str | None:
        if not text: return None
        t = text.lower()
        for w in all_keywords:
            if w in t: return w
        return None

    found = None

    # 1) Pornografski sajtovi u tekstu/linkovima poruke
    found = _site_hit(message.content)

    # 2) Attachmenti (slike/videi) — provjeri naziv fajla
    if not found:
        for att in message.attachments:
            if any(d in att.url.lower() for d in SAFE_DOMAINS):
                continue
            ext = _os.path.splitext(att.filename.lower())[1]
            if ext in IMAGE_EXTS:
                found = _kw_hit(att.filename)
                if not found:
                    found = _site_hit(att.url)
            if found: break

    # 3) Embeds — provjeri URL i title za NSFW sajtove
    if not found:
        for emb in message.embeds:
            url = emb.url or ""
            if any(d in url.lower() for d in SAFE_DOMAINS):
                continue
            for field in [url, emb.title, emb.description]:
                if field and (found := _site_hit(str(field))): break
            if found: break

    if not found: return False
    # OBRIŠI
    try:
        await message.delete()
    except: pass
    # Upozorenje korisniku
    try:
        await message.channel.send(
            embed=em("🔞 NSFW Sadržaj Zabranjen",
                     f"{message.author.mention} — pornografija/eksplicitan sadržaj nije dozvoljen!\n"
                     f"⚠️ Detektovano: `{found}`\n"
                     f"💡 Za NSFW koristi posebne **age-restricted** kanale.",
                     color=COLORS["error"]),
            delete_after=10
        )
    except: pass
    # Auto-warn + log
    try:
        await audit_log(message.guild, "🔞 Anti-NSFW",
                        f"{message.author.mention} pokušao slati NSFW u {message.channel.mention}\n**Trigger:** `{found}`")
    except: pass
    # Dinamičan strikes limit i timeout iz panel konfiguracije
    nsfw_cfg = _prot_nsfw()
    strike_limit  = nsfw_cfg["strikes"]
    timeout_mins  = nsfw_cfg["timeout_min"]
    nsfw_strikes = data.setdefault("nsfw_strikes", {})
    skey = f"{message.guild.id}:{message.author.id}"
    nsfw_strikes[skey] = nsfw_strikes.get(skey, 0) + 1
    save_data()
    if nsfw_strikes[skey] >= strike_limit:
        try:
            await message.author.timeout(timedelta(minutes=timeout_mins), reason=f"Anti-NSFW: {strike_limit}+ pokušaja")
            await message.channel.send(
                embed=em("🔇 Timeout", f"{message.author.mention} dobio **{timeout_mins}min timeout** zbog ponovljenog NSFW sadržaja!", color=COLORS["error"]),
                delete_after=15
            )
            nsfw_strikes[skey] = 0; save_data()
        except: pass
    return True

# ── Anti-Invite (drugi serveri) ─────────────────────────
INVITE_REGEX = re.compile(
    r"(?:"
    r"discord\s*\.\s*(?:gg|io|me|li)\s*\/\s*[a-zA-Z0-9-]+"
    r"|discord(?:app)?\s*\.\s*com\s*\/\s*invite\s*\/\s*[a-zA-Z0-9-]+"
    r"|dsc\s*\.\s*gg\s*\/\s*[a-zA-Z0-9-]+"
    r"|(?<![a-zA-Z0-9])\.gg\/[a-zA-Z0-9-]+"
    r")",
    re.I
)

ALLOWED_UPLOAD_EXTS = {".gif", ".png", ".jpg", ".jpeg", ".webp", ".apng"}

# ── Globalna anti-invite zaštita za SVE slash (/) komande ─────────────────
# Svaki tekstualni argument na slash komandi se skenira; ako ima invite link,
# komanda se odbija sa ephemeral upozorenjem. (Vlasnici su izuzeti.)
async def _global_invite_check(interaction: discord.Interaction) -> bool:
    try:
        if interaction.type != discord.InteractionType.application_command:
            return True
        u = interaction.user
        if u and getattr(u, "id", None) in OWNER_IDS:
            return True
        ns = getattr(interaction, "namespace", None)
        if ns is None:
            return True
        for _k, _v in vars(ns).items():
            if isinstance(_v, str) and INVITE_REGEX.search(_v):
                try:
                    await interaction.response.send_message(
                        embed=em(
                            "🚫 Reklama zabranjena",
                            f"{u.mention if u else ''} — **invite linkovi nisu dozvoljeni** ni na slash komandama!\n"
                            f"Probaj ponovo bez `discord.gg/...` / `.gg/...` linka.",
                            color=COLORS["error"]
                        ),
                        ephemeral=True
                    )
                except Exception:
                    try:
                        await interaction.followup.send(
                            embed=em("🚫 Reklama zabranjena",
                                     "Invite linkovi nisu dozvoljeni!",
                                     color=COLORS["error"]),
                            ephemeral=True
                        )
                    except Exception: pass
                return False
    except Exception as _e:
        print(f"[global-invite-check] {_e}")
    return True

bot.tree.interaction_check = _global_invite_check

# ── Per-server isključene komande (panel → bot) ──────────────────────────
# Vlasnik servera na panelu (giann.uk) može isključiti pojedine komande za
# SVOJ server. Ovdje ih provjeravamo i blokiramo prije izvršavanja.
_guild_features_cache: dict = {}   # guild_id(str) -> (fetched_at, set(disabled))

async def get_guild_disabled(guild_id) -> set:
    """Vrati set isključenih komandi za dati server (cache 60s)."""
    gkey = str(guild_id)
    now = time.time()
    cached = _guild_features_cache.get(gkey)
    if cached and now - cached[0] < 60:
        return cached[1]
    disabled = cached[1] if cached else set()
    try:
        async with aiohttp.ClientSession() as _s:
            async with _s.get(f"{PANEL_API_URL}/api/guild/{gkey}/features",
                              timeout=aiohttp.ClientTimeout(total=3)) as _r:
                if _r.status == 200:
                    _data = await _r.json()
                    disabled = set(_data.get("disabled", []) or [])
    except Exception as _fe:
        print(f"[guild-features] Fetch error guild={gkey}: {_fe}")
    _guild_features_cache[gkey] = (now, disabled)
    return disabled

async def _combined_interaction_check(interaction: discord.Interaction) -> bool:
    # 1) zadrži postojeću anti-invite zaštitu
    if not await _global_invite_check(interaction):
        return False
    # 2) per-server isključene komande
    try:
        if interaction.type != discord.InteractionType.application_command:
            return True
        if not interaction.guild:
            return True
        cmd = interaction.command.name if interaction.command else None
        if not cmd:
            return True
        disabled = await get_guild_disabled(interaction.guild.id)
        if cmd in disabled:
            try:
                await interaction.response.send_message(
                    embed=em("⏸️ Isključeno",
                             f"Komanda `/{cmd}` je **isključena na ovom serveru**.\n"
                             f"Vlasnik je može ponovo uključiti na panelu (giann.uk).",
                             color=COLORS["warning"]),
                    ephemeral=True
                )
            except Exception:
                pass
            return False
    except Exception as _ce:
        print(f"[guild-features-check] {_ce}")
    return True

bot.tree.interaction_check = _combined_interaction_check

async def check_automod(message) -> bool:
    # ── Anti-Invite filter — vrijedi za SVE (admini, staff, svi) ──
    # Jedini izuzetak su vlasnici u OWNER_IDS.
    if message.author.id not in OWNER_IDS:
        invite_found = INVITE_REGEX.search(message.content or "")
        # Provjeri i u embedima koje je korisnik uključio (embed preview od linkova)
        if not invite_found and message.embeds:
            for _emb in message.embeds:
                _check_texts = [
                    _emb.title or "", _emb.description or "", _emb.url or "",
                    getattr(_emb.footer, "text", "") or "",
                    getattr(_emb.author, "name", "") or "",
                    getattr(_emb.author, "url", "") or "",
                ]
                for _fld in (_emb.fields or []):
                    _check_texts.append(str(_fld.name) + " " + str(_fld.value))
                if any(INVITE_REGEX.search(t) for t in _check_texts):
                    invite_found = True
                    break
        if invite_found:
            try:
                await message.delete()
                await message.channel.send(
                    embed=em("🚫 Reklama zabranjena",
                             f"{message.author.mention} — invite linkovi nisu dozvoljeni ni u porukama ni u embedima!",
                             color=COLORS["error"]),
                    delete_after=8
                )
                await audit_log(message.guild, "🚫 Anti-Invite", f"{message.author.mention} pokušao reklamirati drugi server u {message.channel.mention}")
            except: pass
            return True

    if message.author.guild_permissions.administrator:
        return False

    # ── Upload filter: dozvoli samo slike/GIF-ove (.gif/.png/.jpg/.jpeg/.webp) ──
    # NAPOMENA: NSFW filter postoji odvojeno (check_nsfw) — radi ranije u on_message
    if message.attachments:
        for att in message.attachments:
            fname = (att.filename or "").lower()
            ext = "." + fname.rsplit(".", 1)[-1] if "." in fname else ""
            ctype = (att.content_type or "").lower()
            is_image = ext in ALLOWED_UPLOAD_EXTS or ctype.startswith("image/")
            if not is_image:
                try:
                    await message.delete()
                    await message.channel.send(
                        embed=em("📎 Upload Zabranjen",
                                 f"{message.author.mention} — dozvoljene su **samo slike i GIF-ovi** (.gif, .png, .jpg, .jpeg, .webp).\n"
                                 f"❌ Datoteka: `{att.filename}` blokirana.\n\n"
                                 f"💡 GIF-ovi preko Discord GIF picker-a (Tenor/GIPHY) rade normalno.",
                                 color=COLORS["error"]),
                        delete_after=10
                    )
                    await audit_log(message.guild, "📎 Upload Block", f"{message.author.mention} pokušao uploadati `{att.filename}` u {message.channel.mention}")
                except: pass
                return True
    content_lower = message.content.lower()
    for word in BAD_WORDS:
        if word in content_lower:
            try:
                await message.delete()
                await message.channel.send(
                    embed=em("🛡️ Auto-Mod", f"{message.author.mention} — zabranjene riječi!", color=COLORS["warning"]),
                    delete_after=5
                )
            except Exception:
                pass
            return True
    uid = message.author.id
    now = time.time()
    dq  = user_msg_times[uid]
    dq.append(now)
    while dq and dq[0] < now - SPAM_WINDOW:
        dq.popleft()
    if len(dq) >= SPAM_LIMIT:
        dq.clear()
        try:
            await message.author.timeout(timedelta(seconds=30), reason="Auto-Mod: Spam")
            await message.channel.send(
                embed=em("🛡️ Anti-Spam", f"{message.author.mention} dobio/la timeout od **30s** zbog spama! 🔇", color=COLORS["warning"]),
                delete_after=8
            )
        except Exception:
            pass
    return False

# ═══════════════════════════════════════════
#    BLACKJACK
# ═══════════════════════════════════════════
_RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
_VALS  = {'A':11,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':10,'Q':10,'K':10}
_SUITS = ['♠','♥','♦','♣']

def _new_deck():
    d = [(r, s) for r in _RANKS for s in _SUITS]
    random.shuffle(d)
    return d

def _bj_val(hand):
    val  = sum(_VALS[r] for r, _ in hand)
    aces = sum(1 for r, _ in hand if r == 'A')
    while val > 21 and aces:
        val -= 10; aces -= 1
    return val

def _bj_str(hand, hide=False):
    if hide:
        return f"`{hand[0][0]}{hand[0][1]}`  `🂠`"
    return "  ".join(f"`{r}{s}`" for r, s in hand)

def _bj_embed(player, dealer, oklada, note="", hide=True):
    e = discord.Embed(title="🃏 Blackjack", color=COLORS["dark"], timestamp=datetime.now(timezone.utc))
    e.add_field(name=f"Tvoje karte  ({_bj_val(player)})", value=_bj_str(player),         inline=False)
    e.add_field(name=f"Dealer  {'(?)' if hide else f'({_bj_val(dealer)})'}", value=_bj_str(dealer, hide), inline=False)
    if note:
        e.add_field(name="Rezultat", value=note, inline=False)
    e.set_footer(text=f"Oklada: {oklada:,} 💶 • {BOT_NAME}")
    return e

class BjView(discord.ui.View):
    def __init__(self, deck, player, dealer, oklada, uid):
        super().__init__(timeout=30)
        self.deck = deck; self.player = player; self.dealer = dealer
        self.oklada = oklada; self.uid = uid

    async def _finish(self, i, note, delta, color):
        eco = get_economy(self.uid)
        eco["balance"] = max(0, eco["balance"] + delta)
        save_data()
        self.clear_items()
        e = _bj_embed(self.player, self.dealer, self.oklada, note, hide=False)
        e.color = color
        await i.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Hit", emoji="🃏", style=discord.ButtonStyle.primary)
    async def hit(self, i: discord.Interaction, b):
        if i.user.id != self.uid:
            return await i.response.send_message("Ovo nije tvoja igra!", ephemeral=True)
        self.player.append(self.deck.pop())
        val = _bj_val(self.player)
        if val > 21:
            await self._finish(i, f"💥 **BUST!** Izgubio/la si `{self.oklada:,} 💶`", -self.oklada, COLORS["error"])
        elif val == 21:
            await self.stand.callback(self, i, b)
        else:
            await i.response.edit_message(embed=_bj_embed(self.player, self.dealer, self.oklada), view=self)

    @discord.ui.button(label="Stand", emoji="✋", style=discord.ButtonStyle.secondary)
    async def stand(self, i: discord.Interaction, b):
        if i.user.id != self.uid:
            return await i.response.send_message("Ovo nije tvoja igra!", ephemeral=True)
        while _bj_val(self.dealer) < 17:
            self.dealer.append(self.deck.pop())
        pv, dv = _bj_val(self.player), _bj_val(self.dealer)
        if dv > 21 or pv > dv:
            await self._finish(i, f"🏆 **Pobijedio/la si!** `+{self.oklada:,} 💶`", self.oklada, COLORS["success"])
        elif pv == dv:
            await self._finish(i, "🤝 **Nerješeno!** Oklada vraćena.", 0, COLORS["warning"])
        else:
            await self._finish(i, f"😢 **Dealer pobijedio!** `-{self.oklada:,} 💶`", -self.oklada, COLORS["error"])

    async def on_timeout(self):
        self.clear_items()

@bot.tree.command(name="blackjack", description="🃏 Igraj Blackjack protiv dilera!")
@app_commands.describe(oklada="Koliko 💶 ulažeš (min 10)")
async def blackjack(i: discord.Interaction, oklada: int):
    eco = get_economy(i.user.id)
    if oklada < 10:
        return await i.response.send_message(embed=em("❌", "Minimum oklada je `10 💶`!", color=COLORS["error"]), ephemeral=True)
    if eco["balance"] < oklada:
        return await i.response.send_message(embed=em("❌", f"Nemaš dovoljno! Imaš `{eco['balance']:,} 💶`.", color=COLORS["error"]), ephemeral=True)
    deck = _new_deck()
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    if _bj_val(player) == 21:
        won = int(oklada * 1.5)
        eco["balance"] += won
        save_data()
        e = _bj_embed(player, dealer, oklada, f"🎉 **BLACKJACK!** `+{won:,} 💶`!", hide=False)
        e.color = COLORS["gold"]
        return await i.response.send_message(embed=e)
    view = BjView(deck, player, dealer, oklada, i.user.id)
    await i.response.send_message(embed=_bj_embed(player, dealer, oklada), view=view)

# ═══════════════════════════════════════════
#    TRIVIA / KVIZ
# ═══════════════════════════════════════════
TRIVIA_QS = [
    ("Koji grad je glavni grad Bosne i Hercegovine?", "Sarajevo", ["Mostar","Banja Luka","Tuzla"]),
    ("Koja rijeka teče kroz Beograd?", "Sava", ["Dunav","Drina","Morava"]),
    ("U kojoj godini je Hrvatska ušla u EU?", "2013.", ["2007.","2004.","2015."]),
    ("Ko je napisao 'Na Drini ćuprija'?", "Ivo Andrić", ["Meša Selimović","Branko Ćopić","Dobrica Ćosić"]),
    ("Koliko država je nastalo raspadom Jugoslavije?", "6", ["5","7","4"]),
    ("Koji je najveći grad u Srbiji?", "Beograd", ["Novi Sad","Niš","Kragujevac"]),
    ("Koja je najpopularnija hrana u BiH?", "Ćevapi", ["Sarma","Burek","Pita"]),
    ("Koliko Grand Slam titula ima Novak Đoković?", "24", ["20","22","21"]),
    ("Koji planinski vrh je najviši u Bosni?", "Maglić", ["Bjelašnica","Jahorina","Treskavica"]),
    ("Koji grad je poznat po Guča trubačkom festivalu?", "Guča", ["Niš","Beograd","Čačak"]),
    ("Što znači 'merhaba' na bosanskom?", "Zdravo", ["Hvala","Molim","Doviđenja"]),
    ("Koja je zastava Srbije?", "Crvena, plava, bijela", ["Zelena, bijela, crvena","Plava, žuta, crvena","Bijela, zelena, plava"]),
    ("Koji je broj igrača u ekipi fudbala?", "11", ["10","12","9"]),
    ("Koja zemlja je domaćin Eurosonga 2024?", "Švicarska", ["Švedska","Italija","Hrvatska"]),
    ("Ko je pjevao 'Dragana' na Balkanu?", "Ceca", ["Lepa Brena","Jelena Karleuša","Zorana"]),
    ("Koji je glavni grad Hrvatske?", "Zagreb", ["Split","Rijeka","Osijek"]),
    ("Koliko km² ima Srbija?", "77,474", ["88,000","65,000","92,000"]),
    ("Šta je 'kajmak'?", "Mlječni proizvod", ["Vrsta sira","Vrsta mesa","Vrsta hljeba"]),
    ("Koji je najstariji grad na Balkanu?", "Plovdiv", ["Beograd","Sarajevo","Skoplje"]),
    ("Ko je 'Kralj Balkana' u košarci?", "Novak Đoković", ["Nikola Jokić","Goran Dragić","Predrag Stojaković"]),
]

class TriviaView(discord.ui.View):
    def __init__(self, correct, wrong, oklada, uid, pool=None, title="🧠 Balkan Trivia", combo=1, total_won=0):
        super().__init__(timeout=20)
        self.correct = correct; self.oklada = oklada; self.uid = uid
        self.pool = pool; self.title = title
        self.combo = combo; self.total_won = total_won
        opts = wrong[:3] + [correct]
        random.shuffle(opts)
        for opt in opts:
            btn = discord.ui.Button(label=opt[:80], style=discord.ButtonStyle.primary)
            btn.callback = self._make_cb(opt)
            self.add_item(btn)

    def _make_cb(self, choice):
        async def cb(i: discord.Interaction):
            if i.user.id != self.uid:
                return await i.response.send_message("Ovo nije tvoja igra!", ephemeral=True)
            self.clear_items()
            eco = get_economy(self.uid)
            if choice == self.correct:
                # combo multiplier — više tačnih = veća nagrada
                reward = int(self.oklada * self.combo)
                xp_gain = 25 * self.combo
                eco["balance"] += reward
                add_xp(self.uid, xp_gain); save_data()
                new_total = self.total_won + reward
                # nastavi sa novim pitanjem
                if self.pool:
                    q, c, w = random.choice(self.pool)
                    new_view = TriviaView(c, w, self.oklada, self.uid,
                                          pool=self.pool, title=self.title,
                                          combo=self.combo + 1, total_won=new_total)
                    combo_fx = E_FIRE1 if self.combo < 3 else (E_FIRE2 if self.combo < 6 else (E_FIRE3 if self.combo < 10 else E_FIRE4))
                    e = discord.Embed(
                        title=f"{E_GAME} {self.title}",
                        description=(
                            f"✅ **Tačno!** `+{reward:,} 💶` `+{xp_gain} XP`\n"
                            f"{combo_fx} **Combo:** `x{self.combo}` → sljedeće `x{self.combo+1}`\n"
                            f"💰 **Ukupno osvojeno:** `{new_total:,} 💶`\n\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"**{q}**"
                        ),
                        color=GAME_COLORS["kviz"], timestamp=datetime.now(timezone.utc)
                    )
                    e.add_field(name="💶 Oklada", value=f"`{self.oklada}`", inline=True)
                    e.add_field(name=f"{combo_fx} Combo", value=f"`x{self.combo+1}`", inline=True)
                    e.add_field(name="⏱️ Vrijeme", value="`20s`", inline=True)
                    e.set_footer(text=f"{BOT_NAME} • Nastavi nizom!")
                    return await i.response.edit_message(embed=e, view=new_view)
                # fallback bez pool-a
                result = em("✅ Tačno!", f"**{self.correct}**\n`+{reward} 💶` i `+{xp_gain} XP`!", color=COLORS["success"])
            else:
                eco["balance"] = max(0, eco["balance"] - self.oklada)
                save_data()
                desc = f"Tačan odgovor: **{self.correct}**\n`-{self.oklada} 💶`"
                if self.combo > 1:
                    desc += f"\n\n🔥 Combo prekinut na `x{self.combo}`!\n💰 Osvojeno u nizu: `{self.total_won:,} 💶`"
                result = em("❌ Netačno!", desc, color=COLORS["error"])
            await i.response.edit_message(embed=result, view=self)
        return cb

    async def on_timeout(self):
        self.clear_items()

@bot.tree.command(name="kviz", description="🧠 Odgovori na Balkan pitanje i osvoji pare!")
@app_commands.describe(oklada="Koliko 💶 ulažeš (default 50)")
async def kviz(i: discord.Interaction, oklada: int = 50):
    eco = get_economy(i.user.id)
    if oklada < 10:
        return await i.response.send_message(embed=em("❌", "Minimum je `10 💶`!", color=COLORS["error"]), ephemeral=True)
    if eco["balance"] < oklada:
        return await i.response.send_message(embed=em("❌", f"Nemaš dovoljno! Imaš `{eco['balance']:,} 💶`.", color=COLORS["error"]), ephemeral=True)
    question, correct, wrong = random.choice(TRIVIA_QS)
    view = TriviaView(correct, wrong, oklada, i.user.id, pool=TRIVIA_QS, title="🧠 Balkan Trivia")
    e = em_pro(
        f"{E_GAME} Balkan Trivia",
        f"❓ **{question}**",
        color=GAME_COLORS["kviz"],
        author=i.user,
        fields=[
            ("💶 Oklada",        f"`{oklada:,} 💶`", True),
            (f"{E_FIRE2} Combo", "`x1`",            True),
            ("⏱️ Vrijeme",       "`20 sekundi`",     True),
        ],
        footer=f"{BOT_NAME} • Biraj pažljivo — combo raste sa svakim tačnim!"
    )
    await i.response.send_message(embed=e, view=view)

# ═══════════════════════════════════════════
#    GEOGRAFIJA
# ═══════════════════════════════════════════
GEOGRAFIJA_QS = [
    # ── Balkan ──
    ("🇷🇸 Glavni grad Srbije?", "Beograd", ["Novi Sad", "Niš", "Kragujevac"]),
    ("🇭🇷 Glavni grad Hrvatske?", "Zagreb", ["Split", "Rijeka", "Osijek"]),
    ("🇧🇦 Glavni grad Bosne i Hercegovine?", "Sarajevo", ["Mostar", "Banja Luka", "Tuzla"]),
    ("🇲🇪 Glavni grad Crne Gore?", "Podgorica", ["Cetinje", "Nikšić", "Budva"]),
    ("🇲🇰 Glavni grad Sjeverne Makedonije?", "Skoplje", ["Bitola", "Ohrid", "Tetovo"]),
    ("🇸🇮 Glavni grad Slovenije?", "Ljubljana", ["Maribor", "Celje", "Koper"]),
    ("🇦🇱 Glavni grad Albanije?", "Tirana", ["Drač", "Skadar", "Vlora"]),
    ("🇧🇬 Glavni grad Bugarske?", "Sofija", ["Plovdiv", "Varna", "Burgas"]),
    ("🇬🇷 Glavni grad Grčke?", "Atina", ["Solun", "Patras", "Pirej"]),
    ("🇷🇴 Glavni grad Rumunije?", "Bukurešt", ["Kluž", "Brašov", "Temišvar"]),
    ("🇽🇰 Glavni grad Kosova?", "Priština", ["Prizren", "Peć", "Đakovica"]),
    ("Najduža rijeka kroz Srbiju?", "Dunav", ["Sava", "Morava", "Drina"]),
    ("Najviši vrh na Balkanu?", "Musala", ["Triglav", "Olimp", "Đeravica"]),
    ("U kojoj državi se nalazi Plitvička jezera?", "Hrvatska", ["BiH", "Slovenija", "Crna Gora"]),
    ("Koje more okružuje Crnu Goru?", "Jadransko", ["Egejsko", "Crno", "Sredozemno"]),
    ("Najveći grad u Bosni i Hercegovini?", "Sarajevo", ["Banja Luka", "Tuzla", "Mostar"]),
    ("Rijeka koja teče kroz Mostar?", "Neretva", ["Bosna", "Vrbas", "Una"]),
    ("Koja rijeka razdvaja Srbiju i Rumuniju?", "Dunav", ["Tisa", "Sava", "Drina"]),
    ("Najveće jezero na Balkanu?", "Skadarsko", ["Ohridsko", "Prespansko", "Plavsko"]),
    # ── Svijet ──
    ("Glavni grad Francuske?", "Pariz", ["Lion", "Marseilles", "Nica"]),
    ("Glavni grad Njemačke?", "Berlin", ["Minhen", "Hamburg", "Frankfurt"]),
    ("Glavni grad Italije?", "Rim", ["Milano", "Napulj", "Venecija"]),
    ("Glavni grad Španije?", "Madrid", ["Barcelona", "Sevilja", "Valensija"]),
    ("Glavni grad Engleske?", "London", ["Liverpul", "Mančester", "Oksford"]),
    ("Glavni grad SAD-a?", "Washington", ["New York", "Los Angeles", "Chicago"]),
    ("Glavni grad Rusije?", "Moskva", ["Sankt Peterburg", "Kazan", "Soči"]),
    ("Glavni grad Japana?", "Tokio", ["Kjoto", "Osaka", "Hirošima"]),
    ("Glavni grad Kine?", "Peking", ["Šangaj", "Hong Kong", "Guangžou"]),
    ("Glavni grad Australije?", "Canberra", ["Sydney", "Melbourne", "Perth"]),
    ("Glavni grad Brazila?", "Brasilia", ["Rio de Janeiro", "São Paulo", "Salvador"]),
    ("Glavni grad Argentine?", "Buenos Aires", ["Kordoba", "Rosario", "Mendoza"]),
    ("Glavni grad Egipta?", "Kairo", ["Aleksandrija", "Luksor", "Giza"]),
    ("Glavni grad Turske?", "Ankara", ["Istanbul", "Izmir", "Antalija"]),
    ("Najduža rijeka na svijetu?", "Nil", ["Amazon", "Misisipi", "Jangcekjang"]),
    ("Najviši vrh na svijetu?", "Mount Everest", ["K2", "Kangčendžunga", "Lhotse"]),
    ("Najveći okean?", "Tihi", ["Atlantski", "Indijski", "Arktički"]),
    ("Najveće jezero na svijetu?", "Kaspijsko", ["Bajkalsko", "Gornje", "Viktorijino"]),
    ("Najveći kontinent po površini?", "Azija", ["Afrika", "Sjeverna Amerika", "Evropa"]),
    ("Najveća pustinja na svijetu?", "Sahara", ["Gobi", "Kalahari", "Atakama"]),
    ("U kojoj zemlji je Eiffelov toranj?", "Francuska", ["Italija", "Njemačka", "Belgija"]),
    ("U kojoj zemlji je Coloseum?", "Italija", ["Grčka", "Španija", "Francuska"]),
    ("U kojoj zemlji se nalazi Statua slobode?", "SAD", ["Francuska", "Kanada", "Meksiko"]),
    ("Koja zemlja ima najviše stanovnika?", "Indija", ["Kina", "SAD", "Indonezija"]),
    ("Koliko kontinenata postoji?", "7", ["5", "6", "8"]),
    ("U kojem oceanu se nalaze Maldivi?", "Indijski", ["Tihi", "Atlantski", "Arktički"]),
    ("Glavni grad Holandije?", "Amsterdam", ["Hag", "Roterdam", "Utreht"]),
    ("Glavni grad Švicarske?", "Bern", ["Zurih", "Ženeva", "Bazel"]),
    ("Glavni grad Norveške?", "Oslo", ["Bergen", "Trondheim", "Stavanger"]),
    ("Glavni grad Švedske?", "Stockholm", ["Geteborg", "Malme", "Upsala"]),
    ("Glavni grad Finske?", "Helsinki", ["Tampere", "Turku", "Espoo"]),
]

@bot.tree.command(name="geografija", description="🌍 Geografski kviz — pogodi i osvoji pare!")
@app_commands.describe(oklada="Koliko 💶 ulažeš (default 50)")
async def geografija(i: discord.Interaction, oklada: int = 50):
    eco = get_economy(i.user.id)
    if oklada < 10:
        return await i.response.send_message(embed=em("❌", "Minimum je `10 💶`!", color=COLORS["error"]), ephemeral=True)
    if eco["balance"] < oklada:
        return await i.response.send_message(embed=em("❌", f"Nemaš dovoljno! Imaš `{eco['balance']:,} 💶`.", color=COLORS["error"]), ephemeral=True)
    question, correct, wrong = random.choice(GEOGRAFIJA_QS)
    view = TriviaView(correct, wrong, oklada, i.user.id, pool=GEOGRAFIJA_QS, title="🌍 Geografija")
    e = discord.Embed(title="🌍 Geografija", description=f"**{question}**", color=COLORS["info"], timestamp=datetime.now(timezone.utc))
    e.add_field(name="💶 Oklada", value=f"`{oklada}`", inline=True)
    e.add_field(name="⏱️ Vrijeme", value="`20 sekundi`", inline=True)
    e.set_footer(text=f"{BOT_NAME} • Putuj svijetom!")
    await i.response.send_message(embed=e, view=view)

# ═══════════════════════════════════════════
#    KOCKA (DICE)
# ═══════════════════════════════════════════
_DICE_FACES = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"}

# /kocka uklonjeno (na zahtjev)

# ═══════════════════════════════════════════
#    SHOP + KUPI
# ═══════════════════════════════════════════
SHOP_ITEMS = {
    "lucky_hunter": {"name": "🍀 Srećni Lovac", "desc":"2× šansa za lov na životinju (1h)",  "price":800,  "duration":3600},
    "xp_boost":     {"name": "⚡ XP Boost",      "desc":"2× XP od poruka (1h)",               "price":1000, "duration":3600},
    "shield":       {"name": "🛡️ Štit",         "desc":"Zaštita od krađe (24h)",             "price":600,  "duration":86400},
    "double_steal": {"name": "💣 Bomba",         "desc":"Sljedeća krađa donosi duplo",        "price":400,  "duration":None},
    "daily_boost":  {"name": "📅 Daily Boost",   "desc":"+500 💶 bonusa na sljedeći /daily",  "price":350,  "duration":None},
}

def get_items(uid):
    eco = get_economy(uid)
    eco.setdefault("items", {})
    return eco["items"]

def has_item(uid, key):
    items = get_items(uid)
    if key not in items:
        return False
    item = SHOP_ITEMS.get(key, {})
    if item.get("duration"):
        if time.time() > items[key]:
            del items[key]; return False
        return True
    return bool(items.get(key))

@bot.tree.command(name="shop", description="🛒 Pogledaj šta možeš kupiti")
async def shop(i: discord.Interaction):
    e = discord.Embed(title="🛒 GIAN Shop", description="Kupi predmete sa `/kupi <id>` komandom:", color=COLORS["purple"], timestamp=datetime.now(timezone.utc))
    for key, item in SHOP_ITEMS.items():
        dur = "Jednom" if not item["duration"] else f"{item['duration']//3600}h" if item["duration"] >= 3600 else f"{item['duration']//60}min"
        e.add_field(name=item["name"], value=f"**ID:** `{key}`\n{item['desc']}\n⏳ `{dur}` • 💶 `{item['price']:,}`", inline=True)
    e.set_footer(text=f"{BOT_NAME} • /kupi <id> za kupovinu")
    await i.response.send_message(embed=e)

@bot.tree.command(name="kupi", description="💳 Kupi predmet iz shopa")
@app_commands.describe(predmet="ID predmeta iz /shop")
async def kupi(i: discord.Interaction, predmet: str):
    if predmet not in SHOP_ITEMS:
        return await i.response.send_message(embed=em("❌", "Nepoznat predmet! Provjeri `/shop` za listu.", color=COLORS["error"]), ephemeral=True)
    item = SHOP_ITEMS[predmet]
    eco  = get_economy(i.user.id)
    if eco["balance"] < item["price"]:
        return await i.response.send_message(embed=em("❌", f"Nemaš dovoljno! Trebaš `{item['price']:,} 💶`.", color=COLORS["error"]), ephemeral=True)
    eco["balance"] -= item["price"]
    items = get_items(i.user.id)
    items[predmet] = (time.time() + item["duration"]) if item["duration"] else True
    save_data()
    await i.response.send_message(embed=em_pro(
        f"✅ Kupovina Uspješna",
        f"🎁 Nabavio si **{item['name']}**!\n*{item['desc']}*",
        color=COLORS["success"], author=i.user, thumb=i.user.display_avatar.url, fields=[
            ("💸 Cijena", f"```diff\n- {item['price']:,} 💶\n```", True),
            ("🏦 Balans", f"```yaml\n{eco['balance']:,} 💶\n```", True),
        ]
    ))

# ═══════════════════════════════════════════
#    QUESTS / DNEVNI ZADACI
# ═══════════════════════════════════════════
QUEST_POOL = [
    {"id":"hunt5",   "name": "🏹 Lovac",      "desc":"Ulovi 5 životinja",           "target":5,  "reward":200},
    {"id":"work3",   "name": "💼 Radnik",      "desc":"Radi posao 3 puta",           "target":3,  "reward":300},
    {"id":"msgs20",  "name": "💬 Pričalo",     "desc":"Pošalji 20 poruka",           "target":20, "reward":150},
    {"id":"bj_win",  "name": "🃏 Kockar",      "desc":"Pobijedi u Blackjacku",       "target":1,  "reward":500},
    {"id":"kviz3",   "name": "🧠 Znalac",      "desc":"Tačno odgovori na 3 kviz pitanja","target":3,"reward":400},
    {"id":"hunt10",  "name": "🎯 Pro Lovac",   "desc":"Ulovi 10 životinja",          "target":10, "reward":500},
    {"id":"daily1",  "name": "📅 Redovan",     "desc":"Uzmi /daily nagradu",         "target":1,  "reward":250},
]

def get_quests(uid):
    key   = str(uid)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data["quests"].setdefault(key, {})
    if data["quests"][key].get("date") != today:
        chosen = random.sample(QUEST_POOL, 3)
        data["quests"][key] = {
            "date":     today,
            "assigned": [q["id"] for q in chosen],
            "progress": {q["id"]: 0 for q in chosen},
            "done":     {q["id"]: False for q in chosen},
        }
    return data["quests"][key]

def quest_progress(uid, quest_id, amount=1):
    qd = get_quests(uid)
    if quest_id not in qd["progress"] or qd["done"].get(quest_id):
        return None
    qd["progress"][quest_id] += amount
    quest = next((q for q in QUEST_POOL if q["id"] == quest_id), None)
    if quest and qd["progress"][quest_id] >= quest["target"]:
        qd["done"][quest_id] = True
        get_economy(uid)["balance"] += quest["reward"]
        save_data()
        return quest
    save_data()
    return None

@bot.tree.command(name="quests", description="📋 Pogledaj svoje dnevne zadatke")
async def quests_cmd(i: discord.Interaction):
    qd    = get_quests(i.user.id)
    save_data()
    lines = []
    for qid in qd["assigned"]:
        quest = next(q for q in QUEST_POOL if q["id"] == qid)
        prog  = qd["progress"].get(qid, 0)
        done  = qd["done"].get(qid, False)
        check = "✅" if done else "⬜"
        fill  = min(prog, quest["target"])
        bar   = f"`{'█' * fill}{'░' * (quest['target'] - fill)}`"
        lines.append(f"{check} **{quest['name']}** — {quest['desc']}\n{bar} `{prog}/{quest['target']}` • 💶 `+{quest['reward']}`")
    done_count = sum(1 for qid in qd["assigned"] if qd["done"].get(qid))
    e = discord.Embed(
        title="📋 Dnevni Zadaci",
        description="\n\n".join(lines),
        color=COLORS["info"], timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="✅ Završeno", value=f"`{done_count}/3`", inline=True)
    e.set_footer(text=f"Resetuju se u ponoć UTC • {BOT_NAME}")
    await i.response.send_message(embed=e)

# ═══════════════════════════════════════════
#    GIVEAWAY
# ═══════════════════════════════════════════
active_giveaways: dict = {}

def _save_giveaway(msg_id, ga):
    """Persistira giveaway u data fajl (preživljava restart)."""
    data.setdefault("active_giveaways", {})[str(msg_id)] = {
        "entrants": list(ga["entrants"]),
        "prize": ga["prize"],
        "channel_id": ga["channel_id"],
        "msg_id": ga["msg_id"],
        "end_at": ga.get("end_at"),
        "guild_id": ga.get("guild_id"),
    }
    save_data()

def _remove_giveaway(msg_id):
    data.get("active_giveaways", {}).pop(str(msg_id), None)
    save_data()

class GiveawayView(discord.ui.View):
    def __init__(self, msg_id=None):
        super().__init__(timeout=None)
        self.msg_id = msg_id

    @discord.ui.button(label="Učestvuj", emoji="🎉", style=discord.ButtonStyle.success, custom_id="ga_enter")
    async def enter(self, i: discord.Interaction, b):
        # Pronađi giveaway preko msg_id (interaction message ako self.msg_id None)
        mid = self.msg_id or i.message.id
        ga = active_giveaways.get(mid)
        if not ga:
            return await i.response.send_message("Nagradna igra je završena!", ephemeral=True)
        if i.user.id in ga["entrants"]:
            ga["entrants"].discard(i.user.id)
            await i.response.send_message("Odjavljen/a si sa nagradne igre.", ephemeral=True)
        else:
            ga["entrants"].add(i.user.id)
            await i.response.send_message("✅ Prijavljen/a si! Sretno! 🍀", ephemeral=True)
        _save_giveaway(mid, ga)
        try:
            msg = await i.channel.fetch_message(mid)
            e   = msg.embeds[0]
            e.set_field_at(1, name="👥 Učesnici", value=f"`{len(ga['entrants'])}`", inline=True)
            await msg.edit(embed=e)
        except Exception:
            pass

giveaway_group = app_commands.Group(name="giveaway", description="🎉 Nagradne igre")

def _gw_fmt_duration(minuta: int) -> str:
    """Pretvori minute u 'Xh Ymin' string."""
    if minuta <= 0: return "0min"
    h, m = divmod(int(minuta), 60)
    if h and m: return f"{h}h {m}min"
    if h:       return f"{h}h"
    return f"{m}min"

async def _gw_timer(msg_id: int, channel: discord.TextChannel, seconds: float):
    """Pozadinski timer — preživljava jer je odvojen od interaction context-a."""
    try:
        await asyncio.sleep(max(1.0, seconds))
        await _end_giveaway(msg_id, channel)
    except asyncio.CancelledError:
        pass
    except Exception as ex:
        print(f"[giveaway timer] msg={msg_id} error: {ex}")

@giveaway_group.command(name="start", description="🎉 Pokreni nagradnu igru")
@app_commands.describe(nagrada="Šta se osvaja", minuta="Koliko minuta traje (npr. 60 = 1h, 120 = 2h)", kanal="Kanal (default ovaj)")
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_start(i: discord.Interaction, nagrada: str, minuta: int = 60, kanal: discord.TextChannel = None):
    if minuta < 1:
        return await i.response.send_message(
            embed=em("❌", "Minimalno trajanje je **1 minut**.", color=COLORS["error"]), ephemeral=True)
    if minuta > 60 * 24 * 14:
        return await i.response.send_message(
            embed=em("❌", "Maksimalno trajanje je **14 dana** (20160 minuta).", color=COLORS["error"]), ephemeral=True)
    chan = kanal or i.channel
    end  = datetime.now(timezone.utc) + timedelta(minutes=minuta)
    end_ts = int(end.timestamp())
    duration_txt = _gw_fmt_duration(minuta)
    e = discord.Embed(
        title="🎉 NAGRADNA IGRA!",
        description=f"## 🏆  {nagrada}\n\nKlikni dugme **🎉 Učestvuj** da se prijaviš!",
        color=COLORS["gold"], timestamp=end
    )
    e.add_field(name="🕒 Trajanje",  value=f"`{duration_txt}` ({minuta} min)",       inline=True)
    e.add_field(name="👥 Učesnici",  value="`0`",                                    inline=True)
    e.add_field(name="🎟️ Domaćin",   value=i.user.mention,                           inline=True)
    e.add_field(name="📅 Završava",  value=f"<t:{end_ts}:F>\n⏰ <t:{end_ts}:R>",     inline=False)
    e.set_footer(text=f"Završava se automatski • {BOT_NAME}")
    await i.response.send_message(
        embed=em("✅ Pokrenuto!",
                 f"Nagradna igra **{nagrada}** poslata u {chan.mention}.\n🕒 Trajanje: **{duration_txt}**\n📅 Kraj: <t:{end_ts}:F>",
                 color=COLORS["success"]),
        ephemeral=True
    )
    msg = await chan.send(embed=e)
    ga  = {
        "entrants": set(), "prize": nagrada, "channel_id": chan.id,
        "msg_id": msg.id, "end_at": end.timestamp(), "guild_id": chan.guild.id,
    }
    active_giveaways[msg.id] = ga
    _save_giveaway(msg.id, ga)
    await msg.edit(view=GiveawayView(msg.id))
    # Timer u POZADINI — interaction se zatvara odmah, giveaway nastavlja
    asyncio.create_task(_gw_timer(msg.id, chan, minuta * 60))

@giveaway_group.command(name="end", description="🏁 Završi nagradnu igru odmah")
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_end(i: discord.Interaction):
    for mid, ga in list(active_giveaways.items()):
        if ga["channel_id"] == i.channel_id:
            await i.response.send_message("Završavam nagradnu igru...", ephemeral=True)
            await _end_giveaway(mid, i.channel)
            return
    await i.response.send_message("Nema aktivnih nagradnih igara u ovom kanalu!", ephemeral=True)

async def _end_giveaway(msg_id, channel):
    ga = active_giveaways.pop(msg_id, None)
    _remove_giveaway(msg_id)
    if not ga: return
    try: msg = await channel.fetch_message(msg_id)
    except: return
    if not ga["entrants"]:
        e = discord.Embed(title="🎉 Nagradna igra završena", description="Niko se nije prijavio! 😢", color=COLORS["error"])
        await msg.edit(embed=e, view=None); return
    winner_id = random.choice(list(ga["entrants"]))
    winner    = channel.guild.get_member(winner_id)
    e = discord.Embed(
        title="🎉 Nagradna igra ZAVRŠENA!",
        description=f"## 🏆 {ga['prize']}\n\n🥳 Pobjednik: **{winner.mention if winner else f'<@{winner_id}>'}**!",
        color=COLORS["gold"], timestamp=datetime.now(timezone.utc)
    )
    e.add_field(name="👥 Učesnici", value=f"`{len(ga['entrants'])}`", inline=True)
    e.set_footer(text=f"{BOT_NAME} • Čestitamo!")
    await msg.edit(embed=e, view=None)
    await channel.send(f"🎊 Čestitamo {winner.mention if winner else f'<@{winner_id}>'}! Pobijedio/la si **{ga['prize']}**! 🏆")

bot.tree.add_command(giveaway_group)

# ═══════════════════════════════════════════
#    🔄 RESET GIVEAWAY (5 min)
# ═══════════════════════════════════════════
async def _reset_gw_worker(chan: discord.TextChannel, host: discord.Member, nagrada: str):
    """Pozadinski radnik — sačeka 5 min, pa pokrene giveaway na 60min."""
    try:
        await asyncio.sleep(300)
        end    = datetime.now(timezone.utc) + timedelta(minutes=60)
        end_ts = int(end.timestamp())
        ga_e = discord.Embed(
            title="🎉 NAGRADNA IGRA!",
            description=f"## 🏆  {nagrada}\n\nKlikni dugme **🎉 Učestvuj** da se prijaviš!",
            color=COLORS["gold"], timestamp=end
        )
        ga_e.add_field(name="🕒 Trajanje",  value="`1h` (60 min)",               inline=True)
        ga_e.add_field(name="👥 Učesnici", value="`0`",                          inline=True)
        ga_e.add_field(name="🎟️ Domaćin", value=host.mention,                   inline=True)
        ga_e.add_field(name="📅 Završava", value=f"<t:{end_ts}:F>\n⏰ <t:{end_ts}:R>", inline=False)
        ga_e.set_footer(text=f"Završava se automatski • {BOT_NAME}")
        msg = await chan.send(embed=ga_e)
        ga = {"entrants": set(), "prize": nagrada, "channel_id": chan.id,
              "msg_id": msg.id, "end_at": end.timestamp(), "guild_id": chan.guild.id}
        active_giveaways[msg.id] = ga
        _save_giveaway(msg.id, ga)
        await msg.edit(view=GiveawayView(msg.id))
        asyncio.create_task(_gw_timer(msg.id, chan, 60 * 60))
    except Exception as ex:
        print(f"[reset_gw worker] error: {ex}")

@bot.tree.command(name="reset-gw", description="🔄 [ADMIN] Resetuj i ponovo pokreni giveaway za 5 minuta")
@app_commands.describe(nagrada="Nagrada za novi giveaway", kanal="Kanal (default ovaj)")
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.has_permissions(manage_guild=True)
async def reset_gw_cmd(i: discord.Interaction, nagrada: str, kanal: discord.TextChannel = None):
    chan = kanal or i.channel
    for mid, ga in list(active_giveaways.items()):
        if ga["channel_id"] == chan.id:
            active_giveaways.pop(mid, None)
            _remove_giveaway(mid)
    start_ts = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
    sep = "═══════════════════════════"
    countdown_e = discord.Embed(
        title="🔄 ɢɪᴠᴇᴀᴡᴀʏ ʀᴇꜱᴇᴛ!",
        description=(
            f"```ansi\n\u001b[1;36m{sep}\u001b[0m\n```"
            f"⏳ **Novi giveaway počinje za 5 minuta!** (<t:{start_ts}:R>)\n\n"
            f"```yaml\n"
            f"Nagrada  : {nagrada}\n"
            f"Trajanje : 1h (60 min)\n"
            f"Kanal    : #{chan.name}\n"
            f"Pokrece  : {i.user.display_name}\n"
            f"Pocinje  : za 5 min\n"
            f"```"
        ),
        color=COLORS["aqua"], timestamp=datetime.now(timezone.utc)
    )
    countdown_e.set_footer(text=f"🎉 {BOT_NAME} • Giveaway Reset")
    await i.response.send_message(embed=countdown_e)
    asyncio.create_task(_reset_gw_worker(chan, i.user, nagrada))

# ═══════════════════════════════════════════
#    💰 OWNER-ONLY: DODAJ / ODUZMI NOVAC
# ═══════════════════════════════════════════
@bot.tree.command(name="novac", description="💰 [OWNER] Dodaj ili oduzmi coina korisniku")
@app_commands.describe(akcija="dodaj ili oduzmi", korisnik="Kome mijenjamo balans", iznos="Koliko coina")
async def novac_cmd(i: discord.Interaction, akcija: str, korisnik: discord.Member, iznos: int):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("⛔ Zabranjen pristup!", "Ova komanda je samo za **Vlasnika** bota.", color=COLORS["error"]),
            ephemeral=True
        )
    akcija_norm = akcija.lower().strip()
    if akcija_norm not in ("dodaj", "oduzmi", "add", "remove"):
        return await i.response.send_message(
            embed=em("❌ Greška", "Akcija mora biti `dodaj` ili `oduzmi`.\nPrimjer: `/novac dodaj @korisnik 500`", color=COLORS["error"]),
            ephemeral=True
        )
    if iznos <= 0:
        return await i.response.send_message(embed=em("❌", "Iznos mora biti pozitivan!", color=COLORS["error"]), ephemeral=True)
    eco = get_economy(korisnik.id)
    if akcija_norm in ("dodaj", "add"):
        eco["balance"] += iznos
        save_data()
        await i.response.send_message(embed=discord.Embed(
            title="💰 ᴅᴏᴅᴀɴᴏ ᴄᴏɪɴᴀ!",
            description=(
                f"```yaml\n"
                f"Korisnik : {korisnik.display_name}\n"
                f"Dodano   : +{iznos:,} coina\n"
                f"Novi bal : {eco['balance']:,} coina\n"
                f"Vlasnik  : {i.user.display_name}\n"
                f"```"
            ),
            color=COLORS["aqua"], timestamp=datetime.now(timezone.utc)
        ).set_footer(text=f"💰 {BOT_NAME} • Owner Komanda"), ephemeral=True)
    else:
        eco["balance"] = max(0, eco["balance"] - iznos)
        save_data()
        await i.response.send_message(embed=discord.Embed(
            title="💸 ᴏᴅᴜᴢᴇᴛᴏ ᴄᴏɪɴᴀ!",
            description=(
                f"```yaml\n"
                f"Korisnik : {korisnik.display_name}\n"
                f"Oduzeto  : -{iznos:,} coina\n"
                f"Novi bal : {eco['balance']:,} coina\n"
                f"Vlasnik  : {i.user.display_name}\n"
                f"```"
            ),
            color=COLORS["warning"], timestamp=datetime.now(timezone.utc)
        ).set_footer(text=f"💸 {BOT_NAME} • Owner Komanda"), ephemeral=True)

# ═══════════════════════════════════════════
#    POLL / GLASANJE
# ═══════════════════════════════════════════
@bot.tree.command(name="poll", description="📊 Napravi glasanje sa reakcijama")
@app_commands.describe(pitanje="Pitanje", opcija1="1. opcija", opcija2="2. opcija", opcija3="3. opcija (opcionalno)", opcija4="4. opcija (opcionalno)")
async def poll(i: discord.Interaction, pitanje: str, opcija1: str, opcija2: str, opcija3: str = None, opcija4: str = None):
    opts   = [o for o in [opcija1, opcija2, opcija3, opcija4] if o]
    emojis = ["1️⃣","2️⃣","3️⃣","4️⃣"]
    desc   = "\n".join(f"{emojis[idx]}  **{opt}**" for idx, opt in enumerate(opts))
    e = discord.Embed(title=f"📊 {pitanje}", description=desc, color=COLORS["info"], timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"Glasaj sa emoji reakcijama • {BOT_NAME}")
    e.set_author(name=i.user.display_name, icon_url=i.user.display_avatar.url)
    await i.response.send_message(embed=e)
    msg = await i.original_response()
    for idx in range(len(opts)):
        await msg.add_reaction(emojis[idx])

# ═══════════════════════════════════════════
#    TICKET SISTEM
# ═══════════════════════════════════════════
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Zatvori Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close(self, i: discord.Interaction, b):
        await i.response.send_message("🔒 Ticket se zatvara za 5 sekundi...", ephemeral=False)
        await asyncio.sleep(5)
        try:
            await i.channel.delete(reason=f"Ticket zatvorio {i.user}")
        except discord.Forbidden:
            await i.channel.send("❌ Nemam permisiju da obrišem kanal. Obriši ručno.")
        except Exception:
            pass

class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Otvori Ticket", emoji="🎫", style=discord.ButtonStyle.primary, custom_id="ticket_open")
    async def open_ticket(self, i: discord.Interaction, b):
        await i.response.defer(ephemeral=True)
        guild    = i.guild
        safe_name = "".join(c for c in i.user.name.lower() if c.isalnum() or c in "-_")[:20] or str(i.user.id)
        existing  = discord.utils.get(guild.text_channels, name=f"ticket-{safe_name}")
        if existing:
            return await i.followup.send(f"Već imaš otvoren ticket: {existing.mention}", ephemeral=True)

        # Check bot has Manage Channels
        if not guild.me.guild_permissions.manage_channels:
            return await i.followup.send("❌ Bot nema **Manage Channels** permisiju. Daj mu je u Server Settings!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            i.user:             discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me:           discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        try:
            # Try to put tickets in a "tickets" category if it exists
            category = discord.utils.get(guild.categories, name="Tickets") or \
                       discord.utils.get(guild.categories, name="tickets")
            chan = await guild.create_text_channel(
                f"ticket-{safe_name}",
                overwrites=overwrites,
                category=category,
                reason=f"Ticket od {i.user}",
                topic=f"Ticket od {i.user} ({i.user.id})"
            )
        except discord.Forbidden:
            return await i.followup.send("❌ Bot nema permisiju da kreira kanale! Dodaj **Manage Channels** u server settings.", ephemeral=True)
        except Exception as ex:
            return await i.followup.send(f"❌ Greška: `{ex}`", ephemeral=True)

        e = discord.Embed(
            title="🎫 Ticket Otvoren",
            description=(
                f"Zdravo {i.user.mention}! 👋\n\n"
                f"Opiši problem ili pitanje i tim će ti odgovoriti uskoro. 🙏\n\n"
                f"Kad završiš, klikni **Zatvori Ticket** ispod."
            ),
            color=COLORS["info"], timestamp=datetime.now(timezone.utc)
        )
        e.set_thumbnail(url=i.user.display_avatar.url)
        e.set_footer(text=f"{BOT_NAME} • Ticket Sistem")
        await chan.send(content=i.user.mention, embed=e, view=TicketCloseView())
        await i.followup.send(f"✅ Ticket otvoren: {chan.mention}", ephemeral=True)

@bot.tree.command(name="ticket-setup", description="🎫 Postavi ticket sistem u ovaj kanal")
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.has_permissions(administrator=True)
async def ticket_setup(i: discord.Interaction):
    # Respond FIRST, then send the panel
    await i.response.defer(ephemeral=True)

    # Check bot permissions
    missing = []
    perms = i.guild.me.guild_permissions
    if not perms.manage_channels: missing.append("`Manage Channels`")
    if not perms.manage_roles:    missing.append("`Manage Roles`")
    if not perms.send_messages:   missing.append("`Send Messages`")
    if missing:
        return await i.followup.send(
            f"❌ Botu nedostaju permisije: {', '.join(missing)}\n"
            f"Dodaj ih u **Server Settings → Roles → GIAN (Custom)** (bot) pa pokušaj ponovo.",
            ephemeral=True
        )

    e = discord.Embed(
        title="🎫 Sistem Podrške",
        description=(
            "Imaš problem ili pitanje? Klikni dugme ispod!\n\n"
            "Otvorit će ti se privatni kanal sa timom.\n"
            "Odgovorit ćemo što prije! 🙏"
        ),
        color=COLORS["info"], timestamp=datetime.now(timezone.utc)
    )
    if i.guild.icon:
        e.set_thumbnail(url=i.guild.icon.url)
    e.set_footer(text=f"{BOT_NAME} • Ticket Sistem")
    try:
        await i.channel.send(embed=e, view=TicketOpenView())
        await i.followup.send("✅ Ticket sistem postavljen uspješno!", ephemeral=True)
    except discord.Forbidden:
        await i.followup.send("❌ Nemam permisiju da pišem u ovaj kanal!", ephemeral=True)

class SupportTicketModal(discord.ui.Modal, title="🎫 Otvori Tiket za Podršku"):
    razlog = discord.ui.TextInput(
        label="Razlog tiketa (kratko)",
        placeholder="Npr: Problem sa ulogom, ban žalba, pitanje...",
        min_length=3, max_length=100,
        style=discord.TextStyle.short,
    )
    opis = discord.ui.TextInput(
        label="Opiši problem detaljno",
        placeholder="Reci nam što preciznije šta se dešava...",
        min_length=10, max_length=800,
        style=discord.TextStyle.paragraph,
    )
    pokusao = discord.ui.TextInput(
        label="Šta si već pokušao/la?",
        placeholder="Npr: Kontaktirao/la sam moda, čitao/la pravila...",
        min_length=3, max_length=400,
        style=discord.TextStyle.paragraph,
        required=False,
    )

    async def on_submit(self, i: discord.Interaction):
        guild     = i.guild
        safe_name = "".join(c for c in i.user.name.lower() if c.isalnum() or c in "-_")[:20] or str(i.user.id)
        existing  = discord.utils.get(guild.text_channels, name=f"ticket-{safe_name}")
        if existing:
            return await i.response.send_message(
                embed=em("✅ Već otvoren", f"Imaš već otvoren tiket: {existing.mention}", color=COLORS["warning"]),
                ephemeral=True
            )
        if not guild.me.guild_permissions.manage_channels:
            return await i.response.send_message(
                embed=em("❌ Permisija", "Bot nema **Manage Channels** permisiju! Javi adminu.", color=COLORS["error"]),
                ephemeral=True
            )
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            i.user:             discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me:           discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        try:
            category = discord.utils.get(guild.categories, name="Tickets") or \
                       discord.utils.get(guild.categories, name="tickets")
            chan = await guild.create_text_channel(
                f"ticket-{safe_name}",
                overwrites=overwrites,
                category=category,
                reason=f"Ticket od {i.user}",
                topic=f"Ticket od {i.user} ({i.user.id})"
            )
        except discord.Forbidden:
            return await i.response.send_message(
                embed=em("❌ Permisija", "Bot nema dozvolu da kreira kanale!", color=COLORS["error"]),
                ephemeral=True
            )
        except Exception as ex:
            return await i.response.send_message(
                embed=em("❌ Greška", f"`{ex}`", color=COLORS["error"]),
                ephemeral=True
            )

        BAR = "━━━━━━━━━━━━━━━━━━━━━"
        e = discord.Embed(
            title="🎫  Novi Tiket za Podršku",
            description=(
                f"{BAR}\n"
                f"👤 **{i.user.display_name}** ({i.user.mention})\n"
                f"🆔 ID: `{i.user.id}`\n"
                f"📅 Nalog: <t:{int(i.user.created_at.timestamp())}:R>\n"
                f"{BAR}"
            ),
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        e.set_thumbnail(url=i.user.display_avatar.url)
        e.add_field(name="📌  Razlog tiketa",       value=self.razlog.value,                        inline=False)
        e.add_field(name="📝  Opis problema",        value=self.opis.value,                          inline=False)
        e.add_field(name="🔍  Što je pokušano",      value=self.pokusao.value or "*(nije navedeno)*", inline=False)
        e.add_field(
            name="⚙️  Upute za Staff",
            value=(
                "✅ Odgovori što prije i pomozi članu\n"
                "✅ Postavi pitanja ako treba više info\n"
                "✅ Kad je riješeno — zatvori ticket\n"
                "🔒 Klikni **Zatvori Ticket** kad završiš"
            ),
            inline=False,
        )
        e.set_footer(text=f"🎫 GIAN Ticket Sistem  •  {guild.name}")

        await chan.send(content=i.user.mention, embed=e, view=TicketCloseView())

        potvrda = discord.Embed(
            title="✅  Tiket otvoren!",
            description=(
                f"## 🎉 Tvoj tiket je kreiran!\n"
                f"Privatni kanal: {chan.mention}\n\n"
                f"⏳ Staff će ti odgovoriti uskoro. Budemo te obavijestili! 📩"
            ),
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        potvrda.add_field(
            name="📋  Šta dalje?",
            value=(
                "💬 Idi u kanal i čekaj odgovor staffa\n"
                "📎 Možeš priložiti slike/screenshote\n"
                "🔒 Kanal je **privatan** — samo ti i staff\n"
                "✅ Ticket se zatvara kad je problem riješen"
            ),
            inline=False,
        )
        potvrda.set_footer(text="🎫 GIAN  •  Hvala na strpljenju! 🙏")
        await i.response.send_message(embed=potvrda, ephemeral=True)


@bot.tree.command(name="tiket", description="🎫 Otvori tiket za podršku (direktno, bez panela)")
async def tiket_cmd(i: discord.Interaction):
    await i.response.send_modal(SupportTicketModal())

# ═══════════════════════════════════════════
#    SETUP ROLES — GIAN
# ═══════════════════════════════════════════
PERM_ADMIN = discord.Permissions(administrator=True)
PERM_MOD = discord.Permissions(
    ban_members=True, kick_members=True,
    manage_messages=True, moderate_members=True,
    view_channel=True, send_messages=True,
    read_message_history=True, manage_threads=True
)
PERM_MEMBER = discord.Permissions(
    view_channel=True, send_messages=True,
    read_message_history=True, connect=True, speak=True,
    attach_files=True, embed_links=True, add_reactions=True
)
PERM_BOT = discord.Permissions(
    view_channel=True, send_messages=True,
    read_message_history=True, manage_messages=True,
    embed_links=True, attach_files=True, add_reactions=True,
    connect=True, speak=True
)
PERM_BASIC = discord.Permissions(
    view_channel=True, send_messages=True,
    read_message_history=True, add_reactions=True
)
PERM_VOICE = discord.Permissions(
    view_channel=True, connect=True, speak=True,
    use_voice_activation=True, stream=True
)

GIAN_ROLES = [
    # ═══ JEDINA ULOGA SA POWER-OM (ban/kick/admin) ═══
    {"name": "〢 /GIAN",                     "color": discord.Color.from_str("#FFD700"), "permissions": PERM_ADMIN,  "hoist": True,  "desc": "Glavni admin — ban/kick/sve"},
    # ═══ DEKORATIVNE TOP ULOGE ═══
    {"name": "〢 Cryptid Gianni ( Vlasnik )", "color": discord.Color.from_str("#FF3B3B"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Vlasnik (dekorativna)"},
    {"name": "〢 High Masculinity",            "color": discord.Color.from_str("#1F2A44"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "High Masculinity"},
    {"name": "〢 Cristal De Gianni",           "color": discord.Color.from_str("#A569FF"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Cristal De Gianni"},
    {"name": "〢 Toxic Command ™",             "color": discord.Color.from_str("#00E676"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Toxic Command"},
    # ═══ STAFF (dekorativno) ═══
    {"name": "〢 Owners",                      "color": discord.Color.from_str("#FFC400"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Vlasnici"},
    {"name": "〢 Founders",                    "color": discord.Color.from_str("#FF8A00"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Osnivači"},
    {"name": "〢 Creators",                    "color": discord.Color.from_str("#5DADE2"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Kreatori"},
    {"name": "〢 Administrator",               "color": discord.Color.from_str("#EC407A"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Administrator (dekorativna)"},
    {"name": "〢 Hello Kitty Moderator",       "color": discord.Color.from_str("#FF85C8"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Hello Kitty Moderator"},
    {"name": "〢 Moderator",                   "color": discord.Color.from_str("#42A5F5"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Moderator (dekorativna)"},
    {"name": "〢 StaffTeam",                   "color": discord.Color.from_str("#26C6A4"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Staff Team"},
    # ═══ SPECIJALNE ULOGE ═══
    {"name": "〢 Mjauch",                      "color": discord.Color.from_str("#FF9ECF"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Mjauch ✨"},
    {"name": "〢 Samo Njoj",                   "color": discord.Color.from_str("#FF4FA3"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Samo Njoj"},
    {"name": "〢 Girly Pop",                   "color": discord.Color.from_str("#FFB7D5"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Girly Pop"},
    {"name": "〢 Slay Queen",                  "color": discord.Color.from_str("#E91EFF"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Slay Queen"},
    {"name": "〢 67 Pookie",                   "color": discord.Color.from_str("#C58CFF"), "permissions": PERM_MEMBER, "hoist": False, "desc": "67 Pookie"},
    {"name": "〢 Sexy",                        "color": discord.Color.from_str("#D81B60"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Sexy"},
    {"name": "〢 Hello Kitty",                 "color": discord.Color.from_str("#FFC9DD"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Hello Kitty"},
    # ═══ ČLANSTVO & PERMISIJE ═══
    {"name": "〢 Members for /Gianni !",       "color": discord.Color.from_str("#8E44AD"), "permissions": PERM_MEMBER, "hoist": True,  "desc": "Verificirani članovi"},
    {"name": "〢 Chatter",                     "color": discord.Color.from_str("#3DDC97"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Aktivni chatter"},
    {"name": "〢 Main Permission",             "color": discord.Color.from_str("#B0BEC5"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Glavna permisija"},
    {"name": "〢 Voice Permission",            "color": discord.Color.from_str("#78909C"), "permissions": PERM_VOICE,  "hoist": False, "desc": "Voice permisija"},
    # ═══ POL & KATEGORIJE ═══
    {"name": "〢 Musko",                       "color": discord.Color.from_str("#4FC3F7"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Muški članovi"},
    {"name": "〢 Zensko",                      "color": discord.Color.from_str("#F48FB1"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Ženski članovi"},
    {"name": "〢 Radio",                       "color": discord.Color.from_str("#FF5252"), "permissions": PERM_VOICE,  "hoist": False, "desc": "Radio uloga"},
    {"name": "〢 Bots",                        "color": discord.Color.from_str("#90A4AE"), "permissions": PERM_BOT,    "hoist": False, "desc": "Bot uloga"},
    {"name": "〢 Streaks",                     "color": discord.Color.from_str("#AB47BC"), "permissions": PERM_MEMBER, "hoist": False, "desc": "Streak uloga"},
    # ═══ DRŽAVE ═══
    {"name": "〢 Bosnia and Herzegovina",      "color": discord.Color.from_str("#FFCE00"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Bosna i Hercegovina"},
    {"name": "〢 Croatia",                     "color": discord.Color.from_str("#E53935"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Hrvatska"},
    {"name": "〢 Serbia",                      "color": discord.Color.from_str("#1E88E5"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Srbija"},
    {"name": "〢 Macedonia",                   "color": discord.Color.from_str("#FB8C00"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Makedonija"},
    {"name": "〢 Europe",                      "color": discord.Color.from_str("#26A69A"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Europa"},
    # ═══ GODINE ═══
    {"name": "〢 20+",                         "color": discord.Color.from_str("#00897B"), "permissions": PERM_BASIC,  "hoist": False, "desc": "20+ godina"},
    {"name": "〢 18+",                         "color": discord.Color.from_str("#43A047"), "permissions": PERM_BASIC,  "hoist": False, "desc": "18+ godina"},
    {"name": "〢 15+",                         "color": discord.Color.from_str("#FB8C00"), "permissions": PERM_BASIC,  "hoist": False, "desc": "15+ godina"},
    {"name": "〢 14+",                         "color": discord.Color.from_str("#E65100"), "permissions": PERM_BASIC,  "hoist": False, "desc": "14+ godina"},
    # ═══ BOJE (Color Roles) ═══
    {"name": "〢 Bela",                      "color": discord.Color.from_str("#F5F5F5"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Bijela boja"},
    {"name": "〢 Zelena",                    "color": discord.Color.from_str("#4CAF50"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Zelena boja"},
    {"name": "〢 Aqea",                      "color": discord.Color.from_str("#00BCD4"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Aqua boja"},
    {"name": "〢 Žuta",                      "color": discord.Color.from_str("#FFEB3B"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Žuta boja"},
    {"name": "〢 Plava",                     "color": discord.Color.from_str("#2196F3"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Plava boja"},
    {"name": "〢 Roza",                      "color": discord.Color.from_str("#FF4081"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Roza boja"},
    {"name": "〢 Crvena",                    "color": discord.Color.from_str("#F44336"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Crvena boja"},
    {"name": "〢 Crna",                      "color": discord.Color.from_str("#1A1B1E"), "permissions": PERM_BASIC,  "hoist": False, "desc": "Crna boja"},
]

@bot.command(name="sort-roles")
async def sort_roles(ctx: commands.Context):
    if not ctx.author.guild_permissions.administrator and ctx.author.id not in OWNER_IDS:
        return await ctx.send(embed=em("❌ Nemaš pristup", "Samo admin može koristiti `.sort-roles`.", color=COLORS["error"]))
    guild = ctx.guild
    desired_order = [r["name"] for r in GIAN_ROLES]
    role_map = {r.name: r for r in guild.roles}
    found, missing = [], []
    for name in desired_order:
        if name in role_map:
            found.append((name, role_map[name]))
        else:
            missing.append(name)
    if not found:
        return await ctx.send(embed=em("❌", "Nema GIAN uloga! Prvo pokreni `.setup-roles`.", color=COLORS["error"]))
    try:
        positions = {}
        base = 1
        for idx, (name, role) in enumerate(reversed(found)):
            positions[role] = base + idx
        await guild.edit_role_positions(positions=positions)
        ordered_txt = "\n".join(f"`{idx+1}.` {name}" for idx, (name, _) in enumerate(found))
        e = discord.Embed(title="✅ Uloge poređane!", color=COLORS["success"], timestamp=datetime.now(timezone.utc))
        e.add_field(name="📋 Novi redoslijed (gore → dolje)", value=ordered_txt, inline=False)
        if missing:
            e.add_field(name="⚠️ Nisu pronađene na serveru", value="\n".join(missing), inline=False)
        e.set_footer(text=f"{BOT_NAME} • GIAN Role Sort")
        await ctx.send(embed=e)
    except discord.Forbidden:
        await ctx.send(embed=em("❌", "Bot nema permisiju da mjenja redoslijed uloga!\nDaj botu **Administrator** permisiju.", color=COLORS["error"]))
    except Exception as ex:
        await ctx.send(embed=em("❌", f"Greška: `{ex}`", color=COLORS["error"]))

@bot.tree.command(name="setup-roles", description="🏷️ Kreiraj sve GIAN uloge odjednom [ADMIN]")
@app_commands.default_permissions(administrator=True)
async def setup_roles(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    guild = i.guild
    existing = [r.name for r in guild.roles]
    created, skipped = [], []

    for role_data in GIAN_ROLES:
        if role_data["name"] in existing:
            skipped.append(role_data["name"])
            continue
        try:
            await guild.create_role(
                name=role_data["name"],
                color=role_data["color"],
                permissions=role_data["permissions"],
                hoist=role_data["hoist"],
                reason=f"GIAN setup — kreirao {i.user}"
            )
            created.append(role_data["name"])
        except Exception as ex:
            skipped.append(f"{role_data['name']} ❌ ({ex})")

    e = discord.Embed(
        title="🏷️ GIAN Uloge — Setup Završen!",
        color=COLORS["gold"],
        timestamp=datetime.now(timezone.utc)
    )
    if created:
        e.add_field(
            name=f"✅ Kreirano ({len(created)})",
            value="\n".join(created),
            inline=False
        )
    if skipped:
        e.add_field(
            name=f"⏭️ Preskočeno ({len(skipped)}) — već postoje",
            value="\n".join(skipped),
            inline=False
        )
    e.add_field(
        name="📋 Slijedeći korak",
        value=(
            "**Server Settings → Roles** — Povuci uloge u željeni redosljed!\n"
            "Dodijeli `〢 Cryptid Gianni ( Vlasnik )` sebi, `〢 Bots` botu."
        ),
        inline=False
    )
    e.set_footer(text=f"{BOT_NAME} • GIAN Server Setup")
    await i.followup.send(embed=e, ephemeral=True)

# ═══════════════════════════════════════════
#    SERVER SETUP KOMANDE
# ═══════════════════════════════════════════
@bot.tree.command(name="setup", description="⚙️ Postavi sve kanale i uloge servera odjednom [ADMIN]")
@app_commands.default_permissions(administrator=True)
@discord.app_commands.describe(
    welcome="Kanal za dobrodošlicu novih članova",
    leave="Kanal za odlaske (ako se ne postavi, koristi welcome kanal)",
    log="Kanal za logove (edit, delete, join, ban...)",
    starboard="Starboard kanal (popularne poruke sa ⭐)",
    birthday="Kanal za čestitanje rođendana",
    autorole="Uloga koja se automatski daje svim novim članovima",
    welcome_poruka="Custom welcome poruka ({user} = mention, {server} = ime servera)",
    starboard_zvjezdice="Broj ⭐ potrebnih za starboard (default: 3)"
)
@discord.app_commands.default_permissions(manage_guild=True)
async def setup_all(
    i: discord.Interaction,
    welcome:             discord.TextChannel = None,
    leave:               discord.TextChannel = None,
    log:                 discord.TextChannel = None,
    starboard:           discord.TextChannel = None,
    birthday:            discord.TextChannel = None,
    autorole:            discord.Role        = None,
    welcome_poruka:      str = "",
    starboard_zvjezdice: int = 3,
):
    cfg = get_guild_config(i.guild.id)
    lines = []

    if welcome:
        cfg["welcome_channel"] = welcome.id
        lines.append(f"👋 **Welcome:** {welcome.mention}")
    if welcome_poruka:
        cfg["welcome_message"] = welcome_poruka
        lines.append(f"📝 **Welcome poruka:** *{welcome_poruka[:80]}*")
    if leave:
        cfg["leave_channel"] = leave.id
        lines.append(f"👋 **Leave:** {leave.mention}")
    if log:
        cfg["log_channel"] = log.id
        lines.append(f"📋 **Log:** {log.mention}")
    if starboard:
        cfg["starboard_channel"]   = starboard.id
        cfg["starboard_threshold"] = max(1, starboard_zvjezdice)
        lines.append(f"⭐ **Starboard:** {starboard.mention} (min {starboard_zvjezdice}⭐)")
    if birthday:
        cfg["birthday_channel"] = birthday.id
        lines.append(f"🎂 **Rođendani:** {birthday.mention}")
    if autorole:
        if autorole >= i.guild.me.top_role:
            lines.append(f"❌ **Auto-uloga:** `{autorole.name}` je viša od moje — preskočeno!")
        else:
            cfg["auto_role"] = autorole.id
            lines.append(f"🏷️ **Auto-uloga:** {autorole.mention}")

    if not lines:
        return await i.response.send_message(
            embed=em("⚠️ Ništa nije postavljeno",
                     "Proslijedi barem jedan parametar!\nPrimjer:\n`/setup welcome:#dobrodošlica log:#logs autorole:@Member`",
                     color=COLORS["warning"]),
            ephemeral=True
        )

    save_data()
    e = discord.Embed(
        title="✅ Server konfigurisan!",
        description="\n".join(lines),
        color=COLORS["success"],
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f"Pregled svih postavki: /server-config | {BOT_NAME}")
    await i.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="setup-welcome", description="⚙️ Postavi welcome kanal [ADMIN]")
@discord.app_commands.describe(kanal="Kanal gdje bot šalje welcome embed novim članovima")
@discord.app_commands.default_permissions(manage_guild=True)
async def setup_welcome(i: discord.Interaction, kanal: discord.TextChannel):
    cfg = get_guild_config(i.guild.id)
    cfg["welcome_channel"] = kanal.id
    save_data()
    e_out = discord.Embed(
        title="✅ Welcome kanal postavljen!",
        description=(
            f"**Kanal:** {kanal.mention}\n\n"
            f"Svaki novi član će dobiti embed sa:\n"
            f"<a:vatrice1:1500466044429664256> chat · <a:vatrice2:1500466048418185246> info · "
            f"<a:vatrice3:1500466039782113352> news · <a:vatrice4:1500466061970247741> gws\n"
            f"🪶 broj članova\n"
            f"Dugmad: <a:game1:1500459114931949568> game · <a:music2:1500459145382592602> music"
        ),
        color=COLORS["success"],
        timestamp=datetime.now(timezone.utc)
    )
    e_out.set_footer(text=f"{BOT_NAME} • Welcome Setup")
    await i.response.send_message(embed=e_out, ephemeral=True)

@bot.tree.command(name="aktivnost-setup", description="⚙️ Postavi kanal za XP level-up i aktivnost [ADMIN]")
@discord.app_commands.describe(
    levelup_kanal="Kanal gdje bot objavljuje level-up notifikacije",
    xp_kanal="Kanal za XP/rank prikaz (/rank, /leaderboard komande)"
)
@discord.app_commands.default_permissions(manage_guild=True)
async def aktivnost_setup(
    i: discord.Interaction,
    levelup_kanal: discord.TextChannel = None,
    xp_kanal: discord.TextChannel = None
):
    cfg = get_guild_config(i.guild.id)
    linije = []
    if levelup_kanal:
        cfg["levelup_channel"]   = levelup_kanal.id
        cfg["aktivnost_channel"] = levelup_kanal.id
        linije.append(f"📊 **Level-up / Aktivnost:** {levelup_kanal.mention}")
    if xp_kanal:
        cfg["xp_kanal"] = xp_kanal.id
        linije.append(f"📈 **XP / Rank prikaz:** {xp_kanal.mention}")
    if not linije:
        return await i.response.send_message(
            embed=em("⚠️ Ništa nije postavljeno", "Proslijedi barem jedan kanal:\n`/aktivnost-setup levelup_kanal:#aktivnost xp_kanal:#rank`", color=COLORS["warning"]),
            ephemeral=True
        )
    save_data()
    e_out = discord.Embed(
        title="✅ Aktivnost Setup — Sačuvano!",
        description="\n".join(linije),
        color=0xFFD700,
        timestamp=datetime.now(timezone.utc)
    )
    e_out.set_footer(text="GIAN (Custom) • Aktivnost Setup")
    await i.response.send_message(embed=e_out, ephemeral=True)

@bot.tree.command(name="setup-leave", description="⚙️ Postavi leave kanal [ADMIN]")
@discord.app_commands.describe(kanal="Kanal gdje bot šalje poruku kad član napusti server")
@discord.app_commands.default_permissions(manage_guild=True)
async def setup_leave(i: discord.Interaction, kanal: discord.TextChannel):
    get_guild_config(i.guild.id)["leave_channel"] = kanal.id
    save_data()
    e_out = discord.Embed(
        title="✅ Leave kanal postavljen!",
        description=(
            f"**Kanal:** {kanal.mention}\n\n"
            f"Kad član napusti server, bot će poslati embed sa:\n"
            f"<a:vatrice1:1500466044429664256> **bye** ime člana\n"
            f"🪶 broj članova\n"
            f"Thumbnail: avatar člana koji je otišao"
        ),
        color=COLORS["success"],
        timestamp=datetime.now(timezone.utc)
    )
    e_out.set_footer(text=f"{BOT_NAME} • Leave Setup")
    await i.response.send_message(embed=e_out, ephemeral=True)

@bot.tree.command(name="setup-autorole", description="⚙️ Postavi automatsku ulogu pri ulasku [ADMIN]")
@discord.app_commands.describe(uloga="Uloga koja se daje svim novim članovima")
@discord.app_commands.default_permissions(manage_roles=True)
async def setup_autorole(i: discord.Interaction, uloga: discord.Role):
    if uloga >= i.guild.me.top_role:
        return await i.response.send_message(embed=em("❌", "Ta uloga je viša od moje! Ne mogu je davati.", color=COLORS["error"]), ephemeral=True)
    get_guild_config(i.guild.id)["auto_role"] = uloga.id
    save_data()
    await i.response.send_message(embed=em("✅ Auto-Uloga postavljena!", f"Svaki novi član dobije: {uloga.mention}", color=COLORS["success"]), ephemeral=True)

@bot.tree.command(name="setup-log", description="⚙️ Postavi log kanal [ADMIN]")
@discord.app_commands.describe(kanal="Log kanal gdje bot šalje editovane/obrisane poruke, join/leave, banove")
@discord.app_commands.default_permissions(manage_guild=True)
async def setup_log(i: discord.Interaction, kanal: discord.TextChannel):
    get_guild_config(i.guild.id)["log_channel"] = kanal.id
    save_data()
    await i.response.send_message(embed=em("✅ Log kanal postavljen!", f"Kanal: {kanal.mention}\nBiće logovano: join/leave, edit, delete, ban.", color=COLORS["success"]), ephemeral=True)

@bot.tree.command(name="setup-starboard", description="⚙️ Postavi starboard kanal [ADMIN]")
@discord.app_commands.describe(kanal="Starboard kanal", zvjezdice="Broj ⭐ za pin (default: 3)")
@discord.app_commands.default_permissions(manage_guild=True)
async def setup_starboard(i: discord.Interaction, kanal: discord.TextChannel, zvjezdice: int = 3):
    cfg = get_guild_config(i.guild.id)
    cfg["starboard_channel"]   = kanal.id
    cfg["starboard_threshold"] = max(1, zvjezdice)
    save_data()
    await i.response.send_message(embed=em("✅ Starboard postavljen!", f"Kanal: {kanal.mention}\nPotrebno ⭐: `{zvjezdice}`", color=COLORS["success"]), ephemeral=True)

@bot.tree.command(name="setup-levelrole", description="⚙️ Postavi ulogu za određeni level [ADMIN]")
@discord.app_commands.describe(level="Level za koji se daje uloga", uloga="Uloga koja se daje")
@discord.app_commands.default_permissions(manage_roles=True)
async def setup_levelrole(i: discord.Interaction, level: int, uloga: discord.Role):
    if level < 1 or level > 1000:
        return await i.response.send_message(embed=em("❌", "Level mora biti između 1 i 1000.", color=COLORS["error"]), ephemeral=True)
    cfg = get_guild_config(i.guild.id)
    cfg.setdefault("level_roles", {})[str(level)] = uloga.id
    save_data()
    await i.response.send_message(embed=em("✅ Level uloga postavljena!", f"Level **{level}** → {uloga.mention}", color=COLORS["success"]), ephemeral=True)

@bot.tree.command(name="server-config", description="⚙️ Pregled konfiguracije servera [ADMIN]")
@discord.app_commands.default_permissions(manage_guild=True)
async def server_config_cmd(i: discord.Interaction):
    cfg = get_guild_config(i.guild.id)
    def ch(cid): return f"<#{cid}>" if cid else "*nije postavljeno*"
    def ro(rid): return f"<@&{rid}>" if rid else "*nije postavljeno*"
    lr = cfg.get("level_roles", {})
    lr_txt = "\n".join(f"Level **{k}** → <@&{v}>" for k, v in sorted(lr.items(), key=lambda x: int(x[0]))) or "*nema*"
    e = discord.Embed(title=f"⚙️ Konfiguracija — {i.guild.name}", color=COLORS["purple"], timestamp=datetime.now(timezone.utc))
    e.add_field(name="👋 Welcome kanal",    value=ch(cfg.get("welcome_channel")),   inline=True)
    e.add_field(name="👋 Leave kanal",      value=ch(cfg.get("leave_channel")),     inline=True)
    e.add_field(name="🏷️ Auto-Uloga",      value=ro(cfg.get("auto_role")),         inline=True)
    e.add_field(name="📋 Log kanal",        value=ch(cfg.get("log_channel")),       inline=True)
    e.add_field(name="⭐ Starboard",        value=f"{ch(cfg.get('starboard_channel'))} (min {cfg.get('starboard_threshold', 3)}⭐)", inline=True)
    e.add_field(name="🎂 Birthday kanal",   value=ch(cfg.get("birthday_channel")),  inline=True)
    e.add_field(name="🎊 Level uloge",      value=lr_txt, inline=False)
    await i.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="afk", description="😴 Postavi AFK status")
@discord.app_commands.describe(razlog="Razlog zašto si AFK")
async def afk_cmd(i: discord.Interaction, razlog: str = "AFK"):
    uid = str(i.user.id)
    data["afk"][uid] = {"reason": razlog, "since": time.time()}
    save_data()
    await i.response.send_message(embed=em(f"😴 {i.user.display_name} je sada AFK", f"Razlog: *{razlog}*\nBiće skinut AFK kada sljedeći put pišeš.", color=COLORS["warning"]))




# ═══════════════════════════════════════════
#    SELF ROLES
# ═══════════════════════════════════════════
def _selfrole_key(guild_id: int, channel_id: int) -> str:
    return f"{guild_id}:{channel_id}"

def _build_selfrole_view(key: str) -> discord.ui.View:
    panel = data["selfroles"].get(key, {})
    view  = discord.ui.View(timeout=None)
    for r in panel.get("roles", []):
        emoji = r.get("emoji") or None
        btn   = discord.ui.Button(
            label=r["label"],
            emoji=emoji,
            custom_id=f"sr_{key}_{r['role_id']}",
            style=discord.ButtonStyle.secondary,
        )
        async def _cb(interaction: discord.Interaction, role_id=r["role_id"], label=r["label"]):
            try:
                try:
                    await interaction.response.defer(ephemeral=True, thinking=False)
                except (discord.NotFound, discord.InteractionResponded):
                    pass
                role = interaction.guild.get_role(role_id)
                if not role:
                    try: await interaction.followup.send("❌ Uloga ne postoji!", ephemeral=True)
                    except: pass
                    return
                me = interaction.guild.me
                if role >= me.top_role:
                    try: await interaction.followup.send(embed=em("❌", f"Uloga **{label}** je viša od moje! Admin: pomjeri moju ulogu iznad nje.", color=COLORS["error"]), ephemeral=True)
                    except: pass
                    return
                if role in interaction.user.roles:
                    await interaction.user.remove_roles(role, reason="Self-role panel")
                    try: await interaction.followup.send(embed=em("🏷️", f"Uklonjena uloga **{label}**!", color=COLORS["error"]), ephemeral=True)
                    except: pass
                else:
                    await interaction.user.add_roles(role, reason="Self-role panel")
                    try: await interaction.followup.send(embed=em("✅", f"Dobio/la si ulogu **{label}**!", color=COLORS["success"]), ephemeral=True)
                    except: pass
            except discord.Forbidden:
                try: await interaction.followup.send(embed=em("❌", "Nemam dozvolu za upravljanje tom ulogom!", color=COLORS["error"]), ephemeral=True)
                except: pass
            except Exception as ex:
                print(f"[selfrole _cb] {type(ex).__name__}: {ex}")
        btn.callback = _cb
        view.add_item(btn)
    return view

def _selfrole_embed(panel: dict) -> discord.Embed:
    e = discord.Embed(
        title=panel.get("title", "🏷️ Self Roles"),
        description=panel.get("description", "Klikni dugme da dobiješ/skineš ulogu!"),
        color=0x9B59B6,
        timestamp=datetime.now(timezone.utc)
    )
    roles_txt = "\n".join(
        f"{r.get('emoji', '▸')} **{r['label']}**" for r in panel.get("roles", [])
    ) or "*Nema uloga. Admin treba dodati `/selfroles-add`.*"
    e.add_field(name="Dostupne uloge", value=roles_txt, inline=False)
    e.set_footer(text="Klikni dugme ispod ↓")
    return e

# ═══════════════════════════════════════════
#    AUTO SETUP — SVA 3 PANELA ODJEDNOM
# ═══════════════════════════════════════════
PANEL_PRESETS = [
    {
        "title": "🌍 Odaberi svoju državu",
        "description": "Klikni dugme da dobiješ/skineš ulogu!",
        "roles": [
            {"name": "〢 Bosnia and Herzegovina", "label": "Bosnia and Herzegovina", "emoji": "🇧🇦"},
            {"name": "〢 Croatia",                 "label": "Croatia",                 "emoji": "🇭🇷"},
            {"name": "〢 Serbia",                  "label": "Serbia",                  "emoji": "🇷🇸"},
            {"name": "〢 Macedonia",               "label": "Macedonia",               "emoji": "🇲🇰"},
        ],
    },
    {
        "title": "Odaberi svoju malenokst",
        "description": "Klikni dugme da dobiješ/skineš ulogu!",
        "roles": [
            {"name": "〢 Musko",  "label": "Musko",  "emoji": "👦"},
            {"name": "〢 Zensko", "label": "Zensko", "emoji": "👧"},
        ],
    },
    {
        "title": "Klasične Permisije",
        "description": "Klikni dugme da dobiješ/skineš ulogu!",
        "roles": [
            {"name": "〢 Chatter",          "label": "Chatter",          "emoji": "💬"},
            {"name": "〢 Voice Permission", "label": "Voice Permission", "emoji": "🔊"},
            {"name": "〢 Main Permission",  "label": "Main Permission",  "emoji": "✅"},
        ],
    },
]

@bot.tree.command(name="setup-panels", description="🏷️ [ADMIN] Auto-kreiraj sva 3 self-role panela odjednom")
@app_commands.default_permissions(administrator=True)
async def setup_panels_cmd(i: discord.Interaction, kanal: discord.TextChannel = None):
    if not i.user.guild_permissions.administrator:
        return await i.response.send_message("❌ Samo admin.", ephemeral=True)
    ch = kanal or i.channel
    await i.response.send_message(embed=em("⏳", f"Kreiram panele u {ch.mention}...", color=COLORS["info"]), ephemeral=True)
    created, missing = [], []
    for idx, preset in enumerate(PANEL_PRESETS):
        key = _selfrole_key(i.guild.id, ch.id) + f":{idx}"
        # pronađi uloge po imenu (probaj tačan match, pa case-insensitive)
        roles_found = []
        for r in preset["roles"]:
            role = discord.utils.get(i.guild.roles, name=r["name"])
            if not role:
                role = next((rr for rr in i.guild.roles if rr.name.lower().strip() == r["name"].lower().strip()), None)
            if not role:
                role = next((rr for rr in i.guild.roles if r["label"].lower() in rr.name.lower()), None)
            if role:
                roles_found.append({"role_id": role.id, "label": r["label"], "emoji": r["emoji"]})
            else:
                missing.append(r["name"])
        if not roles_found: continue
        data["selfroles"][key] = {
            "guild_id": i.guild.id, "channel_id": ch.id, "message_id": None,
            "title": preset["title"], "description": preset["description"], "roles": roles_found
        }
        view = _build_selfrole_view(key)
        msg = await ch.send(embed=_selfrole_embed(data["selfroles"][key]), view=view)
        data["selfroles"][key]["message_id"] = msg.id
        bot.add_view(view, message_id=msg.id)
        created.append(preset["title"])
    save_data()
    desc = f"✅ Kreirano: **{len(created)}** panela\n" + "\n".join(f"• {t}" for t in created)
    if missing:
        desc += f"\n\n⚠️ Nisu pronađene uloge: {', '.join(set(missing))}\n*(Pokreni `/setup-uloge` ako ih nemaš)*"
    await i.followup.send(embed=em("🎉 Paneli postavljeni!", desc, color=COLORS["success"]), ephemeral=True)


# ═══════════════════════════════════════════
#    HELP
# ═══════════════════════════════════════════
@bot.tree.command(name="help", description="📖 Sve dostupne komande bota")
async def help_cmd(i: discord.Interaction):
    is_admin = False
    is_owner = i.user.id in OWNER_IDS
    try:
        is_admin = i.user.guild_permissions.administrator or any(r.name in ("〢 /GIAN", "〢 /GIANNI") for r in i.user.roles)
    except: pass

    # 🔧 PREFIX DETEKCIJA — ako je pozvano kao .help → koristimo "." prefix u embedu (mobitel-mod)
    px = "/"
    is_mobile = False
    try:
        if isinstance(i, FakeInteraction):
            px = "."
            is_mobile = True
    except Exception: pass

    BAR = "═══════════════════════════════════"

    title = "✦ × G I A N N I  —  K O M A N D E  ✦" if not is_mobile else "📱 × G I A N N I  —  M O B I L E  ✦"
    head_line = f"🔮 Sve komande se koriste sa `{px}`" if not is_mobile else f"📱 **MOBITEL MOD** · Sve komande se koriste sa `{px}` prefixom"

    e = discord.Embed(
        title=title,
        description=(
            f"```ansi\n\u001b[1;36m{BAR}\n"
            f"  ✦ Dobrodošli u GIAN komandni centar! ✦\n"
            f"{BAR}\u001b[0m```\n"
            f"📌 Verzija **{VERSION}** · Ukupno komandi: **100**\n"
            f"{head_line}"
        ),
        color=COLORS["balkan"],
        timestamp=datetime.now(timezone.utc),
    )
    e.set_thumbnail(url=bot.user.display_avatar.url)

    e.add_field(
        name="╔═ ℹ️  INFO & UTILITI",
        value=(
            f"> `{px}ping` `{px}serverinfo` `{px}userinfo` `{px}avatar`\n"
            f"> `{px}invite` `{px}spotify` `{px}qr` `{px}vatrice`\n"
            f"> `{px}topchatters`"
        ),
        inline=False,
    )
    e.add_field(
        name="╠═ 😴  AFK & SOCIJALNO",
        value=(
            f"> `{px}afk` — Postavi AFK status"
        ),
        inline=False,
    )
    e.add_field(
        name="╠═ 💰  EKONOMIJA",
        value=(
            f"> `{px}baki` `{px}posao` `{px}daily` `{px}daj` `{px}kradi`\n"
            f"> `{px}rank` `{px}leaderboard` `{px}shop` `{px}kupi`\n"
            f"> `{px}bank` `{px}lottery` `{px}heist`"
        ),
        inline=False,
    )
    e.add_field(
        name="╠═ 🎮  IGRE & ZABAVA",
        value=(
            f"> `{px}kpm` `{px}slots` `{px}rulet` `{px}vers`\n"
            f"> `{px}vjasala` `{px}kaladont` `{px}kaladont-stop` `{px}toplo-hladno`\n"
            f"> `{px}blackjack` `{px}kviz` `{px}kocka` `{px}geografija` `{px}meme`\n"
            f"> `{px}amogus` `{px}amogus-stop` `{px}aktivnost`\n"
            f"> `{px}meme` — 😂 Balkanski mem\n"
            f"> `{px}poo` `{px}poo-zadaci` `{px}poo-top` `{px}poo-hrani` `{px}poo-info`"
        ),
        inline=False,
    )
    # Mobitel mod = manje zatrpan, izostavi neke opširnije sekcije
    if not is_mobile:
        e.add_field(
            name="╠═ 🎱  BINGO",
            value=(
                f"> `{px}bingo` — Pokreni bingo rundu\n"
                f"> 🔄 Auto-bingo svakih **3 sata** automatski!\n"
                f"> 🎫 Klikni **Uzmi tiket** → unesi 5 brojeva (1-75)\n"
                f"> 💰 Nagrade: `2✓=10k` · `3✓=30k` · `4✓=75k` · `5✓=250k 🏆`\n"
                f"> ⏱️ Rezultati se objavljuju **javno** nakon 2 minute"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ 🐾  OWO — ŽIVOTINJE",
            value=(
                f"> `{px}hunt` `{px}zoo` `{px}battle` `{px}sell`\n"
                f"> `{px}animals` `{px}pray` `{px}curse`"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ ❤️  LJUBAV & AKCIJE",
            value=(
                f"> `{px}zagrljaj` `{px}poljubac` `{px}mazi` `{px}tapsi`\n"
                f"> `{px}high5` `{px}srce` `{px}brak` `{px}pocetkaj` `{px}cudan`\n"
                f"> `{px}pozz` `{px}kompli` `{px}fora` `{px}muv` `{px}crush`"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ 📋  QUESTS, POLL & SOCIAL",
            value=(
                f"> `{px}quests` — Dnevni zadaci za XP i novac\n"
                f"> `{px}poll` — Napravi glasanje\n"
                f"> `{px}confess` — Anonimna ispovjed\n"
                f"> `{px}report` — Prijavi člana\n"
                f"> `{px}tiket` — 🎫 Otvori tiket za podršku\n"
                f"> `{px}tiket-staff` — 📋 Prijavi se za Staff poziciju"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ 🔢  BROJANJE",
            value=(f"> `{px}brojanje-postavi` `{px}brojanje-info` `{px}brojanje-reset`"),
            inline=False,
        )
    else:
        # MOBITEL: kratka zbirna sekcija
        e.add_field(
            name="╠═ 📱  OSTALO (mobitel)",
            value=(
                f"> `{px}bingo` `{px}hunt` `{px}zoo` `{px}battle`\n"
                f"> `{px}quests` `{px}poll` `{px}confess` `{px}tiket`\n"
                f"> `{px}zagrljaj` `{px}poljubac` `{px}srce`\n"
                f"> `{px}meme` `{px}poo` `{px}poo-zadaci`\n"
                f"> `{px}brojanje-postavi` `{px}brojanje-info`"
            ),
            inline=False,
        )

    if (is_admin or is_owner) and not is_mobile:
        e.add_field(
            name="╠═ ⚙️  SERVER SETUP  〔ADMIN〕",
            value=(
                f"> `{px}setup` `{px}setup-levelrole` `{px}server-config`\n"
                f"> `{px}setup-welcome` `{px}setup-leave` `{px}setup-autorole`\n"
                f"> `{px}setup-log` `{px}setup-starboard` `{px}setchannel`\n"
                f"> `{px}setup-panels` — Self-role paneli"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ 🛡️  MODERACIJA  〔ADMIN〕",
            value=(
                f"> `{px}ban` `{px}kick` `{px}timeout` `{px}warn`\n"
                f"> `{px}warnings` `{px}clearwarnings` `{px}clear`"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ 🎁  GIVEAWAY  〔ADMIN〕",
            value=(f"> `{px}giveaway start` `{px}giveaway end` `{px}reset-gw`"),
            inline=False,
        )
        e.add_field(
            name="╠═ 🎫  TICKET & BOT  〔ADMIN〕",
            value=(
                f"> `{px}tiket` — Otvori tiket direktno\n"
                f"> `{px}ticket-setup` `{px}say` `{px}setname`\n"
                f"> `{px}setavatar` `{px}sort-roles` `{px}setup-roles`"
            ),
            inline=False,
        )
        e.add_field(
            name="╠═ 🤖  AUTO-MOD  〔AUTOMATSKI〕",
            value=(
                "> 🚫 Anti-Spam: 7 poruka/5s → 30s timeout\n"
                "> 🛡️ Anti-Nuke: masovna zaštita kanala/uloga\n"
                "> 🔒 Anti-Raid: zaštita od botova pri joinu\n"
                "> ✅ Sve aktivno bez ikakve konfiguracije!"
            ),
            inline=False,
        )

    if is_owner and not is_mobile:
        e.add_field(
            name="╠═ 👑  OWNER KOMANDE  〔VLASNIK〕",
            value=(
                f"> `{px}dodaj-novac` `{px}oduzmi-novac`\n"
                f"> `{px}event` — Objavi event (naslov + opis)"
            ),
            inline=False,
        )

    e.add_field(
        name="╚═ 💡  SAVJET",
        value=(
            f"> Bingo tiket košta **500 coina** 🪙\n"
            f"> Koristi `{px}posao` i `{px}daily` za zaradu!\n"
            f"> 💩 `{px}poo` — hrani serversku kreaturU zajedno!\n"
            f"> Za pomoć: kontaktiraj staff servera 💬"
        ),
        inline=False,
    )

    role_tag = '👑 Owner pristup' if is_owner else ('🛡️ Admin pristup' if is_admin else '👤 Member pristup')
    mob_tag = ' • 📱 mobile' if is_mobile else ''
    e.set_footer(text=f"✦ {BOT_NAME} {VERSION} · {role_tag}{mob_tag} ✦")
    await i.response.send_message(embed=e, ephemeral=True)


# ═══════════════════════════════════════════
#    🎪 EVENT — samo vlasnik
# ═══════════════════════════════════════════
@bot.tree.command(name="event", description="🎪 Objavi event na serveru (samo vlasnik)")
@discord.app_commands.describe(
    naslov="Naslov eventa",
    opis="Opis eventa — šta, kada, gdje, nagrade itd."
)
async def event_cmd(i: discord.Interaction, naslov: str, opis: str):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("👑 Nemaš pristup!", "Ova komanda je rezervisana samo za **Vlasnika** bota.", color=COLORS["error"]),
            ephemeral=True,
        )
    BAR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    e = discord.Embed(
        title=f"🎪  {naslov}",
        description=f"{BAR}\n\n{opis}\n\n{BAR}",
        color=0xFF6B35,
        timestamp=datetime.now(timezone.utc),
    )
    e.set_author(
        name=f"× GIAN — NOVI EVENT!",
        icon_url=bot.user.display_avatar.url,
    )
    e.set_footer(text=f"📢 Event objavio: {i.user.display_name}  ·  {BOT_NAME}")
    e.set_thumbnail(url=bot.user.display_avatar.url)
    await i.response.send_message(embed=e)
    await i.followup.send(embed=em("✅ Event objavljen!", f"**{naslov}** je uspješno objavljen! 🎪", color=COLORS["success"]), ephemeral=True)

# ═══════════════════════════════════════════
#    ERROR HANDLING
# ═══════════════════════════════════════════
@bot.tree.error
async def on_app_error(i: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        mins, secs = divmod(int(error.retry_after), 60)
        t = f"{mins}min {secs}s" if mins else f"{secs}s"
        e = em("⏳ Cooldown!", f"Sačekaj još **{t}**.", color=COLORS["warning"])
    elif isinstance(error, app_commands.MissingPermissions):
        e = em("🛡️ Nemaš dozvole!", "Nisi ovlašćen za ovu komandu.", color=COLORS["error"])
    elif isinstance(error, app_commands.BotMissingPermissions):
        e = em("🤖 Bot nema dozvole!", "Daj mi potrebne dozvole.", color=COLORS["error"])
    else:
        e = em("❌ Greška!", f"`{str(error)[:200]}`", color=COLORS["error"])
        print(f"[tree.error] {type(error).__name__}: {error}")
    try:
        if i.response.is_done(): await i.followup.send(embed=e, ephemeral=True)
        else: await i.response.send_message(embed=e, ephemeral=True)
    except: pass

# ═══════════════════════════════════════════
#    /igre — UKLONJENO
# ═══════════════════════════════════════════
_REMOVED_IGRE = """
GAMES_CATALOG = [
    {
        "emoji": "🧠", "name": "Balkan Trivia", "cmd": "/kviz",
        "img": "attached_assets/games/kviz.png", "color": COLORS["purple"],
        "desc": "Odgovaraj na Balkan pitanja i osvajaj pare!",
        "kako": "Uložiš okladu, biraš jedan od 4 odgovora u 20s.",
        "nagrada": "Tačno → +oklada × combo + 25 XP. Combo raste sa svakim tačnim!"
    },
    {
        "emoji": "🌍", "name": "Geografija", "cmd": "/geografija",
        "img": "attached_assets/games/geografija.png", "color": COLORS["info"],
        "desc": "50+ pitanja o glavnim gradovima, rijekama i planinama.",
        "kako": "Uložiš okladu i biraš tačan odgovor.",
        "nagrada": "Tačno → +oklada × combo + 25 XP po nivou."
    },
    {
        "emoji": "🎲", "name": "Kocka", "cmd": "/kocka",
        "img": "attached_assets/games/kocka.png", "color": COLORS["gold"],
        "desc": "Baci kocku protiv prijatelja — veći broj pobjeđuje!",
        "kako": "Pozoveš protivnika i uložite jednaku okladu.",
        "nagrada": "Pobjednik uzima sve. Gubitnik plaća."
    },
    {
        "emoji": "🎰", "name": "Slot Mašina", "cmd": "/slots",
        "img": "attached_assets/games/slots.png", "color": COLORS["gold"],
        "desc": "Klasična slot mašina — uloži od 20 do 1.000.000.000 💶 i okreni tri kotača!",
        "kako": "Postaviš ulog (npr. `.slots 50000`), vrtiš, čekaš kombinaciju.",
        "nagrada": "3x 7️⃣ = ×50 ulog! 3x 💎 = ×15! Par vraća dio uloga."
    },
    {
        "emoji": "🃏", "name": "Blackjack", "cmd": "/blackjack",
        "img": "attached_assets/games/blackjack.png", "color": COLORS["error"],
        "desc": "Pravi Blackjack protiv dilera. Cilj: 21 ili blizu!",
        "kako": "Hit za novu kartu, Stand da staneš. Diler igra po pravilu.",
        "nagrada": "Pobjeda = 2x uloga, Blackjack = 2.5x!"
    },
    {
        "emoji": "🚀", "name": "Among Us", "cmd": "/amogus",
        "img": "attached_assets/games/amogus.png", "color": COLORS["error"],
        "desc": "Kompletan Among Us u Discordu! Crewmates vs Impostor.",
        "kako": "Pokreni igru, čekaj igrače, zadaci/sastanci/glasanje.",
        "nagrada": "Pobjednička ekipa dobija nagradu i XP."
    },
    {
        "emoji": "🔤", "name": "Kaladont", "cmd": "/kaladont",
        "img": "attached_assets/games/kaladont.png", "color": COLORS["info"],
        "desc": "Klasični Balkan word game — ulanči riječi!",
        "kako": "Svaka nova riječ mora počinjati zadnjim slovima prošle.",
        "nagrada": "Što duži lanac, to više XP-a za sve!"
    },
    {
        "emoji": "🎮", "name": "Vješala", "cmd": "/vjasala",
        "img": "attached_assets/games/vjasala.png", "color": COLORS["warning"],
        "desc": "Pogodi skrivenu riječ slovo po slovo!",
        "kako": "6 grešaka i visi! Predloži slovo dugmetom.",
        "nagrada": "Pogodak = pare + XP, neuspjeh = ništa."
    },
    {
        "emoji": "🌡️", "name": "Toplo-Hladno", "cmd": "/toplo-hladno",
        "img": "attached_assets/games/toplohladno.png", "color": COLORS["info"],
        "desc": "Pogodi skriveni broj — bot ti govori toplije/hladnije!",
        "kako": "Bot bira tajni broj, ti pogađaš.",
        "nagrada": "Manje pokušaja = veća nagrada!"
    },
    {
        "emoji": "✊", "name": "Kamen-Papir-Makaze", "cmd": "/kpm",
        "img": "attached_assets/games/kpm.png", "color": COLORS["purple"],
        "desc": "Klasika protiv bota ili igrača!",
        "kako": "Klikneš dugme i čekaš ishod.",
        "nagrada": "Pobjeda = +pare, neriješeno = nazad ulog."
    },
    {
        "emoji": "🔫", "name": "Ruski Rulet", "cmd": "/rulet",
        "img": "attached_assets/games/rulet.png", "color": COLORS["error"],
        "desc": "Za hrabre — povuci obarač i pomoli se!",
        "kako": "1/6 šanse za 'metak'. Preživi i uzmi pare.",
        "nagrada": "Preživiš = veliki dobitak, padneš = timeout!"
    },
    {
        "emoji": "🏹", "name": "Lov", "cmd": "/hunt",
        "img": "attached_assets/games/hunt.png", "color": COLORS["success"],
        "desc": "OWO-style lov! Uhvati životinje različitog rariteta.",
        "kako": "Komanda /hunt → bot izvuče nasumičnu životinju za tebe.",
        "nagrada": "Životinje idu u tvoj /zoo. Možeš ih /sell ili /battle."
    },
    {
        "emoji": "⚔️", "name": "Battle", "cmd": "/battle",
        "img": "attached_assets/games/battle.png", "color": COLORS["error"],
        "desc": "Bori se sa drugim igračem životinjama iz zoo-a!",
        "kako": "Izabereš protivnika, jača životinja pobjeđuje.",
        "nagrada": "Pobjeda = pare + XP boost."
    },
    {
        "emoji": "🔢", "name": "Brojanje", "cmd": "/brojanje-postavi",
        "img": "attached_assets/games/brojanje.png", "color": COLORS["info"],
        "desc": "Klasični sistem brojanja u kanalu — ne smiješ pogriješiti!",
        "kako": "Admin postavi kanal, svi pišu brojeve redom 1, 2, 3…",
        "nagrada": "Svaki 50. broj = +100 💶 +50 XP. Greška = reset!"
    },
]

class GamesView(discord.ui.View):
    def __init__(self, uid: int):
        super().__init__(timeout=180)
        self.uid = uid
        self.idx = 0
        self._update_buttons()

    def _update_buttons(self):
        self.prev_btn.disabled = self.idx == 0
        self.next_btn.disabled = self.idx == len(GAMES_CATALOG) - 1

    def _build_embed_and_file(self):
        g = GAMES_CATALOG[self.idx]
        e = discord.Embed(
            title=f"{g['emoji']}  {g['name']}",
            description=f"**`{g['cmd']}`**\n\n{g['desc']}",
            color=g["color"], timestamp=datetime.now(timezone.utc)
        )
        e.add_field(name="📖 Kako se igra", value=g["kako"], inline=False)
        e.add_field(name="💰 Nagrada", value=g["nagrada"], inline=False)
        e.set_footer(text=f"Igra {self.idx+1}/{len(GAMES_CATALOG)} • {BOT_NAME} {VERSION}")
        try:
            file = discord.File(g["img"], filename=f"game_{self.idx}.png")
            e.set_image(url=f"attachment://game_{self.idx}.png")
            return e, file
        except Exception:
            return e, None

    @discord.ui.button(label="◀ Nazad", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, i: discord.Interaction, _):
        if i.user.id != self.uid:
            return await i.response.send_message("Ovo nije tvoj meni!", ephemeral=True)
        self.idx = max(0, self.idx - 1)
        self._update_buttons()
        e, file = self._build_embed_and_file()
        kwargs = {"embed": e, "view": self}
        if file: kwargs["attachments"] = [file]
        await i.response.edit_message(**kwargs)

    @discord.ui.button(label="Naprijed ▶", style=discord.ButtonStyle.primary)
    async def next_btn(self, i: discord.Interaction, _):
        if i.user.id != self.uid:
            return await i.response.send_message("Ovo nije tvoj meni!", ephemeral=True)
        self.idx = min(len(GAMES_CATALOG)-1, self.idx + 1)
        self._update_buttons()
        e, file = self._build_embed_and_file()
        kwargs = {"embed": e, "view": self}
        if file: kwargs["attachments"] = [file]
        await i.response.edit_message(**kwargs)

    @discord.ui.button(label="📋 Sve igre", style=discord.ButtonStyle.success)
    async def list_btn(self, i: discord.Interaction, _):
        if i.user.id != self.uid:
            return await i.response.send_message("Ovo nije tvoj meni!", ephemeral=True)
        lines = [f"{g['emoji']} `{g['cmd']:<22}` — {g['name']}" for g in GAMES_CATALOG]
        e = discord.Embed(
            title="🎮 Sve GIAN igre",
            description="\n".join(lines) + f"\n\n*Ukupno: **{len(GAMES_CATALOG)} igara***",
            color=COLORS["gold"]
        )
        e.set_footer(text=f"{BOT_NAME} {VERSION}")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger)
    async def close_btn(self, i: discord.Interaction, _):
        if i.user.id != self.uid:
            return await i.response.send_message("Ovo nije tvoj meni!", ephemeral=True)
        self.clear_items()
        await i.response.edit_message(content="Zatvoreno.", embed=None, view=self, attachments=[])

"""

# ═══════════════════════════════════════════
#    DODATNE KORISNE KOMANDE (v2.1)
# ═══════════════════════════════════════════
data.setdefault("bank", {})
data.setdefault("lottery", {"pot": 0, "tickets": {}, "last_draw": 0})
data.setdefault("reminders", [])
data.setdefault("heist_cooldown", {})
data.setdefault("confess_count", 0)
data.setdefault("cmd_uses", {})



# ─── 🏆 TOP CHATTERS ───
@bot.tree.command(name="topchatters", description="🏆 Top 10 najaktivnijih chatera")
async def topchatters_cmd(i: discord.Interaction):
    gid = str(i.guild.id)
    rows = [(int(k.split(":")[1]), v) for k, v in data.get("msg_count", {}).items() if k.startswith(f"{gid}:")]
    rows.sort(key=lambda x: x[1], reverse=True)
    rows = rows[:10]
    if not rows:
        return await i.response.send_message(embed=em("🏆 Top Chatters", "Još nema podataka.", color=COLORS["warning"]))
    medals = ["🥇", "🥈", "🥉"] + [f"`#{n}`" for n in range(4, 11)]
    desc = []
    for idx, (uid, cnt) in enumerate(rows):
        m = i.guild.get_member(uid)
        name = m.display_name if m else f"User {uid}"
        desc.append(f"{medals[idx]} **{name}** — `{cnt:,}` poruka")
    e = discord.Embed(title="🏆 Top 10 Najaktivnijih", description="\n".join(desc), color=COLORS["success"], timestamp=datetime.now(timezone.utc))
    await i.response.send_message(embed=e)

# ─── 🏦 BANKA ───
@bot.tree.command(name="bank", description="🏦 Banka — deposit/withdraw/balance (5% nedjeljna kamata)")
async def bank_cmd(i: discord.Interaction, akcija: str = "balance", iznos: int = 0):
    uid = str(i.user.id)
    bnk = data["bank"].setdefault(uid, {"saved": 0, "last_interest": int(time.time())})
    eco = get_economy(i.user.id)
    # kamata
    weeks = (int(time.time()) - bnk["last_interest"]) // (7*86400)
    if weeks > 0 and bnk["saved"] > 0:
        for _ in range(weeks): bnk["saved"] = int(bnk["saved"] * 1.05)
        bnk["last_interest"] = int(time.time())
    a = akcija.lower()
    if a in ("balance", "bal", "stanje"):
        return await i.response.send_message(embed=em("🏦 Banka", f"💰 Wallet: `{eco['balance']:,}`\n🏦 Banka: `{bnk['saved']:,}`\n📈 Kamata: **5% / nedjeljno**", color=COLORS["info"]))
    if a in ("deposit", "dep", "ulozi"):
        if iznos <= 0 or iznos > eco["balance"]:
            return await i.response.send_message(embed=em("❌", "Nemaš toliko.", color=COLORS["error"]), ephemeral=True)
        eco["balance"] -= iznos; bnk["saved"] += iznos; save_data()
        return await i.response.send_message(embed=em("✅ Uloženo", f"Uloženo `{iznos:,}` u banku.", color=COLORS["success"]))
    if a in ("withdraw", "wd", "podigni"):
        if iznos <= 0 or iznos > bnk["saved"]:
            return await i.response.send_message(embed=em("❌", "Nemaš toliko u banci.", color=COLORS["error"]), ephemeral=True)
        eco["balance"] += iznos; bnk["saved"] -= iznos; save_data()
        return await i.response.send_message(embed=em("✅ Podignuto", f"Podigao `{iznos:,}` iz banke.", color=COLORS["success"]))
    await i.response.send_message(embed=em("🏦 Banka — pomoć", "`/bank balance` — stanje\n`/bank deposit 100` — uloži\n`/bank withdraw 50` — podigni", color=COLORS["info"]))

# ─── 🎰 LOTO ───
@bot.tree.command(name="lottery", description="🎰 Sedmična loto — kupi tiket za 100 coina")
async def lottery_cmd(i: discord.Interaction, akcija: str = "info"):
    lot = data["lottery"]
    uid = str(i.user.id)
    a = akcija.lower()
    # auto-žrijeb svake nedjelje
    if int(time.time()) - lot.get("last_draw", 0) > 7*86400 and lot["tickets"]:
        winner_uid = random.choice(list(lot["tickets"].keys()))
        prize = lot["pot"]
        get_economy(int(winner_uid))["balance"] += prize
        lot["pot"] = 0; lot["tickets"] = {}; lot["last_draw"] = int(time.time())
        save_data()
        try:
            w = await bot.fetch_user(int(winner_uid))
            await w.send(embed=em("🎉 LOTO POBJEDA!", f"Osvojio si **{prize:,}** coina! 💰", color=COLORS["success"]))
        except: pass
    if a == "buy":
        eco = get_economy(i.user.id)
        if eco["balance"] < 100:
            return await i.response.send_message(embed=em("❌", "Treba ti 100 coina.", color=COLORS["error"]), ephemeral=True)
        eco["balance"] -= 100; lot["pot"] += 100
        lot["tickets"][uid] = lot["tickets"].get(uid, 0) + 1
        save_data()
        return await i.response.send_message(embed=em("🎫 Tiket kupljen", f"Imaš `{lot['tickets'][uid]}` tiket(a).\n💰 Pot: `{lot['pot']:,}`", color=COLORS["success"]))
    total = sum(lot["tickets"].values())
    my = lot["tickets"].get(uid, 0)
    chance = (my/total*100) if total else 0
    next_draw = lot["last_draw"] + 7*86400
    e = discord.Embed(title="🎰 Sedmična Loto", color=COLORS["info"])
    e.add_field(name="💰 Pot", value=f"`{lot['pot']:,}` coina", inline=True)
    e.add_field(name="🎫 Tvoji tiketi", value=f"`{my}` / `{total}`", inline=True)
    e.add_field(name="🎯 Šansa", value=f"`{chance:.1f}%`", inline=True)
    e.add_field(name="⏰ Sljedeći žrijeb", value=f"<t:{next_draw}:R>", inline=False)
    e.set_footer(text="/lottery buy — kupi tiket za 100 coina")
    await i.response.send_message(embed=e)

# ─── 💰 HEIST (timski razboj) ───
@bot.tree.command(name="heist", description="💰 Timski razboj — okupi 3+ ljudi i dobijte 1000-5000")
async def heist_cmd(i: discord.Interaction):
    uid = str(i.user.id)
    cd = data["heist_cooldown"].get(uid, 0)
    if int(time.time()) < cd:
        return await i.response.send_message(embed=em("⏳", f"Pokušaj ponovo <t:{cd}:R>.", color=COLORS["warning"]), ephemeral=True)
    e = discord.Embed(title="💰 RAZBOJ U PRIPREMI", description=f"{i.user.mention} organizuje razboj!\n**Klikni dugme da se pridružiš** (treba 3+ ljudi za uspjeh)\n⏰ 30 sekundi do akcije!", color=COLORS["warning"])
    crew = {i.user.id}
    class HeistView(discord.ui.View):
        def __init__(self): super().__init__(timeout=30)
        @discord.ui.button(label="🤝 Pridruži se", style=discord.ButtonStyle.success)
        async def join(self, ix: discord.Interaction, _):
            crew.add(ix.user.id)
            await ix.response.send_message(f"✅ {ix.user.mention} u ekipi! ({len(crew)} članova)", ephemeral=True, delete_after=5)
    v = HeistView()
    await i.response.send_message(embed=e, view=v)
    await asyncio.sleep(30)
    n = len(crew)
    data["heist_cooldown"][uid] = int(time.time()) + 3600
    if n < 3:
        save_data()
        return await i.followup.send(embed=em("💥 PROPAO RAZBOJ", f"Samo {n} članova — premalo. Policija je došla! 🚓", color=COLORS["error"]))
    success = random.random() < (0.4 + n*0.05)
    if success:
        per = random.randint(1000, 5000) // n
        for cid in crew: get_economy(cid)["balance"] += per
        save_data()
        await i.followup.send(embed=em("🎉 USPJEŠAN RAZBOJ!", f"Ekipa od **{n}** članova podijelila plijen!\n💰 Svako je dobio: `{per:,}` coina", color=COLORS["success"]))
    else:
        for cid in crew:
            eco = get_economy(cid); eco["balance"] = max(0, eco["balance"] - 200)
        save_data()
        await i.followup.send(embed=em("🚓 UHVAĆENI!", f"Policija je sve pohvatala! Svako je izgubio 200 coina.", color=COLORS["error"]))

# ─── 📱 QR KOD ───
@bot.tree.command(name="qr", description="📱 Generiši QR kod iz teksta ili URL-a")
async def qr_cmd(i: discord.Interaction, tekst: str):
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={discord.utils.escape_markdown(tekst).replace(' ', '%20')}"
    e = discord.Embed(title="📱 QR Kod", description=f"```{tekst[:200]}```", color=COLORS["info"])
    e.set_image(url=url)
    e.set_footer(text=f"{BOT_NAME} • QR Generator")
    await i.response.send_message(embed=e)

# ─── 🤫 CONFESS (anonimno) ───
# /confess uklonjeno (v2.1) — anonimnost se može zloupotrijebiti za uznemiravanje.

@bot.tree.command(name="setchannel", description="⚙️ [ADMIN] Postavi confess/report/birthday/staff-apps kanal")
@app_commands.describe(tip="Tip kanala", kanal="Kanal za taj tip")
@app_commands.choices(tip=[
    app_commands.Choice(name="confess",    value="confess_channel"),
    app_commands.Choice(name="report",     value="report_channel"),
    app_commands.Choice(name="birthday",   value="birthday_channel"),
    app_commands.Choice(name="staff-apps", value="staff_apps_channel"),
])
async def setchannel_cmd(i: discord.Interaction, tip: app_commands.Choice[str], kanal: discord.TextChannel):
    if not i.user.guild_permissions.administrator:
        return await i.response.send_message("❌ Samo admin.", ephemeral=True)
    get_guild_config(i.guild.id)[tip.value] = kanal.id; save_data()
    await i.response.send_message(embed=em("✅", f"{tip.name.capitalize()} kanal: {kanal.mention}", color=COLORS["success"]), ephemeral=True)

# ═══════════════════════════════════════════
#    🔥 VATRICE — sistem vatrica (zamjena za /vanity)
#    /vatrice ember — daj vatricu članu (embed, radi za sve članove)
#    /vatrice pup    — top lista (pup = popularni)
#    /vatrice oblik  — postavke (admin: emoji/oblik vatrice)
# ═══════════════════════════════════════════
def _vatrice_store():
    if "vatrice" not in data: data["vatrice"] = {}
    return data["vatrice"]

def _vatrice_cd():
    if "vatrice_cd" not in data: data["vatrice_cd"] = {}
    return data["vatrice_cd"]

def _get_vatrice(guild_id: int, user_id: int) -> int:
    return int(_vatrice_store().get(f"{guild_id}:{user_id}", 0))

def _add_vatrica(guild_id: int, user_id: int, n: int = 1) -> int:
    store = _vatrice_store()
    key = f"{guild_id}:{user_id}"
    store[key] = int(store.get(key, 0)) + n
    return store[key]

vatrice_group = app_commands.Group(name="vatrice", description="🔥 Sistem vatrica — VLASNIK ONLY (daj, top, postavke)")

def _vatrice_owner_only(i: discord.Interaction) -> bool:
    return i.user.id in OWNER_IDS

async def _update_vatrice_nick(member: discord.Member, count: int, emoji: str):
    """Doda/ažurira sufix kraj nicka, npr. 'Marko 🔥3'. Skida postojeći sufix sa baš tim emoji-em."""
    try:
        base = member.display_name
        # Ukloni stari sufix samo ako se završava sa konkretnim 'emoji + brojevi'
        # (preciznije od starog \W+\d+$ koji je sjekao i obične nickove poput 'Marko!2024')
        try:
            base = re.sub(rf"\s*{re.escape(emoji)}\d+\s*$", "", base).strip() or member.name
        except re.error:
            base = member.name
        novi_nick = f"{base} {emoji}{count}"[:32]
        if member.nick != novi_nick:
            await member.edit(nick=novi_nick, reason="Vatrice update")
    except (discord.Forbidden, discord.HTTPException):
        pass

def _vatrice_rank(guild_id: int, user_id: int) -> tuple[int, int]:
    """Vrati (mjesto, ukupno_korisnika) na vatrice top listi za server."""
    store = _vatrice_store()
    gprefix = f"{guild_id}:"
    items = [(int(k.split(":")[1]), int(v)) for k, v in store.items() if k.startswith(gprefix) and int(v) > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    for idx, (uid, _v) in enumerate(items, start=1):
        if uid == user_id:
            return idx, len(items)
    return 0, len(items)

async def _post_vatrice_objava(guild: discord.Guild, davalac: discord.Member | None, primalac: discord.Member, novi: int, emoji: str):
    """Pošalji LIJEPU objavu u podešen kanal kad neko zaradi vatricu (stil sličan level-up porukama)."""
    cfg = get_guild_config(guild.id)
    cid = cfg.get("vatrice_channel")
    if not cid: return
    ch = guild.get_channel(int(cid))
    if not ch: return

    sep = "━━━━━━━━━━━━━━━━━━━━━━"
    mjesto, ukupno = _vatrice_rank(guild.id, primalac.id)

    # naslov sa malo "milestone" osjećaja
    if novi == 1:
        naslov = f"{emoji} ᴘʀᴠᴀ ᴠᴀᴛʀɪᴄᴀ! {emoji}"
        cestit = f"🎉 Dobrodošao/la u vatreni klub, {primalac.mention}!"
    elif novi % 10 == 0:
        naslov = f"{emoji}{emoji}{emoji}  ᴍɪʟᴇsᴛᴏɴᴇ — {novi} ᴠᴀᴛʀɪᴄᴀ!  {emoji}{emoji}{emoji}"
        cestit = f"🔥 Bravo {primalac.mention} — okrugla brojka **{novi}**!"
    else:
        naslov = f"{emoji} ɴᴏᴠᴀ ᴠᴀᴛʀɪᴄᴀ! {emoji}"
        cestit = f"🎉 Čestitamo {primalac.mention}!"

    if davalac:
        izvor_line = f"🎁 Vatricu poklonio: {davalac.mention}"
    else:
        izvor_line = f"💬 Zarađeno aktivnošću u chatu (svakih 150 poruka)"

    # progres bar do sljedeće vatrice po porukama (samo informativno za primaoca)
    msg_key = f"{guild.id}:{primalac.id}"
    msgs_total = data.get("msg_count", {}).get(msg_key, 0)
    do_sljedece = 150 - (msgs_total % 150) if msgs_total > 0 else 150
    progress = max(0, min(150, 150 - do_sljedece))
    bar_full = "█" * (progress // 15)
    bar_empty = "░" * (10 - len(bar_full))
    bar = f"`{bar_full}{bar_empty}`"

    # podij (top 3) za kontekst
    store = _vatrice_store()
    gprefix = f"{guild.id}:"
    items = [(int(k.split(":")[1]), int(v)) for k, v in store.items() if k.startswith(gprefix) and int(v) > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    top_lines = []
    for idx, (uid, cnt) in enumerate(items[:3]):
        m = guild.get_member(uid)
        ime = m.display_name if m else f"ID {uid}"
        top_lines.append(f"{medals[idx]} **{ime}** — {emoji} {cnt}")
    top_block = "\n".join(top_lines) if top_lines else "_još niko nema vatrica_"

    rank_line = f"📊 Tvoje mjesto: **#{mjesto}** od **{ukupno}**" if mjesto else ""

    desc = (
        f"{sep}\n"
        f"{cestit}\n"
        f"Imaš sada **`{novi}`** {emoji}\n"
        f"{sep}\n"
        f"{izvor_line}\n"
        f"{rank_line}\n"
        f"\n**Do sljedeće vatrice:** {bar}  `{progress}/150`\n"
        f"\n**🏆 Trenutni podij:**\n{top_block}\n"
        f"{sep}\n"
        f"_Pogledaj kompletnu top listu sa_ `/vatrice pup`"
    )

    e = discord.Embed(
        title=naslov,
        description=desc,
        color=0xFF6A00,
        timestamp=datetime.now(timezone.utc),
    )
    e.set_thumbnail(url=primalac.display_avatar.url)
    e.set_author(name=str(primalac), icon_url=primalac.display_avatar.url)
    e.set_footer(text=f"🔥 {BOT_NAME} • Vatrice sistem")
    try:
        await ch.send(content=primalac.mention, embed=e)
    except (discord.Forbidden, discord.HTTPException):
        pass

@vatrice_group.command(name="ember", description="🔥 [VLASNIK] Daj vatricu(e) članu — ažurira nick i šalje objavu")
@app_commands.describe(korisnik="Kome daješ vatricu?", kolicina="Koliko vatrica dati (default 1, max 100)")
async def vatrice_ember(i: discord.Interaction, korisnik: discord.Member, kolicina: int = 1):
    if not _vatrice_owner_only(i):
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik bota može davati vatrice.", color=COLORS["error"]),
            ephemeral=True,
        )
    if korisnik.bot:
        return await i.response.send_message(
            embed=em("🔥 Vatrice", "Botovima ne dajemo vatrice!", color=COLORS["error"]),
            ephemeral=True,
        )
    # 🔢 sigurno ograniči količinu
    try:
        kolicina = int(kolicina)
    except Exception:
        kolicina = 1
    if kolicina < 1: kolicina = 1
    if kolicina > 100: kolicina = 100
    cfg = get_guild_config(i.guild.id)
    emoji = cfg.get("vatrice_emoji", "🔥")
    novi = _add_vatrica(i.guild.id, korisnik.id, kolicina)
    save_data()
    await _update_vatrice_nick(korisnik, novi, emoji)
    await _post_vatrice_objava(i.guild, i.user, korisnik, novi, emoji)
    # 📊 AKTIVNOST: napisane poruke + vatrice + level/XP
    msg_key = f"{i.guild.id}:{korisnik.id}"
    msgs_total = data.get("msg_count", {}).get(msg_key, 0)
    msgs_week = data.get("msg_count_week", {}).get(msg_key, 0)
    PRAG = 100
    do_sljedece = PRAG - (msgs_total % PRAG) if msgs_total > 0 else PRAG
    xp_info = get_xp(korisnik.id)
    lvl = xp_info.get("level", 0)
    xp_v = xp_info.get("xp", 0)
    e = discord.Embed(
        title=f"{emoji} Vatrice poslane!",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{i.user.mention} je dao **+{kolicina}** {emoji} {korisnik.mention}!\n\n"
            f"{emoji} Ukupno vatrica: **{novi}**\n"
            f"📛 Nick ažuriran: `{korisnik.display_name}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xFF6A00, timestamp=datetime.now(timezone.utc),
    )
    e.add_field(name="💬 Napisanih poruka (ukupno)", value=f"`{msgs_total:,}`", inline=True)
    e.add_field(name="📅 Poruka ove sedmice", value=f"`{msgs_week:,}`", inline=True)
    e.add_field(name=f"{emoji} Vatrice ukupno", value=f"`{novi}`", inline=True)
    e.add_field(name="⭐ Level", value=f"`{lvl}`", inline=True)
    e.add_field(name="✨ XP", value=f"`{xp_v:,}`", inline=True)
    e.add_field(name="🎯 Do sljedeće auto-vatrice", value=f"`{do_sljedece}` poruka", inline=True)
    e.set_thumbnail(url=korisnik.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} • /vatrice pup za top listu")
    await i.response.send_message(embed=e)

@vatrice_group.command(name="kanal", description="🔥 [VLASNIK] Postavi kanal za objave vatrica")
@app_commands.describe(kanal="Kanal gdje će se slati objave kad neko dobije vatricu")
async def vatrice_kanal(i: discord.Interaction, kanal: discord.TextChannel):
    if not _vatrice_owner_only(i):
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik može postaviti kanal.", color=COLORS["error"]),
            ephemeral=True,
        )
    cfg = get_guild_config(i.guild.id)
    cfg["vatrice_channel"] = kanal.id
    save_data()
    await i.response.send_message(
        embed=em("✅ Kanal postavljen", f"Objave vatrica će se slati u {kanal.mention}", color=COLORS["success"]),
        ephemeral=True,
    )

@vatrice_group.command(name="pup", description="🔥 Top lista — najpopularniji članovi po vatricama")
async def vatrice_pup(i: discord.Interaction):
    store = _vatrice_store()
    cfg = get_guild_config(i.guild.id)
    emoji = cfg.get("vatrice_emoji", "🔥")
    gprefix = f"{i.guild.id}:"
    items = [(int(k.split(":")[1]), int(v)) for k, v in store.items() if k.startswith(gprefix) and int(v) > 0]
    items.sort(key=lambda x: x[1], reverse=True)
    if not items:
        return await i.response.send_message(
            embed=em(f"{emoji} Top vatrice", "Još niko nema vatrica! Pokreni `/vatrice ember @član`.", color=COLORS["warning"]),
            ephemeral=True,
        )
    sep = "━━━━━━━━━━━━━━━━━━━━━━"
    medals = ["🥇", "🥈", "🥉"]

    # PODIJ (top 3) — istaknuto
    podij_lines = []
    for idx, (uid, cnt) in enumerate(items[:3]):
        m = i.guild.get_member(uid)
        ime = m.mention if m else f"`{uid}`"
        podij_lines.append(f"{medals[idx]}  {ime}\n     └─ {emoji} **{cnt}** vatrica")
    podij_block = "\n".join(podij_lines) if podij_lines else "_još niko nije na podiju_"

    # Mjesta 4–10
    ostali_lines = []
    for idx, (uid, cnt) in enumerate(items[3:10], start=4):
        m = i.guild.get_member(uid)
        ime = m.mention if m else f"`{uid}`"
        ostali_lines.append(f"`#{idx:>2}`  {ime} — {emoji} **{cnt}**")

    # Moje mjesto
    moja = _get_vatrice(i.guild.id, i.user.id)
    moje_mjesto, ukupno = _vatrice_rank(i.guild.id, i.user.id)
    moje_line = (
        f"📊 Tvoje mjesto: **#{moje_mjesto}** od **{ukupno}**  •  {emoji} **{moja}**"
        if moje_mjesto else f"📊 Još nemaš vatrica  •  {emoji} **0**"
    )

    desc = (
        f"{sep}\n"
        f"**🏆 PODIJ NAJVATRENIJIH** {emoji}\n"
        f"{sep}\n"
        f"{podij_block}\n"
    )
    if ostali_lines:
        desc += f"\n{sep}\n**Ostali u top 10:**\n" + "\n".join(ostali_lines) + f"\n{sep}\n"
    else:
        desc += f"{sep}\n"
    desc += f"\n{moje_line}"

    e = discord.Embed(
        title=f"{emoji} ᴛᴏᴘ ᴠᴀᴛʀɪᴄᴇ — {i.guild.name} {emoji}",
        description=desc,
        color=0xFF6A00,
        timestamp=datetime.now(timezone.utc),
    )
    if i.guild.icon:
        e.set_thumbnail(url=i.guild.icon.url)
    e.set_footer(text=f"🔥 {BOT_NAME} • Vatrice sistem  •  Vatricu zarađuješ svakih 150 poruka")
    await i.response.send_message(embed=e)

@vatrice_group.command(name="oblik", description="🔥 [VLASNIK] Postavi oblik (emoji) vatrice na serveru")
@app_commands.describe(emoji="Emoji koji predstavlja vatricu (npr. 🔥, 🌶️, ✨)")
async def vatrice_oblik(i: discord.Interaction, emoji: str = None):
    cfg = get_guild_config(i.guild.id)
    if emoji is None:
        cur = cfg.get("vatrice_emoji", "🔥")
        return await i.response.send_message(
            embed=em("🔥 Trenutni oblik vatrice", f"Trenutno: {cur}\n\nKoristi `/vatrice oblik emoji:🔥` da promijeniš.", color=COLORS["info"]),
            ephemeral=True,
        )
    if not _vatrice_owner_only(i):
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik bota može mijenjati oblik vatrice.", color=COLORS["error"]),
            ephemeral=True,
        )
    novi = emoji.strip()[:8] or "🔥"
    cfg["vatrice_emoji"] = novi
    save_data()
    await i.response.send_message(
        embed=em("✅ Oblik postavljen!", f"Novi oblik vatrice: {novi}", color=COLORS["success"]),
        ephemeral=True,
    )

@vatrice_group.command(name="start", description="🔥 [VLASNIK] Aktiviraj početak — svi članovi dobiju po 1 vatricu + nick")
async def vatrice_start(i: discord.Interaction):
    if not _vatrice_owner_only(i):
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik bota može pokrenuti početak vatrica.", color=COLORS["error"]),
            ephemeral=True,
        )
    await i.response.defer(ephemeral=False)
    cfg = get_guild_config(i.guild.id)
    emoji = cfg.get("vatrice_emoji", "🔥")
    store = _vatrice_store()
    dodano = 0
    nick_ok = 0
    skipped_owner = 0
    for m in i.guild.members:
        if m.bot: continue
        key = f"{i.guild.id}:{m.id}"
        store[key] = 1  # RESET — start uvijek postavlja vatrice na 1 (ne akumulira)
        dodano += 1
        if m.id == i.guild.owner_id:
            skipped_owner += 1
            continue  # bot ne može mijenjati nick ownera servera
        try:
            await _update_vatrice_nick(m, store[key], emoji)
            nick_ok += 1
        except Exception:
            pass
        await asyncio.sleep(0.4)  # rate limit zaštita za nick edits
    save_data()
    e = discord.Embed(
        title=f"{emoji} Vatrice — START!",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎉 **Sezona vatrica je započela!**\n\n"
            f"Svi članovi servera **{i.guild.name}** resetovani su na **1 vatricu** {emoji}\n"
            f"👥 Ukupno: **{dodano}** članova\n"
            f"📛 Nickovi ažurirani: **{nick_ok}**\n"
            f"👑 Owner servera (preskočen): **{skipped_owner}**\n\n"
            f"📋 Sada članovi automatski dobijaju vatricu **svakih 150 poruka**.\n"
            f"Vlasnik može i ručno dodijeliti sa `/vatrice ember @član`,\n"
            f"a `/vatrice pup` prikazuje top listu.\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xFF6A00, timestamp=datetime.now(timezone.utc),
    )
    if i.guild.icon:
        e.set_thumbnail(url=i.guild.icon.url)
    e.set_footer(text=f"{BOT_NAME} • Pokrenuo: {i.user.display_name}")
    await i.followup.send(embed=e)

bot.tree.add_command(vatrice_group)

# ═══════════════════════════════════════════
#    🎱 AUTO BINGO — svakih 3h u chatu
# ═══════════════════════════════════════════
@tasks.loop(hours=3)
async def auto_game_loop():
    for guild in bot.guilds:
        chan = discord.utils.get(guild.text_channels, name="chat")
        if not chan: continue

        pool = list(range(1, 76))
        random.shuffle(pool)
        izvuceni = pool[:20]
        session = {"drawn": izvuceni, "players": {}}

        now_str = datetime.now(timezone.utc).strftime("%H:%M")
        e = discord.Embed(
            title="🎱  ✦  B  I  N  G  O  ✦  🎱",
            description=(
                "🎯 **Klikni dugme ispod i unesi 5 brojeva (1–75)!**\n"
                "🎫 Tiket košta samo **500 coina** 🪙\n\n"
                "⏱️ Imaš **2 minute** za tiket — brzo! 🔥\n"
                "📢 Rezultati se objavljuju **javno** za sve 🌍"
            ),
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        e.add_field(
            name="🏆  Nagradna lista",
            value=(
                "🥉 `2 pogotka`  ──  **10.000** coina\n"
                "🥈 `3 pogotka`  ──  **30.000** coina\n"
                "🥇 `4 pogotka`  ──  **75.000** coina\n"
                "👑 `5 pogodaka` ── **250.000** coina  🏆 **JACKPOT!**"
            ),
            inline=False,
        )
        e.set_footer(text=f"🎱 × GIAN Auto-Bingo • svakih 3h • danas u {now_str} UTC")

        view = AutoBingoPupView(session)
        try:
            bingo_msg = await chan.send(embed=e, view=view)
            view.message = bingo_msg
        except: continue

        await asyncio.sleep(120)

        if not view.is_finished():
            view.stop()
        # Zaključaj dugme na originalnoj poruci
        try:
            await bingo_msg.edit(view=None)
        except: pass
        # Objavi javne rezultate
        await _bingo_reveal(session, chan)

@auto_game_loop.before_loop
async def _auto_game_wait(): await bot.wait_until_ready()

# ═══════════════════════════════════════════
#    🏆 ACTIVE MEMBER OF THE WEEK
# ═══════════════════════════════════════════
@tasks.loop(hours=24)
async def active_member_week():
    """Svaki ponedjeljak u 12:00 UTC objavi najaktivnijeg člana sedmice."""
    now = datetime.now(timezone.utc)
    if now.weekday() != 0 or now.hour != 12:
        return
    last = data.get("aotw_last")
    today_str = now.strftime("%Y-%m-%d")
    if last == today_str:
        return
    for guild in bot.guilds:
        cfg = get_guild_config(guild.id)
        weekly = data.get("msg_count_week", {})
        gprefix = f"{guild.id}:"
        gusers = [(k.split(":")[1], v) for k, v in weekly.items() if k.startswith(gprefix)]
        if not gusers:
            continue
        gusers.sort(key=lambda x: x[1], reverse=True)
        top_uid, top_count = gusers[0]
        try:
            top_member = guild.get_member(int(top_uid)) or await guild.fetch_member(int(top_uid))
        except: continue
        if not top_member: continue
        ch = guild.get_channel(cfg.get("welcome_channel") or 1494687347558715543) or guild.system_channel
        if not ch: continue
        # Bonus: 500 coina + 100 XP
        mkey = f"{guild.id}:{top_member.id}"
        data["money"][mkey] = data["money"].get(mkey, 0) + 500
        add_xp(top_member.id, 100)
        e = discord.Embed(
            title="🏆 ᴀᴄᴛɪᴠᴇ ᴍᴇᴍʙᴇʀ ᴏꜰ ᴛʜᴇ ᴡᴇᴇᴋ 🏆",
            description=(
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👑 Najaktivniji član ove sedmice je:\n\n"
                f"## {top_member.mention}\n\n"
                f"💬 Napisao/la **{top_count:,}** poruka u zadnjih 7 dana!\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎁 **Nagrada:** `+500 coina` 💰 + `+100 XP` ⚡\n"
                f"💜 Hvala što si dio × GIAN porodice!"
            ),
            color=0xFFD700, timestamp=now
        )
        e.set_thumbnail(url=top_member.display_avatar.url)
        # Top 3
        top3 = gusers[:3]
        leaderboard = ""
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, cnt) in enumerate(top3):
            mem = guild.get_member(int(uid))
            if mem:
                leaderboard += f"{medals[i]} {mem.mention} — `{cnt:,}` poruka\n"
        if leaderboard:
            e.add_field(name="📊 Top 3 sedmice", value=leaderboard, inline=False)
        e.set_footer(text=f"{BOT_NAME} • Sljedeći AOTW za 7 dana 📅")
        try:
            await ch.send(embed=e)
        except Exception as _e: print(f"[AOTW] {_e}")
    # Resetuj weekly counter
    data["msg_count_week"] = {}
    data["aotw_last"] = today_str
    save_data()

@active_member_week.before_loop
async def _aotw_wait(): await bot.wait_until_ready()

# ─── 🎱 RUČNI BINGO ───
@bot.tree.command(name="bingo", description="🎱 Pokreni Bingo — klikni dugme, unesi 5 brojeva i osvoji nagradu!")
async def bingo_cmd(i: discord.Interaction):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("👑 Nemaš pristup!", "Komandu `/bingo` može pokrenuti samo **Vlasnik** bota.", color=COLORS["error"]),
            ephemeral=True,
        )
    pool = list(range(1, 76))
    random.shuffle(pool)
    izvuceni = pool[:20]
    session = {"drawn": izvuceni, "players": {}}

    now_str = datetime.now(timezone.utc).strftime("%H:%M")
    e = discord.Embed(
        title="🎱  ✦  B  I  N  G  O  ✦  🎱",
        description=(
            "🎯 **Klikni dugme ispod i unesi 5 brojeva (1–75)!**\n"
            "🎫 Tiket košta samo **500 coina** 🪙\n\n"
            "⏱️ Imaš **2 minute** za tiket — brzo! 🔥\n"
            "📢 Rezultati se objavljuju **javno** za sve 🌍"
        ),
        color=0xF1C40F,
        timestamp=datetime.now(timezone.utc),
    )
    e.set_author(name=f"🎱 Pokrenuo/la: {i.user.display_name}", icon_url=i.user.display_avatar.url)
    e.add_field(
        name="🏆  Nagradna lista",
        value=(
            "🥉 `2 pogotka`  ──  **10.000** coina\n"
            "🥈 `3 pogotka`  ──  **30.000** coina\n"
            "🥇 `4 pogotka`  ──  **75.000** coina\n"
            "👑 `5 pogodaka` ── **250.000** coina  🏆 **JACKPOT!**"
        ),
        inline=False,
    )
    e.set_footer(text=f"🎱 × GIAN Bingo • danas u {now_str} UTC • Cijena tiketa: 500 coina 🪙")

    view = AutoBingoPupView(session)
    await i.response.send_message(embed=e, view=view)
    view.message = await i.original_response()

    await asyncio.sleep(120)

    if not view.is_finished():
        view.stop()
    # Zaključaj dugme na originalnoj poruci
    try:
        await view.message.edit(view=None)
    except: pass
    # Objavi javne rezultate u istom kanalu
    await _bingo_reveal(session, i.channel)


# ═══════════════════════════════════════════
#    🎟️ PUP — BINGO LISTIĆ (dugme + modal)
# ═══════════════════════════════════════════
# Nagrade: 2=10k | 3=30k | 4=75k | 5=250k (JACKPOT)
# Cijena listića: 500 coina | Brojevi: 1-75 | Izvlači se 20
# ═══════════════════════════════════════════

PUP_CIJENA = 500
PUP_NAGRADE = {2: 10_000, 3: 30_000, 4: 75_000, 5: 250_000}
PUP_XP      = {2: 50,     3: 100,    4: 200,     5: 500}

class PupModal(discord.ui.Modal, title="🎟️ Unesi 5 brojeva (1–75)"):
    brojevi_input = discord.ui.TextInput(
        label="Unesi 5 različitih brojeva odvojenih razmakom",
        placeholder="Primjer:  7  15  33  55  72",
        min_length=5,
        max_length=30,
        style=discord.TextStyle.short,
    )

    def __init__(self, session: dict):
        super().__init__()
        self.session = session

    async def on_submit(self, i: discord.Interaction):
        uid = i.user.id

        # ── Provjera duplikata ──
        if uid in self.session["players"]:
            return await i.response.send_message(
                embed=em("❌ Već si uzeo/la tiket", "Možeš uzeti samo jedan tiket po bingu!", color=COLORS["error"]),
                ephemeral=True,
            )

        # ── Parsiranje ──
        parts = self.brojevi_input.value.strip().split()
        if len(parts) != 5:
            return await i.response.send_message(
                embed=em("❌ Pogrešan unos", "Moraš unijeti **tačno 5 brojeva**!\n💡 Primjer: `7 15 33 55 72`", color=COLORS["error"]),
                ephemeral=True,
            )
        try:
            odabrani = [int(x) for x in parts]
        except ValueError:
            return await i.response.send_message(
                embed=em("❌ Pogrešan unos", "Svi unosi moraju biti **cijeli brojevi**!", color=COLORS["error"]),
                ephemeral=True,
            )
        if any(n < 1 or n > 75 for n in odabrani):
            return await i.response.send_message(
                embed=em("❌ Broj izvan raspona", "Svi brojevi moraju biti između **1** i **75**!", color=COLORS["error"]),
                ephemeral=True,
            )
        if len(set(odabrani)) != 5:
            return await i.response.send_message(
                embed=em("❌ Duplikati", "Svih 5 brojeva mora biti **različito**!", color=COLORS["error"]),
                ephemeral=True,
            )

        # ── Balans ──
        eco = get_economy(uid)
        if eco.get("balance", 0) < PUP_CIJENA:
            return await i.response.send_message(
                embed=em(
                    "❌ Nema dovoljno coina",
                    f"Cijena listića je **{PUP_CIJENA:,} coina**.\n"
                    f"Tvoj balans: **{eco.get('balance', 0):,}** coina 💸\n\n"
                    f"Zaradi više sa `/posao` ili `/daily`!",
                    color=COLORS["error"],
                ),
                ephemeral=True,
            )

        # ── Oduzmi cijenu i sačuvaj tiket (bez otkrivanja rezultata!) ──
        eco["balance"] = eco.get("balance", 0) - PUP_CIJENA
        self.session["players"][uid] = {"brojevi": odabrani, "user": i.user.display_name, "avatar": str(i.user.display_avatar.url)}
        save_data()

        # ── Potvrda — rezultati se otkrivaju tek nakon 2 minute ──
        potvrda = discord.Embed(
            title="🎟️  Tiket primljen!  ✅",
            description=(
                f"✔️ Tvoji brojevi su **tajno zabilježeni** i čekaju kraj runde!\n"
                f"🤞 Drži fige i čekaj objavu!"
            ),
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        potvrda.add_field(
            name="🔢  Tvoji odabrani brojevi",
            value=" ".join(f"`{n:02d}`" for n in sorted(odabrani)),
            inline=False,
        )
        potvrda.add_field(name="💰  Plaćeno", value=f"**{PUP_CIJENA:,} coina** 🪙", inline=True)
        potvrda.add_field(name="⏳  Rezultati", value="**za ~2 minute** — javno! 📢", inline=True)
        potvrda.set_footer(text="🎱 × GIAN Bingo • Sreće ti! 🍀")
        await i.response.send_message(embed=potvrda, ephemeral=True)


async def _bingo_reveal(session: dict, channel: discord.TextChannel):
    """Nakon 2 minute — javno objavi rezultate za sve igrače."""
    drawn     = sorted(session["drawn"])
    drawn_set = set(drawn)
    players   = session.get("players", {})

    # ── Red izvučenih 20 brojeva (vizualni prikaz) ──
    drawn_display = " ".join(f"`{n:02d}`" for n in drawn)

    if not players:
        e = discord.Embed(
            title="🎱  Bingo — Runda završena",
            description="😔 **Niko nije uzeo tiket ovaj put.**\n💡 Sljedeći auto-bingo za **~3 sata**! ⏰",
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        e.add_field(
            name="🎲  Izvučenih 20 brojeva",
            value=drawn_display,
            inline=False,
        )
        e.set_footer(text="🎱 × GIAN Bingo • Budi brži/a idući put! 🍀")
        try:
            await channel.send(embed=e)
        except Exception:
            pass
        return

    # ── Izračunaj rezultate za svakog igrača ──
    results      = []
    total_prizes = 0
    jackpot_uid  = None

    for uid_str, info in players.items():
        uid     = int(uid_str)
        odabrani = info["brojevi"] if isinstance(info, dict) else info
        ime      = info["user"]    if isinstance(info, dict) else f"Igrač#{uid}"
        pogoci   = sorted(set(odabrani) & drawn_set)
        br       = len(pogoci)
        nagrada  = PUP_NAGRADE.get(br, 0)
        xp_n     = PUP_XP.get(br, 0)

        if nagrada > 0:
            eco = get_economy(uid)
            eco["balance"] = eco.get("balance", 0) + nagrada
            add_xp(uid, xp_n)
            total_prizes += nagrada
            if br == 5:
                jackpot_uid = uid

        results.append({
            "uid": uid, "ime": ime,
            "odabrani": sorted(odabrani), "pogoci": pogoci,
            "br": br, "nagrada": nagrada,
        })

    save_data()

    # ── Sortiraj po broju pogodaka (desc) ──
    results.sort(key=lambda x: x["br"], reverse=True)

    # ── Napravi listu rezultata ──
    icon = {0: "💨", 1: "💨", 2: "🪙", 3: "🪙🪙", 4: "🪙🪙🪙", 5: "🏆"}
    medal = {0: "▫️", 1: "▫️", 2: "🥉", 3: "🥈", 4: "🥇", 5: "👑"}
    rows = []
    for r in results:
        br_icon   = icon.get(r["br"], "")
        med       = medal.get(r["br"], "▫️")
        odab_str  = " ".join(f"`{n:02d}`" for n in r["odabrani"])
        pogoc_str = " ".join(f"**`{n:02d}`**" for n in r["pogoci"]) if r["pogoci"] else "`—`"
        nagrada_str = f"**+{r['nagrada']:,} coina** 🪙" if r["nagrada"] > 0 else "_bez nagrade_"
        rows.append(
            f"{med} {br_icon} **{r['ime']}**  •  {r['br']}/5 ✓  •  {nagrada_str}\n"
            f"> 🔢 {odab_str}\n"
            f"> 🎯 Pogoci: {pogoc_str}"
        )

    results_txt = "\n\n".join(rows) if rows else "*Niko nije igrao.*"

    title = "🏆  ✦  J A C K P O T  ✦  🏆" if jackpot_uid else "🎱  ✦  B I N G O  —  Rezultati  ✦"
    color = 0xFFD700 if jackpot_uid else 0xF1C40F

    e = discord.Embed(
        title=title,
        description="🎉 Runda je gotova! Pogledaj ko je pobijedio!" if total_prizes > 0 else "Ovaj put nema pobjednika. Sreće idući put!",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    e.add_field(
        name="🎲  Izvučenih 20 brojeva",
        value=drawn_display,
        inline=False,
    )
    e.add_field(name=f"📋  Rezultati  ({len(results)} igrača)", value=results_txt[:1020], inline=False)
    if total_prizes > 0:
        e.add_field(name="💰  Ukupno podijeljeno", value=f"**{total_prizes:,} coina** 🪙", inline=True)
        e.add_field(name="🏅  Pobjednici", value=f"**{sum(1 for r in results if r['nagrada'] > 0)}** igrača", inline=True)
    e.set_footer(text="🎱 × GIAN Bingo • Čestitamo pobjednicima! 🎉")
    try:
        await channel.send(embed=e)
    except Exception:
        pass


class AutoBingoPupView(discord.ui.View):
    """View za auto bingo loop — dugme Uzmi tiket otvara modal."""
    def __init__(self, session: dict):
        super().__init__(timeout=120)
        self.session = session
        self.message: discord.Message | None = None

    @discord.ui.button(label="Uzmi tiket", emoji="🎱", style=discord.ButtonStyle.primary)
    async def uzmi_tiket(self, i: discord.Interaction, _btn: discord.ui.Button):
        await i.response.send_modal(PupModal(self.session))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

# ═══════════════════════════════════════════
#    📊 USAGE TRACKING — broji koliko se koja komanda koristi
# ═══════════════════════════════════════════

# ═══════════════════════════════════════════
#    🔊 PRIVATE VOICE — Join To Create
# ═══════════════════════════════════════════
JTC_VOICE_ID = 1494043959213953114  # Glavni "Kreiraj svoj kanal" voice
PVC_INFO_CHANNEL_ID = 1494043958681145570  # Kanal gdje se postavlja uputstvo
data.setdefault("private_voices", {})  # {channel_id: owner_id}
data.setdefault("pvc_info_posted", False)

async def post_pvc_info():
    """Jednom postavi lijep uputstvo embed u info kanal."""
    if data.get("pvc_info_posted"): return
    for guild in bot.guilds:
        ch = guild.get_channel(PVC_INFO_CHANNEL_ID)
        if not ch: continue
        try:
            sep = "━━━━━━━━━━━━━━━━━━━━━━"
            e = discord.Embed(
                title="🔊 ᴋᴀᴋᴏ ᴋᴏʀɪꜱᴛɪᴛɪ ᴘʀɪᴠᴀᴛɴɪ ᴠᴏɪᴄᴇ?",
                description=(
                    f"{sep}\n"
                    f"💡 Napravi **svoj vlastiti voice kanal** koji možeš zaključati, sakriti, "
                    f"renamati, postaviti limit i još mnogo toga!\n"
                    f"{sep}"
                ),
                color=0x9B59B6
            )
            e.add_field(
                name="1️⃣ Kako napraviti svoj kanal",
                value=(
                    f"➜ Uđi u voice kanal **🔊 Kreiraj svoj kanal** <#{JTC_VOICE_ID}>\n"
                    f"➜ Bot će ti **automatski** napraviti privatni voice\n"
                    f"➜ I **odmah** te prebaciti u njega\n"
                    f"➜ Postaješ **vlasnik** 👑 i dobijaš kontrolni panel!\n{sep}"
                ),
                inline=False
            )
            e.add_field(
                name="2️⃣ Kontrolni panel (dugmad u tvom VC-u)",
                value=(
                    "🔒 **Lock** — niko ne može ući u tvoj kanal\n"
                    "🔓 **Unlock** — svi mogu ući\n"
                    "👁️ **Hide** — sakrij kanal od svih\n"
                    "👀 **Show** — vrati kanal vidljiv\n"
                    "✏️ **Rename** — promijeni ime kanala\n"
                    "👥 **Limit** — postavi max broj članova (1-99)\n"
                    "🚫 **Kick** — izbaci nekog iz tvog kanala\n"
                    "👑 **Owner** — prebaci vlasništvo na drugog\n"
                    "❌ **Delete** — odmah obriši kanal\n"
                    f"{sep}"
                ),
                inline=False
            )
            e.add_field(
                name="3️⃣ Automatsko brisanje",
                value=(
                    "🗑️ Kad **svi izađu**, kanal se **automatski briše**\n"
                    "💾 Ne brini o čišćenju — bot to radi za tebe!\n"
                    f"{sep}"
                ),
                inline=False
            )
            e.add_field(
                name="💡 Korisni Tip",
                value=(
                    "✨ Lock + Hide = potpuno privatan VC samo za tebe i prijatelje\n"
                    "🎮 Pozovi prijatelje preko **Invite to channel** desnim klikom\n"
                    "👑 Prebaci vlasništvo prije izlaska ako želiš da kanal ostane"
                ),
                inline=False
            )
            e.set_footer(text=f"{BOT_NAME} • Privatni Voice Sistem 🔊")
            e.set_thumbnail(url="https://cdn.discordapp.com/emojis/963322998568083477.gif")
            await ch.send(embed=e)
            data["pvc_info_posted"] = True
            save_data()
        except Exception as _e:
            print(f"[pvc-info] {_e}")

class PrivateVCPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _check_owner(self, interaction):
        ch = interaction.user.voice.channel if interaction.user.voice else None
        if not ch or str(ch.id) not in data.get("private_voices", {}):
            await interaction.response.send_message("❌ Nisi u privatnom voice kanalu!", ephemeral=True)
            return None
        if data["private_voices"][str(ch.id)] != interaction.user.id:
            await interaction.response.send_message("❌ Nisi vlasnik ovog kanala!", ephemeral=True)
            return None
        return ch

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger, custom_id="pvc_lock")
    async def lock(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        await ch.set_permissions(i.guild.default_role, connect=False)
        await i.response.send_message("🔒 Kanal **zaključan** — niko ne može ući!", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success, custom_id="pvc_unlock")
    async def unlock(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        await ch.set_permissions(i.guild.default_role, connect=None)
        await i.response.send_message("🔓 Kanal **otključan** — svi mogu ući!", ephemeral=True)

    @discord.ui.button(label="👁️ Hide", style=discord.ButtonStyle.secondary, custom_id="pvc_hide")
    async def hide(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        await ch.set_permissions(i.guild.default_role, view_channel=False)
        await i.response.send_message("👁️ Kanal **sakriven** — niko ga ne vidi!", ephemeral=True)

    @discord.ui.button(label="👀 Show", style=discord.ButtonStyle.secondary, custom_id="pvc_show")
    async def show(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        await ch.set_permissions(i.guild.default_role, view_channel=None)
        await i.response.send_message("👀 Kanal **vidljiv** svima!", ephemeral=True)

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary, custom_id="pvc_rename")
    async def rename(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        modal = discord.ui.Modal(title="✏️ Promijeni ime kanala")
        name_in = discord.ui.TextInput(label="Novo ime", placeholder="🔊 Moj kanal", max_length=50)
        modal.add_item(name_in)
        async def cb(m_int):
            await ch.edit(name=name_in.value)
            await m_int.response.send_message(f"✅ Ime promijenjeno u: **{name_in.value}**", ephemeral=True)
        modal.on_submit = cb
        await i.response.send_modal(modal)

    @discord.ui.button(label="👥 Limit", style=discord.ButtonStyle.primary, custom_id="pvc_limit")
    async def limit(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        modal = discord.ui.Modal(title="👥 Postavi limit članova")
        lim_in = discord.ui.TextInput(label="Broj (0 = bez limita, max 99)", placeholder="5")
        modal.add_item(lim_in)
        async def cb(m_int):
            try: n = max(0, min(99, int(lim_in.value)))
            except: return await m_int.response.send_message("❌ Mora biti broj!", ephemeral=True)
            await ch.edit(user_limit=n)
            await m_int.response.send_message(f"✅ Limit postavljen na **{n}** {'(bez limita)' if n==0 else 'članova'}", ephemeral=True)
        modal.on_submit = cb
        await i.response.send_modal(modal)

    @discord.ui.button(label="🚫 Kick", style=discord.ButtonStyle.danger, custom_id="pvc_kick", row=1)
    async def kick(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        if not ch.members or len([m for m in ch.members if m.id != i.user.id]) == 0:
            return await i.response.send_message("❌ Nema nikog za izbacit!", ephemeral=True)
        opts = [discord.SelectOption(label=m.display_name, value=str(m.id))
                for m in ch.members if m.id != i.user.id][:25]
        sel = discord.ui.Select(placeholder="Izaberi koga da izbaciš", options=opts)
        async def sel_cb(s_int):
            mid = int(sel.values[0])
            mem = ch.guild.get_member(mid)
            if mem and mem.voice and mem.voice.channel == ch:
                await mem.move_to(None)
                await s_int.response.send_message(f"🚫 {mem.mention} izbačen iz kanala!", ephemeral=True)
            else:
                await s_int.response.send_message("❌ Već nije u kanalu.", ephemeral=True)
        sel.callback = sel_cb
        view = discord.ui.View(timeout=60)
        view.add_item(sel)
        await i.response.send_message("Izaberi člana:", view=view, ephemeral=True)

    @discord.ui.button(label="👑 Owner", style=discord.ButtonStyle.secondary, custom_id="pvc_transfer", row=1)
    async def transfer(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        opts = [discord.SelectOption(label=m.display_name, value=str(m.id))
                for m in ch.members if m.id != i.user.id and not m.bot][:25]
        if not opts:
            return await i.response.send_message("❌ Nema nikog kome bi prebacio vlasništvo!", ephemeral=True)
        sel = discord.ui.Select(placeholder="Novi vlasnik", options=opts)
        async def sel_cb(s_int):
            new_id = int(sel.values[0])
            new_owner = ch.guild.get_member(new_id)
            data["private_voices"][str(ch.id)] = new_id
            save_data()
            await ch.set_permissions(i.user, overwrite=None)
            await ch.set_permissions(new_owner, manage_channels=True, move_members=True, mute_members=True, deafen_members=True)
            await s_int.response.send_message(f"👑 Vlasništvo prebačeno na {new_owner.mention}!", ephemeral=True)
        sel.callback = sel_cb
        view = discord.ui.View(timeout=60)
        view.add_item(sel)
        await i.response.send_message("Izaberi novog vlasnika:", view=view, ephemeral=True)

    @discord.ui.button(label="❌ Delete", style=discord.ButtonStyle.danger, custom_id="pvc_delete", row=1)
    async def delete(self, i: discord.Interaction, b):
        ch = await self._check_owner(i)
        if not ch: return
        await i.response.send_message("❌ Brišem kanal za 3s...", ephemeral=True)
        await asyncio.sleep(3)
        try:
            data["private_voices"].pop(str(ch.id), None)
            save_data()
            await ch.delete(reason="Vlasnik obrisao privatni VC")
        except: pass

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot: return
    # ── KREIRAJ NOVI PRIVATNI VC ──
    if after.channel and after.channel.id == JTC_VOICE_ID:
        new_ch = None
        try:
            cat = after.channel.category
            me = member.guild.me
            # ── Provjera permisija ──
            missing = []
            if not me.guild_permissions.manage_channels: missing.append("Manage Channels")
            if not me.guild_permissions.move_members:    missing.append("Move Members")
            if cat is not None:
                cat_perms = cat.permissions_for(me)
                if not cat_perms.manage_channels: missing.append("Manage Channels (kategorija)")
                if not cat_perms.connect:         missing.append("Connect (kategorija)")
            if missing:
                msg = f"Botu nedostaju permisije: **{', '.join(missing)}**"
                print(f"[pvc create] ✘ {msg}")
                try: await member.send(f"❌ Ne mogu napraviti tvoj voice kanal.\n{msg}")
                except: pass
                return
            # ── Kreiraj kanal (fallback bez kategorije ako je puna) ──
            try:
                new_ch = await member.guild.create_voice_channel(
                    name=f"🔊 {member.display_name}",
                    category=cat,
                    reason=f"Privatni VC za {member}"
                )
            except discord.HTTPException as he:
                if (he.code == 30013) or ("Maximum number" in str(he)):
                    print(f"[pvc create] kategorija puna → pravim bez kategorije")
                    new_ch = await member.guild.create_voice_channel(
                        name=f"🔊 {member.display_name}",
                        reason=f"Privatni VC za {member} (bez kategorije)"
                    )
                else:
                    raise
            await new_ch.set_permissions(member, manage_channels=True, move_members=True,
                mute_members=True, deafen_members=True, connect=True, view_channel=True)
            data["private_voices"][str(new_ch.id)] = member.id
            save_data()
            await member.move_to(new_ch)
            print(f"[pvc create] ✓ {member} → {new_ch.name} ({new_ch.id})")
            # Pošalji panel u kanal (text chat unutar VC-a, Discord 2024+ feature)
            try:
                e = discord.Embed(
                    title=f"🔊 Dobrodošao u svoj kanal, {member.display_name}!",
                    description=(
                        "**Ti si vlasnik!** 👑 Koristi dugmad ispod:\n\n"
                        "🔒 **Lock** — niko ne može ući\n"
                        "🔓 **Unlock** — svi mogu ući\n"
                        "👁️ **Hide / Show** — sakrij/pokaži kanal\n"
                        "✏️ **Rename** — promijeni ime\n"
                        "👥 **Limit** — postavi max članova\n"
                        "🚫 **Kick** — izbaci nekog iz kanala\n"
                        "👑 **Owner** — prebaci vlasništvo\n"
                        "❌ **Delete** — obriši kanal\n\n"
                        "*Kanal se automatski briše kad ostane prazan.*"
                    ),
                    color=COLORS.get("balkan", 0x9B59B6)
                )
                e.set_footer(text=f"{BOT_NAME} • Privatni Voice Sistem")
                await new_ch.send(content=member.mention, embed=e, view=PrivateVCPanel())
            except Exception as _e: print(f"[pvc panel] {_e}")
        except Exception as _e:
            import traceback
            print(f"[pvc create] ✘ {type(_e).__name__}: {_e}")
            traceback.print_exc()
            try: await member.send(f"❌ Greška pri kreiranju voice kanala:\n```{type(_e).__name__}: {_e}```")
            except: pass

    # ── OBRIŠI PRAZAN PRIVATNI VC ──
    if before.channel and str(before.channel.id) in data.get("private_voices", {}):
        if len([m for m in before.channel.members if not m.bot]) == 0:
            try:
                data["private_voices"].pop(str(before.channel.id), None)
                save_data()
                await before.channel.delete(reason="Privatni VC prazan")
            except Exception as _e: print(f"[pvc delete] {_e}")

    # napomena: tree.error handler je gore (on_app_error)

@bot.event
async def on_app_command_completion(interaction, command):
    try:
        n = command.qualified_name if hasattr(command, "qualified_name") else command.name
        data["cmd_uses"][n] = data["cmd_uses"].get(n, 0) + 1
    except Exception: pass

# ─── 🚨 REPORT — 1 minuta cooldown po članu ───
@bot.tree.command(name="report", description="🚨 Prijavi člana staffu (1x u minuti)")
@app_commands.describe(korisnik="Koga prijavljuješ", razlog="Razlog prijave (kratko i jasno)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: (i.guild_id, i.user.id))
async def report_cmd(i: discord.Interaction, korisnik: discord.Member, razlog: str):
    if korisnik.id == i.user.id:
        return await i.response.send_message(
            embed=em("❌ Greška", "Ne možeš prijaviti samog sebe.", color=COLORS["error"]),
            ephemeral=True
        )
    if korisnik.bot:
        return await i.response.send_message(
            embed=em("❌ Greška", "Botove ne možeš prijaviti.", color=COLORS["error"]),
            ephemeral=True
        )

    # ── Sigurnost: ukloni eventualne invite linkove iz razloga ──
    safe_razlog = INVITE_REGEX.sub("[link uklonjen]", razlog[:1000])
    # ── Sigurnost: očisti ime servera od potencijalnih linkova ──
    safe_guild_name = INVITE_REGEX.sub("[link]", i.guild.name) if i.guild else "—"

    cfg = get_guild_config(i.guild.id)
    ch_id = cfg.get("report_channel")
    target_ch = i.guild.get_channel(ch_id) if ch_id else None

    e = discord.Embed(
        title="🚨 NOVA PRIJAVA",
        color=COLORS["error"],
        timestamp=discord.utils.utcnow(),
    )
    e.add_field(name="👤 Prijavio",   value=f"{i.user.mention}\n`{i.user}`\nID: `{i.user.id}`",     inline=True)
    e.add_field(name="🎯 Prijavljen", value=f"{korisnik.mention}\n`{korisnik}`\nID: `{korisnik.id}`", inline=True)
    e.add_field(name="📍 Kanal",      value=i.channel.mention if i.channel else "—",                  inline=True)
    e.add_field(name="📝 Razlog",     value=safe_razlog,                                               inline=False)
    try:
        e.set_thumbnail(url=korisnik.display_avatar.url)
    except Exception: pass
    e.set_footer(text=f"Server: {safe_guild_name}")

    sent = False
    if target_ch:
        try:
            await target_ch.send(embed=e)
            sent = True
        except Exception: pass

    if not sent:
        for oid in OWNER_IDS:
            try:
                u = await bot.fetch_user(oid)
                await u.send(embed=e)
                sent = True
            except Exception: pass

    if sent:
        await i.response.send_message(
            embed=em("✅ Prijava poslata", "Staff je obaviješten. Hvala!\n\n*Možeš ponovo prijaviti za 1 minutu.*", color=COLORS["success"]),
            ephemeral=True
        )
    else:
        await i.response.send_message(
            embed=em("⚠️ Nije poslato", "Ne mogu poslati prijavu.\nReci adminu: `/setchannel tip:report kanal:#kanal`", color=COLORS["warning"]),
            ephemeral=True
        )

@report_cmd.error
async def report_cmd_error(i: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        secs = int(error.retry_after)
        try:
            await i.response.send_message(
                embed=em("⏳ Sačekaj", f"Možeš opet prijaviti za **{secs}s**.\n*Limit: 1 prijava u minuti po članu.*", color=COLORS["warning"]),
                ephemeral=True
            )
        except Exception: pass
    else:
        try:
            await i.response.send_message(
                embed=em("❌ Greška", f"`{error}`", color=COLORS["error"]),
                ephemeral=True
            )
        except Exception: pass

# ═══════════════════════════════════════════
#    📋 STAFF PRIJAVA — /tiket-staff
# ═══════════════════════════════════════════

class StaffApplicationModal(discord.ui.Modal, title="📋 Prijava za Staff"):
    god = discord.ui.TextInput(
        label="Koliko imaš godina?",
        placeholder="Npr: 18",
        min_length=1, max_length=3,
        style=discord.TextStyle.short,
    )
    iskustvo = discord.ui.TextInput(
        label="Imaš li iskustva kao mod/staff?",
        placeholder="Opiši prethodno iskustvo na Discordu...",
        min_length=10, max_length=500,
        style=discord.TextStyle.paragraph,
    )
    zasto = discord.ui.TextInput(
        label="Zašto želiš biti staff?",
        placeholder="Reci nam šta te motiviše...",
        min_length=20, max_length=600,
        style=discord.TextStyle.paragraph,
    )
    igraci = discord.ui.TextInput(
        label="Koliko igrača možeš dovesti na server?",
        placeholder="Npr: 5-10, imam Discord/Instagram zajednicu...",
        min_length=5, max_length=300,
        style=discord.TextStyle.paragraph,
    )
    aktivnost = discord.ui.TextInput(
        label="Koliko sati dnevno + timezone zona?",
        placeholder="Npr: 3-5 sati, CET zona...",
        min_length=3, max_length=200,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, i: discord.Interaction):
        guild     = i.guild
        safe_name = "".join(c for c in i.user.name.lower() if c.isalnum() or c in "-_")[:20] or str(i.user.id)

        # Provjeri već postojeću prijavu
        existing = discord.utils.get(guild.text_channels, name=f"prijava-{safe_name}")
        if existing:
            return await i.response.send_message(
                embed=em("⚠️ Već prijavljen/a", f"Imaš već aktivnu prijavu: {existing.mention}", color=COLORS["warning"]),
                ephemeral=True,
            )

        if not guild.me.guild_permissions.manage_channels:
            return await i.response.send_message(
                embed=em("❌ Permisija", "Bot nema **Manage Channels** permisiju! Javi adminu.", color=COLORS["error"]),
                ephemeral=True,
            )

        # 🔒 PRIVATNO — vidi SAMO vlasnik bota + aplikant (po želji korisnika)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False, send_messages=False, add_reactions=False
            ),
            i.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=False, add_reactions=False
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            ),
        }
        # Dodaj sve OWNER-e iz OWNER_IDS whiteliste
        for owner_id in OWNER_IDS:
            owner_member = guild.get_member(owner_id)
            if owner_member:
                overwrites[owner_member] = discord.PermissionOverwrite(
                    read_messages=True, send_messages=True, add_reactions=True, manage_channels=True
                )
        # Dodaj i vlasnika servera (guild.owner) da uvijek vidi
        if guild.owner and guild.owner.id not in OWNER_IDS:
            overwrites[guild.owner] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True, add_reactions=True
            )

        # Kategorija: "Staff Prijave" → "Prijave" → "Tickets" → bez kategorije
        category = (
            discord.utils.find(lambda c: any(w in c.name.lower() for w in ("staff prijav", "prijav")), guild.categories) or
            discord.utils.find(lambda c: "ticket" in c.name.lower(), guild.categories)
        )

        try:
            chan = await guild.create_text_channel(
                f"prijava-{safe_name}",
                overwrites=overwrites,
                category=category,
                reason=f"Staff prijava od {i.user}",
                topic=f"📋 Staff prijava — {i.user.display_name} ({i.user.id})",
            )
        except discord.Forbidden:
            return await i.response.send_message(
                embed=em("❌ Permisija", "Bot nema dozvolu da kreira kanale!", color=COLORS["error"]),
                ephemeral=True,
            )
        except Exception as ex:
            return await i.response.send_message(
                embed=em("❌ Greška", f"`{ex}`", color=COLORS["error"]),
                ephemeral=True,
            )

        BAR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        e = discord.Embed(
            title="📋  Nova Staff Prijava",
            description=(
                f"{BAR}\n"
                f"👤 **{i.user.display_name}** ({i.user.mention})\n"
                f"🆔 ID: `{i.user.id}`\n"
                f"📅 Nalog: <t:{int(i.user.created_at.timestamp())}:R>\n"
                f"🌐 Server: **{guild.name}**\n"
                f"{BAR}"
            ),
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        e.set_thumbnail(url=i.user.display_avatar.url)
        e.set_author(
            name=f"× GIAN — STAFF PRIJAVA",
            icon_url=guild.me.display_avatar.url,
        )
        e.add_field(name="🎂  Godine",               value=self.god.value,       inline=True)
        e.add_field(name="⏰  Aktivnost / Zona",     value=self.aktivnost.value,  inline=True)
        e.add_field(name="🎓  Iskustvo kao Staff",   value=self.iskustvo.value,   inline=False)
        e.add_field(name="💬  Zašto želi biti Staff", value=self.zasto.value,     inline=False)
        e.add_field(name="👥  Koliko igrača dovodi",  value=self.igraci.value,    inline=False)
        e.add_field(
            name="📌  Obaveze Staffa",
            value=(
                "✅ Dovodiš nove igrače na server\n"
                "✅ Redovito si aktivan/na u chatovima\n"
                "✅ Pomažeš moderirati i primjenjuješ pravila\n"
                "✅ Štitis server od raida, napada i spama\n"
                "✅ Komuniciraš s timom i prijaviš probleme"
            ),
            inline=False,
        )
        e.add_field(
            name="🗳️  Glasanje Admina",
            value=(
                "✅ **Prihvati** — dodjeljuje StaffTeam ulogu\n"
                "❌ **Odbij** — zatvara kanal\n"
                "⏳ **Na čekanju** — čeka više informacija"
            ),
            inline=False,
        )
        e.set_footer(text=f"🔒 GIAN Staff Prijava  •  {guild.name}  •  PRIVATNO — vidi samo vlasnik")

        await chan.send(
            content=f"🔒 **Nova staff prijava od {i.user.mention}** — vidljivo samo vlasniku 👇",
            embed=e,
            view=StaffVoteView(),
        )

        # Ako postoji konfigurisani staff_apps kanal — pošalji i tamo (ping za admina)
        cfg = get_guild_config(guild.id)
        notify_id = cfg.get("staff_apps_channel") or cfg.get("log_channel")
        notify_ch = guild.get_channel(notify_id) if notify_id else None
        if notify_ch and notify_ch != chan:
            try:
                notif = discord.Embed(
                    title="🔔 Nova Staff Prijava",
                    description=f"**{i.user.display_name}** je podnio/la prijavu!\n📂 Pogledaj: {chan.mention}",
                    color=0xF1C40F,
                )
                await notify_ch.send(embed=notif)
            except Exception:
                pass

        potvrda = discord.Embed(
            title="✅  Prijava primljena!",
            description=(
                f"## 🎉 Uspješno si se prijavio/la za Staff!\n"
                f"📂 Tvoja prijava je objavljena: {chan.mention}\n\n"
                f"🔒 Tvoja prijava je **privatna** — vidi je samo vlasnik bota.\n"
                f"⏳ Pregled traje **1–3 dana**. Budemo te obavijestili! 📩"
            ),
            color=0xF1C40F,
            timestamp=datetime.now(timezone.utc),
        )
        potvrda.add_field(
            name="📋  Šta se čeka od Staffa",
            value=(
                "👥 Dovodiš nove igrače i rasteš zajednicu\n"
                "🛡️ Štitis server od raida, napada i spama\n"
                "💬 Modiraš chatove i primjenjuješ pravila\n"
                "⏳ Admin ručno pregleda prijavu i dodjeljuje ulogu\n"
                "🤝 Nema automatskih permisija — sve odobrava Admin!"
            ),
            inline=False,
        )
        potvrda.set_footer(text="📋 GIAN  •  Hvala na prijavi! 🙏")
        await i.response.send_message(embed=potvrda, ephemeral=True)


class StaffVoteView(discord.ui.View):
    """Admin glasanje za staff prijavu — Prihvati / Odbij / Na čekanju.
    custom_id-ovi su statični → view preživljava bot restart.
    applicant_id se čita direktno iz embed opisa poruke."""
    def __init__(self):
        super().__init__(timeout=None)

    @staticmethod
    def _extract_aid(message) -> int:
        """Izvuci ID prijavljenog iz embeda poruke."""
        if message and message.embeds:
            import re as _re
            m = _re.search(r'ID: `(\d+)`', message.embeds[0].description or "")
            if m:
                return int(m.group(1))
        return 0

    @staticmethod
    async def _auto_close_channel(channel, delay: int = 10):
        """Briše 'prijava-*' kanal nakon zadatog delayas."""
        if channel and channel.name.startswith("prijava-"):
            await asyncio.sleep(delay)
            try:
                await channel.delete(reason="Staff prijava završena — auto-close")
            except Exception:
                pass

    @discord.ui.button(label="Prihvati", emoji="✅", style=discord.ButtonStyle.success, custom_id="sv_prihvati")
    async def prihvati(self, i: discord.Interaction, b: discord.ui.Button):
        if not i.user.guild_permissions.manage_roles:
            return await i.response.send_message(
                embed=em("❌ Nemaš permisiju!", "Samo Staff/Admini mogu glasati.", color=COLORS["error"]),
                ephemeral=True,
            )
        aid = self._extract_aid(i.message)
        for child in self.children: child.disabled = True
        await i.message.edit(view=self)
        if aid:
            try:
                member = i.guild.get_member(aid) or await i.guild.fetch_member(aid)
                dm_e = discord.Embed(
                    title="🎉  Čestitamo — Primljeni si u Staff!",
                    description=(
                        f"## ✅ Tvoja prijava na **{i.guild.name}** je **PRIHVAĆENA**!\n\n"
                        f"Kontaktiraj administratora da dobiješ Staff ulogu.\n"
                        f"Dobrodošao/la u tim! 🤝🛡️"
                    ),
                    color=0x57F287,
                    timestamp=datetime.now(timezone.utc),
                )
                dm_e.set_footer(text=f"📋 {i.guild.name}  •  GIAN Bot")
                await member.send(embed=dm_e)
            except Exception:
                pass
        await i.response.send_message(
            embed=em("✅ Prijava prihvaćena!",
                     "Kandidat je obaviješten putem DM-a.\n"
                     "⚠️ **Ulogu dodijeli ručno** — bot ne daje nikakve permisije automatski!\n"
                     "🗑️ Kanal se briše za **10 sekundi**.",
                     color=COLORS["success"]),
            ephemeral=True,
        )
        asyncio.create_task(self._auto_close_channel(i.channel, delay=10))

    @discord.ui.button(label="Odbij", emoji="❌", style=discord.ButtonStyle.danger, custom_id="sv_odbij")
    async def odbij(self, i: discord.Interaction, b: discord.ui.Button):
        if not i.user.guild_permissions.manage_roles:
            return await i.response.send_message(
                embed=em("❌ Nemaš permisiju!", "Samo Staff/Admini mogu glasati.", color=COLORS["error"]),
                ephemeral=True,
            )
        aid = self._extract_aid(i.message)
        for child in self.children: child.disabled = True
        await i.message.edit(view=self)
        if aid:
            try:
                member = i.guild.get_member(aid) or await i.guild.fetch_member(aid)
                dm_e = discord.Embed(
                    title="📋  Staff Prijava — Odgovor",
                    description=(
                        f"## ❌ Nažalost, tvoja prijava na **{i.guild.name}** je **ODBIJENA**.\n\n"
                        f"Možeš pokušati ponovo za **30 dana**.\n"
                        f"Ne odustaji — nastavite biti aktivni! 💪"
                    ),
                    color=0xED4245,
                    timestamp=datetime.now(timezone.utc),
                )
                dm_e.set_footer(text=f"📋 {i.guild.name}  •  GIAN Bot")
                await member.send(embed=dm_e)
            except Exception:
                pass
        await i.response.send_message(
            embed=em("❌ Prijava odbijena.",
                     "Kandidat je obaviješten putem DM-a.\n"
                     "🗑️ Kanal se briše za **10 sekundi**.",
                     color=COLORS["error"]),
            ephemeral=True,
        )
        asyncio.create_task(self._auto_close_channel(i.channel, delay=10))

    @discord.ui.button(label="Na čekanju", emoji="⏳", style=discord.ButtonStyle.secondary, custom_id="sv_cekanje")
    async def na_cekanju(self, i: discord.Interaction, b: discord.ui.Button):
        if not i.user.guild_permissions.manage_roles:
            return await i.response.send_message(
                embed=em("❌ Nemaš permisiju!", "Samo Staff/Admini mogu glasati.", color=COLORS["error"]),
                ephemeral=True,
            )
        await i.response.send_message(
            embed=em("⏳ Na čekanju!",
                     "Prijava je stavljena na čekanje za daljnju diskusiju.\n"
                     "💬 Razgovarajte u ovom kanalu i onda glasajte!",
                     color=COLORS["warning"]),
            ephemeral=True,
        )


# ═══════════════════════════════════════════
#    📋 STAFF PRIJAVA PANEL — /tiketstaff
#    Postavlja PUBLIČNU panel poruku u kanal (vidi je svako).
#    Ispod je 5 dugmadi (rubrika) — klikom član popunjava polje za polje,
#    ili klikom na "📋 Prijavi se" odmah otvara modal sa svih 5 polja.
# ═══════════════════════════════════════════
def _staff_draft_store():
    if "staff_draft" not in data: data["staff_draft"] = {}
    return data["staff_draft"]

def _staff_draft(guild_id: int, user_id: int) -> dict:
    s = _staff_draft_store()
    k = f"{guild_id}:{user_id}"
    if k not in s: s[k] = {}
    return s[k]

class _OnePoljeModal(discord.ui.Modal):
    def __init__(self, polje_kljuc: str, polje_label: str, placeholder: str, paragraph: bool = False):
        super().__init__(title=f"📋 {polje_label}"[:45])
        self.polje_kljuc = polje_kljuc
        self.tekst = discord.ui.TextInput(
            label=polje_label[:45],
            placeholder=placeholder[:100],
            style=discord.TextStyle.paragraph if paragraph else discord.TextStyle.short,
            min_length=1, max_length=600 if paragraph else 200,
        )
        self.add_item(self.tekst)

    async def on_submit(self, i: discord.Interaction):
        d = _staff_draft(i.guild.id, i.user.id)
        d[self.polje_kljuc] = str(self.tekst.value)
        save_data()
        popunjeno = sum(1 for k in ("god","iskustvo","zasto","igraci","aktivnost") if d.get(k))
        await i.response.send_message(
            embed=em("✅ Sačuvano",
                     f"Polje **{self.polje_kljuc}** sačuvano.\n"
                     f"Popunjeno: **{popunjeno}/5**\n\n"
                     f"Kad popuniš sve, klikni dugme **📤 Pošalji prijavu**.",
                     color=COLORS["success"]),
            ephemeral=True,
        )

class TiketStaffPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔢 Godine", style=discord.ButtonStyle.secondary, custom_id="ts_god", row=0)
    async def b_god(self, i, b):
        await i.response.send_modal(_OnePoljeModal("god", "Koliko imaš godina?", "Npr: 18"))

    @discord.ui.button(label="🛡️ Iskustvo", style=discord.ButtonStyle.secondary, custom_id="ts_isk", row=0)
    async def b_isk(self, i, b):
        await i.response.send_modal(_OnePoljeModal("iskustvo", "Imaš li iskustva kao mod/staff?",
                                                  "Opiši prethodno iskustvo na Discordu...", paragraph=True))

    @discord.ui.button(label="💭 Motivacija", style=discord.ButtonStyle.secondary, custom_id="ts_mot", row=0)
    async def b_mot(self, i, b):
        await i.response.send_modal(_OnePoljeModal("zasto", "Zašto želiš biti staff?",
                                                  "Reci nam šta te motiviše...", paragraph=True))

    @discord.ui.button(label="👥 Igrači", style=discord.ButtonStyle.secondary, custom_id="ts_igr", row=1)
    async def b_igr(self, i, b):
        await i.response.send_modal(_OnePoljeModal("igraci", "Koliko igrača možeš dovesti?",
                                                  "Npr: 5-10, imam zajednicu...", paragraph=True))

    @discord.ui.button(label="⏰ Aktivnost", style=discord.ButtonStyle.secondary, custom_id="ts_akt", row=1)
    async def b_akt(self, i, b):
        await i.response.send_modal(_OnePoljeModal("aktivnost", "Sati dnevno + timezone",
                                                  "Npr: 3-5 sati, CET..."))

    @discord.ui.button(label="📤 Pošalji prijavu", style=discord.ButtonStyle.success, custom_id="ts_send", row=2)
    async def b_send(self, i: discord.Interaction, b):
        d = _staff_draft(i.guild.id, i.user.id)
        nedostaje = [k for k in ("god","iskustvo","zasto","igraci","aktivnost") if not d.get(k)]
        if nedostaje:
            return await i.response.send_message(
                embed=em("⚠️ Nedostaju polja",
                         "Popuni sva polja prije slanja:\n• " + ", ".join(nedostaje),
                         color=COLORS["warning"]),
                ephemeral=True,
            )
        # Provjeri reklamu u poljima
        spojeno = " ".join(d.values())
        if INVITE_REGEX.search(spojeno):
            return await i.response.send_message(
                embed=em("🚫 Reklama zabranjena",
                         "Discord invite linkovi (`discord.gg/...`, `.gg/...`) nisu dozvoljeni u prijavi!",
                         color=COLORS["error"]),
                ephemeral=True,
            )
        # Pošalji kroz isti tok kao stari modal
        fake_modal = StaffApplicationModal()
        # Override vrijednosti
        fake_modal.god._value      = d.get("god", "")
        fake_modal.iskustvo._value = d.get("iskustvo", "")
        fake_modal.zasto._value    = d.get("zasto", "")
        fake_modal.igraci._value   = d.get("igraci", "")
        fake_modal.aktivnost._value = d.get("aktivnost", "")
        await fake_modal.on_submit(i)
        # Obriši draft nakon uspješnog slanja
        try:
            _staff_draft_store().pop(f"{i.guild.id}:{i.user.id}", None)
            save_data()
        except: pass

    @discord.ui.button(label="🗑️ Resetuj polja", style=discord.ButtonStyle.danger, custom_id="ts_reset", row=2)
    async def b_reset(self, i, b):
        try:
            _staff_draft_store().pop(f"{i.guild.id}:{i.user.id}", None)
            save_data()
        except: pass
        await i.response.send_message(
            embed=em("🗑️ Resetovano", "Tvoja polja su obrisana.", color=COLORS["info"]),
            ephemeral=True,
        )


@bot.command(name="tiketstaff")
async def tiketstaff_cmd(ctx: commands.Context):
    if not ctx.author.guild_permissions.administrator and ctx.author.id not in OWNER_IDS:
        return await ctx.send(embed=em("❌ Nemaš pristup", "Samo admin može postaviti panel.", color=COLORS["error"]))
    BAR = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    e = discord.Embed(
        title="📋  STAFF PRIJAVA",
        description=(
            f"{BAR}\n"
            f"Otvorene su prijave za **Staff tim** servera **{ctx.guild.name}**!\n\n"
            f"📝 **Kako se prijaviti:**\n"
            f"1️⃣  Klikni redom na **5 dugmadi** ispod i upiši svoje podatke\n"
            f"2️⃣  Kad popuniš **sva polja**, klikni **📤 Pošalji prijavu**\n"
            f"3️⃣  Bot će ti otvoriti **privatni kanal** sa staff timom\n\n"
            f"🔒 Tvoji odgovori se vide samo tebi dok ne pošalješ prijavu.\n"
            f"🚫 **Discord invite linkovi nisu dozvoljeni** u poljima!\n"
            f"{BAR}"
        ),
        color=0xF1C40F, timestamp=datetime.now(timezone.utc),
    )
    e.add_field(name="📌 Rubrike", value=(
        "🔢 **Godine** — koliko imaš godina\n"
        "🛡️ **Iskustvo** — prethodno iskustvo\n"
        "💭 **Motivacija** — zašto želiš staff\n"
        "👥 **Igrači** — koliko ljudi možeš dovesti\n"
        "⏰ **Aktivnost** — sati dnevno + timezone"
    ), inline=False)
    if ctx.guild.icon:
        e.set_thumbnail(url=ctx.guild.icon.url)
    e.set_footer(text=f"📋 {BOT_NAME} • Staff Prijava")
    try:
        await ctx.send(embed=e, view=TiketStaffPanelView())
    except discord.Forbidden:
        await ctx.send(embed=em("❌ Permisija", "Bot nema dozvolu da piše u ovaj kanal!", color=COLORS["error"]))

# ═══════════════════════════════════════════
#    /INFO — Server info embed (owner only)
# ═══════════════════════════════════════════
@bot.command(name="info")
async def info_cmd(ctx: commands.Context):
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send(embed=em("❌ Nemaš pristup", "Ova komanda je dostupna samo vlasniku bota.", color=COLORS["error"]))

    BAR  = "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"
    LINE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    e = discord.Embed(
        title="🎮 ✦ GIAN (Custom) — Komande ✦ 🎮",
        description=(
            f"```fix\n💻 Kompjuter: /komanda   📱 Mobitel: .komanda```\n"
            f"{LINE}"
        ),
        color=COLORS["default"],
        timestamp=datetime.now(timezone.utc),
    )

    e.add_field(name="🌍 ═╡ B A L K A N  D U H ╞═ 🌍", value=(
        "> *Ovde nije važno odakle si, već kakav si.*\n"
        "> *Donesi smijeh, donesi kafu, donesi sebe.*\n"
        "> 🏠 *Dobrodošao u GIAN — gdje svaka noć ima priču.*"
    ), inline=False)

    e.add_field(name=f"{BAR}\n🕹️ ═╡ K L A S I Č N E  I G R E ╞═ 🕹️", value=(
        "🪨 `/kpm` `.kpm` — Kamen, Papir, Makaze\n"
        "🎰 `/slots [ulog]` `.slots [ulog]` — Slot mašina (20–1.000.000.000 💶)\n"
        "🔫 `/rulet` `.rulet` — Ruski rulet, za hrabre!\n"
        "🃏 `/blackjack` `.blackjack` — Blackjack protiv dilera\n"
        "🎲 `/kocka` `.kocka` — Baci kocku protiv nekog igrača"
    ), inline=False)

    e.add_field(name=f"{BAR}\n🧠 ═╡ T R I V I A  &  Z N A N J E ╞═ 🧠", value=(
        "❓ `/kviz` `.kviz` — Balkan kviz, sa combo multiplierom!\n"
        "🌐 `/geografija` `.geografija` — Geografski kviz sa combo sistemom"
    ), inline=False)

    e.add_field(name=f"{BAR}\n📝 ═╡ R I J E Č I  &  L O G I K A ╞═ 📝", value=(
        "🪢 `/vjasala` `.vjasala` — Vješala, pogodi skrivenu riječ\n"
        "🔗 `/kaladont` `.kaladont` — Ulančavanje riječi (kao Activity)\n"
        "🛑 `/kaladont-stop` `.kaladont-stop` — Zaustavi Kaladont igru\n"
        "🌡️ `/toplo-hladno` `.toplo-hladno` — Pogodi tajni broj"
    ), inline=False)

    e.add_field(name=f"{BAR}\n👥 ═╡ M U L T I P L A Y E R ╞═ 👥", value=(
        "📯 `/amogus` `.amogus` — Pokreni Among Us igru u kanalu\n"
        "🚫 `/amogus-stop` `.amogus-stop` — Zaustavi Among Us igru"
    ), inline=False)

    e.add_field(name=f"{BAR}\n🔢 ═╡ B R O J A N J E ╞═ 🔢", value=(
        "⚙️ `/brojanje-postavi` `.brojanje-postavi` — Postavi kanal *(ADMIN)*\n"
        "📊 `/brojanje-info` `.brojanje-info` — Pokaži trenutno stanje\n"
        "🔄 `/brojanje-reset` `.brojanje-reset` — Resetuj brojanje *(ADMIN)*"
    ), inline=False)

    e.add_field(name=f"{BAR}\n💞 ═╡ S O C I J A L N E  &  L J U B A V N E ╞═ 💞", value=(
        "🤗 `/zagrljaj` `.zagrljaj` — Zagrli nekog\n"
        "💋 `/poljubac` `.poljubac` — Pošalji poljubac\n"
        "🥰 `/mazi` `.mazi` — Pomazi nekog nježno\n"
        "👋 `/tapsi` `.tapsi` — Tapši nekog prijateljski\n"
        "🙏 `/high5` `.high5` — Daj peticu\n"
        "❤️ `/srce` `.srce` — Pošalji srce nekome\n"
        "💍 `/brak` `.brak` — Zaprosi nekog *(za fun)*\n"
        "🌸 `/kompli` `.kompli` — Slatki kompliment\n"
        "😳 `/crush` `.crush` — Otkrij ko je tvoj tajni crush\n"
        "😵 `/cudan` `.cudan` — Razne reakcije"
    ), inline=False)

    e.add_field(name=f"{BAR}\n🇧🇦 ═╡ B A L K A N  S T I L ╞═ 🇧🇦", value=(
        "👋 `/pozz` `.pozz` — Pozdrav sa humorom\n"
        "😄 `/fora` `.fora` — Ubaci foru na nečiji račun\n"
        "😏 `/muv` `.muv` — Muvaj nekog Balkan stilom"
    ), inline=False)

    e.add_field(name=f"{BAR}\n🦁 ═╡ O W O  H U N T I N G ╞═ 🦁", value=(
        "🏹 `/hunt` `.hunt` — Lovi divlje životinje\n"
        "🦒 `/zoo` `.zoo` — Pogledaj svoju zbirku\n"
        "⚔️ `/battle` `.battle` — Bori se sa drugim igračem\n"
        "💰 `/sell` `.sell` — Prodaj životinje za pare\n"
        "📋 `/animals` `.animals` — Lista svih životinja i raritet\n"
        "🙏 `/pray` `.pray` — Pomoli se za nekog *(boost sreće)*"
    ), inline=False)

    e.add_field(name=f"{BAR}\n💵 ═╡ E K O N O M I J A  &  X P ╞═ 💵", value=(
        "👛 `/baki` `.baki` — Provjeri stanje novca\n"
        "🔨 `/posao` `.posao` — Radi i zaradi *(svaki sat)*\n"
        "🎁 `/daily` `.daily` — Dnevna nagrada\n"
        "📤 `/daj` `.daj` — Pošalji pare drugaru\n"
        "🥷 `/kradi` `.kradi` — Pokušaj ukrasti pare *(rizično!)*\n"
        "📈 `/rank` `.rank` — Tvoj level i XP profil\n"
        "🏆 `/leaderboard` `.leaderboard` — Top lista servera\n"
        "🛒 `/shop` `.shop` — Pogledaj šta možeš kupiti\n"
        "💳 `/kupi` `.kupi` — Kupi predmet iz shopa\n"
        "📜 `/quests` `.quests` — Tvoji dnevni zadaci"
    ), inline=False)

    e.add_field(name=LINE, value="✨ *Uživaj i budi dio ekipe!* ✨", inline=False)

    if ctx.guild and ctx.guild.icon:
        e.set_thumbnail(url=ctx.guild.icon.url)
    e.set_footer(text="🎮 GIAN (Custom) • Komande", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)

    try:
        await ctx.send(embed=e)
    except discord.Forbidden:
        await ctx.send(embed=em("❌ Permisija", "Bot nema dozvolu da piše u ovaj kanal!", color=COLORS["error"]))


# ═══════════════════════════════════════════
#    .pravila — Pravilnik servera (owner only)
# ═══════════════════════════════════════════
@bot.command(name="pravila")
async def pravila_cmd(ctx: commands.Context):
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send(embed=em("❌ Nemaš pristup", "Ova komanda je dostupna samo vlasniku bota.", color=COLORS["error"]))

    e = discord.Embed(
        title="📜  P R A V I L N I K  S E R V E R A",
        description=(
            "Dobrodošli na **GIAN** zajednicu!\n"
            "Molimo pročitajte i poštujte sljedeća pravila."
        ),
        color=COLORS["default"],
        timestamp=datetime.now(timezone.utc),
    )

    e.add_field(name="🤝  Poštovanje članova", value=(
        "🚫 Zabranjeno vrijeđanje, maltretiranje i provociranje\n"
        "❌ Nema rasizma, diskriminacije ni govora mržnje\n"
        "💬 Poštuj tuđe mišljenje čak i kad se ne slažeš"
    ), inline=False)

    e.add_field(name="🔇  Bez spama", value=(
        "🔁 Ne šalji iste poruke više puta\n"
        "😶 Ne spamuj emojima, gifovima ni tagovanjem\n"
        "🌊 Flood poruke nisu dozvoljene"
    ), inline=False)

    e.add_field(name="📢  Reklamiranje", value=(
        "🔗 Zabranjena reklama servera i mreža bez odobrenja admina\n"
        "📩 Zabranjeno slanje reklama u DM porukama"
    ), inline=False)

    e.add_field(name="🔞  Neprikladan sadržaj", value=(
        "🩸 Nema nasilnih, šokantnih ni uznemirujućih slika\n"
        "🚫 NSFW sadržaj je zabranjen na cijelom serveru\n"
        "📋 Poštuj pravila Discord platforme i TOS"
    ), inline=False)

    e.add_field(name="📁  Kanali", value=(
        "🎯 Koristi kanale za njihovu predviđenu svrhu\n"
        "🤖 Komande za bota koristi u za to određenim kanalima"
    ), inline=False)

    e.add_field(name="🛡️  Staff & Drama", value=(
        "👮 Odluke admina i moderatora su konačne\n"
        "🎫 Za probleme koristi ticket sistem\n"
        "🕊️ Sporove rješavaj mirno — bez javnih svađa"
    ), inline=False)

    e.add_field(name="⚠️  Kazne", value=(
        "`1.` ⚠️ Upozorenje  `2.` 🔇 Mute  `3.` 👢 Kick  `4.` 🔨 Ban"
    ), inline=False)

    e.add_field(name="✨  Uživaj i budi dio ekipe!", value=(
        "Pravila postoje da bi se **svi** osjećali dobrodošlo.\n"
        "Poštuj druge, čuvaj atmosferu — **dobrodošao kući** 🏠"
    ), inline=False)

    if ctx.guild and ctx.guild.icon:
        e.set_thumbnail(url=ctx.guild.icon.url)
    e.set_footer(text="📜 GIAN • Pravilnik", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)

    try:
        await ctx.send(embed=e)
    except discord.Forbidden:
        await ctx.send(embed=em("❌ Permisija", "Bot nema dozvolu da piše u ovaj kanal!", color=COLORS["error"]))


# ─── 🔊 PRAVILA VOICE (privatni voice kanali) ───
# ─── Panel Role Button — daje/uzima ulogu na klik ───────────────────────────
@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Hvataj panel_role_{roleId} dugmad poslana iz GIAN panela."""
    if interaction.type != discord.InteractionType.component:
        return
    custom_id = (interaction.data or {}).get("custom_id", "")
    if not custom_id.startswith("panel_role_"):
        return
    parts = custom_id.split("_")
    if len(parts) < 3:
        return await interaction.response.send_message("❌ Nevalidan ID dugmeta.", ephemeral=True)
    try:
        role_id = int(parts[2])
    except ValueError:
        return await interaction.response.send_message("❌ Nevalidan ID uloge.", ephemeral=True)

    guild  = interaction.guild
    member = interaction.user
    if not guild or not isinstance(member, discord.Member):
        return await interaction.response.send_message("❌ Greška — pokušaj na serveru.", ephemeral=True)

    role = guild.get_role(role_id)
    if not role:
        return await interaction.response.send_message("❌ Uloga ne postoji!", ephemeral=True)
    if role >= guild.me.top_role:
        return await interaction.response.send_message(
            f"❌ Ne mogu dodijeliti **{role.name}** — uloga je viša od moje. Admin: pomjeri me iznad nje.",
            ephemeral=True,
        )

    try:
        if role in member.roles:
            await member.remove_roles(role, reason="Panel role button — uklanjanje")
            await interaction.response.send_message(
                f"✅ Uloga **{role.name}** je uklonjena.", ephemeral=True
            )
        else:
            await member.add_roles(role, reason="Panel role button — dodavanje")
            await interaction.response.send_message(
                f"✅ Dobio si ulogu **{role.name}**!", ephemeral=True
            )
    except discord.Forbidden:
        await interaction.response.send_message("❌ Bot nema permisiju za upravljanje ulogama.", ephemeral=True)
    except Exception as ex:
        await interaction.response.send_message(f"❌ Greška: `{ex}`", ephemeral=True)


class VoiceCreateButton(discord.ui.View):
    """Dugme ispod /pravila-voice — kreira privatni VC na klik."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔊 Kreiraj svoj voice", style=discord.ButtonStyle.success, custom_id="vc_create_btn")
    async def create(self, i: discord.Interaction, b):
        guild = i.guild
        member = i.user
        # Ako već ima privatni VC, javi
        for ch_id_str, owner_id in data.get("private_voices", {}).items():
            if owner_id == member.id:
                ch = guild.get_channel(int(ch_id_str)) if guild else None
                if ch:
                    return await i.response.send_message(
                        embed=em("⚠️ Već imaš kanal", f"Tvoj voice: {ch.mention}\nUđi i koristi panel za upravljanje.", color=COLORS["warning"]),
                        ephemeral=True,
                    )
        await i.response.defer(ephemeral=True, thinking=True)
        # Kategorija = ista kao JTC voice ili kao text kanal
        jtc = guild.get_channel(JTC_VOICE_ID) if guild else None
        cat = (jtc.category if jtc else None) or i.channel.category
        me = guild.me
        missing = []
        if not me.guild_permissions.manage_channels: missing.append("Manage Channels")
        if not me.guild_permissions.move_members:    missing.append("Move Members")
        if missing:
            return await i.followup.send(
                embed=em("❌ Nedostaju permisije", f"Botu treba: **{', '.join(missing)}**", color=COLORS["error"]),
                ephemeral=True,
            )
        try:
            new_ch = None
            try:
                new_ch = await guild.create_voice_channel(
                    name=f"🔊 {member.display_name}",
                    category=cat,
                    reason=f"Privatni VC (dugme) za {member}"
                )
            except discord.HTTPException as he:
                if he.code == 30013 or "Maximum number" in str(he):
                    new_ch = await guild.create_voice_channel(
                        name=f"🔊 {member.display_name}",
                        reason=f"Privatni VC (dugme, bez kategorije) za {member}"
                    )
                else:
                    raise
            await new_ch.set_permissions(member, manage_channels=True, move_members=True,
                mute_members=True, deafen_members=True, connect=True, view_channel=True)
            data.setdefault("private_voices", {})[str(new_ch.id)] = member.id
            save_data()
            # Ako je već u nekom voice-u, prebaci ga
            try:
                if member.voice and member.voice.channel:
                    await member.move_to(new_ch)
            except: pass
            # Pošalji panel u sam voice kanal
            try:
                ev = discord.Embed(
                    title=f"🔊 Dobrodošao u svoj kanal, {member.display_name}!",
                    description=(
                        "**Ti si vlasnik!** 👑 Koristi dugmad ispod:\n\n"
                        "🔒 **Lock / Unlock** — kontrola ulaza\n"
                        "👁️ **Hide / Show** — sakrij/pokaži\n"
                        "✏️ **Rename** • 👥 **Limit** • 🚫 **Kick**\n"
                        "👑 **Owner transfer** • ❌ **Delete**\n\n"
                        "*Kanal se automatski briše kad ostane prazan.*"
                    ),
                    color=COLORS.get("balkan", 0x9B59B6)
                )
                ev.set_footer(text=f"{BOT_NAME} • Privatni Voice Sistem")
                await new_ch.send(content=member.mention, embed=ev, view=PrivateVCPanel())
            except Exception as _e: print(f"[vc-btn panel] {_e}")
            await i.followup.send(
                embed=em("✅ Voice kreiran!", f"Tvoj kanal: {new_ch.mention}\n👉 Klikni i pridruži se!", color=COLORS["success"]),
                ephemeral=True,
            )
            print(f"[vc-btn] ✓ {member} → {new_ch.name}")
        except Exception as ex:
            import traceback; traceback.print_exc()
            await i.followup.send(
                embed=em("❌ Greška", f"`{type(ex).__name__}: {ex}`", color=COLORS["error"]),
                ephemeral=True,
            )


@bot.command(name="pravila-voice")
async def pravila_voice_cmd(ctx: commands.Context):
    if ctx.author.id not in OWNER_IDS:
        return await ctx.send(embed=em("❌ Nemaš pristup", "Ova komanda je dostupna samo vlasniku bota.", color=COLORS["error"]))

    # ── Fetch embed config from panel (fallback to hardcoded) ──
    _pv = await get_panel_embed("voice-pravila")

    if _pv:
        _vc = int((_pv.get("color") or "#2B2D3A").lstrip("#") or "2B2D3A", 16)
        e = discord.Embed(
            title=_pv.get("title") or "🔊  P R I V A T N I  V O I C E  K A N A L I",
            description=_pv.get("description") or "",
            color=_vc,
            timestamp=datetime.now(timezone.utc),
        )
        for f in (_pv.get("fields") or []):
            e.add_field(name=f.get("name", ""), value=f.get("value", ""), inline=bool(f.get("inline", True)))
        if _pv.get("footer"):
            e.set_footer(text=_pv["footer"], icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
        else:
            e.set_footer(text="🔊 GIAN • Voice Pravila", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)
    else:
        e = discord.Embed(
            title="🔊  P R I V A T N I  V O I C E  K A N A L I",
            description=(
                f"Uđi u <#{JTC_VOICE_ID}> i bot ti **automatski** kreira vlastiti voice kanal.\n"
                "Postaješ **vlasnik** 👑 i dobijaš puni kontrolni panel."
            ),
            color=COLORS["default"],
            timestamp=datetime.now(timezone.utc),
        )
        e.add_field(name="🤝  Ponašanje", value=(
            "🚫 Bez vrijeđanja, maltretiranja i rasizma\n"
            "🎙️ Ne prekidaj druge dok pričaju\n"
            "🔇 Ne lupaj mikrofonom bez razloga"
        ), inline=True)
        e.add_field(name="👑  Vlasništvo", value=(
            "🎛️ Samo vlasnik koristi Lock / Hide / Kick panel\n"
            "🔁 Prebaci vlasništvo prije izlaska\n"
            "⚖️ Ne koristi panel za maltretiranje"
        ), inline=True)
        e.add_field(name="🔞  Sadržaj & Imena", value=(
            "🚫 Bez NSFW sadržaja i streaminga\n"
            "✏️ Ime kanala mora biti pristojno\n"
            "📋 Vrijede sva opšta pravila servera"
        ), inline=True)
        e.add_field(name="🗑️  Automatsko brisanje", value=(
            "Kad svi izađu, bot **automatski briše** kanal.\n"
            "👮 Staff ima pristup svim kanalima zbog moderacije."
        ), inline=False)
        e.add_field(name="⚠️  Kazne", value=(
            "`1.` ⚠️ Upozorenje  `2.` 🔇 Voice mute  `3.` 🚫 Zabrana voice-a  `4.` 👢 Kick / 🔨 Ban"
        ), inline=False)
        e.set_footer(text="🔊 GIAN • Voice Pravila", icon_url=ctx.guild.icon.url if ctx.guild and ctx.guild.icon else None)

    if ctx.guild and ctx.guild.icon:
        e.set_thumbnail(url=ctx.guild.icon.url)

    # ── Build view — optionally use panel button label ──
    view = VoiceCreateButton()
    if _pv:
        _btns = _pv.get("buttons") or []
        if _btns and view.children:
            _bc = _btns[0]
            view.children[0].label = _bc.get("label", "🔊 Kreiraj svoj voice")

    try:
        await ctx.send(embed=e, view=view)
    except discord.Forbidden:
        await ctx.send(embed=em("❌ Permisija", "Bot nema dozvolu da piše u ovaj kanal!", color=COLORS["error"]))


# ─── 🔄 SYNC — manualno ponovno učitavanje slash komandi ───
@bot.tree.command(name="sync", description="🔄 Force-sync svih slash komandi (samo vlasnik)")
@app_commands.describe(scope="global = svi serveri (~1h cache), guild = ovaj server (odmah)")
@app_commands.choices(scope=[
    app_commands.Choice(name="guild (samo ovaj server, odmah)", value="guild"),
    app_commands.Choice(name="global (svi serveri, do 1h cache)", value="global"),
    app_commands.Choice(name="both (oba)", value="both"),
])
async def sync_cmd(i: discord.Interaction, scope: app_commands.Choice[str] = None):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("❌ Nemaš pristup", "Ova komanda je dostupna samo vlasniku bota.", color=COLORS["error"]),
            ephemeral=True,
        )
    await i.response.defer(ephemeral=True)
    sc = scope.value if scope else "both"
    results = []
    # GUILD sync (instant)
    if sc in ("guild", "both") and i.guild:
        try:
            bot.tree.copy_global_to(guild=i.guild)
            synced = await bot.tree.sync(guild=i.guild)
            results.append(f"✅ **Guild sync ({i.guild.name}):** {len(synced)} komandi (odmah dostupne)")
        except Exception as e:
            results.append(f"❌ **Guild sync error:** `{e}`")
    # GLOBAL sync (cached)
    if sc in ("global", "both"):
        try:
            synced = await bot.tree.sync()
            data["_last_synced_count"] = len(synced)
            save_data()
            results.append(f"✅ **Global sync:** {len(synced)} komandi (cache do 1h)")
        except Exception as e:
            results.append(f"❌ **Global sync error:** `{e}`")
    e = discord.Embed(
        title="🔄 Sync rezultati",
        description="\n".join(results) if results else "Ništa nije sinhronizovano.",
        color=COLORS["success"],
        timestamp=datetime.now(timezone.utc),
    )
    e.set_footer(text=f"{BOT_NAME} • Force Sync")
    await i.followup.send(embed=e, ephemeral=True)


# ═══════════════════════════════════════════
#    🎭 MAFIA IGRA — sve sa embedima i klikabilnim dugmadima
#    /mafia       — pokreni novu igru u kanalu (lobby)
#    Igra ima 4–12 igrača, uloge: Civil / Mafia / Doktor / Detektiv
#    Faze: 🌙 Noć (DM komande) → ☀️ Dan (rasprava) → 🗳️ Glasanje
# ═══════════════════════════════════════════
MAFIA_GAMES: dict[int, "MafiaGame"] = {}   # channel_id -> game

class MafiaGame:
    def __init__(self, channel: discord.TextChannel, host: discord.Member):
        self.channel  = channel
        self.host     = host
        self.players: list[discord.Member] = [host]
        self.alive:   set[int]             = set()
        self.roles:   dict[int, str]       = {}   # uid -> role
        self.actions: dict[str, int]       = {}   # "mafia_kill"/"doc_heal"/"det_check" -> uid
        self.vote_msgs: dict[int, int]     = {}   # voter -> target
        self.day      = 0
        self.phase    = "lobby"   # lobby/night/day/vote/over
        self.lock     = asyncio.Lock()
        self.task: asyncio.Task | None = None

    def alive_players(self) -> list[discord.Member]:
        return [p for p in self.players if p.id in self.alive]

    def role_of(self, uid: int) -> str:
        return self.roles.get(uid, "civil")

    def alive_with_role(self, role: str) -> list[discord.Member]:
        return [p for p in self.alive_players() if self.role_of(p.id) == role]

    def winner(self) -> str | None:
        mafia = len(self.alive_with_role("mafia"))
        rest  = len(self.alive_players()) - mafia
        if mafia == 0:                return "civili"
        if mafia >= rest:             return "mafia"
        return None

    def assign_roles(self):
        n = len(self.players)
        ids = [p.id for p in self.players]
        random.shuffle(ids)
        n_mafia = 1 if n <= 6 else 2 if n <= 10 else 3
        # Specijalne uloge se dodaju kako raste broj igrača
        specials = ["doktor", "detektiv"]
        if n >= 6: specials.append("serif")        # 👮 Šerif (1 hitac noću)
        if n >= 8: specials.append("saljivdzija")  # 🃏 Šaljivdžija (pobjeđuje ako ga linčuju)
        n_civil = max(0, n - n_mafia - len(specials))
        roles = (["mafia"] * n_mafia + specials + ["civil"] * n_civil)[:n]
        random.shuffle(roles)
        self.roles = dict(zip(ids, roles))
        self.alive = set(ids)
        # Šerif ima samo 1 hitac u igri
        self.serif_shots: dict[int, int] = {uid: 1 for uid, r in self.roles.items() if r == "serif"}
        self.jester_lynched: int | None  = None

ROLE_INFO = {
    "civil":        ("👨‍🌾 Civil",       "Tvoj cilj: otkrij i izglasaj mafiju!", COLORS["info"]),
    "mafia":        ("🔪 Mafia",         "Noću ubijaš jednog igrača. Cilj: pobij sve civile.", COLORS["error"]),
    "doktor":       ("🛡️ Doktor",       "Noću spašavaš jednog igrača (možeš i sebe — jednom).", COLORS["success"]),
    "detektiv":     ("🕵️ Detektiv",     "Noću provjeravaš identitet jednog igrača.", COLORS["purple"]),
    "serif":        ("👮 Šerif",         "Imaš **1 hitac** za cijelu igru. Pažljivo gađaj — pogodiš li civila, gubiš.", COLORS["gold"]),
    "saljivdzija":  ("🃏 Šaljivdžija",   "Tvoj cilj: budi izglasan na danu! Ako te linčuju — POBJEĐUJEŠ!", COLORS["pink"] if "pink" in COLORS else COLORS["purple"]),
}

# ── LOBBY VIEW ──
class MafiaLobbyView(discord.ui.View):
    def __init__(self, game: MafiaGame):
        super().__init__(timeout=600)
        self.game = game

    @discord.ui.button(label="Pridruži se", style=discord.ButtonStyle.success, emoji="✋")
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        g = self.game
        if g.phase != "lobby":
            return await i.response.send_message(
                embed=em("⚠️ Lobby zatvoren", "Igra je već počela.", color=COLORS["warning"]), ephemeral=True)
        if any(p.id == i.user.id for p in g.players):
            return await i.response.send_message(
                embed=em("⚠️", "Već si u lobby-ju.", color=COLORS["warning"]), ephemeral=True)
        if len(g.players) >= 12:
            return await i.response.send_message(
                embed=em("❌ Puna igra", "Maksimalno 12 igrača.", color=COLORS["error"]), ephemeral=True)
        g.players.append(i.user)
        await i.response.send_message(
            embed=em("✅ Ušao u igru", f"{i.user.mention} se pridružio Mafia igri!", color=COLORS["success"]),
            ephemeral=True,
        )
        await self.refresh_lobby_msg(i)

    @discord.ui.button(label="Napusti", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave(self, i: discord.Interaction, b: discord.ui.Button):
        g = self.game
        if g.phase != "lobby":
            return await i.response.send_message(
                embed=em("⚠️", "Igra je već počela — ne možeš izaći.", color=COLORS["warning"]), ephemeral=True)
        if i.user.id == g.host.id:
            return await i.response.send_message(
                embed=em("⚠️", "Domaćin ne može izaći. Otkaži igru dugmetom **Otkaži**.", color=COLORS["warning"]), ephemeral=True)
        g.players = [p for p in g.players if p.id != i.user.id]
        await i.response.send_message(
            embed=em("👋", f"{i.user.mention} je napustio igru.", color=COLORS["info"]), ephemeral=True)
        await self.refresh_lobby_msg(i)

    @discord.ui.button(label="POKRENI", style=discord.ButtonStyle.primary, emoji="▶️", row=1)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        g = self.game
        if i.user.id != g.host.id:
            return await i.response.send_message(
                embed=em("❌", "Samo domaćin može pokrenuti.", color=COLORS["error"]), ephemeral=True)
        if len(g.players) < 4:
            return await i.response.send_message(
                embed=em("❌ Premalo igrača", "Trebaju **minimalno 4 igrača**.", color=COLORS["error"]), ephemeral=True)
        if g.phase != "lobby":
            return await i.response.send_message("⚠️ Već pokrenuto.", ephemeral=True)
        g.phase = "starting"
        for c in self.children: c.disabled = True
        await i.response.edit_message(view=self)
        await mafia_start_game(g, i)

    @discord.ui.button(label="Otkaži igru", style=discord.ButtonStyle.danger, emoji="🛑", row=1)
    async def cancel(self, i: discord.Interaction, b: discord.ui.Button):
        g = self.game
        if i.user.id != g.host.id:
            return await i.response.send_message(
                embed=em("❌", "Samo domaćin može otkazati.", color=COLORS["error"]), ephemeral=True)
        g.phase = "over"
        MAFIA_GAMES.pop(g.channel.id, None)
        for c in self.children: c.disabled = True
        await i.response.edit_message(
            embed=em("🛑 Igra otkazana", "Domaćin je otkazao Mafia igru.", color=COLORS["error"]),
            view=self,
        )

    async def refresh_lobby_msg(self, i: discord.Interaction):
        g = self.game
        try:
            await i.message.edit(embed=mafia_lobby_embed(g), view=self)
        except Exception: pass

def mafia_lobby_embed(g: MafiaGame) -> discord.Embed:
    lst = "\n".join(f"`{n+1}.` {p.mention}" for n, p in enumerate(g.players)) or "_prazno_"
    e = em(
        "🎭 MAFIA — Lobby",
        f"Domaćin: {g.host.mention}\nKlikni **Pridruži se** da uđeš u igru.\nKad bude **min. 4 igrača**, domaćin klikne **POKRENI**.",
        color=COLORS["balkan"],
        fields=[
            (f"👥 Igrači ({len(g.players)}/12)", lst, False),
            ("⏱️ Trajanje faze", "Noć **45s** • Dan **60s** • Glasanje **45s**", True),
            ("🎲 Uloge", "Civil • 🔪 Mafia • 🛡️ Doktor • 🕵️ Detektiv\n👮 Šerif (6+) • 🃏 Šaljivdžija (8+)", True),
        ],
    )
    e.set_footer(text=f"{BOT_NAME} • Mafia Online")
    return e

# ── ACTION VIEWS (target select za noćne uloge) ──
class MafiaTargetView(discord.ui.View):
    def __init__(self, game: MafiaGame, actor: discord.Member, action_key: str, label: str, allow_self: bool = False):
        super().__init__(timeout=40)
        self.game = game
        self.actor = actor
        self.action_key = action_key
        opts = []
        for p in game.alive_players():
            if not allow_self and p.id == actor.id: continue
            opts.append(discord.SelectOption(label=p.display_name[:80], value=str(p.id)))
        self.sel = discord.ui.Select(placeholder=label, options=opts[:25], min_values=1, max_values=1)
        self.sel.callback = self._cb
        self.add_item(self.sel)

    async def _cb(self, i: discord.Interaction):
        if i.user.id != self.actor.id:
            return await i.response.send_message(
                embed=em("❌", "Ovo nije tvoj odabir.", color=COLORS["error"]), ephemeral=True)
        tid = int(self.sel.values[0])
        self.game.actions[self.action_key] = tid
        target = self.game.channel.guild.get_member(tid)
        await i.response.edit_message(
            embed=em("✅ Akcija primljena",
                     f"Tvoj cilj: **{target.display_name if target else tid}**.\nSačekaj jutro.",
                     color=COLORS["success"]),
            view=None,
        )

# ── VOTE VIEW (u glavnom kanalu) ──
class MafiaVoteView(discord.ui.View):
    def __init__(self, game: MafiaGame):
        super().__init__(timeout=50)
        self.game = game
        opts = [discord.SelectOption(label=p.display_name[:80], value=str(p.id))
                for p in game.alive_players()]
        opts.append(discord.SelectOption(label="❌ Preskoči (nikoga)", value="skip"))
        self.sel = discord.ui.Select(placeholder="Glasaj koga linčovati…", options=opts[:25])
        self.sel.callback = self._cb
        self.add_item(self.sel)

    async def _cb(self, i: discord.Interaction):
        g = self.game
        if i.user.id not in g.alive:
            return await i.response.send_message(
                embed=em("❌", "Mrtvi i nedužni-spektatori ne glasaju.", color=COLORS["error"]), ephemeral=True)
        v = self.sel.values[0]
        g.vote_msgs[i.user.id] = 0 if v == "skip" else int(v)
        await i.response.send_message(
            embed=em("🗳️ Glas zabilježen", "Možeš promijeniti glas dok glasanje traje.", color=COLORS["success"]),
            ephemeral=True,
        )

# ── ENGINE ──
async def _safe_dm(member: discord.Member, **kw):
    try: return await member.send(**kw)
    except Exception: return None

async def mafia_start_game(g: MafiaGame, i: discord.Interaction):
    g.assign_roles()
    g.phase = "starting"
    # DM uloge
    for p in g.players:
        role = g.role_of(p.id)
        title, desc, color = ROLE_INFO[role]
        e = em(f"🎭 Tvoja uloga: {title}", desc, color=color, fields=[
            ("📍 Server", g.channel.guild.name, True),
            ("📺 Kanal igre", g.channel.mention, True),
        ])
        e.set_footer(text="🤫 NIKOM ne otkrivaj svoju ulogu!")
        await _safe_dm(p, embed=e)
    # Najava
    n = len(g.players)
    n_mafia = sum(1 for r in g.roles.values() if r == "mafia")
    await g.channel.send(embed=em(
        "🎭 MAFIA — POČETAK",
        f"**{n} igrača** ulazi u igru.\n🔪 Mafia: **{n_mafia}** • 🛡️ Doktor: **1** • 🕵️ Detektiv: **1**\n\n"
        "Provjerite **DM** — tamo je vaša uloga.",
        color=COLORS["balkan"],
    ))
    await asyncio.sleep(4)
    g.task = asyncio.create_task(mafia_loop(g))

async def mafia_loop(g: MafiaGame):
    try:
        while True:
            g.day += 1
            # ── NOĆ ──
            g.phase = "night"
            g.actions.clear()
            await g.channel.send(embed=em(
                f"🌙 NOĆ #{g.day}",
                "Selo spava… Mafia, Doktor i Detektiv djeluju u DM-u.\nImate **45 sekundi**.",
                color=COLORS["purple"],
            ))
            # Pošalji noćne akcije svim relevantnim igračima u DM
            mafias     = g.alive_with_role("mafia")
            doctors    = g.alive_with_role("doktor")
            detectives = g.alive_with_role("detektiv")
            sherifs    = g.alive_with_role("serif")
            for m in mafias:
                await _safe_dm(m,
                    embed=em("🔪 Mafia akcija", "Odaberi koga noćas ubijate:", color=COLORS["error"]),
                    view=MafiaTargetView(g, m, "mafia_kill", "Žrtva noći…", allow_self=False))
            for d in doctors:
                await _safe_dm(d,
                    embed=em("🛡️ Doktor akcija", "Koga noćas spašavaš?", color=COLORS["success"]),
                    view=MafiaTargetView(g, d, "doc_heal", "Spasi…", allow_self=True))
            for det in detectives:
                await _safe_dm(det,
                    embed=em("🕵️ Detektiv akcija", "Koga noćas provjeravaš?", color=COLORS["purple"]),
                    view=MafiaTargetView(g, det, "det_check", "Provjeri…", allow_self=False))
            for sh in sherifs:
                shots_left = getattr(g, "serif_shots", {}).get(sh.id, 0)
                if shots_left > 0:
                    await _safe_dm(sh,
                        embed=em("👮 Šerif akcija", f"Imaš **{shots_left} hitac**. Možeš pucati ili preskočiti (ne odabirati).\n⚠️ Ako pogodiš civila — **gubiš igru!**", color=COLORS["gold"]),
                        view=MafiaTargetView(g, sh, "serif_shot", "Pucaj na…", allow_self=False))
                else:
                    await _safe_dm(sh,
                        embed=em("👮 Šerif", "Već si potrošio svoj hitac — noćas miruješ.", color=COLORS["info"]))
            await asyncio.sleep(45)
            # Razrešenje noći
            killed_id  = g.actions.get("mafia_kill")
            healed_id  = g.actions.get("doc_heal")
            checked_id = g.actions.get("det_check")
            shot_id    = g.actions.get("serif_shot")
            if checked_id and detectives:
                target = g.channel.guild.get_member(checked_id)
                role   = g.role_of(checked_id)
                t_title, _, t_col = ROLE_INFO.get(role, ROLE_INFO["civil"])
                for det in detectives:
                    await _safe_dm(det, embed=em(
                        "🕵️ Rezultat istrage",
                        f"**{target.display_name if target else checked_id}** je: **{t_title}**",
                        color=t_col,
                    ))
            died = None
            if killed_id and killed_id != healed_id and killed_id in g.alive:
                g.alive.discard(killed_id)
                died = g.channel.guild.get_member(killed_id)
            # Šerif puca (ne može biti spašen od doktora)
            sherif_died = None
            sherif_kill_target = None
            if shot_id and sherifs and shot_id in g.alive:
                shooter = sherifs[0]
                if g.serif_shots.get(shooter.id, 0) > 0:
                    g.serif_shots[shooter.id] -= 1
                    target_role = g.role_of(shot_id)
                    if target_role == "civil":
                        # Šerif je pogodio civila — sam umire kao kazna
                        g.alive.discard(shooter.id)
                        sherif_died = shooter
                        sherif_kill_target = g.channel.guild.get_member(shot_id)
                        await _safe_dm(shooter, embed=em(
                            "💀 Šerif je promašio!",
                            f"Pucao si u **civila** — kazna je smrt!", color=COLORS["error"]))
                    else:
                        g.alive.discard(shot_id)
                        sherif_kill_target = g.channel.guild.get_member(shot_id)
                        await _safe_dm(shooter, embed=em(
                            "🎯 Pogodak!",
                            f"Eliminisao/la si **{sherif_kill_target.display_name if sherif_kill_target else shot_id}**!", color=COLORS["success"]))
            # Najava jutra
            morning_lines = []
            if died:
                morning_lines.append(f"💀 **{died.display_name}** je pronađen mrtav (mafija)!\nUloga: **{ROLE_INFO[g.role_of(died.id)][0]}**")
            elif killed_id and killed_id == healed_id:
                morning_lines.append("🛡️ Doktor je **spasio žrtvu** noćas!")
            if sherif_kill_target and not sherif_died:
                morning_lines.append(f"🎯 **{sherif_kill_target.display_name}** je upucan/a — Šerif je djelovao!\nUloga: **{ROLE_INFO[g.role_of(sherif_kill_target.id)][0]}**")
            if sherif_died:
                morning_lines.append(f"⚖️ **{sherif_died.display_name}** (Šerif) je pucao u civila i umro od kazne!")
            if not morning_lines:
                morning_lines.append("🌅 Selo je spavalo mirno — nema žrtava.")
            de = em(f"☀️ JUTRO #{g.day}", "\n\n".join(morning_lines),
                    color=COLORS["error"] if (died or sherif_kill_target or sherif_died) else COLORS["info"])
            de.add_field(name="📊 Stanje", value=f"👥 Živih: **{len(g.alive_players())}** / {len(g.players)}", inline=False)
            await g.channel.send(embed=de)
            # Pobjeda?
            w = g.winner()
            if w: return await mafia_end(g, w)
            # ── DAN — diskusija ──
            g.phase = "day"
            await g.channel.send(embed=em(
                "💬 DISKUSIJA",
                f"Imate **60 sekundi** da razgovarate prije glasanja.\nŽivi: {', '.join(p.mention for p in g.alive_players())}",
                color=COLORS["info"],
            ))
            await asyncio.sleep(60)
            # ── GLASANJE ──
            g.phase = "vote"
            g.vote_msgs.clear()
            view = MafiaVoteView(g)
            await g.channel.send(
                embed=em("🗳️ GLASANJE", "Svaki živi igrač bira metu (ili **Preskoči**). Imate **45s**.",
                         color=COLORS["warning"]),
                view=view,
            )
            await asyncio.sleep(45)
            for c in view.children: c.disabled = True
            # Prebroji
            tally: dict[int, int] = {}
            for v, t in g.vote_msgs.items():
                if v in g.alive:
                    tally[t] = tally.get(t, 0) + 1
            target_id, top = (None, 0)
            for tid, cnt in tally.items():
                if cnt > top:
                    target_id, top = tid, cnt
            if target_id and target_id != 0 and top > 0:
                victim = g.channel.guild.get_member(target_id)
                g.alive.discard(target_id)
                victim_role = g.role_of(target_id)
                await g.channel.send(embed=em(
                    "⚖️ PRESUDA",
                    f"💀 **{victim.display_name}** je linčovan glasanjem ({top} glasova).\nUloga: **{ROLE_INFO[victim_role][0]}**",
                    color=COLORS["error"],
                ))
                # Šaljivdžija pobjeđuje ako bude izglasan!
                if victim_role == "saljivdzija":
                    g.jester_lynched = target_id
                    return await mafia_end(g, "saljivdzija")
            else:
                await g.channel.send(embed=em(
                    "⚖️ PRESUDA", "Nema dovoljno glasova — niko nije linčovan.", color=COLORS["info"]))
            w = g.winner()
            if w: return await mafia_end(g, w)
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        await g.channel.send(embed=em("❌ Mafia greška", f"`{e}`", color=COLORS["error"]))
        MAFIA_GAMES.pop(g.channel.id, None)

async def mafia_end(g: MafiaGame, winner: str):
    g.phase = "over"
    if winner == "mafia":
        title, color = "🔪 MAFIA POBJEDJUJE!", COLORS["error"]
    elif winner == "civili":
        title, color = "👨‍🌾 CIVILI POBJEDJUJU!", COLORS["success"]
    elif winner == "saljivdzija":
        title, color = "🃏 ŠALJIVDŽIJA POBJEDJUJE!", COLORS["gold"]
    else:
        title, color = f"🏁 KRAJ — {winner}", COLORS["info"]
    revealed = "\n".join(f"{ROLE_INFO[g.role_of(p.id)][0]} — {p.mention}" for p in g.players)
    await g.channel.send(embed=em(
        title,
        f"**Igra završena u danu {g.day}.**\n\n__Otkrivene uloge:__\n{revealed}",
        color=color,
    ))
    MAFIA_GAMES.pop(g.channel.id, None)

@bot.tree.command(name="mafia", description="🎭 Pokreni Mafia igru u ovom kanalu")
async def mafia_cmd(i: discord.Interaction):
    if not isinstance(i.channel, discord.TextChannel):
        return await i.response.send_message(
            embed=em("❌", "Mafia se igra samo u tekstualnom kanalu.", color=COLORS["error"]),
            ephemeral=True,
        )
    ok, left = _check_game_cooldown(i.user, i.guild_id, "mafia")
    if not ok:
        return await _send_cooldown_msg(i, "mafia", left)
    if i.channel.id in MAFIA_GAMES and MAFIA_GAMES[i.channel.id].phase != "over":
        return await i.response.send_message(
            embed=em("⚠️ Već postoji igra",
                     "U ovom kanalu već traje Mafia igra. Sačekaj kraj ili neka domaćin otkaže.",
                     color=COLORS["warning"]),
            ephemeral=True,
        )
    _set_game_cooldown(i.user, i.guild_id, "mafia")
    g = MafiaGame(i.channel, i.user)
    MAFIA_GAMES[i.channel.id] = g
    view = MafiaLobbyView(g)
    await i.response.send_message(embed=mafia_lobby_embed(g), view=view)

@bot.tree.command(name="mafia-stop", description="🛑 [DOMAĆIN] Prekini Mafia igru u ovom kanalu")
async def mafia_stop_cmd(i: discord.Interaction):
    g = MAFIA_GAMES.get(i.channel.id)
    if not g:
        return await i.response.send_message(
            embed=em("ℹ️", "Nema aktivne Mafia igre ovdje.", color=COLORS["info"]), ephemeral=True)
    if i.user.id != g.host.id and i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("❌", "Samo domaćin igre ili vlasnik bota.", color=COLORS["error"]), ephemeral=True)
    g.phase = "over"
    if g.task: g.task.cancel()
    MAFIA_GAMES.pop(i.channel.id, None)
    await i.response.send_message(embed=em("🛑 Mafia prekinuta", "Igra je nasilno zaustavljena.", color=COLORS["error"]))

# ═══════════════════════════════════════════
#    💾 CLOUD BACKUP — /backup grupa (now/restore/status)
#    Spojeno u JEDNU grupu da ne probijemo 100-cmd Discord limit.
# ═══════════════════════════════════════════
backup_group = app_commands.Group(name="backup", description="💾 [VLASNIK] Cloud backup sistem")

@backup_group.command(name="now", description="💾 [VLASNIK] Forsiraj odmah upload backupa na Discord")
async def backup_now_cmd(i: discord.Interaction):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik bota može pokrenuti backup.", color=COLORS["error"]),
            ephemeral=True,
        )
    if not BACKUP_CHANNEL_ID:
        return await i.response.send_message(
            embed=em("⚠️ BACKUP_CHANNEL_ID nije postavljen",
                     "Postavi env varijablu **BACKUP_CHANNEL_ID** (ID privatnog kanala) i restartuj bota.",
                     color=COLORS["warning"]),
            ephemeral=True,
        )
    await i.response.defer(ephemeral=True)
    save_data()
    await _discord_backup_upload()
    await i.followup.send(
        embed=em("✅ Backup gurnut", f"Fajl `oleun_data.json` poslan u <#{BACKUP_CHANNEL_ID}>.",
                 color=COLORS["success"]),
        ephemeral=True,
    )

@backup_group.command(name="restore", description="💾 [VLASNIK] Vrati podatke iz zadnjeg backupa sa Discorda")
async def backup_restore_cmd(i: discord.Interaction):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik bota može pokrenuti restore.", color=COLORS["error"]),
            ephemeral=True,
        )
    if not BACKUP_CHANNEL_ID:
        return await i.response.send_message(
            embed=em("⚠️ BACKUP_CHANNEL_ID nije postavljen",
                     "Postavi env varijablu **BACKUP_CHANNEL_ID** i restartuj bota.",
                     color=COLORS["warning"]),
            ephemeral=True,
        )
    await i.response.defer(ephemeral=True)
    # privremeno izbriši lokalni fajl da restore prođe
    try:
        if os.path.exists(DATA_FILE):
            os.replace(DATA_FILE, DATA_FILE + ".manual_restore.bak")
    except Exception: pass
    ok = await _discord_backup_restore()
    if ok:
        await i.followup.send(
            embed=em("✅ Restore uspio", "Podaci su vraćeni iz zadnjeg backupa.", color=COLORS["success"]),
            ephemeral=True,
        )
    else:
        # vrati lokalni fajl ako restore nije uspio
        try:
            if os.path.exists(DATA_FILE + ".manual_restore.bak"):
                os.replace(DATA_FILE + ".manual_restore.bak", DATA_FILE)
                load_data()
        except Exception: pass
        await i.followup.send(
            embed=em("❌ Restore neuspješan",
                     "Nema validnog backupa u zadnjih 50 poruka kanala. Lokalni fajl vraćen.",
                     color=COLORS["error"]),
            ephemeral=True,
        )

@backup_group.command(name="status", description="💾 [VLASNIK] Status cloud backup sistema")
async def backup_status_cmd(i: discord.Interaction):
    if i.user.id not in OWNER_IDS:
        return await i.response.send_message(
            embed=em("❌ Samo vlasnik", "Samo vlasnik može vidjeti status.", color=COLORS["error"]),
            ephemeral=True,
        )
    last = _DBACKUP_STATE.get("last", 0)
    last_str = datetime.fromtimestamp(last, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if last else "_nikad_"
    ch_str = f"<#{BACKUP_CHANNEL_ID}>" if BACKUP_CHANNEL_ID else "❌ **NIJE POSTAVLJENO** (env var BACKUP_CHANNEL_ID)"
    restored_str = "✅ DA" if _DBACKUP_STATE.get("restored") else "—"
    pending_str = "⏳ DA" if _DBACKUP_STATE.get("pending") else "—"
    fsize = os.path.getsize(DATA_FILE) if os.path.exists(DATA_FILE) else 0
    desc = (
        f"📡 **Backup kanal:** {ch_str}\n"
        f"💾 **Lokalni fajl:** `{DATA_FILE}` ({fsize:,} B)\n"
        f"🕐 **Zadnji upload:** {last_str}\n"
        f"♻️ **Restore na ovom startu:** {restored_str}\n"
        f"📤 **Pending upload:** {pending_str}\n"
        f"⏱️ **Min interval:** {DBACKUP_INTERVAL}s"
    )
    await i.response.send_message(
        embed=em("💾 Cloud Backup status", desc, color=COLORS["info"]),
        ephemeral=True,
    )

bot.tree.add_command(backup_group)


# ═══════════════════════════════════════════
#    BALKANSKI MEMOVI lista
# ═══════════════════════════════════════════
BALKANSKI_MEMOVI = [
    "Kad kazes 'idem samo na 5 minuta' a vratis se za 2 sata",
    "Balkanska dijeta: jednom jedes, drugi put gledat kako drugi jedu",
    "Balkanski 'odmah' = negdje izmedju 30 minuta i nikad",
    "Nana: 'nisi jeo?' Ti: 'jesam' Nana: 'ajde pojedi ovo'",
    "Kad bolja polovina kaze 'kako hoces' — PAZI SE!",
    "Mi ne kazemo 'te volim', mi kazemo 'jesi jeo?'",
    "Balkanski WiFi password: pitaj komšiju",
    "Balkanski 'nije daleko': 45 minuta i tri kontrole",
    "Nema problema koji se ne moze riješiti uz kafu",
    "Kad kaze 'ne ljutim se' — najgore pocinje",
    "Mi smo jedini narod gdje se svi svadjaju a svi u pravu",
    "Nana vs. frizider: nana uvijek pobijedi",
    "Balkanska fizika: rakija lijeci sve, ili boli manje posle",
    "Balkanci ne kazu zbogom, kazu 'e, ajmo' i stoje jos sat",
    "Kad si gladan a mama kaze 'ima u frizideru' — traganje pocinje",
    "Svaka balkanska prica pocinje 'ti ne znas kako je bilo'",
    "Balkanski domacin: gost ne smije gladovati, cak ni slucajno",
    "Piknik plan: idemo u prirodu, jedemo 6 sati, ne vidimo prirodu",
    "Balkanski grad: 10 hiljada ljudi, svi znaju sve o svima",
    "Kad kazes 'gledam samo minutu' a sat prosao",
    "Balkanska logika: sunce zari, ali nosimo jaknu za svaki slucaj",
    "Viber poruka od mame u 6 ujutro: 'jesi ziv?'",
    "Ko nije kasnio 45 minuta na vlak koji je kasnio sat — nije Balkanac",
    "Balkanska tajna: svi znaju, niko ne govori — osim uz rakiju",
    "Komšijska posjeta: dodju na kavu, ostanu na veceri",
    "Balkanski ljekar: 'ajde, nije nista, uzmi caj'",
    "Svaki put kad izlaziš: 'di si bio?' 'di ideš?' 'kad se vracas?'",
    "Balkanski put do prodavnice: sretnješ 3 komšije, sat vremena",
    "Proslava u 14:00 = pocni dolaziti u 16:00",
    "Tata u kuci: tiho. Tata na auto: komentator",
    "Kad mama kaze 'vidi sto si uradio' otac gleda u pod",
    "Balkanski sat: 10:00 = izmedju 10:30 i 11:15",
    "Svadbeni stres: tko sjedi pored koga? Veci problem od rata",
    "Balkanski turist: svi frizideri otvoreni, restorani zaobidjeni",
    "Balkanci na moru: sjena, rostilj, muzika, mora nema",
    "Balkanski muzicki ukus: turbofolk ili metal, ne postoji sredina",
    "Nana ne mari za dijetu — ali mari za tvoje lijepo lice",
    "Djed kaze 'u moje vrjeme': pocni planirati 45 min slusanja",
    "Kad si bolestan: mama donese supu, baka donese rakiju, tata donese savjet",
    "Balkanski frizider: uvijek pun, nikad ne znas cega",
    "Ko ne dodje na slavlje nije nas — ko dodje ne ode kuci sit",
    "Balkanska autopilotnija: put do hamburgera poznaješ bolje od kuce",
    "Rodbina koja te ne vidi: 'narasao si!' (uvijek, bez obzira)",
    "Balkanski dorucak: caj, jaja, med, kajmak, burek — 'nista posebno'",
    "Nana gura hranu, mama gura kapu, tata gura savjete",
    "Balkanski 'jesmo li stigli?' = svakih 5 minuta od polaska",
    "Praznik plan: ne radimo nista CIJELI DAN zajedno",
    "Mama: 'ne brini, niko nista ne prica o tebi' Mama malo posle: '...'",
    "Balkanska ptica rane: mama u 7, svi u kuci u 10",
    "Svaka balkanska prica: pocne s kafom, zavrsi s politikom",
    "Kad sav grad zna tvoj problem, a ti si ga samo rekao prijatelju",
    "Djed u prici: 'a onda...' — pocinje sat vremena epske istorije",
    "Balkanski 'miran covjek': tih dok ne pocne fudbal",
    "Mama cita horoskop, baba cita solje, otac cita novine — svi u pravu",
    "Balkanski domacin misli 'mozda je gladan' = donese cijeli bife",
    "Kad neko kaze 'bit cu za 10 minuta' — naruci pice, moze cekati",
    "Balkanski 'nikad nije kasno' = vec kasno, ali idemo",
    "Kad pise 'br' u chatu — ne znas je l' brate ili nema teksta",
    "Balkanska strpljost: cekaj red 5 minuta, onda gurni se naprijed",
    "Balkanski film: svadba ili sprovod, uvijek ista muzika",
    "Kad ti kazu 'imas vremena' — to znaci hitno",
    "Komšija na vjencanju: 'tko je ova?' Svi gledaju. Komšija zna sve.",
    "Balkanci smo: gledamo lose vrijeme na Balkanu, kunemo vladu",
    "Balkanski 'nije skupo': vise nego sto imam",
    "Kad kazes 'ne trebam nista': trebas svaki dio, ali ne priznaješ",
    "Balkanski poklon: uvijek previse hrane, nikad dovoljno kesa",
    "Tata: 'je l' ugaseno?' Gasi sam, ali pita 3 puta",
    "Balkanski vijest: 10% info, 90% komentar",
    "Kad si kuci kasno — mama je budna, otac spava, ali cuje sve",
    "Balkan matematika: jedna kafa = 3 sata pricanja",
    "Rodit ces se opet ako izjedeš sve s tanjira — balkanska legenda",
    "Balkanski 'odmah se vracam' = video na ulici Ziku i tri sata nestao",
    "Balkanska izjava 'idem lezati malo' = cijela noc",
    "Balkanski alarm: mama vikne jednom, to je upozorenje",
    "Planiram odmor: torba spakirana, novac nema. Klasika.",
    "Cijela familija na telefonu za Bajram — nijedan ne moze da cuje",
    "Balkanska kuhinja: 'tjestenina za troje' = dovoljno za deset",
    "Nije pijanka ako si otisao pjeske i vratio taksijem",
    "Balkanac u restoranu: 'sta je najjeftinije?' (uzme najskuplje)",
    "Svaka balkan porodica ima jednog strucnjaka za sve",
    "Kad kazes 'sad cu' a ni za sat nisi pobjegao iz kreveta",
    "Balkanski 'bit ce gotovo za 5 minuta' a radio 3 sata",
    "Balkanski plan: 'odma idemo' = polazak za pola sata",
    "Godisnija — on zaboravi, ona pamti ZAUVIJEK",
    "Kad kazes 'idem spavati' a sedeš YouTube gledati do 3 ujutro",
    "Ko nije kasnio na vlastitu proslavu — nije nas",
    "Balkanci na dijeti: 'jedan komad torte ne steti' (uzme tri)",
    "Svaka balkanska familija: jedan koji jede sve, jedan koji ne jede nista",
    "Nana u bolnici: svi posjete tamo, nana kuha, doktori jedu",
    "Kad kazes 'nema nista u frizideru' — u njemu je hrana za tjedan",
    "Balkanski 'je l' sve ok?' = pricaj mi o svemu godinu dana",
    "Balkanska prazna torba: uvijek 12 kilograma hrane kad se vrati",
    "Svadbeni ples: stariji par — ne krecu se. Djeca — ne stanu.",
    "Balkanska filozofija: ko ne ceka, ne doceka",
    "Kad imas 'samo jedno pitanje' a imas sto",
    "Balkanci smo: ako nisi zakasnio, stigao si prerano",
    "Kad nana kaze 'pojedi jos malo' a si vec pun 40 minuta",
]

def get_next_meme(guild_id: int) -> str:
    return random.choice(BALKANSKI_MEMOVI)

# ═══════════════════════════════════════════
#    /meme — balkanski mem
# ═══════════════════════════════════════════
@bot.tree.command(name="meme", description="😂 Pošalji balkanski mem u kanal")
async def meme_cmd(i: discord.Interaction):
    meme_text = get_next_meme(i.guild.id if i.guild else 0)
    e = discord.Embed(
        description=f"😂  {meme_text}",
        color=COLORS["fun"],
        timestamp=datetime.now(timezone.utc)
    )
    e.set_author(name=f"{i.user.display_name} šalje mem", icon_url=i.user.display_avatar.url)
    e.set_footer(text=f"{BOT_NAME} • Balkanski memovi")
    await i.response.send_message(embed=e)
    _poo_task_progress(i.guild.id if i.guild else 0, i.user.id, "use_meme")


# ═══════════════════════════════════════════
#    💩 POO GAME — 24/7 virtuelna kreatura
# ═══════════════════════════════════════════
POO_STAGES = [
    (0,    '💩',    'Jaje Poo-a',      'Tek se izleglo. Jedva se pomjera.'),
    (50,   '💩',    'Beba Poo',         'Probudio se! Traži pažnju i hranu.'),
    (150,  '💩✨',  'Rastući Poo',      'Raste svakim danom! Počinje sjajiti.'),
    (350,  '💩⚡',  'Energični Poo',    'Pun energije! Skace unaokolo.'),
    (700,  '💩🔥',  'Vatreni Poo',      'Plamen izlazi iz njega! Vruc i mocan.'),
    (1200, '💩💎',  'Kristalni Poo',    'Pretvorio se u nešto nevjerojatno.'),
    (2000, '💩👑',  'Kraljevski Poo',   'Vladar svih Poo-ova. Legenda servera.'),
    (3500, '💩🌌',  'Kosmički Poo',     'Transcendirao granice prostora i vremena.'),
]

POO_ZADACI = [
    ('chat1','Početnički Chatter','Pošalji 10 poruka u chatu','chat',10,50,1),
    ('chat2','Aktivni Chatter','Pošalji 50 poruka ukupno','chat',50,120,2),
    ('chat3','Neumorni Pisac','Pošalji 200 poruka ukupno','chat',200,300,3),
    ('chat4','Chat Manijak','Pošalji 1000 poruka ukupno','chat',1000,1500,12),
    ('chat5','Legenda Chata','Pošalji 5000 poruka ukupno','chat',5000,5000,25),
    ('meme1','Memer Početnik','Koristi /meme 3 puta','use_meme',3,50,1),
    ('meme2','Balkanski Memer','Koristi /meme 20 puta','use_meme',20,150,2),
    ('meme3','Meme Legenda','Koristi /meme 100 puta','use_meme',100,500,5),
    ('meme4','Meme Bog','Koristi /meme 500 puta','use_meme',500,2000,15),
    ('meme5','Meme Vjecnost','Koristi /meme 2000 puta','use_meme',2000,8000,50),
    ('broj1','Broji Pocetniku','Unesi tacan broj u brojanje 5 puta','count',5,75,1),
    ('broj2','Majstor Brojeva','Unesi tacan broj 25 puta','count',25,200,3),
    ('broj3','Numericki Bog','Unesi tacan broj 100 puta','count',100,600,6),
    ('broj4','Matematicki Genij','Unesi tacan broj 500 puta','count',500,2500,18),
    ('broj5','Numericki Demon','Unesi tacan broj 2000 puta','count',2000,10000,60),
    ('posao1','Mali Radnik','Odradi /posao 5 puta','work',5,80,1),
    ('posao2','Marljivi Radnik','Odradi /posao 25 puta','work',25,220,3),
    ('posao3','Trudenik Dana','Odradi /posao 100 puta','work',100,700,7),
    ('posao4','Radoholic','Odradi /posao 500 puta','work',500,3000,20),
    ('posao5','Radni Bog','Odradi /posao 2000 puta','work',2000,10000,50),
    ('daily1','Dnevna Rutina','Uzmi /daily nagradu 5 puta','daily',5,80,1),
    ('daily2','Konzistentnost','Uzmi /daily nagradu 30 puta','daily',30,300,4),
    ('daily3','Disciplina','Uzmi /daily nagradu 100 puta','daily',100,800,8),
    ('daily4','Daily Master','Uzmi /daily nagradu 500 puta','daily',500,4000,22),
    ('daily5','Vjecni Daily','Uzmi /daily nagradu 2000 puta','daily',2000,15000,80),
    ('daj1','Poklon Darivac','Pošalji pare nekome /daj 10 puta','daj',10,150,2),
    ('daj2','Veliki Darivac','Pošalji pare nekome /daj 50 puta','daj',50,600,6),
    ('mile1','Bogatash','Dostigne 10 000 coina','balance',10000,200,3),
    ('mile2','Milioner','Dostigne 100 000 coina','balance',100000,1000,10),
    ('mile3','Milijarder','Dostigne 1 000 000 coina','balance',1000000,5000,30),
    ('hunt1','Lovac Pocetnik','Idi u lov /hunt 10 puta','hunt',10,100,2),
    ('hunt2','Iskusni Lovac','Idi u lov /hunt 50 puta','hunt',50,350,4),
    ('hunt3','Legendarni Lovac','Idi u lov /hunt 200 puta','hunt',200,1500,12),
    ('hunt4','Bog Lova','Idi u lov /hunt 1000 puta','hunt',1000,6000,35),
    ('kviz1','Kviz Igrac','Odgovori na /kviz 5 puta','kviz',5,80,1),
    ('kviz2','Znalac','Odgovori na /kviz 25 puta','kviz',25,250,3),
    ('kviz3','Enciklopedija','Odgovori na /kviz 100 puta','kviz',100,900,10),
    ('kviz4','Omniznalac','Odgovori na /kviz 500 puta','kviz',500,4000,25),
    ('slots1','Kockar Pocetnik','Odigraj /slots 5 puta','slots',5,70,1),
    ('slots2','Kockar','Odigraj /slots 30 puta','slots',30,280,4),
    ('slots3','Kockar Veteran','Odigraj /slots 100 puta','slots',100,750,8),
    ('slots4','Kockar Boga','Odigraj /slots 500 puta','slots',500,3500,22),
    ('bj1','Blackjack Debi','Odigraj /blackjack 10 puta','blackjack',10,120,2),
    ('bj2','BJ Profesionalac','Odigraj /blackjack 50 puta','blackjack',50,400,5),
    ('bj3','Blackjack Legenda','Odigraj /blackjack 200 puta','blackjack',200,2000,15),
    ('battle1','Borac','Učestvuj u /battle 5 puta','battle',5,80,1),
    ('battle2','Ratnik','Učestvuj u /battle 25 puta','battle',25,280,4),
    ('battle3','Sampion','Učestvuj u /battle 100 puta','battle',100,800,8),
    ('battle4','Ratni Bog','Učestvuj u /battle 500 puta','battle',500,4500,28),
    ('vjasala1','Rjesavac Vjasala','Odigraj /vjasala 5 puta','vjasala',5,70,1),
    ('vjasala2','Majstor Vjasala','Odigraj /vjasala 20 puta','vjasala',20,220,3),
    ('vjasala3','Vjasala Majstor','Odigraj /vjasala 100 puta','vjasala',100,900,10),
    ('kaladont1','Kaladont Pocetniku','Pokreni /kaladont 5 puta','kaladont',5,100,2),
    ('kaladont2','Kaladont Majstor','Pokreni /kaladont 25 puta','kaladont',25,500,6),
    ('bingo1','Bingo Igrac','Uzmi bingo tiket 5 puta','bingo',5,80,1),
    ('bingo2','Bingo Veteran','Uzmi bingo tiket 25 puta','bingo',25,300,4),
    ('zagrljaj1','Zagrljaj Podijelac','Zagrli nekoga 10 puta','zagrljaj',10,80,1),
    ('srce1','Ljubavni Heroj','Pošalji srce 20 puta','srce',20,120,2),
    ('vers1','Zadnji Stih','Pošalji vers /vers 5 puta','vers',5,100,2),
    ('vers2','Reper Servera','Pošalji vers /vers 25 puta','vers',25,400,5),
    ('poll1','Glasac','Napravi /poll glasanje 5 puta','poll',5,80,1),
    ('tiket1','Tiket Heroj','Otvori /tiket 3 puta','tiket',3,100,2),
    ('report1','Reportaz','Prijavi nekoga /report 5 puta','report',5,60,1),
    ('afk1','AFK Nomad','Postavi /afk status 10 puta','afk',10,80,1),
    ('geo1','Geograf','Odigraj /geografija 5 puta','geo',5,70,1),
    ('geo2','Geograf Znalac','Odigraj /geografija 25 puta','geo',25,250,3),
    ('kpm1','KPM Igrac','Odigraj /kpm 10 puta','kpm',10,70,1),
    ('kpm2','KPM Majstor','Odigraj /kpm 50 puta','kpm',50,250,3),
    ('zoo1','Zoo Ljubitelj','Pogledaj /zoo 10 puta','zoo',10,60,1),
    ('lottery1','Loto Igrac','Kupi loto tiket /lottery 5 puta','lottery',5,80,1),
    ('heist1','Razbojnik','Učestvuj u /heist 3 puta','heist',3,150,3),
    ('allpoo1','Poo Sluga','Pomozi Poo-u 50 puta ukupno','poo_total',50,500,5),
    ('allpoo2','Poo Prijatelj','Pomozi Poo-u 200 puta ukupno','poo_total',200,2000,15),
    ('allpoo3','Poo Cuvar','Pomozi Poo-u 1000 puta ukupno','poo_total',1000,10000,60),
    ('allpoo4','Poo Bog','Pomozi Poo-u 5000 puta ukupno','poo_total',5000,50000,250),
    ('mile4','Level 10','Dostigne Level 10','level',10,200,3),
    ('mile5','Level 25','Dostigne Level 25','level',25,500,6),
    ('mile6','Level 50','Dostigne Level 50','level',50,1000,10),
    ('mile7','Level 100','Dostigne Level 100','level',100,5000,30),
    ('mile8','Level 250','Dostigne Level 250','level',250,15000,75),
    ('xp1','XP Sakupljac','Sakupi 1 000 XP ukupno','xp',1000,100,2),
    ('xp2','XP Veteran','Sakupi 10 000 XP ukupno','xp',10000,500,6),
    ('xp3','XP Bog','Sakupi 100 000 XP ukupno','xp',100000,5000,40),
    ('stage1','Poo Budjenje','Pomozi Poo-u da dostigne Stage 2','stage',2,200,0),
    ('stage2','Poo Rast','Pomozi Poo-u da dostigne Stage 3','stage',3,300,0),
    ('stage3','Poo Energija','Pomozi Poo-u da dostigne Stage 4','stage',4,500,0),
    ('stage4','Vatreni Poo','Pomozi Poo-u da dostigne Stage 5','stage',5,1000,0),
    ('stage5','Kristalni Poo','Pomozi Poo-u da dostigne Stage 6','stage',6,2000,0),
    ('stage6','Kraljevski Poo','Pomozi Poo-u da dostigne Stage 7','stage',7,5000,0),
    ('stage7','Kosmicki Poo','Pomozi Poo-u da dostigne Stage 8','stage',8,15000,0),
    ('epic1','Vjecni Pisac','Pošalji 20 000 poruka ukupno','chat',20000,20000,100),
    ('epic2','Workaholic God','Odradi /posao 10 000 puta','work',10000,50000,200),
    ('epic3','Neumorni Lovac','Idi u lov 5 000 puta','hunt',5000,25000,120),
]

def _get_poo_data(guild_id: int) -> dict:
    key = str(guild_id)
    if key not in data['poo']:
        data['poo'][key] = {'xp': 0, 'stage': 0, 'total_helps': 0, 'contributors': {}}
    d = data['poo'][key]
    d.setdefault('xp', 0); d.setdefault('stage', 0)
    d.setdefault('total_helps', 0); d.setdefault('contributors', {})
    return d

def _get_poo_tasks(guild_id: int, uid: int) -> dict:
    key = f"{guild_id}:{uid}"
    if key not in data['poo_tasks']:
        data['poo_tasks'][key] = {}
    return data['poo_tasks'][key]

def _poo_stage_for(xp: int) -> int:
    stage_idx = 0
    for idx, (req, emoji, name, desc) in enumerate(POO_STAGES):
        if xp >= req: stage_idx = idx
        else: break
    return stage_idx

def _poo_task_progress(guild_id: int, uid: int, task_type: str, amount: int = 1):
    if not guild_id: return
    tasks = _get_poo_tasks(guild_id, uid)
    poo = _get_poo_data(guild_id)
    uid_str = str(uid)
    contributed = False
    for row in POO_ZADACI:
        tid, tname, tdesc, ttype, goal, coin_r, poo_contrib = row
        if ttype != task_type: continue
        if tasks.get(tid, 0) >= goal: continue
        tasks[tid] = tasks.get(tid, 0) + amount
        if tasks[tid] >= goal:
            tasks[tid] = goal
            poo['xp'] = poo.get('xp', 0) + poo_contrib
            poo['total_helps'] = poo.get('total_helps', 0) + 1
            poo['contributors'][uid_str] = poo['contributors'].get(uid_str, 0) + poo_contrib
            eco = get_economy(uid)
            eco['balance'] = eco.get('balance', 0) + coin_r
            contributed = True
    new_stage = _poo_stage_for(poo.get('xp', 0))
    if new_stage != poo.get('stage', 0): poo['stage'] = new_stage
    if contributed: save_data()

@bot.tree.command(name="poo", description="💩 Stanje Poo kreature na serveru")
async def poo_cmd(i: discord.Interaction):
    gid = i.guild.id if i.guild else 0
    poo = _get_poo_data(gid)
    xp = poo.get('xp', 0)
    stage_idx = _poo_stage_for(xp)
    stage_xp, emoji, stage_name, stage_desc = POO_STAGES[stage_idx]
    next_stage = POO_STAGES[stage_idx + 1] if stage_idx + 1 < len(POO_STAGES) else None
    helps = poo.get('total_helps', 0)
    if next_stage:
        next_xp = next_stage[0]
        prog = xp - stage_xp
        needed = next_xp - stage_xp
        bar_filled = min(int(prog / needed * 15), 15) if needed > 0 else 15
        bar = '█' * bar_filled + '░' * (15 - bar_filled)
        progress_text = f'\'`{bar}`\' \'`{prog}/{needed} XP`\''
        next_txt = f"{next_stage[1]} {next_stage[2]}"
    else:
        progress_text = '**💩 MAX STAGE DOSTIGNUTO!** 👑'
        next_txt = 'MAX'
    contribs = poo.get('contributors', {})
    top3 = sorted(contribs.items(), key=lambda x: x[1], reverse=True)[:3]
    top_text = ''
    medals = ['🥇', '🥈', '🥉']
    for idx, (uid_str, pts) in enumerate(top3):
        m = i.guild.get_member(int(uid_str)) if i.guild else None
        uname = m.display_name if m else f'User #{uid_str[:4]}'
        top_text += f"{medals[idx]} **{uname}** — `+{pts} Poo XP`\n"
    e = discord.Embed(
        title=f'💩 Serverski POO — Stage {stage_idx + 1}/{len(POO_STAGES)}',
        description=(
            f'{emoji}  **{stage_name}**\n'
            f'*{stage_desc}*\n\n'
            f'**Progres do sljedeceg stage-a:**\n'
            f'{progress_text}\n'
            f'Sljedeci: {next_txt}\n\n'
            f'📊 Ukupni Poo XP: **{xp:,}**\n'
            f'🤝 Ukupno doprinosa: **{helps:,}**'
        ),
        color=0x8B4513,
        timestamp=datetime.now(timezone.utc)
    )
    if top_text:
        e.add_field(name='🏆 Top 3 Cuvara Poo-a', value=top_text, inline=False)
    e.add_field(name='💡 Kako hraniti Poo?', value=(
        '• Pisi u chat aktivno\n'
        '• Koristi `/meme` komandu\n'
        '• Broji u kanalu za brojanje\n'
        '• Igraj igre: `/hunt` `/slots` `/kviz` `/blackjack`\n'
        '• Zaradjuj novac: `/posao` `/daily`\n'
        '• Ili plati direktno: `/poo-hrani` (200 💶)'
    ), inline=False)
    e.set_footer(text=f'💩 POO igra • {BOT_NAME} • 24/7 aktivan • /poo-zadaci za zadatke')
    await i.response.send_message(embed=e)

@bot.tree.command(name="poo-zadaci", description="💩 Lista Poo zadataka (10 po stranici, ukupno 100)")
@app_commands.describe(stranica="Stranica 1-10")
async def poo_zadaci_cmd(i: discord.Interaction, stranica: int = 1):
    gid = i.guild.id if i.guild else 0
    user_tasks = _get_poo_tasks(gid, i.user.id)
    stranica = max(1, min(stranica, 10))
    start = (stranica - 1) * 10
    zadaci_slice = POO_ZADACI[start:start + 10]
    desc = ''
    for tid, tname, tdesc, ttype, goal, coin_r, poo_contrib in zadaci_slice:
        prog = user_tasks.get(tid, 0)
        done = prog >= goal
        icon = '✅' if done else '🔲'
        bar_f = min(int(prog / goal * 8), 8) if goal > 0 else 0
        mini_bar = '▰' * bar_f + '▱' * (8 - bar_f)
        desc += f'{icon} **{tname}**\n'
        desc += f'> _{tdesc}_\n'
        desc += f'> `{mini_bar}` `{prog}/{goal}` · 💩+{poo_contrib} · 💶+{coin_r:,}\n\n'
    done_count = sum(1 for r in POO_ZADACI if user_tasks.get(r[0], 0) >= r[4])
    e = discord.Embed(
        title=f'💩 POO Zadaci — Stranica {stranica}/10',
        description=desc or 'Nema zadataka.',
        color=0x8B4513,
        timestamp=datetime.now(timezone.utc)
    )
    e.set_footer(text=f'Stranica {stranica}/10 · Napredak: {done_count}/{len(POO_ZADACI)} · {BOT_NAME}')
    await i.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="poo-top", description="💩 Top lista cuvara Poo-a na serveru")
async def poo_top_cmd(i: discord.Interaction):
    gid = i.guild.id if i.guild else 0
    poo = _get_poo_data(gid)
    contribs = poo.get('contributors', {})
    if not contribs:
        return await i.response.send_message(
            embed=em('💩 Poo Top Lista', 'Još niko nije doprinjeo Poo-u! Budi aktivan na serveru.', color=0x8B4513))
    top = sorted(contribs.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ['🥇', '🥈', '🥉'] + [f'`#{n}`' for n in range(4, 11)]
    lines = []
    for idx, (uid_str, pts) in enumerate(top):
        m = i.guild.get_member(int(uid_str)) if i.guild else None
        uname = m.display_name if m else f'User #{uid_str[:4]}'
        lines.append(f'{medals[idx]} **{uname}** — `+{pts} Poo XP`')
    stage_idx = _poo_stage_for(poo.get('xp', 0))
    semo, snm = POO_STAGES[stage_idx][1], POO_STAGES[stage_idx][2]
    e = discord.Embed(
        title='💩 Top 10 Cuvara Poo-a',
        description='\n'.join(lines),
        color=0x8B4513, timestamp=datetime.now(timezone.utc))
    e.add_field(name='💩 Trenutni Stage', value=f'{semo} **{snm}** (XP: {poo.get("xp",0):,})', inline=True)
    e.set_footer(text=f'Budi aktivan i hrani Poo-a! · {BOT_NAME}')
    await i.response.send_message(embed=e)

@bot.tree.command(name="poo-hrani", description="💩 Nahrani Poo-a direktno (košta 200 coina)")
async def poo_hrani_cmd(i: discord.Interaction):
    COST = 200
    gid = i.guild.id if i.guild else 0
    eco = get_economy(i.user.id)
    if eco['balance'] < COST:
        return await i.response.send_message(
            embed=em('💩 Nemaš dovoljno',
                     f'Hranjenje Poo-a koštá **{COST} 💶**.\nImaš samo `{eco["balance"]:,} 💶`.',
                     color=COLORS['error']), ephemeral=True)
    eco['balance'] -= COST
    poo = _get_poo_data(gid)
    bonus = random.randint(2, 8)
    old_stage = poo.get('stage', 0)
    poo['xp'] = poo.get('xp', 0) + bonus
    poo['total_helps'] = poo.get('total_helps', 0) + 1
    uid_str = str(i.user.id)
    poo.setdefault('contributors', {})[uid_str] = poo['contributors'].get(uid_str, 0) + bonus
    new_stage = _poo_stage_for(poo['xp'])
    poo['stage'] = new_stage
    save_data()
    semo, snm = POO_STAGES[new_stage][1], POO_STAGES[new_stage][2]
    leveled = new_stage > old_stage
    desc = f'Nahranio/la si Poo-a! +**{bonus} Poo XP** 🍔\nPoo XP ukupno: **{poo["xp"]:,}**'
    if leveled: desc += f'\n\n🎉 **POO JE NAPREDOVAO NA NOVI STAGE!**\n{semo} **{snm}**'
    await i.response.send_message(embed=em('💩 Poo je sit!', desc, color=0x8B4513, fields=[
        ('💰 Potrošeno', f'`{COST} 💶`', True),
        ('🏦 Ostalo', f'`{eco["balance"]:,} 💶`', True),
        ('💩 Stage', f'{semo} {snm}', True),
    ]))

@bot.tree.command(name="poo-info", description="💩 Tvoj licni doprinos i napredak zadataka")
async def poo_info_cmd(i: discord.Interaction):
    gid = i.guild.id if i.guild else 0
    poo = _get_poo_data(gid)
    uid_str = str(i.user.id)
    user_tasks = _get_poo_tasks(gid, i.user.id)
    my_contrib = poo.get('contributors', {}).get(uid_str, 0)
    done_count = sum(1 for r in POO_ZADACI if user_tasks.get(r[0], 0) >= r[4])
    total_tasks = len(POO_ZADACI)
    pct = round(done_count / total_tasks * 100, 1) if total_tasks > 0 else 0
    bar_f = int(done_count / total_tasks * 15) if total_tasks > 0 else 0
    bar = '█' * bar_f + '░' * (15 - bar_f)
    stage_idx = _poo_stage_for(poo.get('xp', 0))
    semo, snm = POO_STAGES[stage_idx][1], POO_STAGES[stage_idx][2]
    contribs = poo.get('contributors', {})
    sorted_c = sorted(contribs.items(), key=lambda x: x[1], reverse=True)
    my_rank = next((idx + 1 for idx, (uid, pts) in enumerate(sorted_c) if uid == uid_str), None)
    rank_txt = f'#{my_rank}' if my_rank else '—'
    e = discord.Embed(
        title='💩 Tvoj Poo Profil',
        description=(
            f'💩 Serverski Poo: {semo} **{snm}**\n'
            f'🤝 Tvoj doprinos: **{my_contrib} Poo XP**\n'
            f'🏆 Rang: **{rank_txt}**\n\n'
            f'📋 Zadaci: `{bar}` `{done_count}/{total_tasks}` ({pct}%)\n\n'
            f'💡 Koristi `/poo-zadaci` za detaljan pregled!'
        ),
        color=0x8B4513, timestamp=datetime.now(timezone.utc)
    )
    e.set_thumbnail(url=i.user.display_avatar.url)
    e.set_footer(text=f'💩 POO igra · {BOT_NAME} · Budi aktivan i pomozi Poo-u!')
    await i.response.send_message(embed=e, ephemeral=True)

# ═══════════════════════════════════════════
#    POKRETANJE
# ═══════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{BOT_NAME} {VERSION} STARTUJE...\n")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("POGRESAN TOKEN!")
    except Exception as e:
        print(f"Greška: {e}")
