"""Read only Codex toast arrival metadata from the local Windows notification store.

The Windows notification listener API requires a packaged app capability. This
small optional adapter never reads notification payloads or changes the store.
"""
import os
from pathlib import Path
import sqlite3
from contextlib import closing


def notification_db_path():
    return Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Notifications" / "wpndatabase.db"


class CodexNotificationWatcher:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else notification_db_path()
        self.last_arrival = None

    def check(self):
        """Return true only for a Codex toast newer than the first observation."""
        with closing(sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=1)) as db:
            row = db.execute("""
                SELECT MAX(n.ArrivalTime)
                FROM Notification AS n
                JOIN NotificationHandler AS h ON h.RecordId = n.HandlerId
                WHERE n.Type = 'toast'
                  AND h.PrimaryId LIKE 'OpenAI.Codex\\_%!App' ESCAPE '\\'
            """).fetchone()
        latest = row[0]
        if latest is None:
            return False
        if self.last_arrival is None or latest < self.last_arrival:
            self.last_arrival = latest
            return False
        if latest > self.last_arrival:
            self.last_arrival = latest
            return True
        return False
