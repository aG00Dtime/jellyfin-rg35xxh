# Jellyfin RG35XX H

An unofficial controller-first Jellyfin client for the Anbernic RG35XX H running KNULLI.

## First-time setup

1. In this folder, rename `config.example.json` to `config.json`.
2. Open `config.json` with a plain-text editor.
3. Enter your Jellyfin server address, username, and password, then save.
4. Launch **Jellyfin RG35XX** from KNULLI's **Ports** section.

Keep `config.json` private. Updates do not include or replace it.

## Controls

- Home and library: D-pad moves, **A** opens, **B** goes back, **Start** exits.
- Video: **A** pauses, **B**, **Start**, or **Select** returns to the app.
- Video seeking: D-pad left/right skips 10 seconds; L1/R1 skips 30 seconds; L2/R2 skips 60 seconds.
- Audio and subtitles: **X** cycles audio tracks; **Y** cycles subtitle tracks, including Off.
- Volume buttons remain controlled by KNULLI.
