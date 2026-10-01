# Cache Raiders

Cache Raiders is a small Pygame CE demo for a live talk about two ways to
organize game data: one object per entity (array of structures, or AoS) and
one packed array per field (structure of arrays, or SoA).

The demo keeps the code paths visible and lets you switch layouts while the
game runs. It is intended to make the tradeoffs easy to discuss, not to serve
as a general-purpose game engine or a benchmark across all hardware.

## Run the demo

Requirements: Python 3.14 or later and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run cache-raiders
```

The rocket image is included as package data, so the installed command does
not depend on the directory from which you launch it.

## Controls

| Key | Action |
| --- | --- |
| `R` | Add 20 ships |
| `F` | Remove 20 ships, keeping at least one |
| `B` | Switch particle storage between AoS and SoA |
| `V` | Switch player-position storage between AoS and SoA |
| `P` | Add one particle per emission and emit a 60-particle burst |
| `O` | Reduce particles per emission |
| `Shift` + `=` | Increase ship speed |
| `-` | Reduce ship speed |

The HUD shows live ship, particle, object, and frame-rate counts, along with
the selected storage modes.

## What the comparison shows

In AoS mode, particles are `Particle` objects and each player's position is a
`Vector2`. In SoA mode, particle fields and player position/speed fields live
in packed arrays. Each player continues to own its particle emitter.

Switching modes transfers live state, so particles and ships continue from
their current positions and ages. The player comparison times only movement
updates, leaving particle simulation and drawing outside that measurement. The
HUD reports rolling averages from the latest 120 frames and names a faster
layout after it has at least 30 samples for each mode. Adding or removing ships
clears those samples. Keep the ship count steady while comparing; the overall
FPS also includes drawing and particle work.

## Build a package

```sh
uv build
```
