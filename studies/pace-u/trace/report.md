# Why was seed 388's blocked rover caught 12 s late with a warm-up? (simulated)

trace_u.py 0.1.0 (pace_u.py 0.1.0, rover_pilot.py 0.18.6), MV2 of Munim, Inc. A diagnostic, not a pre-registered study: pace_u.py's boulevard missions flown again, logging every call of the stuck check up to 60 s (calls-<profile>-<variant>-<seed>.csv). A clear is a call whose history was cleared since the call before; held means a full window with no verdict.

## blocked30, a0.3, seed 388

481 calls up to 60 s; 1801.6 s; recovery moves at [9.1, 24.2]; first outage at 664.5 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 15.2 s, 6.1 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s
- at 30.2 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 39.2-59.9 s: 208 calls, 0 too slow, least moved 2.56 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 1 | 0.0 | 0.0 | 0.0 | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 11 | 1.0 | 0.0 | 0.0 | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 21 | 2.0 | 0.0 | 0.057 | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 31 | 3.0 | 0.046 | 0.057 | no | 0.435 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 41 | 4.0 | 0.18 | 0.127 | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 51 | 5.0 | 0.3 | 0.127 | no | 0.792 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 61 | 6.0 | 0.381 | 0.169 | no | 0.799 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 71 | 7.0 | 0.44 | 0.169 | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 81 | 8.0 | 0.484 | 0.169 | no | 0.8 | no | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 91 | 9.0 | 0.519 | 0.169 | no | 0.8 | no | 0.0 |
| 15.2 | 6.1 | yes | 15.2 | 1 | 0.0 | 0.758 | 0.0 | no | 0.758 | yes | 0.0 |
| 16.0 | 0.1 | no | 15.2 | 9 | 0.8 | 0.76 | 0.029 | no | 0.774 | yes | 0.0 |
| 17.0 | 0.1 | no | 15.2 | 19 | 1.8 | 0.774 | 0.029 | no | 0.799 | no | 0.0 |
| 18.0 | 0.1 | no | 15.2 | 29 | 2.8 | 0.783 | 0.084 | no | 0.8 | yes | 0.0 |
| 19.0 | 0.1 | no | 15.2 | 39 | 3.8 | 0.787 | 0.084 | no | 0.8 | no | 0.0 |
| 20.0 | 0.1 | no | 15.2 | 49 | 4.8 | 0.79 | 0.155 | no | 0.8 | yes | 0.0 |
| 21.0 | 0.1 | no | 15.2 | 59 | 5.8 | 0.791 | 0.155 | no | 0.8 | no | 0.0 |
| 22.0 | 0.1 | no | 15.2 | 69 | 6.8 | 0.793 | 0.209 | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 15.2 | 79 | 7.8 | 0.794 | 0.209 | no | 0.8 | no | 0.0 |
| 24.0 | 0.1 | no | 15.2 | 89 | 8.8 | 0.794 | 0.205 | no | 0.799 | yes | 0.0 |
| 30.2 | 6.0 | yes | 30.2 | 1 | 0.0 | 0.561 | 0.0 | no | 0.561 | yes | 0.0 |
| 31.0 | 0.1 | no | 30.2 | 9 | 0.8 | 0.573 | 0.0 | no | 0.662 | no | 0.0 |
| 32.0 | 0.1 | no | 30.2 | 19 | 1.8 | 0.656 | 0.043 | no | 0.8 | yes | 0.0 |
| 33.0 | 0.1 | no | 30.2 | 29 | 2.8 | 0.705 | 0.043 | no | 0.796 | no | 0.0 |
| 34.0 | 0.1 | no | 30.2 | 39 | 3.8 | 0.729 | 0.59 | no | 0.799 | yes | 0.0 |
| 35.0 | 0.1 | no | 30.2 | 49 | 4.8 | 0.743 | 0.59 | no | 0.8 | no | 0.0 |
| 36.0 | 0.1 | no | 30.2 | 59 | 5.8 | 0.753 | 1.356 | no | 0.8 | yes | 0.0 |
| 37.0 | 0.1 | no | 30.2 | 69 | 6.8 | 0.76 | 1.356 | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 30.2 | 79 | 7.8 | 0.765 | 2.56 | no | 0.8 | yes | 0.0 |
| 39.0 | 0.1 | no | 30.2 | 89 | 8.8 | 0.769 | 2.56 | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 30.2 | 99 | 9.8 | 0.772 | 3.843 | no | 0.8 | yes | 0.0 |

## blocked30, warm5, seed 388

531 calls up to 60 s; 1801.6 s; recovery moves at [26.1]; first outage at 664.5 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 12.0 s, 1.1 s after the call before, new fix: True; meanwhile recoveries +0, telemetry stops +0, tip stops +0, bridged +0.0 s
- at 32.1 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 46.1-59.9 s: 139 calls, 0 too slow, least moved 4.919 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.435 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.792 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 10 | 0.9 | 0.794 | 0.057 | no | 0.799 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 20 | 1.9 | 0.797 | 0.057 | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 30 | 2.9 | 0.798 | 0.057 | no | 0.8 | no | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 40 | 3.9 | 0.798 | 0.057 | no | 0.8 | no | 0.0 |
| 10.0 | 0.1 | no | 0.0 | 50 | 4.9 | 0.799 | 0.057 | no | 0.8 | no | 0.0 |
| 12.0 | 1.1 | yes | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 13.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 14.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 15.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 16.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 17.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 18.0 | 0.1 | no | 12.0 | 10 | 0.9 | 0.8 | 0.056 | no | 0.8 | yes | 0.0 |
| 19.0 | 0.1 | no | 12.0 | 20 | 1.9 | 0.8 | 0.056 | no | 0.8 | no | 0.0 |
| 20.0 | 0.1 | no | 12.0 | 30 | 2.9 | 0.8 | 0.137 | no | 0.8 | yes | 0.0 |
| 21.0 | 0.1 | no | 12.0 | 40 | 3.9 | 0.8 | 0.137 | no | 0.8 | no | 0.0 |
| 22.0 | 0.1 | no | 12.0 | 50 | 4.9 | 0.8 | 0.199 | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 12.0 | 60 | 5.9 | 0.8 | 0.199 | no | 0.8 | no | 0.0 |
| 24.0 | 0.1 | no | 12.0 | 70 | 6.9 | 0.8 | 0.186 | no | 0.799 | yes | 0.0 |
| 25.0 | 0.1 | no | 12.0 | 80 | 7.9 | 0.8 | 0.186 | no | 0.8 | no | 0.0 |
| 26.0 | 0.1 | no | 12.0 | 90 | 8.9 | 0.8 | 0.251 | no | 0.799 | yes | 0.0 |
| 32.1 | 6.0 | yes | 32.1 | 0 |  |  |  | no | 0.59 | yes | 0.0 |
| 33.0 | 0.1 | no | 32.1 | 0 |  |  |  | no | 0.699 | no | 0.0 |
| 34.0 | 0.1 | no | 32.1 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 35.0 | 0.1 | no | 32.1 | 0 |  |  |  | no | 0.798 | no | 0.0 |
| 36.0 | 0.1 | no | 32.1 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 37.0 | 0.1 | no | 32.1 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 32.1 | 10 | 0.9 | 0.8 | 1.069 | no | 0.8 | yes | 0.0 |
| 39.0 | 0.1 | no | 32.1 | 20 | 1.9 | 0.8 | 1.069 | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 32.1 | 30 | 2.9 | 0.8 | 2.232 | no | 0.799 | yes | 0.0 |

## blocked30, warm10, seed 388

531 calls up to 60 s; 1801.6 s; recovery moves at [31.0]; first outage at 664.5 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 12.0 s, 1.1 s after the call before, new fix: True; meanwhile recoveries +0, telemetry stops +0, tip stops +0, bridged +0.0 s
- at 37.0 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 56.0-59.9 s: 40 calls, 0 too slow, least moved 5.367 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.435 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.792 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 10.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 12.0 | 1.1 | yes | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 13.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 14.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 15.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 16.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 17.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 18.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 19.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 20.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 21.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 22.0 | 0.1 | no | 12.0 | 1 | 0.0 | 0.8 | 0.0 | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 12.0 | 11 | 1.0 | 0.8 | 0.0 | no | 0.8 | no | 0.0 |
| 24.0 | 0.1 | no | 12.0 | 21 | 2.0 | 0.8 | 0.071 | no | 0.799 | yes | 0.0 |
| 25.0 | 0.1 | no | 12.0 | 31 | 3.0 | 0.8 | 0.071 | no | 0.8 | no | 0.0 |
| 26.0 | 0.1 | no | 12.0 | 41 | 4.0 | 0.8 | 0.066 | no | 0.799 | yes | 0.0 |
| 27.0 | 0.1 | no | 12.0 | 51 | 5.0 | 0.8 | 0.066 | no | 0.8 | no | 0.0 |
| 28.0 | 0.1 | no | 12.0 | 61 | 6.0 | 0.8 | 0.146 | no | 0.8 | yes | 0.0 |
| 29.0 | 0.1 | no | 12.0 | 71 | 7.0 | 0.8 | 0.146 | no | 0.8 | no | 0.0 |
| 30.0 | 0.1 | no | 12.0 | 81 | 8.0 | 0.8 | 0.161 | no | 0.8 | yes | 0.0 |
| 31.0 | 0.1 | no | 12.0 | 91 | 9.0 | 0.8 | 0.161 | yes | 0.8 | no | 0.0 |
| 37.0 | 6.0 | yes | 37.0 | 0 |  |  |  | no | 0.556 | yes | 0.0 |
| 38.0 | 0.1 | no | 37.0 | 0 |  |  |  | no | 0.705 | yes | 0.0 |
| 39.0 | 0.1 | no | 37.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 37.0 | 0 |  |  |  | no | 0.799 | yes | 0.0 |

## quiet90, a0.3, seed 388

540 calls up to 60 s; 1801.6 s; recovery moves at [9.1]; first outage at 664.5 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 15.2 s, 6.1 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 24.2-59.9 s: 358 calls, 0 too slow, least moved 4.828 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 1 | 0.0 | 0.0 | 0.0 | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 11 | 1.0 | 0.0 | 0.0 | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 21 | 2.0 | 0.0 | 0.057 | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 31 | 3.0 | 0.046 | 0.057 | no | 0.435 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 41 | 4.0 | 0.18 | 0.127 | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 51 | 5.0 | 0.3 | 0.127 | no | 0.792 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 61 | 6.0 | 0.381 | 0.377 | no | 0.8 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 71 | 7.0 | 0.44 | 0.377 | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 81 | 8.0 | 0.484 | 0.377 | no | 0.8 | no | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 91 | 9.0 | 0.519 | 0.377 | no | 0.8 | no | 0.0 |
| 15.2 | 6.1 | yes | 15.2 | 1 | 0.0 | 0.743 | 0.0 | no | 0.743 | yes | 0.0 |
| 16.0 | 0.1 | no | 15.2 | 9 | 0.8 | 0.746 | 0.792 | no | 0.761 | yes | 0.0 |
| 17.0 | 0.1 | no | 15.2 | 19 | 1.8 | 0.763 | 0.792 | no | 0.799 | no | 0.0 |
| 18.0 | 0.1 | no | 15.2 | 29 | 2.8 | 0.775 | 1.74 | no | 0.8 | yes | 0.0 |
| 19.0 | 0.1 | no | 15.2 | 39 | 3.8 | 0.782 | 1.74 | no | 0.8 | no | 0.0 |
| 20.0 | 0.1 | no | 15.2 | 49 | 4.8 | 0.785 | 2.815 | no | 0.799 | yes | 0.0 |
| 21.0 | 0.1 | no | 15.2 | 59 | 5.8 | 0.788 | 2.815 | no | 0.8 | no | 0.0 |
| 22.0 | 0.1 | no | 15.2 | 69 | 6.8 | 0.79 | 4.085 | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 15.2 | 79 | 7.8 | 0.791 | 4.085 | no | 0.8 | no | 0.0 |
| 24.0 | 0.1 | no | 15.2 | 89 | 8.8 | 0.792 | 5.62 | no | 0.799 | yes | 0.0 |
| 25.0 | 0.1 | no | 15.2 | 99 | 9.8 | 0.793 | 5.62 | no | 0.8 | no | 0.0 |
| 26.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.798 | 6.322 | no | 0.8 | yes | 0.0 |
| 27.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 6.322 | no | 0.8 | no | 0.0 |
| 28.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 6.976 | no | 0.8 | yes | 0.0 |
| 29.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 6.976 | no | 0.8 | no | 0.0 |
| 30.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 7.667 | no | 0.8 | yes | 0.0 |
| 31.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 7.667 | no | 0.8 | no | 0.0 |
| 32.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.073 | no | 0.799 | yes | 0.0 |
| 33.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.073 | no | 0.8 | no | 0.0 |
| 34.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.354 | no | 0.8 | yes | 0.0 |
| 35.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.354 | no | 0.8 | no | 0.0 |
| 36.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.516 | no | 0.8 | yes | 0.0 |
| 37.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.516 | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.732 | no | 0.8 | yes | 0.0 |
| 39.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.732 | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 15.2 | 100 | 9.9 | 0.8 | 8.689 | no | 0.799 | yes | 0.0 |

## quiet90, warm10, seed 388

590 calls up to 60 s; 1801.6 s; recovery moves at []; first outage at 664.5 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 12.0 s, 1.1 s after the call before, new fix: True; meanwhile recoveries +0, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 31.0-59.9 s: 290 calls, 0 too slow, least moved 5.199 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.435 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.792 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 10.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 12.0 | 1.1 | yes | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 13.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.799 | no | 0.0 |
| 14.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 15.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 16.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 17.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 18.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 19.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 20.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 21.0 | 0.1 | no | 12.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 22.0 | 0.1 | no | 12.0 | 1 | 0.0 | 0.8 | 0.0 | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 12.0 | 11 | 1.0 | 0.8 | 0.0 | no | 0.8 | no | 0.0 |
| 24.0 | 0.1 | no | 12.0 | 21 | 2.0 | 0.8 | 1.789 | no | 0.799 | yes | 0.0 |
| 25.0 | 0.1 | no | 12.0 | 31 | 3.0 | 0.8 | 1.789 | no | 0.8 | no | 0.0 |
| 26.0 | 0.1 | no | 12.0 | 41 | 4.0 | 0.8 | 3.467 | no | 0.8 | yes | 0.0 |
| 27.0 | 0.1 | no | 12.0 | 51 | 5.0 | 0.8 | 3.467 | no | 0.8 | no | 0.0 |
| 28.0 | 0.1 | no | 12.0 | 61 | 6.0 | 0.8 | 5.192 | no | 0.8 | yes | 0.0 |
| 29.0 | 0.1 | no | 12.0 | 71 | 7.0 | 0.8 | 5.192 | no | 0.8 | no | 0.0 |
| 30.0 | 0.1 | no | 12.0 | 81 | 8.0 | 0.8 | 7.043 | no | 0.8 | yes | 0.0 |
| 31.0 | 0.1 | no | 12.0 | 91 | 9.0 | 0.8 | 7.043 | no | 0.8 | no | 0.0 |
| 32.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.8 | 8.773 | no | 0.799 | yes | 0.0 |
| 33.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.8 | 8.773 | no | 0.8 | no | 0.0 |
| 34.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.8 | 8.843 | no | 0.8 | yes | 0.0 |
| 35.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.8 | 8.843 | no | 0.8 | no | 0.0 |
| 36.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.8 | 8.856 | no | 0.8 | yes | 0.0 |
| 37.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.8 | 8.856 | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.799 | 8.964 | no | 0.727 | yes | 0.0 |
| 39.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.792 | 8.964 | no | 0.77 | no | 0.0 |
| 40.0 | 0.1 | no | 12.0 | 100 | 9.9 | 0.791 | 8.852 | no | 0.8 | yes | 0.0 |

## blocked30, a0.3, seed 374

481 calls up to 60 s; 1827.6 s; recovery moves at [9.1, 24.2]; first outage at 363.0 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 15.2 s, 6.1 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s
- at 30.2 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 39.2-59.9 s: 208 calls, 0 too slow, least moved 2.532 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 1 | 0.0 | 0.0 | 0.0 | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 11 | 1.0 | 0.0 | 0.0 | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 21 | 2.0 | 0.0 | 0.147 | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 31 | 3.0 | 0.048 | 0.147 | no | 0.484 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 41 | 4.0 | 0.188 | 0.255 | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 51 | 5.0 | 0.307 | 0.255 | no | 0.793 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 61 | 6.0 | 0.387 | 0.3 | no | 0.799 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 71 | 7.0 | 0.445 | 0.3 | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 81 | 8.0 | 0.489 | 0.357 | no | 0.8 | yes | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 91 | 9.0 | 0.523 | 0.357 | no | 0.8 | no | 0.0 |
| 15.2 | 6.1 | yes | 15.2 | 1 | 0.0 | 0.591 | 0.0 | no | 0.591 | yes | 0.0 |
| 16.0 | 0.1 | no | 15.2 | 9 | 0.8 | 0.592 | 0.102 | no | 0.656 | yes | 0.0 |
| 17.0 | 0.1 | no | 15.2 | 19 | 1.8 | 0.661 | 0.102 | no | 0.797 | no | 0.0 |
| 18.0 | 0.1 | no | 15.2 | 29 | 2.8 | 0.708 | 0.039 | no | 0.8 | yes | 0.0 |
| 19.0 | 0.1 | no | 15.2 | 39 | 3.8 | 0.732 | 0.039 | no | 0.8 | no | 0.0 |
| 20.0 | 0.1 | no | 15.2 | 49 | 4.8 | 0.746 | 0.096 | no | 0.8 | yes | 0.0 |
| 21.0 | 0.1 | no | 15.2 | 59 | 5.8 | 0.755 | 0.096 | no | 0.8 | no | 0.0 |
| 22.0 | 0.1 | no | 15.2 | 69 | 6.8 | 0.761 | 0.047 | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 15.2 | 79 | 7.8 | 0.766 | 0.047 | no | 0.8 | no | 0.0 |
| 24.0 | 0.1 | no | 15.2 | 89 | 8.8 | 0.77 | 0.062 | no | 0.799 | yes | 0.0 |
| 30.2 | 6.0 | yes | 30.2 | 1 | 0.0 | 0.587 | 0.0 | no | 0.587 | yes | 0.0 |
| 31.0 | 0.1 | no | 30.2 | 9 | 0.8 | 0.595 | 0.0 | no | 0.684 | no | 0.0 |
| 32.0 | 0.1 | no | 30.2 | 19 | 1.8 | 0.671 | 0.065 | no | 0.798 | yes | 0.0 |
| 33.0 | 0.1 | no | 30.2 | 29 | 2.8 | 0.716 | 0.065 | no | 0.8 | no | 0.0 |
| 34.0 | 0.1 | no | 30.2 | 39 | 3.8 | 0.737 | 0.676 | no | 0.8 | yes | 0.0 |
| 35.0 | 0.1 | no | 30.2 | 49 | 4.8 | 0.75 | 0.676 | no | 0.8 | no | 0.0 |
| 36.0 | 0.1 | no | 30.2 | 59 | 5.8 | 0.758 | 1.478 | no | 0.8 | yes | 0.0 |
| 37.0 | 0.1 | no | 30.2 | 69 | 6.8 | 0.764 | 1.478 | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 30.2 | 79 | 7.8 | 0.769 | 2.532 | no | 0.8 | yes | 0.0 |
| 39.0 | 0.1 | no | 30.2 | 89 | 8.8 | 0.772 | 2.532 | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 30.2 | 99 | 9.8 | 0.775 | 3.896 | no | 0.8 | yes | 0.0 |

## blocked30, warm5, seed 374

482 calls up to 60 s; 1827.6 s; recovery moves at [14.2, 34.2]; first outage at 363.0 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 20.2 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s
- at 40.2 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 54.2-59.9 s: 58 calls, 0 too slow, least moved 6.011 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.484 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.793 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 10 | 0.9 | 0.795 | 0.047 | no | 0.799 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 20 | 1.9 | 0.797 | 0.047 | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 30 | 2.9 | 0.798 | 0.117 | no | 0.8 | yes | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 40 | 3.9 | 0.799 | 0.117 | no | 0.8 | no | 0.0 |
| 10.0 | 0.1 | no | 0.0 | 50 | 4.9 | 0.799 | 0.204 | no | 0.8 | yes | 0.0 |
| 11.0 | 0.1 | no | 0.0 | 60 | 5.9 | 0.799 | 0.204 | no | 0.8 | no | 0.0 |
| 12.0 | 0.1 | no | 0.0 | 70 | 6.9 | 0.799 | 0.162 | no | 0.8 | yes | 0.0 |
| 13.0 | 0.1 | no | 0.0 | 80 | 7.9 | 0.799 | 0.162 | no | 0.8 | no | 0.0 |
| 14.0 | 0.1 | no | 0.0 | 90 | 8.9 | 0.799 | 0.122 | no | 0.8 | yes | 0.0 |
| 20.2 | 6.0 | yes | 20.2 | 0 |  |  |  | no | 0.587 | yes | 0.0 |
| 21.0 | 0.1 | no | 20.2 | 0 |  |  |  | no | 0.668 | no | 0.0 |
| 22.0 | 0.1 | no | 20.2 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 23.0 | 0.1 | no | 20.2 | 0 |  |  |  | no | 0.797 | no | 0.0 |
| 24.0 | 0.1 | no | 20.2 | 0 |  |  |  | no | 0.798 | yes | 0.0 |
| 25.0 | 0.1 | no | 20.2 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 26.0 | 0.1 | no | 20.2 | 9 | 0.8 | 0.8 | 0.133 | no | 0.799 | yes | 0.0 |
| 27.0 | 0.1 | no | 20.2 | 19 | 1.8 | 0.8 | 0.133 | no | 0.8 | no | 0.0 |
| 28.0 | 0.1 | no | 20.2 | 29 | 2.8 | 0.8 | 0.173 | no | 0.8 | yes | 0.0 |
| 29.0 | 0.1 | no | 20.2 | 39 | 3.8 | 0.8 | 0.173 | no | 0.8 | no | 0.0 |
| 30.0 | 0.1 | no | 20.2 | 49 | 4.8 | 0.8 | 0.08 | no | 0.8 | yes | 0.0 |
| 31.0 | 0.1 | no | 20.2 | 59 | 5.8 | 0.8 | 0.08 | no | 0.8 | no | 0.0 |
| 32.0 | 0.1 | no | 20.2 | 69 | 6.8 | 0.8 | 0.177 | no | 0.8 | yes | 0.0 |
| 33.0 | 0.1 | no | 20.2 | 79 | 7.8 | 0.8 | 0.177 | no | 0.799 | no | 0.0 |
| 34.0 | 0.1 | no | 20.2 | 89 | 8.8 | 0.8 | 0.847 | no | 0.8 | yes | 0.0 |

## blocked30, warm10, seed 374

541 calls up to 60 s; 1827.6 s; recovery moves at [19.1]; first outage at 363.0 s; against pace_u.py's record: identical.

Clears:

- at 0.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 25.1 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 44.1-59.9 s: 159 calls, 0 too slow, least moved 5.66 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0 |  | yes | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 1.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | no | 0.0 |
| 2.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.484 | no | 0.0 |
| 4.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.791 | yes | 0.0 |
| 5.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.793 | no | 0.0 |
| 6.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 7.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 8.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 9.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 10.0 | 0.1 | no | 0.0 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 11.0 | 0.1 | no | 0.0 | 10 | 0.9 | 0.799 | 0.0 | no | 0.8 | no | 0.0 |
| 12.0 | 0.1 | no | 0.0 | 20 | 1.9 | 0.799 | 0.068 | no | 0.8 | yes | 0.0 |
| 13.0 | 0.1 | no | 0.0 | 30 | 2.9 | 0.8 | 0.068 | no | 0.8 | no | 0.0 |
| 14.0 | 0.1 | no | 0.0 | 40 | 3.9 | 0.8 | 0.104 | no | 0.8 | yes | 0.0 |
| 15.0 | 0.1 | no | 0.0 | 50 | 4.9 | 0.8 | 0.104 | no | 0.8 | no | 0.0 |
| 16.0 | 0.1 | no | 0.0 | 60 | 5.9 | 0.8 | 0.106 | no | 0.8 | yes | 0.0 |
| 17.0 | 0.1 | no | 0.0 | 70 | 6.9 | 0.8 | 0.106 | no | 0.8 | no | 0.0 |
| 18.0 | 0.1 | no | 0.0 | 80 | 7.9 | 0.8 | 0.115 | no | 0.799 | yes | 0.0 |
| 19.0 | 0.1 | no | 0.0 | 90 | 8.9 | 0.8 | 0.115 | no | 0.8 | no | 0.0 |
| 25.1 | 6.0 | yes | 25.1 | 0 |  |  |  | no | 0.599 | yes | 0.0 |
| 26.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.691 | yes | 0.0 |
| 27.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 28.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.797 | yes | 0.0 |
| 29.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 30.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 31.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 32.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 33.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.799 | no | 0.0 |
| 34.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 35.0 | 0.1 | no | 25.1 | 0 |  |  |  | no | 0.799 | no | 0.0 |
| 36.0 | 0.1 | no | 25.1 | 10 | 0.9 | 0.799 | 0.945 | no | 0.799 | yes | 0.0 |
| 37.0 | 0.1 | no | 25.1 | 20 | 1.9 | 0.799 | 0.945 | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 25.1 | 30 | 2.9 | 0.8 | 2.102 | no | 0.8 | yes | 0.0 |
| 39.0 | 0.1 | no | 25.1 | 40 | 3.9 | 0.8 | 2.102 | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 25.1 | 50 | 4.9 | 0.8 | 3.537 | no | 0.8 | yes | 0.0 |

## blocked30, warm5, seed 373

521 calls up to 60 s; 1771.6 s; recovery moves at [16.2]; first outage at 1000.6 s; against pace_u.py's record: identical.

Clears:

- at 2.0 s, None s after the call before, new fix: True; meanwhile recoveries +None, telemetry stops +None, tip stops +None, bridged +None s
- at 22.2 s, 6.0 s after the call before, new fix: True; meanwhile recoveries +1, telemetry stops +0, tip stops +0, bridged +0.0 s

Held (full window, no verdict):

- 36.2-59.9 s: 238 calls, 0 too slow, least moved 1.694 m

| t | gap s | cleared | warm from | n | span s | mean lin | moved m | verdict | linear | new fix | bridged s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.0 |  | yes | 2.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 3.0 | 0.1 | no | 2.0 | 0 |  |  |  | no | 0.0 | no | 0.0 |
| 4.0 | 0.1 | no | 2.0 | 0 |  |  |  | no | 0.0 | yes | 0.0 |
| 5.0 | 0.1 | no | 2.0 | 0 |  |  |  | no | 0.447 | no | 0.0 |
| 6.0 | 0.1 | no | 2.0 | 0 |  |  |  | no | 0.79 | yes | 0.0 |
| 7.0 | 0.1 | no | 2.0 | 0 |  |  |  | no | 0.792 | no | 0.0 |
| 8.0 | 0.1 | no | 2.0 | 10 | 0.9 | 0.793 | 0.214 | no | 0.793 | yes | 0.0 |
| 9.0 | 0.1 | no | 2.0 | 20 | 1.9 | 0.794 | 0.214 | no | 0.8 | no | 0.0 |
| 10.0 | 0.1 | no | 2.0 | 30 | 2.9 | 0.796 | 0.187 | no | 0.8 | yes | 0.0 |
| 11.0 | 0.1 | no | 2.0 | 40 | 3.9 | 0.797 | 0.187 | no | 0.8 | no | 0.0 |
| 12.0 | 0.1 | no | 2.0 | 50 | 4.9 | 0.797 | 0.17 | no | 0.8 | yes | 0.0 |
| 13.0 | 0.1 | no | 2.0 | 60 | 5.9 | 0.798 | 0.17 | no | 0.8 | no | 0.0 |
| 14.0 | 0.1 | no | 2.0 | 70 | 6.9 | 0.798 | 0.123 | no | 0.8 | yes | 0.0 |
| 15.0 | 0.1 | no | 2.0 | 80 | 7.9 | 0.798 | 0.123 | no | 0.8 | no | 0.0 |
| 16.0 | 0.1 | no | 2.0 | 90 | 8.9 | 0.799 | 0.165 | no | 0.8 | yes | 0.0 |
| 22.2 | 6.0 | yes | 22.2 | 0 |  |  |  | no | 0.595 | yes | 0.0 |
| 23.0 | 0.1 | no | 22.2 | 0 |  |  |  | no | 0.676 | no | 0.0 |
| 24.0 | 0.1 | no | 22.2 | 0 |  |  |  | no | 0.799 | yes | 0.0 |
| 25.0 | 0.1 | no | 22.2 | 0 |  |  |  | no | 0.797 | no | 0.0 |
| 26.0 | 0.1 | no | 22.2 | 0 |  |  |  | no | 0.8 | yes | 0.0 |
| 27.0 | 0.1 | no | 22.2 | 0 |  |  |  | no | 0.8 | no | 0.0 |
| 28.0 | 0.1 | no | 22.2 | 9 | 0.8 | 0.8 | 0.0 | no | 0.799 | no | 0.0 |
| 29.0 | 0.1 | no | 22.2 | 19 | 1.8 | 0.8 | 0.0 | no | 0.8 | no | 0.0 |
| 30.0 | 0.1 | no | 22.2 | 29 | 2.8 | 0.8 | 0.06 | no | 0.8 | yes | 0.0 |
| 31.0 | 0.1 | no | 22.2 | 39 | 3.8 | 0.8 | 0.06 | no | 0.8 | no | 0.0 |
| 32.0 | 0.1 | no | 22.2 | 49 | 4.8 | 0.8 | 0.18 | no | 0.8 | yes | 0.0 |
| 33.0 | 0.1 | no | 22.2 | 59 | 5.8 | 0.8 | 0.18 | no | 0.8 | no | 0.0 |
| 34.0 | 0.1 | no | 22.2 | 69 | 6.8 | 0.8 | 0.797 | no | 0.8 | yes | 0.0 |
| 35.0 | 0.1 | no | 22.2 | 79 | 7.8 | 0.8 | 0.797 | no | 0.8 | no | 0.0 |
| 36.0 | 0.1 | no | 22.2 | 89 | 8.8 | 0.8 | 1.694 | no | 0.8 | yes | 0.0 |
| 37.0 | 0.1 | no | 22.2 | 99 | 9.8 | 0.8 | 1.694 | no | 0.8 | no | 0.0 |
| 38.0 | 0.1 | no | 22.2 | 100 | 9.9 | 0.8 | 2.943 | no | 0.8 | yes | 0.0 |
| 39.0 | 0.1 | no | 22.2 | 100 | 9.9 | 0.8 | 2.943 | no | 0.8 | no | 0.0 |
| 40.0 | 0.1 | no | 22.2 | 100 | 9.9 | 0.8 | 4.261 | no | 0.799 | yes | 0.0 |

