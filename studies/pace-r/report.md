# Is a truer GPS position worth anything once the rover really aims as far ahead? (simulated)

pace_r.py 0.1.0 (pace_q.py 0.1.0, pace_p.py 0.1.0, rover_pilot.py 0.18.2, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_q.py flies it (pace_p.py's keep16: pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3 and pace_o.py's keep planner) with pace_q.py's a0.3 filter (as it ships) or its track filter (alpha 0.3 with a tracked velocity), and a path follower aiming 12, 16 or 20 m ahead. Profiles: outage90 (90 s GPS outages, a steady compass error, 1.5 m of GPS noise per axis), quiet90 (the same with 0.22 m) and quietdrift90 (a drifting compass with 0.22 m). Seeds 301-324. 864 of 864 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_p.py's runs: 18 compared, 18 identical, 0 missing.

Check against pace_q.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3-16 | 72/72 | 0.873 | 0.983 | 72 | 0.999 | 0.028 |
| outage90 | track-12 | 72/72 | 0.879 | 0.989 | 72 | 0.997 | 0.028 |
| outage90 | a0.3-20 | 72/72 | 0.883 | 0.993 | 72 | 0.997 | 0.027 |
| outage90 | track-16 | 72/72 | 0.883 | 0.993 | 72 | 0.993 | 0.028 |
| quiet90 | a0.3-16 | 72/72 | 0.873 | 0.983 | 72 | 0.999 | 0.029 |
| quiet90 | track-12 | 72/72 | 0.88 | 0.99 | 72 | 0.993 | 0.029 |
| quiet90 | a0.3-20 | 72/72 | 0.883 | 0.994 | 72 | 0.997 | 0.026 |
| quiet90 | track-16 | 72/72 | 0.885 | 0.995 | 72 | 0.991 | 0.029 |
| quietdrift90 | a0.3-16 | 72/72 | 0.857 | 0.964 | 72 | 1.003 | 0.03 |
| quietdrift90 | track-12 | 72/72 | 0.873 | 0.982 | 72 | 1.001 | 0.03 |
| quietdrift90 | a0.3-20 | 72/72 | 0.874 | 0.983 | 72 | 1.002 | 0.028 |
| quietdrift90 | track-16 | 72/72 | 0.877 | 0.986 | 72 | 0.998 | 0.028 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| outage90 | track-12 | a0.3-16 | 2/3 | 1 | 0 | 0 | -0.0137 |
| quiet90 | track-12 | a0.3-16 | 3/3 | 0 | 0 | 0 | -0.0175 |
| quietdrift90 | track-12 | a0.3-16 | 2/3 | 0 | 0 | 0 | -0.016 |
| outage90 | a0.3-20 | a0.3-16 | 3/3 | 0 | 0 | 0 | -0.0162 |
| quiet90 | a0.3-20 | a0.3-16 | 2/3 | 0 | 0 | 0 | -0.02 |
| quietdrift90 | a0.3-20 | a0.3-16 | 2/3 | 0 | 0 | 0 | -0.016 |
| outage90 | track-16 | a0.3-16 | 2/3 | 0 | 0 | 0 | -0.0356 |
| quiet90 | track-16 | a0.3-16 | 3/3 | 0 | 0 | 0 | -0.0393 |
| quietdrift90 | track-16 | a0.3-16 | 2/3 | 0 | 0 | 0 | -0.0382 |
| outage90 | track-16 | a0.3-20 | 2/3 | 1 | 0 | 0 | -0.0149 |
| quiet90 | track-16 | a0.3-20 | 3/3 | 0 | 0 | 0 | -0.0175 |
| quietdrift90 | track-16 | a0.3-20 | 2/3 | 0 | 0 | 0 | -0.0178 |
| outage90 | track-16 | track-12 | 3/3 | 0 | 0 | 0 | -0.0187 |
| quiet90 | track-16 | track-12 | 2/3 | 0 | 0 | 0 | -0.0188 |
| quietdrift90 | track-16 | track-12 | 3/3 | 0 | 0 | 0 | -0.0178 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| outage90 | track-12 | a0.3-16 | bayside | 17 | 1 | -6.0 | -0.004 | 0.0001 |
| outage90 | track-12 | a0.3-16 | blocks | 23 | 0 | -22.0 | -0.0137 | 0.0 |
| outage90 | track-12 | a0.3-16 | boulevard | 1 | 13 | 2.0 | 0.0011 | 0.0018 |
| quiet90 | track-12 | a0.3-16 | bayside | 20 | 0 | -9.0 | -0.006 | 0.0 |
| quiet90 | track-12 | a0.3-16 | blocks | 22 | 2 | -28.0 | -0.0175 | 0.0 |
| quiet90 | track-12 | a0.3-16 | boulevard | 13 | 2 | -2.0 | -0.0011 | 0.0074 |
| quietdrift90 | track-12 | a0.3-16 | bayside | 19 | 1 | -8.0 | -0.0053 | 0.0 |
| quietdrift90 | track-12 | a0.3-16 | blocks | 23 | 0 | -26.0 | -0.016 | 0.0 |
| quietdrift90 | track-12 | a0.3-16 | boulevard | 4 | 5 | 0.0 | 0.0 | 1.0 |
| outage90 | a0.3-20 | a0.3-16 | bayside | 18 | 0 | -4.0 | -0.0027 | 0.0 |
| outage90 | a0.3-20 | a0.3-16 | blocks | 24 | 0 | -26.0 | -0.0162 | 0.0 |
| outage90 | a0.3-20 | a0.3-16 | boulevard | 11 | 0 | 0.0 | 0.0 | 0.001 |
| quiet90 | a0.3-20 | a0.3-16 | bayside | 19 | 0 | -4.0 | -0.0027 | 0.0 |
| quiet90 | a0.3-20 | a0.3-16 | blocks | 24 | 0 | -32.0 | -0.02 | 0.0 |
| quiet90 | a0.3-20 | a0.3-16 | boulevard | 4 | 0 | 0.0 | 0.0 | 0.125 |
| quietdrift90 | a0.3-20 | a0.3-16 | bayside | 18 | 0 | -2.0 | -0.0013 | 0.0 |
| quietdrift90 | a0.3-20 | a0.3-16 | blocks | 24 | 0 | -26.0 | -0.016 | 0.0 |
| quietdrift90 | a0.3-20 | a0.3-16 | boulevard | 3 | 1 | 0.0 | 0.0 | 0.625 |
| outage90 | track-16 | a0.3-16 | bayside | 20 | 0 | -10.0 | -0.0067 | 0.0 |
| outage90 | track-16 | a0.3-16 | blocks | 24 | 0 | -57.0 | -0.0356 | 0.0 |
| outage90 | track-16 | a0.3-16 | boulevard | 3 | 4 | 0.0 | 0.0 | 1.0 |
| quiet90 | track-16 | a0.3-16 | bayside | 20 | 0 | -12.0 | -0.008 | 0.0 |
| quiet90 | track-16 | a0.3-16 | blocks | 23 | 1 | -63.0 | -0.0393 | 0.0 |
| quiet90 | track-16 | a0.3-16 | boulevard | 15 | 1 | -2.0 | -0.0011 | 0.0005 |
| quietdrift90 | track-16 | a0.3-16 | bayside | 20 | 1 | -13.0 | -0.0087 | 0.0 |
| quietdrift90 | track-16 | a0.3-16 | blocks | 24 | 0 | -62.0 | -0.0382 | 0.0 |
| quietdrift90 | track-16 | a0.3-16 | boulevard | 11 | 3 | 0.0 | 0.0 | 0.0574 |
| outage90 | track-16 | a0.3-20 | bayside | 17 | 0 | -4.0 | -0.0027 | 0.0 |
| outage90 | track-16 | a0.3-20 | blocks | 24 | 0 | -23.0 | -0.0149 | 0.0 |
| outage90 | track-16 | a0.3-20 | boulevard | 0 | 12 | 1.0 | 0.0006 | 0.0005 |
| quiet90 | track-16 | a0.3-20 | bayside | 17 | 1 | -6.0 | -0.004 | 0.0001 |
| quiet90 | track-16 | a0.3-20 | blocks | 23 | 1 | -27.0 | -0.0175 | 0.0 |
| quiet90 | track-16 | a0.3-20 | boulevard | 11 | 1 | 0.0 | 0.0 | 0.0063 |
| quietdrift90 | track-16 | a0.3-20 | bayside | 19 | 1 | -10.0 | -0.0067 | 0.0 |
| quietdrift90 | track-16 | a0.3-20 | blocks | 23 | 1 | -28.0 | -0.0178 | 0.0 |
| quietdrift90 | track-16 | a0.3-20 | boulevard | 9 | 3 | 0.0 | 0.0 | 0.146 |
| outage90 | track-16 | track-12 | bayside | 19 | 1 | -4.0 | -0.0027 | 0.0 |
| outage90 | track-16 | track-12 | blocks | 24 | 0 | -29.0 | -0.0187 | 0.0 |
| outage90 | track-16 | track-12 | boulevard | 13 | 1 | -2.0 | -0.0011 | 0.0018 |
| quiet90 | track-16 | track-12 | bayside | 17 | 0 | -2.0 | -0.0014 | 0.0 |
| quiet90 | track-16 | track-12 | blocks | 24 | 0 | -29.0 | -0.0188 | 0.0 |
| quiet90 | track-16 | track-12 | boulevard | 3 | 1 | 0.0 | 0.0 | 0.625 |
| quietdrift90 | track-16 | track-12 | bayside | 18 | 0 | -3.0 | -0.002 | 0.0 |
| quietdrift90 | track-16 | track-12 | blocks | 23 | 1 | -28.0 | -0.0178 | 0.0 |
| quietdrift90 | track-16 | track-12 | boulevard | 10 | 1 | 0.0 | 0.0 | 0.0117 |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| a0.3-16 | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | -0.0006 |
| a0.3-16 | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0044 |
| track-12 | quiet90 | outage90 | 2/3 | 0 | 0 | 0 | -0.0032 |
| track-12 | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0045 |
| a0.3-20 | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | -0.0013 |
| a0.3-20 | quietdrift90 | quiet90 | 0/3 | 2 | 0 | 0 | 0.0065 |
| track-16 | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | -0.0013 |
| track-16 | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0053 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | 24 | 6.42 | 8.68 |
| outage90 | a0.3-16 | blocks | 24 | 6.41 | 8.69 |
| outage90 | a0.3-16 | boulevard | 24 | 6.47 | 8.89 |
| outage90 | a0.3-20 | bayside | 24 | 6.42 | 8.7 |
| outage90 | a0.3-20 | blocks | 24 | 6.41 | 8.68 |
| outage90 | a0.3-20 | boulevard | 24 | 6.47 | 8.91 |
| outage90 | track-12 | bayside | 24 | 2.62 | 4.96 |
| outage90 | track-12 | blocks | 24 | 3.0 | 5.96 |
| outage90 | track-12 | boulevard | 24 | 2.64 | 5.04 |
| outage90 | track-16 | bayside | 24 | 2.62 | 4.97 |
| outage90 | track-16 | blocks | 24 | 2.96 | 5.79 |
| outage90 | track-16 | boulevard | 24 | 2.58 | 5.19 |
| quiet90 | a0.3-16 | bayside | 24 | 6.4 | 8.45 |
| quiet90 | a0.3-16 | blocks | 24 | 6.31 | 8.43 |
| quiet90 | a0.3-16 | boulevard | 24 | 6.39 | 8.59 |
| quiet90 | a0.3-20 | bayside | 24 | 6.4 | 8.46 |
| quiet90 | a0.3-20 | blocks | 24 | 6.3 | 8.36 |
| quiet90 | a0.3-20 | boulevard | 24 | 6.39 | 8.59 |
| quiet90 | track-12 | bayside | 24 | 2.25 | 4.25 |
| quiet90 | track-12 | blocks | 24 | 2.38 | 5.27 |
| quiet90 | track-12 | boulevard | 24 | 2.18 | 4.15 |
| quiet90 | track-16 | bayside | 24 | 2.25 | 4.23 |
| quiet90 | track-16 | blocks | 24 | 2.37 | 5.08 |
| quiet90 | track-16 | boulevard | 24 | 2.17 | 4.15 |
| quietdrift90 | a0.3-16 | bayside | 24 | 6.44 | 8.82 |
| quietdrift90 | a0.3-16 | blocks | 24 | 6.33 | 8.45 |
| quietdrift90 | a0.3-16 | boulevard | 24 | 6.44 | 8.72 |
| quietdrift90 | a0.3-20 | bayside | 24 | 6.45 | 8.77 |
| quietdrift90 | a0.3-20 | blocks | 24 | 6.34 | 8.54 |
| quietdrift90 | a0.3-20 | boulevard | 24 | 6.44 | 8.76 |
| quietdrift90 | track-12 | bayside | 24 | 2.39 | 4.87 |
| quietdrift90 | track-12 | blocks | 24 | 2.55 | 5.7 |
| quietdrift90 | track-12 | boulevard | 24 | 2.31 | 4.86 |
| quietdrift90 | track-16 | bayside | 24 | 2.38 | 4.99 |
| quietdrift90 | track-16 | blocks | 24 | 2.57 | 5.42 |
| quietdrift90 | track-16 | boulevard | 24 | 2.33 | 4.93 |

## Recovery moves and filter restarts

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | 24 | 1.0 | None |
| outage90 | a0.3-16 | blocks | 24 | 1.0 | None |
| outage90 | a0.3-16 | boulevard | 24 | 1.0 | None |
| outage90 | a0.3-20 | bayside | 24 | 1.0 | None |
| outage90 | a0.3-20 | blocks | 24 | 1.0 | None |
| outage90 | a0.3-20 | boulevard | 24 | 1.0 | None |
| outage90 | track-12 | bayside | 24 | 1.0 | 4.0 |
| outage90 | track-12 | blocks | 24 | 1.0 | 4.5 |
| outage90 | track-12 | boulevard | 24 | 1.0 | 5.0 |
| outage90 | track-16 | bayside | 24 | 1.0 | 4.0 |
| outage90 | track-16 | blocks | 24 | 1.0 | 4.0 |
| outage90 | track-16 | boulevard | 24 | 1.0 | 5.0 |
| quiet90 | a0.3-16 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3-16 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3-16 | boulevard | 24 | 1.0 | None |
| quiet90 | a0.3-20 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3-20 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3-20 | boulevard | 24 | 1.0 | None |
| quiet90 | track-12 | bayside | 24 | 1.0 | 4.0 |
| quiet90 | track-12 | blocks | 24 | 1.0 | 4.5 |
| quiet90 | track-12 | boulevard | 24 | 1.0 | 5.0 |
| quiet90 | track-16 | bayside | 24 | 1.0 | 4.0 |
| quiet90 | track-16 | blocks | 24 | 1.0 | 4.0 |
| quiet90 | track-16 | boulevard | 24 | 1.0 | 5.0 |
| quietdrift90 | a0.3-16 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3-16 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3-16 | boulevard | 24 | 1.0 | None |
| quietdrift90 | a0.3-20 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3-20 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3-20 | boulevard | 24 | 1.0 | None |
| quietdrift90 | track-12 | bayside | 24 | 1.0 | 4.0 |
| quietdrift90 | track-12 | blocks | 24 | 1.0 | 4.5 |
| quietdrift90 | track-12 | boulevard | 24 | 1.0 | 5.0 |
| quietdrift90 | track-16 | bayside | 24 | 1.0 | 4.0 |
| quietdrift90 | track-16 | blocks | 24 | 1.0 | 4.5 |
| quietdrift90 | track-16 | boulevard | 24 | 1.0 | 5.0 |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| outage90 | a0.3-16 | blocks | 24 | 9.0 | 1.1 | 2.95 | 4.63 | 2.12 | 3.33 |
| outage90 | a0.3-20 | blocks | 24 | 9.0 | 0.97 | 3.06 | 4.96 | 1.15 | 2.47 |
| outage90 | track-12 | blocks | 24 | 9.0 | 1.07 | 3.08 | 4.54 | -0.99 | 0.98 |
| outage90 | track-16 | blocks | 24 | 9.0 | 1.78 | 3.88 | 5.17 | -1.94 | 0.01 |
| quiet90 | a0.3-16 | blocks | 24 | 9.0 | 0.94 | 2.71 | 4.8 | 1.99 | 2.76 |
| quiet90 | a0.3-20 | blocks | 24 | 9.0 | 0.81 | 3.26 | 5.74 | 1.07 | 1.75 |
| quiet90 | track-12 | blocks | 24 | 9.0 | 1.04 | 2.27 | 3.27 | -1.08 | 0.02 |
| quiet90 | track-16 | blocks | 24 | 9.0 | 1.98 | 3.65 | 4.47 | -2.02 | -0.64 |
| quietdrift90 | a0.3-16 | blocks | 24 | 9.0 | 1.56 | 4.29 | 5.28 | 2.2 | 4.23 |
| quietdrift90 | a0.3-20 | blocks | 24 | 9.0 | 1.56 | 4.69 | 6.98 | 0.99 | 4.08 |
| quietdrift90 | track-12 | blocks | 24 | 9.0 | 1.21 | 3.67 | 5.55 | -0.83 | 1.38 |
| quietdrift90 | track-16 | blocks | 24 | 9.0 | 2.0 | 4.37 | 5.65 | -1.83 | 1.08 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | 24 | 0.61 | 3.99 |
| outage90 | a0.3-16 | blocks | 24 | 0.8 | 3.38 |
| outage90 | a0.3-16 | boulevard | 24 | 0.67 | 3.86 |
| outage90 | a0.3-20 | bayside | 24 | 0.67 | 4.0 |
| outage90 | a0.3-20 | blocks | 24 | 0.77 | 3.85 |
| outage90 | a0.3-20 | boulevard | 24 | 0.77 | 3.79 |
| outage90 | track-12 | bayside | 24 | 0.8 | 3.63 |
| outage90 | track-12 | blocks | 24 | 0.86 | 3.58 |
| outage90 | track-12 | boulevard | 24 | 0.65 | 3.52 |
| outage90 | track-16 | bayside | 24 | 0.97 | 3.38 |
| outage90 | track-16 | blocks | 24 | 1.07 | 3.75 |
| outage90 | track-16 | boulevard | 24 | 0.72 | 4.18 |
| quiet90 | a0.3-16 | bayside | 24 | 0.21 | 2.32 |
| quiet90 | a0.3-16 | blocks | 24 | 0.33 | 3.15 |
| quiet90 | a0.3-16 | boulevard | 24 | 0.15 | 1.04 |
| quiet90 | a0.3-20 | bayside | 24 | 0.32 | 2.59 |
| quiet90 | a0.3-20 | blocks | 24 | 0.44 | 3.55 |
| quiet90 | a0.3-20 | boulevard | 24 | 0.16 | 1.23 |
| quiet90 | track-12 | bayside | 24 | 0.56 | 1.35 |
| quiet90 | track-12 | blocks | 24 | 0.36 | 2.33 |
| quiet90 | track-12 | boulevard | 24 | 0.14 | 0.96 |
| quiet90 | track-16 | bayside | 24 | 0.82 | 1.81 |
| quiet90 | track-16 | blocks | 24 | 0.55 | 3.3 |
| quiet90 | track-16 | boulevard | 24 | 0.15 | 1.18 |
| quietdrift90 | a0.3-16 | bayside | 24 | 1.42 | 6.26 |
| quietdrift90 | a0.3-16 | blocks | 24 | 1.71 | 5.44 |
| quietdrift90 | a0.3-16 | boulevard | 24 | 1.52 | 6.26 |
| quietdrift90 | a0.3-20 | bayside | 24 | 1.69 | 6.28 |
| quietdrift90 | a0.3-20 | blocks | 24 | 1.75 | 6.26 |
| quietdrift90 | a0.3-20 | boulevard | 24 | 1.83 | 6.96 |
| quietdrift90 | track-12 | bayside | 24 | 1.17 | 5.12 |
| quietdrift90 | track-12 | blocks | 24 | 1.29 | 4.88 |
| quietdrift90 | track-12 | boulevard | 24 | 1.15 | 4.78 |
| quietdrift90 | track-16 | bayside | 24 | 1.42 | 5.56 |
| quietdrift90 | track-16 | blocks | 24 | 1.74 | 5.54 |
| quietdrift90 | track-16 | boulevard | 24 | 1.41 | 5.63 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | 24 | 7.34 | 11.2 | 0 | 0 |
| outage90 | a0.3-16 | blocks | 24 | 7.67 | 13.23 | 0 | 0 |
| outage90 | a0.3-16 | boulevard | 24 | 7.26 | 11.55 | 0 | 0 |
| outage90 | a0.3-20 | bayside | 24 | 8.0 | 10.46 | 0 | 0 |
| outage90 | a0.3-20 | blocks | 24 | 8.55 | 11.16 | 0 | 0 |
| outage90 | a0.3-20 | boulevard | 24 | 8.21 | 11.39 | 0 | 0 |
| outage90 | track-12 | bayside | 24 | 5.53 | 8.34 | 0 | 0 |
| outage90 | track-12 | blocks | 24 | 6.22 | 7.56 | 0 | 0 |
| outage90 | track-12 | boulevard | 24 | 6.55 | 32.68 | 0 | 0 |
| outage90 | track-16 | bayside | 24 | 6.31 | 9.37 | 0 | 0 |
| outage90 | track-16 | blocks | 24 | 6.71 | 10.22 | 0 | 0 |
| outage90 | track-16 | boulevard | 24 | 6.91 | 11.64 | 0 | 0 |
| quiet90 | a0.3-16 | bayside | 24 | 7.31 | 7.55 | 0 | 0 |
| quiet90 | a0.3-16 | blocks | 24 | 7.4 | 9.46 | 0 | 0 |
| quiet90 | a0.3-16 | boulevard | 24 | 7.36 | 7.88 | 0 | 0 |
| quiet90 | a0.3-20 | bayside | 24 | 8.09 | 8.6 | 0 | 0 |
| quiet90 | a0.3-20 | blocks | 24 | 8.37 | 9.18 | 0 | 0 |
| quiet90 | a0.3-20 | boulevard | 24 | 8.44 | 9.22 | 0 | 0 |
| quiet90 | track-12 | bayside | 24 | 5.28 | 5.6 | 0 | 0 |
| quiet90 | track-12 | blocks | 24 | 5.33 | 5.79 | 0 | 0 |
| quiet90 | track-12 | boulevard | 24 | 5.32 | 5.78 | 0 | 0 |
| quiet90 | track-16 | bayside | 24 | 6.19 | 6.84 | 0 | 0 |
| quiet90 | track-16 | blocks | 24 | 6.56 | 7.44 | 0 | 0 |
| quiet90 | track-16 | boulevard | 24 | 6.62 | 7.37 | 0 | 0 |
| quietdrift90 | a0.3-16 | bayside | 24 | 9.8 | 27.3 | 0 | 0 |
| quietdrift90 | a0.3-16 | blocks | 24 | 10.33 | 24.74 | 0 | 0 |
| quietdrift90 | a0.3-16 | boulevard | 24 | 10.96 | 25.54 | 0 | 0 |
| quietdrift90 | a0.3-20 | bayside | 24 | 10.44 | 27.12 | 0 | 0 |
| quietdrift90 | a0.3-20 | blocks | 24 | 10.8 | 21.36 | 0 | 0 |
| quietdrift90 | a0.3-20 | boulevard | 24 | 11.46 | 28.27 | 0 | 0 |
| quietdrift90 | track-12 | bayside | 24 | 8.9 | 24.81 | 0 | 0 |
| quietdrift90 | track-12 | blocks | 24 | 8.31 | 22.62 | 0 | 0 |
| quietdrift90 | track-12 | boulevard | 24 | 10.89 | 24.82 | 0 | 0 |
| quietdrift90 | track-16 | bayside | 24 | 9.47 | 25.49 | 0 | 0 |
| quietdrift90 | track-16 | blocks | 24 | 9.45 | 20.92 | 0 | 0 |
| quietdrift90 | track-16 | boulevard | 24 | 10.59 | 25.04 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | checkpoint | 24 | 6351 | 0 | 0.0 | 0.57 | 2.08 | 2.98 |
| outage90 | a0.3-16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3-16 | bayside | other | 24 | 26569 | 78 | 1.0 | 0.66 | 4.18 | 7.34 |
| outage90 | a0.3-16 | bayside | outage | 22 | 4338 | 26 | 0.333 | 2.02 | 4.25 | 4.79 |
| outage90 | a0.3-16 | bayside | fix | 24 | 28582 | 52 | 0.667 | 0.52 | 3.16 | 7.34 |
| outage90 | a0.3-16 | blocks | checkpoint | 24 | 8315 | 13 | 0.12 | 0.9 | 3.29 | 5.27 |
| outage90 | a0.3-16 | blocks | corner | 24 | 8707 | 27 | 0.25 | 1.1 | 2.95 | 4.63 |
| outage90 | a0.3-16 | blocks | other | 24 | 18786 | 68 | 0.63 | 0.68 | 4.38 | 7.46 |
| outage90 | a0.3-16 | blocks | outage | 22 | 4644 | 6 | 0.056 | 2.12 | 3.81 | 5.23 |
| outage90 | a0.3-16 | blocks | fix | 24 | 31164 | 102 | 0.944 | 0.73 | 3.34 | 7.62 |
| outage90 | a0.3-16 | boulevard | checkpoint | 24 | 6294 | 0 | 0.0 | 0.6 | 1.76 | 1.9 |
| outage90 | a0.3-16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3-16 | boulevard | other | 24 | 33646 | 112 | 1.0 | 0.71 | 3.92 | 7.26 |
| outage90 | a0.3-16 | boulevard | outage | 24 | 5197 | 46 | 0.411 | 1.89 | 4.07 | 4.82 |
| outage90 | a0.3-16 | boulevard | fix | 24 | 34743 | 66 | 0.589 | 0.62 | 2.8 | 7.26 |
| outage90 | a0.3-20 | bayside | checkpoint | 24 | 6335 | 0 | 0.0 | 0.58 | 2.37 | 3.25 |
| outage90 | a0.3-20 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3-20 | bayside | other | 24 | 26451 | 143 | 1.0 | 0.73 | 4.55 | 8.0 |
| outage90 | a0.3-20 | bayside | outage | 22 | 4296 | 30 | 0.21 | 1.6 | 3.85 | 4.21 |
| outage90 | a0.3-20 | bayside | fix | 24 | 28490 | 113 | 0.79 | 0.65 | 3.54 | 8.0 |
| outage90 | a0.3-20 | blocks | checkpoint | 24 | 8201 | 46 | 0.192 | 0.89 | 3.41 | 4.89 |
| outage90 | a0.3-20 | blocks | corner | 24 | 8201 | 36 | 0.15 | 0.97 | 3.06 | 4.96 |
| outage90 | a0.3-20 | blocks | other | 24 | 18714 | 158 | 0.658 | 0.72 | 4.7 | 8.25 |
| outage90 | a0.3-20 | blocks | outage | 22 | 4602 | 13 | 0.054 | 1.58 | 4.04 | 5.42 |
| outage90 | a0.3-20 | blocks | fix | 24 | 30514 | 227 | 0.946 | 0.73 | 3.6 | 8.55 |
| outage90 | a0.3-20 | boulevard | checkpoint | 24 | 6277 | 0 | 0.0 | 0.66 | 1.96 | 2.17 |
| outage90 | a0.3-20 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3-20 | boulevard | other | 24 | 33626 | 265 | 1.0 | 0.79 | 3.9 | 8.21 |
| outage90 | a0.3-20 | boulevard | outage | 24 | 5192 | 78 | 0.294 | 1.69 | 4.09 | 4.32 |
| outage90 | a0.3-20 | boulevard | fix | 24 | 34711 | 187 | 0.706 | 0.68 | 2.71 | 8.21 |
| outage90 | track-12 | bayside | checkpoint | 24 | 6344 | 0 | 0.0 | 0.67 | 2.2 | 2.92 |
| outage90 | track-12 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | track-12 | bayside | other | 24 | 26396 | 7 | 1.0 | 0.83 | 3.75 | 5.53 |
| outage90 | track-12 | bayside | outage | 22 | 4290 | 4 | 0.571 | 2.08 | 4.1 | 4.31 |
| outage90 | track-12 | bayside | fix | 24 | 28450 | 3 | 0.429 | 0.7 | 2.49 | 5.53 |
| outage90 | track-12 | blocks | checkpoint | 24 | 8161 | 0 | None | 0.9 | 2.85 | 3.73 |
| outage90 | track-12 | blocks | corner | 24 | 8319 | 0 | None | 1.07 | 3.08 | 4.54 |
| outage90 | track-12 | blocks | other | 24 | 18665 | 0 | None | 0.76 | 4.03 | 5.88 |
| outage90 | track-12 | blocks | outage | 22 | 4488 | 0 | None | 1.63 | 4.0 | 4.96 |
| outage90 | track-12 | blocks | fix | 24 | 30657 | 0 | None | 0.82 | 3.02 | 6.05 |
| outage90 | track-12 | boulevard | checkpoint | 24 | 6291 | 29 | 0.084 | 0.76 | 1.81 | 2.21 |
| outage90 | track-12 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | track-12 | boulevard | other | 24 | 33732 | 318 | 0.916 | 0.63 | 3.72 | 6.55 |
| outage90 | track-12 | boulevard | outage | 24 | 5232 | 136 | 0.392 | 1.81 | 4.12 | 4.39 |
| outage90 | track-12 | boulevard | fix | 24 | 34791 | 211 | 0.608 | 0.56 | 2.34 | 6.55 |
| outage90 | track-16 | bayside | checkpoint | 24 | 6329 | 0 | 0.0 | 0.8 | 2.23 | 2.9 |
| outage90 | track-16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | track-16 | bayside | other | 24 | 26304 | 35 | 1.0 | 1.04 | 3.66 | 6.31 |
| outage90 | track-16 | bayside | outage | 22 | 4325 | 27 | 0.771 | 2.0 | 3.73 | 4.06 |
| outage90 | track-16 | bayside | fix | 24 | 28308 | 8 | 0.229 | 0.92 | 2.85 | 6.31 |
| outage90 | track-16 | blocks | checkpoint | 24 | 7969 | 6 | 0.111 | 1.08 | 3.21 | 4.24 |
| outage90 | track-16 | blocks | corner | 24 | 7799 | 10 | 0.185 | 1.78 | 3.88 | 5.17 |
| outage90 | track-16 | blocks | other | 24 | 18645 | 38 | 0.704 | 0.9 | 3.93 | 6.69 |
| outage90 | track-16 | blocks | outage | 22 | 4489 | 31 | 0.574 | 1.41 | 3.9 | 5.26 |
| outage90 | track-16 | blocks | fix | 24 | 29924 | 23 | 0.426 | 1.02 | 3.66 | 6.69 |
| outage90 | track-16 | boulevard | checkpoint | 24 | 6288 | 0 | 0.0 | 0.85 | 1.97 | 2.46 |
| outage90 | track-16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | track-16 | boulevard | other | 24 | 33663 | 158 | 1.0 | 0.69 | 4.17 | 6.91 |
| outage90 | track-16 | boulevard | outage | 24 | 5207 | 115 | 0.728 | 1.81 | 5.19 | 5.7 |
| outage90 | track-16 | boulevard | fix | 24 | 34744 | 43 | 0.272 | 0.65 | 2.46 | 6.91 |
| quiet90 | a0.3-16 | bayside | checkpoint | 24 | 6327 | 0 | None | 0.17 | 0.65 | 0.98 |
| quiet90 | a0.3-16 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3-16 | bayside | other | 24 | 26531 | 0 | None | 0.23 | 3.08 | 7.31 |
| quiet90 | a0.3-16 | bayside | outage | 22 | 4241 | 0 | None | 0.59 | 1.59 | 2.0 |
| quiet90 | a0.3-16 | bayside | fix | 24 | 28617 | 0 | None | 0.2 | 2.96 | 7.31 |
| quiet90 | a0.3-16 | blocks | checkpoint | 24 | 8318 | 12 | 1.0 | 0.43 | 2.85 | 3.98 |
| quiet90 | a0.3-16 | blocks | corner | 24 | 8633 | 0 | 0.0 | 0.94 | 2.71 | 4.8 |
| quiet90 | a0.3-16 | blocks | other | 24 | 18813 | 0 | 0.0 | 0.23 | 3.69 | 7.31 |
| quiet90 | a0.3-16 | blocks | outage | 22 | 4610 | 0 | 0.0 | 0.53 | 3.34 | 4.84 |
| quiet90 | a0.3-16 | blocks | fix | 24 | 31154 | 12 | 1.0 | 0.29 | 3.0 | 7.33 |
| quiet90 | a0.3-16 | boulevard | checkpoint | 24 | 6285 | 0 | None | 0.18 | 0.65 | 0.84 |
| quiet90 | a0.3-16 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3-16 | boulevard | other | 24 | 33621 | 0 | None | 0.14 | 1.19 | 7.36 |
| quiet90 | a0.3-16 | boulevard | outage | 24 | 5250 | 0 | None | 0.35 | 1.17 | 1.31 |
| quiet90 | a0.3-16 | boulevard | fix | 24 | 34656 | 0 | None | 0.14 | 0.92 | 7.36 |
| quiet90 | a0.3-20 | bayside | checkpoint | 24 | 6319 | 0 | 0.0 | 0.26 | 0.93 | 1.44 |
| quiet90 | a0.3-20 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3-20 | bayside | other | 24 | 26442 | 70 | 1.0 | 0.34 | 3.08 | 8.09 |
| quiet90 | a0.3-20 | bayside | outage | 22 | 4293 | 0 | 0.0 | 0.84 | 2.04 | 2.48 |
| quiet90 | a0.3-20 | bayside | fix | 24 | 28468 | 70 | 1.0 | 0.28 | 2.83 | 8.09 |
| quiet90 | a0.3-20 | blocks | checkpoint | 24 | 8173 | 11 | 0.061 | 0.56 | 2.5 | 3.7 |
| quiet90 | a0.3-20 | blocks | corner | 24 | 8160 | 0 | 0.0 | 0.81 | 3.26 | 5.74 |
| quiet90 | a0.3-20 | blocks | other | 24 | 18758 | 168 | 0.939 | 0.31 | 4.14 | 8.37 |
| quiet90 | a0.3-20 | blocks | outage | 22 | 4714 | 0 | 0.0 | 0.77 | 4.2 | 5.79 |
| quiet90 | a0.3-20 | blocks | fix | 24 | 30377 | 179 | 1.0 | 0.39 | 3.17 | 8.37 |
| quiet90 | a0.3-20 | boulevard | checkpoint | 24 | 6278 | 0 | 0.0 | 0.18 | 0.79 | 1.14 |
| quiet90 | a0.3-20 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3-20 | boulevard | other | 24 | 33618 | 176 | 1.0 | 0.17 | 1.23 | 8.44 |
| quiet90 | a0.3-20 | boulevard | outage | 24 | 5247 | 0 | 0.0 | 0.36 | 1.18 | 1.33 |
| quiet90 | a0.3-20 | boulevard | fix | 24 | 34649 | 176 | 1.0 | 0.15 | 1.19 | 8.44 |
| quiet90 | track-12 | bayside | checkpoint | 24 | 6309 | 0 | None | 0.46 | 0.99 | 1.25 |
| quiet90 | track-12 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | track-12 | bayside | other | 24 | 26307 | 0 | None | 0.6 | 1.46 | 5.28 |
| quiet90 | track-12 | bayside | outage | 22 | 4299 | 0 | None | 0.65 | 1.38 | 1.64 |
| quiet90 | track-12 | bayside | fix | 24 | 28317 | 0 | None | 0.56 | 1.35 | 5.28 |
| quiet90 | track-12 | blocks | checkpoint | 24 | 8062 | 0 | None | 0.45 | 2.12 | 2.59 |
| quiet90 | track-12 | blocks | corner | 24 | 8312 | 0 | None | 1.04 | 2.27 | 3.27 |
| quiet90 | track-12 | blocks | other | 24 | 18626 | 0 | None | 0.27 | 2.49 | 5.33 |
| quiet90 | track-12 | blocks | outage | 22 | 4453 | 0 | None | 0.56 | 2.06 | 3.35 |
| quiet90 | track-12 | blocks | fix | 24 | 30547 | 0 | None | 0.32 | 2.34 | 5.33 |
| quiet90 | track-12 | boulevard | checkpoint | 24 | 6265 | 0 | None | 0.22 | 0.91 | 1.17 |
| quiet90 | track-12 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | track-12 | boulevard | other | 24 | 33609 | 0 | None | 0.13 | 1.04 | 5.32 |
| quiet90 | track-12 | boulevard | outage | 24 | 5080 | 0 | None | 0.36 | 1.15 | 1.27 |
| quiet90 | track-12 | boulevard | fix | 24 | 34794 | 0 | None | 0.13 | 0.87 | 5.32 |
| quiet90 | track-16 | bayside | checkpoint | 24 | 6297 | 0 | None | 0.64 | 1.4 | 1.69 |
| quiet90 | track-16 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | track-16 | bayside | other | 24 | 26262 | 0 | None | 0.89 | 1.94 | 6.19 |
| quiet90 | track-16 | bayside | outage | 22 | 4280 | 0 | None | 0.81 | 1.72 | 2.1 |
| quiet90 | track-16 | bayside | fix | 24 | 28279 | 0 | None | 0.83 | 1.81 | 6.19 |
| quiet90 | track-16 | blocks | checkpoint | 24 | 7954 | 0 | None | 0.69 | 2.51 | 3.69 |
| quiet90 | track-16 | blocks | corner | 24 | 7771 | 0 | None | 1.98 | 3.65 | 4.47 |
| quiet90 | track-16 | blocks | other | 24 | 18607 | 0 | None | 0.36 | 2.98 | 6.56 |
| quiet90 | track-16 | blocks | outage | 22 | 4467 | 0 | None | 0.69 | 2.73 | 4.54 |
| quiet90 | track-16 | blocks | fix | 24 | 29865 | 0 | None | 0.48 | 3.31 | 6.56 |
| quiet90 | track-16 | boulevard | checkpoint | 24 | 6262 | 0 | None | 0.27 | 1.21 | 1.5 |
| quiet90 | track-16 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | track-16 | boulevard | other | 24 | 33608 | 0 | None | 0.14 | 1.15 | 6.62 |
| quiet90 | track-16 | boulevard | outage | 24 | 5165 | 0 | None | 0.35 | 1.15 | 1.37 |
| quiet90 | track-16 | boulevard | fix | 24 | 34705 | 0 | None | 0.14 | 1.13 | 6.62 |
| quietdrift90 | a0.3-16 | bayside | checkpoint | 24 | 6383 | 42 | 0.034 | 1.33 | 3.69 | 4.06 |
| quietdrift90 | a0.3-16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3-16 | bayside | other | 24 | 26723 | 1180 | 0.966 | 1.42 | 5.92 | 9.8 |
| quietdrift90 | a0.3-16 | bayside | outage | 22 | 4373 | 663 | 0.543 | 2.28 | 8.99 | 9.56 |
| quietdrift90 | a0.3-16 | bayside | fix | 24 | 28733 | 559 | 0.457 | 1.29 | 4.71 | 9.6 |
| quietdrift90 | a0.3-16 | blocks | checkpoint | 24 | 8413 | 106 | 0.119 | 1.52 | 5.37 | 7.29 |
| quietdrift90 | a0.3-16 | blocks | corner | 24 | 8590 | 131 | 0.147 | 1.56 | 4.29 | 5.28 |
| quietdrift90 | a0.3-16 | blocks | other | 24 | 18990 | 652 | 0.733 | 1.65 | 5.95 | 9.73 |
| quietdrift90 | a0.3-16 | blocks | outage | 22 | 4572 | 468 | 0.526 | 2.92 | 7.34 | 8.29 |
| quietdrift90 | a0.3-16 | blocks | fix | 24 | 31421 | 421 | 0.474 | 1.6 | 4.86 | 9.62 |
| quietdrift90 | a0.3-16 | boulevard | checkpoint | 24 | 6318 | 44 | 0.039 | 1.29 | 3.69 | 4.03 |
| quietdrift90 | a0.3-16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3-16 | boulevard | other | 24 | 33803 | 1097 | 0.961 | 1.58 | 6.8 | 10.96 |
| quietdrift90 | a0.3-16 | boulevard | outage | 24 | 5158 | 574 | 0.503 | 2.38 | 8.32 | 10.15 |
| quietdrift90 | a0.3-16 | boulevard | fix | 24 | 34963 | 567 | 0.497 | 1.46 | 5.12 | 10.96 |
| quietdrift90 | a0.3-20 | bayside | checkpoint | 24 | 6360 | 44 | 0.033 | 1.5 | 4.0 | 4.33 |
| quietdrift90 | a0.3-20 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3-20 | bayside | other | 24 | 26638 | 1305 | 0.967 | 1.71 | 6.18 | 10.44 |
| quietdrift90 | a0.3-20 | bayside | outage | 22 | 4323 | 674 | 0.5 | 2.62 | 8.56 | 9.5 |
| quietdrift90 | a0.3-20 | bayside | fix | 24 | 28675 | 675 | 0.5 | 1.6 | 5.42 | 10.41 |
| quietdrift90 | a0.3-20 | blocks | checkpoint | 24 | 8282 | 163 | 0.14 | 1.48 | 6.0 | 7.97 |
| quietdrift90 | a0.3-20 | blocks | corner | 24 | 8054 | 127 | 0.109 | 1.56 | 4.69 | 6.98 |
| quietdrift90 | a0.3-20 | blocks | other | 24 | 18973 | 875 | 0.751 | 1.83 | 7.28 | 10.59 |
| quietdrift90 | a0.3-20 | blocks | outage | 22 | 4580 | 548 | 0.47 | 3.26 | 7.46 | 8.78 |
| quietdrift90 | a0.3-20 | blocks | fix | 24 | 30729 | 617 | 0.53 | 1.61 | 5.79 | 9.91 |
| quietdrift90 | a0.3-20 | boulevard | checkpoint | 24 | 6324 | 59 | 0.04 | 1.58 | 4.39 | 4.74 |
| quietdrift90 | a0.3-20 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3-20 | boulevard | other | 24 | 33803 | 1426 | 0.96 | 1.89 | 7.39 | 11.46 |
| quietdrift90 | a0.3-20 | boulevard | outage | 24 | 5235 | 674 | 0.454 | 2.43 | 8.92 | 10.36 |
| quietdrift90 | a0.3-20 | boulevard | fix | 24 | 34892 | 811 | 0.546 | 1.78 | 5.88 | 11.29 |
| quietdrift90 | track-12 | bayside | checkpoint | 24 | 6366 | 84 | 0.093 | 0.97 | 2.94 | 3.58 |
| quietdrift90 | track-12 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | track-12 | bayside | other | 24 | 26518 | 820 | 0.907 | 1.21 | 4.95 | 8.9 |
| quietdrift90 | track-12 | bayside | outage | 22 | 4420 | 602 | 0.666 | 2.09 | 8.62 | 8.9 |
| quietdrift90 | track-12 | bayside | fix | 24 | 28464 | 302 | 0.334 | 1.13 | 3.71 | 8.07 |
| quietdrift90 | track-12 | blocks | checkpoint | 24 | 8117 | 80 | 0.142 | 1.17 | 4.33 | 5.38 |
| quietdrift90 | track-12 | blocks | corner | 24 | 8259 | 48 | 0.085 | 1.21 | 3.67 | 5.55 |
| quietdrift90 | track-12 | blocks | other | 24 | 18808 | 437 | 0.773 | 1.27 | 5.58 | 7.93 |
| quietdrift90 | track-12 | blocks | outage | 22 | 4440 | 423 | 0.749 | 2.23 | 7.19 | 7.94 |
| quietdrift90 | track-12 | blocks | fix | 24 | 30744 | 142 | 0.251 | 1.23 | 4.16 | 7.2 |
| quietdrift90 | track-12 | boulevard | checkpoint | 24 | 6309 | 20 | 0.023 | 1.11 | 2.78 | 3.2 |
| quietdrift90 | track-12 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | track-12 | boulevard | other | 24 | 33825 | 845 | 0.977 | 1.17 | 5.52 | 10.89 |
| quietdrift90 | track-12 | boulevard | outage | 24 | 5166 | 602 | 0.696 | 2.33 | 8.67 | 10.4 |
| quietdrift90 | track-12 | boulevard | fix | 24 | 34968 | 263 | 0.304 | 1.06 | 3.42 | 10.71 |
| quietdrift90 | track-16 | bayside | checkpoint | 24 | 6359 | 64 | 0.068 | 1.29 | 3.65 | 4.08 |
| quietdrift90 | track-16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | track-16 | bayside | other | 24 | 26418 | 873 | 0.932 | 1.5 | 5.55 | 9.47 |
| quietdrift90 | track-16 | bayside | outage | 22 | 4371 | 620 | 0.662 | 2.46 | 8.08 | 9.02 |
| quietdrift90 | track-16 | bayside | fix | 24 | 28406 | 317 | 0.338 | 1.38 | 4.5 | 8.5 |
| quietdrift90 | track-16 | blocks | checkpoint | 24 | 8012 | 90 | 0.137 | 1.73 | 4.63 | 5.75 |
| quietdrift90 | track-16 | blocks | corner | 24 | 7699 | 78 | 0.119 | 2.0 | 4.37 | 5.65 |
| quietdrift90 | track-16 | blocks | other | 24 | 18794 | 489 | 0.744 | 1.68 | 6.29 | 9.18 |
| quietdrift90 | track-16 | blocks | outage | 22 | 4488 | 425 | 0.647 | 2.69 | 7.23 | 8.57 |
| quietdrift90 | track-16 | blocks | fix | 24 | 30017 | 232 | 0.353 | 1.71 | 4.77 | 8.5 |
| quietdrift90 | track-16 | boulevard | checkpoint | 24 | 6293 | 25 | 0.027 | 1.32 | 3.43 | 3.74 |
| quietdrift90 | track-16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | track-16 | boulevard | other | 24 | 33807 | 888 | 0.973 | 1.43 | 6.14 | 10.59 |
| quietdrift90 | track-16 | boulevard | outage | 24 | 5156 | 572 | 0.627 | 2.5 | 8.51 | 10.2 |
| quietdrift90 | track-16 | boulevard | fix | 24 | 34944 | 341 | 0.373 | 1.33 | 4.28 | 10.59 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | 24 | 1.59 | 4.67 |
| outage90 | a0.3-16 | blocks | 24 | 1.61 | 4.38 |
| outage90 | a0.3-16 | boulevard | 24 | 1.54 | 4.13 |
| outage90 | a0.3-20 | bayside | 24 | 1.56 | 4.54 |
| outage90 | a0.3-20 | blocks | 24 | 1.62 | 4.34 |
| outage90 | a0.3-20 | boulevard | 24 | 1.57 | 4.12 |
| outage90 | track-12 | bayside | 24 | 1.62 | 4.88 |
| outage90 | track-12 | blocks | 24 | 1.72 | 4.54 |
| outage90 | track-12 | boulevard | 24 | 1.6 | 4.39 |
| outage90 | track-16 | bayside | 24 | 1.65 | 4.84 |
| outage90 | track-16 | blocks | 24 | 1.72 | 4.54 |
| outage90 | track-16 | boulevard | 24 | 1.55 | 4.25 |
| quiet90 | a0.3-16 | bayside | 24 | 0.99 | 4.26 |
| quiet90 | a0.3-16 | blocks | 24 | 1.02 | 4.14 |
| quiet90 | a0.3-16 | boulevard | 24 | 0.96 | 3.84 |
| quiet90 | a0.3-20 | bayside | 24 | 0.99 | 4.27 |
| quiet90 | a0.3-20 | blocks | 24 | 1.01 | 4.17 |
| quiet90 | a0.3-20 | boulevard | 24 | 0.96 | 3.84 |
| quiet90 | track-12 | bayside | 24 | 0.99 | 4.29 |
| quiet90 | track-12 | blocks | 24 | 1.04 | 4.14 |
| quiet90 | track-12 | boulevard | 24 | 0.96 | 3.86 |
| quiet90 | track-16 | bayside | 24 | 0.99 | 4.28 |
| quiet90 | track-16 | blocks | 24 | 1.02 | 4.19 |
| quiet90 | track-16 | boulevard | 24 | 0.96 | 3.84 |
| quietdrift90 | a0.3-16 | bayside | 24 | 5.34 | 8.66 |
| quietdrift90 | a0.3-16 | blocks | 24 | 5.64 | 8.67 |
| quietdrift90 | a0.3-16 | boulevard | 24 | 5.31 | 8.36 |
| quietdrift90 | a0.3-20 | bayside | 24 | 5.3 | 8.65 |
| quietdrift90 | a0.3-20 | blocks | 24 | 5.2 | 8.94 |
| quietdrift90 | a0.3-20 | boulevard | 24 | 5.19 | 8.43 |
| quietdrift90 | track-12 | bayside | 24 | 5.29 | 8.72 |
| quietdrift90 | track-12 | blocks | 24 | 5.23 | 8.86 |
| quietdrift90 | track-12 | boulevard | 24 | 5.29 | 8.3 |
| quietdrift90 | track-16 | bayside | 24 | 5.36 | 8.63 |
| quietdrift90 | track-16 | blocks | 24 | 5.08 | 8.51 |
| quietdrift90 | track-16 | boulevard | 24 | 5.21 | 8.33 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| outage90 | a0.3-16 | bayside | 24 | 0.0315 |
| outage90 | a0.3-16 | blocks | 24 | 0.0417 |
| outage90 | a0.3-16 | boulevard | 24 | 0.0272 |
| outage90 | a0.3-20 | bayside | 24 | 0.0288 |
| outage90 | a0.3-20 | blocks | 24 | 0.0393 |
| outage90 | a0.3-20 | boulevard | 24 | 0.0248 |
| outage90 | track-12 | bayside | 24 | 0.0344 |
| outage90 | track-12 | blocks | 24 | 0.046 |
| outage90 | track-12 | boulevard | 24 | 0.0321 |
| outage90 | track-16 | bayside | 24 | 0.0297 |
| outage90 | track-16 | blocks | 24 | 0.0408 |
| outage90 | track-16 | boulevard | 24 | 0.0278 |
| quiet90 | a0.3-16 | bayside | 24 | 0.0249 |
| quiet90 | a0.3-16 | blocks | 24 | 0.0361 |
| quiet90 | a0.3-16 | boulevard | 24 | 0.02 |
| quiet90 | a0.3-20 | bayside | 24 | 0.0241 |
| quiet90 | a0.3-20 | blocks | 24 | 0.035 |
| quiet90 | a0.3-20 | boulevard | 24 | 0.0198 |
| quiet90 | track-12 | bayside | 24 | 0.0236 |
| quiet90 | track-12 | blocks | 24 | 0.0368 |
| quiet90 | track-12 | boulevard | 24 | 0.0206 |
| quiet90 | track-16 | bayside | 24 | 0.0227 |
| quiet90 | track-16 | blocks | 24 | 0.0347 |
| quiet90 | track-16 | boulevard | 24 | 0.0202 |
| quietdrift90 | a0.3-16 | bayside | 24 | 0.0289 |
| quietdrift90 | a0.3-16 | blocks | 24 | 0.0398 |
| quietdrift90 | a0.3-16 | boulevard | 24 | 0.0251 |
| quietdrift90 | a0.3-20 | bayside | 24 | 0.0284 |
| quietdrift90 | a0.3-20 | blocks | 24 | 0.0393 |
| quietdrift90 | a0.3-20 | boulevard | 24 | 0.0248 |
| quietdrift90 | track-12 | bayside | 24 | 0.0292 |
| quietdrift90 | track-12 | blocks | 24 | 0.0416 |
| quietdrift90 | track-12 | boulevard | 24 | 0.0267 |
| quietdrift90 | track-16 | bayside | 24 | 0.028 |
| quietdrift90 | track-16 | blocks | 24 | 0.0389 |
| quietdrift90 | track-16 | boulevard | 24 | 0.0258 |
