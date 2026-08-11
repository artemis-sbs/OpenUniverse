# Frontier

## Frontier Command {#frontier-hail}

| Fact | Value |
|---|---|
| Speaker | `frontier_command` |
| When | comms |

> *One of:*
>
> - Frontier Command here, captain. You're a long way from home.
> - Report when able. We read what the sides make of you out there.

- **Report in** -> [Out](#frontier-done)
- **Request guidance** -> [Guidance](#frontier-advice)

## Guidance {#frontier-advice}

| Fact | Value |
|---|---|
| Speaker | `frontier_command` |

> *One of:*
>
> - Keep your standing clean with the neutral sides; the foe systems will test you.
> - Watch the Ashfang lanes - their captains hold grudges.

- **Understood** -> [Out](#frontier-done)

## Out {#frontier-done}

| Fact | Value |
|---|---|
| Speaker | `frontier_command` |

> Frontier Command out. Stay sharp, captain.

## Doctor Sela Voss {#sela-hail}

| Fact | Value |
|---|---|
| Speaker | `sela_voss` |
| When | comms |

> *One of:*
>
> - Thank you for the passage, captain. The Verdant worlds are a long way out.
> - Mind the Ashfang lanes - I'd rather arrive in one piece.

- **Reassure her** -> [Settled In](#sela-done)
- **Say nothing** -> [Settled In](#sela-done)

## Settled In {#sela-done}

| Fact | Value |
|---|---|
| Speaker | `sela_voss` |

> I'll be in the observation lounge if you need me.

## A Nervous Courier {#courier-hail}

| Fact | Value |
|---|---|
| Speaker | `courier` |
| When | comms |

> *One of:*
>
> - I paid for passage, not an interrogation. Eyes forward, captain.
> - ...is something wrong? You're looking at me strangely.

- **Let it go** -> [Move Along](#courier-done)
- **Detain him** -> [Caught](#courier-caught) *(signal detain_saboteur)*

## Caught {#courier-caught}

| Fact | Value |
|---|---|
| Speaker | `courier` |

> You don't know what you've just stopped, captain. They'll send another.

## Move Along {#courier-done}

| Fact | Value |
|---|---|
| Speaker | `courier` |

> Smart. Mind your own business and we'll get along fine.
