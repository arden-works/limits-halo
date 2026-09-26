"""Read the signed-in Codex account through a local app-server stdio session."""
import json
import logging
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone

from models import LimitState
from providers.base import LimitProvider


def _find_codex_executable():
    local = os.environ.get("LOCALAPPDATA")
    if local:
        binaries = list((Path(local) / "OpenAI" / "Codex" / "bin").glob("*/codex.exe"))
        if binaries:
            return str(max(binaries, key=lambda path: path.stat().st_mtime))
    return shutil.which("codex.exe") or shutil.which("codex")


def _window(bucket, minutes):
    if bucket is None:
        return None, None
    if not isinstance(bucket, dict) or bucket.get("windowDurationMins") != minutes:
        raise ValueError(f"Invalid {minutes}-minute Codex window")
    percent, reset = bucket.get("usedPercent"), bucket.get("resetsAt")
    if isinstance(percent, bool) or not isinstance(percent, (int, float)):
        raise ValueError("Invalid Codex usage percentage")
    if isinstance(reset, bool) or not isinstance(reset, (int, float)):
        raise ValueError("Invalid Codex reset timestamp")
    return 100 - percent, datetime.fromtimestamp(reset, timezone.utc)


def map_rate_limits(result):
    """Use the core Codex bucket; never mix in another metered allowance."""
    buckets = result.get("rateLimitsByLimitId")
    limits = buckets.get("codex") if isinstance(buckets, dict) else None
    if not isinstance(limits, dict):
        limits = result.get("rateLimits")
    if not isinstance(limits, dict) or limits.get("limitId") not in (None, "codex"):
        raise ValueError("Core Codex rate limits unavailable")
    windows = (limits.get("primary"), limits.get("secondary"))
    by_duration = {item.get("windowDurationMins"): item for item in windows if isinstance(item, dict)}
    five, five_reset = _window(by_duration.get(300), 300)
    week, week_reset = _window(by_duration.get(10080), 10080)
    if five is None and week is None:
        raise ValueError("Codex did not return a supported rate-limit window")
    return LimitState(five, five_reset, week, week_reset, datetime.now(timezone.utc))


class CodexLimitProvider(LimitProvider):
    name = "Codex"

    def __init__(self, executable=None, timeout=12):
        # Prefer the native binary: npm's .cmd shim otherwise adds cmd and Node
        # processes for the lifetime of this lightweight provider.
        self.executable = executable or _find_codex_executable()
        self.timeout = timeout
        self.process = None
        self.messages = None
        self.request_id = 0
        self.reader = None
        self._start_lock = threading.Lock()
        self._stopping = False

    def stop_new_work(self):
        with self._start_lock:
            self._stopping = True

    def _start(self):
        with self._start_lock:
            if self._stopping:
                raise RuntimeError("Codex provider is stopping")
            if not self.executable:
                raise FileNotFoundError("Codex CLI is not installed")
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self.process = subprocess.Popen(
                [self.executable, "app-server"], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0,
                creationflags=creationflags,
            )
            self.messages = queue.Queue()
            process, messages = self.process, self.messages

            def read():
                try:
                    for line in process.stdout:
                        try:
                            messages.put(json.loads(line))
                        except (ValueError, UnicodeDecodeError):
                            logging.debug("Ignoring malformed Codex app-server message")
                finally:
                    messages.put(None)

            self.reader = threading.Thread(target=read, daemon=True, name="codex-app-server-reader")
            self.reader.start()
        self._request("initialize", {"clientInfo": {
            "name": "ai_limit_monitor", "title": "LimitsHalo", "version": "0.1.0-beta"}})
        self._send({"method": "initialized", "params": {}})

    def _send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        self.process.stdin.flush()

    def _request(self, method, params=None):
        self.request_id += 1
        request_id = self.request_id
        message = {"id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                reply = self.messages.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as error:
                raise TimeoutError("Codex app-server did not respond") from error
            if reply is None:
                raise ConnectionError("Codex app-server exited")
            if reply.get("id") != request_id:
                continue
            if "error" in reply:
                detail = reply["error"]
                raise ConnectionError(f"Codex app-server error: {detail.get('code', 'unknown')}")
            return reply["result"]

    def get_state(self):
        try:
            if self.process is None or self.process.poll() is not None:
                self.close()
                self._start()
            return map_rate_limits(self._request("account/rateLimits/read"))
        except Exception:
            self.close()
            raise

    def close(self):
        process, self.process = self.process, None
        if process is not None:
            try:
                process.stdin.close()
            except (OSError, ValueError):
                pass
            if process.poll() is None:
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    if process.poll() is None:
                        process.terminate()
                    try:
                        process.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            if process.stdout is not None:
                process.stdout.close()
        reader, self.reader = self.reader, None
        if reader is not None and reader is not threading.current_thread():
            reader.join(timeout=1)
