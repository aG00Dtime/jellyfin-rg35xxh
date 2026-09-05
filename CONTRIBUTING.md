# Contributing

Thank you for helping improve Jellyfin RG35XX H.

Please keep the handheld experience in mind: it has a 640×480 screen, a D-pad, face buttons, limited memory, and no touchscreen.

Before opening a pull request, run:

```powershell
.\package.ps1
python -m unittest discover -s tests -v
```

Do not commit `config.json`, server addresses, usernames, passwords, device logs, screenshots with personal information, or SD-card recovery copies. Use `config/config.example.json` for documentation and test data.

Changes to playback need testing on an RG35XX H running KNULLI. Describe the firmware version, video type, and the buttons you used when reporting an issue.
