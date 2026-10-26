# The stuck detector's warm-up again: 5 s or 10 s, and a fair stuck test (simulated)

pace_u.py 0.1.0 (pace_t.py 0.1.0, pace_s.py 0.1.0, pace_q.py 0.1.0, pace_p.py 0.1.0, rover_pilot.py 0.18.5, dead_reckon.py 0.2.0), MV2 of Munim, Inc. Every mission is v0.18.2's real-rover pilot as pace_t.py flies it, with Pilot._stuck as it ships (a0.3), with no stuck verdict until 5 s or 10 s after the stuck history was last cleared (warm5, warm10), or with that and the GPS average started again from the fix after more than 3 s without one (restart+warm5, restart+warm10). Profiles: outage90 (90 s GPS outages, 1.5 m of GPS noise per axis), quiet90, quietdrift90 and quiet45 (the same idea with 0.22 m), and blocked30 (quiet90 with a rover that cannot move for its first 30 s). Seeds 373-396. 1800 of 1800 missions completed. Simulated rovers only, so these speeds are upper bounds.

Check against pace_s.py's runs: 18 compared, 18 identical, 0 missing.

Check against pace_t.py's runs: 11 compared, 11 identical.

## Overview (courses pooled)

| profile | variant | completed | made good m/s (median) | efficiency | runs beating 0.754 | path ratio | share stopped |
|---|---|---|---|---|---|---|---|
| outage90 | a0.3 | 72/72 | 0.881 | 0.991 | 72 | 1.0 | 0.017 |
| outage90 | warm5 | 72/72 | 0.885 | 0.996 | 72 | 0.998 | 0.015 |
| outage90 | warm10 | 72/72 | 0.885 | 0.996 | 72 | 0.999 | 0.015 |
| outage90 | restart+warm5 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.015 |
| outage90 | restart+warm10 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.015 |
| quiet90 | a0.3 | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.017 |
| quiet90 | warm5 | 72/72 | 0.888 | 0.999 | 72 | 0.997 | 0.015 |
| quiet90 | warm10 | 72/72 | 0.888 | 0.999 | 72 | 0.997 | 0.015 |
| quiet90 | restart+warm5 | 72/72 | 0.889 | 1.0 | 72 | 0.996 | 0.011 |
| quiet90 | restart+warm10 | 72/72 | 0.889 | 1.0 | 72 | 0.996 | 0.011 |
| quietdrift90 | a0.3 | 72/72 | 0.874 | 0.983 | 72 | 1.005 | 0.019 |
| quietdrift90 | warm5 | 72/72 | 0.879 | 0.988 | 72 | 1.003 | 0.014 |
| quietdrift90 | warm10 | 72/72 | 0.879 | 0.988 | 72 | 1.003 | 0.014 |
| quietdrift90 | restart+warm5 | 72/72 | 0.882 | 0.992 | 72 | 1.002 | 0.012 |
| quietdrift90 | restart+warm10 | 72/72 | 0.882 | 0.992 | 72 | 1.002 | 0.012 |
| quiet45 | a0.3 | 72/72 | 0.882 | 0.992 | 72 | 0.999 | 0.011 |
| quiet45 | warm5 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.009 |
| quiet45 | warm10 | 72/72 | 0.886 | 0.997 | 72 | 0.997 | 0.009 |
| quiet45 | restart+warm5 | 72/72 | 0.889 | 1.0 | 72 | 0.995 | 0.009 |
| quiet45 | restart+warm10 | 72/72 | 0.889 | 1.0 | 72 | 0.995 | 0.009 |
| blocked30 | a0.3 | 72/72 | 0.869 | 0.978 | 72 | 0.997 | 0.02 |
| blocked30 | warm5 | 72/72 | 0.867 | 0.975 | 72 | 0.998 | 0.02 |
| blocked30 | warm10 | 72/72 | 0.869 | 0.978 | 72 | 0.997 | 0.02 |
| blocked30 | restart+warm5 | 72/72 | 0.869 | 0.978 | 72 | 0.997 | 0.021 |
| blocked30 | restart+warm10 | 72/72 | 0.873 | 0.982 | 72 | 0.996 | 0.02 |

## Recovery moves (first before 30 s: at the start; late: moves at or after 30 s; eligible: GPS up until 30 s)

| profile | variant | course | missions | with a recovery | recoveries | first before 30 s | late | eligible | eligible caught early | median first s | latest first s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 24 | 48 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| blocked30 | a0.3 | blocks | 24 | 24 | 48 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| blocked30 | a0.3 | boulevard | 24 | 24 | 48 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| blocked30 | restart+warm10 | bayside | 24 | 24 | 24 | 23 | 1 | 24 | 23 | 19.1 | 31.0 |
| blocked30 | restart+warm10 | blocks | 24 | 24 | 24 | 23 | 1 | 24 | 23 | 19.1 | 31.0 |
| blocked30 | restart+warm10 | boulevard | 24 | 24 | 24 | 23 | 1 | 24 | 23 | 19.1 | 31.0 |
| blocked30 | restart+warm5 | bayside | 24 | 24 | 43 | 24 | 19 | 24 | 24 | 14.2 | 26.1 |
| blocked30 | restart+warm5 | blocks | 24 | 24 | 43 | 24 | 19 | 24 | 24 | 14.2 | 26.1 |
| blocked30 | restart+warm5 | boulevard | 24 | 24 | 43 | 24 | 19 | 24 | 24 | 14.2 | 26.1 |
| blocked30 | warm10 | bayside | 24 | 24 | 24 | 23 | 1 | 24 | 23 | 19.1 | 31.0 |
| blocked30 | warm10 | blocks | 24 | 24 | 24 | 23 | 1 | 24 | 23 | 19.1 | 31.0 |
| blocked30 | warm10 | boulevard | 24 | 24 | 24 | 23 | 1 | 24 | 23 | 19.1 | 31.0 |
| blocked30 | warm5 | bayside | 24 | 24 | 43 | 24 | 19 | 24 | 24 | 14.2 | 26.1 |
| blocked30 | warm5 | blocks | 24 | 24 | 43 | 24 | 19 | 24 | 24 | 14.2 | 26.1 |
| blocked30 | warm5 | boulevard | 24 | 24 | 43 | 24 | 19 | 24 | 24 | 14.2 | 26.1 |
| outage90 | a0.3 | bayside | 24 | 11 | 11 | 11 | 0 | 24 | 11 | 9.1 | 11.1 |
| outage90 | a0.3 | blocks | 24 | 13 | 13 | 13 | 0 | 24 | 13 | 9.1 | 14.0 |
| outage90 | a0.3 | boulevard | 24 | 14 | 14 | 14 | 0 | 24 | 14 | 9.1 | 14.0 |
| outage90 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | restart+warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | restart+warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | restart+warm5 | boulevard | 24 | 1 | 1 | 1 | 0 | 24 | 1 | 14.2 | 14.2 |
| outage90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| outage90 | warm5 | boulevard | 24 | 1 | 1 | 1 | 0 | 24 | 1 | 14.2 | 14.2 |
| quiet45 | a0.3 | bayside | 24 | 23 | 23 | 23 | 0 | 24 | 23 | 9.1 | 11.1 |
| quiet45 | a0.3 | blocks | 24 | 24 | 24 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| quiet45 | a0.3 | boulevard | 24 | 24 | 24 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| quiet45 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | restart+warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | restart+warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | restart+warm5 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet45 | warm5 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | a0.3 | bayside | 24 | 23 | 23 | 23 | 0 | 24 | 23 | 9.1 | 11.1 |
| quiet90 | a0.3 | blocks | 24 | 24 | 24 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| quiet90 | a0.3 | boulevard | 24 | 24 | 24 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| quiet90 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | restart+warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | restart+warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | restart+warm5 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quiet90 | warm5 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | a0.3 | bayside | 24 | 22 | 22 | 22 | 0 | 24 | 22 | 9.1 | 11.1 |
| quietdrift90 | a0.3 | blocks | 24 | 24 | 24 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| quietdrift90 | a0.3 | boulevard | 24 | 24 | 24 | 24 | 0 | 24 | 24 | 9.1 | 11.1 |
| quietdrift90 | restart+warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | restart+warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | restart+warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | restart+warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | restart+warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | restart+warm5 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | warm10 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | warm10 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | warm10 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | warm5 | bayside | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | warm5 | blocks | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |
| quietdrift90 | warm5 | boulevard | 24 | 0 | 0 | 0 | 0 | 24 | 0 | None | None |

## Pairs, same profile

Faster / slower: courses where a paired sign test gives p < 0.05.

| profile | variant | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| blocked30 | warm5 | a0.3 | 0/3 | 2 | 0 | 0 | 0.0017 |
| outage90 | warm5 | a0.3 | 2/3 | 0 | 0 | 0 | 0.0 |
| quiet45 | warm5 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0056 |
| quiet90 | warm5 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0042 |
| quietdrift90 | warm5 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0055 |
| blocked30 | warm10 | a0.3 | 2/3 | 0 | 0 | 0 | 0.0 |
| outage90 | warm10 | a0.3 | 2/3 | 0 | 0 | 0 | -0.0006 |
| quiet45 | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0056 |
| quiet90 | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0042 |
| quietdrift90 | warm10 | a0.3 | 3/3 | 0 | 0 | 0 | -0.0055 |
| blocked30 | warm5 | warm10 | 0/3 | 3 | 0 | 0 | 0.0017 |
| outage90 | warm5 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| quiet45 | warm5 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| quiet90 | warm5 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| quietdrift90 | warm5 | warm10 | 0/3 | 0 | 0 | 0 | 0.0 |
| blocked30 | restart+warm5 | warm5 | 2/3 | 0 | 0 | 0 | -0.0069 |
| outage90 | restart+warm5 | warm5 | 2/3 | 0 | 0 | 0 | -0.007 |
| quiet45 | restart+warm5 | warm5 | 2/3 | 0 | 0 | 0 | -0.0071 |
| quiet90 | restart+warm5 | warm5 | 2/3 | 0 | 0 | 0 | -0.0077 |
| quietdrift90 | restart+warm5 | warm5 | 2/3 | 0 | 0 | 0 | -0.0127 |
| blocked30 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0088 |
| outage90 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.007 |
| quiet45 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0071 |
| quiet90 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0077 |
| quietdrift90 | restart+warm10 | warm10 | 2/3 | 0 | 0 | 0 | -0.0127 |

| profile | variant | against | course | faster | slower | median diff s | share | p |
|---|---|---|---|---|---|---|---|---|
| blocked30 | warm5 | a0.3 | bayside | 3 | 10 | 0.0 | 0.0 | 0.0923 |
| blocked30 | warm5 | a0.3 | blocks | 1 | 11 | 0.0 | 0.0 | 0.0063 |
| blocked30 | warm5 | a0.3 | boulevard | 2 | 13 | 3.0 | 0.0017 | 0.0074 |
| outage90 | warm5 | a0.3 | bayside | 7 | 1 | 0.0 | 0.0 | 0.0703 |
| outage90 | warm5 | a0.3 | blocks | 9 | 0 | 0.0 | 0.0 | 0.0039 |
| outage90 | warm5 | a0.3 | boulevard | 11 | 0 | 0.0 | 0.0 | 0.001 |
| quiet45 | warm5 | a0.3 | bayside | 19 | 0 | -8.0 | -0.0056 | 0.0 |
| quiet45 | warm5 | a0.3 | blocks | 17 | 0 | -5.0 | -0.0032 | 0.0 |
| quiet45 | warm5 | a0.3 | boulevard | 13 | 0 | -6.0 | -0.0034 | 0.0002 |
| quiet90 | warm5 | a0.3 | bayside | 14 | 0 | -6.0 | -0.0042 | 0.0001 |
| quiet90 | warm5 | a0.3 | blocks | 15 | 0 | -5.0 | -0.0032 | 0.0001 |
| quiet90 | warm5 | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| quietdrift90 | warm5 | a0.3 | bayside | 15 | 1 | -8.0 | -0.0055 | 0.0005 |
| quietdrift90 | warm5 | a0.3 | blocks | 15 | 3 | -2.0 | -0.0013 | 0.0075 |
| quietdrift90 | warm5 | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| blocked30 | warm10 | a0.3 | bayside | 7 | 1 | 0.0 | 0.0 | 0.0703 |
| blocked30 | warm10 | a0.3 | blocks | 6 | 0 | 0.0 | 0.0 | 0.0312 |
| blocked30 | warm10 | a0.3 | boulevard | 6 | 0 | 0.0 | 0.0 | 0.0312 |
| outage90 | warm10 | a0.3 | bayside | 7 | 1 | 0.0 | 0.0 | 0.0703 |
| outage90 | warm10 | a0.3 | blocks | 9 | 0 | 0.0 | 0.0 | 0.0039 |
| outage90 | warm10 | a0.3 | boulevard | 12 | 0 | -1.0 | -0.0006 | 0.0005 |
| quiet45 | warm10 | a0.3 | bayside | 19 | 0 | -8.0 | -0.0056 | 0.0 |
| quiet45 | warm10 | a0.3 | blocks | 17 | 0 | -5.0 | -0.0032 | 0.0 |
| quiet45 | warm10 | a0.3 | boulevard | 13 | 0 | -6.0 | -0.0034 | 0.0002 |
| quiet90 | warm10 | a0.3 | bayside | 14 | 0 | -6.0 | -0.0042 | 0.0001 |
| quiet90 | warm10 | a0.3 | blocks | 15 | 0 | -5.0 | -0.0032 | 0.0001 |
| quiet90 | warm10 | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| quietdrift90 | warm10 | a0.3 | bayside | 15 | 1 | -8.0 | -0.0055 | 0.0005 |
| quietdrift90 | warm10 | a0.3 | blocks | 15 | 3 | -2.0 | -0.0013 | 0.0075 |
| quietdrift90 | warm10 | a0.3 | boulevard | 17 | 0 | -6.0 | -0.0034 | 0.0 |
| blocked30 | warm5 | warm10 | bayside | 0 | 9 | 0.0 | 0.0 | 0.0039 |
| blocked30 | warm5 | warm10 | blocks | 0 | 11 | 0.0 | 0.0 | 0.001 |
| blocked30 | warm5 | warm10 | boulevard | 0 | 13 | 3.0 | 0.0017 | 0.0002 |
| outage90 | warm5 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| outage90 | warm5 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| outage90 | warm5 | warm10 | boulevard | 0 | 1 | 0.0 | 0.0 | 1.0 |
| quiet45 | warm5 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| quiet45 | warm5 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| quiet45 | warm5 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | warm5 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | warm5 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | warm5 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quietdrift90 | warm5 | warm10 | bayside | 0 | 0 | 0.0 | 0.0 | None |
| quietdrift90 | warm5 | warm10 | blocks | 0 | 0 | 0.0 | 0.0 | None |
| quietdrift90 | warm5 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| blocked30 | restart+warm5 | warm5 | bayside | 16 | 0 | -3.0 | -0.0021 | 0.0 |
| blocked30 | restart+warm5 | warm5 | blocks | 18 | 0 | -11.0 | -0.0069 | 0.0 |
| blocked30 | restart+warm5 | warm5 | boulevard | 3 | 1 | 0.0 | 0.0 | 0.625 |
| outage90 | restart+warm5 | warm5 | bayside | 14 | 0 | -4.0 | -0.0028 | 0.0001 |
| outage90 | restart+warm5 | warm5 | blocks | 17 | 0 | -11.0 | -0.007 | 0.0 |
| outage90 | restart+warm5 | warm5 | boulevard | 1 | 2 | 0.0 | 0.0 | 1.0 |
| quiet45 | restart+warm5 | warm5 | bayside | 18 | 0 | -2.0 | -0.0014 | 0.0 |
| quiet45 | restart+warm5 | warm5 | blocks | 22 | 0 | -11.0 | -0.0071 | 0.0 |
| quiet45 | restart+warm5 | warm5 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | restart+warm5 | warm5 | bayside | 15 | 0 | -4.0 | -0.0028 | 0.0001 |
| quiet90 | restart+warm5 | warm5 | blocks | 19 | 0 | -12.0 | -0.0077 | 0.0 |
| quiet90 | restart+warm5 | warm5 | boulevard | 2 | 0 | 0.0 | 0.0 | 0.5 |
| quietdrift90 | restart+warm5 | warm5 | bayside | 14 | 2 | -4.0 | -0.0028 | 0.0042 |
| quietdrift90 | restart+warm5 | warm5 | blocks | 18 | 1 | -20.0 | -0.0127 | 0.0001 |
| quietdrift90 | restart+warm5 | warm5 | boulevard | 3 | 6 | 0.0 | 0.0 | 0.5078 |
| blocked30 | restart+warm10 | warm10 | bayside | 15 | 0 | -4.0 | -0.0027 | 0.0001 |
| blocked30 | restart+warm10 | warm10 | blocks | 18 | 0 | -14.0 | -0.0088 | 0.0 |
| blocked30 | restart+warm10 | warm10 | boulevard | 2 | 0 | 0.0 | 0.0 | 0.5 |
| outage90 | restart+warm10 | warm10 | bayside | 14 | 0 | -4.0 | -0.0028 | 0.0001 |
| outage90 | restart+warm10 | warm10 | blocks | 17 | 0 | -11.0 | -0.007 | 0.0 |
| outage90 | restart+warm10 | warm10 | boulevard | 1 | 2 | 0.0 | 0.0 | 1.0 |
| quiet45 | restart+warm10 | warm10 | bayside | 18 | 0 | -2.0 | -0.0014 | 0.0 |
| quiet45 | restart+warm10 | warm10 | blocks | 22 | 0 | -11.0 | -0.0071 | 0.0 |
| quiet45 | restart+warm10 | warm10 | boulevard | 0 | 0 | 0.0 | 0.0 | None |
| quiet90 | restart+warm10 | warm10 | bayside | 15 | 0 | -4.0 | -0.0028 | 0.0001 |
| quiet90 | restart+warm10 | warm10 | blocks | 19 | 0 | -12.0 | -0.0077 | 0.0 |
| quiet90 | restart+warm10 | warm10 | boulevard | 2 | 0 | 0.0 | 0.0 | 0.5 |
| quietdrift90 | restart+warm10 | warm10 | bayside | 14 | 2 | -4.0 | -0.0028 | 0.0042 |
| quietdrift90 | restart+warm10 | warm10 | blocks | 18 | 1 | -20.0 | -0.0127 | 0.0001 |
| quietdrift90 | restart+warm10 | warm10 | boulevard | 3 | 6 | 0.0 | 0.0 | 0.5078 |

## What the profile costs each variant

| variant | profile | against | faster | slower | lost | gained | largest median diff |
|---|---|---|---|---|---|---|---|
| a0.3 | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0139 |
| warm5 | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0224 |
| warm10 | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0182 |
| restart+warm5 | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0225 |
| restart+warm10 | blocked30 | quiet90 | 0/3 | 3 | 0 | 0 | 0.0183 |

## The pilot's worst idea of where it is, per mission (over 20 m: thrown off)

| profile | variant | course | missions | median of max m | largest m | missions over 20 m |
|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 61.28 | 63.82 | 19 |
| blocked30 | a0.3 | blocks | 24 | 56.53 | 61.96 | 19 |
| blocked30 | a0.3 | boulevard | 24 | 63.15 | 66.61 | 20 |
| blocked30 | restart+warm10 | bayside | 24 | 10.03 | 10.93 | 0 |
| blocked30 | restart+warm10 | blocks | 24 | 10.12 | 11.41 | 0 |
| blocked30 | restart+warm10 | boulevard | 24 | 10.16 | 11.29 | 0 |
| blocked30 | restart+warm5 | bayside | 24 | 10.18 | 10.93 | 0 |
| blocked30 | restart+warm5 | blocks | 24 | 10.27 | 11.03 | 0 |
| blocked30 | restart+warm5 | boulevard | 24 | 10.29 | 11.03 | 0 |
| blocked30 | warm10 | bayside | 24 | 61.24 | 63.83 | 19 |
| blocked30 | warm10 | blocks | 24 | 56.23 | 62.29 | 18 |
| blocked30 | warm10 | boulevard | 24 | 63.0 | 66.43 | 20 |
| blocked30 | warm5 | bayside | 24 | 61.12 | 63.65 | 19 |
| blocked30 | warm5 | blocks | 24 | 56.88 | 61.94 | 18 |
| blocked30 | warm5 | boulevard | 24 | 63.14 | 66.61 | 20 |
| outage90 | a0.3 | bayside | 24 | 60.72 | 64.96 | 19 |
| outage90 | a0.3 | blocks | 24 | 54.36 | 62.95 | 18 |
| outage90 | a0.3 | boulevard | 24 | 63.34 | 66.99 | 20 |
| outage90 | restart+warm10 | bayside | 24 | 10.5 | 11.8 | 0 |
| outage90 | restart+warm10 | blocks | 24 | 10.82 | 12.34 | 0 |
| outage90 | restart+warm10 | boulevard | 24 | 10.94 | 11.67 | 0 |
| outage90 | restart+warm5 | bayside | 24 | 10.5 | 11.8 | 0 |
| outage90 | restart+warm5 | blocks | 24 | 10.82 | 12.34 | 0 |
| outage90 | restart+warm5 | boulevard | 24 | 10.94 | 11.67 | 0 |
| outage90 | warm10 | bayside | 24 | 60.85 | 64.78 | 18 |
| outage90 | warm10 | blocks | 24 | 56.61 | 62.84 | 19 |
| outage90 | warm10 | boulevard | 24 | 63.34 | 67.53 | 20 |
| outage90 | warm5 | bayside | 24 | 60.85 | 64.78 | 18 |
| outage90 | warm5 | blocks | 24 | 56.61 | 62.84 | 19 |
| outage90 | warm5 | boulevard | 24 | 63.34 | 67.53 | 20 |
| quiet45 | a0.3 | bayside | 24 | 35.28 | 63.82 | 24 |
| quiet45 | a0.3 | blocks | 24 | 35.16 | 58.16 | 24 |
| quiet45 | a0.3 | boulevard | 24 | 36.3 | 64.35 | 24 |
| quiet45 | restart+warm10 | bayside | 24 | 10.02 | 11.99 | 0 |
| quiet45 | restart+warm10 | blocks | 24 | 10.12 | 11.96 | 0 |
| quiet45 | restart+warm10 | boulevard | 24 | 10.21 | 12.02 | 0 |
| quiet45 | restart+warm5 | bayside | 24 | 10.02 | 11.99 | 0 |
| quiet45 | restart+warm5 | blocks | 24 | 10.12 | 11.96 | 0 |
| quiet45 | restart+warm5 | boulevard | 24 | 10.21 | 12.02 | 0 |
| quiet45 | warm10 | bayside | 24 | 35.43 | 64.02 | 24 |
| quiet45 | warm10 | blocks | 24 | 35.22 | 56.39 | 24 |
| quiet45 | warm10 | boulevard | 24 | 36.49 | 63.9 | 24 |
| quiet45 | warm5 | bayside | 24 | 35.43 | 64.02 | 24 |
| quiet45 | warm5 | blocks | 24 | 35.22 | 56.39 | 24 |
| quiet45 | warm5 | boulevard | 24 | 36.49 | 63.9 | 24 |
| quiet90 | a0.3 | bayside | 24 | 60.83 | 65.35 | 19 |
| quiet90 | a0.3 | blocks | 24 | 53.72 | 61.58 | 18 |
| quiet90 | a0.3 | boulevard | 24 | 62.98 | 65.97 | 20 |
| quiet90 | restart+warm10 | bayside | 24 | 9.95 | 10.94 | 0 |
| quiet90 | restart+warm10 | blocks | 24 | 9.98 | 11.41 | 0 |
| quiet90 | restart+warm10 | boulevard | 24 | 10.11 | 11.22 | 0 |
| quiet90 | restart+warm5 | bayside | 24 | 9.95 | 10.94 | 0 |
| quiet90 | restart+warm5 | blocks | 24 | 9.98 | 11.41 | 0 |
| quiet90 | restart+warm5 | boulevard | 24 | 10.11 | 11.22 | 0 |
| quiet90 | warm10 | bayside | 24 | 61.05 | 64.62 | 18 |
| quiet90 | warm10 | blocks | 24 | 55.7 | 62.75 | 19 |
| quiet90 | warm10 | boulevard | 24 | 63.12 | 66.43 | 20 |
| quiet90 | warm5 | bayside | 24 | 61.05 | 64.62 | 18 |
| quiet90 | warm5 | blocks | 24 | 55.7 | 62.75 | 19 |
| quiet90 | warm5 | boulevard | 24 | 63.12 | 66.43 | 20 |
| quietdrift90 | a0.3 | bayside | 24 | 61.14 | 65.69 | 19 |
| quietdrift90 | a0.3 | blocks | 24 | 55.94 | 61.27 | 19 |
| quietdrift90 | a0.3 | boulevard | 24 | 62.73 | 65.83 | 20 |
| quietdrift90 | restart+warm10 | bayside | 24 | 11.5 | 26.15 | 3 |
| quietdrift90 | restart+warm10 | blocks | 24 | 10.7 | 22.68 | 2 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 11.47 | 24.73 | 3 |
| quietdrift90 | restart+warm5 | bayside | 24 | 11.5 | 26.15 | 3 |
| quietdrift90 | restart+warm5 | blocks | 24 | 10.7 | 22.68 | 2 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 11.47 | 24.73 | 3 |
| quietdrift90 | warm10 | bayside | 24 | 60.86 | 65.23 | 19 |
| quietdrift90 | warm10 | blocks | 24 | 55.22 | 62.72 | 19 |
| quietdrift90 | warm10 | boulevard | 24 | 62.75 | 65.92 | 20 |
| quietdrift90 | warm5 | bayside | 24 | 60.86 | 65.23 | 19 |
| quietdrift90 | warm5 | blocks | 24 | 55.22 | 62.72 | 19 |
| quietdrift90 | warm5 | boulevard | 24 | 62.75 | 65.92 | 20 |

## Where the pilot thinks it is, against where it is

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 6.55 | 8.63 |
| blocked30 | a0.3 | blocks | 24 | 6.4 | 8.33 |
| blocked30 | a0.3 | boulevard | 24 | 6.54 | 8.61 |
| blocked30 | restart+warm10 | bayside | 24 | 6.37 | 7.9 |
| blocked30 | restart+warm10 | blocks | 24 | 6.24 | 7.86 |
| blocked30 | restart+warm10 | boulevard | 24 | 6.39 | 7.91 |
| blocked30 | restart+warm5 | bayside | 24 | 6.42 | 7.97 |
| blocked30 | restart+warm5 | blocks | 24 | 6.33 | 7.93 |
| blocked30 | restart+warm5 | boulevard | 24 | 6.38 | 8.0 |
| blocked30 | warm10 | bayside | 24 | 6.52 | 8.5 |
| blocked30 | warm10 | blocks | 24 | 6.37 | 8.31 |
| blocked30 | warm10 | boulevard | 24 | 6.5 | 8.54 |
| blocked30 | warm5 | bayside | 24 | 6.54 | 8.56 |
| blocked30 | warm5 | blocks | 24 | 6.4 | 8.35 |
| blocked30 | warm5 | boulevard | 24 | 6.53 | 8.59 |
| outage90 | a0.3 | bayside | 24 | 6.45 | 8.57 |
| outage90 | a0.3 | blocks | 24 | 6.42 | 8.5 |
| outage90 | a0.3 | boulevard | 24 | 6.54 | 8.71 |
| outage90 | restart+warm10 | bayside | 24 | 6.29 | 8.14 |
| outage90 | restart+warm10 | blocks | 24 | 6.36 | 8.19 |
| outage90 | restart+warm10 | boulevard | 24 | 6.47 | 8.23 |
| outage90 | restart+warm5 | bayside | 24 | 6.29 | 8.14 |
| outage90 | restart+warm5 | blocks | 24 | 6.36 | 8.19 |
| outage90 | restart+warm5 | boulevard | 24 | 6.47 | 8.27 |
| outage90 | warm10 | bayside | 24 | 6.41 | 8.54 |
| outage90 | warm10 | blocks | 24 | 6.45 | 8.56 |
| outage90 | warm10 | boulevard | 24 | 6.56 | 8.71 |
| outage90 | warm5 | bayside | 24 | 6.41 | 8.54 |
| outage90 | warm5 | blocks | 24 | 6.45 | 8.56 |
| outage90 | warm5 | boulevard | 24 | 6.58 | 8.71 |
| quiet45 | a0.3 | bayside | 24 | 6.42 | 8.77 |
| quiet45 | a0.3 | blocks | 24 | 6.36 | 8.62 |
| quiet45 | a0.3 | boulevard | 24 | 6.41 | 9.08 |
| quiet45 | restart+warm10 | bayside | 24 | 6.28 | 7.78 |
| quiet45 | restart+warm10 | blocks | 24 | 6.25 | 7.84 |
| quiet45 | restart+warm10 | boulevard | 24 | 6.35 | 7.95 |
| quiet45 | restart+warm5 | bayside | 24 | 6.28 | 7.78 |
| quiet45 | restart+warm5 | blocks | 24 | 6.25 | 7.84 |
| quiet45 | restart+warm5 | boulevard | 24 | 6.35 | 7.95 |
| quiet45 | warm10 | bayside | 24 | 6.45 | 8.91 |
| quiet45 | warm10 | blocks | 24 | 6.39 | 8.75 |
| quiet45 | warm10 | boulevard | 24 | 6.56 | 9.14 |
| quiet45 | warm5 | bayside | 24 | 6.45 | 8.91 |
| quiet45 | warm5 | blocks | 24 | 6.39 | 8.75 |
| quiet45 | warm5 | boulevard | 24 | 6.56 | 9.14 |
| quiet90 | a0.3 | bayside | 24 | 6.4 | 8.29 |
| quiet90 | a0.3 | blocks | 24 | 6.28 | 8.16 |
| quiet90 | a0.3 | boulevard | 24 | 6.41 | 8.37 |
| quiet90 | restart+warm10 | bayside | 24 | 6.33 | 7.75 |
| quiet90 | restart+warm10 | blocks | 24 | 6.28 | 7.83 |
| quiet90 | restart+warm10 | boulevard | 24 | 6.41 | 7.92 |
| quiet90 | restart+warm5 | bayside | 24 | 6.33 | 7.75 |
| quiet90 | restart+warm5 | blocks | 24 | 6.28 | 7.83 |
| quiet90 | restart+warm5 | boulevard | 24 | 6.41 | 7.92 |
| quiet90 | warm10 | bayside | 24 | 6.46 | 8.32 |
| quiet90 | warm10 | blocks | 24 | 6.38 | 8.25 |
| quiet90 | warm10 | boulevard | 24 | 6.54 | 8.57 |
| quiet90 | warm5 | bayside | 24 | 6.46 | 8.32 |
| quiet90 | warm5 | blocks | 24 | 6.38 | 8.25 |
| quiet90 | warm5 | boulevard | 24 | 6.54 | 8.57 |
| quietdrift90 | a0.3 | bayside | 24 | 6.42 | 8.91 |
| quietdrift90 | a0.3 | blocks | 24 | 6.35 | 8.43 |
| quietdrift90 | a0.3 | boulevard | 24 | 6.44 | 8.71 |
| quietdrift90 | restart+warm10 | bayside | 24 | 6.42 | 8.32 |
| quietdrift90 | restart+warm10 | blocks | 24 | 6.35 | 8.04 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 6.5 | 8.12 |
| quietdrift90 | restart+warm5 | bayside | 24 | 6.42 | 8.32 |
| quietdrift90 | restart+warm5 | blocks | 24 | 6.35 | 8.04 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 6.5 | 8.12 |
| quietdrift90 | warm10 | bayside | 24 | 6.48 | 8.95 |
| quietdrift90 | warm10 | blocks | 24 | 6.44 | 8.56 |
| quietdrift90 | warm10 | boulevard | 24 | 6.62 | 9.09 |
| quietdrift90 | warm5 | bayside | 24 | 6.48 | 8.95 |
| quietdrift90 | warm5 | blocks | 24 | 6.44 | 8.56 |
| quietdrift90 | warm5 | boulevard | 24 | 6.62 | 9.09 |

## Recovery moves and filter restarts (medians)

| profile | variant | course | missions | recoveries (median) | restarts (median) |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 2.0 | None |
| blocked30 | a0.3 | blocks | 24 | 2.0 | None |
| blocked30 | a0.3 | boulevard | 24 | 2.0 | None |
| blocked30 | restart+warm10 | bayside | 24 | 1.0 | 4.0 |
| blocked30 | restart+warm10 | blocks | 24 | 1.0 | 4.0 |
| blocked30 | restart+warm10 | boulevard | 24 | 1.0 | 5.0 |
| blocked30 | restart+warm5 | bayside | 24 | 2.0 | 4.0 |
| blocked30 | restart+warm5 | blocks | 24 | 2.0 | 4.0 |
| blocked30 | restart+warm5 | boulevard | 24 | 2.0 | 5.0 |
| blocked30 | warm10 | bayside | 24 | 1.0 | None |
| blocked30 | warm10 | blocks | 24 | 1.0 | None |
| blocked30 | warm10 | boulevard | 24 | 1.0 | None |
| blocked30 | warm5 | bayside | 24 | 2.0 | None |
| blocked30 | warm5 | blocks | 24 | 2.0 | None |
| blocked30 | warm5 | boulevard | 24 | 2.0 | None |
| outage90 | a0.3 | bayside | 24 | 0.0 | None |
| outage90 | a0.3 | blocks | 24 | 1.0 | None |
| outage90 | a0.3 | boulevard | 24 | 1.0 | None |
| outage90 | restart+warm10 | bayside | 24 | 0.0 | 4.0 |
| outage90 | restart+warm10 | blocks | 24 | 0.0 | 4.0 |
| outage90 | restart+warm10 | boulevard | 24 | 0.0 | 5.0 |
| outage90 | restart+warm5 | bayside | 24 | 0.0 | 4.0 |
| outage90 | restart+warm5 | blocks | 24 | 0.0 | 4.0 |
| outage90 | restart+warm5 | boulevard | 24 | 0.0 | 5.0 |
| outage90 | warm10 | bayside | 24 | 0.0 | None |
| outage90 | warm10 | blocks | 24 | 0.0 | None |
| outage90 | warm10 | boulevard | 24 | 0.0 | None |
| outage90 | warm5 | bayside | 24 | 0.0 | None |
| outage90 | warm5 | blocks | 24 | 0.0 | None |
| outage90 | warm5 | boulevard | 24 | 0.0 | None |
| quiet45 | a0.3 | bayside | 24 | 1.0 | None |
| quiet45 | a0.3 | blocks | 24 | 1.0 | None |
| quiet45 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet45 | restart+warm10 | bayside | 24 | 0.0 | 6.0 |
| quiet45 | restart+warm10 | blocks | 24 | 0.0 | 6.0 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.0 | 8.0 |
| quiet45 | restart+warm5 | bayside | 24 | 0.0 | 6.0 |
| quiet45 | restart+warm5 | blocks | 24 | 0.0 | 6.0 |
| quiet45 | restart+warm5 | boulevard | 24 | 0.0 | 8.0 |
| quiet45 | warm10 | bayside | 24 | 0.0 | None |
| quiet45 | warm10 | blocks | 24 | 0.0 | None |
| quiet45 | warm10 | boulevard | 24 | 0.0 | None |
| quiet45 | warm5 | bayside | 24 | 0.0 | None |
| quiet45 | warm5 | blocks | 24 | 0.0 | None |
| quiet45 | warm5 | boulevard | 24 | 0.0 | None |
| quiet90 | a0.3 | bayside | 24 | 1.0 | None |
| quiet90 | a0.3 | blocks | 24 | 1.0 | None |
| quiet90 | a0.3 | boulevard | 24 | 1.0 | None |
| quiet90 | restart+warm10 | bayside | 24 | 0.0 | 4.0 |
| quiet90 | restart+warm10 | blocks | 24 | 0.0 | 4.0 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.0 | 5.0 |
| quiet90 | restart+warm5 | bayside | 24 | 0.0 | 4.0 |
| quiet90 | restart+warm5 | blocks | 24 | 0.0 | 4.0 |
| quiet90 | restart+warm5 | boulevard | 24 | 0.0 | 5.0 |
| quiet90 | warm10 | bayside | 24 | 0.0 | None |
| quiet90 | warm10 | blocks | 24 | 0.0 | None |
| quiet90 | warm10 | boulevard | 24 | 0.0 | None |
| quiet90 | warm5 | bayside | 24 | 0.0 | None |
| quiet90 | warm5 | blocks | 24 | 0.0 | None |
| quiet90 | warm5 | boulevard | 24 | 0.0 | None |
| quietdrift90 | a0.3 | bayside | 24 | 1.0 | None |
| quietdrift90 | a0.3 | blocks | 24 | 1.0 | None |
| quietdrift90 | a0.3 | boulevard | 24 | 1.0 | None |
| quietdrift90 | restart+warm10 | bayside | 24 | 0.0 | 4.0 |
| quietdrift90 | restart+warm10 | blocks | 24 | 0.0 | 4.0 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 0.0 | 5.0 |
| quietdrift90 | restart+warm5 | bayside | 24 | 0.0 | 4.0 |
| quietdrift90 | restart+warm5 | blocks | 24 | 0.0 | 4.0 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 0.0 | 5.0 |
| quietdrift90 | warm10 | bayside | 24 | 0.0 | None |
| quietdrift90 | warm10 | blocks | 24 | 0.0 | None |
| quietdrift90 | warm10 | boulevard | 24 | 0.0 | None |
| quietdrift90 | warm5 | bayside | 24 | 0.0 | None |
| quietdrift90 | warm5 | blocks | 24 | 0.0 | None |
| quietdrift90 | warm5 | boulevard | 24 | 0.0 | None |

## Near path corners (pace_n.py's record)

| profile | variant | course | missions | corners | median m | p95 m | max m | median past m | max past m |
|---|---|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | blocks | 24 | 9.0 | 1.06 | 3.25 | 5.06 | 2.03 | 3.27 |
| blocked30 | restart+warm10 | blocks | 24 | 9.0 | 0.95 | 2.66 | 4.54 | 1.94 | 2.78 |
| blocked30 | restart+warm5 | blocks | 24 | 9.0 | 0.91 | 2.79 | 4.68 | 1.97 | 2.63 |
| blocked30 | warm10 | blocks | 24 | 9.0 | 1.0 | 3.26 | 5.07 | 2.0 | 3.16 |
| blocked30 | warm5 | blocks | 24 | 9.0 | 0.98 | 3.14 | 4.94 | 2.02 | 3.45 |
| outage90 | a0.3 | blocks | 24 | 9.0 | 1.2 | 3.36 | 5.4 | 2.17 | 3.74 |
| outage90 | restart+warm10 | blocks | 24 | 9.0 | 1.17 | 2.95 | 4.14 | 2.16 | 3.16 |
| outage90 | restart+warm5 | blocks | 24 | 9.0 | 1.17 | 2.95 | 4.14 | 2.16 | 3.16 |
| outage90 | warm10 | blocks | 24 | 9.0 | 1.23 | 3.33 | 4.92 | 2.2 | 3.46 |
| outage90 | warm5 | blocks | 24 | 9.0 | 1.23 | 3.33 | 4.92 | 2.2 | 3.46 |
| quiet45 | a0.3 | blocks | 24 | 9.0 | 0.96 | 3.1 | 4.83 | 2.06 | 3.68 |
| quiet45 | restart+warm10 | blocks | 24 | 9.0 | 0.86 | 2.56 | 4.66 | 1.95 | 2.64 |
| quiet45 | restart+warm5 | blocks | 24 | 9.0 | 0.86 | 2.56 | 4.66 | 1.95 | 2.64 |
| quiet45 | warm10 | blocks | 24 | 9.0 | 0.91 | 3.37 | 4.97 | 2.04 | 4.41 |
| quiet45 | warm5 | blocks | 24 | 9.0 | 0.91 | 3.37 | 4.97 | 2.04 | 4.41 |
| quiet90 | a0.3 | blocks | 24 | 9.0 | 1.0 | 2.95 | 4.69 | 2.02 | 2.96 |
| quiet90 | restart+warm10 | blocks | 24 | 9.0 | 0.93 | 2.52 | 4.57 | 1.94 | 2.62 |
| quiet90 | restart+warm5 | blocks | 24 | 9.0 | 0.93 | 2.52 | 4.57 | 1.94 | 2.62 |
| quiet90 | warm10 | blocks | 24 | 9.0 | 0.98 | 2.88 | 4.71 | 2.01 | 2.87 |
| quiet90 | warm5 | blocks | 24 | 9.0 | 0.98 | 2.88 | 4.71 | 2.01 | 2.87 |
| quietdrift90 | a0.3 | blocks | 24 | 9.0 | 1.6 | 4.63 | 6.58 | 2.2 | 4.62 |
| quietdrift90 | restart+warm10 | blocks | 24 | 9.0 | 1.49 | 4.44 | 6.99 | 1.73 | 3.98 |
| quietdrift90 | restart+warm5 | blocks | 24 | 9.0 | 1.49 | 4.44 | 6.99 | 1.73 | 3.98 |
| quietdrift90 | warm10 | blocks | 24 | 9.0 | 1.49 | 4.59 | 7.61 | 2.04 | 4.65 |
| quietdrift90 | warm5 | blocks | 24 | 9.0 | 1.49 | 4.59 | 7.61 | 2.04 | 4.65 |

## Distance from the course while driving forward

| profile | variant | course | missions | median m | p95 m |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 0.2 | 1.7 |
| blocked30 | a0.3 | blocks | 24 | 0.3 | 2.94 |
| blocked30 | a0.3 | boulevard | 24 | 0.14 | 0.73 |
| blocked30 | restart+warm10 | bayside | 24 | 0.19 | 0.97 |
| blocked30 | restart+warm10 | blocks | 24 | 0.27 | 2.39 |
| blocked30 | restart+warm10 | boulevard | 24 | 0.13 | 0.66 |
| blocked30 | restart+warm5 | bayside | 24 | 0.2 | 1.04 |
| blocked30 | restart+warm5 | blocks | 24 | 0.24 | 2.42 |
| blocked30 | restart+warm5 | boulevard | 24 | 0.14 | 0.68 |
| blocked30 | warm10 | bayside | 24 | 0.2 | 1.71 |
| blocked30 | warm10 | blocks | 24 | 0.3 | 2.98 |
| blocked30 | warm10 | boulevard | 24 | 0.14 | 0.72 |
| blocked30 | warm5 | bayside | 24 | 0.2 | 1.85 |
| blocked30 | warm5 | blocks | 24 | 0.29 | 2.93 |
| blocked30 | warm5 | boulevard | 24 | 0.15 | 0.8 |
| outage90 | a0.3 | bayside | 24 | 0.57 | 4.05 |
| outage90 | a0.3 | blocks | 24 | 0.76 | 3.67 |
| outage90 | a0.3 | boulevard | 24 | 0.58 | 3.02 |
| outage90 | restart+warm10 | bayside | 24 | 0.53 | 2.73 |
| outage90 | restart+warm10 | blocks | 24 | 0.76 | 3.05 |
| outage90 | restart+warm10 | boulevard | 24 | 0.56 | 3.03 |
| outage90 | restart+warm5 | bayside | 24 | 0.53 | 2.73 |
| outage90 | restart+warm5 | blocks | 24 | 0.76 | 3.05 |
| outage90 | restart+warm5 | boulevard | 24 | 0.56 | 3.03 |
| outage90 | warm10 | bayside | 24 | 0.56 | 3.64 |
| outage90 | warm10 | blocks | 24 | 0.76 | 3.74 |
| outage90 | warm10 | boulevard | 24 | 0.58 | 2.96 |
| outage90 | warm5 | bayside | 24 | 0.56 | 3.64 |
| outage90 | warm5 | blocks | 24 | 0.76 | 3.74 |
| outage90 | warm5 | boulevard | 24 | 0.58 | 2.96 |
| quiet45 | a0.3 | bayside | 24 | 0.22 | 2.15 |
| quiet45 | a0.3 | blocks | 24 | 0.32 | 3.05 |
| quiet45 | a0.3 | boulevard | 24 | 0.15 | 0.9 |
| quiet45 | restart+warm10 | bayside | 24 | 0.21 | 1.44 |
| quiet45 | restart+warm10 | blocks | 24 | 0.28 | 2.35 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.14 | 0.69 |
| quiet45 | restart+warm5 | bayside | 24 | 0.21 | 1.44 |
| quiet45 | restart+warm5 | blocks | 24 | 0.28 | 2.35 |
| quiet45 | restart+warm5 | boulevard | 24 | 0.14 | 0.69 |
| quiet45 | warm10 | bayside | 24 | 0.21 | 1.96 |
| quiet45 | warm10 | blocks | 24 | 0.33 | 2.8 |
| quiet45 | warm10 | boulevard | 24 | 0.15 | 0.85 |
| quiet45 | warm5 | bayside | 24 | 0.21 | 1.96 |
| quiet45 | warm5 | blocks | 24 | 0.33 | 2.8 |
| quiet45 | warm5 | boulevard | 24 | 0.15 | 0.85 |
| quiet90 | a0.3 | bayside | 24 | 0.21 | 2.56 |
| quiet90 | a0.3 | blocks | 24 | 0.3 | 3.21 |
| quiet90 | a0.3 | boulevard | 24 | 0.14 | 0.84 |
| quiet90 | restart+warm10 | bayside | 24 | 0.19 | 1.09 |
| quiet90 | restart+warm10 | blocks | 24 | 0.27 | 2.42 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.14 | 0.62 |
| quiet90 | restart+warm5 | bayside | 24 | 0.19 | 1.09 |
| quiet90 | restart+warm5 | blocks | 24 | 0.27 | 2.42 |
| quiet90 | restart+warm5 | boulevard | 24 | 0.14 | 0.62 |
| quiet90 | warm10 | bayside | 24 | 0.21 | 2.06 |
| quiet90 | warm10 | blocks | 24 | 0.31 | 2.88 |
| quiet90 | warm10 | boulevard | 24 | 0.14 | 0.75 |
| quiet90 | warm5 | bayside | 24 | 0.21 | 2.06 |
| quiet90 | warm5 | blocks | 24 | 0.31 | 2.88 |
| quiet90 | warm5 | boulevard | 24 | 0.14 | 0.75 |
| quietdrift90 | a0.3 | bayside | 24 | 1.46 | 6.37 |
| quietdrift90 | a0.3 | blocks | 24 | 1.62 | 5.79 |
| quietdrift90 | a0.3 | boulevard | 24 | 1.44 | 7.0 |
| quietdrift90 | restart+warm10 | bayside | 24 | 1.51 | 6.37 |
| quietdrift90 | restart+warm10 | blocks | 24 | 1.58 | 5.48 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 1.42 | 5.96 |
| quietdrift90 | restart+warm5 | bayside | 24 | 1.51 | 6.37 |
| quietdrift90 | restart+warm5 | blocks | 24 | 1.58 | 5.48 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 1.42 | 5.96 |
| quietdrift90 | warm10 | bayside | 24 | 1.59 | 6.63 |
| quietdrift90 | warm10 | blocks | 24 | 1.58 | 5.51 |
| quietdrift90 | warm10 | boulevard | 24 | 1.45 | 6.7 |
| quietdrift90 | warm5 | bayside | 24 | 1.59 | 6.63 |
| quietdrift90 | warm5 | blocks | 24 | 1.58 | 5.51 |
| quietdrift90 | warm5 | boulevard | 24 | 1.45 | 6.7 |

## Largest distance from the course, and refused reports

| profile | variant | course | missions | median of max m | largest m | refused | missions refused |
|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 6.54 | 7.15 | 0 | 0 |
| blocked30 | a0.3 | blocks | 24 | 6.89 | 8.29 | 0 | 0 |
| blocked30 | a0.3 | boulevard | 24 | 6.82 | 7.22 | 0 | 0 |
| blocked30 | restart+warm10 | bayside | 24 | 6.42 | 7.04 | 0 | 0 |
| blocked30 | restart+warm10 | blocks | 24 | 6.84 | 7.25 | 0 | 0 |
| blocked30 | restart+warm10 | boulevard | 24 | 6.81 | 7.35 | 0 | 0 |
| blocked30 | restart+warm5 | bayside | 24 | 6.74 | 7.4 | 0 | 0 |
| blocked30 | restart+warm5 | blocks | 24 | 6.94 | 7.28 | 0 | 0 |
| blocked30 | restart+warm5 | boulevard | 24 | 6.99 | 7.45 | 0 | 0 |
| blocked30 | warm10 | bayside | 24 | 6.44 | 7.33 | 0 | 0 |
| blocked30 | warm10 | blocks | 24 | 6.91 | 8.94 | 0 | 0 |
| blocked30 | warm10 | boulevard | 24 | 6.81 | 7.35 | 0 | 0 |
| blocked30 | warm5 | bayside | 24 | 6.74 | 7.54 | 0 | 0 |
| blocked30 | warm5 | blocks | 24 | 7.04 | 8.39 | 0 | 0 |
| blocked30 | warm5 | boulevard | 24 | 6.99 | 7.67 | 0 | 0 |
| outage90 | a0.3 | bayside | 24 | 7.08 | 11.12 | 0 | 0 |
| outage90 | a0.3 | blocks | 24 | 8.05 | 11.01 | 0 | 0 |
| outage90 | a0.3 | boulevard | 24 | 7.72 | 10.22 | 0 | 0 |
| outage90 | restart+warm10 | bayside | 24 | 6.91 | 7.95 | 0 | 0 |
| outage90 | restart+warm10 | blocks | 24 | 7.15 | 8.9 | 0 | 0 |
| outage90 | restart+warm10 | boulevard | 24 | 7.56 | 10.19 | 0 | 0 |
| outage90 | restart+warm5 | bayside | 24 | 6.91 | 7.95 | 0 | 0 |
| outage90 | restart+warm5 | blocks | 24 | 7.15 | 8.9 | 0 | 0 |
| outage90 | restart+warm5 | boulevard | 24 | 7.56 | 10.19 | 0 | 0 |
| outage90 | warm10 | bayside | 24 | 6.85 | 11.12 | 0 | 0 |
| outage90 | warm10 | blocks | 24 | 7.82 | 11.06 | 0 | 0 |
| outage90 | warm10 | boulevard | 24 | 7.65 | 10.22 | 0 | 0 |
| outage90 | warm5 | bayside | 24 | 6.85 | 11.12 | 0 | 0 |
| outage90 | warm5 | blocks | 24 | 7.82 | 11.06 | 0 | 0 |
| outage90 | warm5 | boulevard | 24 | 7.65 | 10.22 | 0 | 0 |
| quiet45 | a0.3 | bayside | 24 | 7.27 | 7.69 | 0 | 0 |
| quiet45 | a0.3 | blocks | 24 | 7.44 | 8.92 | 0 | 0 |
| quiet45 | a0.3 | boulevard | 24 | 7.44 | 7.85 | 0 | 0 |
| quiet45 | restart+warm10 | bayside | 24 | 6.67 | 7.0 | 0 | 0 |
| quiet45 | restart+warm10 | blocks | 24 | 6.9 | 7.58 | 0 | 0 |
| quiet45 | restart+warm10 | boulevard | 24 | 6.91 | 7.62 | 0 | 0 |
| quiet45 | restart+warm5 | bayside | 24 | 6.67 | 7.0 | 0 | 0 |
| quiet45 | restart+warm5 | blocks | 24 | 6.9 | 7.58 | 0 | 0 |
| quiet45 | restart+warm5 | boulevard | 24 | 6.91 | 7.62 | 0 | 0 |
| quiet45 | warm10 | bayside | 24 | 6.67 | 7.58 | 0 | 0 |
| quiet45 | warm10 | blocks | 24 | 6.98 | 8.67 | 0 | 0 |
| quiet45 | warm10 | boulevard | 24 | 6.91 | 7.84 | 0 | 0 |
| quiet45 | warm5 | bayside | 24 | 6.67 | 7.58 | 0 | 0 |
| quiet45 | warm5 | blocks | 24 | 6.98 | 8.67 | 0 | 0 |
| quiet45 | warm5 | boulevard | 24 | 6.91 | 7.84 | 0 | 0 |
| quiet90 | a0.3 | bayside | 24 | 7.27 | 7.62 | 0 | 0 |
| quiet90 | a0.3 | blocks | 24 | 7.46 | 9.61 | 0 | 0 |
| quiet90 | a0.3 | boulevard | 24 | 7.44 | 7.85 | 0 | 0 |
| quiet90 | restart+warm10 | bayside | 24 | 6.67 | 7.0 | 0 | 0 |
| quiet90 | restart+warm10 | blocks | 24 | 6.9 | 7.58 | 0 | 0 |
| quiet90 | restart+warm10 | boulevard | 24 | 6.91 | 7.62 | 0 | 0 |
| quiet90 | restart+warm5 | bayside | 24 | 6.67 | 7.0 | 0 | 0 |
| quiet90 | restart+warm5 | blocks | 24 | 6.9 | 7.58 | 0 | 0 |
| quiet90 | restart+warm5 | boulevard | 24 | 6.91 | 7.62 | 0 | 0 |
| quiet90 | warm10 | bayside | 24 | 6.69 | 7.58 | 0 | 0 |
| quiet90 | warm10 | blocks | 24 | 7.05 | 9.15 | 0 | 0 |
| quiet90 | warm10 | boulevard | 24 | 6.91 | 7.84 | 0 | 0 |
| quiet90 | warm5 | bayside | 24 | 6.69 | 7.58 | 0 | 0 |
| quiet90 | warm5 | blocks | 24 | 7.05 | 9.15 | 0 | 0 |
| quiet90 | warm5 | boulevard | 24 | 6.91 | 7.84 | 0 | 0 |
| quietdrift90 | a0.3 | bayside | 24 | 11.91 | 25.38 | 0 | 0 |
| quietdrift90 | a0.3 | blocks | 24 | 10.43 | 22.22 | 0 | 0 |
| quietdrift90 | a0.3 | boulevard | 24 | 12.88 | 25.13 | 0 | 0 |
| quietdrift90 | restart+warm10 | bayside | 24 | 11.98 | 24.78 | 0 | 0 |
| quietdrift90 | restart+warm10 | blocks | 24 | 9.97 | 22.56 | 0 | 0 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 12.25 | 25.08 | 0 | 0 |
| quietdrift90 | restart+warm5 | bayside | 24 | 11.98 | 24.78 | 0 | 0 |
| quietdrift90 | restart+warm5 | blocks | 24 | 9.97 | 22.56 | 0 | 0 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 12.25 | 25.08 | 0 | 0 |
| quietdrift90 | warm10 | bayside | 24 | 12.93 | 24.99 | 0 | 0 |
| quietdrift90 | warm10 | blocks | 24 | 10.27 | 22.5 | 0 | 0 |
| quietdrift90 | warm10 | boulevard | 24 | 12.37 | 24.92 | 0 | 0 |
| quietdrift90 | warm5 | bayside | 24 | 12.93 | 24.99 | 0 | 0 |
| quietdrift90 | warm5 | blocks | 24 | 10.27 | 22.5 | 0 | 0 |
| quietdrift90 | warm5 | boulevard | 24 | 12.37 | 24.92 | 0 | 0 |

## Where the rover strays (true distance from the course by context; far: over 8 m)

| profile | variant | course | context | missions | samples | far | far share | median m | p95 m | max m |
|---|---|---|---|---|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | checkpoint | 24 | 6339 | 0 | None | 0.18 | 0.73 | 1.12 |
| blocked30 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | a0.3 | bayside | other | 24 | 26897 | 0 | None | 0.21 | 2.38 | 6.54 |
| blocked30 | a0.3 | bayside | outage | 19 | 3357 | 0 | None | 0.43 | 1.05 | 1.26 |
| blocked30 | a0.3 | bayside | fix | 24 | 29879 | 0 | None | 0.19 | 2.17 | 6.54 |
| blocked30 | a0.3 | blocks | checkpoint | 24 | 8249 | 10 | 0.714 | 0.34 | 2.59 | 3.41 |
| blocked30 | a0.3 | blocks | corner | 24 | 8770 | 4 | 0.286 | 1.06 | 3.25 | 5.06 |
| blocked30 | a0.3 | blocks | other | 24 | 19170 | 0 | 0.0 | 0.21 | 2.42 | 6.81 |
| blocked30 | a0.3 | blocks | outage | 19 | 3770 | 0 | 0.0 | 0.51 | 3.42 | 4.82 |
| blocked30 | a0.3 | blocks | fix | 24 | 32419 | 14 | 1.0 | 0.27 | 2.73 | 6.89 |
| blocked30 | a0.3 | boulevard | checkpoint | 24 | 6289 | 0 | None | 0.19 | 0.62 | 0.89 |
| blocked30 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | a0.3 | boulevard | other | 24 | 34005 | 0 | None | 0.13 | 0.73 | 6.82 |
| blocked30 | a0.3 | boulevard | outage | 21 | 4420 | 0 | None | 0.33 | 0.83 | 0.87 |
| blocked30 | a0.3 | boulevard | fix | 24 | 35874 | 0 | None | 0.13 | 0.68 | 6.82 |
| blocked30 | restart+warm10 | bayside | checkpoint | 24 | 6310 | 0 | None | 0.17 | 0.58 | 1.0 |
| blocked30 | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | restart+warm10 | bayside | other | 24 | 26863 | 0 | None | 0.19 | 1.07 | 6.42 |
| blocked30 | restart+warm10 | bayside | outage | 19 | 3416 | 0 | None | 0.49 | 1.33 | 1.71 |
| blocked30 | restart+warm10 | bayside | fix | 24 | 29757 | 0 | None | 0.18 | 0.72 | 6.42 |
| blocked30 | restart+warm10 | blocks | checkpoint | 24 | 8144 | 0 | None | 0.32 | 2.08 | 2.56 |
| blocked30 | restart+warm10 | blocks | corner | 24 | 8608 | 0 | None | 0.95 | 2.66 | 4.54 |
| blocked30 | restart+warm10 | blocks | other | 24 | 19084 | 0 | None | 0.19 | 1.98 | 6.84 |
| blocked30 | restart+warm10 | blocks | outage | 19 | 3740 | 0 | None | 0.49 | 3.32 | 4.78 |
| blocked30 | restart+warm10 | blocks | fix | 24 | 32096 | 0 | None | 0.24 | 2.32 | 6.84 |
| blocked30 | restart+warm10 | boulevard | checkpoint | 24 | 6296 | 0 | None | 0.16 | 0.51 | 0.79 |
| blocked30 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | restart+warm10 | boulevard | other | 24 | 34043 | 0 | None | 0.13 | 0.66 | 6.81 |
| blocked30 | restart+warm10 | boulevard | outage | 21 | 4420 | 0 | None | 0.35 | 0.75 | 0.86 |
| blocked30 | restart+warm10 | boulevard | fix | 24 | 35919 | 0 | None | 0.13 | 0.55 | 6.81 |
| blocked30 | restart+warm5 | bayside | checkpoint | 24 | 6322 | 0 | None | 0.18 | 0.54 | 0.98 |
| blocked30 | restart+warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | restart+warm5 | bayside | other | 24 | 26928 | 0 | None | 0.2 | 1.25 | 6.74 |
| blocked30 | restart+warm5 | bayside | outage | 19 | 3398 | 0 | None | 0.46 | 1.19 | 1.72 |
| blocked30 | restart+warm5 | bayside | fix | 24 | 29852 | 0 | None | 0.18 | 0.85 | 6.74 |
| blocked30 | restart+warm5 | blocks | checkpoint | 24 | 8151 | 0 | None | 0.3 | 2.07 | 2.56 |
| blocked30 | restart+warm5 | blocks | corner | 24 | 8627 | 0 | None | 0.91 | 2.79 | 4.68 |
| blocked30 | restart+warm5 | blocks | other | 24 | 19081 | 0 | None | 0.2 | 1.94 | 6.94 |
| blocked30 | restart+warm5 | blocks | outage | 19 | 3684 | 0 | None | 0.58 | 3.37 | 4.7 |
| blocked30 | restart+warm5 | blocks | fix | 24 | 32175 | 0 | None | 0.23 | 2.25 | 6.94 |
| blocked30 | restart+warm5 | boulevard | checkpoint | 24 | 6291 | 0 | None | 0.15 | 0.49 | 0.8 |
| blocked30 | restart+warm5 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | restart+warm5 | boulevard | other | 24 | 34081 | 0 | None | 0.13 | 0.84 | 6.99 |
| blocked30 | restart+warm5 | boulevard | outage | 21 | 4376 | 0 | None | 0.28 | 0.79 | 0.92 |
| blocked30 | restart+warm5 | boulevard | fix | 24 | 35996 | 0 | None | 0.13 | 0.56 | 6.99 |
| blocked30 | warm10 | bayside | checkpoint | 24 | 6336 | 0 | None | 0.18 | 0.71 | 1.09 |
| blocked30 | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | warm10 | bayside | other | 24 | 26937 | 0 | None | 0.21 | 2.3 | 6.44 |
| blocked30 | warm10 | bayside | outage | 19 | 3356 | 0 | None | 0.49 | 1.12 | 1.54 |
| blocked30 | warm10 | bayside | fix | 24 | 29917 | 0 | None | 0.18 | 2.21 | 6.44 |
| blocked30 | warm10 | blocks | checkpoint | 24 | 8239 | 15 | 1.0 | 0.36 | 2.61 | 3.54 |
| blocked30 | warm10 | blocks | corner | 24 | 8775 | 0 | 0.0 | 1.0 | 3.26 | 5.07 |
| blocked30 | warm10 | blocks | other | 24 | 19209 | 0 | 0.0 | 0.21 | 2.49 | 6.84 |
| blocked30 | warm10 | blocks | outage | 19 | 3766 | 0 | 0.0 | 0.5 | 3.29 | 4.81 |
| blocked30 | warm10 | blocks | fix | 24 | 32457 | 15 | 1.0 | 0.27 | 2.94 | 6.91 |
| blocked30 | warm10 | boulevard | checkpoint | 24 | 6299 | 0 | None | 0.19 | 0.61 | 0.88 |
| blocked30 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | warm10 | boulevard | other | 24 | 34047 | 0 | None | 0.13 | 0.73 | 6.81 |
| blocked30 | warm10 | boulevard | outage | 21 | 4422 | 0 | None | 0.38 | 0.81 | 0.87 |
| blocked30 | warm10 | boulevard | fix | 24 | 35924 | 0 | None | 0.14 | 0.65 | 6.81 |
| blocked30 | warm5 | bayside | checkpoint | 24 | 6330 | 0 | None | 0.2 | 0.81 | 1.11 |
| blocked30 | warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | warm5 | bayside | other | 24 | 27018 | 0 | None | 0.2 | 2.58 | 6.74 |
| blocked30 | warm5 | bayside | outage | 19 | 3422 | 0 | None | 0.51 | 1.08 | 1.69 |
| blocked30 | warm5 | bayside | fix | 24 | 29926 | 0 | None | 0.18 | 2.17 | 6.74 |
| blocked30 | warm5 | blocks | checkpoint | 24 | 8235 | 0 | 0.0 | 0.34 | 2.52 | 3.42 |
| blocked30 | warm5 | blocks | corner | 24 | 8791 | 7 | 1.0 | 0.98 | 3.14 | 4.94 |
| blocked30 | warm5 | blocks | other | 24 | 19247 | 0 | 0.0 | 0.21 | 2.87 | 6.94 |
| blocked30 | warm5 | blocks | outage | 19 | 3803 | 0 | 0.0 | 0.52 | 3.16 | 4.85 |
| blocked30 | warm5 | blocks | fix | 24 | 32470 | 7 | 1.0 | 0.27 | 2.74 | 7.04 |
| blocked30 | warm5 | boulevard | checkpoint | 24 | 6297 | 0 | None | 0.17 | 0.63 | 0.91 |
| blocked30 | warm5 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| blocked30 | warm5 | boulevard | other | 24 | 34082 | 0 | None | 0.14 | 0.85 | 6.99 |
| blocked30 | warm5 | boulevard | outage | 21 | 4378 | 0 | None | 0.35 | 0.77 | 0.92 |
| blocked30 | warm5 | boulevard | fix | 24 | 36001 | 0 | None | 0.14 | 0.78 | 6.99 |
| outage90 | a0.3 | bayside | checkpoint | 24 | 6340 | 0 | 0.0 | 0.49 | 1.94 | 2.58 |
| outage90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | bayside | other | 24 | 26588 | 89 | 1.0 | 0.62 | 4.22 | 7.08 |
| outage90 | a0.3 | bayside | outage | 19 | 3589 | 0 | 0.0 | 1.28 | 3.93 | 4.48 |
| outage90 | a0.3 | bayside | fix | 24 | 29339 | 89 | 1.0 | 0.54 | 3.2 | 7.08 |
| outage90 | a0.3 | blocks | checkpoint | 24 | 8324 | 72 | 0.333 | 0.79 | 3.11 | 3.66 |
| outage90 | a0.3 | blocks | corner | 24 | 8745 | 39 | 0.181 | 1.2 | 3.36 | 5.4 |
| outage90 | a0.3 | blocks | other | 24 | 18793 | 105 | 0.486 | 0.64 | 4.36 | 7.51 |
| outage90 | a0.3 | blocks | outage | 19 | 3696 | 9 | 0.042 | 1.72 | 4.06 | 5.56 |
| outage90 | a0.3 | blocks | fix | 24 | 32166 | 207 | 0.958 | 0.67 | 3.29 | 7.97 |
| outage90 | a0.3 | boulevard | checkpoint | 24 | 6310 | 36 | 0.193 | 0.51 | 1.58 | 1.84 |
| outage90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | a0.3 | boulevard | other | 24 | 33656 | 151 | 0.807 | 0.62 | 3.04 | 7.72 |
| outage90 | a0.3 | boulevard | outage | 20 | 4497 | 49 | 0.262 | 1.81 | 3.93 | 4.17 |
| outage90 | a0.3 | boulevard | fix | 24 | 35469 | 138 | 0.738 | 0.54 | 2.47 | 7.72 |
| outage90 | restart+warm10 | bayside | checkpoint | 24 | 6325 | 0 | None | 0.48 | 1.46 | 1.88 |
| outage90 | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| outage90 | restart+warm10 | bayside | other | 24 | 26455 | 0 | None | 0.54 | 3.09 | 6.91 |
| outage90 | restart+warm10 | bayside | outage | 19 | 3677 | 0 | None | 1.13 | 3.8 | 3.98 |
| outage90 | restart+warm10 | bayside | fix | 24 | 29103 | 0 | None | 0.52 | 2.04 | 6.91 |
| outage90 | restart+warm10 | blocks | checkpoint | 24 | 8224 | 0 | 0.0 | 0.72 | 2.51 | 3.45 |
| outage90 | restart+warm10 | blocks | corner | 24 | 8639 | 0 | 0.0 | 1.17 | 2.95 | 4.14 |
| outage90 | restart+warm10 | blocks | other | 24 | 18589 | 65 | 1.0 | 0.65 | 3.36 | 7.04 |
| outage90 | restart+warm10 | blocks | outage | 19 | 3732 | 0 | 0.0 | 1.53 | 3.83 | 5.28 |
| outage90 | restart+warm10 | blocks | fix | 24 | 31720 | 65 | 1.0 | 0.69 | 2.78 | 7.06 |
| outage90 | restart+warm10 | boulevard | checkpoint | 24 | 6308 | 23 | 0.178 | 0.54 | 1.46 | 1.84 |
| outage90 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart+warm10 | boulevard | other | 24 | 33604 | 106 | 0.822 | 0.56 | 2.9 | 7.56 |
| outage90 | restart+warm10 | boulevard | outage | 20 | 4476 | 37 | 0.287 | 1.43 | 3.96 | 4.47 |
| outage90 | restart+warm10 | boulevard | fix | 24 | 35436 | 92 | 0.713 | 0.51 | 2.13 | 7.56 |
| outage90 | restart+warm5 | bayside | checkpoint | 24 | 6325 | 0 | None | 0.48 | 1.46 | 1.88 |
| outage90 | restart+warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| outage90 | restart+warm5 | bayside | other | 24 | 26455 | 0 | None | 0.54 | 3.09 | 6.91 |
| outage90 | restart+warm5 | bayside | outage | 19 | 3677 | 0 | None | 1.13 | 3.8 | 3.98 |
| outage90 | restart+warm5 | bayside | fix | 24 | 29103 | 0 | None | 0.52 | 2.04 | 6.91 |
| outage90 | restart+warm5 | blocks | checkpoint | 24 | 8224 | 0 | 0.0 | 0.72 | 2.51 | 3.45 |
| outage90 | restart+warm5 | blocks | corner | 24 | 8639 | 0 | 0.0 | 1.17 | 2.95 | 4.14 |
| outage90 | restart+warm5 | blocks | other | 24 | 18589 | 65 | 1.0 | 0.65 | 3.36 | 7.04 |
| outage90 | restart+warm5 | blocks | outage | 19 | 3732 | 0 | 0.0 | 1.53 | 3.83 | 5.28 |
| outage90 | restart+warm5 | blocks | fix | 24 | 31720 | 65 | 1.0 | 0.69 | 2.78 | 7.06 |
| outage90 | restart+warm5 | boulevard | checkpoint | 24 | 6308 | 23 | 0.176 | 0.54 | 1.46 | 1.84 |
| outage90 | restart+warm5 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | restart+warm5 | boulevard | other | 24 | 33603 | 108 | 0.824 | 0.56 | 2.9 | 7.56 |
| outage90 | restart+warm5 | boulevard | outage | 20 | 4476 | 37 | 0.282 | 1.43 | 3.96 | 4.47 |
| outage90 | restart+warm5 | boulevard | fix | 24 | 35435 | 94 | 0.718 | 0.51 | 2.13 | 7.56 |
| outage90 | warm10 | bayside | checkpoint | 24 | 6335 | 0 | 0.0 | 0.5 | 2.08 | 2.97 |
| outage90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10 | bayside | other | 24 | 26546 | 59 | 1.0 | 0.58 | 3.88 | 6.85 |
| outage90 | warm10 | bayside | outage | 19 | 3691 | 0 | 0.0 | 1.36 | 3.96 | 4.06 |
| outage90 | warm10 | bayside | fix | 24 | 29190 | 59 | 1.0 | 0.53 | 3.17 | 6.85 |
| outage90 | warm10 | blocks | checkpoint | 24 | 8325 | 40 | 0.207 | 0.77 | 3.17 | 3.86 |
| outage90 | warm10 | blocks | corner | 24 | 8736 | 48 | 0.249 | 1.23 | 3.33 | 4.92 |
| outage90 | warm10 | blocks | other | 24 | 18745 | 105 | 0.544 | 0.66 | 4.23 | 7.19 |
| outage90 | warm10 | blocks | outage | 19 | 3800 | 11 | 0.057 | 1.54 | 3.87 | 5.28 |
| outage90 | warm10 | blocks | fix | 24 | 32006 | 182 | 0.943 | 0.69 | 3.27 | 7.82 |
| outage90 | warm10 | boulevard | checkpoint | 24 | 6312 | 36 | 0.226 | 0.52 | 1.52 | 1.84 |
| outage90 | warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm10 | boulevard | other | 24 | 33601 | 123 | 0.774 | 0.61 | 2.83 | 7.65 |
| outage90 | warm10 | boulevard | outage | 20 | 4478 | 45 | 0.283 | 1.54 | 3.97 | 4.56 |
| outage90 | warm10 | boulevard | fix | 24 | 35435 | 114 | 0.717 | 0.51 | 2.42 | 7.65 |
| outage90 | warm5 | bayside | checkpoint | 24 | 6335 | 0 | 0.0 | 0.5 | 2.08 | 2.97 |
| outage90 | warm5 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm5 | bayside | other | 24 | 26546 | 59 | 1.0 | 0.58 | 3.88 | 6.85 |
| outage90 | warm5 | bayside | outage | 19 | 3691 | 0 | 0.0 | 1.36 | 3.96 | 4.06 |
| outage90 | warm5 | bayside | fix | 24 | 29190 | 59 | 1.0 | 0.53 | 3.17 | 6.85 |
| outage90 | warm5 | blocks | checkpoint | 24 | 8325 | 40 | 0.207 | 0.77 | 3.17 | 3.86 |
| outage90 | warm5 | blocks | corner | 24 | 8736 | 48 | 0.249 | 1.23 | 3.33 | 4.92 |
| outage90 | warm5 | blocks | other | 24 | 18745 | 105 | 0.544 | 0.66 | 4.23 | 7.19 |
| outage90 | warm5 | blocks | outage | 19 | 3800 | 11 | 0.057 | 1.54 | 3.87 | 5.28 |
| outage90 | warm5 | blocks | fix | 24 | 32006 | 182 | 0.943 | 0.69 | 3.27 | 7.82 |
| outage90 | warm5 | boulevard | checkpoint | 24 | 6312 | 36 | 0.224 | 0.52 | 1.52 | 1.84 |
| outage90 | warm5 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| outage90 | warm5 | boulevard | other | 24 | 33600 | 125 | 0.776 | 0.61 | 2.86 | 7.65 |
| outage90 | warm5 | boulevard | outage | 20 | 4478 | 45 | 0.28 | 1.54 | 3.97 | 4.56 |
| outage90 | warm5 | boulevard | fix | 24 | 35434 | 116 | 0.72 | 0.51 | 2.54 | 7.65 |
| quiet45 | a0.3 | bayside | checkpoint | 24 | 6310 | 0 | None | 0.21 | 1.23 | 1.92 |
| quiet45 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3 | bayside | other | 24 | 26537 | 0 | None | 0.22 | 2.35 | 7.27 |
| quiet45 | a0.3 | bayside | outage | 24 | 3752 | 0 | None | 0.6 | 1.65 | 2.13 |
| quiet45 | a0.3 | bayside | fix | 24 | 29095 | 0 | None | 0.21 | 2.2 | 7.27 |
| quiet45 | a0.3 | blocks | checkpoint | 24 | 8250 | 8 | 1.0 | 0.39 | 2.38 | 3.18 |
| quiet45 | a0.3 | blocks | corner | 24 | 8774 | 0 | 0.0 | 0.96 | 3.1 | 4.83 |
| quiet45 | a0.3 | blocks | other | 24 | 18695 | 0 | 0.0 | 0.23 | 3.56 | 7.44 |
| quiet45 | a0.3 | blocks | outage | 24 | 4033 | 0 | 0.0 | 0.48 | 3.19 | 4.63 |
| quiet45 | a0.3 | blocks | fix | 24 | 31686 | 8 | 1.0 | 0.31 | 3.07 | 7.44 |
| quiet45 | a0.3 | boulevard | checkpoint | 24 | 6301 | 0 | None | 0.17 | 0.57 | 0.92 |
| quiet45 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | a0.3 | boulevard | other | 24 | 33633 | 0 | None | 0.15 | 0.83 | 7.44 |
| quiet45 | a0.3 | boulevard | outage | 24 | 5021 | 0 | None | 0.26 | 0.76 | 0.89 |
| quiet45 | a0.3 | boulevard | fix | 24 | 34913 | 0 | None | 0.14 | 1.02 | 7.44 |
| quiet45 | restart+warm10 | bayside | checkpoint | 24 | 6302 | 0 | None | 0.17 | 0.61 | 1.21 |
| quiet45 | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm10 | bayside | other | 24 | 26383 | 0 | None | 0.21 | 1.52 | 6.67 |
| quiet45 | restart+warm10 | bayside | outage | 24 | 3911 | 0 | None | 0.46 | 1.69 | 2.04 |
| quiet45 | restart+warm10 | bayside | fix | 24 | 28774 | 0 | None | 0.19 | 1.11 | 6.67 |
| quiet45 | restart+warm10 | blocks | checkpoint | 24 | 8176 | 0 | None | 0.33 | 2.08 | 2.6 |
| quiet45 | restart+warm10 | blocks | corner | 24 | 8588 | 0 | None | 0.86 | 2.56 | 4.66 |
| quiet45 | restart+warm10 | blocks | other | 24 | 18553 | 0 | None | 0.21 | 2.04 | 6.9 |
| quiet45 | restart+warm10 | blocks | outage | 24 | 4018 | 0 | None | 0.41 | 2.88 | 4.79 |
| quiet45 | restart+warm10 | blocks | fix | 24 | 31299 | 0 | None | 0.25 | 2.3 | 6.9 |
| quiet45 | restart+warm10 | boulevard | checkpoint | 24 | 6294 | 0 | None | 0.18 | 0.54 | 0.87 |
| quiet45 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm10 | boulevard | other | 24 | 33548 | 0 | None | 0.13 | 0.75 | 6.91 |
| quiet45 | restart+warm10 | boulevard | outage | 24 | 4963 | 0 | None | 0.21 | 0.78 | 0.94 |
| quiet45 | restart+warm10 | boulevard | fix | 24 | 34879 | 0 | None | 0.13 | 0.65 | 6.91 |
| quiet45 | restart+warm5 | bayside | checkpoint | 24 | 6302 | 0 | None | 0.17 | 0.61 | 1.21 |
| quiet45 | restart+warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm5 | bayside | other | 24 | 26383 | 0 | None | 0.21 | 1.52 | 6.67 |
| quiet45 | restart+warm5 | bayside | outage | 24 | 3911 | 0 | None | 0.46 | 1.69 | 2.04 |
| quiet45 | restart+warm5 | bayside | fix | 24 | 28774 | 0 | None | 0.19 | 1.11 | 6.67 |
| quiet45 | restart+warm5 | blocks | checkpoint | 24 | 8176 | 0 | None | 0.33 | 2.08 | 2.6 |
| quiet45 | restart+warm5 | blocks | corner | 24 | 8588 | 0 | None | 0.86 | 2.56 | 4.66 |
| quiet45 | restart+warm5 | blocks | other | 24 | 18553 | 0 | None | 0.21 | 2.04 | 6.9 |
| quiet45 | restart+warm5 | blocks | outage | 24 | 4018 | 0 | None | 0.41 | 2.88 | 4.79 |
| quiet45 | restart+warm5 | blocks | fix | 24 | 31299 | 0 | None | 0.25 | 2.3 | 6.9 |
| quiet45 | restart+warm5 | boulevard | checkpoint | 24 | 6294 | 0 | None | 0.18 | 0.54 | 0.87 |
| quiet45 | restart+warm5 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | restart+warm5 | boulevard | other | 24 | 33548 | 0 | None | 0.13 | 0.75 | 6.91 |
| quiet45 | restart+warm5 | boulevard | outage | 24 | 4963 | 0 | None | 0.21 | 0.78 | 0.94 |
| quiet45 | restart+warm5 | boulevard | fix | 24 | 34879 | 0 | None | 0.13 | 0.65 | 6.91 |
| quiet45 | warm10 | bayside | checkpoint | 24 | 6311 | 0 | None | 0.2 | 1.24 | 1.92 |
| quiet45 | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10 | bayside | other | 24 | 26455 | 0 | None | 0.21 | 2.14 | 6.67 |
| quiet45 | warm10 | bayside | outage | 24 | 3926 | 0 | None | 0.51 | 1.61 | 2.05 |
| quiet45 | warm10 | bayside | fix | 24 | 28840 | 0 | None | 0.2 | 2.05 | 6.67 |
| quiet45 | warm10 | blocks | checkpoint | 24 | 8259 | 7 | 1.0 | 0.39 | 2.38 | 3.08 |
| quiet45 | warm10 | blocks | corner | 24 | 8765 | 0 | 0.0 | 0.91 | 3.37 | 4.97 |
| quiet45 | warm10 | blocks | other | 24 | 18585 | 0 | 0.0 | 0.24 | 2.71 | 6.93 |
| quiet45 | warm10 | blocks | outage | 24 | 4027 | 0 | 0.0 | 0.47 | 3.1 | 4.71 |
| quiet45 | warm10 | blocks | fix | 24 | 31582 | 7 | 1.0 | 0.3 | 2.75 | 6.98 |
| quiet45 | warm10 | boulevard | checkpoint | 24 | 6301 | 0 | None | 0.2 | 0.56 | 0.86 |
| quiet45 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm10 | boulevard | other | 24 | 33543 | 0 | None | 0.14 | 0.88 | 6.91 |
| quiet45 | warm10 | boulevard | outage | 24 | 4965 | 0 | None | 0.24 | 0.84 | 0.95 |
| quiet45 | warm10 | boulevard | fix | 24 | 34879 | 0 | None | 0.15 | 0.77 | 6.91 |
| quiet45 | warm5 | bayside | checkpoint | 24 | 6311 | 0 | None | 0.2 | 1.24 | 1.92 |
| quiet45 | warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm5 | bayside | other | 24 | 26455 | 0 | None | 0.21 | 2.14 | 6.67 |
| quiet45 | warm5 | bayside | outage | 24 | 3926 | 0 | None | 0.51 | 1.61 | 2.05 |
| quiet45 | warm5 | bayside | fix | 24 | 28840 | 0 | None | 0.2 | 2.05 | 6.67 |
| quiet45 | warm5 | blocks | checkpoint | 24 | 8259 | 7 | 1.0 | 0.39 | 2.38 | 3.08 |
| quiet45 | warm5 | blocks | corner | 24 | 8765 | 0 | 0.0 | 0.91 | 3.37 | 4.97 |
| quiet45 | warm5 | blocks | other | 24 | 18585 | 0 | 0.0 | 0.24 | 2.71 | 6.93 |
| quiet45 | warm5 | blocks | outage | 24 | 4027 | 0 | 0.0 | 0.47 | 3.1 | 4.71 |
| quiet45 | warm5 | blocks | fix | 24 | 31582 | 7 | 1.0 | 0.3 | 2.75 | 6.98 |
| quiet45 | warm5 | boulevard | checkpoint | 24 | 6301 | 0 | None | 0.2 | 0.56 | 0.86 |
| quiet45 | warm5 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet45 | warm5 | boulevard | other | 24 | 33543 | 0 | None | 0.14 | 0.88 | 6.91 |
| quiet45 | warm5 | boulevard | outage | 24 | 4965 | 0 | None | 0.24 | 0.84 | 0.95 |
| quiet45 | warm5 | boulevard | fix | 24 | 34879 | 0 | None | 0.15 | 0.77 | 6.91 |
| quiet90 | a0.3 | bayside | checkpoint | 24 | 6322 | 0 | None | 0.18 | 0.67 | 1.14 |
| quiet90 | a0.3 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3 | bayside | other | 24 | 26567 | 0 | None | 0.21 | 3.52 | 7.27 |
| quiet90 | a0.3 | bayside | outage | 19 | 3586 | 0 | None | 0.55 | 1.3 | 1.65 |
| quiet90 | a0.3 | bayside | fix | 24 | 29303 | 0 | None | 0.19 | 3.16 | 7.27 |
| quiet90 | a0.3 | blocks | checkpoint | 24 | 8289 | 22 | 0.688 | 0.36 | 2.45 | 3.37 |
| quiet90 | a0.3 | blocks | corner | 24 | 8712 | 10 | 0.312 | 1.0 | 2.95 | 4.69 |
| quiet90 | a0.3 | blocks | other | 24 | 18794 | 0 | 0.0 | 0.23 | 3.73 | 7.42 |
| quiet90 | a0.3 | blocks | outage | 19 | 3681 | 0 | 0.0 | 0.55 | 3.36 | 4.68 |
| quiet90 | a0.3 | blocks | fix | 24 | 32114 | 32 | 1.0 | 0.27 | 3.07 | 7.46 |
| quiet90 | a0.3 | boulevard | checkpoint | 24 | 6295 | 0 | None | 0.17 | 0.55 | 0.99 |
| quiet90 | a0.3 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | a0.3 | boulevard | other | 24 | 33618 | 0 | None | 0.14 | 0.85 | 7.44 |
| quiet90 | a0.3 | boulevard | outage | 20 | 4479 | 0 | None | 0.32 | 0.79 | 0.91 |
| quiet90 | a0.3 | boulevard | fix | 24 | 35434 | 0 | None | 0.14 | 0.94 | 7.44 |
| quiet90 | restart+warm10 | bayside | checkpoint | 24 | 6299 | 0 | None | 0.16 | 0.52 | 0.87 |
| quiet90 | restart+warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm10 | bayside | other | 24 | 26397 | 0 | None | 0.2 | 1.25 | 6.67 |
| quiet90 | restart+warm10 | bayside | outage | 19 | 3727 | 0 | None | 0.57 | 1.37 | 1.72 |
| quiet90 | restart+warm10 | bayside | fix | 24 | 28969 | 0 | None | 0.18 | 0.68 | 6.67 |
| quiet90 | restart+warm10 | blocks | checkpoint | 24 | 8184 | 0 | None | 0.34 | 2.14 | 2.71 |
| quiet90 | restart+warm10 | blocks | corner | 24 | 8582 | 0 | None | 0.93 | 2.52 | 4.57 |
| quiet90 | restart+warm10 | blocks | other | 24 | 18555 | 0 | None | 0.21 | 2.04 | 6.9 |
| quiet90 | restart+warm10 | blocks | outage | 19 | 3937 | 0 | None | 0.59 | 3.29 | 4.73 |
| quiet90 | restart+warm10 | blocks | fix | 24 | 31384 | 0 | None | 0.25 | 2.33 | 6.9 |
| quiet90 | restart+warm10 | boulevard | checkpoint | 24 | 6296 | 0 | None | 0.15 | 0.54 | 0.84 |
| quiet90 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm10 | boulevard | other | 24 | 33529 | 0 | None | 0.14 | 0.67 | 6.91 |
| quiet90 | restart+warm10 | boulevard | outage | 20 | 4515 | 0 | None | 0.34 | 0.81 | 0.88 |
| quiet90 | restart+warm10 | boulevard | fix | 24 | 35310 | 0 | None | 0.13 | 0.57 | 6.91 |
| quiet90 | restart+warm5 | bayside | checkpoint | 24 | 6299 | 0 | None | 0.16 | 0.52 | 0.87 |
| quiet90 | restart+warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm5 | bayside | other | 24 | 26397 | 0 | None | 0.2 | 1.25 | 6.67 |
| quiet90 | restart+warm5 | bayside | outage | 19 | 3727 | 0 | None | 0.57 | 1.37 | 1.72 |
| quiet90 | restart+warm5 | bayside | fix | 24 | 28969 | 0 | None | 0.18 | 0.68 | 6.67 |
| quiet90 | restart+warm5 | blocks | checkpoint | 24 | 8184 | 0 | None | 0.34 | 2.14 | 2.71 |
| quiet90 | restart+warm5 | blocks | corner | 24 | 8582 | 0 | None | 0.93 | 2.52 | 4.57 |
| quiet90 | restart+warm5 | blocks | other | 24 | 18555 | 0 | None | 0.21 | 2.04 | 6.9 |
| quiet90 | restart+warm5 | blocks | outage | 19 | 3937 | 0 | None | 0.59 | 3.29 | 4.73 |
| quiet90 | restart+warm5 | blocks | fix | 24 | 31384 | 0 | None | 0.25 | 2.33 | 6.9 |
| quiet90 | restart+warm5 | boulevard | checkpoint | 24 | 6296 | 0 | None | 0.15 | 0.54 | 0.84 |
| quiet90 | restart+warm5 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | restart+warm5 | boulevard | other | 24 | 33529 | 0 | None | 0.14 | 0.67 | 6.91 |
| quiet90 | restart+warm5 | boulevard | outage | 20 | 4515 | 0 | None | 0.34 | 0.81 | 0.88 |
| quiet90 | restart+warm5 | boulevard | fix | 24 | 35310 | 0 | None | 0.13 | 0.57 | 6.91 |
| quiet90 | warm10 | bayside | checkpoint | 24 | 6315 | 0 | None | 0.17 | 0.69 | 1.13 |
| quiet90 | warm10 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10 | bayside | other | 24 | 26486 | 0 | None | 0.2 | 2.83 | 6.69 |
| quiet90 | warm10 | bayside | outage | 19 | 3607 | 0 | None | 0.47 | 1.25 | 1.61 |
| quiet90 | warm10 | bayside | fix | 24 | 29194 | 0 | None | 0.18 | 2.51 | 6.69 |
| quiet90 | warm10 | blocks | checkpoint | 24 | 8266 | 17 | 0.85 | 0.35 | 2.44 | 2.96 |
| quiet90 | warm10 | blocks | corner | 24 | 8698 | 3 | 0.15 | 0.98 | 2.88 | 4.71 |
| quiet90 | warm10 | blocks | other | 24 | 18702 | 0 | 0.0 | 0.22 | 2.89 | 6.93 |
| quiet90 | warm10 | blocks | outage | 19 | 3904 | 0 | 0.0 | 0.63 | 3.33 | 4.74 |
| quiet90 | warm10 | blocks | fix | 24 | 31762 | 20 | 1.0 | 0.28 | 2.69 | 7.05 |
| quiet90 | warm10 | boulevard | checkpoint | 24 | 6296 | 0 | None | 0.18 | 0.55 | 0.94 |
| quiet90 | warm10 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm10 | boulevard | other | 24 | 33534 | 0 | None | 0.14 | 0.7 | 6.91 |
| quiet90 | warm10 | boulevard | outage | 20 | 4516 | 0 | None | 0.34 | 0.82 | 0.89 |
| quiet90 | warm10 | boulevard | fix | 24 | 35314 | 0 | None | 0.13 | 0.7 | 6.91 |
| quiet90 | warm5 | bayside | checkpoint | 24 | 6315 | 0 | None | 0.17 | 0.69 | 1.13 |
| quiet90 | warm5 | bayside | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm5 | bayside | other | 24 | 26486 | 0 | None | 0.2 | 2.83 | 6.69 |
| quiet90 | warm5 | bayside | outage | 19 | 3607 | 0 | None | 0.47 | 1.25 | 1.61 |
| quiet90 | warm5 | bayside | fix | 24 | 29194 | 0 | None | 0.18 | 2.51 | 6.69 |
| quiet90 | warm5 | blocks | checkpoint | 24 | 8266 | 17 | 0.85 | 0.35 | 2.44 | 2.96 |
| quiet90 | warm5 | blocks | corner | 24 | 8698 | 3 | 0.15 | 0.98 | 2.88 | 4.71 |
| quiet90 | warm5 | blocks | other | 24 | 18702 | 0 | 0.0 | 0.22 | 2.89 | 6.93 |
| quiet90 | warm5 | blocks | outage | 19 | 3904 | 0 | 0.0 | 0.63 | 3.33 | 4.74 |
| quiet90 | warm5 | blocks | fix | 24 | 31762 | 20 | 1.0 | 0.28 | 2.69 | 7.05 |
| quiet90 | warm5 | boulevard | checkpoint | 24 | 6296 | 0 | None | 0.18 | 0.55 | 0.94 |
| quiet90 | warm5 | boulevard | corner | 0 | 0 | 0 | None | None | None | None |
| quiet90 | warm5 | boulevard | other | 24 | 33534 | 0 | None | 0.14 | 0.7 | 6.91 |
| quiet90 | warm5 | boulevard | outage | 20 | 4516 | 0 | None | 0.34 | 0.82 | 0.89 |
| quiet90 | warm5 | boulevard | fix | 24 | 35314 | 0 | None | 0.13 | 0.7 | 6.91 |
| quietdrift90 | a0.3 | bayside | checkpoint | 24 | 6403 | 106 | 0.077 | 1.25 | 4.42 | 5.33 |
| quietdrift90 | a0.3 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | bayside | other | 24 | 26740 | 1262 | 0.923 | 1.46 | 6.54 | 11.18 |
| quietdrift90 | a0.3 | bayside | outage | 19 | 3354 | 637 | 0.466 | 3.44 | 10.69 | 13.03 |
| quietdrift90 | a0.3 | bayside | fix | 24 | 29789 | 731 | 0.534 | 1.34 | 5.18 | 11.91 |
| quietdrift90 | a0.3 | blocks | checkpoint | 24 | 8357 | 143 | 0.132 | 1.67 | 4.51 | 5.37 |
| quietdrift90 | a0.3 | blocks | corner | 24 | 8636 | 105 | 0.097 | 1.6 | 4.63 | 6.58 |
| quietdrift90 | a0.3 | blocks | other | 24 | 19082 | 836 | 0.771 | 1.58 | 6.58 | 10.12 |
| quietdrift90 | a0.3 | blocks | outage | 19 | 3721 | 446 | 0.411 | 1.97 | 6.77 | 8.35 |
| quietdrift90 | a0.3 | blocks | fix | 24 | 32354 | 638 | 0.589 | 1.56 | 5.42 | 9.83 |
| quietdrift90 | a0.3 | boulevard | checkpoint | 24 | 6368 | 157 | 0.094 | 1.42 | 3.83 | 4.42 |
| quietdrift90 | a0.3 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | a0.3 | boulevard | other | 24 | 33845 | 1522 | 0.906 | 1.46 | 7.12 | 12.88 |
| quietdrift90 | a0.3 | boulevard | outage | 20 | 4440 | 786 | 0.468 | 2.62 | 11.38 | 14.03 |
| quietdrift90 | a0.3 | boulevard | fix | 24 | 35773 | 893 | 0.532 | 1.42 | 5.18 | 12.88 |
| quietdrift90 | restart+warm10 | bayside | checkpoint | 24 | 6362 | 62 | 0.047 | 1.24 | 3.9 | 4.85 |
| quietdrift90 | restart+warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm10 | bayside | other | 24 | 26626 | 1268 | 0.953 | 1.58 | 6.94 | 11.21 |
| quietdrift90 | restart+warm10 | bayside | outage | 19 | 3649 | 733 | 0.551 | 3.13 | 10.69 | 12.51 |
| quietdrift90 | restart+warm10 | bayside | fix | 24 | 29339 | 597 | 0.449 | 1.4 | 5.18 | 11.98 |
| quietdrift90 | restart+warm10 | blocks | checkpoint | 24 | 8249 | 95 | 0.116 | 1.69 | 3.77 | 4.7 |
| quietdrift90 | restart+warm10 | blocks | corner | 24 | 8498 | 86 | 0.105 | 1.49 | 4.44 | 6.99 |
| quietdrift90 | restart+warm10 | blocks | other | 24 | 18766 | 637 | 0.779 | 1.56 | 6.55 | 9.25 |
| quietdrift90 | restart+warm10 | blocks | outage | 19 | 3955 | 417 | 0.51 | 2.44 | 7.37 | 9.85 |
| quietdrift90 | restart+warm10 | blocks | fix | 24 | 31558 | 401 | 0.49 | 1.48 | 4.81 | 9.25 |
| quietdrift90 | restart+warm10 | boulevard | checkpoint | 24 | 6367 | 155 | 0.107 | 1.46 | 3.96 | 4.63 |
| quietdrift90 | restart+warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm10 | boulevard | other | 24 | 33780 | 1298 | 0.893 | 1.46 | 6.29 | 11.84 |
| quietdrift90 | restart+warm10 | boulevard | outage | 20 | 4590 | 837 | 0.576 | 2.56 | 11.56 | 14.76 |
| quietdrift90 | restart+warm10 | boulevard | fix | 24 | 35557 | 616 | 0.424 | 1.38 | 4.59 | 12.25 |
| quietdrift90 | restart+warm5 | bayside | checkpoint | 24 | 6362 | 62 | 0.047 | 1.24 | 3.9 | 4.85 |
| quietdrift90 | restart+warm5 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm5 | bayside | other | 24 | 26626 | 1268 | 0.953 | 1.58 | 6.94 | 11.21 |
| quietdrift90 | restart+warm5 | bayside | outage | 19 | 3649 | 733 | 0.551 | 3.13 | 10.69 | 12.51 |
| quietdrift90 | restart+warm5 | bayside | fix | 24 | 29339 | 597 | 0.449 | 1.4 | 5.18 | 11.98 |
| quietdrift90 | restart+warm5 | blocks | checkpoint | 24 | 8249 | 95 | 0.116 | 1.69 | 3.77 | 4.7 |
| quietdrift90 | restart+warm5 | blocks | corner | 24 | 8498 | 86 | 0.105 | 1.49 | 4.44 | 6.99 |
| quietdrift90 | restart+warm5 | blocks | other | 24 | 18766 | 637 | 0.779 | 1.56 | 6.55 | 9.25 |
| quietdrift90 | restart+warm5 | blocks | outage | 19 | 3955 | 417 | 0.51 | 2.44 | 7.37 | 9.85 |
| quietdrift90 | restart+warm5 | blocks | fix | 24 | 31558 | 401 | 0.49 | 1.48 | 4.81 | 9.25 |
| quietdrift90 | restart+warm5 | boulevard | checkpoint | 24 | 6367 | 155 | 0.107 | 1.46 | 3.96 | 4.63 |
| quietdrift90 | restart+warm5 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | restart+warm5 | boulevard | other | 24 | 33780 | 1298 | 0.893 | 1.46 | 6.29 | 11.84 |
| quietdrift90 | restart+warm5 | boulevard | outage | 20 | 4590 | 837 | 0.576 | 2.56 | 11.56 | 14.76 |
| quietdrift90 | restart+warm5 | boulevard | fix | 24 | 35557 | 616 | 0.424 | 1.38 | 4.59 | 12.25 |
| quietdrift90 | warm10 | bayside | checkpoint | 24 | 6371 | 80 | 0.052 | 1.23 | 4.23 | 4.93 |
| quietdrift90 | warm10 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10 | bayside | other | 24 | 26714 | 1453 | 0.948 | 1.54 | 7.08 | 12.0 |
| quietdrift90 | warm10 | bayside | outage | 19 | 3602 | 766 | 0.5 | 3.3 | 10.68 | 12.59 |
| quietdrift90 | warm10 | bayside | fix | 24 | 29483 | 767 | 0.5 | 1.4 | 5.71 | 12.93 |
| quietdrift90 | warm10 | blocks | checkpoint | 24 | 8329 | 121 | 0.122 | 1.57 | 4.15 | 4.88 |
| quietdrift90 | warm10 | blocks | corner | 24 | 8632 | 144 | 0.145 | 1.49 | 4.59 | 7.61 |
| quietdrift90 | warm10 | blocks | other | 24 | 19010 | 726 | 0.733 | 1.6 | 6.38 | 9.66 |
| quietdrift90 | warm10 | blocks | outage | 19 | 3867 | 436 | 0.44 | 2.17 | 8.3 | 9.81 |
| quietdrift90 | warm10 | blocks | fix | 24 | 32104 | 555 | 0.56 | 1.51 | 5.17 | 10.27 |
| quietdrift90 | warm10 | boulevard | checkpoint | 24 | 6386 | 244 | 0.133 | 1.46 | 3.99 | 4.62 |
| quietdrift90 | warm10 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm10 | boulevard | other | 24 | 33746 | 1584 | 0.867 | 1.52 | 6.98 | 11.88 |
| quietdrift90 | warm10 | boulevard | outage | 20 | 4585 | 858 | 0.469 | 2.79 | 11.92 | 14.77 |
| quietdrift90 | warm10 | boulevard | fix | 24 | 35547 | 970 | 0.531 | 1.45 | 4.98 | 12.37 |
| quietdrift90 | warm5 | bayside | checkpoint | 24 | 6371 | 80 | 0.052 | 1.23 | 4.23 | 4.93 |
| quietdrift90 | warm5 | bayside | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm5 | bayside | other | 24 | 26714 | 1453 | 0.948 | 1.54 | 7.08 | 12.0 |
| quietdrift90 | warm5 | bayside | outage | 19 | 3602 | 766 | 0.5 | 3.3 | 10.68 | 12.59 |
| quietdrift90 | warm5 | bayside | fix | 24 | 29483 | 767 | 0.5 | 1.4 | 5.71 | 12.93 |
| quietdrift90 | warm5 | blocks | checkpoint | 24 | 8329 | 121 | 0.122 | 1.57 | 4.15 | 4.88 |
| quietdrift90 | warm5 | blocks | corner | 24 | 8632 | 144 | 0.145 | 1.49 | 4.59 | 7.61 |
| quietdrift90 | warm5 | blocks | other | 24 | 19010 | 726 | 0.733 | 1.6 | 6.38 | 9.66 |
| quietdrift90 | warm5 | blocks | outage | 19 | 3867 | 436 | 0.44 | 2.17 | 8.3 | 9.81 |
| quietdrift90 | warm5 | blocks | fix | 24 | 32104 | 555 | 0.56 | 1.51 | 5.17 | 10.27 |
| quietdrift90 | warm5 | boulevard | checkpoint | 24 | 6386 | 244 | 0.133 | 1.46 | 3.99 | 4.62 |
| quietdrift90 | warm5 | boulevard | corner | 0 | 0 | 0 | 0.0 | None | None | None |
| quietdrift90 | warm5 | boulevard | other | 24 | 33746 | 1584 | 0.867 | 1.52 | 6.98 | 11.88 |
| quietdrift90 | warm5 | boulevard | outage | 20 | 4585 | 858 | 0.469 | 2.79 | 11.92 | 14.77 |
| quietdrift90 | warm5 | boulevard | fix | 24 | 35547 | 970 | 0.531 | 1.45 | 4.98 | 12.37 |

## Heading error

| profile | variant | course | missions | median abs deg | rms deg |
|---|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 1.01 | 4.8 |
| blocked30 | a0.3 | blocks | 24 | 1.04 | 4.63 |
| blocked30 | a0.3 | boulevard | 24 | 0.97 | 4.33 |
| blocked30 | restart+warm10 | bayside | 24 | 1.0 | 4.79 |
| blocked30 | restart+warm10 | blocks | 24 | 1.03 | 4.64 |
| blocked30 | restart+warm10 | boulevard | 24 | 0.97 | 4.34 |
| blocked30 | restart+warm5 | bayside | 24 | 1.02 | 5.21 |
| blocked30 | restart+warm5 | blocks | 24 | 1.03 | 5.03 |
| blocked30 | restart+warm5 | boulevard | 24 | 0.97 | 4.71 |
| blocked30 | warm10 | bayside | 24 | 1.0 | 4.81 |
| blocked30 | warm10 | blocks | 24 | 1.03 | 4.66 |
| blocked30 | warm10 | boulevard | 24 | 0.98 | 4.34 |
| blocked30 | warm5 | bayside | 24 | 1.02 | 5.21 |
| blocked30 | warm5 | blocks | 24 | 1.04 | 5.03 |
| blocked30 | warm5 | boulevard | 24 | 0.97 | 4.71 |
| outage90 | a0.3 | bayside | 24 | 1.67 | 4.42 |
| outage90 | a0.3 | blocks | 24 | 1.54 | 4.33 |
| outage90 | a0.3 | boulevard | 24 | 1.66 | 4.18 |
| outage90 | restart+warm10 | bayside | 24 | 1.65 | 4.21 |
| outage90 | restart+warm10 | blocks | 24 | 1.6 | 4.19 |
| outage90 | restart+warm10 | boulevard | 24 | 1.65 | 4.0 |
| outage90 | restart+warm5 | bayside | 24 | 1.65 | 4.21 |
| outage90 | restart+warm5 | blocks | 24 | 1.6 | 4.19 |
| outage90 | restart+warm5 | boulevard | 24 | 1.65 | 4.0 |
| outage90 | warm10 | bayside | 24 | 1.67 | 4.29 |
| outage90 | warm10 | blocks | 24 | 1.54 | 4.08 |
| outage90 | warm10 | boulevard | 24 | 1.69 | 4.04 |
| outage90 | warm5 | bayside | 24 | 1.67 | 4.29 |
| outage90 | warm5 | blocks | 24 | 1.54 | 4.08 |
| outage90 | warm5 | boulevard | 24 | 1.69 | 4.04 |
| quiet45 | a0.3 | bayside | 24 | 0.99 | 4.29 |
| quiet45 | a0.3 | blocks | 24 | 1.02 | 4.14 |
| quiet45 | a0.3 | boulevard | 24 | 0.96 | 3.88 |
| quiet45 | restart+warm10 | bayside | 24 | 1.01 | 3.81 |
| quiet45 | restart+warm10 | blocks | 24 | 1.01 | 3.71 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.96 | 3.47 |
| quiet45 | restart+warm5 | bayside | 24 | 1.01 | 3.81 |
| quiet45 | restart+warm5 | blocks | 24 | 1.01 | 3.71 |
| quiet45 | restart+warm5 | boulevard | 24 | 0.96 | 3.47 |
| quiet45 | warm10 | bayside | 24 | 0.99 | 3.79 |
| quiet45 | warm10 | blocks | 24 | 1.02 | 3.71 |
| quiet45 | warm10 | boulevard | 24 | 0.96 | 3.47 |
| quiet45 | warm5 | bayside | 24 | 0.99 | 3.79 |
| quiet45 | warm5 | blocks | 24 | 1.02 | 3.71 |
| quiet45 | warm5 | boulevard | 24 | 0.96 | 3.47 |
| quiet90 | a0.3 | bayside | 24 | 0.99 | 4.28 |
| quiet90 | a0.3 | blocks | 24 | 1.02 | 4.15 |
| quiet90 | a0.3 | boulevard | 24 | 0.96 | 3.87 |
| quiet90 | restart+warm10 | bayside | 24 | 0.99 | 3.78 |
| quiet90 | restart+warm10 | blocks | 24 | 1.01 | 3.71 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.96 | 3.47 |
| quiet90 | restart+warm5 | bayside | 24 | 0.99 | 3.78 |
| quiet90 | restart+warm5 | blocks | 24 | 1.01 | 3.71 |
| quiet90 | restart+warm5 | boulevard | 24 | 0.96 | 3.47 |
| quiet90 | warm10 | bayside | 24 | 1.0 | 3.8 |
| quiet90 | warm10 | blocks | 24 | 1.01 | 3.71 |
| quiet90 | warm10 | boulevard | 24 | 0.96 | 3.47 |
| quiet90 | warm5 | bayside | 24 | 1.0 | 3.8 |
| quiet90 | warm5 | blocks | 24 | 1.01 | 3.71 |
| quiet90 | warm5 | boulevard | 24 | 0.96 | 3.47 |
| quietdrift90 | a0.3 | bayside | 24 | 5.26 | 8.75 |
| quietdrift90 | a0.3 | blocks | 24 | 5.25 | 9.29 |
| quietdrift90 | a0.3 | boulevard | 24 | 5.05 | 8.56 |
| quietdrift90 | restart+warm10 | bayside | 24 | 5.36 | 8.93 |
| quietdrift90 | restart+warm10 | blocks | 24 | 5.26 | 8.57 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 5.14 | 8.22 |
| quietdrift90 | restart+warm5 | bayside | 24 | 5.36 | 8.93 |
| quietdrift90 | restart+warm5 | blocks | 24 | 5.26 | 8.57 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 5.14 | 8.22 |
| quietdrift90 | warm10 | bayside | 24 | 5.36 | 9.04 |
| quietdrift90 | warm10 | blocks | 24 | 5.27 | 8.55 |
| quietdrift90 | warm10 | boulevard | 24 | 5.17 | 8.32 |
| quietdrift90 | warm5 | bayside | 24 | 5.36 | 9.04 |
| quietdrift90 | warm5 | blocks | 24 | 5.27 | 8.55 |
| quietdrift90 | warm5 | boulevard | 24 | 5.17 | 8.32 |

## How hard the pilot steers

| profile | variant | course | missions | mean abs angular |
|---|---|---|---|---|
| blocked30 | a0.3 | bayside | 24 | 0.0254 |
| blocked30 | a0.3 | blocks | 24 | 0.0369 |
| blocked30 | a0.3 | boulevard | 24 | 0.0206 |
| blocked30 | restart+warm10 | bayside | 24 | 0.0229 |
| blocked30 | restart+warm10 | blocks | 24 | 0.0338 |
| blocked30 | restart+warm10 | boulevard | 24 | 0.02 |
| blocked30 | restart+warm5 | bayside | 24 | 0.0232 |
| blocked30 | restart+warm5 | blocks | 24 | 0.034 |
| blocked30 | restart+warm5 | boulevard | 24 | 0.0205 |
| blocked30 | warm10 | bayside | 24 | 0.0249 |
| blocked30 | warm10 | blocks | 24 | 0.0363 |
| blocked30 | warm10 | boulevard | 24 | 0.02 |
| blocked30 | warm5 | bayside | 24 | 0.0251 |
| blocked30 | warm5 | blocks | 24 | 0.0368 |
| blocked30 | warm5 | boulevard | 24 | 0.0205 |
| outage90 | a0.3 | bayside | 24 | 0.0317 |
| outage90 | a0.3 | blocks | 24 | 0.0414 |
| outage90 | a0.3 | boulevard | 24 | 0.0269 |
| outage90 | restart+warm10 | bayside | 24 | 0.029 |
| outage90 | restart+warm10 | blocks | 24 | 0.0393 |
| outage90 | restart+warm10 | boulevard | 24 | 0.0268 |
| outage90 | restart+warm5 | bayside | 24 | 0.029 |
| outage90 | restart+warm5 | blocks | 24 | 0.0393 |
| outage90 | restart+warm5 | boulevard | 24 | 0.0269 |
| outage90 | warm10 | bayside | 24 | 0.0311 |
| outage90 | warm10 | blocks | 24 | 0.0413 |
| outage90 | warm10 | boulevard | 24 | 0.0267 |
| outage90 | warm5 | bayside | 24 | 0.0311 |
| outage90 | warm5 | blocks | 24 | 0.0413 |
| outage90 | warm5 | boulevard | 24 | 0.0268 |
| quiet45 | a0.3 | bayside | 24 | 0.0254 |
| quiet45 | a0.3 | blocks | 24 | 0.0358 |
| quiet45 | a0.3 | boulevard | 24 | 0.02 |
| quiet45 | restart+warm10 | bayside | 24 | 0.0224 |
| quiet45 | restart+warm10 | blocks | 24 | 0.0336 |
| quiet45 | restart+warm10 | boulevard | 24 | 0.0196 |
| quiet45 | restart+warm5 | bayside | 24 | 0.0224 |
| quiet45 | restart+warm5 | blocks | 24 | 0.0336 |
| quiet45 | restart+warm5 | boulevard | 24 | 0.0196 |
| quiet45 | warm10 | bayside | 24 | 0.0248 |
| quiet45 | warm10 | blocks | 24 | 0.0357 |
| quiet45 | warm10 | boulevard | 24 | 0.0195 |
| quiet45 | warm5 | bayside | 24 | 0.0248 |
| quiet45 | warm5 | blocks | 24 | 0.0357 |
| quiet45 | warm5 | boulevard | 24 | 0.0195 |
| quiet90 | a0.3 | bayside | 24 | 0.0254 |
| quiet90 | a0.3 | blocks | 24 | 0.0362 |
| quiet90 | a0.3 | boulevard | 24 | 0.02 |
| quiet90 | restart+warm10 | bayside | 24 | 0.0222 |
| quiet90 | restart+warm10 | blocks | 24 | 0.0334 |
| quiet90 | restart+warm10 | boulevard | 24 | 0.0195 |
| quiet90 | restart+warm5 | bayside | 24 | 0.0222 |
| quiet90 | restart+warm5 | blocks | 24 | 0.0334 |
| quiet90 | restart+warm5 | boulevard | 24 | 0.0195 |
| quiet90 | warm10 | bayside | 24 | 0.0247 |
| quiet90 | warm10 | blocks | 24 | 0.0363 |
| quiet90 | warm10 | boulevard | 24 | 0.0195 |
| quiet90 | warm5 | bayside | 24 | 0.0247 |
| quiet90 | warm5 | blocks | 24 | 0.0363 |
| quiet90 | warm5 | boulevard | 24 | 0.0195 |
| quietdrift90 | a0.3 | bayside | 24 | 0.0299 |
| quietdrift90 | a0.3 | blocks | 24 | 0.0404 |
| quietdrift90 | a0.3 | boulevard | 24 | 0.0255 |
| quietdrift90 | restart+warm10 | bayside | 24 | 0.0272 |
| quietdrift90 | restart+warm10 | blocks | 24 | 0.0378 |
| quietdrift90 | restart+warm10 | boulevard | 24 | 0.0251 |
| quietdrift90 | restart+warm5 | bayside | 24 | 0.0272 |
| quietdrift90 | restart+warm5 | blocks | 24 | 0.0378 |
| quietdrift90 | restart+warm5 | boulevard | 24 | 0.0251 |
| quietdrift90 | warm10 | bayside | 24 | 0.0293 |
| quietdrift90 | warm10 | blocks | 24 | 0.0401 |
| quietdrift90 | warm10 | boulevard | 24 | 0.025 |
| quietdrift90 | warm5 | bayside | 24 | 0.0293 |
| quietdrift90 | warm5 | blocks | 24 | 0.0401 |
| quietdrift90 | warm5 | boulevard | 24 | 0.025 |
