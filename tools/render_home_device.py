"""Render the real Jellyfin home data at 640x480 for device-layout verification."""
import io
import os
import sys

APP = os.environ.get("JELLYFIN_APP_DIR", "/userdata/roms/ports/jellyfinrg35xx")
sys.path.insert(0, APP)

import pygame
import jellyfin_rg35xx as app
from library import Artwork, LibraryAPI, Rows
from ui import Renderer

pygame.init()
screen = pygame.display.set_mode((640, 480))
config, error = app.load_config()
assert config, error
token, user_id = app.authenticate(config)
api = LibraryAPI(config, token, user_id, app.auth_headers(token), app.CA_BUNDLE)
views = api.views()
rows = Rows([
    {"title": "My Media", "items": views, "loaded": True},
    {"title": "Next Up", "items": api.next_up(), "loaded": True},
    {"title": "Continue Watching", "items": api.resume(), "loaded": True},
])
artwork = Artwork(api, "/tmp/jellyfin-home-render-art")
for row in rows.values:
    for item in row["items"][:3]:
        key = artwork.key(item, True)
        content = artwork._download(item, True, key)
        if content:
            artwork.images[key] = pygame.image.load(io.BytesIO(content)).convert()
renderer = Renderer(screen, "1.4")
renderer.home(rows, artwork, lambda _: None)
pygame.image.save(screen, "/tmp/jellyfin-home-1.4.png")
print("HOME_RENDER_OK rows=%d artwork=%d" % (len(rows.values), len(artwork.images)), flush=True)
pygame.quit()
