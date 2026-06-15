import { Router } from "express";

const router = Router();

export const ALL_COMMANDS = [
  {
    category: "Opšte",
    icon: "Info",
    commands: [
      { name: "ping",       description: "Provjeri brzinu bota",                                    usage: "/ping",                    prefix: true,  adminOnly: false, cooldown: null, aliases: ["p"] },
      { name: "serverinfo", description: "Informacije o serveru",                                   usage: "/serverinfo",               prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "userinfo",   description: "Informacije o korisniku",                                 usage: "/userinfo [korisnik]",      prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "avatar",     description: "Prikaži avatar korisnika",                                usage: "/avatar [korisnik]",        prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "invite",     description: "Statistika — poruke + invite-ovi",                        usage: "/invite [korisnik]",        prefix: true,  adminOnly: false, cooldown: null, aliases: ["i","inv"] },
      { name: "spotify",    description: "Pogledaj šta korisnik trenutno sluša na Spotifyu",        usage: "/spotify [korisnik]",       prefix: true,  adminOnly: false, cooldown: null, aliases: ["np","sp"] },
      { name: "help",       description: "Sve dostupne komande bota",                               usage: "/help",                     prefix: true,  adminOnly: false, cooldown: null, aliases: ["h"] },
    ],
  },
  {
    category: "Moderacija",
    icon: "Shield",
    commands: [
      { name: "ban",           description: "Ban korisnika [VLASNIK / GIANNI]",                          usage: "/ban <korisnik> [razlog]",                prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "ban-dozvola",   description: "Dozvoli/oduzmi pravo na /ban za GIANNI člana [VLASNIK]",    usage: "/ban-dozvola <akcija> <korisnik>",        prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "kick",          description: "Pravi kick / dodjela GIANNI oznake [VLASNIK]",              usage: "/kick <korisnik> [razlog]",               prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "timeout",       description: "Ućutkaj korisnika",                                         usage: "/timeout <korisnik> [minuta] [razlog]",   prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "warn",          description: "Upozori korisnika",                                         usage: "/warn <korisnik> [razlog]",               prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "warnings",      description: "Upozorenja korisnika",                                      usage: "/warnings <korisnik>",                    prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "clearwarnings", description: "Obriši upozorenja korisnika",                               usage: "/clearwarnings <korisnik>",               prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "clear",         description: "Obriši poruke iz kanala",                                   usage: "/clear [kolicina]",                       prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "report",        description: "Prijavi člana staffu (1x u minuti)",                        usage: "/report <korisnik> <razlog>",             prefix: false, adminOnly: false, cooldown: 60,   aliases: [] },
    ],
  },
  {
    category: "Ekonomija",
    icon: "Coins",
    commands: [
      { name: "baki",          description: "Provjeri stanje novca",                                             usage: "/baki [korisnik]",               prefix: true,  adminOnly: false, cooldown: null, aliases: ["b"] },
      { name: "posao",         description: "Radi i zaradi (svakih 30 min)",                                     usage: "/posao",                          prefix: true,  adminOnly: false, cooldown: 1800, aliases: [] },
      { name: "daily",         description: "Nagrada svakih 30 minuta",                                          usage: "/daily",                          prefix: false, adminOnly: false, cooldown: 1800, aliases: [] },
      { name: "daj",           description: "Pošalji pare drugaru",                                              usage: "/daj <korisnik> <iznos>",         prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "kradi",         description: "Pokušaj ukrasti (rizično!)",                                        usage: "/kradi <korisnik>",               prefix: true,  adminOnly: false, cooldown: 300,  aliases: [] },
      { name: "bank",          description: "Banka — deposit/withdraw/balance (5% nedjeljna kamata)",            usage: "/bank [akcija] [iznos]",          prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "lottery",       description: "Sedmična loto — kupi tiket za 100 coina",                          usage: "/lottery [akcija]",               prefix: true,  adminOnly: false, cooldown: null, aliases: ["lot"] },
      { name: "heist",         description: "Timski razboj — okupi 3+ ljudi i dobijte 1000-5000",               usage: "/heist",                          prefix: false, adminOnly: false, cooldown: 600,  aliases: [] },
      { name: "shop",          description: "Pogledaj šta možeš kupiti",                                         usage: "/shop",                           prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "kupi",          description: "Kupi predmet iz shopa",                                             usage: "/kupi <id>",                      prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "quests",        description: "Pogledaj svoje dnevne zadatke",                                     usage: "/quests",                         prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "giveaway",      description: "Pokreni giveaway [ADMIN]",                                          usage: "/giveaway <nagrada> [minuta] [kanal]", prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "giveaway-end",  description: "Završi aktivni giveaway i izvuci pobjednika [ADMIN]",               usage: "/giveaway-end",                   prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "novac",         description: "Dodaj ili oduzmi coina korisniku [OWNER]",                          usage: "/novac <akcija> <korisnik> <iznos>", prefix: false, adminOnly: true, cooldown: null, aliases: [] },
    ],
  },
  {
    category: "XP i Aktivnost",
    icon: "TrendingUp",
    commands: [
      { name: "rank",        description: "Level i XP na serveru",                       usage: "/rank [korisnik]",    prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "aktivnost",   description: "Tvoja aktivnost: level, XP i broj poruka",    usage: "/aktivnost [korisnik]", prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "leaderboard", description: "Top lista servera (xp/novac)",                usage: "/leaderboard [tip]",  prefix: true,  adminOnly: false, cooldown: null, aliases: ["lb"] },
      { name: "topchatters", description: "Top 10 najaktivnijih chatera",                usage: "/topchatters",        prefix: true,  adminOnly: false, cooldown: null, aliases: ["tc","top"] },
    ],
  },
  {
    category: "Vatrice 🔥",
    icon: "Flame",
    commands: [
      { name: "vatrice-ember",  description: "Daj vatricu(e) članu — ažurira nick i šalje objavu [VLASNIK]", usage: "/vatrice ember <korisnik> [kolicina]", prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "vatrice-pup",   description: "Top lista — najpopularniji članovi po vatricama",              usage: "/vatrice pup",                         prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "vatrice-kanal", description: "Postavi kanal za objave vatrica [VLASNIK]",                    usage: "/vatrice kanal <kanal>",               prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "vatrice-oblik", description: "Promijeni emoji koji predstavlja vatricu [VLASNIK]",           usage: "/vatrice oblik [emoji]",               prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "vatrice-start", description: "Pokreni / resetuj vatrica sistem na serveru [VLASNIK]",        usage: "/vatrice start",                       prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
    ],
  },
  {
    category: "Igre",
    icon: "Gamepad2",
    commands: [
      { name: "kpm",           description: "Kamen-Papir-Makaze",                                                    usage: "/kpm",                          prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "slots",         description: "Slot mašina — uloži od 20 do 1.000.000.000",                            usage: "/slots [ulog]",                 prefix: true,  adminOnly: false, cooldown: 30,   aliases: [] },
      { name: "blackjack",     description: "Igraj Blackjack protiv dilera",                                          usage: "/blackjack <oklada>",            prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "vjasala",       description: "Igra Vješala — pogodi skrivenu riječ!",                                  usage: "/vjasala",                      prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "kaladont",      description: "Pokretanje igre Kaladont — ulančaj riječi!",                             usage: "/kaladont [slova]",             prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "kaladont-stop", description: "Zaustavi trenutnu Kaladont igru u ovom kanalu",                         usage: "/kaladont-stop",                prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "toplo-hladno",  description: "Pogodi tajni broj — Toplo ili Hladno!",                                  usage: "/toplo-hladno [maksimum]",      prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "kviz",          description: "Odgovori na Balkan pitanje i osvoji pare!",                              usage: "/kviz [oklada]",                prefix: true,  adminOnly: false, cooldown: 30,   aliases: [] },
      { name: "geografija",    description: "Geografski kviz — pogodi i osvoji pare!",                                usage: "/geografija [oklada]",          prefix: true,  adminOnly: false, cooldown: 30,   aliases: [] },
      { name: "amogus",        description: "Pokreni Among Us igru!",                                                 usage: "/amogus",                       prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "amogus-stop",   description: "Zaustavi Among Us igru [HOST/ADMIN]",                                   usage: "/amogus-stop",                  prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "poker",         description: "Pokreni Texas Hold'em Poker za pravi novac (2-9 igrača)",               usage: "/poker [ulog]",                 prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "bingo",         description: "Pokreni Bingo — unesi 5 brojeva i osvoji nagradu!",                     usage: "/bingo",                        prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "mafia",         description: "Pokreni Mafia igru u ovom kanalu",                                       usage: "/mafia",                        prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "mafia-stop",    description: "Prekini Mafia igru u ovom kanalu [DOMAĆIN]",                            usage: "/mafia-stop",                   prefix: false, adminOnly: false, cooldown: null, aliases: [] },
    ],
  },
  {
    category: "Ljubavne",
    icon: "Heart",
    commands: [
      { name: "zagrljaj", description: "Zagrli nekog na serveru",    usage: "/zagrljaj <korisnik>", prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "poljubac", description: "Pošalji poljubac nekome",    usage: "/poljubac <korisnik>", prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "mazi",     description: "Pomazi nekoga nježno",       usage: "/mazi <korisnik>",     prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "tapsi",    description: "Tapši nekoga prijateljski",  usage: "/tapsi <korisnik>",    prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "high5",    description: "Daj peticu nekome",          usage: "/high5 <korisnik>",    prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "cudan",    description: "Budi ćudan prema nekome",   usage: "/cudan <korisnik>",    prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "srce",     description: "Pošalji srce nekome",        usage: "/srce <korisnik>",     prefix: true, adminOnly: false, cooldown: 10, aliases: [] },
      { name: "brak",     description: "Zaprosio nekoga (za fun)",   usage: "/brak <korisnik>",     prefix: false, adminOnly: false, cooldown: null, aliases: [] },
    ],
  },
  {
    category: "Fun",
    icon: "Laugh",
    commands: [
      { name: "kompli",   description: "Pošalji slatki kompliment nekome",                    usage: "/kompli <korisnik>",       prefix: false, adminOnly: false, cooldown: 15,   aliases: [] },
      { name: "fora",     description: "Ubaci foru na račun nekoga (sve u šali!)",            usage: "/fora <korisnik>",         prefix: false, adminOnly: false, cooldown: 15,   aliases: [] },
      { name: "muv",      description: "Muvaj nekoga Balkan stilom",                          usage: "/muv <korisnik>",          prefix: false, adminOnly: false, cooldown: 15,   aliases: [] },
      { name: "crush",    description: "Otkrij ko je tvoj tajni crush na serveru!",           usage: "/crush",                   prefix: false, adminOnly: false, cooldown: 300,  aliases: [] },
      { name: "hunt",     description: "Idi u lov na životinje!",                             usage: "/hunt",                    prefix: false, adminOnly: false, cooldown: 30,   aliases: [] },
      { name: "zoo",      description: "Pogledaj svoju zbirku životinja",                     usage: "/zoo [korisnik]",          prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "battle",   description: "Bori se sa nekim",                                    usage: "/battle <korisnik>",       prefix: false, adminOnly: false, cooldown: 30,   aliases: [] },
      { name: "sell",     description: "Prodaj životinje iz zoo-a",                           usage: "/sell <životinja> [kolicina]", prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "animals",  description: "Lista svih životinja i raritet",                      usage: "/animals",                 prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "pray",     description: "Pomoli se za nekoga",                                 usage: "/pray <korisnik>",         prefix: false, adminOnly: false, cooldown: 30,   aliases: [] },
      { name: "meme",     description: "Pošalji balkanski mem u kanal",                       usage: "/meme",                    prefix: true,  adminOnly: false, cooldown: 15,   aliases: [] },
      { name: "vers",     description: "Pošalji rimu / vers u hip-hop stylish embedu",        usage: "/vers <tekst>",            prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
    ],
  },
  {
    category: "Poo",
    icon: "Target",
    commands: [
      { name: "poo",          description: "Stanje Poo kreature na serveru",                          usage: "/poo",                    prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "poo-zadaci",   description: "Lista Poo zadataka (10 po stranici, ukupno 100)",         usage: "/poo-zadaci [stranica]",  prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "poo-top",      description: "Top lista cuvara Poo-a na serveru",                       usage: "/poo-top",                prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "poo-hrani",    description: "Nahrani Poo-a direktno (košta 200 coina)",                usage: "/poo-hrani",              prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "poo-info",     description: "Tvoj licni doprinos i napredak zadataka",                 usage: "/poo-info",               prefix: false, adminOnly: false, cooldown: null, aliases: [] },
    ],
  },
  {
    category: "Setup / Admin",
    icon: "Settings",
    commands: [
      { name: "setup",              description: "Postavi sve kanale i uloge servera odjednom [ADMIN]",          usage: "/setup",                            prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-roles",        description: "Kreiraj sve GIANNI uloge odjednom [ADMIN]",                    usage: "/setup-roles",                      prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-welcome",      description: "Postavi welcome kanal [ADMIN]",                                usage: "/setup-welcome <kanal>",            prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-leave",        description: "Postavi leave kanal [ADMIN]",                                  usage: "/setup-leave <kanal>",              prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-autorole",     description: "Postavi automatsku ulogu pri ulasku [ADMIN]",                  usage: "/setup-autorole <uloga>",           prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-log",          description: "Postavi log kanal [ADMIN]",                                    usage: "/setup-log <kanal>",                prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-starboard",    description: "Postavi starboard kanal (min. zvjezdice) [ADMIN]",             usage: "/setup-starboard <kanal> [zvjezdice]", prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-levelrole",    description: "Postavi ulogu za određeni level [ADMIN]",                      usage: "/setup-levelrole <level> <uloga>",  prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setup-panels",       description: "Auto-kreiraj sva 3 self-role panela odjednom [ADMIN]",         usage: "/setup-panels [kanal]",             prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "aktivnost-setup",    description: "Postavi kanal za XP level-up i aktivnost [ADMIN]",             usage: "/aktivnost-setup <kanal>",          prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "ticket-setup",       description: "Postavi ticket sistem u ovaj kanal [ADMIN]",                   usage: "/ticket-setup",                     prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "server-config",      description: "Pregled konfiguracije servera [ADMIN]",                        usage: "/server-config",                    prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "setchannel",         description: "Postavi confess/report/birthday/staff-apps kanal [ADMIN]",     usage: "/setchannel <tip> <kanal>",         prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "reset-gw",           description: "Resetuj i ponovo pokreni giveaway za 5 minuta [ADMIN]",        usage: "/reset-gw <nagrada> [kanal]",       prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "backup",             description: "Odmah snimi backup podataka bota [OWNER]",                     usage: "/backup",                           prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "backup-restore",     description: "Vrati zadnji cloud backup bota [OWNER]",                       usage: "/backup-restore",                   prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "backup-status",      description: "Pregled cloud backup statusa i istorije [OWNER]",              usage: "/backup-status",                    prefix: false, adminOnly: true, cooldown: null, aliases: [] },
      { name: "sync",               description: "Force-sync svih slash komandi [OWNER]",                        usage: "/sync [scope]",                     prefix: false, adminOnly: true, cooldown: null, aliases: [] },
    ],
  },
  {
    category: "Ostalo",
    icon: "MoreHorizontal",
    commands: [
      { name: "brojanje-postavi", description: "Postavi kanal za brojanje [ADMIN]",     usage: "/brojanje-postavi <kanal> [pocetak]", prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "brojanje-info",   description: "Pokaži stanje brojanja",                 usage: "/brojanje-info",                      prefix: false, adminOnly: false, cooldown: null, aliases: [] },
      { name: "brojanje-reset",  description: "Resetuj brojanje na 0 [ADMIN]",          usage: "/brojanje-reset",                     prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "poll",            description: "Napravi glasanje sa do 4 opcije",         usage: "/poll <pitanje> <opcija1> <opcija2> [opcija3] [opcija4]", prefix: true, adminOnly: false, cooldown: null, aliases: [] },
      { name: "tiket",           description: "Otvori tiket za podršku",                usage: "/tiket",                              prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "afk",             description: "Postavi AFK status",                      usage: "/afk [razlog]",                       prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "qr",              description: "Generiši QR kod iz teksta ili URL-a",     usage: "/qr <tekst>",                         prefix: true,  adminOnly: false, cooldown: null, aliases: ["qrcode"] },
      { name: "event",           description: "Objavi event na serveru [OWNER]",         usage: "/event <naslov> <opis>",              prefix: false, adminOnly: true,  cooldown: null, aliases: [] },
      { name: "sort-roles",      description: "Sortiraj uloge na serveru [prefix only]", usage: ".sort-roles",                         prefix: true,  adminOnly: true,  cooldown: null, aliases: [] },
      { name: "info",            description: "Informacije o botu i serveru [prefix]",   usage: ".info",                               prefix: true,  adminOnly: false, cooldown: null, aliases: [] },
      { name: "pravila",         description: "Objavi pravila u kanal [prefix only]",    usage: ".pravila",                            prefix: true,  adminOnly: true,  cooldown: null, aliases: [] },
      { name: "pravila-voice",   description: "Objavi voice pravila u kanal [prefix]",   usage: ".pravila-voice",                      prefix: true,  adminOnly: true,  cooldown: null, aliases: [] },
      { name: "tiketstaff",      description: "Staff tiket panel u kanal [prefix only]", usage: ".tiketstaff",                         prefix: true,  adminOnly: true,  cooldown: null, aliases: [] },
    ],
  },
];

router.get("/commands", (req, res) => {
  res.json(ALL_COMMANDS);
});

router.get("/commands/:name", (req, res) => {
  const { name } = req.params;
  for (const cat of ALL_COMMANDS) {
    const cmd = cat.commands.find((c) => c.name === name);
    if (cmd) {
      return res.json({ ...cmd, category: cat.name });
    }
  }
  return res.status(404).json({ error: "Command not found" });
});

export default router;
