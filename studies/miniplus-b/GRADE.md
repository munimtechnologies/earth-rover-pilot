# miniplus-b-v1: grade

Graded 2026-10-22 (~07:50 UTC) against `PREDICTION.md`, which was committed to this folder before the run. MV2 of Munim, Inc.; written with AI agents. Text CC BY 4.0.

The run: `miniplus_b.py` 0.1.0, 2026-10-22 06:19-06:22 UTC in a sealed container. Its 30 unit tests passed first. It read 10 public LeRobot recordings of the Earth Rover Mini+ (52 episodes, 22,929 frames; table data only) and skipped 3 Hub hits that have no `meta/info.json`. Every number below is copied from `summary.json` or `report.md` in this folder.

## Predictions

| | prediction | result | grade |
|---|---|---|---|
| Q1 | D1 has enough windows, and the pooled clockwise share is >= 0.8 | 77 qualifying windows from 3 recordings (enough); clockwise share 0.675 (52 of 77) | **missed** |
| Q2 | every recording with >= 10 qualifying windows has a clockwise share >= 0.7 | scout-earth-rover-mini 0.828 (29), scout-earthrover-ecot 0.595 (37), lilkm/earthrover-test 0.545 (11) | **missed** |
| Q3 | rpm2 = rpm0 and rpm3 = rpm1 on >= 99% of frames with a wheel turning (pooled) | 406 of 777 (0.523): every frame in lilkm/earthrover-test (406 of 406), none in AmitGMU/earthrover-navigation_20260610_165303 (0 of 371) | **missed** |
| Q4 | D2 has enough frames, and the four share a sign on >= 90% of them | 17 forward frames with all four wheels non-zero, fewer than the 30 needed (all 17 were all positive) | ungraded |
| Q5 | rpm1 is the right-hand side (>= 20 frames each; >= 60% each way) | left turns: rpm1 higher on 64 of 68 (0.941); right turns: rpm0 higher on 32 of 33 (0.970) | **held** |
| Q6 | the speed check's median is in [0.85, 1.05] (>= 50 frames) | 0.947 (IQR 0.945-0.948) on 289 frames | **held** |
| Q7 | median refresh 0.4-0.6 s in lilkm/earthrover-test and AmitGMU/... | 0.5 s and 0.3 s | **missed** |
| Q8 | gyroscope z has the largest \|r\| with the orientation rate, and r is negative | x has the largest: r = -0.615 (x), -0.345 (y), -0.106 (z), 65 windows | **missed** |
| Q9 | pooled median turn rate 15-90 °/s per unit of `angular` | 48.3 | **held** |
| Q10 | no recording has a valid GPS fix | valid share 0.0 on all 20,937 frames that log latitude, in all 8 recordings that do | **held** |

**4 held, 5 missed, 1 ungraded.**

## Decisions (rules stated before the run)

- **D1 (which way `orientation` runs): mixed, so no change.** 77 windows from 3 recordings met the minimum, but the clockwise share (0.675) is between the 0.2 and 0.8 bounds. The pilot keeps its real-rover default (degrees clockwise from north, a positive `angular` turning left) and `--calibrate` stays the way to find out on a real rover.
- **D2 (wheel signs): too few frames, so no change.** 17 qualifying forward frames against 30 needed. All 17 had four positive wheels, which agrees with the pilot's average of the four, but the rule can't call it.
- **D3 (wheel size): in range, so the 0.00497 m/s per RPM prior stays.** Median ratio 0.947 on 289 frames.

## Per recording

| recording | frames | live fields | qualifying turns | clockwise share | slope °/s per unit | refresh s |
|---|---|---|---|---|---|---|
| AmitGMU/earthrover-navigation_20260610_165303 | 600 | gyro, orientation, rpm, speed | 0 | - | -26.9 | 0.3 |
| anirudhgudi/frodobots-lerobot-dataset (2 fps) | 1,814 | orientation | 0 | - | +0.4 | 0.5 |
| cagataydev/scout-earth-rover-mini-20260616-053232 | 4,176 | orientation, speed | 29 | 0.828 | -41.0 | 0.5 |
| cagataydev/scout-earthrover-ecot | 11,762 | orientation | 37 | 0.595 | -14.2 | 0.5 |
| dkuzmenko/earth-rover-mini-test-4 | 2,400 | none | 0 | - | - | - |
| lilkm/earthrover-navigation | 595 | orientation | 0 | - | - | 0.6 |
| lilkm/earthrover-navigation-low-level-sdk (30 fps) | 178 | gyro | 0 | - | - | 0.033 |
| lilkm/earthrover-test | 755 | gyro, orientation, rpm, speed | 11 | 0.545 | -3.0 | 0.5 |
| lilkm/earthrover-test-2 | 328 | orientation | 0 | - | -0.1 | 0.3 |
| lilkm/earthrover-test-3 | 321 | orientation | 0 | - | -9.4 | 0.3 |

"Slope" is the least-squares slope of orientation's rate on the mean `angular` over every one-signed window (qualifying or not); negative means orientation falls under a positive (left-turn) command, which is what the pilot's default expects.

## What it shows

- **The Mini+'s orientation changes every 0.3-0.6 s** (pooled median 0.5 s over 3,567 changes). The earlier simulation assumed 2 s; FINDINGS' line saying the Mini+ holds `orientation` "for up to about 2 s" is wrong and is corrected in the next docs release.
- **Which way orientation runs is not settled by these recordings.** Window by window it is 2 to 1 in the pilot's favour, short of the 4 to 1 the rule needs. Not pre-registered, so only a pointer: the fitted slope is negative in all six recordings that have it with any size (-3 to -41), and positive only in the 2 fps recording with no qualifying window (+0.4). The median turn per unit of command (48 °/s) is about twice the pooled slope (22.6), so much of orientation's movement isn't explained by the command: indoor magnetic disturbance, short autonomous runs with small commands, and the 0.5 s refresh are all plausible causes, none tested.
- **rpm0 is the left side and rpm1 the right** (Q5, 96 of 101 turning frames). Whether rpm2 and rpm3 repeat them depends on the recording (all frames in one, none in the other), so they may be separate wheels on some firmware or set-ups. The pilot's mean of the four is the centre's speed either way, so `dead_reckon.py` needs no change.
- **`speed` is km/h and agrees with 95 mm wheels** to within about 5%. 288 of the 289 frames come from one recording.
- **No public Mini+ recording has a GPS fix,** so orientation can't be tied to north, and the FrodoBots-2K GPS-course studies can't be repeated on a Mini+ from public data.
- **Gyroscope:** x follows orientation's rate most closely, with a negative r. That fits x being the yaw axis with counter-clockwise positive, as measured on the Earth Rover Zero, if orientation runs clockwise. The look at about 190 rows before the run had pointed to z (Q8), and over whole windows z hardly follows. The size (about 0.06 per °/s of orientation) fits neither degrees nor radians per second cleanly. Two recordings, 65 windows; the pilot doesn't read the gyroscope.

## Limits

Hobby and test recordings, minutes long, from a handful of rovers, mostly indoors and without GPS. Q3, Q6 and Q8 were informed by a look at one recording before the predictions were written (disclosed in PREDICTION.md); the wheel and speed results rest almost entirely on that recording. cagataydev/scout-earth-rover-mini-20260616-053232's robot_type says "earth-rover-mini", not "plus". LeRobot repeats the last `/data` answer when a request fails, so refresh intervals include the network. The recordings belong to their uploaders (nine Apache-2.0, one MIT); only measurements are published here.

## Prior art

The Earth Rover SDK documents none of these conventions (its README shows `orientation` as a bare number and `rpms` as zeros). As far as found, no one has published them measured from recordings.
