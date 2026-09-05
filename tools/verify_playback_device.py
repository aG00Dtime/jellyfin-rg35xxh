"""Run explicitly on KNULLI. Tests use a local generated clip, not library media."""
import argparse
import json
import logging
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import parse_qs, urlsplit

APP = Path(os.environ.get("JELLYFIN_APP_DIR", "/userdata/roms/ports/jellyfinrg35xx"))
sys.path.insert(0, str(APP))
from playback import ControllerInput, InputDecoder, MpvIPC, PlaybackReporter, PlaybackSession


def rescue(pid):
    import jellyfin_rg35xx as app
    cmd = Path(f"/proc/{pid}/cmdline").read_bytes().decode().split("\0")
    assert Path(cmd[0]).name == "mpv", "Target is not mpv"
    ipc_path = next(v.split("=", 1)[1] for v in cmd if v.startswith("--input-ipc-server=/tmp/jellyfin-mpv-"))
    config, error = app.load_config()
    assert config, error
    media_url = next(v for v in cmd if v.startswith(config["serverUrl"].rstrip("/") + "/Videos/"))
    parts = urlsplit(media_url)
    item_id = parts.path.split("/Videos/", 1)[1].split("/")[0]
    params = parse_qs(parts.query)
    token = next(v.split("X-Emby-Token: ", 1)[1] for v in cmd if v.startswith("--http-header-fields=X-Emby-Token: "))
    ipc = MpvIPC(ipc_path)
    assert ipc.connect(), "Cannot recover player position"
    ipc.command("get_property", "time-pos", property_name="time-pos")
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and "time-pos" not in ipc.properties:
        ipc.poll()
        time.sleep(0.02)
    ticks = ipc.position_ticks(0)
    session_id = Path(ipc_path).name.removeprefix("jellyfin-mpv-").removesuffix(".sock")
    # Capture/report the abandoned movie position before releasing its display.
    try:
        app.report_playing(config, token, None, {"Id": item_id}, session_id, ticks,
                           event="stopped", play_method="Transcode" if "m3u8" in parts.path else "DirectPlay",
                           media_source_id=params.get("MediaSourceId", [item_id])[0])
        print("RESCUE_PROGRESS_SAVED seconds=", ticks / 10000000, flush=True)
    finally:
        try:
            ipc.command("quit")
            ipc.poll()
        except OSError:
            pass
        ipc.close()
        time.sleep(0.5)
        if Path(f"/proc/{pid}/cmdline").exists():
            # Recheck exact identity before signalling; never target all players.
            current = Path(f"/proc/{pid}/cmdline").read_bytes()
            if ipc_path.encode() in current:
                os.kill(pid, signal.SIGTERM)
        print("RESCUE_QUIT_SENT", flush=True)


def inject(kind, code, value):
    path = next(p for p in Path("/sys/class/input").glob("event*")
                if (p / "device/name").read_text().strip() == "Anbernic RG35XX-H Controller")
    with open("/dev/input/" + path.name, "wb", buffering=0) as device:
        device.write(InputDecoder.EVENT.pack(0, 0, kind, code, value))
        device.write(InputDecoder.EVENT.pack(0, 0, 0, 0, 0))


def press(code):
    inject(1, code, 1)
    inject(1, code, 0)


def test_session(clip, stop_code, exercise_seek=False):
    controls = ControllerInput()
    sent = []
    reporter = PlaybackReporter(lambda *args: sent.append(args))
    path = f"/tmp/jellyfin-mpv-verify-{os.getpid()}-{stop_code}.sock"
    session = PlaybackSession(["mpv", "--no-config", "--really-quiet", "--fullscreen",
                               "--force-window=yes", "--input-terminal=no",
                               "--input-default-bindings=no", "--input-vo-keyboard=no",
                               "--volume=0", "--osd-font=DejaVu Sans", "--osd-font-size=22",
                               "--input-ipc-server=" + path, str(clip)],
                              path, 0, reporter, controls)
    observations = {}
    driver_errors = []
    def wait_for(predicate, label, seconds=5):
        deadline = time.monotonic() + seconds
        while not predicate() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not predicate():
            driver_errors.append(label)
    def drive():
        deadline = time.monotonic() + 10
        while not session.started and time.monotonic() < deadline:
            time.sleep(0.05)
        if session.started:
            if exercise_seek:
                wait_for(lambda: session.position_ticks > 0, "initial position")
                before = session.position_ticks
                inject(3, 16, 1)
                inject(3, 16, 0)
                wait_for(lambda: session.position_ticks > before + 90000000, "seek right")
                observations["right"] = session.position_ticks
                inject(3, 16, -1)
                inject(3, 16, 0)
                wait_for(lambda: session.position_ticks < observations["right"] - 60000000, "seek left")
                observations["left"] = session.position_ticks
                press(309)
                wait_for(lambda: session.position_ticks > observations["left"] + 250000000, "shoulder seek")
                observations["shoulder"] = session.position_ticks
                press(304)
                wait_for(lambda: session.paused, "pause")
                observations["paused"] = session.paused
                press(304)
            time.sleep(0.3)
        observations["stop_time"] = time.monotonic()
        press(stop_code)
        # A failed test must also clean up; do not leave another player behind.
        time.sleep(2)
        if session.player and session.player.poll() is None:
            session.player.terminate()
    driver = threading.Thread(target=drive, daemon=True)
    driver.start()
    session.run()
    latency = time.monotonic() - observations.get("stop_time", time.monotonic())
    assert session.started, "Test clip never loaded"
    assert not driver_errors, driver_errors
    assert latency < 1.5, f"Stop took {latency:.2f}s"
    assert session.player.poll() is not None, "Player was orphaned"
    assert reporter.finished.wait(1), "Stop reporting did not finish"
    assert sent[0][0] == "started" and sent[-1][0] == "stopped", sent
    assert sent[-1][1] == session.position_ticks and session.position_ticks > 0, sent
    if exercise_seek:
        assert observations["right"] > 90000000, observations
        assert observations["left"] < observations["right"] - 60000000, observations
        assert observations["shoulder"] > observations["left"] + 250000000, observations
        assert observations["paused"], observations
    print(json.dumps({"stop_code": stop_code, "stop_latency_seconds": round(latency, 3),
                      "final_seconds": round(session.position_ticks / 10000000, 3),
                      "seek_pause_verified": exercise_seek, "child_reaped": True}), flush=True)
    driver.join(3)


def test_ui_return(clip):
    """Exercise production play_item with pygame and real HTTP reports to a stub."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from unittest.mock import patch
    import jellyfin_rg35xx as app
    import pygame
    received = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if self.path.startswith("/Items/"):
                value = json.dumps({"MediaSources": []}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(value)))
                self.end_headers()
                self.wfile.write(value)
            else:
                received.append((self.path, body))
                self.send_response(204)
                self.end_headers()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    class LocalSession(PlaybackSession):
        def __init__(self, args, *values, **kwargs):
            args[-1] = str(clip)
            super().__init__(args, *values, **kwargs)
            def drive():
                deadline = time.monotonic() + 15
                while not self.started and time.monotonic() < deadline:
                    time.sleep(0.05)
                time.sleep(6)
                press(305)
                time.sleep(2)
                if self.player and self.player.poll() is None:
                    self.player.terminate()
            threading.Thread(target=drive, daemon=True).start()
    pygame.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
    for joystick in joysticks:
        joystick.init()
    pygame.display.set_mode((640, 480))
    item = {"Id": "local-verification", "Name": "Local test clip", "UserData": {}}
    try:
        with patch.object(app, "PlaybackSession", LocalSession):
            screen, status, reporter = app.play_item(
                {"serverUrl": f"http://127.0.0.1:{server.server_port}"}, "test-token", "test-user", item)
        assert screen.get_size() == (640, 480), "UI display did not return"
        assert reporter.finished.wait(3) and reporter.stop_ok, "Final HTTP report failed"
        assert [path for path, _ in received] == ["/Sessions/Playing", "/Sessions/Playing/Progress", "/Sessions/Playing/Stopped"], received
        assert received[-1][1]["PositionTicks"] > 50000000, received
        assert item["UserData"]["PlaybackPositionTicks"] == received[-1][1]["PositionTicks"]
        font = pygame.font.Font("/usr/share/fonts/dejavu/DejaVuSans.ttf", 22)
        screen.fill((12, 16, 25))
        screen.blit(font.render("Playback closed. Library display restored.", True, (0, 164, 220)), (55, 225))
        pygame.display.flip()
        pygame.event.clear()
        press(304)
        deadline = time.monotonic() + 2
        button = None
        while time.monotonic() < deadline and button is None:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    button = event.button
            time.sleep(0.02)
        assert button == 3, f"UI controller not restored, A button={button}"
        pygame.image.save(screen, str(clip.parent / "ui-return.png"))
        print("UI_RETURN_OK A_BUTTON=3 HTTP_START_PROGRESS_STOP_OK", flush=True)
    finally:
        pygame.quit()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["rescue", "test", "ui"])
    parser.add_argument("value")
    options = parser.parse_args()
    if options.mode == "rescue":
        rescue(int(options.value))
    elif options.mode == "test":
        test_session(Path(options.value), 305, exercise_seek=True)
        test_session(Path(options.value), 311)
        test_session(Path(options.value), 310)
    else:
        test_ui_return(Path(options.value))
