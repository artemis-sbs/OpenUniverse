# The Quiet Shore {: #quiet-shore}

A boarding site: a colony that is fine, welcoming, and lying.

Declared by a landmark carrying \`Site: quiet_shore\`. Everything here is content - the cast that beams down, the call that arrives when you dock, and the beats they play. The engine side is \`universe_sites.py\` (the seam) and \`universe_sites.mast\` (the arrival); neither knows a word of what follows.

\*\*Every role can reach TWO readings on its own, and the shed opens at \`learned \>= 3\`.\*\* Three is reachable by any crew because a short boarding party DOUBLES UP - one console speaks for several characters, so every role's readings are in play however many people are aboard. The two-per-role floor still matters: it is what keeps a reading worth taking rather than a duplicate of one already had. The first cut broke both rules at once - the engineer read \`cold\` in BOTH rooms and the science officer got nothing at all in the first, so before doubling up a single console could hold exactly one fact and the shed was unreachable, with the east cable looping between itself and the orchard forever. If a reading is moved, check that every role still reaches two DISTINCT facts.

\*\*Every room is REVERSIBLE, not just exitable.\*\* The east cable used to offer only two flavour loops and a gated shed, so a party that walked there under-informed could go back to nothing - the only way out was off the planet. A room whose options all loop is a dead end however many of them there are. Every room now leads BACK as well as on, and a gated \`%{learned \< 3}\` line says plainly that they have not found enough yet, rather than leaving the crew to guess whether the game is broken.

\*\*Every room offers a way home.\*\* The shed is the only scene that ENDS the visit on its own, and it is gated at \`learned \>= 3\` - so without a \`- \[Beam back up\]()\` in each room a party that gathers two readings is stuck walking between them with no exit at all. That is what happened the first time this was played.

\*\*The shape worth keeping.\*\* Every room offers each character something only they can do, and nobody can take all four. A reading that matters carries \`; learn \<name\>\`; the shed opens at \`if learned \>= 3\`. Three of the four, so there is no single correct route through Ferrow Landing, and \`learn\` is a set - walking back into a room you have already read counts once. What is wrong with Ferrow Landing is legible only when the party puts its readings together and finds they do not agree - which is the whole reason this is played by four people at four consoles rather than one person with a menu.

## Boarding Party {: #quiet-shore-team}

### Dr Sorel {: #quiet-shore-team-sorel}

| Fact | Value |
|---|---|
| Face | terran_female |
| Roles | boarding, medical |
| Color | `"#4cf"` |

Ship's surgeon. Reads bodies, and does not much care what the paperwork says.

### Chief Ruiz {: #quiet-shore-team-ruiz}

| Fact | Value |
|---|---|
| Face | terran_male |
| Roles | boarding, engineering |
| Color | `"#fc4"` |

Engineer. Trusts machines further than the people running them.

### Ensign Vale {: #quiet-shore-team-vale}

| Fact | Value |
|---|---|
| Face | terran_male |
| Roles | boarding, security |
| Color | `"#f66"` |

Security. Reads rooms. Notices what is missing before what is there.

### Lt Anders {: #quiet-shore-team-anders}

| Fact | Value |
|---|---|
| Face | terran_fluid |
| Roles | boarding, science |
| Color | `"#8f8"` |

Science officer. Would rather be right slowly than first.

## Voices {: #quiet-shore-voices}

### Administrator Bel {: #quiet-shore-voices-bel}

| Fact | Value |
|---|---|
| Face | terran_female |
| Roles | narrator |
| Color | `"#fd8"` |

Ferrow Landing's administrator. Delighted to see you. Has an answer ready for everything.

## Hails {: #quiet-shore-hails}

### Ferrow Landing Answers {: #quiet-shore-hails-shore-call}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |
| Title | Ferrow Landing |
| Color | `"#fd8"` |

> *One of:*
>
> - Ferrow Landing here, and you are very welcome. We are all fine. Nothing needed, nothing to report.
> - We had a quiet year, that is all. You are welcome to come down and see the place if you have the time.

- **Assemble a boarding party** *(signal boarding_down)*
- **Thank her and stay aboard**

## Scenes {: #quiet-shore-boarding}

### The Landing Field {: #quiet-shore-boarding-arrival}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Warm, still, and swept. Somebody has raked the gravel into lines this morning.
> - Eleven of us now. We manage. The children are at their lessons, so it is quieter than usual.

- **Look at the people meeting you** -> [The People Meeting You](#quiet-shore-boarding-arrival-med) *(if medical \>= 1)* *(learn thin)*
- **Look at the power spur** -> [The Power Spur](#quiet-shore-boarding-arrival-eng) *(if engineering \>= 1)* *(learn cold)*
- **Count the doors** -> [Counting The Doors](#quiet-shore-boarding-arrival-sec) *(if security \>= 1)* *(learn watched)*
- **Ask when the last supply run came** -> [The Last Supply Run](#quiet-shore-boarding-arrival-sci) *(if science \>= 1)* *(learn idle)*
- **Walk in with her** -> [The Long Hall](#quiet-shore-boarding-hall)
- **Beam back up**

### The People Meeting You {: #quiet-shore-boarding-arrival-med}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Four adults, all well fed, all with the same faint tremor in the hands.
> - Not illness. Not cold. You have seen it in people who have not slept properly in a long time and have stopped mentioning it.

- **Say it out loud** -> [The Landing Field](#quiet-shore-boarding-arrival)

### The Power Spur {: #quiet-shore-boarding-arrival-eng}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Rated for eleven, drawing for forty. Every one of those amps is going somewhere and it is not going into these buildings.
> - The cable heading east is the newest thing on this colony.

- **Say it out loud** -> [The Landing Field](#quiet-shore-boarding-arrival)

### Counting The Doors {: #quiet-shore-boarding-arrival-sec}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Nine doors on the square, and every one of them opens inward and locks from the outside.
> - That is not how you build against weather.

- **Say it out loud** -> [The Landing Field](#quiet-shore-boarding-arrival)

### The Last Supply Run {: #quiet-shore-boarding-arrival-sci}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Fourteen months, she says, and the manifest agrees with her.
> - What it also says is that they ordered nothing on it. Not one item. A colony that needs nothing is a colony that has stopped planning.

- **Say it out loud** -> [The Landing Field](#quiet-shore-boarding-arrival)

### The Long Hall {: #quiet-shore-boarding-hall}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Tables for forty and eleven place settings, laid at the near end where the light is.
> - We keep it as it was. It seemed better than taking the rest away.

- **Look at the place settings** -> [The Place Settings](#quiet-shore-boarding-hall-med) *(if medical \>= 1)* *(learn tended)*
- **Look at what is heating this room** -> [What Is Heating This Room](#quiet-shore-boarding-hall-eng) *(if engineering \>= 1)* *(learn idle)*
- **Look at the far end** -> [The Far End](#quiet-shore-boarding-hall-sec) *(if security \>= 1)* *(learn tended)*
- **Read the colony register** -> [The Colony Register](#quiet-shore-boarding-hall-sci) *(if science \>= 1)* *(learn thin)*
- **Ask to see the east cable** -> [The East Cable](#quiet-shore-boarding-east)
- **Beam back up**

### The Place Settings {: #quiet-shore-boarding-hall-med}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Eleven laid, and every one of them worn at the same corner by the same right-handed grip.
> - One person set all of these, every day, for a long time.

- **Say it out loud** -> [The Long Hall](#quiet-shore-boarding-hall)

### What Is Heating This Room {: #quiet-shore-boarding-hall-eng}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Nothing is. The heat in here is coming through the east wall, from something on the other side of it that is running hot.
> - You could warm this hall on the waste alone, and nobody has thought to.

- **Say it out loud** -> [The Long Hall](#quiet-shore-boarding-hall)

### The Far End {: #quiet-shore-boarding-hall-sec}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Dust on the tables, and no dust on the floor between them. That floor is walked every day and never sat at.
> - Something goes down this hall regularly. It does not stop to eat.

- **Say it out loud** -> [The Long Hall](#quiet-shore-boarding-hall)

### The Colony Register {: #quiet-shore-boarding-hall-sci}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Forty one names. Eleven without a line through them, and the lines are all in the same hand and the same ink.
> - They were not crossed out as it happened. Somebody sat down one afternoon and did all thirty at once.

- **Say it out loud** -> [The Long Hall](#quiet-shore-boarding-hall)

### The East Cable {: #quiet-shore-boarding-east}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - It runs a kilometre to a shed with no windows, and the shed is the warmest thing on this world.
> - That is the relay. It is not interesting. I would rather show you the orchard.
> - *(if learned \< 3)* She says it pleasantly and does not move. You have nothing to put to her yet - whatever is wrong with Ferrow Landing, you have not found enough of it to say out loud.

- **Ask her plainly what is in the shed** -> [Asking Plainly](#quiet-shore-boarding-east-ask)
- **Open it** -> [The Shed](#quiet-shore-boarding-open) *(if learned \>= 3)*
- **Let her show you the orchard** -> [The Orchard](#quiet-shore-boarding-orchard)
- **Walk back to the hall** -> [The Long Hall](#quiet-shore-boarding-hall)
- **Beam back up**

### Asking Plainly {: #quiet-shore-boarding-east-ask}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - It is the relay.
> - She says it the same way both times, with the same pauses. You have heard a person say a true thing twice. This is not what that sounds like.

- **Back to the shed** -> [The East Cable](#quiet-shore-boarding-east)

### The Orchard {: #quiet-shore-boarding-orchard}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Thirty saplings in rows, none of them older than a year, each with a stone at its foot.
> - We plant one for each of them. It is what we could think of.

- **Go back to the shed** -> [The East Cable](#quiet-shore-boarding-east)
- **Walk back to the hall** -> [The Long Hall](#quiet-shore-boarding-hall)

### The Shed {: #quiet-shore-boarding-open}

| Fact | Value |
|---|---|
| Speaker | [Administrator Bel](#quiet-shore-voices-bel) |

> *One of:*
>
> - Thirty of them, warm, breathing, and asleep. The machine keeping them that way is drawing every spare amp on the colony and Bel is not stopping you looking at it.
> - We could not wake them. We could not bury them either. So we kept them, and we set their places, and we said we were fine.

- **She was not lying, exactly**
