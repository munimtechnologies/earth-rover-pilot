# miniplus-v1: grade

Graded 2026-10-22 (~06:30 UTC) against `PREDICTION.md`, from `summary.json` and `report.md` (miniplus.py 0.1.0, run 2026-10-22 04:37-04:40 UTC, unit tests passed). MV2 of Munim, Inc.; written with AI agents. Text CC BY 4.0.

## What it read

8 public Earth Rover Mini+ datasets on the Hugging Face Hub: 44 episodes, 16,939 frames, 1,678 s (28 minutes). The largest was cagataydev/scout-earthrover-ecot (30 episodes, 11,762 frames). Two other Mini+ recordings were skipped because their robot_type was spelled differently (`earth_rover_mini_plus`, `earth-rover-mini`).

## Predictions

| | prediction | result | grade |
|---|---|---|---|
| P1 | >= 3 readable Mini+ datasets, >= 2,000 frames | 8 datasets, 16,939 frames | held |
| P2 | every `orientation` in [0, 360] | 0.0 to 358.0 | held |
| P3 | while turning, `orientation` changes at a median 1.5-2.5 s | median 0.5 s (n 107); 0.5 s over all frames (n 1,196) | **missed** |
| P4 | D1 has enough windows, clockwise share >= 0.8 | 2 windows from 1 dataset (minimum 10 from 2) | ungraded |
| P5 | turn rate 20-60 deg/s per unit | 7.1 deg/s per unit, from the same 2 windows | **missed**, on 2 windows only |
| P6 | D2 has enough frames, wheels share a sign >= 90% | 0 forward frames with all four wheels non-zero (minimum 50) | ungraded |
| P7 | GPS position changes at a median 0.5-2.5 s | no recording has a GPS fix: latitude and longitude read the no-fix value 1000 throughout | ungraded |
| P8 | with >= 20 course pairs, clockwise spread smaller | 0 pairs | ungraded |
| P9 | the gyroscope axis with the largest \|r\| is z | 0 windows with a gyroscope | ungraded |

2 held, 2 missed, 5 ungraded.

## Decisions

- **D1:** too few turn windows (2 from 1 dataset): no change.
- **D2:** too few forward frames (0): no change.

`rover_pilot.py` and `dead_reckon.py` stay as they are.

## What went wrong, plainly

The study found the data but its filters matched almost none of it. That was a design failure, not missing data:

- **The commands don't look like what the filters expected.** The teleop recordings send a turn as linear 0.3 with angular +-1, never as a spin with linear below 0.1. The autonomous runs (cagataydev) use small commands, |angular| at most 0.8 and mostly below 0.3. The 4 s windows of one-signed angular >= 0.3 almost never occurred.
- **The state arrives late and in steps.** In these recordings the whole `/data` state refreshes about every 0.5 s and lags the command by about 0.5 s. Asking for 1 s of one pure command right up to the frame left no forward frames.
- **Two naming misses.** cagataydev/scout-earthrover-ecot names its gyroscope `imu.gyro.x/y/z`, which v1 didn't look for (in that dataset it reads 0 throughout anyway). Two datasets were skipped over robot_type spelling.
- **No GPS anywhere.** Every public Mini+ recording we found has latitude and longitude at 1000, the no-fix value (`rover_pilot.py` already rejects it). So orientation can't be checked against the GPS course on public data.

## What it still shows

- **The Mini+'s `orientation` updates about twice a second** in these recordings (median 0.5 s between changes, also while turning), not every ~2 s as P3 assumed. 0.783 of readings are whole degrees. `FINDINGS-frodobots-2k.md` says the Mini+ "holds `orientation` for up to about 2 s between reports". That came from simulation assumptions, and this measurement says otherwise for these rovers. It will be corrected with the second pass.
- 0.923 of 10 fps frames repeat every field of the frame before, consistent with a state refresh of about 2 Hz recorded at 10 fps.

## Next

miniplus-b (pre-registered in `studies/miniplus-b/PREDICTION.md`) re-reads the same recordings with frame-based windows that allow for the 0.5 s lag, 2 s windows, any linear on turns, and the missing field names. It also checks whether the four `wheel_rpm` columns are really two, and whether the SDK's `speed` matches the wheels at 95 mm.
