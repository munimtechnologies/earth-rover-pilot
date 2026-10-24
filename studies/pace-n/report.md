# How far ahead should the rover aim along its path? (simulated)

pace_n.py 0.1.0 (pace_m.py 0.1.0, rover_pilot.py 0.17.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.17.0's real-rover pilot (pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3) on pace_l.py's outage90 (90 s GPS outages, a steady compass error) or drift90 (the compass error drifts, SD 10 deg, 120 s time constant); only the path follower's lookahead changes: look8 (as shipped), look4, look12 and look16 metres. Seeds 205-228. 576 of 576 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_m.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | look8 | 72/72 | 0.863 | 0.971 | 71 | 1.009 | 0.02 |
| outage90 | look4 | 72/72 | 0.815 | 0.917 | 69 | 1.048 | 0.025 |
| outage90 | look12 | 72/72 | 0.873 | 0.982 | 72 | 1.001 | 0.017 |
| outage90 | look16 | 72/72 | 0.879 | 0.989 | 72 | 0.999 | 0.018 |
| drift90 | look8 | 72/72 | 0.859 | 0.966 | 69 | 1.017 | 0.021 |
| drift90 | look4 | 72/72 | 0.805 | 0.906 | 66 | 1.058 | 0.026 |
| drift90 | look12 | 72/72 | 0.867 | 0.976 | 70 | 1.009 | 0.025 |
| drift90 | look16 | 72/72 | 0.869 | 0.978 | 70 | 1.004 | 0.025 |

## Each lookahead against 8 m, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| drift90 | look4 | look8 | 0/3 | 3 | 0 | 0 | 0.0691 |
| outage90 | look4 | look8 | 0/3 | 3 | 0 | 0 | 0.0673 |
| drift90 | look12 | look8 | 3/3 | 0 | 0 | 0 | -0.0158 |
| outage90 | look12 | look8 | 3/3 | 0 | 0 | 0 | -0.0196 |
| drift90 | look16 | look8 | 3/3 | 0 | 0 | 0 | -0.0388 |
| outage90 | look16 | look8 | 3/3 | 0 | 0 | 0 | -0.0361 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| drift90 | look4 | look8 | bayside | 0 | 21 | 54.0 | 0.0369 | 0.0 |
| drift90 | look4 | look8 | blocks | 0 | 23 | 114.0 | 0.0691 | 0.0 |
| drift90 | look4 | look8 | boulevard | 1 | 22 | 64.0 | 0.0358 | 0.0 |
| outage90 | look4 | look8 | bayside | 1 | 23 | 54.0 | 0.0369 | 0.0 |
| outage90 | look4 | look8 | blocks | 0 | 24 | 110.0 | 0.0673 | 0.0 |
| outage90 | look4 | look8 | boulevard | 0 | 23 | 55.0 | 0.0309 | 0.0 |
| drift90 | look12 | look8 | bayside | 19 | 1 | -8.0 | -0.0055 | 0.0 |
| drift90 | look12 | look8 | blocks | 20 | 2 | -26.0 | -0.0158 | 0.0001 |
| drift90 | look12 | look8 | boulevard | 13 | 4 | -2.0 | -0.0011 | 0.049 |
| outage90 | look12 | look8 | bayside | 23 | 0 | -13.0 | -0.0089 | 0.0 |
| outage90 | look12 | look8 | blocks | 23 | 1 | -32.0 | -0.0196 | 0.0 |
| outage90 | look12 | look8 | boulevard | 17 | 2 | -2.0 | -0.0011 | 0.0007 |
| drift90 | look16 | look8 | bayside | 21 | 1 | -10.0 | -0.0068 | 0.0 |
| drift90 | look16 | look8 | blocks | 23 | 1 | -64.0 | -0.0388 | 0.0 |
| drift90 | look16 | look8 | boulevard | 16 | 5 | -5.0 | -0.0028 | 0.0266 |
| outage90 | look16 | look8 | bayside | 23 | 0 | -18.0 | -0.0123 | 0.0 |
| outage90 | look16 | look8 | blocks | 23 | 1 | -59.0 | -0.0361 | 0.0 |
| outage90 | look16 | look8 | boulevard | 18 | 1 | -6.0 | -0.0034 | 0.0001 |

## What the drift costs each lookahead

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| look8 | drift90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0061 |
| look4 | drift90 | outage90 | 0/3 | 0 | 0 | 0 | 0.0087 |
| look12 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0068 |
| look16 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0062 |

## Near path corners (true distance from the course; past: how far beyond the corner)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| drift90 | look12 | blocks | 24 | 9.0 | 2.03 | 5.07 | 7.56 | 3.16 | 5.46 |
| drift90 | look16 | blocks | 24 | 9.0 | 1.81 | 5.18 | 7.75 | 2.2 | 5.94 |
| drift90 | look4 | blocks | 24 | 9.0 | 2.51 | 7.09 | 10.91 | 5.46 | 8.61 |
| drift90 | look8 | blocks | 24 | 9.0 | 2.17 | 5.68 | 9.03 | 4.25 | 6.54 |
| outage90 | look12 | blocks | 24 | 9.0 | 1.6 | 3.9 | 7.38 | 2.96 | 4.21 |
| outage90 | look16 | blocks | 24 | 9.0 | 1.25 | 3.34 | 6.91 | 1.73 | 3.38 |
| outage90 | look4 | blocks | 24 | 9.0 | 2.28 | 6.19 | 8.96 | 5.67 | 7.37 |
| outage90 | look8 | blocks | 24 | 9.0 | 1.65 | 4.86 | 7.56 | 4.27 | 5.54 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | look12 | bayside | 24 | 1.52 | 7.87 |
| drift90 | look12 | blocks | 24 | 2.41 | 10.48 |
| drift90 | look12 | boulevard | 24 | 2.37 | 8.93 |
| drift90 | look16 | bayside | 24 | 1.83 | 7.82 |
| drift90 | look16 | blocks | 24 | 2.48 | 10.0 |
| drift90 | look16 | boulevard | 24 | 2.54 | 9.79 |
| drift90 | look4 | bayside | 24 | 1.84 | 15.11 |
| drift90 | look4 | blocks | 24 | 2.71 | 16.2 |
| drift90 | look4 | boulevard | 24 | 3.5 | 16.18 |
| drift90 | look8 | bayside | 24 | 1.42 | 7.34 |
| drift90 | look8 | blocks | 24 | 2.26 | 10.66 |
| drift90 | look8 | boulevard | 24 | 2.35 | 11.52 |
| outage90 | look12 | bayside | 24 | 0.61 | 4.7 |
| outage90 | look12 | blocks | 24 | 1.29 | 10.25 |
| outage90 | look12 | boulevard | 24 | 1.85 | 5.57 |
| outage90 | look16 | bayside | 24 | 0.56 | 3.94 |
| outage90 | look16 | blocks | 24 | 1.24 | 8.95 |
| outage90 | look16 | boulevard | 24 | 2.04 | 5.56 |
| outage90 | look4 | bayside | 24 | 1.59 | 15.25 |
| outage90 | look4 | blocks | 24 | 2.4 | 13.35 |
| outage90 | look4 | boulevard | 24 | 2.66 | 12.69 |
| outage90 | look8 | bayside | 24 | 0.72 | 4.27 |
| outage90 | look8 | blocks | 24 | 1.51 | 11.05 |
| outage90 | look8 | boulevard | 24 | 2.17 | 6.16 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| drift90 | look12 | bayside | 24 | 14.32 | 37.36 | 0 | 0 |
| drift90 | look12 | blocks | 24 | 13.62 | 39.08 | 0 | 0 |
| drift90 | look12 | boulevard | 24 | 14.12 | 44.33 | 0 | 0 |
| drift90 | look16 | bayside | 24 | 13.84 | 41.42 | 0 | 0 |
| drift90 | look16 | blocks | 24 | 13.66 | 34.4 | 0 | 0 |
| drift90 | look16 | boulevard | 24 | 14.47 | 43.41 | 0 | 0 |
| drift90 | look4 | bayside | 24 | 28.84 | 73.31 | 0 | 0 |
| drift90 | look4 | blocks | 24 | 30.36 | 50.26 | 0 | 0 |
| drift90 | look4 | boulevard | 24 | 34.02 | 68.57 | 0 | 0 |
| drift90 | look8 | bayside | 24 | 17.99 | 44.06 | 0 | 0 |
| drift90 | look8 | blocks | 24 | 15.88 | 45.96 | 0 | 0 |
| drift90 | look8 | boulevard | 24 | 15.74 | 51.96 | 0 | 0 |
| outage90 | look12 | bayside | 24 | 7.78 | 12.91 | 0 | 0 |
| outage90 | look12 | blocks | 24 | 14.09 | 29.91 | 0 | 0 |
| outage90 | look12 | boulevard | 24 | 7.98 | 26.15 | 0 | 0 |
| outage90 | look16 | bayside | 24 | 7.45 | 14.86 | 0 | 0 |
| outage90 | look16 | blocks | 24 | 12.84 | 25.19 | 0 | 0 |
| outage90 | look16 | boulevard | 24 | 9.09 | 20.34 | 0 | 0 |
| outage90 | look4 | bayside | 24 | 31.23 | 39.33 | 0 | 0 |
| outage90 | look4 | blocks | 24 | 26.39 | 38.29 | 0 | 0 |
| outage90 | look4 | boulevard | 24 | 31.94 | 43.88 | 0 | 0 |
| outage90 | look8 | bayside | 24 | 7.6 | 33.29 | 0 | 0 |
| outage90 | look8 | blocks | 24 | 17.8 | 33.06 | 0 | 0 |
| outage90 | look8 | boulevard | 24 | 9.79 | 35.55 | 0 | 0 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| drift90 | look12 | bayside | 24 | 6.15 | 9.97 |
| drift90 | look12 | blocks | 24 | 6.19 | 9.77 |
| drift90 | look12 | boulevard | 24 | 5.88 | 9.41 |
| drift90 | look16 | bayside | 24 | 6.03 | 9.34 |
| drift90 | look16 | blocks | 24 | 6.17 | 9.83 |
| drift90 | look16 | boulevard | 24 | 5.7 | 8.9 |
| drift90 | look4 | bayside | 24 | 17.77 | 20.84 |
| drift90 | look4 | blocks | 24 | 14.94 | 19.41 |
| drift90 | look4 | boulevard | 24 | 14.18 | 19.34 |
| drift90 | look8 | bayside | 24 | 7.37 | 11.2 |
| drift90 | look8 | blocks | 24 | 7.11 | 10.97 |
| drift90 | look8 | boulevard | 24 | 6.48 | 10.04 |
| outage90 | look12 | bayside | 24 | 1.66 | 4.61 |
| outage90 | look12 | blocks | 24 | 1.73 | 4.61 |
| outage90 | look12 | boulevard | 24 | 1.6 | 4.34 |
| outage90 | look16 | bayside | 24 | 1.55 | 4.59 |
| outage90 | look16 | blocks | 24 | 1.58 | 4.48 |
| outage90 | look16 | boulevard | 24 | 1.62 | 4.2 |
| outage90 | look4 | bayside | 24 | 9.95 | 17.92 |
| outage90 | look4 | blocks | 24 | 9.34 | 16.59 |
| outage90 | look4 | boulevard | 24 | 4.12 | 13.26 |
| outage90 | look8 | bayside | 24 | 1.83 | 5.26 |
| outage90 | look8 | blocks | 24 | 1.79 | 5.53 |
| outage90 | look8 | boulevard | 24 | 1.69 | 4.95 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | look12 | bayside | 24 | 6.53 | 9.84 |
| drift90 | look12 | blocks | 24 | 6.42 | 9.18 |
| drift90 | look12 | boulevard | 24 | 6.56 | 9.93 |
| drift90 | look16 | bayside | 24 | 6.56 | 9.96 |
| drift90 | look16 | blocks | 24 | 6.44 | 9.2 |
| drift90 | look16 | boulevard | 24 | 6.56 | 10.57 |
| drift90 | look4 | bayside | 24 | 6.54 | 14.98 |
| drift90 | look4 | blocks | 24 | 6.25 | 13.91 |
| drift90 | look4 | boulevard | 24 | 6.5 | 12.74 |
| drift90 | look8 | bayside | 24 | 6.49 | 10.55 |
| drift90 | look8 | blocks | 24 | 6.37 | 9.54 |
| drift90 | look8 | boulevard | 24 | 6.52 | 10.44 |
| outage90 | look12 | bayside | 24 | 6.49 | 8.85 |
| outage90 | look12 | blocks | 24 | 6.33 | 8.39 |
| outage90 | look12 | boulevard | 24 | 6.52 | 8.82 |
| outage90 | look16 | bayside | 24 | 6.45 | 8.98 |
| outage90 | look16 | blocks | 24 | 6.34 | 8.55 |
| outage90 | look16 | boulevard | 24 | 6.52 | 8.82 |
| outage90 | look4 | bayside | 24 | 6.44 | 15.12 |
| outage90 | look4 | blocks | 24 | 6.25 | 10.83 |
| outage90 | look4 | boulevard | 24 | 6.45 | 10.3 |
| outage90 | look8 | bayside | 24 | 6.5 | 8.82 |
| outage90 | look8 | blocks | 24 | 6.36 | 8.68 |
| outage90 | look8 | boulevard | 24 | 6.47 | 9.0 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| drift90 | look12 | bayside | 24 | 0.0389 |
| drift90 | look12 | blocks | 24 | 0.0505 |
| drift90 | look12 | boulevard | 24 | 0.0353 |
| drift90 | look16 | bayside | 24 | 0.0352 |
| drift90 | look16 | blocks | 24 | 0.0456 |
| drift90 | look16 | boulevard | 24 | 0.0313 |
| drift90 | look4 | bayside | 24 | 0.0829 |
| drift90 | look4 | blocks | 24 | 0.0945 |
| drift90 | look4 | boulevard | 24 | 0.0767 |
| drift90 | look8 | bayside | 24 | 0.0496 |
| drift90 | look8 | blocks | 24 | 0.0611 |
| drift90 | look8 | boulevard | 24 | 0.0442 |
| outage90 | look12 | bayside | 24 | 0.0358 |
| outage90 | look12 | blocks | 24 | 0.0473 |
| outage90 | look12 | boulevard | 24 | 0.0316 |
| outage90 | look16 | bayside | 24 | 0.0311 |
| outage90 | look16 | blocks | 24 | 0.0432 |
| outage90 | look16 | boulevard | 24 | 0.0274 |
| outage90 | look4 | bayside | 24 | 0.0813 |
| outage90 | look4 | blocks | 24 | 0.0934 |
| outage90 | look4 | boulevard | 24 | 0.0756 |
| outage90 | look8 | bayside | 24 | 0.0462 |
| outage90 | look8 | blocks | 24 | 0.0593 |
| outage90 | look8 | boulevard | 24 | 0.0411 |
