# Should --smooth-heading be on by default? (simulated)

pace_f.py 0.1.0 (pace_e.py 0.1.0, pace_d.py 0.1.0, rover_pilot.py 0.12.1), MV2 of Munim, Inc. Every profile is pace_b.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, 3 deg of compass noise, a -25 deg compass error to learn) with one or two things changed: 4, 5, 6 or 8 deg of noise, a rover turning at 32 or 64 deg/s, commands landing after 1.0 s, or a -60 deg compass error. Variants: shipped; cf0.3 (--smooth-heading, which assumes 48 deg/s and 0.5 s). Seeds 13-36. 1584 of 1584 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_e.py's runs: 36 compared, 36 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio |
|---|---|---|---|---|---|---|
| measured | shipped | 72/72 | 0.878 | 0.988 | 72 | 1.003 |
| measured | cf0.3 | 72/72 | 0.879 | 0.989 | 72 | 1.003 |
| noise4 | shipped | 72/72 | 0.876 | 0.986 | 72 | 1.004 |
| noise4 | cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.004 |
| noise5 | shipped | 72/72 | 0.873 | 0.982 | 72 | 1.005 |
| noise5 | cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.004 |
| noise6 | shipped | 72/72 | 0.871 | 0.98 | 72 | 1.006 |
| noise6 | cf0.3 | 72/72 | 0.878 | 0.988 | 72 | 1.004 |
| yaw32 | shipped | 72/72 | 0.876 | 0.986 | 72 | 1.006 |
| yaw32 | cf0.3 | 72/72 | 0.877 | 0.986 | 72 | 1.006 |
| yaw64 | shipped | 72/72 | 0.877 | 0.987 | 72 | 1.003 |
| yaw64 | cf0.3 | 72/72 | 0.879 | 0.989 | 72 | 1.004 |
| lag1.0 | shipped | 72/72 | 0.872 | 0.981 | 72 | 1.007 |
| lag1.0 | cf0.3 | 72/72 | 0.875 | 0.985 | 72 | 1.006 |
| yaw32-noise8 | shipped | 72/72 | 0.866 | 0.974 | 72 | 1.006 |
| yaw32-noise8 | cf0.3 | 72/72 | 0.874 | 0.984 | 72 | 1.007 |
| yaw64-noise8 | shipped | 72/72 | 0.86 | 0.967 | 72 | 1.01 |
| yaw64-noise8 | cf0.3 | 72/72 | 0.875 | 0.985 | 72 | 1.006 |
| bias60 | shipped | 72/72 | 0.871 | 0.98 | 72 | 1.012 |
| bias60 | cf0.3 | 72/72 | 0.873 | 0.982 | 72 | 1.011 |
| bias60-noise8 | shipped | 72/72 | 0.577 | 0.649 | 0 | 1.507 |
| bias60-noise8 | cf0.3 | 72/72 | 0.869 | 0.978 | 72 | 1.013 |

## --smooth-heading against the shipped pilot, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|
| measured | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0014 |
| noise4 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0025 |
| noise5 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0068 |
| noise6 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0147 |
| yaw32 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0014 |
| yaw64 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0021 |
| lag1.0 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0041 |
| yaw32-noise8 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.017 |
| yaw64-noise8 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0231 |
| bias60 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0023 |
| bias60-noise8 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.3717 |

| profile | variant | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|
| measured | cf0.3 | bayside | 15 | 1 | -2.0 | -0.0014 | 0.0005 |
| measured | cf0.3 | blocks | 11 | 3 | 0.0 | 0.0 | 0.0574 |
| measured | cf0.3 | boulevard | 14 | 0 | -2.0 | -0.0011 | 0.0001 |
| noise4 | cf0.3 | bayside | 19 | 2 | -2.0 | -0.0014 | 0.0002 |
| noise4 | cf0.3 | blocks | 16 | 1 | -4.0 | -0.0025 | 0.0003 |
| noise4 | cf0.3 | boulevard | 17 | 0 | -4.0 | -0.0023 | 0.0 |
| noise5 | cf0.3 | bayside | 23 | 0 | -6.0 | -0.0042 | 0.0 |
| noise5 | cf0.3 | blocks | 18 | 1 | -11.0 | -0.0068 | 0.0001 |
| noise5 | cf0.3 | boulevard | 22 | 0 | -6.0 | -0.0034 | 0.0 |
| noise6 | cf0.3 | bayside | 24 | 0 | -10.0 | -0.0069 | 0.0 |
| noise6 | cf0.3 | blocks | 22 | 0 | -24.0 | -0.0147 | 0.0 |
| noise6 | cf0.3 | boulevard | 23 | 1 | -12.0 | -0.0068 | 0.0 |
| yaw32 | cf0.3 | bayside | 13 | 2 | -2.0 | -0.0014 | 0.0074 |
| yaw32 | cf0.3 | blocks | 8 | 6 | 0.0 | 0.0 | 0.7905 |
| yaw32 | cf0.3 | boulevard | 11 | 0 | 0.0 | 0.0 | 0.001 |
| yaw64 | cf0.3 | bayside | 21 | 1 | -3.0 | -0.0021 | 0.0 |
| yaw64 | cf0.3 | blocks | 15 | 3 | -3.0 | -0.0019 | 0.0075 |
| yaw64 | cf0.3 | boulevard | 8 | 3 | 0.0 | 0.0 | 0.2266 |
| lag1.0 | cf0.3 | bayside | 19 | 0 | -6.0 | -0.0041 | 0.0 |
| lag1.0 | cf0.3 | blocks | 18 | 1 | -5.0 | -0.0031 | 0.0001 |
| lag1.0 | cf0.3 | boulevard | 24 | 0 | -5.0 | -0.0028 | 0.0 |
| yaw32-noise8 | cf0.3 | bayside | 24 | 0 | -14.0 | -0.0096 | 0.0 |
| yaw32-noise8 | cf0.3 | blocks | 24 | 0 | -28.0 | -0.017 | 0.0 |
| yaw32-noise8 | cf0.3 | boulevard | 24 | 0 | -19.0 | -0.0106 | 0.0 |
| yaw64-noise8 | cf0.3 | bayside | 24 | 0 | -24.0 | -0.0164 | 0.0 |
| yaw64-noise8 | cf0.3 | blocks | 24 | 0 | -38.0 | -0.0231 | 0.0 |
| yaw64-noise8 | cf0.3 | boulevard | 24 | 0 | -32.0 | -0.0178 | 0.0 |
| bias60 | cf0.3 | bayside | 17 | 1 | -3.0 | -0.0021 | 0.0001 |
| bias60 | cf0.3 | blocks | 10 | 6 | 0.0 | 0.0 | 0.4545 |
| bias60 | cf0.3 | boulevard | 13 | 3 | -4.0 | -0.0023 | 0.0213 |
| bias60-noise8 | cf0.3 | bayside | 24 | 0 | -710.0 | -0.3271 | 0.0 |
| bias60-noise8 | cf0.3 | blocks | 24 | 0 | -955.0 | -0.3717 | 0.0 |
| bias60-noise8 | cf0.3 | boulevard | 24 | 0 | -743.0 | -0.2955 | 0.0 |

## The learner

| profile | variant | course | missions | median calibrations | missions with none | fits / mission | turned down | median abs bias error deg |
|---|---|---|---|---|---|---|---|---|
| bias60 | cf0.3 | bayside | 24 | 58.5 | 0 | 57.67 | 0.0 | 2.53 |
| bias60 | cf0.3 | blocks | 24 | 61.0 | 0 | 61.58 | 0.0 | 2.52 |
| bias60 | cf0.3 | boulevard | 24 | 79.0 | 0 | 77.96 | 0.0 | 2.35 |
| bias60 | shipped | bayside | 24 | 24.0 | 0 | 23.88 | 0.0 | 2.71 |
| bias60 | shipped | blocks | 24 | 23.5 | 0 | 24.17 | 0.0 | 2.52 |
| bias60 | shipped | boulevard | 24 | 32.5 | 0 | 33.29 | 0.0 | 3.29 |
| bias60-noise8 | cf0.3 | bayside | 24 | 23.5 | 0 | 23.12 | 0.0 | 3.41 |
| bias60-noise8 | cf0.3 | blocks | 24 | 25.0 | 0 | 25.25 | 0.0 | 3.53 |
| bias60-noise8 | cf0.3 | boulevard | 24 | 34.0 | 0 | 33.79 | 0.0 | 2.89 |
| bias60-noise8 | shipped | bayside | 24 | 0.0 | 22 | 0.08 | 0.0 | 60.0 |
| bias60-noise8 | shipped | blocks | 24 | 0.0 | 22 | 0.08 | 0.0 | 60.0 |
| bias60-noise8 | shipped | boulevard | 24 | 0.0 | 24 | 0.0 | None | 60.0 |
| lag1.0 | cf0.3 | bayside | 24 | 56.0 | 0 | 56.04 | 0.0 | 2.96 |
| lag1.0 | cf0.3 | blocks | 24 | 59.0 | 0 | 58.67 | 0.0 | 2.67 |
| lag1.0 | cf0.3 | boulevard | 24 | 75.5 | 0 | 74.83 | 0.0 | 3.0 |
| lag1.0 | shipped | bayside | 24 | 12.0 | 0 | 12.21 | 0.0 | 1.77 |
| lag1.0 | shipped | blocks | 24 | 11.0 | 0 | 11.21 | 0.0 | 2.27 |
| lag1.0 | shipped | boulevard | 24 | 14.5 | 0 | 15.33 | 0.0 | 2.73 |
| measured | cf0.3 | bayside | 24 | 58.0 | 0 | 59.04 | 0.0 | 2.88 |
| measured | cf0.3 | blocks | 24 | 61.0 | 0 | 61.17 | 0.0007 | 2.97 |
| measured | cf0.3 | boulevard | 24 | 79.0 | 0 | 78.04 | 0.0 | 1.65 |
| measured | shipped | bayside | 24 | 23.5 | 0 | 23.17 | 0.0 | 2.25 |
| measured | shipped | blocks | 24 | 23.5 | 0 | 23.62 | 0.0 | 2.73 |
| measured | shipped | boulevard | 24 | 33.0 | 0 | 33.04 | 0.0 | 3.5 |
| noise4 | cf0.3 | bayside | 24 | 54.0 | 0 | 54.83 | 0.0 | 2.19 |
| noise4 | cf0.3 | blocks | 24 | 57.0 | 0 | 56.75 | 0.0 | 1.23 |
| noise4 | cf0.3 | boulevard | 24 | 74.5 | 0 | 73.46 | 0.0 | 1.99 |
| noise4 | shipped | bayside | 24 | 9.0 | 0 | 8.54 | 0.0 | 2.87 |
| noise4 | shipped | blocks | 24 | 8.0 | 0 | 8.62 | 0.0 | 3.46 |
| noise4 | shipped | boulevard | 24 | 11.5 | 0 | 11.67 | 0.0 | 4.11 |
| noise5 | cf0.3 | bayside | 24 | 47.5 | 0 | 47.83 | 0.0009 | 2.26 |
| noise5 | cf0.3 | blocks | 24 | 51.0 | 0 | 50.83 | 0.0 | 2.17 |
| noise5 | cf0.3 | boulevard | 24 | 65.0 | 0 | 65.21 | 0.0 | 2.31 |
| noise5 | shipped | bayside | 24 | 2.0 | 3 | 2.17 | 0.0 | 4.67 |
| noise5 | shipped | blocks | 24 | 2.0 | 3 | 1.88 | 0.0 | 7.16 |
| noise5 | shipped | boulevard | 24 | 3.0 | 2 | 2.96 | 0.0 | 4.88 |
| noise6 | cf0.3 | bayside | 24 | 40.0 | 0 | 39.5 | 0.0 | 2.79 |
| noise6 | cf0.3 | blocks | 24 | 42.0 | 0 | 42.21 | 0.0 | 2.77 |
| noise6 | cf0.3 | boulevard | 24 | 56.5 | 0 | 56.29 | 0.0 | 2.79 |
| noise6 | shipped | bayside | 24 | 0.0 | 18 | 0.29 | 0.0 | 25.0 |
| noise6 | shipped | blocks | 24 | 0.0 | 20 | 0.29 | 0.0 | 25.0 |
| noise6 | shipped | boulevard | 24 | 0.0 | 17 | 0.38 | 0.0 | 25.0 |
| yaw32 | cf0.3 | bayside | 24 | 57.5 | 0 | 57.29 | 0.0 | 2.29 |
| yaw32 | cf0.3 | blocks | 24 | 55.0 | 0 | 54.62 | 0.0 | 1.69 |
| yaw32 | cf0.3 | boulevard | 24 | 79.5 | 0 | 77.96 | 0.0 | 2.75 |
| yaw32 | shipped | bayside | 24 | 22.0 | 0 | 22.08 | 0.0 | 3.27 |
| yaw32 | shipped | blocks | 24 | 24.0 | 0 | 23.92 | 0.0 | 2.94 |
| yaw32 | shipped | boulevard | 24 | 33.0 | 0 | 33.04 | 0.0 | 2.55 |
| yaw32-noise8 | cf0.3 | bayside | 24 | 23.5 | 0 | 23.62 | 0.0 | 3.06 |
| yaw32-noise8 | cf0.3 | blocks | 24 | 23.0 | 0 | 23.17 | 0.0 | 4.04 |
| yaw32-noise8 | cf0.3 | boulevard | 24 | 35.0 | 0 | 35.83 | 0.0 | 3.38 |
| yaw32-noise8 | shipped | bayside | 24 | 0.0 | 24 | 0.0 | None | 25.0 |
| yaw32-noise8 | shipped | blocks | 24 | 0.0 | 23 | 0.04 | 0.0 | 25.0 |
| yaw32-noise8 | shipped | boulevard | 24 | 0.0 | 24 | 0.0 | None | 25.0 |
| yaw64 | cf0.3 | bayside | 24 | 58.0 | 0 | 57.71 | 0.0 | 3.1 |
| yaw64 | cf0.3 | blocks | 24 | 61.0 | 0 | 61.12 | 0.002 | 3.05 |
| yaw64 | cf0.3 | boulevard | 24 | 77.5 | 0 | 76.83 | 0.0005 | 2.38 |
| yaw64 | shipped | bayside | 24 | 20.0 | 0 | 20.38 | 0.0 | 2.39 |
| yaw64 | shipped | blocks | 24 | 21.5 | 0 | 21.17 | 0.0 | 3.58 |
| yaw64 | shipped | boulevard | 24 | 26.0 | 0 | 26.67 | 0.0 | 2.56 |
| yaw64-noise8 | cf0.3 | bayside | 24 | 21.5 | 0 | 21.58 | 0.0 | 2.39 |
| yaw64-noise8 | cf0.3 | blocks | 24 | 22.5 | 0 | 22.42 | 0.0 | 1.94 |
| yaw64-noise8 | cf0.3 | boulevard | 24 | 30.0 | 0 | 29.75 | 0.0 | 3.13 |
| yaw64-noise8 | shipped | bayside | 24 | 0.0 | 24 | 0.0 | None | 25.0 |
| yaw64-noise8 | shipped | blocks | 24 | 0.0 | 24 | 0.0 | None | 25.0 |
| yaw64-noise8 | shipped | boulevard | 24 | 0.0 | 24 | 0.0 | None | 25.0 |

## Distance from the course while driving forward

Medians over the completed missions of each mission's median and 95th percentile; diff is --smooth-heading's median minus the shipped pilot's.

| profile | variant | course | missions | median m | p95 m | diff m |
|---|---|---|---|---|---|---|
| bias60 | cf0.3 | bayside | 24 | 0.71 | 2.48 | -0.01 |
| bias60 | cf0.3 | blocks | 24 | 1.32 | 10.47 | -0.03 |
| bias60 | cf0.3 | boulevard | 24 | 1.85 | 5.2 | -0.09 |
| bias60 | shipped | bayside | 24 | 0.72 | 2.83 |  |
| bias60 | shipped | blocks | 24 | 1.35 | 10.98 |  |
| bias60 | shipped | boulevard | 24 | 1.94 | 5.82 |  |
| bias60-noise8 | cf0.3 | bayside | 24 | 0.75 | 4.85 | -12.05 |
| bias60-noise8 | cf0.3 | blocks | 24 | 1.31 | 10.61 | -11.76 |
| bias60-noise8 | cf0.3 | boulevard | 24 | 1.9 | 5.7 | -11.06 |
| bias60-noise8 | shipped | bayside | 24 | 12.8 | 15.75 |  |
| bias60-noise8 | shipped | blocks | 24 | 13.07 | 16.76 |  |
| bias60-noise8 | shipped | boulevard | 24 | 12.96 | 18.75 |  |
| lag1.0 | cf0.3 | bayside | 24 | 0.73 | 2.27 | 0.04 |
| lag1.0 | cf0.3 | blocks | 24 | 1.27 | 10.01 | -0.24 |
| lag1.0 | cf0.3 | boulevard | 24 | 1.82 | 5.15 | -0.1 |
| lag1.0 | shipped | bayside | 24 | 0.69 | 3.09 |  |
| lag1.0 | shipped | blocks | 24 | 1.51 | 10.36 |  |
| lag1.0 | shipped | boulevard | 24 | 1.92 | 5.15 |  |
| measured | cf0.3 | bayside | 24 | 0.73 | 2.24 | 0.03 |
| measured | cf0.3 | blocks | 24 | 1.29 | 10.14 | -0.03 |
| measured | cf0.3 | boulevard | 24 | 1.9 | 5.38 | 0.05 |
| measured | shipped | bayside | 24 | 0.7 | 2.41 |  |
| measured | shipped | blocks | 24 | 1.32 | 10.11 |  |
| measured | shipped | boulevard | 24 | 1.85 | 4.97 |  |
| noise4 | cf0.3 | bayside | 24 | 0.71 | 2.17 | -0.03 |
| noise4 | cf0.3 | blocks | 24 | 1.23 | 10.44 | -0.25 |
| noise4 | cf0.3 | boulevard | 24 | 1.85 | 5.04 | -0.38 |
| noise4 | shipped | bayside | 24 | 0.74 | 3.61 |  |
| noise4 | shipped | blocks | 24 | 1.48 | 10.02 |  |
| noise4 | shipped | boulevard | 24 | 2.23 | 5.31 |  |
| noise5 | cf0.3 | bayside | 24 | 0.69 | 2.19 | -1.77 |
| noise5 | cf0.3 | blocks | 24 | 1.27 | 10.14 | -1.73 |
| noise5 | cf0.3 | boulevard | 24 | 1.88 | 5.35 | -0.41 |
| noise5 | shipped | bayside | 24 | 2.46 | 4.89 |  |
| noise5 | shipped | blocks | 24 | 3.0 | 10.54 |  |
| noise5 | shipped | boulevard | 24 | 2.29 | 6.76 |  |
| noise6 | cf0.3 | bayside | 24 | 0.71 | 2.19 | -2.99 |
| noise6 | cf0.3 | blocks | 24 | 1.25 | 10.2 | -2.6 |
| noise6 | cf0.3 | boulevard | 24 | 1.85 | 5.18 | -1.79 |
| noise6 | shipped | bayside | 24 | 3.7 | 5.16 |  |
| noise6 | shipped | blocks | 24 | 3.85 | 10.82 |  |
| noise6 | shipped | boulevard | 24 | 3.64 | 10.04 |  |
| yaw32 | cf0.3 | bayside | 24 | 0.77 | 2.41 | 0.06 |
| yaw32 | cf0.3 | blocks | 24 | 1.42 | 10.3 | 0.07 |
| yaw32 | cf0.3 | boulevard | 24 | 1.77 | 5.16 | -0.15 |
| yaw32 | shipped | bayside | 24 | 0.71 | 2.46 |  |
| yaw32 | shipped | blocks | 24 | 1.35 | 10.07 |  |
| yaw32 | shipped | boulevard | 24 | 1.92 | 5.12 |  |
| yaw32-noise8 | cf0.3 | bayside | 24 | 0.77 | 2.88 | -2.92 |
| yaw32-noise8 | cf0.3 | blocks | 24 | 1.51 | 10.31 | -2.37 |
| yaw32-noise8 | cf0.3 | boulevard | 24 | 1.85 | 5.5 | -1.93 |
| yaw32-noise8 | shipped | bayside | 24 | 3.69 | 5.36 |  |
| yaw32-noise8 | shipped | blocks | 24 | 3.88 | 10.71 |  |
| yaw32-noise8 | shipped | boulevard | 24 | 3.78 | 9.97 |  |
| yaw64 | cf0.3 | bayside | 24 | 0.69 | 2.21 | 0.0 |
| yaw64 | cf0.3 | blocks | 24 | 1.17 | 10.05 | -0.1 |
| yaw64 | cf0.3 | boulevard | 24 | 1.79 | 5.07 | -0.02 |
| yaw64 | shipped | bayside | 24 | 0.69 | 2.59 |  |
| yaw64 | shipped | blocks | 24 | 1.27 | 9.95 |  |
| yaw64 | shipped | boulevard | 24 | 1.81 | 5.02 |  |
| yaw64-noise8 | cf0.3 | bayside | 24 | 0.72 | 2.71 | -2.97 |
| yaw64-noise8 | cf0.3 | blocks | 24 | 1.27 | 9.88 | -2.57 |
| yaw64-noise8 | cf0.3 | boulevard | 24 | 1.86 | 4.91 | -1.81 |
| yaw64-noise8 | shipped | bayside | 24 | 3.69 | 5.2 |  |
| yaw64-noise8 | shipped | blocks | 24 | 3.84 | 10.84 |  |
| yaw64-noise8 | shipped | boulevard | 24 | 3.67 | 9.81 |  |

## Heading steered by against the true heading, while driving forward

| profile | variant | course | missions | median abs deg | RMS deg |
|---|---|---|---|---|---|
| bias60 | cf0.3 | bayside | 24 | 2.92 | 9.93 |
| bias60 | cf0.3 | blocks | 24 | 3.21 | 9.41 |
| bias60 | cf0.3 | boulevard | 24 | 2.84 | 8.98 |
| bias60 | shipped | bayside | 24 | 3.86 | 11.38 |
| bias60 | shipped | blocks | 24 | 4.03 | 11.18 |
| bias60 | shipped | boulevard | 24 | 3.75 | 10.91 |
| bias60-noise8 | cf0.3 | bayside | 24 | 3.96 | 13.29 |
| bias60-noise8 | cf0.3 | blocks | 24 | 4.12 | 11.22 |
| bias60-noise8 | cf0.3 | boulevard | 24 | 3.74 | 10.74 |
| bias60-noise8 | shipped | bayside | 24 | 59.75 | 60.26 |
| bias60-noise8 | shipped | blocks | 24 | 59.64 | 60.2 |
| bias60-noise8 | shipped | boulevard | 24 | 59.7 | 60.26 |
| lag1.0 | cf0.3 | bayside | 24 | 2.8 | 5.62 |
| lag1.0 | cf0.3 | blocks | 24 | 3.02 | 5.75 |
| lag1.0 | cf0.3 | boulevard | 24 | 3.11 | 5.51 |
| lag1.0 | shipped | bayside | 24 | 3.58 | 7.8 |
| lag1.0 | shipped | blocks | 24 | 4.5 | 8.61 |
| lag1.0 | shipped | boulevard | 24 | 4.0 | 7.64 |
| measured | cf0.3 | bayside | 24 | 2.97 | 5.39 |
| measured | cf0.3 | blocks | 24 | 3.01 | 5.58 |
| measured | cf0.3 | boulevard | 24 | 3.04 | 5.5 |
| measured | shipped | bayside | 24 | 3.75 | 6.6 |
| measured | shipped | blocks | 24 | 3.65 | 6.93 |
| measured | shipped | boulevard | 24 | 3.71 | 6.96 |
| noise4 | cf0.3 | bayside | 24 | 2.91 | 5.54 |
| noise4 | cf0.3 | blocks | 24 | 2.88 | 5.48 |
| noise4 | cf0.3 | boulevard | 24 | 3.08 | 5.66 |
| noise4 | shipped | bayside | 24 | 4.46 | 9.53 |
| noise4 | shipped | blocks | 24 | 5.03 | 9.84 |
| noise4 | shipped | boulevard | 24 | 5.02 | 9.59 |
| noise5 | cf0.3 | bayside | 24 | 3.22 | 5.81 |
| noise5 | cf0.3 | blocks | 24 | 3.42 | 5.92 |
| noise5 | cf0.3 | boulevard | 24 | 3.17 | 5.81 |
| noise5 | shipped | bayside | 24 | 16.85 | 19.18 |
| noise5 | shipped | blocks | 24 | 11.38 | 17.11 |
| noise5 | shipped | boulevard | 24 | 8.67 | 14.22 |
| noise6 | cf0.3 | bayside | 24 | 3.41 | 6.1 |
| noise6 | cf0.3 | blocks | 24 | 3.6 | 6.2 |
| noise6 | cf0.3 | boulevard | 24 | 3.42 | 6.41 |
| noise6 | shipped | bayside | 24 | 24.94 | 25.71 |
| noise6 | shipped | blocks | 24 | 24.93 | 25.7 |
| noise6 | shipped | boulevard | 24 | 24.92 | 25.67 |
| yaw32 | cf0.3 | bayside | 24 | 3.0 | 5.92 |
| yaw32 | cf0.3 | blocks | 24 | 2.74 | 5.62 |
| yaw32 | cf0.3 | boulevard | 24 | 2.75 | 5.54 |
| yaw32 | shipped | bayside | 24 | 3.44 | 6.61 |
| yaw32 | shipped | blocks | 24 | 3.61 | 6.68 |
| yaw32 | shipped | boulevard | 24 | 3.51 | 6.36 |
| yaw32-noise8 | cf0.3 | bayside | 24 | 3.78 | 7.53 |
| yaw32-noise8 | cf0.3 | blocks | 24 | 4.31 | 7.73 |
| yaw32-noise8 | cf0.3 | boulevard | 24 | 3.96 | 7.2 |
| yaw32-noise8 | shipped | bayside | 24 | 24.95 | 26.24 |
| yaw32-noise8 | shipped | blocks | 24 | 24.91 | 26.22 |
| yaw32-noise8 | shipped | boulevard | 24 | 24.98 | 26.21 |
| yaw64 | cf0.3 | bayside | 24 | 3.19 | 5.75 |
| yaw64 | cf0.3 | blocks | 24 | 2.85 | 5.62 |
| yaw64 | cf0.3 | boulevard | 24 | 2.96 | 5.3 |
| yaw64 | shipped | bayside | 24 | 3.71 | 7.49 |
| yaw64 | shipped | blocks | 24 | 3.83 | 7.72 |
| yaw64 | shipped | boulevard | 24 | 3.71 | 7.22 |
| yaw64-noise8 | cf0.3 | bayside | 24 | 4.32 | 7.69 |
| yaw64-noise8 | cf0.3 | blocks | 24 | 4.36 | 7.8 |
| yaw64-noise8 | cf0.3 | boulevard | 24 | 4.23 | 7.92 |
| yaw64-noise8 | shipped | bayside | 24 | 24.95 | 26.35 |
| yaw64-noise8 | shipped | blocks | 24 | 24.93 | 26.35 |
| yaw64-noise8 | shipped | boulevard | 24 | 24.94 | 26.31 |
