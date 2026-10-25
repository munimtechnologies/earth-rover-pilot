# Should the GPS average start again after a gap? (simulated)

pace_s.py 0.1.0 (pace_q.py 0.1.0, pace_p.py 0.1.0, rover_pilot.py 0.18.4, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_q.py flies it (pace_p.py's keep16: pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3, pace_o.py's keep planner and a 16 m lookahead) with GpsFilter as it ships (a0.3) or the same average started again from the fix after more than 3 s without one (restart). Profiles: outage90 (90 s GPS outages, a steady compass error, 1.5 m of GPS noise per axis), quiet90 (the same with 0.22 m), quietdrift90 (a drifting compass with 0.22 m) and quiet45 (45 s outages with 0.22 m). Seeds 325-348. 576 of 576 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_r.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | 72/72 | 0.879 | 0.989 | 72 | 0.999 | 0.021 |
| outage90 | restart | 72/72 | 0.882 | 0.992 | 72 | 0.997 | 0.021 |
| quiet90 | a0.3 | 72/72 | 0.879 | 0.989 | 72 | 0.999 | 0.02 |
| quiet90 | restart | 72/72 | 0.884 | 0.995 | 72 | 0.998 | 0.019 |
| quietdrift90 | a0.3 | 72/72 | 0.874 | 0.984 | 72 | 1.003 | 0.021 |
| quietdrift90 | restart | 72/72 | 0.877 | 0.986 | 72 | 1.001 | 0.021 |
| quiet45 | a0.3 | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.016 |
| quiet45 | restart | 72/72 | 0.885 | 0.996 | 72 | 0.998 | 0.015 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| outage90 | restart | a0.3 | 2/3 | 1 | 0 | 0 | -0.0051 |
| quiet45 | restart | a0.3 | 2/3 | 0 | 0 | 0 | -0.0057 |
| quiet90 | restart | a0.3 | 2/3 | 0 | 0 | 0 | -0.007 |
| quietdrift90 | restart | a0.3 | 2/3 | 0 | 0 | 0 | -0.005 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| outage90 | restart | a0.3 | bayside | 14 | 1 | -2.0 | -0.0014 | 0.001 |
| outage90 | restart | a0.3 | blocks | 15 | 1 | -8.0 | -0.0051 | 0.0005 |
| outage90 | restart | a0.3 | boulevard | 0 | 6 | 0.0 | 0.0 | 0.0312 |
| quiet45 | restart | a0.3 | bayside | 19 | 0 | -4.0 | -0.0028 | 0.0 |
| quiet45 | restart | a0.3 | blocks | 22 | 0 | -9.0 | -0.0057 | 0.0 |
| quiet45 | restart | a0.3 | boulevard | 4 | 0 | 0.0 | 0.0 | 0.125 |
| quiet90 | restart | a0.3 | bayside | 18 | 0 | -4.0 | -0.0028 | 0.0 |
| quiet90 | restart | a0.3 | blocks | 21 | 0 | -11.0 | -0.007 | 0.0 |
| quiet90 | restart | a0.3 | boulevard | 1 | 0 | 0.0 | 0.0 | 1.0 |
| quietdrift90 | restart | a0.3 | bayside | 20 | 1 | -4.0 | -0.0028 | 0.0 |
| quietdrift90 | restart | a0.3 | blocks | 20 | 0 | -8.0 | -0.005 | 0.0 |
| quietdrift90 | restart | a0.3 | boulevard | 2 | 6 | 0.0 | 0.0 | 0.2891 |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| a0.3 | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | 0.0 |
| a0.3 | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0051 |
| a0.3 | quiet90 | quiet45 | 0/3 | 0 | 0 | 0 | 0.0114 |
| restart | quiet90 | outage90 | 0/3 | 0 | 0 | 0 | -0.0006 |
| restart | quietdrift90 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0064 |
| restart | quiet90 | quiet45 | 0/3 | 0 | 0 | 0 | 0.0077 |

## The pilot's worst idea of where it is, per mission (over 20 m: thrown off)

| profile | variant | course | missions | median of max m | largest m | missions over 20 m |
|---|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 61.73 | 63.65 | 21 |
| outage90 | a0.3 | blocks | 24 | 55.24 | 62.69 | 21 |
| outage90 | a0.3 | boulevard | 24 | 63.47 | 65.94 | 22 |
| outage90 | restart | bayside | 24 | 10.43 | 11.82 | 0 |
| outage90 | restart | blocks | 24 | 10.57 | 11.26 | 0 |
| outage90 | restart | boulevard | 24 | 10.7 | 11.6 | 0 |
| quiet45 | a0.3 | bayside | 24 | 35.55 | 51.88 | 24 |
| quiet45 | a0.3 | blocks | 24 | 35.36 | 44.03 | 24 |
| quiet45 | a0.3 | boulevard | 24 | 36.22 | 52.43 | 24 |
| quiet45 | restart | bayside | 24 | 10.32 | 16.52 | 0 |
| quiet45 | restart | blocks | 24 | 10.29 | 16.02 | 0 |
| quiet45 | restart | boulevard | 24 | 10.41 | 16.55 | 0 |
| quiet90 | a0.3 | bayside | 24 | 61.92 | 64.7 | 21 |
| quiet90 | a0.3 | blocks | 24 | 55.67 | 63.22 | 21 |
| quiet90 | a0.3 | boulevard | 24 | 63.2 | 65.65 | 22 |
| quiet90 | restart | bayside | 24 | 9.9 | 11.47 | 0 |
| quiet90 | restart | blocks | 24 | 10.0 | 10.81 | 0 |
| quiet90 | restart | boulevard | 24 | 10.11 | 10.82 | 0 |
| quietdrift90 | a0.3 | bayside | 24 | 62.05 | 63.74 | 21 |
| quietdrift90 | a0.3 | blocks | 24 | 55.45 | 61.99 | 21 |
| quietdrift90 | a0.3 | boulevard | 24 | 63.0 | 65.41 | 22 |
| quietdrift90 | restart | bayside | 24 | 11.45 | 20.11 | 1 |
| quietdrift90 | restart | blocks | 24 | 12.45 | 24.31 | 1 |
| quietdrift90 | restart | boulevard | 24 | 11.97 | 26.72 | 4 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 6.38 | 8.75 |
| outage90 | a0.3 | blocks | 24 | 6.36 | 8.55 |
| outage90 | a0.3 | boulevard | 24 | 6.52 | 8.75 |
| outage90 | restart | bayside | 24 | 6.26 | 8.07 |
| outage90 | restart | blocks | 24 | 6.29 | 8.09 |
| outage90 | restart | boulevard | 24 | 6.39 | 8.18 |
| quiet45 | a0.3 | bayside | 24 | 6.42 | 9.09 |
| quiet45 | a0.3 | blocks | 24 | 6.31 | 8.95 |
| quiet45 | a0.3 | boulevard | 24 | 6.42 | 9.04 |
| quiet45 | restart | bayside | 24 | 6.29 | 7.81 |
| quiet45 | restart | blocks | 24 | 6.15 | 7.72 |
| quiet45 | restart | boulevard | 24 | 6.28 | 7.83 |
| quiet90 | a0.3 | bayside | 24 | 6.38 | 8.39 |
| quiet90 | a0.3 | blocks | 24 | 6.27 | 8.23 |
| quiet90 | a0.3 | boulevard | 24 | 6.39 | 8.42 |
| quiet90 | restart | bayside | 24 | 6.28 | 7.75 |
| quiet90 | restart | blocks | 24 | 6.16 | 7.67 |
| quiet90 | restart | boulevard | 24 | 6.33 | 7.76 |
| quietdrift90 | a0.3 | bayside | 24 | 6.41 | 8.96 |
| quietdrift90 | a0.3 | blocks | 24 | 6.3 | 8.48 |
| quietdrift90 | a0.3 | boulevard | 24 | 6.43 | 9.14 |
| quietdrift90 | restart | bayside | 24 | 6.33 | 8.04 |
| quietdrift90 | restart | blocks | 24 | 6.21 | 7.93 |
| quietdrift90 | restart | boulevard | 24 | 6.37 | 8.16 |

## Recovery moves and filter restarts

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 0.0 | None |
| outage90 | a0.3 | blocks | 24 | 0.0 | None |
| outage90 | a0.3 | boulevard | 24 | 0.0 | None |
| outage90 | restart | bayside | 24 | 0.0 | 3.5 |
| outage90 | restart | blocks | 24 | 1.0 | 4.5 |
| outage90 | restart | boulevard | 24 | 0.5 | 5.5 |
| quiet45 | a0.3 | bayside | 24 | 1.0 | None |
| quiet45 | a0.3 | blocks | 24 | 1.0 | None |
| quiet45 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet45 | restart | bayside | 24 | 1.0 | 7.0 |
| quiet45 | restart | blocks | 24 | 1.0 | 7.0 |
| quiet45 | restart | boulevard | 24 | 1.0 | 8.0 |
| quiet90 | a0.3 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet90 | restart | bayside | 24 | 1.0 | 3.5 |
| quiet90 | restart | blocks | 24 | 1.0 | 4.5 |
| quiet90 | restart | boulevard | 24 | 1.0 | 5.0 |
| quietdrift90 | a0.3 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3 | boulevard | 24 | 1.0 | None |
| quietdrift90 | restart | bayside | 24 | 1.0 | 3.5 |
| quietdrift90 | restart | blocks | 24 | 1.0 | 4.5 |
| quietdrift90 | restart | boulevard | 24 | 1.0 | 5.5 |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | blocks | 24 | 9.0 | 1.15 | 2.97 | 4.64 | 1.98 | 3.35 |
| outage90 | restart | blocks | 24 | 9.0 | 1.04 | 3.06 | 4.94 | 1.85 | 2.84 |
| quiet45 | a0.3 | blocks | 24 | 9.0 | 0.99 | 3.25 | 4.69 | 2.01 | 3.25 |
| quiet45 | restart | blocks | 24 | 9.0 | 0.86 | 2.81 | 4.63 | 1.92 | 2.66 |
| quiet90 | a0.3 | blocks | 24 | 9.0 | 0.94 | 2.83 | 4.63 | 2.0 | 2.75 |
| quiet90 | restart | blocks | 24 | 9.0 | 0.84 | 2.8 | 4.62 | 1.91 | 2.59 |
| quietdrift90 | a0.3 | blocks | 24 | 9.0 | 1.62 | 4.59 | 6.53 | 1.85 | 4.9 |
| quietdrift90 | restart | blocks | 24 | 9.0 | 1.54 | 4.22 | 5.9 | 1.85 | 4.54 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 0.61 | 4.46 |
| outage90 | a0.3 | blocks | 24 | 0.8 | 3.58 |
| outage90 | a0.3 | boulevard | 24 | 0.61 | 3.7 |
| outage90 | restart | bayside | 24 | 0.57 | 3.83 |
| outage90 | restart | blocks | 24 | 0.77 | 3.14 |
| outage90 | restart | boulevard | 24 | 0.59 | 3.24 |
| quiet45 | a0.3 | bayside | 24 | 0.23 | 2.2 |
| quiet45 | a0.3 | blocks | 24 | 0.33 | 3.38 |
| quiet45 | a0.3 | boulevard | 24 | 0.16 | 0.88 |
| quiet45 | restart | bayside | 24 | 0.22 | 1.54 |
| quiet45 | restart | blocks | 24 | 0.29 | 2.62 |
| quiet45 | restart | boulevard | 24 | 0.15 | 0.81 |
| quiet90 | a0.3 | bayside | 24 | 0.23 | 2.7 |
| quiet90 | a0.3 | blocks | 24 | 0.31 | 3.29 |
| quiet90 | a0.3 | boulevard | 24 | 0.15 | 0.88 |
| quiet90 | restart | bayside | 24 | 0.2 | 1.23 |
| quiet90 | restart | blocks | 24 | 0.27 | 2.51 |
| quiet90 | restart | boulevard | 24 | 0.14 | 0.76 |
| quietdrift90 | a0.3 | bayside | 24 | 1.48 | 7.03 |
| quietdrift90 | a0.3 | blocks | 24 | 1.64 | 5.75 |
| quietdrift90 | a0.3 | boulevard | 24 | 1.58 | 6.93 |
| quietdrift90 | restart | bayside | 24 | 1.4 | 6.22 |
| quietdrift90 | restart | blocks | 24 | 1.58 | 5.43 |
| quietdrift90 | restart | boulevard | 24 | 1.48 | 6.53 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 7.51 | 11.72 | 0 | 0 |
| outage90 | a0.3 | blocks | 24 | 7.59 | 10.0 | 0 | 0 |
| outage90 | a0.3 | boulevard | 24 | 7.12 | 10.33 | 0 | 0 |
| outage90 | restart | bayside | 24 | 7.02 | 10.32 | 0 | 0 |
| outage90 | restart | blocks | 24 | 7.17 | 8.72 | 0 | 0 |
| outage90 | restart | boulevard | 24 | 7.33 | 10.7 | 0 | 0 |
| quiet45 | a0.3 | bayside | 24 | 7.38 | 8.11 | 0 | 0 |
| quiet45 | a0.3 | blocks | 24 | 7.41 | 13.42 | 0 | 0 |
| quiet45 | a0.3 | boulevard | 24 | 7.39 | 17.81 | 0 | 0 |
| quiet45 | restart | bayside | 24 | 7.33 | 16.87 | 0 | 0 |
| quiet45 | restart | blocks | 24 | 7.39 | 13.43 | 0 | 0 |
| quiet45 | restart | boulevard | 24 | 7.39 | 17.59 | 0 | 0 |
| quiet90 | a0.3 | bayside | 24 | 7.33 | 8.11 | 0 | 0 |
| quiet90 | a0.3 | blocks | 24 | 7.46 | 9.64 | 0 | 0 |
| quiet90 | a0.3 | boulevard | 24 | 7.32 | 8.05 | 0 | 0 |
| quiet90 | restart | bayside | 24 | 7.33 | 7.82 | 0 | 0 |
| quiet90 | restart | blocks | 24 | 7.38 | 7.78 | 0 | 0 |
| quiet90 | restart | boulevard | 24 | 7.32 | 7.91 | 0 | 0 |
| quietdrift90 | a0.3 | bayside | 24 | 11.71 | 21.65 | 0 | 0 |
| quietdrift90 | a0.3 | blocks | 24 | 11.32 | 24.59 | 0 | 0 |
| quietdrift90 | a0.3 | boulevard | 24 | 13.21 | 27.15 | 0 | 0 |
| quietdrift90 | restart | bayside | 24 | 10.96 | 21.59 | 0 | 0 |
| quietdrift90 | restart | blocks | 24 | 11.36 | 24.66 | 0 | 0 |
| quietdrift90 | restart | boulevard | 24 | 12.52 | 26.7 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | checkpoint | 24 | 6329 | 44 | 0.299 | 0.49 | 1.48 | 2.2 |
| outage90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | bayside | other | 24 | 26581 | 103 | 0.701 | 0.62 | 4.57 | 7.42 |
| outage90 | a0.3 | bayside | outage | 21 | 4202 | 60 | 0.408 | 2.29 | 5.09 | 5.32 |
| outage90 | a0.3 | bayside | fix | 24 | 28708 | 87 | 0.592 | 0.52 | 3.47 | 7.42 |
| outage90 | a0.3 | blocks | checkpoint | 24 | 8344 | 17 | 0.115 | 0.83 | 3.38 | 5.03 |
| outage90 | a0.3 | blocks | corner | 24 | 8703 | 18 | 0.122 | 1.15 | 2.97 | 4.64 |
| outage90 | a0.3 | blocks | other | 24 | 18747 | 113 | 0.764 | 0.68 | 3.77 | 6.95 |
| outage90 | a0.3 | blocks | outage | 21 | 4096 | 6 | 0.041 | 1.61 | 4.23 | 5.27 |
| outage90 | a0.3 | blocks | fix | 24 | 31698 | 142 | 0.959 | 0.73 | 3.32 | 7.59 |
| outage90 | a0.3 | boulevard | checkpoint | 24 | 6334 | 0 | 0.0 | 0.62 | 1.59 | 2.38 |
| outage90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | boulevard | other | 24 | 33656 | 272 | 1.0 | 0.64 | 3.72 | 7.12 |
| outage90 | a0.3 | boulevard | outage | 23 | 4816 | 77 | 0.283 | 2.04 | 4.15 | 4.31 |
| outage90 | a0.3 | boulevard | fix | 24 | 35174 | 195 | 0.717 | 0.57 | 2.92 | 7.12 |
| outage90 | restart | bayside | checkpoint | 24 | 6328 | 33 | 0.355 | 0.47 | 1.39 | 1.67 |
| outage90 | restart | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart | bayside | other | 24 | 26455 | 60 | 0.645 | 0.59 | 3.77 | 6.88 |
| outage90 | restart | bayside | outage | 21 | 4165 | 71 | 0.763 | 2.27 | 5.09 | 5.28 |
| outage90 | restart | bayside | fix | 24 | 28618 | 22 | 0.237 | 0.51 | 2.17 | 6.89 |
| outage90 | restart | blocks | checkpoint | 24 | 8208 | 0 | 0.0 | 0.79 | 2.64 | 3.41 |
| outage90 | restart | blocks | corner | 24 | 8614 | 3 | 0.027 | 1.04 | 3.06 | 4.94 |
| outage90 | restart | blocks | other | 24 | 18649 | 108 | 0.973 | 0.68 | 4.03 | 6.79 |
| outage90 | restart | blocks | outage | 21 | 4092 | 3 | 0.027 | 1.71 | 3.95 | 5.37 |
| outage90 | restart | blocks | fix | 24 | 31379 | 108 | 0.973 | 0.71 | 2.79 | 6.86 |
| outage90 | restart | boulevard | checkpoint | 24 | 6329 | 0 | 0.0 | 0.55 | 1.43 | 1.8 |
| outage90 | restart | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart | boulevard | other | 24 | 33686 | 276 | 1.0 | 0.6 | 3.41 | 7.33 |
| outage90 | restart | boulevard | outage | 23 | 4835 | 93 | 0.337 | 1.94 | 3.68 | 3.83 |
| outage90 | restart | boulevard | fix | 24 | 35180 | 183 | 0.663 | 0.52 | 2.21 | 7.33 |
| quiet45 | a0.3 | bayside | checkpoint | 24 | 6307 | 0 | 0.0 | 0.2 | 0.86 | 1.63 |
| quiet45 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet45 | a0.3 | bayside | other | 24 | 26568 | 7 | 1.0 | 0.23 | 2.52 | 7.38 |
| quiet45 | a0.3 | bayside | outage | 24 | 4193 | 0 | 0.0 | 0.45 | 1.71 | 2.19 |
| quiet45 | a0.3 | bayside | fix | 24 | 28682 | 7 | 1.0 | 0.22 | 2.37 | 7.38 |
| quiet45 | a0.3 | blocks | checkpoint | 24 | 8287 | 0 | 0.0 | 0.45 | 2.98 | 4.58 |
| quiet45 | a0.3 | blocks | corner | 24 | 8678 | 9 | 0.29 | 0.99 | 3.25 | 4.69 |
| quiet45 | a0.3 | blocks | other | 24 | 18706 | 22 | 0.71 | 0.24 | 3.56 | 7.39 |
| quiet45 | a0.3 | blocks | outage | 24 | 4393 | 28 | 0.903 | 0.55 | 3.51 | 4.73 |
| quiet45 | a0.3 | blocks | fix | 24 | 31278 | 3 | 0.097 | 0.3 | 3.17 | 7.41 |
| quiet45 | a0.3 | boulevard | checkpoint | 24 | 6295 | 0 | 0.0 | 0.21 | 0.67 | 1.01 |
| quiet45 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet45 | a0.3 | boulevard | other | 24 | 33631 | 71 | 1.0 | 0.16 | 0.96 | 7.39 |
| quiet45 | a0.3 | boulevard | outage | 24 | 4999 | 30 | 0.423 | 0.26 | 0.86 | 1.13 |
| quiet45 | a0.3 | boulevard | fix | 24 | 34927 | 41 | 0.577 | 0.15 | 0.96 | 7.39 |
| quiet45 | restart | bayside | checkpoint | 24 | 6298 | 0 | 0.0 | 0.19 | 0.69 | 1.22 |
| quiet45 | restart | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet45 | restart | bayside | other | 24 | 26482 | 42 | 1.0 | 0.23 | 1.85 | 7.33 |
| quiet45 | restart | bayside | outage | 24 | 4233 | 27 | 0.643 | 0.51 | 1.56 | 2.06 |
| quiet45 | restart | bayside | fix | 24 | 28547 | 15 | 0.357 | 0.2 | 1.42 | 7.33 |
| quiet45 | restart | blocks | checkpoint | 24 | 8160 | 0 | 0.0 | 0.33 | 2.05 | 2.51 |
| quiet45 | restart | blocks | corner | 24 | 8523 | 10 | 0.357 | 0.86 | 2.81 | 4.63 |
| quiet45 | restart | blocks | other | 24 | 18663 | 18 | 0.643 | 0.22 | 3.46 | 7.39 |
| quiet45 | restart | blocks | outage | 24 | 4433 | 28 | 1.0 | 0.53 | 3.35 | 4.63 |
| quiet45 | restart | blocks | fix | 24 | 30913 | 0 | 0.0 | 0.27 | 2.45 | 7.39 |
| quiet45 | restart | boulevard | checkpoint | 24 | 6290 | 0 | 0.0 | 0.19 | 0.58 | 0.89 |
| quiet45 | restart | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet45 | restart | boulevard | other | 24 | 33631 | 47 | 1.0 | 0.14 | 0.91 | 7.39 |
| quiet45 | restart | boulevard | outage | 24 | 5002 | 31 | 0.66 | 0.23 | 0.79 | 1.12 |
| quiet45 | restart | boulevard | fix | 24 | 34919 | 16 | 0.34 | 0.14 | 0.72 | 7.39 |
| quiet90 | a0.3 | bayside | checkpoint | 24 | 6313 | 0 | 0.0 | 0.18 | 0.61 | 1.25 |
| quiet90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3 | bayside | other | 24 | 26561 | 7 | 1.0 | 0.23 | 3.42 | 7.33 |
| quiet90 | a0.3 | bayside | outage | 21 | 4137 | 0 | 0.0 | 0.55 | 1.54 | 1.94 |
| quiet90 | a0.3 | bayside | fix | 24 | 28737 | 7 | 1.0 | 0.2 | 3.14 | 7.33 |
| quiet90 | a0.3 | blocks | checkpoint | 24 | 8331 | 21 | 0.6 | 0.39 | 2.77 | 3.96 |
| quiet90 | a0.3 | blocks | corner | 24 | 8660 | 11 | 0.314 | 0.94 | 2.83 | 4.63 |
| quiet90 | a0.3 | blocks | other | 24 | 18799 | 3 | 0.086 | 0.23 | 3.54 | 7.38 |
| quiet90 | a0.3 | blocks | outage | 21 | 4195 | 0 | 0.0 | 0.61 | 3.23 | 4.61 |
| quiet90 | a0.3 | blocks | fix | 24 | 31595 | 35 | 1.0 | 0.27 | 3.37 | 7.46 |
| quiet90 | a0.3 | boulevard | checkpoint | 24 | 6315 | 0 | 0.0 | 0.18 | 0.6 | 1.05 |
| quiet90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3 | boulevard | other | 24 | 33652 | 4 | 1.0 | 0.15 | 0.77 | 7.32 |
| quiet90 | a0.3 | boulevard | outage | 23 | 4941 | 0 | 0.0 | 0.3 | 0.77 | 0.85 |
| quiet90 | a0.3 | boulevard | fix | 24 | 35026 | 4 | 1.0 | 0.14 | 0.93 | 7.32 |
| quiet90 | restart | bayside | checkpoint | 24 | 6316 | 0 | None | 0.16 | 0.46 | 0.69 |
| quiet90 | restart | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart | bayside | other | 24 | 26446 | 0 | None | 0.21 | 1.48 | 7.33 |
| quiet90 | restart | bayside | outage | 21 | 4113 | 0 | None | 0.55 | 1.58 | 1.95 |
| quiet90 | restart | bayside | fix | 24 | 28649 | 0 | None | 0.19 | 0.94 | 7.33 |
| quiet90 | restart | blocks | checkpoint | 24 | 8197 | 0 | None | 0.29 | 2.13 | 2.55 |
| quiet90 | restart | blocks | corner | 24 | 8574 | 0 | None | 0.84 | 2.8 | 4.62 |
| quiet90 | restart | blocks | other | 24 | 18647 | 0 | None | 0.22 | 3.46 | 7.38 |
| quiet90 | restart | blocks | outage | 21 | 4203 | 0 | None | 0.7 | 3.19 | 4.75 |
| quiet90 | restart | blocks | fix | 24 | 31215 | 0 | None | 0.25 | 2.43 | 7.38 |
| quiet90 | restart | boulevard | checkpoint | 24 | 6307 | 0 | None | 0.17 | 0.56 | 0.99 |
| quiet90 | restart | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart | boulevard | other | 24 | 33655 | 0 | None | 0.13 | 0.78 | 7.32 |
| quiet90 | restart | boulevard | outage | 23 | 4940 | 0 | None | 0.35 | 0.77 | 0.85 |
| quiet90 | restart | boulevard | fix | 24 | 35022 | 0 | None | 0.13 | 0.64 | 7.32 |
| quietdrift90 | a0.3 | bayside | checkpoint | 24 | 6358 | 124 | 0.116 | 1.25 | 3.66 | 4.36 |
| quietdrift90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | bayside | other | 24 | 26690 | 949 | 0.884 | 1.48 | 6.88 | 11.23 |
| quietdrift90 | a0.3 | bayside | outage | 21 | 4176 | 596 | 0.555 | 2.91 | 10.23 | 11.39 |
| quietdrift90 | a0.3 | bayside | fix | 24 | 28872 | 477 | 0.445 | 1.35 | 5.16 | 11.61 |
| quietdrift90 | a0.3 | blocks | checkpoint | 24 | 8403 | 110 | 0.108 | 1.61 | 4.96 | 6.32 |
| quietdrift90 | a0.3 | blocks | corner | 24 | 8606 | 57 | 0.056 | 1.62 | 4.59 | 6.53 |
| quietdrift90 | a0.3 | blocks | other | 24 | 19076 | 855 | 0.837 | 1.7 | 6.29 | 11.32 |
| quietdrift90 | a0.3 | blocks | outage | 21 | 4206 | 442 | 0.432 | 2.5 | 9.26 | 10.6 |
| quietdrift90 | a0.3 | blocks | fix | 24 | 31879 | 580 | 0.568 | 1.54 | 5.17 | 10.85 |
| quietdrift90 | a0.3 | boulevard | checkpoint | 24 | 6345 | 89 | 0.051 | 1.19 | 4.21 | 4.65 |
| quietdrift90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | boulevard | other | 24 | 33886 | 1665 | 0.949 | 1.61 | 7.32 | 13.21 |
| quietdrift90 | a0.3 | boulevard | outage | 23 | 4961 | 867 | 0.494 | 3.6 | 11.23 | 13.24 |
| quietdrift90 | a0.3 | boulevard | fix | 24 | 35270 | 887 | 0.506 | 1.4 | 5.25 | 13.21 |
| quietdrift90 | restart | bayside | checkpoint | 24 | 6355 | 95 | 0.093 | 1.34 | 3.47 | 4.35 |
| quietdrift90 | restart | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart | bayside | other | 24 | 26578 | 925 | 0.907 | 1.4 | 6.87 | 10.96 |
| quietdrift90 | restart | bayside | outage | 21 | 4156 | 638 | 0.625 | 2.91 | 10.54 | 11.83 |
| quietdrift90 | restart | bayside | fix | 24 | 28777 | 382 | 0.375 | 1.31 | 4.61 | 10.84 |
| quietdrift90 | restart | blocks | checkpoint | 24 | 8267 | 68 | 0.077 | 1.46 | 4.32 | 4.92 |
| quietdrift90 | restart | blocks | corner | 24 | 8539 | 23 | 0.026 | 1.54 | 4.22 | 5.9 |
| quietdrift90 | restart | blocks | other | 24 | 18871 | 792 | 0.897 | 1.57 | 6.84 | 11.36 |
| quietdrift90 | restart | blocks | outage | 21 | 4130 | 467 | 0.529 | 2.74 | 10.28 | 11.7 |
| quietdrift90 | restart | blocks | fix | 24 | 31547 | 416 | 0.471 | 1.53 | 4.61 | 10.88 |
| quietdrift90 | restart | boulevard | checkpoint | 24 | 6337 | 47 | 0.033 | 1.21 | 4.13 | 4.38 |
| quietdrift90 | restart | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart | boulevard | other | 24 | 33909 | 1368 | 0.967 | 1.47 | 7.0 | 12.52 |
| quietdrift90 | restart | boulevard | outage | 23 | 4975 | 844 | 0.596 | 3.3 | 10.86 | 12.21 |
| quietdrift90 | restart | boulevard | fix | 24 | 35271 | 571 | 0.404 | 1.33 | 4.4 | 12.52 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 1.54 | 4.47 |
| outage90 | a0.3 | blocks | 24 | 1.65 | 4.39 |
| outage90 | a0.3 | boulevard | 24 | 1.51 | 4.03 |
| outage90 | restart | bayside | 24 | 1.52 | 4.36 |
| outage90 | restart | blocks | 24 | 1.63 | 4.33 |
| outage90 | restart | boulevard | 24 | 1.51 | 4.01 |
| quiet45 | a0.3 | bayside | 24 | 1.0 | 4.28 |
| quiet45 | a0.3 | blocks | 24 | 1.02 | 4.17 |
| quiet45 | a0.3 | boulevard | 24 | 0.96 | 3.89 |
| quiet45 | restart | bayside | 24 | 1.02 | 4.29 |
| quiet45 | restart | blocks | 24 | 1.02 | 4.17 |
| quiet45 | restart | boulevard | 24 | 0.96 | 3.89 |
| quiet90 | a0.3 | bayside | 24 | 1.0 | 4.28 |
| quiet90 | a0.3 | blocks | 24 | 1.02 | 4.16 |
| quiet90 | a0.3 | boulevard | 24 | 0.96 | 3.88 |
| quiet90 | restart | bayside | 24 | 0.99 | 4.28 |
| quiet90 | restart | blocks | 24 | 1.02 | 4.14 |
| quiet90 | restart | boulevard | 24 | 0.96 | 3.88 |
| quietdrift90 | a0.3 | bayside | 24 | 5.24 | 8.63 |
| quietdrift90 | a0.3 | blocks | 24 | 5.41 | 9.04 |
| quietdrift90 | a0.3 | boulevard | 24 | 5.1 | 8.27 |
| quietdrift90 | restart | bayside | 24 | 5.13 | 8.53 |
| quietdrift90 | restart | blocks | 24 | 5.62 | 8.9 |
| quietdrift90 | restart | boulevard | 24 | 5.06 | 8.27 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| outage90 | a0.3 | bayside | 24 | 0.0311 |
| outage90 | a0.3 | blocks | 24 | 0.0415 |
| outage90 | a0.3 | boulevard | 24 | 0.0268 |
| outage90 | restart | bayside | 24 | 0.0293 |
| outage90 | restart | blocks | 24 | 0.04 |
| outage90 | restart | boulevard | 24 | 0.0272 |
| quiet45 | a0.3 | bayside | 24 | 0.0252 |
| quiet45 | a0.3 | blocks | 24 | 0.0363 |
| quiet45 | a0.3 | boulevard | 24 | 0.0202 |
| quiet45 | restart | bayside | 24 | 0.023 |
| quiet45 | restart | blocks | 24 | 0.0341 |
| quiet45 | restart | boulevard | 24 | 0.0203 |
| quiet90 | a0.3 | bayside | 24 | 0.0253 |
| quiet90 | a0.3 | blocks | 24 | 0.0366 |
| quiet90 | a0.3 | boulevard | 24 | 0.02 |
| quiet90 | restart | bayside | 24 | 0.0228 |
| quiet90 | restart | blocks | 24 | 0.034 |
| quiet90 | restart | boulevard | 24 | 0.0201 |
| quietdrift90 | a0.3 | bayside | 24 | 0.0301 |
| quietdrift90 | a0.3 | blocks | 24 | 0.0412 |
| quietdrift90 | a0.3 | boulevard | 24 | 0.0255 |
| quietdrift90 | restart | bayside | 24 | 0.0277 |
| quietdrift90 | restart | blocks | 24 | 0.0387 |
| quietdrift90 | restart | boulevard | 24 | 0.026 |
