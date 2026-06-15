
export interface CEmojiDef {
  id: string;
  name: string;
  anim: boolean;
}

export function cEmojiUrl(e: CEmojiDef, size = 32) {
  return `https://cdn.discordapp.com/emojis/${e.id}.${e.anim ? "gif" : "png"}?size=${size}&quality=lossless`;
}

export function CEmoji({
  e,
  size = 20,
  className = "",
}: {
  e: CEmojiDef;
  size?: number;
  className?: string;
}) {
  return (
    <img
      src={cEmojiUrl(e, size)}
      alt={`:${e.name}:`}
      title={`:${e.name}:`}
      width={size}
      height={size}
      className={`inline-block object-contain flex-shrink-0 ${className}`}
      draggable={false}
    />
  );
}

export const CE = {
  dashboard:   { id: "1500203557134270534", anim: true,  name: "aktivnost"              },
  commands:    { id: "1496899031786459356", anim: false, name: "admin"                  },
  embeds:      { id: "1504505912939909141", anim: false, name: "announcement"           },
  members:     { id: "1504505910314405888", anim: false, name: "members"                },
  server:      { id: "1504506880423231508", anim: false, name: "modernserverguide"      },
  permissions: { id: "1496898576150954165", anim: false, name: "roleadminblue2"         },
  protection:  { id: "1496898603246161970", anim: false, name: "twopartshieldids"       },
  games:       { id: "1500459114931949568", anim: true,  name: "game1"                  },
  settings:    { id: "1504505863032012832", anim: false, name: "settings"               },

  check:       { id: "1496898532559421571", anim: false, name: "neonverifiedcheck"      },
  warn:        { id: "1496899181674238053", anim: false, name: "warningids"             },
  ban:         { id: "1500446026715103253", anim: true,  name: "ban"                    },
  cancel:      { id: "1500443837452255302", anim: true,  name: "cancel"                 },
  bot:         { id: "1496898476976636055", anim: false, name: "bot"                    },
  crown:       { id: "1496899185516216400", anim: false, name: "shinycrown"             },
  star:        { id: "1496898993395859457", anim: false, name: "blueneonstar"           },
  lock:        { id: "1504509321613148342", anim: false, name: "locked"                 },
  lockgif:     { id: "1500444008760217641", anim: true,  name: "lockkey"                },
  bell:        { id: "1504505860720820395", anim: false, name: "bell"                   },

  coin:        { id: "1500444133389635704", anim: true,  name: "coin"                   },
  slots:       { id: "1500443990129115196", anim: true,  name: "slots"                  },
  dice:        { id: "1500260185510248448", anim: true,  name: "dice"                   },
  dice2:       { id: "1500443897489526965", anim: true,  name: "dice1"                  },
  globe:       { id: "1500443832674947132", anim: true,  name: "globespin"              },
  spellbook:   { id: "1504506083094565125", anim: true,  name: "spellbook"              },
  amogus:      { id: "1500461621800337448", anim: true,  name: "amongusfloss"           },
  gun:         { id: "1500443902182948954", anim: true,  name: "gun"                    },
  bow:         { id: "1500262801862824047", anim: true,  name: "bow"                    },
  butterfly:   { id: "1496899500160192562", anim: true,  name: "butterfly"              },
  ticket:      { id: "1500196243853541397", anim: true,  name: "ticket"                 },
  joystick:    { id: "1500443845752524893", anim: true,  name: "joystick"               },
  question:    { id: "1500444013994709093", anim: true,  name: "questionexclaimanimated"},
  potion:      { id: "1504507420238676188", anim: true,  name: "bluepotion"             },
  sword:       { id: "1500462011648049192", anim: true,  name: "flamingfiresword"       },
  present:     { id: "1500461835860709487", anim: true,  name: "bluepresent"            },
  bank:        { id: "1500444133389635704", anim: true,  name: "coin"                   },
  shop:        { id: "1504507147973558403", anim: true,  name: "shinybluediamond"       },
  quests:      { id: "1500196243853541397", anim: true,  name: "ticket"                 },
  aktivnost:   { id: "1500203403362435234", anim: true,  name: "aktivnost1"             },
  rank:        { id: "1500203557134270534", anim: true,  name: "aktivnost"              },
  leaderboard: { id: "1496899185516216400", anim: false, name: "shinycrown"             },

  zagrljaj:    { id: "1500203677917511741", anim: true,  name: "zagrljaj"               },
  poljubac:    { id: "1500203685450617032", anim: true,  name: "poljubac"               },
  mazi:        { id: "1500203682199896245", anim: true,  name: "mazi"                   },
  paw:         { id: "1500259928936284211", anim: true,  name: "pinkpaw"                },
  heartpop:    { id: "1496899299487907870", anim: true,  name: "heartpop"               },
  annoyed:     { id: "1496899399077330994", anim: true,  name: "annoyedgojo"            },
  srce:        { id: "1500197728267927734", anim: true,  name: "srce"                   },
  diamond:     { id: "1496898969052381407", anim: false, name: "diamond"                },
  sparkles:    { id: "1500259869259989033", anim: true,  name: "pinksparkles"           },
  oof:         { id: "1496898747018379305", anim: true,  name: "oof"                    },
  sleepy:      { id: "1496898915176415413", anim: true,  name: "sleepyhellokitty"       },
  pinkheart:   { id: "1504504866700132534", anim: true,  name: "pinkheart"              },
  love:        { id: "1500058006308519936", anim: true,  name: "love"                   },
  giveaway:    { id: "1500196200157020172", anim: true,  name: "giveaways"              },
  vatrice:     { id: "1496898836155596962", anim: true,  name: "vatrice"                },
  music:       { id: "1500459145382592602", anim: true,  name: "music2"                 },
} satisfies Record<string, CEmojiDef>;
