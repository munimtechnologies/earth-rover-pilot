# Should dead reckoning stay on by default? (simulated)

pace_h.py 0.1.0 (pace_g.py 0.1.0, rover_pilot.py 0.13.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every profile is pace_g.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, GPS every 2 s and 1.5 s late, 3 deg of compass noise, a -25 deg compass error to learn, wheels reporting RPM), with 8 deg of noise, 30% of GPS fixes missing, or both. Variants: dr+cf0.3 (v0.13.0 on a real rover), cf0.3 (--smooth-heading only), bridge+cf0.3 (dead reckoning only through GPS gaps), drg0.3+cf0.3 (dead reckoning moved 0.3 of the way to each fix), dr+cf0.3+kb (v0.13.0 with the compass bias known from the start). Seeds 61-84. 1440 of 1440 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_g.py's runs: 36 compared, 36 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| measured | dr+cf0.3 | 72/72 | 0.828 | 0.932 | 72 | 1.025 | 0.001 |
| measured | cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.005 | 0.002 |
| measured | bridge+cf0.3 | 72/72 | 0.879 | 0.989 | 72 | 1.005 | 0.001 |
| measured | drg0.3+cf0.3 | 72/72 | 0.864 | 0.971 | 72 | 1.013 | 0.001 |
| measured | dr+cf0.3+kb | 72/72 | 0.827 | 0.93 | 72 | 1.025 | 0.001 |
| noise8 | dr+cf0.3 | 72/72 | 0.833 | 0.937 | 72 | 1.021 | 0.001 |
| noise8 | cf0.3 | 72/72 | 0.875 | 0.985 | 72 | 1.006 | 0.002 |
| noise8 | bridge+cf0.3 | 72/72 | 0.877 | 0.986 | 72 | 1.006 | 0.001 |
| noise8 | drg0.3+cf0.3 | 72/72 | 0.862 | 0.97 | 72 | 1.014 | 0.001 |
| noise8 | dr+cf0.3+kb | 72/72 | 0.824 | 0.927 | 72 | 1.026 | 0.001 |
| dropout0.3 | dr+cf0.3 | 72/72 | 0.832 | 0.936 | 72 | 1.026 | 0.005 |
| dropout0.3 | cf0.3 | 72/72 | 0.822 | 0.924 | 72 | 1.007 | 0.058 |
| dropout0.3 | bridge+cf0.3 | 72/72 | 0.869 | 0.978 | 72 | 1.009 | 0.005 |
| dropout0.3 | drg0.3+cf0.3 | 72/72 | 0.863 | 0.971 | 72 | 1.013 | 0.005 |
| dropout0.3 | dr+cf0.3+kb | 72/72 | 0.832 | 0.936 | 72 | 1.027 | 0.004 |
| dropout0.3-noise8 | dr+cf0.3 | 72/72 | 0.835 | 0.94 | 72 | 1.026 | 0.005 |
| dropout0.3-noise8 | cf0.3 | 72/72 | 0.82 | 0.922 | 72 | 1.01 | 0.058 |
| dropout0.3-noise8 | bridge+cf0.3 | 72/72 | 0.867 | 0.975 | 72 | 1.011 | 0.004 |
| dropout0.3-noise8 | drg0.3+cf0.3 | 72/72 | 0.861 | 0.968 | 72 | 1.015 | 0.005 |
| dropout0.3-noise8 | dr+cf0.3+kb | 72/72 | 0.828 | 0.932 | 72 | 1.029 | 0.004 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| measured | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0668 |
| noise8 | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0607 |
| dropout0.3 | dr+cf0.3 | cf0.3 | 1/3 | 0 | 0 | 0 | -0.06 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | 1/3 | 0 | 0 | 0 | -0.0678 |
| measured | bridge+cf0.3 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0006 |
| noise8 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0014 |
| dropout0.3 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0536 |
| dropout0.3-noise8 | bridge+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0541 |
| measured | bridge+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0625 |
| noise8 | bridge+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0579 |
| dropout0.3 | bridge+cf0.3 | dr+cf0.3 | 2/3 | 0 | 0 | 0 | -0.0539 |
| dropout0.3-noise8 | bridge+cf0.3 | dr+cf0.3 | 2/3 | 1 | 0 | 0 | -0.047 |
| measured | drg0.3+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0443 |
| noise8 | drg0.3+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0403 |
| dropout0.3 | drg0.3+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0393 |
| dropout0.3-noise8 | drg0.3+cf0.3 | dr+cf0.3 | 3/3 | 0 | 0 | 0 | -0.0332 |
| measured | drg0.3+cf0.3 | cf0.3 | 1/3 | 2 | 0 | 0 | 0.0216 |
| noise8 | drg0.3+cf0.3 | cf0.3 | 1/3 | 2 | 0 | 0 | 0.0218 |
| dropout0.3 | drg0.3+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.085 |
| dropout0.3-noise8 | drg0.3+cf0.3 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0819 |
| measured | dr+cf0.3+kb | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0696 |
| noise8 | dr+cf0.3+kb | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0689 |
| dropout0.3 | dr+cf0.3+kb | cf0.3 | 1/3 | 0 | 0 | 0 | -0.0628 |
| dropout0.3-noise8 | dr+cf0.3+kb | cf0.3 | 1/3 | 0 | 0 | 0 | -0.0633 |
| measured | dr+cf0.3+kb | dr+cf0.3 | 0/3 | 1 | 0 | 0 | 0.0035 |
| noise8 | dr+cf0.3+kb | dr+cf0.3 | 0/3 | 2 | 0 | 0 | 0.0091 |
| dropout0.3 | dr+cf0.3+kb | dr+cf0.3 | 0/3 | 0 | 0 | 0 | 0.0024 |
| dropout0.3-noise8 | dr+cf0.3+kb | dr+cf0.3 | 0/3 | 2 | 0 | 0 | 0.0052 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| measured | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 96.0 | 0.0668 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | blocks | 0 | 24 | 20.0 | 0.0124 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 114.0 | 0.0647 | 0.0 |
| noise8 | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 87.5 | 0.0607 | 0.0 |
| noise8 | dr+cf0.3 | cf0.3 | blocks | 6 | 18 | 15.6 | 0.0097 | 0.0227 |
| noise8 | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 107.0 | 0.0606 | 0.0 |
| dropout0.3 | dr+cf0.3 | cf0.3 | bayside | 15 | 9 | -7.4 | -0.0049 | 0.3075 |
| dropout0.3 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -104.1 | -0.06 | 0.0 |
| dropout0.3 | dr+cf0.3 | cf0.3 | boulevard | 9 | 13 | 3.4 | 0.0018 | 0.5235 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | bayside | 17 | 7 | -15.4 | -0.01 | 0.0639 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -117.8 | -0.0678 | 0.0 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | boulevard | 12 | 11 | -1.0 | -0.0005 | 1.0 |
| measured | bridge+cf0.3 | cf0.3 | bayside | 8 | 0 | 0.0 | 0.0 | 0.0078 |
| measured | bridge+cf0.3 | cf0.3 | blocks | 6 | 3 | 0.0 | 0.0 | 0.5078 |
| measured | bridge+cf0.3 | cf0.3 | boulevard | 12 | 0 | -1.0 | -0.0006 | 0.0005 |
| noise8 | bridge+cf0.3 | cf0.3 | bayside | 13 | 0 | -2.0 | -0.0014 | 0.0002 |
| noise8 | bridge+cf0.3 | cf0.3 | blocks | 10 | 1 | 0.0 | 0.0 | 0.0117 |
| noise8 | bridge+cf0.3 | cf0.3 | boulevard | 10 | 0 | 0.0 | 0.0 | 0.002 |
| dropout0.3 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -75.0 | -0.0492 | 0.0 |
| dropout0.3 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -93.0 | -0.0536 | 0.0 |
| dropout0.3 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -90.0 | -0.0483 | 0.0 |
| dropout0.3-noise8 | bridge+cf0.3 | cf0.3 | bayside | 24 | 0 | -78.0 | -0.0509 | 0.0 |
| dropout0.3-noise8 | bridge+cf0.3 | cf0.3 | blocks | 24 | 0 | -94.0 | -0.0541 | 0.0 |
| dropout0.3-noise8 | bridge+cf0.3 | cf0.3 | boulevard | 24 | 0 | -93.0 | -0.0497 | 0.0 |
| measured | bridge+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -96.0 | -0.0625 | 0.0 |
| measured | bridge+cf0.3 | dr+cf0.3 | blocks | 24 | 0 | -20.0 | -0.0123 | 0.0 |
| measured | bridge+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -116.0 | -0.0618 | 0.0 |
| noise8 | bridge+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -88.5 | -0.0579 | 0.0 |
| noise8 | bridge+cf0.3 | dr+cf0.3 | blocks | 18 | 5 | -15.6 | -0.0096 | 0.0106 |
| noise8 | bridge+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -107.0 | -0.0571 | 0.0 |
| dropout0.3 | bridge+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -72.1 | -0.0474 | 0.0 |
| dropout0.3 | bridge+cf0.3 | dr+cf0.3 | blocks | 6 | 15 | 7.0 | 0.0043 | 0.0784 |
| dropout0.3 | bridge+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -101.0 | -0.0539 | 0.0 |
| dropout0.3-noise8 | bridge+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -62.8 | -0.0414 | 0.0 |
| dropout0.3-noise8 | bridge+cf0.3 | dr+cf0.3 | blocks | 3 | 21 | 20.4 | 0.0126 | 0.0003 |
| dropout0.3-noise8 | bridge+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -88.0 | -0.047 | 0.0 |
| measured | drg0.3+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -68.0 | -0.0443 | 0.0 |
| measured | drg0.3+cf0.3 | dr+cf0.3 | blocks | 24 | 0 | -43.2 | -0.0265 | 0.0 |
| measured | drg0.3+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -76.3 | -0.0407 | 0.0 |
| noise8 | drg0.3+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -61.5 | -0.0403 | 0.0 |
| noise8 | drg0.3+cf0.3 | dr+cf0.3 | blocks | 24 | 0 | -38.6 | -0.0238 | 0.0 |
| noise8 | drg0.3+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -69.8 | -0.0373 | 0.0 |
| dropout0.3 | drg0.3+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -56.6 | -0.0372 | 0.0 |
| dropout0.3 | drg0.3+cf0.3 | dr+cf0.3 | blocks | 24 | 0 | -39.4 | -0.0242 | 0.0 |
| dropout0.3 | drg0.3+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -73.6 | -0.0393 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | dr+cf0.3 | bayside | 24 | 0 | -48.0 | -0.0316 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | dr+cf0.3 | blocks | 23 | 1 | -28.1 | -0.0173 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | dr+cf0.3 | boulevard | 24 | 0 | -62.2 | -0.0332 | 0.0 |
| measured | drg0.3+cf0.3 | cf0.3 | bayside | 0 | 24 | 30.0 | 0.0209 | 0.0 |
| measured | drg0.3+cf0.3 | cf0.3 | blocks | 24 | 0 | -22.0 | -0.0137 | 0.0 |
| measured | drg0.3+cf0.3 | cf0.3 | boulevard | 0 | 24 | 38.0 | 0.0216 | 0.0 |
| noise8 | drg0.3+cf0.3 | cf0.3 | bayside | 0 | 24 | 25.8 | 0.0179 | 0.0 |
| noise8 | drg0.3+cf0.3 | cf0.3 | blocks | 24 | 0 | -21.5 | -0.0133 | 0.0 |
| noise8 | drg0.3+cf0.3 | cf0.3 | boulevard | 0 | 24 | 38.5 | 0.0218 | 0.0 |
| dropout0.3 | drg0.3+cf0.3 | cf0.3 | bayside | 24 | 0 | -57.3 | -0.0376 | 0.0 |
| dropout0.3 | drg0.3+cf0.3 | cf0.3 | blocks | 24 | 0 | -147.5 | -0.085 | 0.0 |
| dropout0.3 | drg0.3+cf0.3 | cf0.3 | boulevard | 24 | 0 | -67.2 | -0.0361 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | cf0.3 | bayside | 24 | 0 | -66.3 | -0.0432 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | cf0.3 | blocks | 24 | 0 | -142.3 | -0.0819 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | cf0.3 | boulevard | 24 | 0 | -67.2 | -0.0359 | 0.0 |
| measured | dr+cf0.3+kb | cf0.3 | bayside | 0 | 24 | 98.0 | 0.0682 | 0.0 |
| measured | dr+cf0.3+kb | cf0.3 | blocks | 0 | 24 | 25.1 | 0.0156 | 0.0 |
| measured | dr+cf0.3+kb | cf0.3 | boulevard | 0 | 24 | 122.6 | 0.0696 | 0.0 |
| noise8 | dr+cf0.3+kb | cf0.3 | bayside | 0 | 24 | 97.6 | 0.0677 | 0.0 |
| noise8 | dr+cf0.3+kb | cf0.3 | blocks | 0 | 24 | 23.4 | 0.0145 | 0.0 |
| noise8 | dr+cf0.3+kb | cf0.3 | boulevard | 0 | 24 | 121.5 | 0.0689 | 0.0 |
| dropout0.3 | dr+cf0.3+kb | cf0.3 | bayside | 13 | 11 | -2.8 | -0.0018 | 0.8388 |
| dropout0.3 | dr+cf0.3+kb | cf0.3 | blocks | 24 | 0 | -109.0 | -0.0628 | 0.0 |
| dropout0.3 | dr+cf0.3+kb | cf0.3 | boulevard | 10 | 14 | 9.0 | 0.0048 | 0.5413 |
| dropout0.3-noise8 | dr+cf0.3+kb | cf0.3 | bayside | 11 | 11 | 0.0 | 0.0 | 1.0 |
| dropout0.3-noise8 | dr+cf0.3+kb | cf0.3 | blocks | 24 | 0 | -110.0 | -0.0633 | 0.0 |
| dropout0.3-noise8 | dr+cf0.3+kb | cf0.3 | boulevard | 9 | 14 | 14.8 | 0.0079 | 0.4049 |
| measured | dr+cf0.3+kb | dr+cf0.3 | bayside | 11 | 12 | 0.4 | 0.0003 | 1.0 |
| measured | dr+cf0.3+kb | dr+cf0.3 | blocks | 8 | 14 | 2.0 | 0.0012 | 0.2863 |
| measured | dr+cf0.3+kb | dr+cf0.3 | boulevard | 4 | 17 | 6.5 | 0.0035 | 0.0072 |
| noise8 | dr+cf0.3+kb | dr+cf0.3 | bayside | 5 | 18 | 10.7 | 0.007 | 0.0106 |
| noise8 | dr+cf0.3+kb | dr+cf0.3 | blocks | 6 | 16 | 12.4 | 0.0076 | 0.0525 |
| noise8 | dr+cf0.3+kb | dr+cf0.3 | boulevard | 3 | 21 | 17.0 | 0.0091 | 0.0003 |
| dropout0.3 | dr+cf0.3+kb | dr+cf0.3 | bayside | 9 | 14 | 3.6 | 0.0024 | 0.4049 |
| dropout0.3 | dr+cf0.3+kb | dr+cf0.3 | blocks | 12 | 10 | -0.0 | -0.0 | 0.8318 |
| dropout0.3 | dr+cf0.3+kb | dr+cf0.3 | boulevard | 9 | 12 | 0.1 | 0.0001 | 0.6636 |
| dropout0.3-noise8 | dr+cf0.3+kb | dr+cf0.3 | bayside | 5 | 18 | 6.5 | 0.0043 | 0.0106 |
| dropout0.3-noise8 | dr+cf0.3+kb | dr+cf0.3 | blocks | 9 | 13 | 1.3 | 0.0008 | 0.5235 |
| dropout0.3-noise8 | dr+cf0.3+kb | dr+cf0.3 | boulevard | 4 | 17 | 9.8 | 0.0052 | 0.0072 |

## How hard the pilot steers

Median over the completed missions of each mission's mean |angular| applied while driving forward.

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| dropout0.3 | bridge+cf0.3 | bayside | 24 | 0.0548 |
| dropout0.3 | bridge+cf0.3 | blocks | 24 | 0.0698 |
| dropout0.3 | bridge+cf0.3 | boulevard | 24 | 0.0518 |
| dropout0.3 | cf0.3 | bayside | 24 | 0.0414 |
| dropout0.3 | cf0.3 | blocks | 24 | 0.0563 |
| dropout0.3 | cf0.3 | boulevard | 24 | 0.0393 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 0.1744 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 0.1836 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 0.1742 |
| dropout0.3 | dr+cf0.3+kb | bayside | 24 | 0.1817 |
| dropout0.3 | dr+cf0.3+kb | blocks | 24 | 0.185 |
| dropout0.3 | dr+cf0.3+kb | boulevard | 24 | 0.178 |
| dropout0.3 | drg0.3+cf0.3 | bayside | 24 | 0.0978 |
| dropout0.3 | drg0.3+cf0.3 | blocks | 24 | 0.1041 |
| dropout0.3 | drg0.3+cf0.3 | boulevard | 24 | 0.095 |
| dropout0.3-noise8 | bridge+cf0.3 | bayside | 24 | 0.0741 |
| dropout0.3-noise8 | bridge+cf0.3 | blocks | 24 | 0.0877 |
| dropout0.3-noise8 | bridge+cf0.3 | boulevard | 24 | 0.0707 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 0.0614 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 0.0759 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 0.0597 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 0.1789 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 0.1809 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 0.1745 |
| dropout0.3-noise8 | dr+cf0.3+kb | bayside | 24 | 0.188 |
| dropout0.3-noise8 | dr+cf0.3+kb | blocks | 24 | 0.1939 |
| dropout0.3-noise8 | dr+cf0.3+kb | boulevard | 24 | 0.1879 |
| dropout0.3-noise8 | drg0.3+cf0.3 | bayside | 24 | 0.1084 |
| dropout0.3-noise8 | drg0.3+cf0.3 | blocks | 24 | 0.1169 |
| dropout0.3-noise8 | drg0.3+cf0.3 | boulevard | 24 | 0.1067 |
| measured | bridge+cf0.3 | bayside | 24 | 0.0463 |
| measured | bridge+cf0.3 | blocks | 24 | 0.0592 |
| measured | bridge+cf0.3 | boulevard | 24 | 0.0445 |
| measured | cf0.3 | bayside | 24 | 0.0461 |
| measured | cf0.3 | blocks | 24 | 0.0589 |
| measured | cf0.3 | boulevard | 24 | 0.044 |
| measured | dr+cf0.3 | bayside | 24 | 0.2233 |
| measured | dr+cf0.3 | blocks | 24 | 0.2237 |
| measured | dr+cf0.3 | boulevard | 24 | 0.2086 |
| measured | dr+cf0.3+kb | bayside | 24 | 0.2269 |
| measured | dr+cf0.3+kb | blocks | 24 | 0.2306 |
| measured | dr+cf0.3+kb | boulevard | 24 | 0.2191 |
| measured | drg0.3+cf0.3 | bayside | 24 | 0.1262 |
| measured | drg0.3+cf0.3 | blocks | 24 | 0.13 |
| measured | drg0.3+cf0.3 | boulevard | 24 | 0.1195 |
| noise8 | bridge+cf0.3 | bayside | 24 | 0.0643 |
| noise8 | bridge+cf0.3 | blocks | 24 | 0.0763 |
| noise8 | bridge+cf0.3 | boulevard | 24 | 0.0626 |
| noise8 | cf0.3 | bayside | 24 | 0.0635 |
| noise8 | cf0.3 | blocks | 24 | 0.076 |
| noise8 | cf0.3 | boulevard | 24 | 0.0624 |
| noise8 | dr+cf0.3 | bayside | 24 | 0.2191 |
| noise8 | dr+cf0.3 | blocks | 24 | 0.2239 |
| noise8 | dr+cf0.3 | boulevard | 24 | 0.207 |
| noise8 | dr+cf0.3+kb | bayside | 24 | 0.2314 |
| noise8 | dr+cf0.3+kb | blocks | 24 | 0.2344 |
| noise8 | dr+cf0.3+kb | boulevard | 24 | 0.2241 |
| noise8 | drg0.3+cf0.3 | bayside | 24 | 0.129 |
| noise8 | drg0.3+cf0.3 | blocks | 24 | 0.1336 |
| noise8 | drg0.3+cf0.3 | boulevard | 24 | 0.1252 |

## The compass-bias learner

| profile | variant | course | missions | median calibrations | median breaks | median abs bias error deg |
|---|---|---|---|---|---|---|
| dropout0.3 | bridge+cf0.3 | bayside | 24 | 38.5 | 135.0 | 2.72 |
| dropout0.3 | bridge+cf0.3 | blocks | 24 | 38.0 | 176.5 | 2.13 |
| dropout0.3 | bridge+cf0.3 | boulevard | 24 | 56.0 | 141.5 | 2.49 |
| dropout0.3 | cf0.3 | bayside | 24 | 37.0 | 131.0 | 2.14 |
| dropout0.3 | cf0.3 | blocks | 24 | 36.0 | 175.0 | 3.78 |
| dropout0.3 | cf0.3 | boulevard | 24 | 52.5 | 140.5 | 2.65 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 2.0 | 389.0 | 5.09 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 2.0 | 418.5 | 4.0 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 2.0 | 476.0 | 4.09 |
| dropout0.3 | dr+cf0.3+kb | bayside | 24 | 1.5 | 388.0 | 1.54 |
| dropout0.3 | dr+cf0.3+kb | blocks | 24 | 2.0 | 418.0 | 1.46 |
| dropout0.3 | dr+cf0.3+kb | boulevard | 24 | 2.0 | 474.5 | 1.54 |
| dropout0.3 | drg0.3+cf0.3 | bayside | 24 | 4.5 | 283.5 | 3.66 |
| dropout0.3 | drg0.3+cf0.3 | blocks | 24 | 4.0 | 307.0 | 1.98 |
| dropout0.3 | drg0.3+cf0.3 | boulevard | 24 | 6.0 | 343.0 | 2.52 |
| dropout0.3-noise8 | bridge+cf0.3 | bayside | 24 | 14.0 | 226.0 | 1.81 |
| dropout0.3-noise8 | bridge+cf0.3 | blocks | 24 | 15.0 | 273.0 | 2.49 |
| dropout0.3-noise8 | bridge+cf0.3 | boulevard | 24 | 21.5 | 257.5 | 2.25 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 14.0 | 230.0 | 2.46 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 14.0 | 278.5 | 2.25 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 21.0 | 267.0 | 1.98 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 1.0 | 434.5 | 18.05 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 1.0 | 464.5 | 15.87 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 1.0 | 535.5 | 15.65 |
| dropout0.3-noise8 | dr+cf0.3+kb | bayside | 24 | 1.0 | 433.5 | 1.01 |
| dropout0.3-noise8 | dr+cf0.3+kb | blocks | 24 | 0.0 | 462.0 | 0.0 |
| dropout0.3-noise8 | dr+cf0.3+kb | boulevard | 24 | 0.0 | 529.5 | 0.0 |
| dropout0.3-noise8 | drg0.3+cf0.3 | bayside | 24 | 1.0 | 364.5 | 11.37 |
| dropout0.3-noise8 | drg0.3+cf0.3 | blocks | 24 | 1.0 | 387.5 | 6.45 |
| dropout0.3-noise8 | drg0.3+cf0.3 | boulevard | 24 | 1.0 | 444.0 | 6.53 |
| measured | bridge+cf0.3 | bayside | 24 | 60.5 | 98.0 | 1.68 |
| measured | bridge+cf0.3 | blocks | 24 | 60.0 | 127.0 | 1.77 |
| measured | bridge+cf0.3 | boulevard | 24 | 82.0 | 98.5 | 3.6 |
| measured | cf0.3 | bayside | 24 | 59.0 | 97.5 | 2.31 |
| measured | cf0.3 | blocks | 24 | 61.5 | 129.5 | 2.5 |
| measured | cf0.3 | boulevard | 24 | 82.5 | 98.0 | 2.98 |
| measured | dr+cf0.3 | bayside | 24 | 3.0 | 477.0 | 3.46 |
| measured | dr+cf0.3 | blocks | 24 | 2.5 | 505.5 | 3.52 |
| measured | dr+cf0.3 | boulevard | 24 | 3.0 | 588.0 | 4.26 |
| measured | dr+cf0.3+kb | bayside | 24 | 2.0 | 483.0 | 2.02 |
| measured | dr+cf0.3+kb | blocks | 24 | 2.0 | 510.5 | 2.16 |
| measured | dr+cf0.3+kb | boulevard | 24 | 2.0 | 594.5 | 2.29 |
| measured | drg0.3+cf0.3 | bayside | 24 | 3.5 | 371.5 | 3.49 |
| measured | drg0.3+cf0.3 | blocks | 24 | 4.0 | 393.5 | 4.27 |
| measured | drg0.3+cf0.3 | boulevard | 24 | 4.0 | 443.5 | 4.03 |
| noise8 | bridge+cf0.3 | bayside | 24 | 25.0 | 200.5 | 2.18 |
| noise8 | bridge+cf0.3 | blocks | 24 | 24.0 | 240.5 | 3.43 |
| noise8 | bridge+cf0.3 | boulevard | 24 | 33.5 | 236.5 | 3.05 |
| noise8 | cf0.3 | bayside | 24 | 24.0 | 203.0 | 2.07 |
| noise8 | cf0.3 | blocks | 24 | 23.5 | 241.0 | 3.02 |
| noise8 | cf0.3 | boulevard | 24 | 32.0 | 236.0 | 3.36 |
| noise8 | dr+cf0.3 | bayside | 24 | 1.0 | 507.5 | 10.84 |
| noise8 | dr+cf0.3 | blocks | 24 | 1.0 | 539.5 | 13.27 |
| noise8 | dr+cf0.3 | boulevard | 24 | 1.0 | 627.5 | 16.89 |
| noise8 | dr+cf0.3+kb | bayside | 24 | 0.5 | 511.0 | 0.03 |
| noise8 | dr+cf0.3+kb | blocks | 24 | 1.0 | 541.0 | 1.28 |
| noise8 | dr+cf0.3+kb | boulevard | 24 | 0.5 | 625.5 | 0.07 |
| noise8 | drg0.3+cf0.3 | bayside | 24 | 1.0 | 416.0 | 10.77 |
| noise8 | drg0.3+cf0.3 | blocks | 24 | 1.0 | 446.0 | 10.49 |
| noise8 | drg0.3+cf0.3 | boulevard | 24 | 1.0 | 512.0 | 7.59 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| dropout0.3 | bridge+cf0.3 | bayside | 24 | 8.09 | 11.39 |
| dropout0.3 | bridge+cf0.3 | blocks | 24 | 7.86 | 11.17 |
| dropout0.3 | bridge+cf0.3 | boulevard | 24 | 8.14 | 11.52 |
| dropout0.3 | cf0.3 | bayside | 24 | 8.07 | 10.75 |
| dropout0.3 | cf0.3 | blocks | 24 | 7.77 | 10.59 |
| dropout0.3 | cf0.3 | boulevard | 24 | 8.04 | 10.82 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 2.63 | 7.1 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 2.68 | 7.06 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 2.61 | 6.92 |
| dropout0.3 | dr+cf0.3+kb | bayside | 24 | 2.56 | 6.88 |
| dropout0.3 | dr+cf0.3+kb | blocks | 24 | 2.59 | 6.71 |
| dropout0.3 | dr+cf0.3+kb | boulevard | 24 | 2.55 | 6.54 |
| dropout0.3 | drg0.3+cf0.3 | bayside | 24 | 2.91 | 6.88 |
| dropout0.3 | drg0.3+cf0.3 | blocks | 24 | 2.87 | 6.79 |
| dropout0.3 | drg0.3+cf0.3 | boulevard | 24 | 2.75 | 6.5 |
| dropout0.3-noise8 | bridge+cf0.3 | bayside | 24 | 8.05 | 11.31 |
| dropout0.3-noise8 | bridge+cf0.3 | blocks | 24 | 7.82 | 11.09 |
| dropout0.3-noise8 | bridge+cf0.3 | boulevard | 24 | 8.11 | 11.39 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 8.04 | 10.73 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 7.75 | 10.56 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 8.03 | 10.83 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 2.64 | 7.05 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 2.68 | 7.06 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 2.68 | 6.96 |
| dropout0.3-noise8 | dr+cf0.3+kb | bayside | 24 | 2.59 | 6.93 |
| dropout0.3-noise8 | dr+cf0.3+kb | blocks | 24 | 2.6 | 6.67 |
| dropout0.3-noise8 | dr+cf0.3+kb | boulevard | 24 | 2.56 | 6.69 |
| dropout0.3-noise8 | drg0.3+cf0.3 | bayside | 24 | 2.94 | 6.87 |
| dropout0.3-noise8 | drg0.3+cf0.3 | blocks | 24 | 2.9 | 6.96 |
| dropout0.3-noise8 | drg0.3+cf0.3 | boulevard | 24 | 2.85 | 6.68 |
| measured | bridge+cf0.3 | bayside | 24 | 6.43 | 8.18 |
| measured | bridge+cf0.3 | blocks | 24 | 6.41 | 8.16 |
| measured | bridge+cf0.3 | boulevard | 24 | 6.58 | 8.3 |
| measured | cf0.3 | bayside | 24 | 6.47 | 8.2 |
| measured | cf0.3 | blocks | 24 | 6.42 | 8.18 |
| measured | cf0.3 | boulevard | 24 | 6.6 | 8.3 |
| measured | dr+cf0.3 | bayside | 24 | 2.64 | 6.59 |
| measured | dr+cf0.3 | blocks | 24 | 2.6 | 6.42 |
| measured | dr+cf0.3 | boulevard | 24 | 2.55 | 6.42 |
| measured | dr+cf0.3+kb | bayside | 24 | 2.62 | 6.33 |
| measured | dr+cf0.3+kb | blocks | 24 | 2.62 | 6.37 |
| measured | dr+cf0.3+kb | boulevard | 24 | 2.56 | 6.26 |
| measured | drg0.3+cf0.3 | bayside | 24 | 3.01 | 6.56 |
| measured | drg0.3+cf0.3 | blocks | 24 | 3.02 | 6.42 |
| measured | drg0.3+cf0.3 | boulevard | 24 | 2.95 | 6.36 |
| noise8 | bridge+cf0.3 | bayside | 24 | 6.42 | 8.17 |
| noise8 | bridge+cf0.3 | blocks | 24 | 6.39 | 8.14 |
| noise8 | bridge+cf0.3 | boulevard | 24 | 6.56 | 8.27 |
| noise8 | cf0.3 | bayside | 24 | 6.47 | 8.21 |
| noise8 | cf0.3 | blocks | 24 | 6.42 | 8.16 |
| noise8 | cf0.3 | boulevard | 24 | 6.59 | 8.3 |
| noise8 | dr+cf0.3 | bayside | 24 | 2.65 | 6.5 |
| noise8 | dr+cf0.3 | blocks | 24 | 2.63 | 6.42 |
| noise8 | dr+cf0.3 | boulevard | 24 | 2.58 | 6.45 |
| noise8 | dr+cf0.3+kb | bayside | 24 | 2.62 | 6.39 |
| noise8 | dr+cf0.3+kb | blocks | 24 | 2.6 | 6.38 |
| noise8 | dr+cf0.3+kb | boulevard | 24 | 2.55 | 6.26 |
| noise8 | drg0.3+cf0.3 | bayside | 24 | 3.04 | 6.42 |
| noise8 | drg0.3+cf0.3 | blocks | 24 | 2.92 | 6.38 |
| noise8 | drg0.3+cf0.3 | boulevard | 24 | 2.86 | 6.3 |

## Dead reckoning

| profile | variant | course | missions | never trusted | first trusted s | s on wheels alone | abs scale error |
|---|---|---|---|---|---|---|---|
| dropout0.3 | bridge+cf0.3 | bayside | 24 | 0 | 90.0 | 77.9 | 0.0116 |
| dropout0.3 | bridge+cf0.3 | blocks | 24 | 0 | 92.0 | 89.0 | 0.0124 |
| dropout0.3 | bridge+cf0.3 | boulevard | 24 | 0 | 91.0 | 97.5 | 0.0101 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 0 | 90.0 | 82.7 | 0.0511 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 0 | 92.0 | 88.3 | 0.068 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 0 | 91.0 | 100.0 | 0.069 |
| dropout0.3 | dr+cf0.3+kb | bayside | 24 | 0 | 65.0 | 83.2 | 0.0588 |
| dropout0.3 | dr+cf0.3+kb | blocks | 24 | 0 | 61.0 | 88.3 | 0.0475 |
| dropout0.3 | dr+cf0.3+kb | boulevard | 24 | 0 | 58.0 | 102.6 | 0.0378 |
| dropout0.3 | drg0.3+cf0.3 | bayside | 24 | 0 | 90.0 | 78.0 | 0.0237 |
| dropout0.3 | drg0.3+cf0.3 | blocks | 24 | 0 | 92.0 | 86.8 | 0.0187 |
| dropout0.3 | drg0.3+cf0.3 | boulevard | 24 | 0 | 91.0 | 98.5 | 0.0141 |
| dropout0.3-noise8 | bridge+cf0.3 | bayside | 24 | 0 | 85.0 | 78.2 | 0.0142 |
| dropout0.3-noise8 | bridge+cf0.3 | blocks | 24 | 0 | 94.0 | 89.7 | 0.0189 |
| dropout0.3-noise8 | bridge+cf0.3 | boulevard | 24 | 0 | 98.0 | 99.9 | 0.004 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 0 | 85.0 | 83.2 | 0.0397 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 0 | 94.0 | 88.7 | 0.0475 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 0 | 98.0 | 100.5 | 0.0361 |
| dropout0.3-noise8 | dr+cf0.3+kb | bayside | 24 | 0 | 63.0 | 82.7 | 0.073 |
| dropout0.3-noise8 | dr+cf0.3+kb | blocks | 24 | 0 | 67.0 | 88.8 | 0.0401 |
| dropout0.3-noise8 | dr+cf0.3+kb | boulevard | 24 | 0 | 67.0 | 102.7 | 0.043 |
| dropout0.3-noise8 | drg0.3+cf0.3 | bayside | 24 | 0 | 85.0 | 79.1 | 0.0255 |
| dropout0.3-noise8 | drg0.3+cf0.3 | blocks | 24 | 0 | 94.0 | 87.8 | 0.0289 |
| dropout0.3-noise8 | drg0.3+cf0.3 | boulevard | 24 | 0 | 98.0 | 99.9 | 0.0239 |
| measured | bridge+cf0.3 | bayside | 24 | 0 | 104.0 | 1.1 | 0.0076 |
| measured | bridge+cf0.3 | blocks | 24 | 0 | 90.0 | 1.1 | 0.0102 |
| measured | bridge+cf0.3 | boulevard | 24 | 0 | 86.0 | 1.1 | 0.0085 |
| measured | dr+cf0.3 | bayside | 24 | 0 | 104.0 | 1.1 | 0.0232 |
| measured | dr+cf0.3 | blocks | 24 | 0 | 90.0 | 1.1 | 0.0697 |
| measured | dr+cf0.3 | boulevard | 24 | 0 | 86.0 | 1.1 | 0.0669 |
| measured | dr+cf0.3+kb | bayside | 24 | 0 | 59.0 | 1.1 | 0.0482 |
| measured | dr+cf0.3+kb | blocks | 24 | 0 | 60.0 | 1.1 | 0.034 |
| measured | dr+cf0.3+kb | boulevard | 24 | 0 | 58.0 | 1.1 | 0.0367 |
| measured | drg0.3+cf0.3 | bayside | 24 | 0 | 104.0 | 1.1 | 0.0124 |
| measured | drg0.3+cf0.3 | blocks | 24 | 0 | 90.0 | 1.1 | 0.0246 |
| measured | drg0.3+cf0.3 | boulevard | 24 | 0 | 86.0 | 1.1 | 0.0206 |
| noise8 | bridge+cf0.3 | bayside | 24 | 0 | 89.0 | 1.1 | 0.0152 |
| noise8 | bridge+cf0.3 | blocks | 24 | 0 | 74.0 | 1.1 | 0.011 |
| noise8 | bridge+cf0.3 | boulevard | 24 | 0 | 77.0 | 1.1 | 0.0085 |
| noise8 | dr+cf0.3 | bayside | 24 | 0 | 89.0 | 1.1 | 0.0565 |
| noise8 | dr+cf0.3 | blocks | 24 | 0 | 74.0 | 1.1 | 0.0588 |
| noise8 | dr+cf0.3 | boulevard | 24 | 0 | 77.0 | 1.1 | 0.0746 |
| noise8 | dr+cf0.3+kb | bayside | 24 | 0 | 63.0 | 1.1 | 0.0555 |
| noise8 | dr+cf0.3+kb | blocks | 24 | 0 | 65.0 | 1.1 | 0.0332 |
| noise8 | dr+cf0.3+kb | boulevard | 24 | 0 | 61.0 | 1.1 | 0.034 |
| noise8 | drg0.3+cf0.3 | bayside | 24 | 0 | 89.0 | 1.1 | 0.0212 |
| noise8 | drg0.3+cf0.3 | blocks | 24 | 0 | 74.0 | 1.1 | 0.0301 |
| noise8 | drg0.3+cf0.3 | boulevard | 24 | 0 | 77.0 | 1.1 | 0.0302 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| dropout0.3 | bridge+cf0.3 | bayside | 24 | 0.86 | 2.83 |
| dropout0.3 | bridge+cf0.3 | blocks | 24 | 1.64 | 10.94 |
| dropout0.3 | bridge+cf0.3 | boulevard | 24 | 1.97 | 5.67 |
| dropout0.3 | cf0.3 | bayside | 24 | 0.82 | 2.6 |
| dropout0.3 | cf0.3 | blocks | 24 | 1.6 | 10.96 |
| dropout0.3 | cf0.3 | boulevard | 24 | 1.94 | 5.33 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 1.0 | 2.77 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 1.33 | 7.07 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 1.53 | 5.33 |
| dropout0.3 | dr+cf0.3+kb | bayside | 24 | 0.65 | 1.97 |
| dropout0.3 | dr+cf0.3+kb | blocks | 24 | 0.98 | 6.82 |
| dropout0.3 | dr+cf0.3+kb | boulevard | 24 | 1.3 | 3.91 |
| dropout0.3 | drg0.3+cf0.3 | bayside | 24 | 0.94 | 3.04 |
| dropout0.3 | drg0.3+cf0.3 | blocks | 24 | 1.34 | 7.11 |
| dropout0.3 | drg0.3+cf0.3 | boulevard | 24 | 1.71 | 5.17 |
| dropout0.3-noise8 | bridge+cf0.3 | bayside | 24 | 0.94 | 3.58 |
| dropout0.3-noise8 | bridge+cf0.3 | blocks | 24 | 1.77 | 10.61 |
| dropout0.3-noise8 | bridge+cf0.3 | boulevard | 24 | 1.97 | 5.26 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 0.88 | 3.46 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 1.77 | 11.12 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 1.94 | 5.46 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 3.87 | 5.76 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 3.2 | 7.48 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 3.93 | 7.99 |
| dropout0.3-noise8 | dr+cf0.3+kb | bayside | 24 | 0.63 | 1.93 |
| dropout0.3-noise8 | dr+cf0.3+kb | blocks | 24 | 0.98 | 6.7 |
| dropout0.3-noise8 | dr+cf0.3+kb | boulevard | 24 | 1.21 | 4.19 |
| dropout0.3-noise8 | drg0.3+cf0.3 | bayside | 24 | 2.63 | 5.82 |
| dropout0.3-noise8 | drg0.3+cf0.3 | blocks | 24 | 2.19 | 7.64 |
| dropout0.3-noise8 | drg0.3+cf0.3 | boulevard | 24 | 3.46 | 8.43 |
| measured | bridge+cf0.3 | bayside | 24 | 0.73 | 2.17 |
| measured | bridge+cf0.3 | blocks | 24 | 1.29 | 10.2 |
| measured | bridge+cf0.3 | boulevard | 24 | 1.88 | 5.12 |
| measured | cf0.3 | bayside | 24 | 0.72 | 2.19 |
| measured | cf0.3 | blocks | 24 | 1.31 | 10.23 |
| measured | cf0.3 | boulevard | 24 | 1.77 | 5.19 |
| measured | dr+cf0.3 | bayside | 24 | 0.69 | 1.97 |
| measured | dr+cf0.3 | blocks | 24 | 0.96 | 7.32 |
| measured | dr+cf0.3 | boulevard | 24 | 1.5 | 4.6 |
| measured | dr+cf0.3+kb | bayside | 24 | 0.55 | 1.6 |
| measured | dr+cf0.3+kb | blocks | 24 | 0.85 | 7.09 |
| measured | dr+cf0.3+kb | boulevard | 24 | 1.21 | 4.25 |
| measured | drg0.3+cf0.3 | bayside | 24 | 0.71 | 2.3 |
| measured | drg0.3+cf0.3 | blocks | 24 | 1.12 | 7.68 |
| measured | drg0.3+cf0.3 | boulevard | 24 | 1.52 | 4.8 |
| noise8 | bridge+cf0.3 | bayside | 24 | 0.72 | 3.08 |
| noise8 | bridge+cf0.3 | blocks | 24 | 1.44 | 10.08 |
| noise8 | bridge+cf0.3 | boulevard | 24 | 1.94 | 4.97 |
| noise8 | cf0.3 | bayside | 24 | 0.74 | 2.96 |
| noise8 | cf0.3 | blocks | 24 | 1.44 | 10.02 |
| noise8 | cf0.3 | boulevard | 24 | 1.96 | 5.05 |
| noise8 | dr+cf0.3 | bayside | 24 | 1.87 | 3.35 |
| noise8 | dr+cf0.3 | blocks | 24 | 2.62 | 7.87 |
| noise8 | dr+cf0.3 | boulevard | 24 | 3.29 | 7.37 |
| noise8 | dr+cf0.3+kb | bayside | 24 | 0.5 | 1.48 |
| noise8 | dr+cf0.3+kb | blocks | 24 | 0.83 | 6.99 |
| noise8 | dr+cf0.3+kb | boulevard | 24 | 1.2 | 3.87 |
| noise8 | drg0.3+cf0.3 | bayside | 24 | 1.57 | 3.75 |
| noise8 | drg0.3+cf0.3 | blocks | 24 | 2.31 | 8.45 |
| noise8 | drg0.3+cf0.3 | boulevard | 24 | 2.47 | 7.03 |
