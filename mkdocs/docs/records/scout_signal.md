# The Fading Signal {#the-fading-signal}

| Fact | Value |
|---|---|
| Display | The Fading Signal |

A single scout, a beacon that should be dead, and a long quiet run to whatever is still transmitting from the edge of the chart.

## Scenario {#the-fading-signal-scenario}

| Fact | Value |
|---|---|
| Mode | story |

## Narrative {#the-fading-signal-narrative}

### A Voice in the Static {#the-fading-signal-narrative-signal-1}

| Fact | Value |
|---|---|
| At start | active |
| Done when | reach 1, -1 |
| Then | `reveal` [The Trail Goes Cold](#the-fading-signal-narrative-signal-2) |
| Scope | shared |

Deep-range sensors keep catching the same clipped distress loop, folded into the background hiss on a channel nobody has used in years. The bearing points coreward, out past the last charted buoy at (1, -1). Command wants eyes on it. Engage the jump drive on Navigation and follow the signal in.

### The Trail Goes Cold {#the-fading-signal-narrative-signal-2}

| Fact | Value |
|---|---|
| At start | secret |
| Done when | reach 3, -2 |
| Then | `reveal` [The Long Quiet](#the-fading-signal-narrative-signal-3) |
| Scope | shared |
| Reward | 120 credits |

The buoy is dead - just a relay, still dutifully bouncing a loop it can no longer read. But the registry tag finally resolves against the archive: TSN Meridian, a survey ship logged overdue eleven years ago and quietly struck from the rolls. Her last position was two jumps on, at (3, -2). Someone is still transmitting from a ship that is not supposed to exist.

### The Long Quiet {#the-fading-signal-narrative-signal-3}

| Fact | Value |
|---|---|
| At start | secret |
| Done when | scan 1 derelict |
| Scope | shared |
| Reward | 300 credits |

There she is - a cold hulk adrift off the lane, no power, no life, running lights gone dark a decade ago. And a beacon that should have died with its batteries, still whispering the same eleven-year-old words into an empty sky. Bring the science array to bear and find out what the Meridian has been calling for all this time.

## Goals {#the-fading-signal-goals}

### Answer the Signal {#the-fading-signal-goals-goal-answer}

| Fact | Value |
|---|---|
| At start | active |
| Done when | scan 1 derelict |
| Scope | shared |
| Win | true |
| Citation | The Meridian's beacon finally has a listener. Whatever she was calling into the dark for eleven years, this scout answered it - and flew home with the story her crew never could. |

Follow the signal to the TSN Meridian at (3, -2) and scan the derelict to read what her beacon has been repeating into the static since before you had a commission.

## Landmarks {#the-fading-signal-landmarks}

### TSN Meridian {#the-fading-signal-landmarks-meridian}

| Fact | Value |
|---|---|
| Kind | derelict |
| At | 3, -2 |

A Terran survey ship eleven years adrift, running lights long cold and hull scarred by whatever ended her survey - and one stubborn beacon still whispering into the static, patient as the dark it hangs in.
