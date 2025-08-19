import asyncio
import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = "schedules.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            frequency INTEGER NOT NULL,
            last_run TIMESTAMP
        )
    """)

    conn.execute(
        """
        DELETE FROM schedules
        WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM schedules GROUP BY name
        )
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_schedules_name ON schedules(name)")
    conn.commit()
    conn.close()

def add_schedule(name: str, frequency_seconds: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO schedules (name, frequency, last_run)
        VALUES (?, ?, NULL)
        ON CONFLICT(name) DO UPDATE SET frequency=excluded.frequency
        """,
        (name, frequency_seconds),
    )
    conn.commit()
    conn.close()

def get_schedules():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, name, frequency, last_run FROM schedules").fetchall()
    conn.close()
    return rows


def update_last_run(schedule_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE schedules SET last_run = ? WHERE id = ?",
        (datetime.now(timezone.utc).isoformat(), schedule_id)
    )
    conn.commit()
    conn.close()
import asyncio
from datetime import datetime, timezone, timedelta

async def scheduler_loop(task_callback):
    try:
        while True:
            now = datetime.now(timezone.utc)
            for (id_, name, freq, last_run) in get_schedules():
                if not freq or freq <= 0:
                    continue
                try:
                    last_dt = None if not last_run else datetime.fromisoformat(last_run)
                    if (last_dt is None) or (now >= last_dt + timedelta(seconds=freq)):
                        await task_callback()
                        update_last_run(id_)
                except Exception as e:
                    print(f"[scheduler] job {name} failed: {e}")
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        print("[scheduler] cancelled, exiting")
        return