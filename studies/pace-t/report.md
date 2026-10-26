# Should the stuck detector wait before it judges? (simulated)

pace_t.py 0.1.0 (pace_s.py 0.1.0, pace_q.py 0.1.0, pace_p.py 0.1.0, rover_pilot.py 0.18.5, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_s.py flies it, with Pilot._stuck as it ships (a0.3), with no stuck verdict until 10 s after the stuck history was last cleared (warm), or with that and the GPS average started again from the fix after more than 3 s without one (restart+warm). Profiles: outage90 (90 s GPS outages, 1.5 m of GPS noise per axis), quiet90, quietdrift90 and quiet45 (the same idea with 0.22 m), and blocked30 (quiet90 with a rover that cannot move for its first 30 s). Seeds 349-372. 1080 of 1080 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_s.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | 72/72 | 0.879 | 0.989 | 72 | 0.999 | 0.019 |
| outage90 | warm | 72/72 | 0.879 | 0.989 | 72 | 0.998 | 0.019 |
| outage90 | restart+warm | 72/72 | 0.885 | 0.996 | 72 | 0.997 | 0.018 |
| quiet90 | a0.3 | 72/72 | 0.877 | 0.987 | 72 | 0.999 | 0.021 |
| quiet90 | warm | 72/72 | 0.881 | 0.991 | 72 | 0.997 | 0.02 |
| quiet90 | restart+warm | 72/72 | 0.888 | 0.999 | 72 | 0.996 | 0.017 |
| quietdrift90 | a0.3 | 72/72 | 0.866 | 0.974 | 72 | 1.005 | 0.021 |
| quietdrift90 | warm | 72/72 | 0.871 | 0.98 | 72 | 1.003 | 0.02 |
| quietdrift90 | restart+warm | 72/72 | 0.876 | 0.985 | 72 | 1.001 | 0.02 |
| quiet45 | a0.3 | 72/72 | 0.882 | 0.993 | 72 | 0.999 | 0.012 |
| quiet45 | warm | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.013 |
| quiet45 | restart+warm | 72/72 | 0.889 | 1.0 | 72 | 0.995 | 0.012 |
| blocked30 | a0.3 | 72/72 | 0.862 | 0.97 | 72 | 0.997 | 0.021 |
| blocked30 | warm | 72/72 | 0.865 | 0.973 | 72 | 0.997 | 0.021 |
| blocked30 | restart+warm | 72/72 | 0.868 | 0.977 | 72 | 0.996 | 0.021 |

## Recovery moves (first before 30 s: at the start)

| profile | variant | course | missions | with a recovery | recoveries | first before 30 s | median first s | latest first s |
|---|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 23 | 48 | 23 | 9.1 | 11.1 |
| blocked30 | a0.3 | blocks | 24 | 23 | 48 | 23 | 9.1 | 11.1 |
| blocked30 | a0.3 | boulevard | 24 | 23 | 48 | 23 | 9.1 | 11.1 |
| blocked30 | restart+warm | bayside | 24 | 22 | 22 | 22 | 19.1 | 21.1 |
| blocked30 | restart+warm | blocks | 24 | 22 | 22 | 22 | 19.1 | 21.1 |
| blocked30 | restart+warm | boulevard | 24 | 22 | 22 | 22 | 19.1 | 21.1 |
| blocked30 | warm | bayside | 24 | 22 | 22 | 22 | 19.1 | 21.1 |
| blocked30 | warm | blocks | 24 | 22 | 22 | 22 | 19.1 | 21.1 |
| blocked30 | warm | boulevard | 24 | 22 | 22 | 22 | 19.1 | 21.1 |
| outage90 | a0.3 | bayside | 24 | 8 | 8 | 8 | 9.1 | 11.1 |
| outage90 | a0.3 | blocks | 24 | 9 | 9 | 9 | 9.1 | 11.1 |
| outage90 | a0.3 | boulevard | 24 | 9 | 9 | 9 | 9.1 | 11.1 |
| outage90 | restart+warm | bayside | 24 | 0 | 0 | 0 | None | None |
| outage90 | restart+warm | blocks | 24 | 0 | 0 | 0 | None | None |
| outage90 | restart+warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| outage90 | warm | bayside | 24 | 0 | 0 | 0 | None | None |
| outage90 | warm | blocks | 24 | 0 | 0 | 0 | None | None |
| outage90 | warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| quiet45 | a0.3 | bayside | 24 | 22 | 22 | 22 | 9.1 | 11.1 |
| quiet45 | a0.3 | blocks | 24 | 22 | 22 | 22 | 9.1 | 11.1 |
| quiet45 | a0.3 | boulevard | 24 | 22 | 22 | 22 | 9.1 | 11.1 |
| quiet45 | restart+warm | bayside | 24 | 0 | 0 | 0 | None | None |
| quiet45 | restart+warm | blocks | 24 | 0 | 0 | 0 | None | None |
| quiet45 | restart+warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| quiet45 | warm | bayside | 24 | 0 | 0 | 0 | None | None |
| quiet45 | warm | blocks | 24 | 0 | 0 | 0 | None | None |
| quiet45 | warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| quiet90 | a0.3 | bayside | 24 | 23 | 23 | 23 | 9.1 | 11.1 |
| quiet90 | a0.3 | blocks | 24 | 23 | 23 | 23 | 9.1 | 11.1 |
| quiet90 | a0.3 | boulevard | 24 | 23 | 23 | 23 | 9.1 | 11.1 |
| quiet90 | restart+warm | bayside | 24 | 0 | 0 | 0 | None | None |
| quiet90 | restart+warm | blocks | 24 | 0 | 0 | 0 | None | None |
| quiet90 | restart+warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| quiet90 | warm | bayside | 24 | 0 | 0 | 0 | None | None |
| quiet90 | warm | blocks | 24 | 0 | 0 | 0 | None | None |
| quiet90 | warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| quietdrift90 | a0.3 | bayside | 24 | 22 | 22 | 22 | 9.1 | 11.1 |
| quietdrift90 | a0.3 | blocks | 24 | 24 | 27 | 23 | 9.1 | 805.9 |
| quietdrift90 | a0.3 | boulevard | 24 | 23 | 23 | 23 | 9.1 | 11.1 |
| quietdrift90 | restart+warm | bayside | 24 | 0 | 0 | 0 | None | None |
| quietdrift90 | restart+warm | blocks | 24 | 2 | 2 | 0 | 1107.0 | 1420.0 |
| quietdrift90 | restart+warm | boulevard | 24 | 0 | 0 | 0 | None | None |
| quietdrift90 | warm | bayside | 24 | 0 | 0 | 0 | None | None |
| quietdrift90 | warm | blocks | 24 | 3 | 3 | 0 | 1434.0 | 1470.0 |
| quietdrift90 | warm | boulevard | 24 | 0 | 0 | 0 | None | None |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| blocked30 | warm | a0.3 | 2/3 | 0 | 0 | 0 | 0.0 |
| outage90 | warm | a0.3 | 1/3 | 0 | 0 | 0 | 0.0 |
| quiet45 | warm | a0.3 | 3/3 | 0 | 0 | 0 | -0.0035 |
| quiet90 | warm | a0.3 | 3/3 | 0 | 0 | 0 | -0.0042 |
| quietdrift90 | warm | a0.3 | 3/3 | 0 | 0 | 0 | -0.0034 |
| blocked30 | restart+warm | warm | 2/3 | 0 | 0 | 0 | -0.0049 |
| outage90 | restart+warm | warm | 2/3 | 0 | 0 | 0 | -0.0031 |
| quiet45 | restart+warm | warm | 2/3 | 0 | 0 | 0 | -0.0051 |
| quiet90 | restart+warm | warm | 2/3 | 0 | 0 | 0 | -0.005 |
| quietdrift90 | restart+warm | warm | 2/3 | 0 | 0 | 0 | -0.0056 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| blocked30 | warm | a0.3 | bayside | 11 | 1 | 0.0 | 0.0 | 0.0063 |
| blocked30 | warm | a0.3 | blocks | 5 | 0 | 0.0 | 0.0 | 0.0625 |
| blocked30 | warm | a0.3 | boulevard | 6 | 0 | 0.0 | 0.0 | 0.0312 |
| outage90 | warm | a0.3 | bayside | 6 | 0 | 0.0 | 0.0 | 0.0312 |
| outage90 | warm | a0.3 | blocks | 4 | 0 | 0.0 | 0.0 | 0.125 |
| outage90 | warm | a0.3 | boulevard | 5 | 0 | 0.0 | 0.0 | 0.0625 |
| quiet45 | warm | a0.3 | bayside | 13 | 0 | -5.0 | -0.0035 | 0.0002 |
| quiet45 | warm | a0.3 | blocks | 10 | 0 | 0.0 | 0.0 | 0.002 |
| quiet45 | warm | a0.3 | boulevard | 15 | 0 | -4.0 | -0.0023 | 0.0001 |
| quiet90 | warm | a0.3 | bayside | 14 | 0 | -6.0 | -0.0042 | 0.0001 |
| quiet90 | warm | a0.3 | blocks | 10 | 0 | 0.0 | 0.0 | 0.002 |
| quiet90 | warm | a0.3 | boulevard | 14 | 0 | -6.0 | -0.0034 | 0.0001 |
| quietdrift90 | warm | a0.3 | bayside | 15 | 0 | -5.0 | -0.0034 | 0.0001 |
| quietdrift90 | warm | a0.3 | blocks | 11 | 0 | 0.0 | 0.0 | 0.001 |
| quietdrift90 | warm | a0.3 | boulevard | 13 | 2 | -5.0 | -0.0028 | 0.0074 |
| blocked30 | restart+warm | warm | bayside | 14 | 0 | -2.0 | -0.0014 | 0.0001 |
| blocked30 | restart+warm | warm | blocks | 16 | 0 | -8.0 | -0.0049 | 0.0 |
| blocked30 | restart+warm | warm | boulevard | 3 | 0 | 0.0 | 0.0 | 0.25 |
| outage90 | restart+warm | warm | bayside | 9 | 1 | 0.0 | 0.0 | 0.0215 |
| outage90 | restart+warm | warm | blocks | 17 | 1 | -5.0 | -0.0031 | 0.0001 |
| outage90 | restart+warm | warm | boulevard | 0 | 2 | 0.0 | 0.0 | 0.5 |
| quiet45 | restart+warm | warm | bayside | 18 | 0 | -2.0 | -0.0014 | 0.0 |
| quiet45 | restart+warm | warm | blocks | 21 | 0 | -8.0 | -0.0051 | 0.0 |
| quiet45 | restart+warm | warm | boulevard | 3 | 0 | 0.0 | 0.0 | 0.25 |
| quiet90 | restart+warm | warm | bayside | 14 | 0 | -2.0 | -0.0014 | 0.0001 |
| quiet90 | restart+warm | warm | blocks | 18 | 0 | -8.0 | -0.005 | 0.0 |
| quiet90 | restart+warm | warm | boulevard | 1 | 0 | 0.0 | 0.0 | 1.0 |
| quietdrift90 | restart+warm | warm | bayside | 14 | 2 | -2.0 | -0.0014 | 0.0042 |
| quietdrift90 | restart+warm | warm | blocks | 18 | 0 | -9.0 | -0.0056 | 0.0 |
| quietdrift90 | restart+warm | warm | boulevard | 4 | 7 | 0.0 | 0.0 | 0.5488 |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| a0.3 | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0139 |
| warm | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0154 |
| restart+warm | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0182 |

## The pilot's worst idea of where it is, per mission (over 20 m: thrown off)

| profile | variant | course | missions | median of max m | largest m | missions over 20 m |
|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 61.41 | 64.26 | 19 |
| blocked30 | a0.3 | blocks | 24 | 56.97 | 62.97 | 20 |
| blocked30 | a0.3 | boulevard | 24 | 63.16 | 65.03 | 22 |
| blocked30 | restart+warm | bayside | 24 | 10.16 | 11.25 | 0 |
| blocked30 | restart+warm | blocks | 24 | 10.21 | 11.17 | 0 |
| blocked30 | restart+warm | boulevard | 24 | 10.25 | 11.27 | 0 |
| blocked30 | warm | bayside | 24 | 61.47 | 64.29 | 19 |
| blocked30 | warm | blocks | 24 | 56.52 | 62.96 | 20 |
| blocked30 | warm | boulevard | 24 | 63.14 | 65.03 | 22 |
| outage90 | a0.3 | bayside | 24 | 61.12 | 65.05 | 18 |
| outage90 | a0.3 | blocks | 24 | 55.84 | 63.64 | 19 |
| outage90 | a0.3 | boulevard | 24 | 63.14 | 65.8 | 22 |
| outage90 | restart+warm | bayside | 24 | 10.4 | 11.58 | 0 |
| outage90 | restart+warm | blocks | 24 | 10.53 | 11.57 | 0 |
| outage90 | restart+warm | boulevard | 24 | 10.82 | 11.6 | 0 |
| outage90 | warm | bayside | 24 | 61.13 | 65.05 | 19 |
| outage90 | warm | blocks | 24 | 54.87 | 63.64 | 19 |
| outage90 | warm | boulevard | 24 | 63.35 | 65.8 | 22 |
| quiet45 | a0.3 | bayside | 24 | 35.55 | 53.1 | 23 |
| quiet45 | a0.3 | blocks | 24 | 35.58 | 56.38 | 24 |
| quiet45 | a0.3 | boulevard | 24 | 36.01 | 64.11 | 24 |
| quiet45 | restart+warm | bayside | 24 | 9.91 | 11.29 | 0 |
| quiet45 | restart+warm | blocks | 24 | 10.24 | 11.31 | 0 |
| quiet45 | restart+warm | boulevard | 24 | 10.44 | 11.56 | 0 |
| quiet45 | warm | bayside | 24 | 35.45 | 53.09 | 24 |
| quiet45 | warm | blocks | 24 | 35.56 | 57.4 | 24 |
| quiet45 | warm | boulevard | 24 | 36.3 | 63.66 | 24 |
| quiet90 | a0.3 | bayside | 24 | 61.55 | 64.26 | 18 |
| quiet90 | a0.3 | blocks | 24 | 56.24 | 61.73 | 19 |
| quiet90 | a0.3 | boulevard | 24 | 63.11 | 65.04 | 22 |
| quiet90 | restart+warm | bayside | 24 | 9.96 | 11.07 | 0 |
| quiet90 | restart+warm | blocks | 24 | 10.14 | 11.31 | 0 |
| quiet90 | restart+warm | boulevard | 24 | 10.15 | 11.27 | 0 |
| quiet90 | warm | bayside | 24 | 61.38 | 64.25 | 19 |
| quiet90 | warm | blocks | 24 | 54.66 | 62.32 | 18 |
| quiet90 | warm | boulevard | 24 | 63.21 | 65.03 | 22 |
| quietdrift90 | a0.3 | bayside | 24 | 61.13 | 64.06 | 18 |
| quietdrift90 | a0.3 | blocks | 24 | 56.73 | 63.19 | 20 |
| quietdrift90 | a0.3 | boulevard | 24 | 62.66 | 64.65 | 22 |
| quietdrift90 | restart+warm | bayside | 24 | 10.43 | 29.67 | 4 |
| quietdrift90 | restart+warm | blocks | 24 | 11.18 | 22.84 | 3 |
| quietdrift90 | restart+warm | boulevard | 24 | 12.13 | 22.65 | 2 |
| quietdrift90 | warm | bayside | 24 | 61.56 | 63.55 | 19 |
| quietdrift90 | warm | blocks | 24 | 56.14 | 63.76 | 19 |
| quietdrift90 | warm | boulevard | 24 | 62.8 | 64.64 | 22 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 6.56 | 8.5 |
| blocked30 | a0.3 | blocks | 24 | 6.45 | 8.32 |
| blocked30 | a0.3 | boulevard | 24 | 6.58 | 8.57 |
| blocked30 | restart+warm | bayside | 24 | 6.38 | 7.87 |
| blocked30 | restart+warm | blocks | 24 | 6.31 | 7.8 |
| blocked30 | restart+warm | boulevard | 24 | 6.45 | 7.92 |
| blocked30 | warm | bayside | 24 | 6.54 | 8.45 |
| blocked30 | warm | blocks | 24 | 6.4 | 8.29 |
| blocked30 | warm | boulevard | 24 | 6.56 | 8.57 |
| outage90 | a0.3 | bayside | 24 | 6.5 | 8.62 |
| outage90 | a0.3 | blocks | 24 | 6.52 | 8.46 |
| outage90 | a0.3 | boulevard | 24 | 6.56 | 8.75 |
| outage90 | restart+warm | bayside | 24 | 6.41 | 8.2 |
| outage90 | restart+warm | blocks | 24 | 6.42 | 8.18 |
| outage90 | restart+warm | boulevard | 24 | 6.49 | 8.27 |
| outage90 | warm | bayside | 24 | 6.5 | 8.62 |
| outage90 | warm | blocks | 24 | 6.5 | 8.46 |
| outage90 | warm | boulevard | 24 | 6.58 | 8.77 |
| quiet45 | a0.3 | bayside | 24 | 6.39 | 9.07 |
| quiet45 | a0.3 | blocks | 24 | 6.29 | 8.89 |
| quiet45 | a0.3 | boulevard | 24 | 6.41 | 9.12 |
| quiet45 | restart+warm | bayside | 24 | 6.25 | 7.81 |
| quiet45 | restart+warm | blocks | 24 | 6.21 | 7.81 |
| quiet45 | restart+warm | boulevard | 24 | 6.31 | 7.96 |
| quiet45 | warm | bayside | 24 | 6.45 | 9.09 |
| quiet45 | warm | blocks | 24 | 6.4 | 8.98 |
| quiet45 | warm | boulevard | 24 | 6.54 | 9.23 |
| quiet90 | a0.3 | bayside | 24 | 6.42 | 8.34 |
| quiet90 | a0.3 | blocks | 24 | 6.29 | 8.15 |
| quiet90 | a0.3 | boulevard | 24 | 6.42 | 8.39 |
| quiet90 | restart+warm | bayside | 24 | 6.41 | 7.8 |
| quiet90 | restart+warm | blocks | 24 | 6.32 | 7.81 |
| quiet90 | restart+warm | boulevard | 24 | 6.47 | 7.95 |
| quiet90 | warm | bayside | 24 | 6.46 | 8.37 |
| quiet90 | warm | blocks | 24 | 6.4 | 8.29 |
| quiet90 | warm | boulevard | 24 | 6.57 | 8.59 |
| quietdrift90 | a0.3 | bayside | 24 | 6.47 | 8.5 |
| quietdrift90 | a0.3 | blocks | 24 | 6.36 | 8.36 |
| quietdrift90 | a0.3 | boulevard | 24 | 6.44 | 8.61 |
| quietdrift90 | restart+warm | bayside | 24 | 6.44 | 8.1 |
| quietdrift90 | restart+warm | blocks | 24 | 6.35 | 8.08 |
| quietdrift90 | restart+warm | boulevard | 24 | 6.46 | 8.23 |
| quietdrift90 | warm | bayside | 24 | 6.54 | 8.6 |
| quietdrift90 | warm | blocks | 24 | 6.43 | 8.53 |
| quietdrift90 | warm | boulevard | 24 | 6.59 | 8.82 |

## Recovery moves and filter restarts (medians)

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 2.0 | None |
| blocked30 | a0.3 | blocks | 24 | 2.0 | None |
| blocked30 | a0.3 | boulevard | 24 | 2.0 | None |
| blocked30 | restart+warm | bayside | 24 | 1.0 | 3.0 |
| blocked30 | restart+warm | blocks | 24 | 1.0 | 3.5 |
| blocked30 | restart+warm | boulevard | 24 | 1.0 | 4.5 |
| blocked30 | warm | bayside | 24 | 1.0 | None |
| blocked30 | warm | blocks | 24 | 1.0 | None |
| blocked30 | warm | boulevard | 24 | 1.0 | None |
| outage90 | a0.3 | bayside | 24 | 0.0 | None |
| outage90 | a0.3 | blocks | 24 | 0.0 | None |
| outage90 | a0.3 | boulevard | 24 | 0.0 | None |
| outage90 | restart+warm | bayside | 24 | 0.0 | 3.0 |
| outage90 | restart+warm | blocks | 24 | 0.0 | 3.5 |
| outage90 | restart+warm | boulevard | 24 | 0.0 | 4.0 |
| outage90 | warm | bayside | 24 | 0.0 | None |
| outage90 | warm | blocks | 24 | 0.0 | None |
| outage90 | warm | boulevard | 24 | 0.0 | None |
| quiet45 | a0.3 | bayside | 24 | 1.0 | None |
| quiet45 | a0.3 | blocks | 24 | 1.0 | None |
| quiet45 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet45 | restart+warm | bayside | 24 | 0.0 | 6.5 |
| quiet45 | restart+warm | blocks | 24 | 0.0 | 7.0 |
| quiet45 | restart+warm | boulevard | 24 | 0.0 | 7.0 |
| quiet45 | warm | bayside | 24 | 0.0 | None |
| quiet45 | warm | blocks | 24 | 0.0 | None |
| quiet45 | warm | boulevard | 24 | 0.0 | None |
| quiet90 | a0.3 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet90 | restart+warm | bayside | 24 | 0.0 | 3.0 |
| quiet90 | restart+warm | blocks | 24 | 0.0 | 3.5 |
| quiet90 | restart+warm | boulevard | 24 | 0.0 | 4.0 |
| quiet90 | warm | bayside | 24 | 0.0 | None |
| quiet90 | warm | blocks | 24 | 0.0 | None |
| quiet90 | warm | boulevard | 24 | 0.0 | None |
| quietdrift90 | a0.3 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3 | boulevard | 24 | 1.0 | None |
| quietdrift90 | restart+warm | bayside | 24 | 0.0 | 3.0 |
| quietdrift90 | restart+warm | blocks | 24 | 0.0 | 3.5 |
| quietdrift90 | restart+warm | boulevard | 24 | 0.0 | 4.5 |
| quietdrift90 | warm | bayside | 24 | 0.0 | None |
| quietdrift90 | warm | blocks | 24 | 0.0 | None |
| quietdrift90 | warm | boulevard | 24 | 0.0 | None |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | blocks | 24 | 9.0 | 0.82 | 2.52 | 3.59 | 2.01 | 2.79 |
| blocked30 | restart+warm | blocks | 24 | 9.0 | 0.79 | 2.36 | 3.7 | 1.94 | 2.71 |
| blocked30 | warm | blocks | 24 | 9.0 | 0.8 | 2.47 | 3.46 | 2.01 | 2.75 |
| outage90 | a0.3 | blocks | 24 | 9.0 | 1.07 | 2.8 | 4.04 | 2.12 | 3.35 |
| outage90 | restart+warm | blocks | 24 | 9.0 | 1.08 | 2.85 | 4.41 | 2.06 | 3.04 |
| outage90 | warm | blocks | 24 | 9.0 | 1.06 | 2.73 | 3.87 | 2.15 | 3.25 |
| quiet45 | a0.3 | blocks | 24 | 9.0 | 0.91 | 2.79 | 4.62 | 1.99 | 3.38 |
| quiet45 | restart+warm | blocks | 24 | 9.0 | 0.83 | 2.62 | 4.56 | 1.9 | 2.73 |
| quiet45 | warm | blocks | 24 | 9.0 | 0.94 | 2.82 | 4.62 | 2.0 | 3.24 |
| quiet90 | a0.3 | blocks | 24 | 9.0 | 0.8 | 2.52 | 3.75 | 1.99 | 2.81 |
| quiet90 | restart+warm | blocks | 24 | 9.0 | 0.81 | 2.46 | 3.75 | 1.96 | 2.73 |
| quiet90 | warm | blocks | 24 | 9.0 | 0.82 | 2.59 | 4.36 | 2.03 | 2.83 |
| quietdrift90 | a0.3 | blocks | 24 | 9.0 | 1.65 | 4.41 | 6.14 | 2.38 | 4.71 |
| quietdrift90 | restart+warm | blocks | 24 | 9.0 | 1.64 | 4.19 | 5.72 | 2.37 | 4.55 |
| quietdrift90 | warm | blocks | 24 | 9.0 | 1.62 | 4.33 | 5.87 | 2.37 | 4.86 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 0.2 | 1.69 |
| blocked30 | a0.3 | blocks | 24 | 0.28 | 2.62 |
| blocked30 | a0.3 | boulevard | 24 | 0.14 | 0.69 |
| blocked30 | restart+warm | bayside | 24 | 0.18 | 1.02 |
| blocked30 | restart+warm | blocks | 24 | 0.26 | 2.17 |
| blocked30 | restart+warm | boulevard | 24 | 0.13 | 0.62 |
| blocked30 | warm | bayside | 24 | 0.2 | 1.6 |
| blocked30 | warm | blocks | 24 | 0.28 | 2.67 |
| blocked30 | warm | boulevard | 24 | 0.14 | 0.74 |
| outage90 | a0.3 | bayside | 24 | 0.58 | 2.87 |
| outage90 | a0.3 | blocks | 24 | 0.77 | 3.49 |
| outage90 | a0.3 | boulevard | 24 | 0.6 | 3.1 |
| outage90 | restart+warm | bayside | 24 | 0.52 | 2.81 |
| outage90 | restart+warm | blocks | 24 | 0.79 | 3.13 |
| outage90 | restart+warm | boulevard | 24 | 0.58 | 2.68 |
| outage90 | warm | bayside | 24 | 0.56 | 3.23 |
| outage90 | warm | blocks | 24 | 0.75 | 3.48 |
| outage90 | warm | boulevard | 24 | 0.61 | 3.17 |
| quiet45 | a0.3 | bayside | 24 | 0.22 | 2.0 |
| quiet45 | a0.3 | blocks | 24 | 0.34 | 3.1 |
| quiet45 | a0.3 | boulevard | 24 | 0.16 | 0.94 |
| quiet45 | restart+warm | bayside | 24 | 0.21 | 1.15 |
| quiet45 | restart+warm | blocks | 24 | 0.28 | 2.33 |
| quiet45 | restart+warm | boulevard | 24 | 0.14 | 0.68 |
| quiet45 | warm | bayside | 24 | 0.23 | 2.01 |
| quiet45 | warm | blocks | 24 | 0.34 | 2.85 |
| quiet45 | warm | boulevard | 24 | 0.15 | 0.83 |
| quiet90 | a0.3 | bayside | 24 | 0.2 | 2.1 |
| quiet90 | a0.3 | blocks | 24 | 0.29 | 2.98 |
| quiet90 | a0.3 | boulevard | 24 | 0.15 | 0.85 |
| quiet90 | restart+warm | bayside | 24 | 0.2 | 1.04 |
| quiet90 | restart+warm | blocks | 24 | 0.28 | 2.29 |
| quiet90 | restart+warm | boulevard | 24 | 0.13 | 0.63 |
| quiet90 | warm | bayside | 24 | 0.2 | 1.56 |
| quiet90 | warm | blocks | 24 | 0.29 | 2.67 |
| quiet90 | warm | boulevard | 24 | 0.14 | 0.8 |
| quietdrift90 | a0.3 | bayside | 24 | 1.54 | 5.22 |
| quietdrift90 | a0.3 | blocks | 24 | 1.65 | 6.62 |
| quietdrift90 | a0.3 | boulevard | 24 | 1.54 | 7.48 |
| quietdrift90 | restart+warm | bayside | 24 | 1.5 | 4.5 |
| quietdrift90 | restart+warm | blocks | 24 | 1.6 | 5.16 |
| quietdrift90 | restart+warm | boulevard | 24 | 1.46 | 5.79 |
| quietdrift90 | warm | bayside | 24 | 1.5 | 4.89 |
| quietdrift90 | warm | blocks | 24 | 1.62 | 6.99 |
| quietdrift90 | warm | boulevard | 24 | 1.51 | 6.64 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 6.67 | 7.53 | 0 | 0 |
| blocked30 | a0.3 | blocks | 24 | 7.17 | 8.8 | 0 | 0 |
| blocked30 | a0.3 | boulevard | 24 | 6.97 | 7.54 | 0 | 0 |
| blocked30 | restart+warm | bayside | 24 | 6.43 | 7.3 | 0 | 0 |
| blocked30 | restart+warm | blocks | 24 | 6.83 | 7.48 | 0 | 0 |
| blocked30 | restart+warm | boulevard | 24 | 6.85 | 7.52 | 0 | 0 |
| blocked30 | warm | bayside | 24 | 6.45 | 7.3 | 0 | 0 |
| blocked30 | warm | blocks | 24 | 6.98 | 9.76 | 0 | 0 |
| blocked30 | warm | boulevard | 24 | 6.85 | 7.52 | 0 | 0 |
| outage90 | a0.3 | bayside | 24 | 7.02 | 11.89 | 0 | 0 |
| outage90 | a0.3 | blocks | 24 | 7.54 | 10.48 | 0 | 0 |
| outage90 | a0.3 | boulevard | 24 | 7.33 | 9.66 | 0 | 0 |
| outage90 | restart+warm | bayside | 24 | 6.9 | 8.19 | 0 | 0 |
| outage90 | restart+warm | blocks | 24 | 7.17 | 9.08 | 0 | 0 |
| outage90 | restart+warm | boulevard | 24 | 7.0 | 11.05 | 0 | 0 |
| outage90 | warm | bayside | 24 | 7.02 | 13.18 | 0 | 0 |
| outage90 | warm | blocks | 24 | 7.38 | 10.48 | 0 | 0 |
| outage90 | warm | boulevard | 24 | 7.05 | 9.66 | 0 | 0 |
| quiet45 | a0.3 | bayside | 24 | 7.21 | 7.61 | 0 | 0 |
| quiet45 | a0.3 | blocks | 24 | 7.46 | 8.01 | 0 | 0 |
| quiet45 | a0.3 | boulevard | 24 | 7.45 | 7.89 | 0 | 0 |
| quiet45 | restart+warm | bayside | 24 | 6.54 | 6.97 | 0 | 0 |
| quiet45 | restart+warm | blocks | 24 | 6.88 | 7.31 | 0 | 0 |
| quiet45 | restart+warm | boulevard | 24 | 6.9 | 7.42 | 0 | 0 |
| quiet45 | warm | bayside | 24 | 6.55 | 7.69 | 0 | 0 |
| quiet45 | warm | blocks | 24 | 6.89 | 8.01 | 0 | 0 |
| quiet45 | warm | boulevard | 24 | 6.93 | 7.61 | 0 | 0 |
| quiet90 | a0.3 | bayside | 24 | 7.29 | 7.74 | 0 | 0 |
| quiet90 | a0.3 | blocks | 24 | 7.51 | 9.54 | 0 | 0 |
| quiet90 | a0.3 | boulevard | 24 | 7.45 | 7.89 | 0 | 0 |
| quiet90 | restart+warm | bayside | 24 | 6.55 | 7.29 | 0 | 0 |
| quiet90 | restart+warm | blocks | 24 | 6.89 | 7.33 | 0 | 0 |
| quiet90 | restart+warm | boulevard | 24 | 6.93 | 7.42 | 0 | 0 |
| quiet90 | warm | bayside | 24 | 6.57 | 7.73 | 0 | 0 |
| quiet90 | warm | blocks | 24 | 7.18 | 9.27 | 0 | 0 |
| quiet90 | warm | boulevard | 24 | 6.93 | 7.85 | 0 | 0 |
| quietdrift90 | a0.3 | bayside | 24 | 9.3 | 25.48 | 0 | 0 |
| quietdrift90 | a0.3 | blocks | 24 | 12.23 | 24.68 | 0 | 0 |
| quietdrift90 | a0.3 | boulevard | 24 | 13.36 | 23.9 | 0 | 0 |
| quietdrift90 | restart+warm | bayside | 24 | 8.31 | 25.07 | 0 | 0 |
| quietdrift90 | restart+warm | blocks | 24 | 10.01 | 22.14 | 0 | 0 |
| quietdrift90 | restart+warm | boulevard | 24 | 12.34 | 22.62 | 0 | 0 |
| quietdrift90 | warm | bayside | 24 | 8.93 | 22.51 | 0 | 0 |
| quietdrift90 | warm | blocks | 24 | 11.59 | 22.86 | 0 | 0 |
| quietdrift90 | warm | boulevard | 24 | 12.8 | 23.38 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | checkpoint | 24 | 6315 | 0 | None | 0.19 | 0.81 | 1.1 |
| blocked30 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | a0.3 | bayside | other | 24 | 26896 | 0 | None | 0.2 | 2.16 | 6.67 |
| blocked30 | a0.3 | bayside | outage | 20 | 3214 | 0 | None | 0.55 | 1.43 | 1.78 |
| blocked30 | a0.3 | bayside | fix | 24 | 29997 | 0 | None | 0.18 | 1.99 | 6.67 |
| blocked30 | a0.3 | blocks | checkpoint | 24 | 8266 | 38 | 0.95 | 0.39 | 2.69 | 4.35 |
| blocked30 | a0.3 | blocks | corner | 24 | 8771 | 2 | 0.05 | 0.82 | 2.52 | 3.59 |
| blocked30 | a0.3 | blocks | other | 24 | 19083 | 0 | 0.0 | 0.21 | 2.15 | 6.92 |
| blocked30 | a0.3 | blocks | outage | 22 | 3438 | 0 | 0.0 | 0.46 | 2.42 | 4.22 |
| blocked30 | a0.3 | blocks | fix | 24 | 32682 | 40 | 1.0 | 0.28 | 2.66 | 7.17 |
| blocked30 | a0.3 | boulevard | checkpoint | 24 | 6280 | 0 | None | 0.18 | 0.57 | 0.88 |
| blocked30 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | a0.3 | boulevard | other | 24 | 34014 | 0 | None | 0.14 | 0.7 | 6.97 |
| blocked30 | a0.3 | boulevard | outage | 23 | 4267 | 0 | None | 0.31 | 0.69 | 0.8 |
| blocked30 | a0.3 | boulevard | fix | 24 | 36027 | 0 | None | 0.13 | 0.66 | 6.97 |
| blocked30 | restart+warm | bayside | checkpoint | 24 | 6294 | 0 | None | 0.18 | 0.51 | 0.81 |
| blocked30 | restart+warm | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | restart+warm | bayside | other | 24 | 26837 | 0 | None | 0.19 | 1.25 | 6.43 |
| blocked30 | restart+warm | bayside | outage | 20 | 3192 | 0 | None | 0.61 | 1.3 | 1.79 |
| blocked30 | restart+warm | bayside | fix | 24 | 29939 | 0 | None | 0.17 | 0.7 | 6.43 |
| blocked30 | restart+warm | blocks | checkpoint | 24 | 8146 | 0 | None | 0.32 | 2.03 | 2.4 |
| blocked30 | restart+warm | blocks | corner | 24 | 8713 | 0 | None | 0.79 | 2.36 | 3.7 |
| blocked30 | restart+warm | blocks | other | 24 | 19047 | 0 | None | 0.19 | 1.85 | 6.83 |
| blocked30 | restart+warm | blocks | outage | 22 | 3334 | 0 | None | 0.44 | 1.83 | 3.2 |
| blocked30 | restart+warm | blocks | fix | 24 | 32572 | 0 | None | 0.24 | 2.21 | 6.83 |
| blocked30 | restart+warm | boulevard | checkpoint | 24 | 6288 | 0 | None | 0.14 | 0.49 | 0.83 |
| blocked30 | restart+warm | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | restart+warm | boulevard | other | 24 | 34016 | 0 | None | 0.12 | 0.67 | 6.85 |
| blocked30 | restart+warm | boulevard | outage | 23 | 4235 | 0 | None | 0.27 | 0.71 | 0.81 |
| blocked30 | restart+warm | boulevard | fix | 24 | 36069 | 0 | None | 0.12 | 0.49 | 6.85 |
| blocked30 | warm | bayside | checkpoint | 24 | 6315 | 0 | None | 0.19 | 0.69 | 1.0 |
| blocked30 | warm | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | warm | bayside | other | 24 | 26913 | 0 | None | 0.2 | 2.11 | 6.45 |
| blocked30 | warm | bayside | outage | 20 | 3210 | 0 | None | 0.52 | 1.42 | 1.81 |
| blocked30 | warm | bayside | fix | 24 | 30018 | 0 | None | 0.18 | 1.87 | 6.45 |
| blocked30 | warm | blocks | checkpoint | 24 | 8282 | 47 | 0.839 | 0.4 | 3.0 | 4.58 |
| blocked30 | warm | blocks | corner | 24 | 8770 | 9 | 0.161 | 0.8 | 2.47 | 3.46 |
| blocked30 | warm | blocks | other | 24 | 19113 | 0 | 0.0 | 0.21 | 1.96 | 6.83 |
| blocked30 | warm | blocks | outage | 22 | 3437 | 0 | 0.0 | 0.39 | 2.44 | 4.1 |
| blocked30 | warm | blocks | fix | 24 | 32728 | 56 | 1.0 | 0.26 | 2.66 | 6.98 |
| blocked30 | warm | boulevard | checkpoint | 24 | 6289 | 0 | None | 0.17 | 0.55 | 0.88 |
| blocked30 | warm | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | warm | boulevard | other | 24 | 34024 | 0 | None | 0.13 | 0.71 | 6.85 |
| blocked30 | warm | boulevard | outage | 23 | 4238 | 0 | None | 0.27 | 0.74 | 0.87 |
| blocked30 | warm | boulevard | fix | 24 | 36075 | 0 | None | 0.13 | 0.66 | 6.85 |
| outage90 | a0.3 | bayside | checkpoint | 24 | 6324 | 0 | 0.0 | 0.58 | 1.67 | 2.13 |
| outage90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | bayside | other | 24 | 26522 | 57 | 1.0 | 0.57 | 3.98 | 7.02 |
| outage90 | a0.3 | bayside | outage | 20 | 3061 | 13 | 0.228 | 1.77 | 3.49 | 4.88 |
| outage90 | a0.3 | bayside | fix | 24 | 29785 | 44 | 0.772 | 0.55 | 2.77 | 7.02 |
| outage90 | a0.3 | blocks | checkpoint | 24 | 8372 | 75 | 0.487 | 0.81 | 3.19 | 5.33 |
| outage90 | a0.3 | blocks | corner | 24 | 8797 | 29 | 0.188 | 1.07 | 2.8 | 4.04 |
| outage90 | a0.3 | blocks | other | 24 | 18722 | 50 | 0.325 | 0.66 | 3.53 | 7.25 |
| outage90 | a0.3 | blocks | outage | 22 | 3419 | 2 | 0.013 | 2.0 | 4.12 | 4.93 |
| outage90 | a0.3 | blocks | fix | 24 | 32472 | 152 | 0.987 | 0.73 | 3.13 | 7.54 |
| outage90 | a0.3 | boulevard | checkpoint | 24 | 6306 | 0 | 0.0 | 0.54 | 1.44 | 1.85 |
| outage90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | boulevard | other | 24 | 33618 | 92 | 1.0 | 0.61 | 3.27 | 7.33 |
| outage90 | a0.3 | boulevard | outage | 22 | 4247 | 18 | 0.196 | 1.63 | 4.21 | 4.56 |
| outage90 | a0.3 | boulevard | fix | 24 | 35677 | 74 | 0.804 | 0.56 | 2.38 | 7.33 |
| outage90 | restart+warm | bayside | checkpoint | 24 | 6330 | 0 | 0.0 | 0.52 | 1.45 | 1.7 |
| outage90 | restart+warm | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart+warm | bayside | other | 24 | 26441 | 10 | 1.0 | 0.55 | 3.47 | 6.9 |
| outage90 | restart+warm | bayside | outage | 20 | 3174 | 7 | 0.7 | 2.06 | 4.02 | 4.8 |
| outage90 | restart+warm | bayside | fix | 24 | 29597 | 3 | 0.3 | 0.5 | 1.86 | 6.89 |
| outage90 | restart+warm | blocks | checkpoint | 24 | 8215 | 0 | 0.0 | 0.83 | 2.69 | 3.68 |
| outage90 | restart+warm | blocks | corner | 24 | 8671 | 2 | 0.143 | 1.08 | 2.85 | 4.41 |
| outage90 | restart+warm | blocks | other | 24 | 18613 | 12 | 0.857 | 0.67 | 3.29 | 7.04 |
| outage90 | restart+warm | blocks | outage | 22 | 3353 | 2 | 0.143 | 1.81 | 4.33 | 5.24 |
| outage90 | restart+warm | blocks | fix | 24 | 32146 | 12 | 0.857 | 0.7 | 2.69 | 7.04 |
| outage90 | restart+warm | boulevard | checkpoint | 24 | 6306 | 0 | 0.0 | 0.5 | 1.36 | 1.75 |
| outage90 | restart+warm | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart+warm | boulevard | other | 24 | 33593 | 70 | 1.0 | 0.61 | 2.85 | 7.0 |
| outage90 | restart+warm | boulevard | outage | 22 | 4225 | 48 | 0.686 | 1.86 | 4.04 | 4.33 |
| outage90 | restart+warm | boulevard | fix | 24 | 35674 | 22 | 0.314 | 0.55 | 1.9 | 7.0 |
| outage90 | warm | bayside | checkpoint | 24 | 6327 | 0 | 0.0 | 0.56 | 1.7 | 2.38 |
| outage90 | warm | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm | bayside | other | 24 | 26510 | 92 | 1.0 | 0.57 | 4.06 | 7.02 |
| outage90 | warm | bayside | outage | 20 | 3117 | 33 | 0.359 | 2.0 | 3.83 | 5.14 |
| outage90 | warm | bayside | fix | 24 | 29720 | 59 | 0.641 | 0.53 | 2.75 | 7.02 |
| outage90 | warm | blocks | checkpoint | 24 | 8373 | 54 | 0.54 | 0.84 | 3.37 | 5.21 |
| outage90 | warm | blocks | corner | 24 | 8779 | 26 | 0.26 | 1.06 | 2.73 | 3.87 |
| outage90 | warm | blocks | other | 24 | 18681 | 20 | 0.2 | 0.65 | 3.25 | 7.13 |
| outage90 | warm | blocks | outage | 22 | 3368 | 2 | 0.02 | 1.65 | 3.85 | 4.79 |
| outage90 | warm | blocks | fix | 24 | 32465 | 98 | 0.98 | 0.72 | 3.07 | 7.33 |
| outage90 | warm | boulevard | checkpoint | 24 | 6309 | 0 | 0.0 | 0.56 | 1.44 | 1.89 |
| outage90 | warm | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm | boulevard | other | 24 | 33583 | 35 | 1.0 | 0.63 | 3.35 | 7.05 |
| outage90 | warm | boulevard | outage | 22 | 4223 | 8 | 0.229 | 1.72 | 4.21 | 4.49 |
| outage90 | warm | boulevard | fix | 24 | 35669 | 27 | 0.771 | 0.56 | 2.09 | 7.05 |
| quiet45 | a0.3 | bayside | checkpoint | 24 | 6322 | 0 | None | 0.19 | 0.95 | 1.77 |
| quiet45 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3 | bayside | other | 24 | 26532 | 0 | None | 0.23 | 2.31 | 7.21 |
| quiet45 | a0.3 | bayside | outage | 24 | 4195 | 0 | None | 0.46 | 1.42 | 1.65 |
| quiet45 | a0.3 | bayside | fix | 24 | 28659 | 0 | None | 0.2 | 2.28 | 7.21 |
| quiet45 | a0.3 | blocks | checkpoint | 24 | 8331 | 1 | 1.0 | 0.4 | 3.11 | 4.85 |
| quiet45 | a0.3 | blocks | corner | 24 | 8735 | 0 | 0.0 | 0.91 | 2.79 | 4.62 |
| quiet45 | a0.3 | blocks | other | 24 | 18652 | 0 | 0.0 | 0.24 | 3.5 | 7.41 |
| quiet45 | a0.3 | blocks | outage | 24 | 4470 | 0 | 0.0 | 0.49 | 2.34 | 4.3 |
| quiet45 | a0.3 | blocks | fix | 24 | 31248 | 1 | 1.0 | 0.3 | 3.24 | 7.46 |
| quiet45 | a0.3 | boulevard | checkpoint | 24 | 6323 | 0 | None | 0.18 | 0.97 | 1.51 |
| quiet45 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3 | boulevard | other | 24 | 33600 | 0 | None | 0.15 | 0.94 | 7.45 |
| quiet45 | a0.3 | boulevard | outage | 24 | 5173 | 0 | None | 0.28 | 0.8 | 0.98 |
| quiet45 | a0.3 | boulevard | fix | 24 | 34750 | 0 | None | 0.15 | 1.03 | 7.45 |
| quiet45 | restart+warm | bayside | checkpoint | 24 | 6313 | 0 | None | 0.2 | 0.65 | 0.91 |
| quiet45 | restart+warm | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm | bayside | other | 24 | 26362 | 0 | None | 0.22 | 1.24 | 6.54 |
| quiet45 | restart+warm | bayside | outage | 24 | 4185 | 0 | None | 0.55 | 1.46 | 1.66 |
| quiet45 | restart+warm | bayside | fix | 24 | 28490 | 0 | None | 0.19 | 0.97 | 6.54 |
| quiet45 | restart+warm | blocks | checkpoint | 24 | 8200 | 0 | None | 0.33 | 1.94 | 2.54 |
| quiet45 | restart+warm | blocks | corner | 24 | 8598 | 0 | None | 0.83 | 2.62 | 4.56 |
| quiet45 | restart+warm | blocks | other | 24 | 18566 | 0 | None | 0.21 | 2.04 | 6.88 |
| quiet45 | restart+warm | blocks | outage | 24 | 4431 | 0 | None | 0.37 | 2.78 | 4.5 |
| quiet45 | restart+warm | blocks | fix | 24 | 30933 | 0 | None | 0.26 | 2.29 | 6.88 |
| quiet45 | restart+warm | boulevard | checkpoint | 24 | 6313 | 0 | None | 0.17 | 0.56 | 0.86 |
| quiet45 | restart+warm | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm | boulevard | other | 24 | 33508 | 0 | None | 0.13 | 0.64 | 6.9 |
| quiet45 | restart+warm | boulevard | outage | 24 | 5110 | 0 | None | 0.21 | 0.68 | 0.86 |
| quiet45 | restart+warm | boulevard | fix | 24 | 34711 | 0 | None | 0.13 | 0.62 | 6.9 |
| quiet45 | warm | bayside | checkpoint | 24 | 6324 | 0 | None | 0.18 | 1.08 | 1.72 |
| quiet45 | warm | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm | bayside | other | 24 | 26451 | 0 | None | 0.23 | 2.17 | 6.55 |
| quiet45 | warm | bayside | outage | 24 | 4170 | 0 | None | 0.46 | 1.4 | 1.76 |
| quiet45 | warm | bayside | fix | 24 | 28605 | 0 | None | 0.2 | 2.12 | 6.55 |
| quiet45 | warm | blocks | checkpoint | 24 | 8325 | 1 | 1.0 | 0.39 | 3.1 | 5.08 |
| quiet45 | warm | blocks | corner | 24 | 8763 | 0 | 0.0 | 0.94 | 2.82 | 4.62 |
| quiet45 | warm | blocks | other | 24 | 18576 | 0 | 0.0 | 0.26 | 2.43 | 6.89 |
| quiet45 | warm | blocks | outage | 24 | 4456 | 0 | 0.0 | 0.49 | 2.27 | 4.4 |
| quiet45 | warm | blocks | fix | 24 | 31208 | 1 | 1.0 | 0.31 | 2.9 | 6.89 |
| quiet45 | warm | boulevard | checkpoint | 24 | 6322 | 0 | None | 0.18 | 0.85 | 1.15 |
| quiet45 | warm | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm | boulevard | other | 24 | 33510 | 0 | None | 0.15 | 0.79 | 6.93 |
| quiet45 | warm | boulevard | outage | 24 | 5113 | 0 | None | 0.21 | 0.72 | 0.9 |
| quiet45 | warm | boulevard | fix | 24 | 34719 | 0 | None | 0.15 | 0.86 | 6.93 |
| quiet90 | a0.3 | bayside | checkpoint | 24 | 6316 | 0 | None | 0.18 | 0.58 | 0.8 |
| quiet90 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3 | bayside | other | 24 | 26518 | 0 | None | 0.21 | 2.58 | 7.29 |
| quiet90 | a0.3 | bayside | outage | 20 | 3071 | 0 | None | 0.59 | 1.47 | 1.98 |
| quiet90 | a0.3 | bayside | fix | 24 | 29763 | 0 | None | 0.19 | 2.4 | 7.29 |
| quiet90 | a0.3 | blocks | checkpoint | 24 | 8311 | 25 | 1.0 | 0.4 | 3.19 | 3.86 |
| quiet90 | a0.3 | blocks | corner | 24 | 8750 | 0 | 0.0 | 0.8 | 2.52 | 3.75 |
| quiet90 | a0.3 | blocks | other | 24 | 18751 | 0 | 0.0 | 0.21 | 3.51 | 7.41 |
| quiet90 | a0.3 | blocks | outage | 22 | 3293 | 0 | 0.0 | 0.41 | 2.1 | 2.92 |
| quiet90 | a0.3 | blocks | fix | 24 | 32519 | 25 | 1.0 | 0.27 | 3.31 | 7.51 |
| quiet90 | a0.3 | boulevard | checkpoint | 24 | 6287 | 0 | None | 0.18 | 0.55 | 0.84 |
| quiet90 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3 | boulevard | other | 24 | 33636 | 0 | None | 0.14 | 0.89 | 7.45 |
| quiet90 | a0.3 | boulevard | outage | 23 | 4241 | 0 | None | 0.31 | 0.78 | 0.95 |
| quiet90 | a0.3 | boulevard | fix | 24 | 35682 | 0 | None | 0.14 | 0.73 | 7.45 |
| quiet90 | restart+warm | bayside | checkpoint | 24 | 6311 | 0 | None | 0.17 | 0.53 | 0.71 |
| quiet90 | restart+warm | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm | bayside | other | 24 | 26348 | 0 | None | 0.2 | 1.13 | 6.55 |
| quiet90 | restart+warm | bayside | outage | 20 | 3130 | 0 | None | 0.61 | 1.36 | 1.77 |
| quiet90 | restart+warm | bayside | fix | 24 | 29529 | 0 | None | 0.18 | 0.72 | 6.55 |
| quiet90 | restart+warm | blocks | checkpoint | 24 | 8174 | 0 | None | 0.34 | 2.04 | 2.48 |
| quiet90 | restart+warm | blocks | corner | 24 | 8649 | 0 | None | 0.81 | 2.46 | 3.75 |
| quiet90 | restart+warm | blocks | other | 24 | 18561 | 0 | None | 0.2 | 2.04 | 6.89 |
| quiet90 | restart+warm | blocks | outage | 21 | 3312 | 0 | None | 0.6 | 2.55 | 4.19 |
| quiet90 | restart+warm | blocks | fix | 24 | 32072 | 0 | None | 0.24 | 2.25 | 6.89 |
| quiet90 | restart+warm | boulevard | checkpoint | 24 | 6288 | 0 | None | 0.16 | 0.53 | 0.83 |
| quiet90 | restart+warm | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm | boulevard | other | 24 | 33532 | 0 | None | 0.12 | 0.67 | 6.93 |
| quiet90 | restart+warm | boulevard | outage | 22 | 4202 | 0 | None | 0.3 | 0.74 | 1.0 |
| quiet90 | restart+warm | boulevard | fix | 24 | 35618 | 0 | None | 0.12 | 0.5 | 6.93 |
| quiet90 | warm | bayside | checkpoint | 24 | 6318 | 0 | None | 0.17 | 0.6 | 0.89 |
| quiet90 | warm | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm | bayside | other | 24 | 26441 | 0 | None | 0.2 | 2.17 | 6.57 |
| quiet90 | warm | bayside | outage | 20 | 3081 | 0 | None | 0.53 | 1.42 | 1.75 |
| quiet90 | warm | bayside | fix | 24 | 29678 | 0 | None | 0.18 | 1.9 | 6.57 |
| quiet90 | warm | blocks | checkpoint | 24 | 8331 | 24 | 1.0 | 0.4 | 3.17 | 4.64 |
| quiet90 | warm | blocks | corner | 24 | 8760 | 0 | 0.0 | 0.82 | 2.59 | 4.36 |
| quiet90 | warm | blocks | other | 24 | 18634 | 0 | 0.0 | 0.21 | 2.17 | 6.89 |
| quiet90 | warm | blocks | outage | 21 | 3285 | 0 | 0.0 | 0.48 | 2.65 | 4.29 |
| quiet90 | warm | blocks | fix | 24 | 32440 | 24 | 1.0 | 0.27 | 2.64 | 7.18 |
| quiet90 | warm | boulevard | checkpoint | 24 | 6299 | 0 | None | 0.18 | 0.64 | 1.04 |
| quiet90 | warm | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm | boulevard | other | 24 | 33526 | 0 | None | 0.13 | 0.82 | 6.93 |
| quiet90 | warm | boulevard | outage | 22 | 4205 | 0 | None | 0.29 | 0.85 | 0.99 |
| quiet90 | warm | boulevard | fix | 24 | 35620 | 0 | None | 0.13 | 0.72 | 6.93 |
| quietdrift90 | a0.3 | bayside | checkpoint | 24 | 6355 | 74 | 0.063 | 1.27 | 4.32 | 5.01 |
| quietdrift90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | bayside | other | 24 | 26725 | 1100 | 0.937 | 1.56 | 5.04 | 8.44 |
| quietdrift90 | a0.3 | bayside | outage | 20 | 3118 | 541 | 0.461 | 3.94 | 8.59 | 9.62 |
| quietdrift90 | a0.3 | bayside | fix | 24 | 29962 | 633 | 0.539 | 1.44 | 5.38 | 9.3 |
| quietdrift90 | a0.3 | blocks | checkpoint | 24 | 8404 | 258 | 0.196 | 1.65 | 4.95 | 7.29 |
| quietdrift90 | a0.3 | blocks | corner | 24 | 8781 | 96 | 0.073 | 1.65 | 4.41 | 6.14 |
| quietdrift90 | a0.3 | blocks | other | 24 | 19029 | 959 | 0.73 | 1.67 | 6.72 | 12.23 |
| quietdrift90 | a0.3 | blocks | outage | 22 | 3397 | 542 | 0.413 | 3.41 | 8.8 | 11.08 |
| quietdrift90 | a0.3 | blocks | fix | 24 | 32817 | 771 | 0.587 | 1.61 | 5.66 | 11.27 |
| quietdrift90 | a0.3 | boulevard | checkpoint | 24 | 6340 | 219 | 0.12 | 1.64 | 4.58 | 5.21 |
| quietdrift90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | boulevard | other | 24 | 33848 | 1607 | 0.88 | 1.52 | 7.78 | 13.25 |
| quietdrift90 | a0.3 | boulevard | outage | 23 | 4277 | 800 | 0.438 | 3.71 | 10.67 | 13.22 |
| quietdrift90 | a0.3 | boulevard | fix | 24 | 35911 | 1026 | 0.562 | 1.44 | 5.52 | 13.36 |
| quietdrift90 | restart+warm | bayside | checkpoint | 24 | 6349 | 47 | 0.046 | 1.25 | 3.83 | 4.65 |
| quietdrift90 | restart+warm | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm | bayside | other | 24 | 26580 | 979 | 0.954 | 1.54 | 4.67 | 8.02 |
| quietdrift90 | restart+warm | bayside | outage | 20 | 3202 | 547 | 0.533 | 3.21 | 8.5 | 9.05 |
| quietdrift90 | restart+warm | bayside | fix | 24 | 29727 | 479 | 0.467 | 1.42 | 4.44 | 8.31 |
| quietdrift90 | restart+warm | blocks | checkpoint | 24 | 8255 | 134 | 0.147 | 1.58 | 4.66 | 5.38 |
| quietdrift90 | restart+warm | blocks | corner | 24 | 8711 | 78 | 0.086 | 1.64 | 4.19 | 5.72 |
| quietdrift90 | restart+warm | blocks | other | 24 | 18788 | 700 | 0.768 | 1.63 | 5.5 | 9.48 |
| quietdrift90 | restart+warm | blocks | outage | 21 | 3270 | 475 | 0.521 | 3.04 | 9.91 | 10.54 |
| quietdrift90 | restart+warm | blocks | fix | 24 | 32484 | 437 | 0.479 | 1.6 | 4.57 | 9.37 |
| quietdrift90 | restart+warm | boulevard | checkpoint | 24 | 6332 | 161 | 0.111 | 1.67 | 4.4 | 5.26 |
| quietdrift90 | restart+warm | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm | boulevard | other | 24 | 33778 | 1289 | 0.889 | 1.41 | 6.72 | 12.34 |
| quietdrift90 | restart+warm | boulevard | outage | 23 | 4248 | 810 | 0.559 | 3.29 | 10.93 | 12.16 |
| quietdrift90 | restart+warm | boulevard | fix | 24 | 35862 | 640 | 0.441 | 1.4 | 4.63 | 12.34 |
| quietdrift90 | warm | bayside | checkpoint | 24 | 6347 | 64 | 0.058 | 1.33 | 3.96 | 4.61 |
| quietdrift90 | warm | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm | bayside | other | 24 | 26651 | 1043 | 0.942 | 1.54 | 4.74 | 8.16 |
| quietdrift90 | warm | bayside | outage | 20 | 3137 | 529 | 0.478 | 3.5 | 8.47 | 8.96 |
| quietdrift90 | warm | bayside | fix | 24 | 29861 | 578 | 0.522 | 1.44 | 4.88 | 8.93 |
| quietdrift90 | warm | blocks | checkpoint | 24 | 8419 | 260 | 0.2 | 1.64 | 5.22 | 7.34 |
| quietdrift90 | warm | blocks | corner | 24 | 8771 | 142 | 0.109 | 1.62 | 4.33 | 5.87 |
| quietdrift90 | warm | blocks | other | 24 | 18967 | 900 | 0.691 | 1.71 | 6.47 | 11.58 |
| quietdrift90 | warm | blocks | outage | 21 | 3405 | 563 | 0.432 | 3.4 | 9.06 | 11.17 |
| quietdrift90 | warm | blocks | fix | 24 | 32752 | 739 | 0.568 | 1.56 | 5.62 | 11.44 |
| quietdrift90 | warm | boulevard | checkpoint | 24 | 6333 | 196 | 0.112 | 1.75 | 4.37 | 5.18 |
| quietdrift90 | warm | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm | boulevard | other | 24 | 33767 | 1551 | 0.888 | 1.47 | 7.25 | 12.8 |
| quietdrift90 | warm | boulevard | outage | 23 | 4244 | 806 | 0.461 | 3.29 | 10.31 | 12.15 |
| quietdrift90 | warm | boulevard | fix | 24 | 35856 | 941 | 0.539 | 1.48 | 5.19 | 12.8 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 1.02 | 4.85 |
| blocked30 | a0.3 | blocks | 24 | 1.02 | 4.63 |
| blocked30 | a0.3 | boulevard | 24 | 0.99 | 4.35 |
| blocked30 | restart+warm | bayside | 24 | 1.0 | 4.75 |
| blocked30 | restart+warm | blocks | 24 | 1.03 | 4.58 |
| blocked30 | restart+warm | boulevard | 24 | 0.97 | 4.29 |
| blocked30 | warm | bayside | 24 | 1.01 | 4.75 |
| blocked30 | warm | blocks | 24 | 1.03 | 4.59 |
| blocked30 | warm | boulevard | 24 | 0.98 | 4.29 |
| outage90 | a0.3 | bayside | 24 | 1.57 | 4.52 |
| outage90 | a0.3 | blocks | 24 | 1.62 | 4.29 |
| outage90 | a0.3 | boulevard | 24 | 1.6 | 4.14 |
| outage90 | restart+warm | bayside | 24 | 1.61 | 4.4 |
| outage90 | restart+warm | blocks | 24 | 1.61 | 4.17 |
| outage90 | restart+warm | boulevard | 24 | 1.64 | 3.9 |
| outage90 | warm | bayside | 24 | 1.57 | 4.3 |
| outage90 | warm | blocks | 24 | 1.6 | 4.12 |
| outage90 | warm | boulevard | 24 | 1.64 | 3.91 |
| quiet45 | a0.3 | bayside | 24 | 1.0 | 4.26 |
| quiet45 | a0.3 | blocks | 24 | 1.02 | 4.12 |
| quiet45 | a0.3 | boulevard | 24 | 0.97 | 3.85 |
| quiet45 | restart+warm | bayside | 24 | 1.02 | 3.71 |
| quiet45 | restart+warm | blocks | 24 | 1.02 | 3.66 |
| quiet45 | restart+warm | boulevard | 24 | 0.95 | 3.42 |
| quiet45 | warm | bayside | 24 | 1.0 | 3.72 |
| quiet45 | warm | blocks | 24 | 1.02 | 3.65 |
| quiet45 | warm | boulevard | 24 | 0.96 | 3.42 |
| quiet90 | a0.3 | bayside | 24 | 1.0 | 4.26 |
| quiet90 | a0.3 | blocks | 24 | 1.01 | 4.12 |
| quiet90 | a0.3 | boulevard | 24 | 0.98 | 3.86 |
| quiet90 | restart+warm | bayside | 24 | 0.99 | 3.73 |
| quiet90 | restart+warm | blocks | 24 | 1.0 | 3.65 |
| quiet90 | restart+warm | boulevard | 24 | 0.96 | 3.42 |
| quiet90 | warm | bayside | 24 | 0.99 | 3.73 |
| quiet90 | warm | blocks | 24 | 1.01 | 3.65 |
| quiet90 | warm | boulevard | 24 | 0.96 | 3.42 |
| quietdrift90 | a0.3 | bayside | 24 | 5.32 | 8.68 |
| quietdrift90 | a0.3 | blocks | 24 | 5.53 | 9.15 |
| quietdrift90 | a0.3 | boulevard | 24 | 5.29 | 8.49 |
| quietdrift90 | restart+warm | bayside | 24 | 5.24 | 8.52 |
| quietdrift90 | restart+warm | blocks | 24 | 5.58 | 8.73 |
| quietdrift90 | restart+warm | boulevard | 24 | 5.18 | 8.48 |
| quietdrift90 | warm | bayside | 24 | 5.28 | 8.48 |
| quietdrift90 | warm | blocks | 24 | 5.67 | 8.91 |
| quietdrift90 | warm | boulevard | 24 | 5.1 | 8.47 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 0.0251 |
| blocked30 | a0.3 | blocks | 24 | 0.0352 |
| blocked30 | a0.3 | boulevard | 24 | 0.0207 |
| blocked30 | restart+warm | bayside | 24 | 0.0225 |
| blocked30 | restart+warm | blocks | 24 | 0.0337 |
| blocked30 | restart+warm | boulevard | 24 | 0.0201 |
| blocked30 | warm | bayside | 24 | 0.0244 |
| blocked30 | warm | blocks | 24 | 0.0343 |
| blocked30 | warm | boulevard | 24 | 0.02 |
| outage90 | a0.3 | bayside | 24 | 0.0304 |
| outage90 | a0.3 | blocks | 24 | 0.0406 |
| outage90 | a0.3 | boulevard | 24 | 0.0268 |
| outage90 | restart+warm | bayside | 24 | 0.0291 |
| outage90 | restart+warm | blocks | 24 | 0.0397 |
| outage90 | restart+warm | boulevard | 24 | 0.027 |
| outage90 | warm | bayside | 24 | 0.0302 |
| outage90 | warm | blocks | 24 | 0.0406 |
| outage90 | warm | boulevard | 24 | 0.0266 |
| quiet45 | a0.3 | bayside | 24 | 0.0255 |
| quiet45 | a0.3 | blocks | 24 | 0.0352 |
| quiet45 | a0.3 | boulevard | 24 | 0.02 |
| quiet45 | restart+warm | bayside | 24 | 0.0222 |
| quiet45 | restart+warm | blocks | 24 | 0.0335 |
| quiet45 | restart+warm | boulevard | 24 | 0.0195 |
| quiet45 | warm | bayside | 24 | 0.0248 |
| quiet45 | warm | blocks | 24 | 0.0345 |
| quiet45 | warm | boulevard | 24 | 0.0195 |
| quiet90 | a0.3 | bayside | 24 | 0.0239 |
| quiet90 | a0.3 | blocks | 24 | 0.0344 |
| quiet90 | a0.3 | boulevard | 24 | 0.02 |
| quiet90 | restart+warm | bayside | 24 | 0.022 |
| quiet90 | restart+warm | blocks | 24 | 0.0332 |
| quiet90 | restart+warm | boulevard | 24 | 0.0195 |
| quiet90 | warm | bayside | 24 | 0.0234 |
| quiet90 | warm | blocks | 24 | 0.0337 |
| quiet90 | warm | boulevard | 24 | 0.0195 |
| quietdrift90 | a0.3 | bayside | 24 | 0.029 |
| quietdrift90 | a0.3 | blocks | 24 | 0.0389 |
| quietdrift90 | a0.3 | boulevard | 24 | 0.0252 |
| quietdrift90 | restart+warm | bayside | 24 | 0.0268 |
| quietdrift90 | restart+warm | blocks | 24 | 0.0376 |
| quietdrift90 | restart+warm | boulevard | 24 | 0.0251 |
| quietdrift90 | warm | bayside | 24 | 0.0285 |
| quietdrift90 | warm | blocks | 24 | 0.0387 |
| quietdrift90 | warm | boulevard | 24 | 0.0248 |
