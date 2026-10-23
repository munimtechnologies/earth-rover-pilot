# pace-j grade: bridging GPS outages when the GPS wanders first

MV2 of Munim, Inc. Graded with AI agents. CC BY 4.0.

Predictions: `studies/pace-j/PREDICTION.md` (SHA-256 d156c227…, on main before the job fetched it; see `fetched.json`). Job `pace-j-v1`: fetched main at 2026-10-23T17:51:09Z (rover_pilot.py 0.14.0, pace_i.py d4dc9304… as pace-i-v1 ran it), `tests_exit` 0 (33 tests: test_pace_j and test_pace_i), then flew 864 missions in 1,788 s. Every number below is read from `summary.json` in this folder. The code is `pace_j.py` and `test_pace_j.py` as the job ran them (pace_j.py SHA-256 6a73b2fb…, test_pace_j.py bb82eb35…).

**Result: 9 of 9 predictions held. Rule R1 applies: bridging stays the real-rover default.**

## Predictions

| | prediction | result | |
|---|---|---|---|
| J1 | check: compared 18, identical 18, missing 0 | 18, 18, 0 | held |
| J2 | all 864 missions completed | 864 of 864 | held |
| J3 | bridge+cf0.3 against cf0.3: faster 3, slower 0, lost 0 on wander15 and wander45 | wander15 3/0/0; wander45 3/0/0 | held |
| J4 | bridge+cf0.3, wander15 against outage15: slower ≥ 2, every course's share in (0, +0.03] | slower 3; +0.0138, +0.0142, +0.0147 | held |
| J5 | cf0.3, wander15 against outage15: slower ≥ 2 | slower 3 | held |
| J6 | bridge+cf0.3 loses less pooled speed from outage45 to wander45 than from outage15 to wander15 | 0.824 → 0.819 (−0.005) against 0.870 → 0.857 (−0.013) | held |
| J7 | bridge+cf0.3 bayside p95 offset: wander15 ≥ outage15 + 1.5 m | 6.64 against 2.87 m (+3.77) | held |
| J8 | bridge+cf0.3 p95 position error: wander15 ≥ outage15 + 1.5 m on every course | bayside 12.80/9.67 (+3.13), blocks 12.93/9.61 (+3.32), boulevard 13.26/9.94 (+3.32) | held |
| J9 | bridge+cf0.3 beat_human_pace: 72 on wander15, ≥ 66 on wander45 | 72; 71 | held |

## Decision

- **R1 applies.** J1 held, and on both wander profiles `bridge+cf0.3` against `cf0.3` has `groups_slower` 0 and `groups_lost` 0 (and `groups_faster` 3). Bridging GPS outages on the wheels stays the real-rover default (v0.15.0). The README and FINDINGS get what wandering costs each pilot in the next documentation release.
- R2 does not apply: no course where wandering fixes made bridging slower than v0.14.0's pilot, so no gating study is needed to keep the default.
- R3 does not apply: the check found no difference (18 of 18 identical).

## What wandering costs (paired by seed against the same outages)

Median paired time difference per course (bayside / blocks / boulevard), as a share of the clean-outage median:

| variant | wander15 vs outage15 | wander45 vs outage45 |
|---|---|---|
| cf0.3 (v0.14.0) | +21 / +17 / +25 s (+1.3 / +1.0 / +1.3%), slower 3 of 3 | +9 / +7 / +15 s (+0.6 / +0.4 / +0.7%), slower 2 of 3 |
| bridge+cf0.3 (v0.15.0) | +20 / +23 / +26 s (+1.4 / +1.4 / +1.5%), slower 3 of 3 | +7 / +7 / +12 s (+0.5 / +0.4 / +0.6%), slower 3 of 3 |
| dr+cf0.3 (v0.13.0) | +11 / +14 / +16 s (+0.7 / +0.9 / +0.8%), slower 3 of 3 | +4 / +0.4 / +1 s (+0.3 / 0.0 / +0.1%), slower 1 of 3 |

Bridging against v0.14.0's pilot, per course: −7.5 / −7.3 / −7.7% on outage15 and −6.8 / −6.2 / −7.0% on wander15; −6.7 / −6.5 / −6.6% on outage45 and −6.7 / −6.0 / −7.1% on wander45. All 24 seeds faster on every one of these 12 courses. Pooled made good (m/s): cf0.3 0.806 / 0.796 / 0.769 / 0.764; bridge+cf0.3 0.870 / 0.857 / 0.824 / 0.819; dr+cf0.3 0.825 / 0.819 / 0.789 / 0.786 (outage15 / wander15 / outage45 / wander45). Human marathon pace 0.754 m/s: bridge+cf0.3 beat it in 72 / 72 / 72 / 71 of 72 missions, cf0.3 in 72 / 72 / 46 / 43.

## Findings

1. **Bridging keeps almost all of its lead when the fixes wander.** Wandering cost the bridging pilot 20-26 s a mission with 15 s outages, slightly more than the 17-25 s it cost v0.14.0's pilot, because bridging starts from the last wandered fix and carries that error through the outage. Its lead shrank from 7.3-7.7% to 6.2-7.0% with 15 s outages and barely changed with 45 s outages (6.5-6.7% to 6.0-7.1%).
2. **The cost scales with how often the GPS wanders.** Every pilot lost about 1-1.5% with an outage every ~165 s and 0-0.7% with one every ~345 s. The prediction's arithmetic (path lengthened about 4% during the 40 s of wandering around each outage) gave about 1%; the bridging pilot's 1.4-1.5% is a little more than that.
3. **Bridging's position suffers most.** The 95th-percentile distance between where the pilot thinks it is and where it is grew 3.1-3.3 m for bridging (to 12.8-13.3 m), 2.3-2.9 m for v0.14.0's pilot (to 10.9-11.5 m) and 3.0-3.1 m for always-on dead reckoning (to 9.6 m). On bayside the bridging rover's p95 distance from the course grew from 2.87 to 6.64 m.
4. **The steadiest position is still not the fastest.** Always-on dead reckoning (dr+cf0.3) knew best where it was (median position error 2.6-3.5 m against bridging's 6.4-6.8 m) and was the least hurt by wandering, yet it was 4-5% slower than bridging on every profile: it steers about four times harder (mean |angular| 0.19-0.21 against 0.045-0.062). This is the fourth study (after pace-g, pace-h and pace-i) where a truer position did not steer faster.
5. **Wandering fixes blur what the wheels learn.** The bridging reckoner's median scale error rose from 0.7-0.8% to 1.0-1.5% on wander15 and from 0.4-1.0% to 1.2-1.6% on wander45, because it learns metres per RPM against fixes that are drifting. It still bridged as long (median 107-137 s a mission on wheels alone).
6. **45 s outages still stop the bridging pilot.** On outage45 and wander45 it stood still a median 86-108 s a mission, against 9-13 s with 15 s outages: the reckoner carries the position for at most 30 s after the last fix, so the last ~15 s of each 45 s outage are spent waiting. That is what the next study (pace-k) tests.

## Limits

Simulated rovers only (pace_h.py's measured Mini+ profile), so speeds are upper bounds on what a sidewalk allows. The wandering is one simple shape: a straight drift out to 8 m and back over 20 s each way, in one random direction per outage. Real multipath can jump, oscillate, or last longer, and a jump larger than the GPS filter's test would be rejected instead of followed. The simulated wheels report the commanded speed exactly. Not yet driven on a live Mini+.
