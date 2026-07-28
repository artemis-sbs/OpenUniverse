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

**Next: [Captains and the cast](people.md)** - give the galaxy faces.
