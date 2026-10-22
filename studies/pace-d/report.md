# Compass errors that last, and --smooth-heading (simulated)

pace_d.py 0.1.0 (pace_c.py 0.1.0, pace_b.py 0.1.0, pace_study.py 0.1.0, rover_pilot.py 0.12.0), MV2 of Munim, Inc. Human benchmark: 0.7543 m/s made good. Every profile is pace_b.py's measured Mini+ (orientation every 0.5 s, 48 deg/s, 0.5 s latency, 3 deg compass noise); measured-noise10 has 10 deg of noise; hardiron10/20 add A sin(heading + phase); drift10 adds a drift with SD 10 deg and a 120 s time constant. Variants: shipped, cf0.3 (--smooth-heading). Seeds 1-12. 720 of 720 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_c.py's runs: 288 compared, 288 identical, 0 missing.

## Overview (courses pooled)

| profile | variant | cruise | completed | made good m/s (median) | efficiency | runs beating 0.754 | every course? | path ratio |
|---|---|---|---|---|---|---|---|---|
| measured | shipped | 0.7 | 36/36 | 0.769 | 0.989 | 36 | yes | 1.001 |
| measured | shipped | 0.8 | 36/36 | 0.878 | 0.988 | 36 | yes | 1.003 |
| measured | cf0.3 | 0.7 | 36/36 | 0.771 | 0.991 | 36 | yes | 1.002 |
| measured | cf0.3 | 0.8 | 36/36 | 0.878 | 0.988 | 36 | yes | 1.004 |
| measured-noise10 | shipped | 0.7 | 36/36 | 0.75 | 0.965 | 1 | no | 1.007 |
| measured-noise10 | shipped | 0.8 | 36/36 | 0.855 | 0.962 | 36 | yes | 1.009 |
| measured-noise10 | cf0.3 | 0.7 | 36/36 | 0.768 | 0.987 | 36 | yes | 1.003 |
| measured-noise10 | cf0.3 | 0.8 | 36/36 | 0.874 | 0.984 | 36 | yes | 1.005 |
| hardiron10 | shipped | 0.7 | 36/36 | 0.769 | 0.989 | 36 | yes | 1.001 |
| hardiron10 | shipped | 0.8 | 36/36 | 0.877 | 0.987 | 36 | yes | 1.003 |
| hardiron10 | cf0.3 | 0.7 | 36/36 | 0.77 | 0.99 | 36 | yes | 1.002 |
| hardiron10 | cf0.3 | 0.8 | 36/36 | 0.878 | 0.988 | 36 | yes | 1.004 |
| hardiron20 | shipped | 0.7 | 36/36 | 0.768 | 0.987 | 34 | yes | 1.004 |
| hardiron20 | shipped | 0.8 | 36/36 | 0.875 | 0.985 | 36 | yes | 1.006 |
| hardiron20 | cf0.3 | 0.7 | 36/36 | 0.769 | 0.988 | 34 | yes | 1.003 |
| hardiron20 | cf0.3 | 0.8 | 36/36 | 0.877 | 0.986 | 36 | yes | 1.006 |
| drift10 | shipped | 0.7 | 36/36 | 0.767 | 0.986 | 36 | yes | 1.004 |
| drift10 | shipped | 0.8 | 36/36 | 0.873 | 0.982 | 36 | yes | 1.007 |
| drift10 | cf0.3 | 0.7 | 36/36 | 0.769 | 0.988 | 36 | yes | 1.004 |
| drift10 | cf0.3 | 0.8 | 36/36 | 0.874 | 0.983 | 36 | yes | 1.007 |

## Each profile against measured, same variant

Faster / slower: cruise x course groups where a paired sign test gives p < 0.05.

| profile | variant | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|
| drift10 | cf0.3 | 0/6 | 6 | 0 | 0 | 0.0061 |
| drift10 | shipped | 0/6 | 5 | 0 | 0 | 0.0055 |
| hardiron10 | cf0.3 | 0/6 | 0 | 0 | 0 | 0.0044 |
| hardiron10 | shipped | 0/6 | 0 | 0 | 0 | 0.005 |
| hardiron20 | cf0.3 | 0/6 | 1 | 0 | 0 | 0.0087 |
| hardiron20 | shipped | 0/6 | 1 | 0 | 0 | 0.0099 |
| measured-noise10 | cf0.3 | 0/6 | 5 | 0 | 0 | 0.0055 |
| measured-noise10 | shipped | 0/6 | 6 | 0 | 0 | 0.0305 |

| profile | variant | cruise | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| drift10 | cf0.3 | 0.7 | bayside | 0 | 10 | 5.0 | 0.0031 | 0.002 |
| drift10 | cf0.3 | 0.7 | blocks | 1 | 9 | 11.0 | 0.0061 | 0.0215 |
| drift10 | cf0.3 | 0.7 | boulevard | 0 | 12 | 5.0 | 0.0025 | 0.0005 |
| drift10 | cf0.3 | 0.8 | bayside | 0 | 9 | 6.0 | 0.0042 | 0.0039 |
| drift10 | cf0.3 | 0.8 | blocks | 1 | 8 | 4.0 | 0.0025 | 0.0391 |
| drift10 | cf0.3 | 0.8 | boulevard | 0 | 12 | 4.0 | 0.0023 | 0.0005 |
| drift10 | shipped | 0.7 | bayside | 1 | 10 | 6.0 | 0.0037 | 0.0117 |
| drift10 | shipped | 0.7 | blocks | 0 | 10 | 10.0 | 0.0055 | 0.002 |
| drift10 | shipped | 0.7 | boulevard | 0 | 11 | 7.0 | 0.0035 | 0.001 |
| drift10 | shipped | 0.8 | bayside | 0 | 9 | 7.0 | 0.0049 | 0.0039 |
| drift10 | shipped | 0.8 | blocks | 3 | 8 | 6.0 | 0.0037 | 0.2266 |
| drift10 | shipped | 0.8 | boulevard | 0 | 11 | 6.0 | 0.0034 | 0.001 |
| hardiron10 | cf0.3 | 0.7 | bayside | 1 | 3 | 0.0 | 0.0 | 0.625 |
| hardiron10 | cf0.3 | 0.7 | blocks | 3 | 7 | 8.0 | 0.0044 | 0.3438 |
| hardiron10 | cf0.3 | 0.7 | boulevard | 5 | 4 | 0.0 | 0.0 | 1.0 |
| hardiron10 | cf0.3 | 0.8 | bayside | 0 | 3 | 0.0 | 0.0 | 0.25 |
| hardiron10 | cf0.3 | 0.8 | blocks | 5 | 6 | 2.0 | 0.0012 | 1.0 |
| hardiron10 | cf0.3 | 0.8 | boulevard | 5 | 4 | 0.0 | 0.0 | 1.0 |
| hardiron10 | shipped | 0.7 | bayside | 1 | 4 | 0.0 | 0.0 | 0.375 |
| hardiron10 | shipped | 0.7 | blocks | 6 | 6 | 0.0 | 0.0 | 1.0 |
| hardiron10 | shipped | 0.7 | boulevard | 3 | 5 | 0.0 | 0.0 | 0.7266 |
| hardiron10 | shipped | 0.8 | bayside | 1 | 4 | 0.0 | 0.0 | 0.375 |
| hardiron10 | shipped | 0.8 | blocks | 5 | 7 | 8.0 | 0.005 | 0.7744 |
| hardiron10 | shipped | 0.8 | boulevard | 1 | 5 | 0.0 | 0.0 | 0.2188 |
| hardiron20 | cf0.3 | 0.7 | bayside | 1 | 8 | 4.0 | 0.0024 | 0.0391 |
| hardiron20 | cf0.3 | 0.7 | blocks | 5 | 6 | 7.0 | 0.0039 | 1.0 |
| hardiron20 | cf0.3 | 0.7 | boulevard | 5 | 4 | 0.0 | 0.0 | 1.0 |
| hardiron20 | cf0.3 | 0.8 | bayside | 0 | 4 | 0.0 | 0.0 | 0.125 |
| hardiron20 | cf0.3 | 0.8 | blocks | 5 | 7 | 14.0 | 0.0087 | 0.7744 |
| hardiron20 | cf0.3 | 0.8 | boulevard | 4 | 5 | 0.0 | 0.0 | 1.0 |
| hardiron20 | shipped | 0.7 | bayside | 1 | 6 | 1.0 | 0.0006 | 0.125 |
| hardiron20 | shipped | 0.7 | blocks | 5 | 6 | 9.0 | 0.0049 | 1.0 |
| hardiron20 | shipped | 0.7 | boulevard | 2 | 6 | 1.0 | 0.0005 | 0.2891 |
| hardiron20 | shipped | 0.8 | bayside | 1 | 10 | 7.0 | 0.0049 | 0.0117 |
| hardiron20 | shipped | 0.8 | blocks | 5 | 7 | 16.0 | 0.0099 | 0.7744 |
| hardiron20 | shipped | 0.8 | boulevard | 2 | 6 | 1.0 | 0.0006 | 0.2891 |
| measured-noise10 | cf0.3 | 0.7 | bayside | 0 | 12 | 8.0 | 0.0049 | 0.0005 |
| measured-noise10 | cf0.3 | 0.7 | blocks | 0 | 11 | 10.0 | 0.0055 | 0.001 |
| measured-noise10 | cf0.3 | 0.7 | boulevard | 0 | 12 | 7.0 | 0.0035 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | bayside | 0 | 12 | 7.0 | 0.0049 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | blocks | 1 | 7 | 3.0 | 0.0019 | 0.0703 |
| measured-noise10 | cf0.3 | 0.8 | boulevard | 0 | 12 | 5.0 | 0.0028 | 0.0005 |
| measured-noise10 | shipped | 0.7 | bayside | 0 | 12 | 40.0 | 0.0244 | 0.0005 |
| measured-noise10 | shipped | 0.7 | blocks | 0 | 12 | 51.0 | 0.028 | 0.0005 |
| measured-noise10 | shipped | 0.7 | boulevard | 0 | 12 | 50.0 | 0.0248 | 0.0005 |
| measured-noise10 | shipped | 0.8 | bayside | 0 | 12 | 35.0 | 0.0244 | 0.0005 |
| measured-noise10 | shipped | 0.8 | blocks | 0 | 12 | 49.0 | 0.0305 | 0.0005 |
| measured-noise10 | shipped | 0.8 | boulevard | 0 | 12 | 45.0 | 0.0255 | 0.0005 |

## cf0.3 against the shipped pilot, same profile

| profile | variant | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|
| measured | cf0.3 | 3/6 | 0 | 0 | 0 | -0.0027 |
| measured-noise10 | cf0.3 | 6/6 | 0 | 0 | 0 | -0.0248 |
| hardiron10 | cf0.3 | 4/6 | 0 | 0 | 0 | -0.0024 |
| hardiron20 | cf0.3 | 1/6 | 0 | 0 | 0 | -0.0021 |
| drift10 | cf0.3 | 4/6 | 0 | 0 | 0 | -0.0021 |

| profile | variant | cruise | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| measured | cf0.3 | 0.7 | bayside | 9 | 0 | -2.0 | -0.0012 | 0.0039 |
| measured | cf0.3 | 0.7 | blocks | 9 | 1 | -5.0 | -0.0027 | 0.0215 |
| measured | cf0.3 | 0.7 | boulevard | 4 | 1 | 0.0 | 0.0 | 0.375 |
| measured | cf0.3 | 0.8 | bayside | 7 | 0 | -2.0 | -0.0014 | 0.0156 |
| measured | cf0.3 | 0.8 | blocks | 4 | 3 | 0.0 | 0.0 | 1.0 |
| measured | cf0.3 | 0.8 | boulevard | 3 | 1 | 0.0 | 0.0 | 0.625 |
| measured-noise10 | cf0.3 | 0.7 | bayside | 12 | 0 | -36.0 | -0.0214 | 0.0005 |
| measured-noise10 | cf0.3 | 0.7 | blocks | 12 | 0 | -45.0 | -0.0241 | 0.0005 |
| measured-noise10 | cf0.3 | 0.7 | boulevard | 12 | 0 | -46.0 | -0.0223 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | bayside | 12 | 0 | -32.0 | -0.0217 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | blocks | 12 | 0 | -41.0 | -0.0248 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | boulevard | 12 | 0 | -41.0 | -0.0227 | 0.0005 |
| hardiron10 | cf0.3 | 0.7 | bayside | 9 | 0 | -4.0 | -0.0024 | 0.0039 |
| hardiron10 | cf0.3 | 0.7 | blocks | 4 | 4 | 0.0 | 0.0 | 1.0 |
| hardiron10 | cf0.3 | 0.7 | boulevard | 8 | 0 | -3.0 | -0.0015 | 0.0078 |
| hardiron10 | cf0.3 | 0.8 | bayside | 6 | 0 | -1.0 | -0.0007 | 0.0312 |
| hardiron10 | cf0.3 | 0.8 | blocks | 4 | 1 | 0.0 | 0.0 | 0.375 |
| hardiron10 | cf0.3 | 0.8 | boulevard | 9 | 0 | -2.0 | -0.0011 | 0.0039 |
| hardiron20 | cf0.3 | 0.7 | bayside | 6 | 1 | -1.0 | -0.0006 | 0.125 |
| hardiron20 | cf0.3 | 0.7 | blocks | 3 | 5 | 0.0 | 0.0 | 0.7266 |
| hardiron20 | cf0.3 | 0.7 | boulevard | 8 | 2 | -3.0 | -0.0015 | 0.1094 |
| hardiron20 | cf0.3 | 0.8 | bayside | 9 | 1 | -3.0 | -0.0021 | 0.0215 |
| hardiron20 | cf0.3 | 0.8 | blocks | 4 | 4 | 0.0 | 0.0 | 1.0 |
| hardiron20 | cf0.3 | 0.8 | boulevard | 5 | 0 | 0.0 | 0.0 | 0.0625 |
| drift10 | cf0.3 | 0.7 | bayside | 8 | 0 | -3.0 | -0.0018 | 0.0078 |
| drift10 | cf0.3 | 0.7 | blocks | 8 | 1 | -2.0 | -0.0011 | 0.0391 |
| drift10 | cf0.3 | 0.7 | boulevard | 6 | 1 | -1.0 | -0.0005 | 0.125 |
| drift10 | cf0.3 | 0.8 | bayside | 9 | 0 | -3.0 | -0.0021 | 0.0039 |
| drift10 | cf0.3 | 0.8 | blocks | 7 | 1 | -3.0 | -0.0019 | 0.0703 |
| drift10 | cf0.3 | 0.8 | boulevard | 7 | 0 | -2.0 | -0.0011 | 0.0156 |

## Heading steered by against the true heading, while driving forward

Medians over the completed missions of each mission's median |error| and RMS error.

| profile | variant | cruise | course | missions | median abs deg | RMS deg |
|---|---|---|---|---|---|---|
| drift10 | cf0.3 | 0.7 | bayside | 12 | 5.54 | 8.62 |
| drift10 | cf0.3 | 0.7 | blocks | 12 | 6.08 | 9.16 |
| drift10 | cf0.3 | 0.7 | boulevard | 12 | 5.54 | 9.18 |
| drift10 | cf0.3 | 0.8 | bayside | 12 | 5.51 | 8.39 |
| drift10 | cf0.3 | 0.8 | blocks | 12 | 5.42 | 8.46 |
| drift10 | cf0.3 | 0.8 | boulevard | 12 | 5.48 | 8.84 |
| drift10 | shipped | 0.7 | bayside | 12 | 8.19 | 12.5 |
| drift10 | shipped | 0.7 | blocks | 12 | 7.5 | 12.41 |
| drift10 | shipped | 0.7 | boulevard | 12 | 7.79 | 11.52 |
| drift10 | shipped | 0.8 | bayside | 12 | 8.16 | 12.05 |
| drift10 | shipped | 0.8 | blocks | 12 | 8.0 | 12.27 |
| drift10 | shipped | 0.8 | boulevard | 12 | 7.44 | 10.96 |
| hardiron10 | cf0.3 | 0.7 | bayside | 12 | 3.45 | 5.99 |
| hardiron10 | cf0.3 | 0.7 | blocks | 12 | 5.52 | 8.3 |
| hardiron10 | cf0.3 | 0.7 | boulevard | 12 | 2.64 | 5.33 |
| hardiron10 | cf0.3 | 0.8 | bayside | 12 | 3.25 | 6.01 |
| hardiron10 | cf0.3 | 0.8 | blocks | 12 | 5.01 | 8.27 |
| hardiron10 | cf0.3 | 0.8 | boulevard | 12 | 2.96 | 5.87 |
| hardiron10 | shipped | 0.7 | bayside | 12 | 3.8 | 7.62 |
| hardiron10 | shipped | 0.7 | blocks | 12 | 6.23 | 8.4 |
| hardiron10 | shipped | 0.7 | boulevard | 12 | 3.42 | 6.81 |
| hardiron10 | shipped | 0.8 | bayside | 12 | 3.7 | 7.53 |
| hardiron10 | shipped | 0.8 | blocks | 12 | 5.92 | 9.1 |
| hardiron10 | shipped | 0.8 | boulevard | 12 | 3.97 | 7.0 |
| hardiron20 | cf0.3 | 0.7 | bayside | 12 | 4.29 | 6.8 |
| hardiron20 | cf0.3 | 0.7 | blocks | 12 | 10.19 | 13.88 |
| hardiron20 | cf0.3 | 0.7 | boulevard | 12 | 3.09 | 6.61 |
| hardiron20 | cf0.3 | 0.8 | bayside | 12 | 3.85 | 7.36 |
| hardiron20 | cf0.3 | 0.8 | blocks | 12 | 9.85 | 13.95 |
| hardiron20 | cf0.3 | 0.8 | boulevard | 12 | 3.17 | 6.0 |
| hardiron20 | shipped | 0.7 | bayside | 12 | 6.08 | 9.77 |
| hardiron20 | shipped | 0.7 | blocks | 12 | 10.91 | 15.18 |
| hardiron20 | shipped | 0.7 | boulevard | 12 | 3.87 | 8.27 |
| hardiron20 | shipped | 0.8 | bayside | 12 | 5.07 | 9.29 |
| hardiron20 | shipped | 0.8 | blocks | 12 | 11.47 | 15.02 |
| hardiron20 | shipped | 0.8 | boulevard | 12 | 4.42 | 8.27 |
| measured | cf0.3 | 0.7 | bayside | 12 | 2.75 | 5.14 |
| measured | cf0.3 | 0.7 | blocks | 12 | 2.84 | 5.37 |
| measured | cf0.3 | 0.7 | boulevard | 12 | 2.55 | 5.11 |
| measured | cf0.3 | 0.8 | bayside | 12 | 2.52 | 5.52 |
| measured | cf0.3 | 0.8 | blocks | 12 | 3.05 | 5.62 |
| measured | cf0.3 | 0.8 | boulevard | 12 | 2.81 | 5.19 |
| measured | shipped | 0.7 | bayside | 12 | 3.6 | 7.02 |
| measured | shipped | 0.7 | blocks | 12 | 3.83 | 7.23 |
| measured | shipped | 0.7 | boulevard | 12 | 3.75 | 7.34 |
| measured | shipped | 0.8 | bayside | 12 | 3.54 | 6.52 |
| measured | shipped | 0.8 | blocks | 12 | 3.57 | 6.9 |
| measured | shipped | 0.8 | boulevard | 12 | 3.95 | 6.87 |
| measured-noise10 | cf0.3 | 0.7 | bayside | 12 | 4.8 | 9.89 |
| measured-noise10 | cf0.3 | 0.7 | blocks | 12 | 5.0 | 9.32 |
| measured-noise10 | cf0.3 | 0.7 | boulevard | 12 | 4.55 | 8.52 |
| measured-noise10 | cf0.3 | 0.8 | bayside | 12 | 4.25 | 8.04 |
| measured-noise10 | cf0.3 | 0.8 | blocks | 12 | 5.37 | 9.29 |
| measured-noise10 | cf0.3 | 0.8 | boulevard | 12 | 4.74 | 8.4 |
| measured-noise10 | shipped | 0.7 | bayside | 12 | 25.02 | 27.02 |
| measured-noise10 | shipped | 0.7 | blocks | 12 | 24.96 | 27.03 |
| measured-noise10 | shipped | 0.7 | boulevard | 12 | 24.98 | 27.02 |
| measured-noise10 | shipped | 0.8 | bayside | 12 | 25.03 | 27.02 |
| measured-noise10 | shipped | 0.8 | blocks | 12 | 24.99 | 27.04 |
| measured-noise10 | shipped | 0.8 | boulevard | 12 | 25.03 | 27.04 |
