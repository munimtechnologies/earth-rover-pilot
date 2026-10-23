# pace-i: grade

MV2 of Munim, Inc. Graded with AI agents from the output fields of the `pace-i-v1` job. CC BY 4.0.

The predictions (`studies/pace-i/PREDICTION.md`, SHA-256 8a83e237…) were on main before any mission was flown: the job waited for them and recorded that hash and the time it fetched main in `fetched.json` (14:41:38 UTC on 2026-10-23, rover_pilot 0.13.0, pace_h.py db0306b3…). `tests.txt`: the study's own tests passed (tests_exit 0). 864 missions on seeds 85-108 took 1,586 s. `pace_i.py` and `test_pace_i.py` are published byte for byte as the job ran them.

**7 of 9 predictions held.** I6 and I9 missed.

| | prediction | result | |
|---|---|---|---|
| I1 | check: compared 18, identical 18, missing 0 | compared 18, identical 18, missing 0 | held |
| I2 | all 864 missions completed | 864 of 864 | held |
| I3 | measured: bridge+cf0.3 and bridge-r+cf0.3 vs cf0.3, `groups_slower` 0, `groups_lost` 0, \|share\| ≤ 0.005 on every course | both: slower 0, lost 0; share 0.0 on all 6 course rows | held |
| I4 | outage15: bridge-r+cf0.3 vs cf0.3 faster on all 3, share ≤ −0.04 each | faster 3/3; −0.0587 bayside, −0.0757 blocks, −0.0666 boulevard (24 of 24 seeds each) | held |
| I5 | outage45: bridge-r+cf0.3 vs cf0.3 faster on all 3, share ≤ −0.03 each | faster 3/3; −0.0656, −0.0714, −0.0690 (24 of 24 each) | held |
| I6 | outage45: bridge-r+cf0.3 vs bridge+cf0.3 faster on ≥ 2 courses | faster on 1 (blocks, 15 of 24, p 0.0023); **slower** on bayside (14 of 24 slower, p 0.0127) and boulevard (16 of 24, p < 0.001) | **missed** |
| I7 | cf0.3 `share_stopped` ≥ 0.05 (outage15) and ≥ 0.08 (outage45); bridge-r+cf0.3 at most half of cf0.3's on both | cf0.3 0.080 and 0.130; bridge-r+cf0.3 0.007 (≤ 0.040) and 0.061 (≤ 0.065) | held |
| I8 | measured: dr+cf0.3 vs cf0.3 slower on all 3 | slower 3/3: +6.66%, +1.60%, +6.95% (24, 23, 24 of 24 seeds) | held |
| I9 | bridge-r+cf0.3 pooled made good ≥ 0.85 (outage15) and ≥ 0.80 (outage45), `beat_human_pace` 72 on both; cf0.3 ≤ 0.80 on outage45 | 0.869 and 0.828 (held); beat_human_pace 72 and **70** (missed); cf0.3 0.768 (held) | **missed** |

## Decision rules

- **R1 applies: bridge+cf0.3 is chosen.** Against cf0.3, bridge+cf0.3 has `groups_slower` 0 and `groups_lost` 0 on all three profiles and is faster on 3 of 3 courses of each outage profile. bridge-r+cf0.3 also qualifies (slower 0, lost 0 everywhere; faster on 3 of 3 of each outage profile). But it is slower than bridge+cf0.3 on 2 courses of outage15 (bayside, boulevard) and 2 of outage45 (bayside, boulevard), so by the rule it is not the one chosen, and `--dead-reckon-gaps` does not gain the filter restart. I1 was not failed. So the next release (v0.15.0) makes bridging the real-rover default, `--no-dead-reckon` restores v0.14.0's pilot, and `--dead-reckon` keeps v0.13.0's. The `Pilot` class keeps its defaults. The release must fly a sample of pace-i's `bridge+cf0.3` missions exactly before it is published.
- R2 does not apply. R3 does not apply: the check found no difference. R4: this grade, the outputs and the code are published in `studies/pace-i/`, and the results go into the README and FINDINGS with the release.

## Key numbers

Pooled median m/s made good (72 missions each, cruise 0.8; human marathon pace 0.754):

| profile | cf0.3 (v0.14.0) | bridge+cf0.3 (chosen) | bridge-r+cf0.3 | dr+cf0.3 (v0.13.0) |
|---|---|---|---|---|
| measured | 0.877 | 0.878 | 0.877 | 0.825 |
| outage15 | 0.809 | 0.870 | 0.869 | 0.827 |
| outage45 | 0.768 | 0.829 | 0.828 | 0.793 |

Missions beating the human pace on outage45: cf0.3 44 of 72, bridge+cf0.3 69, bridge-r+cf0.3 70, dr+cf0.3 64. Share of time stood still: outage15 cf0.3 0.080, bridge 0.006; outage45 cf0.3 0.130, bridge 0.062.

bridge+cf0.3 against cf0.3: outage15 −6.32%, −7.23%, −6.71%; outage45 −6.98%, −6.81%, −7.24% (bayside, blocks, boulevard; 24 of 24 seeds faster on each).

## What the misses say

- **I6: restarting the GPS average after a gap did not pay.** The reasoning was that after 30 s on the wheels, a filter blending the first new fix with fixes from before the gap would put the rover about 18 m behind itself. The restart did make the position better: the 95th-percentile position error fell from 9.5-9.9 m to 8.1-8.2 m on outage15 and from 8.9-9.1 m to 8.1-8.3 m on outage45, and the 95th-percentile distance from the course on blocks fell from 10.7 m to 9.7-9.8 m. It paid on blocks (faster on both outage profiles), but cost 2-4 s on the straighter bayside and boulevard. There it also made more recovery manoeuvres (mean 0.9 against 0.5 per mission on outage15, 1.18 against 0.5 on outage45). A likely cause, not tested, is that a single fresh fix carries the full noise of one fix, which the average had damped. The differences are small (|share| ≤ 0.35%). This is the third time in these studies that a position closer to the truth did not steer faster (pace-g, pace-h).
- **I9: 45 s outages cost a few missions their margin.** With bridging, 69-70 of 72 missions beat the human pace on outage45, not all 72. The reckoner carries the position for at most 30 s after the last fix, so the rover still stands still for about the last 15 s of every 45 s outage (bridge+cf0.3: median 83-102 s a mission). Even so, without bridging only 44 of 72 beat it.

## Diagnostics not predicted

- On outage15 bridging stood still a median 3.5-12.6 s a mission against 119-148 s for cf0.3; on outage45, 83-102 s against 214-255 s.
- dr+cf0.3 (v0.13.0) beat cf0.3 through outages on blocks (−5.7%, −6.2%) and boulevard (−1.3%, −1.1%) but not on bayside (p 0.06 and 0.31), and bridge-r+cf0.3 beat it on every course of every profile.
- Steering stayed calm with bridging: mean |angular| 0.044-0.062 against 0.198-0.224 for dr+cf0.3 on measured and outage15.

## Limits

Simulated rovers only, so speeds are bounds on what a real sidewalk allows. Outages are all-or-nothing and of fixed length; a real GPS often wanders off by metres before it drops out, which this study does not model. The simulated wheels report the commanded speed exactly. None of this has been measured on a live Mini+.
