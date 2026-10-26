# Why was restarting the GPS average slower on outage90 boulevard? (simulated)

trace_s.py 0.1.0 (pace_s.py 0.1.0, rover_pilot.py 0.18.4), MV2 of Munim, Inc. A diagnostic, not a pre-registered study: pace_s.py's missions flown again with both GPS filters, one row a second of simulated time (trace-<profile>-<variant>-<seed>.csv). A stop is 4 s or more with the rover told to stand.

## outage90, seed 327

### a0.3

1680 rows; 1765.6 s; 1 recoveries; time stopped 9.4 s; largest estimate error 55.71 m.
Against pace_s.py's record: identical.

Outages (first and last second): 1253.5-1341.5

Checkpoints reached at: 456.6 s, 914.6 s, 1344.8 s

Stops:

- 1337.1-1343.7 s, 71% in an outage, fresh fix at its start: False, 2 checkpoints reached, 4.35 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.96 m off, 395.2 m from the next checkpoint

### restart

1687 rows; 1773.6 s; 2 recoveries; time stopped 9.3 s; largest estimate error 10.21 m.
Against pace_s.py's record: identical.

Outages (first and last second): 1253.5-1341.5

Checkpoints reached at: 456.6 s, 914.6 s, 1344.8 s

Stops:

- 1337.1-1343.7 s, 71% in an outage, fresh fix at its start: False, 2 checkpoints reached, 4.35 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.96 m off, 395.2 m from the next checkpoint
- at 1353.6 s, with sky, fresh fix: True, estimate 5.06 m off, 371.62 m from the next checkpoint

restart minus a0.3: 8.0 s; the rovers first part at 172.0 s.

## outage90, seed 328

### a0.3

1738 rows; 1829.6 s; 0 recoveries; time stopped 74.7 s; largest estimate error 63.01 m.
Against pace_s.py's record: identical.

Outages (first and last second): 109.3-197.3; 378.6-467.6; 686.6-775.6; 1004.6-1092.9; 1321.7-1410.8; 1651.7-1739.7

Checkpoints reached at: 468.6 s, 928.6 s, 1413 s

Stops:

- 451.6-467.6 s, 100% in an outage, fresh fix at its start: False, 0 checkpoints reached, 9.09 m from the next
- 1358-1411.9 s, 98% in an outage, fresh fix at its start: False, 2 checkpoints reached, 4.22 m from the next

Recovery moves:

- none

### restart

1744 rows; 1835.6 s; 1 recoveries; time stopped 70.5 s; largest estimate error 11.0 m.
Against pace_s.py's record: identical.

Outages (first and last second): 109.3-197.3; 378.6-467.6; 686.6-775.6; 1004.6-1092.9; 1321.7-1410.8; 1651.7-1739.7

Checkpoints reached at: 468.6 s, 928.6 s, 1413 s

Stops:

- 451.6-467.6 s, 100% in an outage, fresh fix at its start: False, 0 checkpoints reached, 7.32 m from the next
- 1362.4-1411.9 s, 98% in an outage, fresh fix at its start: False, 2 checkpoints reached, 4.68 m from the next

Recovery moves:

- at 477.6 s, with sky, fresh fix: True, estimate 5.25 m off, 404.06 m from the next checkpoint

restart minus a0.3: 6.0 s; the rovers first part at 201.7 s.

## outage90, seed 331

### a0.3

1800 rows; 1897.6 s; 1 recoveries; time stopped 136.7 s; largest estimate error 65.26 m.
Against pace_s.py's record: identical.

Outages (first and last second): 90.6-178.6; 506.6-595.6; 1365.7-1454.8

Checkpoints reached at: 598.6 s, 1054.4 s, 1472.4 s

Stops:

- 93.9-179.7 s, 99% in an outage, fresh fix at its start: False, 0 checkpoints reached, 329.77 m from the next
- 550.6-597.6 s, 96% in an outage, fresh fix at its start: False, 0 checkpoints reached, 5.36 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 5.43 m off, 395.33 m from the next checkpoint

### restart

1802 rows; 1899.6 s; 2 recoveries; time stopped 137.4 s; largest estimate error 11.41 m.
Against pace_s.py's record: identical.

Outages (first and last second): 90.6-178.6; 506.6-595.6; 1365.7-1454.8

Checkpoints reached at: 598.6 s, 1058.8 s, 1474.6 s

Stops:

- 93.9-179.7 s, 99% in an outage, fresh fix at its start: False, 0 checkpoints reached, 329.77 m from the next
- 550.6-597.6 s, 96% in an outage, fresh fix at its start: False, 0 checkpoints reached, 4.82 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 5.43 m off, 395.33 m from the next checkpoint
- at 607.6 s, with sky, fresh fix: True, estimate 5.97 m off, 401.43 m from the next checkpoint

restart minus a0.3: 2.0 s; the rovers first part at 181.9 s.

## outage90, seed 337

### a0.3

1669 rows; 1753.6 s; 1 recoveries; time stopped 1.5 s; largest estimate error 63.95 m.
Against pace_s.py's record: identical.

Outages (first and last second): 523.6-612.6; 1025.8-1114.9; 1202.9-1290.9

Checkpoints reached at: 454.6 s, 910.6 s, 1328.3 s

Stops:

- none

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.66 m off, 395.25 m from the next checkpoint

### restart

1671 rows; 1755.6 s; 1 recoveries; time stopped 1.5 s; largest estimate error 10.75 m.
Against pace_s.py's record: identical.

Outages (first and last second): 523.6-612.6; 1025.8-1114.9; 1202.9-1290.9

Checkpoints reached at: 454.6 s, 912.6 s, 1330.5 s

Stops:

- none

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.66 m off, 395.25 m from the next checkpoint

restart minus a0.3: 2.0 s; the rovers first part at 97.2 s.

## outage90, seed 338

### a0.3

1733 rows; 1823.6 s; 1 recoveries; time stopped 64.6 s; largest estimate error 62.43 m.
Against pace_s.py's record: identical.

Outages (first and last second): 118.1-207.2; 1311.8-1400.9; 1498.8-1587.9

Checkpoints reached at: 454.6 s, 914.6 s, 1402 s

Stops:

- 1340.4-1402 s, 98% in an outage, fresh fix at its start: False, 2 checkpoints reached, 1.41 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.95 m off, 395.31 m from the next checkpoint

### restart

1818 rows; 1917.6 s; 2 recoveries; time stopped 144.8 s; largest estimate error 10.61 m.
Against pace_s.py's record: identical.

Outages (first and last second): 118.1-207.2; 1311.8-1400.9; 1498.8-1587.9; 1824.4-1913.5

Checkpoints reached at: 456.6 s, 914.6 s, 1402 s

Stops:

- 1340.4-1402 s, 98% in an outage, fresh fix at its start: False, 2 checkpoints reached, 1.27 m from the next
- 1837.6-1916.8 s, 96% in an outage, fresh fix at its start: False, 3 checkpoints reached, 4.44 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.95 m off, 395.31 m from the next checkpoint
- at 1411.9 s, with sky, fresh fix: True, estimate 4.91 m off, 370.22 m from the next checkpoint

restart minus a0.3: 94.0 s; the rovers first part at 209.4 s.

## outage90, seed 339

### a0.3

1673 rows; 1757.6 s; 1 recoveries; time stopped 1.5 s; largest estimate error 62.57 m.
Against pace_s.py's record: identical.

Outages (first and last second): 521.6-610.6

Checkpoints reached at: 454.6 s, 910.6 s, 1328.3 s

Stops:

- none

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 3.11 m off, 395.23 m from the next checkpoint

### restart

1676 rows; 1761.6 s; 2 recoveries; time stopped 1.5 s; largest estimate error 11.54 m.
Against pace_s.py's record: identical.

Outages (first and last second): 521.6-610.6

Checkpoints reached at: 454.6 s, 910.6 s, 1336 s

Stops:

- none

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 3.11 m off, 395.23 m from the next checkpoint
- at 984.6 s, with sky, fresh fix: True, estimate 5.18 m off, 313.88 m from the next checkpoint

restart minus a0.3: 4.0 s; the rovers first part at 357.6 s.

## quietdrift90, seed 338

### a0.3

1818 rows; 1917.6 s; 1 recoveries; time stopped 141.2 s; largest estimate error 62.57 m.
Against pace_s.py's record: identical.

Outages (first and last second): 118.1-207.2; 1311.8-1400.9; 1498.8-1587.9; 1824.4-1913.5

Checkpoints reached at: 458.6 s, 914.6 s, 1402 s

Stops:

- 1339.3-1402 s, 98% in an outage, fresh fix at its start: False, 2 checkpoints reached, 3.15 m from the next
- 1840.9-1916.8 s, 96% in an outage, fresh fix at its start: False, 3 checkpoints reached, 2.98 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.36 m off, 395.43 m from the next checkpoint

### restart

1818 rows; 1917.6 s; 1 recoveries; time stopped 138.8 s; largest estimate error 26.42 m.
Against pace_s.py's record: identical.

Outages (first and last second): 118.1-207.2; 1311.8-1400.9; 1498.8-1587.9; 1824.4-1913.5

Checkpoints reached at: 458.6 s, 914.6 s, 1402 s

Stops:

- 1339.3-1402 s, 98% in an outage, fresh fix at its start: False, 2 checkpoints reached, 3.2 m from the next
- 1843.1-1916.8 s, 96% in an outage, fresh fix at its start: False, 3 checkpoints reached, 2.99 m from the next

Recovery moves:

- at 9.6 s, with sky, fresh fix: True, estimate 4.36 m off, 395.43 m from the next checkpoint

restart minus a0.3: 0.0 s; the rovers first part at 209.4 s.

