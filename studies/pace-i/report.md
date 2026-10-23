# Should bridging GPS gaps be the default? (simulated)

pace_i.py 0.1.0 (pace_h.py 0.1.0, rover_pilot.py 0.13.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every profile is pace_h.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, GPS every 2 s and 1.5 s late, 3 deg of compass noise, a -25 deg compass error to learn, wheels reporting RPM), alone or with GPS outages of 15 s (after 150 s of sky on average) or 45 s (after 300 s). Variants: cf0.3 (v0.14.0 on a real rover), bridge+cf0.3 (dead reckoning only while the GPS has no fresh fix), bridge-r+cf0.3 (the same, the GPS filter starting again from the first fix after a gap), dr+cf0.3 (v0.13.0 on a real rover). Seeds 85-108. 864 of 864 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_h.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| measured | cf0.3 | 72/72 | 0.877 | 0.986 | 72 | 1.005 | 0.002 |
| measured | bridge+cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.006 | 0.001 |
| measured | bridge-r+cf0.3 | 72/72 | 0.877 | 0.987 | 72 | 1.006 | 0.001 |
| measured | dr+cf0.3 | 72/72 | 0.825 | 0.928 | 72 | 1.025 | 0.001 |
| outage15 | cf0.3 | 72/72 | 0.809 | 0.91 | 72 | 1.005 | 0.08 |
| outage15 | bridge+cf0.3 | 72/72 | 0.87 | 0.978 | 72 | 1.008 | 0.006 |
| outage15 | bridge-r+cf0.3 | 72/72 | 0.869 | 0.978 | 72 | 1.009 | 0.007 |
| outage15 | dr+cf0.3 | 72/72 | 0.827 | 0.93 | 72 | 1.025 | 0.006 |
| outage45 | cf0.3 | 72/72 | 0.768 | 0.864 | 44 | 1.005 | 0.13 |
| outage45 | bridge+cf0.3 | 72/72 | 0.829 | 0.932 | 69 | 1.007 | 0.062 |
| outage45 | bridge-r+cf0.3 | 72/72 | 0.828 | 0.932 | 70 | 1.007 | 0.061 |
| outage45 | dr+cf0.3 | 72/72 | 0.793 | 0.892 | 64 | 1.025 | 0.061 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| measured | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | 0.0 |
| outage15 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0723 |
| outage45 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0724 |
| measured | bridge-r+cf0.3 | cf0.3 | 2/3 | 0 | 0 | 0 | 0.0 |
| outage15 | bridge-r+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0757 |
| outage45 | bridge-r+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0714 |
| measured | bridge-r+cf0.3 | bridge+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| outage15 | bridge-r+cf0.3 | bridge+cf0.3 | 1/3 | 2 | 0 | 0 | 0.0014 |
| outage45 | bridge-r+cf0.3 | bridge+cf0.3 | 1/3 | 2 | 0 | 0 | -0.0035 |
| measured | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0695 |
| outage15 | dr+cf0.3 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0574 |
| outage45 | dr+cf0.3 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0615 |
| measured | bridge-r+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0654 |
| outage15 | bridge-r+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0558 |
| outage45 | bridge-r+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0533 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| measured | bridge+cf0.3 | cf0.3 | bayside | 10 | 0 | 0.0 | 0.0 | 0.002 |
| measured | bridge+cf0.3 | cf0.3 | blocks | 10 | 1 | 0.0 | 0.0 | 0.0117 |
| measured | bridge+cf0.3 | cf0.3 | boulevard | 11 | 0 | 0.0 | 0.0 | 0.001 |
| outage15 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -98.0 | -0.0632 | 0.0 |
| outage15 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -126.0 | -0.0723 | 0.0 |
| outage15 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -128.0 | -0.0671 | 0.0 |
| outage45 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -115.0 | -0.0698 | 0.0 |
| outage45 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -124.0 | -0.0681 | 0.0 |
| outage45 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -146.0 | -0.0724 | 0.0 |
| measured | bridge-r+cf0.3 | cf0.3 | bayside | 7 | 1 | 0.0 | 0.0 | 0.0703 |
| measured | bridge-r+cf0.3 | cf0.3 | blocks | 10 | 1 | 0.0 | 0.0 | 0.0117 |
| measured | bridge-r+cf0.3 | cf0.3 | boulevard | 7 | 0 | 0.0 | 0.0 | 0.0156 |
| outage15 | bridge-r+cf0.3 | cf0.3 | bayside | 24 | 0 | -91.0 | -0.0587 | 0.0 |
| outage15 | bridge-r+cf0.3 | cf0.3 | blocks | 24 | 0 | -132.0 | -0.0757 | 0.0 |
| outage15 | bridge-r+cf0.3 | cf0.3 | boulevard | 24 | 0 | -127.0 | -0.0666 | 0.0 |
| outage45 | bridge-r+cf0.3 | cf0.3 | bayside | 24 | 0 | -108.0 | -0.0656 | 0.0 |
| outage45 | bridge-r+cf0.3 | cf0.3 | blocks | 24 | 0 | -130.0 | -0.0714 | 0.0 |
| outage45 | bridge-r+cf0.3 | cf0.3 | boulevard | 24 | 0 | -139.0 | -0.069 | 0.0 |
| measured | bridge-r+cf0.3 | bridge+cf0.3 | bayside | 0 | 4 | 0.0 | 0.0 | 0.125 |
| measured | bridge-r+cf0.3 | bridge+cf0.3 | blocks | 0 | 1 | 0.0 | 0.0 | 1.0 |
| measured | bridge-r+cf0.3 | bridge+cf0.3 | boulevard | 0 | 4 | 0.0 | 0.0 | 0.125 |
| outage15 | bridge-r+cf0.3 | bridge+cf0.3 | bayside | 1 | 14 | 2.0 | 0.0014 | 0.001 |
| outage15 | bridge-r+cf0.3 | bridge+cf0.3 | blocks | 12 | 1 | -1.0 | -0.0006 | 0.0034 |
| outage15 | bridge-r+cf0.3 | bridge+cf0.3 | boulevard | 0 | 16 | 2.0 | 0.0011 | 0.0 |
| outage45 | bridge-r+cf0.3 | bridge+cf0.3 | bayside | 3 | 14 | 3.0 | 0.002 | 0.0127 |
| outage45 | bridge-r+cf0.3 | bridge+cf0.3 | blocks | 15 | 2 | -6.0 | -0.0035 | 0.0023 |
| outage45 | bridge-r+cf0.3 | bridge+cf0.3 | boulevard | 0 | 16 | 4.0 | 0.0021 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 95.9 | 0.0666 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | blocks | 1 | 23 | 25.7 | 0.016 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 122.7 | 0.0695 | 0.0 |
| outage15 | dr+cf0.3 | cf0.3 | bayside | 17 | 7 | -14.1 | -0.0091 | 0.0639 |
| outage15 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -100.0 | -0.0574 | 0.0 |
| outage15 | dr+cf0.3 | cf0.3 | boulevard | 17 | 6 | -25.0 | -0.0131 | 0.0347 |
| outage45 | dr+cf0.3 | cf0.3 | bayside | 15 | 9 | -13.0 | -0.0079 | 0.3075 |
| outage45 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -111.9 | -0.0615 | 0.0 |
| outage45 | dr+cf0.3 | cf0.3 | boulevard | 17 | 6 | -22.0 | -0.0109 | 0.0347 |
| measured | bridge-r+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -96.0 | -0.0625 | 0.0 |
| measured | bridge-r+cf0.3 | dr+cf0.3 | blocks | 24 | 0 | -26.2 | -0.0161 | 0.0 |
| measured | bridge-r+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -123.5 | -0.0654 | 0.0 |
| outage15 | bridge-r+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -80.1 | -0.0522 | 0.0 |
| outage15 | bridge-r+cf0.3 | dr+cf0.3 | blocks | 19 | 4 | -9.5 | -0.0058 | 0.0026 |
| outage15 | bridge-r+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -105.0 | -0.0558 | 0.0 |
| outage45 | bridge-r+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -86.0 | -0.0533 | 0.0 |
| outage45 | bridge-r+cf0.3 | dr+cf0.3 | blocks | 20 | 3 | -19.1 | -0.0112 | 0.0005 |
| outage45 | bridge-r+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -102.4 | -0.0518 | 0.0 |

## GPS outages

| profile | variant | course | missions | reports withheld | s stood still | GPS filter restarts |
|---|---|---|---|---|---|---|
| measured | bridge+cf0.3 | bayside | 24 | 0.0 | 1.5 | None |
| measured | bridge+cf0.3 | blocks | 24 | 0.0 | 1.5 | None |
| measured | bridge+cf0.3 | boulevard | 24 | 0.0 | 1.5 | None |
| measured | bridge-r+cf0.3 | bayside | 24 | 0.0 | 1.5 | 1.5 |
| measured | bridge-r+cf0.3 | blocks | 24 | 0.0 | 1.5 | 2.0 |
| measured | bridge-r+cf0.3 | boulevard | 24 | 0.0 | 1.5 | 2.0 |
| measured | cf0.3 | bayside | 24 | 0.0 | 3.0 | None |
| measured | cf0.3 | blocks | 24 | 0.0 | 3.5 | None |
| measured | cf0.3 | boulevard | 24 | 0.0 | 3.6 | None |
| measured | dr+cf0.3 | bayside | 24 | 0.0 | 1.5 | None |
| measured | dr+cf0.3 | blocks | 24 | 0.0 | 1.5 | None |
| measured | dr+cf0.3 | boulevard | 24 | 0.0 | 1.5 | None |
| outage15 | bridge+cf0.3 | bayside | 24 | 64.0 | 12.6 | None |
| outage15 | bridge+cf0.3 | blocks | 24 | 70.5 | 6.2 | None |
| outage15 | bridge+cf0.3 | boulevard | 24 | 83.5 | 3.5 | None |
| outage15 | bridge-r+cf0.3 | bayside | 24 | 64.0 | 12.6 | 10.0 |
| outage15 | bridge-r+cf0.3 | blocks | 24 | 70.5 | 3.6 | 11.0 |
| outage15 | bridge-r+cf0.3 | boulevard | 24 | 83.5 | 6.2 | 12.5 |
| outage15 | cf0.3 | bayside | 24 | 70.5 | 118.8 | None |
| outage15 | cf0.3 | blocks | 24 | 82.0 | 137.1 | None |
| outage15 | cf0.3 | boulevard | 24 | 87.5 | 147.7 | None |
| outage15 | dr+cf0.3 | bayside | 24 | 70.0 | 12.6 | None |
| outage15 | dr+cf0.3 | blocks | 24 | 71.5 | 2.5 | None |
| outage15 | dr+cf0.3 | boulevard | 24 | 87.5 | 6.0 | None |
| outage45 | bridge+cf0.3 | bayside | 24 | 91.5 | 82.6 | None |
| outage45 | bridge+cf0.3 | blocks | 24 | 113.5 | 93.6 | None |
| outage45 | bridge+cf0.3 | boulevard | 24 | 114.0 | 102.3 | None |
| outage45 | bridge-r+cf0.3 | bayside | 24 | 91.5 | 81.9 | 5.5 |
| outage45 | bridge-r+cf0.3 | blocks | 24 | 113.5 | 90.2 | 6.5 |
| outage45 | bridge-r+cf0.3 | boulevard | 24 | 114.0 | 97.1 | 7.0 |
| outage45 | cf0.3 | bayside | 24 | 113.0 | 214.3 | None |
| outage45 | cf0.3 | blocks | 24 | 114.0 | 217.2 | None |
| outage45 | cf0.3 | boulevard | 24 | 135.0 | 255.1 | None |
| outage45 | dr+cf0.3 | bayside | 24 | 113.0 | 90.2 | None |
| outage45 | dr+cf0.3 | blocks | 24 | 113.5 | 91.6 | None |
| outage45 | dr+cf0.3 | boulevard | 24 | 135.0 | 110.8 | None |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| measured | bridge+cf0.3 | bayside | 24 | 0.0466 |
| measured | bridge+cf0.3 | blocks | 24 | 0.0592 |
| measured | bridge+cf0.3 | boulevard | 24 | 0.0445 |
| measured | bridge-r+cf0.3 | bayside | 24 | 0.0469 |
| measured | bridge-r+cf0.3 | blocks | 24 | 0.0595 |
| measured | bridge-r+cf0.3 | boulevard | 24 | 0.0447 |
| measured | cf0.3 | bayside | 24 | 0.0461 |
| measured | cf0.3 | blocks | 24 | 0.0592 |
| measured | cf0.3 | boulevard | 24 | 0.0442 |
| measured | dr+cf0.3 | bayside | 24 | 0.2244 |
| measured | dr+cf0.3 | blocks | 24 | 0.2237 |
| measured | dr+cf0.3 | boulevard | 24 | 0.2179 |
| outage15 | bridge+cf0.3 | bayside | 24 | 0.0479 |
| outage15 | bridge+cf0.3 | blocks | 24 | 0.0611 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 0.0455 |
| outage15 | bridge-r+cf0.3 | bayside | 24 | 0.0509 |
| outage15 | bridge-r+cf0.3 | blocks | 24 | 0.0622 |
| outage15 | bridge-r+cf0.3 | boulevard | 24 | 0.0481 |
| outage15 | cf0.3 | bayside | 24 | 0.046 |
| outage15 | cf0.3 | blocks | 24 | 0.0586 |
| outage15 | cf0.3 | boulevard | 24 | 0.0439 |
| outage15 | dr+cf0.3 | bayside | 24 | 0.2076 |
| outage15 | dr+cf0.3 | blocks | 24 | 0.2059 |
| outage15 | dr+cf0.3 | boulevard | 24 | 0.1983 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.0466 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0.0597 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0.0442 |
| outage45 | bridge-r+cf0.3 | bayside | 24 | 0.0485 |
| outage45 | bridge-r+cf0.3 | blocks | 24 | 0.06 |
| outage45 | bridge-r+cf0.3 | boulevard | 24 | 0.0459 |
| outage45 | cf0.3 | bayside | 24 | 0.0462 |
| outage45 | cf0.3 | blocks | 24 | 0.0589 |
| outage45 | cf0.3 | boulevard | 24 | 0.044 |
| outage45 | dr+cf0.3 | bayside | 24 | 0.2059 |
| outage45 | dr+cf0.3 | blocks | 24 | 0.2072 |
| outage45 | dr+cf0.3 | boulevard | 24 | 0.1976 |

## The compass-bias learner

| profile | variant | course | missions | median calibrations | median breaks | median abs bias error deg |
|---|---|---|---|---|---|---|
| measured | bridge+cf0.3 | bayside | 24 | 59.5 | 99.5 | 2.25 |
| measured | bridge+cf0.3 | blocks | 24 | 61.0 | 129.0 | 2.54 |
| measured | bridge+cf0.3 | boulevard | 24 | 81.0 | 103.5 | 2.46 |
| measured | bridge-r+cf0.3 | bayside | 24 | 61.0 | 99.5 | 2.69 |
| measured | bridge-r+cf0.3 | blocks | 24 | 61.0 | 130.0 | 3.16 |
| measured | bridge-r+cf0.3 | boulevard | 24 | 80.0 | 104.5 | 3.45 |
| measured | cf0.3 | bayside | 24 | 60.0 | 98.0 | 2.61 |
| measured | cf0.3 | blocks | 24 | 61.0 | 129.5 | 4.02 |
| measured | cf0.3 | boulevard | 24 | 80.0 | 106.5 | 2.71 |
| measured | dr+cf0.3 | bayside | 24 | 2.5 | 477.5 | 6.33 |
| measured | dr+cf0.3 | blocks | 24 | 3.0 | 506.0 | 2.75 |
| measured | dr+cf0.3 | boulevard | 24 | 3.0 | 585.5 | 2.69 |
| outage15 | bridge+cf0.3 | bayside | 24 | 51.0 | 107.0 | 2.27 |
| outage15 | bridge+cf0.3 | blocks | 24 | 51.0 | 138.5 | 2.77 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 69.5 | 111.5 | 2.53 |
| outage15 | bridge-r+cf0.3 | bayside | 24 | 50.0 | 114.0 | 2.05 |
| outage15 | bridge-r+cf0.3 | blocks | 24 | 53.0 | 139.0 | 1.89 |
| outage15 | bridge-r+cf0.3 | boulevard | 24 | 68.0 | 116.5 | 3.28 |
| outage15 | cf0.3 | bayside | 24 | 54.0 | 110.5 | 3.8 |
| outage15 | cf0.3 | blocks | 24 | 56.5 | 138.0 | 1.94 |
| outage15 | cf0.3 | boulevard | 24 | 75.0 | 115.0 | 2.84 |
| outage15 | dr+cf0.3 | bayside | 24 | 2.0 | 444.5 | 6.37 |
| outage15 | dr+cf0.3 | blocks | 24 | 3.0 | 463.5 | 3.29 |
| outage15 | dr+cf0.3 | boulevard | 24 | 2.0 | 537.0 | 3.36 |
| outage45 | bridge+cf0.3 | bayside | 24 | 51.5 | 106.0 | 2.22 |
| outage45 | bridge+cf0.3 | blocks | 24 | 52.0 | 137.0 | 2.38 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 72.0 | 108.0 | 2.41 |
| outage45 | bridge-r+cf0.3 | bayside | 24 | 51.5 | 109.0 | 3.28 |
| outage45 | bridge-r+cf0.3 | blocks | 24 | 53.0 | 133.0 | 2.92 |
| outage45 | bridge-r+cf0.3 | boulevard | 24 | 70.5 | 114.0 | 2.34 |
| outage45 | cf0.3 | bayside | 24 | 57.0 | 105.0 | 3.96 |
| outage45 | cf0.3 | blocks | 24 | 58.0 | 135.0 | 2.37 |
| outage45 | cf0.3 | boulevard | 24 | 78.0 | 108.0 | 2.71 |
| outage45 | dr+cf0.3 | bayside | 24 | 2.5 | 435.0 | 5.8 |
| outage45 | dr+cf0.3 | blocks | 24 | 3.0 | 467.5 | 2.58 |
| outage45 | dr+cf0.3 | boulevard | 24 | 3.0 | 539.5 | 3.25 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| measured | bridge+cf0.3 | bayside | 24 | 6.46 | 8.19 |
| measured | bridge+cf0.3 | blocks | 24 | 6.38 | 8.16 |
| measured | bridge+cf0.3 | boulevard | 24 | 6.5 | 8.25 |
| measured | bridge-r+cf0.3 | bayside | 24 | 6.44 | 8.14 |
| measured | bridge-r+cf0.3 | blocks | 24 | 6.36 | 8.1 |
| measured | bridge-r+cf0.3 | boulevard | 24 | 6.46 | 8.21 |
| measured | cf0.3 | bayside | 24 | 6.48 | 8.23 |
| measured | cf0.3 | blocks | 24 | 6.39 | 8.18 |
| measured | cf0.3 | boulevard | 24 | 6.55 | 8.27 |
| measured | dr+cf0.3 | bayside | 24 | 2.67 | 6.54 |
| measured | dr+cf0.3 | blocks | 24 | 2.66 | 6.51 |
| measured | dr+cf0.3 | boulevard | 24 | 2.6 | 6.36 |
| outage15 | bridge+cf0.3 | bayside | 24 | 6.5 | 9.53 |
| outage15 | bridge+cf0.3 | blocks | 24 | 6.38 | 9.48 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 6.51 | 9.88 |
| outage15 | bridge-r+cf0.3 | bayside | 24 | 6.19 | 8.16 |
| outage15 | bridge-r+cf0.3 | blocks | 24 | 6.1 | 8.13 |
| outage15 | bridge-r+cf0.3 | boulevard | 24 | 6.2 | 8.19 |
| outage15 | cf0.3 | bayside | 24 | 6.69 | 8.6 |
| outage15 | cf0.3 | blocks | 24 | 6.53 | 8.48 |
| outage15 | cf0.3 | boulevard | 24 | 6.67 | 8.62 |
| outage15 | dr+cf0.3 | bayside | 24 | 2.71 | 6.77 |
| outage15 | dr+cf0.3 | blocks | 24 | 2.7 | 6.75 |
| outage15 | dr+cf0.3 | boulevard | 24 | 2.67 | 6.54 |
| outage45 | bridge+cf0.3 | bayside | 24 | 6.63 | 9.09 |
| outage45 | bridge+cf0.3 | blocks | 24 | 6.43 | 8.86 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 6.6 | 9.12 |
| outage45 | bridge-r+cf0.3 | bayside | 24 | 6.38 | 8.22 |
| outage45 | bridge-r+cf0.3 | blocks | 24 | 6.23 | 8.11 |
| outage45 | bridge-r+cf0.3 | boulevard | 24 | 6.39 | 8.26 |
| outage45 | cf0.3 | bayside | 24 | 6.65 | 8.43 |
| outage45 | cf0.3 | blocks | 24 | 6.51 | 8.34 |
| outage45 | cf0.3 | boulevard | 24 | 6.62 | 8.43 |
| outage45 | dr+cf0.3 | bayside | 24 | 2.75 | 6.86 |
| outage45 | dr+cf0.3 | blocks | 24 | 2.71 | 6.73 |
| outage45 | dr+cf0.3 | boulevard | 24 | 2.67 | 6.66 |

## Dead reckoning

| profile | variant | course | missions | never trusted | first trusted s | s on wheels alone | abs scale error |
|---|---|---|---|---|---|---|---|
| measured | bridge+cf0.3 | bayside | 24 | 0 | 95.0 | 1.1 | 0.0091 |
| measured | bridge+cf0.3 | blocks | 24 | 0 | 91.0 | 1.6 | 0.0073 |
| measured | bridge+cf0.3 | boulevard | 24 | 0 | 93.0 | 2.0 | 0.0121 |
| measured | bridge-r+cf0.3 | bayside | 24 | 0 | 83.0 | 1.1 | 0.0121 |
| measured | bridge-r+cf0.3 | blocks | 24 | 0 | 88.0 | 1.6 | 0.0081 |
| measured | bridge-r+cf0.3 | boulevard | 24 | 0 | 93.0 | 2.0 | 0.0104 |
| measured | dr+cf0.3 | bayside | 24 | 0 | 95.0 | 1.1 | 0.0356 |
| measured | dr+cf0.3 | blocks | 24 | 0 | 91.0 | 1.6 | 0.0549 |
| measured | dr+cf0.3 | boulevard | 24 | 0 | 93.0 | 2.1 | 0.0397 |
| outage15 | bridge+cf0.3 | bayside | 24 | 0 | 101.0 | 97.8 | 0.0124 |
| outage15 | bridge+cf0.3 | blocks | 24 | 0 | 95.0 | 110.0 | 0.0071 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 0 | 93.0 | 132.6 | 0.0065 |
| outage15 | bridge-r+cf0.3 | bayside | 24 | 0 | 103.0 | 95.5 | 0.0132 |
| outage15 | bridge-r+cf0.3 | blocks | 24 | 0 | 93.0 | 110.0 | 0.0071 |
| outage15 | bridge-r+cf0.3 | boulevard | 24 | 0 | 95.0 | 132.6 | 0.0046 |
| outage15 | dr+cf0.3 | bayside | 24 | 0 | 101.0 | 104.1 | 0.0555 |
| outage15 | dr+cf0.3 | blocks | 24 | 0 | 95.0 | 116.8 | 0.0399 |
| outage15 | dr+cf0.3 | boulevard | 24 | 0 | 93.0 | 138.5 | 0.0422 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0 | 117.0 | 100.9 | 0.0126 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0 | 101.0 | 125.5 | 0.0119 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0 | 101.0 | 126.5 | 0.0104 |
| outage45 | bridge-r+cf0.3 | bayside | 24 | 0 | 122.0 | 100.9 | 0.0127 |
| outage45 | bridge-r+cf0.3 | blocks | 24 | 0 | 99.0 | 125.5 | 0.0095 |
| outage45 | bridge-r+cf0.3 | boulevard | 24 | 0 | 101.0 | 126.5 | 0.0109 |
| outage45 | dr+cf0.3 | bayside | 24 | 0 | 117.0 | 102.3 | 0.0524 |
| outage45 | dr+cf0.3 | blocks | 24 | 0 | 101.0 | 125.5 | 0.0549 |
| outage45 | dr+cf0.3 | boulevard | 24 | 0 | 101.0 | 139.5 | 0.0375 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| measured | bridge+cf0.3 | bayside | 24 | 0.69 | 2.31 |
| measured | bridge+cf0.3 | blocks | 24 | 1.33 | 10.29 |
| measured | bridge+cf0.3 | boulevard | 24 | 1.94 | 5.14 |
| measured | bridge-r+cf0.3 | bayside | 24 | 0.69 | 2.34 |
| measured | bridge-r+cf0.3 | blocks | 24 | 1.31 | 10.21 |
| measured | bridge-r+cf0.3 | boulevard | 24 | 1.87 | 5.09 |
| measured | cf0.3 | bayside | 24 | 0.68 | 2.34 |
| measured | cf0.3 | blocks | 24 | 1.31 | 10.24 |
| measured | cf0.3 | boulevard | 24 | 1.81 | 5.0 |
| measured | dr+cf0.3 | bayside | 24 | 1.0 | 2.38 |
| measured | dr+cf0.3 | blocks | 24 | 1.03 | 7.21 |
| measured | dr+cf0.3 | boulevard | 24 | 1.25 | 4.09 |
| outage15 | bridge+cf0.3 | bayside | 24 | 0.83 | 2.95 |
| outage15 | bridge+cf0.3 | blocks | 24 | 1.44 | 10.71 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 1.92 | 5.15 |
| outage15 | bridge-r+cf0.3 | bayside | 24 | 0.77 | 2.67 |
| outage15 | bridge-r+cf0.3 | blocks | 24 | 1.26 | 9.71 |
| outage15 | bridge-r+cf0.3 | boulevard | 24 | 1.77 | 5.25 |
| outage15 | cf0.3 | bayside | 24 | 0.7 | 2.27 |
| outage15 | cf0.3 | blocks | 24 | 1.3 | 10.05 |
| outage15 | cf0.3 | boulevard | 24 | 1.79 | 4.96 |
| outage15 | dr+cf0.3 | bayside | 24 | 1.1 | 3.02 |
| outage15 | dr+cf0.3 | blocks | 24 | 1.12 | 7.08 |
| outage15 | dr+cf0.3 | boulevard | 24 | 1.35 | 4.57 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.76 | 3.21 |
| outage45 | bridge+cf0.3 | blocks | 24 | 1.42 | 10.69 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 1.88 | 5.5 |
| outage45 | bridge-r+cf0.3 | bayside | 24 | 0.74 | 2.85 |
| outage45 | bridge-r+cf0.3 | blocks | 24 | 1.29 | 9.81 |
| outage45 | bridge-r+cf0.3 | boulevard | 24 | 1.75 | 5.01 |
| outage45 | cf0.3 | bayside | 24 | 0.72 | 2.45 |
| outage45 | cf0.3 | blocks | 24 | 1.28 | 10.22 |
| outage45 | cf0.3 | boulevard | 24 | 1.82 | 5.12 |
| outage45 | dr+cf0.3 | bayside | 24 | 1.02 | 2.92 |
| outage45 | dr+cf0.3 | blocks | 24 | 1.1 | 6.88 |
| outage45 | dr+cf0.3 | boulevard | 24 | 1.42 | 4.7 |
