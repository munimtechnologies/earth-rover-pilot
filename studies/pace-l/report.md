# Does the 120 s reach hold up when the wheels and the compass lie? (simulated)

pace_l.py 0.1.0 (pace_k.py 0.1.0, pace_j.py 0.1.0, rover_pilot.py 0.16.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every profile is pace_k.py's measured Mini+ with 45 s GPS outages (after 300 s of sky on average) or 90 s outages (after 600 s); slip: the wheels report a factor drawn from [0.85, 1.15] times their true RPM, changing every 120 s on average; drift: the compass error drifts (SD 10 deg, 120 s time constant); lie: both. Variants: the bridging pilot with the reckoner carrying the position up to 30 s (bridge+cf0.3), 60 s (bridge60+cf0.3) or 120 s (bridge120+cf0.3, v0.16.0 on a real rover) after the last fix. Seeds 157-180. 1296 of 1296 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_k.py's runs: 36 compared, 36 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage45 | bridge+cf0.3 | 72/72 | 0.825 | 0.928 | 72 | 1.007 | 0.059 |
| outage45 | bridge60+cf0.3 | 72/72 | 0.862 | 0.97 | 72 | 1.008 | 0.016 |
| outage45 | bridge120+cf0.3 | 72/72 | 0.862 | 0.97 | 72 | 1.008 | 0.016 |
| lie45 | bridge+cf0.3 | 72/72 | 0.822 | 0.925 | 71 | 1.011 | 0.058 |
| lie45 | bridge60+cf0.3 | 72/72 | 0.858 | 0.965 | 72 | 1.014 | 0.015 |
| lie45 | bridge120+cf0.3 | 72/72 | 0.858 | 0.965 | 72 | 1.014 | 0.015 |
| outage90 | bridge+cf0.3 | 72/72 | 0.809 | 0.91 | 57 | 1.006 | 0.088 |
| outage90 | bridge60+cf0.3 | 72/72 | 0.836 | 0.94 | 70 | 1.007 | 0.053 |
| outage90 | bridge120+cf0.3 | 72/72 | 0.868 | 0.976 | 72 | 1.008 | 0.018 |
| slip90 | bridge+cf0.3 | 72/72 | 0.809 | 0.91 | 57 | 1.005 | 0.088 |
| slip90 | bridge60+cf0.3 | 72/72 | 0.836 | 0.94 | 70 | 1.007 | 0.053 |
| slip90 | bridge120+cf0.3 | 72/72 | 0.866 | 0.974 | 72 | 1.007 | 0.019 |
| drift90 | bridge+cf0.3 | 72/72 | 0.807 | 0.907 | 57 | 1.009 | 0.087 |
| drift90 | bridge60+cf0.3 | 72/72 | 0.831 | 0.934 | 69 | 1.011 | 0.053 |
| drift90 | bridge120+cf0.3 | 72/72 | 0.86 | 0.967 | 72 | 1.014 | 0.016 |
| lie90 | bridge+cf0.3 | 72/72 | 0.807 | 0.908 | 56 | 1.009 | 0.087 |
| lie90 | bridge60+cf0.3 | 72/72 | 0.831 | 0.934 | 70 | 1.012 | 0.054 |
| lie90 | bridge120+cf0.3 | 72/72 | 0.861 | 0.969 | 72 | 1.014 | 0.017 |

## Longer reach against shorter, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0452 |
| drift90 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0322 |
| lie45 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0434 |
| lie90 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0322 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0317 |
| slip90 | bridge60+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0317 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0452 |
| drift90 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0651 |
| lie45 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0434 |
| lie90 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0645 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0645 |
| slip90 | bridge120+cf0.3 | bridge+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0645 |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| drift90 | bridge120+cf0.3 | bridge60+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0267 |
| lie45 | bridge120+cf0.3 | bridge60+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0 |
| lie90 | bridge120+cf0.3 | bridge60+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0266 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0268 |
| slip90 | bridge120+cf0.3 | bridge60+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0286 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 23 | 0 | -57.0 | -0.0373 | 0.0 |
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 22 | 0 | -76.0 | -0.0445 | 0.0 |
| outage45 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -85.0 | -0.0452 | 0.0 |
| drift90 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 19 | 0 | -37.0 | -0.0236 | 0.0 |
| drift90 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 17 | 1 | -54.0 | -0.0311 | 0.0001 |
| drift90 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -62.0 | -0.0322 | 0.0 |
| lie45 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 23 | 0 | -54.0 | -0.0352 | 0.0 |
| lie45 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 22 | 0 | -66.0 | -0.0386 | 0.0 |
| lie45 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -82.0 | -0.0434 | 0.0 |
| lie90 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 20 | 0 | -37.0 | -0.0237 | 0.0 |
| lie90 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 18 | 0 | -50.0 | -0.0288 | 0.0 |
| lie90 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -62.0 | -0.0322 | 0.0 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 20 | 0 | -48.0 | -0.0308 | 0.0 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 20 | 0 | -53.0 | -0.0306 | 0.0 |
| outage90 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -61.0 | -0.0317 | 0.0 |
| slip90 | bridge60+cf0.3 | bridge+cf0.3 | bayside | 20 | 0 | -48.0 | -0.0308 | 0.0 |
| slip90 | bridge60+cf0.3 | bridge+cf0.3 | blocks | 20 | 0 | -48.0 | -0.0277 | 0.0 |
| slip90 | bridge60+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -61.0 | -0.0317 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 23 | 0 | -57.0 | -0.0373 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 22 | 0 | -76.0 | -0.0445 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -85.0 | -0.0452 | 0.0 |
| drift90 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 19 | 0 | -76.0 | -0.0486 | 0.0 |
| drift90 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 18 | 1 | -113.0 | -0.0651 | 0.0001 |
| drift90 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -119.0 | -0.0618 | 0.0 |
| lie45 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 23 | 0 | -54.0 | -0.0352 | 0.0 |
| lie45 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 22 | 0 | -66.0 | -0.0386 | 0.0 |
| lie45 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 24 | 0 | -82.0 | -0.0434 | 0.0 |
| lie90 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 20 | 0 | -74.0 | -0.0473 | 0.0 |
| lie90 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 18 | 0 | -112.0 | -0.0645 | 0.0 |
| lie90 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -119.0 | -0.0618 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 20 | 0 | -71.0 | -0.0455 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 20 | 0 | -108.0 | -0.0624 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -124.0 | -0.0645 | 0.0 |
| slip90 | bridge120+cf0.3 | bridge+cf0.3 | bayside | 20 | 0 | -71.0 | -0.0455 | 0.0 |
| slip90 | bridge120+cf0.3 | bridge+cf0.3 | blocks | 20 | 0 | -105.0 | -0.0606 | 0.0 |
| slip90 | bridge120+cf0.3 | bridge+cf0.3 | boulevard | 21 | 0 | -124.0 | -0.0645 | 0.0 |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| outage45 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| drift90 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 18 | 0 | -36.0 | -0.0237 | 0.0 |
| drift90 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 17 | 0 | -45.0 | -0.0267 | 0.0 |
| drift90 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 21 | 0 | -48.0 | -0.0258 | 0.0 |
| lie45 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| lie45 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| lie45 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| lie90 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 18 | 0 | -32.0 | -0.0211 | 0.0 |
| lie90 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 18 | 0 | -45.0 | -0.0266 | 0.0 |
| lie90 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 21 | 0 | -48.0 | -0.0258 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 19 | 0 | -30.0 | -0.0199 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 19 | 1 | -45.0 | -0.0268 | 0.0 |
| outage90 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 21 | 0 | -49.0 | -0.0264 | 0.0 |
| slip90 | bridge120+cf0.3 | bridge60+cf0.3 | bayside | 19 | 0 | -32.0 | -0.0212 | 0.0 |
| slip90 | bridge120+cf0.3 | bridge60+cf0.3 | blocks | 19 | 1 | -48.0 | -0.0286 | 0.0 |
| slip90 | bridge120+cf0.3 | bridge60+cf0.3 | boulevard | 21 | 0 | -50.0 | -0.0269 | 0.0 |

## What the lies cost, same variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| bridge+cf0.3 | lie45 | outage45 | 0/3 | 2 | 0 | 0 | 0.0039 |
| bridge+cf0.3 | slip90 | outage90 | 0/3 | 0 | 0 | 0 | 0.0 |
| bridge+cf0.3 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0029 |
| bridge+cf0.3 | lie90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0032 |
| bridge60+cf0.3 | lie45 | outage45 | 0/3 | 3 | 0 | 0 | 0.0055 |
| bridge60+cf0.3 | slip90 | outage90 | 0/3 | 0 | 0 | 0 | 0.0 |
| bridge60+cf0.3 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0042 |
| bridge60+cf0.3 | lie90 | outage90 | 0/3 | 3 | 0 | 0 | 0.004 |
| bridge120+cf0.3 | lie45 | outage45 | 0/3 | 3 | 0 | 0 | 0.0055 |
| bridge120+cf0.3 | slip90 | outage90 | 0/3 | 0 | 0 | 0 | 0.0 |
| bridge120+cf0.3 | drift90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0055 |
| bridge120+cf0.3 | lie90 | outage90 | 0/3 | 3 | 0 | 0 | 0.0049 |

| variant | profile | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| bridge+cf0.3 | lie45 | outage45 | bayside | 3 | 18 | 6.0 | 0.0039 | 0.0015 |
| bridge+cf0.3 | lie45 | outage45 | blocks | 5 | 12 | 1.0 | 0.0006 | 0.1435 |
| bridge+cf0.3 | lie45 | outage45 | boulevard | 1 | 16 | 4.0 | 0.0021 | 0.0003 |
| bridge+cf0.3 | slip90 | outage90 | bayside | 1 | 1 | 0.0 | 0.0 | 1.0 |
| bridge+cf0.3 | slip90 | outage90 | blocks | 2 | 0 | 0.0 | 0.0 | 0.5 |
| bridge+cf0.3 | slip90 | outage90 | boulevard | 1 | 0 | 0.0 | 0.0 | 1.0 |
| bridge+cf0.3 | drift90 | outage90 | bayside | 1 | 19 | 4.0 | 0.0026 | 0.0 |
| bridge+cf0.3 | drift90 | outage90 | blocks | 3 | 16 | 5.0 | 0.0029 | 0.0044 |
| bridge+cf0.3 | drift90 | outage90 | boulevard | 1 | 20 | 4.0 | 0.0021 | 0.0 |
| bridge+cf0.3 | lie90 | outage90 | bayside | 1 | 18 | 5.0 | 0.0032 | 0.0001 |
| bridge+cf0.3 | lie90 | outage90 | blocks | 4 | 16 | 5.0 | 0.0029 | 0.0118 |
| bridge+cf0.3 | lie90 | outage90 | boulevard | 1 | 20 | 4.0 | 0.0021 | 0.0 |
| bridge60+cf0.3 | lie45 | outage45 | bayside | 2 | 16 | 8.0 | 0.0055 | 0.0013 |
| bridge60+cf0.3 | lie45 | outage45 | blocks | 4 | 13 | 2.0 | 0.0012 | 0.049 |
| bridge60+cf0.3 | lie45 | outage45 | boulevard | 1 | 16 | 5.0 | 0.0028 | 0.0003 |
| bridge60+cf0.3 | slip90 | outage90 | bayside | 2 | 3 | 0.0 | 0.0 | 1.0 |
| bridge60+cf0.3 | slip90 | outage90 | blocks | 2 | 4 | 0.0 | 0.0 | 0.6875 |
| bridge60+cf0.3 | slip90 | outage90 | boulevard | 2 | 2 | 0.0 | 0.0 | 1.0 |
| bridge60+cf0.3 | drift90 | outage90 | bayside | 1 | 18 | 6.0 | 0.004 | 0.0001 |
| bridge60+cf0.3 | drift90 | outage90 | blocks | 3 | 17 | 7.0 | 0.0042 | 0.0026 |
| bridge60+cf0.3 | drift90 | outage90 | boulevard | 1 | 18 | 5.0 | 0.0027 | 0.0001 |
| bridge60+cf0.3 | lie90 | outage90 | bayside | 1 | 18 | 6.0 | 0.004 | 0.0001 |
| bridge60+cf0.3 | lie90 | outage90 | blocks | 4 | 16 | 5.0 | 0.003 | 0.0118 |
| bridge60+cf0.3 | lie90 | outage90 | boulevard | 2 | 18 | 4.0 | 0.0022 | 0.0004 |
| bridge120+cf0.3 | lie45 | outage45 | bayside | 2 | 16 | 8.0 | 0.0055 | 0.0013 |
| bridge120+cf0.3 | lie45 | outage45 | blocks | 4 | 13 | 2.0 | 0.0012 | 0.049 |
| bridge120+cf0.3 | lie45 | outage45 | boulevard | 1 | 16 | 5.0 | 0.0028 | 0.0003 |
| bridge120+cf0.3 | slip90 | outage90 | bayside | 3 | 5 | 0.0 | 0.0 | 0.7266 |
| bridge120+cf0.3 | slip90 | outage90 | blocks | 5 | 7 | 0.0 | 0.0 | 0.7744 |
| bridge120+cf0.3 | slip90 | outage90 | boulevard | 2 | 2 | 0.0 | 0.0 | 1.0 |
| bridge120+cf0.3 | drift90 | outage90 | bayside | 4 | 17 | 8.0 | 0.0055 | 0.0072 |
| bridge120+cf0.3 | drift90 | outage90 | blocks | 4 | 17 | 8.0 | 0.0049 | 0.0072 |
| bridge120+cf0.3 | drift90 | outage90 | boulevard | 1 | 18 | 4.0 | 0.0023 | 0.0001 |
| bridge120+cf0.3 | lie90 | outage90 | bayside | 3 | 17 | 7.0 | 0.0048 | 0.0026 |
| bridge120+cf0.3 | lie90 | outage90 | blocks | 5 | 16 | 8.0 | 0.0049 | 0.0266 |
| bridge120+cf0.3 | lie90 | outage90 | boulevard | 2 | 17 | 5.0 | 0.0028 | 0.0007 |

## GPS outages

| profile | variant | course | missions | reports withheld | s stood still |
|---|---|---|---|---|---|
| drift90 | bridge+cf0.3 | bayside | 24 | 90.0 | 125.5 |
| drift90 | bridge+cf0.3 | blocks | 24 | 90.0 | 125.5 |
| drift90 | bridge+cf0.3 | boulevard | 24 | 112.5 | 161.4 |
| drift90 | bridge120+cf0.3 | bayside | 24 | 90.0 | 1.5 |
| drift90 | bridge120+cf0.3 | blocks | 24 | 90.0 | 5.8 |
| drift90 | bridge120+cf0.3 | boulevard | 24 | 90.0 | 3.5 |
| drift90 | bridge60+cf0.3 | bayside | 24 | 90.0 | 66.5 |
| drift90 | bridge60+cf0.3 | blocks | 24 | 90.0 | 66.5 |
| drift90 | bridge60+cf0.3 | boulevard | 24 | 112.5 | 98.3 |
| lie45 | bridge+cf0.3 | bayside | 24 | 101.5 | 87.7 |
| lie45 | bridge+cf0.3 | blocks | 24 | 113.0 | 94.8 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 134.5 | 115.6 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 101.5 | 14.9 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 101.5 | 20.1 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 124.0 | 23.2 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 101.5 | 14.9 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 101.5 | 20.1 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 124.0 | 23.2 |
| lie90 | bridge+cf0.3 | bayside | 24 | 90.0 | 125.5 |
| lie90 | bridge+cf0.3 | blocks | 24 | 90.0 | 125.5 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 112.5 | 162.8 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 90.0 | 3.0 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 90.0 | 6.1 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 90.0 | 3.5 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 90.0 | 66.5 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 90.0 | 66.6 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 112.5 | 98.3 |
| outage45 | bridge+cf0.3 | bayside | 24 | 101.5 | 87.3 |
| outage45 | bridge+cf0.3 | blocks | 24 | 113.0 | 95.2 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 134.5 | 118.1 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 101.5 | 22.2 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 101.5 | 22.2 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 124.0 | 21.6 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 101.5 | 22.2 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 101.5 | 22.2 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 124.0 | 21.6 |
| outage90 | bridge+cf0.3 | bayside | 24 | 90.0 | 125.5 |
| outage90 | bridge+cf0.3 | blocks | 24 | 90.0 | 125.5 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 112.5 | 163.2 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 90.0 | 2.6 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 90.0 | 14.4 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 90.0 | 2.5 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 90.0 | 65.5 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 90.0 | 66.3 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 112.5 | 98.3 |
| slip90 | bridge+cf0.3 | bayside | 24 | 90.0 | 125.5 |
| slip90 | bridge+cf0.3 | blocks | 24 | 90.0 | 125.5 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 112.5 | 164.4 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 90.0 | 4.2 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 90.0 | 13.7 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 90.0 | 2.5 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 90.0 | 65.5 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 90.0 | 66.5 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 112.5 | 98.3 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | bridge+cf0.3 | bayside | 24 | 6.49 | 8.54 |
| drift90 | bridge+cf0.3 | blocks | 24 | 6.4 | 8.52 |
| drift90 | bridge+cf0.3 | boulevard | 24 | 6.57 | 8.71 |
| drift90 | bridge120+cf0.3 | bayside | 24 | 6.46 | 8.8 |
| drift90 | bridge120+cf0.3 | blocks | 24 | 6.38 | 8.62 |
| drift90 | bridge120+cf0.3 | boulevard | 24 | 6.56 | 9.04 |
| drift90 | bridge60+cf0.3 | bayside | 24 | 6.48 | 8.69 |
| drift90 | bridge60+cf0.3 | blocks | 24 | 6.36 | 8.54 |
| drift90 | bridge60+cf0.3 | boulevard | 24 | 6.57 | 8.82 |
| lie45 | bridge+cf0.3 | bayside | 24 | 6.59 | 9.05 |
| lie45 | bridge+cf0.3 | blocks | 24 | 6.42 | 9.07 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 6.62 | 9.29 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 6.5 | 9.27 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 6.39 | 9.21 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 6.58 | 9.66 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 6.5 | 9.27 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 6.39 | 9.21 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 6.58 | 9.66 |
| lie90 | bridge+cf0.3 | bayside | 24 | 6.49 | 8.54 |
| lie90 | bridge+cf0.3 | blocks | 24 | 6.4 | 8.53 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 6.58 | 8.71 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 6.48 | 8.89 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 6.41 | 8.77 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 6.56 | 9.28 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 6.5 | 8.73 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 6.37 | 8.59 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 6.58 | 8.85 |
| outage45 | bridge+cf0.3 | bayside | 24 | 6.6 | 9.03 |
| outage45 | bridge+cf0.3 | blocks | 24 | 6.42 | 8.9 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 6.61 | 9.27 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 6.45 | 9.11 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 6.36 | 9.2 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 6.56 | 9.53 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 6.45 | 9.11 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 6.36 | 9.2 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 6.56 | 9.53 |
| outage90 | bridge+cf0.3 | bayside | 24 | 6.5 | 8.54 |
| outage90 | bridge+cf0.3 | blocks | 24 | 6.44 | 8.56 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 6.6 | 8.66 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 6.42 | 8.63 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 6.33 | 8.52 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 6.51 | 8.77 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 6.47 | 8.66 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 6.36 | 8.52 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 6.55 | 8.76 |
| slip90 | bridge+cf0.3 | bayside | 24 | 6.5 | 8.57 |
| slip90 | bridge+cf0.3 | blocks | 24 | 6.43 | 8.56 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 6.6 | 8.66 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 6.46 | 8.78 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 6.34 | 8.57 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 6.56 | 8.85 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 6.49 | 8.69 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 6.36 | 8.58 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 6.56 | 8.77 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift90 | bridge+cf0.3 | bayside | 24 | 1.06 | 3.48 |
| drift90 | bridge+cf0.3 | blocks | 24 | 1.73 | 10.4 |
| drift90 | bridge+cf0.3 | boulevard | 24 | 2.03 | 6.37 |
| drift90 | bridge120+cf0.3 | bayside | 24 | 1.15 | 4.19 |
| drift90 | bridge120+cf0.3 | blocks | 24 | 1.95 | 11.19 |
| drift90 | bridge120+cf0.3 | boulevard | 24 | 2.09 | 7.05 |
| drift90 | bridge60+cf0.3 | bayside | 24 | 1.1 | 4.07 |
| drift90 | bridge60+cf0.3 | blocks | 24 | 1.87 | 10.8 |
| drift90 | bridge60+cf0.3 | boulevard | 24 | 2.04 | 6.7 |
| lie45 | bridge+cf0.3 | bayside | 24 | 1.13 | 3.93 |
| lie45 | bridge+cf0.3 | blocks | 24 | 1.9 | 10.59 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 1.98 | 6.21 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 1.19 | 4.73 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 1.99 | 11.1 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 2.16 | 7.29 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 1.19 | 4.73 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 1.99 | 11.1 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 2.16 | 7.29 |
| lie90 | bridge+cf0.3 | bayside | 24 | 1.06 | 3.42 |
| lie90 | bridge+cf0.3 | blocks | 24 | 1.69 | 10.49 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 2.04 | 6.3 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 1.12 | 4.34 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 1.96 | 11.13 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 1.99 | 7.38 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 1.1 | 4.08 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 1.89 | 10.69 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 2.04 | 6.63 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.79 | 2.7 |
| outage45 | bridge+cf0.3 | blocks | 24 | 1.43 | 10.11 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 1.77 | 5.66 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 0.82 | 3.46 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 1.46 | 10.87 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 1.95 | 5.91 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 0.82 | 3.46 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 1.46 | 10.87 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 1.95 | 5.91 |
| outage90 | bridge+cf0.3 | bayside | 24 | 0.76 | 2.44 |
| outage90 | bridge+cf0.3 | blocks | 24 | 1.34 | 10.39 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 1.85 | 5.5 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 0.81 | 3.61 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 1.52 | 10.69 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 1.85 | 5.79 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 0.79 | 2.96 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 1.39 | 10.44 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 1.81 | 5.64 |
| slip90 | bridge+cf0.3 | bayside | 24 | 0.75 | 2.4 |
| slip90 | bridge+cf0.3 | blocks | 24 | 1.31 | 10.52 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 1.84 | 5.5 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 0.82 | 3.42 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 1.54 | 11.01 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 1.83 | 5.78 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 0.81 | 2.9 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 1.48 | 10.34 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 1.81 | 5.63 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| drift90 | bridge+cf0.3 | bayside | 24 | 5.75 | 9.28 |
| drift90 | bridge+cf0.3 | blocks | 24 | 5.68 | 9.52 |
| drift90 | bridge+cf0.3 | boulevard | 24 | 5.32 | 8.62 |
| drift90 | bridge120+cf0.3 | bayside | 24 | 5.76 | 9.5 |
| drift90 | bridge120+cf0.3 | blocks | 24 | 5.67 | 9.2 |
| drift90 | bridge120+cf0.3 | boulevard | 24 | 5.45 | 9.11 |
| drift90 | bridge60+cf0.3 | bayside | 24 | 5.66 | 9.43 |
| drift90 | bridge60+cf0.3 | blocks | 24 | 5.71 | 9.2 |
| drift90 | bridge60+cf0.3 | boulevard | 24 | 5.36 | 8.68 |
| lie45 | bridge+cf0.3 | bayside | 24 | 5.99 | 9.51 |
| lie45 | bridge+cf0.3 | blocks | 24 | 5.95 | 9.31 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 5.29 | 8.98 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 5.87 | 9.6 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 5.79 | 8.9 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 5.57 | 9.19 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 5.87 | 9.6 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 5.79 | 8.9 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 5.57 | 9.19 |
| lie90 | bridge+cf0.3 | bayside | 24 | 5.65 | 9.13 |
| lie90 | bridge+cf0.3 | blocks | 24 | 5.57 | 9.44 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 5.42 | 8.62 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 5.84 | 9.38 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 5.67 | 9.37 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 5.44 | 8.89 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 5.86 | 9.37 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 5.71 | 9.3 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 5.35 | 8.93 |
| outage45 | bridge+cf0.3 | bayside | 24 | 2.82 | 5.37 |
| outage45 | bridge+cf0.3 | blocks | 24 | 3.04 | 5.62 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 3.02 | 5.48 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 3.08 | 5.5 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 3.02 | 5.62 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 2.88 | 5.47 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 3.08 | 5.5 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 3.02 | 5.62 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 2.88 | 5.47 |
| outage90 | bridge+cf0.3 | bayside | 24 | 2.88 | 5.4 |
| outage90 | bridge+cf0.3 | blocks | 24 | 3.11 | 5.77 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 2.88 | 5.27 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 3.03 | 5.37 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 2.92 | 5.66 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 2.81 | 5.41 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 2.97 | 5.4 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 3.26 | 5.83 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 2.73 | 5.33 |
| slip90 | bridge+cf0.3 | bayside | 24 | 2.91 | 5.43 |
| slip90 | bridge+cf0.3 | blocks | 24 | 3.04 | 5.69 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 2.88 | 5.25 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 2.96 | 5.29 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 3.04 | 5.89 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 2.71 | 5.43 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 2.92 | 5.37 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 3.12 | 5.67 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 2.75 | 5.29 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| drift90 | bridge+cf0.3 | bayside | 24 | 0.0488 |
| drift90 | bridge+cf0.3 | blocks | 24 | 0.0622 |
| drift90 | bridge+cf0.3 | boulevard | 24 | 0.0471 |
| drift90 | bridge120+cf0.3 | bayside | 24 | 0.0502 |
| drift90 | bridge120+cf0.3 | blocks | 24 | 0.0612 |
| drift90 | bridge120+cf0.3 | boulevard | 24 | 0.0452 |
| drift90 | bridge60+cf0.3 | bayside | 24 | 0.0493 |
| drift90 | bridge60+cf0.3 | blocks | 24 | 0.0619 |
| drift90 | bridge60+cf0.3 | boulevard | 24 | 0.0461 |
| lie45 | bridge+cf0.3 | bayside | 24 | 0.0491 |
| lie45 | bridge+cf0.3 | blocks | 24 | 0.062 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 0.0471 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 0.0507 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 0.0618 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 0.0463 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 0.0507 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 0.0618 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 0.0463 |
| lie90 | bridge+cf0.3 | bayside | 24 | 0.0486 |
| lie90 | bridge+cf0.3 | blocks | 24 | 0.0616 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 0.0471 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 0.0494 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 0.0614 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 0.0452 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 0.0498 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 0.062 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 0.046 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.046 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0.0595 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0.0442 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 0.047 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 0.0597 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 0.0435 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 0.047 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 0.0597 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 0.0435 |
| outage90 | bridge+cf0.3 | bayside | 24 | 0.0463 |
| outage90 | bridge+cf0.3 | blocks | 24 | 0.059 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 0.0442 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 0.0471 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 0.0588 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 0.0427 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 0.0476 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 0.0602 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 0.0436 |
| slip90 | bridge+cf0.3 | bayside | 24 | 0.0463 |
| slip90 | bridge+cf0.3 | blocks | 24 | 0.0595 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 0.0444 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 0.0474 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 0.0596 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 0.0427 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 0.0473 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 0.0602 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 0.0434 |

## Dead reckoning

| profile | variant | course | missions | never trusted | first trusted s | s on wheels alone | abs scale error |
|---|---|---|---|---|---|---|---|
| drift90 | bridge+cf0.3 | bayside | 24 | 0 | 101.0 | 52.2 | 0.0137 |
| drift90 | bridge+cf0.3 | blocks | 24 | 0 | 82.0 | 54.5 | 0.0067 |
| drift90 | bridge+cf0.3 | boulevard | 24 | 0 | 80.0 | 64.9 | 0.0086 |
| drift90 | bridge120+cf0.3 | bayside | 24 | 0 | 101.0 | 176.2 | 0.0116 |
| drift90 | bridge120+cf0.3 | blocks | 24 | 0 | 82.0 | 176.7 | 0.0081 |
| drift90 | bridge120+cf0.3 | boulevard | 24 | 0 | 80.0 | 179.8 | 0.0081 |
| drift90 | bridge60+cf0.3 | bayside | 24 | 0 | 101.0 | 112.2 | 0.0137 |
| drift90 | bridge60+cf0.3 | blocks | 24 | 0 | 82.0 | 112.8 | 0.0085 |
| drift90 | bridge60+cf0.3 | boulevard | 24 | 0 | 80.0 | 139.9 | 0.0091 |
| lie45 | bridge+cf0.3 | bayside | 24 | 0 | 102.0 | 104.2 | 0.0288 |
| lie45 | bridge+cf0.3 | blocks | 24 | 0 | 88.0 | 128.1 | 0.0164 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 0 | 89.0 | 151.6 | 0.0201 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 0 | 102.0 | 172.9 | 0.0304 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 0 | 88.0 | 192.8 | 0.0239 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 0 | 89.0 | 218.8 | 0.0216 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 0 | 102.0 | 172.9 | 0.0304 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 0 | 88.0 | 192.8 | 0.0239 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 0 | 89.0 | 218.8 | 0.0216 |
| lie90 | bridge+cf0.3 | bayside | 24 | 0 | 101.0 | 52.2 | 0.033 |
| lie90 | bridge+cf0.3 | blocks | 24 | 0 | 82.0 | 54.5 | 0.0171 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 0 | 80.0 | 64.9 | 0.024 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 0 | 101.0 | 176.2 | 0.0274 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 0 | 82.0 | 176.7 | 0.0184 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 0 | 80.0 | 179.8 | 0.0208 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 0 | 101.0 | 112.2 | 0.0263 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 0 | 82.0 | 113.4 | 0.0163 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 0 | 80.0 | 139.9 | 0.0212 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0 | 111.0 | 115.0 | 0.0137 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0 | 98.0 | 128.1 | 0.0101 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0 | 96.0 | 151.6 | 0.006 |
| outage45 | bridge120+cf0.3 | bayside | 24 | 0 | 111.0 | 173.8 | 0.0158 |
| outage45 | bridge120+cf0.3 | blocks | 24 | 0 | 98.0 | 191.3 | 0.01 |
| outage45 | bridge120+cf0.3 | boulevard | 24 | 0 | 96.0 | 218.8 | 0.0073 |
| outage45 | bridge60+cf0.3 | bayside | 24 | 0 | 111.0 | 173.8 | 0.0158 |
| outage45 | bridge60+cf0.3 | blocks | 24 | 0 | 98.0 | 191.3 | 0.01 |
| outage45 | bridge60+cf0.3 | boulevard | 24 | 0 | 96.0 | 218.8 | 0.0073 |
| outage90 | bridge+cf0.3 | bayside | 24 | 0 | 109.0 | 52.2 | 0.0066 |
| outage90 | bridge+cf0.3 | blocks | 24 | 0 | 94.0 | 54.0 | 0.0092 |
| outage90 | bridge+cf0.3 | boulevard | 24 | 0 | 94.0 | 64.9 | 0.0093 |
| outage90 | bridge120+cf0.3 | bayside | 24 | 0 | 109.0 | 176.2 | 0.0115 |
| outage90 | bridge120+cf0.3 | blocks | 24 | 0 | 94.0 | 176.7 | 0.0085 |
| outage90 | bridge120+cf0.3 | boulevard | 24 | 0 | 94.0 | 178.3 | 0.0082 |
| outage90 | bridge60+cf0.3 | bayside | 24 | 0 | 109.0 | 112.2 | 0.0116 |
| outage90 | bridge60+cf0.3 | blocks | 24 | 0 | 94.0 | 112.8 | 0.0077 |
| outage90 | bridge60+cf0.3 | boulevard | 24 | 0 | 94.0 | 139.9 | 0.0066 |
| slip90 | bridge+cf0.3 | bayside | 24 | 0 | 109.0 | 52.2 | 0.0188 |
| slip90 | bridge+cf0.3 | blocks | 24 | 0 | 94.0 | 54.0 | 0.0156 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 0 | 94.0 | 64.9 | 0.0196 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 0 | 109.0 | 176.2 | 0.0248 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 0 | 94.0 | 176.7 | 0.0192 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 0 | 94.0 | 178.3 | 0.0218 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 0 | 109.0 | 112.2 | 0.0207 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 0 | 94.0 | 112.8 | 0.0195 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 0 | 94.0 | 139.9 | 0.0203 |

## Wheel slip spells

| profile | variant | course | missions | spells | mean abs slip |
|---|---|---|---|---|---|
| lie45 | bridge+cf0.3 | bayside | 24 | 15.0 | 0.0745 |
| lie45 | bridge+cf0.3 | blocks | 24 | 15.5 | 0.0765 |
| lie45 | bridge+cf0.3 | boulevard | 24 | 18.0 | 0.0742 |
| lie45 | bridge120+cf0.3 | bayside | 24 | 14.0 | 0.0737 |
| lie45 | bridge120+cf0.3 | blocks | 24 | 15.0 | 0.0764 |
| lie45 | bridge120+cf0.3 | boulevard | 24 | 17.0 | 0.0764 |
| lie45 | bridge60+cf0.3 | bayside | 24 | 14.0 | 0.0737 |
| lie45 | bridge60+cf0.3 | blocks | 24 | 15.0 | 0.0764 |
| lie45 | bridge60+cf0.3 | boulevard | 24 | 17.0 | 0.0764 |
| lie90 | bridge+cf0.3 | bayside | 24 | 15.0 | 0.0761 |
| lie90 | bridge+cf0.3 | blocks | 24 | 16.5 | 0.0765 |
| lie90 | bridge+cf0.3 | boulevard | 24 | 18.0 | 0.0739 |
| lie90 | bridge120+cf0.3 | bayside | 24 | 14.0 | 0.0737 |
| lie90 | bridge120+cf0.3 | blocks | 24 | 15.5 | 0.0765 |
| lie90 | bridge120+cf0.3 | boulevard | 24 | 17.0 | 0.0764 |
| lie90 | bridge60+cf0.3 | bayside | 24 | 14.5 | 0.0748 |
| lie90 | bridge60+cf0.3 | blocks | 24 | 16.0 | 0.0765 |
| lie90 | bridge60+cf0.3 | boulevard | 24 | 18.0 | 0.0756 |
| slip90 | bridge+cf0.3 | bayside | 24 | 14.5 | 0.0755 |
| slip90 | bridge+cf0.3 | blocks | 24 | 16.5 | 0.0765 |
| slip90 | bridge+cf0.3 | boulevard | 24 | 18.0 | 0.0739 |
| slip90 | bridge120+cf0.3 | bayside | 24 | 14.0 | 0.0737 |
| slip90 | bridge120+cf0.3 | blocks | 24 | 15.5 | 0.0765 |
| slip90 | bridge120+cf0.3 | boulevard | 24 | 17.0 | 0.0764 |
| slip90 | bridge60+cf0.3 | bayside | 24 | 14.0 | 0.0748 |
| slip90 | bridge60+cf0.3 | blocks | 24 | 16.0 | 0.0765 |
| slip90 | bridge60+cf0.3 | boulevard | 24 | 18.0 | 0.0756 |
