import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


def new_id():
    return uuid4().hex


def encode(value):
    return json.dumps(value, ensure_ascii=False)


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS branches (
                    id TEXT PRIMARY KEY, game_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT, revision INTEGER NOT NULL DEFAULT 0,
                    snapshot TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY, branch_id TEXT NOT NULL REFERENCES branches(id),
                    label TEXT NOT NULL, revision INTEGER NOT NULL, snapshot TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE TABLE IF NOT EXISTS private_settings (
                    branch_id TEXT PRIMARY KEY REFERENCES branches(id),
                    ending TEXT NOT NULL, seed TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS access_attempts (
                    id TEXT PRIMARY KEY, branch_id TEXT NOT NULL UNIQUE REFERENCES branches(id),
                    game_id TEXT NOT NULL, revision INTEGER NOT NULL,
                    request_hash TEXT NOT NULL, request_json TEXT NOT NULL, resolution TEXT NOT NULL,
                    decision TEXT NOT NULL, before_snapshot TEXT NOT NULL,
                    status TEXT NOT NULL, receipt TEXT
                );
                CREATE TABLE IF NOT EXISTS exports (
                    id TEXT PRIMARY KEY, branch_id TEXT NOT NULL REFERENCES branches(id),
                    attempt_id TEXT NOT NULL REFERENCES access_attempts(id), kind TEXT NOT NULL,
                    payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                    directory TEXT, error TEXT
                );
            """)

    @contextmanager
    def connect(self, write=False):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def view(row):
        return {k: row[k] for k in ("id", "game_id", "parent_checkpoint_id", "revision", "created_at")} | {"state": json.loads(row["snapshot"])}
