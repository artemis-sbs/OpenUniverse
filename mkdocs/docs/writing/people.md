# Captains and the cast

Sides are institutions. These two chapters give the galaxy *faces*.

## Captains

Captains are named NPCs of a side - a person a crew can meet, deal with, and
make an enemy of. A captain has personal `Values`, roams a system, and has one
dramatic hinge: `Rival when:` - the standing threshold at which they stop
being a character you talk to and start being a character who hunts you.

```
## [Captains](captains)

### [Mara Dusk](mara)
---
Side: veil
Title: the Lanternless
Values: fearsome 40, violent 30, resourceful 20
Flies: Torgoth
Roams: 5, -4
Rival when: standing < -20
---
The Veil's sharpest knife, said to have cut her own name out of the
Combine's convoy rolls. She keeps accounts, and she always collects.
```

`standing` here means the captain's *personal* opinion of the player - cross
Mara enough times and the `Rival when:` line makes it a vendetta.

## The cast (Lifeforms)

Cast members are comms characters - voices on the radio. A cast member with no
location is hailable anywhere: your recurring narrator, dispatcher, or mystery
voice.

```
## [Lifeforms](lifeforms)

### [Harbormaster Quill](quill)
---
Face: terran
Roles: lantern
Scene: quill_hail
Color: #ffcc44
---
The Combine's unflappable harbormaster - the voice that has talked a
thousand freighters through the dark, and does not intend to lose yours.
```

`Face:` is `terran` / `male` / `female` (a random face of that kind);
`Scene:` names the dialogue scene that is this character's voice - which is
the [next page](dialogue.md).

## Passengers

A cast member with a `Pickup`, a `Deliver to`, and a `Pays` becomes a
**passenger** - offered for transport at one station, delivered to another:

```
### [Brother Calen](calen)
---
Face: male
Roles: civilian
Pickup: -4, 2
Deliver to: 5, -4
Pays: 500 credits
Scene: calen_hail
---
A quiet pilgrim paying convoy rates for passage into Veil country, of all
places. He does not say why, and he pays in advance.
```

!!! tip "The passenger who is not what he seems"
    Give a passenger a `Sabotage: sensors, weapons` line and he damages those
    systems mid-voyage until the crew confronts him. Use sparingly; the first
    betrayal is drama, the third is a pattern.

**Next: [Dialogue](dialogue.md)** - the words.
