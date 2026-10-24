# Is the compass-bias learner too slow for a drifting compass, or are its fits too noisy? (simulated)

pace_m.py 0.1.0 (pace_l.py 0.1.0, rover_pilot.py 0.16.1, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is pace_l.py's bridge120+cf0.3 (v0.16.x on a real rover) on pace_l.py's outage90 (90 s GPS outages, a steady compass error), drift90 (the compass error drifts, SD 10 deg, 120 s time constant) or lie90 (drift and wheel slip); only the compass-bias learner changes: shipped (gain 0.3, 10 m stretches), gain0.5, gain0.15, long20 (20 m stretches) and long20-g0.5. Seeds 181-204. 1080 of 1080 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_l.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | shipped | 72/72 | 0.866 | 0.974 | 72 | 1.009 | 0.016 |
| outage90 | gain0.5 | 72/72 | 0.863 | 0.971 | 72 | 1.012 | 0.016 |
| outage90 | gain0.15 | 72/72 | 0.866 | 0.974 | 72 | 1.009 | 0.016 |
| outage90 | long20 | 72/72 | 0.867 | 0.975 | 71 | 1.008 | 0.017 |
| outage90 | long20-g0.5 | 72/72 | 0.866 | 0.974 | 71 | 1.008 | 0.017 |
| drift90 | shipped | 72/72 | 0.863 | 0.971 | 71 | 1.015 | 0.016 |
| drift90 | gain0.5 | 72/72 | 0.861 | 0.969 | 71 | 1.016 | 0.015 |
| drift90 | gain0.15 | 72/72 | 0.863 | 0.971 | 71 | 1.013 | 0.016 |
| drift90 | long20 | 72/72 | 0.861 | 0.969 | 71 | 1.012 | 0.017 |
| drift90 | long20-g0.5 | 72/72 | 0.862 | 0.97 | 71 | 1.013 | 0.016 |
| lie90 | shipped | 72/72 | 0.862 | 0.97 | 71 | 1.014 | 0.016 |
| lie90 | gain0.5 | 72/72 | 0.86 | 0.968 | 71 | 1.016 | 0.014 |
| lie90 | gain0.15 | 72/72 | 0.863 | 0.971 | 71 | 1.014 | 0.016 |
| lie90 | long20 | 72/72 | 0.861 | 0.969 | 71 | 1.013 | 0.017 |
| lie90 | long20-g0.5 | 72/72 | 0.864 | 0.972 | 71 | 1.013 | 0.016 |

## Each learner against the shipped one, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| drift90 | gain0.5 | shipped | 0/3 | 2 | 0 | 0 | 0.0022 |
| lie90 | gain0.5 | shipped | 0/3 | 2 | 0 | 0 | 0.0022 |
| outage90 | gain0.5 | shipped | 0/3 | 3 | 0 | 0 | 0.0022 |
| drift90 | gain0.15 | shipped | 0/3 | 0 | 0 | 0 | 0.0 |
| lie90 | gain0.15 | shipped | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | gain0.15 | shipped | 2/3 | 0 | 0 | 0 | -0.0011 |
| drift90 | long20 | shipped | 1/3 | 0 | 0 | 0 | -0.0006 |
| lie90 | long20 | shipped | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | long20 | shipped | 2/3 | 0 | 0 | 0 | -0.0022 |
| drift90 | long20-g0.5 | shipped | 1/3 | 0 | 0 | 0 | -0.0012 |
| lie90 | long20-g0.5 | shipped | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | long20-g0.5 | shipped | 1/3 | 0 | 0 | 0 | -0.0017 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| drift90 | gain0.5 | shipped | bayside | 2 | 12 | 1.0 | 0.0007 | 0.0129 |
| drift90 | gain0.5 | shipped | blocks | 6 | 12 | 1.0 | 0.0006 | 0.2379 |
| drift90 | gain0.5 | shipped | boulevard | 2 | 16 | 4.0 | 0.0022 | 0.0013 |
| lie90 | gain0.5 | shipped | bayside | 4 | 10 | 0.0 | 0.0 | 0.1796 |
| lie90 | gain0.5 | shipped | blocks | 3 | 13 | 2.0 | 0.0012 | 0.0213 |
| lie90 | gain0.5 | shipped | boulevard | 1 | 16 | 4.0 | 0.0022 | 0.0003 |
| outage90 | gain0.5 | shipped | bayside | 2 | 15 | 2.0 | 0.0014 | 0.0023 |
| outage90 | gain0.5 | shipped | blocks | 2 | 13 | 3.0 | 0.0018 | 0.0074 |
| outage90 | gain0.5 | shipped | boulevard | 0 | 16 | 4.0 | 0.0022 | 0.0 |
| drift90 | gain0.15 | shipped | bayside | 10 | 4 | 0.0 | 0.0 | 0.1796 |
| drift90 | gain0.15 | shipped | blocks | 9 | 4 | 0.0 | 0.0 | 0.2668 |
| drift90 | gain0.15 | shipped | boulevard | 7 | 5 | 0.0 | 0.0 | 0.7744 |
| lie90 | gain0.15 | shipped | bayside | 9 | 5 | 0.0 | 0.0 | 0.424 |
| lie90 | gain0.15 | shipped | blocks | 9 | 7 | 0.0 | 0.0 | 0.8036 |
| lie90 | gain0.15 | shipped | boulevard | 9 | 4 | 0.0 | 0.0 | 0.2668 |
| outage90 | gain0.15 | shipped | bayside | 10 | 0 | 0.0 | 0.0 | 0.002 |
| outage90 | gain0.15 | shipped | blocks | 6 | 4 | 0.0 | 0.0 | 0.7539 |
| outage90 | gain0.15 | shipped | boulevard | 15 | 0 | -2.0 | -0.0011 | 0.0001 |
| drift90 | long20 | shipped | bayside | 8 | 5 | 0.0 | 0.0 | 0.5811 |
| drift90 | long20 | shipped | blocks | 12 | 3 | -1.0 | -0.0006 | 0.0352 |
| drift90 | long20 | shipped | boulevard | 7 | 6 | 0.0 | 0.0 | 1.0 |
| lie90 | long20 | shipped | bayside | 9 | 7 | 0.0 | 0.0 | 0.8036 |
| lie90 | long20 | shipped | blocks | 9 | 6 | 0.0 | 0.0 | 0.6072 |
| lie90 | long20 | shipped | boulevard | 9 | 4 | 0.0 | 0.0 | 0.2668 |
| outage90 | long20 | shipped | bayside | 10 | 1 | 0.0 | 0.0 | 0.0117 |
| outage90 | long20 | shipped | blocks | 6 | 3 | 0.0 | 0.0 | 0.5078 |
| outage90 | long20 | shipped | boulevard | 20 | 1 | -4.0 | -0.0022 | 0.0 |
| drift90 | long20-g0.5 | shipped | bayside | 7 | 6 | 0.0 | 0.0 | 1.0 |
| drift90 | long20-g0.5 | shipped | blocks | 15 | 3 | -2.0 | -0.0012 | 0.0075 |
| drift90 | long20-g0.5 | shipped | boulevard | 7 | 4 | 0.0 | 0.0 | 0.5488 |
| lie90 | long20-g0.5 | shipped | bayside | 8 | 6 | 0.0 | 0.0 | 0.7905 |
| lie90 | long20-g0.5 | shipped | blocks | 9 | 6 | 0.0 | 0.0 | 0.6072 |
| lie90 | long20-g0.5 | shipped | boulevard | 9 | 3 | 0.0 | 0.0 | 0.146 |
| outage90 | long20-g0.5 | shipped | bayside | 7 | 2 | 0.0 | 0.0 | 0.1797 |
| outage90 | long20-g0.5 | shipped | blocks | 5 | 5 | 0.0 | 0.0 | 1.0 |
| outage90 | long20-g0.5 | shipped | boulevard | 18 | 1 | -3.0 | -0.0017 | 0.0001 |

## What the drift costs each learner

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| shipped | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0042 |
| shipped | lie90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0055 |
| gain0.5 | drift90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0041 |
| gain0.5 | lie90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0041 |
| gain0.15 | drift90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0035 |
| gain0.15 | lie90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0055 |
| long20 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0034 |
| long20 | lie90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0042 |
| long20-g0.5 | drift90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0034 |
| long20-g0.5 | lie90 | outage90 | 0/3 | 2 | 0 | 0 | 0.0035 |

| variant | profile | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| shipped | drift90 | outage90 | bayside | 3 | 15 | 6.0 | 0.0042 | 0.0075 |
| shipped | drift90 | outage90 | blocks | 3 | 16 | 3.0 | 0.0018 | 0.0044 |
| shipped | drift90 | outage90 | boulevard | 5 | 17 | 4.0 | 0.0022 | 0.0169 |
| shipped | lie90 | outage90 | bayside | 3 | 16 | 8.0 | 0.0055 | 0.0044 |
| shipped | lie90 | outage90 | blocks | 5 | 13 | 2.0 | 0.0012 | 0.0963 |
| shipped | lie90 | outage90 | boulevard | 3 | 19 | 4.0 | 0.0022 | 0.0009 |
| gain0.5 | drift90 | outage90 | bayside | 2 | 16 | 6.0 | 0.0041 | 0.0013 |
| gain0.5 | drift90 | outage90 | blocks | 6 | 16 | 2.0 | 0.0012 | 0.0525 |
| gain0.5 | drift90 | outage90 | boulevard | 4 | 18 | 4.0 | 0.0022 | 0.0043 |
| gain0.5 | lie90 | outage90 | bayside | 4 | 16 | 6.0 | 0.0041 | 0.0118 |
| gain0.5 | lie90 | outage90 | blocks | 7 | 14 | 2.0 | 0.0012 | 0.1892 |
| gain0.5 | lie90 | outage90 | boulevard | 4 | 18 | 4.0 | 0.0022 | 0.0043 |
| gain0.15 | drift90 | outage90 | bayside | 1 | 18 | 5.0 | 0.0035 | 0.0001 |
| gain0.15 | drift90 | outage90 | blocks | 7 | 12 | 1.0 | 0.0006 | 0.3593 |
| gain0.15 | drift90 | outage90 | boulevard | 2 | 19 | 6.0 | 0.0034 | 0.0002 |
| gain0.15 | lie90 | outage90 | bayside | 3 | 18 | 8.0 | 0.0055 | 0.0015 |
| gain0.15 | lie90 | outage90 | blocks | 5 | 13 | 4.0 | 0.0025 | 0.0963 |
| gain0.15 | lie90 | outage90 | boulevard | 1 | 20 | 6.0 | 0.0034 | 0.0 |
| long20 | drift90 | outage90 | bayside | 0 | 16 | 4.0 | 0.0028 | 0.0 |
| long20 | drift90 | outage90 | blocks | 5 | 15 | 4.0 | 0.0025 | 0.0414 |
| long20 | drift90 | outage90 | boulevard | 0 | 22 | 6.0 | 0.0034 | 0.0 |
| long20 | lie90 | outage90 | bayside | 1 | 17 | 6.0 | 0.0042 | 0.0001 |
| long20 | lie90 | outage90 | blocks | 5 | 16 | 5.0 | 0.0031 | 0.0266 |
| long20 | lie90 | outage90 | boulevard | 0 | 21 | 7.0 | 0.0039 | 0.0 |
| long20-g0.5 | drift90 | outage90 | bayside | 0 | 12 | 2.0 | 0.0014 | 0.0005 |
| long20-g0.5 | drift90 | outage90 | blocks | 7 | 14 | 2.0 | 0.0012 | 0.1892 |
| long20-g0.5 | drift90 | outage90 | boulevard | 0 | 22 | 6.0 | 0.0034 | 0.0 |
| long20-g0.5 | lie90 | outage90 | bayside | 3 | 14 | 5.0 | 0.0035 | 0.0127 |
| long20-g0.5 | lie90 | outage90 | blocks | 5 | 12 | 1.0 | 0.0006 | 0.1435 |
| long20-g0.5 | lie90 | outage90 | boulevard | 0 | 21 | 6.0 | 0.0034 | 0.0 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| drift90 | gain0.15 | bayside | 24 | 6.37 | 9.13 |
| drift90 | gain0.15 | blocks | 24 | 6.62 | 9.43 |
| drift90 | gain0.15 | boulevard | 24 | 5.88 | 9.23 |
| drift90 | gain0.5 | bayside | 24 | 5.84 | 9.38 |
| drift90 | gain0.5 | blocks | 24 | 6.11 | 9.6 |
| drift90 | gain0.5 | boulevard | 24 | 5.59 | 9.11 |
| drift90 | long20 | bayside | 24 | 6.73 | 11.0 |
| drift90 | long20 | blocks | 24 | 6.92 | 10.6 |
| drift90 | long20 | boulevard | 24 | 6.34 | 9.84 |
| drift90 | long20-g0.5 | bayside | 24 | 6.64 | 10.75 |
| drift90 | long20-g0.5 | blocks | 24 | 6.46 | 10.55 |
| drift90 | long20-g0.5 | boulevard | 24 | 6.13 | 9.86 |
| drift90 | shipped | bayside | 24 | 5.44 | 9.08 |
| drift90 | shipped | blocks | 24 | 5.95 | 9.02 |
| drift90 | shipped | boulevard | 24 | 5.55 | 8.89 |
| lie90 | gain0.15 | bayside | 24 | 6.2 | 9.09 |
| lie90 | gain0.15 | blocks | 24 | 6.59 | 9.47 |
| lie90 | gain0.15 | boulevard | 24 | 5.88 | 9.43 |
| lie90 | gain0.5 | bayside | 24 | 5.95 | 9.54 |
| lie90 | gain0.5 | blocks | 24 | 6.17 | 9.57 |
| lie90 | gain0.5 | boulevard | 24 | 5.62 | 9.04 |
| lie90 | long20 | bayside | 24 | 6.92 | 11.31 |
| lie90 | long20 | blocks | 24 | 6.95 | 11.0 |
| lie90 | long20 | boulevard | 24 | 6.6 | 9.82 |
| lie90 | long20-g0.5 | bayside | 24 | 6.6 | 10.68 |
| lie90 | long20-g0.5 | blocks | 24 | 6.36 | 10.87 |
| lie90 | long20-g0.5 | boulevard | 24 | 6.37 | 9.91 |
| lie90 | shipped | bayside | 24 | 5.89 | 8.99 |
| lie90 | shipped | blocks | 24 | 5.79 | 9.3 |
| lie90 | shipped | boulevard | 24 | 5.6 | 8.66 |
| outage90 | gain0.15 | bayside | 24 | 2.36 | 5.03 |
| outage90 | gain0.15 | blocks | 24 | 2.31 | 5.15 |
| outage90 | gain0.15 | boulevard | 24 | 2.09 | 4.79 |
| outage90 | gain0.5 | bayside | 24 | 4.08 | 6.85 |
| outage90 | gain0.5 | blocks | 24 | 4.0 | 6.67 |
| outage90 | gain0.5 | boulevard | 24 | 3.75 | 6.54 |
| outage90 | long20 | bayside | 24 | 1.71 | 5.6 |
| outage90 | long20 | blocks | 24 | 1.73 | 5.17 |
| outage90 | long20 | boulevard | 24 | 1.63 | 4.76 |
| outage90 | long20-g0.5 | bayside | 24 | 1.94 | 5.69 |
| outage90 | long20-g0.5 | blocks | 24 | 2.1 | 5.34 |
| outage90 | long20-g0.5 | boulevard | 24 | 1.98 | 4.99 |
| outage90 | shipped | bayside | 24 | 2.94 | 5.62 |
| outage90 | shipped | blocks | 24 | 3.08 | 5.73 |
| outage90 | shipped | boulevard | 24 | 2.88 | 5.35 |

## Error of each measurement the learner used

| profile | variant | course | missions | measurements | median abs deg | rms deg |
|---|---|---|---|---|---|---|
| drift90 | gain0.15 | bayside | 24 | 48.5 | 6.08 | 9.66 |
| drift90 | gain0.15 | blocks | 24 | 49.5 | 6.73 | 9.98 |
| drift90 | gain0.15 | boulevard | 24 | 67.0 | 6.55 | 9.62 |
| drift90 | gain0.5 | bayside | 24 | 45.5 | 6.57 | 9.96 |
| drift90 | gain0.5 | blocks | 24 | 48.0 | 6.28 | 9.75 |
| drift90 | gain0.5 | boulevard | 24 | 65.0 | 6.73 | 9.57 |
| drift90 | long20 | bayside | 24 | 15.5 | 3.79 | 5.56 |
| drift90 | long20 | blocks | 24 | 15.5 | 4.29 | 5.56 |
| drift90 | long20 | boulevard | 24 | 26.5 | 3.9 | 5.5 |
| drift90 | long20-g0.5 | bayside | 24 | 16.0 | 3.46 | 5.4 |
| drift90 | long20-g0.5 | blocks | 24 | 15.5 | 4.06 | 5.58 |
| drift90 | long20-g0.5 | boulevard | 24 | 25.0 | 3.92 | 5.29 |
| drift90 | shipped | bayside | 24 | 47.5 | 6.55 | 9.71 |
| drift90 | shipped | blocks | 24 | 47.0 | 6.39 | 9.79 |
| drift90 | shipped | boulevard | 24 | 66.0 | 6.25 | 9.71 |
| lie90 | gain0.15 | bayside | 24 | 48.5 | 6.04 | 9.54 |
| lie90 | gain0.15 | blocks | 24 | 50.0 | 6.41 | 10.19 |
| lie90 | gain0.15 | boulevard | 24 | 67.5 | 6.56 | 9.54 |
| lie90 | gain0.5 | bayside | 24 | 46.5 | 6.09 | 9.8 |
| lie90 | gain0.5 | blocks | 24 | 48.5 | 6.56 | 10.05 |
| lie90 | gain0.5 | boulevard | 24 | 66.0 | 6.72 | 9.81 |
| lie90 | long20 | bayside | 24 | 15.0 | 3.91 | 5.65 |
| lie90 | long20 | blocks | 24 | 15.0 | 4.17 | 5.71 |
| lie90 | long20 | boulevard | 24 | 26.5 | 4.01 | 5.53 |
| lie90 | long20-g0.5 | bayside | 24 | 16.0 | 4.04 | 5.53 |
| lie90 | long20-g0.5 | blocks | 24 | 14.5 | 4.13 | 5.52 |
| lie90 | long20-g0.5 | boulevard | 24 | 25.0 | 4.0 | 5.44 |
| lie90 | shipped | bayside | 24 | 47.5 | 6.65 | 9.54 |
| lie90 | shipped | blocks | 24 | 49.5 | 6.52 | 9.94 |
| lie90 | shipped | boulevard | 24 | 64.0 | 6.46 | 9.66 |
| outage90 | gain0.15 | bayside | 24 | 53.0 | 6.22 | 9.28 |
| outage90 | gain0.15 | blocks | 24 | 51.0 | 6.03 | 9.1 |
| outage90 | gain0.15 | boulevard | 24 | 73.0 | 6.01 | 9.0 |
| outage90 | gain0.5 | bayside | 24 | 52.5 | 6.14 | 9.5 |
| outage90 | gain0.5 | blocks | 24 | 51.0 | 5.95 | 9.36 |
| outage90 | gain0.5 | boulevard | 24 | 69.0 | 5.92 | 9.2 |
| outage90 | long20 | bayside | 24 | 18.5 | 2.65 | 4.07 |
| outage90 | long20 | blocks | 24 | 18.5 | 2.6 | 4.04 |
| outage90 | long20 | boulevard | 24 | 31.5 | 2.73 | 4.0 |
| outage90 | long20-g0.5 | bayside | 24 | 18.0 | 2.59 | 3.67 |
| outage90 | long20-g0.5 | blocks | 24 | 19.0 | 2.62 | 3.99 |
| outage90 | long20-g0.5 | boulevard | 24 | 30.5 | 2.57 | 3.92 |
| outage90 | shipped | bayside | 24 | 52.0 | 6.42 | 9.2 |
| outage90 | shipped | blocks | 24 | 51.0 | 6.09 | 9.12 |
| outage90 | shipped | boulevard | 24 | 74.0 | 5.91 | 9.27 |

## The learner

| profile | variant | course | missions | calibrations | stretches broken off | abs bias error at the end |
|---|---|---|---|---|---|---|
| drift90 | gain0.15 | bayside | 24 | 48.5 | 104.5 | 6.03 |
| drift90 | gain0.15 | blocks | 24 | 49.5 | 137.0 | 4.58 |
| drift90 | gain0.15 | boulevard | 24 | 67.0 | 106.0 | 3.44 |
| drift90 | gain0.5 | bayside | 24 | 45.5 | 120.0 | 7.96 |
| drift90 | gain0.5 | blocks | 24 | 48.0 | 152.0 | 6.44 |
| drift90 | gain0.5 | boulevard | 24 | 65.0 | 123.5 | 5.42 |
| drift90 | long20 | bayside | 24 | 15.5 | 101.0 | 5.0 |
| drift90 | long20 | blocks | 24 | 15.5 | 130.0 | 5.81 |
| drift90 | long20 | boulevard | 24 | 26.5 | 99.0 | 4.11 |
| drift90 | long20-g0.5 | bayside | 24 | 16.0 | 103.0 | 7.45 |
| drift90 | long20-g0.5 | blocks | 24 | 15.5 | 135.5 | 5.33 |
| drift90 | long20-g0.5 | boulevard | 24 | 25.0 | 106.0 | 4.22 |
| drift90 | shipped | bayside | 24 | 47.5 | 108.5 | 5.53 |
| drift90 | shipped | blocks | 24 | 47.0 | 143.5 | 4.96 |
| drift90 | shipped | boulevard | 24 | 66.0 | 112.0 | 4.36 |
| lie90 | gain0.15 | bayside | 24 | 48.5 | 103.0 | 4.57 |
| lie90 | gain0.15 | blocks | 24 | 50.0 | 137.0 | 4.95 |
| lie90 | gain0.15 | boulevard | 24 | 67.5 | 104.0 | 3.82 |
| lie90 | gain0.5 | bayside | 24 | 46.5 | 119.0 | 5.23 |
| lie90 | gain0.5 | blocks | 24 | 48.5 | 150.5 | 6.47 |
| lie90 | gain0.5 | boulevard | 24 | 66.0 | 124.5 | 5.51 |
| lie90 | long20 | bayside | 24 | 15.0 | 101.0 | 5.16 |
| lie90 | long20 | blocks | 24 | 15.0 | 134.5 | 5.64 |
| lie90 | long20 | boulevard | 24 | 26.5 | 99.5 | 4.54 |
| lie90 | long20-g0.5 | bayside | 24 | 16.0 | 103.0 | 6.7 |
| lie90 | long20-g0.5 | blocks | 24 | 14.5 | 136.0 | 4.61 |
| lie90 | long20-g0.5 | boulevard | 24 | 25.0 | 106.5 | 3.38 |
| lie90 | shipped | bayside | 24 | 47.5 | 109.5 | 5.04 |
| lie90 | shipped | blocks | 24 | 49.5 | 144.5 | 4.97 |
| lie90 | shipped | boulevard | 24 | 64.0 | 114.0 | 4.81 |
| outage90 | gain0.15 | bayside | 24 | 53.0 | 91.5 | 1.58 |
| outage90 | gain0.15 | blocks | 24 | 51.0 | 125.0 | 2.42 |
| outage90 | gain0.15 | boulevard | 24 | 73.0 | 89.5 | 1.46 |
| outage90 | gain0.5 | bayside | 24 | 52.5 | 106.5 | 2.27 |
| outage90 | gain0.5 | blocks | 24 | 51.0 | 139.0 | 4.59 |
| outage90 | gain0.5 | boulevard | 24 | 69.0 | 114.0 | 5.26 |
| outage90 | long20 | bayside | 24 | 18.5 | 89.0 | 0.94 |
| outage90 | long20 | blocks | 24 | 18.5 | 118.0 | 1.25 |
| outage90 | long20 | boulevard | 24 | 31.5 | 84.0 | 1.35 |
| outage90 | long20-g0.5 | bayside | 24 | 18.0 | 93.5 | 2.18 |
| outage90 | long20-g0.5 | blocks | 24 | 19.0 | 119.0 | 0.94 |
| outage90 | long20-g0.5 | boulevard | 24 | 30.5 | 84.5 | 1.46 |
| outage90 | shipped | bayside | 24 | 52.0 | 97.5 | 2.4 |
| outage90 | shipped | blocks | 24 | 51.0 | 130.5 | 3.0 |
| outage90 | shipped | boulevard | 24 | 74.0 | 98.0 | 3.41 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | gain0.15 | bayside | 24 | 6.44 | 8.82 |
| drift90 | gain0.15 | blocks | 24 | 6.29 | 8.84 |
| drift90 | gain0.15 | boulevard | 24 | 6.53 | 8.96 |
| drift90 | gain0.5 | bayside | 24 | 6.4 | 8.91 |
| drift90 | gain0.5 | blocks | 24 | 6.29 | 9.0 |
| drift90 | gain0.5 | boulevard | 24 | 6.48 | 8.93 |
| drift90 | long20 | bayside | 24 | 6.43 | 8.79 |
| drift90 | long20 | blocks | 24 | 6.33 | 8.63 |
| drift90 | long20 | boulevard | 24 | 6.5 | 8.93 |
| drift90 | long20-g0.5 | bayside | 24 | 6.42 | 9.02 |
| drift90 | long20-g0.5 | blocks | 24 | 6.29 | 8.74 |
| drift90 | long20-g0.5 | boulevard | 24 | 6.5 | 8.95 |
| drift90 | shipped | bayside | 24 | 6.44 | 9.11 |
| drift90 | shipped | blocks | 24 | 6.29 | 8.83 |
| drift90 | shipped | boulevard | 24 | 6.47 | 8.91 |
| lie90 | gain0.15 | bayside | 24 | 6.46 | 9.09 |
| lie90 | gain0.15 | blocks | 24 | 6.32 | 8.75 |
| lie90 | gain0.15 | boulevard | 24 | 6.54 | 9.0 |
| lie90 | gain0.5 | bayside | 24 | 6.46 | 9.26 |
| lie90 | gain0.5 | blocks | 24 | 6.33 | 9.0 |
| lie90 | gain0.5 | boulevard | 24 | 6.51 | 9.02 |
| lie90 | long20 | bayside | 24 | 6.47 | 8.9 |
| lie90 | long20 | blocks | 24 | 6.37 | 8.71 |
| lie90 | long20 | boulevard | 24 | 6.5 | 8.94 |
| lie90 | long20-g0.5 | bayside | 24 | 6.47 | 9.11 |
| lie90 | long20-g0.5 | blocks | 24 | 6.3 | 8.79 |
| lie90 | long20-g0.5 | boulevard | 24 | 6.53 | 8.97 |
| lie90 | shipped | bayside | 24 | 6.47 | 9.23 |
| lie90 | shipped | blocks | 24 | 6.34 | 9.11 |
| lie90 | shipped | boulevard | 24 | 6.5 | 8.96 |
| outage90 | gain0.15 | bayside | 24 | 6.36 | 8.37 |
| outage90 | gain0.15 | blocks | 24 | 6.29 | 8.39 |
| outage90 | gain0.15 | boulevard | 24 | 6.45 | 8.73 |
| outage90 | gain0.5 | bayside | 24 | 6.4 | 8.54 |
| outage90 | gain0.5 | blocks | 24 | 6.34 | 8.56 |
| outage90 | gain0.5 | boulevard | 24 | 6.46 | 8.84 |
| outage90 | long20 | bayside | 24 | 6.36 | 8.32 |
| outage90 | long20 | blocks | 24 | 6.25 | 8.38 |
| outage90 | long20 | boulevard | 24 | 6.45 | 8.57 |
| outage90 | long20-g0.5 | bayside | 24 | 6.36 | 8.34 |
| outage90 | long20-g0.5 | blocks | 24 | 6.28 | 8.37 |
| outage90 | long20-g0.5 | boulevard | 24 | 6.46 | 8.63 |
| outage90 | shipped | bayside | 24 | 6.38 | 8.37 |
| outage90 | shipped | blocks | 24 | 6.29 | 8.41 |
| outage90 | shipped | boulevard | 24 | 6.44 | 8.79 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | gain0.15 | bayside | 24 | 1.17 | 5.16 |
| drift90 | gain0.15 | blocks | 24 | 2.05 | 10.92 |
| drift90 | gain0.15 | boulevard | 24 | 2.38 | 7.16 |
| drift90 | gain0.5 | bayside | 24 | 1.13 | 4.33 |
| drift90 | gain0.5 | blocks | 24 | 1.99 | 11.25 |
| drift90 | gain0.5 | boulevard | 24 | 2.33 | 7.67 |
| drift90 | long20 | bayside | 24 | 1.33 | 6.12 |
| drift90 | long20 | blocks | 24 | 2.1 | 10.89 |
| drift90 | long20 | boulevard | 24 | 2.33 | 7.66 |
| drift90 | long20-g0.5 | bayside | 24 | 1.35 | 5.92 |
| drift90 | long20-g0.5 | blocks | 24 | 2.01 | 11.11 |
| drift90 | long20-g0.5 | boulevard | 24 | 2.33 | 7.6 |
| drift90 | shipped | bayside | 24 | 1.1 | 5.2 |
| drift90 | shipped | blocks | 24 | 2.0 | 10.98 |
| drift90 | shipped | boulevard | 24 | 2.64 | 7.07 |
| lie90 | gain0.15 | bayside | 24 | 1.15 | 5.54 |
| lie90 | gain0.15 | blocks | 24 | 2.07 | 11.07 |
| lie90 | gain0.15 | boulevard | 24 | 2.43 | 7.09 |
| lie90 | gain0.5 | bayside | 24 | 1.11 | 4.67 |
| lie90 | gain0.5 | blocks | 24 | 2.02 | 11.04 |
| lie90 | gain0.5 | boulevard | 24 | 2.32 | 7.38 |
| lie90 | long20 | bayside | 24 | 1.33 | 6.03 |
| lie90 | long20 | blocks | 24 | 2.09 | 11.11 |
| lie90 | long20 | boulevard | 24 | 2.28 | 7.44 |
| lie90 | long20-g0.5 | bayside | 24 | 1.26 | 5.83 |
| lie90 | long20-g0.5 | blocks | 24 | 2.08 | 10.94 |
| lie90 | long20-g0.5 | boulevard | 24 | 2.27 | 7.6 |
| lie90 | shipped | bayside | 24 | 1.11 | 5.56 |
| lie90 | shipped | blocks | 24 | 2.0 | 10.89 |
| lie90 | shipped | boulevard | 24 | 2.46 | 6.84 |
| outage90 | gain0.15 | bayside | 24 | 0.7 | 2.74 |
| outage90 | gain0.15 | blocks | 24 | 1.39 | 10.25 |
| outage90 | gain0.15 | boulevard | 24 | 1.9 | 5.47 |
| outage90 | gain0.5 | bayside | 24 | 0.94 | 4.41 |
| outage90 | gain0.5 | blocks | 24 | 1.64 | 10.77 |
| outage90 | gain0.5 | boulevard | 24 | 2.02 | 6.33 |
| outage90 | long20 | bayside | 24 | 0.65 | 3.9 |
| outage90 | long20 | blocks | 24 | 1.28 | 10.79 |
| outage90 | long20 | boulevard | 24 | 2.02 | 5.82 |
| outage90 | long20-g0.5 | bayside | 24 | 0.7 | 3.92 |
| outage90 | long20-g0.5 | blocks | 24 | 1.35 | 10.73 |
| outage90 | long20-g0.5 | boulevard | 24 | 2.02 | 5.81 |
| outage90 | shipped | bayside | 24 | 0.78 | 3.57 |
| outage90 | shipped | blocks | 24 | 1.52 | 10.55 |
| outage90 | shipped | boulevard | 24 | 2.09 | 5.71 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| drift90 | gain0.15 | bayside | 24 | 0.0492 |
| drift90 | gain0.15 | blocks | 24 | 0.0611 |
| drift90 | gain0.15 | boulevard | 24 | 0.0451 |
| drift90 | gain0.5 | bayside | 24 | 0.0514 |
| drift90 | gain0.5 | blocks | 24 | 0.0633 |
| drift90 | gain0.5 | boulevard | 24 | 0.0486 |
| drift90 | long20 | bayside | 24 | 0.0476 |
| drift90 | long20 | blocks | 24 | 0.0606 |
| drift90 | long20 | boulevard | 24 | 0.0448 |
| drift90 | long20-g0.5 | bayside | 24 | 0.0484 |
| drift90 | long20-g0.5 | blocks | 24 | 0.0608 |
| drift90 | long20-g0.5 | boulevard | 24 | 0.0452 |
| drift90 | shipped | bayside | 24 | 0.0495 |
| drift90 | shipped | blocks | 24 | 0.0623 |
| drift90 | shipped | boulevard | 24 | 0.0465 |
| lie90 | gain0.15 | bayside | 24 | 0.0487 |
| lie90 | gain0.15 | blocks | 24 | 0.0617 |
| lie90 | gain0.15 | boulevard | 24 | 0.045 |
| lie90 | gain0.5 | bayside | 24 | 0.0514 |
| lie90 | gain0.5 | blocks | 24 | 0.0636 |
| lie90 | gain0.5 | boulevard | 24 | 0.0487 |
| lie90 | long20 | bayside | 24 | 0.0476 |
| lie90 | long20 | blocks | 24 | 0.0607 |
| lie90 | long20 | boulevard | 24 | 0.0449 |
| lie90 | long20-g0.5 | bayside | 24 | 0.0484 |
| lie90 | long20-g0.5 | blocks | 24 | 0.0607 |
| lie90 | long20-g0.5 | boulevard | 24 | 0.0451 |
| lie90 | shipped | bayside | 24 | 0.0497 |
| lie90 | shipped | blocks | 24 | 0.0619 |
| lie90 | shipped | boulevard | 24 | 0.0464 |
| outage90 | gain0.15 | bayside | 24 | 0.0458 |
| outage90 | gain0.15 | blocks | 24 | 0.059 |
| outage90 | gain0.15 | boulevard | 24 | 0.0421 |
| outage90 | gain0.5 | bayside | 24 | 0.0484 |
| outage90 | gain0.5 | blocks | 24 | 0.0611 |
| outage90 | gain0.5 | boulevard | 24 | 0.0454 |
| outage90 | long20 | bayside | 24 | 0.0452 |
| outage90 | long20 | blocks | 24 | 0.0582 |
| outage90 | long20 | boulevard | 24 | 0.0415 |
| outage90 | long20-g0.5 | bayside | 24 | 0.0453 |
| outage90 | long20-g0.5 | blocks | 24 | 0.0586 |
| outage90 | long20-g0.5 | boulevard | 24 | 0.0417 |
| outage90 | shipped | bayside | 24 | 0.0469 |
| outage90 | shipped | blocks | 24 | 0.0599 |
| outage90 | shipped | boulevard | 24 | 0.0433 |
