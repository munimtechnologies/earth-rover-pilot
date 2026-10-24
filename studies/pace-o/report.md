# Where does the rover stray from its course? (simulated)

pace_o.py 0.1.0 (pace_n.py 0.1.0, pace_m.py 0.1.0, rover_pilot.py 0.18.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.0's real-rover pilot (pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3) on pace_l.py's outage90 (90 s GPS outages, a steady compass error) or drift90 (the compass error drifts, SD 10 deg, 120 s time constant); only the planner (diag: the studies' CoursePlanner; keep: through each checkpoint corner) and the path follower's lookahead (metres) change. Seeds 229-252. 576 of 576 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_n.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | diag16 | 72/72 | 0.883 | 0.993 | 72 | 0.998 | 0.015 |
| outage90 | keep16 | 72/72 | 0.883 | 0.993 | 72 | 0.999 | 0.015 |
| outage90 | keep8 | 72/72 | 0.853 | 0.959 | 72 | 1.008 | 0.016 |
| outage90 | keep24 | 72/72 | 0.888 | 0.999 | 72 | 0.993 | 0.015 |
| drift90 | diag16 | 72/72 | 0.877 | 0.987 | 72 | 1.004 | 0.015 |
| drift90 | keep16 | 72/72 | 0.876 | 0.985 | 72 | 1.005 | 0.015 |
| drift90 | keep8 | 72/72 | 0.853 | 0.96 | 72 | 1.018 | 0.014 |
| drift90 | keep24 | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.014 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| drift90 | keep16 | diag16 | 0/3 | 1 | 0 | 0 | 0.0107 |
| outage90 | keep16 | diag16 | 0/3 | 1 | 0 | 0 | 0.0077 |
| drift90 | keep8 | keep16 | 0/3 | 3 | 0 | 0 | 0.0544 |
| outage90 | keep8 | keep16 | 0/3 | 3 | 0 | 0 | 0.0616 |
| drift90 | keep24 | keep16 | 2/3 | 0 | 0 | 0 | -0.035 |
| outage90 | keep24 | keep16 | 3/3 | 0 | 0 | 0 | -0.0362 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| drift90 | keep16 | diag16 | bayside | 1 | 3 | 0.0 | 0.0 | 0.625 |
| drift90 | keep16 | diag16 | blocks | 1 | 21 | 17.0 | 0.0107 | 0.0 |
| drift90 | keep16 | diag16 | boulevard | 6 | 5 | 0.0 | 0.0 | 1.0 |
| outage90 | keep16 | diag16 | bayside | 0 | 2 | 0.0 | 0.0 | 0.5 |
| outage90 | keep16 | diag16 | blocks | 1 | 22 | 12.0 | 0.0077 | 0.0 |
| outage90 | keep16 | diag16 | boulevard | 1 | 3 | 0.0 | 0.0 | 0.625 |
| drift90 | keep8 | keep16 | bayside | 1 | 19 | 11.0 | 0.0076 | 0.0 |
| drift90 | keep8 | keep16 | blocks | 1 | 23 | 87.0 | 0.0544 | 0.0 |
| drift90 | keep8 | keep16 | boulevard | 3 | 18 | 6.0 | 0.0034 | 0.0015 |
| outage90 | keep8 | keep16 | bayside | 0 | 19 | 10.0 | 0.007 | 0.0 |
| outage90 | keep8 | keep16 | blocks | 0 | 24 | 97.0 | 0.0616 | 0.0 |
| outage90 | keep8 | keep16 | boulevard | 0 | 16 | 6.0 | 0.0034 | 0.0 |
| drift90 | keep24 | keep16 | bayside | 19 | 0 | -10.0 | -0.0069 | 0.0 |
| drift90 | keep24 | keep16 | blocks | 24 | 0 | -56.0 | -0.035 | 0.0 |
| drift90 | keep24 | keep16 | boulevard | 7 | 4 | 0.0 | 0.0 | 0.5488 |
| outage90 | keep24 | keep16 | bayside | 19 | 0 | -9.0 | -0.0063 | 0.0 |
| outage90 | keep24 | keep16 | blocks | 24 | 0 | -57.0 | -0.0362 | 0.0 |
| outage90 | keep24 | keep16 | boulevard | 12 | 0 | -1.0 | -0.0006 | 0.0005 |

## What the drift costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| diag16 | drift90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0049 |
| keep16 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0051 |
| keep8 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0062 |
| keep24 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0068 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| drift90 | diag16 | bayside | checkpoint | 24 | 6354 | 70 | 0.06 | 1.33 | 3.77 | 4.69 |
| drift90 | diag16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | diag16 | bayside | other | 24 | 26768 | 1100 | 0.94 | 1.58 | 6.08 | 10.49 |
| drift90 | diag16 | bayside | outage | 22 | 2917 | 529 | 0.452 | 2.86 | 6.86 | 7.41 |
| drift90 | diag16 | bayside | fix | 24 | 30205 | 641 | 0.548 | 1.44 | 4.85 | 10.49 |
| drift90 | diag16 | blocks | checkpoint | 24 | 7854 | 2738 | 0.712 | 6.58 | 11.97 | 13.04 |
| drift90 | diag16 | blocks | corner | 24 | 8673 | 157 | 0.041 | 1.71 | 5.35 | 7.75 |
| drift90 | diag16 | blocks | other | 24 | 19109 | 951 | 0.247 | 1.88 | 7.21 | 10.98 |
| drift90 | diag16 | blocks | outage | 23 | 3201 | 564 | 0.147 | 3.8 | 7.68 | 8.28 |
| drift90 | diag16 | blocks | fix | 24 | 32435 | 3282 | 0.853 | 2.13 | 9.92 | 13.18 |
| drift90 | diag16 | boulevard | checkpoint | 24 | 6345 | 705 | 0.197 | 3.21 | 8.1 | 8.82 |
| drift90 | diag16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | diag16 | boulevard | other | 24 | 33924 | 2882 | 0.803 | 2.51 | 8.58 | 14.42 |
| drift90 | diag16 | boulevard | outage | 24 | 4097 | 1023 | 0.285 | 4.13 | 13.32 | 13.91 |
| drift90 | diag16 | boulevard | fix | 24 | 36172 | 2564 | 0.715 | 2.5 | 7.4 | 15.0 |
| drift90 | keep16 | bayside | checkpoint | 24 | 6356 | 49 | 0.044 | 1.28 | 3.63 | 4.56 |
| drift90 | keep16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep16 | bayside | other | 24 | 26770 | 1070 | 0.956 | 1.58 | 5.79 | 10.32 |
| drift90 | keep16 | bayside | outage | 22 | 2916 | 509 | 0.455 | 3.18 | 6.11 | 6.47 |
| drift90 | keep16 | bayside | fix | 24 | 30210 | 610 | 0.545 | 1.42 | 4.88 | 10.4 |
| drift90 | keep16 | blocks | checkpoint | 24 | 8316 | 119 | 0.116 | 1.62 | 4.69 | 5.94 |
| drift90 | keep16 | blocks | corner | 24 | 8674 | 143 | 0.139 | 1.69 | 4.63 | 7.67 |
| drift90 | keep16 | blocks | other | 24 | 19064 | 768 | 0.746 | 1.77 | 6.67 | 10.04 |
| drift90 | keep16 | blocks | outage | 23 | 3238 | 510 | 0.495 | 3.09 | 7.0 | 8.4 |
| drift90 | keep16 | blocks | fix | 24 | 32816 | 520 | 0.505 | 1.55 | 5.08 | 9.64 |
| drift90 | keep16 | boulevard | checkpoint | 24 | 6345 | 103 | 0.051 | 1.55 | 4.31 | 5.14 |
| drift90 | keep16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep16 | boulevard | other | 24 | 33910 | 1922 | 0.949 | 1.65 | 8.14 | 14.57 |
| drift90 | keep16 | boulevard | outage | 24 | 4132 | 947 | 0.468 | 4.5 | 11.81 | 14.18 |
| drift90 | keep16 | boulevard | fix | 24 | 36123 | 1078 | 0.532 | 1.52 | 5.61 | 14.57 |
| drift90 | keep24 | bayside | checkpoint | 24 | 6329 | 123 | 0.09 | 1.71 | 4.63 | 5.3 |
| drift90 | keep24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep24 | bayside | other | 24 | 26564 | 1242 | 0.91 | 2.16 | 6.9 | 11.46 |
| drift90 | keep24 | bayside | outage | 22 | 3016 | 655 | 0.48 | 3.86 | 7.42 | 7.88 |
| drift90 | keep24 | bayside | fix | 24 | 29877 | 710 | 0.52 | 2.02 | 5.88 | 11.34 |
| drift90 | keep24 | blocks | checkpoint | 24 | 8095 | 141 | 0.107 | 1.74 | 4.96 | 6.12 |
| drift90 | keep24 | blocks | corner | 24 | 7530 | 108 | 0.082 | 1.97 | 5.81 | 7.88 |
| drift90 | keep24 | blocks | other | 24 | 19058 | 1069 | 0.811 | 2.09 | 7.4 | 11.17 |
| drift90 | keep24 | blocks | outage | 22 | 3031 | 546 | 0.414 | 3.64 | 8.15 | 9.44 |
| drift90 | keep24 | blocks | fix | 24 | 31652 | 772 | 0.586 | 1.9 | 6.2 | 11.17 |
| drift90 | keep24 | boulevard | checkpoint | 24 | 6340 | 89 | 0.036 | 1.71 | 5.04 | 5.36 |
| drift90 | keep24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep24 | boulevard | other | 24 | 33893 | 2413 | 0.964 | 2.0 | 8.21 | 14.38 |
| drift90 | keep24 | boulevard | outage | 24 | 4159 | 1016 | 0.406 | 3.81 | 11.17 | 13.27 |
| drift90 | keep24 | boulevard | fix | 24 | 36074 | 1486 | 0.594 | 1.82 | 6.84 | 14.38 |
| drift90 | keep8 | bayside | checkpoint | 24 | 6429 | 86 | 0.077 | 1.09 | 2.92 | 3.69 |
| drift90 | keep8 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep8 | bayside | other | 24 | 27030 | 1035 | 0.923 | 1.25 | 5.12 | 9.85 |
| drift90 | keep8 | bayside | outage | 22 | 2914 | 703 | 0.627 | 3.55 | 9.64 | 10.11 |
| drift90 | keep8 | bayside | fix | 24 | 30545 | 418 | 0.373 | 1.14 | 3.9 | 12.46 |
| drift90 | keep8 | blocks | checkpoint | 24 | 8906 | 161 | 0.172 | 1.46 | 4.75 | 7.67 |
| drift90 | keep8 | blocks | corner | 24 | 10088 | 140 | 0.149 | 1.81 | 5.13 | 6.67 |
| drift90 | keep8 | blocks | other | 24 | 19000 | 636 | 0.679 | 1.31 | 5.17 | 8.98 |
| drift90 | keep8 | blocks | outage | 24 | 3445 | 609 | 0.65 | 2.48 | 7.86 | 8.49 |
| drift90 | keep8 | blocks | fix | 24 | 34549 | 328 | 0.35 | 1.41 | 4.82 | 8.38 |
| drift90 | keep8 | boulevard | checkpoint | 24 | 6388 | 80 | 0.047 | 1.25 | 3.24 | 3.73 |
| drift90 | keep8 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep8 | boulevard | other | 24 | 34089 | 1617 | 0.953 | 1.25 | 7.11 | 16.26 |
| drift90 | keep8 | boulevard | outage | 24 | 4226 | 942 | 0.555 | 4.06 | 12.96 | 15.52 |
| drift90 | keep8 | boulevard | fix | 24 | 36251 | 755 | 0.445 | 1.1 | 4.17 | 16.26 |
| outage90 | diag16 | bayside | checkpoint | 24 | 6316 | 0 | 0.0 | 0.49 | 1.52 | 1.99 |
| outage90 | diag16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | diag16 | bayside | other | 24 | 26540 | 32 | 1.0 | 0.55 | 3.13 | 7.25 |
| outage90 | diag16 | bayside | outage | 22 | 2833 | 11 | 0.344 | 1.75 | 3.13 | 3.19 |
| outage90 | diag16 | bayside | fix | 24 | 30023 | 21 | 0.656 | 0.52 | 1.79 | 7.25 |
| outage90 | diag16 | blocks | checkpoint | 24 | 7828 | 3237 | 0.95 | 7.56 | 10.54 | 10.94 |
| outage90 | diag16 | blocks | corner | 24 | 8710 | 13 | 0.004 | 1.44 | 3.4 | 6.19 |
| outage90 | diag16 | blocks | other | 24 | 18879 | 158 | 0.046 | 0.81 | 5.38 | 7.76 |
| outage90 | diag16 | blocks | outage | 23 | 3214 | 140 | 0.041 | 2.14 | 5.49 | 6.83 |
| outage90 | diag16 | blocks | fix | 24 | 32203 | 3268 | 0.959 | 1.24 | 9.16 | 10.94 |
| outage90 | diag16 | boulevard | checkpoint | 24 | 6317 | 443 | 0.262 | 3.39 | 5.97 | 6.33 |
| outage90 | diag16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | diag16 | boulevard | other | 24 | 33671 | 1248 | 0.738 | 1.79 | 5.25 | 8.01 |
| outage90 | diag16 | boulevard | outage | 24 | 4158 | 248 | 0.147 | 2.5 | 4.34 | 4.76 |
| outage90 | diag16 | boulevard | fix | 24 | 35830 | 1443 | 0.853 | 1.94 | 5.25 | 8.12 |
| outage90 | keep16 | bayside | checkpoint | 24 | 6319 | 0 | 0.0 | 0.47 | 1.5 | 1.99 |
| outage90 | keep16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep16 | bayside | other | 24 | 26544 | 34 | 1.0 | 0.55 | 3.13 | 7.25 |
| outage90 | keep16 | bayside | outage | 22 | 2834 | 11 | 0.324 | 1.48 | 3.13 | 3.19 |
| outage90 | keep16 | bayside | fix | 24 | 30029 | 23 | 0.676 | 0.53 | 1.79 | 7.25 |
| outage90 | keep16 | blocks | checkpoint | 24 | 8262 | 11 | 0.186 | 0.73 | 2.94 | 3.86 |
| outage90 | keep16 | blocks | corner | 24 | 8674 | 21 | 0.356 | 1.13 | 3.23 | 5.82 |
| outage90 | keep16 | blocks | other | 24 | 18825 | 27 | 0.458 | 0.62 | 4.24 | 7.08 |
| outage90 | keep16 | blocks | outage | 23 | 3250 | 0 | 0.0 | 1.64 | 3.89 | 5.69 |
| outage90 | keep16 | blocks | fix | 24 | 32511 | 59 | 1.0 | 0.69 | 3.25 | 7.66 |
| outage90 | keep16 | boulevard | checkpoint | 24 | 6317 | 21 | 0.095 | 0.49 | 1.54 | 1.88 |
| outage90 | keep16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep16 | boulevard | other | 24 | 33670 | 201 | 0.905 | 0.6 | 2.74 | 7.45 |
| outage90 | keep16 | boulevard | outage | 24 | 4155 | 138 | 0.622 | 1.76 | 3.55 | 4.14 |
| outage90 | keep16 | boulevard | fix | 24 | 35832 | 84 | 0.378 | 0.55 | 2.06 | 7.45 |
| outage90 | keep24 | bayside | checkpoint | 24 | 6290 | 0 | 0.0 | 0.68 | 1.88 | 2.47 |
| outage90 | keep24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep24 | bayside | other | 24 | 26335 | 69 | 1.0 | 0.91 | 3.42 | 7.79 |
| outage90 | keep24 | bayside | outage | 22 | 2842 | 0 | 0.0 | 1.82 | 3.92 | 4.25 |
| outage90 | keep24 | bayside | fix | 24 | 29783 | 69 | 1.0 | 0.86 | 2.87 | 7.79 |
| outage90 | keep24 | blocks | checkpoint | 24 | 8034 | 6 | 0.023 | 0.69 | 2.34 | 3.73 |
| outage90 | keep24 | blocks | corner | 24 | 7584 | 69 | 0.262 | 1.16 | 4.8 | 7.16 |
| outage90 | keep24 | blocks | other | 24 | 18795 | 188 | 0.715 | 0.68 | 4.98 | 8.42 |
| outage90 | keep24 | blocks | outage | 22 | 3063 | 75 | 0.285 | 2.07 | 5.77 | 7.54 |
| outage90 | keep24 | blocks | fix | 24 | 31350 | 188 | 0.715 | 0.68 | 3.98 | 8.58 |
| outage90 | keep24 | boulevard | checkpoint | 24 | 6287 | 12 | 0.05 | 0.64 | 1.63 | 2.25 |
| outage90 | keep24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep24 | boulevard | other | 24 | 33651 | 226 | 0.95 | 0.65 | 2.96 | 8.53 |
| outage90 | keep24 | boulevard | outage | 24 | 4141 | 35 | 0.147 | 1.35 | 3.79 | 3.92 |
| outage90 | keep24 | boulevard | fix | 24 | 35797 | 203 | 0.853 | 0.62 | 2.48 | 8.56 |
| outage90 | keep8 | bayside | checkpoint | 24 | 6372 | 0 | 0.0 | 0.6 | 1.88 | 2.38 |
| outage90 | keep8 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep8 | bayside | other | 24 | 26789 | 116 | 1.0 | 0.66 | 3.76 | 5.26 |
| outage90 | keep8 | bayside | outage | 22 | 2781 | 72 | 0.621 | 2.15 | 3.39 | 3.56 |
| outage90 | keep8 | bayside | fix | 24 | 30380 | 44 | 0.379 | 0.59 | 2.46 | 5.26 |
| outage90 | keep8 | blocks | checkpoint | 24 | 8840 | 102 | 0.226 | 0.87 | 4.42 | 6.12 |
| outage90 | keep8 | blocks | corner | 24 | 10079 | 56 | 0.124 | 1.18 | 4.8 | 6.22 |
| outage90 | keep8 | blocks | other | 24 | 18854 | 294 | 0.65 | 0.65 | 4.17 | 5.9 |
| outage90 | keep8 | blocks | outage | 24 | 3442 | 218 | 0.482 | 1.82 | 4.14 | 4.59 |
| outage90 | keep8 | blocks | fix | 24 | 34331 | 234 | 0.518 | 0.76 | 4.44 | 7.58 |
| outage90 | keep8 | boulevard | checkpoint | 24 | 6355 | 0 | 0.0 | 0.62 | 1.84 | 2.54 |
| outage90 | keep8 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep8 | boulevard | other | 24 | 33794 | 153 | 1.0 | 0.6 | 3.58 | 5.11 |
| outage90 | keep8 | boulevard | outage | 24 | 4118 | 64 | 0.418 | 2.13 | 3.98 | 4.19 |
| outage90 | keep8 | boulevard | fix | 24 | 36031 | 89 | 0.582 | 0.55 | 2.42 | 5.11 |

## Plans, and plans made before reaching the leg's first point

| profile | variant | course | missions | plans (median) | behind (median) |
|---|---|---|---|---|---|
| drift90 | diag16 | bayside | 24 | 5.0 | 3.0 |
| drift90 | diag16 | blocks | 24 | 6.0 | 4.0 |
| drift90 | diag16 | boulevard | 24 | 5.0 | 3.0 |
| drift90 | keep16 | bayside | 24 | 5.0 | 3.0 |
| drift90 | keep16 | blocks | 24 | 6.0 | 4.0 |
| drift90 | keep16 | boulevard | 24 | 5.0 | 3.0 |
| drift90 | keep24 | bayside | 24 | 5.0 | 3.0 |
| drift90 | keep24 | blocks | 24 | 6.0 | 4.0 |
| drift90 | keep24 | boulevard | 24 | 5.0 | 3.0 |
| drift90 | keep8 | bayside | 24 | 5.0 | 3.0 |
| drift90 | keep8 | blocks | 24 | 6.0 | 4.0 |
| drift90 | keep8 | boulevard | 24 | 5.5 | 3.0 |
| outage90 | diag16 | bayside | 24 | 5.0 | 3.0 |
| outage90 | diag16 | blocks | 24 | 6.0 | 4.0 |
| outage90 | diag16 | boulevard | 24 | 5.0 | 3.0 |
| outage90 | keep16 | bayside | 24 | 5.0 | 3.0 |
| outage90 | keep16 | blocks | 24 | 6.0 | 4.0 |
| outage90 | keep16 | boulevard | 24 | 5.0 | 3.0 |
| outage90 | keep24 | bayside | 24 | 5.0 | 3.0 |
| outage90 | keep24 | blocks | 24 | 6.0 | 4.0 |
| outage90 | keep24 | boulevard | 24 | 5.0 | 3.0 |
| outage90 | keep8 | bayside | 24 | 5.0 | 3.0 |
| outage90 | keep8 | blocks | 24 | 6.0 | 4.0 |
| outage90 | keep8 | boulevard | 24 | 5.0 | 3.0 |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| drift90 | diag16 | blocks | 24 | 9.0 | 1.71 | 5.35 | 7.75 | 2.4 | 4.61 |
| drift90 | keep16 | blocks | 24 | 9.0 | 1.69 | 4.63 | 7.67 | 2.27 | 4.76 |
| drift90 | keep24 | blocks | 24 | 9.0 | 1.97 | 5.81 | 7.88 | 0.17 | 3.46 |
| drift90 | keep8 | blocks | 24 | 9.0 | 1.81 | 5.13 | 6.67 | 4.45 | 6.4 |
| outage90 | diag16 | blocks | 24 | 9.0 | 1.44 | 3.4 | 6.19 | 2.09 | 2.92 |
| outage90 | keep16 | blocks | 24 | 9.0 | 1.13 | 3.23 | 5.82 | 2.25 | 3.4 |
| outage90 | keep24 | blocks | 24 | 9.0 | 1.16 | 4.8 | 7.16 | 0.17 | 1.19 |
| outage90 | keep8 | blocks | 24 | 9.0 | 1.18 | 4.8 | 6.22 | 4.34 | 6.12 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | diag16 | bayside | 24 | 1.54 | 5.45 |
| drift90 | diag16 | blocks | 24 | 2.19 | 9.93 |
| drift90 | diag16 | boulevard | 24 | 2.6 | 8.82 |
| drift90 | keep16 | bayside | 24 | 1.55 | 5.37 |
| drift90 | keep16 | blocks | 24 | 1.66 | 5.73 |
| drift90 | keep16 | boulevard | 24 | 1.6 | 7.15 |
| drift90 | keep24 | bayside | 24 | 2.14 | 6.65 |
| drift90 | keep24 | blocks | 24 | 1.96 | 6.83 |
| drift90 | keep24 | boulevard | 24 | 1.98 | 7.63 |
| drift90 | keep8 | bayside | 24 | 1.19 | 4.78 |
| drift90 | keep8 | blocks | 24 | 1.47 | 5.24 |
| drift90 | keep8 | boulevard | 24 | 1.23 | 6.7 |
| outage90 | diag16 | bayside | 24 | 0.56 | 2.82 |
| outage90 | diag16 | blocks | 24 | 1.25 | 9.11 |
| outage90 | diag16 | boulevard | 24 | 1.98 | 5.51 |
| outage90 | keep16 | bayside | 24 | 0.53 | 2.93 |
| outage90 | keep16 | blocks | 24 | 0.72 | 3.53 |
| outage90 | keep16 | boulevard | 24 | 0.58 | 2.54 |
| outage90 | keep24 | bayside | 24 | 0.88 | 3.16 |
| outage90 | keep24 | blocks | 24 | 0.73 | 4.33 |
| outage90 | keep24 | boulevard | 24 | 0.67 | 3.17 |
| outage90 | keep8 | bayside | 24 | 0.63 | 3.54 |
| outage90 | keep8 | blocks | 24 | 0.8 | 4.69 |
| outage90 | keep8 | boulevard | 24 | 0.59 | 3.52 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| drift90 | diag16 | bayside | 24 | 10.49 | 29.22 | 0 | 0 |
| drift90 | diag16 | blocks | 24 | 13.4 | 25.48 | 0 | 0 |
| drift90 | diag16 | boulevard | 24 | 15.0 | 38.03 | 0 | 0 |
| drift90 | keep16 | bayside | 24 | 10.4 | 29.48 | 0 | 0 |
| drift90 | keep16 | blocks | 24 | 10.35 | 27.17 | 0 | 0 |
| drift90 | keep16 | boulevard | 24 | 14.57 | 31.66 | 0 | 0 |
| drift90 | keep24 | bayside | 24 | 11.46 | 29.12 | 0 | 0 |
| drift90 | keep24 | blocks | 24 | 11.55 | 24.39 | 0 | 0 |
| drift90 | keep24 | boulevard | 24 | 14.38 | 29.0 | 0 | 0 |
| drift90 | keep8 | bayside | 24 | 12.46 | 48.35 | 0 | 0 |
| drift90 | keep8 | blocks | 24 | 11.7 | 33.92 | 0 | 0 |
| drift90 | keep8 | boulevard | 24 | 16.26 | 45.15 | 0 | 0 |
| outage90 | diag16 | bayside | 24 | 7.25 | 11.5 | 0 | 0 |
| outage90 | diag16 | blocks | 24 | 10.94 | 26.38 | 0 | 0 |
| outage90 | diag16 | boulevard | 24 | 8.12 | 19.11 | 0 | 0 |
| outage90 | keep16 | bayside | 24 | 7.25 | 11.5 | 0 | 0 |
| outage90 | keep16 | blocks | 24 | 7.66 | 9.03 | 0 | 0 |
| outage90 | keep16 | boulevard | 24 | 7.45 | 10.57 | 0 | 0 |
| outage90 | keep24 | bayside | 24 | 7.79 | 8.99 | 0 | 0 |
| outage90 | keep24 | blocks | 24 | 9.09 | 11.64 | 0 | 0 |
| outage90 | keep24 | boulevard | 24 | 8.56 | 10.9 | 0 | 0 |
| outage90 | keep8 | bayside | 24 | 5.26 | 11.73 | 0 | 0 |
| outage90 | keep8 | blocks | 24 | 7.62 | 33.54 | 0 | 0 |
| outage90 | keep8 | boulevard | 24 | 5.11 | 36.16 | 0 | 0 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| drift90 | diag16 | bayside | 24 | 5.45 | 8.93 |
| drift90 | diag16 | blocks | 24 | 5.26 | 8.96 |
| drift90 | diag16 | boulevard | 24 | 5.38 | 8.54 |
| drift90 | keep16 | bayside | 24 | 5.34 | 8.77 |
| drift90 | keep16 | blocks | 24 | 5.32 | 9.0 |
| drift90 | keep16 | boulevard | 24 | 5.33 | 8.54 |
| drift90 | keep24 | bayside | 24 | 5.09 | 8.38 |
| drift90 | keep24 | blocks | 24 | 5.88 | 8.66 |
| drift90 | keep24 | boulevard | 24 | 5.15 | 8.33 |
| drift90 | keep8 | bayside | 24 | 6.87 | 10.53 |
| drift90 | keep8 | blocks | 24 | 6.32 | 10.44 |
| drift90 | keep8 | boulevard | 24 | 6.42 | 9.87 |
| outage90 | diag16 | bayside | 24 | 1.62 | 4.56 |
| outage90 | diag16 | blocks | 24 | 1.6 | 4.47 |
| outage90 | diag16 | boulevard | 24 | 1.56 | 4.2 |
| outage90 | keep16 | bayside | 24 | 1.61 | 4.53 |
| outage90 | keep16 | blocks | 24 | 1.58 | 4.31 |
| outage90 | keep16 | boulevard | 24 | 1.6 | 4.2 |
| outage90 | keep24 | bayside | 24 | 1.63 | 4.33 |
| outage90 | keep24 | blocks | 24 | 1.59 | 4.46 |
| outage90 | keep24 | boulevard | 24 | 1.56 | 4.06 |
| outage90 | keep8 | bayside | 24 | 1.76 | 5.02 |
| outage90 | keep8 | blocks | 24 | 1.89 | 5.37 |
| outage90 | keep8 | boulevard | 24 | 1.55 | 4.52 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | diag16 | bayside | 24 | 6.5 | 8.95 |
| drift90 | diag16 | blocks | 24 | 6.42 | 8.61 |
| drift90 | diag16 | boulevard | 24 | 6.55 | 9.09 |
| drift90 | keep16 | bayside | 24 | 6.5 | 8.96 |
| drift90 | keep16 | blocks | 24 | 6.45 | 8.72 |
| drift90 | keep16 | boulevard | 24 | 6.55 | 9.07 |
| drift90 | keep24 | bayside | 24 | 6.49 | 8.86 |
| drift90 | keep24 | blocks | 24 | 6.42 | 8.64 |
| drift90 | keep24 | boulevard | 24 | 6.55 | 9.13 |
| drift90 | keep8 | bayside | 24 | 6.45 | 8.88 |
| drift90 | keep8 | blocks | 24 | 6.39 | 8.64 |
| drift90 | keep8 | boulevard | 24 | 6.53 | 9.13 |
| outage90 | diag16 | bayside | 24 | 6.39 | 8.52 |
| outage90 | diag16 | blocks | 24 | 6.36 | 8.41 |
| outage90 | diag16 | boulevard | 24 | 6.53 | 8.66 |
| outage90 | keep16 | bayside | 24 | 6.41 | 8.53 |
| outage90 | keep16 | blocks | 24 | 6.39 | 8.39 |
| outage90 | keep16 | boulevard | 24 | 6.53 | 8.62 |
| outage90 | keep24 | bayside | 24 | 6.4 | 8.52 |
| outage90 | keep24 | blocks | 24 | 6.38 | 8.41 |
| outage90 | keep24 | boulevard | 24 | 6.51 | 8.62 |
| outage90 | keep8 | bayside | 24 | 6.42 | 8.61 |
| outage90 | keep8 | blocks | 24 | 6.41 | 8.48 |
| outage90 | keep8 | boulevard | 24 | 6.5 | 8.61 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| drift90 | diag16 | bayside | 24 | 0.0338 |
| drift90 | diag16 | blocks | 24 | 0.0456 |
| drift90 | diag16 | boulevard | 24 | 0.0313 |
| drift90 | keep16 | bayside | 24 | 0.0338 |
| drift90 | keep16 | blocks | 24 | 0.0449 |
| drift90 | keep16 | boulevard | 24 | 0.0307 |
| drift90 | keep24 | bayside | 24 | 0.0304 |
| drift90 | keep24 | blocks | 24 | 0.0413 |
| drift90 | keep24 | boulevard | 24 | 0.0274 |
| drift90 | keep8 | bayside | 24 | 0.0482 |
| drift90 | keep8 | blocks | 24 | 0.0609 |
| drift90 | keep8 | boulevard | 24 | 0.0437 |
| outage90 | diag16 | bayside | 24 | 0.0301 |
| outage90 | diag16 | blocks | 24 | 0.0431 |
| outage90 | diag16 | boulevard | 24 | 0.0272 |
| outage90 | keep16 | bayside | 24 | 0.0301 |
| outage90 | keep16 | blocks | 24 | 0.0421 |
| outage90 | keep16 | boulevard | 24 | 0.0267 |
| outage90 | keep24 | bayside | 24 | 0.0261 |
| outage90 | keep24 | blocks | 24 | 0.0382 |
| outage90 | keep24 | boulevard | 24 | 0.0232 |
| outage90 | keep8 | bayside | 24 | 0.045 |
| outage90 | keep8 | blocks | 24 | 0.0579 |
| outage90 | keep8 | boulevard | 24 | 0.0405 |
