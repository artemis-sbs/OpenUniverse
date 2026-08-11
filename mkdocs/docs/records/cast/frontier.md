# Frontier

## Frontier Command {#frontier-command}

| Fact | Value |
|---|---|
| Face | terran |
| Roles | tsn, command |
| Scene | frontier_hail |
| Color | `#4cf` |

Distant TSN fleet command, keeping a thin watch over the frontier.

## Doctor Sela Voss {#sela-voss}

| Fact | Value |
|---|---|
| Face | female |
| Roles | civilian |
| Pickup | 0, 0 |
| Deliver to | -5, 3 |
| Reward | 500 credits |
| Patience | 20m |
| Scene | sela_hail |
| Color | `#6cf` |

A xenobiologist needing passage from the home base to the Verdant worlds.

### Still waiting for passage {#sela-voss-sela-waiting}

| Fact | Value |
|---|---|
| Every | 4m |
| Escalates | with deadline |

> *One of:*
>
> - Doctor Voss is on the docking ring, if anyone is bound for the Verdant worlds.
> - Sela Voss here - still looking for passage out to Verdant. I can pay.
> - % Voss again. My window at the Verdant site closes, captain.
> - % I am asking around the ring now. Anyone headed out that way?
> - %% Last call. I need to be on a hull today or not at all.

### Gives up and goes {#sela-voss-sela-gives-up}

| Fact | Value |
|---|---|
| Whenever | quest waiting_sela_voss failed |
| Weight | 90 |
| Action | \- self departs |

> *One of:*
>
> - Never mind. I have found other arrangements.
> - Too late, I am afraid. I have taken a berth on a freighter.

## A Nervous Courier {#courier}

| Fact | Value |
|---|---|
| Face | male |
| Roles | civilian |
| Pickup | 6, 4 |
| Deliver to | 0, 0 |
| Reward | 600 credits |
| Sabotage | sensors, weapons, engines |
| Scene | courier_hail |
| Color | `#f84` |

A twitchy courier with a heavy sealed case, paying well for fast, quiet passage off the Iron Concord home. Too well.
