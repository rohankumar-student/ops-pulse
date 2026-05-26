  # OpsPulse Dashboard - main entry point
  # Rohan Rudraraju - IT599 Capstone

  from datetime import datetime, timezone

  import pandas as pd
  import streamlit as st

  from opspulse import __version__, auth
  from opspulse.db import connect, init_schema

  st.set_page_config(
      page_title="OpsPulse — NexGen Digital Solutions",
      page_icon="📊",
      layout="wide",
  )

  init_schema()
  sess = auth.require_login()
  auth.render_sidebar(sess)

  st.title("OpsPulse Dashboard")
  st.caption(f"NexGen Digital Solutions  |  build {__version__}  |  logged in as {sess.display} ({sess.role})")

  with connect() as conn:
      services = pd.read_sql_query("SELECT COUNT(*) AS n FROM services", conn).iloc[0]["n"]
      latest_health = pd.read_sql_query(
          """
          SELECT state, COUNT(*) AS n FROM (
              SELECT service_id, state,
                     ROW_NUMBER() OVER (PARTITION BY service_id ORDER BY observed_at DESC) AS rn
              FROM health_status
          ) WHERE rn = 1
          GROUP BY state
          """,
          conn,
      )
      deploys_24h = pd.read_sql_query(
          """
          SELECT outcome, COUNT(*) AS n FROM deployments
          WHERE deployed_at >= datetime('now','-1 day')
          GROUP BY outcome
          """,
          conn,
      )

  states = {row["state"]: row["n"] for _, row in latest_health.iterrows()}
  up = states.get("up", 0)
  degraded = states.get("degraded", 0)
  down = states.get("down", 0)

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Services monitored", int(services))
  c2.metric("Up", up)
  c3.metric("Degraded", degraded, delta=None if not degraded else f"+{degraded}", delta_color="inverse")
  c4.metric("Down", down, delta=None if not down else f"+{down}", delta_color="inverse")

  st.divider()

  left, right = st.columns([2, 1])
  with left:
      st.subheader("Welcome")
      st.markdown(
          """
          OpsPulse brings together **service health**, **API latency**,
          **error rates**, **host resource utilization**, and **deployment events**
          into a single view for the NexGen Digital Solutions engineering team.

          Use the sidebar to navigate between pages:

          - **Service Health** — live up / degraded / down state for all monitored services
          - **API Latency** — p50 / p95 / p99 trends and error rates over the last 10 days
          - **Resources** — CPU, memory, and disk usage across app, db, and cache hosts
          - **Deployments** — recent deployment events and outcomes
          """
      )

  with right:
      st.subheader("Deployments (last 24h)")
      if deploys_24h.empty:
          st.info("No deployments in the last 24 hours.")
      else:
          st.dataframe(deploys_24h, hide_index=True, use_container_width=True)

  st.divider()
  st.caption(
      f"Last refresh: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} • "
      "Polling cadence: 30 minutes • Historical retention: 90 days"
  )
