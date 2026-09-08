# Changelog

## [2.1.3] - 2026-09-08

### Fixed

- Added Jellyfin 12-compatible `Authorization: MediaBrowser` request headers.
- Switched authenticated playback URLs from legacy `api_key=` to `ApiKey=`.
- Updated mpv playback authentication so transcoded streams work with Jellyfin 12.

### Documentation

- Documented Jellyfin Server 12.0 as the target server version.
- Documented Jellyfin Server 10.11.x as the older compatibility line.
- Added troubleshooting guidance for Jellyfin 12 authorization failures.

## [2.1.2] - 2026-09-05

- Reduced artwork download sizes and memory cache limits for faster browsing on the RG35XX H.
