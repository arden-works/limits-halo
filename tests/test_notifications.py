"""Codex toast detection uses only Windows notification metadata."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from windows.notifications import CodexNotificationWatcher


class NotificationWatcherTests(unittest.TestCase):
    def test_new_codex_toast_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notifications.db"
            with closing(sqlite3.connect(path)) as db:
                db.executescript("""
                    CREATE TABLE NotificationHandler (RecordId INTEGER PRIMARY KEY, PrimaryId TEXT);
                    CREATE TABLE Notification (HandlerId INTEGER, Type TEXT, ArrivalTime INTEGER);
                    INSERT INTO NotificationHandler VALUES (1, 'OpenAI.Codex_2p2nqsd0c76g0!App');
                    INSERT INTO NotificationHandler VALUES (2, 'Another.App_abc!App');
                    INSERT INTO Notification VALUES (1, 'toast', 100);
                """)
                db.commit()
            watcher = CodexNotificationWatcher(path)
            self.assertFalse(watcher.check())  # Old notifications are the baseline.
            with closing(sqlite3.connect(path)) as db:
                db.execute("INSERT INTO Notification VALUES (2, 'toast', 200)")
                db.execute("INSERT INTO Notification VALUES (1, 'badge', 250)")
                db.commit()
            self.assertFalse(watcher.check())
            with closing(sqlite3.connect(path)) as db:
                db.execute("INSERT INTO Notification VALUES (1, 'toast', 300)")
                db.commit()
            self.assertTrue(watcher.check())
            self.assertFalse(watcher.check())


if __name__ == "__main__":
    unittest.main()
