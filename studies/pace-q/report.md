# Does the GPS filter's lag cost time once the GPS is as quiet as a real one? (simulated)

pace_q.py 0.1.0 (pace_p.py 0.1.0, pace_o.py 0.1.0, rover_pilot.py 0.18.2, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_p.py flies keep16 (pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3, pace_o.py's keep planner, a 16 m lookahead); only the GPS filter changes (a0.3 as it ships, a0.6, raw = alpha 1, track = alpha 0.3 with a tracked velocity). Profiles: outage90 (90 s GPS outages, a steady compass error, 1.5 m of GPS noise per axis), quiet90 (the same with 0.22 m) and quietdrift90 (pace_l.py's drift90 with 0.22 m). Seeds 277-300. 864 of 864 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_p.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | 72/72 | 0.88 | 0.99 | 72 | 0.999 | 0.021 |
| outage90 | a0.6 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.019 |
| outage90 | raw | 72/72 | 0.875 | 0.985 | 72 | 1.0 | 0.017 |
| outage90 | track | 72/72 | 0.888 | 0.999 | 71 | 0.992 | 0.019 |
| quiet90 | a0.3 | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.02 |
| quiet90 | a0.6 | 72/72 | 0.889 | 1.0 | 72 | 0.992 | 0.018 |
| quiet90 | raw | 72/72 | 0.89 | 1.001 | 72 | 0.99 | 0.019 |
| quiet90 | track | 72/72 | 0.886 | 0.997 | 72 | 0.991 | 0.02 |
| quietdrift90 | a0.3 | 72/72 | 0.873 | 0.982 | 72 | 1.004 | 0.018 |
| quietdrift90 | a0.6 | 72/72 | 0.885 | 0.996 | 72 | 0.998 | 0.018 |
| quietdrift90 | raw | 72/72 | 0.885 | 0.996 | 72 | 0.996 | 0.019 |
| quietdrift90 | track | 72/72 | 0.881 | 0.991 | 72 | 0.996 | 0.019 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| outage90 | a0.6 | a0.3 | 2/3 | 0 | 0 | 0 | -0.0308 |
| quiet90 | a0.6 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0323 |
| quietdrift90 | a0.6 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0314 |
| outage90 | raw | a0.3 | 1/3 | 2 | 0 | 0 | -0.0295 |
| quiet90 | raw | a0.3 | 3/3 | 0 | 0 | 0 | -0.0437 |
| quietdrift90 | raw | a0.3 | 3/3 | 0 | 0 | 0 | -0.0421 |
| outage90 | track | a0.3 | 2/3 | 0 | 0 | 0 | -0.0421 |
| quiet90 | track | a0.3 | 3/3 | 0 | 0 | 0 | -0.0411 |
| quietdrift90 | track | a0.3 | 2/3 | 0 | 0 | 0 | -0.0371 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| outage90 | a0.6 | a0.3 | bayside | 16 | 0 | -4.0 | -0.0028 | 0.0 |
| outage90 | a0.6 | a0.3 | blocks | 24 | 0 | -49.0 | -0.0308 | 0.0 |
| outage90 | a0.6 | a0.3 | boulevard | 8 | 5 | 0.0 | 0.0 | 0.5811 |
| quiet90 | a0.6 | a0.3 | bayside | 23 | 0 | -14.0 | -0.0098 | 0.0 |
| quiet90 | a0.6 | a0.3 | blocks | 24 | 0 | -51.0 | -0.0323 | 0.0 |
| quiet90 | a0.6 | a0.3 | boulevard | 15 | 0 | -6.0 | -0.0034 | 0.0001 |
| quietdrift90 | a0.6 | a0.3 | bayside | 22 | 0 | -12.0 | -0.0083 | 0.0 |
| quietdrift90 | a0.6 | a0.3 | blocks | 24 | 0 | -50.0 | -0.0314 | 0.0 |
| quietdrift90 | a0.6 | a0.3 | boulevard | 22 | 0 | -8.0 | -0.0045 | 0.0 |
| outage90 | raw | a0.3 | bayside | 3 | 17 | 7.0 | 0.0049 | 0.0026 |
| outage90 | raw | a0.3 | blocks | 18 | 4 | -47.0 | -0.0295 | 0.0043 |
| outage90 | raw | a0.3 | boulevard | 0 | 20 | 10.0 | 0.0057 | 0.0 |
| quiet90 | raw | a0.3 | bayside | 23 | 0 | -16.0 | -0.0111 | 0.0 |
| quiet90 | raw | a0.3 | blocks | 24 | 0 | -69.0 | -0.0437 | 0.0 |
| quiet90 | raw | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| quietdrift90 | raw | a0.3 | bayside | 22 | 0 | -15.0 | -0.0103 | 0.0 |
| quietdrift90 | raw | a0.3 | blocks | 24 | 0 | -67.0 | -0.0421 | 0.0 |
| quietdrift90 | raw | a0.3 | boulevard | 21 | 0 | -8.0 | -0.0045 | 0.0 |
| outage90 | track | a0.3 | bayside | 22 | 1 | -12.0 | -0.0083 | 0.0 |
| outage90 | track | a0.3 | blocks | 24 | 0 | -67.0 | -0.0421 | 0.0 |
| outage90 | track | a0.3 | boulevard | 8 | 2 | 0.0 | 0.0 | 0.1094 |
| quiet90 | track | a0.3 | bayside | 23 | 0 | -13.0 | -0.0091 | 0.0 |
| quiet90 | track | a0.3 | blocks | 24 | 0 | -65.0 | -0.0411 | 0.0 |
| quiet90 | track | a0.3 | boulevard | 10 | 0 | 0.0 | 0.0 | 0.002 |
| quietdrift90 | track | a0.3 | bayside | 20 | 2 | -12.0 | -0.0083 | 0.0001 |
| quietdrift90 | track | a0.3 | blocks | 24 | 0 | -59.0 | -0.0371 | 0.0 |
| quietdrift90 | track | a0.3 | boulevard | 11 | 4 | 0.0 | 0.0 | 0.1185 |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| a0.3 | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | 0.0 |
| a0.3 | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0057 |
| a0.6 | quiet90 | outage90 | 3/3 | 0 | 0 | 0 | -0.0035 |
| a0.6 | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0053 |
| raw | quiet90 | outage90 | 3/3 | 0 | 0 | 0 | -0.0169 |
| raw | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0067 |
| track | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | -0.0011 |
| track | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.008 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 6.39 | 8.63 |
| outage90 | a0.3 | blocks | 24 | 6.37 | 8.5 |
| outage90 | a0.3 | boulevard | 24 | 6.44 | 8.75 |
| outage90 | a0.6 | bayside | 24 | 3.57 | 5.61 |
| outage90 | a0.6 | blocks | 24 | 3.67 | 5.74 |
| outage90 | a0.6 | boulevard | 24 | 3.63 | 5.86 |
| outage90 | raw | bayside | 24 | 2.77 | 6.77 |
| outage90 | raw | blocks | 24 | 2.8 | 6.71 |
| outage90 | raw | boulevard | 24 | 2.84 | 6.21 |
| outage90 | track | bayside | 24 | 2.55 | 4.79 |
| outage90 | track | blocks | 24 | 2.87 | 5.62 |
| outage90 | track | boulevard | 24 | 2.52 | 4.99 |
| quiet90 | a0.3 | bayside | 24 | 6.39 | 8.33 |
| quiet90 | a0.3 | blocks | 24 | 6.31 | 8.18 |
| quiet90 | a0.3 | boulevard | 24 | 6.41 | 8.32 |
| quiet90 | a0.6 | bayside | 24 | 3.32 | 4.62 |
| quiet90 | a0.6 | blocks | 24 | 3.33 | 4.72 |
| quiet90 | a0.6 | boulevard | 24 | 3.37 | 4.8 |
| quiet90 | raw | bayside | 24 | 2.05 | 3.17 |
| quiet90 | raw | blocks | 24 | 2.11 | 3.26 |
| quiet90 | raw | boulevard | 24 | 2.13 | 3.25 |
| quiet90 | track | bayside | 24 | 2.23 | 4.23 |
| quiet90 | track | blocks | 24 | 2.34 | 5.05 |
| quiet90 | track | boulevard | 24 | 2.17 | 4.12 |
| quietdrift90 | a0.3 | bayside | 24 | 6.41 | 8.75 |
| quietdrift90 | a0.3 | blocks | 24 | 6.37 | 9.04 |
| quietdrift90 | a0.3 | boulevard | 24 | 6.44 | 9.14 |
| quietdrift90 | a0.6 | bayside | 24 | 3.46 | 5.6 |
| quietdrift90 | a0.6 | blocks | 24 | 3.46 | 5.91 |
| quietdrift90 | a0.6 | boulevard | 24 | 3.47 | 5.75 |
| quietdrift90 | raw | bayside | 24 | 2.22 | 4.23 |
| quietdrift90 | raw | blocks | 24 | 2.29 | 4.45 |
| quietdrift90 | raw | boulevard | 24 | 2.27 | 4.46 |
| quietdrift90 | track | bayside | 24 | 2.35 | 4.8 |
| quietdrift90 | track | blocks | 24 | 2.5 | 5.83 |
| quietdrift90 | track | boulevard | 24 | 2.3 | 5.05 |

## Recovery moves and filter restarts

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 0.5 | None |
| outage90 | a0.3 | blocks | 24 | 1.0 | None |
| outage90 | a0.3 | boulevard | 24 | 1.0 | None |
| outage90 | a0.6 | bayside | 24 | 0.0 | None |
| outage90 | a0.6 | blocks | 24 | 0.0 | None |
| outage90 | a0.6 | boulevard | 24 | 0.0 | None |
| outage90 | raw | bayside | 24 | 1.0 | None |
| outage90 | raw | blocks | 24 | 1.0 | None |
| outage90 | raw | boulevard | 24 | 1.0 | None |
| outage90 | track | bayside | 24 | 1.0 | 3.0 |
| outage90 | track | blocks | 24 | 1.0 | 3.0 |
| outage90 | track | boulevard | 24 | 1.0 | 4.0 |
| quiet90 | a0.3 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet90 | a0.6 | bayside | 24 | 0.0 | None |
| quiet90 | a0.6 | blocks | 24 | 0.0 | None |
| quiet90 | a0.6 | boulevard | 24 | 0.0 | None |
| quiet90 | raw | bayside | 24 | 0.0 | None |
| quiet90 | raw | blocks | 24 | 0.0 | None |
| quiet90 | raw | boulevard | 24 | 0.0 | None |
| quiet90 | track | bayside | 24 | 1.0 | 3.0 |
| quiet90 | track | blocks | 24 | 1.0 | 3.0 |
| quiet90 | track | boulevard | 24 | 1.0 | 4.0 |
| quietdrift90 | a0.3 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3 | boulevard | 24 | 1.0 | None |
| quietdrift90 | a0.6 | bayside | 24 | 0.0 | None |
| quietdrift90 | a0.6 | blocks | 24 | 0.0 | None |
| quietdrift90 | a0.6 | boulevard | 24 | 0.0 | None |
| quietdrift90 | raw | bayside | 24 | 0.0 | None |
| quietdrift90 | raw | blocks | 24 | 0.0 | None |
| quietdrift90 | raw | boulevard | 24 | 0.0 | None |
| quietdrift90 | track | bayside | 24 | 1.0 | 3.0 |
| quietdrift90 | track | blocks | 24 | 1.0 | 3.0 |
| quietdrift90 | track | boulevard | 24 | 1.0 | 4.0 |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | blocks | 24 | 9.0 | 1.15 | 4.34 | 6.58 | 2.16 | 4.21 |
| outage90 | a0.6 | blocks | 24 | 9.0 | 0.91 | 3.6 | 5.56 | -0.07 | 1.46 |
| outage90 | raw | blocks | 24 | 9.0 | 2.28 | 8.08 | 8.91 | -0.89 | 6.1 |
| outage90 | track | blocks | 24 | 9.0 | 1.68 | 4.05 | 5.61 | -1.79 | -0.43 |
| quiet90 | a0.3 | blocks | 24 | 9.0 | 1.0 | 3.17 | 4.85 | 2.07 | 3.6 |
| quiet90 | a0.6 | blocks | 24 | 9.0 | 0.51 | 3.04 | 4.75 | -0.22 | 0.14 |
| quiet90 | raw | blocks | 24 | 9.0 | 1.15 | 3.6 | 4.68 | -0.84 | -0.56 |
| quiet90 | track | blocks | 24 | 9.0 | 2.02 | 3.74 | 4.68 | -2.09 | -1.18 |
| quietdrift90 | a0.3 | blocks | 24 | 9.0 | 1.6 | 4.58 | 6.8 | 2.1 | 4.55 |
| quietdrift90 | a0.6 | blocks | 24 | 9.0 | 1.46 | 4.35 | 7.83 | -0.37 | 2.7 |
| quietdrift90 | raw | blocks | 24 | 9.0 | 1.85 | 4.53 | 6.92 | -1.07 | 2.04 |
| quietdrift90 | track | blocks | 24 | 9.0 | 2.17 | 5.04 | 7.71 | -2.06 | 1.14 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 0.6 | 3.75 |
| outage90 | a0.3 | blocks | 24 | 0.81 | 4.34 |
| outage90 | a0.3 | boulevard | 24 | 0.65 | 3.58 |
| outage90 | a0.6 | bayside | 24 | 0.69 | 3.99 |
| outage90 | a0.6 | blocks | 24 | 0.61 | 4.01 |
| outage90 | a0.6 | boulevard | 24 | 0.68 | 4.48 |
| outage90 | raw | bayside | 24 | 1.52 | 7.99 |
| outage90 | raw | blocks | 24 | 1.96 | 9.47 |
| outage90 | raw | boulevard | 24 | 0.91 | 8.61 |
| outage90 | track | bayside | 24 | 0.97 | 3.5 |
| outage90 | track | blocks | 24 | 1.02 | 3.59 |
| outage90 | track | boulevard | 24 | 0.67 | 3.17 |
| quiet90 | a0.3 | bayside | 24 | 0.22 | 2.17 |
| quiet90 | a0.3 | blocks | 24 | 0.29 | 3.31 |
| quiet90 | a0.3 | boulevard | 24 | 0.15 | 0.86 |
| quiet90 | a0.6 | bayside | 24 | 0.41 | 1.36 |
| quiet90 | a0.6 | blocks | 24 | 0.18 | 2.65 |
| quiet90 | a0.6 | boulevard | 24 | 0.15 | 0.88 |
| quiet90 | raw | bayside | 24 | 0.58 | 1.43 |
| quiet90 | raw | blocks | 24 | 0.25 | 3.1 |
| quiet90 | raw | boulevard | 24 | 0.14 | 0.9 |
| quiet90 | track | bayside | 24 | 0.85 | 1.82 |
| quiet90 | track | blocks | 24 | 0.57 | 3.34 |
| quiet90 | track | boulevard | 24 | 0.15 | 1.09 |
| quietdrift90 | a0.3 | bayside | 24 | 1.6 | 6.79 |
| quietdrift90 | a0.3 | blocks | 24 | 1.86 | 6.78 |
| quietdrift90 | a0.3 | boulevard | 24 | 1.69 | 7.51 |
| quietdrift90 | a0.6 | bayside | 24 | 1.5 | 5.72 |
| quietdrift90 | a0.6 | blocks | 24 | 1.6 | 5.76 |
| quietdrift90 | a0.6 | boulevard | 24 | 1.54 | 7.12 |
| quietdrift90 | raw | bayside | 24 | 1.58 | 5.4 |
| quietdrift90 | raw | blocks | 24 | 1.71 | 5.51 |
| quietdrift90 | raw | boulevard | 24 | 1.53 | 5.86 |
| quietdrift90 | track | bayside | 24 | 1.77 | 5.5 |
| quietdrift90 | track | blocks | 24 | 1.94 | 6.13 |
| quietdrift90 | track | boulevard | 24 | 1.52 | 6.43 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 7.14 | 8.42 | 0 | 0 |
| outage90 | a0.3 | blocks | 24 | 7.98 | 13.63 | 0 | 0 |
| outage90 | a0.3 | boulevard | 24 | 7.79 | 11.97 | 0 | 0 |
| outage90 | a0.6 | bayside | 24 | 6.75 | 9.58 | 0 | 0 |
| outage90 | a0.6 | blocks | 24 | 7.56 | 11.77 | 0 | 0 |
| outage90 | a0.6 | boulevard | 24 | 7.38 | 11.76 | 0 | 0 |
| outage90 | raw | bayside | 24 | 12.34 | 40.25 | 0 | 0 |
| outage90 | raw | blocks | 24 | 12.11 | 38.15 | 0 | 0 |
| outage90 | raw | boulevard | 24 | 10.25 | 44.77 | 0 | 0 |
| outage90 | track | bayside | 24 | 6.12 | 8.09 | 0 | 0 |
| outage90 | track | blocks | 24 | 6.84 | 8.86 | 0 | 0 |
| outage90 | track | boulevard | 24 | 6.5 | 9.45 | 0 | 0 |
| quiet90 | a0.3 | bayside | 24 | 7.28 | 8.59 | 0 | 0 |
| quiet90 | a0.3 | blocks | 24 | 7.43 | 9.34 | 0 | 0 |
| quiet90 | a0.3 | boulevard | 24 | 7.42 | 8.01 | 0 | 0 |
| quiet90 | a0.6 | bayside | 24 | 5.75 | 6.45 | 0 | 0 |
| quiet90 | a0.6 | blocks | 24 | 6.26 | 7.03 | 0 | 0 |
| quiet90 | a0.6 | boulevard | 24 | 6.31 | 7.13 | 0 | 0 |
| quiet90 | raw | bayside | 24 | 5.57 | 6.27 | 0 | 0 |
| quiet90 | raw | blocks | 24 | 6.07 | 6.82 | 0 | 0 |
| quiet90 | raw | boulevard | 24 | 6.1 | 6.98 | 0 | 0 |
| quiet90 | track | bayside | 24 | 6.19 | 6.59 | 0 | 0 |
| quiet90 | track | blocks | 24 | 6.62 | 7.09 | 0 | 0 |
| quiet90 | track | boulevard | 24 | 6.71 | 7.27 | 0 | 0 |
| quietdrift90 | a0.3 | bayside | 24 | 12.02 | 33.78 | 0 | 0 |
| quietdrift90 | a0.3 | blocks | 24 | 12.51 | 29.76 | 0 | 0 |
| quietdrift90 | a0.3 | boulevard | 24 | 15.21 | 34.06 | 0 | 0 |
| quietdrift90 | a0.6 | bayside | 24 | 11.38 | 31.99 | 0 | 0 |
| quietdrift90 | a0.6 | blocks | 24 | 12.32 | 35.56 | 0 | 0 |
| quietdrift90 | a0.6 | boulevard | 24 | 14.46 | 32.72 | 0 | 0 |
| quietdrift90 | raw | bayside | 24 | 10.92 | 31.55 | 0 | 0 |
| quietdrift90 | raw | blocks | 24 | 11.75 | 35.85 | 0 | 0 |
| quietdrift90 | raw | boulevard | 24 | 12.8 | 32.54 | 0 | 0 |
| quietdrift90 | track | bayside | 24 | 10.62 | 31.52 | 0 | 0 |
| quietdrift90 | track | blocks | 24 | 12.01 | 34.98 | 0 | 0 |
| quietdrift90 | track | boulevard | 24 | 13.66 | 32.35 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | checkpoint | 24 | 6348 | 0 | 0.0 | 0.62 | 1.81 | 2.37 |
| outage90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | bayside | other | 24 | 26532 | 22 | 1.0 | 0.61 | 4.19 | 7.14 |
| outage90 | a0.3 | bayside | outage | 23 | 3633 | 10 | 0.455 | 1.82 | 4.32 | 4.6 |
| outage90 | a0.3 | bayside | fix | 24 | 29247 | 12 | 0.545 | 0.55 | 2.98 | 7.14 |
| outage90 | a0.3 | blocks | checkpoint | 24 | 8306 | 54 | 0.204 | 0.73 | 2.84 | 3.64 |
| outage90 | a0.3 | blocks | corner | 24 | 8782 | 32 | 0.121 | 1.15 | 4.34 | 6.58 |
| outage90 | a0.3 | blocks | other | 24 | 18817 | 179 | 0.675 | 0.7 | 4.82 | 7.3 |
| outage90 | a0.3 | blocks | outage | 24 | 4122 | 64 | 0.242 | 1.57 | 4.71 | 5.97 |
| outage90 | a0.3 | blocks | fix | 24 | 31783 | 201 | 0.758 | 0.75 | 3.9 | 7.98 |
| outage90 | a0.3 | boulevard | checkpoint | 24 | 6296 | 5 | 0.024 | 0.56 | 1.58 | 1.98 |
| outage90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | boulevard | other | 24 | 33669 | 200 | 0.976 | 0.69 | 3.83 | 7.79 |
| outage90 | a0.3 | boulevard | outage | 24 | 4859 | 61 | 0.298 | 2.04 | 4.17 | 4.88 |
| outage90 | a0.3 | boulevard | fix | 24 | 35106 | 144 | 0.702 | 0.58 | 2.53 | 7.79 |
| outage90 | a0.6 | bayside | checkpoint | 24 | 6341 | 0 | 0.0 | 0.63 | 2.11 | 2.54 |
| outage90 | a0.6 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.6 | bayside | other | 24 | 26411 | 55 | 1.0 | 0.73 | 4.86 | 6.75 |
| outage90 | a0.6 | bayside | outage | 23 | 3592 | 47 | 0.855 | 1.95 | 3.88 | 4.48 |
| outage90 | a0.6 | bayside | fix | 24 | 29160 | 8 | 0.145 | 0.65 | 3.02 | 6.75 |
| outage90 | a0.6 | blocks | checkpoint | 24 | 8072 | 2 | 0.009 | 0.57 | 2.12 | 3.58 |
| outage90 | a0.6 | blocks | corner | 24 | 8119 | 30 | 0.139 | 0.91 | 3.6 | 5.56 |
| outage90 | a0.6 | blocks | other | 24 | 18627 | 184 | 0.852 | 0.59 | 5.87 | 7.48 |
| outage90 | a0.6 | blocks | outage | 23 | 3906 | 91 | 0.421 | 1.86 | 3.91 | 5.74 |
| outage90 | a0.6 | blocks | fix | 24 | 30912 | 125 | 0.579 | 0.56 | 3.39 | 7.48 |
| outage90 | a0.6 | boulevard | checkpoint | 24 | 6292 | 0 | 0.0 | 0.53 | 1.91 | 2.41 |
| outage90 | a0.6 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.6 | boulevard | other | 24 | 33674 | 388 | 1.0 | 0.69 | 4.75 | 7.38 |
| outage90 | a0.6 | boulevard | outage | 24 | 4852 | 119 | 0.307 | 2.38 | 4.9 | 5.24 |
| outage90 | a0.6 | boulevard | fix | 24 | 35114 | 269 | 0.693 | 0.6 | 3.48 | 7.38 |
| outage90 | raw | bayside | checkpoint | 24 | 6438 | 417 | 0.146 | 1.2 | 6.38 | 6.87 |
| outage90 | raw | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | raw | bayside | other | 24 | 26819 | 2448 | 0.854 | 1.65 | 7.94 | 9.25 |
| outage90 | raw | bayside | outage | 23 | 3762 | 1240 | 0.433 | 3.7 | 13.4 | 14.75 |
| outage90 | raw | bayside | fix | 24 | 29495 | 1625 | 0.567 | 1.36 | 7.76 | 12.34 |
| outage90 | raw | blocks | checkpoint | 24 | 8362 | 923 | 0.238 | 1.67 | 6.62 | 7.85 |
| outage90 | raw | blocks | corner | 24 | 7602 | 477 | 0.123 | 2.28 | 8.08 | 8.91 |
| outage90 | raw | blocks | other | 24 | 19143 | 2486 | 0.64 | 2.08 | 9.96 | 11.74 |
| outage90 | raw | blocks | outage | 23 | 4048 | 1529 | 0.393 | 4.25 | 13.23 | 13.88 |
| outage90 | raw | blocks | fix | 24 | 31059 | 2357 | 0.607 | 1.82 | 8.34 | 11.82 |
| outage90 | raw | boulevard | checkpoint | 24 | 6387 | 425 | 0.077 | 0.76 | 4.04 | 5.12 |
| outage90 | raw | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | raw | boulevard | other | 24 | 33984 | 5069 | 0.923 | 0.98 | 8.55 | 10.25 |
| outage90 | raw | boulevard | outage | 24 | 4958 | 1400 | 0.255 | 4.0 | 9.29 | 10.03 |
| outage90 | raw | boulevard | fix | 24 | 35413 | 4094 | 0.745 | 0.78 | 8.39 | 10.25 |
| outage90 | track | bayside | checkpoint | 24 | 6327 | 0 | 0.0 | 0.9 | 2.1 | 2.79 |
| outage90 | track | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | track | bayside | other | 24 | 26230 | 3 | 1.0 | 1.01 | 3.54 | 6.12 |
| outage90 | track | bayside | outage | 23 | 3452 | 3 | 1.0 | 1.66 | 4.0 | 4.34 |
| outage90 | track | bayside | fix | 24 | 29105 | 0 | 0.0 | 0.94 | 2.74 | 6.12 |
| outage90 | track | blocks | checkpoint | 24 | 7953 | 2 | 0.042 | 1.18 | 3.01 | 4.0 |
| outage90 | track | blocks | corner | 24 | 7782 | 6 | 0.125 | 1.68 | 4.05 | 5.61 |
| outage90 | track | blocks | other | 24 | 18655 | 40 | 0.833 | 0.76 | 3.92 | 6.42 |
| outage90 | track | blocks | outage | 23 | 3906 | 21 | 0.438 | 1.56 | 3.51 | 5.53 |
| outage90 | track | blocks | fix | 24 | 30484 | 27 | 0.562 | 0.93 | 3.44 | 6.59 |
| outage90 | track | boulevard | checkpoint | 24 | 6281 | 1 | 0.015 | 0.71 | 1.98 | 2.19 |
| outage90 | track | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | track | boulevard | other | 24 | 33669 | 65 | 0.985 | 0.7 | 3.42 | 6.5 |
| outage90 | track | boulevard | outage | 24 | 4926 | 21 | 0.318 | 1.84 | 3.99 | 4.2 |
| outage90 | track | boulevard | fix | 24 | 35024 | 45 | 0.682 | 0.64 | 2.21 | 6.5 |
| quiet90 | a0.3 | bayside | checkpoint | 24 | 6331 | 0 | 0.0 | 0.19 | 0.54 | 0.93 |
| quiet90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3 | bayside | other | 24 | 26540 | 10 | 1.0 | 0.22 | 3.21 | 7.28 |
| quiet90 | a0.3 | bayside | outage | 23 | 3647 | 0 | 0.0 | 0.8 | 1.48 | 2.06 |
| quiet90 | a0.3 | bayside | fix | 24 | 29224 | 10 | 1.0 | 0.19 | 2.65 | 7.28 |
| quiet90 | a0.3 | blocks | checkpoint | 24 | 8286 | 35 | 0.7 | 0.33 | 2.55 | 3.06 |
| quiet90 | a0.3 | blocks | corner | 24 | 8799 | 10 | 0.2 | 1.0 | 3.17 | 4.85 |
| quiet90 | a0.3 | blocks | other | 24 | 18755 | 5 | 0.1 | 0.21 | 3.56 | 7.34 |
| quiet90 | a0.3 | blocks | outage | 24 | 4128 | 0 | 0.0 | 0.43 | 2.61 | 4.28 |
| quiet90 | a0.3 | blocks | fix | 24 | 31712 | 50 | 1.0 | 0.27 | 3.55 | 7.43 |
| quiet90 | a0.3 | boulevard | checkpoint | 24 | 6286 | 0 | 0.0 | 0.17 | 0.6 | 1.0 |
| quiet90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3 | boulevard | other | 24 | 33626 | 1 | 1.0 | 0.15 | 0.88 | 7.42 |
| quiet90 | a0.3 | boulevard | outage | 24 | 4849 | 0 | 0.0 | 0.33 | 0.86 | 0.94 |
| quiet90 | a0.3 | boulevard | fix | 24 | 35063 | 1 | 1.0 | 0.14 | 0.8 | 7.42 |
| quiet90 | a0.6 | bayside | checkpoint | 24 | 6310 | 0 | None | 0.3 | 0.82 | 1.13 |
| quiet90 | a0.6 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.6 | bayside | other | 24 | 26278 | 0 | None | 0.44 | 1.5 | 5.75 |
| quiet90 | a0.6 | bayside | outage | 23 | 3538 | 0 | None | 0.82 | 1.56 | 1.87 |
| quiet90 | a0.6 | bayside | fix | 24 | 29050 | 0 | None | 0.38 | 1.19 | 5.75 |
| quiet90 | a0.6 | blocks | checkpoint | 24 | 8032 | 0 | None | 0.17 | 1.77 | 3.06 |
| quiet90 | a0.6 | blocks | corner | 24 | 8091 | 0 | None | 0.51 | 3.04 | 4.75 |
| quiet90 | a0.6 | blocks | other | 24 | 18531 | 0 | None | 0.15 | 2.08 | 6.26 |
| quiet90 | a0.6 | blocks | outage | 23 | 3933 | 0 | None | 0.6 | 2.99 | 4.74 |
| quiet90 | a0.6 | blocks | fix | 24 | 30721 | 0 | None | 0.17 | 2.53 | 6.26 |
| quiet90 | a0.6 | boulevard | checkpoint | 24 | 6271 | 0 | None | 0.18 | 0.89 | 1.24 |
| quiet90 | a0.6 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.6 | boulevard | other | 24 | 33567 | 0 | None | 0.14 | 0.85 | 6.31 |
| quiet90 | a0.6 | boulevard | outage | 24 | 4892 | 0 | None | 0.38 | 0.9 | 1.02 |
| quiet90 | a0.6 | boulevard | fix | 24 | 34946 | 0 | None | 0.13 | 0.89 | 6.31 |
| quiet90 | raw | bayside | checkpoint | 24 | 6310 | 0 | None | 0.4 | 1.03 | 1.38 |
| quiet90 | raw | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | raw | bayside | other | 24 | 26203 | 0 | None | 0.61 | 1.55 | 5.57 |
| quiet90 | raw | bayside | outage | 23 | 3523 | 0 | None | 0.94 | 1.66 | 2.0 |
| quiet90 | raw | bayside | fix | 24 | 28990 | 0 | None | 0.54 | 1.37 | 5.57 |
| quiet90 | raw | blocks | checkpoint | 24 | 7972 | 0 | None | 0.28 | 2.21 | 3.66 |
| quiet90 | raw | blocks | corner | 24 | 7808 | 0 | None | 1.15 | 3.6 | 4.68 |
| quiet90 | raw | blocks | other | 24 | 18494 | 0 | None | 0.19 | 2.08 | 6.07 |
| quiet90 | raw | blocks | outage | 23 | 3871 | 0 | None | 0.78 | 3.2 | 4.71 |
| quiet90 | raw | blocks | fix | 24 | 30403 | 0 | None | 0.23 | 3.0 | 6.07 |
| quiet90 | raw | boulevard | checkpoint | 24 | 6274 | 0 | None | 0.2 | 1.04 | 1.4 |
| quiet90 | raw | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | raw | boulevard | other | 24 | 33543 | 0 | None | 0.13 | 0.82 | 6.1 |
| quiet90 | raw | boulevard | outage | 24 | 4876 | 0 | None | 0.39 | 0.86 | 0.94 |
| quiet90 | raw | boulevard | fix | 24 | 34941 | 0 | None | 0.12 | 0.94 | 6.1 |
| quiet90 | track | bayside | checkpoint | 24 | 6303 | 0 | None | 0.59 | 1.35 | 1.65 |
| quiet90 | track | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | track | bayside | other | 24 | 26234 | 0 | None | 0.93 | 1.92 | 6.19 |
| quiet90 | track | bayside | outage | 23 | 3567 | 0 | None | 0.99 | 1.67 | 2.16 |
| quiet90 | track | bayside | fix | 24 | 28970 | 0 | None | 0.81 | 1.79 | 6.19 |
| quiet90 | track | blocks | checkpoint | 24 | 7947 | 0 | None | 0.71 | 2.55 | 3.67 |
| quiet90 | track | blocks | corner | 24 | 7756 | 0 | None | 2.02 | 3.74 | 4.68 |
| quiet90 | track | blocks | other | 24 | 18617 | 0 | None | 0.39 | 3.03 | 6.62 |
| quiet90 | track | blocks | outage | 23 | 3852 | 0 | None | 0.77 | 3.35 | 4.71 |
| quiet90 | track | blocks | fix | 24 | 30468 | 0 | None | 0.54 | 3.29 | 6.62 |
| quiet90 | track | boulevard | checkpoint | 24 | 6262 | 0 | None | 0.34 | 1.18 | 1.5 |
| quiet90 | track | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | track | boulevard | other | 24 | 33623 | 0 | None | 0.14 | 0.93 | 6.71 |
| quiet90 | track | boulevard | outage | 24 | 4842 | 0 | None | 0.35 | 0.87 | 0.94 |
| quiet90 | track | boulevard | fix | 24 | 35043 | 0 | None | 0.14 | 1.15 | 6.71 |
| quietdrift90 | a0.3 | bayside | checkpoint | 24 | 6381 | 109 | 0.076 | 1.35 | 3.81 | 4.32 |
| quietdrift90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | bayside | other | 24 | 26733 | 1329 | 0.924 | 1.58 | 8.15 | 12.02 |
| quietdrift90 | a0.3 | bayside | outage | 23 | 3758 | 675 | 0.469 | 2.76 | 10.12 | 11.26 |
| quietdrift90 | a0.3 | bayside | fix | 24 | 29356 | 763 | 0.531 | 1.49 | 5.5 | 12.0 |
| quietdrift90 | a0.3 | blocks | checkpoint | 24 | 8386 | 216 | 0.154 | 1.92 | 5.28 | 7.11 |
| quietdrift90 | a0.3 | blocks | corner | 24 | 8510 | 170 | 0.121 | 1.6 | 4.58 | 6.8 |
| quietdrift90 | a0.3 | blocks | other | 24 | 19070 | 1014 | 0.724 | 1.88 | 8.5 | 12.51 |
| quietdrift90 | a0.3 | blocks | outage | 24 | 4089 | 801 | 0.572 | 3.29 | 11.88 | 12.51 |
| quietdrift90 | a0.3 | blocks | fix | 24 | 31877 | 599 | 0.428 | 1.75 | 5.52 | 11.08 |
| quietdrift90 | a0.3 | boulevard | checkpoint | 24 | 6358 | 171 | 0.077 | 1.51 | 4.54 | 5.26 |
| quietdrift90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | boulevard | other | 24 | 33906 | 2038 | 0.923 | 1.69 | 7.64 | 15.11 |
| quietdrift90 | a0.3 | boulevard | outage | 24 | 4927 | 1052 | 0.476 | 3.33 | 11.77 | 13.97 |
| quietdrift90 | a0.3 | boulevard | fix | 24 | 35337 | 1157 | 0.524 | 1.61 | 5.83 | 15.21 |
| quietdrift90 | a0.6 | bayside | checkpoint | 24 | 6348 | 57 | 0.053 | 1.39 | 3.58 | 3.85 |
| quietdrift90 | a0.6 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.6 | bayside | other | 24 | 26456 | 1017 | 0.947 | 1.48 | 6.56 | 11.38 |
| quietdrift90 | a0.6 | bayside | outage | 23 | 3627 | 591 | 0.55 | 2.7 | 9.86 | 9.99 |
| quietdrift90 | a0.6 | bayside | fix | 24 | 29177 | 483 | 0.45 | 1.41 | 4.7 | 11.07 |
| quietdrift90 | a0.6 | blocks | checkpoint | 24 | 8142 | 167 | 0.135 | 1.46 | 4.22 | 5.04 |
| quietdrift90 | a0.6 | blocks | corner | 24 | 7888 | 113 | 0.091 | 1.46 | 4.35 | 7.83 |
| quietdrift90 | a0.6 | blocks | other | 24 | 18837 | 959 | 0.774 | 1.67 | 6.75 | 11.79 |
| quietdrift90 | a0.6 | blocks | outage | 23 | 3917 | 778 | 0.628 | 3.64 | 11.08 | 12.54 |
| quietdrift90 | a0.6 | blocks | fix | 24 | 30950 | 461 | 0.372 | 1.45 | 4.58 | 11.12 |
| quietdrift90 | a0.6 | boulevard | checkpoint | 24 | 6340 | 170 | 0.073 | 1.33 | 4.12 | 4.91 |
| quietdrift90 | a0.6 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.6 | boulevard | other | 24 | 33769 | 2145 | 0.927 | 1.6 | 7.56 | 14.01 |
| quietdrift90 | a0.6 | boulevard | outage | 24 | 4962 | 1054 | 0.455 | 3.15 | 11.56 | 13.94 |
| quietdrift90 | a0.6 | boulevard | fix | 24 | 35147 | 1261 | 0.545 | 1.43 | 6.31 | 14.46 |
| quietdrift90 | raw | bayside | checkpoint | 24 | 6350 | 50 | 0.05 | 1.32 | 3.56 | 4.02 |
| quietdrift90 | raw | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | raw | bayside | other | 24 | 26375 | 952 | 0.95 | 1.51 | 6.62 | 10.92 |
| quietdrift90 | raw | bayside | outage | 23 | 3610 | 586 | 0.585 | 3.1 | 9.38 | 10.17 |
| quietdrift90 | raw | bayside | fix | 24 | 29115 | 416 | 0.415 | 1.48 | 4.5 | 10.68 |
| quietdrift90 | raw | blocks | checkpoint | 24 | 8072 | 133 | 0.13 | 1.5 | 4.26 | 5.12 |
| quietdrift90 | raw | blocks | corner | 24 | 7653 | 111 | 0.108 | 1.85 | 4.53 | 6.92 |
| quietdrift90 | raw | blocks | other | 24 | 18758 | 781 | 0.762 | 1.68 | 6.33 | 9.87 |
| quietdrift90 | raw | blocks | outage | 23 | 3839 | 714 | 0.697 | 3.6 | 10.67 | 12.21 |
| quietdrift90 | raw | blocks | fix | 24 | 30644 | 311 | 0.303 | 1.58 | 4.58 | 8.73 |
| quietdrift90 | raw | boulevard | checkpoint | 24 | 6340 | 104 | 0.066 | 1.33 | 4.33 | 4.78 |
| quietdrift90 | raw | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | raw | boulevard | other | 24 | 33781 | 1471 | 0.934 | 1.53 | 5.74 | 12.8 |
| quietdrift90 | raw | boulevard | outage | 24 | 4963 | 980 | 0.622 | 3.04 | 10.96 | 12.55 |
| quietdrift90 | raw | boulevard | fix | 24 | 35158 | 595 | 0.378 | 1.44 | 4.49 | 12.8 |
| quietdrift90 | track | bayside | checkpoint | 24 | 6347 | 43 | 0.044 | 1.42 | 3.61 | 4.26 |
| quietdrift90 | track | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | track | bayside | other | 24 | 26417 | 936 | 0.956 | 1.62 | 6.33 | 10.62 |
| quietdrift90 | track | bayside | outage | 23 | 3544 | 597 | 0.61 | 2.9 | 8.99 | 9.48 |
| quietdrift90 | track | bayside | fix | 24 | 29220 | 382 | 0.39 | 1.61 | 4.81 | 10.35 |
| quietdrift90 | track | blocks | checkpoint | 24 | 8076 | 146 | 0.131 | 1.71 | 4.28 | 5.08 |
| quietdrift90 | track | blocks | corner | 24 | 7607 | 132 | 0.118 | 2.17 | 5.04 | 7.71 |
| quietdrift90 | track | blocks | other | 24 | 18877 | 840 | 0.751 | 1.85 | 7.15 | 11.0 |
| quietdrift90 | track | blocks | outage | 23 | 3887 | 731 | 0.654 | 3.83 | 10.85 | 12.09 |
| quietdrift90 | track | blocks | fix | 24 | 30673 | 387 | 0.346 | 1.85 | 5.29 | 9.22 |
| quietdrift90 | track | boulevard | checkpoint | 24 | 6343 | 92 | 0.055 | 1.38 | 4.33 | 4.72 |
| quietdrift90 | track | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | track | boulevard | other | 24 | 33885 | 1587 | 0.945 | 1.54 | 6.69 | 13.66 |
| quietdrift90 | track | boulevard | outage | 24 | 4930 | 1004 | 0.598 | 3.45 | 12.05 | 13.6 |
| quietdrift90 | track | boulevard | fix | 24 | 35298 | 675 | 0.402 | 1.46 | 4.88 | 13.66 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 1.58 | 4.42 |
| outage90 | a0.3 | blocks | 24 | 1.65 | 4.34 |
| outage90 | a0.3 | boulevard | 24 | 1.62 | 4.17 |
| outage90 | a0.6 | bayside | 24 | 1.84 | 5.74 |
| outage90 | a0.6 | blocks | 24 | 1.61 | 5.0 |
| outage90 | a0.6 | boulevard | 24 | 1.67 | 4.72 |
| outage90 | raw | bayside | 24 | 3.98 | 13.8 |
| outage90 | raw | blocks | 24 | 5.67 | 14.05 |
| outage90 | raw | boulevard | 24 | 2.63 | 9.98 |
| outage90 | track | bayside | 24 | 1.58 | 4.64 |
| outage90 | track | blocks | 24 | 1.71 | 4.47 |
| outage90 | track | boulevard | 24 | 1.66 | 4.14 |
| quiet90 | a0.3 | bayside | 24 | 0.99 | 4.26 |
| quiet90 | a0.3 | blocks | 24 | 1.01 | 4.12 |
| quiet90 | a0.3 | boulevard | 24 | 0.96 | 3.85 |
| quiet90 | a0.6 | bayside | 24 | 0.98 | 3.81 |
| quiet90 | a0.6 | blocks | 24 | 1.01 | 3.76 |
| quiet90 | a0.6 | boulevard | 24 | 0.95 | 3.46 |
| quiet90 | raw | bayside | 24 | 0.98 | 3.83 |
| quiet90 | raw | blocks | 24 | 0.99 | 3.76 |
| quiet90 | raw | boulevard | 24 | 0.96 | 3.45 |
| quiet90 | track | bayside | 24 | 0.98 | 4.28 |
| quiet90 | track | blocks | 24 | 1.01 | 4.19 |
| quiet90 | track | boulevard | 24 | 0.96 | 3.85 |
| quietdrift90 | a0.3 | bayside | 24 | 5.53 | 8.77 |
| quietdrift90 | a0.3 | blocks | 24 | 6.03 | 9.49 |
| quietdrift90 | a0.3 | boulevard | 24 | 5.63 | 8.47 |
| quietdrift90 | a0.6 | bayside | 24 | 5.45 | 8.81 |
| quietdrift90 | a0.6 | blocks | 24 | 5.87 | 9.34 |
| quietdrift90 | a0.6 | boulevard | 24 | 5.6 | 8.46 |
| quietdrift90 | raw | bayside | 24 | 5.45 | 8.8 |
| quietdrift90 | raw | blocks | 24 | 5.96 | 9.18 |
| quietdrift90 | raw | boulevard | 24 | 5.57 | 8.41 |
| quietdrift90 | track | bayside | 24 | 5.45 | 8.79 |
| quietdrift90 | track | blocks | 24 | 5.98 | 9.37 |
| quietdrift90 | track | boulevard | 24 | 5.5 | 8.52 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 0.0314 |
| outage90 | a0.3 | blocks | 24 | 0.0415 |
| outage90 | a0.3 | boulevard | 24 | 0.0267 |
| outage90 | a0.6 | bayside | 24 | 0.0449 |
| outage90 | a0.6 | blocks | 24 | 0.0549 |
| outage90 | a0.6 | boulevard | 24 | 0.0407 |
| outage90 | raw | bayside | 24 | 0.0713 |
| outage90 | raw | blocks | 24 | 0.0806 |
| outage90 | raw | boulevard | 24 | 0.0678 |
| outage90 | track | bayside | 24 | 0.0296 |
| outage90 | track | blocks | 24 | 0.0406 |
| outage90 | track | boulevard | 24 | 0.0272 |
| quiet90 | a0.3 | bayside | 24 | 0.0253 |
| quiet90 | a0.3 | blocks | 24 | 0.0358 |
| quiet90 | a0.3 | boulevard | 24 | 0.0202 |
| quiet90 | a0.6 | bayside | 24 | 0.0244 |
| quiet90 | a0.6 | blocks | 24 | 0.035 |
| quiet90 | a0.6 | boulevard | 24 | 0.0203 |
| quiet90 | raw | bayside | 24 | 0.0248 |
| quiet90 | raw | blocks | 24 | 0.0354 |
| quiet90 | raw | boulevard | 24 | 0.0223 |
| quiet90 | track | bayside | 24 | 0.0226 |
| quiet90 | track | blocks | 24 | 0.0346 |
| quiet90 | track | boulevard | 24 | 0.0204 |
| quietdrift90 | a0.3 | bayside | 24 | 0.0295 |
| quietdrift90 | a0.3 | blocks | 24 | 0.0394 |
| quietdrift90 | a0.3 | boulevard | 24 | 0.0255 |
| quietdrift90 | a0.6 | bayside | 24 | 0.029 |
| quietdrift90 | a0.6 | blocks | 24 | 0.0395 |
| quietdrift90 | a0.6 | boulevard | 24 | 0.0258 |
| quietdrift90 | raw | bayside | 24 | 0.0297 |
| quietdrift90 | raw | blocks | 24 | 0.0401 |
| quietdrift90 | raw | boulevard | 24 | 0.0277 |
| quietdrift90 | track | bayside | 24 | 0.0279 |
| quietdrift90 | track | blocks | 24 | 0.0394 |
| quietdrift90 | track | boulevard | 24 | 0.0262 |
