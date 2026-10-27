# A warm-up only after a stand, and blocks of many lengths (simulated)

pace_v.py 0.1.0 (pace_u.py 0.1.0, pace_t.py 0.1.0, pace_q.py 0.1.0, pace_p.py 0.1.0, rover_pilot.py 0.18.6, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_u.py flies it, with Pilot._stuck as it ships (a0.3), with no stuck verdict until 10 s after every clear of the stuck history (warm10), or with that warm-up only at the first check and after a stand of 3 s or more with no recovery move (warmstand10). Profiles: outage90, quiet90, quietdrift90 and quiet45 as in pace-u, and blockedstart and blockedmid (quiet90 with a block of 30-60 s drawn per seed, at the start or starting 240-600 s in). Seeds 397-420; a0.3:B is a0.3 on seeds 421-444, for the seed-to-seed spread. 1728 of 1728 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_u.py's runs: 8 compared, 8 identical.

## Tolerances from the spread between the two seed sets of a0.3

| figure | spread m | tolerance m |
|---|---|---|
| blocks corner p95 | 0.94 | 0.95 |
| p95 offset | 1.4 | 1.4 |

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | 72/72 | 0.875 | 0.984 | 72 | 1.0 | 0.022 |
| outage90 | warm10 | 72/72 | 0.88 | 0.99 | 72 | 0.999 | 0.023 |
| outage90 | warmstand10 | 72/72 | 0.88 | 0.99 | 72 | 0.999 | 0.023 |
| outage90 | a0.3:B | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.016 |
| quiet90 | a0.3 | 72/72 | 0.879 | 0.988 | 72 | 0.999 | 0.022 |
| quiet90 | warm10 | 72/72 | 0.884 | 0.995 | 72 | 0.997 | 0.021 |
| quiet90 | warmstand10 | 72/72 | 0.884 | 0.995 | 72 | 0.997 | 0.021 |
| quiet90 | a0.3:B | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.017 |
| quietdrift90 | a0.3 | 72/72 | 0.867 | 0.975 | 71 | 1.004 | 0.023 |
| quietdrift90 | warm10 | 72/72 | 0.869 | 0.977 | 71 | 1.002 | 0.025 |
| quietdrift90 | warmstand10 | 72/72 | 0.869 | 0.977 | 71 | 1.002 | 0.025 |
| quietdrift90 | a0.3:B | 72/72 | 0.871 | 0.98 | 72 | 1.004 | 0.02 |
| quiet45 | a0.3 | 72/72 | 0.877 | 0.987 | 72 | 0.999 | 0.019 |
| quiet45 | warm10 | 72/72 | 0.885 | 0.996 | 72 | 0.997 | 0.013 |
| quiet45 | warmstand10 | 72/72 | 0.885 | 0.996 | 72 | 0.997 | 0.013 |
| quiet45 | a0.3:B | 72/72 | 0.883 | 0.993 | 72 | 0.999 | 0.014 |
| blockedstart | a0.3 | 72/72 | 0.846 | 0.952 | 71 | 0.998 | 0.028 |
| blockedstart | warm10 | 72/72 | 0.848 | 0.954 | 71 | 0.997 | 0.028 |
| blockedstart | warmstand10 | 72/72 | 0.842 | 0.948 | 71 | 0.998 | 0.029 |
| blockedstart | a0.3:B | 72/72 | 0.849 | 0.956 | 72 | 0.997 | 0.022 |
| blockedmid | a0.3 | 72/72 | 0.846 | 0.952 | 71 | 1.0 | 0.023 |
| blockedmid | warm10 | 72/72 | 0.851 | 0.957 | 71 | 0.998 | 0.023 |
| blockedmid | warmstand10 | 72/72 | 0.849 | 0.955 | 71 | 0.998 | 0.024 |
| blockedmid | a0.3:B | 72/72 | 0.849 | 0.955 | 71 | 1.0 | 0.02 |

## Blocked rovers (caught: a recovery move within 30 s of the block's start; eligible: no outage and no stand in that time; post: moves within 10 s after the block)

| profile | variant | course | missions | eligible | caught | missed | caught at all | median catch s | latest catch s | post moves | missions with one |
|---|---|---|---|---|---|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 21 | 21 | 0 | 21 | 16.7 | 18.8 | 10 | 10 |
| blockedmid | a0.3 | blocks | 24 | 21 | 21 | 0 | 21 | 16.8 | 18.8 | 10 | 10 |
| blockedmid | a0.3 | boulevard | 24 | 21 | 21 | 0 | 21 | 16.7 | 18.8 | 10 | 10 |
| blockedmid | a0.3:B | bayside | 24 | 21 | 21 | 0 | 22 | 16.6 | 22.6 | 15 | 15 |
| blockedmid | a0.3:B | blocks | 24 | 21 | 21 | 0 | 22 | 16.6 | 22.6 | 15 | 15 |
| blockedmid | a0.3:B | boulevard | 24 | 21 | 21 | 0 | 22 | 16.6 | 22.6 | 15 | 15 |
| blockedmid | warm10 | bayside | 24 | 21 | 21 | 0 | 21 | 16.7 | 18.8 | 5 | 5 |
| blockedmid | warm10 | blocks | 24 | 21 | 21 | 0 | 21 | 16.8 | 18.8 | 5 | 5 |
| blockedmid | warm10 | boulevard | 24 | 21 | 21 | 0 | 21 | 16.7 | 18.8 | 5 | 5 |
| blockedmid | warmstand10 | bayside | 24 | 21 | 21 | 0 | 21 | 16.7 | 18.8 | 10 | 10 |
| blockedmid | warmstand10 | blocks | 24 | 21 | 21 | 0 | 21 | 16.8 | 18.8 | 10 | 10 |
| blockedmid | warmstand10 | boulevard | 24 | 21 | 21 | 0 | 21 | 16.7 | 18.8 | 10 | 10 |
| blockedstart | a0.3 | bayside | 24 | 20 | 20 | 0 | 23 | 9.1 | 11.1 | 10 | 10 |
| blockedstart | a0.3 | blocks | 24 | 20 | 20 | 0 | 23 | 9.1 | 11.1 | 10 | 10 |
| blockedstart | a0.3 | boulevard | 24 | 20 | 20 | 0 | 23 | 9.1 | 11.1 | 10 | 10 |
| blockedstart | a0.3:B | bayside | 24 | 24 | 24 | 0 | 24 | 9.1 | 9.1 | 8 | 8 |
| blockedstart | a0.3:B | blocks | 24 | 24 | 24 | 0 | 24 | 9.1 | 9.1 | 8 | 8 |
| blockedstart | a0.3:B | boulevard | 24 | 24 | 24 | 0 | 24 | 9.1 | 9.1 | 8 | 8 |
| blockedstart | warm10 | bayside | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 2 | 2 |
| blockedstart | warm10 | blocks | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 2 | 2 |
| blockedstart | warm10 | boulevard | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 2 | 2 |
| blockedstart | warmstand10 | bayside | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 9 | 9 |
| blockedstart | warmstand10 | blocks | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 9 | 9 |
| blockedstart | warmstand10 | boulevard | 24 | 20 | 20 | 0 | 21 | 19.1 | 21.1 | 9 | 9 |

## Recovery moves (first before 30 s: at the start; late: moves at or after 30 s)

| profile | variant | course | missions | with a recovery | recoveries | first before 30 s | late | stands | median first s | latest first s |
|---|---|---|---|---|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 24 | 86 | 23 | 63 | 12 | 9.1 | 267.9 |
| blockedmid | a0.3 | blocks | 24 | 24 | 86 | 23 | 63 | 15 | 9.1 | 269.9 |
| blockedmid | a0.3 | boulevard | 24 | 24 | 86 | 23 | 63 | 15 | 9.1 | 269.9 |
| blockedmid | a0.3:B | bayside | 24 | 24 | 89 | 24 | 65 | 15 | 9.1 | 9.1 |
| blockedmid | a0.3:B | blocks | 24 | 24 | 89 | 24 | 65 | 14 | 9.1 | 9.1 |
| blockedmid | a0.3:B | boulevard | 24 | 24 | 89 | 24 | 65 | 8 | 9.1 | 9.1 |
| blockedmid | warm10 | bayside | 24 | 21 | 42 | 0 | 42 | 13 | 435.9 | 611.9 |
| blockedmid | warm10 | blocks | 24 | 21 | 42 | 0 | 42 | 17 | 437.9 | 611.9 |
| blockedmid | warm10 | boulevard | 24 | 21 | 42 | 0 | 42 | 17 | 435.9 | 611.9 |
| blockedmid | warmstand10 | bayside | 24 | 21 | 63 | 0 | 63 | 15 | 435.9 | 611.9 |
| blockedmid | warmstand10 | blocks | 24 | 21 | 63 | 0 | 63 | 16 | 437.9 | 611.9 |
| blockedmid | warmstand10 | boulevard | 24 | 21 | 63 | 0 | 63 | 17 | 435.9 | 611.9 |
| blockedstart | a0.3 | bayside | 24 | 23 | 73 | 23 | 30 | 17 | 9.1 | 11.1 |
| blockedstart | a0.3 | blocks | 24 | 23 | 73 | 23 | 30 | 12 | 9.1 | 11.1 |
| blockedstart | a0.3 | boulevard | 24 | 23 | 73 | 23 | 30 | 15 | 9.1 | 11.1 |
| blockedstart | a0.3:B | bayside | 24 | 24 | 79 | 24 | 31 | 13 | 9.1 | 9.1 |
| blockedstart | a0.3:B | blocks | 24 | 24 | 79 | 24 | 31 | 16 | 9.1 | 9.1 |
| blockedstart | a0.3:B | boulevard | 24 | 24 | 79 | 24 | 31 | 12 | 9.1 | 9.1 |
| blockedstart | warm10 | bayside | 24 | 21 | 35 | 21 | 14 | 15 | 19.1 | 21.1 |
| blockedstart | warm10 | blocks | 24 | 21 | 35 | 21 | 14 | 12 | 19.1 | 21.1 |
| blockedstart | warm10 | boulevard | 24 | 21 | 35 | 21 | 14 | 16 | 19.1 | 21.1 |
| blockedstart | warmstand10 | bayside | 24 | 21 | 56 | 21 | 35 | 16 | 19.1 | 21.1 |
| blockedstart | warmstand10 | blocks | 24 | 21 | 56 | 21 | 35 | 15 | 19.1 | 21.1 |
| blockedstart | warmstand10 | boulevard | 24 | 21 | 56 | 21 | 35 | 16 | 19.1 | 21.1 |
| outage90 | a0.3 | bayside | 24 | 13 | 13 | 13 | 0 | 9 | 9.1 | 11.1 |
| outage90 | a0.3 | blocks | 24 | 13 | 13 | 13 | 0 | 14 | 9.1 | 12.0 |
| outage90 | a0.3 | boulevard | 24 | 13 | 13 | 13 | 0 | 15 | 9.1 | 12.0 |
| outage90 | a0.3:B | bayside | 24 | 11 | 11 | 11 | 0 | 10 | 9.1 | 9.1 |
| outage90 | a0.3:B | blocks | 24 | 14 | 14 | 14 | 0 | 12 | 9.1 | 10.0 |
| outage90 | a0.3:B | boulevard | 24 | 14 | 14 | 14 | 0 | 9 | 9.1 | 10.0 |
| outage90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 12 | None | None |
| outage90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| outage90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| outage90 | warmstand10 | bayside | 24 | 0 | 0 | 0 | 0 | 12 | None | None |
| outage90 | warmstand10 | blocks | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| outage90 | warmstand10 | boulevard | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quiet45 | a0.3 | bayside | 24 | 22 | 22 | 22 | 0 | 17 | 9.1 | 11.1 |
| quiet45 | a0.3 | blocks | 24 | 22 | 22 | 22 | 0 | 19 | 9.1 | 11.1 |
| quiet45 | a0.3 | boulevard | 24 | 22 | 22 | 22 | 0 | 15 | 9.1 | 11.1 |
| quiet45 | a0.3:B | bayside | 24 | 24 | 24 | 24 | 0 | 13 | 9.1 | 9.1 |
| quiet45 | a0.3:B | blocks | 24 | 24 | 24 | 24 | 0 | 16 | 9.1 | 9.1 |
| quiet45 | a0.3:B | boulevard | 24 | 24 | 24 | 24 | 0 | 11 | 9.1 | 9.1 |
| quiet45 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 13 | None | None |
| quiet45 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quiet45 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quiet45 | warmstand10 | bayside | 24 | 0 | 0 | 0 | 0 | 13 | None | None |
| quiet45 | warmstand10 | blocks | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quiet45 | warmstand10 | boulevard | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quiet90 | a0.3 | bayside | 24 | 23 | 23 | 23 | 0 | 10 | 9.1 | 11.1 |
| quiet90 | a0.3 | blocks | 24 | 23 | 23 | 23 | 0 | 14 | 9.1 | 11.1 |
| quiet90 | a0.3 | boulevard | 24 | 23 | 23 | 23 | 0 | 15 | 9.1 | 11.1 |
| quiet90 | a0.3:B | bayside | 24 | 24 | 24 | 24 | 0 | 11 | 9.1 | 9.1 |
| quiet90 | a0.3:B | blocks | 24 | 24 | 24 | 24 | 0 | 10 | 9.1 | 9.1 |
| quiet90 | a0.3:B | boulevard | 24 | 24 | 24 | 24 | 0 | 7 | 9.1 | 9.1 |
| quiet90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quiet90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quiet90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quiet90 | warmstand10 | bayside | 24 | 0 | 0 | 0 | 0 | 11 | None | None |
| quiet90 | warmstand10 | blocks | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quiet90 | warmstand10 | boulevard | 24 | 0 | 0 | 0 | 0 | 14 | None | None |
| quietdrift90 | a0.3 | bayside | 24 | 22 | 22 | 22 | 0 | 14 | 9.1 | 11.1 |
| quietdrift90 | a0.3 | blocks | 24 | 23 | 23 | 23 | 0 | 15 | 9.1 | 11.1 |
| quietdrift90 | a0.3 | boulevard | 24 | 23 | 23 | 23 | 0 | 14 | 9.1 | 11.1 |
| quietdrift90 | a0.3:B | bayside | 24 | 24 | 24 | 24 | 0 | 10 | 9.1 | 9.1 |
| quietdrift90 | a0.3:B | blocks | 24 | 24 | 25 | 24 | 1 | 13 | 9.1 | 9.1 |
| quietdrift90 | a0.3:B | boulevard | 24 | 24 | 24 | 24 | 0 | 10 | 9.1 | 9.1 |
| quietdrift90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quietdrift90 | warm10 | blocks | 24 | 1 | 1 | 0 | 1 | 17 | 1021.9 | 1021.9 |
| quietdrift90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 15 | None | None |
| quietdrift90 | warmstand10 | bayside | 24 | 0 | 0 | 0 | 0 | 16 | None | None |
| quietdrift90 | warmstand10 | blocks | 24 | 1 | 1 | 0 | 1 | 17 | 1021.9 | 1021.9 |
| quietdrift90 | warmstand10 | boulevard | 24 | 0 | 0 | 0 | 0 | 15 | None | None |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| blockedmid | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0027 |
| blockedstart | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | 0.0 |
| outage90 | warm10 | a0.3 | 2/3 | 0 | 0 | 0 | 0.0 |
| quiet45 | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0048 |
| quiet90 | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0042 |
| quietdrift90 | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0014 |
| blockedmid | warmstand10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.002 |
| blockedstart | warmstand10 | a0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | warmstand10 | a0.3 | 2/3 | 0 | 0 | 0 | 0.0 |
| quiet45 | warmstand10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0048 |
| quiet90 | warmstand10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0042 |
| quietdrift90 | warmstand10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0014 |
| blockedmid | warmstand10 | warm10 | 0/3 | 1 | 0 | 0 | 0.0 |
| blockedstart | warmstand10 | warm10 | 0/3 | 3 | 0 | 0 | 0.0006 |
| outage90 | warmstand10 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| quiet45 | warmstand10 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| quiet90 | warmstand10 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| quietdrift90 | warmstand10 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| blockedmid | warm10 | a0.3 | bayside | 15 | 0 | -4.0 | -0.0027 | 0.0001 |
| blockedmid | warm10 | a0.3 | blocks | 12 | 1 | -1.0 | -0.0006 | 0.0034 |
| blockedmid | warm10 | a0.3 | boulevard | 13 | 1 | -5.0 | -0.0027 | 0.0018 |
| blockedstart | warm10 | a0.3 | bayside | 9 | 0 | 0.0 | 0.0 | 0.0039 |
| blockedstart | warm10 | a0.3 | blocks | 8 | 1 | 0.0 | 0.0 | 0.0391 |
| blockedstart | warm10 | a0.3 | boulevard | 9 | 1 | 0.0 | 0.0 | 0.0215 |
| outage90 | warm10 | a0.3 | bayside | 8 | 0 | 0.0 | 0.0 | 0.0078 |
| outage90 | warm10 | a0.3 | blocks | 5 | 1 | 0.0 | 0.0 | 0.2188 |
| outage90 | warm10 | a0.3 | boulevard | 7 | 0 | 0.0 | 0.0 | 0.0156 |
| quiet45 | warm10 | a0.3 | bayside | 17 | 0 | -7.0 | -0.0048 | 0.0 |
| quiet45 | warm10 | a0.3 | blocks | 15 | 0 | -4.0 | -0.0025 | 0.0001 |
| quiet45 | warm10 | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| quiet90 | warm10 | a0.3 | bayside | 16 | 0 | -6.0 | -0.0042 | 0.0 |
| quiet90 | warm10 | a0.3 | blocks | 12 | 0 | -1.0 | -0.0006 | 0.0005 |
| quiet90 | warm10 | a0.3 | boulevard | 13 | 0 | -6.0 | -0.0033 | 0.0002 |
| quietdrift90 | warm10 | a0.3 | bayside | 12 | 1 | -2.0 | -0.0014 | 0.0034 |
| quietdrift90 | warm10 | a0.3 | blocks | 12 | 2 | -1.0 | -0.0006 | 0.0129 |
| quietdrift90 | warm10 | a0.3 | boulevard | 12 | 0 | -1.0 | -0.0006 | 0.0005 |
| blockedmid | warmstand10 | a0.3 | bayside | 14 | 0 | -3.0 | -0.002 | 0.0001 |
| blockedmid | warmstand10 | a0.3 | blocks | 10 | 1 | 0.0 | 0.0 | 0.0117 |
| blockedmid | warmstand10 | a0.3 | boulevard | 11 | 0 | 0.0 | 0.0 | 0.001 |
| blockedstart | warmstand10 | a0.3 | bayside | 3 | 2 | 0.0 | 0.0 | 1.0 |
| blockedstart | warmstand10 | a0.3 | blocks | 2 | 6 | 0.0 | 0.0 | 0.2891 |
| blockedstart | warmstand10 | a0.3 | boulevard | 4 | 3 | 0.0 | 0.0 | 1.0 |
| outage90 | warmstand10 | a0.3 | bayside | 8 | 0 | 0.0 | 0.0 | 0.0078 |
| outage90 | warmstand10 | a0.3 | blocks | 5 | 1 | 0.0 | 0.0 | 0.2188 |
| outage90 | warmstand10 | a0.3 | boulevard | 7 | 0 | 0.0 | 0.0 | 0.0156 |
| quiet45 | warmstand10 | a0.3 | bayside | 17 | 0 | -7.0 | -0.0048 | 0.0 |
| quiet45 | warmstand10 | a0.3 | blocks | 15 | 0 | -4.0 | -0.0025 | 0.0001 |
| quiet45 | warmstand10 | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| quiet90 | warmstand10 | a0.3 | bayside | 16 | 0 | -6.0 | -0.0042 | 0.0 |
| quiet90 | warmstand10 | a0.3 | blocks | 12 | 0 | -1.0 | -0.0006 | 0.0005 |
| quiet90 | warmstand10 | a0.3 | boulevard | 13 | 0 | -6.0 | -0.0033 | 0.0002 |
| quietdrift90 | warmstand10 | a0.3 | bayside | 12 | 1 | -2.0 | -0.0014 | 0.0034 |
| quietdrift90 | warmstand10 | a0.3 | blocks | 12 | 2 | -1.0 | -0.0006 | 0.0129 |
| quietdrift90 | warmstand10 | a0.3 | boulevard | 12 | 0 | -1.0 | -0.0006 | 0.0005 |
| blockedmid | warmstand10 | warm10 | bayside | 2 | 7 | 0.0 | 0.0 | 0.1797 |
| blockedmid | warmstand10 | warm10 | blocks | 1 | 6 | 0.0 | 0.0 | 0.125 |
| blockedmid | warmstand10 | warm10 | boulevard | 1 | 8 | 0.0 | 0.0 | 0.0391 |
| blockedstart | warmstand10 | warm10 | bayside | 0 | 9 | 0.0 | 0.0 | 0.0039 |
| blockedstart | warmstand10 | warm10 | blocks | 1 | 12 | 1.0 | 0.0006 | 0.0034 |
| blockedstart | warmstand10 | warm10 | boulevard | 1 | 9 | 0.0 | 0.0 | 0.0215 |
| outage90 | warmstand10 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage90 | warmstand10 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| outage90 | warmstand10 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quiet45 | warmstand10 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| quiet45 | warmstand10 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| quiet45 | warmstand10 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | warmstand10 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | warmstand10 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | warmstand10 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quietdrift90 | warmstand10 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| quietdrift90 | warmstand10 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| quietdrift90 | warmstand10 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| a0.3 | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0272 |
| a0.3 | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0355 |
| warm10 | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0273 |
| warm10 | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0363 |
| warmstand10 | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0322 |
| warmstand10 | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0369 |
| a0.3:B | blockedstart | quiet90 | 0/3 | 3 | 0 | 0 | 0.0402 |
| a0.3:B | blockedmid | quiet90 | 0/3 | 3 | 0 | 0 | 0.0383 |

## The pilot's worst idea of where it is, per mission (over 20 m: thrown off)

| profile | variant | course | missions | median of max m | largest m | missions over 20 m |
|---|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 61.33 | 84.4 | 21 |
| blockedmid | a0.3 | blocks | 24 | 54.38 | 62.11 | 21 |
| blockedmid | a0.3 | boulevard | 24 | 63.51 | 82.41 | 21 |
| blockedmid | a0.3:B | bayside | 24 | 61.09 | 63.84 | 20 |
| blockedmid | a0.3:B | blocks | 24 | 56.27 | 61.48 | 20 |
| blockedmid | a0.3:B | boulevard | 24 | 63.14 | 68.07 | 22 |
| blockedmid | warm10 | bayside | 24 | 60.96 | 82.64 | 21 |
| blockedmid | warm10 | blocks | 24 | 53.75 | 61.9 | 21 |
| blockedmid | warm10 | boulevard | 24 | 63.44 | 82.05 | 21 |
| blockedmid | warmstand10 | bayside | 24 | 61.16 | 82.64 | 21 |
| blockedmid | warmstand10 | blocks | 24 | 51.94 | 62.48 | 21 |
| blockedmid | warmstand10 | boulevard | 24 | 63.48 | 82.05 | 21 |
| blockedstart | a0.3 | bayside | 24 | 61.62 | 85.56 | 20 |
| blockedstart | a0.3 | blocks | 24 | 58.27 | 62.66 | 21 |
| blockedstart | a0.3 | boulevard | 24 | 63.7 | 90.42 | 21 |
| blockedstart | a0.3:B | bayside | 24 | 61.28 | 64.61 | 20 |
| blockedstart | a0.3:B | blocks | 24 | 55.34 | 61.94 | 20 |
| blockedstart | a0.3:B | boulevard | 24 | 63.39 | 65.84 | 21 |
| blockedstart | warm10 | bayside | 24 | 61.55 | 85.56 | 21 |
| blockedstart | warm10 | blocks | 24 | 58.97 | 62.32 | 21 |
| blockedstart | warm10 | boulevard | 24 | 63.56 | 90.24 | 21 |
| blockedstart | warmstand10 | bayside | 24 | 61.71 | 85.68 | 20 |
| blockedstart | warmstand10 | blocks | 24 | 58.0 | 62.66 | 21 |
| blockedstart | warmstand10 | boulevard | 24 | 63.54 | 89.8 | 21 |
| outage90 | a0.3 | bayside | 24 | 61.43 | 87.46 | 21 |
| outage90 | a0.3 | blocks | 24 | 58.81 | 63.04 | 21 |
| outage90 | a0.3 | boulevard | 24 | 63.53 | 82.22 | 21 |
| outage90 | a0.3:B | bayside | 24 | 61.2 | 63.95 | 20 |
| outage90 | a0.3:B | blocks | 24 | 55.81 | 64.57 | 21 |
| outage90 | a0.3:B | boulevard | 24 | 63.36 | 65.3 | 22 |
| outage90 | warm10 | bayside | 24 | 61.39 | 84.97 | 21 |
| outage90 | warm10 | blocks | 24 | 58.99 | 63.05 | 21 |
| outage90 | warm10 | boulevard | 24 | 63.67 | 82.22 | 21 |
| outage90 | warmstand10 | bayside | 24 | 61.39 | 84.97 | 21 |
| outage90 | warmstand10 | blocks | 24 | 58.99 | 63.05 | 21 |
| outage90 | warmstand10 | boulevard | 24 | 63.67 | 82.22 | 21 |
| quiet45 | a0.3 | bayside | 24 | 35.91 | 54.63 | 24 |
| quiet45 | a0.3 | blocks | 24 | 35.28 | 53.49 | 24 |
| quiet45 | a0.3 | boulevard | 24 | 36.34 | 55.6 | 24 |
| quiet45 | a0.3:B | bayside | 24 | 35.28 | 51.03 | 22 |
| quiet45 | a0.3:B | blocks | 24 | 35.12 | 39.42 | 22 |
| quiet45 | a0.3:B | boulevard | 24 | 36.02 | 58.08 | 23 |
| quiet45 | warm10 | bayside | 24 | 36.16 | 54.8 | 24 |
| quiet45 | warm10 | blocks | 24 | 35.49 | 52.36 | 24 |
| quiet45 | warm10 | boulevard | 24 | 36.73 | 55.6 | 24 |
| quiet45 | warmstand10 | bayside | 24 | 36.16 | 54.8 | 24 |
| quiet45 | warmstand10 | blocks | 24 | 35.49 | 52.36 | 24 |
| quiet45 | warmstand10 | boulevard | 24 | 36.73 | 55.6 | 24 |
| quiet90 | a0.3 | bayside | 24 | 60.89 | 84.4 | 21 |
| quiet90 | a0.3 | blocks | 24 | 59.27 | 62.14 | 21 |
| quiet90 | a0.3 | boulevard | 24 | 63.41 | 82.05 | 21 |
| quiet90 | a0.3:B | bayside | 24 | 60.73 | 63.84 | 20 |
| quiet90 | a0.3:B | blocks | 24 | 56.51 | 63.86 | 21 |
| quiet90 | a0.3:B | boulevard | 24 | 63.29 | 65.86 | 22 |
| quiet90 | warm10 | bayside | 24 | 61.04 | 82.64 | 21 |
| quiet90 | warm10 | blocks | 24 | 59.41 | 63.71 | 21 |
| quiet90 | warm10 | boulevard | 24 | 63.33 | 82.05 | 21 |
| quiet90 | warmstand10 | bayside | 24 | 61.04 | 82.64 | 21 |
| quiet90 | warmstand10 | blocks | 24 | 59.41 | 63.71 | 21 |
| quiet90 | warmstand10 | boulevard | 24 | 63.33 | 82.05 | 21 |
| quietdrift90 | a0.3 | bayside | 24 | 60.97 | 73.21 | 21 |
| quietdrift90 | a0.3 | blocks | 24 | 58.61 | 62.68 | 21 |
| quietdrift90 | a0.3 | boulevard | 24 | 63.28 | 85.18 | 21 |
| quietdrift90 | a0.3:B | bayside | 24 | 60.75 | 63.94 | 20 |
| quietdrift90 | a0.3:B | blocks | 24 | 55.93 | 62.56 | 21 |
| quietdrift90 | a0.3:B | boulevard | 24 | 62.98 | 66.02 | 22 |
| quietdrift90 | warm10 | bayside | 24 | 61.22 | 72.81 | 21 |
| quietdrift90 | warm10 | blocks | 24 | 58.64 | 62.64 | 21 |
| quietdrift90 | warm10 | boulevard | 24 | 63.2 | 80.75 | 21 |
| quietdrift90 | warmstand10 | bayside | 24 | 61.22 | 72.81 | 21 |
| quietdrift90 | warmstand10 | blocks | 24 | 58.64 | 62.64 | 21 |
| quietdrift90 | warmstand10 | boulevard | 24 | 63.2 | 80.75 | 21 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 6.28 | 8.36 |
| blockedmid | a0.3 | blocks | 24 | 6.21 | 8.18 |
| blockedmid | a0.3 | boulevard | 24 | 6.31 | 8.61 |
| blockedmid | a0.3:B | bayside | 24 | 6.32 | 8.2 |
| blockedmid | a0.3:B | blocks | 24 | 6.22 | 8.09 |
| blockedmid | a0.3:B | boulevard | 24 | 6.34 | 8.25 |
| blockedmid | warm10 | bayside | 24 | 6.27 | 8.36 |
| blockedmid | warm10 | blocks | 24 | 6.2 | 8.23 |
| blockedmid | warm10 | boulevard | 24 | 6.31 | 8.68 |
| blockedmid | warmstand10 | bayside | 24 | 6.29 | 8.33 |
| blockedmid | warmstand10 | blocks | 24 | 6.2 | 8.22 |
| blockedmid | warmstand10 | boulevard | 24 | 6.31 | 8.68 |
| blockedstart | a0.3 | bayside | 24 | 6.5 | 8.69 |
| blockedstart | a0.3 | blocks | 24 | 6.36 | 8.43 |
| blockedstart | a0.3 | boulevard | 24 | 6.49 | 8.82 |
| blockedstart | a0.3:B | bayside | 24 | 6.55 | 8.48 |
| blockedstart | a0.3:B | blocks | 24 | 6.39 | 8.19 |
| blockedstart | a0.3:B | boulevard | 24 | 6.51 | 8.61 |
| blockedstart | warm10 | bayside | 24 | 6.45 | 8.6 |
| blockedstart | warm10 | blocks | 24 | 6.27 | 8.34 |
| blockedstart | warm10 | boulevard | 24 | 6.41 | 8.75 |
| blockedstart | warmstand10 | bayside | 24 | 6.45 | 8.6 |
| blockedstart | warmstand10 | blocks | 24 | 6.33 | 8.34 |
| blockedstart | warmstand10 | boulevard | 24 | 6.45 | 8.75 |
| outage90 | a0.3 | bayside | 24 | 6.39 | 8.9 |
| outage90 | a0.3 | blocks | 24 | 6.39 | 8.52 |
| outage90 | a0.3 | boulevard | 24 | 6.51 | 9.0 |
| outage90 | a0.3:B | bayside | 24 | 6.44 | 8.66 |
| outage90 | a0.3:B | blocks | 24 | 6.36 | 8.52 |
| outage90 | a0.3:B | boulevard | 24 | 6.46 | 8.71 |
| outage90 | warm10 | bayside | 24 | 6.45 | 8.9 |
| outage90 | warm10 | blocks | 24 | 6.42 | 8.6 |
| outage90 | warm10 | boulevard | 24 | 6.59 | 9.08 |
| outage90 | warmstand10 | bayside | 24 | 6.45 | 8.9 |
| outage90 | warmstand10 | blocks | 24 | 6.42 | 8.6 |
| outage90 | warmstand10 | boulevard | 24 | 6.59 | 9.08 |
| quiet45 | a0.3 | bayside | 24 | 6.38 | 8.99 |
| quiet45 | a0.3 | blocks | 24 | 6.29 | 9.0 |
| quiet45 | a0.3 | boulevard | 24 | 6.42 | 9.12 |
| quiet45 | a0.3:B | bayside | 24 | 6.39 | 8.7 |
| quiet45 | a0.3:B | blocks | 24 | 6.28 | 8.7 |
| quiet45 | a0.3:B | boulevard | 24 | 6.41 | 9.16 |
| quiet45 | warm10 | bayside | 24 | 6.42 | 9.34 |
| quiet45 | warm10 | blocks | 24 | 6.33 | 9.3 |
| quiet45 | warm10 | boulevard | 24 | 6.49 | 9.41 |
| quiet45 | warmstand10 | bayside | 24 | 6.42 | 9.34 |
| quiet45 | warmstand10 | blocks | 24 | 6.33 | 9.3 |
| quiet45 | warmstand10 | boulevard | 24 | 6.49 | 9.41 |
| quiet90 | a0.3 | bayside | 24 | 6.37 | 8.36 |
| quiet90 | a0.3 | blocks | 24 | 6.27 | 8.22 |
| quiet90 | a0.3 | boulevard | 24 | 6.38 | 8.52 |
| quiet90 | a0.3:B | bayside | 24 | 6.42 | 8.23 |
| quiet90 | a0.3:B | blocks | 24 | 6.33 | 8.1 |
| quiet90 | a0.3:B | boulevard | 24 | 6.41 | 8.26 |
| quiet90 | warm10 | bayside | 24 | 6.41 | 8.39 |
| quiet90 | warm10 | blocks | 24 | 6.33 | 8.3 |
| quiet90 | warm10 | boulevard | 24 | 6.44 | 8.69 |
| quiet90 | warmstand10 | bayside | 24 | 6.41 | 8.39 |
| quiet90 | warmstand10 | blocks | 24 | 6.33 | 8.3 |
| quiet90 | warmstand10 | boulevard | 24 | 6.44 | 8.69 |
| quietdrift90 | a0.3 | bayside | 24 | 6.4 | 8.64 |
| quietdrift90 | a0.3 | blocks | 24 | 6.35 | 8.59 |
| quietdrift90 | a0.3 | boulevard | 24 | 6.44 | 8.71 |
| quietdrift90 | a0.3:B | bayside | 24 | 6.44 | 8.7 |
| quietdrift90 | a0.3:B | blocks | 24 | 6.33 | 8.58 |
| quietdrift90 | a0.3:B | boulevard | 24 | 6.44 | 8.84 |
| quietdrift90 | warm10 | bayside | 24 | 6.48 | 8.7 |
| quietdrift90 | warm10 | blocks | 24 | 6.44 | 8.59 |
| quietdrift90 | warm10 | boulevard | 24 | 6.57 | 8.85 |
| quietdrift90 | warmstand10 | bayside | 24 | 6.48 | 8.7 |
| quietdrift90 | warmstand10 | blocks | 24 | 6.44 | 8.59 |
| quietdrift90 | warmstand10 | boulevard | 24 | 6.57 | 8.85 |

## Recovery moves and filter restarts (medians)

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 4.0 | None |
| blockedmid | a0.3 | blocks | 24 | 4.0 | None |
| blockedmid | a0.3 | boulevard | 24 | 4.0 | None |
| blockedmid | a0.3:B | bayside | 24 | 4.0 | None |
| blockedmid | a0.3:B | blocks | 24 | 4.0 | None |
| blockedmid | a0.3:B | boulevard | 24 | 4.0 | None |
| blockedmid | warm10 | bayside | 24 | 2.0 | None |
| blockedmid | warm10 | blocks | 24 | 2.0 | None |
| blockedmid | warm10 | boulevard | 24 | 2.0 | None |
| blockedmid | warmstand10 | bayside | 24 | 3.0 | None |
| blockedmid | warmstand10 | blocks | 24 | 3.0 | None |
| blockedmid | warmstand10 | boulevard | 24 | 3.0 | None |
| blockedstart | a0.3 | bayside | 24 | 3.0 | None |
| blockedstart | a0.3 | blocks | 24 | 3.0 | None |
| blockedstart | a0.3 | boulevard | 24 | 3.0 | None |
| blockedstart | a0.3:B | bayside | 24 | 3.0 | None |
| blockedstart | a0.3:B | blocks | 24 | 3.0 | None |
| blockedstart | a0.3:B | boulevard | 24 | 3.0 | None |
| blockedstart | warm10 | bayside | 24 | 2.0 | None |
| blockedstart | warm10 | blocks | 24 | 2.0 | None |
| blockedstart | warm10 | boulevard | 24 | 2.0 | None |
| blockedstart | warmstand10 | bayside | 24 | 3.0 | None |
| blockedstart | warmstand10 | blocks | 24 | 3.0 | None |
| blockedstart | warmstand10 | boulevard | 24 | 3.0 | None |
| outage90 | a0.3 | bayside | 24 | 1.0 | None |
| outage90 | a0.3 | blocks | 24 | 1.0 | None |
| outage90 | a0.3 | boulevard | 24 | 1.0 | None |
| outage90 | a0.3:B | bayside | 24 | 0.0 | None |
| outage90 | a0.3:B | blocks | 24 | 1.0 | None |
| outage90 | a0.3:B | boulevard | 24 | 1.0 | None |
| outage90 | warm10 | bayside | 24 | 0.0 | None |
| outage90 | warm10 | blocks | 24 | 0.0 | None |
| outage90 | warm10 | boulevard | 24 | 0.0 | None |
| outage90 | warmstand10 | bayside | 24 | 0.0 | None |
| outage90 | warmstand10 | blocks | 24 | 0.0 | None |
| outage90 | warmstand10 | boulevard | 24 | 0.0 | None |
| quiet45 | a0.3 | bayside | 24 | 1.0 | None |
| quiet45 | a0.3 | blocks | 24 | 1.0 | None |
| quiet45 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet45 | a0.3:B | bayside | 24 | 1.0 | None |
| quiet45 | a0.3:B | blocks | 24 | 1.0 | None |
| quiet45 | a0.3:B | boulevard | 24 | 1.0 | None |
| quiet45 | warm10 | bayside | 24 | 0.0 | None |
| quiet45 | warm10 | blocks | 24 | 0.0 | None |
| quiet45 | warm10 | boulevard | 24 | 0.0 | None |
| quiet45 | warmstand10 | bayside | 24 | 0.0 | None |
| quiet45 | warmstand10 | blocks | 24 | 0.0 | None |
| quiet45 | warmstand10 | boulevard | 24 | 0.0 | None |
| quiet90 | a0.3 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet90 | a0.3:B | bayside | 24 | 1.0 | None |
| quiet90 | a0.3:B | blocks | 24 | 1.0 | None |
| quiet90 | a0.3:B | boulevard | 24 | 1.0 | None |
| quiet90 | warm10 | bayside | 24 | 0.0 | None |
| quiet90 | warm10 | blocks | 24 | 0.0 | None |
| quiet90 | warm10 | boulevard | 24 | 0.0 | None |
| quiet90 | warmstand10 | bayside | 24 | 0.0 | None |
| quiet90 | warmstand10 | blocks | 24 | 0.0 | None |
| quiet90 | warmstand10 | boulevard | 24 | 0.0 | None |
| quietdrift90 | a0.3 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3 | boulevard | 24 | 1.0 | None |
| quietdrift90 | a0.3:B | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3:B | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3:B | boulevard | 24 | 1.0 | None |
| quietdrift90 | warm10 | bayside | 24 | 0.0 | None |
| quietdrift90 | warm10 | blocks | 24 | 0.0 | None |
| quietdrift90 | warm10 | boulevard | 24 | 0.0 | None |
| quietdrift90 | warmstand10 | bayside | 24 | 0.0 | None |
| quietdrift90 | warmstand10 | blocks | 24 | 0.0 | None |
| quietdrift90 | warmstand10 | boulevard | 24 | 0.0 | None |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| blockedmid | a0.3 | blocks | 24 | 9.0 | 1.06 | 3.58 | 5.15 | 1.96 | 3.96 |
| blockedmid | a0.3:B | blocks | 24 | 9.0 | 0.83 | 2.64 | 4.48 | 2.0 | 2.96 |
| blockedmid | warm10 | blocks | 24 | 9.0 | 1.0 | 3.43 | 5.38 | 1.94 | 2.95 |
| blockedmid | warmstand10 | blocks | 24 | 9.0 | 1.04 | 3.51 | 5.47 | 1.97 | 3.31 |
| blockedstart | a0.3 | blocks | 24 | 9.0 | 0.98 | 3.09 | 4.88 | 1.99 | 3.04 |
| blockedstart | a0.3:B | blocks | 24 | 9.0 | 0.87 | 2.74 | 4.63 | 1.98 | 2.72 |
| blockedstart | warm10 | blocks | 24 | 9.0 | 1.02 | 3.07 | 4.94 | 2.03 | 3.08 |
| blockedstart | warmstand10 | blocks | 24 | 9.0 | 1.03 | 2.91 | 4.83 | 2.0 | 2.9 |
| outage90 | a0.3 | blocks | 24 | 9.0 | 1.2 | 3.42 | 5.68 | 2.39 | 4.17 |
| outage90 | a0.3:B | blocks | 24 | 9.0 | 1.12 | 3.1 | 4.81 | 2.09 | 3.37 |
| outage90 | warm10 | blocks | 24 | 9.0 | 1.13 | 4.26 | 6.09 | 2.29 | 5.42 |
| outage90 | warmstand10 | blocks | 24 | 9.0 | 1.13 | 4.26 | 6.09 | 2.29 | 5.42 |
| quiet45 | a0.3 | blocks | 24 | 9.0 | 0.88 | 3.32 | 5.0 | 2.05 | 3.88 |
| quiet45 | a0.3:B | blocks | 24 | 9.0 | 0.81 | 2.76 | 4.62 | 2.0 | 3.13 |
| quiet45 | warm10 | blocks | 24 | 9.0 | 1.04 | 3.79 | 4.89 | 2.08 | 4.51 |
| quiet45 | warmstand10 | blocks | 24 | 9.0 | 1.04 | 3.79 | 4.89 | 2.08 | 4.51 |
| quiet90 | a0.3 | blocks | 24 | 9.0 | 0.98 | 3.09 | 4.94 | 2.04 | 3.67 |
| quiet90 | a0.3:B | blocks | 24 | 9.0 | 0.91 | 2.76 | 4.64 | 2.0 | 3.19 |
| quiet90 | warm10 | blocks | 24 | 9.0 | 0.96 | 3.17 | 5.08 | 1.98 | 3.23 |
| quiet90 | warmstand10 | blocks | 24 | 9.0 | 0.96 | 3.17 | 5.08 | 1.98 | 3.23 |
| quietdrift90 | a0.3 | blocks | 24 | 9.0 | 1.54 | 5.36 | 8.19 | 2.07 | 5.82 |
| quietdrift90 | a0.3:B | blocks | 24 | 9.0 | 1.62 | 4.84 | 8.09 | 2.19 | 4.96 |
| quietdrift90 | warm10 | blocks | 24 | 9.0 | 1.44 | 5.05 | 6.67 | 2.3 | 5.09 |
| quietdrift90 | warmstand10 | blocks | 24 | 9.0 | 1.44 | 5.05 | 6.67 | 2.3 | 5.09 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 0.23 | 3.32 |
| blockedmid | a0.3 | blocks | 24 | 0.35 | 3.71 |
| blockedmid | a0.3 | boulevard | 24 | 0.17 | 1.08 |
| blockedmid | a0.3:B | bayside | 24 | 0.21 | 2.14 |
| blockedmid | a0.3:B | blocks | 24 | 0.3 | 2.88 |
| blockedmid | a0.3:B | boulevard | 24 | 0.14 | 0.74 |
| blockedmid | warm10 | bayside | 24 | 0.22 | 2.74 |
| blockedmid | warm10 | blocks | 24 | 0.35 | 3.58 |
| blockedmid | warm10 | boulevard | 24 | 0.16 | 0.97 |
| blockedmid | warmstand10 | bayside | 24 | 0.23 | 2.68 |
| blockedmid | warmstand10 | blocks | 24 | 0.35 | 3.54 |
| blockedmid | warmstand10 | boulevard | 24 | 0.15 | 0.92 |
| blockedstart | a0.3 | bayside | 24 | 0.21 | 2.39 |
| blockedstart | a0.3 | blocks | 24 | 0.29 | 2.87 |
| blockedstart | a0.3 | boulevard | 24 | 0.16 | 0.93 |
| blockedstart | a0.3:B | bayside | 24 | 0.2 | 1.97 |
| blockedstart | a0.3:B | blocks | 24 | 0.27 | 2.74 |
| blockedstart | a0.3:B | boulevard | 24 | 0.14 | 0.73 |
| blockedstart | warm10 | bayside | 24 | 0.21 | 2.15 |
| blockedstart | warm10 | blocks | 24 | 0.29 | 2.79 |
| blockedstart | warm10 | boulevard | 24 | 0.14 | 0.82 |
| blockedstart | warmstand10 | bayside | 24 | 0.21 | 2.49 |
| blockedstart | warmstand10 | blocks | 24 | 0.29 | 2.84 |
| blockedstart | warmstand10 | boulevard | 24 | 0.15 | 0.84 |
| outage90 | a0.3 | bayside | 24 | 0.58 | 4.28 |
| outage90 | a0.3 | blocks | 24 | 0.78 | 4.38 |
| outage90 | a0.3 | boulevard | 24 | 0.62 | 3.6 |
| outage90 | a0.3:B | bayside | 24 | 0.54 | 2.88 |
| outage90 | a0.3:B | blocks | 24 | 0.79 | 3.44 |
| outage90 | a0.3:B | boulevard | 24 | 0.59 | 3.47 |
| outage90 | warm10 | bayside | 24 | 0.59 | 3.71 |
| outage90 | warm10 | blocks | 24 | 0.81 | 4.3 |
| outage90 | warm10 | boulevard | 24 | 0.64 | 4.38 |
| outage90 | warmstand10 | bayside | 24 | 0.59 | 3.71 |
| outage90 | warmstand10 | blocks | 24 | 0.81 | 4.3 |
| outage90 | warmstand10 | boulevard | 24 | 0.64 | 4.38 |
| quiet45 | a0.3 | bayside | 24 | 0.22 | 2.08 |
| quiet45 | a0.3 | blocks | 24 | 0.3 | 3.15 |
| quiet45 | a0.3 | boulevard | 24 | 0.15 | 0.95 |
| quiet45 | a0.3:B | bayside | 24 | 0.22 | 2.03 |
| quiet45 | a0.3:B | blocks | 24 | 0.32 | 2.93 |
| quiet45 | a0.3:B | boulevard | 24 | 0.15 | 0.94 |
| quiet45 | warm10 | bayside | 24 | 0.22 | 1.85 |
| quiet45 | warm10 | blocks | 24 | 0.32 | 3.11 |
| quiet45 | warm10 | boulevard | 24 | 0.15 | 0.84 |
| quiet45 | warmstand10 | bayside | 24 | 0.22 | 1.85 |
| quiet45 | warmstand10 | blocks | 24 | 0.32 | 3.11 |
| quiet45 | warmstand10 | boulevard | 24 | 0.15 | 0.84 |
| quiet90 | a0.3 | bayside | 24 | 0.21 | 2.85 |
| quiet90 | a0.3 | blocks | 24 | 0.34 | 3.59 |
| quiet90 | a0.3 | boulevard | 24 | 0.15 | 0.96 |
| quiet90 | a0.3:B | bayside | 24 | 0.21 | 2.32 |
| quiet90 | a0.3:B | blocks | 24 | 0.27 | 3.04 |
| quiet90 | a0.3:B | boulevard | 24 | 0.15 | 0.72 |
| quiet90 | warm10 | bayside | 24 | 0.21 | 2.41 |
| quiet90 | warm10 | blocks | 24 | 0.34 | 3.41 |
| quiet90 | warm10 | boulevard | 24 | 0.15 | 0.89 |
| quiet90 | warmstand10 | bayside | 24 | 0.21 | 2.41 |
| quiet90 | warmstand10 | blocks | 24 | 0.34 | 3.41 |
| quiet90 | warmstand10 | boulevard | 24 | 0.15 | 0.89 |
| quietdrift90 | a0.3 | bayside | 24 | 1.46 | 6.03 |
| quietdrift90 | a0.3 | blocks | 24 | 1.61 | 6.52 |
| quietdrift90 | a0.3 | boulevard | 24 | 1.52 | 6.24 |
| quietdrift90 | a0.3:B | bayside | 24 | 1.39 | 5.9 |
| quietdrift90 | a0.3:B | blocks | 24 | 1.67 | 5.96 |
| quietdrift90 | a0.3:B | boulevard | 24 | 1.65 | 7.32 |
| quietdrift90 | warm10 | bayside | 24 | 1.46 | 6.16 |
| quietdrift90 | warm10 | blocks | 24 | 1.63 | 6.47 |
| quietdrift90 | warm10 | boulevard | 24 | 1.48 | 6.56 |
| quietdrift90 | warmstand10 | bayside | 24 | 1.46 | 6.16 |
| quietdrift90 | warmstand10 | blocks | 24 | 1.63 | 6.47 |
| quietdrift90 | warmstand10 | boulevard | 24 | 1.48 | 6.56 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 7.29 | 16.38 | 0 | 0 |
| blockedmid | a0.3 | blocks | 24 | 7.51 | 21.87 | 0 | 0 |
| blockedmid | a0.3 | boulevard | 24 | 7.46 | 7.97 | 0 | 0 |
| blockedmid | a0.3:B | bayside | 24 | 7.24 | 15.85 | 0 | 0 |
| blockedmid | a0.3:B | blocks | 24 | 7.42 | 8.46 | 0 | 0 |
| blockedmid | a0.3:B | boulevard | 24 | 7.37 | 8.19 | 0 | 0 |
| blockedmid | warm10 | bayside | 24 | 6.69 | 17.41 | 0 | 0 |
| blockedmid | warm10 | blocks | 24 | 7.55 | 25.46 | 0 | 0 |
| blockedmid | warm10 | boulevard | 24 | 7.12 | 7.7 | 0 | 0 |
| blockedmid | warmstand10 | bayside | 24 | 6.69 | 17.41 | 0 | 0 |
| blockedmid | warmstand10 | blocks | 24 | 7.39 | 25.46 | 0 | 0 |
| blockedmid | warmstand10 | boulevard | 24 | 7.12 | 7.7 | 0 | 0 |
| blockedstart | a0.3 | bayside | 24 | 6.62 | 8.16 | 0 | 0 |
| blockedstart | a0.3 | blocks | 24 | 7.11 | 8.96 | 0 | 0 |
| blockedstart | a0.3 | boulevard | 24 | 6.98 | 7.92 | 0 | 0 |
| blockedstart | a0.3:B | bayside | 24 | 6.77 | 7.82 | 0 | 0 |
| blockedstart | a0.3:B | blocks | 24 | 7.12 | 8.35 | 0 | 0 |
| blockedstart | a0.3:B | boulevard | 24 | 6.95 | 7.72 | 0 | 0 |
| blockedstart | warm10 | bayside | 24 | 6.5 | 7.36 | 0 | 0 |
| blockedstart | warm10 | blocks | 24 | 6.91 | 8.93 | 0 | 0 |
| blockedstart | warm10 | boulevard | 24 | 6.82 | 7.45 | 0 | 0 |
| blockedstart | warmstand10 | bayside | 24 | 6.87 | 8.3 | 0 | 0 |
| blockedstart | warmstand10 | blocks | 24 | 7.29 | 8.93 | 0 | 0 |
| blockedstart | warmstand10 | boulevard | 24 | 7.11 | 7.99 | 0 | 0 |
| outage90 | a0.3 | bayside | 24 | 7.42 | 12.32 | 0 | 0 |
| outage90 | a0.3 | blocks | 24 | 8.22 | 9.33 | 0 | 0 |
| outage90 | a0.3 | boulevard | 24 | 7.85 | 10.16 | 0 | 0 |
| outage90 | a0.3:B | bayside | 24 | 7.11 | 9.56 | 0 | 0 |
| outage90 | a0.3:B | blocks | 24 | 7.71 | 11.36 | 0 | 0 |
| outage90 | a0.3:B | boulevard | 24 | 7.46 | 9.12 | 0 | 0 |
| outage90 | warm10 | bayside | 24 | 7.25 | 11.51 | 0 | 0 |
| outage90 | warm10 | blocks | 24 | 8.13 | 11.43 | 0 | 0 |
| outage90 | warm10 | boulevard | 24 | 7.74 | 12.14 | 0 | 0 |
| outage90 | warmstand10 | bayside | 24 | 7.25 | 11.51 | 0 | 0 |
| outage90 | warmstand10 | blocks | 24 | 8.13 | 11.43 | 0 | 0 |
| outage90 | warmstand10 | boulevard | 24 | 7.74 | 12.14 | 0 | 0 |
| quiet45 | a0.3 | bayside | 24 | 7.26 | 7.7 | 0 | 0 |
| quiet45 | a0.3 | blocks | 24 | 7.39 | 7.9 | 0 | 0 |
| quiet45 | a0.3 | boulevard | 24 | 7.44 | 7.97 | 0 | 0 |
| quiet45 | a0.3:B | bayside | 24 | 7.28 | 7.68 | 0 | 0 |
| quiet45 | a0.3:B | blocks | 24 | 7.38 | 7.76 | 0 | 0 |
| quiet45 | a0.3:B | boulevard | 24 | 7.38 | 7.92 | 0 | 0 |
| quiet45 | warm10 | bayside | 24 | 6.67 | 7.54 | 0 | 0 |
| quiet45 | warm10 | blocks | 24 | 7.11 | 9.0 | 0 | 0 |
| quiet45 | warm10 | boulevard | 24 | 7.11 | 7.43 | 0 | 0 |
| quiet45 | warmstand10 | bayside | 24 | 6.67 | 7.54 | 0 | 0 |
| quiet45 | warmstand10 | blocks | 24 | 7.11 | 9.0 | 0 | 0 |
| quiet45 | warmstand10 | boulevard | 24 | 7.11 | 7.43 | 0 | 0 |
| quiet90 | a0.3 | bayside | 24 | 7.29 | 7.9 | 0 | 0 |
| quiet90 | a0.3 | blocks | 24 | 7.49 | 9.24 | 0 | 0 |
| quiet90 | a0.3 | boulevard | 24 | 7.46 | 7.97 | 0 | 0 |
| quiet90 | a0.3:B | bayside | 24 | 7.24 | 8.06 | 0 | 0 |
| quiet90 | a0.3:B | blocks | 24 | 7.4 | 8.62 | 0 | 0 |
| quiet90 | a0.3:B | boulevard | 24 | 7.37 | 8.19 | 0 | 0 |
| quiet90 | warm10 | bayside | 24 | 6.67 | 7.83 | 0 | 0 |
| quiet90 | warm10 | blocks | 24 | 7.25 | 9.5 | 0 | 0 |
| quiet90 | warm10 | boulevard | 24 | 7.12 | 7.7 | 0 | 0 |
| quiet90 | warmstand10 | bayside | 24 | 6.67 | 7.83 | 0 | 0 |
| quiet90 | warmstand10 | blocks | 24 | 7.25 | 9.5 | 0 | 0 |
| quiet90 | warmstand10 | boulevard | 24 | 7.12 | 7.7 | 0 | 0 |
| quietdrift90 | a0.3 | bayside | 24 | 10.41 | 24.44 | 0 | 0 |
| quietdrift90 | a0.3 | blocks | 24 | 10.43 | 22.99 | 0 | 0 |
| quietdrift90 | a0.3 | boulevard | 24 | 11.05 | 34.13 | 0 | 0 |
| quietdrift90 | a0.3:B | bayside | 24 | 10.84 | 23.04 | 0 | 0 |
| quietdrift90 | a0.3:B | blocks | 24 | 11.29 | 22.97 | 0 | 0 |
| quietdrift90 | a0.3:B | boulevard | 24 | 14.46 | 25.0 | 0 | 0 |
| quietdrift90 | warm10 | bayside | 24 | 10.41 | 26.07 | 0 | 0 |
| quietdrift90 | warm10 | blocks | 24 | 11.12 | 22.89 | 0 | 0 |
| quietdrift90 | warm10 | boulevard | 24 | 11.27 | 34.04 | 0 | 0 |
| quietdrift90 | warmstand10 | bayside | 24 | 10.41 | 26.07 | 0 | 0 |
| quietdrift90 | warmstand10 | blocks | 24 | 11.12 | 22.89 | 0 | 0 |
| quietdrift90 | warmstand10 | boulevard | 24 | 11.27 | 34.04 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | checkpoint | 24 | 6592 | 0 | 0.0 | 0.2 | 0.81 | 1.21 |
| blockedmid | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedmid | a0.3 | bayside | other | 24 | 27263 | 40 | 1.0 | 0.24 | 3.55 | 7.29 |
| blockedmid | a0.3 | bayside | outage | 21 | 4680 | 26 | 0.65 | 0.61 | 1.6 | 1.87 |
| blockedmid | a0.3 | bayside | fix | 24 | 29175 | 14 | 0.35 | 0.2 | 3.61 | 7.29 |
| blockedmid | a0.3 | blocks | checkpoint | 24 | 8327 | 32 | 0.296 | 0.41 | 2.96 | 4.19 |
| blockedmid | a0.3 | blocks | corner | 24 | 8968 | 0 | 0.0 | 1.06 | 3.58 | 5.15 |
| blockedmid | a0.3 | blocks | other | 24 | 19502 | 76 | 0.704 | 0.24 | 3.71 | 7.42 |
| blockedmid | a0.3 | blocks | outage | 21 | 4884 | 29 | 0.269 | 0.61 | 3.23 | 4.64 |
| blockedmid | a0.3 | blocks | fix | 24 | 31913 | 79 | 0.731 | 0.29 | 3.88 | 7.51 |
| blockedmid | a0.3 | boulevard | checkpoint | 24 | 6639 | 0 | None | 0.2 | 1.24 | 1.57 |
| blockedmid | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | a0.3 | boulevard | other | 24 | 34221 | 0 | None | 0.15 | 0.97 | 7.46 |
| blockedmid | a0.3 | boulevard | outage | 22 | 5715 | 0 | None | 0.29 | 0.97 | 1.18 |
| blockedmid | a0.3 | boulevard | fix | 24 | 35145 | 0 | None | 0.14 | 1.08 | 7.46 |
| blockedmid | a0.3:B | bayside | checkpoint | 24 | 6758 | 0 | 0.0 | 0.17 | 0.7 | 1.26 |
| blockedmid | a0.3:B | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedmid | a0.3:B | bayside | other | 24 | 27014 | 69 | 1.0 | 0.21 | 3.05 | 7.24 |
| blockedmid | a0.3:B | bayside | outage | 21 | 3111 | 36 | 0.522 | 0.54 | 1.63 | 1.88 |
| blockedmid | a0.3:B | bayside | fix | 24 | 30661 | 33 | 0.478 | 0.2 | 2.52 | 7.24 |
| blockedmid | a0.3:B | blocks | checkpoint | 24 | 8629 | 19 | 0.76 | 0.39 | 2.83 | 3.29 |
| blockedmid | a0.3:B | blocks | corner | 24 | 8911 | 6 | 0.24 | 0.83 | 2.64 | 4.48 |
| blockedmid | a0.3:B | blocks | other | 24 | 19173 | 0 | 0.0 | 0.22 | 3.5 | 7.36 |
| blockedmid | a0.3:B | blocks | outage | 22 | 3601 | 0 | 0.0 | 0.42 | 2.2 | 4.38 |
| blockedmid | a0.3:B | blocks | fix | 24 | 33112 | 25 | 1.0 | 0.28 | 2.96 | 7.42 |
| blockedmid | a0.3:B | boulevard | checkpoint | 24 | 6557 | 0 | 0.0 | 0.2 | 0.63 | 0.96 |
| blockedmid | a0.3:B | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedmid | a0.3:B | boulevard | other | 24 | 34258 | 17 | 1.0 | 0.13 | 0.73 | 7.37 |
| blockedmid | a0.3:B | boulevard | outage | 22 | 4466 | 0 | 0.0 | 0.23 | 0.68 | 0.78 |
| blockedmid | a0.3:B | boulevard | fix | 24 | 36349 | 17 | 1.0 | 0.14 | 0.79 | 7.37 |
| blockedmid | warm10 | bayside | checkpoint | 24 | 6561 | 0 | 0.0 | 0.2 | 0.77 | 1.31 |
| blockedmid | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedmid | warm10 | bayside | other | 24 | 27226 | 44 | 1.0 | 0.23 | 3.12 | 6.67 |
| blockedmid | warm10 | bayside | outage | 21 | 4666 | 29 | 0.659 | 0.62 | 1.67 | 2.02 |
| blockedmid | warm10 | bayside | fix | 24 | 29121 | 15 | 0.341 | 0.2 | 3.05 | 6.69 |
| blockedmid | warm10 | blocks | checkpoint | 24 | 8348 | 44 | 0.31 | 0.39 | 3.06 | 4.39 |
| blockedmid | warm10 | blocks | corner | 24 | 8890 | 12 | 0.085 | 1.0 | 3.43 | 5.38 |
| blockedmid | warm10 | blocks | other | 24 | 19495 | 86 | 0.606 | 0.26 | 3.13 | 7.06 |
| blockedmid | warm10 | blocks | outage | 21 | 4804 | 35 | 0.246 | 0.68 | 3.51 | 4.84 |
| blockedmid | warm10 | blocks | fix | 24 | 31929 | 107 | 0.754 | 0.29 | 3.4 | 7.48 |
| blockedmid | warm10 | boulevard | checkpoint | 24 | 6696 | 0 | None | 0.2 | 1.29 | 1.58 |
| blockedmid | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | warm10 | boulevard | other | 24 | 34096 | 0 | None | 0.15 | 0.92 | 7.12 |
| blockedmid | warm10 | boulevard | outage | 22 | 5639 | 0 | None | 0.33 | 0.96 | 1.31 |
| blockedmid | warm10 | boulevard | fix | 24 | 35153 | 0 | None | 0.14 | 0.95 | 7.12 |
| blockedmid | warmstand10 | bayside | checkpoint | 24 | 6564 | 0 | 0.0 | 0.21 | 0.96 | 1.52 |
| blockedmid | warmstand10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedmid | warmstand10 | bayside | other | 24 | 27199 | 44 | 1.0 | 0.24 | 2.77 | 6.67 |
| blockedmid | warmstand10 | bayside | outage | 21 | 4611 | 29 | 0.659 | 0.66 | 1.62 | 1.96 |
| blockedmid | warmstand10 | bayside | fix | 24 | 29152 | 15 | 0.341 | 0.21 | 3.1 | 6.69 |
| blockedmid | warmstand10 | blocks | checkpoint | 24 | 8327 | 34 | 0.26 | 0.41 | 2.95 | 4.56 |
| blockedmid | warmstand10 | blocks | corner | 24 | 8888 | 11 | 0.084 | 1.04 | 3.51 | 5.47 |
| blockedmid | warmstand10 | blocks | other | 24 | 19507 | 86 | 0.656 | 0.26 | 2.96 | 7.06 |
| blockedmid | warmstand10 | blocks | outage | 21 | 4829 | 35 | 0.267 | 0.67 | 3.48 | 4.8 |
| blockedmid | warmstand10 | blocks | fix | 24 | 31893 | 96 | 0.733 | 0.29 | 3.42 | 7.39 |
| blockedmid | warmstand10 | boulevard | checkpoint | 24 | 6686 | 0 | None | 0.21 | 1.49 | 2.17 |
| blockedmid | warmstand10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedmid | warmstand10 | boulevard | other | 24 | 34080 | 0 | None | 0.15 | 0.88 | 7.12 |
| blockedmid | warmstand10 | boulevard | outage | 22 | 5643 | 0 | None | 0.38 | 0.86 | 1.29 |
| blockedmid | warmstand10 | boulevard | fix | 24 | 35123 | 0 | None | 0.14 | 1.02 | 7.12 |
| blockedstart | a0.3 | bayside | checkpoint | 24 | 6325 | 0 | 0.0 | 0.18 | 0.74 | 1.26 |
| blockedstart | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedstart | a0.3 | bayside | other | 24 | 27191 | 9 | 1.0 | 0.22 | 2.71 | 6.62 |
| blockedstart | a0.3 | bayside | outage | 21 | 4251 | 0 | 0.0 | 0.64 | 1.6 | 1.96 |
| blockedstart | a0.3 | bayside | fix | 24 | 29265 | 9 | 1.0 | 0.19 | 2.6 | 6.62 |
| blockedstart | a0.3 | blocks | checkpoint | 24 | 8203 | 12 | 0.387 | 0.39 | 2.46 | 3.13 |
| blockedstart | a0.3 | blocks | corner | 24 | 8805 | 19 | 0.613 | 0.98 | 3.09 | 4.88 |
| blockedstart | a0.3 | blocks | other | 24 | 19371 | 0 | 0.0 | 0.21 | 2.79 | 6.96 |
| blockedstart | a0.3 | blocks | outage | 21 | 4920 | 0 | 0.0 | 0.56 | 3.23 | 4.71 |
| blockedstart | a0.3 | blocks | fix | 24 | 31459 | 31 | 1.0 | 0.28 | 2.67 | 7.11 |
| blockedstart | a0.3 | boulevard | checkpoint | 24 | 6259 | 0 | None | 0.19 | 0.72 | 0.99 |
| blockedstart | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | a0.3 | boulevard | other | 24 | 34274 | 0 | None | 0.15 | 0.92 | 6.98 |
| blockedstart | a0.3 | boulevard | outage | 22 | 5568 | 0 | None | 0.34 | 0.97 | 1.36 |
| blockedstart | a0.3 | boulevard | fix | 24 | 34965 | 0 | None | 0.13 | 0.88 | 6.98 |
| blockedstart | a0.3:B | bayside | checkpoint | 24 | 6312 | 0 | None | 0.16 | 0.5 | 0.66 |
| blockedstart | a0.3:B | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | a0.3:B | bayside | other | 24 | 27236 | 0 | None | 0.21 | 2.29 | 6.77 |
| blockedstart | a0.3:B | bayside | outage | 21 | 3182 | 0 | None | 0.56 | 1.56 | 2.07 |
| blockedstart | a0.3:B | bayside | fix | 24 | 30366 | 0 | None | 0.18 | 1.69 | 6.77 |
| blockedstart | a0.3:B | blocks | checkpoint | 24 | 8231 | 10 | 0.769 | 0.35 | 2.33 | 3.05 |
| blockedstart | a0.3:B | blocks | corner | 24 | 8788 | 3 | 0.231 | 0.87 | 2.74 | 4.63 |
| blockedstart | a0.3:B | blocks | other | 24 | 19467 | 0 | 0.0 | 0.2 | 2.37 | 6.94 |
| blockedstart | a0.3:B | blocks | outage | 22 | 3452 | 0 | 0.0 | 0.42 | 2.75 | 4.42 |
| blockedstart | a0.3:B | blocks | fix | 24 | 33034 | 13 | 1.0 | 0.26 | 2.62 | 7.12 |
| blockedstart | a0.3:B | boulevard | checkpoint | 24 | 6257 | 0 | None | 0.18 | 0.62 | 0.85 |
| blockedstart | a0.3:B | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | a0.3:B | boulevard | other | 24 | 34352 | 0 | None | 0.14 | 0.77 | 6.95 |
| blockedstart | a0.3:B | boulevard | outage | 22 | 4287 | 0 | None | 0.32 | 0.8 | 0.92 |
| blockedstart | a0.3:B | boulevard | fix | 24 | 36322 | 0 | None | 0.13 | 0.71 | 6.95 |
| blockedstart | warm10 | bayside | checkpoint | 24 | 6322 | 0 | None | 0.18 | 0.9 | 1.28 |
| blockedstart | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | warm10 | bayside | other | 24 | 27220 | 0 | None | 0.22 | 2.71 | 6.5 |
| blockedstart | warm10 | bayside | outage | 21 | 4382 | 0 | None | 0.62 | 1.61 | 1.91 |
| blockedstart | warm10 | bayside | fix | 24 | 29160 | 0 | None | 0.2 | 2.25 | 6.5 |
| blockedstart | warm10 | blocks | checkpoint | 24 | 8199 | 12 | 0.6 | 0.37 | 2.4 | 3.04 |
| blockedstart | warm10 | blocks | corner | 24 | 8818 | 8 | 0.4 | 1.02 | 3.07 | 4.94 |
| blockedstart | warm10 | blocks | other | 24 | 19412 | 0 | 0.0 | 0.2 | 2.45 | 6.79 |
| blockedstart | warm10 | blocks | outage | 21 | 4905 | 0 | 0.0 | 0.53 | 3.28 | 4.72 |
| blockedstart | warm10 | blocks | fix | 24 | 31524 | 20 | 1.0 | 0.26 | 2.68 | 6.91 |
| blockedstart | warm10 | boulevard | checkpoint | 24 | 6250 | 0 | None | 0.18 | 0.75 | 0.96 |
| blockedstart | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | warm10 | boulevard | other | 24 | 34320 | 0 | None | 0.13 | 0.78 | 6.82 |
| blockedstart | warm10 | boulevard | outage | 22 | 5467 | 0 | None | 0.34 | 0.85 | 1.04 |
| blockedstart | warm10 | boulevard | fix | 24 | 35103 | 0 | None | 0.13 | 0.72 | 6.82 |
| blockedstart | warmstand10 | bayside | checkpoint | 24 | 6320 | 0 | 0.0 | 0.18 | 0.84 | 1.36 |
| blockedstart | warmstand10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| blockedstart | warmstand10 | bayside | other | 24 | 27236 | 12 | 1.0 | 0.22 | 3.01 | 6.87 |
| blockedstart | warmstand10 | bayside | outage | 21 | 4342 | 0 | 0.0 | 0.64 | 1.61 | 1.96 |
| blockedstart | warmstand10 | bayside | fix | 24 | 29214 | 12 | 1.0 | 0.2 | 2.68 | 6.87 |
| blockedstart | warmstand10 | blocks | checkpoint | 24 | 8193 | 12 | 0.462 | 0.37 | 2.43 | 3.13 |
| blockedstart | warmstand10 | blocks | corner | 24 | 8784 | 14 | 0.538 | 1.03 | 2.91 | 4.83 |
| blockedstart | warmstand10 | blocks | other | 24 | 19451 | 0 | 0.0 | 0.2 | 2.54 | 7.07 |
| blockedstart | warmstand10 | blocks | outage | 21 | 4768 | 0 | 0.0 | 0.59 | 3.34 | 4.66 |
| blockedstart | warmstand10 | blocks | fix | 24 | 31660 | 26 | 1.0 | 0.26 | 2.69 | 7.29 |
| blockedstart | warmstand10 | boulevard | checkpoint | 24 | 6245 | 0 | None | 0.19 | 0.77 | 1.01 |
| blockedstart | warmstand10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blockedstart | warmstand10 | boulevard | other | 24 | 34338 | 0 | None | 0.15 | 0.82 | 7.11 |
| blockedstart | warmstand10 | boulevard | outage | 22 | 5448 | 0 | None | 0.34 | 0.96 | 1.28 |
| blockedstart | warmstand10 | boulevard | fix | 24 | 35135 | 0 | None | 0.13 | 0.84 | 7.11 |
| outage90 | a0.3 | bayside | checkpoint | 24 | 6317 | 19 | 0.096 | 0.45 | 1.59 | 1.96 |
| outage90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | bayside | other | 24 | 26603 | 179 | 0.904 | 0.61 | 4.46 | 7.42 |
| outage90 | a0.3 | bayside | outage | 21 | 4596 | 53 | 0.268 | 1.95 | 4.26 | 4.68 |
| outage90 | a0.3 | bayside | fix | 24 | 28324 | 145 | 0.732 | 0.54 | 3.99 | 7.42 |
| outage90 | a0.3 | blocks | checkpoint | 24 | 8343 | 27 | 0.126 | 0.86 | 4.09 | 5.4 |
| outage90 | a0.3 | blocks | corner | 24 | 8810 | 11 | 0.051 | 1.2 | 3.42 | 5.68 |
| outage90 | a0.3 | blocks | other | 24 | 18799 | 177 | 0.823 | 0.68 | 4.59 | 7.91 |
| outage90 | a0.3 | blocks | outage | 21 | 4775 | 14 | 0.065 | 2.22 | 4.55 | 5.43 |
| outage90 | a0.3 | blocks | fix | 24 | 31177 | 201 | 0.935 | 0.75 | 3.96 | 8.07 |
| outage90 | a0.3 | boulevard | checkpoint | 24 | 6309 | 0 | 0.0 | 0.53 | 1.54 | 2.09 |
| outage90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | boulevard | other | 24 | 33665 | 220 | 1.0 | 0.62 | 3.9 | 7.85 |
| outage90 | a0.3 | boulevard | outage | 22 | 5523 | 16 | 0.073 | 1.6 | 4.52 | 4.92 |
| outage90 | a0.3 | boulevard | fix | 24 | 34451 | 204 | 0.927 | 0.56 | 3.07 | 7.85 |
| outage90 | a0.3:B | bayside | checkpoint | 24 | 6329 | 0 | 0.0 | 0.5 | 2.02 | 2.55 |
| outage90 | a0.3:B | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3:B | bayside | other | 24 | 26533 | 75 | 1.0 | 0.55 | 3.31 | 7.11 |
| outage90 | a0.3:B | bayside | outage | 21 | 3236 | 33 | 0.44 | 1.48 | 2.82 | 3.39 |
| outage90 | a0.3:B | bayside | fix | 24 | 29626 | 42 | 0.56 | 0.49 | 2.79 | 7.11 |
| outage90 | a0.3:B | blocks | checkpoint | 24 | 8316 | 52 | 0.495 | 0.87 | 2.99 | 3.43 |
| outage90 | a0.3:B | blocks | corner | 24 | 8732 | 14 | 0.133 | 1.12 | 3.1 | 4.81 |
| outage90 | a0.3:B | blocks | other | 24 | 18743 | 39 | 0.371 | 0.67 | 4.3 | 7.49 |
| outage90 | a0.3:B | blocks | outage | 21 | 3416 | 12 | 0.114 | 1.44 | 3.47 | 5.38 |
| outage90 | a0.3:B | blocks | fix | 24 | 32375 | 93 | 0.886 | 0.73 | 3.13 | 7.53 |
| outage90 | a0.3:B | boulevard | checkpoint | 24 | 6294 | 0 | 0.0 | 0.56 | 1.48 | 1.88 |
| outage90 | a0.3:B | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3:B | boulevard | other | 24 | 33657 | 61 | 1.0 | 0.6 | 3.65 | 7.46 |
| outage90 | a0.3:B | boulevard | outage | 22 | 4115 | 16 | 0.262 | 1.98 | 4.24 | 4.46 |
| outage90 | a0.3:B | boulevard | fix | 24 | 35836 | 45 | 0.738 | 0.54 | 2.62 | 7.46 |
| outage90 | warm10 | bayside | checkpoint | 24 | 6321 | 16 | 0.137 | 0.46 | 1.54 | 1.82 |
| outage90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10 | bayside | other | 24 | 26549 | 101 | 0.863 | 0.6 | 3.87 | 7.23 |
| outage90 | warm10 | bayside | outage | 21 | 4569 | 29 | 0.248 | 1.7 | 4.14 | 4.45 |
| outage90 | warm10 | bayside | fix | 24 | 28301 | 88 | 0.752 | 0.53 | 3.42 | 7.25 |
| outage90 | warm10 | blocks | checkpoint | 24 | 8351 | 58 | 0.258 | 0.82 | 3.76 | 5.27 |
| outage90 | warm10 | blocks | corner | 24 | 8835 | 19 | 0.084 | 1.13 | 4.26 | 6.09 |
| outage90 | warm10 | blocks | other | 24 | 18730 | 148 | 0.658 | 0.74 | 4.36 | 7.74 |
| outage90 | warm10 | blocks | outage | 21 | 4748 | 30 | 0.133 | 1.86 | 4.69 | 6.01 |
| outage90 | warm10 | blocks | fix | 24 | 31168 | 195 | 0.867 | 0.76 | 3.88 | 8.07 |
| outage90 | warm10 | boulevard | checkpoint | 24 | 6305 | 0 | 0.0 | 0.53 | 1.65 | 2.21 |
| outage90 | warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10 | boulevard | other | 24 | 33618 | 242 | 1.0 | 0.65 | 4.17 | 7.74 |
| outage90 | warm10 | boulevard | outage | 22 | 5489 | 61 | 0.252 | 1.8 | 5.05 | 5.74 |
| outage90 | warm10 | boulevard | fix | 24 | 34434 | 181 | 0.748 | 0.56 | 2.91 | 7.74 |
| outage90 | warmstand10 | bayside | checkpoint | 24 | 6321 | 16 | 0.137 | 0.46 | 1.54 | 1.82 |
| outage90 | warmstand10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warmstand10 | bayside | other | 24 | 26549 | 101 | 0.863 | 0.6 | 3.87 | 7.23 |
| outage90 | warmstand10 | bayside | outage | 21 | 4569 | 29 | 0.248 | 1.7 | 4.14 | 4.45 |
| outage90 | warmstand10 | bayside | fix | 24 | 28301 | 88 | 0.752 | 0.53 | 3.42 | 7.25 |
| outage90 | warmstand10 | blocks | checkpoint | 24 | 8351 | 58 | 0.258 | 0.82 | 3.76 | 5.27 |
| outage90 | warmstand10 | blocks | corner | 24 | 8835 | 19 | 0.084 | 1.13 | 4.26 | 6.09 |
| outage90 | warmstand10 | blocks | other | 24 | 18730 | 148 | 0.658 | 0.74 | 4.36 | 7.74 |
| outage90 | warmstand10 | blocks | outage | 21 | 4748 | 30 | 0.133 | 1.86 | 4.69 | 6.01 |
| outage90 | warmstand10 | blocks | fix | 24 | 31168 | 195 | 0.867 | 0.76 | 3.88 | 8.07 |
| outage90 | warmstand10 | boulevard | checkpoint | 24 | 6305 | 0 | 0.0 | 0.53 | 1.65 | 2.21 |
| outage90 | warmstand10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warmstand10 | boulevard | other | 24 | 33618 | 242 | 1.0 | 0.65 | 4.17 | 7.74 |
| outage90 | warmstand10 | boulevard | outage | 22 | 5489 | 61 | 0.252 | 1.8 | 5.05 | 5.74 |
| outage90 | warmstand10 | boulevard | fix | 24 | 34434 | 181 | 0.748 | 0.56 | 2.91 | 7.74 |
| quiet45 | a0.3 | bayside | checkpoint | 24 | 6310 | 0 | None | 0.18 | 1.23 | 1.76 |
| quiet45 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3 | bayside | other | 24 | 26547 | 0 | None | 0.23 | 2.29 | 7.26 |
| quiet45 | a0.3 | bayside | outage | 24 | 4397 | 0 | None | 0.46 | 1.69 | 2.08 |
| quiet45 | a0.3 | bayside | fix | 24 | 28460 | 0 | None | 0.2 | 2.27 | 7.26 |
| quiet45 | a0.3 | blocks | checkpoint | 24 | 8267 | 0 | None | 0.38 | 2.66 | 3.83 |
| quiet45 | a0.3 | blocks | corner | 24 | 8856 | 0 | None | 0.88 | 3.32 | 5.0 |
| quiet45 | a0.3 | blocks | other | 24 | 18649 | 0 | None | 0.23 | 3.48 | 7.39 |
| quiet45 | a0.3 | blocks | outage | 24 | 4694 | 0 | None | 0.4 | 2.83 | 4.65 |
| quiet45 | a0.3 | blocks | fix | 24 | 31078 | 0 | None | 0.29 | 3.06 | 7.39 |
| quiet45 | a0.3 | boulevard | checkpoint | 24 | 6295 | 0 | None | 0.18 | 0.59 | 0.86 |
| quiet45 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3 | boulevard | other | 24 | 33612 | 0 | None | 0.14 | 0.8 | 7.44 |
| quiet45 | a0.3 | boulevard | outage | 24 | 5313 | 0 | None | 0.26 | 0.78 | 1.11 |
| quiet45 | a0.3 | boulevard | fix | 24 | 34594 | 0 | None | 0.15 | 0.94 | 7.44 |
| quiet45 | a0.3:B | bayside | checkpoint | 24 | 6313 | 0 | None | 0.19 | 1.01 | 1.71 |
| quiet45 | a0.3:B | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3:B | bayside | other | 24 | 26544 | 0 | None | 0.23 | 2.27 | 7.28 |
| quiet45 | a0.3:B | bayside | outage | 22 | 3520 | 0 | None | 0.51 | 1.62 | 2.0 |
| quiet45 | a0.3:B | bayside | fix | 24 | 29337 | 0 | None | 0.21 | 2.19 | 7.28 |
| quiet45 | a0.3:B | blocks | checkpoint | 24 | 8236 | 0 | None | 0.36 | 2.43 | 3.21 |
| quiet45 | a0.3:B | blocks | corner | 24 | 8790 | 0 | None | 0.81 | 2.76 | 4.62 |
| quiet45 | a0.3:B | blocks | other | 24 | 18670 | 0 | None | 0.23 | 3.53 | 7.38 |
| quiet45 | a0.3:B | blocks | outage | 22 | 3671 | 0 | None | 0.47 | 2.65 | 4.57 |
| quiet45 | a0.3:B | blocks | fix | 24 | 32025 | 0 | None | 0.29 | 2.77 | 7.38 |
| quiet45 | a0.3:B | boulevard | checkpoint | 24 | 6300 | 0 | None | 0.17 | 0.96 | 1.24 |
| quiet45 | a0.3:B | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3:B | boulevard | other | 24 | 33616 | 0 | None | 0.15 | 0.93 | 7.38 |
| quiet45 | a0.3:B | boulevard | outage | 23 | 4702 | 0 | None | 0.29 | 0.92 | 1.28 |
| quiet45 | a0.3:B | boulevard | fix | 24 | 35214 | 0 | None | 0.14 | 0.99 | 7.38 |
| quiet45 | warm10 | bayside | checkpoint | 24 | 6312 | 0 | None | 0.18 | 1.08 | 1.92 |
| quiet45 | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10 | bayside | other | 24 | 26467 | 0 | None | 0.22 | 2.08 | 6.67 |
| quiet45 | warm10 | bayside | outage | 24 | 4495 | 0 | None | 0.45 | 1.65 | 1.96 |
| quiet45 | warm10 | bayside | fix | 24 | 28284 | 0 | None | 0.2 | 1.97 | 6.67 |
| quiet45 | warm10 | blocks | checkpoint | 24 | 8273 | 0 | 0.0 | 0.39 | 2.46 | 3.12 |
| quiet45 | warm10 | blocks | corner | 24 | 8861 | 5 | 1.0 | 1.04 | 3.79 | 4.89 |
| quiet45 | warm10 | blocks | other | 24 | 18572 | 0 | 0.0 | 0.24 | 2.66 | 7.04 |
| quiet45 | warm10 | blocks | outage | 24 | 4871 | 5 | 1.0 | 0.51 | 2.65 | 4.69 |
| quiet45 | warm10 | blocks | fix | 24 | 30835 | 0 | 0.0 | 0.32 | 2.96 | 7.04 |
| quiet45 | warm10 | boulevard | checkpoint | 24 | 6297 | 0 | None | 0.17 | 0.69 | 0.85 |
| quiet45 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10 | boulevard | other | 24 | 33518 | 0 | None | 0.15 | 0.81 | 7.11 |
| quiet45 | warm10 | boulevard | outage | 24 | 5497 | 0 | None | 0.27 | 0.8 | 1.06 |
| quiet45 | warm10 | boulevard | fix | 24 | 34318 | 0 | None | 0.14 | 0.82 | 7.11 |
| quiet45 | warmstand10 | bayside | checkpoint | 24 | 6312 | 0 | None | 0.18 | 1.08 | 1.92 |
| quiet45 | warmstand10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warmstand10 | bayside | other | 24 | 26467 | 0 | None | 0.22 | 2.08 | 6.67 |
| quiet45 | warmstand10 | bayside | outage | 24 | 4495 | 0 | None | 0.45 | 1.65 | 1.96 |
| quiet45 | warmstand10 | bayside | fix | 24 | 28284 | 0 | None | 0.2 | 1.97 | 6.67 |
| quiet45 | warmstand10 | blocks | checkpoint | 24 | 8273 | 0 | 0.0 | 0.39 | 2.46 | 3.12 |
| quiet45 | warmstand10 | blocks | corner | 24 | 8861 | 5 | 1.0 | 1.04 | 3.79 | 4.89 |
| quiet45 | warmstand10 | blocks | other | 24 | 18572 | 0 | 0.0 | 0.24 | 2.66 | 7.04 |
| quiet45 | warmstand10 | blocks | outage | 24 | 4871 | 5 | 1.0 | 0.51 | 2.65 | 4.69 |
| quiet45 | warmstand10 | blocks | fix | 24 | 30835 | 0 | 0.0 | 0.32 | 2.96 | 7.04 |
| quiet45 | warmstand10 | boulevard | checkpoint | 24 | 6297 | 0 | None | 0.17 | 0.69 | 0.85 |
| quiet45 | warmstand10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warmstand10 | boulevard | other | 24 | 33518 | 0 | None | 0.15 | 0.81 | 7.11 |
| quiet45 | warmstand10 | boulevard | outage | 24 | 5497 | 0 | None | 0.27 | 0.8 | 1.06 |
| quiet45 | warmstand10 | boulevard | fix | 24 | 34318 | 0 | None | 0.14 | 0.82 | 7.11 |
| quiet90 | a0.3 | bayside | checkpoint | 24 | 6305 | 0 | None | 0.17 | 0.55 | 0.93 |
| quiet90 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3 | bayside | other | 24 | 26597 | 0 | None | 0.21 | 3.62 | 7.29 |
| quiet90 | a0.3 | bayside | outage | 21 | 4609 | 0 | None | 0.49 | 1.49 | 1.99 |
| quiet90 | a0.3 | bayside | fix | 24 | 28293 | 0 | None | 0.19 | 3.41 | 7.29 |
| quiet90 | a0.3 | blocks | checkpoint | 24 | 8313 | 26 | 0.703 | 0.45 | 2.77 | 3.83 |
| quiet90 | a0.3 | blocks | corner | 24 | 8782 | 11 | 0.297 | 0.98 | 3.09 | 4.94 |
| quiet90 | a0.3 | blocks | other | 24 | 18742 | 0 | 0.0 | 0.25 | 3.7 | 7.42 |
| quiet90 | a0.3 | blocks | outage | 21 | 4767 | 0 | 0.0 | 0.7 | 3.42 | 4.83 |
| quiet90 | a0.3 | blocks | fix | 24 | 31070 | 37 | 1.0 | 0.29 | 3.79 | 7.49 |
| quiet90 | a0.3 | boulevard | checkpoint | 24 | 6302 | 0 | None | 0.17 | 0.73 | 0.92 |
| quiet90 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3 | boulevard | other | 24 | 33622 | 0 | None | 0.15 | 0.96 | 7.46 |
| quiet90 | a0.3 | boulevard | outage | 22 | 5522 | 0 | None | 0.36 | 0.98 | 1.04 |
| quiet90 | a0.3 | boulevard | fix | 24 | 34402 | 0 | None | 0.14 | 0.97 | 7.46 |
| quiet90 | a0.3:B | bayside | checkpoint | 24 | 6327 | 0 | 0.0 | 0.18 | 0.62 | 1.01 |
| quiet90 | a0.3:B | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3:B | bayside | other | 24 | 26548 | 6 | 1.0 | 0.21 | 3.06 | 7.24 |
| quiet90 | a0.3:B | bayside | outage | 21 | 3108 | 0 | 0.0 | 0.69 | 1.51 | 1.76 |
| quiet90 | a0.3:B | bayside | fix | 24 | 29767 | 6 | 1.0 | 0.19 | 2.74 | 7.24 |
| quiet90 | a0.3:B | blocks | checkpoint | 24 | 8295 | 11 | 0.478 | 0.39 | 2.46 | 3.21 |
| quiet90 | a0.3:B | blocks | corner | 24 | 8736 | 12 | 0.522 | 0.91 | 2.76 | 4.64 |
| quiet90 | a0.3:B | blocks | other | 24 | 18745 | 0 | 0.0 | 0.21 | 3.62 | 7.36 |
| quiet90 | a0.3:B | blocks | outage | 21 | 3521 | 0 | 0.0 | 0.44 | 2.64 | 4.65 |
| quiet90 | a0.3:B | blocks | fix | 24 | 32255 | 23 | 1.0 | 0.27 | 3.01 | 7.4 |
| quiet90 | a0.3:B | boulevard | checkpoint | 24 | 6295 | 0 | 0.0 | 0.19 | 0.67 | 1.01 |
| quiet90 | a0.3:B | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quiet90 | a0.3:B | boulevard | other | 24 | 33623 | 17 | 1.0 | 0.14 | 0.71 | 7.37 |
| quiet90 | a0.3:B | boulevard | outage | 22 | 4305 | 0 | 0.0 | 0.22 | 0.65 | 0.79 |
| quiet90 | a0.3:B | boulevard | fix | 24 | 35613 | 17 | 1.0 | 0.14 | 0.74 | 7.37 |
| quiet90 | warm10 | bayside | checkpoint | 24 | 6311 | 0 | None | 0.18 | 0.56 | 1.33 |
| quiet90 | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10 | bayside | other | 24 | 26509 | 0 | None | 0.21 | 2.92 | 6.67 |
| quiet90 | warm10 | bayside | outage | 21 | 4627 | 0 | None | 0.63 | 1.54 | 1.96 |
| quiet90 | warm10 | bayside | fix | 24 | 28193 | 0 | None | 0.19 | 3.02 | 6.67 |
| quiet90 | warm10 | blocks | checkpoint | 24 | 8337 | 38 | 0.745 | 0.4 | 2.85 | 4.46 |
| quiet90 | warm10 | blocks | corner | 24 | 8784 | 13 | 0.255 | 0.96 | 3.17 | 5.08 |
| quiet90 | warm10 | blocks | other | 24 | 18653 | 0 | 0.0 | 0.22 | 2.92 | 7.04 |
| quiet90 | warm10 | blocks | outage | 21 | 4798 | 0 | 0.0 | 0.64 | 3.42 | 4.87 |
| quiet90 | warm10 | blocks | fix | 24 | 30976 | 51 | 1.0 | 0.28 | 3.41 | 7.25 |
| quiet90 | warm10 | boulevard | checkpoint | 24 | 6297 | 0 | None | 0.18 | 0.67 | 0.95 |
| quiet90 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10 | boulevard | other | 24 | 33537 | 0 | None | 0.15 | 0.84 | 7.12 |
| quiet90 | warm10 | boulevard | outage | 21 | 5548 | 0 | None | 0.37 | 1.06 | 1.14 |
| quiet90 | warm10 | boulevard | fix | 24 | 34286 | 0 | None | 0.13 | 0.95 | 7.12 |
| quiet90 | warmstand10 | bayside | checkpoint | 24 | 6311 | 0 | None | 0.18 | 0.56 | 1.33 |
| quiet90 | warmstand10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warmstand10 | bayside | other | 24 | 26509 | 0 | None | 0.21 | 2.92 | 6.67 |
| quiet90 | warmstand10 | bayside | outage | 21 | 4627 | 0 | None | 0.63 | 1.54 | 1.96 |
| quiet90 | warmstand10 | bayside | fix | 24 | 28193 | 0 | None | 0.19 | 3.02 | 6.67 |
| quiet90 | warmstand10 | blocks | checkpoint | 24 | 8337 | 38 | 0.745 | 0.4 | 2.85 | 4.46 |
| quiet90 | warmstand10 | blocks | corner | 24 | 8784 | 13 | 0.255 | 0.96 | 3.17 | 5.08 |
| quiet90 | warmstand10 | blocks | other | 24 | 18653 | 0 | 0.0 | 0.22 | 2.92 | 7.04 |
| quiet90 | warmstand10 | blocks | outage | 21 | 4798 | 0 | 0.0 | 0.64 | 3.42 | 4.87 |
| quiet90 | warmstand10 | blocks | fix | 24 | 30976 | 51 | 1.0 | 0.28 | 3.41 | 7.25 |
| quiet90 | warmstand10 | boulevard | checkpoint | 24 | 6297 | 0 | None | 0.18 | 0.67 | 0.95 |
| quiet90 | warmstand10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warmstand10 | boulevard | other | 24 | 33537 | 0 | None | 0.15 | 0.84 | 7.12 |
| quiet90 | warmstand10 | boulevard | outage | 21 | 5548 | 0 | None | 0.37 | 1.06 | 1.14 |
| quiet90 | warmstand10 | boulevard | fix | 24 | 34286 | 0 | None | 0.13 | 0.95 | 7.12 |
| quietdrift90 | a0.3 | bayside | checkpoint | 24 | 6357 | 37 | 0.026 | 1.33 | 3.35 | 4.04 |
| quietdrift90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | bayside | other | 24 | 26707 | 1373 | 0.974 | 1.54 | 6.4 | 10.41 |
| quietdrift90 | a0.3 | bayside | outage | 21 | 4453 | 817 | 0.579 | 2.85 | 9.04 | 9.59 |
| quietdrift90 | a0.3 | bayside | fix | 24 | 28611 | 593 | 0.421 | 1.35 | 4.88 | 10.41 |
| quietdrift90 | a0.3 | blocks | checkpoint | 24 | 8427 | 239 | 0.166 | 1.77 | 5.92 | 6.52 |
| quietdrift90 | a0.3 | blocks | corner | 24 | 8740 | 104 | 0.072 | 1.54 | 5.36 | 8.19 |
| quietdrift90 | a0.3 | blocks | other | 24 | 18999 | 1095 | 0.761 | 1.68 | 7.36 | 10.43 |
| quietdrift90 | a0.3 | blocks | outage | 21 | 4746 | 784 | 0.545 | 3.32 | 9.1 | 9.89 |
| quietdrift90 | a0.3 | blocks | fix | 24 | 31420 | 654 | 0.455 | 1.58 | 5.95 | 10.43 |
| quietdrift90 | a0.3 | boulevard | checkpoint | 24 | 6358 | 313 | 0.13 | 1.38 | 4.38 | 4.6 |
| quietdrift90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | boulevard | other | 24 | 33847 | 2097 | 0.87 | 1.5 | 6.51 | 11.05 |
| quietdrift90 | a0.3 | boulevard | outage | 22 | 5554 | 1105 | 0.459 | 2.92 | 8.39 | 10.29 |
| quietdrift90 | a0.3 | boulevard | fix | 24 | 34651 | 1305 | 0.541 | 1.37 | 5.58 | 11.05 |
| quietdrift90 | a0.3:B | bayside | checkpoint | 24 | 6370 | 154 | 0.174 | 1.44 | 4.46 | 5.0 |
| quietdrift90 | a0.3:B | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3:B | bayside | other | 24 | 26690 | 729 | 0.826 | 1.38 | 6.01 | 9.93 |
| quietdrift90 | a0.3:B | bayside | outage | 21 | 3190 | 420 | 0.476 | 3.52 | 8.32 | 9.46 |
| quietdrift90 | a0.3:B | bayside | fix | 24 | 29870 | 463 | 0.524 | 1.29 | 4.85 | 10.84 |
| quietdrift90 | a0.3:B | blocks | checkpoint | 24 | 8394 | 240 | 0.208 | 1.61 | 4.96 | 5.81 |
| quietdrift90 | a0.3:B | blocks | corner | 24 | 8594 | 111 | 0.096 | 1.62 | 4.84 | 8.09 |
| quietdrift90 | a0.3:B | blocks | other | 24 | 19018 | 805 | 0.696 | 1.61 | 5.81 | 9.75 |
| quietdrift90 | a0.3:B | blocks | outage | 21 | 3392 | 610 | 0.528 | 3.27 | 10.48 | 11.6 |
| quietdrift90 | a0.3:B | blocks | fix | 24 | 32614 | 546 | 0.472 | 1.57 | 5.17 | 9.78 |
| quietdrift90 | a0.3:B | boulevard | checkpoint | 24 | 6333 | 70 | 0.037 | 1.21 | 3.94 | 4.6 |
| quietdrift90 | a0.3:B | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3:B | boulevard | other | 24 | 33883 | 1827 | 0.963 | 1.58 | 8.14 | 14.46 |
| quietdrift90 | a0.3:B | boulevard | outage | 22 | 4320 | 1066 | 0.562 | 4.13 | 12.59 | 14.09 |
| quietdrift90 | a0.3:B | boulevard | fix | 24 | 35896 | 831 | 0.438 | 1.54 | 5.38 | 14.46 |
| quietdrift90 | warm10 | bayside | checkpoint | 24 | 6370 | 33 | 0.024 | 1.3 | 3.35 | 3.92 |
| quietdrift90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10 | bayside | other | 24 | 26622 | 1370 | 0.976 | 1.48 | 7.03 | 10.41 |
| quietdrift90 | warm10 | bayside | outage | 21 | 4397 | 779 | 0.555 | 2.91 | 8.98 | 9.76 |
| quietdrift90 | warm10 | bayside | fix | 24 | 28595 | 624 | 0.445 | 1.33 | 4.83 | 10.41 |
| quietdrift90 | warm10 | blocks | checkpoint | 24 | 8426 | 201 | 0.167 | 1.83 | 5.78 | 6.71 |
| quietdrift90 | warm10 | blocks | corner | 24 | 8710 | 65 | 0.054 | 1.44 | 5.05 | 6.67 |
| quietdrift90 | warm10 | blocks | other | 24 | 18917 | 939 | 0.779 | 1.69 | 7.29 | 11.12 |
| quietdrift90 | warm10 | blocks | outage | 21 | 4635 | 662 | 0.549 | 2.98 | 8.76 | 10.46 |
| quietdrift90 | warm10 | blocks | fix | 24 | 31418 | 543 | 0.451 | 1.59 | 5.43 | 11.12 |
| quietdrift90 | warm10 | boulevard | checkpoint | 24 | 6356 | 328 | 0.146 | 1.33 | 3.84 | 4.32 |
| quietdrift90 | warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10 | boulevard | other | 24 | 33766 | 1911 | 0.854 | 1.52 | 6.05 | 10.85 |
| quietdrift90 | warm10 | boulevard | outage | 22 | 5557 | 1128 | 0.504 | 3.36 | 8.62 | 10.27 |
| quietdrift90 | warm10 | boulevard | fix | 24 | 34565 | 1111 | 0.496 | 1.33 | 5.42 | 11.27 |
| quietdrift90 | warmstand10 | bayside | checkpoint | 24 | 6370 | 33 | 0.024 | 1.3 | 3.35 | 3.92 |
| quietdrift90 | warmstand10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warmstand10 | bayside | other | 24 | 26622 | 1370 | 0.976 | 1.48 | 7.03 | 10.41 |
| quietdrift90 | warmstand10 | bayside | outage | 21 | 4397 | 779 | 0.555 | 2.91 | 8.98 | 9.76 |
| quietdrift90 | warmstand10 | bayside | fix | 24 | 28595 | 624 | 0.445 | 1.33 | 4.83 | 10.41 |
| quietdrift90 | warmstand10 | blocks | checkpoint | 24 | 8426 | 201 | 0.167 | 1.83 | 5.78 | 6.71 |
| quietdrift90 | warmstand10 | blocks | corner | 24 | 8710 | 65 | 0.054 | 1.44 | 5.05 | 6.67 |
| quietdrift90 | warmstand10 | blocks | other | 24 | 18917 | 939 | 0.779 | 1.69 | 7.29 | 11.12 |
| quietdrift90 | warmstand10 | blocks | outage | 21 | 4635 | 662 | 0.549 | 2.98 | 8.76 | 10.46 |
| quietdrift90 | warmstand10 | blocks | fix | 24 | 31418 | 543 | 0.451 | 1.59 | 5.43 | 11.12 |
| quietdrift90 | warmstand10 | boulevard | checkpoint | 24 | 6356 | 328 | 0.146 | 1.33 | 3.84 | 4.32 |
| quietdrift90 | warmstand10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warmstand10 | boulevard | other | 24 | 33766 | 1911 | 0.854 | 1.52 | 6.05 | 10.85 |
| quietdrift90 | warmstand10 | boulevard | outage | 22 | 5557 | 1128 | 0.504 | 3.36 | 8.62 | 10.27 |
| quietdrift90 | warmstand10 | boulevard | fix | 24 | 34565 | 1111 | 0.496 | 1.33 | 5.42 | 11.27 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 1.0 | 4.23 |
| blockedmid | a0.3 | blocks | 24 | 1.02 | 4.09 |
| blockedmid | a0.3 | boulevard | 24 | 0.97 | 3.83 |
| blockedmid | a0.3:B | bayside | 24 | 0.99 | 4.22 |
| blockedmid | a0.3:B | blocks | 24 | 1.02 | 4.08 |
| blockedmid | a0.3:B | boulevard | 24 | 0.97 | 3.83 |
| blockedmid | warm10 | bayside | 24 | 1.01 | 3.75 |
| blockedmid | warm10 | blocks | 24 | 1.03 | 3.67 |
| blockedmid | warm10 | boulevard | 24 | 0.97 | 3.42 |
| blockedmid | warmstand10 | bayside | 24 | 1.0 | 3.77 |
| blockedmid | warmstand10 | blocks | 24 | 1.03 | 3.67 |
| blockedmid | warmstand10 | boulevard | 24 | 0.97 | 3.42 |
| blockedstart | a0.3 | bayside | 24 | 1.03 | 5.42 |
| blockedstart | a0.3 | blocks | 24 | 1.05 | 5.28 |
| blockedstart | a0.3 | boulevard | 24 | 0.99 | 4.94 |
| blockedstart | a0.3:B | bayside | 24 | 1.02 | 5.34 |
| blockedstart | a0.3:B | blocks | 24 | 1.03 | 5.12 |
| blockedstart | a0.3:B | boulevard | 24 | 0.99 | 4.83 |
| blockedstart | warm10 | bayside | 24 | 1.04 | 5.55 |
| blockedstart | warm10 | blocks | 24 | 1.05 | 5.35 |
| blockedstart | warm10 | boulevard | 24 | 0.99 | 5.01 |
| blockedstart | warmstand10 | bayside | 24 | 1.03 | 5.62 |
| blockedstart | warmstand10 | blocks | 24 | 1.05 | 5.41 |
| blockedstart | warmstand10 | boulevard | 24 | 0.98 | 5.07 |
| outage90 | a0.3 | bayside | 24 | 1.58 | 4.69 |
| outage90 | a0.3 | blocks | 24 | 1.67 | 4.36 |
| outage90 | a0.3 | boulevard | 24 | 1.55 | 4.08 |
| outage90 | a0.3:B | bayside | 24 | 1.57 | 4.38 |
| outage90 | a0.3:B | blocks | 24 | 1.67 | 4.38 |
| outage90 | a0.3:B | boulevard | 24 | 1.58 | 4.23 |
| outage90 | warm10 | bayside | 24 | 1.52 | 4.15 |
| outage90 | warm10 | blocks | 24 | 1.67 | 4.12 |
| outage90 | warm10 | boulevard | 24 | 1.56 | 3.85 |
| outage90 | warmstand10 | bayside | 24 | 1.52 | 4.15 |
| outage90 | warmstand10 | blocks | 24 | 1.67 | 4.12 |
| outage90 | warmstand10 | boulevard | 24 | 1.56 | 3.85 |
| quiet45 | a0.3 | bayside | 24 | 1.0 | 4.23 |
| quiet45 | a0.3 | blocks | 24 | 1.02 | 4.09 |
| quiet45 | a0.3 | boulevard | 24 | 0.97 | 3.83 |
| quiet45 | a0.3:B | bayside | 24 | 1.0 | 4.26 |
| quiet45 | a0.3:B | blocks | 24 | 1.03 | 4.11 |
| quiet45 | a0.3:B | boulevard | 24 | 0.97 | 3.87 |
| quiet45 | warm10 | bayside | 24 | 1.01 | 3.78 |
| quiet45 | warm10 | blocks | 24 | 1.03 | 3.7 |
| quiet45 | warm10 | boulevard | 24 | 0.96 | 3.45 |
| quiet45 | warmstand10 | bayside | 24 | 1.01 | 3.78 |
| quiet45 | warmstand10 | blocks | 24 | 1.03 | 3.7 |
| quiet45 | warmstand10 | boulevard | 24 | 0.96 | 3.45 |
| quiet90 | a0.3 | bayside | 24 | 0.99 | 4.27 |
| quiet90 | a0.3 | blocks | 24 | 1.02 | 4.12 |
| quiet90 | a0.3 | boulevard | 24 | 0.97 | 3.84 |
| quiet90 | a0.3:B | bayside | 24 | 0.99 | 4.25 |
| quiet90 | a0.3:B | blocks | 24 | 1.02 | 4.11 |
| quiet90 | a0.3:B | boulevard | 24 | 0.97 | 3.85 |
| quiet90 | warm10 | bayside | 24 | 1.02 | 3.79 |
| quiet90 | warm10 | blocks | 24 | 1.02 | 3.69 |
| quiet90 | warm10 | boulevard | 24 | 0.97 | 3.44 |
| quiet90 | warmstand10 | bayside | 24 | 1.02 | 3.79 |
| quiet90 | warmstand10 | blocks | 24 | 1.02 | 3.69 |
| quiet90 | warmstand10 | boulevard | 24 | 0.97 | 3.44 |
| quietdrift90 | a0.3 | bayside | 24 | 5.12 | 8.69 |
| quietdrift90 | a0.3 | blocks | 24 | 5.34 | 8.95 |
| quietdrift90 | a0.3 | boulevard | 24 | 5.08 | 8.16 |
| quietdrift90 | a0.3:B | bayside | 24 | 5.4 | 8.73 |
| quietdrift90 | a0.3:B | blocks | 24 | 5.6 | 9.16 |
| quietdrift90 | a0.3:B | boulevard | 24 | 5.37 | 8.27 |
| quietdrift90 | warm10 | bayside | 24 | 5.04 | 8.72 |
| quietdrift90 | warm10 | blocks | 24 | 5.24 | 8.82 |
| quietdrift90 | warm10 | boulevard | 24 | 5.14 | 8.02 |
| quietdrift90 | warmstand10 | bayside | 24 | 5.04 | 8.72 |
| quietdrift90 | warmstand10 | blocks | 24 | 5.24 | 8.82 |
| quietdrift90 | warmstand10 | boulevard | 24 | 5.14 | 8.02 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| blockedmid | a0.3 | bayside | 24 | 0.0277 |
| blockedmid | a0.3 | blocks | 24 | 0.0375 |
| blockedmid | a0.3 | boulevard | 24 | 0.0216 |
| blockedmid | a0.3:B | bayside | 24 | 0.0264 |
| blockedmid | a0.3:B | blocks | 24 | 0.0364 |
| blockedmid | a0.3:B | boulevard | 24 | 0.0217 |
| blockedmid | warm10 | bayside | 24 | 0.027 |
| blockedmid | warm10 | blocks | 24 | 0.0367 |
| blockedmid | warm10 | boulevard | 24 | 0.0205 |
| blockedmid | warmstand10 | bayside | 24 | 0.0273 |
| blockedmid | warmstand10 | blocks | 24 | 0.0374 |
| blockedmid | warmstand10 | boulevard | 24 | 0.0211 |
| blockedstart | a0.3 | bayside | 24 | 0.0265 |
| blockedstart | a0.3 | blocks | 24 | 0.0366 |
| blockedstart | a0.3 | boulevard | 24 | 0.0212 |
| blockedstart | a0.3:B | bayside | 24 | 0.0261 |
| blockedstart | a0.3:B | blocks | 24 | 0.0364 |
| blockedstart | a0.3:B | boulevard | 24 | 0.0214 |
| blockedstart | warm10 | bayside | 24 | 0.0257 |
| blockedstart | warm10 | blocks | 24 | 0.036 |
| blockedstart | warm10 | boulevard | 24 | 0.0202 |
| blockedstart | warmstand10 | bayside | 24 | 0.0262 |
| blockedstart | warmstand10 | blocks | 24 | 0.0372 |
| blockedstart | warmstand10 | boulevard | 24 | 0.0209 |
| outage90 | a0.3 | bayside | 24 | 0.0317 |
| outage90 | a0.3 | blocks | 24 | 0.0418 |
| outage90 | a0.3 | boulevard | 24 | 0.0267 |
| outage90 | a0.3:B | bayside | 24 | 0.0311 |
| outage90 | a0.3:B | blocks | 24 | 0.0406 |
| outage90 | a0.3:B | boulevard | 24 | 0.0271 |
| outage90 | warm10 | bayside | 24 | 0.0312 |
| outage90 | warm10 | blocks | 24 | 0.0417 |
| outage90 | warm10 | boulevard | 24 | 0.0265 |
| outage90 | warmstand10 | bayside | 24 | 0.0312 |
| outage90 | warmstand10 | blocks | 24 | 0.0417 |
| outage90 | warmstand10 | boulevard | 24 | 0.0265 |
| quiet45 | a0.3 | bayside | 24 | 0.0255 |
| quiet45 | a0.3 | blocks | 24 | 0.0362 |
| quiet45 | a0.3 | boulevard | 24 | 0.02 |
| quiet45 | a0.3:B | bayside | 24 | 0.025 |
| quiet45 | a0.3:B | blocks | 24 | 0.0352 |
| quiet45 | a0.3:B | boulevard | 24 | 0.0201 |
| quiet45 | warm10 | bayside | 24 | 0.0248 |
| quiet45 | warm10 | blocks | 24 | 0.0364 |
| quiet45 | warm10 | boulevard | 24 | 0.0195 |
| quiet45 | warmstand10 | bayside | 24 | 0.0248 |
| quiet45 | warmstand10 | blocks | 24 | 0.0364 |
| quiet45 | warmstand10 | boulevard | 24 | 0.0195 |
| quiet90 | a0.3 | bayside | 24 | 0.0258 |
| quiet90 | a0.3 | blocks | 24 | 0.0367 |
| quiet90 | a0.3 | boulevard | 24 | 0.02 |
| quiet90 | a0.3:B | bayside | 24 | 0.0253 |
| quiet90 | a0.3:B | blocks | 24 | 0.0358 |
| quiet90 | a0.3:B | boulevard | 24 | 0.0202 |
| quiet90 | warm10 | bayside | 24 | 0.0258 |
| quiet90 | warm10 | blocks | 24 | 0.0363 |
| quiet90 | warm10 | boulevard | 24 | 0.0195 |
| quiet90 | warmstand10 | bayside | 24 | 0.0258 |
| quiet90 | warmstand10 | blocks | 24 | 0.0363 |
| quiet90 | warmstand10 | boulevard | 24 | 0.0195 |
| quietdrift90 | a0.3 | bayside | 24 | 0.0303 |
| quietdrift90 | a0.3 | blocks | 24 | 0.0408 |
| quietdrift90 | a0.3 | boulevard | 24 | 0.0253 |
| quietdrift90 | a0.3:B | bayside | 24 | 0.0297 |
| quietdrift90 | a0.3:B | blocks | 24 | 0.0403 |
| quietdrift90 | a0.3:B | boulevard | 24 | 0.0255 |
| quietdrift90 | warm10 | bayside | 24 | 0.0293 |
| quietdrift90 | warm10 | blocks | 24 | 0.0404 |
| quietdrift90 | warm10 | boulevard | 24 | 0.0249 |
| quietdrift90 | warmstand10 | bayside | 24 | 0.0293 |
| quietdrift90 | warmstand10 | blocks | 24 | 0.0404 |
| quietdrift90 | warmstand10 | boulevard | 24 | 0.0249 |
