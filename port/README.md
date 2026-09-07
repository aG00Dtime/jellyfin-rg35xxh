# Jellyfin RG35XX H

An unofficial controller-first Jellyfin client for the Anbernic RG35XX H running KNULLI.

## First-time setup

1. Copy the `Jellyfin RG35XX.sh` file and the `jellyfinrg35xx` folder into `roms/ports` on the KNULLI data card.
2. Launch **Jellyfin RG35XX** from KNULLI's **Ports** section.
3. On the first launch, use the controller keyboard to enter your Jellyfin server URL, username, and password.

The app accepts a bare domain and adds `https://` automatically. It also accepts explicit `http://` and `https://` URLs. After login, open Settings with **R1** to change video quality, edit connection details, or log out. Logging out asks for confirmation and keeps the server URL and username while requiring the password again.

Credentials are encrypted on the device using a device-local key. Never share the config or key files. Updates do not include or replace your saved connection data.

## Controls

- Home and library: D-pad moves, **A** opens, **B** goes back, **Y** searches, **R1** opens Settings, **Start** exits.
- Search keyboard: D-pad chooses, **A** types, **R1** toggles caps/symbols, **X** inserts a space, **Y** deletes, **Start** searches, **B** cancels.
- Details: **A** plays or resumes; **X** opens audio/subtitle Play Options; **Y** toggles watched status; **B** goes back.
- Video: **A** pauses, **B**, **Start**, or **Select** returns to the app.
- Video seeking: D-pad left/right skips 10 seconds; L1/R1 skips 30 seconds; L2/R2 skips 60 seconds.
- Audio and subtitles: **X** cycles audio tracks; **Y** cycles subtitle tracks, including Off.
- Volume buttons remain controlled by KNULLI.

Automatic KNULLI idle sleep is paused while Jellyfin is open and returns to normal when you exit.

Unfinished items resume from Jellyfin's saved position. Episode playback advances automatically to the next episode after a short loading screen. Library folders load more results automatically as you reach the end of the current page.
