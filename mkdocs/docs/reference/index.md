# Reference - every label on one page

The compact version of the [walkthrough](../writing/index.md): every chapter
of a universe file and the facts each accepts. Every chapter and every fact is
optional unless noted. For the full AMD format (including the YAML form used
by other addons), see `AMD_AUTHORS_GUIDE.md` in the missions folder.

## The root (`#` heading)

| Fact | Meaning |
|---|---|
| `Display:` | The name shown in the Universe dropdown. |
| `Axis: a / b` | Replace the built-in trait pairs (one line per pair). Authoring *any* axis replaces *all* seven. |
| `Job tiers: N, M` | Standing needed for tier-2 / tier-3 side work. |
| `Foe deals at: N` | Standing at which a `foe` side will deal with you. |
| `Alliance at: N` | Standing at which a side counts as an ally. |
| `Max reward: X` | Pay multiplier at maximum standing (`2.0` = double). |
| `Ceasefire free at: N` | Standing at which a ceasefire costs nothing. |
| `Ceasefire per point: N` | Credits per point of standing below that. |
| `Station mix: %` | Chance a system holds a station. |
| `Enemy mix: %` | Chance a system holds hostiles. |
| `Nebula mix: %` | Chance a system is nebula. |
| `Anomaly mix: %` | Chance of an anomaly. |
| `Derelict chance: %` | Chance a system hides a scannable wreck. |
| `Outpost chance: %` | Chance of a minor outpost. |
| `Mine chance: %` | Chance an enemy system is mined. |
| `Loot max: N` | Most loot caches per system. |

The built-in trait pairs: `honest`/`liar`, `fearsome`/`cowardly`,
`peaceful`/`violent`, `generous`/`selfish`, `kind`/`cruel`,
`resourceful`/`by-the-book`, `intellectual`/`foolish`.

## `## Sides`

| Fact | Meaning |
|---|---|
| `Color:` | Map/side color, e.g. `#cc2244`. |
| `Archetype:` | `military` / `trader` / `settler` / `mercenary` / `pirate` / `cult`. |
| `Disposition:` | `neutral` (talks) or `foe` (shoots first). |
| `Home:` / `Homes:` | Home system `col, row`; several separated with `;`. |
| `Values:` | Trait leanings: `pole N` weights, comma-separated. |
| `Offers:` | Job keys from `## Jobs`, comma-separated. |
| `Flies:` | Ship races: one, an even list, or weighted (`60% Kralien, 40% Arvonian`). Races: `Kralien`, `Torgoth`, `Arvonian`, `Ximni`. |

## `## Jobs`

| Fact | Meaning |
|---|---|
| `Tier:` | `1` (anyone) / `2` (good standing) / `3` (proven friends). |
| `Goal:` | English objective; the verb picks the trigger (below). |
| `Pays:` | Reward, e.g. `300 credits` (scaled up by standing). |
| `Earns:` | Reputation on completion: `side pole delta`, comma-separated. |

**Goal / When triggers** - the leading verb decides:

| Phrase | Tracks |
|---|---|
| `destroy N <foe>` (or `kill`) | kills |
| `recover N <good>` (or `collect`, `gather`) | cargo collected |
| `scan N derelicts` (or `survey`) | science scans |
| `dock station` | a docking |
| `reach col, row` (or `travel`) | traveling to a system |

Built-in goods for `recover`: `provisions`, `ore`, `gas`, `tech`,
`contraband`.

## `## Narrative` and `## Goals`

| Fact | Meaning |
|---|---|
| `Scope: shared` | The whole crew shares this step. Write it on every beat. |
| `State:` | `active` (live at launch) or `secret` (waits for a reveal). |
| `When:` | The trigger (same verb phrases as `Goal:`). |
| `Then: reveal <key>` | Completing this step activates that one. |
| `Then: signal <name>` | Completing this step fires a named signal. |
| `Pays:` / `Earns:` | Credits / reputation on completion. |
| `Win: true` / `Lose: true` | *(Goals only)* ends the campaign. |
| `Citation:` | *(Goals only)* the end-card text. |

## `## Regions`

| Fact | Meaning |
|---|---|
| `Center:` | Middle system, `col, row`. |
| `Radius:` | Half-width of the square it covers. |
| `Skybox:` | Sky shown inside the region. |
| `Music:` | Music track inside the region. |
| `Color:` | Faint wash on the map. |
| *any generation dial* | Overrides the global inside this region. |

Smaller overlapping regions must be written first - they win.

## `## Landmarks`

| Fact | Meaning |
|---|---|
| `At:` | The system it sits in, `col, row`. |
| `Kind:` | `station` or `derelict`. |
| `Side:` | *(station)* the owning side key. |
| `Art:` | *(station)* the station model. |

## `## Goods`

| Fact | Meaning |
|---|---|
| `Weight:` | How often this good scatters as loot. |

## `## Captains`

| Fact | Meaning |
|---|---|
| `Side:` | The side key they belong to. |
| `Title:` | An honorific shown with the name. |
| `Values:` | Personal trait poles, `pole N` weights. |
| `Flies:` | Their ship's race. |
| `Roams:` | The system where they can be hailed, `col, row`. |
| `Rival when:` | Personal-standing guard that turns them hostile, e.g. `standing < -20`. |

## `## Lifeforms` (the cast)

| Fact | Meaning |
|---|---|
| `Face:` | `terran` / `male` / `female`, or a literal face string. |
| `Roles:` | Tags, comma-separated. |
| `Scene:` | The dialogue scene that is this character's voice. |
| `Color:` | Comms card color. |
| `Pickup:` | *(passenger)* the station system they wait at. |
| `Deliver to:` | *(passenger)* their destination system. |
| `Pays:` | *(passenger)* the fare, paid on delivery. |
| `Sabotage:` | *(optional)* systems a hostile passenger damages, e.g. `sensors, weapons`. |

## `## Dialogue`

| Piece | Meaning |
|---|---|
| `Speaker:` | Side, captain, or cast key - whose face the scene wears. |
| `When: comms` | This scene opens when the speaker is hailed. |
| `% line` | One alternate take (one is played at random). |
| `%{guard} line` | A take that plays only when the guard holds; first match wins. |
| `- [Label](scene_key)` | A player reply, leading to the next scene. |
| `... if <guard>` | Reply offered only when the guard holds. |
| `... ; <outcomes>` | On choosing: `costs N credits`, `earns <who> <pole> <delta>`, `signal <name>` - comma-separated. |

Guards may reference trait poles (`fearsome > 20`), `credits`, and - for a
captain's scene - `standing` (the player's personal standing with them).

## Splitting a chapter into files

```
## Dialogue
---
File: dialogue/veil.amd
File: dialogue/lantern.amd
---
```

Included files hold just that chapter's entries and splice in, in order.
Paths are relative to the universe file.
