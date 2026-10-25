# What threw the pilot's position off on outage90 boulevard, seed 313? (diagnostic, simulated)

MV2 of Munim, Inc. Written with AI agents. CC BY 4.0.

**This is a diagnostic, not a pre-registered study.** pace-r (`studies/pace-r/GRADE.md`) left one thing unexplained. On outage90 boulevard, seed 313 (`runs.jsonl` lines 13, 85 and 229), the shipped pilot's idea of where it was went up to 63.72 m from the rover while the rover itself never strayed more than 7.71 m from the course, and the alpha-beta tracker at 12 m drove 32.68 m from the course. `trace_r.py` 0.1.0 (job `trace-r-v1`, rover_pilot.py 0.18.3, pace_r.py 0.1.0) flew that mission again with each of pace-r's four variants and logged one row a second of simulated time: the rover's true position and its distance from the course, the GPS fix, the pilot's estimate, the GPS filter's average, rejected fixes and restarts (`trace/trace-<variant>.csv`). Each traced mission came out **identical** to pace-r's record (`check.different` is empty for all four), so the trace did not change what it watched. Every number below is read from `trace/summary.json`, `trace/report.md` or the CSVs. Positions are metres north and east of the start. The boulevard runs north.

The three outages fell at 87.3-176.4 s, 941.6-1030.2 s and 1264.5-1352.5 s.

## The shipped pilot (`a0.3-16`): the first fix after an outage is averaged with the average from before it

The pilot's estimate was more than 10 m from the rover in three long stretches, each starting right **after** an outage, never inside one: 178.6-197.3 s (peak 64.25 m at 179.7 s), 1032.4-1048.9 s (peak 63.03 m) and 1354.7-1369.0 s (peak 52.7 m). There were also four single-second blips of 10.1-10.4 m, two of them in the first seconds of an outage.

The first outage, step by step (`trace-a0.3-16.csv`):

1. The last fix before it came at 86.2 s: (62.39, 1.01). `GpsFilter`'s average then stood at **(58.56, 0.79)**, and it stayed exactly there through the whole outage.
2. From 91.7 s, 3 s after the last fix, the pilot steered by the dead reckoner, as v0.15.0 made it do. That kept its estimate close: 2.5 m off at 91.7 s and 7.17 m off at 177.5 s, when it read (140.40, −0.14) and the rover was at (145.99, 4.35).
3. At 178.6 s the first fix after the outage came in: (142.55, 3.18), 80 m from the last accepted fix. `GpsFilter.update` allows a jump of `max_speed_mps × dt + jump_slack_m`, 3 m/s × about 92 s + 10 m, which is about 290 m, so it accepted the fix (`rejected` stayed 0). It then averaged it with the 90-second-old average: 58.56 + 0.3 × (142.55 − 58.56) = **83.76** north, 0.79 + 0.3 × (3.18 − 0.79) = **1.51** east. That is exactly the logged estimate.
4. The fix was fresh, so `Pilot._position` switched from the reckoner back to the average. The estimate jumped **56.6 m backwards** along the course, from 140.40 to 83.76 north, while the rover was at 146.97: 63.28 m off. It peaked at 64.25 m off one second later.
5. Each later fix moved it 30% of the way: 102.68 (180.8 s), 116.76 (183.0 s), 127.58 (184.1 s), 134.95 (186.3 s), 141.63 (190.7 s), 152.13 (196.2 s). It was back under 10 m at 198.4 s (8.84 m), about 20 s after the outage ended.

The same arithmetic happens at a small scale after every short dropout of more than 3 s. At 73.0-75.2 s there were no fixes, so the reckoner carried the estimate to (55.2, 6.56). The fix at 76.3 s (53.98, 1.29) was then averaged with the stale (45.64, 3.84), giving 45.64 + 0.3 × 8.34 = 48.14 north, about 7 m back.

**Why the rover stayed on course anyway:** the boulevard is straight, so almost all of the error lay along the course. The estimate was 2.9 m east of the truth at 178.6 s. The aim point stayed ahead on the same line, the rover kept going straight, and its distance from the course stayed at 3.9-4.7 m through the whole jump. On a course with a corner inside the outage the same jump would put the estimate back before the corner. The trace does not show what happens then; pace-s tests it.

`a0.3-20` (the shipped filter at 20 m) did the same, with peaks of 64.24, 63.11 and 52.35 m at the same moments.

**This is in the real-rover code, not only in the study.** rover_pilot.py 0.18.3 and 0.18.4 have the same `GpsFilter.update`: it accepts the fix, then `self.lat += self.alpha * (fix[0] - self.lat)` with no restart after a gap. They also have the same `Pilot._position`, which with `dead_reckon_gaps` returns the reckoner's estimate only while `gps.has_fix(t)` is false. A real rover on v0.18.x would therefore jump back by about 70% of the distance it drove through any GPS gap longer than 3 s.

**How common it is:** in pace-r's record, 65 of the shipped pilot's 72 outage90 missions (seeds 301-324, three courses) had a largest position error over 20 m, most of them between 57 and 65 m, and so did 65 of 72 on quietdrift90. The rest peaked at 9.7-17.6 m.

## The tracker (`track-16`, `track-12`): it starts again from the fix

pace-q's `TrackingGpsFilter` starts again from the fix after more than 3 s without one (`restarts`). At 178.6 s `track-12`'s estimate jumped *to* the fix (142.84 true north, 138.58 estimated: 4.65 m off), and its restart count went from 1 to 2. `track-16`'s estimate was never more than 10 m from the rover in the whole mission (largest 8.63 m). In pace-r none of `track-16`'s 72 outage90 missions went over 11.8 m.

## `track-12`'s 32.7 m from the course: the reckoner drifted inside the outage

`track-12` was more than 8 m from the course from 109.3 to 389.6 s, peaking at 32.69 m at 179.7 s. 23% of that stretch fell inside the first outage. Its estimate was more than 10 m off from 118.1 to 177.5 s, 98% of it inside the outage, peaking at 32.46 m at 177.5 s. That is a different fault from the shipped filter's. Inside the outage the pilot steered its dead-reckoned estimate back onto the course line: its east coordinate went from 6.29 m at 91.7 s to −0.17 m at 176.4 s. Meanwhile the real rover drifted east from 6.04 m to 31.8 m, about 0.30 m/s sideways while it went 0.83 m/s north (70.99 to 141.05 m). That is a heading error of about 20°. Over the same 85 s the shipped pilot's rover drifted only from 1.23 to 4.29 m east. The restart at 178.6 s put the estimate back onto the rover (4.65 m off), but the rover was then 32.6 m east of the course, and it took until 389.6 s to come back within 8 m.

**Not explained by these outputs:** why `track-12`'s reckoner carried a heading about 20° off through this outage when the shipped pilot's, on the same seed, did not. The trace logged no heading, compass bias or learner state. `track-12` is not shipped (pace-r's rule R2 kept the shipped filter), so this does not touch the real-rover pilot today. It is a lead for any later study of the tracker.

## What follows

- The jump is a fault in the shipped pilot's position estimate, not a quirk of the study. The plain fix, starting the average again from the first fix after a gap, is pre-registered as **pace-s** (`studies/pace-s/PREDICTION.md`). It is tested on 576 new missions with a rule for whether a real rover's pilot takes it.
- Nothing in the pilot changes because of this trace alone.

## Limits

- One mission, one seed, simulated. The prevalence figures come from pace-r's record, and the mechanism from reading the code and this trace. The numbers are one row a second, so a peak may be up to a second off.
- The simulated outage is a clean 90 s with no fixes at all, and the receiver comes back with its usual noise.
- Files: `trace_r.py`, `test_trace_r.py` (8 tests passed in the job, `trace/tests.txt`), `trace/summary.json`, `trace/report.md`, `trace/trace-*.csv`, `trace/fetched.json`.
