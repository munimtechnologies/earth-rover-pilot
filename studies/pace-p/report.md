# Does a longer lookahead save time on straights, or only at corners? (simulated)

pace_p.py 0.1.0 (pace_o.py 0.1.0, pace_m.py 0.1.0, rover_pilot.py 0.18.1, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.1's real-rover pilot (pace_m.py's long20 learner on pace_l.py's bridge120+cf0.3) on pace_o.py's keep planner, on pace_l.py's outage90 (90 s GPS outages, a steady compass error) or drift90 (the compass error drifts, SD 10 deg, 120 s time constant); only the path follower changes (keep: a plain lookahead; bend and calm: the long lookahead unless the path ahead turns by 45 or 10 deg, then 16 m). Seeds 253-276. 720 of 720 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_o.py's runs: 36 compared, 36 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | keep16 | 72/72 | 0.884 | 0.995 | 71 | 0.999 | 0.017 |
| outage90 | keep24 | 72/72 | 0.888 | 0.999 | 72 | 0.993 | 0.018 |
| outage90 | bend24 | 72/72 | 0.887 | 0.998 | 72 | 0.994 | 0.016 |
| outage90 | calm24 | 72/72 | 0.884 | 0.995 | 71 | 0.998 | 0.017 |
| outage90 | calm32 | 72/72 | 0.885 | 0.995 | 71 | 0.998 | 0.017 |
| drift90 | keep16 | 72/72 | 0.88 | 0.99 | 70 | 1.002 | 0.019 |
| drift90 | keep24 | 72/72 | 0.884 | 0.995 | 71 | 0.999 | 0.02 |
| drift90 | bend24 | 72/72 | 0.883 | 0.993 | 70 | 1.0 | 0.018 |
| drift90 | calm24 | 72/72 | 0.881 | 0.991 | 70 | 1.002 | 0.019 |
| drift90 | calm32 | 72/72 | 0.879 | 0.989 | 70 | 1.002 | 0.02 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| drift90 | keep24 | keep16 | 2/3 | 0 | 0 | 0 | -0.0316 |
| outage90 | keep24 | keep16 | 3/3 | 0 | 0 | 0 | -0.0382 |
| drift90 | bend24 | keep16 | 1/3 | 0 | 0 | 0 | -0.0076 |
| outage90 | bend24 | keep16 | 3/3 | 0 | 0 | 0 | -0.007 |
| drift90 | calm24 | keep16 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | calm24 | keep16 | 2/3 | 0 | 0 | 0 | 0.0 |
| drift90 | calm32 | keep16 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | calm32 | keep16 | 3/3 | 0 | 0 | 0 | -0.0007 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| drift90 | keep24 | keep16 | bayside | 23 | 0 | -12.0 | -0.0083 | 0.0 |
| drift90 | keep24 | keep16 | blocks | 22 | 0 | -50.0 | -0.0316 | 0.0 |
| drift90 | keep24 | keep16 | boulevard | 3 | 2 | 0.0 | 0.0 | 1.0 |
| outage90 | keep24 | keep16 | bayside | 22 | 0 | -10.0 | -0.007 | 0.0 |
| outage90 | keep24 | keep16 | blocks | 22 | 0 | -60.0 | -0.0382 | 0.0 |
| outage90 | keep24 | keep16 | boulevard | 9 | 0 | 0.0 | 0.0 | 0.0039 |
| drift90 | bend24 | keep16 | bayside | 23 | 0 | -11.0 | -0.0076 | 0.0 |
| drift90 | bend24 | keep16 | blocks | 4 | 4 | 0.0 | 0.0 | 1.0 |
| drift90 | bend24 | keep16 | boulevard | 3 | 2 | 0.0 | 0.0 | 1.0 |
| outage90 | bend24 | keep16 | bayside | 22 | 0 | -10.0 | -0.007 | 0.0 |
| outage90 | bend24 | keep16 | blocks | 11 | 1 | 0.0 | 0.0 | 0.0063 |
| outage90 | bend24 | keep16 | boulevard | 9 | 0 | 0.0 | 0.0 | 0.0039 |
| drift90 | calm24 | keep16 | bayside | 9 | 2 | 0.0 | 0.0 | 0.0654 |
| drift90 | calm24 | keep16 | blocks | 4 | 4 | 0.0 | 0.0 | 1.0 |
| drift90 | calm24 | keep16 | boulevard | 1 | 3 | 0.0 | 0.0 | 0.625 |
| outage90 | calm24 | keep16 | bayside | 10 | 2 | 0.0 | 0.0 | 0.0386 |
| outage90 | calm24 | keep16 | blocks | 11 | 1 | 0.0 | 0.0 | 0.0063 |
| outage90 | calm24 | keep16 | boulevard | 5 | 0 | 0.0 | 0.0 | 0.0625 |
| drift90 | calm32 | keep16 | bayside | 6 | 7 | 0.0 | 0.0 | 1.0 |
| drift90 | calm32 | keep16 | blocks | 4 | 6 | 0.0 | 0.0 | 0.7539 |
| drift90 | calm32 | keep16 | boulevard | 2 | 2 | 0.0 | 0.0 | 1.0 |
| outage90 | calm32 | keep16 | bayside | 12 | 2 | -1.0 | -0.0007 | 0.0129 |
| outage90 | calm32 | keep16 | blocks | 10 | 2 | 0.0 | 0.0 | 0.0386 |
| outage90 | calm32 | keep16 | boulevard | 6 | 0 | 0.0 | 0.0 | 0.0312 |

## What the drift costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| keep16 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.007 |
| keep24 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0106 |
| bend24 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0056 |
| calm24 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.007 |
| calm32 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0084 |

## How often the follower aimed long

| profile | variant | course | missions | targets (median) | long share (median) |
|---|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 14250.0 | 1.0 |
| drift90 | bend24 | blocks | 24 | 15752.0 | 0.83 |
| drift90 | bend24 | boulevard | 24 | 17592.5 | 1.0 |
| drift90 | calm24 | bayside | 24 | 14335.5 | 0.599 |
| drift90 | calm24 | blocks | 24 | 15752.0 | 0.83 |
| drift90 | calm24 | boulevard | 24 | 17592.5 | 0.978 |
| drift90 | calm32 | bayside | 24 | 14379.5 | 0.52 |
| drift90 | calm32 | blocks | 24 | 15772.0 | 0.778 |
| drift90 | calm32 | boulevard | 24 | 17592.5 | 0.981 |
| outage90 | bend24 | bayside | 24 | 14186.5 | 1.0 |
| outage90 | bend24 | blocks | 24 | 15631.5 | 0.83 |
| outage90 | bend24 | boulevard | 24 | 17530.5 | 1.0 |
| outage90 | calm24 | bayside | 24 | 14261.5 | 0.609 |
| outage90 | calm24 | blocks | 24 | 15631.5 | 0.83 |
| outage90 | calm24 | boulevard | 24 | 17541.0 | 0.976 |
| outage90 | calm32 | bayside | 24 | 14279.5 | 0.53 |
| outage90 | calm32 | blocks | 24 | 15631.5 | 0.778 |
| outage90 | calm32 | boulevard | 24 | 17530.5 | 0.975 |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| drift90 | bend24 | blocks | 24 | 9.0 | 1.62 | 4.39 | 7.05 | 1.9 | 5.09 |
| drift90 | calm24 | blocks | 24 | 9.0 | 1.62 | 4.39 | 7.05 | 1.9 | 5.09 |
| drift90 | calm32 | blocks | 24 | 9.0 | 1.6 | 4.84 | 7.23 | 1.9 | 5.21 |
| drift90 | keep16 | blocks | 24 | 9.0 | 1.6 | 4.28 | 5.9 | 2.05 | 4.88 |
| drift90 | keep24 | blocks | 24 | 9.0 | 1.9 | 5.48 | 7.21 | 0.21 | 4.1 |
| outage90 | bend24 | blocks | 24 | 9.0 | 1.09 | 2.97 | 3.69 | 2.08 | 3.0 |
| outage90 | calm24 | blocks | 24 | 9.0 | 1.09 | 2.97 | 3.69 | 2.08 | 3.0 |
| outage90 | calm32 | blocks | 24 | 9.0 | 1.06 | 2.92 | 3.71 | 1.95 | 2.97 |
| outage90 | keep16 | blocks | 24 | 9.0 | 1.04 | 2.94 | 4.01 | 2.08 | 3.1 |
| outage90 | keep24 | blocks | 24 | 9.0 | 1.04 | 4.37 | 5.55 | 0.14 | 1.15 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| drift90 | bend24 | bayside | checkpoint | 24 | 6339 | 100 | 0.073 | 1.57 | 4.62 | 5.06 |
| drift90 | bend24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | bend24 | bayside | other | 24 | 26490 | 1275 | 0.927 | 2.08 | 7.32 | 10.29 |
| drift90 | bend24 | bayside | outage | 17 | 2898 | 671 | 0.488 | 3.33 | 9.6 | 10.32 |
| drift90 | bend24 | bayside | fix | 24 | 29931 | 704 | 0.512 | 1.94 | 5.58 | 9.61 |
| drift90 | bend24 | blocks | checkpoint | 24 | 8406 | 238 | 0.209 | 1.83 | 5.05 | 6.21 |
| drift90 | bend24 | blocks | corner | 24 | 8662 | 109 | 0.096 | 1.62 | 4.39 | 7.05 |
| drift90 | bend24 | blocks | other | 24 | 18939 | 790 | 0.695 | 2.12 | 6.39 | 10.61 |
| drift90 | bend24 | blocks | outage | 18 | 3238 | 507 | 0.446 | 3.03 | 7.36 | 8.52 |
| drift90 | bend24 | blocks | fix | 24 | 32769 | 630 | 0.554 | 1.87 | 5.71 | 10.15 |
| drift90 | bend24 | boulevard | checkpoint | 24 | 6382 | 260 | 0.146 | 1.76 | 5.27 | 5.75 |
| drift90 | bend24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | bend24 | boulevard | other | 24 | 33790 | 1525 | 0.854 | 2.13 | 6.94 | 11.7 |
| drift90 | bend24 | boulevard | outage | 20 | 3748 | 815 | 0.457 | 3.05 | 10.1 | 10.92 |
| drift90 | bend24 | boulevard | fix | 24 | 36424 | 970 | 0.543 | 1.98 | 6.04 | 11.52 |
| drift90 | calm24 | bayside | checkpoint | 24 | 6368 | 85 | 0.066 | 1.5 | 3.96 | 4.42 |
| drift90 | calm24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | calm24 | bayside | other | 24 | 26661 | 1194 | 0.934 | 1.68 | 6.46 | 10.52 |
| drift90 | calm24 | bayside | outage | 17 | 2886 | 577 | 0.451 | 3.34 | 8.84 | 9.55 |
| drift90 | calm24 | bayside | fix | 24 | 30143 | 702 | 0.549 | 1.65 | 5.5 | 10.23 |
| drift90 | calm24 | blocks | checkpoint | 24 | 8406 | 238 | 0.209 | 1.83 | 5.05 | 6.21 |
| drift90 | calm24 | blocks | corner | 24 | 8662 | 109 | 0.096 | 1.62 | 4.39 | 7.05 |
| drift90 | calm24 | blocks | other | 24 | 18939 | 790 | 0.695 | 2.12 | 6.39 | 10.61 |
| drift90 | calm24 | blocks | outage | 18 | 3238 | 507 | 0.446 | 3.03 | 7.36 | 8.52 |
| drift90 | calm24 | blocks | fix | 24 | 32769 | 630 | 0.554 | 1.87 | 5.71 | 10.15 |
| drift90 | calm24 | boulevard | checkpoint | 24 | 6388 | 260 | 0.138 | 1.69 | 4.84 | 5.45 |
| drift90 | calm24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | calm24 | boulevard | other | 24 | 33797 | 1624 | 0.862 | 2.05 | 7.12 | 11.7 |
| drift90 | calm24 | boulevard | outage | 20 | 3751 | 814 | 0.432 | 3.29 | 9.82 | 10.96 |
| drift90 | calm24 | boulevard | fix | 24 | 36434 | 1070 | 0.568 | 1.89 | 5.84 | 11.52 |
| drift90 | calm32 | bayside | checkpoint | 24 | 6362 | 83 | 0.053 | 1.54 | 4.46 | 5.0 |
| drift90 | calm32 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | calm32 | bayside | other | 24 | 26727 | 1486 | 0.947 | 1.92 | 7.02 | 9.96 |
| drift90 | calm32 | bayside | outage | 18 | 2898 | 725 | 0.462 | 3.49 | 8.21 | 8.84 |
| drift90 | calm32 | bayside | fix | 24 | 30191 | 844 | 0.538 | 1.83 | 6.38 | 9.96 |
| drift90 | calm32 | blocks | checkpoint | 24 | 8405 | 259 | 0.165 | 2.1 | 5.61 | 6.92 |
| drift90 | calm32 | blocks | corner | 24 | 8652 | 117 | 0.074 | 1.6 | 4.84 | 7.23 |
| drift90 | calm32 | blocks | other | 24 | 18960 | 1195 | 0.761 | 2.62 | 7.0 | 11.68 |
| drift90 | calm32 | blocks | outage | 18 | 3246 | 555 | 0.353 | 2.13 | 7.21 | 8.76 |
| drift90 | calm32 | blocks | fix | 24 | 32771 | 1016 | 0.647 | 2.08 | 6.64 | 10.4 |
| drift90 | calm32 | boulevard | checkpoint | 24 | 6389 | 321 | 0.148 | 1.79 | 5.12 | 5.94 |
| drift90 | calm32 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | calm32 | boulevard | other | 24 | 33781 | 1843 | 0.852 | 2.41 | 7.62 | 12.32 |
| drift90 | calm32 | boulevard | outage | 20 | 3752 | 765 | 0.354 | 3.12 | 9.29 | 9.42 |
| drift90 | calm32 | boulevard | fix | 24 | 36418 | 1399 | 0.646 | 2.23 | 6.75 | 12.11 |
| drift90 | keep16 | bayside | checkpoint | 24 | 6374 | 38 | 0.035 | 1.3 | 3.74 | 4.11 |
| drift90 | keep16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep16 | bayside | other | 24 | 26690 | 1060 | 0.965 | 1.5 | 5.88 | 9.79 |
| drift90 | keep16 | bayside | outage | 17 | 2881 | 581 | 0.529 | 3.09 | 9.68 | 10.07 |
| drift90 | keep16 | bayside | fix | 24 | 30183 | 517 | 0.471 | 1.37 | 4.78 | 9.73 |
| drift90 | keep16 | blocks | checkpoint | 24 | 8408 | 222 | 0.231 | 1.55 | 4.36 | 5.21 |
| drift90 | keep16 | blocks | corner | 24 | 8693 | 128 | 0.133 | 1.6 | 4.28 | 5.9 |
| drift90 | keep16 | blocks | other | 24 | 18922 | 609 | 0.635 | 1.65 | 5.95 | 9.12 |
| drift90 | keep16 | blocks | outage | 18 | 3248 | 527 | 0.55 | 2.66 | 8.43 | 9.38 |
| drift90 | keep16 | blocks | fix | 24 | 32775 | 432 | 0.45 | 1.54 | 4.91 | 9.21 |
| drift90 | keep16 | boulevard | checkpoint | 24 | 6383 | 161 | 0.106 | 1.43 | 3.75 | 4.4 |
| drift90 | keep16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep16 | boulevard | other | 24 | 33805 | 1364 | 0.894 | 1.71 | 5.79 | 10.41 |
| drift90 | keep16 | boulevard | outage | 20 | 3761 | 855 | 0.561 | 2.71 | 10.0 | 10.81 |
| drift90 | keep16 | boulevard | fix | 24 | 36427 | 670 | 0.439 | 1.58 | 4.64 | 10.07 |
| drift90 | keep24 | bayside | checkpoint | 24 | 6341 | 100 | 0.073 | 1.57 | 4.62 | 5.0 |
| drift90 | keep24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep24 | bayside | other | 24 | 26475 | 1270 | 0.927 | 2.06 | 7.32 | 10.29 |
| drift90 | keep24 | bayside | outage | 17 | 2897 | 669 | 0.488 | 3.51 | 9.6 | 10.14 |
| drift90 | keep24 | bayside | fix | 24 | 29919 | 701 | 0.512 | 1.94 | 5.58 | 9.68 |
| drift90 | keep24 | blocks | checkpoint | 24 | 8196 | 237 | 0.16 | 1.88 | 5.95 | 6.99 |
| drift90 | keep24 | blocks | corner | 24 | 7642 | 145 | 0.098 | 1.9 | 5.48 | 7.21 |
| drift90 | keep24 | blocks | other | 24 | 18986 | 1096 | 0.742 | 2.25 | 6.58 | 10.22 |
| drift90 | keep24 | blocks | outage | 18 | 3013 | 666 | 0.451 | 3.83 | 8.57 | 9.03 |
| drift90 | keep24 | blocks | fix | 24 | 31811 | 812 | 0.549 | 1.95 | 6.03 | 10.22 |
| drift90 | keep24 | boulevard | checkpoint | 24 | 6381 | 259 | 0.145 | 1.76 | 5.27 | 5.75 |
| drift90 | keep24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| drift90 | keep24 | boulevard | other | 24 | 33790 | 1525 | 0.855 | 2.13 | 6.94 | 11.7 |
| drift90 | keep24 | boulevard | outage | 20 | 3747 | 815 | 0.457 | 3.05 | 10.1 | 10.92 |
| drift90 | keep24 | boulevard | fix | 24 | 36424 | 969 | 0.543 | 1.98 | 6.04 | 11.52 |
| outage90 | bend24 | bayside | checkpoint | 24 | 6279 | 24 | 0.358 | 0.81 | 2.08 | 2.62 |
| outage90 | bend24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | bend24 | bayside | other | 24 | 26349 | 43 | 0.642 | 0.87 | 3.26 | 7.75 |
| outage90 | bend24 | bayside | outage | 17 | 2965 | 0 | 0.0 | 1.55 | 3.52 | 4.35 |
| outage90 | bend24 | bayside | fix | 24 | 29663 | 67 | 1.0 | 0.79 | 2.67 | 7.75 |
| outage90 | bend24 | blocks | checkpoint | 24 | 8306 | 69 | 0.24 | 1.0 | 2.6 | 3.2 |
| outage90 | bend24 | blocks | corner | 24 | 8712 | 6 | 0.021 | 1.09 | 2.97 | 3.69 |
| outage90 | bend24 | blocks | other | 24 | 18735 | 212 | 0.739 | 0.84 | 4.08 | 8.72 |
| outage90 | bend24 | blocks | outage | 18 | 3358 | 5 | 0.017 | 1.64 | 3.95 | 4.58 |
| outage90 | bend24 | blocks | fix | 24 | 32395 | 282 | 0.983 | 0.87 | 3.27 | 8.83 |
| outage90 | bend24 | boulevard | checkpoint | 24 | 6283 | 0 | 0.0 | 0.53 | 1.56 | 2.21 |
| outage90 | bend24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | bend24 | boulevard | other | 24 | 33603 | 266 | 1.0 | 0.66 | 2.71 | 8.85 |
| outage90 | bend24 | boulevard | outage | 20 | 3743 | 28 | 0.105 | 1.52 | 3.58 | 4.5 |
| outage90 | bend24 | boulevard | fix | 24 | 36143 | 238 | 0.895 | 0.6 | 2.5 | 8.85 |
| outage90 | calm24 | bayside | checkpoint | 24 | 6318 | 26 | 0.236 | 0.61 | 1.58 | 1.96 |
| outage90 | calm24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | calm24 | bayside | other | 24 | 26497 | 84 | 0.764 | 0.65 | 3.71 | 7.68 |
| outage90 | calm24 | bayside | outage | 17 | 2904 | 2 | 0.018 | 1.5 | 3.07 | 3.59 |
| outage90 | calm24 | bayside | fix | 24 | 29911 | 108 | 0.982 | 0.6 | 2.61 | 7.68 |
| outage90 | calm24 | blocks | checkpoint | 24 | 8306 | 69 | 0.24 | 1.0 | 2.6 | 3.2 |
| outage90 | calm24 | blocks | corner | 24 | 8712 | 6 | 0.021 | 1.09 | 2.97 | 3.69 |
| outage90 | calm24 | blocks | other | 24 | 18735 | 212 | 0.739 | 0.84 | 4.08 | 8.72 |
| outage90 | calm24 | blocks | outage | 18 | 3358 | 5 | 0.017 | 1.64 | 3.95 | 4.58 |
| outage90 | calm24 | blocks | fix | 24 | 32395 | 282 | 0.983 | 0.87 | 3.27 | 8.83 |
| outage90 | calm24 | boulevard | checkpoint | 24 | 6294 | 0 | 0.0 | 0.52 | 1.43 | 1.61 |
| outage90 | calm24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | calm24 | boulevard | other | 24 | 33609 | 230 | 1.0 | 0.6 | 3.02 | 8.85 |
| outage90 | calm24 | boulevard | outage | 20 | 3748 | 6 | 0.026 | 1.69 | 3.88 | 4.8 |
| outage90 | calm24 | boulevard | fix | 24 | 36155 | 224 | 0.974 | 0.55 | 2.65 | 8.85 |
| outage90 | calm32 | bayside | checkpoint | 24 | 6316 | 0 | 0.0 | 0.6 | 1.79 | 2.18 |
| outage90 | calm32 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | calm32 | bayside | other | 24 | 26508 | 31 | 1.0 | 0.71 | 3.88 | 7.44 |
| outage90 | calm32 | bayside | outage | 17 | 2915 | 6 | 0.194 | 1.11 | 2.96 | 3.7 |
| outage90 | calm32 | bayside | fix | 24 | 29909 | 25 | 0.806 | 0.65 | 3.33 | 7.39 |
| outage90 | calm32 | blocks | checkpoint | 24 | 8294 | 71 | 0.174 | 1.17 | 3.0 | 3.44 |
| outage90 | calm32 | blocks | corner | 24 | 8704 | 5 | 0.012 | 1.06 | 2.92 | 3.71 |
| outage90 | calm32 | blocks | other | 24 | 18736 | 332 | 0.814 | 1.0 | 4.65 | 9.38 |
| outage90 | calm32 | blocks | outage | 18 | 3348 | 4 | 0.01 | 1.59 | 3.9 | 5.04 |
| outage90 | calm32 | blocks | fix | 24 | 32386 | 404 | 0.99 | 1.0 | 3.56 | 9.38 |
| outage90 | calm32 | boulevard | checkpoint | 24 | 6289 | 0 | 0.0 | 0.53 | 1.3 | 1.75 |
| outage90 | calm32 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | calm32 | boulevard | other | 24 | 33607 | 344 | 1.0 | 0.69 | 3.31 | 9.38 |
| outage90 | calm32 | boulevard | outage | 20 | 3745 | 5 | 0.015 | 1.58 | 3.69 | 4.71 |
| outage90 | calm32 | boulevard | fix | 24 | 36151 | 339 | 0.985 | 0.63 | 3.06 | 9.38 |
| outage90 | keep16 | bayside | checkpoint | 24 | 6328 | 33 | 0.786 | 0.46 | 1.41 | 1.68 |
| outage90 | keep16 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep16 | bayside | other | 24 | 26539 | 9 | 0.214 | 0.56 | 3.05 | 7.19 |
| outage90 | keep16 | bayside | outage | 17 | 2916 | 0 | 0.0 | 1.29 | 3.17 | 3.57 |
| outage90 | keep16 | bayside | fix | 24 | 29951 | 42 | 1.0 | 0.49 | 2.06 | 7.19 |
| outage90 | keep16 | blocks | checkpoint | 24 | 8309 | 63 | 0.496 | 0.79 | 2.58 | 3.33 |
| outage90 | keep16 | blocks | corner | 24 | 8717 | 7 | 0.055 | 1.04 | 2.94 | 4.01 |
| outage90 | keep16 | blocks | other | 24 | 18785 | 57 | 0.449 | 0.67 | 3.5 | 7.6 |
| outage90 | keep16 | blocks | outage | 18 | 3382 | 8 | 0.063 | 1.53 | 3.81 | 4.77 |
| outage90 | keep16 | blocks | fix | 24 | 32429 | 119 | 0.937 | 0.71 | 3.08 | 8.05 |
| outage90 | keep16 | boulevard | checkpoint | 24 | 6294 | 0 | 0.0 | 0.48 | 1.42 | 1.82 |
| outage90 | keep16 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep16 | boulevard | other | 24 | 33634 | 78 | 1.0 | 0.58 | 2.75 | 7.42 |
| outage90 | keep16 | boulevard | outage | 20 | 3757 | 0 | 0.0 | 1.69 | 3.05 | 3.46 |
| outage90 | keep16 | boulevard | fix | 24 | 36171 | 78 | 1.0 | 0.53 | 2.07 | 7.42 |
| outage90 | keep24 | bayside | checkpoint | 24 | 6280 | 24 | 0.343 | 0.81 | 2.16 | 2.62 |
| outage90 | keep24 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep24 | bayside | other | 24 | 26345 | 46 | 0.657 | 0.88 | 3.26 | 7.75 |
| outage90 | keep24 | bayside | outage | 17 | 2964 | 0 | 0.0 | 1.55 | 3.52 | 4.9 |
| outage90 | keep24 | bayside | fix | 24 | 29661 | 70 | 1.0 | 0.79 | 2.67 | 7.75 |
| outage90 | keep24 | blocks | checkpoint | 24 | 8097 | 41 | 0.138 | 0.72 | 2.66 | 4.3 |
| outage90 | keep24 | blocks | corner | 24 | 7626 | 48 | 0.162 | 1.04 | 4.37 | 5.55 |
| outage90 | keep24 | blocks | other | 24 | 18727 | 208 | 0.7 | 0.62 | 4.31 | 8.72 |
| outage90 | keep24 | blocks | outage | 18 | 3034 | 63 | 0.212 | 1.88 | 5.16 | 6.75 |
| outage90 | keep24 | blocks | fix | 24 | 31416 | 234 | 0.788 | 0.66 | 4.09 | 8.77 |
| outage90 | keep24 | boulevard | checkpoint | 24 | 6283 | 0 | 0.0 | 0.53 | 1.56 | 2.21 |
| outage90 | keep24 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | keep24 | boulevard | other | 24 | 33603 | 266 | 1.0 | 0.66 | 2.71 | 8.85 |
| outage90 | keep24 | boulevard | outage | 20 | 3743 | 28 | 0.105 | 1.52 | 3.58 | 4.5 |
| outage90 | keep24 | boulevard | fix | 24 | 36143 | 238 | 0.895 | 0.6 | 2.47 | 8.85 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 2.01 | 6.77 |
| drift90 | bend24 | blocks | 24 | 1.96 | 6.09 |
| drift90 | bend24 | boulevard | 24 | 2.09 | 6.58 |
| drift90 | calm24 | bayside | 24 | 1.73 | 6.02 |
| drift90 | calm24 | blocks | 24 | 1.96 | 6.09 |
| drift90 | calm24 | boulevard | 24 | 2.0 | 6.98 |
| drift90 | calm32 | bayside | 24 | 1.9 | 6.75 |
| drift90 | calm32 | blocks | 24 | 2.16 | 6.99 |
| drift90 | calm32 | boulevard | 24 | 2.24 | 7.39 |
| drift90 | keep16 | bayside | 24 | 1.46 | 5.46 |
| drift90 | keep16 | blocks | 24 | 1.59 | 5.13 |
| drift90 | keep16 | boulevard | 24 | 1.6 | 5.49 |
| drift90 | keep24 | bayside | 24 | 2.0 | 6.72 |
| drift90 | keep24 | blocks | 24 | 2.07 | 6.56 |
| drift90 | keep24 | boulevard | 24 | 2.09 | 6.58 |
| outage90 | bend24 | bayside | 24 | 0.85 | 3.21 |
| outage90 | bend24 | blocks | 24 | 0.94 | 3.65 |
| outage90 | bend24 | boulevard | 24 | 0.64 | 2.77 |
| outage90 | calm24 | bayside | 24 | 0.6 | 3.29 |
| outage90 | calm24 | blocks | 24 | 0.94 | 3.65 |
| outage90 | calm24 | boulevard | 24 | 0.61 | 3.04 |
| outage90 | calm32 | bayside | 24 | 0.68 | 3.56 |
| outage90 | calm32 | blocks | 24 | 1.03 | 3.99 |
| outage90 | calm32 | boulevard | 24 | 0.67 | 3.17 |
| outage90 | keep16 | bayside | 24 | 0.52 | 2.5 |
| outage90 | keep16 | blocks | 24 | 0.74 | 3.33 |
| outage90 | keep16 | boulevard | 24 | 0.55 | 2.61 |
| outage90 | keep24 | bayside | 24 | 0.85 | 3.21 |
| outage90 | keep24 | blocks | 24 | 0.73 | 4.12 |
| outage90 | keep24 | boulevard | 24 | 0.64 | 2.77 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 10.29 | 36.91 | 0 | 0 |
| drift90 | bend24 | blocks | 24 | 10.88 | 30.42 | 0 | 0 |
| drift90 | bend24 | boulevard | 24 | 11.7 | 46.16 | 0 | 0 |
| drift90 | calm24 | bayside | 24 | 10.52 | 36.67 | 0 | 0 |
| drift90 | calm24 | blocks | 24 | 10.88 | 30.42 | 0 | 0 |
| drift90 | calm24 | boulevard | 24 | 11.7 | 42.68 | 0 | 0 |
| drift90 | calm32 | bayside | 24 | 9.96 | 34.59 | 0 | 0 |
| drift90 | calm32 | blocks | 24 | 11.68 | 29.83 | 0 | 0 |
| drift90 | calm32 | boulevard | 24 | 12.37 | 33.48 | 0 | 0 |
| drift90 | keep16 | bayside | 24 | 9.79 | 32.46 | 0 | 0 |
| drift90 | keep16 | blocks | 24 | 9.52 | 30.64 | 0 | 0 |
| drift90 | keep16 | boulevard | 24 | 10.41 | 39.12 | 0 | 0 |
| drift90 | keep24 | bayside | 24 | 10.29 | 37.43 | 0 | 0 |
| drift90 | keep24 | blocks | 24 | 10.51 | 29.37 | 0 | 0 |
| drift90 | keep24 | boulevard | 24 | 11.7 | 46.16 | 0 | 0 |
| outage90 | bend24 | bayside | 24 | 7.75 | 11.02 | 0 | 0 |
| outage90 | bend24 | blocks | 24 | 8.83 | 13.42 | 0 | 0 |
| outage90 | bend24 | boulevard | 24 | 8.85 | 10.55 | 0 | 0 |
| outage90 | calm24 | bayside | 24 | 7.68 | 11.73 | 0 | 0 |
| outage90 | calm24 | blocks | 24 | 8.83 | 13.42 | 0 | 0 |
| outage90 | calm24 | boulevard | 24 | 8.85 | 10.55 | 0 | 0 |
| outage90 | calm32 | bayside | 24 | 7.44 | 8.94 | 0 | 0 |
| outage90 | calm32 | blocks | 24 | 9.38 | 13.3 | 0 | 0 |
| outage90 | calm32 | boulevard | 24 | 9.38 | 11.6 | 0 | 0 |
| outage90 | keep16 | bayside | 24 | 7.19 | 11.22 | 0 | 0 |
| outage90 | keep16 | blocks | 24 | 8.05 | 12.98 | 0 | 0 |
| outage90 | keep16 | boulevard | 24 | 7.42 | 8.8 | 0 | 0 |
| outage90 | keep24 | bayside | 24 | 7.75 | 11.02 | 0 | 0 |
| outage90 | keep24 | blocks | 24 | 8.77 | 11.14 | 0 | 0 |
| outage90 | keep24 | boulevard | 24 | 8.85 | 10.55 | 0 | 0 |

## Plans, and plans made before reaching the leg's first point

| profile | variant | course | missions | plans (median) | behind (median) |
|---|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 5.0 | 3.0 |
| drift90 | bend24 | blocks | 24 | 6.0 | 4.0 |
| drift90 | bend24 | boulevard | 24 | 6.0 | 3.0 |
| drift90 | calm24 | bayside | 24 | 5.0 | 3.0 |
| drift90 | calm24 | blocks | 24 | 6.0 | 4.0 |
| drift90 | calm24 | boulevard | 24 | 6.0 | 3.0 |
| drift90 | calm32 | bayside | 24 | 5.0 | 3.0 |
| drift90 | calm32 | blocks | 24 | 6.0 | 4.0 |
| drift90 | calm32 | boulevard | 24 | 6.0 | 3.0 |
| drift90 | keep16 | bayside | 24 | 5.0 | 3.0 |
| drift90 | keep16 | blocks | 24 | 6.0 | 4.0 |
| drift90 | keep16 | boulevard | 24 | 6.0 | 3.0 |
| drift90 | keep24 | bayside | 24 | 5.0 | 3.0 |
| drift90 | keep24 | blocks | 24 | 6.0 | 4.0 |
| drift90 | keep24 | boulevard | 24 | 6.0 | 3.0 |
| outage90 | bend24 | bayside | 24 | 5.0 | 3.0 |
| outage90 | bend24 | blocks | 24 | 6.0 | 4.0 |
| outage90 | bend24 | boulevard | 24 | 5.5 | 3.0 |
| outage90 | calm24 | bayside | 24 | 5.0 | 3.0 |
| outage90 | calm24 | blocks | 24 | 6.0 | 4.0 |
| outage90 | calm24 | boulevard | 24 | 5.5 | 3.0 |
| outage90 | calm32 | bayside | 24 | 5.0 | 3.0 |
| outage90 | calm32 | blocks | 24 | 6.0 | 4.0 |
| outage90 | calm32 | boulevard | 24 | 5.5 | 3.0 |
| outage90 | keep16 | bayside | 24 | 5.0 | 3.0 |
| outage90 | keep16 | blocks | 24 | 6.0 | 4.0 |
| outage90 | keep16 | boulevard | 24 | 6.0 | 3.0 |
| outage90 | keep24 | bayside | 24 | 5.0 | 3.0 |
| outage90 | keep24 | blocks | 24 | 6.0 | 4.0 |
| outage90 | keep24 | boulevard | 24 | 5.5 | 3.0 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 5.2 | 8.09 |
| drift90 | bend24 | blocks | 24 | 5.46 | 8.43 |
| drift90 | bend24 | boulevard | 24 | 5.16 | 8.18 |
| drift90 | calm24 | bayside | 24 | 5.12 | 8.25 |
| drift90 | calm24 | blocks | 24 | 5.46 | 8.43 |
| drift90 | calm24 | boulevard | 24 | 5.08 | 7.97 |
| drift90 | calm32 | bayside | 24 | 5.35 | 8.71 |
| drift90 | calm32 | blocks | 24 | 5.6 | 8.56 |
| drift90 | calm32 | boulevard | 24 | 4.94 | 7.92 |
| drift90 | keep16 | bayside | 24 | 5.2 | 8.46 |
| drift90 | keep16 | blocks | 24 | 5.4 | 8.38 |
| drift90 | keep16 | boulevard | 24 | 5.24 | 8.13 |
| drift90 | keep24 | bayside | 24 | 5.22 | 8.09 |
| drift90 | keep24 | blocks | 24 | 5.39 | 8.57 |
| drift90 | keep24 | boulevard | 24 | 5.16 | 8.18 |
| outage90 | bend24 | bayside | 24 | 1.57 | 4.38 |
| outage90 | bend24 | blocks | 24 | 1.55 | 4.24 |
| outage90 | bend24 | boulevard | 24 | 1.48 | 3.97 |
| outage90 | calm24 | bayside | 24 | 1.58 | 4.47 |
| outage90 | calm24 | blocks | 24 | 1.55 | 4.24 |
| outage90 | calm24 | boulevard | 24 | 1.49 | 3.98 |
| outage90 | calm32 | bayside | 24 | 1.56 | 4.71 |
| outage90 | calm32 | blocks | 24 | 1.56 | 4.22 |
| outage90 | calm32 | boulevard | 24 | 1.46 | 3.97 |
| outage90 | keep16 | bayside | 24 | 1.52 | 4.46 |
| outage90 | keep16 | blocks | 24 | 1.64 | 4.27 |
| outage90 | keep16 | boulevard | 24 | 1.51 | 4.02 |
| outage90 | keep24 | bayside | 24 | 1.56 | 4.38 |
| outage90 | keep24 | blocks | 24 | 1.52 | 4.21 |
| outage90 | keep24 | boulevard | 24 | 1.48 | 3.97 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 6.46 | 8.79 |
| drift90 | bend24 | blocks | 24 | 6.5 | 8.53 |
| drift90 | bend24 | boulevard | 24 | 6.64 | 8.86 |
| drift90 | calm24 | bayside | 24 | 6.43 | 8.66 |
| drift90 | calm24 | blocks | 24 | 6.5 | 8.53 |
| drift90 | calm24 | boulevard | 24 | 6.64 | 8.85 |
| drift90 | calm32 | bayside | 24 | 6.47 | 8.62 |
| drift90 | calm32 | blocks | 24 | 6.43 | 8.43 |
| drift90 | calm32 | boulevard | 24 | 6.64 | 8.78 |
| drift90 | keep16 | bayside | 24 | 6.45 | 8.69 |
| drift90 | keep16 | blocks | 24 | 6.51 | 8.62 |
| drift90 | keep16 | boulevard | 24 | 6.64 | 8.87 |
| drift90 | keep24 | bayside | 24 | 6.46 | 8.79 |
| drift90 | keep24 | blocks | 24 | 6.5 | 8.37 |
| drift90 | keep24 | boulevard | 24 | 6.64 | 8.86 |
| outage90 | bend24 | bayside | 24 | 6.43 | 8.55 |
| outage90 | bend24 | blocks | 24 | 6.42 | 8.42 |
| outage90 | bend24 | boulevard | 24 | 6.57 | 8.62 |
| outage90 | calm24 | bayside | 24 | 6.42 | 8.55 |
| outage90 | calm24 | blocks | 24 | 6.42 | 8.42 |
| outage90 | calm24 | boulevard | 24 | 6.56 | 8.59 |
| outage90 | calm32 | bayside | 24 | 6.41 | 8.6 |
| outage90 | calm32 | blocks | 24 | 6.4 | 8.4 |
| outage90 | calm32 | boulevard | 24 | 6.57 | 8.6 |
| outage90 | keep16 | bayside | 24 | 6.42 | 8.6 |
| outage90 | keep16 | blocks | 24 | 6.44 | 8.46 |
| outage90 | keep16 | boulevard | 24 | 6.55 | 8.62 |
| outage90 | keep24 | bayside | 24 | 6.39 | 8.55 |
| outage90 | keep24 | blocks | 24 | 6.43 | 8.39 |
| outage90 | keep24 | boulevard | 24 | 6.57 | 8.62 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| drift90 | bend24 | bayside | 24 | 0.0301 |
| drift90 | bend24 | blocks | 24 | 0.041 |
| drift90 | bend24 | boulevard | 24 | 0.0274 |
| drift90 | calm24 | bayside | 24 | 0.0326 |
| drift90 | calm24 | blocks | 24 | 0.041 |
| drift90 | calm24 | boulevard | 24 | 0.0273 |
| drift90 | calm32 | bayside | 24 | 0.0333 |
| drift90 | calm32 | blocks | 24 | 0.0407 |
| drift90 | calm32 | boulevard | 24 | 0.0262 |
| drift90 | keep16 | bayside | 24 | 0.0338 |
| drift90 | keep16 | blocks | 24 | 0.0436 |
| drift90 | keep16 | boulevard | 24 | 0.0307 |
| drift90 | keep24 | bayside | 24 | 0.0301 |
| drift90 | keep24 | blocks | 24 | 0.0399 |
| drift90 | keep24 | boulevard | 24 | 0.0274 |
| outage90 | bend24 | bayside | 24 | 0.027 |
| outage90 | bend24 | blocks | 24 | 0.0379 |
| outage90 | bend24 | boulevard | 24 | 0.0234 |
| outage90 | calm24 | bayside | 24 | 0.0285 |
| outage90 | calm24 | blocks | 24 | 0.0379 |
| outage90 | calm24 | boulevard | 24 | 0.0234 |
| outage90 | calm32 | bayside | 24 | 0.029 |
| outage90 | calm32 | blocks | 24 | 0.0372 |
| outage90 | calm32 | boulevard | 24 | 0.0221 |
| outage90 | keep16 | bayside | 24 | 0.0307 |
| outage90 | keep16 | blocks | 24 | 0.0408 |
| outage90 | keep16 | boulevard | 24 | 0.027 |
| outage90 | keep24 | bayside | 24 | 0.0268 |
| outage90 | keep24 | blocks | 24 | 0.0368 |
| outage90 | keep24 | boulevard | 24 | 0.0234 |
