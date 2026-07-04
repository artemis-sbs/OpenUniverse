# Multi-System Feasibility — Multiple Player Ships & Admirals Viewing Different Systems

Brainstorm note. **No engine changes assumed** — this is about what the current
Cosmos engine + sbs_utils primitives already allow, and where the real work lives.

Status: feasibility established + **Model A shipping in OU**. Perf spike done
(real-engine `perf_probe`, 2026-07-03); one spike (coordinate precision) remains.
Multi-cell build (**Model A — coexisting systems, faking B**) **Phase 0–2d done and
ENGINE-VERIFIED (2026-07-03): two player ships jumped to different systems at once,
each Navigation console showed its own cell.** Cells coexist at distinct world slots,
per-ship jump, per-ship nav view. Remaining: Phase 2e/3 — per-cell damage/saves/
watches/captains + admiral self-jump (still keyed to the shared global). See
`universe/universe_helpers.py` (slot allocator + occupancy) and `universe/universe.mast`.

---

## The one fact everything hangs on: there is exactly one `sim`

Cosmos has a **single simulation and a single coordinate space**. No shards, no
instances, no "System A vs System B" containers. Every object — worldlet, asteroid,
NPC, player ship, admiral camera — lives in the same 3D space and ticks in the same
`cosmos_event_handler` loop.

"Different systems" is therefore **not an engine primitive**. It is spatial
separation within one space — which is already exactly what OU does with worldlets
scattered across coordinates.

The question decomposes into two things people usually conflate:

| Question | Answer |
|---|---|
| **View isolation** — can two clients look at two different regions at once? | **Yes, cleanly, today.** |
| **Simulation isolation** — are those regions independent (perf, bleed, lifecycle)? | **No** — that's where the real work is. |

---

## The good news: "view" is already per-client

A console's vantage is whatever object it's assigned to
(`sbs.assign_client_to_ship(client_id, ship_id)`). A player ship at `(0,0,0)` and
one at `(0,0,900_000)` inherently see different space — the 2D radar and 3D view
center on the assigned object, and **scan range** decides what populates them.

You get multi-system viewing *for free* the moment you separate content in
coordinates. It is not a feature to build; it is a consequence of the architecture.

Both target cases reduce to "place the vantage, set its scan range":

### Multiple player ships in different systems
Spawn them at far-apart coordinates. Each sees its own neighborhood. Warp/jump
between systems = moving the ship's coordinates a long way (instant reposition, or a
warp animation). Nothing engine-level blocks this.

### Multiple admirals viewing different systems
This is the **detached-camera pattern** (LM `gamemaster.mast`, OU `admiral.mast`)
replicated N times:

- Each admiral is an invisible `player_spawn` camera with a large
  `ship_base_scan_range`, riding a `gamemaster_`/`admiral` console with an embedded
  2D view (`gui_layout_widget("comms_2d_view")`).
- Position the camera over a system → it sees that system.
- Multiple cameras = multiple admirals, each independent.
- Click-to-pan already works: `//focus/comms` → `COMMS_ORIGIN.pos =
  Vec3(EVENT.source_point)`. Nothing stops each admiral from panning to a *different*
  system.

See `MAST_CLAUDE.md` → "Detached command consoles" for the full cambot recipe
(console-name selection routing, `gamemaster_` optimized network path, side-wide
scan so comms enables, `remove_role` for art-derived roles).

---

## The levers you already have

| Lever | Role |
|---|---|
| **Coordinate separation** | Primary isolation mechanism. OU worldlets are already spaced so scan ranges don't overlap. |
| **`ship_base_scan_range`** | The "how much of my system do I see" dial. Admiral = system-wide; fighter = local. |
| **`link(cam, "extra_scan_source", …)`** | Force-see specific objects regardless of range. |
| **Per-client media** | `play_music_file(client_id, …)`, per-client story dialog — each system can feel distinct to its viewer. |
| **Console-name selection routing** | Each admiral's console name still governs sci/comms click routing; N admirals = N appropriately-named consoles. |

---

## The hard limits — where it actually gets tricky

Roughly in order of how much they'd bite:

### 1. Everything ticks, always — MEASURED (see the perf-run section below)
Objects in an unwatched system still integrate physics, run brains, and count
against the engine's global budget. There is **no "sleep this region."** Scan-range
culling affects rendering/network, **not** simulation cost. This is the real ceiling
on "how many systems at once," and it's a content/perf problem, not a view problem.

**The `perf_probe` run answered "how big is the budget," and it's enormous:**
- **Passive content is nearly free** — 100,000 mostly-passive agents (asteroids) held
  **rtf ≈ 1.0, flat, no ceiling.**
- **Active combat is the cost** — the engine holds real-time to **~190 fighting ships
  / ~38k active agents** (~15–20 simultaneously-pitched-battle systems), then
  **degrades gradually and gracefully** to a stable ~0.75–0.83 plateau at
  330k agents / 536 ships — **no O(n²) cliff.**

So the ceiling is high and the failure mode is benign. Since a real universe rarely
has every system in pitched battle at once, the headroom is large. Full numbers in
the **"Measured: perf_probe results"** section below.

### 2. Bleed-through & coordinate budget
Two systems must be far enough apart that scan ranges, radar, and object exclusion
never overlap — else objects from system A ghost onto system B's radar. Admiral scan
range tops out ~40,000u, so systems want **~100k+ separation** to be safe. OU
already respects this.

**Coordinate budget.** There's no floating-origin / rebasing in a single sim —
every object sits at its true magnitude relative to one global origin, so a
far-flung system inherits the float precision *at that magnitude*. Precision is
absolute (tied to distance from 0), so clustering a system tightly helps bleed, not
precision — magnitude is what bites.

Recommended envelope (**±1M is also where the team already landed independently**):

| Envelope | Per-axis | Verdict |
|---|---|---|
| **Comfortable** | ±1,000,000 u | Rock-solid under float32 *or* float64. Design here. |
| **Soft ceiling** | ±8,000,000 u | Fine at radar scale; marginal fine helm control if float32 (ulp ≈ 1u at 2²³). |
| **Hard line** | ±16,000,000 u | Don't cross without confirming float64. |

Keep it **symmetric around origin**. The pivotal unknown is **float32 vs float64**
for world positions: if float32, ulp hits 1u at ±8.4M and motion quantizes/jitters
in fine control; if float64, no practical game-scale limit. Failure mode is jitter &
snapping, not a crash. See Spike #2 to measure it.

**The budget is not the binding constraint.** Even the conservative ±1M envelope
with 100k spacing yields a ~20×20×20 grid — thousands of slots. The single-sim tick
budget (Hard Limit #1) hits *long* before you run out of safe coordinate space.
Budget coordinates at ±1M and spend the worry on perf.

### 3. Skybox scope — RESOLVED: per-client works
**Skyboxes are settable per client** — the engine API takes a `clientID`:

- `sbs.set_sky_box(clientID, artFileName)` — per client (`0` = server).
- `sbs.set_sky_box_all(artFileName)` — broadcast to all.
- `skybox_schedule(name, ID=0)` — procedural wrapper (per client via `ID`).

So each viewer can have a different backdrop keyed to whichever system their vantage
sits in — set it when a client's camera/ship enters a region. The "distinct systems"
illusion holds visually, not just on radar/scan. Non-issue; no longer a gating
unknown.

### 4. Network / client count — UNMEASURED (the perf run had no clients)
Each admiral camera + each player ship is a console the server streams frames to. No
hard max-client number in hand. "Many admirals each streaming a full 2D view of a
busy system" is the scaling axis to watch — likely **bandwidth before CPU**.

**The `perf_probe` run does NOT speak to this** — it ran with ~no connected consoles,
so replication cost was ~zero and `rtf` measured compute only. This axis is still
open, and it's the one that gates a *populated* universe. It needs its own run:
several browser consoles + admirals on busy systems, measuring **client frame
latency + bytes/sec** (not server rtf — networking is likely a separate thread, so it
may not slow the sim tick even when it saturates the client). Note this also makes
`standby`'s network-culling value hard to state until measured (Hard Limit #1 note /
"don't standby terrain" rests on the *reasoned* terrain-replicates-once model).

### 5. Global game state
Game-end conditions, `shared` story state, win/lose are story-wide today. A true
multi-system universe wants **per-system** objectives and lifecycle — script
architecture work (OU's side/roster model is already halfway there), not an engine
change.

---

## Measured: perf_probe results (real engine, 2026-07-03)

Two auto-ramping runs of the `perf_probe` mission on the real engine (fixed 30 Hz),
metric = **real-time factor (rtf) = Δsim / Δwall** (1.0 = holding real-time). Each
run adds one "system" every ~6 s. Snapshots in the scratchpad
(`perf_run_asteroid.log`, `perf_run_brainheavy.log`).

**Scope caveat — this measured COMPUTE, not NETWORK.** Both runs had ~no connected
consoles, so the engine replicated object state to nobody. `rtf` captures only the
server sim/CPU axis (physics + brains + steering); the **network/bandwidth axis
(Hard Limit #4) is completely unmeasured.** Real play adds N consoles + admirals each
streaming a busy region — a separate cost stacked on top, and one that likely shows
up as **client frame lag / bandwidth**, not as server `rtf` (networking is probably
its own thread/budget). So these numbers are a **no-client compute ceiling**; the
"how many active systems with M people watching" ceiling could be lower and
**network-gated**. A client-heavy run (several browser consoles/admirals on busy
systems, measuring client latency + bytes/sec) is the missing half.

**Run A — passive (asteroid-heavy).** Rode to the full 64 systems / **~100,000 agents
/ 193 NPCs at rtf ≈ 1.00, dead flat, CEILING never tripped.** Terrain is effectively
free; passive object count is *not* the constraint.

**Run B — active (brain-heavy: 8 fleets/system @ difficulty 9, asteroids off).**
Combat ships + steering + projectile churn. The curve:

| Phase | Systems | NPCs | Active agents | rtf |
|---|---|---|---|---|
| Flat (real-time) | 1–16 | ≤145 | ≤24k | ~1.01 |
| Knee | 17–23 | 154–207 | 26k–48k | 1.0 → 0.94 |
| **Ceiling trip** (rtf<0.95×3) | **23** | **207** | **48k** | **0.939** |
| Gentle decline | 23–45 | 207–388 | 48k–166k | 0.94 → 0.83 |
| **Stable plateau** | 45–64 | 388–536 | 166k–330k | **~0.75–0.83** |

**Reading:**
- **Real-time ceiling** for heavy active combat ≈ **190 ships / ~38k active agents**
  (~15–20 simultaneously-fighting systems of this density).
- **The roll-off is gradual and linear → compute-bound, NO O(n²) `role()` cliff.**
  Best-possible shape: the ceiling rises with hardware; there's no algorithmic
  landmine. Even at **3× overload (330k agents, 536 ships) it holds ~75% real-time**
  and finds a *stable degraded plateau* rather than spiralling to collapse.
- **Python GC flux is real but secondary** — sample-to-sample rtf jitter grew from
  ±2% early to ±5–10% past ~230k agents (GC pressure scales with live-object count),
  riding on top of the ~1%/system saturation trend. It adds noise, not the trend.
- **Passive ≠ active:** 100k passive agents = free; ~40–48k *active combat* agents =
  the knee. **Budget for what's actively fighting, not for total object count.**

### Design implication: don't standby terrain — cull the fighters, not the rocks

`sbs_utils.procedural.standby` culls objects out of the engine **sim + network** by
player proximity (the py Agent persists; it's an engine-side optimization only). The
perf data says **terrain is the wrong thing to feed it:**

- **Tick cost of passive terrain is near-zero** (100k passive agents held real-time),
  so standby saves ~nothing on the sim side.
- **Terrain is network-static** — streamed to a client once, then only on a *forced*
  update. There's no ongoing replication for standby to cull.
- **Standby doesn't shrink the Python heap** (Agent persists), so no GC benefit.
- It's **net-negative** for terrain: `retrieve` re-inserts into sim + network, so a
  player crossing the radius **re-sends parked terrain** (network burst + pop-in
  hitch) that resident terrain never causes.

**Rule:** keep terrain resident; aim standby at **active, brained, per-tick-
replicating content** (`standby_cull_fleets` — park the ships, pause the one fleet
brain). Terrain standby is justified only as an engine-side *memory* measure for
genuinely dormant, far, unlikely-to-be-visited systems — never as a per-tick or
network win. (Codified in `standby.py`'s docstring.)

*One thing to confirm empirically:* that a `retrieve` of parked terrain does trigger
a client re-send (the churn cost) — watch for terrain network traffic on retrieve.

---

## Feasibility verdict

- **Viewing different systems simultaneously: fully feasible now, zero engine
  changes.** Natural behavior of per-client vantage + coordinate separation.
  Multiple player ships *and* multiple admirals, each on their own region, all work
  with today's primitives.
- **Limiting factors are content-side, not engine-side:** the tick budget is now
  **measured and large** — ~190 actively-fighting ships / ~38k active agents at
  real-time, degrading gracefully (no cliff) far beyond that; passive content is
  nearly free (100k agents flat). Network cost per streamed view is the other axis.
  Coordinate budget is generous (design at ±1M/axis). Skybox scope resolved
  (per-client).
- **What makes it *feel* like real separate systems** (per-region lifecycle,
  objectives, skybox, "dormant until visited") is script architecture layered on the
  single sim — an OU design problem, and one the side-roster + persistence work is
  already pointed at.

---

## Target scope — Model A (coexisting systems), faking B

**The model.** OU today is a **galaxy of virtual systems, one live cell at a time**:
the galaxy map is a seed/UI grid (`(i,j)` = seed index, *not* world coordinates), and
a jump **wipes the current cell and regenerates the destination at origin (0,0,0)**.
The target is **Model A** — several virtual systems materialized **simultaneously at
distinct real coordinates**, players/admirals able to sit in different ones, jump/warp
between. We **fake Model B** (a seamless continuous galaxy) as *presentation* — fast
warp + a pre-spawned destination — over an A architecture. The far-apart coordinate
layout A requires is itself the fiction: **space is mostly dead space** — systems are
separated by vast emptiness you warp across — so the gaps between coordinate islands
read *as the galaxy*, not as a seam. The technical spacing constraint (bleed /
precision) becomes the narrative. True per-system instances (Model C) are impossible
(one sim).

**The core refactor: de-origin + don't-wipe.** OU-today → A means: spawn each live
cell at its own coordinate offset (not origin), and **proximity-cull far cells via
`standby` instead of wiping on jump**. The origin assumption is threaded through
`universe_enter_system`, so this is real work — but perf-de-risked (the engine holds
the multi-cell load), and `standby` is already the cull mechanism.

**Jump control must change (also the testing prerequisite).** Today the galaxy map
jumps **all player ships together** to the one shared cell — inherent to single-cell.
Model A needs:
- **Per-ship (or per-group) jump** — a ship jumps to a destination cell that becomes/
  stays live at *its own* coordinates, **without wiping other players' cells**. Two
  ships in the same cell share it.
- **Admiral self-jump** — admirals ride detached cameras, so "jumping" an admiral =
  repositioning its camera to a target system (and ensuring that system is live),
  independent of players.

This is the **prerequisite for testing multi-system at all** — you can't put players in
different systems without it.

**Client scope — tiered (don't commit to one number).**

| Tier | Players | Admirals | Status |
|---|---|---|---|
| **Must-hold** (design to this) | 4–8 ships | 1–2 | Almost certainly fine on both axes |
| **Stretch** (validate, don't assume) | up to 16 ships | up to 8 | Gate on the multi-client **network** run |

**The budget math.**
- **Viewers imply live systems:** ~24 max clients → ~24 systems with a viewer +
  standby-buffer neighbors → **~30–50 live at peak** — which the ±1M budget swallows
  (≥64 slots at 250k spacing). Coordinate *count* is not the constraint.
- **Passive content is ~free** (100k agents rode flat) — scenery/terrain density per
  system isn't perf-bound.
- **Active is a shared pool:** the ~190-fighting-ship ceiling is **across all
  simultaneously-hot systems**. Per-system active budget = 190 ÷ (systems in combat at
  once). Bound combat (player-driven / capped events) so only ~4–6 are hot at a time →
  each holds ~30–45 active ships; let the whole map ignite at once → each must be
  sparse. **This is the primary content-design lever.**
- **Spatial size:** OU's 50k radius is conservative; the sensible band is **~50–150k
  radius** — bounded not by the engine but by admiral scan (~40k) oversight (a bigger
  system can't be seen whole from one vantage). Precision is fine anywhere in ±1M.

**Still to measure before the stretch tier is real:** the **network run** (several
browser clients + admirals on busy systems — client latency + bytes/sec) and a
**content-accurate compute run** (perf_probe with OU's real per-cell mix). Compute is
manageable if combat is bounded; network is the genuine unknown.

---

## Next steps — one spike left

1. **Perf probe — DONE (real engine, 2026-07-03).** See "Measured: perf_probe
   results" above. Ceiling ≈ 190 active-combat ships / ~38k active agents at
   real-time; gradual compute-bound decline (no O(n²) cliff); passive content nearly
   free. Follow-ups if wanted: (a) calibrate the per-system template to a *real* OU
   system's mix for a content-accurate ceiling; (b) profile whether steering, brain
   ticks, or projectiles dominate the active cost; (c) the growing GC flux hints a
   pooling/allocation pass could lift the plateau.
2. **Coordinate precision measurement.** Via the `cosmos_devqueue` / EngineDriver
   path (drives the **real** Pybind engine — the mock is pure-Python float64 and
   can't reveal this): park a ship at 1M, 4M, 8M, 16M, command slow impulse, and log
   successive position deltas. When they quantize in >0.1u steps you've found
   float32's ulp and the true ceiling. → confirms the ±1M budget in Hard Limit #2.

Per-client skybox is confirmed working, so the visual-isolation question is closed.
Everything else here is high-confidence with current primitives.
