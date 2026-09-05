# Build 1.3 device verification

Tested on 2026-09-04, KNULLI scarab, RG35XX H, aarch64, Python 3.12.8, pygame 2.5.2, mpv 0.40.0.

The installed build 1.2 log showed `JSONDecodeError: Extra data` in the single-read mpv JSON parser. Python exited and left mpv adopted by PID 1. KNULLI volume controls continued working independently.

Verified the RG35XX-H mapping in `/usr/share/emulationstation/es_input.cfg`: B=305, Start=311, Select=310, A=304, L1=308, R1=309. The previous player used generic mappings that do not match this controller. Negative hat values also require a signed input-event value.

## Completed checks

- All 12 regression tests passed on the device, including batched/fragmented JSON, interleaved replies, signed controller input, volume exclusion, nonblocking ordered reports, child cleanup after exceptions, and the Linux parent-death guard after SIGKILL.
- Ran a local 90-second generated clip through real mpv. Injected native controller events through the built-in evdev device, using the production controller reader and playback loop.
- B exit: 0.311 seconds; Start: 0.321 seconds; Select: 0.336 seconds. Each player process was reaped.
- Verified timestamp changes for D-pad +10/-10 seconds and R1 +30 seconds, plus A pause/resume. Exact seeking corrected keyframe-only jumps discovered during the test.
- Ran the production `play_item` with real pygame display handoff and HTTP reporting to a local stub. Verified start, progress, and stopped endpoints; final position 5.958333 seconds; the item received that resume position.
- Verified the returned display is 640x480 and receives SDL A button index 3 after mpv closes.
- Recovered the old abandoned movie position (875.250333 seconds), submitted it to the real Jellyfin server (HTTP 204), and verified it appears in the server's resume list.
- Subsequent live playback in the installed app logged native seek and stop commands, restored the library, and received HTTP 204 for real progress/stop reports. The recovered movie resumed at 875.250333 seconds and stopped at 886.218667 seconds.
- Added launcher and Python instance locks after overlapping app launches invalidated the older login during restart.
- Checked the installed file hashes match the tested staging files; rebuilt the update ZIP including `playback.py` without replacing user credentials.

These are automated device checks using injected controller events, not a claim that someone physically pressed each button. The local stub verifies report payload delivery, while the recovered movie provided a real-server save/readback check. This pass addresses the player crash, input mapping, cleanup, seek, and progress handling; it is not a full UI redesign.

## Repeating checks

Run `python -m unittest discover -s tests -v` locally. The Linux guard check runs on KNULLI and is skipped on Windows. `tools/verify_playback_device.py` contains the explicitly invoked device integration tests and the narrowly scoped orphan recovery helper. These tools are not included in the update package.
