  # seed.py - generates mock telemetry data for the OpsPulse demo
  # run this once before starting the dashboard: python -m opspulse.seed

  import math
  import random
  from datetime import datetime, timedelta, timezone

  from .db import connect, init_schema

  SERVICES = [
      ("svc-auth",      "Auth API",              "tier-0", "us-east-1"),
      ("svc-billing",   "Billing API",           "tier-0", "us-east-1"),
      ("svc-catalog",   "Catalog API",           "tier-1", "us-east-1"),
      ("svc-cart",      "Cart Service",          "tier-1", "us-east-1"),
      ("svc-checkout",  "Checkout API",          "tier-0", "us-east-1"),
      ("svc-orders",    "Order Service",         "tier-0", "us-east-1"),
      ("svc-inventory", "Inventory Service",     "tier-1", "us-west-2"),
      ("svc-search",    "Search Service",        "tier-2", "us-west-2"),
      ("svc-notify",    "Notification Service",  "tier-2", "us-east-1"),
      ("svc-recs",      "Recommendation Engine", "tier-2", "us-west-2"),
      ("svc-fraud",     "Fraud Detection",       "tier-1", "us-east-1"),
      ("svc-reports",   "Reporting API",         "tier-2", "us-east-1"),
  ]

  HOSTS = [
      "host-app-01", "host-app-02", "host-app-03",
      "host-db-01",  "host-db-02",
      "host-cache-01",
  ]

  DAYS_OF_HISTORY = 10
  SAMPLE_INTERVAL_MIN = 30


  def _iter_timestamps(now):
      start = now - timedelta(days=DAYS_OF_HISTORY)
      samples_per_day = (24 * 60) // SAMPLE_INTERVAL_MIN
      total = samples_per_day * DAYS_OF_HISTORY
      return [
          (start + timedelta(minutes=i * SAMPLE_INTERVAL_MIN)).isoformat(timespec="seconds")
          for i in range(total)
      ]


  def _latency_for(t, base_p50, jitter, incident):
      diurnal = 1.0 + 0.25 * math.sin(2 * math.pi * (t % 48) / 48.0)
      p50 = base_p50 * diurnal + random.uniform(-jitter, jitter)
      p95 = p50 * (2.3 + random.uniform(-0.2, 0.2))
      p99 = p50 * (4.1 + random.uniform(-0.4, 0.4))
      err = max(0.0, random.gauss(0.6, 0.3))
      if incident:
          p50 *= 2.5
          p95 *= 3.0
          p99 *= 3.8
          err += random.uniform(2.0, 5.0)
      return round(p50, 1), round(p95, 1), round(p99, 1), round(err, 2)


  def seed():
      random.seed(20260512)
      now = datetime.now(timezone.utc).replace(microsecond=0)
      init_schema()

      with connect() as conn:
          conn.executescript("""
              DELETE FROM services;
              DELETE FROM health_status;
              DELETE FROM latency_samples;
              DELETE FROM host_resources;
              DELETE FROM deployments;
          """)
          conn.executemany(
              "INSERT INTO services VALUES (?,?,?,?)", SERVICES
          )

          timestamps = _iter_timestamps(now)

          incident_windows = {}
          for sid, *_ in SERVICES:
              anchor = random.randint(len(timestamps) // 4, len(timestamps) - 8)
              incident_windows[sid] = set(range(anchor, anchor + 4))
          tail = len(timestamps)
          incident_windows["svc-search"] |= set(range(tail - 3, tail))
          incident_windows["svc-recs"]   |= set(range(tail - 2, tail))
          incident_windows["svc-notify"] |= set(range(tail - 4, tail))

          health_rows = []
          latency_rows = []
          for sid, name, tier, region in SERVICES:
              base_p50 = {"tier-0": 65, "tier-1": 110, "tier-2": 180}[tier]
              jitter = base_p50 * 0.18
              for ti, ts in enumerate(timestamps):
                  incident = ti in incident_windows[sid]
                  p50, p95, p99, err = _latency_for(ti, base_p50, jitter, incident)
                  latency_rows.append((sid, ts, p50, p95, p99, err))
                  if incident:
                      tail_start = len(timestamps) - 4
                      if ti >= tail_start and sid == "svc-notify":
                          state = "down"
                      elif ti >= tail_start and sid in ("svc-search", "svc-recs"):
                          state = "degraded"
                      else:
                          state = "down" if err > 4.5 else "degraded"
                  else:
                      state = "up"
                  health_rows.append((sid, ts, state))

          conn.executemany(
              "INSERT INTO health_status VALUES (?,?,?)", health_rows
          )
          conn.executemany(
              "INSERT INTO latency_samples VALUES (?,?,?,?,?,?)", latency_rows
          )

          host_rows = []
          for host in HOSTS:
              base_cpu = random.uniform(25, 55)
              base_mem = random.uniform(40, 70)
              base_disk = random.uniform(35, 60)
              for ti, ts in enumerate(timestamps):
                  diurnal = 1.0 + 0.20 * math.sin(2 * math.pi * (ti % 48) / 48.0)
                  cpu = min(99.0, max(2.0, base_cpu * diurnal + random.uniform(-6, 6)))
                  mem = min(99.0, max(2.0, base_mem + random.uniform(-4, 4)))
                  disk = min(99.0, max(2.0, base_disk + ti * 0.005))
                  host_rows.append((host, ts, round(cpu, 1), round(mem, 1), round(disk, 1)))
          conn.executemany(
              "INSERT INTO host_resources VALUES (?,?,?,?,?)", host_rows
          )

          deploy_rows = []
          for n in range(18):
              sid = random.choice([s[0] for s in SERVICES])
              ts_idx = random.randint(0, len(timestamps) - 1)
              ts = timestamps[ts_idx]
              version = f"v1.{random.randint(0, 9)}.{random.randint(0, 30)}"
              outcome = random.choices(
                  ["success", "rolled_back", "failed"], weights=[0.78, 0.15, 0.07]
              )[0]
              deploy_rows.append((f"dep-{n+1:03d}", sid, ts, version, outcome))
          conn.executemany(
              "INSERT INTO deployments VALUES (?,?,?,?,?)", deploy_rows
          )

          conn.commit()

      from .db import row_count
      print("Seeded:")
      for t in ["services", "health_status", "latency_samples", "host_resources", "deployments"]:
          print(f"  {t:18s} {row_count(t):>6d} rows")


  if __name__ == "__main__":
      seed()
