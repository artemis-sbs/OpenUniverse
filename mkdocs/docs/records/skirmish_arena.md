# The Broken Accord {#the-broken-accord}

| Fact | Value |
|---|---|
| Display | Skirmish - The Broken Accord |

Two fleets, one field of worldlets, and a truce that lasted exactly as long as the ore did. Build an economy, raise a navy, and end the other admiral's war - the last side with a Headquarters keeps the Reach.

## Scenario {#the-broken-accord-scenario}

| Fact | Value |
|---|---|
| Mode | skirmish |

Multi-admiral PvP. Set Player Ships to 2 or more - player two flies for Orion. Each side starts in its OWN home system (worlds apart), so build an economy and a navy at home, then jump the fleet toward the enemy to engage - use the Navigation galaxy map. Victory is the last side standing (raze every enemy Headquarters); a well-placed strike on the enemy's first HQ - its capital - ends it faster.

## Worldlets {#the-broken-accord-worldlets}

The resource bodies both admirals fight over - build Extractors on them, refine and bank the yield, spend it on platforms and fleets. A dry worldlet stops producing.

### Cinder World {#the-broken-accord-worldlets-cinder}

| Fact | Value |
|---|---|
| Palette | base #8c2f1c, emissive #48180c, clouds #776655 |
| Also | economy |
| Yields | ore 8 |
| Reserve | 4000 |

A cracked, mineral-rich ember of a world. Miners love it; nobody else does.

### Veiled Giant {#the-broken-accord-worldlets-veiled-giant}

| Fact | Value |
|---|---|
| Palette | base #2c4a8c, clouds #b8c4e0, bands 3.7 |
| Also | economy |
| Yields | gas 10 |
| Reserve | 6000 |

A banded gas giant, its high winds rich in fuel-grade volatiles.

### Haven World {#the-broken-accord-worldlets-haven}

| Fact | Value |
|---|---|
| Palette | base #2f6e3a, clouds #ffffff |
| Also | economy |
| Yields | crew 2, ore 2, gas 2 |
| Reserve | unlimited |

A small settled world. People, modest industry, and somewhere to hold.

## Admiralty {#the-broken-accord-admiralty}

| Fact | Value |
|---|---|
| Worldlet chance | 70% |

A resource-rich arena (worldlets in most systems) so the fight is over ground worth holding, not over finding any at all. Economy pace comes from \`Mode: skirmish\` (brisk); override it here with \`Economy pace:\` if you want a slower or faster match.

## Regions {#the-broken-accord-regions}

The battlefield's terrain: each region claims a square of systems with its own Skybox and Nav-map Color, and can bias the local spawn mix (enemy / mines) or mark a lethal antimatter veil. In a skirmish they give the open arena shape - a contested middle both sides bleed for, and a hazard that channels the fleets. Author smaller regions first so they win over larger ones. Driven by universe_regions.py.

### The No-Man's Reach {#the-broken-accord-regions-no-mans-reach}

| Fact | Value |
|---|---|
| Center | 0, 0 |
| Radius | 3 |
| Color | `#cc6633` |
| Skybox | sky-neb2-rvb |
| Enemy mix | 25% |
| Mine chance | 60% |

The dead space between two capitals, where the Accord broke. Neither admiral holds it and both bleed for it - drifting mines, scavenger raiders, and the wrecks of the last fleet that massed here in the open. Take the middle and you take the war; linger in it and you feed it.

### The Slagged Veil {#the-broken-accord-regions-slagged-veil}

| Fact | Value |
|---|---|
| Center | 0, 6 |
| Radius | 1 |
| Color | `#aa33ff` |
| Kind | antimatter |
| Skybox | sky-neb2-rvb |

A wound left by a scuttled antimatter core - a curtain of raw shear that cooks a hull from the inside within minutes. It splits the northern approach in two: the admiral who routes around it flanks; the one who forgets it is there loses a fleet to the dark, not to the enemy.

## Officers {#the-broken-accord-officers}

Example Academy roster for testing the Admiral navy: named fleet captains any admiral can commission at the Shipyard once an Academy stands. Values use the reputation poles and drive each officer's fleet bonuses (by-the-book runs leaner on gas, resourceful salvages richer, fearsome engages farther). Placeholder flavor for now: authored voices come later. Currently a shared pool both sides draw from (per-side rosters are a later design pass).

### Commodore Ansel Vale {#the-broken-accord-officers-vale}

| Fact | Value |
|---|---|
| Face | male |
| Title | the Quartermaster |
| Values | by-the-book 40, honest 30, kind 10 |

Ran the academy logistics course for a decade and the lanes know it. Fleets under Vale come home fueled, patched, and on schedule.

### Captain Iris Kade {#the-broken-accord-officers-kade}

| Fact | Value |
|---|---|
| Face | female |
| Title | Old Thunder |
| Values | fearsome 40, violent 20, generous 10 |

Leads from the front and shoots first. Kade's fleets hit harder and scare weaker prey off the board before a shot lands.

### Captain Juno Ashwell {#the-broken-accord-officers-ashwell}

| Fact | Value |
|---|---|
| Face | female |
| Title | the Magpie |
| Values | resourceful 40, intellectual 20, selfish 10 |

Never met a wreck she could not strip or a sensor shadow she could not slip through. Ashwell's fleets salvage more and die less.

### Commander Rho Serval {#the-broken-accord-officers-serval}

| Fact | Value |
|---|---|
| Face | male |
| Title | the Blade |
| Values | fearsome 30, by-the-book 20, honest 10 |

Precise and relentless. Serval keeps a disciplined line that holds under fire.

### Captain Mira Voss {#the-broken-accord-officers-voss}

| Fact | Value |
|---|---|
| Face | female |
| Title | the Fox |
| Values | resourceful 30, intellectual 30, generous 10 |

Reads a battle two moves ahead and wastes neither a shot nor a ton of ore.

### Commander Dax Orlan {#the-broken-accord-officers-orlan}

| Fact | Value |
|---|---|
| Face | male |
| Title | the Anvil |
| Values | by-the-book 30, generous 20, kind 20 |

Steady under pressure and never leaves a wingman behind. Orlan's fleets hold together long past when they should have broken.
