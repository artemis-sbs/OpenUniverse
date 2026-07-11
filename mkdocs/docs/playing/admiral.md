# How to play the Admiral

Most of the bridge flies ships. **You command the war.** The Admiral runs the
whole side from above - mining worldlets, building platforms, raising fleets, and
climbing a tech ladder - while the other consoles do the flying and fighting.
This page is how to play that role, start to finish.

!!! note "Where the Admiral lives"
    Open the **Admiral** console from the bridge. If your universe has no
    Admiralty (some don't), the console simply isn't there - that's up to whoever
    wrote the universe (see [writing the Admiralty](../writing/admiralty.md)).

!!! note "More than one Admiral"
    A universe can field **more than one player-commanded side**. When it does,
    each side has **its own Admiral** running **its own** economy, fleets, and
    research - you command **your** side, and the map you ride shows your side's
    view of the system. Whether the other sides are **allies** (a co-op war) or
    **rivals** is up to the universe.

## The command view

The Admiral doesn't sit on a ship. You ride a **camera high over the current
system** - a god's-eye 2D map of everything on your side. (A second view, the
**Galaxy** tab, zooms out to the whole map of star systems - see [the galaxy
map](#the-galaxy-map-commanding-across-systems) below.) You give every order by
**selecting things on that map**:

- **Click empty space** - the view pans there. Use it to reach worldlets and
  fleets out past the edge.
- **Click an object** - it's selected (the view recenters on it) and its actions
  appear on the right.
- **Zoom control** - above the map; zoom out to see the whole system at once.

Two readouts keep you informed:

- **The ticker** (top): `ORE` / `GAS` / `CREW` stockpiles, each `held / cap`, and
  `CMD` - your command points (fleets in play / maximum).
- **The status panel** (right, under the menu): what's under construction, the
  result of your last order, and hints like *"No extractors yet."*

## Your first five minutes

The opening is always the same, and there is one trap in it. Follow this:

1. **Find your worldlet.** Every home system has one - a lone planet out on the
   ring. Zoom out or pan until you see it, then click it.
2. **Build an HQ.** It's the only option at first. Wait for it to finish (the
   status panel shows the progress).
3. **Build an Extractor.** Click the worldlet again - now the menu has grown.
   Build the Extractor.
4. **Watch the ticker.** Ore and gas start climbing. You now have an economy.

!!! warning "The trap: don't overspend before the Extractor"
    An HQ and the first Extractor together cost more than your starting pile has
    to spare - and **nothing produces income until that Extractor is up**. Build
    the HQ, then the Extractor, *before* anything else. (And if you turned on the
    crew subsidy, turn it back off until the ore is flowing - it only drains.)

## Building the base

Click any of your **worldlets** or **platforms** to build or command. Each new
platform unlocks the next, so the menu grows as you go. The kit:

| Platform | What it gives you |
|---|---|
| **HQ** | The hub. Your first build; everything else needs it. |
| **Extractor** | Pulls a worldlet's yield into your stockpiles. Your income. |
| **Refinery** | Speeds up its worldlet and raises your storage cap. |
| **Academy** | Lets you commission officers into fleets. |
| **Shipyard** | Where fleets are built - and where research happens. |
| **Lab** | Runs research; one project per Lab at a time. |
| **Sensor Relay** | +1 command point, and charts the neighbouring systems. |
| **Depot** | Keeps fleets fuelled when they operate far from home. |
| **Bastion** | Draws and holds border raids - your fortress. |

Extractors sit **on worldlets** (build them by clicking the worldlet); the rest
are your infrastructure. Spread Extractors across different worldlets to pull ore,
gas, and crew all at once.

## Raising and commanding fleets

The navy is how you project force across the system.

1. **Build an Academy and a Shipyard.** Fleets need both.
2. **Commission a captain.** Click the **Shipyard** - your available officers are
   offered. Pick one, and a fleet forms at the yard. Each fleet costs one
   **command point** (the `CMD` number caps how many you can field; Sensor Relays
   raise it).
3. **Give orders.** Click any of that fleet's ships and choose:
   - **Escort** - guard the flagship.
   - **Patrol** - sweep the system.
   - **Strike** - hunt and engage hostiles.
   - **Hold** - stay put.
   - **Salvage** - strip wrecks for ore and gas.
   - **Withdraw** - return to base.

Captains **get better with service** - a veteran deepens the strengths they were
built for. Which is why losing one hurts: a flagship can go down, and the
captain's pod has only a short window to be **rescued** before they're captured
(ransom them at the captor's stations) or lost for good. Fleets also burn **gas**
on active orders and won't operate inside an antimatter **veil** - keep them
fuelled and out of the lethal systems.

## The galaxy map - commanding across systems

Everything above is your **home system**. To command the wider galaxy, open the
**Galaxy** tab. The command camera rides out to a strategic **map of star systems** -
one icon per system, meshed and coloured by what's there (your bases, foes, nebulae,
unexplored fog). It's your whole theatre at a glance, and where you move forces
**between** systems.

**Click a system**, and its orders appear:

- **Send \<captain\> here** - dispatch that fleet to the system. It travels, arrives,
  and takes orders there (a fleet holds a system *live* while it's on station).
- **Send \<ship\> here** - vector a **player ship** to the system. You're the strategic
  navigator: crews fly locally, you move them between systems. (A ship already in the
  selected system isn't offered - no point sending it where it is.)
- **Focus here** - take **yourself** (the command camera) to that system to oversee it
  up close.
- **Known locations** - a shortcut list of notable systems (home, clan capitals, active
  objectives) to focus on without hunting the map.

Your own forces show as **live icons** on the map: **player ships** are health-tinted
fighters (green -> amber -> red as shields fall), **fleets** are gold battle-cruisers
labelled with their officer and order. Each icon is labelled with **its system** (e.g.
`Artemis (2,3)`) and, while travelling, where it's headed (`->(2,3)`). Icons show out to
the edge of the map view; the map updates as forces move - no need to reopen it.

Beside the map, the **Forces** list ("who is where") names **every** friendly ship and
fleet and the system it's in - including forces too far away to fit on the map view.
**Click a row to focus** on that unit's system.

!!! note "Your own galaxy map"
    With more than one Admiral, **each commands its own galaxy map**, centred on its own
    theatre - your orders and your board never disturb another Admiral's.

!!! note "How crews travel on their own"
    You aren't the only way a ship moves. A bridge crew **takes a job** and travels to it:
    the **Quests tab** has an **Engage** button that jumps the ship to its current
    objective. So movement is *purposeful* - the Admiral vectors the fleet, and crews
    pursue their own contracts - with no free-roam map to babysit.

## Research

Build a **Lab**, then click it to see the tech ladder. Each project costs
resources and time, some require an earlier one first, and they unlock real
upgrades - **bigger storage**, **faster extraction**, or new **requisition**
hardware for the bridge crews. Every Lab you build lets you run one more project
at once.

## Keeping the economy healthy

- **Storage caps** limit each stockpile. Refineries and research raise them; a
  full pool wastes income, so spend or expand.
- **Crew subsidy** (click the **HQ**) discounts station prices for your crews -
  paid for out of your stockpiles, so it's a lever, not free. Stand it down when
  the pools run thin.
- **Command points** cap your fleets. Want a bigger navy? Build **Sensor Relays**.
- **Depots** keep distant fleets supplied; **Bastions** soak up the border raids
  that come with sitting next to hostile territory.

## Seeing the galaxy

A **Sensor Relay** doesn't just add a command point - it **charts the neighbouring
systems**, revealing what's out there (they light up on the **Galaxy map** above)
without a scout having to fly the jump. Relays you leave behind also keep sending a
share of their system's income home, so an expanding network pays you even while the
fleet moves on.

---

That's the whole loop: **mine, build, expand, command.** Start with an Extractor,
grow the base that lets you field a navy, and command it across the galaxy the
rest of the bridge is flying through.
