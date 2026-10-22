# The marathon pace on a Mini+ that reports like the measured one (simulated)

pace_b.py 0.1.0 (pace_study.py 0.1.0, rover_pilot.py 0.11.1), MV2 of Munim, Inc. Human benchmark: 50 miles Berkeley to Stanford in 29 h 38 min = 0.7543 m/s. Simulated Mini+: 1.111 m/s per unit of linear, GPS every 2 s, steered with ROVER_STEERING {"max_angular": 1.0, "turn_in_place_deg": 90.0}. Seeds 1-12. 720 of 720 missions completed. Simulated rovers only, so these speeds are upper bounds.

Profiles: fresh = orientation fresh on every poll (30 deg/s, 0.8 s latency); mini+ = pace_study's Mini+ (held 2 s, 30 deg/s, 0.8 s); measured = refreshed every 0.5 s, 48 deg/s, 0.5 s latency; measured-lag0.8 = the same with 0.8 s latency; measured-noise10 = the same with 10 deg compass noise.

## Overview (courses pooled)

| profile | cruise | completed | made good m/s (median) | efficiency | runs beating 0.754 | every course? | recoveries/run | path ratio |
|---|---|---|---|---|---|---|---|---|
| fresh | 0.6 | 36/36 | 0.659 | 0.989 | 0 | no | 0.78 | 1.001 |
| fresh | 0.7 | 36/36 | 0.766 | 0.985 | 36 | yes | 0.69 | 1.003 |
| fresh | 0.8 | 36/36 | 0.873 | 0.983 | 36 | yes | 0.64 | 1.006 |
| fresh | 1 | 36/36 | 1.087 | 0.979 | 36 | yes | 0.64 | 1.009 |
| mini+ | 0.6 | 36/36 | 0.657 | 0.985 | 0 | no | 0.92 | 1.002 |
| mini+ | 0.7 | 36/36 | 0.763 | 0.981 | 35 | yes | 0.89 | 1.004 |
| mini+ | 0.8 | 36/36 | 0.868 | 0.977 | 36 | yes | 0.72 | 1.008 |
| mini+ | 1 | 36/36 | 1.079 | 0.971 | 36 | yes | 0.75 | 1.013 |
| measured | 0.6 | 36/36 | 0.662 | 0.992 | 0 | no | 0.56 | 1.0 |
| measured | 0.7 | 36/36 | 0.769 | 0.989 | 36 | yes | 0.53 | 1.001 |
| measured | 0.8 | 36/36 | 0.878 | 0.988 | 36 | yes | 0.47 | 1.003 |
| measured | 1 | 36/36 | 1.09 | 0.981 | 36 | yes | 0.28 | 1.008 |
| measured-lag0.8 | 0.6 | 36/36 | 0.659 | 0.989 | 0 | no | 0.67 | 1.001 |
| measured-lag0.8 | 0.7 | 36/36 | 0.768 | 0.987 | 36 | yes | 0.61 | 1.003 |
| measured-lag0.8 | 0.8 | 36/36 | 0.874 | 0.983 | 36 | yes | 0.58 | 1.005 |
| measured-lag0.8 | 1 | 36/36 | 1.087 | 0.978 | 36 | yes | 0.53 | 1.009 |
| measured-noise10 | 0.6 | 36/36 | 0.645 | 0.968 | 0 | no | 0.69 | 1.006 |
| measured-noise10 | 0.7 | 36/36 | 0.75 | 0.965 | 1 | no | 0.53 | 1.007 |
| measured-noise10 | 0.8 | 36/36 | 0.855 | 0.962 | 36 | yes | 0.47 | 1.009 |
| measured-noise10 | 1 | 36/36 | 1.065 | 0.958 | 36 | yes | 0.33 | 1.013 |

## Per course

| profile | cruise | course | completed | made good m/s (median) | path ratio |
|---|---|---|---|---|---|
| fresh | 0.6 | bayside | 12/12 | 0.659 | 1.003 |
| fresh | 0.6 | blocks | 12/12 | 0.661 | 0.993 |
| fresh | 0.6 | boulevard | 12/12 | 0.659 | 1.002 |
| fresh | 0.7 | bayside | 12/12 | 0.767 | 1.004 |
| fresh | 0.7 | blocks | 12/12 | 0.76 | 1.006 |
| fresh | 0.7 | boulevard | 12/12 | 0.768 | 1.002 |
| fresh | 0.8 | bayside | 12/12 | 0.874 | 1.006 |
| fresh | 0.8 | blocks | 12/12 | 0.858 | 1.017 |
| fresh | 0.8 | boulevard | 12/12 | 0.877 | 1.002 |
| fresh | 1 | bayside | 12/12 | 1.088 | 1.009 |
| fresh | 1 | blocks | 12/12 | 1.04 | 1.043 |
| fresh | 1 | boulevard | 12/12 | 1.092 | 1.005 |
| measured | 0.6 | bayside | 12/12 | 0.661 | 1.001 |
| measured | 0.6 | blocks | 12/12 | 0.667 | 0.987 |
| measured | 0.6 | boulevard | 12/12 | 0.661 | 1.001 |
| measured | 0.7 | bayside | 12/12 | 0.768 | 1.004 |
| measured | 0.7 | blocks | 12/12 | 0.77 | 0.996 |
| measured | 0.7 | boulevard | 12/12 | 0.77 | 1.002 |
| measured | 0.8 | bayside | 12/12 | 0.879 | 1.004 |
| measured | 0.8 | blocks | 12/12 | 0.87 | 1.004 |
| measured | 0.8 | boulevard | 12/12 | 0.879 | 1.002 |
| measured | 1 | bayside | 12/12 | 1.091 | 1.008 |
| measured | 1 | blocks | 12/12 | 1.063 | 1.028 |
| measured | 1 | boulevard | 12/12 | 1.099 | 1.002 |
| measured-lag0.8 | 0.6 | bayside | 12/12 | 0.658 | 1.003 |
| measured-lag0.8 | 0.6 | blocks | 12/12 | 0.664 | 0.99 |
| measured-lag0.8 | 0.6 | boulevard | 12/12 | 0.66 | 1.001 |
| measured-lag0.8 | 0.7 | bayside | 12/12 | 0.766 | 1.005 |
| measured-lag0.8 | 0.7 | blocks | 12/12 | 0.767 | 0.998 |
| measured-lag0.8 | 0.7 | boulevard | 12/12 | 0.768 | 1.003 |
| measured-lag0.8 | 0.8 | bayside | 12/12 | 0.874 | 1.006 |
| measured-lag0.8 | 0.8 | blocks | 12/12 | 0.869 | 1.007 |
| measured-lag0.8 | 0.8 | boulevard | 12/12 | 0.878 | 1.002 |
| measured-lag0.8 | 1 | bayside | 12/12 | 1.087 | 1.009 |
| measured-lag0.8 | 1 | blocks | 12/12 | 1.057 | 1.03 |
| measured-lag0.8 | 1 | boulevard | 12/12 | 1.093 | 1.005 |
| measured-noise10 | 0.6 | bayside | 12/12 | 0.645 | 1.007 |
| measured-noise10 | 0.6 | blocks | 12/12 | 0.646 | 0.997 |
| measured-noise10 | 0.6 | boulevard | 12/12 | 0.645 | 1.006 |
| measured-noise10 | 0.7 | bayside | 12/12 | 0.75 | 1.009 |
| measured-noise10 | 0.7 | blocks | 12/12 | 0.75 | 1.004 |
| measured-noise10 | 0.7 | boulevard | 12/12 | 0.752 | 1.007 |
| measured-noise10 | 0.8 | bayside | 12/12 | 0.857 | 1.009 |
| measured-noise10 | 0.8 | blocks | 12/12 | 0.846 | 1.016 |
| measured-noise10 | 0.8 | boulevard | 12/12 | 0.858 | 1.008 |
| measured-noise10 | 1 | bayside | 12/12 | 1.065 | 1.013 |
| measured-noise10 | 1 | blocks | 12/12 | 1.03 | 1.039 |
| measured-noise10 | 1 | boulevard | 12/12 | 1.071 | 1.008 |
| mini+ | 0.6 | bayside | 12/12 | 0.655 | 1.006 |
| mini+ | 0.6 | blocks | 12/12 | 0.658 | 0.991 |
| mini+ | 0.6 | boulevard | 12/12 | 0.658 | 1.003 |
| mini+ | 0.7 | bayside | 12/12 | 0.762 | 1.007 |
| mini+ | 0.7 | blocks | 12/12 | 0.76 | 1.001 |
| mini+ | 0.7 | boulevard | 12/12 | 0.765 | 1.004 |
| mini+ | 0.8 | bayside | 12/12 | 0.868 | 1.009 |
| mini+ | 0.8 | blocks | 12/12 | 0.859 | 1.01 |
| mini+ | 0.8 | boulevard | 12/12 | 0.874 | 1.004 |
| mini+ | 1 | bayside | 12/12 | 1.079 | 1.013 |
| mini+ | 1 | blocks | 12/12 | 1.04 | 1.035 |
| mini+ | 1 | boulevard | 12/12 | 1.086 | 1.007 |

## Lowest cruise whose median beats the human pace on every course

| profile | cruise |
|---|---|
| fresh | 0.7 |
| mini+ | 0.7 |
| measured | 0.7 |
| measured-lag0.8 | 0.7 |
| measured-noise10 | 0.8 |

## Seed-by-seed comparisons

Faster / slower: cruise x course groups where a paired sign test gives p < 0.05. Lost / gained: groups where one side completed more seeds.

| profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|
| measured | mini+ | 12/12 | 0 | 0 | 0 | -0.0216 |
| measured-lag0.8 | measured | 0/12 | 11 | 0 | 0 | 0.0062 |
| measured-noise10 | measured | 0/12 | 12 | 0 | 0 | 0.0305 |

| profile | against | cruise | course | faster | slower | median diff s | p |
|---|---|---|---|---|---|---|---|
| measured | mini+ | 0.6 | bayside | 12 | 0 | -14.0 | 0.0005 |
| measured | mini+ | 0.6 | blocks | 12 | 0 | -25.0 | 0.0005 |
| measured | mini+ | 0.6 | boulevard | 12 | 0 | -15.0 | 0.0005 |
| measured | mini+ | 0.7 | bayside | 12 | 0 | -12.0 | 0.0005 |
| measured | mini+ | 0.7 | blocks | 12 | 0 | -24.0 | 0.0005 |
| measured | mini+ | 0.7 | boulevard | 12 | 0 | -13.0 | 0.0005 |
| measured | mini+ | 0.8 | bayside | 12 | 0 | -14.0 | 0.0005 |
| measured | mini+ | 0.8 | blocks | 11 | 1 | -27.0 | 0.0063 |
| measured | mini+ | 0.8 | boulevard | 12 | 0 | -10.0 | 0.0005 |
| measured | mini+ | 1 | bayside | 12 | 0 | -14.0 | 0.0005 |
| measured | mini+ | 1 | blocks | 12 | 0 | -29.0 | 0.0005 |
| measured | mini+ | 1 | boulevard | 12 | 0 | -14.0 | 0.0005 |
| measured-lag0.8 | measured | 0.6 | bayside | 0 | 10 | 6.0 | 0.002 |
| measured-lag0.8 | measured | 0.6 | blocks | 0 | 10 | 13.0 | 0.002 |
| measured-lag0.8 | measured | 0.6 | boulevard | 0 | 10 | 4.0 | 0.002 |
| measured-lag0.8 | measured | 0.7 | bayside | 0 | 10 | 6.0 | 0.002 |
| measured-lag0.8 | measured | 0.7 | blocks | 0 | 9 | 5.0 | 0.0039 |
| measured-lag0.8 | measured | 0.7 | boulevard | 0 | 11 | 4.0 | 0.001 |
| measured-lag0.8 | measured | 0.8 | bayside | 0 | 11 | 6.0 | 0.001 |
| measured-lag0.8 | measured | 0.8 | blocks | 1 | 7 | 6.0 | 0.0703 |
| measured-lag0.8 | measured | 0.8 | boulevard | 0 | 10 | 2.0 | 0.002 |
| measured-lag0.8 | measured | 1 | bayside | 0 | 9 | 5.0 | 0.0039 |
| measured-lag0.8 | measured | 1 | blocks | 0 | 10 | 6.0 | 0.002 |
| measured-lag0.8 | measured | 1 | boulevard | 0 | 10 | 5.0 | 0.002 |
| measured-noise10 | measured | 0.6 | bayside | 0 | 12 | 46.0 | 0.0005 |
| measured-noise10 | measured | 0.6 | blocks | 0 | 12 | 64.0 | 0.0005 |
| measured-noise10 | measured | 0.6 | boulevard | 0 | 12 | 60.0 | 0.0005 |
| measured-noise10 | measured | 0.7 | bayside | 0 | 12 | 40.0 | 0.0005 |
| measured-noise10 | measured | 0.7 | blocks | 0 | 12 | 51.0 | 0.0005 |
| measured-noise10 | measured | 0.7 | boulevard | 0 | 12 | 50.0 | 0.0005 |
| measured-noise10 | measured | 0.8 | bayside | 0 | 12 | 35.0 | 0.0005 |
| measured-noise10 | measured | 0.8 | blocks | 0 | 12 | 49.0 | 0.0005 |
| measured-noise10 | measured | 0.8 | boulevard | 0 | 12 | 45.0 | 0.0005 |
| measured-noise10 | measured | 1 | bayside | 0 | 12 | 29.0 | 0.0005 |
| measured-noise10 | measured | 1 | blocks | 0 | 12 | 39.0 | 0.0005 |
| measured-noise10 | measured | 1 | boulevard | 0 | 12 | 36.0 | 0.0005 |
