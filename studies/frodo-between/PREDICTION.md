# frodo-between-v1: the compass between its 1 Hz reads, as a live pilot sees it

Pre-registered 2026-10-22 (~01:40 UTC), before frodo-between-v1 ran. MV2 of Munim, Inc.; written with AI agents. CC BY-SA 4.0 (results derive from FrodoBots-2K).

## Why

Every FrodoBots-2K compass study so far (frodo_compass, frodo_compass_live, frodo_blend, frodo_blend_b) gave each 0.2 s cell a heading **interpolated** between the 1 Hz magnetometer samples on either side of it. So inside each gap the heading uses a sample up to about a second in the future. A pilot driving the rover only has the samples it has already read. This study measures what that look-ahead was worth: it scores headings a live pilot can actually compute. It also asks whether the gyroscope or the turn command can fill the gap between compass reads.

## Design (fixed before the run)

- Rides, anchors, skip rules, running hard-iron fit and learned bias are frodo_blend_b 0.1.0's: in each of the 24 parts, 30 rides spread evenly through those frodo_blend's sample left out (same `held_out`). Same horizons. Every variant is scored on the same anchors.
- Variants, all with the running fit's bias (learned from the interpolated headings, so the anchors stay identical):
  - `interp`: frodo_blend_b's `running` (the reference; uses up to ~1 s of future compass).
  - `last`: the latest compass sample at or before the cell, held.
  - `gyro05`, `gyro1`: `last` turned by 0.5x / 1x the gyroscope's x-axis turn since that read. The rate is the latest gyroscope sample at or before the cell, at most 1.5 s old, less the median gyroscope reading over the first 300 s of compass data.
  - `cmd20`: `last` turned by the angular command since that read, at 20 deg/s per unit, 0.5 s behind the command.
  - `b2_<each>`: v0.11.0's course hold on that heading (the last GPS course for 2 s, then the heading with the difference fading out over 2 s more).
  - `course`: the last GPS course.
- 95% intervals: 200 resamples of rides, seed 1.

## Check (E1)

At 10 s, at least 2,000 pairs, `interp`/`course` within 0.002 of 0.883 and `b2_interp`/`interp` within 0.002 of 0.944 (frodo-blend-b-v2's `running`/`course` and `blend2`/`running`). If not, nothing is decided. Expected: an exact match on 13,460 pairs, since the code path and rides are the same.

## Decision rules

- **D1 (always reported):** `last`/`interp` at 10 s and 30 s is the cost of the look-ahead. FINDINGS-frodobots-2k.md will report the `last` figures as what a live pilot gets, beside the interpolated ones.
- **D2:** a between-read heading X in {gyro05, gyro1, cmd20} is worth building into the pilot (behind an off-by-default switch, then a held-out check) only if X/`last` at 10 s <= 0.98, its 95% CI's top is below 1, and X over course at 30 s is no more than 0.02 above `last` over course. If several pass, the lowest X/`last` at 10 s. Otherwise nothing is built.
- **D3:** v0.11.0's course hold stays if `b2_last`/`last` at 10 s <= 0.97 with the CI's top below 1. Otherwise FINDINGS will say that the hold's gain was measured on an interpolated compass, and the hold is re-examined on `last`.

## Predictions

- **P1:** E1 passes with exactly 13,460 pairs at 10 s.
- **P2:** `last`/`interp` at 10 s is between 1.00 and 1.05 (the live compass costs at most 5%).
- **P3:** `gyro05`/`last` at 10 s <= 1.00.
- **P4:** `gyro1`/`last` at 10 s is greater than `gyro05`/`last` (the full gyroscope turn overshoots, as in frodo_odometry).
- **P5:** `cmd20`/`last` at 10 s is between 0.98 and 1.01.
- **P6:** D3 is met (`b2_last`/`last` <= 0.97, CI top below 1).
- **P7:** D2 builds nothing.
- **P8:** `last`/`interp` at 30 s is at most 1.03.

## Limits known in advance

- Earth Rover Zero, raw 1 Hz magnetometer and 1 Hz gyroscope. A Mini+ reports an on-board `orientation` at its own rate, so a Mini+ pilot may see a smaller gap.
- The bias every variant uses was learned from interpolated headings. It is learned on straight stretches, where `last` and `interp` nearly agree.
- The reference is the next GPS fix, not surveyed truth.
- The gyroscope's units are inferred (deg/s), not documented.
