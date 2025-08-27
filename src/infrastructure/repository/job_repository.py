# app/infrastructure/job_repository.py
import sqlite3
from pathlib import Path
from src.domain.Job import Job
from datetime import datetime
from typing import Optional
from src.infrastructure.config.config import DB_PATH

DB_PATH = DB_PATH

class JobRepository:
    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                name TEXT,
                next_run_time TEXT,
                last_run_time TEXT
            )
        """)
        self.conn.commit()

    def upsert_job(self, job: Job):
        """
        Inserta o actualiza un job en la base de datos.

        Si el job ya existe, actualiza los campos `next_run_time` y
        `last_run_time`. Si no existe, lo crea.
        """
        self.conn.execute("""
            INSERT INTO jobs (id, name, next_run_time, last_run_time)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              next_run_time=excluded.next_run_time,
              last_run_time=excluded.last_run_time
        """, (
            job.id,
            job.name,
            job.next_run_time.isoformat() if job.next_run_time else None,
            job.last_run_time.isoformat() if job.last_run_time else None,
        ))
        self.conn.commit()

    def get_jobs(self) -> list[Job]:
        cur = self.conn.execute("SELECT id, name, next_run_time, last_run_time FROM jobs")
        rows = cur.fetchall()
        return [
            Job(
                id=row[0],
                name=row[1],
                next_run_time=datetime.fromisoformat(row[2]) if row[2] else None,
                last_run_time=datetime.fromisoformat(row[3]) if row[3] else None,
            )
            for row in rows
        ]

    def get_job_by_name(self, name: str) -> Optional[Job]:
        cur = self.conn.execute("SELECT id, name, next_run_time, last_run_time FROM jobs WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return Job(
                id=row[0],
                name=row[1],
                next_run_time=datetime.fromisoformat(row[2]) if row[2] else None,
                last_run_time=datetime.fromisoformat(row[3]) if row[3] else None,
            )
        return None
    def get_job_by_id(self, id: str) -> Optional[Job]:
        cur = self.conn.execute("SELECT id, name, next_run_time, last_run_time FROM jobs WHERE id = ?", (id,))
        row = cur.fetchone()
        if row:
            return Job(
                id=row[0],
                name=row[1],
                next_run_time=datetime.fromisoformat(row[2]) if row[2] else None,
                last_run_time=datetime.fromisoformat(row[3]) if row[3] else None,
            )
        return None

    def remove_job(self, id: str):
        self.conn.execute("DELETE FROM jobs WHERE id = ?", (id,))
        self.conn.commit()