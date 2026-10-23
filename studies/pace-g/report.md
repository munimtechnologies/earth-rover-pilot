# Dead reckoning and --smooth-heading together (simulated)

pace_g.py 0.1.0 (pace_f.py 0.1.0, rover_pilot.py 0.13.0, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every profile is pace_f.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, GPS every 2 s and 1.5 s late, 3 deg of compass noise, a -25 deg compass error to learn), reporting its wheels' RPM, with one or two things changed: 6 or 8 deg of noise, 30% of GPS fixes missing, or wheels driving 0.85 of the 95 mm prior per RPM. Variants: dr+cf0.3 (v0.13.0 on a real rover), dr (dead reckoning only), cf0.3 (--smooth-heading only), plain (neither; pace_f.py's shipped). Seeds 37-60. 1728 of 1728 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_f.py's runs: 36 compared, 36 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio |
|---|---|---|---|---|---|---|
| measured | dr+cf0.3 | 72/72 | 0.826 | 0.93 | 72 | 1.026 |
| measured | dr | 72/72 | 0.83 | 0.934 | 72 | 1.023 |
| measured | cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.004 |
| measured | plain | 72/72 | 0.877 | 0.986 | 72 | 1.004 |
| noise6 | dr+cf0.3 | 72/72 | 0.828 | 0.931 | 72 | 1.025 |
| noise6 | dr | 72/72 | 0.839 | 0.944 | 72 | 1.017 |
| noise6 | cf0.3 | 72/72 | 0.877 | 0.987 | 72 | 1.004 |
| noise6 | plain | 72/72 | 0.87 | 0.978 | 72 | 1.007 |
| noise8 | dr+cf0.3 | 72/72 | 0.831 | 0.935 | 72 | 1.023 |
| noise8 | dr | 72/72 | 0.863 | 0.971 | 72 | 1.009 |
| noise8 | cf0.3 | 72/72 | 0.876 | 0.986 | 72 | 1.005 |
| noise8 | plain | 72/72 | 0.863 | 0.971 | 72 | 1.008 |
| dropout0.3 | dr+cf0.3 | 72/72 | 0.832 | 0.936 | 72 | 1.028 |
| dropout0.3 | dr | 72/72 | 0.835 | 0.939 | 72 | 1.024 |
| dropout0.3 | cf0.3 | 72/72 | 0.821 | 0.924 | 72 | 1.009 |
| dropout0.3 | plain | 72/72 | 0.821 | 0.924 | 72 | 1.009 |
| dropout0.3-noise8 | dr+cf0.3 | 72/72 | 0.834 | 0.938 | 72 | 1.024 |
| dropout0.3-noise8 | dr | 72/72 | 0.808 | 0.909 | 72 | 1.011 |
| dropout0.3-noise8 | cf0.3 | 72/72 | 0.819 | 0.922 | 72 | 1.01 |
| dropout0.3-noise8 | plain | 72/72 | 0.808 | 0.909 | 72 | 1.011 |
| wheels0.85 | dr+cf0.3 | 72/72 | 0.826 | 0.93 | 72 | 1.026 |
| wheels0.85 | dr | 72/72 | 0.83 | 0.934 | 72 | 1.023 |
| wheels0.85 | cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.004 |
| wheels0.85 | plain | 72/72 | 0.877 | 0.986 | 72 | 1.004 |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| measured | dr+cf0.3 | dr | 0/3 | 0 | 0 | 0 | 0.0018 |
| noise6 | dr+cf0.3 | dr | 0/3 | 2 | 0 | 0 | 0.0166 |
| noise8 | dr+cf0.3 | dr | 1/3 | 2 | 0 | 0 | 0.0493 |
| dropout0.3 | dr+cf0.3 | dr | 0/3 | 0 | 0 | 0 | 0.0046 |
| dropout0.3-noise8 | dr+cf0.3 | dr | 3/3 | 0 | 0 | 0 | -0.084 |
| wheels0.85 | dr+cf0.3 | dr | 0/3 | 0 | 0 | 0 | 0.0018 |
| measured | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0696 |
| noise6 | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0686 |
| noise8 | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.066 |
| dropout0.3 | dr+cf0.3 | cf0.3 | 1/3 | 0 | 0 | 0 | -0.0621 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | 1/3 | 0 | 0 | 0 | -0.0659 |
| wheels0.85 | dr+cf0.3 | cf0.3 | 0/3 | 3 | 0 | 0 | 0.0696 |
| measured | dr | plain | 0/3 | 3 | 0 | 0 | 0.0663 |
| noise6 | dr | plain | 0/3 | 2 | 0 | 0 | 0.0484 |
| noise8 | dr | plain | 0/3 | 0 | 0 | 0 | 0.0 |
| dropout0.3 | dr | plain | 2/3 | 0 | 0 | 0 | -0.0602 |
| dropout0.3-noise8 | dr | plain | 0/3 | 0 | 0 | 0 | 0.0 |
| wheels0.85 | dr | plain | 0/3 | 3 | 0 | 0 | 0.0663 |
| measured | cf0.3 | plain | 2/3 | 0 | 0 | 0 | -0.0011 |
| noise6 | cf0.3 | plain | 3/3 | 0 | 0 | 0 | -0.0123 |
| noise8 | cf0.3 | plain | 3/3 | 0 | 0 | 0 | -0.0207 |
| dropout0.3 | cf0.3 | plain | 2/3 | 0 | 0 | 0 | 0.0 |
| dropout0.3-noise8 | cf0.3 | plain | 3/3 | 0 | 0 | 0 | -0.0198 |
| wheels0.85 | cf0.3 | plain | 2/3 | 0 | 0 | 0 | -0.0011 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| measured | dr+cf0.3 | dr | bayside | 12 | 11 | -0.9 | -0.0006 | 1.0 |
| measured | dr+cf0.3 | dr | blocks | 12 | 11 | -0.1 | -0.0001 | 1.0 |
| measured | dr+cf0.3 | dr | boulevard | 10 | 13 | 3.4 | 0.0018 | 0.6776 |
| noise6 | dr+cf0.3 | dr | bayside | 3 | 21 | 25.1 | 0.0166 | 0.0003 |
| noise6 | dr+cf0.3 | dr | blocks | 8 | 15 | 2.5 | 0.0015 | 0.21 |
| noise6 | dr+cf0.3 | dr | boulevard | 2 | 21 | 16.1 | 0.0086 | 0.0001 |
| noise8 | dr+cf0.3 | dr | bayside | 0 | 24 | 72.0 | 0.0493 | 0.0 |
| noise8 | dr+cf0.3 | dr | blocks | 19 | 5 | -19.2 | -0.0117 | 0.0066 |
| noise8 | dr+cf0.3 | dr | boulevard | 0 | 24 | 82.4 | 0.046 | 0.0 |
| dropout0.3 | dr+cf0.3 | dr | bayside | 8 | 13 | 7.0 | 0.0046 | 0.3833 |
| dropout0.3 | dr+cf0.3 | dr | blocks | 14 | 6 | -1.5 | -0.0009 | 0.1153 |
| dropout0.3 | dr+cf0.3 | dr | boulevard | 9 | 14 | 1.5 | 0.0008 | 0.4049 |
| dropout0.3-noise8 | dr+cf0.3 | dr | bayside | 21 | 3 | -34.9 | -0.0225 | 0.0003 |
| dropout0.3-noise8 | dr+cf0.3 | dr | blocks | 24 | 0 | -148.1 | -0.084 | 0.0 |
| dropout0.3-noise8 | dr+cf0.3 | dr | boulevard | 21 | 3 | -27.8 | -0.0146 | 0.0003 |
| wheels0.85 | dr+cf0.3 | dr | bayside | 12 | 11 | -0.9 | -0.0006 | 1.0 |
| wheels0.85 | dr+cf0.3 | dr | blocks | 12 | 11 | -0.1 | -0.0001 | 1.0 |
| wheels0.85 | dr+cf0.3 | dr | boulevard | 10 | 13 | 3.4 | 0.0018 | 0.6776 |
| measured | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 100.0 | 0.0696 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | blocks | 0 | 24 | 24.1 | 0.015 | 0.0 |
| measured | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 120.7 | 0.0685 | 0.0 |
| noise6 | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 98.6 | 0.0686 | 0.0 |
| noise6 | dr+cf0.3 | cf0.3 | blocks | 0 | 23 | 26.0 | 0.0162 | 0.0 |
| noise6 | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 117.0 | 0.0663 | 0.0 |
| noise8 | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 95.0 | 0.066 | 0.0 |
| noise8 | dr+cf0.3 | cf0.3 | blocks | 3 | 19 | 15.8 | 0.0098 | 0.0009 |
| noise8 | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 111.6 | 0.0632 | 0.0 |
| dropout0.3 | dr+cf0.3 | cf0.3 | bayside | 13 | 9 | -7.0 | -0.0046 | 0.5235 |
| dropout0.3 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -107.5 | -0.0621 | 0.0 |
| dropout0.3 | dr+cf0.3 | cf0.3 | boulevard | 11 | 13 | 3.7 | 0.002 | 0.8388 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | bayside | 16 | 6 | -15.0 | -0.0098 | 0.0525 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | blocks | 24 | 0 | -114.0 | -0.0659 | 0.0 |
| dropout0.3-noise8 | dr+cf0.3 | cf0.3 | boulevard | 13 | 11 | -4.9 | -0.0026 | 0.8388 |
| wheels0.85 | dr+cf0.3 | cf0.3 | bayside | 0 | 24 | 100.0 | 0.0696 | 0.0 |
| wheels0.85 | dr+cf0.3 | cf0.3 | blocks | 0 | 24 | 24.1 | 0.015 | 0.0 |
| wheels0.85 | dr+cf0.3 | cf0.3 | boulevard | 0 | 24 | 120.7 | 0.0685 | 0.0 |
| measured | dr | plain | bayside | 0 | 24 | 95.1 | 0.0661 | 0.0 |
| measured | dr | plain | blocks | 2 | 22 | 23.9 | 0.0149 | 0.0 |
| measured | dr | plain | boulevard | 0 | 24 | 117.0 | 0.0663 | 0.0 |
| noise6 | dr | plain | bayside | 0 | 24 | 61.0 | 0.0421 | 0.0 |
| noise6 | dr | plain | blocks | 13 | 9 | -2.2 | -0.0014 | 0.5235 |
| noise6 | dr | plain | boulevard | 0 | 24 | 85.9 | 0.0484 | 0.0 |
| noise8 | dr | plain | bayside | 0 | 1 | 0.0 | 0.0 | 1.0 |
| noise8 | dr | plain | blocks | 0 | 0 | 0.0 | 0.0 | None |
| noise8 | dr | plain | boulevard | 0 | 1 | 0.0 | 0.0 | 1.0 |
| dropout0.3 | dr | plain | bayside | 17 | 6 | -14.1 | -0.0092 | 0.0347 |
| dropout0.3 | dr | plain | blocks | 24 | 0 | -103.9 | -0.0602 | 0.0 |
| dropout0.3 | dr | plain | boulevard | 11 | 12 | 3.3 | 0.0018 | 1.0 |
| dropout0.3-noise8 | dr | plain | bayside | 0 | 0 | 0.0 | 0.0 | None |
| dropout0.3-noise8 | dr | plain | blocks | 2 | 0 | 0.0 | 0.0 | 0.5 |
| dropout0.3-noise8 | dr | plain | boulevard | 1 | 0 | 0.0 | 0.0 | 1.0 |
| wheels0.85 | dr | plain | bayside | 0 | 24 | 95.1 | 0.0661 | 0.0 |
| wheels0.85 | dr | plain | blocks | 2 | 22 | 23.9 | 0.0149 | 0.0 |
| wheels0.85 | dr | plain | boulevard | 0 | 24 | 117.0 | 0.0663 | 0.0 |
| measured | cf0.3 | plain | bayside | 11 | 3 | 0.0 | 0.0 | 0.0574 |
| measured | cf0.3 | plain | blocks | 11 | 1 | 0.0 | 0.0 | 0.0063 |
| measured | cf0.3 | plain | boulevard | 13 | 2 | -2.0 | -0.0011 | 0.0074 |
| noise6 | cf0.3 | plain | bayside | 23 | 0 | -10.0 | -0.0069 | 0.0 |
| noise6 | cf0.3 | plain | blocks | 24 | 0 | -20.0 | -0.0123 | 0.0 |
| noise6 | cf0.3 | plain | boulevard | 23 | 1 | -12.0 | -0.0068 | 0.0 |
| noise8 | cf0.3 | plain | bayside | 24 | 0 | -18.0 | -0.0123 | 0.0 |
| noise8 | cf0.3 | plain | blocks | 24 | 0 | -34.0 | -0.0207 | 0.0 |
| noise8 | cf0.3 | plain | boulevard | 24 | 0 | -26.0 | -0.0145 | 0.0 |
| dropout0.3 | cf0.3 | plain | bayside | 8 | 1 | 0.0 | 0.0 | 0.0391 |
| dropout0.3 | cf0.3 | plain | blocks | 7 | 7 | 0.0 | 0.0 | 1.0 |
| dropout0.3 | cf0.3 | plain | boulevard | 10 | 0 | 0.0 | 0.0 | 0.002 |
| dropout0.3-noise8 | cf0.3 | plain | bayside | 24 | 0 | -21.0 | -0.0135 | 0.0 |
| dropout0.3-noise8 | cf0.3 | plain | blocks | 24 | 0 | -35.0 | -0.0198 | 0.0 |
| dropout0.3-noise8 | cf0.3 | plain | boulevard | 24 | 0 | -25.0 | -0.0132 | 0.0 |
| wheels0.85 | cf0.3 | plain | bayside | 11 | 3 | 0.0 | 0.0 | 0.0574 |
| wheels0.85 | cf0.3 | plain | blocks | 11 | 1 | 0.0 | 0.0 | 0.0063 |
| wheels0.85 | cf0.3 | plain | boulevard | 13 | 2 | -2.0 | -0.0011 | 0.0074 |

## Where the pilot thinks it is, against where it is

Sampled once a second while driving forward; medians over the completed missions of each mission's median and 95th percentile.

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| dropout0.3 | cf0.3 | bayside | 24 | 8.03 | 10.7 |
| dropout0.3 | cf0.3 | blocks | 24 | 7.75 | 10.57 |
| dropout0.3 | cf0.3 | boulevard | 24 | 8.05 | 10.82 |
| dropout0.3 | dr | bayside | 24 | 2.73 | 7.23 |
| dropout0.3 | dr | blocks | 24 | 2.71 | 7.37 |
| dropout0.3 | dr | boulevard | 24 | 2.65 | 7.14 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 2.65 | 7.21 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 2.64 | 7.06 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 2.6 | 6.87 |
| dropout0.3 | plain | bayside | 24 | 8.0 | 10.68 |
| dropout0.3 | plain | blocks | 24 | 7.74 | 10.57 |
| dropout0.3 | plain | boulevard | 24 | 8.04 | 10.8 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 8.01 | 10.66 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 7.74 | 10.55 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 8.03 | 10.79 |
| dropout0.3-noise8 | dr | bayside | 24 | 7.9 | 10.51 |
| dropout0.3-noise8 | dr | blocks | 24 | 7.64 | 10.39 |
| dropout0.3-noise8 | dr | boulevard | 24 | 7.92 | 10.63 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 2.73 | 7.41 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 2.66 | 7.11 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 2.61 | 6.95 |
| dropout0.3-noise8 | plain | bayside | 24 | 7.9 | 10.51 |
| dropout0.3-noise8 | plain | blocks | 24 | 7.65 | 10.41 |
| dropout0.3-noise8 | plain | boulevard | 24 | 7.94 | 10.65 |
| measured | cf0.3 | bayside | 24 | 6.46 | 8.23 |
| measured | cf0.3 | blocks | 24 | 6.37 | 8.2 |
| measured | cf0.3 | boulevard | 24 | 6.56 | 8.25 |
| measured | dr | bayside | 24 | 2.65 | 6.55 |
| measured | dr | blocks | 24 | 2.66 | 6.47 |
| measured | dr | boulevard | 24 | 2.63 | 6.43 |
| measured | dr+cf0.3 | bayside | 24 | 2.62 | 6.5 |
| measured | dr+cf0.3 | blocks | 24 | 2.61 | 6.47 |
| measured | dr+cf0.3 | boulevard | 24 | 2.6 | 6.43 |
| measured | plain | bayside | 24 | 6.46 | 8.21 |
| measured | plain | blocks | 24 | 6.37 | 8.19 |
| measured | plain | boulevard | 24 | 6.55 | 8.25 |
| noise6 | cf0.3 | bayside | 24 | 6.46 | 8.21 |
| noise6 | cf0.3 | blocks | 24 | 6.38 | 8.18 |
| noise6 | cf0.3 | boulevard | 24 | 6.55 | 8.25 |
| noise6 | dr | bayside | 24 | 3.56 | 7.46 |
| noise6 | dr | blocks | 24 | 3.04 | 7.19 |
| noise6 | dr | boulevard | 24 | 2.96 | 7.16 |
| noise6 | dr+cf0.3 | bayside | 24 | 2.62 | 6.46 |
| noise6 | dr+cf0.3 | blocks | 24 | 2.62 | 6.47 |
| noise6 | dr+cf0.3 | boulevard | 24 | 2.58 | 6.44 |
| noise6 | plain | bayside | 24 | 6.42 | 8.17 |
| noise6 | plain | blocks | 24 | 6.36 | 8.12 |
| noise6 | plain | boulevard | 24 | 6.49 | 8.22 |
| noise8 | cf0.3 | bayside | 24 | 6.45 | 8.19 |
| noise8 | cf0.3 | blocks | 24 | 6.37 | 8.18 |
| noise8 | cf0.3 | boulevard | 24 | 6.54 | 8.23 |
| noise8 | dr | bayside | 24 | 6.37 | 8.11 |
| noise8 | dr | blocks | 24 | 6.29 | 8.05 |
| noise8 | dr | boulevard | 24 | 6.39 | 8.12 |
| noise8 | dr+cf0.3 | bayside | 24 | 2.63 | 6.5 |
| noise8 | dr+cf0.3 | blocks | 24 | 2.61 | 6.49 |
| noise8 | dr+cf0.3 | boulevard | 24 | 2.61 | 6.4 |
| noise8 | plain | bayside | 24 | 6.38 | 8.15 |
| noise8 | plain | blocks | 24 | 6.29 | 8.05 |
| noise8 | plain | boulevard | 24 | 6.39 | 8.14 |
| wheels0.85 | cf0.3 | bayside | 24 | 6.46 | 8.23 |
| wheels0.85 | cf0.3 | blocks | 24 | 6.37 | 8.2 |
| wheels0.85 | cf0.3 | boulevard | 24 | 6.56 | 8.25 |
| wheels0.85 | dr | bayside | 24 | 2.65 | 6.55 |
| wheels0.85 | dr | blocks | 24 | 2.66 | 6.47 |
| wheels0.85 | dr | boulevard | 24 | 2.63 | 6.43 |
| wheels0.85 | dr+cf0.3 | bayside | 24 | 2.62 | 6.5 |
| wheels0.85 | dr+cf0.3 | blocks | 24 | 2.61 | 6.47 |
| wheels0.85 | dr+cf0.3 | boulevard | 24 | 2.6 | 6.43 |
| wheels0.85 | plain | bayside | 24 | 6.46 | 8.21 |
| wheels0.85 | plain | blocks | 24 | 6.37 | 8.19 |
| wheels0.85 | plain | boulevard | 24 | 6.55 | 8.25 |

## Dead reckoning

Trusted after two straight stretches of about 20 s agree with the wheel-size prior; 'first trusted' is a median with missions never trusted counted last (blank if most never were).

| profile | variant | course | missions | trusted at end | never trusted | first trusted s | stretches learned | turned down | s on wheels alone | abs scale error |
|---|---|---|---|---|---|---|---|---|---|---|
| dropout0.3 | dr | bayside | 24 | 24 | 0 | 91.0 | 2.0 | 0.0 | 81.0 | 0.0563 |
| dropout0.3 | dr | blocks | 24 | 24 | 0 | 101.0 | 2.0 | 0.0 | 86.4 | 0.0641 |
| dropout0.3 | dr | boulevard | 24 | 24 | 0 | 106.0 | 3.0 | 0.0 | 102.2 | 0.0638 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 24 | 0 | 94.0 | 3.0 | 0.0 | 82.8 | 0.0372 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 24 | 0 | 83.0 | 3.0 | 0.0 | 87.8 | 0.0506 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 24 | 0 | 84.0 | 3.0 | 0.0 | 102.2 | 0.0306 |
| dropout0.3-noise8 | dr | bayside | 24 | 0 | 24 | None | 0.0 | 0.0 | 0.0 | 0.0 |
| dropout0.3-noise8 | dr | blocks | 24 | 2 | 22 | None | 0.0 | 0.0 | 0.0 | 0.0 |
| dropout0.3-noise8 | dr | boulevard | 24 | 1 | 23 | None | 0.5 | 0.0 | 0.0 | 0.0053 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 24 | 0 | 97.0 | 3.0 | 0.0 | 81.0 | 0.0648 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 24 | 0 | 83.0 | 2.5 | 0.0 | 87.3 | 0.0421 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 24 | 0 | 86.0 | 3.0 | 0.0 | 99.8 | 0.0589 |
| measured | dr | bayside | 24 | 24 | 0 | 110.0 | 2.0 | 0.0 | 1.1 | 0.0655 |
| measured | dr | blocks | 24 | 24 | 0 | 81.0 | 2.0 | 0.0 | 1.1 | 0.0457 |
| measured | dr | boulevard | 24 | 24 | 0 | 82.0 | 2.0 | 0.0 | 2.0 | 0.0321 |
| measured | dr+cf0.3 | bayside | 24 | 24 | 0 | 94.0 | 2.0 | 0.0 | 1.1 | 0.062 |
| measured | dr+cf0.3 | blocks | 24 | 24 | 0 | 91.0 | 2.0 | 0.0 | 1.1 | 0.031 |
| measured | dr+cf0.3 | boulevard | 24 | 24 | 0 | 90.0 | 2.0 | 0.0 | 2.0 | 0.0524 |
| noise6 | dr | bayside | 24 | 24 | 0 | 474.0 | 2.0 | 0.0 | 1.0 | 0.0443 |
| noise6 | dr | blocks | 24 | 24 | 0 | 335.0 | 2.0 | 0.0 | 1.0 | 0.0539 |
| noise6 | dr | boulevard | 24 | 24 | 0 | 298.0 | 2.0 | 0.0 | 1.1 | 0.0396 |
| noise6 | dr+cf0.3 | bayside | 24 | 24 | 0 | 89.0 | 2.0 | 0.0 | 1.1 | 0.0532 |
| noise6 | dr+cf0.3 | blocks | 24 | 24 | 0 | 92.0 | 2.0 | 0.0 | 1.1 | 0.0617 |
| noise6 | dr+cf0.3 | boulevard | 24 | 24 | 0 | 87.0 | 2.0 | 0.0 | 2.0 | 0.0378 |
| noise8 | dr | bayside | 24 | 1 | 23 | None | 0.0 | 0.0 | 0.0 | 0.0 |
| noise8 | dr | blocks | 24 | 0 | 24 | None | 0.0 | 0.0 | 0.0 | 0.0 |
| noise8 | dr | boulevard | 24 | 1 | 23 | None | 0.0 | 0.0 | 0.0 | 0.0 |
| noise8 | dr+cf0.3 | bayside | 24 | 24 | 0 | 85.0 | 2.0 | 0.0 | 1.1 | 0.0507 |
| noise8 | dr+cf0.3 | blocks | 24 | 24 | 0 | 74.0 | 2.0 | 0.0 | 1.1 | 0.062 |
| noise8 | dr+cf0.3 | boulevard | 24 | 24 | 0 | 75.0 | 2.0 | 0.0 | 2.0 | 0.0512 |
| wheels0.85 | dr | bayside | 24 | 24 | 0 | 110.0 | 2.0 | 0.0 | 1.1 | 0.0655 |
| wheels0.85 | dr | blocks | 24 | 24 | 0 | 81.0 | 2.0 | 0.0 | 1.1 | 0.0457 |
| wheels0.85 | dr | boulevard | 24 | 24 | 0 | 82.0 | 2.0 | 0.0 | 2.0 | 0.0321 |
| wheels0.85 | dr+cf0.3 | bayside | 24 | 24 | 0 | 94.0 | 2.0 | 0.0 | 1.1 | 0.062 |
| wheels0.85 | dr+cf0.3 | blocks | 24 | 24 | 0 | 91.0 | 2.0 | 0.0 | 1.1 | 0.031 |
| wheels0.85 | dr+cf0.3 | boulevard | 24 | 24 | 0 | 90.0 | 2.0 | 0.0 | 2.0 | 0.0524 |

## The compass-bias learner

| profile | variant | course | missions | median calibrations | missions with none | median abs bias error deg |
|---|---|---|---|---|---|---|
| dropout0.3 | cf0.3 | bayside | 24 | 35.0 | 0 | 3.71 |
| dropout0.3 | cf0.3 | blocks | 24 | 37.0 | 0 | 2.02 |
| dropout0.3 | cf0.3 | boulevard | 24 | 49.5 | 0 | 2.94 |
| dropout0.3 | dr | bayside | 24 | 0.0 | 13 | 25.0 |
| dropout0.3 | dr | blocks | 24 | 1.0 | 8 | 10.66 |
| dropout0.3 | dr | boulevard | 24 | 1.0 | 9 | 10.81 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 2.0 | 3 | 2.86 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 2.0 | 4 | 4.09 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 2.0 | 3 | 4.62 |
| dropout0.3 | plain | bayside | 24 | 14.0 | 0 | 1.65 |
| dropout0.3 | plain | blocks | 24 | 14.0 | 0 | 3.54 |
| dropout0.3 | plain | boulevard | 24 | 20.0 | 0 | 3.0 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 14.0 | 0 | 2.35 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 14.5 | 0 | 1.97 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 20.0 | 0 | 2.22 |
| dropout0.3-noise8 | dr | bayside | 24 | 0.0 | 24 | 25.0 |
| dropout0.3-noise8 | dr | blocks | 24 | 0.0 | 24 | 25.0 |
| dropout0.3-noise8 | dr | boulevard | 24 | 0.0 | 24 | 25.0 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 0.5 | 12 | 21.88 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 1.0 | 10 | 15.52 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 1.0 | 8 | 12.69 |
| dropout0.3-noise8 | plain | bayside | 24 | 0.0 | 24 | 25.0 |
| dropout0.3-noise8 | plain | blocks | 24 | 0.0 | 24 | 25.0 |
| dropout0.3-noise8 | plain | boulevard | 24 | 0.0 | 24 | 25.0 |
| measured | cf0.3 | bayside | 24 | 61.0 | 0 | 2.49 |
| measured | cf0.3 | blocks | 24 | 62.0 | 0 | 2.67 |
| measured | cf0.3 | boulevard | 24 | 84.0 | 0 | 3.1 |
| measured | dr | bayside | 24 | 1.0 | 7 | 7.53 |
| measured | dr | blocks | 24 | 1.0 | 9 | 6.83 |
| measured | dr | boulevard | 24 | 1.0 | 10 | 17.41 |
| measured | dr+cf0.3 | bayside | 24 | 3.0 | 0 | 4.25 |
| measured | dr+cf0.3 | blocks | 24 | 3.0 | 0 | 4.81 |
| measured | dr+cf0.3 | boulevard | 24 | 3.0 | 0 | 4.96 |
| measured | plain | bayside | 24 | 23.0 | 0 | 2.71 |
| measured | plain | blocks | 24 | 26.5 | 0 | 1.99 |
| measured | plain | boulevard | 24 | 34.5 | 0 | 1.79 |
| noise6 | cf0.3 | bayside | 24 | 40.5 | 0 | 2.21 |
| noise6 | cf0.3 | blocks | 24 | 43.0 | 0 | 3.34 |
| noise6 | cf0.3 | boulevard | 24 | 59.0 | 0 | 3.85 |
| noise6 | dr | bayside | 24 | 0.0 | 21 | 25.0 |
| noise6 | dr | blocks | 24 | 0.0 | 21 | 25.0 |
| noise6 | dr | boulevard | 24 | 0.0 | 22 | 25.0 |
| noise6 | dr+cf0.3 | bayside | 24 | 2.0 | 4 | 4.96 |
| noise6 | dr+cf0.3 | blocks | 24 | 1.0 | 3 | 5.31 |
| noise6 | dr+cf0.3 | boulevard | 24 | 2.0 | 4 | 6.76 |
| noise6 | plain | bayside | 24 | 0.0 | 19 | 25.0 |
| noise6 | plain | blocks | 24 | 0.0 | 14 | 25.0 |
| noise6 | plain | boulevard | 24 | 0.5 | 12 | 18.71 |
| noise8 | cf0.3 | bayside | 24 | 25.0 | 0 | 2.9 |
| noise8 | cf0.3 | blocks | 24 | 26.0 | 0 | 3.37 |
| noise8 | cf0.3 | boulevard | 24 | 34.5 | 0 | 3.22 |
| noise8 | dr | bayside | 24 | 0.0 | 24 | 25.0 |
| noise8 | dr | blocks | 24 | 0.0 | 24 | 25.0 |
| noise8 | dr | boulevard | 24 | 0.0 | 23 | 25.0 |
| noise8 | dr+cf0.3 | bayside | 24 | 1.0 | 6 | 8.25 |
| noise8 | dr+cf0.3 | blocks | 24 | 1.0 | 10 | 13.27 |
| noise8 | dr+cf0.3 | boulevard | 24 | 1.0 | 10 | 14.71 |
| noise8 | plain | bayside | 24 | 0.0 | 24 | 25.0 |
| noise8 | plain | blocks | 24 | 0.0 | 24 | 25.0 |
| noise8 | plain | boulevard | 24 | 0.0 | 23 | 25.0 |
| wheels0.85 | cf0.3 | bayside | 24 | 61.0 | 0 | 2.49 |
| wheels0.85 | cf0.3 | blocks | 24 | 62.0 | 0 | 2.67 |
| wheels0.85 | cf0.3 | boulevard | 24 | 84.0 | 0 | 3.1 |
| wheels0.85 | dr | bayside | 24 | 1.0 | 7 | 7.53 |
| wheels0.85 | dr | blocks | 24 | 1.0 | 9 | 6.83 |
| wheels0.85 | dr | boulevard | 24 | 1.0 | 10 | 17.41 |
| wheels0.85 | dr+cf0.3 | bayside | 24 | 3.0 | 0 | 4.25 |
| wheels0.85 | dr+cf0.3 | blocks | 24 | 3.0 | 0 | 4.81 |
| wheels0.85 | dr+cf0.3 | boulevard | 24 | 3.0 | 0 | 4.96 |
| wheels0.85 | plain | bayside | 24 | 23.0 | 0 | 2.71 |
| wheels0.85 | plain | blocks | 24 | 26.5 | 0 | 1.99 |
| wheels0.85 | plain | boulevard | 24 | 34.5 | 0 | 1.79 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| dropout0.3 | cf0.3 | bayside | 24 | 0.82 | 2.75 |
| dropout0.3 | cf0.3 | blocks | 24 | 1.51 | 10.77 |
| dropout0.3 | cf0.3 | boulevard | 24 | 1.9 | 5.54 |
| dropout0.3 | dr | bayside | 24 | 4.23 | 5.71 |
| dropout0.3 | dr | blocks | 24 | 2.02 | 7.62 |
| dropout0.3 | dr | boulevard | 24 | 2.87 | 6.95 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 0.81 | 2.78 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 1.26 | 7.29 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 1.51 | 4.44 |
| dropout0.3 | plain | bayside | 24 | 0.88 | 3.48 |
| dropout0.3 | plain | blocks | 24 | 1.56 | 11.05 |
| dropout0.3 | plain | boulevard | 24 | 2.01 | 5.73 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 0.89 | 3.47 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 1.69 | 10.93 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 2.0 | 5.48 |
| dropout0.3-noise8 | dr | bayside | 24 | 3.75 | 5.66 |
| dropout0.3-noise8 | dr | blocks | 24 | 4.03 | 11.18 |
| dropout0.3-noise8 | dr | boulevard | 24 | 3.93 | 10.04 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 3.92 | 5.53 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 2.79 | 7.71 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 2.62 | 5.29 |
| dropout0.3-noise8 | plain | bayside | 24 | 3.75 | 5.66 |
| dropout0.3-noise8 | plain | blocks | 24 | 4.02 | 11.2 |
| dropout0.3-noise8 | plain | boulevard | 24 | 3.91 | 10.05 |
| measured | cf0.3 | bayside | 24 | 0.69 | 2.25 |
| measured | cf0.3 | blocks | 24 | 1.25 | 10.06 |
| measured | cf0.3 | boulevard | 24 | 1.77 | 5.0 |
| measured | dr | bayside | 24 | 1.19 | 2.62 |
| measured | dr | blocks | 24 | 2.18 | 7.57 |
| measured | dr | boulevard | 24 | 3.31 | 7.1 |
| measured | dr+cf0.3 | bayside | 24 | 0.74 | 2.36 |
| measured | dr+cf0.3 | blocks | 24 | 1.15 | 6.91 |
| measured | dr+cf0.3 | boulevard | 24 | 1.31 | 4.68 |
| measured | plain | bayside | 24 | 0.69 | 2.29 |
| measured | plain | blocks | 24 | 1.36 | 9.87 |
| measured | plain | boulevard | 24 | 1.81 | 4.76 |
| noise6 | cf0.3 | bayside | 24 | 0.69 | 2.33 |
| noise6 | cf0.3 | blocks | 24 | 1.29 | 10.21 |
| noise6 | cf0.3 | boulevard | 24 | 1.92 | 5.08 |
| noise6 | dr | bayside | 24 | 4.21 | 5.5 |
| noise6 | dr | blocks | 24 | 4.16 | 8.99 |
| noise6 | dr | boulevard | 24 | 4.73 | 9.71 |
| noise6 | dr+cf0.3 | bayside | 24 | 0.96 | 2.33 |
| noise6 | dr+cf0.3 | blocks | 24 | 1.31 | 7.04 |
| noise6 | dr+cf0.3 | boulevard | 24 | 1.61 | 5.71 |
| noise6 | plain | bayside | 24 | 3.71 | 5.29 |
| noise6 | plain | blocks | 24 | 3.87 | 10.57 |
| noise6 | plain | boulevard | 24 | 3.95 | 9.73 |
| noise8 | cf0.3 | bayside | 24 | 0.72 | 2.34 |
| noise8 | cf0.3 | blocks | 24 | 1.36 | 10.23 |
| noise8 | cf0.3 | boulevard | 24 | 1.94 | 5.27 |
| noise8 | dr | bayside | 24 | 3.74 | 5.38 |
| noise8 | dr | blocks | 24 | 3.91 | 10.88 |
| noise8 | dr | boulevard | 24 | 3.93 | 9.9 |
| noise8 | dr+cf0.3 | bayside | 24 | 1.42 | 3.17 |
| noise8 | dr+cf0.3 | blocks | 24 | 2.38 | 7.53 |
| noise8 | dr+cf0.3 | boulevard | 24 | 2.66 | 6.44 |
| noise8 | plain | bayside | 24 | 3.74 | 5.38 |
| noise8 | plain | blocks | 24 | 3.91 | 10.88 |
| noise8 | plain | boulevard | 24 | 3.91 | 9.9 |
| wheels0.85 | cf0.3 | bayside | 24 | 0.69 | 2.25 |
| wheels0.85 | cf0.3 | blocks | 24 | 1.25 | 10.06 |
| wheels0.85 | cf0.3 | boulevard | 24 | 1.77 | 5.0 |
| wheels0.85 | dr | bayside | 24 | 1.19 | 2.62 |
| wheels0.85 | dr | blocks | 24 | 2.18 | 7.57 |
| wheels0.85 | dr | boulevard | 24 | 3.31 | 7.1 |
| wheels0.85 | dr+cf0.3 | bayside | 24 | 0.74 | 2.36 |
| wheels0.85 | dr+cf0.3 | blocks | 24 | 1.15 | 6.91 |
| wheels0.85 | dr+cf0.3 | boulevard | 24 | 1.31 | 4.68 |
| wheels0.85 | plain | bayside | 24 | 0.69 | 2.29 |
| wheels0.85 | plain | blocks | 24 | 1.36 | 9.87 |
| wheels0.85 | plain | boulevard | 24 | 1.81 | 4.76 |

## Heading steered by against the true heading, while driving forward

| profile | variant | course | missions | median abs deg | RMS deg |
|---|---|---|---|---|---|
| dropout0.3 | cf0.3 | bayside | 24 | 2.96 | 5.89 |
| dropout0.3 | cf0.3 | blocks | 24 | 3.19 | 5.86 |
| dropout0.3 | cf0.3 | boulevard | 24 | 2.93 | 5.82 |
| dropout0.3 | dr | bayside | 24 | 24.91 | 25.2 |
| dropout0.3 | dr | blocks | 24 | 10.83 | 12.16 |
| dropout0.3 | dr | boulevard | 24 | 13.44 | 14.32 |
| dropout0.3 | dr+cf0.3 | bayside | 24 | 3.13 | 6.39 |
| dropout0.3 | dr+cf0.3 | blocks | 24 | 4.51 | 6.87 |
| dropout0.3 | dr+cf0.3 | boulevard | 24 | 4.79 | 6.54 |
| dropout0.3 | plain | bayside | 24 | 3.65 | 7.96 |
| dropout0.3 | plain | blocks | 24 | 4.07 | 7.57 |
| dropout0.3 | plain | boulevard | 24 | 3.46 | 6.83 |
| dropout0.3-noise8 | cf0.3 | bayside | 24 | 4.21 | 8.94 |
| dropout0.3-noise8 | cf0.3 | blocks | 24 | 4.56 | 8.27 |
| dropout0.3-noise8 | cf0.3 | boulevard | 24 | 3.8 | 7.38 |
| dropout0.3-noise8 | dr | bayside | 24 | 24.97 | 26.27 |
| dropout0.3-noise8 | dr | blocks | 24 | 24.98 | 26.34 |
| dropout0.3-noise8 | dr | boulevard | 24 | 24.98 | 26.31 |
| dropout0.3-noise8 | dr+cf0.3 | bayside | 24 | 21.74 | 22.27 |
| dropout0.3-noise8 | dr+cf0.3 | blocks | 24 | 15.99 | 16.86 |
| dropout0.3-noise8 | dr+cf0.3 | boulevard | 24 | 12.97 | 14.29 |
| dropout0.3-noise8 | plain | bayside | 24 | 24.97 | 26.27 |
| dropout0.3-noise8 | plain | blocks | 24 | 24.98 | 26.34 |
| dropout0.3-noise8 | plain | boulevard | 24 | 24.98 | 26.31 |
| measured | cf0.3 | bayside | 24 | 3.16 | 5.78 |
| measured | cf0.3 | blocks | 24 | 2.84 | 5.47 |
| measured | cf0.3 | boulevard | 24 | 2.9 | 5.37 |
| measured | dr | bayside | 24 | 7.6 | 9.46 |
| measured | dr | blocks | 24 | 7.96 | 12.49 |
| measured | dr | boulevard | 24 | 17.46 | 18.12 |
| measured | dr+cf0.3 | bayside | 24 | 4.45 | 6.62 |
| measured | dr+cf0.3 | blocks | 24 | 4.85 | 6.75 |
| measured | dr+cf0.3 | boulevard | 24 | 4.92 | 6.69 |
| measured | plain | bayside | 24 | 3.92 | 6.73 |
| measured | plain | blocks | 24 | 3.73 | 7.31 |
| measured | plain | boulevard | 24 | 3.7 | 7.35 |
| noise6 | cf0.3 | bayside | 24 | 3.41 | 6.33 |
| noise6 | cf0.3 | blocks | 24 | 3.28 | 6.45 |
| noise6 | cf0.3 | boulevard | 24 | 3.4 | 6.13 |
| noise6 | dr | bayside | 24 | 24.96 | 25.84 |
| noise6 | dr | blocks | 24 | 24.99 | 25.84 |
| noise6 | dr | boulevard | 24 | 25.02 | 25.86 |
| noise6 | dr+cf0.3 | bayside | 24 | 6.11 | 8.05 |
| noise6 | dr+cf0.3 | blocks | 24 | 5.56 | 7.69 |
| noise6 | dr+cf0.3 | boulevard | 24 | 6.88 | 8.25 |
| noise6 | plain | bayside | 24 | 24.96 | 25.7 |
| noise6 | plain | blocks | 24 | 24.9 | 25.69 |
| noise6 | plain | boulevard | 24 | 24.47 | 25.12 |
| noise8 | cf0.3 | bayside | 24 | 4.0 | 7.16 |
| noise8 | cf0.3 | blocks | 24 | 4.08 | 7.79 |
| noise8 | cf0.3 | boulevard | 24 | 3.9 | 7.16 |
| noise8 | dr | bayside | 24 | 24.98 | 26.3 |
| noise8 | dr | blocks | 24 | 24.97 | 26.28 |
| noise8 | dr | boulevard | 24 | 24.98 | 26.32 |
| noise8 | dr+cf0.3 | bayside | 24 | 8.43 | 10.09 |
| noise8 | dr+cf0.3 | blocks | 24 | 13.46 | 14.38 |
| noise8 | dr+cf0.3 | boulevard | 24 | 14.89 | 15.66 |
| noise8 | plain | bayside | 24 | 24.98 | 26.29 |
| noise8 | plain | blocks | 24 | 24.97 | 26.28 |
| noise8 | plain | boulevard | 24 | 24.98 | 26.32 |
| wheels0.85 | cf0.3 | bayside | 24 | 3.16 | 5.78 |
| wheels0.85 | cf0.3 | blocks | 24 | 2.84 | 5.47 |
| wheels0.85 | cf0.3 | boulevard | 24 | 2.9 | 5.37 |
| wheels0.85 | dr | bayside | 24 | 7.6 | 9.46 |
| wheels0.85 | dr | blocks | 24 | 7.96 | 12.49 |
| wheels0.85 | dr | boulevard | 24 | 17.46 | 18.12 |
| wheels0.85 | dr+cf0.3 | bayside | 24 | 4.45 | 6.62 |
| wheels0.85 | dr+cf0.3 | blocks | 24 | 4.85 | 6.75 |
| wheels0.85 | dr+cf0.3 | boulevard | 24 | 4.92 | 6.69 |
| wheels0.85 | plain | bayside | 24 | 3.92 | 6.73 |
| wheels0.85 | plain | blocks | 24 | 3.73 | 7.31 |
| wheels0.85 | plain | boulevard | 24 | 3.7 | 7.35 |
