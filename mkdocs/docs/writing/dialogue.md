# Dialogue

Dialogue scenes are written the way a screenwriter drafts them - a scene, some
alternate line readings, and the other character's possible replies. This is
deliberately *not* a scripting language; if a scene starts feeling like code,
it has gone wrong.

Add a `## Dialogue` chapter:

```
## [Dialogue](dialogue)

### [Veil Hail](veil_hail)
---
Speaker: veil
When: comms
---
% Well now. Fresh freight, flying no colors we fear.
% You are a long way from the lanterns, captain.

- [Back away slowly](veil_parting)
- [Warn them off](veil_standoff) if fearsome > 20
- [Offer a toll](veil_toll) if credits >= 200

### [The Toll](veil_toll)
---
Speaker: veil
---
% Smart. The Reach teaches quick or it buries slow. Leave the crates.

- [Pay it](veil_parting) ; costs 200 credits, earns veil selfish 5

### [Standoff](veil_standoff)
---
Speaker: veil
---
% Big words for a convoy dog. Say them again with your guns lit.

- [Hold your course](veil_parting) ; earns veil fearsome 10
- [Stand down](veil_parting) ; earns veil cowardly 5

### [Parting](veil_parting)
---
Speaker: veil
---
% Fly on, then. The dark is patient.
```

## How to read a scene

- **Speaker** - whose face and name the message wears: a clan key, a captain
  key, or a cast key. `When: comms` marks the scene that opens when a player
  hails that speaker's station.
- **`%` lines are alternate takes.** The game performs *one*, at random.
  Write two or three so the character doesn't repeat like a recording.
- **A take can be conditional:** `%{standing < -20} You again. Bold.` plays
  only when its condition holds - so the same hail can read differently to a
  hated rival, a stranger, and a friend. First matching take wins.
- **`- [Label](next_scene)` lines are the player's replies.** The label is
  the line the player speaks; the `(key)` is the scene it leads to. Two
  optional clauses:
    - `if <condition>` - the reply is only offered when it's true
      (`if fearsome > 20`: only a feared captain gets the intimidation
      option).
    - `; <consequences>` - what choosing it does, comma-separated:
      `costs 200 credits`, `earns veil fearsome 10`, `signal veil_paid`.
- A scene with no replies (like *Parting*) simply ends the conversation.

Conditions can reference the seven trait poles, `credits`, and - in a
captain's scene - `standing`, his personal opinion of the player. That
vocabulary is the whole of it, and that's on purpose.

!!! success "In play"
    Hail a Veil station and the scene tree above *is* the conversation - with
    the player's reputation deciding which lines exist.

## Every voice needs a scene

Any character whose fact sheet names a `Scene:` (Harbormaster Quill, Brother
Calen) needs that scene written here, with the character's key as `Speaker:`.
The [complete example](silver-reach.md) shows them all wired up.

**Next: [The dials](dials.md)** - only if you want them.
