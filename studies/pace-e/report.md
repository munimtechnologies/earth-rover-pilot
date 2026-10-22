# What the compass-bias learner does under noise (simulated)

pace_e.py 0.1.0 (pace_d.py 0.1.0, pace_c.py 0.1.0, pace_b.py 0.1.0, pace_study.py 0.1.0, rover_pilot.py 0.12.0), MV2 of Munim, Inc. Every profile is pace_b.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, a -25 deg compass error to learn) with 3, 6, 8, 10 or 12 deg of compass noise, or pace_d.py's drift10. Variants: shipped; cf0.3 (--smooth-heading); spread0.95, straight0.3 and both (the learner's gates loosened). Seeds 1-12. 1080 of 1080 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_d.py's runs: 216 compared, 216 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | cruise | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio |
|---|---|---|---|---|---|---|---|
| measured | shipped | 0.8 | 36/36 | 0.878 | 0.988 | 36 | 1.003 |
| measured | cf0.3 | 0.8 | 36/36 | 0.878 | 0.988 | 36 | 1.004 |
| measured | spread0.95 | 0.8 | 36/36 | 0.878 | 0.988 | 36 | 1.003 |
| measured | straight0.3 | 0.8 | 36/36 | 0.874 | 0.984 | 36 | 1.005 |
| measured | both | 0.8 | 36/36 | 0.875 | 0.984 | 36 | 1.005 |
| noise6 | shipped | 0.8 | 36/36 | 0.869 | 0.978 | 36 | 1.006 |
| noise6 | cf0.3 | 0.8 | 36/36 | 0.878 | 0.988 | 36 | 1.004 |
| noise6 | spread0.95 | 0.8 | 36/36 | 0.869 | 0.978 | 36 | 1.006 |
| noise6 | straight0.3 | 0.8 | 36/36 | 0.868 | 0.977 | 36 | 1.006 |
| noise6 | both | 0.8 | 36/36 | 0.868 | 0.977 | 36 | 1.007 |
| noise8 | shipped | 0.8 | 36/36 | 0.863 | 0.971 | 36 | 1.007 |
| noise8 | cf0.3 | 0.8 | 36/36 | 0.876 | 0.986 | 36 | 1.004 |
| noise8 | spread0.95 | 0.8 | 36/36 | 0.863 | 0.971 | 36 | 1.007 |
| noise8 | straight0.3 | 0.8 | 36/36 | 0.863 | 0.971 | 36 | 1.007 |
| noise8 | both | 0.8 | 36/36 | 0.862 | 0.97 | 36 | 1.007 |
| measured-noise10 | shipped | 0.8 | 36/36 | 0.855 | 0.962 | 36 | 1.009 |
| measured-noise10 | cf0.3 | 0.8 | 36/36 | 0.874 | 0.984 | 36 | 1.005 |
| measured-noise10 | spread0.95 | 0.8 | 36/36 | 0.855 | 0.962 | 36 | 1.009 |
| measured-noise10 | straight0.3 | 0.8 | 36/36 | 0.855 | 0.962 | 36 | 1.009 |
| measured-noise10 | both | 0.8 | 36/36 | 0.855 | 0.962 | 36 | 1.009 |
| noise12 | shipped | 0.8 | 36/36 | 0.845 | 0.951 | 36 | 1.012 |
| noise12 | cf0.3 | 0.8 | 36/36 | 0.873 | 0.982 | 36 | 1.006 |
| noise12 | spread0.95 | 0.8 | 36/36 | 0.845 | 0.951 | 36 | 1.012 |
| noise12 | straight0.3 | 0.8 | 36/36 | 0.846 | 0.951 | 36 | 1.011 |
| noise12 | both | 0.8 | 36/36 | 0.845 | 0.951 | 36 | 1.012 |
| drift10 | shipped | 0.8 | 36/36 | 0.873 | 0.982 | 36 | 1.007 |
| drift10 | cf0.3 | 0.8 | 36/36 | 0.874 | 0.983 | 36 | 1.007 |
| drift10 | spread0.95 | 0.8 | 36/36 | 0.873 | 0.982 | 36 | 1.007 |
| drift10 | straight0.3 | 0.8 | 36/36 | 0.871 | 0.98 | 36 | 1.009 |
| drift10 | both | 0.8 | 36/36 | 0.87 | 0.979 | 36 | 1.01 |

## The learner

Per mission: calibrations (fits it used), stretches broken off, fits that reached the spread test; the share of those it turned down; the median spread of a checked fit; and |bias error| at the end (0 = the compass error fully cancelled).

| profile | variant | course | missions | median calibrations | missions with none | fits / mission | spread checks / mission | turned down | median spread | median breaks | median abs bias error deg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| drift10 | both | bayside | 12 | 99.5 | 0 | 99.83 | 99.83 | 0.0 | 0.995 | 3.5 | 5.28 |
| drift10 | both | blocks | 12 | 103.0 | 0 | 103.67 | 103.67 | 0.0129 | 0.9947 | 25.0 | 4.89 |
| drift10 | both | boulevard | 12 | 122.5 | 0 | 122.58 | 122.58 | 0.0 | 0.9955 | 6.5 | 4.08 |
| drift10 | cf0.3 | bayside | 12 | 55.0 | 0 | 56.0 | 56.0 | 0.003 | 0.9985 | 110.5 | 5.86 |
| drift10 | cf0.3 | blocks | 12 | 54.5 | 0 | 54.25 | 54.25 | 0.0015 | 0.9986 | 143.0 | 3.71 |
| drift10 | cf0.3 | boulevard | 12 | 76.5 | 0 | 76.92 | 76.92 | 0.0 | 0.9985 | 119.0 | 4.24 |
| drift10 | shipped | bayside | 12 | 16.5 | 0 | 16.17 | 16.17 | 0.0 | 0.9974 | 248.0 | 4.8 |
| drift10 | shipped | blocks | 12 | 18.5 | 0 | 17.67 | 17.67 | 0.0 | 0.9977 | 286.5 | 3.25 |
| drift10 | shipped | boulevard | 12 | 22.0 | 0 | 23.0 | 23.0 | 0.0 | 0.9974 | 283.5 | 5.91 |
| drift10 | spread0.95 | bayside | 12 | 16.5 | 0 | 16.17 | 16.17 | 0.0 | 0.9974 | 248.0 | 4.8 |
| drift10 | spread0.95 | blocks | 12 | 18.5 | 0 | 17.67 | 17.67 | 0.0 | 0.9977 | 286.5 | 3.25 |
| drift10 | spread0.95 | boulevard | 12 | 22.0 | 0 | 23.0 | 23.0 | 0.0 | 0.9974 | 283.5 | 5.91 |
| drift10 | straight0.3 | bayside | 12 | 96.5 | 0 | 99.83 | 99.83 | 0.0351 | 0.995 | 3.5 | 5.86 |
| drift10 | straight0.3 | blocks | 12 | 94.0 | 0 | 104.17 | 104.17 | 0.0904 | 0.9948 | 25.0 | 3.46 |
| drift10 | straight0.3 | boulevard | 12 | 120.5 | 0 | 122.58 | 122.58 | 0.0163 | 0.9955 | 6.0 | 4.5 |
| measured | both | bayside | 12 | 99.5 | 0 | 99.67 | 99.67 | 0.0 | 0.9955 | 3.5 | 2.75 |
| measured | both | blocks | 12 | 104.0 | 0 | 104.08 | 104.08 | 0.0064 | 0.9953 | 24.5 | 3.5 |
| measured | both | boulevard | 12 | 121.5 | 0 | 122.08 | 122.08 | 0.0 | 0.9961 | 6.0 | 2.49 |
| measured | cf0.3 | bayside | 12 | 60.5 | 0 | 60.08 | 60.08 | 0.0 | 0.9985 | 96.0 | 2.74 |
| measured | cf0.3 | blocks | 12 | 60.0 | 0 | 60.42 | 60.42 | 0.0014 | 0.9986 | 128.5 | 3.17 |
| measured | cf0.3 | boulevard | 12 | 82.0 | 0 | 82.5 | 82.5 | 0.0 | 0.9986 | 100.5 | 3.2 |
| measured | shipped | bayside | 12 | 23.5 | 0 | 23.17 | 23.17 | 0.0 | 0.9977 | 217.5 | 2.21 |
| measured | shipped | blocks | 12 | 24.0 | 0 | 24.42 | 24.42 | 0.0 | 0.9976 | 253.5 | 2.99 |
| measured | shipped | boulevard | 12 | 33.0 | 0 | 33.33 | 33.33 | 0.0 | 0.9977 | 247.5 | 2.85 |
| measured | spread0.95 | bayside | 12 | 23.5 | 0 | 23.17 | 23.17 | 0.0 | 0.9977 | 217.5 | 2.21 |
| measured | spread0.95 | blocks | 12 | 24.0 | 0 | 24.42 | 24.42 | 0.0 | 0.9976 | 253.5 | 2.99 |
| measured | spread0.95 | boulevard | 12 | 33.0 | 0 | 33.33 | 33.33 | 0.0 | 0.9977 | 247.5 | 2.85 |
| measured | straight0.3 | bayside | 12 | 98.0 | 0 | 99.92 | 99.92 | 0.0267 | 0.9955 | 3.0 | 2.46 |
| measured | straight0.3 | blocks | 12 | 94.0 | 0 | 104.17 | 104.17 | 0.0944 | 0.9953 | 25.0 | 3.2 |
| measured | straight0.3 | boulevard | 12 | 121.5 | 0 | 122.25 | 122.25 | 0.0143 | 0.9961 | 5.5 | 2.52 |
| measured-noise10 | both | bayside | 12 | 52.5 | 0 | 52.17 | 52.17 | 0.0 | 0.9822 | 128.5 | 2.66 |
| measured-noise10 | both | blocks | 12 | 52.0 | 0 | 50.42 | 50.42 | 0.0033 | 0.9822 | 165.0 | 3.58 |
| measured-noise10 | both | boulevard | 12 | 63.5 | 0 | 64.17 | 64.17 | 0.0 | 0.983 | 159.5 | 2.83 |
| measured-noise10 | cf0.3 | bayside | 12 | 13.0 | 0 | 13.42 | 13.42 | 0.0 | 0.9977 | 272.0 | 3.2 |
| measured-noise10 | cf0.3 | blocks | 12 | 12.0 | 0 | 12.0 | 12.0 | 0.0 | 0.9979 | 310.0 | 5.02 |
| measured-noise10 | cf0.3 | boulevard | 12 | 18.0 | 0 | 17.42 | 17.42 | 0.0 | 0.9978 | 323.0 | 2.45 |
| measured-noise10 | shipped | bayside | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.9958 | 799.0 | 25.0 |
| measured-noise10 | shipped | blocks | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 888.0 | 25.0 |
| measured-noise10 | shipped | boulevard | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 987.5 | 25.0 |
| measured-noise10 | spread0.95 | bayside | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.9958 | 799.0 | 25.0 |
| measured-noise10 | spread0.95 | blocks | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 888.0 | 25.0 |
| measured-noise10 | spread0.95 | boulevard | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 987.5 | 25.0 |
| measured-noise10 | straight0.3 | bayside | 12 | 13.5 | 0 | 52.75 | 52.75 | 0.7362 | 0.9821 | 123.0 | 2.48 |
| measured-noise10 | straight0.3 | blocks | 12 | 12.5 | 0 | 51.83 | 51.83 | 0.7492 | 0.9819 | 162.0 | 3.85 |
| measured-noise10 | straight0.3 | boulevard | 12 | 19.5 | 0 | 65.92 | 65.92 | 0.7067 | 0.9831 | 154.0 | 2.25 |
| noise12 | both | bayside | 12 | 24.5 | 0 | 25.58 | 25.58 | 0.0 | 0.9796 | 237.0 | 2.95 |
| noise12 | both | blocks | 12 | 25.5 | 0 | 26.08 | 26.08 | 0.0 | 0.978 | 271.5 | 3.62 |
| noise12 | both | boulevard | 12 | 35.0 | 0 | 33.5 | 33.5 | 0.0 | 0.9794 | 288.0 | 4.29 |
| noise12 | cf0.3 | bayside | 12 | 5.0 | 0 | 5.08 | 5.08 | 0.0 | 0.9977 | 339.0 | 3.9 |
| noise12 | cf0.3 | blocks | 12 | 4.0 | 0 | 4.17 | 4.17 | 0.0 | 0.9974 | 379.5 | 3.45 |
| noise12 | cf0.3 | boulevard | 12 | 8.0 | 0 | 7.92 | 7.92 | 0.0 | 0.9977 | 407.5 | 2.6 |
| noise12 | shipped | bayside | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 880.5 | 25.0 |
| noise12 | shipped | blocks | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 963.0 | 25.0 |
| noise12 | shipped | boulevard | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 1076.0 | 25.0 |
| noise12 | spread0.95 | bayside | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 880.5 | 25.0 |
| noise12 | spread0.95 | blocks | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 963.0 | 25.0 |
| noise12 | spread0.95 | boulevard | 12 | 0.0 | 12 | 0.0 | 0.0 | None | None | 1076.0 | 25.0 |
| noise12 | straight0.3 | bayside | 12 | 2.0 | 0 | 24.83 | 24.83 | 0.8926 | 0.98 | 230.0 | 4.15 |
| noise12 | straight0.3 | blocks | 12 | 3.0 | 0 | 26.25 | 26.25 | 0.8825 | 0.9789 | 278.5 | 4.0 |
| noise12 | straight0.3 | boulevard | 12 | 4.0 | 0 | 33.0 | 33.0 | 0.8611 | 0.9795 | 279.5 | 4.18 |
| noise6 | both | bayside | 12 | 95.5 | 0 | 95.75 | 95.75 | 0.0 | 0.99 | 12.5 | 3.1 |
| noise6 | both | blocks | 12 | 100.0 | 0 | 99.08 | 99.08 | 0.0067 | 0.9901 | 38.5 | 1.78 |
| noise6 | both | boulevard | 12 | 118.0 | 0 | 118.67 | 118.67 | 0.0 | 0.9906 | 15.0 | 3.59 |
| noise6 | cf0.3 | bayside | 12 | 43.0 | 0 | 41.5 | 41.5 | 0.002 | 0.9981 | 144.0 | 3.48 |
| noise6 | cf0.3 | blocks | 12 | 41.0 | 0 | 41.17 | 41.17 | 0.0 | 0.9982 | 178.5 | 4.86 |
| noise6 | cf0.3 | boulevard | 12 | 57.5 | 0 | 57.33 | 57.33 | 0.0 | 0.9982 | 166.0 | 2.73 |
| noise6 | shipped | bayside | 12 | 0.0 | 8 | 0.5 | 0.5 | 0.0 | 0.9963 | 541.0 | 25.0 |
| noise6 | shipped | blocks | 12 | 0.5 | 6 | 0.58 | 0.58 | 0.0 | 0.9963 | 599.0 | 22.88 |
| noise6 | shipped | boulevard | 12 | 1.0 | 5 | 0.67 | 0.67 | 0.0 | 0.9968 | 651.0 | 20.23 |
| noise6 | spread0.95 | bayside | 12 | 0.0 | 8 | 0.5 | 0.5 | 0.0 | 0.9963 | 541.0 | 25.0 |
| noise6 | spread0.95 | blocks | 12 | 0.5 | 6 | 0.58 | 0.58 | 0.0 | 0.9963 | 599.0 | 22.88 |
| noise6 | spread0.95 | boulevard | 12 | 1.0 | 5 | 0.67 | 0.67 | 0.0 | 0.9968 | 651.0 | 20.23 |
| noise6 | straight0.3 | bayside | 12 | 85.0 | 0 | 95.42 | 95.42 | 0.1118 | 0.9903 | 13.5 | 3.04 |
| noise6 | straight0.3 | blocks | 12 | 83.0 | 0 | 98.83 | 98.83 | 0.1644 | 0.99 | 37.0 | 2.38 |
| noise6 | straight0.3 | boulevard | 12 | 109.0 | 0 | 119.0 | 119.0 | 0.0854 | 0.9906 | 16.0 | 3.38 |
| noise8 | both | bayside | 12 | 78.5 | 0 | 79.5 | 79.5 | 0.0 | 0.9858 | 52.0 | 2.96 |
| noise8 | both | blocks | 12 | 82.0 | 0 | 82.75 | 82.75 | 0.004 | 0.9856 | 80.0 | 1.08 |
| noise8 | both | boulevard | 12 | 99.5 | 0 | 99.42 | 99.42 | 0.0 | 0.9864 | 61.0 | 3.8 |
| noise8 | cf0.3 | bayside | 12 | 25.0 | 0 | 25.42 | 25.42 | 0.0 | 0.998 | 209.0 | 2.33 |
| noise8 | cf0.3 | blocks | 12 | 26.0 | 0 | 26.33 | 26.33 | 0.0 | 0.998 | 239.0 | 3.82 |
| noise8 | cf0.3 | boulevard | 12 | 36.0 | 0 | 34.33 | 34.33 | 0.0 | 0.998 | 235.5 | 2.06 |
| noise8 | shipped | bayside | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.9972 | 700.5 | 25.0 |
| noise8 | shipped | blocks | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.9972 | 764.0 | 25.0 |
| noise8 | shipped | boulevard | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.997 | 854.5 | 25.0 |
| noise8 | spread0.95 | bayside | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.9972 | 700.5 | 25.0 |
| noise8 | spread0.95 | blocks | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.9972 | 764.0 | 25.0 |
| noise8 | spread0.95 | boulevard | 12 | 0.0 | 11 | 0.08 | 0.08 | 0.0 | 0.997 | 854.5 | 25.0 |
| noise8 | straight0.3 | bayside | 12 | 46.5 | 0 | 79.42 | 79.42 | 0.425 | 0.9858 | 51.5 | 2.67 |
| noise8 | straight0.3 | blocks | 12 | 48.5 | 0 | 83.83 | 83.83 | 0.4344 | 0.9858 | 79.0 | 2.69 |
| noise8 | straight0.3 | boulevard | 12 | 66.0 | 0 | 99.75 | 99.75 | 0.3425 | 0.9864 | 61.5 | 3.44 |

## Distance from the course while driving forward

Medians over the completed missions of each mission's median and 95th percentile.

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| drift10 | both | bayside | 12 | 0.95 | 2.76 |
| drift10 | both | blocks | 12 | 1.65 | 9.79 |
| drift10 | both | boulevard | 12 | 1.82 | 5.34 |
| drift10 | cf0.3 | bayside | 12 | 1.02 | 3.05 |
| drift10 | cf0.3 | blocks | 12 | 1.65 | 10.11 |
| drift10 | cf0.3 | boulevard | 12 | 2.03 | 5.5 |
| drift10 | shipped | bayside | 12 | 1.33 | 3.62 |
| drift10 | shipped | blocks | 12 | 2.04 | 9.89 |
| drift10 | shipped | boulevard | 12 | 2.09 | 6.33 |
| drift10 | spread0.95 | bayside | 12 | 1.33 | 3.62 |
| drift10 | spread0.95 | blocks | 12 | 2.04 | 9.89 |
| drift10 | spread0.95 | boulevard | 12 | 2.09 | 6.33 |
| drift10 | straight0.3 | bayside | 12 | 0.95 | 2.77 |
| drift10 | straight0.3 | blocks | 12 | 1.64 | 10.0 |
| drift10 | straight0.3 | boulevard | 12 | 1.9 | 5.25 |
| measured | both | bayside | 12 | 0.7 | 2.15 |
| measured | both | blocks | 12 | 1.36 | 10.23 |
| measured | both | boulevard | 12 | 1.81 | 5.04 |
| measured | cf0.3 | bayside | 12 | 0.68 | 2.21 |
| measured | cf0.3 | blocks | 12 | 1.29 | 10.15 |
| measured | cf0.3 | boulevard | 12 | 1.83 | 4.91 |
| measured | shipped | bayside | 12 | 0.64 | 2.34 |
| measured | shipped | blocks | 12 | 1.31 | 10.47 |
| measured | shipped | boulevard | 12 | 1.9 | 5.02 |
| measured | spread0.95 | bayside | 12 | 0.64 | 2.34 |
| measured | spread0.95 | blocks | 12 | 1.31 | 10.47 |
| measured | spread0.95 | boulevard | 12 | 1.9 | 5.02 |
| measured | straight0.3 | bayside | 12 | 0.69 | 2.17 |
| measured | straight0.3 | blocks | 12 | 1.34 | 10.17 |
| measured | straight0.3 | boulevard | 12 | 1.79 | 4.91 |
| measured-noise10 | both | bayside | 12 | 0.83 | 2.4 |
| measured-noise10 | both | blocks | 12 | 1.36 | 10.59 |
| measured-noise10 | both | boulevard | 12 | 1.69 | 4.9 |
| measured-noise10 | cf0.3 | bayside | 12 | 0.72 | 2.55 |
| measured-noise10 | cf0.3 | blocks | 12 | 1.55 | 10.09 |
| measured-noise10 | cf0.3 | boulevard | 12 | 1.89 | 5.06 |
| measured-noise10 | shipped | bayside | 12 | 3.69 | 5.32 |
| measured-noise10 | shipped | blocks | 12 | 3.88 | 10.64 |
| measured-noise10 | shipped | boulevard | 12 | 3.71 | 9.92 |
| measured-noise10 | spread0.95 | bayside | 12 | 3.69 | 5.32 |
| measured-noise10 | spread0.95 | blocks | 12 | 3.88 | 10.64 |
| measured-noise10 | spread0.95 | boulevard | 12 | 3.71 | 9.92 |
| measured-noise10 | straight0.3 | bayside | 12 | 0.72 | 2.88 |
| measured-noise10 | straight0.3 | blocks | 12 | 1.71 | 10.16 |
| measured-noise10 | straight0.3 | boulevard | 12 | 1.77 | 5.0 |
| noise12 | both | bayside | 12 | 0.78 | 2.85 |
| noise12 | both | blocks | 12 | 1.5 | 9.62 |
| noise12 | both | boulevard | 12 | 1.56 | 5.02 |
| noise12 | cf0.3 | bayside | 12 | 1.01 | 4.04 |
| noise12 | cf0.3 | blocks | 12 | 2.24 | 10.29 |
| noise12 | cf0.3 | boulevard | 12 | 2.04 | 5.1 |
| noise12 | shipped | bayside | 12 | 3.7 | 5.31 |
| noise12 | shipped | blocks | 12 | 3.92 | 11.06 |
| noise12 | shipped | boulevard | 12 | 3.85 | 9.93 |
| noise12 | spread0.95 | bayside | 12 | 3.7 | 5.31 |
| noise12 | spread0.95 | blocks | 12 | 3.92 | 11.06 |
| noise12 | spread0.95 | boulevard | 12 | 3.85 | 9.93 |
| noise12 | straight0.3 | bayside | 12 | 1.79 | 4.81 |
| noise12 | straight0.3 | blocks | 12 | 2.88 | 10.61 |
| noise12 | straight0.3 | boulevard | 12 | 2.5 | 6.08 |
| noise6 | both | bayside | 12 | 0.69 | 2.06 |
| noise6 | both | blocks | 12 | 1.27 | 9.98 |
| noise6 | both | boulevard | 12 | 1.69 | 4.91 |
| noise6 | cf0.3 | bayside | 12 | 0.64 | 2.21 |
| noise6 | cf0.3 | blocks | 12 | 1.25 | 10.22 |
| noise6 | cf0.3 | boulevard | 12 | 1.81 | 4.96 |
| noise6 | shipped | bayside | 12 | 3.63 | 5.17 |
| noise6 | shipped | blocks | 12 | 3.83 | 10.81 |
| noise6 | shipped | boulevard | 12 | 3.71 | 9.54 |
| noise6 | spread0.95 | bayside | 12 | 3.63 | 5.17 |
| noise6 | spread0.95 | blocks | 12 | 3.83 | 10.81 |
| noise6 | spread0.95 | boulevard | 12 | 3.71 | 9.54 |
| noise6 | straight0.3 | bayside | 12 | 0.7 | 2.21 |
| noise6 | straight0.3 | blocks | 12 | 1.32 | 10.03 |
| noise6 | straight0.3 | boulevard | 12 | 1.75 | 5.0 |
| noise8 | both | bayside | 12 | 0.72 | 2.16 |
| noise8 | both | blocks | 12 | 1.29 | 10.14 |
| noise8 | both | boulevard | 12 | 1.77 | 4.89 |
| noise8 | cf0.3 | bayside | 12 | 0.67 | 2.37 |
| noise8 | cf0.3 | blocks | 12 | 1.21 | 9.89 |
| noise8 | cf0.3 | boulevard | 12 | 1.76 | 4.75 |
| noise8 | shipped | bayside | 12 | 3.69 | 5.3 |
| noise8 | shipped | blocks | 12 | 3.85 | 10.69 |
| noise8 | shipped | boulevard | 12 | 3.91 | 10.09 |
| noise8 | spread0.95 | bayside | 12 | 3.69 | 5.3 |
| noise8 | spread0.95 | blocks | 12 | 3.85 | 10.69 |
| noise8 | spread0.95 | boulevard | 12 | 3.91 | 10.09 |
| noise8 | straight0.3 | bayside | 12 | 0.71 | 2.35 |
| noise8 | straight0.3 | blocks | 12 | 1.29 | 10.12 |
| noise8 | straight0.3 | boulevard | 12 | 1.77 | 4.99 |

## Each variant against the shipped pilot, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|
| measured | cf0.3 | 1/3 | 0 | 0 | 0 | -0.0014 |
| measured | spread0.95 | 0/3 | 0 | 0 | 0 | 0.0 |
| measured | straight0.3 | 0/3 | 2 | 0 | 0 | 0.0028 |
| measured | both | 0/3 | 2 | 0 | 0 | 0.0028 |
| noise6 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0111 |
| noise6 | spread0.95 | 0/3 | 0 | 0 | 0 | 0.0 |
| noise6 | straight0.3 | 0/3 | 1 | 0 | 0 | -0.0018 |
| noise6 | both | 0/3 | 1 | 0 | 0 | -0.0018 |
| noise8 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0195 |
| noise8 | spread0.95 | 0/3 | 0 | 0 | 0 | 0.0 |
| noise8 | straight0.3 | 1/3 | 0 | 0 | 0 | -0.0049 |
| noise8 | both | 1/3 | 1 | 0 | 0 | -0.0049 |
| measured-noise10 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0248 |
| measured-noise10 | spread0.95 | 0/3 | 0 | 0 | 0 | 0.0 |
| measured-noise10 | straight0.3 | 1/3 | 0 | 0 | 0 | -0.0054 |
| measured-noise10 | both | 1/3 | 0 | 0 | 0 | -0.0054 |
| noise12 | cf0.3 | 3/3 | 0 | 0 | 0 | -0.0341 |
| noise12 | spread0.95 | 0/3 | 0 | 0 | 0 | 0.0 |
| noise12 | straight0.3 | 1/3 | 0 | 0 | 0 | -0.003 |
| noise12 | both | 1/3 | 0 | 0 | 0 | -0.0036 |
| drift10 | cf0.3 | 2/3 | 0 | 0 | 0 | -0.0021 |
| drift10 | spread0.95 | 0/3 | 0 | 0 | 0 | 0.0 |
| drift10 | straight0.3 | 0/3 | 2 | 0 | 0 | 0.0028 |
| drift10 | both | 0/3 | 3 | 0 | 0 | 0.0043 |

| profile | variant | cruise | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| measured | cf0.3 | 0.8 | bayside | 7 | 0 | -2.0 | -0.0014 | 0.0156 |
| measured | cf0.3 | 0.8 | blocks | 4 | 3 | 0.0 | 0.0 | 1.0 |
| measured | cf0.3 | 0.8 | boulevard | 3 | 1 | 0.0 | 0.0 | 0.625 |
| measured | spread0.95 | 0.8 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| measured | spread0.95 | 0.8 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| measured | spread0.95 | 0.8 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| measured | straight0.3 | 0.8 | bayside | 0 | 9 | 4.0 | 0.0028 | 0.0039 |
| measured | straight0.3 | 0.8 | blocks | 2 | 7 | 3.0 | 0.0019 | 0.1797 |
| measured | straight0.3 | 0.8 | boulevard | 0 | 10 | 4.0 | 0.0023 | 0.002 |
| measured | both | 0.8 | bayside | 0 | 9 | 4.0 | 0.0028 | 0.0039 |
| measured | both | 0.8 | blocks | 2 | 7 | 3.0 | 0.0019 | 0.1797 |
| measured | both | 0.8 | boulevard | 0 | 10 | 4.0 | 0.0023 | 0.002 |
| noise6 | cf0.3 | 0.8 | bayside | 12 | 0 | -13.0 | -0.009 | 0.0005 |
| noise6 | cf0.3 | 0.8 | blocks | 11 | 0 | -18.0 | -0.0111 | 0.001 |
| noise6 | cf0.3 | 0.8 | boulevard | 12 | 0 | -13.0 | -0.0073 | 0.0005 |
| noise6 | spread0.95 | 0.8 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| noise6 | spread0.95 | 0.8 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| noise6 | spread0.95 | 0.8 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| noise6 | straight0.3 | 0.8 | bayside | 2 | 8 | 2.0 | 0.0014 | 0.1094 |
| noise6 | straight0.3 | 0.8 | blocks | 6 | 4 | -3.0 | -0.0018 | 0.7539 |
| noise6 | straight0.3 | 0.8 | boulevard | 1 | 8 | 2.0 | 0.0011 | 0.0391 |
| noise6 | both | 0.8 | bayside | 1 | 6 | 1.0 | 0.0007 | 0.125 |
| noise6 | both | 0.8 | blocks | 6 | 3 | -3.0 | -0.0018 | 0.5078 |
| noise6 | both | 0.8 | boulevard | 1 | 8 | 2.0 | 0.0011 | 0.0391 |
| noise8 | cf0.3 | 0.8 | bayside | 12 | 0 | -21.0 | -0.0144 | 0.0005 |
| noise8 | cf0.3 | 0.8 | blocks | 12 | 0 | -32.0 | -0.0195 | 0.0005 |
| noise8 | cf0.3 | 0.8 | boulevard | 12 | 0 | -26.0 | -0.0145 | 0.0005 |
| noise8 | spread0.95 | 0.8 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| noise8 | spread0.95 | 0.8 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| noise8 | spread0.95 | 0.8 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| noise8 | straight0.3 | 0.8 | bayside | 4 | 3 | 0.0 | 0.0 | 1.0 |
| noise8 | straight0.3 | 0.8 | blocks | 12 | 0 | -8.0 | -0.0049 | 0.0005 |
| noise8 | straight0.3 | 0.8 | boulevard | 2 | 0 | 0.0 | 0.0 | 0.5 |
| noise8 | both | 0.8 | bayside | 1 | 4 | 0.0 | 0.0 | 0.375 |
| noise8 | both | 0.8 | blocks | 11 | 0 | -8.0 | -0.0049 | 0.001 |
| noise8 | both | 0.8 | boulevard | 0 | 6 | 1.0 | 0.0006 | 0.0312 |
| measured-noise10 | cf0.3 | 0.8 | bayside | 12 | 0 | -32.0 | -0.0217 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | blocks | 12 | 0 | -41.0 | -0.0248 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | boulevard | 12 | 0 | -41.0 | -0.0227 | 0.0005 |
| measured-noise10 | spread0.95 | 0.8 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| measured-noise10 | spread0.95 | 0.8 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| measured-noise10 | spread0.95 | 0.8 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| measured-noise10 | straight0.3 | 0.8 | bayside | 2 | 7 | 2.0 | 0.0014 | 0.1797 |
| measured-noise10 | straight0.3 | 0.8 | blocks | 11 | 0 | -9.0 | -0.0054 | 0.001 |
| measured-noise10 | straight0.3 | 0.8 | boulevard | 6 | 2 | -1.0 | -0.0006 | 0.2891 |
| measured-noise10 | both | 0.8 | bayside | 2 | 8 | 2.0 | 0.0014 | 0.1094 |
| measured-noise10 | both | 0.8 | blocks | 10 | 0 | -9.0 | -0.0054 | 0.002 |
| measured-noise10 | both | 0.8 | boulevard | 2 | 3 | 0.0 | 0.0 | 1.0 |
| noise12 | cf0.3 | 0.8 | bayside | 12 | 0 | -45.0 | -0.0301 | 0.0005 |
| noise12 | cf0.3 | 0.8 | blocks | 12 | 0 | -57.0 | -0.0341 | 0.0005 |
| noise12 | cf0.3 | 0.8 | boulevard | 12 | 0 | -57.0 | -0.0311 | 0.0005 |
| noise12 | spread0.95 | 0.8 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| noise12 | spread0.95 | 0.8 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| noise12 | spread0.95 | 0.8 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| noise12 | straight0.3 | 0.8 | bayside | 2 | 2 | 0.0 | 0.0 | 1.0 |
| noise12 | straight0.3 | 0.8 | blocks | 8 | 1 | -5.0 | -0.003 | 0.0391 |
| noise12 | straight0.3 | 0.8 | boulevard | 7 | 1 | -2.0 | -0.0011 | 0.0703 |
| noise12 | both | 0.8 | bayside | 0 | 3 | 0.0 | 0.0 | 0.25 |
| noise12 | both | 0.8 | blocks | 10 | 0 | -6.0 | -0.0036 | 0.002 |
| noise12 | both | 0.8 | boulevard | 1 | 1 | 0.0 | 0.0 | 1.0 |
| drift10 | cf0.3 | 0.8 | bayside | 9 | 0 | -3.0 | -0.0021 | 0.0039 |
| drift10 | cf0.3 | 0.8 | blocks | 7 | 1 | -3.0 | -0.0019 | 0.0703 |
| drift10 | cf0.3 | 0.8 | boulevard | 7 | 0 | -2.0 | -0.0011 | 0.0156 |
| drift10 | spread0.95 | 0.8 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| drift10 | spread0.95 | 0.8 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| drift10 | spread0.95 | 0.8 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| drift10 | straight0.3 | 0.8 | bayside | 0 | 8 | 4.0 | 0.0028 | 0.0078 |
| drift10 | straight0.3 | 0.8 | blocks | 3 | 6 | 2.0 | 0.0012 | 0.5078 |
| drift10 | straight0.3 | 0.8 | boulevard | 0 | 10 | 4.0 | 0.0023 | 0.002 |
| drift10 | both | 0.8 | bayside | 0 | 8 | 4.0 | 0.0028 | 0.0078 |
| drift10 | both | 0.8 | blocks | 1 | 8 | 7.0 | 0.0043 | 0.0391 |
| drift10 | both | 0.8 | boulevard | 0 | 9 | 6.0 | 0.0034 | 0.0039 |

## Heading steered by against the true heading, while driving forward

| profile | variant | course | missions | median abs deg | RMS deg |
|---|---|---|---|---|---|
| drift10 | both | bayside | 12 | 5.53 | 8.18 |
| drift10 | both | blocks | 12 | 5.87 | 9.03 |
| drift10 | both | boulevard | 12 | 5.5 | 8.46 |
| drift10 | cf0.3 | bayside | 12 | 5.51 | 8.39 |
| drift10 | cf0.3 | blocks | 12 | 5.42 | 8.46 |
| drift10 | cf0.3 | boulevard | 12 | 5.48 | 8.84 |
| drift10 | shipped | bayside | 12 | 8.16 | 12.05 |
| drift10 | shipped | blocks | 12 | 8.0 | 12.27 |
| drift10 | shipped | boulevard | 12 | 7.44 | 10.96 |
| drift10 | spread0.95 | bayside | 12 | 8.16 | 12.05 |
| drift10 | spread0.95 | blocks | 12 | 8.0 | 12.27 |
| drift10 | spread0.95 | boulevard | 12 | 7.44 | 10.96 |
| drift10 | straight0.3 | bayside | 12 | 5.61 | 8.33 |
| drift10 | straight0.3 | blocks | 12 | 5.95 | 9.07 |
| drift10 | straight0.3 | boulevard | 12 | 5.46 | 8.73 |
| measured | both | bayside | 12 | 3.42 | 5.85 |
| measured | both | blocks | 12 | 3.64 | 6.12 |
| measured | both | boulevard | 12 | 3.52 | 5.96 |
| measured | cf0.3 | bayside | 12 | 2.52 | 5.52 |
| measured | cf0.3 | blocks | 12 | 3.05 | 5.62 |
| measured | cf0.3 | boulevard | 12 | 2.81 | 5.19 |
| measured | shipped | bayside | 12 | 3.54 | 6.52 |
| measured | shipped | blocks | 12 | 3.57 | 6.9 |
| measured | shipped | boulevard | 12 | 3.95 | 6.87 |
| measured | spread0.95 | bayside | 12 | 3.54 | 6.52 |
| measured | spread0.95 | blocks | 12 | 3.57 | 6.9 |
| measured | spread0.95 | boulevard | 12 | 3.95 | 6.87 |
| measured | straight0.3 | bayside | 12 | 3.41 | 6.1 |
| measured | straight0.3 | blocks | 12 | 3.66 | 6.2 |
| measured | straight0.3 | boulevard | 12 | 3.53 | 6.0 |
| measured-noise10 | both | bayside | 12 | 7.96 | 12.2 |
| measured-noise10 | both | blocks | 12 | 7.8 | 11.88 |
| measured-noise10 | both | boulevard | 12 | 7.79 | 11.85 |
| measured-noise10 | cf0.3 | bayside | 12 | 4.25 | 8.04 |
| measured-noise10 | cf0.3 | blocks | 12 | 5.37 | 9.29 |
| measured-noise10 | cf0.3 | boulevard | 12 | 4.74 | 8.4 |
| measured-noise10 | shipped | bayside | 12 | 25.03 | 27.02 |
| measured-noise10 | shipped | blocks | 12 | 24.99 | 27.04 |
| measured-noise10 | shipped | boulevard | 12 | 25.03 | 27.04 |
| measured-noise10 | spread0.95 | bayside | 12 | 25.03 | 27.02 |
| measured-noise10 | spread0.95 | blocks | 12 | 24.99 | 27.04 |
| measured-noise10 | spread0.95 | boulevard | 12 | 25.03 | 27.04 |
| measured-noise10 | straight0.3 | bayside | 12 | 7.79 | 12.15 |
| measured-noise10 | straight0.3 | blocks | 12 | 8.95 | 13.46 |
| measured-noise10 | straight0.3 | boulevard | 12 | 8.31 | 12.69 |
| noise12 | both | bayside | 12 | 9.53 | 14.21 |
| noise12 | both | blocks | 12 | 9.37 | 14.41 |
| noise12 | both | boulevard | 12 | 9.27 | 14.01 |
| noise12 | cf0.3 | bayside | 12 | 6.33 | 12.09 |
| noise12 | cf0.3 | blocks | 12 | 7.37 | 14.18 |
| noise12 | cf0.3 | boulevard | 12 | 5.39 | 8.87 |
| noise12 | shipped | bayside | 12 | 25.13 | 27.89 |
| noise12 | shipped | blocks | 12 | 24.98 | 27.91 |
| noise12 | shipped | boulevard | 12 | 25.01 | 27.88 |
| noise12 | spread0.95 | bayside | 12 | 25.13 | 27.89 |
| noise12 | spread0.95 | blocks | 12 | 24.98 | 27.91 |
| noise12 | spread0.95 | boulevard | 12 | 25.01 | 27.88 |
| noise12 | straight0.3 | bayside | 12 | 15.11 | 20.59 |
| noise12 | straight0.3 | blocks | 12 | 13.95 | 19.95 |
| noise12 | straight0.3 | boulevard | 12 | 11.99 | 18.23 |
| noise6 | both | bayside | 12 | 4.97 | 7.84 |
| noise6 | both | blocks | 12 | 5.37 | 8.32 |
| noise6 | both | boulevard | 12 | 5.2 | 8.01 |
| noise6 | cf0.3 | bayside | 12 | 3.21 | 6.22 |
| noise6 | cf0.3 | blocks | 12 | 3.21 | 6.06 |
| noise6 | cf0.3 | boulevard | 12 | 3.08 | 5.71 |
| noise6 | shipped | bayside | 12 | 24.91 | 25.64 |
| noise6 | shipped | blocks | 12 | 24.77 | 25.52 |
| noise6 | shipped | boulevard | 12 | 24.32 | 25.0 |
| noise6 | spread0.95 | bayside | 12 | 24.91 | 25.64 |
| noise6 | spread0.95 | blocks | 12 | 24.77 | 25.52 |
| noise6 | spread0.95 | boulevard | 12 | 24.32 | 25.0 |
| noise6 | straight0.3 | bayside | 12 | 5.14 | 8.25 |
| noise6 | straight0.3 | blocks | 12 | 5.38 | 8.46 |
| noise6 | straight0.3 | boulevard | 12 | 5.12 | 8.12 |
| noise8 | both | bayside | 12 | 6.41 | 9.91 |
| noise8 | both | blocks | 12 | 6.55 | 10.18 |
| noise8 | both | boulevard | 12 | 6.42 | 9.87 |
| noise8 | cf0.3 | bayside | 12 | 3.81 | 7.13 |
| noise8 | cf0.3 | blocks | 12 | 3.63 | 6.52 |
| noise8 | cf0.3 | boulevard | 12 | 3.62 | 6.7 |
| noise8 | shipped | bayside | 12 | 25.0 | 26.29 |
| noise8 | shipped | blocks | 12 | 24.95 | 26.31 |
| noise8 | shipped | boulevard | 12 | 24.99 | 26.3 |
| noise8 | spread0.95 | bayside | 12 | 25.0 | 26.29 |
| noise8 | spread0.95 | blocks | 12 | 24.95 | 26.31 |
| noise8 | spread0.95 | boulevard | 12 | 24.99 | 26.3 |
| noise8 | straight0.3 | bayside | 12 | 6.67 | 10.42 |
| noise8 | straight0.3 | blocks | 12 | 6.48 | 10.31 |
| noise8 | straight0.3 | boulevard | 12 | 6.38 | 10.04 |
