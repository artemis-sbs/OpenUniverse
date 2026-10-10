# Painting the map

So far the galaxy's geography is uniform. Regions give parts of it a face:
their own sky, their own music, their own color wash on the map - and their
own weather, in the form of local danger. Landmarks pin single, named places
to the chart.

## Regions

```
## [Regions](regions)

### [The Veilfall](veilfall)
---
Center: 5, -4
Radius: 3
Skybox: sky-neb2-rvb
Music: Artemis2
Color: #cc2244
Enemy mix: 40%
Station mix: 5%
Mine chance: 75%
---
Veil country. Red skies, salted lanes, and no honest ports for miles.

### [The Lantern Lanes](lantern_lanes)
---
Center: -4, 2
Radius: 3
Skybox: sky-delight
Color: #ffcc44
Enemy mix: 0%
Station mix: 30%
---
The Combine's home lanes - calm, bright, and busy. The safest miles in
the Reach.
```

- **Center / Radius** - a square patch of map: `Center: 5, -4` with
  `Radius: 3` covers everything within 3 cells of that system. Centering a
  region on a side's home turns their neighborhood into their territory.
- **Skybox / Music / Color** - arrival mood. The sky and music change when
  the crew jumps in; the color faintly washes those cells on the map.
- **The danger lines** (`Enemy mix`, `Station mix`, `Mine chance`...) - these
  override the galaxy's average *inside this region only*. That's how you
  write a warzone (enemies up, ports down, mines everywhere) or a haven
  (enemies zero, ports plentiful) without touching anything global. The full
  list of dials is on [The dials](dials.md) page.

!!! warning "Overlapping regions"
    If two regions overlap, write the smaller one first - it wins.

## Landmarks

Landmarks are the opposite of procedural: single, named, hand-placed places -
the locations of legend your dialogue and story can point at.

```
## [Landmarks](landmarks)

### [The Pale Ark](pale_ark)
---
At: 1, -2
Kind: derelict
---
A colony ship a century adrift, lanterns long cold. Every spacer in the
Reach has a story about what still walks her corridors.

### [Lighthouse Station](lighthouse)
---
At: -4, 2
Kind: station
Side: lantern
Art: starbase_science
---
The Combine's great beacon at the heart of the home lanes - half port,
half promise.
```

`Kind:` is `station` or `derelict`; a station can name a `Side:` (a side key)
and an `Art:` (its model). `At:` pins it to a system.

Landmarks can also carry `Guards:` (a fleet that contests them, once) and
`Terrain:` (a nebula or asteroid envelope, so the place sits in cover whatever
the cell rolled).

## A landmark you fly INTO

A landmark carrying `Relic:` is not a prop. It is an interior - chambers,
passages, boxes, subtracted masses, named places and authored contents - built
when the crew arrives and torn down with the cell.

```
### [Torgoth Megastation](giants_house)
---
At: 2, -1
Kind: derelict
Relic: voice
Relic file: relics/voice.amd
Cutscene: arrive_voice
---
```

| field | means |
|---|---|
| `Relic:` | the relic key in that file - this ruin has an inside |
| `Relic file:` | the `.amd` holding it. Defaults to `<key>.amd` |
| `Cutscene:` | played ONCE, the first time anyone arrives in this system |

The ruin itself is authored in its own file, as a `## Relics` section - see the
library's [relic guide](https://artemis-sbs.github.io/sbs_utils/build/relics/)
for the geometry. A relic file is **self-contained**: its `## Items`, its
`## Cutscenes` and its dialogue scenes are registered when it loads, so the whole
ruin - the space, what is in it, and what is said in it - opens as one document.

Three things happen for free when a landmark becomes a relic:

- **The way in is on the map.** A selectable contact and a navpoint at the point
  carrying `Roles: entrance`. Nothing else in the interior is marked.
- **The inside draws itself as you fly it.** Every point carrying `Roles:` is a
  dark measuring post until a ship reaches it, and then it lights up and stays
  lit. The radar fills in behind the crew rather than handing them a floor plan.
- **The relic brings its own atmosphere**, sized to the structure, so the
  landmark's own `Terrain:` is skipped - two nebulae over one ruin would fight,
  and the relic's is the one that has to be right, because it is what caps warp
  inside.

`universe_in_relic(ship)` answers "are they in the ruin right now", which is how
a mission leaves a crew alone while they are inside one.

## A landmark you beam down to

A landmark carrying `Site:` is somewhere the crew leaves the ship for: a colony,
an outpost, a station that stopped answering. The crew go as themselves - whoever
is at each console beams down as the person they have been all evening.

```
### [Customs House](customs_house)
---
At: 0, 0
Kind: station
Site: customs
---
A customs post that waves everybody through.
```

| field | means |
|---|---|
| `Site:` | the site's key |
| `Site file:` | the `.amd` holding it. Defaults to `<key>.amd`, beside your universe file |

How the crew arrives depends on what the landmark is: they **dock** with a
station or a derelict, and **orbit** a worldlet.

The site is a file of its own, with two sections:

```
# [Customs House](customs)

## [Hails](hails)

### [Customs Answers](customs_call)
---
Speaker: customs_clerk
Title: Customs House
---
% Customs. Nothing to declare? Then come and look around, if you must.

- [Assemble a boarding party]() ; signal boarding_down
- [Stay aboard]()

## [Scenes](boarding)

### [The Counter](customs_counter)
% A long counter and one clerk, who does not look up.

- [Read the manifest on the counter](customs_manifest) ; learn the manifest
- [Beam back up]()
```

- **`## [Hails](hails)`** is the call that arrives when the ship ties up. The
  answer that sends a party down carries `; signal boarding_down`. Leave the
  section out and the party is offered as soon as the ship arrives. (The
  `Speaker:` is a record in a `## [Voices](voices)` section of the same file -
  a name, a `Face:` and a `Color:`.)
- **`## [Scenes](boarding)`** are the rooms. The FIRST one is where the party
  arrives. An answer with empty brackets, `()`, ends the scene; when no scene is
  open the visit is over and everybody is back at their console.

That is a **text site**: rooms and choices, no map. Docking again offers it again.

| A site's call | |
|---|---|
| "Stay aboard" | The call is over and nothing else happens. The next time the ship docks there, the place calls again |
| Not answered | The call waits. It is not placed a second time while it is still waiting |
| No `## Hails` chapter | The party is offered as the ship arrives. If nobody goes down, it is withdrawn when the ship undocks (or leaves orbit, or leaves the system), and offered again on the next arrival |

!!! warning "When a site does not appear, read `mast.runtime.log`"
    A site that cannot be made says so there, once, with the site's key and its file:

    - its file was not found, or has no rooms under `## [Scenes](boarding)`;
    - it has a `## Hails` chapter and no answer ends with `; signal boarding_down`
      (also when the signal is misspelled), so the crew could take the call and
      never go down;
    - it is written as a site the party walks, and no map has its key (below).

### A site the party walks

The same `Site:` is a place the party **walks** when your universe's folder has a
map for it: a tile area file whose first lines say `area:` and **the site's own
key**.

```
area: tally_yard
title: Tally Yard
tileset: starter
entry: pad
```

Nothing else joins them - no new field on the landmark, no new word in the site
file. A landmark that says `Site: tally_yard`, and a `.tiles` file that says
`area: tally_yard`, are one place.

**The two keys must be the same word.** A walked site keeps its scenes under
`## [Scenes](scenes)`, where each one belongs to a thing or a person, so it has no
first room to arrive in. If the area's key does not match (`area: yard` beside
`Site: tally_yard`) there is no map and nothing to play as text either, and **the
site does not exist**: no call when the ship docks, nothing to board. `sbs lint`
reports it as `site-no-area`, and the game says so once in `mast.runtime.log`.

Only a site file that also has rooms under `## [Scenes](boarding)` is played as a
text site when it has no map. Its Props and People are then not used, and the same
two places say so.

On a map there is no first room. The party stands at the area's `entry:`, and a
scene belongs to the thing or the person that opens it. So a walked site's file
says what stands on the map:

```
## [Props](props)

### [Tally house door](yard_door)
---
Area: tally_yard
Mark: yard_door
Sprite: prop:hatch
Open sprite: prop:doorframe
Blocks: yes
Opens with: key yard_key
---
The only way into the tally house.

## [People](people)

### [The Tallyman](yard_keeper)
---
Area: tally_yard
Mark: yard_keeper
Sprite: fig:junker_m
Calm: yes
Talk scene: yard_keeper
---

## [Scenes](scenes)

### [The Tallyman](yard_keeper)
% "Nine days. I kept counting and nobody came."

- [Leave him to it]()
```

`## Props`, `## People`, `## Hostiles`, `## Scenes` and `## Side Stories` are
written exactly as in a tile-map mission of its own - see the library's
[tile map guide](https://artemis-sbs.github.io/sbs_utils/build/ground-tile-maps/)
for every field, for the area file, and for the `.tileset` file that says which
ground can be walked. A site file written for one plays in the other unchanged.

| A walked site | |
|---|---|
| When it ends | When the **last** of the party is back aboard (BEAM UP on the ePADD). Docking again offers it again. If nobody went down at all, it ends when the ship undocks or leaves the system |
| What it remembers | Opened doors, things picked up, people put down, and what was learned there - through a jump away and back, and through Continue |
| Where the files go | Anywhere in your mission's folder. The `away` starter keeps them in `ground/` |
| The art | The `TILE_ART:` setting names the art sets, and `story.json` pins the packs that hold them. Without the packs the map is black; everything still works |
| When it loads | The area files and the art load once, as the universe starts |

!!! warning "Keys are unique across the whole universe"
    A prop or a person's key - `yard_door`, `yard_keeper` - must not be used in
    two site files. The second one is never put on its map. `sbs lint` reports
    it (`site-key-collision`), and reports a site file that has Props or People
    but no map of its key (`site-no-area`). Starting every key with the site's
    own key is the easy way to keep them apart.

One party at a time: while a party is down at one site, arriving at another
offers nothing.

## Saying where they are

Every arrival shows a title card naming the system - the landmark, else a side's
home, else the region, else the coordinates. Nothing named a cell out loud
before; the galaxy map header does, and most story missions never enable that
console.

**Next: [Captains and the cast](people.md)** - give the galaxy faces.
