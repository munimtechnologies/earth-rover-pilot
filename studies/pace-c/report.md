# Smoothing the heading on a Mini+ with a noisy compass (simulated)

pace_c.py 0.1.0 (pace_b.py 0.1.0, pace_study.py 0.1.0, rover_pilot.py 0.11.2), MV2 of Munim, Inc. Human benchmark: 0.7543 m/s made good. Profiles from pace_b.py: measured = orientation every 0.5 s, 48 deg/s, 0.5 s latency, 3 deg compass noise; measured-noise10 = the same with 10 deg. Variants: {"shipped": null, "ema0.5": {"gain": 0.5, "yaw_dps": 0.0}, "ema0.3": {"gain": 0.3, "yaw_dps": 0.0}, "cf0.3": {"gain": 0.3, "yaw_dps": 48.0, "lag_s": 0.5}, "cf0.3-yaw30": {"gain": 0.3, "yaw_dps": 30.0, "lag_s": 0.5}}. Seeds 1-12. 720 of 720 missions completed. Simulated rovers only, so these speeds are upper bounds.

## Overview (courses pooled)

| profile | variant | cruise | completed | made good m/s (median) | efficiency | runs beating 0.754 | every course? | path ratio |
|---|---|---|---|---|---|---|---|---|
| measured | shipped | 0.7 | 36/36 | 0.769 | 0.989 | 36 | yes | 1.001 |
| measured | shipped | 0.8 | 36/36 | 0.878 | 0.988 | 36 | yes | 1.003 |
| measured | ema0.5 | 0.7 | 36/36 | 0.769 | 0.989 | 36 | yes | 1.003 |
| measured | ema0.5 | 0.8 | 36/36 | 0.876 | 0.985 | 36 | yes | 1.004 |
| measured | ema0.3 | 0.7 | 36/36 | 0.765 | 0.984 | 36 | yes | 1.005 |
| measured | ema0.3 | 0.8 | 36/36 | 0.872 | 0.981 | 36 | yes | 1.007 |
| measured | cf0.3 | 0.7 | 36/36 | 0.771 | 0.991 | 36 | yes | 1.002 |
| measured | cf0.3 | 0.8 | 36/36 | 0.878 | 0.988 | 36 | yes | 1.004 |
| measured | cf0.3-yaw30 | 0.7 | 36/36 | 0.77 | 0.99 | 36 | yes | 1.002 |
| measured | cf0.3-yaw30 | 0.8 | 36/36 | 0.878 | 0.987 | 36 | yes | 1.004 |
| measured-noise10 | shipped | 0.7 | 36/36 | 0.75 | 0.965 | 1 | no | 1.007 |
| measured-noise10 | shipped | 0.8 | 36/36 | 0.855 | 0.962 | 36 | yes | 1.009 |
| measured-noise10 | ema0.5 | 0.7 | 36/36 | 0.759 | 0.975 | 31 | yes | 1.007 |
| measured-noise10 | ema0.5 | 0.8 | 36/36 | 0.863 | 0.971 | 36 | yes | 1.01 |
| measured-noise10 | ema0.3 | 0.7 | 36/36 | 0.759 | 0.975 | 35 | yes | 1.009 |
| measured-noise10 | ema0.3 | 0.8 | 36/36 | 0.865 | 0.973 | 36 | yes | 1.011 |
| measured-noise10 | cf0.3 | 0.7 | 36/36 | 0.768 | 0.987 | 36 | yes | 1.003 |
| measured-noise10 | cf0.3 | 0.8 | 36/36 | 0.874 | 0.984 | 36 | yes | 1.005 |
| measured-noise10 | cf0.3-yaw30 | 0.7 | 36/36 | 0.767 | 0.986 | 36 | yes | 1.004 |
| measured-noise10 | cf0.3-yaw30 | 0.8 | 36/36 | 0.873 | 0.982 | 36 | yes | 1.006 |

## Each variant against the shipped pilot

Faster / slower: cruise x course groups where a paired sign test gives p < 0.05.

| profile | variant | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|
| measured | ema0.5 | 0/6 | 3 | 0 | 0 | 0.0014 |
| measured | ema0.3 | 0/6 | 6 | 0 | 0 | 0.0081 |
| measured | cf0.3 | 3/6 | 0 | 0 | 0 | -0.0027 |
| measured | cf0.3-yaw30 | 0/6 | 0 | 0 | 0 | -0.0011 |
| measured-noise10 | ema0.5 | 6/6 | 0 | 0 | 0 | -0.0121 |
| measured-noise10 | ema0.3 | 6/6 | 0 | 0 | 0 | -0.0131 |
| measured-noise10 | cf0.3 | 6/6 | 0 | 0 | 0 | -0.0248 |
| measured-noise10 | cf0.3-yaw30 | 6/6 | 0 | 0 | 0 | -0.0254 |

| profile | variant | cruise | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| measured | ema0.5 | 0.7 | bayside | 0 | 7 | 2.0 | 0.0012 | 0.0156 |
| measured | ema0.5 | 0.7 | blocks | 4 | 3 | 0.0 | 0.0 | 1.0 |
| measured | ema0.5 | 0.7 | boulevard | 0 | 5 | 0.0 | 0.0 | 0.0625 |
| measured | ema0.5 | 0.8 | bayside | 0 | 7 | 2.0 | 0.0014 | 0.0156 |
| measured | ema0.5 | 0.8 | blocks | 4 | 1 | 0.0 | 0.0 | 0.375 |
| measured | ema0.5 | 0.8 | boulevard | 0 | 6 | 1.0 | 0.0006 | 0.0312 |
| measured | ema0.3 | 0.7 | bayside | 0 | 11 | 8.0 | 0.0049 | 0.001 |
| measured | ema0.3 | 0.7 | blocks | 0 | 12 | 13.0 | 0.0071 | 0.0005 |
| measured | ema0.3 | 0.7 | boulevard | 0 | 12 | 9.0 | 0.0045 | 0.0005 |
| measured | ema0.3 | 0.8 | bayside | 0 | 11 | 9.0 | 0.0063 | 0.001 |
| measured | ema0.3 | 0.8 | blocks | 0 | 10 | 13.0 | 0.0081 | 0.002 |
| measured | ema0.3 | 0.8 | boulevard | 0 | 11 | 8.0 | 0.0045 | 0.001 |
| measured | cf0.3 | 0.7 | bayside | 9 | 0 | -2.0 | -0.0012 | 0.0039 |
| measured | cf0.3 | 0.7 | blocks | 9 | 1 | -5.0 | -0.0027 | 0.0215 |
| measured | cf0.3 | 0.7 | boulevard | 4 | 1 | 0.0 | 0.0 | 0.375 |
| measured | cf0.3 | 0.8 | bayside | 7 | 0 | -2.0 | -0.0014 | 0.0156 |
| measured | cf0.3 | 0.8 | blocks | 4 | 3 | 0.0 | 0.0 | 1.0 |
| measured | cf0.3 | 0.8 | boulevard | 3 | 1 | 0.0 | 0.0 | 0.625 |
| measured | cf0.3-yaw30 | 0.7 | bayside | 5 | 2 | 0.0 | 0.0 | 0.4531 |
| measured | cf0.3-yaw30 | 0.7 | blocks | 7 | 1 | -2.0 | -0.0011 | 0.0703 |
| measured | cf0.3-yaw30 | 0.7 | boulevard | 1 | 1 | 0.0 | 0.0 | 1.0 |
| measured | cf0.3-yaw30 | 0.8 | bayside | 2 | 3 | 0.0 | 0.0 | 1.0 |
| measured | cf0.3-yaw30 | 0.8 | blocks | 3 | 0 | 0.0 | 0.0 | 0.25 |
| measured | cf0.3-yaw30 | 0.8 | boulevard | 0 | 2 | 0.0 | 0.0 | 0.5 |
| measured-noise10 | ema0.5 | 0.7 | bayside | 12 | 0 | -18.0 | -0.0107 | 0.0005 |
| measured-noise10 | ema0.5 | 0.7 | blocks | 12 | 0 | -15.0 | -0.008 | 0.0005 |
| measured-noise10 | ema0.5 | 0.7 | boulevard | 12 | 0 | -25.0 | -0.0121 | 0.0005 |
| measured-noise10 | ema0.5 | 0.8 | bayside | 11 | 1 | -13.0 | -0.0088 | 0.0063 |
| measured-noise10 | ema0.5 | 0.8 | blocks | 12 | 0 | -16.0 | -0.0097 | 0.0005 |
| measured-noise10 | ema0.5 | 0.8 | boulevard | 12 | 0 | -20.0 | -0.0111 | 0.0005 |
| measured-noise10 | ema0.3 | 0.7 | bayside | 12 | 0 | -18.0 | -0.0107 | 0.0005 |
| measured-noise10 | ema0.3 | 0.7 | blocks | 12 | 0 | -22.0 | -0.0118 | 0.0005 |
| measured-noise10 | ema0.3 | 0.7 | boulevard | 12 | 0 | -27.0 | -0.0131 | 0.0005 |
| measured-noise10 | ema0.3 | 0.8 | bayside | 12 | 0 | -14.0 | -0.0095 | 0.0005 |
| measured-noise10 | ema0.3 | 0.8 | blocks | 12 | 0 | -21.0 | -0.0127 | 0.0005 |
| measured-noise10 | ema0.3 | 0.8 | boulevard | 12 | 0 | -22.0 | -0.0122 | 0.0005 |
| measured-noise10 | cf0.3 | 0.7 | bayside | 12 | 0 | -36.0 | -0.0214 | 0.0005 |
| measured-noise10 | cf0.3 | 0.7 | blocks | 12 | 0 | -45.0 | -0.0241 | 0.0005 |
| measured-noise10 | cf0.3 | 0.7 | boulevard | 12 | 0 | -46.0 | -0.0223 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | bayside | 12 | 0 | -32.0 | -0.0217 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | blocks | 12 | 0 | -41.0 | -0.0248 | 0.0005 |
| measured-noise10 | cf0.3 | 0.8 | boulevard | 12 | 0 | -41.0 | -0.0227 | 0.0005 |
| measured-noise10 | cf0.3-yaw30 | 0.7 | bayside | 12 | 0 | -32.0 | -0.019 | 0.0005 |
| measured-noise10 | cf0.3-yaw30 | 0.7 | blocks | 12 | 0 | -42.0 | -0.0225 | 0.0005 |
| measured-noise10 | cf0.3-yaw30 | 0.7 | boulevard | 12 | 0 | -42.0 | -0.0203 | 0.0005 |
| measured-noise10 | cf0.3-yaw30 | 0.8 | bayside | 12 | 0 | -28.0 | -0.019 | 0.0005 |
| measured-noise10 | cf0.3-yaw30 | 0.8 | blocks | 12 | 0 | -42.0 | -0.0254 | 0.0005 |
| measured-noise10 | cf0.3-yaw30 | 0.8 | boulevard | 12 | 0 | -36.0 | -0.0199 | 0.0005 |
