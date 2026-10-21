# frodo-blend-b-v1: predictions (frozen 2026-10-21 ~20:10 UTC, when the job was queued)

By MV2 of Munim, Inc.; written with AI agents. Code Apache-2.0; FrodoBots-2K data CC BY-SA 4.0.
Everything below was written before the job ran and is graded as written.

## Why
frodo-blend-a-v1 (frodo_blend.py 0.1.0; 146 FrodoBots-2K rides with pairs, 14,172 pairs at 10 s)
found that holding the last GPS course for 2 s after a fix, then switching to the live-calibrated
compass with the difference fading out over 2 s more (`blend2`), missed the fix 10 s later by
1.60 m, against 1.72 m for the compass alone (`running`) and 1.85 m for the course alone:
blend2 / running = 0.930 (95% CI 0.917-0.953). By its pre-stated rule D1 that adopts blend2.
But B = 2 was the best of three holds (2, 5, 10 s) on those same rides, and its rule D2 turned
out not to look at the sign: the hard switch at 5 s beat the fading one by 0.047. So before the
pilot's default changes, this checks blend2 on rides that sample did not contain, and scans the
hold from 1 to 4 s, hard and fading.

## Design
- Rides: in each of the 24 parts, the usable rides that `fm.pick_evenly(usable, 30)` (the sample
  of frodo-blend-a-v1 and frodo-compass-live-v1) did not pick, and 30 of those spread evenly
  (fewer where fewer are left). A unit test checks that no ride is shared.
- Variants, all causal and on the same anchors: `course`, `running` (as in frodo_blend), `hard1`
  to `hard4` (course for B s, then the compass with no shift), `blend1` to `blend3` (course for
  B s, then the compass shifted onto the course, the shift fading out over B s more).
- Ride analysis: frodo_blend's, with the variants passed in. A unit test checks that with
  frodo_blend's six variants it gives frodo_blend's misses exactly. frodo_blend.py 0.1.0 is
  imported, not copied; frodo_compass(_live) from v0.10.0; frodo_motion.py from v0.8.0.

## Rules (implemented in frodo_blend_b.decide)
- E1: test_frodo_compass, test_frodo_compass_live, test_frodo_blend and test_frodo_blend_b pass.
- Check: at least 2,000 pairs at 10 s, or nothing is decided.
- C1 (confirmation): blend2 / running at 10 s <= 0.97 AND the top of its 95% CI (rides
  resampled, 200 reps) below 1.00.
- C2 (no cost later): blend2 minus running, each over course at 30 s, <= 0.02.
- If C1 and C2 hold, blend2 is confirmed and the pilot gets a course hold. S1: the setting is
  blend2, unless another hold beats it at 10 s by at least 0.01 (over course) and is not worse
  than running at 30 s by more than 0.02; then that one. If C1 or C2 fails, the pilot keeps
  following the compass alone and the FINDINGS say the 2 s hold did not hold up.
- Transfer limit, stated up front: Earth Rover Zero, raw 1 Hz magnetometer, 1 Hz GPS. On a
  Mini+ with its on-board `orientation`, the hold is a starting value, not a measurement.

## Predictions (each graded met / not met)
- Q1: C1 and C2 hold; blend2 / running at 10 s lands in 0.90-0.97.
- Q2: running / course at 10 s lands in 0.864-0.985 (frodo-blend-a-v1's 95% CI).
- Q3: the best hold at 10 s is one of hard2, hard3 or blend2 (about 2-3 s of course in effect).
- Q4: at B = 2, hard2 and blend2 are within 0.01 of each other at 10 s.
- Q5: S1 keeps blend2.
- Q6: at 1 s, running / course > 1.00 (right after a fix the course is better).

If the first run's tests fail, the code is fixed and the job re-run as -v2; these predictions
stay frozen.

## Run log (added after the predictions; nothing above was changed)
- 2026-10-21, frodo-blend-b-v1: E1 failed before any ride was read. 61 of 65 tests passed; four
  decision-rule tests in test_frodo_blend_b.py raised `TypeError: keywords must be strings`,
  because they built their tables as `dict(BASE, **{(variant, h): x})` and Python allows only
  string keys there. frodo_blend_b.py itself was not at fault and is unchanged. The four tests
  now build the tables as `{**BASE, (variant, h): x}` with the same values and expectations,
  and the job is re-run unchanged as frodo-blend-b-v2.
