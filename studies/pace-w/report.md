# Starting the GPS average again after a gap, with the stuck check's warm-up (simulated)

pace_w.py 0.1.0 (pace_v.py 0.1.0, pace_u.py 0.1.0, pace_s.py 0.1.0, pace_q.py 0.1.0, pace_p.py 0.1.0, rover_pilot.py 0.19.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot with v0.19.0's 10 s warm-up for the stuck check after every clear of its history (warm10), with the GPS average as it ships or started again from the fix after more than 3 s without one (restart+warm10). Profiles: outage90, quiet90, quietdrift90, quiet45, blockedstart and blockedmid as in pace-v. Seeds 445-468; warm10:B is warm10 on seeds 469-492, for the seed-to-seed spread. 1296 of 1296 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_v.py's warm10 and pace_s.py's restart runs: 7 compared, 7 identical.

## Tolerances from the spread between the two seed sets of warm10

| figure | spread m | tolerance m |
|---|---|---|
| blocks corner p95 | 0.73 | 0.75 |
| p95 offset | 0.77 | 0.8 |

## The pilot's worst idea of where it is, per mission (over 20 m: thrown off)

| profile | variant | course | missions | median of max m | largest m | missions over 20 m |
|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 10.1 | 29.65 | 1 |
| blockedmid | restart+warm10 | blocks | 24 | 10.21 | 26.34 | 1 |
| blockedmid | restart+warm10 | boulevard | 24 | 10.29 | 29.6 | 1 |
| blockedmid | warm10 | bayside | 24 | 61.72 | 64.84 | 22 |
| blockedmid | warm10 | blocks | 24 | 56.31 | 62.33 | 23 |
| blockedmid | warm10 | boulevard | 24 | 63.01 | 102.15 | 23 |
| blockedmid | warm10:B | bayside | 24 | 60.88 | 63.07 | 19 |
| blockedmid | warm10:B | blocks | 24 | 55.99 | 62.43 | 20 |
| blockedmid | warm10:B | boulevard | 24 | 63.2 | 68.24 | 20 |
| blockedstart | restart+warm10 | bayside | 24 | 10.09 | 11.11 | 0 |
| blockedstart | restart+warm10 | blocks | 24 | 10.0 | 11.07 | 0 |
| blockedstart | restart+warm10 | boulevard | 24 | 10.12 | 11.08 | 0 |
| blockedstart | warm10 | bayside | 24 | 61.96 | 64.84 | 23 |
| blockedstart | warm10 | blocks | 24 | 57.45 | 63.41 | 23 |
| blockedstart | warm10 | boulevard | 24 | 63.03 | 101.8 | 23 |
| blockedstart | warm10:B | bayside | 24 | 62.04 | 63.42 | 19 |
| blockedstart | warm10:B | blocks | 24 | 56.66 | 61.97 | 20 |
| blockedstart | warm10:B | boulevard | 24 | 63.23 | 68.83 | 20 |
| outage90 | restart+warm10 | bayside | 24 | 10.37 | 11.26 | 0 |
| outage90 | restart+warm10 | blocks | 24 | 10.6 | 11.37 | 0 |
| outage90 | restart+warm10 | boulevard | 24 | 10.72 | 11.74 | 0 |
| outage90 | warm10 | bayside | 24 | 61.64 | 65.55 | 20 |
| outage90 | warm10 | blocks | 24 | 54.33 | 62.98 | 24 |
| outage90 | warm10 | boulevard | 24 | 62.98 | 101.47 | 24 |
| outage90 | warm10:B | bayside | 24 | 61.68 | 63.19 | 19 |
| outage90 | warm10:B | blocks | 24 | 57.89 | 63.27 | 20 |
| outage90 | warm10:B | boulevard | 24 | 63.57 | 66.0 | 20 |
| quiet45 | restart+warm10 | bayside | 24 | 10.25 | 10.66 | 0 |
| quiet45 | restart+warm10 | blocks | 24 | 10.13 | 11.23 | 0 |
| quiet45 | restart+warm10 | boulevard | 24 | 10.37 | 11.05 | 0 |
| quiet45 | warm10 | bayside | 24 | 35.55 | 61.07 | 24 |
| quiet45 | warm10 | blocks | 24 | 35.35 | 53.37 | 24 |
| quiet45 | warm10 | boulevard | 24 | 36.55 | 64.13 | 24 |
| quiet45 | warm10:B | bayside | 24 | 35.56 | 44.35 | 24 |
| quiet45 | warm10:B | blocks | 24 | 35.48 | 41.49 | 24 |
| quiet45 | warm10:B | boulevard | 24 | 36.36 | 45.02 | 24 |
| quiet90 | restart+warm10 | bayside | 24 | 10.1 | 10.63 | 0 |
| quiet90 | restart+warm10 | blocks | 24 | 10.03 | 11.0 | 0 |
| quiet90 | restart+warm10 | boulevard | 24 | 10.19 | 11.08 | 0 |
| quiet90 | warm10 | bayside | 24 | 61.98 | 64.85 | 21 |
| quiet90 | warm10 | blocks | 24 | 51.62 | 61.74 | 24 |
| quiet90 | warm10 | boulevard | 24 | 63.08 | 101.8 | 24 |
| quiet90 | warm10:B | bayside | 24 | 61.88 | 63.29 | 19 |
| quiet90 | warm10:B | blocks | 24 | 56.89 | 62.43 | 20 |
| quiet90 | warm10:B | boulevard | 24 | 63.2 | 66.9 | 20 |
| quietdrift90 | restart+warm10 | bayside | 24 | 10.61 | 22.16 | 2 |
| quietdrift90 | restart+warm10 | blocks | 24 | 11.24 | 20.64 | 1 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 11.37 | 22.38 | 3 |
| quietdrift90 | warm10 | bayside | 24 | 61.66 | 64.21 | 21 |
| quietdrift90 | warm10 | blocks | 24 | 54.53 | 62.71 | 24 |
| quietdrift90 | warm10 | boulevard | 24 | 62.97 | 100.8 | 24 |
| quietdrift90 | warm10:B | bayside | 24 | 61.69 | 63.96 | 19 |
| quietdrift90 | warm10:B | blocks | 24 | 55.91 | 63.08 | 20 |
| quietdrift90 | warm10:B | boulevard | 24 | 63.02 | 66.47 | 20 |

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | warm10 | 72/72 | 0.88 | 0.99 | 72 | 0.998 | 0.021 |
| outage90 | restart+warm10 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.019 |
| outage90 | warm10:B | 72/72 | 0.879 | 0.989 | 72 | 0.998 | 0.026 |
| quiet90 | warm10 | 72/72 | 0.885 | 0.995 | 72 | 0.997 | 0.021 |
| quiet90 | restart+warm10 | 72/72 | 0.889 | 1.0 | 72 | 0.995 | 0.02 |
| quiet90 | warm10:B | 72/72 | 0.883 | 0.994 | 72 | 0.997 | 0.024 |
| quietdrift90 | warm10 | 72/72 | 0.878 | 0.988 | 72 | 1.002 | 0.019 |
| quietdrift90 | restart+warm10 | 72/72 | 0.881 | 0.991 | 72 | 1.0 | 0.019 |
| quietdrift90 | warm10:B | 72/72 | 0.868 | 0.977 | 72 | 1.002 | 0.026 |
| quiet45 | warm10 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.012 |
| quiet45 | restart+warm10 | 72/72 | 0.889 | 1.0 | 72 | 0.995 | 0.012 |
| quiet45 | warm10:B | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.013 |
| blockedstart | warm10 | 72/72 | 0.857 | 0.964 | 72 | 0.997 | 0.022 |
| blockedstart | restart+warm10 | 72/72 | 0.859 | 0.967 | 72 | 0.996 | 0.022 |
| blockedstart | warm10:B | 72/72 | 0.852 | 0.959 | 72 | 0.997 | 0.025 |
| blockedmid | warm10 | 72/72 | 0.856 | 0.963 | 72 | 0.997 | 0.019 |
| blockedmid | restart+warm10 | 72/72 | 0.857 | 0.964 | 72 | 0.996 | 0.02 |
| blockedmid | warm10:B | 72/72 | 0.851 | 0.957 | 71 | 0.998 | 0.024 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0087 |
| blockedstart | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0086 |
| outage90 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0088 |
| quiet45 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0057 |
| quiet90 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0076 |
| quietdrift90 | restart+warm10 | warm10 | 2/3 | 1 | 0 | 0 | -0.0088 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | warm10 | bayside | 10 | 0 | 0.0 | 0.0 | 0.002 |
| blockedmid | restart+warm10 | warm10 | blocks | 21 | 0 | -14.0 | -0.0087 | 0.0 |
| blockedmid | restart+warm10 | warm10 | boulevard | 3 | 0 | 0.0 | 0.0 | 0.25 |
| blockedstart | restart+warm10 | warm10 | bayside | 12 | 0 | -1.0 | -0.0007 | 0.0005 |
| blockedstart | restart+warm10 | warm10 | blocks | 22 | 0 | -14.0 | -0.0086 | 0.0 |
| blockedstart | restart+warm10 | warm10 | boulevard | 4 | 0 | 0.0 | 0.0 | 0.125 |
| outage90 | restart+warm10 | warm10 | bayside | 16 | 0 | -4.0 | -0.0028 | 0.0 |
| outage90 | restart+warm10 | warm10 | blocks | 21 | 0 | -14.0 | -0.0088 | 0.0 |
| outage90 | restart+warm10 | warm10 | boulevard | 2 | 4 | 0.0 | 0.0 | 0.6875 |
| quiet45 | restart+warm10 | warm10 | bayside | 19 | 0 | -4.0 | -0.0028 | 0.0 |
| quiet45 | restart+warm10 | warm10 | blocks | 19 | 0 | -9.0 | -0.0057 | 0.0 |
| quiet45 | restart+warm10 | warm10 | boulevard | 3 | 0 | 0.0 | 0.0 | 0.25 |
| quiet90 | restart+warm10 | warm10 | bayside | 16 | 0 | -4.0 | -0.0028 | 0.0 |
| quiet90 | restart+warm10 | warm10 | blocks | 20 | 0 | -12.0 | -0.0076 | 0.0 |
| quiet90 | restart+warm10 | warm10 | boulevard | 2 | 0 | 0.0 | 0.0 | 0.5 |
| quietdrift90 | restart+warm10 | warm10 | bayside | 17 | 0 | -4.0 | -0.0028 | 0.0 |
| quietdrift90 | restart+warm10 | warm10 | blocks | 22 | 0 | -14.0 | -0.0088 | 0.0 |
| quietdrift90 | restart+warm10 | warm10 | boulevard | 1 | 14 | 2.0 | 0.0011 | 0.001 |

## Blocked rovers (caught: a recovery move within 30 s of the block's start; eligible: no outage and no stand in that time; post: moves within 10 s after the block)

| profile | variant | course | missions | eligible | caught | missed | caught at all | median catch s | latest catch s | post moves | missions with one |
|---|---|---|---|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 22 | 22 | 0 | 23 | 16.5 | 18.8 | 7 | 7 |
| blockedmid | restart+warm10 | blocks | 24 | 22 | 22 | 0 | 23 | 16.5 | 18.8 | 7 | 7 |
| blockedmid | restart+warm10 | boulevard | 24 | 22 | 22 | 0 | 23 | 16.5 | 18.8 | 7 | 7 |
| blockedmid | warm10 | bayside | 24 | 22 | 22 | 0 | 23 | 16.6 | 18.8 | 7 | 7 |
| blockedmid | warm10 | blocks | 24 | 22 | 22 | 0 | 23 | 16.6 | 18.8 | 7 | 7 |
| blockedmid | warm10 | boulevard | 24 | 22 | 22 | 0 | 23 | 16.6 | 18.8 | 7 | 7 |
| blockedmid | warm10:B | bayside | 24 | 22 | 22 | 0 | 23 | 17.4 | 22.6 | 10 | 10 |
| blockedmid | warm10:B | blocks | 24 | 22 | 22 | 0 | 23 | 16.9 | 20.6 | 10 | 10 |
| blockedmid | warm10:B | boulevard | 24 | 22 | 22 | 0 | 23 | 17.4 | 22.6 | 10 | 10 |
| blockedstart | restart+warm10 | bayside | 24 | 22 | 22 | 0 | 22 | 19.1 | 29.0 | 4 | 4 |
| blockedstart | restart+warm10 | blocks | 24 | 22 | 22 | 0 | 22 | 19.1 | 29.0 | 4 | 4 |
| blockedstart | restart+warm10 | boulevard | 24 | 22 | 22 | 0 | 22 | 19.1 | 29.0 | 4 | 4 |
| blockedstart | warm10 | bayside | 24 | 22 | 22 | 0 | 22 | 19.1 | 29.0 | 4 | 4 |
| blockedstart | warm10 | blocks | 24 | 22 | 22 | 0 | 22 | 19.1 | 29.0 | 4 | 4 |
| blockedstart | warm10 | boulevard | 24 | 22 | 22 | 0 | 22 | 19.1 | 29.0 | 4 | 4 |
| blockedstart | warm10:B | bayside | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 5 | 5 |
| blockedstart | warm10:B | blocks | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 5 | 5 |
| blockedstart | warm10:B | boulevard | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 5 | 5 |

## Recovery moves (first before 30 s: at the start; late: moves at or after 30 s)

| profile | variant | course | missions | with a recovery | recoveries | first before 30 s | late | stands | median first s | latest first s |
|---|---|---|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 23 | 41 | 0 | 41 | 12 | 433.9 | 595.9 |
| blockedmid | restart+warm10 | blocks | 24 | 23 | 41 | 0 | 41 | 11 | 433.9 | 595.9 |
| blockedmid | restart+warm10 | boulevard | 24 | 23 | 41 | 0 | 41 | 10 | 433.9 | 595.9 |
| blockedmid | warm10 | bayside | 24 | 23 | 41 | 0 | 41 | 12 | 433.9 | 595.9 |
| blockedmid | warm10 | blocks | 24 | 23 | 41 | 0 | 41 | 12 | 433.9 | 595.9 |
| blockedmid | warm10 | boulevard | 24 | 23 | 41 | 0 | 41 | 10 | 433.9 | 595.9 |
| blockedmid | warm10:B | bayside | 24 | 23 | 41 | 0 | 41 | 17 | 449.9 | 617.9 |
| blockedmid | warm10:B | blocks | 24 | 23 | 41 | 0 | 41 | 23 | 449.9 | 617.9 |
| blockedmid | warm10:B | boulevard | 24 | 23 | 41 | 0 | 41 | 12 | 449.9 | 617.9 |
| blockedstart | restart+warm10 | bayside | 24 | 22 | 39 | 22 | 17 | 11 | 19.1 | 29.0 |
| blockedstart | restart+warm10 | blocks | 24 | 22 | 39 | 22 | 17 | 14 | 19.1 | 29.0 |
| blockedstart | restart+warm10 | boulevard | 24 | 22 | 39 | 22 | 17 | 11 | 19.1 | 29.0 |
| blockedstart | warm10 | bayside | 24 | 22 | 39 | 22 | 17 | 11 | 19.1 | 29.0 |
| blockedstart | warm10 | blocks | 24 | 22 | 39 | 22 | 17 | 14 | 19.1 | 29.0 |
| blockedstart | warm10 | boulevard | 24 | 22 | 39 | 22 | 17 | 11 | 19.1 | 29.0 |
| blockedstart | warm10:B | bayside | 24 | 21 | 36 | 21 | 15 | 16 | 19.1 | 21.1 |
| blockedstart | warm10:B | blocks | 24 | 21 | 36 | 21 | 15 | 22 | 19.1 | 21.1 |
| blockedstart | warm10:B | boulevard | 24 | 21 | 36 | 21 | 15 | 9 | 19.1 | 21.1 |
| outage90 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 9 | None | None |
| outage90 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| outage90 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 12 | None | None |
| outage90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| outage90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 18 | None | None |
| outage90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 12 | None | None |
| outage90 | warm10:B | bayside | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| outage90 | warm10:B | blocks | 24 | 0 | 0 | 0 | 0 | 17 | None | None |
| outage90 | warm10:B | boulevard | 24 | 0 | 0 | 0 | 0 | 8 | None | None |
| quiet45 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quiet45 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 13 | None | None |
| quiet45 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quiet45 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quiet45 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 15 | None | None |
| quiet45 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quiet45 | warm10:B | bayside | 24 | 0 | 0 | 0 | 0 | 21 | None | None |
| quiet45 | warm10:B | blocks | 24 | 0 | 0 | 0 | 0 | 15 | None | None |
| quiet45 | warm10:B | boulevard | 24 | 0 | 0 | 0 | 0 | 7 | None | None |
| quiet90 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 9 | None | None |
| quiet90 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 15 | None | None |
| quiet90 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 10 | None | None |
| quiet90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 10 | None | None |
| quiet90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quiet90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 10 | None | None |
| quiet90 | warm10:B | bayside | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quiet90 | warm10:B | blocks | 24 | 0 | 0 | 0 | 0 | 17 | None | None |
| quiet90 | warm10:B | boulevard | 24 | 0 | 0 | 0 | 0 | 7 | None | None |
| quietdrift90 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 10 | None | None |
| quietdrift90 | restart+warm10 | blocks | 24 | 1 | 1 | 0 | 1 | 16 | 703.0 | 703.0 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 12 | None | None |
| quietdrift90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quietdrift90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quietdrift90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 12 | None | None |
| quietdrift90 | warm10:B | bayside | 24 | 0 | 0 | 0 | 0 | 17 | None | None |
| quietdrift90 | warm10:B | blocks | 24 | 0 | 0 | 0 | 0 | 19 | None | None |
| quietdrift90 | warm10:B | boulevard | 24 | 0 | 0 | 0 | 0 | 8 | None | None |

## Recovery moves and filter restarts (medians)

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 2.0 | 4.0 |
| blockedmid | restart+warm10 | blocks | 24 | 2.0 | 4.0 |
| blockedmid | restart+warm10 | boulevard | 24 | 2.0 | 5.0 |
| blockedmid | warm10 | bayside | 24 | 2.0 | None |
| blockedmid | warm10 | blocks | 24 | 2.0 | None |
| blockedmid | warm10 | boulevard | 24 | 2.0 | None |
| blockedmid | warm10:B | bayside | 24 | 2.0 | None |
| blockedmid | warm10:B | blocks | 24 | 2.0 | None |
| blockedmid | warm10:B | boulevard | 24 | 2.0 | None |
| blockedstart | restart+warm10 | bayside | 24 | 2.0 | 4.0 |
| blockedstart | restart+warm10 | blocks | 24 | 2.0 | 4.0 |
| blockedstart | restart+warm10 | boulevard | 24 | 2.0 | 5.0 |
| blockedstart | warm10 | bayside | 24 | 2.0 | None |
| blockedstart | warm10 | blocks | 24 | 2.0 | None |
| blockedstart | warm10 | boulevard | 24 | 2.0 | None |
| blockedstart | warm10:B | bayside | 24 | 2.0 | None |
| blockedstart | warm10:B | blocks | 24 | 2.0 | None |
| blockedstart | warm10:B | boulevard | 24 | 2.0 | None |
| outage90 | restart+warm10 | bayside | 24 | 0.0 | 4.0 |
| outage90 | restart+warm10 | blocks | 24 | 0.0 | 4.0 |
| outage90 | restart+warm10 | boulevard | 24 | 0.0 | 4.5 |
| outage90 | warm10 | bayside | 24 | 0.0 | None |
| outage90 | warm10 | blocks | 24 | 0.0 | None |
| outage90 | warm10 | boulevard | 24 | 0.0 | None |
| outage90 | warm10:B | bayside | 24 | 0.0 | None |
| outage90 | warm10:B | blocks | 24 | 0.0 | None |
| outage90 | warm10:B | boulevard | 24 | 0.0 | None |
| quiet45 | restart+warm10 | bayside | 24 | 0.0 | 5.5 |
| quiet45 | restart+warm10 | blocks | 24 | 0.0 | 6.0 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.0 | 7.0 |
| quiet45 | warm10 | bayside | 24 | 0.0 | None |
| quiet45 | warm10 | blocks | 24 | 0.0 | None |
| quiet45 | warm10 | boulevard | 24 | 0.0 | None |
| quiet45 | warm10:B | bayside | 24 | 0.0 | None |
| quiet45 | warm10:B | blocks | 24 | 0.0 | None |
| quiet45 | warm10:B | boulevard | 24 | 0.0 | None |
| quiet90 | restart+warm10 | bayside | 24 | 0.0 | 4.0 |
| quiet90 | restart+warm10 | blocks | 24 | 0.0 | 4.0 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.0 | 4.0 |
| quiet90 | warm10 | bayside | 24 | 0.0 | None |
| quiet90 | warm10 | blocks | 24 | 0.0 | None |
| quiet90 | warm10 | boulevard | 24 | 0.0 | None |
| quiet90 | warm10:B | bayside | 24 | 0.0 | None |
| quiet90 | warm10:B | blocks | 24 | 0.0 | None |
| quiet90 | warm10:B | boulevard | 24 | 0.0 | None |
| quietdrift90 | restart+warm10 | bayside | 24 | 0.0 | 4.0 |
| quietdrift90 | restart+warm10 | blocks | 24 | 0.0 | 4.0 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 0.0 | 4.5 |
| quietdrift90 | warm10 | bayside | 24 | 0.0 | None |
| quietdrift90 | warm10 | blocks | 24 | 0.0 | None |
| quietdrift90 | warm10 | boulevard | 24 | 0.0 | None |
| quietdrift90 | warm10:B | bayside | 24 | 0.0 | None |
| quietdrift90 | warm10:B | blocks | 24 | 0.0 | None |
| quietdrift90 | warm10:B | boulevard | 24 | 0.0 | None |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| warm10 | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0294 |
| warm10 | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0308 |
| restart+warm10 | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0317 |
| restart+warm10 | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0345 |
| warm10:B | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0252 |
| warm10:B | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0289 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 6.25 | 7.84 |
| blockedmid | restart+warm10 | blocks | 24 | 6.14 | 7.72 |
| blockedmid | restart+warm10 | boulevard | 24 | 6.28 | 7.8 |
| blockedmid | warm10 | bayside | 24 | 6.33 | 8.32 |
| blockedmid | warm10 | blocks | 24 | 6.22 | 8.2 |
| blockedmid | warm10 | boulevard | 24 | 6.35 | 8.5 |
| blockedmid | warm10:B | bayside | 24 | 6.3 | 8.34 |
| blockedmid | warm10:B | blocks | 24 | 6.21 | 8.34 |
| blockedmid | warm10:B | boulevard | 24 | 6.33 | 8.6 |
| blockedstart | restart+warm10 | bayside | 24 | 6.35 | 7.92 |
| blockedstart | restart+warm10 | blocks | 24 | 6.27 | 7.84 |
| blockedstart | restart+warm10 | boulevard | 24 | 6.38 | 7.93 |
| blockedstart | warm10 | bayside | 24 | 6.46 | 8.52 |
| blockedstart | warm10 | blocks | 24 | 6.34 | 8.28 |
| blockedstart | warm10 | boulevard | 24 | 6.5 | 8.54 |
| blockedstart | warm10:B | bayside | 24 | 6.47 | 8.57 |
| blockedstart | warm10:B | blocks | 24 | 6.33 | 8.29 |
| blockedstart | warm10:B | boulevard | 24 | 6.49 | 8.74 |
| outage90 | restart+warm10 | bayside | 24 | 6.29 | 8.11 |
| outage90 | restart+warm10 | blocks | 24 | 6.33 | 8.16 |
| outage90 | restart+warm10 | boulevard | 24 | 6.39 | 8.25 |
| outage90 | warm10 | bayside | 24 | 6.41 | 8.62 |
| outage90 | warm10 | blocks | 24 | 6.46 | 8.55 |
| outage90 | warm10 | boulevard | 24 | 6.5 | 8.89 |
| outage90 | warm10:B | bayside | 24 | 6.44 | 8.89 |
| outage90 | warm10:B | blocks | 24 | 6.44 | 8.69 |
| outage90 | warm10:B | boulevard | 24 | 6.56 | 8.87 |
| quiet45 | restart+warm10 | bayside | 24 | 6.28 | 7.86 |
| quiet45 | restart+warm10 | blocks | 24 | 6.24 | 7.91 |
| quiet45 | restart+warm10 | boulevard | 24 | 6.33 | 7.99 |
| quiet45 | warm10 | bayside | 24 | 6.46 | 8.95 |
| quiet45 | warm10 | blocks | 24 | 6.41 | 8.9 |
| quiet45 | warm10 | boulevard | 24 | 6.54 | 9.16 |
| quiet45 | warm10:B | bayside | 24 | 6.47 | 9.14 |
| quiet45 | warm10:B | blocks | 24 | 6.38 | 8.98 |
| quiet45 | warm10:B | boulevard | 24 | 6.51 | 9.23 |
| quiet90 | restart+warm10 | bayside | 24 | 6.35 | 7.85 |
| quiet90 | restart+warm10 | blocks | 24 | 6.29 | 7.86 |
| quiet90 | restart+warm10 | boulevard | 24 | 6.41 | 7.98 |
| quiet90 | warm10 | bayside | 24 | 6.47 | 8.39 |
| quiet90 | warm10 | blocks | 24 | 6.42 | 8.25 |
| quiet90 | warm10 | boulevard | 24 | 6.53 | 8.54 |
| quiet90 | warm10:B | bayside | 24 | 6.46 | 8.52 |
| quiet90 | warm10:B | blocks | 24 | 6.36 | 8.48 |
| quiet90 | warm10:B | boulevard | 24 | 6.49 | 8.73 |
| quietdrift90 | restart+warm10 | bayside | 24 | 6.44 | 8.08 |
| quietdrift90 | restart+warm10 | blocks | 24 | 6.33 | 8.05 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 6.45 | 8.18 |
| quietdrift90 | warm10 | bayside | 24 | 6.49 | 8.66 |
| quietdrift90 | warm10 | blocks | 24 | 6.41 | 8.46 |
| quietdrift90 | warm10 | boulevard | 24 | 6.58 | 8.87 |
| quietdrift90 | warm10:B | bayside | 24 | 6.5 | 8.83 |
| quietdrift90 | warm10:B | blocks | 24 | 6.46 | 8.68 |
| quietdrift90 | warm10:B | boulevard | 24 | 6.58 | 9.2 |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | blocks | 24 | 9.0 | 0.91 | 2.87 | 4.67 | 1.92 | 2.78 |
| blockedmid | warm10 | blocks | 24 | 9.0 | 0.93 | 3.11 | 4.84 | 1.98 | 3.63 |
| blockedmid | warm10:B | blocks | 24 | 9.0 | 0.81 | 2.65 | 4.67 | 1.96 | 2.83 |
| blockedstart | restart+warm10 | blocks | 24 | 9.0 | 0.87 | 2.62 | 4.58 | 1.9 | 2.69 |
| blockedstart | warm10 | blocks | 24 | 9.0 | 0.9 | 2.78 | 4.64 | 1.98 | 3.14 |
| blockedstart | warm10:B | blocks | 24 | 9.0 | 0.89 | 2.75 | 4.67 | 2.01 | 3.02 |
| outage90 | restart+warm10 | blocks | 24 | 9.0 | 1.1 | 3.18 | 5.59 | 1.98 | 3.19 |
| outage90 | warm10 | blocks | 24 | 9.0 | 1.08 | 3.53 | 6.2 | 2.06 | 3.26 |
| outage90 | warm10:B | blocks | 24 | 9.0 | 1.17 | 4.26 | 6.96 | 2.26 | 4.21 |
| quiet45 | restart+warm10 | blocks | 24 | 9.0 | 0.8 | 2.78 | 4.56 | 1.96 | 2.79 |
| quiet45 | warm10 | blocks | 24 | 9.0 | 0.86 | 2.87 | 4.56 | 2.01 | 3.21 |
| quiet45 | warm10:B | blocks | 24 | 9.0 | 0.81 | 2.85 | 4.62 | 1.99 | 3.04 |
| quiet90 | restart+warm10 | blocks | 24 | 9.0 | 0.9 | 2.83 | 4.78 | 1.92 | 2.77 |
| quiet90 | warm10 | blocks | 24 | 9.0 | 0.92 | 2.98 | 4.92 | 1.94 | 2.9 |
| quiet90 | warm10:B | blocks | 24 | 9.0 | 0.94 | 3.01 | 4.99 | 2.11 | 3.58 |
| quietdrift90 | restart+warm10 | blocks | 24 | 9.0 | 1.6 | 4.45 | 6.51 | 2.08 | 4.72 |
| quietdrift90 | warm10 | blocks | 24 | 9.0 | 1.73 | 4.83 | 7.24 | 2.2 | 5.13 |
| quietdrift90 | warm10:B | blocks | 24 | 9.0 | 1.65 | 5.33 | 6.88 | 2.29 | 5.13 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 0.21 | 1.21 |
| blockedmid | restart+warm10 | blocks | 24 | 0.3 | 2.51 |
| blockedmid | restart+warm10 | boulevard | 24 | 0.13 | 0.63 |
| blockedmid | warm10 | bayside | 24 | 0.22 | 1.66 |
| blockedmid | warm10 | blocks | 24 | 0.32 | 2.81 |
| blockedmid | warm10 | boulevard | 24 | 0.14 | 0.65 |
| blockedmid | warm10:B | bayside | 24 | 0.21 | 2.06 |
| blockedmid | warm10:B | blocks | 24 | 0.3 | 2.96 |
| blockedmid | warm10:B | boulevard | 24 | 0.15 | 0.89 |
| blockedstart | restart+warm10 | bayside | 24 | 0.2 | 1.23 |
| blockedstart | restart+warm10 | blocks | 24 | 0.27 | 2.33 |
| blockedstart | restart+warm10 | boulevard | 24 | 0.13 | 0.74 |
| blockedstart | warm10 | bayside | 24 | 0.2 | 1.81 |
| blockedstart | warm10 | blocks | 24 | 0.3 | 2.77 |
| blockedstart | warm10 | boulevard | 24 | 0.14 | 0.83 |
| blockedstart | warm10:B | bayside | 24 | 0.21 | 1.69 |
| blockedstart | warm10:B | blocks | 24 | 0.3 | 2.73 |
| blockedstart | warm10:B | boulevard | 24 | 0.14 | 0.8 |
| outage90 | restart+warm10 | bayside | 24 | 0.55 | 3.08 |
| outage90 | restart+warm10 | blocks | 24 | 0.78 | 3.48 |
| outage90 | restart+warm10 | boulevard | 24 | 0.6 | 2.84 |
| outage90 | warm10 | bayside | 24 | 0.56 | 3.92 |
| outage90 | warm10 | blocks | 24 | 0.78 | 4.08 |
| outage90 | warm10 | boulevard | 24 | 0.65 | 3.1 |
| outage90 | warm10:B | bayside | 24 | 0.57 | 3.65 |
| outage90 | warm10:B | blocks | 24 | 0.83 | 4.16 |
| outage90 | warm10:B | boulevard | 24 | 0.62 | 3.16 |
| quiet45 | restart+warm10 | bayside | 24 | 0.21 | 1.48 |
| quiet45 | restart+warm10 | blocks | 24 | 0.29 | 2.48 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.14 | 0.72 |
| quiet45 | warm10 | bayside | 24 | 0.23 | 1.91 |
| quiet45 | warm10 | blocks | 24 | 0.34 | 2.76 |
| quiet45 | warm10 | boulevard | 24 | 0.17 | 0.81 |
| quiet45 | warm10:B | bayside | 24 | 0.23 | 1.83 |
| quiet45 | warm10:B | blocks | 24 | 0.32 | 2.84 |
| quiet45 | warm10:B | boulevard | 24 | 0.14 | 0.81 |
| quiet90 | restart+warm10 | bayside | 24 | 0.21 | 1.21 |
| quiet90 | restart+warm10 | blocks | 24 | 0.31 | 2.45 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.14 | 0.64 |
| quiet90 | warm10 | bayside | 24 | 0.21 | 1.95 |
| quiet90 | warm10 | blocks | 24 | 0.32 | 3.0 |
| quiet90 | warm10 | boulevard | 24 | 0.15 | 0.79 |
| quiet90 | warm10:B | bayside | 24 | 0.21 | 2.17 |
| quiet90 | warm10:B | blocks | 24 | 0.32 | 3.25 |
| quiet90 | warm10:B | boulevard | 24 | 0.14 | 0.76 |
| quietdrift90 | restart+warm10 | bayside | 24 | 1.43 | 5.75 |
| quietdrift90 | restart+warm10 | blocks | 24 | 1.58 | 5.2 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 1.44 | 5.58 |
| quietdrift90 | warm10 | bayside | 24 | 1.44 | 6.27 |
| quietdrift90 | warm10 | blocks | 24 | 1.75 | 5.46 |
| quietdrift90 | warm10 | boulevard | 24 | 1.5 | 6.54 |
| quietdrift90 | warm10:B | bayside | 24 | 1.47 | 6.41 |
| quietdrift90 | warm10:B | blocks | 24 | 1.74 | 6.23 |
| quietdrift90 | warm10:B | boulevard | 24 | 1.79 | 7.16 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 6.55 | 7.07 | 0 | 0 |
| blockedmid | restart+warm10 | blocks | 24 | 6.94 | 13.69 | 0 | 0 |
| blockedmid | restart+warm10 | boulevard | 24 | 6.96 | 7.54 | 0 | 0 |
| blockedmid | warm10 | bayside | 24 | 6.55 | 7.78 | 0 | 0 |
| blockedmid | warm10 | blocks | 24 | 7.08 | 21.78 | 0 | 0 |
| blockedmid | warm10 | boulevard | 24 | 6.98 | 7.77 | 0 | 0 |
| blockedmid | warm10:B | bayside | 24 | 6.88 | 7.62 | 0 | 0 |
| blockedmid | warm10:B | blocks | 24 | 7.38 | 18.7 | 0 | 0 |
| blockedmid | warm10:B | boulevard | 24 | 7.0 | 7.69 | 0 | 0 |
| blockedstart | restart+warm10 | bayside | 24 | 6.41 | 7.32 | 0 | 0 |
| blockedstart | restart+warm10 | blocks | 24 | 6.79 | 7.33 | 0 | 0 |
| blockedstart | restart+warm10 | boulevard | 24 | 6.81 | 7.21 | 0 | 0 |
| blockedstart | warm10 | bayside | 24 | 6.47 | 8.23 | 0 | 0 |
| blockedstart | warm10 | blocks | 24 | 6.88 | 12.03 | 0 | 0 |
| blockedstart | warm10 | boulevard | 24 | 6.81 | 7.47 | 0 | 0 |
| blockedstart | warm10:B | bayside | 24 | 6.51 | 6.94 | 0 | 0 |
| blockedstart | warm10:B | blocks | 24 | 6.93 | 11.86 | 0 | 0 |
| blockedstart | warm10:B | boulevard | 24 | 6.75 | 7.22 | 0 | 0 |
| outage90 | restart+warm10 | bayside | 24 | 6.56 | 8.8 | 0 | 0 |
| outage90 | restart+warm10 | blocks | 24 | 7.2 | 9.13 | 0 | 0 |
| outage90 | restart+warm10 | boulevard | 24 | 6.74 | 10.7 | 0 | 0 |
| outage90 | warm10 | bayside | 24 | 7.09 | 12.55 | 0 | 0 |
| outage90 | warm10 | blocks | 24 | 7.79 | 11.48 | 0 | 0 |
| outage90 | warm10 | boulevard | 24 | 6.62 | 10.84 | 0 | 0 |
| outage90 | warm10:B | bayside | 24 | 7.22 | 13.96 | 0 | 0 |
| outage90 | warm10:B | blocks | 24 | 7.76 | 13.68 | 0 | 0 |
| outage90 | warm10:B | boulevard | 24 | 7.12 | 9.55 | 0 | 0 |
| quiet45 | restart+warm10 | bayside | 24 | 6.55 | 7.07 | 0 | 0 |
| quiet45 | restart+warm10 | blocks | 24 | 6.94 | 7.36 | 0 | 0 |
| quiet45 | restart+warm10 | boulevard | 24 | 6.96 | 7.54 | 0 | 0 |
| quiet45 | warm10 | bayside | 24 | 6.55 | 7.78 | 0 | 0 |
| quiet45 | warm10 | blocks | 24 | 6.96 | 7.68 | 0 | 0 |
| quiet45 | warm10 | boulevard | 24 | 6.98 | 7.77 | 0 | 0 |
| quiet45 | warm10:B | bayside | 24 | 6.84 | 7.72 | 0 | 0 |
| quiet45 | warm10:B | blocks | 24 | 7.0 | 7.89 | 0 | 0 |
| quiet45 | warm10:B | boulevard | 24 | 7.0 | 7.69 | 0 | 0 |
| quiet90 | restart+warm10 | bayside | 24 | 6.55 | 7.07 | 0 | 0 |
| quiet90 | restart+warm10 | blocks | 24 | 6.94 | 7.36 | 0 | 0 |
| quiet90 | restart+warm10 | boulevard | 24 | 6.96 | 7.54 | 0 | 0 |
| quiet90 | warm10 | bayside | 24 | 6.56 | 8.41 | 0 | 0 |
| quiet90 | warm10 | blocks | 24 | 7.08 | 12.08 | 0 | 0 |
| quiet90 | warm10 | boulevard | 24 | 6.98 | 7.77 | 0 | 0 |
| quiet90 | warm10:B | bayside | 24 | 6.94 | 7.62 | 0 | 0 |
| quiet90 | warm10:B | blocks | 24 | 7.35 | 9.08 | 0 | 0 |
| quiet90 | warm10:B | boulevard | 24 | 7.0 | 7.69 | 0 | 0 |
| quietdrift90 | restart+warm10 | bayside | 24 | 9.8 | 22.29 | 0 | 0 |
| quietdrift90 | restart+warm10 | blocks | 24 | 10.23 | 15.72 | 0 | 0 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 11.38 | 22.3 | 0 | 0 |
| quietdrift90 | warm10 | bayside | 24 | 11.12 | 22.28 | 0 | 0 |
| quietdrift90 | warm10 | blocks | 24 | 10.73 | 20.29 | 0 | 0 |
| quietdrift90 | warm10 | boulevard | 24 | 12.28 | 22.93 | 0 | 0 |
| quietdrift90 | warm10:B | bayside | 24 | 12.62 | 23.85 | 0 | 0 |
| quietdrift90 | warm10:B | blocks | 24 | 11.16 | 25.79 | 0 | 0 |
| quietdrift90 | warm10:B | boulevard | 24 | 13.16 | 33.42 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | checkpoint | 24 | 6444 | 0 | None | 0.17 | 0.53 | 0.79 |
| blockedmid | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | restart+warm10 | bayside | other | 24 | 27126 | 0 | None | 0.23 | 1.31 | 6.55 |
| blockedmid | restart+warm10 | bayside | outage | 24 | 4066 | 0 | None | 0.63 | 1.33 | 1.56 |
| blockedmid | restart+warm10 | bayside | fix | 24 | 29504 | 0 | None | 0.2 | 0.73 | 6.55 |
| blockedmid | restart+warm10 | blocks | checkpoint | 24 | 8267 | 0 | 0.0 | 0.33 | 2.04 | 2.66 |
| blockedmid | restart+warm10 | blocks | corner | 24 | 8846 | 7 | 0.175 | 0.91 | 2.87 | 4.67 |
| blockedmid | restart+warm10 | blocks | other | 24 | 19036 | 33 | 0.825 | 0.21 | 2.07 | 6.94 |
| blockedmid | restart+warm10 | blocks | outage | 24 | 4616 | 21 | 0.525 | 0.61 | 3.26 | 4.67 |
| blockedmid | restart+warm10 | blocks | fix | 24 | 31533 | 19 | 0.475 | 0.26 | 2.33 | 6.94 |
| blockedmid | restart+warm10 | boulevard | checkpoint | 24 | 6593 | 0 | None | 0.16 | 0.53 | 0.8 |
| blockedmid | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | restart+warm10 | boulevard | other | 24 | 34085 | 0 | None | 0.13 | 0.65 | 6.96 |
| blockedmid | restart+warm10 | boulevard | outage | 24 | 4994 | 0 | None | 0.24 | 0.62 | 0.77 |
| blockedmid | restart+warm10 | boulevard | fix | 24 | 35684 | 0 | None | 0.12 | 0.56 | 6.96 |
| blockedmid | warm10 | bayside | checkpoint | 24 | 6446 | 0 | None | 0.19 | 0.53 | 0.89 |
| blockedmid | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | warm10 | bayside | other | 24 | 27211 | 0 | None | 0.23 | 2.17 | 6.55 |
| blockedmid | warm10 | bayside | outage | 24 | 4113 | 0 | None | 0.59 | 1.37 | 1.58 |
| blockedmid | warm10 | bayside | fix | 24 | 29544 | 0 | None | 0.2 | 1.78 | 6.55 |
| blockedmid | warm10 | blocks | checkpoint | 24 | 8363 | 18 | 0.247 | 0.38 | 2.35 | 3.11 |
| blockedmid | warm10 | blocks | corner | 24 | 8982 | 6 | 0.082 | 0.93 | 3.11 | 4.84 |
| blockedmid | warm10 | blocks | other | 24 | 19242 | 49 | 0.671 | 0.22 | 2.96 | 6.96 |
| blockedmid | warm10 | blocks | outage | 24 | 4686 | 22 | 0.301 | 0.58 | 3.06 | 4.54 |
| blockedmid | warm10 | blocks | fix | 24 | 31901 | 51 | 0.699 | 0.29 | 2.71 | 7.08 |
| blockedmid | warm10 | boulevard | checkpoint | 24 | 6595 | 0 | None | 0.17 | 0.56 | 0.91 |
| blockedmid | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | warm10 | boulevard | other | 24 | 34087 | 0 | None | 0.13 | 0.62 | 6.98 |
| blockedmid | warm10 | boulevard | outage | 24 | 4994 | 0 | None | 0.22 | 0.56 | 0.73 |
| blockedmid | warm10 | boulevard | fix | 24 | 35688 | 0 | None | 0.13 | 0.63 | 6.98 |
| blockedmid | warm10:B | bayside | checkpoint | 24 | 6700 | 0 | None | 0.18 | 1.04 | 1.44 |
| blockedmid | warm10:B | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | warm10:B | bayside | other | 24 | 27026 | 0 | None | 0.23 | 2.5 | 6.88 |
| blockedmid | warm10:B | bayside | outage | 21 | 4342 | 0 | None | 0.75 | 1.67 | 2.21 |
| blockedmid | warm10:B | bayside | fix | 24 | 29384 | 0 | None | 0.19 | 2.13 | 6.88 |
| blockedmid | warm10:B | blocks | checkpoint | 24 | 8747 | 49 | 0.386 | 0.42 | 2.46 | 3.73 |
| blockedmid | warm10:B | blocks | corner | 24 | 8939 | 10 | 0.079 | 0.81 | 2.65 | 4.67 |
| blockedmid | warm10:B | blocks | other | 24 | 18989 | 68 | 0.535 | 0.21 | 2.84 | 7.0 |
| blockedmid | warm10:B | blocks | outage | 21 | 4303 | 58 | 0.457 | 0.5 | 3.1 | 4.81 |
| blockedmid | warm10:B | blocks | fix | 24 | 32372 | 69 | 0.543 | 0.28 | 2.78 | 7.38 |
| blockedmid | warm10:B | boulevard | checkpoint | 24 | 6564 | 0 | None | 0.17 | 0.58 | 0.91 |
| blockedmid | warm10:B | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | warm10:B | boulevard | other | 24 | 34155 | 0 | None | 0.14 | 0.82 | 7.0 |
| blockedmid | warm10:B | boulevard | outage | 22 | 5028 | 0 | None | 0.28 | 0.83 | 1.08 |
| blockedmid | warm10:B | boulevard | fix | 24 | 35691 | 0 | None | 0.14 | 0.86 | 7.0 |
| blockedstart | restart+warm10 | bayside | checkpoint | 24 | 6304 | 0 | None | 0.16 | 0.5 | 0.86 |
| blockedstart | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | restart+warm10 | bayside | other | 24 | 27163 | 0 | None | 0.21 | 1.34 | 6.41 |
| blockedstart | restart+warm10 | bayside | outage | 24 | 3985 | 0 | None | 0.55 | 1.44 | 1.8 |
| blockedstart | restart+warm10 | bayside | fix | 24 | 29482 | 0 | None | 0.17 | 0.74 | 6.41 |
| blockedstart | restart+warm10 | blocks | checkpoint | 24 | 8120 | 0 | None | 0.34 | 2.08 | 2.51 |
| blockedstart | restart+warm10 | blocks | corner | 24 | 8638 | 0 | None | 0.87 | 2.62 | 4.58 |
| blockedstart | restart+warm10 | blocks | other | 24 | 19315 | 0 | None | 0.2 | 1.83 | 6.79 |
| blockedstart | restart+warm10 | blocks | outage | 24 | 4468 | 0 | None | 0.51 | 3.22 | 4.66 |
| blockedstart | restart+warm10 | blocks | fix | 24 | 31605 | 0 | None | 0.25 | 2.23 | 6.79 |
| blockedstart | restart+warm10 | boulevard | checkpoint | 24 | 6255 | 0 | None | 0.16 | 0.52 | 0.81 |
| blockedstart | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | restart+warm10 | boulevard | other | 24 | 34313 | 0 | None | 0.12 | 0.66 | 6.81 |
| blockedstart | restart+warm10 | boulevard | outage | 24 | 4874 | 0 | None | 0.32 | 0.85 | 0.95 |
| blockedstart | restart+warm10 | boulevard | fix | 24 | 35694 | 0 | None | 0.12 | 0.54 | 6.81 |
| blockedstart | warm10 | bayside | checkpoint | 24 | 6319 | 0 | 0.0 | 0.18 | 0.7 | 1.2 |
| blockedstart | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedstart | warm10 | bayside | other | 24 | 27273 | 10 | 1.0 | 0.2 | 1.87 | 6.47 |
| blockedstart | warm10 | bayside | outage | 24 | 4040 | 0 | 0.0 | 0.59 | 1.42 | 1.75 |
| blockedstart | warm10 | bayside | fix | 24 | 29552 | 10 | 1.0 | 0.19 | 1.47 | 6.47 |
| blockedstart | warm10 | blocks | checkpoint | 24 | 8243 | 42 | 0.689 | 0.4 | 2.56 | 3.58 |
| blockedstart | warm10 | blocks | corner | 24 | 8815 | 19 | 0.311 | 0.9 | 2.78 | 4.64 |
| blockedstart | warm10 | blocks | other | 24 | 19473 | 0 | 0.0 | 0.21 | 2.83 | 6.78 |
| blockedstart | warm10 | blocks | outage | 24 | 4539 | 0 | 0.0 | 0.62 | 3.29 | 4.54 |
| blockedstart | warm10 | blocks | fix | 24 | 31992 | 61 | 1.0 | 0.27 | 2.62 | 6.88 |
| blockedstart | warm10 | boulevard | checkpoint | 24 | 6252 | 0 | None | 0.17 | 0.73 | 0.99 |
| blockedstart | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | warm10 | boulevard | other | 24 | 34325 | 0 | None | 0.13 | 0.72 | 6.81 |
| blockedstart | warm10 | boulevard | outage | 24 | 4874 | 0 | None | 0.29 | 0.79 | 0.94 |
| blockedstart | warm10 | boulevard | fix | 24 | 35703 | 0 | None | 0.13 | 0.7 | 6.81 |
| blockedstart | warm10:B | bayside | checkpoint | 24 | 6323 | 0 | None | 0.17 | 0.61 | 1.19 |
| blockedstart | warm10:B | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | warm10:B | bayside | other | 24 | 27222 | 0 | None | 0.23 | 1.9 | 6.51 |
| blockedstart | warm10:B | bayside | outage | 21 | 4246 | 0 | None | 0.69 | 1.53 | 1.95 |
| blockedstart | warm10:B | bayside | fix | 24 | 29299 | 0 | None | 0.19 | 1.77 | 6.51 |
| blockedstart | warm10:B | blocks | checkpoint | 24 | 8290 | 32 | 0.525 | 0.36 | 2.27 | 3.67 |
| blockedstart | warm10:B | blocks | corner | 24 | 8809 | 26 | 0.426 | 0.89 | 2.75 | 4.67 |
| blockedstart | warm10:B | blocks | other | 24 | 19380 | 3 | 0.049 | 0.21 | 2.48 | 6.79 |
| blockedstart | warm10:B | blocks | outage | 21 | 4117 | 12 | 0.197 | 0.53 | 3.16 | 4.58 |
| blockedstart | warm10:B | blocks | fix | 24 | 32362 | 49 | 0.803 | 0.27 | 2.65 | 6.93 |
| blockedstart | warm10:B | boulevard | checkpoint | 24 | 6258 | 0 | None | 0.15 | 0.53 | 0.84 |
| blockedstart | warm10:B | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | warm10:B | boulevard | other | 24 | 34275 | 0 | None | 0.14 | 0.72 | 6.75 |
| blockedstart | warm10:B | boulevard | outage | 22 | 5133 | 0 | None | 0.26 | 0.77 | 0.89 |
| blockedstart | warm10:B | boulevard | fix | 24 | 35400 | 0 | None | 0.14 | 0.69 | 6.75 |
| outage90 | restart+warm10 | bayside | checkpoint | 24 | 6306 | 0 | 0.0 | 0.52 | 1.48 | 2.17 |
| outage90 | restart+warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart+warm10 | bayside | other | 24 | 26427 | 27 | 1.0 | 0.55 | 3.54 | 6.56 |
| outage90 | restart+warm10 | bayside | outage | 23 | 3953 | 18 | 0.667 | 1.54 | 4.71 | 4.92 |
| outage90 | restart+warm10 | bayside | fix | 24 | 28780 | 9 | 0.333 | 0.49 | 1.98 | 6.56 |
| outage90 | restart+warm10 | blocks | checkpoint | 24 | 8199 | 2 | 0.118 | 0.78 | 2.26 | 3.33 |
| outage90 | restart+warm10 | blocks | corner | 24 | 8562 | 1 | 0.059 | 1.1 | 3.18 | 5.59 |
| outage90 | restart+warm10 | blocks | other | 24 | 18619 | 14 | 0.824 | 0.69 | 3.92 | 6.48 |
| outage90 | restart+warm10 | blocks | outage | 24 | 4505 | 2 | 0.118 | 1.62 | 4.74 | 5.63 |
| outage90 | restart+warm10 | blocks | fix | 24 | 30875 | 15 | 0.882 | 0.72 | 2.71 | 6.48 |
| outage90 | restart+warm10 | boulevard | checkpoint | 24 | 6294 | 0 | 0.0 | 0.53 | 1.64 | 2.0 |
| outage90 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart+warm10 | boulevard | other | 24 | 33585 | 100 | 1.0 | 0.64 | 3.04 | 6.74 |
| outage90 | restart+warm10 | boulevard | outage | 24 | 4911 | 49 | 0.49 | 1.46 | 3.63 | 4.04 |
| outage90 | restart+warm10 | boulevard | fix | 24 | 34968 | 51 | 0.51 | 0.54 | 2.05 | 6.74 |
| outage90 | warm10 | bayside | checkpoint | 24 | 6334 | 41 | 0.383 | 0.54 | 1.73 | 2.59 |
| outage90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10 | bayside | other | 24 | 26524 | 66 | 0.617 | 0.57 | 3.9 | 7.09 |
| outage90 | warm10 | bayside | outage | 23 | 3830 | 31 | 0.29 | 1.37 | 4.77 | 5.02 |
| outage90 | warm10 | bayside | fix | 24 | 29028 | 76 | 0.71 | 0.52 | 3.05 | 7.09 |
| outage90 | warm10 | blocks | checkpoint | 24 | 8312 | 41 | 0.394 | 0.93 | 2.91 | 4.4 |
| outage90 | warm10 | blocks | corner | 24 | 8684 | 29 | 0.279 | 1.08 | 3.53 | 6.2 |
| outage90 | warm10 | blocks | other | 24 | 18829 | 34 | 0.327 | 0.66 | 4.61 | 6.95 |
| outage90 | warm10 | blocks | outage | 24 | 4490 | 3 | 0.029 | 1.64 | 5.21 | 6.18 |
| outage90 | warm10 | blocks | fix | 24 | 31335 | 101 | 0.971 | 0.72 | 3.17 | 7.79 |
| outage90 | warm10 | boulevard | checkpoint | 24 | 6300 | 5 | 0.039 | 0.53 | 1.64 | 2.12 |
| outage90 | warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10 | boulevard | other | 24 | 33564 | 124 | 0.961 | 0.69 | 3.06 | 6.62 |
| outage90 | warm10 | boulevard | outage | 24 | 4909 | 54 | 0.419 | 1.52 | 3.48 | 4.04 |
| outage90 | warm10 | boulevard | fix | 24 | 34955 | 75 | 0.581 | 0.6 | 2.18 | 6.62 |
| outage90 | warm10:B | bayside | checkpoint | 24 | 6339 | 0 | 0.0 | 0.52 | 1.44 | 1.79 |
| outage90 | warm10:B | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10:B | bayside | other | 24 | 26536 | 159 | 1.0 | 0.59 | 3.99 | 7.22 |
| outage90 | warm10:B | bayside | outage | 21 | 3933 | 98 | 0.616 | 1.69 | 3.84 | 5.04 |
| outage90 | warm10:B | bayside | fix | 24 | 28942 | 61 | 0.384 | 0.54 | 3.12 | 7.22 |
| outage90 | warm10:B | blocks | checkpoint | 24 | 8339 | 19 | 0.207 | 0.78 | 3.41 | 5.0 |
| outage90 | warm10:B | blocks | corner | 24 | 8772 | 46 | 0.5 | 1.17 | 4.26 | 6.96 |
| outage90 | warm10:B | blocks | other | 24 | 18764 | 27 | 0.293 | 0.74 | 4.19 | 7.28 |
| outage90 | warm10:B | blocks | outage | 21 | 4418 | 11 | 0.12 | 1.57 | 4.72 | 6.81 |
| outage90 | warm10:B | blocks | fix | 24 | 31457 | 81 | 0.88 | 0.79 | 3.46 | 7.62 |
| outage90 | warm10:B | boulevard | checkpoint | 24 | 6285 | 0 | 0.0 | 0.46 | 1.29 | 1.67 |
| outage90 | warm10:B | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10:B | boulevard | other | 24 | 33610 | 150 | 1.0 | 0.67 | 3.52 | 7.12 |
| outage90 | warm10:B | boulevard | outage | 22 | 5000 | 82 | 0.547 | 1.84 | 4.2 | 4.46 |
| outage90 | warm10:B | boulevard | fix | 24 | 34895 | 68 | 0.453 | 0.55 | 2.38 | 7.12 |
| quiet45 | restart+warm10 | bayside | checkpoint | 24 | 6312 | 0 | None | 0.21 | 0.73 | 1.39 |
| quiet45 | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm10 | bayside | other | 24 | 26363 | 0 | None | 0.22 | 1.57 | 6.55 |
| quiet45 | restart+warm10 | bayside | outage | 24 | 4223 | 0 | None | 0.56 | 1.75 | 2.08 |
| quiet45 | restart+warm10 | bayside | fix | 24 | 28452 | 0 | None | 0.2 | 1.14 | 6.55 |
| quiet45 | restart+warm10 | blocks | checkpoint | 24 | 8174 | 0 | None | 0.35 | 2.08 | 2.53 |
| quiet45 | restart+warm10 | blocks | corner | 24 | 8593 | 0 | None | 0.8 | 2.78 | 4.56 |
| quiet45 | restart+warm10 | blocks | other | 24 | 18558 | 0 | None | 0.23 | 2.12 | 6.94 |
| quiet45 | restart+warm10 | blocks | outage | 24 | 4491 | 0 | None | 0.43 | 2.56 | 4.5 |
| quiet45 | restart+warm10 | blocks | fix | 24 | 30834 | 0 | None | 0.28 | 2.38 | 6.94 |
| quiet45 | restart+warm10 | boulevard | checkpoint | 24 | 6297 | 0 | None | 0.16 | 0.55 | 0.83 |
| quiet45 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm10 | boulevard | other | 24 | 33514 | 0 | None | 0.14 | 0.72 | 6.96 |
| quiet45 | restart+warm10 | boulevard | outage | 24 | 5256 | 0 | None | 0.23 | 0.74 | 1.02 |
| quiet45 | restart+warm10 | boulevard | fix | 24 | 34555 | 0 | None | 0.13 | 0.64 | 6.96 |
| quiet45 | warm10 | bayside | checkpoint | 24 | 6328 | 0 | None | 0.23 | 1.35 | 1.86 |
| quiet45 | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10 | bayside | other | 24 | 26439 | 0 | None | 0.24 | 2.06 | 6.55 |
| quiet45 | warm10 | bayside | outage | 24 | 4199 | 0 | None | 0.51 | 1.78 | 2.22 |
| quiet45 | warm10 | bayside | fix | 24 | 28568 | 0 | None | 0.22 | 1.97 | 6.55 |
| quiet45 | warm10 | blocks | checkpoint | 24 | 8285 | 0 | None | 0.43 | 2.61 | 3.22 |
| quiet45 | warm10 | blocks | corner | 24 | 8764 | 0 | None | 0.86 | 2.87 | 4.56 |
| quiet45 | warm10 | blocks | other | 24 | 18595 | 0 | None | 0.24 | 2.74 | 6.96 |
| quiet45 | warm10 | blocks | outage | 24 | 4512 | 0 | None | 0.55 | 2.73 | 4.48 |
| quiet45 | warm10 | blocks | fix | 24 | 31132 | 0 | None | 0.32 | 2.77 | 6.96 |
| quiet45 | warm10 | boulevard | checkpoint | 24 | 6308 | 0 | None | 0.18 | 0.67 | 0.9 |
| quiet45 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10 | boulevard | other | 24 | 33510 | 0 | None | 0.17 | 0.84 | 6.98 |
| quiet45 | warm10 | boulevard | outage | 24 | 5257 | 0 | None | 0.26 | 0.77 | 1.08 |
| quiet45 | warm10 | boulevard | fix | 24 | 34561 | 0 | None | 0.15 | 0.81 | 6.98 |
| quiet45 | warm10:B | bayside | checkpoint | 24 | 6339 | 0 | None | 0.18 | 0.73 | 1.08 |
| quiet45 | warm10:B | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10:B | bayside | other | 24 | 26415 | 0 | None | 0.23 | 1.96 | 6.84 |
| quiet45 | warm10:B | bayside | outage | 24 | 3974 | 0 | None | 0.46 | 1.5 | 2.04 |
| quiet45 | warm10:B | bayside | fix | 24 | 28780 | 0 | None | 0.21 | 1.82 | 6.84 |
| quiet45 | warm10:B | blocks | checkpoint | 24 | 8249 | 0 | None | 0.45 | 2.35 | 3.01 |
| quiet45 | warm10:B | blocks | corner | 24 | 8771 | 0 | None | 0.81 | 2.85 | 4.62 |
| quiet45 | warm10:B | blocks | other | 24 | 18583 | 0 | None | 0.23 | 2.62 | 6.98 |
| quiet45 | warm10:B | blocks | outage | 24 | 4407 | 0 | None | 0.51 | 2.77 | 4.55 |
| quiet45 | warm10:B | blocks | fix | 24 | 31196 | 0 | None | 0.3 | 2.78 | 7.0 |
| quiet45 | warm10:B | boulevard | checkpoint | 24 | 6293 | 0 | None | 0.16 | 0.58 | 0.86 |
| quiet45 | warm10:B | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10:B | boulevard | other | 24 | 33531 | 0 | None | 0.14 | 0.89 | 7.0 |
| quiet45 | warm10:B | boulevard | outage | 24 | 5181 | 0 | None | 0.27 | 0.76 | 0.96 |
| quiet45 | warm10:B | boulevard | fix | 24 | 34643 | 0 | None | 0.14 | 0.8 | 7.0 |
| quiet90 | restart+warm10 | bayside | checkpoint | 24 | 6297 | 0 | None | 0.17 | 0.53 | 0.9 |
| quiet90 | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm10 | bayside | other | 24 | 26376 | 0 | None | 0.21 | 1.36 | 6.55 |
| quiet90 | restart+warm10 | bayside | outage | 23 | 3941 | 0 | None | 0.73 | 1.54 | 1.81 |
| quiet90 | restart+warm10 | bayside | fix | 24 | 28732 | 0 | None | 0.19 | 0.81 | 6.55 |
| quiet90 | restart+warm10 | blocks | checkpoint | 24 | 8179 | 0 | None | 0.32 | 1.99 | 2.38 |
| quiet90 | restart+warm10 | blocks | corner | 24 | 8546 | 0 | None | 0.9 | 2.83 | 4.78 |
| quiet90 | restart+warm10 | blocks | other | 24 | 18563 | 0 | None | 0.23 | 2.16 | 6.94 |
| quiet90 | restart+warm10 | blocks | outage | 24 | 4480 | 0 | None | 0.63 | 3.37 | 4.78 |
| quiet90 | restart+warm10 | blocks | fix | 24 | 30808 | 0 | None | 0.27 | 2.29 | 6.94 |
| quiet90 | restart+warm10 | boulevard | checkpoint | 24 | 6287 | 0 | None | 0.17 | 0.52 | 0.83 |
| quiet90 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm10 | boulevard | other | 24 | 33517 | 0 | None | 0.14 | 0.66 | 6.96 |
| quiet90 | restart+warm10 | boulevard | outage | 24 | 4915 | 0 | None | 0.28 | 0.53 | 0.74 |
| quiet90 | restart+warm10 | boulevard | fix | 24 | 34889 | 0 | None | 0.13 | 0.56 | 6.96 |
| quiet90 | warm10 | bayside | checkpoint | 24 | 6321 | 0 | 0.0 | 0.17 | 1.34 | 1.89 |
| quiet90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | warm10 | bayside | other | 24 | 26492 | 7 | 1.0 | 0.22 | 2.44 | 6.56 |
| quiet90 | warm10 | bayside | outage | 23 | 3889 | 0 | 0.0 | 0.7 | 1.6 | 1.91 |
| quiet90 | warm10 | bayside | fix | 24 | 28924 | 7 | 1.0 | 0.19 | 2.27 | 6.56 |
| quiet90 | warm10 | blocks | checkpoint | 24 | 8284 | 36 | 1.0 | 0.38 | 2.67 | 4.06 |
| quiet90 | warm10 | blocks | corner | 24 | 8631 | 0 | 0.0 | 0.92 | 2.98 | 4.92 |
| quiet90 | warm10 | blocks | other | 24 | 18804 | 0 | 0.0 | 0.23 | 3.38 | 6.96 |
| quiet90 | warm10 | blocks | outage | 24 | 4484 | 0 | 0.0 | 0.57 | 3.38 | 4.74 |
| quiet90 | warm10 | blocks | fix | 24 | 31235 | 36 | 1.0 | 0.29 | 2.88 | 7.08 |
| quiet90 | warm10 | boulevard | checkpoint | 24 | 6287 | 0 | None | 0.18 | 0.6 | 0.88 |
| quiet90 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10 | boulevard | other | 24 | 33522 | 0 | None | 0.14 | 0.74 | 6.98 |
| quiet90 | warm10 | boulevard | outage | 24 | 4916 | 0 | None | 0.25 | 0.57 | 0.95 |
| quiet90 | warm10 | boulevard | fix | 24 | 34893 | 0 | None | 0.14 | 0.69 | 6.98 |
| quiet90 | warm10:B | bayside | checkpoint | 24 | 6335 | 0 | None | 0.17 | 0.53 | 1.13 |
| quiet90 | warm10:B | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10:B | bayside | other | 24 | 26488 | 0 | None | 0.22 | 2.55 | 6.94 |
| quiet90 | warm10:B | bayside | outage | 21 | 3900 | 0 | None | 0.73 | 1.7 | 2.39 |
| quiet90 | warm10:B | bayside | fix | 24 | 28923 | 0 | None | 0.19 | 1.94 | 6.88 |
| quiet90 | warm10:B | blocks | checkpoint | 24 | 8308 | 22 | 0.564 | 0.39 | 2.38 | 3.53 |
| quiet90 | warm10:B | blocks | corner | 24 | 8795 | 17 | 0.436 | 0.94 | 3.01 | 4.99 |
| quiet90 | warm10:B | blocks | other | 24 | 18693 | 0 | 0.0 | 0.23 | 3.63 | 7.0 |
| quiet90 | warm10:B | blocks | outage | 21 | 4390 | 0 | 0.0 | 0.67 | 3.28 | 4.91 |
| quiet90 | warm10:B | blocks | fix | 24 | 31406 | 39 | 1.0 | 0.27 | 3.38 | 7.35 |
| quiet90 | warm10:B | boulevard | checkpoint | 24 | 6271 | 0 | None | 0.16 | 0.56 | 0.89 |
| quiet90 | warm10:B | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10:B | boulevard | other | 24 | 33533 | 0 | None | 0.14 | 0.8 | 7.0 |
| quiet90 | warm10:B | boulevard | outage | 22 | 5068 | 0 | None | 0.26 | 0.9 | 1.24 |
| quiet90 | warm10:B | boulevard | fix | 24 | 34736 | 0 | None | 0.13 | 0.68 | 7.0 |
| quietdrift90 | restart+warm10 | bayside | checkpoint | 24 | 6331 | 92 | 0.09 | 1.41 | 3.55 | 4.19 |
| quietdrift90 | restart+warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm10 | bayside | other | 24 | 26577 | 932 | 0.91 | 1.42 | 5.95 | 9.8 |
| quietdrift90 | restart+warm10 | bayside | outage | 23 | 4024 | 645 | 0.63 | 3.03 | 8.86 | 9.08 |
| quietdrift90 | restart+warm10 | bayside | fix | 24 | 28884 | 379 | 0.37 | 1.31 | 4.84 | 9.8 |
| quietdrift90 | restart+warm10 | blocks | checkpoint | 24 | 8235 | 34 | 0.051 | 1.44 | 4.09 | 4.83 |
| quietdrift90 | restart+warm10 | blocks | corner | 24 | 8575 | 77 | 0.115 | 1.6 | 4.45 | 6.51 |
| quietdrift90 | restart+warm10 | blocks | other | 24 | 18746 | 556 | 0.834 | 1.61 | 6.06 | 9.66 |
| quietdrift90 | restart+warm10 | blocks | outage | 24 | 4437 | 461 | 0.691 | 3.15 | 7.51 | 9.95 |
| quietdrift90 | restart+warm10 | blocks | fix | 24 | 31119 | 206 | 0.309 | 1.51 | 4.52 | 8.91 |
| quietdrift90 | restart+warm10 | boulevard | checkpoint | 24 | 6322 | 122 | 0.096 | 1.35 | 4.21 | 4.76 |
| quietdrift90 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm10 | boulevard | other | 24 | 33750 | 1144 | 0.904 | 1.49 | 5.77 | 11.38 |
| quietdrift90 | restart+warm10 | boulevard | outage | 24 | 4931 | 812 | 0.641 | 3.38 | 10.07 | 10.88 |
| quietdrift90 | restart+warm10 | boulevard | fix | 24 | 35141 | 454 | 0.359 | 1.36 | 4.67 | 11.38 |
| quietdrift90 | warm10 | bayside | checkpoint | 24 | 6349 | 125 | 0.109 | 1.5 | 3.93 | 5.04 |
| quietdrift90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10 | bayside | other | 24 | 26684 | 1020 | 0.891 | 1.41 | 6.54 | 11.12 |
| quietdrift90 | warm10 | bayside | outage | 23 | 3975 | 617 | 0.539 | 2.81 | 8.86 | 9.08 |
| quietdrift90 | warm10 | bayside | fix | 24 | 29058 | 528 | 0.461 | 1.36 | 4.92 | 11.12 |
| quietdrift90 | warm10 | blocks | checkpoint | 24 | 8347 | 109 | 0.131 | 1.39 | 5.14 | 6.22 |
| quietdrift90 | warm10 | blocks | corner | 24 | 8698 | 173 | 0.208 | 1.73 | 4.83 | 7.24 |
| quietdrift90 | warm10 | blocks | other | 24 | 18986 | 550 | 0.661 | 1.77 | 6.14 | 9.79 |
| quietdrift90 | warm10 | blocks | outage | 24 | 4582 | 418 | 0.502 | 3.04 | 7.51 | 9.48 |
| quietdrift90 | warm10 | blocks | fix | 24 | 31449 | 414 | 0.498 | 1.55 | 5.26 | 9.68 |
| quietdrift90 | warm10 | boulevard | checkpoint | 24 | 6318 | 167 | 0.101 | 1.33 | 4.65 | 5.16 |
| quietdrift90 | warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10 | boulevard | other | 24 | 33705 | 1480 | 0.899 | 1.47 | 6.37 | 12.28 |
| quietdrift90 | warm10 | boulevard | outage | 24 | 4930 | 777 | 0.472 | 3.46 | 9.78 | 10.85 |
| quietdrift90 | warm10 | boulevard | fix | 24 | 35093 | 870 | 0.528 | 1.41 | 5.28 | 12.28 |
| quietdrift90 | warm10:B | bayside | checkpoint | 24 | 6385 | 105 | 0.068 | 1.31 | 4.85 | 5.54 |
| quietdrift90 | warm10:B | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10:B | bayside | other | 24 | 26683 | 1430 | 0.932 | 1.46 | 7.12 | 12.62 |
| quietdrift90 | warm10:B | bayside | outage | 21 | 3955 | 710 | 0.463 | 2.8 | 10.23 | 10.93 |
| quietdrift90 | warm10:B | bayside | fix | 24 | 29113 | 825 | 0.537 | 1.42 | 5.19 | 12.62 |
| quietdrift90 | warm10:B | blocks | checkpoint | 24 | 8405 | 238 | 0.183 | 1.71 | 5.53 | 6.99 |
| quietdrift90 | warm10:B | blocks | corner | 24 | 8627 | 181 | 0.139 | 1.65 | 5.33 | 6.88 |
| quietdrift90 | warm10:B | blocks | other | 24 | 18967 | 883 | 0.678 | 1.77 | 6.72 | 10.55 |
| quietdrift90 | warm10:B | blocks | outage | 21 | 4328 | 759 | 0.583 | 3.35 | 9.87 | 12.31 |
| quietdrift90 | warm10:B | blocks | fix | 24 | 31671 | 543 | 0.417 | 1.62 | 5.67 | 10.26 |
| quietdrift90 | warm10:B | boulevard | checkpoint | 24 | 6307 | 136 | 0.066 | 1.53 | 3.94 | 4.82 |
| quietdrift90 | warm10:B | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10:B | boulevard | other | 24 | 33784 | 1938 | 0.934 | 1.75 | 7.62 | 13.16 |
| quietdrift90 | warm10:B | boulevard | outage | 22 | 5030 | 1060 | 0.511 | 4.34 | 12.31 | 14.02 |
| quietdrift90 | warm10:B | boulevard | fix | 24 | 35061 | 1014 | 0.489 | 1.56 | 6.34 | 13.16 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 1.0 | 3.69 |
| blockedmid | restart+warm10 | blocks | 24 | 1.02 | 3.64 |
| blockedmid | restart+warm10 | boulevard | 24 | 0.96 | 3.42 |
| blockedmid | warm10 | bayside | 24 | 0.99 | 3.7 |
| blockedmid | warm10 | blocks | 24 | 1.01 | 3.65 |
| blockedmid | warm10 | boulevard | 24 | 0.95 | 3.42 |
| blockedmid | warm10:B | bayside | 24 | 0.98 | 3.8 |
| blockedmid | warm10:B | blocks | 24 | 1.01 | 3.7 |
| blockedmid | warm10:B | boulevard | 24 | 0.95 | 3.46 |
| blockedstart | restart+warm10 | bayside | 24 | 1.03 | 5.58 |
| blockedstart | restart+warm10 | blocks | 24 | 1.04 | 5.37 |
| blockedstart | restart+warm10 | boulevard | 24 | 0.97 | 5.04 |
| blockedstart | warm10 | bayside | 24 | 1.02 | 5.57 |
| blockedstart | warm10 | blocks | 24 | 1.04 | 5.37 |
| blockedstart | warm10 | boulevard | 24 | 0.96 | 5.04 |
| blockedstart | warm10:B | bayside | 24 | 1.02 | 5.53 |
| blockedstart | warm10:B | blocks | 24 | 1.04 | 5.33 |
| blockedstart | warm10:B | boulevard | 24 | 0.98 | 5.0 |
| outage90 | restart+warm10 | bayside | 24 | 1.58 | 4.2 |
| outage90 | restart+warm10 | blocks | 24 | 1.62 | 4.17 |
| outage90 | restart+warm10 | boulevard | 24 | 1.56 | 3.98 |
| outage90 | warm10 | bayside | 24 | 1.59 | 4.27 |
| outage90 | warm10 | blocks | 24 | 1.59 | 4.2 |
| outage90 | warm10 | boulevard | 24 | 1.66 | 4.02 |
| outage90 | warm10:B | bayside | 24 | 1.62 | 4.24 |
| outage90 | warm10:B | blocks | 24 | 1.67 | 4.27 |
| outage90 | warm10:B | boulevard | 24 | 1.57 | 4.01 |
| quiet45 | restart+warm10 | bayside | 24 | 1.02 | 3.74 |
| quiet45 | restart+warm10 | blocks | 24 | 1.02 | 3.67 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.95 | 3.43 |
| quiet45 | warm10 | bayside | 24 | 0.99 | 3.73 |
| quiet45 | warm10 | blocks | 24 | 1.02 | 3.65 |
| quiet45 | warm10 | boulevard | 24 | 0.96 | 3.43 |
| quiet45 | warm10:B | bayside | 24 | 1.0 | 3.84 |
| quiet45 | warm10:B | blocks | 24 | 1.02 | 3.73 |
| quiet45 | warm10:B | boulevard | 24 | 0.95 | 3.46 |
| quiet90 | restart+warm10 | bayside | 24 | 1.0 | 3.73 |
| quiet90 | restart+warm10 | blocks | 24 | 1.0 | 3.67 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.95 | 3.44 |
| quiet90 | warm10 | bayside | 24 | 0.99 | 3.73 |
| quiet90 | warm10 | blocks | 24 | 1.01 | 3.67 |
| quiet90 | warm10 | boulevard | 24 | 0.95 | 3.44 |
| quiet90 | warm10:B | bayside | 24 | 0.98 | 3.84 |
| quiet90 | warm10:B | blocks | 24 | 1.0 | 3.72 |
| quiet90 | warm10:B | boulevard | 24 | 0.96 | 3.48 |
| quietdrift90 | restart+warm10 | bayside | 24 | 5.17 | 8.38 |
| quietdrift90 | restart+warm10 | blocks | 24 | 5.45 | 8.79 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 4.93 | 8.2 |
| quietdrift90 | warm10 | bayside | 24 | 5.17 | 8.41 |
| quietdrift90 | warm10 | blocks | 24 | 5.39 | 8.88 |
| quietdrift90 | warm10 | boulevard | 24 | 4.88 | 8.16 |
| quietdrift90 | warm10:B | bayside | 24 | 5.41 | 8.59 |
| quietdrift90 | warm10:B | blocks | 24 | 5.77 | 9.27 |
| quietdrift90 | warm10:B | boulevard | 24 | 5.21 | 8.45 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| blockedmid | restart+warm10 | bayside | 24 | 0.0231 |
| blockedmid | restart+warm10 | blocks | 24 | 0.034 |
| blockedmid | restart+warm10 | boulevard | 24 | 0.0205 |
| blockedmid | warm10 | bayside | 24 | 0.0248 |
| blockedmid | warm10 | blocks | 24 | 0.0368 |
| blockedmid | warm10 | boulevard | 24 | 0.0205 |
| blockedmid | warm10:B | bayside | 24 | 0.0251 |
| blockedmid | warm10:B | blocks | 24 | 0.0364 |
| blockedmid | warm10:B | boulevard | 24 | 0.0204 |
| blockedstart | restart+warm10 | bayside | 24 | 0.0232 |
| blockedstart | restart+warm10 | blocks | 24 | 0.034 |
| blockedstart | restart+warm10 | boulevard | 24 | 0.0205 |
| blockedstart | warm10 | bayside | 24 | 0.0252 |
| blockedstart | warm10 | blocks | 24 | 0.0367 |
| blockedstart | warm10 | boulevard | 24 | 0.0205 |
| blockedstart | warm10:B | bayside | 24 | 0.0244 |
| blockedstart | warm10:B | blocks | 24 | 0.0369 |
| blockedstart | warm10:B | boulevard | 24 | 0.0204 |
| outage90 | restart+warm10 | bayside | 24 | 0.0285 |
| outage90 | restart+warm10 | blocks | 24 | 0.0393 |
| outage90 | restart+warm10 | boulevard | 24 | 0.0267 |
| outage90 | warm10 | bayside | 24 | 0.0315 |
| outage90 | warm10 | blocks | 24 | 0.0423 |
| outage90 | warm10 | boulevard | 24 | 0.0264 |
| outage90 | warm10:B | bayside | 24 | 0.0301 |
| outage90 | warm10:B | blocks | 24 | 0.0423 |
| outage90 | warm10:B | boulevard | 24 | 0.0264 |
| quiet45 | restart+warm10 | bayside | 24 | 0.0222 |
| quiet45 | restart+warm10 | blocks | 24 | 0.0334 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.0197 |
| quiet45 | warm10 | bayside | 24 | 0.0246 |
| quiet45 | warm10 | blocks | 24 | 0.0348 |
| quiet45 | warm10 | boulevard | 24 | 0.0195 |
| quiet45 | warm10:B | bayside | 24 | 0.0247 |
| quiet45 | warm10:B | blocks | 24 | 0.0348 |
| quiet45 | warm10:B | boulevard | 24 | 0.0195 |
| quiet90 | restart+warm10 | bayside | 24 | 0.0221 |
| quiet90 | restart+warm10 | blocks | 24 | 0.0332 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.0195 |
| quiet90 | warm10 | bayside | 24 | 0.0249 |
| quiet90 | warm10 | blocks | 24 | 0.036 |
| quiet90 | warm10 | boulevard | 24 | 0.0195 |
| quiet90 | warm10:B | bayside | 24 | 0.0239 |
| quiet90 | warm10:B | blocks | 24 | 0.0365 |
| quiet90 | warm10:B | boulevard | 24 | 0.0194 |
| quietdrift90 | restart+warm10 | bayside | 24 | 0.0271 |
| quietdrift90 | restart+warm10 | blocks | 24 | 0.0373 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 0.0252 |
| quietdrift90 | warm10 | bayside | 24 | 0.0289 |
| quietdrift90 | warm10 | blocks | 24 | 0.04 |
| quietdrift90 | warm10 | boulevard | 24 | 0.0249 |
| quietdrift90 | warm10:B | bayside | 24 | 0.0287 |
| quietdrift90 | warm10:B | blocks | 24 | 0.0399 |
| quietdrift90 | warm10:B | boulevard | 24 | 0.0248 |
