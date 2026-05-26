  # db.py - handles SQLite setup and connection for OpsPulse
  # keeping it simple for the prototype; PostgreSQL would replace this in prod

  import sqlite3
  from pathlib import Path

  DB_PATH = Path(__file__).resolve().parent.parent / "data" / "opspulse.db"

  SCHEMA = """
  CREATE TABLE IF NOT EXISTS services (
      service_id   TEXT PRIMARY KEY,
      display_name TEXT NOT NULL,
      tier         TEXT NOT NULL,
      region       TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS health_status (
      service_id TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      state      TEXT NOT NULL CHECK(state IN ('up','degraded','down')),
      PRIMARY KEY (service_id, observed_at)
  );

  CREATE TABLE IF NOT EXISTS latency_samples (
      service_id TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      p50_ms REAL NOT NULL,
      p95_ms REAL NOT NULL,
      p99_ms REAL NOT NULL,
      error_rate REAL NOT NULL,
      PRIMARY KEY (service_id, observed_at)
  );

  CREATE TABLE IF NOT EXISTS host_resources (
      host_id TEXT NOT NULL,
      observed_at TEXT NOT NULL,
      cpu_pct REAL NOT NULL,
      mem_pct REAL NOT NULL,
      disk_pct REAL NOT NULL,
      PRIMARY KEY (host_id, observed_at)
  );

  CREATE TABLE IF NOT EXISTS deployments (
      deploy_id   TEXT PRIMARY KEY,
      service_id  TEXT NOT NULL,
      deployed_at TEXT NOT NULL,
      version     TEXT NOT NULL,
      outcome     TEXT NOT NULL CHECK(outcome IN ('success','rolled_back','failed'))
  );
  """


  def connect():
      DB_PATH.parent.mkdir(parents=True, exist_ok=True)
      conn = sqlite3.connect(DB_PATH)
      conn.row_factory = sqlite3.Row
      return conn


  def init_schema():
      with connect() as conn:
          conn.executescript(SCHEMA)
          conn.commit()


  def row_count(table):
      with connect() as conn:
          cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
          return cur.fetchone()[0]
