# Does bridging GPS outages still pay when the GPS wanders first? (simulated)

pace_j.py 0.1.0 (pace_i.py 0.1.0, rover_pilot.py 0.14.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every profile is pace_i.py's measured Mini+ with GPS outages of 15 s (after 150 s of sky on average) or 45 s (after 300 s), alone (outage15, outage45) or with the fixes drifting steadily away to 8 m off over the 20 s before each outage and back over the 20 s after it (wander15, wander45). Variants: cf0.3 (v0.14.0 on a real rover), bridge+cf0.3 (dead reckoning only while the GPS has no fresh fix; v0.15.0 on a real rover), dr+cf0.3 (v0.13.0 on a real rover). Seeds 109-132. 864 of 864 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_i.py's runs: 18 compared, 18 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage15 | cf0.3 | 72/72 | 0.806 | 0.907 | 72 | 1.005 | 0.082 |
| outage15 | bridge+cf0.3 | 72/72 | 0.87 | 0.979 | 72 | 1.008 | 0.006 |
| outage15 | dr+cf0.3 | 72/72 | 0.825 | 0.928 | 72 | 1.026 | 0.006 |
| wander15 | cf0.3 | 72/72 | 0.796 | 0.895 | 72 | 1.017 | 0.082 |
| wander15 | bridge+cf0.3 | 72/72 | 0.857 | 0.964 | 72 | 1.022 | 0.007 |
| wander15 | dr+cf0.3 | 72/72 | 0.819 | 0.921 | 72 | 1.034 | 0.006 |
| outage45 | cf0.3 | 72/72 | 0.769 | 0.865 | 46 | 1.005 | 0.121 |
| outage45 | bridge+cf0.3 | 72/72 | 0.824 | 0.927 | 72 | 1.007 | 0.057 |
| outage45 | dr+cf0.3 | 72/72 | 0.789 | 0.888 | 67 | 1.026 | 0.057 |
| wander45 | cf0.3 | 72/72 | 0.764 | 0.86 | 43 | 1.011 | 0.123 |
| wander45 | bridge+cf0.3 | 72/72 | 0.819 | 0.921 | 71 | 1.014 | 0.057 |
| wander45 | dr+cf0.3 | 72/72 | 0.786 | 0.885 | 64 | 1.028 | 0.056 |

## Pilots against v0.14.0's, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0767 |
| outage45 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0673 |
| wander15 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0698 |
| wander45 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0706 |
| outage15 | dr+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0644 |
| outage45 | dr+cf0.3 | cf0.3 | 1/3 | 0 | 0 | 0 | -0.052 |
| wander15 | dr+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.069 |
| wander45 | dr+cf0.3 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0578 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -117.0 | -0.0748 | 0.0 |
| outage15 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -128.0 | -0.0732 | 0.0 |
| outage15 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -147.0 | -0.0767 | 0.0 |
| outage45 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -111.0 | -0.0673 | 0.0 |
| outage45 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -118.0 | -0.0648 | 0.0 |
| outage45 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -134.0 | -0.0664 | 0.0 |
| wander15 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -108.0 | -0.0679 | 0.0 |
| wander15 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -108.0 | -0.0615 | 0.0 |
| wander15 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -136.0 | -0.0698 | 0.0 |
| wander45 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -111.0 | -0.0671 | 0.0 |
| wander45 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -111.0 | -0.0604 | 0.0 |
| wander45 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -143.0 | -0.0706 | 0.0 |
| outage15 | dr+cf0.3 | cf0.3 | bayside | 18 | 5 | -26.1 | -0.0167 | 0.0106 |
| outage15 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -112.6 | -0.0644 | 0.0 |
| outage15 | dr+cf0.3 | cf0.3 | boulevard | 20 | 4 | -30.2 | -0.0157 | 0.0015 |
| outage45 | dr+cf0.3 | cf0.3 | bayside | 16 | 8 | -28.9 | -0.0175 | 0.1516 |
| outage45 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -94.8 | -0.052 | 0.0 |
| outage45 | dr+cf0.3 | cf0.3 | boulevard | 16 | 8 | -26.8 | -0.0133 | 0.1516 |
| wander15 | dr+cf0.3 | cf0.3 | bayside | 19 | 5 | -32.7 | -0.0206 | 0.0066 |
| wander15 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -121.1 | -0.069 | 0.0 |
| wander15 | dr+cf0.3 | cf0.3 | boulevard | 20 | 3 | -52.0 | -0.0267 | 0.0005 |
| wander45 | dr+cf0.3 | cf0.3 | bayside | 15 | 8 | -24.0 | -0.0145 | 0.21 |
| wander45 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -106.2 | -0.0578 | 0.0 |
| wander45 | dr+cf0.3 | cf0.3 | boulevard | 17 | 6 | -43.0 | -0.0212 | 0.0347 |

## What wandering costs each pilot

Each variant with wandering fixes against itself on the same outages, paired by seed.

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| cf0.3 | wander15 | outage15 | 0/3 | 3 | 0 | 0 | 0.0134 |
| cf0.3 | wander45 | outage45 | 0/3 | 2 | 0 | 0 | 0.0074 |
| bridge+cf0.3 | wander15 | outage15 | 0/3 | 3 | 0 | 0 | 0.0147 |
| bridge+cf0.3 | wander45 | outage45 | 0/3 | 3 | 0 | 0 | 0.0064 |
| dr+cf0.3 | wander15 | outage15 | 0/3 | 3 | 0 | 0 | 0.0088 |
| dr+cf0.3 | wander45 | outage45 | 0/3 | 1 | 0 | 0 | 0.0025 |

| variant | profile | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| cf0.3 | wander15 | outage15 | bayside | 0 | 23 | 21.0 | 0.0134 | 0.0 |
| cf0.3 | wander15 | outage15 | blocks | 3 | 18 | 17.0 | 0.0097 | 0.0015 |
| cf0.3 | wander15 | outage15 | boulevard | 0 | 24 | 25.0 | 0.013 | 0.0 |
| cf0.3 | wander45 | outage45 | bayside | 0 | 21 | 9.0 | 0.0055 | 0.0 |
| cf0.3 | wander45 | outage45 | blocks | 6 | 16 | 7.0 | 0.0038 | 0.0525 |
| cf0.3 | wander45 | outage45 | boulevard | 0 | 23 | 15.0 | 0.0074 | 0.0 |
| bridge+cf0.3 | wander15 | outage15 | bayside | 0 | 23 | 20.0 | 0.0138 | 0.0 |
| bridge+cf0.3 | wander15 | outage15 | blocks | 2 | 20 | 23.0 | 0.0142 | 0.0001 |
| bridge+cf0.3 | wander15 | outage15 | boulevard | 0 | 24 | 26.0 | 0.0147 | 0.0 |
| bridge+cf0.3 | wander45 | outage45 | bayside | 1 | 18 | 7.0 | 0.0046 | 0.0001 |
| bridge+cf0.3 | wander45 | outage45 | blocks | 6 | 17 | 7.0 | 0.0041 | 0.0347 |
| bridge+cf0.3 | wander45 | outage45 | boulevard | 2 | 17 | 12.0 | 0.0064 | 0.0007 |
| dr+cf0.3 | wander15 | outage15 | bayside | 2 | 22 | 10.6 | 0.0069 | 0.0 |
| dr+cf0.3 | wander15 | outage15 | blocks | 6 | 17 | 14.4 | 0.0088 | 0.0347 |
| dr+cf0.3 | wander15 | outage15 | boulevard | 1 | 23 | 15.8 | 0.0084 | 0.0 |
| dr+cf0.3 | wander45 | outage45 | bayside | 4 | 18 | 4.1 | 0.0025 | 0.0043 |
| dr+cf0.3 | wander45 | outage45 | blocks | 10 | 13 | 0.4 | 0.0002 | 0.6776 |
| dr+cf0.3 | wander45 | outage45 | boulevard | 6 | 14 | 1.2 | 0.0006 | 0.1153 |

## GPS outages and wandering fixes

| profile | variant | course | missions | reports withheld | reports moved | s stood still |
|---|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 68.0 | 0.0 | 8.9 |
| outage15 | bridge+cf0.3 | blocks | 24 | 80.0 | 0.0 | 9.8 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 87.0 | 0.0 | 9.8 |
| outage15 | cf0.3 | bayside | 24 | 76.0 | 0.0 | 127.0 |
| outage15 | cf0.3 | blocks | 24 | 82.5 | 0.0 | 139.3 |
| outage15 | cf0.3 | boulevard | 24 | 93.5 | 0.0 | 158.1 |
| outage15 | dr+cf0.3 | bayside | 24 | 75.0 | 0.0 | 9.6 |
| outage15 | dr+cf0.3 | blocks | 24 | 80.0 | 0.0 | 12.4 |
| outage15 | dr+cf0.3 | boulevard | 24 | 93.5 | 0.0 | 9.6 |
| outage45 | bridge+cf0.3 | bayside | 24 | 112.0 | 0.0 | 86.4 |
| outage45 | bridge+cf0.3 | blocks | 24 | 113.0 | 0.0 | 95.6 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 133.5 | 0.0 | 106.6 |
| outage45 | cf0.3 | bayside | 24 | 112.5 | 0.0 | 213.2 |
| outage45 | cf0.3 | blocks | 24 | 113.0 | 0.0 | 214.8 |
| outage45 | cf0.3 | boulevard | 24 | 134.5 | 0.0 | 254.2 |
| outage45 | dr+cf0.3 | bayside | 24 | 112.5 | 0.0 | 90.8 |
| outage45 | dr+cf0.3 | blocks | 24 | 113.0 | 0.0 | 102.2 |
| outage45 | dr+cf0.3 | boulevard | 24 | 134.5 | 0.0 | 108.9 |
| wander15 | bridge+cf0.3 | bayside | 24 | 69.5 | 157.0 | 12.6 |
| wander15 | bridge+cf0.3 | blocks | 24 | 80.0 | 176.5 | 11.9 |
| wander15 | bridge+cf0.3 | boulevard | 24 | 89.0 | 193.5 | 9.8 |
| wander15 | cf0.3 | bayside | 24 | 80.0 | 173.5 | 132.9 |
| wander15 | cf0.3 | blocks | 24 | 86.0 | 185.0 | 144.8 |
| wander15 | cf0.3 | boulevard | 24 | 94.0 | 208.0 | 160.8 |
| wander15 | dr+cf0.3 | bayside | 24 | 76.0 | 168.0 | 12.6 |
| wander15 | dr+cf0.3 | blocks | 24 | 80.0 | 176.5 | 10.8 |
| wander15 | dr+cf0.3 | boulevard | 24 | 93.5 | 206.0 | 9.6 |
| wander45 | bridge+cf0.3 | bayside | 24 | 112.0 | 83.5 | 92.0 |
| wander45 | bridge+cf0.3 | blocks | 24 | 113.0 | 93.5 | 95.6 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 133.5 | 96.0 | 108.2 |
| wander45 | cf0.3 | bayside | 24 | 112.5 | 95.5 | 213.2 |
| wander45 | cf0.3 | blocks | 24 | 113.0 | 95.5 | 214.8 |
| wander45 | cf0.3 | boulevard | 24 | 134.5 | 104.0 | 254.2 |
| wander45 | dr+cf0.3 | bayside | 24 | 112.5 | 92.0 | 90.8 |
| wander45 | dr+cf0.3 | blocks | 24 | 113.0 | 95.5 | 103.1 |
| wander45 | dr+cf0.3 | boulevard | 24 | 134.5 | 104.0 | 104.8 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 0.0479 |
| outage15 | bridge+cf0.3 | blocks | 24 | 0.061 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 0.0454 |
| outage15 | cf0.3 | bayside | 24 | 0.0456 |
| outage15 | cf0.3 | blocks | 24 | 0.058 |
| outage15 | cf0.3 | boulevard | 24 | 0.0435 |
| outage15 | dr+cf0.3 | bayside | 24 | 0.2063 |
| outage15 | dr+cf0.3 | blocks | 24 | 0.2033 |
| outage15 | dr+cf0.3 | boulevard | 24 | 0.1968 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.046 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0.0596 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0.0442 |
| outage45 | cf0.3 | bayside | 24 | 0.0457 |
| outage45 | cf0.3 | blocks | 24 | 0.0586 |
| outage45 | cf0.3 | boulevard | 24 | 0.0437 |
| outage45 | dr+cf0.3 | bayside | 24 | 0.2086 |
| outage45 | dr+cf0.3 | blocks | 24 | 0.2076 |
| outage45 | dr+cf0.3 | boulevard | 24 | 0.2008 |
| wander15 | bridge+cf0.3 | bayside | 24 | 0.0505 |
| wander15 | bridge+cf0.3 | blocks | 24 | 0.0622 |
| wander15 | bridge+cf0.3 | boulevard | 24 | 0.0484 |
| wander15 | cf0.3 | bayside | 24 | 0.0487 |
| wander15 | cf0.3 | blocks | 24 | 0.0606 |
| wander15 | cf0.3 | boulevard | 24 | 0.0469 |
| wander15 | dr+cf0.3 | bayside | 24 | 0.205 |
| wander15 | dr+cf0.3 | blocks | 24 | 0.2031 |
| wander15 | dr+cf0.3 | boulevard | 24 | 0.193 |
| wander45 | bridge+cf0.3 | bayside | 24 | 0.0472 |
| wander45 | bridge+cf0.3 | blocks | 24 | 0.0607 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 0.0454 |
| wander45 | cf0.3 | bayside | 24 | 0.0476 |
| wander45 | cf0.3 | blocks | 24 | 0.0597 |
| wander45 | cf0.3 | boulevard | 24 | 0.0451 |
| wander45 | dr+cf0.3 | bayside | 24 | 0.2071 |
| wander45 | dr+cf0.3 | blocks | 24 | 0.2039 |
| wander45 | dr+cf0.3 | boulevard | 24 | 0.1941 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 6.54 | 9.67 |
| outage15 | bridge+cf0.3 | blocks | 24 | 6.46 | 9.61 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 6.6 | 9.94 |
| outage15 | cf0.3 | bayside | 24 | 6.71 | 8.61 |
| outage15 | cf0.3 | blocks | 24 | 6.53 | 8.54 |
| outage15 | cf0.3 | boulevard | 24 | 6.69 | 8.66 |
| outage15 | dr+cf0.3 | bayside | 24 | 2.74 | 6.57 |
| outage15 | dr+cf0.3 | blocks | 24 | 2.66 | 6.53 |
| outage15 | dr+cf0.3 | boulevard | 24 | 2.64 | 6.46 |
| outage45 | bridge+cf0.3 | bayside | 24 | 6.62 | 9.04 |
| outage45 | bridge+cf0.3 | blocks | 24 | 6.44 | 8.89 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 6.61 | 9.06 |
| outage45 | cf0.3 | bayside | 24 | 6.66 | 8.48 |
| outage45 | cf0.3 | blocks | 24 | 6.47 | 8.29 |
| outage45 | cf0.3 | boulevard | 24 | 6.63 | 8.46 |
| outage45 | dr+cf0.3 | bayside | 24 | 2.75 | 6.74 |
| outage45 | dr+cf0.3 | blocks | 24 | 2.73 | 6.7 |
| outage45 | dr+cf0.3 | boulevard | 24 | 2.68 | 6.58 |
| wander15 | bridge+cf0.3 | bayside | 24 | 6.76 | 12.8 |
| wander15 | bridge+cf0.3 | blocks | 24 | 6.66 | 12.93 |
| wander15 | bridge+cf0.3 | boulevard | 24 | 6.78 | 13.26 |
| wander15 | cf0.3 | bayside | 24 | 6.78 | 11.49 |
| wander15 | cf0.3 | blocks | 24 | 6.58 | 10.88 |
| wander15 | cf0.3 | boulevard | 24 | 6.74 | 11.43 |
| wander15 | dr+cf0.3 | bayside | 24 | 3.47 | 9.57 |
| wander15 | dr+cf0.3 | blocks | 24 | 3.39 | 9.61 |
| wander15 | dr+cf0.3 | boulevard | 24 | 3.37 | 9.6 |
| wander45 | bridge+cf0.3 | bayside | 24 | 6.74 | 11.04 |
| wander45 | bridge+cf0.3 | blocks | 24 | 6.58 | 11.53 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 6.71 | 11.71 |
| wander45 | cf0.3 | bayside | 24 | 6.67 | 9.49 |
| wander45 | cf0.3 | blocks | 24 | 6.53 | 9.32 |
| wander45 | cf0.3 | boulevard | 24 | 6.67 | 9.5 |
| wander45 | dr+cf0.3 | bayside | 24 | 3.21 | 9.07 |
| wander45 | dr+cf0.3 | blocks | 24 | 3.12 | 8.59 |
| wander45 | dr+cf0.3 | boulevard | 24 | 3.01 | 9.03 |

## Dead reckoning

| profile | variant | course | missions | never trusted | first trusted s | s on wheels alone | abs scale error |
|---|---|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 0 | 88.0 | 106.4 | 0.0072 |
| outage15 | bridge+cf0.3 | blocks | 24 | 0 | 88.0 | 125.2 | 0.0081 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 0 | 91.0 | 135.6 | 0.0073 |
| outage15 | dr+cf0.3 | bayside | 24 | 0 | 88.0 | 118.1 | 0.0466 |
| outage15 | dr+cf0.3 | blocks | 24 | 0 | 88.0 | 125.2 | 0.0457 |
| outage15 | dr+cf0.3 | boulevard | 24 | 0 | 91.0 | 149.0 | 0.0569 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0 | 95.0 | 115.1 | 0.0093 |
| outage45 | bridge+cf0.3 | blocks | 24 | 0 | 96.0 | 127.0 | 0.0096 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 0 | 95.0 | 127.0 | 0.0044 |
| outage45 | dr+cf0.3 | bayside | 24 | 0 | 95.0 | 126.0 | 0.0532 |
| outage45 | dr+cf0.3 | blocks | 24 | 0 | 96.0 | 127.0 | 0.0573 |
| outage45 | dr+cf0.3 | boulevard | 24 | 0 | 95.0 | 151.1 | 0.0368 |
| wander15 | bridge+cf0.3 | bayside | 24 | 0 | 106.0 | 107.5 | 0.0096 |
| wander15 | bridge+cf0.3 | blocks | 24 | 0 | 92.0 | 125.2 | 0.0149 |
| wander15 | bridge+cf0.3 | boulevard | 24 | 0 | 90.0 | 137.2 | 0.0107 |
| wander15 | dr+cf0.3 | bayside | 24 | 0 | 106.0 | 114.4 | 0.0686 |
| wander15 | dr+cf0.3 | blocks | 24 | 0 | 92.0 | 125.2 | 0.082 |
| wander15 | dr+cf0.3 | boulevard | 24 | 0 | 90.0 | 149.0 | 0.0685 |
| wander45 | bridge+cf0.3 | bayside | 24 | 0 | 95.0 | 126.0 | 0.0163 |
| wander45 | bridge+cf0.3 | blocks | 24 | 0 | 96.0 | 127.0 | 0.0142 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 0 | 95.0 | 127.0 | 0.0121 |
| wander45 | dr+cf0.3 | bayside | 24 | 0 | 95.0 | 126.0 | 0.0572 |
| wander45 | dr+cf0.3 | blocks | 24 | 0 | 96.0 | 127.0 | 0.0812 |
| wander45 | dr+cf0.3 | boulevard | 24 | 0 | 95.0 | 151.1 | 0.0723 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| outage15 | bridge+cf0.3 | bayside | 24 | 0.81 | 2.87 |
| outage15 | bridge+cf0.3 | blocks | 24 | 1.44 | 10.7 |
| outage15 | bridge+cf0.3 | boulevard | 24 | 1.89 | 5.55 |
| outage15 | cf0.3 | bayside | 24 | 0.69 | 2.13 |
| outage15 | cf0.3 | blocks | 24 | 1.33 | 10.21 |
| outage15 | cf0.3 | boulevard | 24 | 1.81 | 5.12 |
| outage15 | dr+cf0.3 | bayside | 24 | 0.78 | 2.73 |
| outage15 | dr+cf0.3 | blocks | 24 | 1.2 | 7.17 |
| outage15 | dr+cf0.3 | boulevard | 24 | 1.4 | 4.68 |
| outage45 | bridge+cf0.3 | bayside | 24 | 0.78 | 2.95 |
| outage45 | bridge+cf0.3 | blocks | 24 | 1.46 | 10.29 |
| outage45 | bridge+cf0.3 | boulevard | 24 | 1.95 | 5.4 |
| outage45 | cf0.3 | bayside | 24 | 0.71 | 2.12 |
| outage45 | cf0.3 | blocks | 24 | 1.27 | 10.27 |
| outage45 | cf0.3 | boulevard | 24 | 1.85 | 5.1 |
| outage45 | dr+cf0.3 | bayside | 24 | 0.87 | 2.73 |
| outage45 | dr+cf0.3 | blocks | 24 | 1.1 | 7.02 |
| outage45 | dr+cf0.3 | boulevard | 24 | 1.55 | 5.25 |
| wander15 | bridge+cf0.3 | bayside | 24 | 1.04 | 6.64 |
| wander15 | bridge+cf0.3 | blocks | 24 | 2.02 | 11.04 |
| wander15 | bridge+cf0.3 | boulevard | 24 | 2.28 | 8.34 |
| wander15 | cf0.3 | bayside | 24 | 0.95 | 5.5 |
| wander15 | cf0.3 | blocks | 24 | 1.76 | 10.16 |
| wander15 | cf0.3 | boulevard | 24 | 2.09 | 7.34 |
| wander15 | dr+cf0.3 | bayside | 24 | 1.08 | 5.55 |
| wander15 | dr+cf0.3 | blocks | 24 | 1.6 | 7.75 |
| wander15 | dr+cf0.3 | boulevard | 24 | 1.88 | 7.4 |
| wander45 | bridge+cf0.3 | bayside | 24 | 0.9 | 6.06 |
| wander45 | bridge+cf0.3 | blocks | 24 | 1.76 | 11.14 |
| wander45 | bridge+cf0.3 | boulevard | 24 | 2.05 | 7.17 |
| wander45 | cf0.3 | bayside | 24 | 0.78 | 4.37 |
| wander45 | cf0.3 | blocks | 24 | 1.52 | 10.18 |
| wander45 | cf0.3 | boulevard | 24 | 1.75 | 5.81 |
| wander45 | dr+cf0.3 | bayside | 24 | 0.89 | 5.71 |
| wander45 | dr+cf0.3 | blocks | 24 | 1.37 | 8.03 |
| wander45 | dr+cf0.3 | boulevard | 24 | 1.65 | 6.21 |
