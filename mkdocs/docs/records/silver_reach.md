# The Silver Reach {#the-silver-reach}

| Fact | Value |
|---|---|
| Display | The Silver Reach |

A ribbon of frontier stars beyond the last patrol line. Freight moves by lantern-light convoys, and the dark between systems belongs to whoever claims it.

## Sides {#the-silver-reach-sides}

### The Lantern Combine {#the-silver-reach-sides-lantern}

| Fact | Value |
|---|---|
| Color | `#ffcc44` |
| Character | trader |
| Disposition | neutral |
| Home | -4, 2 |
| Offers | escort, bounty |
| Flies | Arvonian |
| Jump charge | [Lantern spool-up](#the-silver-reach-effects-lantern-charge) |
| Values | honest 40, generous 30, peaceful 20 |

Convoy families who keep the freight lanes lit. Fair dealers with long memories for a kept promise - and longer ones for a broken cargo contract.

### The Red Veil {#the-silver-reach-sides-veil}

| Fact | Value |
|---|---|
| Color | `#cc2244` |
| Character | pirate |
| Disposition | foe |
| Home | 5, -4 |
| Offers | smuggle, bounty |
| Flies | Torgoth |
| Jump charge | [Veil snatch](#the-silver-reach-effects-veil-charge) |
| Values | violent 40, fearsome 30, selfish 20 |

Corsairs of the outer dark. They take what the light forgets, and they respect exactly one thing: a captain more dangerous than they are.

## Jobs {#the-silver-reach-jobs}

### Convoy Escort {#the-silver-reach-jobs-escort}

| Fact | Value |
|---|---|
| Done when | dock station |
| Reward | 260 credits |
| Tier | 1 |

A lantern convoy needs a shepherd through the dark miles. See it safe to port and the Combine settles up.

### Veil Bounty {#the-silver-reach-jobs-bounty}

| Fact | Value |
|---|---|
| Done when | destroy 3 enemies |
| Reward | 300 credits |
| Tier | 1 |

The Veil has been working the lanes again. There is a standing price on their hulls - three will do for a start.

### Quiet Cargo {#the-silver-reach-jobs-smuggle}

| Fact | Value |
|---|---|
| Done when | recover 2 contraband |
| Reward | 480 credits |
| Tier | 2 |

Sealed crates, no manifest, no questions. Bring them in quietly and be paid the same way.

## Narrative {#the-silver-reach-narrative}

### The Dimming: A Cold Lane {#the-silver-reach-narrative-dimming-1}

| Fact | Value |
|---|---|
| At start | active |
| Done when | reach -4, 2 |
| Then | `reveal` [The Dimming: Ash on the Manifest](#the-silver-reach-narrative-dimming-2) |
| Scope | shared |

Three Combine convoys have gone dark in a month, and the Combine is quietly asking for outside help. Their harbormaster waits at the home lanterns at (-4, 2).

### The Dimming: Ash on the Manifest {#the-silver-reach-narrative-dimming-2}

| Fact | Value |
|---|---|
| At start | secret |
| Done when | scan 2 derelicts |
| Then | `reveal` [The Dimming: The Long Answer](#the-silver-reach-narrative-dimming-3) |
| Scope | shared |
| Reward | 200 credits |

The lost convoys did not vanish - something left the wrecks adrift off the lanes. Find them and read what is left in the hulls.

### The Dimming: The Long Answer {#the-silver-reach-narrative-dimming-3}

| Fact | Value |
|---|---|
| At start | secret |
| Done when | destroy 5 veil |
| Scope | shared |
| Reward | 600 credits |
| Standing | lantern honest 15, lantern generous 10 |

The manifests all point one way: the Red Veil is bleeding the lanes dry. The Combine will not say the word "war" - but they will pay well for captains who end this quietly.

## Goals {#the-silver-reach-goals}

### Break the Veil {#the-silver-reach-goals-goal-break-veil}

| Fact | Value |
|---|---|
| At start | active |
| Done when | destroy 15 veil |
| Scope | shared |
| Win | true |
| Citation | The Red Veil is broken and the lanterns burn the length of the Reach. The convoy families will tell this captain's story for a generation. |

End the Veil's grip on the Reach for good - fifteen of their hulls, however long it takes - and win the lanes their peace.

## Effects {#the-silver-reach-effects}

### Lantern spool-up {#the-silver-reach-effects-lantern-charge}

| Fact | Value |
|---|---|
| Look | charge |
| Size | 0.6 -\> 2.0 |
| Count | 10 -\> 80 |
| Speed | 0.5 -\> 3.0 |
| On | hull |
| Grows over | 3.5 seconds |
| Color | `#ffcc44, white` |

Convoy drives take their time and make no secret of it - lantern-gold light running the plating until the whole hull is lit, then gone.

### Veil snatch {#the-silver-reach-effects-veil-charge}

| Fact | Value |
|---|---|
| Look | charge |
| Size | 12 -\> 2 |
| Count | 20 -\> 120 |
| On | hull |
| Offset | 0, 0, 400 -\> 0, 0, 0 |
| Grows over | 3 seconds |
| Color | `#cc2244, white` |

Corsair drives bite before they let go. A red bloom stands off the hull and closes onto it, and the ship is simply not there any more.

## Regions {#the-silver-reach-regions}

### The Veilfall {#the-silver-reach-regions-veilfall}

| Fact | Value |
|---|---|
| Center | 5, -4 |
| Radius | 3 |
| Color | `#cc2244` |
| Skybox | sky-neb2-rvb |
| Music | Artemis2 |
| Enemy mix | 40% |
| Station mix | 5% |
| Mine chance | 75% |

Veil country. Red skies, salted lanes, and no honest ports for miles.

### The Lantern Lanes {#the-silver-reach-regions-lantern-lanes}

| Fact | Value |
|---|---|
| Center | -4, 2 |
| Radius | 3 |
| Color | `#ffcc44` |
| Skybox | sky-delight |
| Enemy mix | 0% |
| Station mix | 30% |

The Combine's home lanes - calm, bright, and busy. The safest miles in the Reach.

## Landmarks {#the-silver-reach-landmarks}

### The Pale Ark {#the-silver-reach-landmarks-pale-ark}

| Fact | Value |
|---|---|
| Kind | derelict |
| At | 1, -2 |

A colony ship a century adrift, lanterns long cold. Every spacer in the Reach has a story about what still walks her corridors.

### Lighthouse Station {#the-silver-reach-landmarks-lighthouse}

| Fact | Value |
|---|---|
| Kind | station |
| Side | lantern |
| Art | starbase_science |
| At | -4, 2 |

The Combine's great beacon at the heart of the home lanes - half port, half promise.

## Captains {#the-silver-reach-captains}

### Mara Dusk {#the-silver-reach-captains-mara}

| Fact | Value |
|---|---|
| Title | the Lanternless |
| Side | [The Red Veil](#the-silver-reach-sides-veil) |
| Flies | Torgoth |
| Roams | 5, -4 |
| Values | fearsome 40, violent 30, resourceful 20 |
| Rival when | standing \< -20 |

The Veil's sharpest knife, said to have cut her own name out of the Combine's convoy rolls. She keeps accounts, and she always collects.

## Lifeforms {#the-silver-reach-lifeforms}

### Harbormaster Quill {#the-silver-reach-lifeforms-quill}

| Fact | Value |
|---|---|
| Face | terran |
| Roles | lantern |
| Color | `#ffcc44` |
| Scene | [Quill Hail](#the-silver-reach-dialogue-quill-hail) |

The Combine's unflappable harbormaster - the voice that has talked a thousand freighters through the dark, and does not intend to lose yours.

### Brother Calen {#the-silver-reach-lifeforms-calen}

| Fact | Value |
|---|---|
| Face | male |
| Roles | civilian |
| Color | `#6cf` |
| Scene | [Calen Hail](#the-silver-reach-dialogue-calen-hail) |
| Pickup | -4, 2 |
| Deliver to | 5, -4 |
| Reward | 500 credits |

A quiet pilgrim paying convoy rates for passage into Veil country, of all places. He does not say why, and he pays in advance.

## Dialogue {#the-silver-reach-dialogue}

### Veil Hail {#the-silver-reach-dialogue-veil-hail}

| Fact | Value |
|---|---|
| Speaker | [The Red Veil](#the-silver-reach-sides-veil) |
| When | comms |

> *One of:*
>
> - Well now. Fresh freight, flying no colors we fear.
> - You are a long way from the lanterns, captain.

- **Back away slowly** -> [Parting](#the-silver-reach-dialogue-veil-parting)
- **Warn them off** -> [Standoff](#the-silver-reach-dialogue-veil-standoff) *(if fearsome \> 20)*
- **Offer a toll** -> [The Toll](#the-silver-reach-dialogue-veil-toll) *(if credits \>= 200)*

### The Toll {#the-silver-reach-dialogue-veil-toll}

| Fact | Value |
|---|---|
| Speaker | [The Red Veil](#the-silver-reach-sides-veil) |

> Smart. The Reach teaches quick or it buries slow. Leave the crates.

- **Pay it** -> [Parting](#the-silver-reach-dialogue-veil-parting) *(costs 200 credits)* *(earns veil selfish 5)*

### Standoff {#the-silver-reach-dialogue-veil-standoff}

| Fact | Value |
|---|---|
| Speaker | [The Red Veil](#the-silver-reach-sides-veil) |

> Big words for a convoy dog. Say them again with your guns lit.

- **Hold your course** -> [Parting](#the-silver-reach-dialogue-veil-parting) *(earns veil fearsome 10)*
- **Stand down** -> [Parting](#the-silver-reach-dialogue-veil-parting) *(earns veil cowardly 5)*

### Parting {#the-silver-reach-dialogue-veil-parting}

| Fact | Value |
|---|---|
| Speaker | [The Red Veil](#the-silver-reach-sides-veil) |

> Fly on, then. The dark is patient.

### Mara Dusk {#the-silver-reach-dialogue-mara-hail}

| Fact | Value |
|---|---|
| Speaker | [Mara Dusk](#the-silver-reach-captains-mara) |
| When | comms |

> *One of:*
>
> - *(if standing \< -20)* You. The Reach is not wide enough for what you owe me.
> - *(if standing \>= 30)* The Lanternless remembers her friends, captain. Speak.
> - Mara Dusk. You have heard the name. Choose your next words with care.

- **Match her menace** -> [Mara Parting](#the-silver-reach-dialogue-mara-parting) *(earns mara fearsome 10)*
- **Offer respect** -> [Mara Parting](#the-silver-reach-dialogue-mara-parting) *(earns mara kind 5)*
- **Say nothing** -> [Mara Parting](#the-silver-reach-dialogue-mara-parting)

### Mara Parting {#the-silver-reach-dialogue-mara-parting}

| Fact | Value |
|---|---|
| Speaker | [Mara Dusk](#the-silver-reach-captains-mara) |

> We will meet again, captain. The dark keeps all appointments.

### Quill Hail {#the-silver-reach-dialogue-quill-hail}

| Fact | Value |
|---|---|
| Speaker | [Harbormaster Quill](#the-silver-reach-lifeforms-quill) |
| When | comms |

> *One of:*
>
> - Lighthouse control to wandering freight - state your heading, captain.
> - Quill here. The lanes are listening, so make it brief and make it honest.

- **Ask about work** -> [Quill on Work](#the-silver-reach-dialogue-quill-work)
- **Sign off** -> [Quill Out](#the-silver-reach-dialogue-quill-done)

### Quill on Work {#the-silver-reach-dialogue-quill-work}

| Fact | Value |
|---|---|
| Speaker | [Harbormaster Quill](#the-silver-reach-lifeforms-quill) |

> *One of:*
>
> - The Combine posts work at every lantern port. Fly honest and it pays.
> - Convoys need shepherds and the Veil needs thinning. Take your pick.

- **Understood** -> [Quill Out](#the-silver-reach-dialogue-quill-done)

### Quill Out {#the-silver-reach-dialogue-quill-done}

| Fact | Value |
|---|---|
| Speaker | [Harbormaster Quill](#the-silver-reach-lifeforms-quill) |

> Lighthouse out. Keep your running lights on, captain.

### Calen Hail {#the-silver-reach-dialogue-calen-hail}

| Fact | Value |
|---|---|
| Speaker | [Brother Calen](#the-silver-reach-lifeforms-calen) |
| When | comms |

> *One of:*
>
> - Thank you for the berth, captain. I am no trouble; I keep to my prayers.
> - The Veilfall, yes. Everyone asks. Some debts are paid where they were made.

- **Ask what awaits him there** -> [Calen's Reason](#the-silver-reach-dialogue-calen-why)
- **Leave him be** -> [Calen Settles](#the-silver-reach-dialogue-calen-done)

### Calen's Reason {#the-silver-reach-dialogue-calen-why}

| Fact | Value |
|---|---|
| Speaker | [Brother Calen](#the-silver-reach-lifeforms-calen) |

> A grave, captain. I go to tend a grave. The rest is between me and the dark.

- **Say nothing more** -> [Calen Settles](#the-silver-reach-dialogue-calen-done)

### Calen Settles {#the-silver-reach-dialogue-calen-done}

| Fact | Value |
|---|---|
| Speaker | [Brother Calen](#the-silver-reach-lifeforms-calen) |

> Peace to your bridge, captain. I will be no bother.
