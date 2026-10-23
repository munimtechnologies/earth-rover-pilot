# How long should the wheels carry the position through a GPS outage? (simulated)

pace_k.py 0.1.0 (pace_j.py 0.1.0, pace_i.py 0.1.0, rover_pilot.py 0.15.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every profile is pace_i.py's measured Mini+ with GPS outages of 15 s (after 150 s of sky on average), 45 s (after 300 s), 45 s with the fixes wandering 8 m off over the 20 s before and after each outage (pace_j.py's wander45), or 90 s (after 600 s). Variants: the bridging pilot (v0.15.0 on a real rover) with the reckoner carrying the position up to 30 s (bridge+cf0.3), 60 s (bridge60+cf0.3) or 120 s (bridge120+cf0.3) after the last fix. Seeds 133-156. 864 of 864 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_j.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | 72/72 | 0.87 | 0.979 | 72 | 1.008 | 0.007 |
| outage15 | bridge60+cf0.3 | 72/72 | 0.87 | 0.979 | 72 | 1.008 | 0.007 |
| outage15 | bridge120+cf0.3 | 72/72 | 0.87 | 0.979 | 72 | 1.008 | 0.007 |
| outage45 | bridge+cf0.3 | 72/72 | 0.82 | 0.923 | 72 | 1.006 | 0.061 |
| outage45 | bridge60+cf0.3 | 72/72 | 0.862 | 0.97 | 72 | 1.008 | 0.016 |
| outage45 | bridge120+cf0.3 | 72/72 | 0.864 | 0.972 | 72 | 1.008 | 0.015 |
| wander45 | bridge+cf0.3 | 72/72 | 0.818 | 0.92 | 71 | 1.012 | 0.062 |
| wander45 | bridge60+cf0.3 | 72/72 | 0.858 | 0.965 | 72 | 1.014 | 0.017 |
| wander45 | bridge120+cf0.3 | 72/72 | 0.858 | 0.965 | 72 | 1.014 | 0.017 |
| outage90 | bridge+cf0.3 | 72/72 | 0.797 | 0.897 | 52 | 1.005 | 0.096 |
| outage90 | bridge60+cf0.3 | 72/72 | 0.826 | 0.929 | 70 | 1.007 | 0.057 |
| outage90 | bridge120+cf0.3 | 72/72 | 0.864 | 0.972 | 72 | 1.009 | 0.02 |

## Longer reach against shorter, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| outage15 | bridge60+cf0.3 | bridge+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0472 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0373 |
| wander45 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0443 |
| outage15 | bridge120+cf0.3 | bridge+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0472 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0683 |
| wander45 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0443 |
| outage15 | bridge120+cf0.3 | bridge60+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0316 |
| wander45 | bridge120+cf0.3 | bridge60+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| outage15 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage15 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| outage15 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 24 | 0 | -52.0 | -0.0338 | 0.0 |
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 24 | 0 | -67.0 | -0.0392 | 0.0 |
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -89.0 | -0.0472 | 0.0 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 21 | 0 | -42.0 | -0.0262 | 0.0 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 23 | 0 | -66.0 | -0.0373 | 0.0 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -66.0 | -0.0343 | 0.0 |
| wander45 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 24 | 0 | -57.0 | -0.0368 | 0.0 |
| wander45 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 24 | 0 | -56.0 | -0.0327 | 0.0 |
| wander45 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -84.0 | -0.0443 | 0.0 |
| outage15 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage15 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| outage15 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 24 | 0 | -52.0 | -0.0338 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 24 | 0 | -67.0 | -0.0392 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -89.0 | -0.0472 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 21 | 0 | -93.0 | -0.058 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 23 | 0 | -121.0 | -0.0683 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -128.0 | -0.0664 | 0.0 |
| wander45 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 24 | 0 | -57.0 | -0.0368 | 0.0 |
| wander45 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 24 | 0 | -56.0 | -0.0327 | 0.0 |
| wander45 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -84.0 | -0.0443 | 0.0 |
| outage15 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage15 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| outage15 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 1 | 0 | 0.0 | 0.0 | 1.0 |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 1 | 0 | 0.0 | 0.0 | 1.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 19 | 0 | -36.0 | -0.0232 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 22 | 0 | -39.0 | -0.0228 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 24 | 0 | -59.0 | -0.0316 | 0.0 |
| wander45 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| wander45 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 1 | 0 | 0.0 | 0.0 | 1.0 |
| wander45 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 1 | 0 | 0.0 | 0.0 | 1.0 |

## GPS outages

| profile | variant | course | missions | reports withheld | s stood still |
|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 78.5 | 7.8 |
| outage15 | bridge+cf0.3 | blocks | 24 | 85.0 | 5.6 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 95.0 | 6.2 |
| outage15 | bridge120+cf0.3 | bayside | 24 | 78.5 | 7.8 |
| outage15 | bridge120+cf0.3 | blocks | 24 | 85.0 | 5.6 |
| outage15 | bridge120+cf0.3 | boulevard | 24 | 95.0 | 6.2 |
| outage15 | bridge60+cf0.3 | bayside | 24 | 78.5 | 7.8 |
| outage15 | bridge60+cf0.3 | blocks | 24 | 85.0 | 5.6 |
| outage15 | bridge60+cf0.3 | boulevard | 24 | 95.0 | 6.2 |
| outage45 | bridge+cf0.3 | bayside | 24 | 112.5 | 100.7 |
| outage45 | bridge+cf0.3 | blocks | 24 | 124.0 | 104.0 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 136.0 | 121.0 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 111.5 | 3.0 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 113.0 | 24.2 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 136.0 | 20.1 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 111.5 | 3.0 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 113.0 | 26.6 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 136.0 | 20.1 |
| outage90 | bridge+cf0.3 | bayside | 24 | 112.5 | 168.9 |
| outage90 | bridge+cf0.3 | blocks | 24 | 112.5 | 168.9 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 112.5 | 168.9 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 90.0 | 2.0 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 112.5 | 3.0 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 112.5 | 10.0 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 90.0 | 108.9 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 112.5 | 97.3 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 112.5 | 101.6 |
| wander45 | bridge+cf0.3 | bayside | 24 | 113.0 | 95.7 |
| wander45 | bridge+cf0.3 | blocks | 24 | 124.5 | 110.6 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 136.0 | 121.0 |
| wander45 | bridge120+cf0.3 | bayside | 24 | 111.5 | 5.9 |
| wander45 | bridge120+cf0.3 | blocks | 24 | 113.0 | 15.1 |
| wander45 | bridge120+cf0.3 | boulevard | 24 | 136.0 | 15.2 |
| wander45 | bridge60+cf0.3 | bayside | 24 | 111.5 | 5.9 |
| wander45 | bridge60+cf0.3 | blocks | 24 | 113.0 | 15.1 |
| wander45 | bridge60+cf0.3 | boulevard | 24 | 136.0 | 15.2 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 0.0469 |
| outage15 | bridge+cf0.3 | blocks | 24 | 0.0612 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 0.0446 |
| outage15 | bridge120+cf0.3 | bayside | 24 | 0.0469 |
| outage15 | bridge120+cf0.3 | blocks | 24 | 0.0612 |
| outage15 | bridge120+cf0.3 | boulevard | 24 | 0.0446 |
| outage15 | bridge60+cf0.3 | bayside | 24 | 0.0469 |
| outage15 | bridge60+cf0.3 | blocks | 24 | 0.0612 |
| outage15 | bridge60+cf0.3 | boulevard | 24 | 0.0446 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.046 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0.0599 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0.0437 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 0.0474 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 0.0594 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 0.0427 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 0.0474 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 0.0594 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 0.0427 |
| outage90 | bridge+cf0.3 | bayside | 24 | 0.046 |
| outage90 | bridge+cf0.3 | blocks | 24 | 0.059 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 0.0437 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 0.047 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 0.0601 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 0.0428 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 0.0473 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 0.0599 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 0.0431 |
| wander45 | bridge+cf0.3 | bayside | 24 | 0.0476 |
| wander45 | bridge+cf0.3 | blocks | 24 | 0.0605 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 0.0452 |
| wander45 | bridge120+cf0.3 | bayside | 24 | 0.0483 |
| wander45 | bridge120+cf0.3 | blocks | 24 | 0.0599 |
| wander45 | bridge120+cf0.3 | boulevard | 24 | 0.0441 |
| wander45 | bridge60+cf0.3 | bayside | 24 | 0.0483 |
| wander45 | bridge60+cf0.3 | blocks | 24 | 0.0599 |
| wander45 | bridge60+cf0.3 | boulevard | 24 | 0.0441 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 6.57 | 10.07 |
| outage15 | bridge+cf0.3 | blocks | 24 | 6.45 | 9.62 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 6.62 | 10.13 |
| outage15 | bridge120+cf0.3 | bayside | 24 | 6.57 | 10.07 |
| outage15 | bridge120+cf0.3 | blocks | 24 | 6.45 | 9.62 |
| outage15 | bridge120+cf0.3 | boulevard | 24 | 6.61 | 10.04 |
| outage15 | bridge60+cf0.3 | bayside | 24 | 6.57 | 10.07 |
| outage15 | bridge60+cf0.3 | blocks | 24 | 6.45 | 9.62 |
| outage15 | bridge60+cf0.3 | boulevard | 24 | 6.61 | 10.04 |
| outage45 | bridge+cf0.3 | bayside | 24 | 6.57 | 9.12 |
| outage45 | bridge+cf0.3 | blocks | 24 | 6.42 | 9.11 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 6.62 | 9.26 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 6.46 | 9.2 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 6.36 | 9.18 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 6.57 | 9.56 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 6.46 | 9.2 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 6.36 | 9.18 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 6.57 | 9.56 |
| outage90 | bridge+cf0.3 | bayside | 24 | 6.56 | 8.81 |
| outage90 | bridge+cf0.3 | blocks | 24 | 6.42 | 8.48 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 6.56 | 8.73 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 6.39 | 8.54 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 6.34 | 8.52 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 6.47 | 8.83 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 6.51 | 8.69 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 6.38 | 8.6 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 6.51 | 8.86 |
| wander45 | bridge+cf0.3 | bayside | 24 | 6.73 | 11.29 |
| wander45 | bridge+cf0.3 | blocks | 24 | 6.59 | 11.42 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 6.74 | 11.87 |
| wander45 | bridge120+cf0.3 | bayside | 24 | 6.68 | 12.46 |
| wander45 | bridge120+cf0.3 | blocks | 24 | 6.59 | 12.42 |
| wander45 | bridge120+cf0.3 | boulevard | 24 | 6.79 | 13.3 |
| wander45 | bridge60+cf0.3 | bayside | 24 | 6.68 | 12.46 |
| wander45 | bridge60+cf0.3 | blocks | 24 | 6.61 | 12.42 |
| wander45 | bridge60+cf0.3 | boulevard | 24 | 6.79 | 13.3 |

## Dead reckoning

| profile | variant | course | missions | never trusted | first trusted s | s on wheels alone | abs scale error |
|---|---|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 0 | 77.0 | 114.7 | 0.0063 |
| outage15 | bridge+cf0.3 | blocks | 24 | 0 | 87.0 | 131.4 | 0.0086 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 0 | 90.0 | 148.6 | 0.0089 |
| outage15 | bridge120+cf0.3 | bayside | 24 | 0 | 77.0 | 114.7 | 0.0063 |
| outage15 | bridge120+cf0.3 | blocks | 24 | 0 | 87.0 | 131.4 | 0.0101 |
| outage15 | bridge120+cf0.3 | boulevard | 24 | 0 | 90.0 | 148.6 | 0.0089 |
| outage15 | bridge60+cf0.3 | bayside | 24 | 0 | 77.0 | 114.7 | 0.0063 |
| outage15 | bridge60+cf0.3 | blocks | 24 | 0 | 87.0 | 131.4 | 0.0101 |
| outage15 | bridge60+cf0.3 | boulevard | 24 | 0 | 90.0 | 148.6 | 0.0089 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0 | 100.0 | 115.0 | 0.0119 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0 | 91.0 | 129.6 | 0.0101 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0 | 94.0 | 140.6 | 0.0099 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 0 | 100.0 | 171.8 | 0.0134 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 0 | 91.0 | 214.2 | 0.0082 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 0 | 94.0 | 235.2 | 0.0083 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 0 | 100.0 | 171.8 | 0.0134 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 0 | 91.0 | 214.2 | 0.01 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 0 | 94.0 | 235.2 | 0.0083 |
| outage90 | bridge+cf0.3 | bayside | 24 | 0 | 86.0 | 65.3 | 0.0081 |
| outage90 | bridge+cf0.3 | blocks | 24 | 0 | 91.0 | 65.3 | 0.0082 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 0 | 92.0 | 65.8 | 0.0089 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 0 | 86.0 | 175.7 | 0.0107 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 0 | 91.0 | 221.1 | 0.0097 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 0 | 92.0 | 221.1 | 0.0077 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 0 | 86.0 | 113.3 | 0.0096 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 0 | 91.0 | 140.3 | 0.0089 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 0 | 92.0 | 140.3 | 0.0081 |
| wander45 | bridge+cf0.3 | bayside | 24 | 0 | 89.0 | 125.5 | 0.0093 |
| wander45 | bridge+cf0.3 | blocks | 24 | 0 | 93.0 | 127.1 | 0.0139 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 0 | 94.0 | 129.5 | 0.0084 |
| wander45 | bridge120+cf0.3 | bayside | 24 | 0 | 89.0 | 191.3 | 0.0147 |
| wander45 | bridge120+cf0.3 | blocks | 24 | 0 | 93.0 | 213.6 | 0.0119 |
| wander45 | bridge120+cf0.3 | boulevard | 24 | 0 | 94.0 | 214.2 | 0.0088 |
| wander45 | bridge60+cf0.3 | bayside | 24 | 0 | 89.0 | 191.3 | 0.0147 |
| wander45 | bridge60+cf0.3 | blocks | 24 | 0 | 93.0 | 213.6 | 0.011 |
| wander45 | bridge60+cf0.3 | boulevard | 24 | 0 | 94.0 | 214.2 | 0.0088 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 0.78 | 2.74 |
| outage15 | bridge+cf0.3 | blocks | 24 | 1.42 | 10.39 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 1.96 | 5.21 |
| outage15 | bridge120+cf0.3 | bayside | 24 | 0.78 | 2.74 |
| outage15 | bridge120+cf0.3 | blocks | 24 | 1.42 | 10.39 |
| outage15 | bridge120+cf0.3 | boulevard | 24 | 1.96 | 5.21 |
| outage15 | bridge60+cf0.3 | bayside | 24 | 0.78 | 2.74 |
| outage15 | bridge60+cf0.3 | blocks | 24 | 1.42 | 10.39 |
| outage15 | bridge60+cf0.3 | boulevard | 24 | 1.96 | 5.21 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.77 | 3.04 |
| outage45 | bridge+cf0.3 | blocks | 24 | 1.44 | 10.41 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 1.81 | 5.38 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 0.82 | 4.12 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 1.5 | 10.54 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 2.03 | 6.08 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 0.82 | 4.12 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 1.5 | 10.44 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 2.03 | 6.08 |
| outage90 | bridge+cf0.3 | bayside | 24 | 0.74 | 2.37 |
| outage90 | bridge+cf0.3 | blocks | 24 | 1.23 | 10.15 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 1.87 | 5.32 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 0.79 | 3.74 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 1.48 | 10.21 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 2.06 | 7.56 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 0.76 | 2.83 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 1.39 | 10.38 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 2.08 | 6.12 |
| wander45 | bridge+cf0.3 | bayside | 24 | 0.85 | 6.06 |
| wander45 | bridge+cf0.3 | blocks | 24 | 1.78 | 11.36 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 2.16 | 7.5 |
| wander45 | bridge120+cf0.3 | bayside | 24 | 0.92 | 6.76 |
| wander45 | bridge120+cf0.3 | blocks | 24 | 1.88 | 10.97 |
| wander45 | bridge120+cf0.3 | boulevard | 24 | 2.27 | 8.84 |
| wander45 | bridge60+cf0.3 | bayside | 24 | 0.92 | 6.76 |
| wander45 | bridge60+cf0.3 | blocks | 24 | 1.88 | 10.97 |
| wander45 | bridge60+cf0.3 | boulevard | 24 | 2.27 | 8.84 |
