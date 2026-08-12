# Ashfang

## Ashfang Hail {: #ashfang-hail}

| Fact | Value |
|---|---|
| Speaker | `ashfang` |
| When | comms |

> *One of:*
>
> - You're a long way from friends, captain.
> - Brave or stupid, flying in here. Hard to tell which.

- **Apologize and back off** -> [Back Off](#ashfang-backoff)
- **Threaten them** -> [Standoff](#ashfang-standoff) *(if fearsome \> 20)*
- **Offer a cut of your cargo** -> [The Deal](#ashfang-deal) *(if credits \>= 200)*

## The Deal {: #ashfang-deal}

| Fact | Value |
|---|---|
| Speaker | `ashfang` |

> Hah. Maybe you're smarter than you look. Leave the crates and go.

- **Hand it over** -> [Done](#ashfang-done) *(costs 200 credits)* *(earns ashfang selfish 5)* *(signal ashfang_paid)*

## Standoff {: #ashfang-standoff}

| Fact | Value |
|---|---|
| Speaker | `ashfang` |

> Bold. We respect bold... right up until we don't.

- **Hold your ground** -> [Done](#ashfang-done) *(earns ashfang fearsome 10)*
- **Think better of it** -> [Back Off](#ashfang-backoff) *(earns ashfang cowardly 5)*

## Back Off {: #ashfang-backoff}

| Fact | Value |
|---|---|
| Speaker | `ashfang` |

> Smart. Run along, little ship.

## Done {: #ashfang-done}

| Fact | Value |
|---|---|
| Speaker | `ashfang` |

> We're done here. For now.

## Vex Karr {: #vex-hail}

| Fact | Value |
|---|---|
| Speaker | `vex` |
| When | comms |

> *One of:*
>
> - *(if standing \< -20)* You. The captain who crossed me. Bold, showing that face out here.
> - *(if standing \>= 30)* Karr's heard of your work. The Ashfang could use a hand like yours.
> - Vex Karr. You've heard the name. State your business.

- **Match his menace** -> [Parting](#vex-parting) *(earns vex fearsome 10)*
- **Grovel** -> [Parting](#vex-parting) *(earns vex cowardly 10)*
- **Say nothing** -> [Parting](#vex-parting)

## Parting {: #vex-parting}

| Fact | Value |
|---|---|
| Speaker | `vex` |

> We'll cross paths again, captain. Count on it.
