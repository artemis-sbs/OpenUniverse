"""A walked (tile-map) site, as TEXT - the files a writer adds to a universe's folder.

Not a test. Strings, not files, on purpose: a `.tiles` file anywhere under the Open
Universe folder would make Open Universe itself a universe with a tile world (the files
are found by a search of the mission's folder), and it ships none. A test writes these
into a temp mission folder.

  TILESET     ground/starter.tileset   what kinds of ground there are
  AREA        ground/tally_yard.tiles  the map; its header says `area: tally_yard`
  SITE        tally_yard.amd           what stands on it, who is there, what they say
  LANDMARKS   two landmark records: one `Site:` that is walked, one that is text
  TEXT_SITE   customs.amd              a text site, for a universe that has both
"""

TILESET = """tileset: starter
title: Starter ground
kinds:
  dust:    walk see   look=dirt
  pad:     walk see   look=stone_tiles
  floor:   walk see   look=floor_metal
  rock:               look=rock
  wall:    tall       look=wall_metal
"""

# Two rooms: the open yard, and the tally house behind its door.
AREA = """area: tally_yard
title: Tally Yard
tileset: starter
entry: pad
legend:
  .: dust
  #: rock
  =: pad
  _: floor
  W: wall
  P: pad @pad
  D: floor @yard_door
  T: dust @yard_terminal
  k: dust @yard_keeper
  c: dust @yard_keycard
  s: dust @yard_loader
  L: floor @yard_ledger
---
########################
#......................#
#..===.......WWWWWWW...#
#..=P=..k....W_____W...#
#..===.......W__L__W...#
#............WWWDWWW...#
#......c.......T.......#
#..................s...#
#......................#
########################
"""

SITE = """# [Tally Yard](tally_yard)

A place the party WALKS. The landmark says `Site: tally_yard`, and the map is the area
file whose header says `area: tally_yard` - the same key. Nothing else joins them.

## [Voices](voices)

### [The Tallyman](yard_voice)
---
Face: terran_male
Roles: narrator
Color: "#fd8"
---
Keeps the count at Tally Yard.

## [Hails](hails)

### [Tally Yard Answers](yard_call)
---
Speaker: yard_voice
Title: Tally Yard
Color: "#fd8"
---
% Tally Yard. The count is short and the loader has stopped listening. Come down if you like.

- [Assemble a boarding party]() ; signal boarding_down
- [Stay aboard]()

## [Side Stories](side_stories)

### [Clear the Yard](yard_clear)
---
For: weapons
Starts when: at once
Objective: Put the loader out of action
Done when: signal hostile_down_yard_loader
Leads to: yard_loader
---
The loader does not know a friend from a thief any more.

## [Props](props)

### [Yard terminal](yard_terminal)
---
Area: tally_yard
Mark: yard_terminal
Sprite: prop:terminal
Scene: yard_terminal
Blocks: yes
Scan: Still drawing power. Its last entry is nine days old.
---
A weatherproof terminal beside the tally house door.

### [Tally house door](yard_door)
---
Area: tally_yard
Mark: yard_door
Sprite: prop:hatch
Open sprite: prop:doorframe
Blocks: yes
Opens with: key yard_key
Scan: Mag locked. The keycard reader beside it is live.
---
The only way into the tally house.

### [Yard keycard](yard_keycard)
---
Area: tally_yard
Mark: yard_keycard
Sprite: prop:keycard
Item: yard_key
---
A gray keycard on a lanyard, dropped where the loader walks.

### [The tally ledger](yard_ledger)
---
Area: tally_yard
Mark: yard_ledger
Sprite: prop:terminal
Scene: yard_ledger
Scan: A paper ledger. The last page is in a different hand.
---
The yard's count, kept by hand.

## [People](people)

### [The Tallyman](yard_keeper)
---
Area: tally_yard
Mark: yard_keeper
Sprite: fig:junker_m
Face: male
Calm: yes
Talk scene: yard_keeper
Scan: One human. Tired, and not armed.
---
The man who keeps the count, sitting on an upturned crate.

## [Hostiles](hostiles)

### [Loader frame](yard_loader)
---
Area: tally_yard
Mark: yard_loader
Sprite: fig:robot_war
HP: 2
Damage: 1
Notice: 3
Stun: 10
Speed: 2
Patrol: 19 7; 21 7; 21 8; 19 8
Scan: A cargo frame, nine days without a recognition update.
---
A loader walking the same square it has walked for nine days.

## [Scenes](scenes)

### [The Yard Terminal](yard_terminal)
% One line on the screen, over and over: COUNT SHORT. SEE LEDGER.

- [Read the log](yard_terminal_log) ; learn the count is short
- [Step back]()

### [Nine Days](yard_terminal_log)
% Day one: forty crates in, thirty-eight counted. Day two: the loader stops answering. The entries stop.

- [Step back]()

### [The Tallyman](yard_keeper)
% "Nine days. I kept counting and nobody came."

- [Ask how to get into the tally house](yard_keeper_key)
- [Leave him to it]()

### [The Keycard](yard_keeper_key)
% "Keycard. I dropped it in the yard the day the loader turned on me."

- [Thank him]()

### [The Ledger](yard_ledger)
%{learned the count is short} Two crates short, and the last page is not his writing.
%{learned the count is short < 1} Columns of figures. Without the terminal's count they mean nothing.

- [Close the ledger]() ; learn a second hand
"""

# Two landmarks in the home system: a walked site and a text one, side by side.
LANDMARKS = """
### [Tally Yard](tally_yard_station)
---
At: 0, 0
Kind: station
Side: tsn
Art: starbase_industry
Site: tally_yard
---
A counting yard on the edge of the lane.

### [Customs House](customs_house)
---
At: 0, 0
Kind: station
Side: tsn
Art: starbase_civil
Site: customs
---
A customs post that waves everybody through.
"""

TEXT_SITE = """# [Customs House](customs)

A text site: rooms and choices, no map.

## [Voices](voices)

### [The Clerk](customs_clerk)
---
Face: terran_female
Roles: narrator
Color: "#8df"
---
Stamps what is put in front of her.

## [Hails](hails)

### [Customs Answers](customs_call)
---
Speaker: customs_clerk
Title: Customs House
Color: "#8df"
---
% Customs. Nothing to declare? Then come and look around, if you must.

- [Assemble a boarding party]() ; signal boarding_down
- [Stay aboard]()

## [Scenes](boarding)

### [The Counter](customs_counter)
---
Speaker: customs_clerk
---
% A long counter and one clerk, who does not look up.

- [Read the manifest on the counter](customs_manifest) ; learn the manifest
- [Beam back up]()

### [The Manifest](customs_manifest)
---
Speaker: customs_clerk
---
% Forty crates declared for Tally Yard. Somebody has initialed every line.

- [Back to the counter](customs_counter)
- [Beam back up]()
"""
