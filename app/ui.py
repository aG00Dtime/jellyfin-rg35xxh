"""640x480 controller UI with Jellyfin home shelves and asynchronous artwork."""
import math
import os
import time

import pygame

from library import Artwork, Jobs, LibraryAPI, Rows

BG = (16, 16, 20)
PANEL = (28, 29, 36)
TEXT = (244, 244, 248)
MUTED = (161, 165, 180)
ACCENT = (0, 164, 220)
BODY = pygame.Rect(0, 66, 640, 370)
ROW_HEIGHT = 182


class Renderer:
    def __init__(self, screen, build):
        self.screen, self.build = screen, build
        bundled_font = os.path.join(os.path.dirname(__file__), "assets", "DejaVuSans.ttf")
        font = bundled_font if os.path.exists(bundled_font) else "/usr/share/fonts/dejavu/DejaVuSans.ttf"
        self.small = pygame.font.Font(font, 14)
        self.font = pygame.font.Font(font, 17)
        self.heading = pygame.font.Font(font, 21)
        self.title = pygame.font.Font(font, 25)
        self.logo = pygame.transform.smoothscale(pygame.image.load(
            os.path.join(os.path.dirname(__file__), "assets", "jellyfin-icon.png")).convert_alpha(), (35, 35))
        self.scroll = 0.0

    def text(self, value, x, y, width, font=None, color=TEXT, center=False):
        font = font or self.font
        value = str(value or "").replace("\n", " ")
        while value and font.size(value)[0] > width:
            value = value[:-2].rstrip("…") + "…" if len(value) > 2 else ""
        image = font.render(value, True, color)
        self.screen.blit(image, (x + ((width - image.get_width()) // 2 if center else 0), y))

    def wrap(self, value, x, y, width, lines, font=None, color=MUTED):
        font = font or self.small
        words = str(value or "").split()
        height = font.get_linesize() + 3
        for line in range(lines):
            current = ""
            while words and (not current or font.size(current + " " + words[0])[0] <= width):
                current = (current + " " + words.pop(0)).strip()
            if line == lines - 1 and words:
                current += "…"
            self.text(current, x, y + line * height, width, font, color)
            if not words:
                break

    def spinner(self, x, y, radius=10):
        angle = time.monotonic() * 4.5
        for index in range(10):
            light = 65 + index * 19
            point = (round(x + math.cos(angle + index * 0.6) * radius),
                     round(y + math.sin(angle + index * 0.6) * radius))
            pygame.draw.circle(self.screen, (0, min(light, 164), min(light + 35, 255)), point, 2)

    def header(self, home=True):
        self.screen.set_clip(None)
        self.screen.fill(BG)
        self.screen.blit(self.logo, (16, 13))
        self.text("Jellyfin", 59, 15, 122, self.title)
        self.text("Home" if home else "Library", 222, 24, 130, self.font, TEXT)
        pygame.draw.rect(self.screen, ACCENT, (222, 57, 48 if home else 62, 3), border_radius=1)
        self.text("RG35XX H", 418, 24, 121, self.small, MUTED)
        self.text(self.build, 560, 24, 62, self.small, MUTED)
        pygame.draw.line(self.screen, (43, 44, 52), (18, 63), (622, 63))

    def footer(self, message):
        self.screen.set_clip(None)
        pygame.draw.rect(self.screen, BG, (0, 438, 640, 42))
        pygame.draw.line(self.screen, (43, 44, 52), (18, 438), (622, 438))
        self.text(message, 18, 450, 607, self.small, MUTED)

    def card(self, item, rect, artwork, selected, landscape=True, subtitle=True):
        image_height = rect.height - (42 if subtitle else 25)
        image_rect = pygame.Rect(rect.x, rect.y, rect.width, image_height)
        pygame.draw.rect(self.screen, PANEL, image_rect, border_radius=5)
        surface, loading = artwork.get(item, (image_rect.width, image_rect.height), landscape) if artwork else (None, True)
        if surface:
            self.screen.blit(surface, (image_rect.centerx - surface.get_width() // 2,
                                       image_rect.centery - surface.get_height() // 2))
        elif loading:
            self.spinner(*image_rect.center)
        else:
            cx, cy = image_rect.center
            pygame.draw.rect(self.screen, (86, 97, 123), (cx - 19, cy - 9, 38, 24), 2, border_radius=3)
            pygame.draw.line(self.screen, (86, 97, 123), (cx - 17, cy - 12), (cx - 3, cy - 12), 3)
        if selected:
            pygame.draw.rect(self.screen, ACCENT, image_rect.inflate(6, 6), 3, border_radius=7)
        data = item.get("UserData") or {}
        if data.get("Played"):
            # Match Jellyfin's familiar watched badge without obscuring poster art.
            badge = (image_rect.right - 15, image_rect.y + 15)
            pygame.draw.circle(self.screen, (24, 143, 89), badge, 11)
            pygame.draw.lines(self.screen, (255, 255, 255), False,
                              [(badge[0] - 5, badge[1]), (badge[0] - 1, badge[1] + 4),
                               (badge[0] + 6, badge[1] - 5)], 2)
        ticks, duration = data.get("PlaybackPositionTicks", 0), item.get("RunTimeTicks", 0)
        if ticks and duration:
            fraction = max(0, min(1, ticks / duration))
            pygame.draw.rect(self.screen, (35, 37, 46), (image_rect.x, image_rect.bottom - 4, image_rect.width, 4))
            pygame.draw.rect(self.screen, ACCENT, (image_rect.x, image_rect.bottom - 4, round(image_rect.width * fraction), 4))
        name = item.get("SeriesName") if item.get("Type") == "Episode" else item.get("Name")
        self.text(name or item.get("Name", "Untitled"), rect.x, image_rect.bottom + 7, rect.width,
                  self.font, TEXT if selected else (221, 223, 232), center=True)
        if subtitle:
            if item.get("Type") == "Episode":
                extra = "S%s E%s · %s" % (item.get("ParentIndexNumber", "?"), item.get("IndexNumber", "?"), item.get("Name", ""))
            else:
                extra = str(item.get("ProductionYear") or "")
            self.text(extra, rect.x, image_rect.bottom + 28, rect.width, self.small, MUTED, center=True)

    def home(self, rows, artwork, load_row):
        self.header()
        top = max(0, rows.row - 1)
        target = top * ROW_HEIGHT
        self.scroll += (target - self.scroll) * 0.35
        if abs(target - self.scroll) < 1:
            self.scroll = target
        self.screen.set_clip(BODY)
        for index, row in enumerate(rows.values):
            y = round(76 + index * ROW_HEIGHT - self.scroll)
            if y + ROW_HEIGHT < BODY.top or y > BODY.bottom:
                continue
            load_row(index)
            self.text(row["title"], 18, y, 485, self.heading)
            items = row.get("items", [])
            col = min(rows.columns[index], max(0, len(items) - 1))
            first = max(0, col - 2)
            if items:
                self.text(f"{col + 1} / {len(items)}", 527, y + 5, 92, self.small, MUTED)
            if row.get("loading"):
                self.spinner(314, y + 78)
                self.text("Loading...", 254, y + 102, 120, self.small, MUTED, center=True)
            elif not items:
                self.text(row.get("error") or row.get("empty", "Nothing here yet"), 20, y + 61, 600, self.font, MUTED)
            for offset, item in enumerate(items[first:first + 3]):
                self.card(item, pygame.Rect(18 + offset * 204, y + 31, 188, 144), artwork,
                          index == rows.row and first + offset == col)
        self.footer("D-pad  Browse rows     A  Open     X  Refresh     Start  Exit")

    def search(self, page, artwork, loading=False):
        self.header(False)
        title = "Search all libraries" if not page.get("parent") else "Search in " + page["parent"].get("Name", "folder")
        self.text(title, 18, 78, 390, self.heading)
        query = page.get("query") or ""
        self.text(query or "Enter a title, series, or episode", 18, 108, 500, self.font,
                  TEXT if query else MUTED)
        character = page["alphabet"][page["character"]]
        self.text("D-pad  <  " + character + "  >", 450, 108, 170, self.small, ACCENT, center=True)
        items = page.get("items", [])
        selected = page.get("selection", 0)
        total = page.get("total")
        self.text((str(total) + " results") if query else "", 18, 137, 180, self.small, MUTED)
        if query and not items and not loading:
            self.text("No matches yet", 18, 210, 604, self.heading, MUTED, center=True)
        first = max(0, min(selected, max(0, len(items) - 3)))
        for offset, item in enumerate(items[first:first + 3]):
            self.card(item, pygame.Rect(18 + offset * 204, 163, 188, 144), artwork,
                      first + offset == selected, True)
        if loading:
            self.spinner(606, 143, 7)
        self.wrap("A Add character     X Delete     Up/Down Select result     Y Open result", 18, 340, 604, 2,
                  self.small, MUTED)
        self.footer("B  Back     Start  Exit")

    def listing(self, page, artwork, loading=False):
        self.header(False)
        self.text(page["title"], 18, 79, 480, self.heading)
        items = page["items"]
        selected = page["selection"]
        portrait = page.get("portrait", True)
        capacity = 4 if portrait else 6
        first = selected // capacity * capacity
        total = page.get("total")
        counter = f"{selected + 1 if items else 0} / {total if total is not None else len(items)}"
        self.text(counter, 510, 83, 112, self.small, MUTED)
        if not items and not loading:
            self.text("No items in this folder", 70, 220, 500, self.heading, MUTED, center=True)
        for offset, item in enumerate(items[first:first + capacity]):
            if portrait:
                rect = pygame.Rect(18 + offset * 155, 121, 140, 262)
            else:
                rect = pygame.Rect(18 + (offset % 3) * 204, 121 + (offset // 3) * 153, 188, 139)
            self.card(item, rect, artwork, first + offset == selected, not portrait)
        if page.get("more"):
            self.text("More titles load as you browse", 18, 411, 580, self.small, MUTED)
        self.footer("D-pad  Browse     A  Open     Y  Search here     B  Back     Start  Exit")

    def detail(self, item, artwork, status, options=None):
        self.header(False)
        self.card(item, pygame.Rect(18, 110, 144, 240), artwork, False, False, False)
        self.wrap(item.get("SeriesName") or item.get("Name", "Untitled"), 185, 82, 434, 2, self.heading, TEXT)
        extra = [item.get("Type", ""), str(item.get("ProductionYear") or "")]
        if item.get("RunTimeTicks"):
            extra.append(str(round(item["RunTimeTicks"] / 600000000)) + " min")
        self.text(" · ".join(v for v in extra if v), 185, 143, 434, self.small, MUTED)
        if item.get("Type") == "Episode":
            self.text(item.get("Name"), 185, 166, 434, self.font, TEXT)
        self.wrap(item.get("Overview") or "No description available.", 185, 195, 432, 7)
        ticks = (item.get("UserData") or {}).get("PlaybackPositionTicks", 0)
        label = "Resume %d:%02d" % (ticks // 600000000, (ticks // 10000000) % 60) if ticks > 30000000 else "Play"
        if item.get("Type") in ("Movie", "Episode", "Video", "MusicVideo"):
            pygame.draw.rect(self.screen, ACCENT, (185, 362, 212, 39), border_radius=5)
            self.text("A   " + label, 195, 371, 192, self.font, TEXT, center=True)
        else:
            self.text("This media type is not playable yet", 185, 370, 429, self.small, MUTED)
        self.text(status, 18, 414, 600, self.small, MUTED)
        self.footer("A  Play / Resume     X  Play options     B  Back     Start  Exit")
        if options:
            pygame.draw.rect(self.screen, (30, 32, 41), (174, 268, 452, 150), border_radius=8)
            self.text("Play options", 192, 282, 400, self.heading)
            values = [("Play", "Start video"), ("Audio", options["audio"][options["audio_at"]]["label"]),
                      ("Subtitles", options["subtitles"][options["subtitle_at"]]["label"])]
            for index, (label, value) in enumerate(values):
                y = 315 + index * 30
                if index == options["row"]:
                    pygame.draw.rect(self.screen, ACCENT, (188, y - 3, 420, 25), border_radius=4)
                self.text(label, 201, y, 105, self.small, TEXT)
                self.text(value, 315, y, 280, self.small, TEXT)
            self.footer("D-pad  Choose     A  Change / Play     B  Save and return")

    def loading(self, label, modal=True):
        if modal:
            shade = pygame.Surface((640, 374), pygame.SRCALPHA)
            shade.fill((10, 10, 15, 218))
            self.screen.blit(shade, (0, 64))
        pygame.draw.rect(self.screen, (30, 32, 41), (116, 175, 408, 127), border_radius=9)
        self.spinner(320, 210, 13)
        self.text(label, 136, 244, 368, self.font, TEXT, center=True)


class LibraryUI:
    def __init__(self, config, error, build, authenticate, play_item, prepare_playback, headers, verify):
        pygame.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joystick in self.joysticks:
            joystick.init()
        self.screen = pygame.display.set_mode((640, 480))
        self.renderer = Renderer(self.screen, build)
        self.config, self.authenticate, self.play_item = config, authenticate, play_item
        self.prepare_playback = prepare_playback
        self.headers, self.verify = headers, verify
        self.jobs = Jobs()
        self.api = self.artwork = None
        self.rows = Rows([])
        self.pages = []
        self.pending = None
        self.loading = ""
        self.status = error or ""
        self.reporter = None
        self.running = True
        self.home_generation = 0
        self.return_home_refresh = False
        self.repeat_at = 0
        self.direction = (0, 0)
        if config:
            self.start("Connecting to Jellyfin...", lambda: authenticate(config), self.connected)

    def start(self, label, function, done):
        if self.pending:
            self.jobs.cancel(self.pending)
        self.loading = label
        def completed(value, error):
            self.pending = None
            self.loading = ""
            if error:
                self.status = "Could not load. Check the connection and press X to retry."
            else:
                self.status = ""
                done(value)
        self.pending = self.jobs.submit(function, completed)

    def connected(self, credentials):
        token, user = credentials
        self.api = LibraryAPI(self.config, token, user, self.headers(token), self.verify)
        self.artwork = Artwork(self.api, os.path.join(os.path.dirname(os.environ.get(
            "JELLYFIN_CONFIG", "/userdata/roms/ports/jellyfinrg35xx/config.json")), "cache", "artwork"))
        self.refresh()

    def refresh(self):
        if not self.api:
            if self.config:
                self.start("Connecting to Jellyfin...", lambda: self.authenticate(self.config), self.connected)
            return
        self.home_generation += 1
        def ready(views):
            values = [{"title": "My Media", "items": views, "loaded": True},
                      {"title": "Next Up", "fetch": self.api.next_up, "empty": "You are all caught up"},
                      {"title": "Continue Watching", "fetch": self.api.resume, "empty": "No unfinished videos"}]
            for view in views:
                values.append({"title": "Recently Added in " + view.get("Name", "Library"),
                               "fetch": lambda parent=view["Id"]: self.api.latest(parent)})
            self.rows = Rows(values)
        self.start("Loading My Media...", self.api.views, ready)

    def load_row(self, index):
        row = self.rows.values[index]
        if row.get("loaded") or row.get("loading"):
            return
        row["loading"] = True
        generation = self.home_generation
        def done(value, error):
            if generation != self.home_generation:
                return
            row["loading"] = False
            row["loaded"] = True
            row["items"] = value or []
            if error:
                row["error"] = "Could not load this row. X to refresh."
        self.jobs.submit(row["fetch"], done)

    def open_item(self, item, library=False):
        if not item:
            return
        kind = item.get("Type", "")
        if library or item.get("IsFolder") or kind in ("Series", "Season", "Folder", "CollectionFolder", "UserView", "BoxSet"):
            def ready(result):
                items, total, more = result
                portrait = not items or items[0].get("Type") not in ("Episode", "Video", "MusicVideo")
                self.pages.append(dict(kind="list", title=item.get("Name", "Library"), parent=item,
                                       items=items, total=total, more=more, next_start=len(items),
                                       selection=0, portrait=portrait, paging=False))
            self.start("Opening " + item.get("Name", "folder") + "...", lambda: self.api.children(item), ready)
        else:
            self.start("Loading details...", lambda: self.api.detail(item),
                       lambda value: self.pages.append(dict(kind="detail", item=value, options=None, track_options=None)))

    def options_for(self, item):
        streams = ((item.get("MediaSources") or [{}])[0].get("MediaStreams")
                   or item.get("MediaStreams") or [])
        def label(stream):
            return stream.get("DisplayTitle") or stream.get("Language") or stream.get("Codec") or "Unknown"
        audio = [{"index": s.get("Index"), "label": label(s)} for s in streams if s.get("Type") == "Audio"]
        subtitles = [{"index": None, "label": "Off"}] + [{"index": s.get("Index"), "label": label(s)} for s in streams if s.get("Type") == "Subtitle"]
        return {"row": 0, "audio": audio or [{"index": None, "label": "Default"}], "audio_at": 0,
                "subtitles": subtitles, "subtitle_at": 0}

    def more(self, page):
        if not page["more"] or page["paging"]:
            return
        page["paging"] = True
        def done(result, error):
            page["paging"] = False
            if error:
                self.status = "Could not load more titles. Press X to retry."
                return
            items, total, more = result
            known = {item.get("Id") for item in page["items"]}
            page["items"].extend(item for item in items if item.get("Id") not in known)
            page["next_start"] += len(items)
            page["total"], page["more"] = total, bool(more and items)
        self.jobs.submit(lambda: self.api.children(page["parent"], page["next_start"]), done)

    def begin_search(self):
        parent = self.pages[-1].get("parent") if self.pages and self.pages[-1]["kind"] == "list" else None
        self.pages.append(dict(kind="search", parent=parent, query="", alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -",
                               character=0, items=[], total=0, selection=0, searching=False))

    def update_search(self, page):
        query = page["query"].strip()
        page["items"], page["total"], page["selection"] = [], 0, 0
        if not query:
            return
        page["searching"] = True
        def done(result):
            page["searching"] = False
            page["items"], page["total"], _ = result
        self.start("Searching Jellyfin...", lambda: self.api.search(query, page.get("parent")), done)

    def move(self, x, y):
        if self.pending or not self.api:
            return
        if not self.pages:
            self.rows.move(x, y)
            return
        page = self.pages[-1]
        if page["kind"] == "search":
            if x:
                page["character"] = (page["character"] + x) % len(page["alphabet"])
            if y and page["items"]:
                page["selection"] = max(0, min(len(page["items"]) - 1, page["selection"] - y))
            return
        if page["kind"] == "detail" and page.get("options"):
            options = page["options"]
            if y: options["row"] = max(0, min(2, options["row"] - y))
            if x and options["row"] == 1:
                options["audio_at"] = (options["audio_at"] + x) % len(options["audio"])
            if x and options["row"] == 2:
                options["subtitle_at"] = (options["subtitle_at"] + x) % len(options["subtitles"])
            return
        if page["kind"] != "list":
            return
        columns = 4 if page["portrait"] else 3
        page["selection"] = max(0, min(len(page["items"]) - 1, page["selection"] + x - y * columns))
        if len(page["items"]) - page["selection"] <= 8:
            self.more(page)

    def activate(self):
        if self.pending or not self.api:
            return
        if not self.pages:
            self.open_item(self.rows.selected(), self.rows.row == 0)
        elif self.pages[-1]["kind"] == "search":
            page = self.pages[-1]
            page["query"] += page["alphabet"][page["character"]]
            self.update_search(page)
        elif self.pages[-1]["kind"] == "list":
            page = self.pages[-1]
            if page["items"]:
                self.open_item(page["items"][page["selection"]])
        else:
            page = self.pages[-1]
            item = page["item"]
            if item.get("Type") not in ("Movie", "Episode", "Video", "MusicVideo"):
                return
            options = page.get("options") or page.get("track_options")
            if options:
                page["track_options"] = options
            if page.get("options") and options["row"] == 1:
                    options["audio_at"] = (options["audio_at"] + 1) % len(options["audio"]); return
            if page.get("options") and options["row"] == 2:
                    options["subtitle_at"] = (options["subtitle_at"] + 1) % len(options["subtitles"]); return
            if options:
                audio_index = options["audio"][options["audio_at"]]["index"]
                subtitle_index = options["subtitles"][options["subtitle_at"]]["index"]
            else:
                audio_index = subtitle_index = None
            if self.reporter and not self.reporter.finished.is_set():
                self.status = "Saving previous playback..."
                return
            def ready(prepared):
                self.screen, self.status, self.reporter = self.play_item(
                    self.config, self.api.token, self.api.user_id, item, prepared=prepared)
                self.renderer.screen = self.screen
                self.return_home_refresh = True
                self.direction = (0, 0)
                pygame.event.clear()
            self.start("Preparing video...", lambda: self.prepare_playback(
                self.config, self.api.token, self.api.user_id, item, audio_index, subtitle_index), ready)

    def back(self):
        if self.pending:
            self.jobs.cancel(self.pending)
            self.pending = None
            self.loading = ""
        elif self.pages and self.pages[-1].get("options"):
            # Keep the selected streams when returning to the details page.
            self.pages[-1]["track_options"] = self.pages[-1]["options"]
            self.pages[-1]["options"] = None
        elif self.pages:
            self.pages.pop()
            if not self.pages and self.return_home_refresh and not self.reporter:
                self.return_home_refresh = False
                self.refresh()

    def draw(self):
        if not self.api:
            self.renderer.header()
            self.renderer.wrap(self.status or "Connect to your Jellyfin library", 82, 205, 476, 4, self.renderer.font)
            self.renderer.footer("X  Retry     Start  Exit")
        elif not self.pages:
            self.renderer.home(self.rows, self.artwork, self.load_row)
        elif self.pages[-1]["kind"] == "search":
            page = self.pages[-1]
            self.renderer.search(page, self.artwork, bool(self.pending) or page.get("searching"))
        elif self.pages[-1]["kind"] == "list":
            page = self.pages[-1]
            self.renderer.listing(page, self.artwork, bool(self.pending))
            if page["paging"]:
                self.renderer.spinner(606, 418, 7)
        else:
            page = self.pages[-1]
            self.renderer.detail(page["item"], self.artwork, self.status, page.get("options"))
        if self.pending:
            self.renderer.loading(self.loading)
            self.renderer.footer("Loading...     B  Cancel     Start  Exit")
        elif self.status.startswith("Could not") and self.api:
            self.renderer.footer(self.status)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.jobs.poll()
            if self.artwork:
                self.artwork.jobs.poll()
            if self.reporter and self.reporter.finished.is_set():
                self.status = "Progress saved" if self.reporter.stop_ok else "Could not save progress to Jellyfin"
                self.reporter = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.JOYHATMOTION:
                    self.direction = event.value
                    self.move(*self.direction)
                    self.repeat_at = time.monotonic() + 0.35
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button in (9, 10, 11):
                        self.running = False
                    elif event.button == 4:
                        self.back()
                    elif event.button == 3:
                        self.activate()
                        break
                    elif event.button == 6:
                        if self.pages and self.pages[-1]["kind"] == "search":
                            page = self.pages[-1]
                            if page["query"]:
                                page["query"] = page["query"][:-1]
                                self.update_search(page)
                        elif self.pages and self.pages[-1]["kind"] == "detail":
                            page = self.pages[-1]
                            page["options"] = page.get("track_options") or self.options_for(page["item"])
                            page["track_options"] = page["options"]
                        elif self.pages and self.pages[-1]["kind"] == "list":
                            self.more(self.pages[-1])
                        else:
                            self.refresh()
                    elif event.button == 7:
                        if self.pages and self.pages[-1]["kind"] == "search":
                            page = self.pages[-1]
                            if page["items"]:
                                self.open_item(page["items"][page["selection"]])
                        else:
                            self.begin_search()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_RETURN:
                        self.activate()
                        break
                    elif event.key == pygame.K_BACKSPACE:
                        self.back()
                    elif event.key == pygame.K_x and self.pages and self.pages[-1]["kind"] == "search":
                        page = self.pages[-1]
                        if page["query"]:
                            page["query"] = page["query"][:-1]
                            self.update_search(page)
                    elif event.key == pygame.K_y:
                        if self.pages and self.pages[-1]["kind"] == "search":
                            page = self.pages[-1]
                            if page["items"]:
                                self.open_item(page["items"][page["selection"]])
                        else:
                            self.begin_search()
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                        self.move(*{pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0), pygame.K_UP: (0, 1), pygame.K_DOWN: (0, -1)}[event.key])
            if self.direction != (0, 0) and time.monotonic() >= self.repeat_at:
                self.move(*self.direction)
                self.repeat_at = time.monotonic() + 0.15
            self.draw()
            pygame.display.flip()
            clock.tick(30)
        deadline = time.monotonic() + 25
        while self.reporter and not self.reporter.finished.is_set() and time.monotonic() < deadline:
            pygame.event.pump()
            self.renderer.header()
            self.renderer.loading("Saving playback progress...", False)
            pygame.display.flip()
            clock.tick(30)
        pygame.quit()
