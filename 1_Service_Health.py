  # Service Health page - shows current up/degraded/down state for all services

  import pandas as pd
  import streamlit as st

  from opspulse import auth
  from opspulse.db import connect

  st.set_page_config(page_title="OpsPulse — Service Health", page_icon="🟢", layout="wide")

  sess = auth.require_login()
  auth.render_sidebar(sess)

  st.title("Service Health")
  st.caption("Latest observed state per service • polling cadence: 30 minutes")

  with connect() as conn:
      df = pd.read_sql_query(
          """
          SELECT s.service_id, s.display_name, s.tier, s.region,
                 h.state, h.observed_at
          FROM services s
          JOIN (
              SELECT service_id, state, observed_at,
                     ROW_NUMBER() OVER (PARTITION BY service_id ORDER BY observed_at DESC) AS rn
              FROM health_status
          ) h ON h.service_id = s.service_id AND h.rn = 1
          ORDER BY
            CASE h.state WHEN 'down' THEN 0 WHEN 'degraded' THEN 1 ELSE 2 END,
            s.tier, s.display_name
          """,
          conn,
      )

  if df.empty:
      st.warning(
          "No health data found. Run `python -m opspulse.seed` from the project "
          "root to seed mock data, then refresh."
      )
      st.stop()

  state_chip = {
      "up":       ":green[● UP]",
      "degraded": ":orange[● DEGRADED]",
      "down":     ":red[● DOWN]",
  }

  cols = st.columns(4)
  for i, row in df.iterrows():
      col = cols[i % 4]
      with col:
          with st.container(border=True):
              st.markdown(f"**{row['display_name']}**")
              st.markdown(state_chip[row["state"]])
              st.caption(f"`{row['service_id']}` • {row['tier']} • {row['region']}")
              st.caption(f"observed {row['observed_at']}")

  st.divider()

  summary = df.groupby("state").size().reindex(["up", "degraded", "down"], fill_value=0)
  m1, m2, m3 = st.columns(3)
  m1.metric("Up", int(summary["up"]))
  m2.metric("Degraded", int(summary["degraded"]))
  m3.metric("Down", int(summary["down"]))

  with st.expander("Raw observations"):
      st.dataframe(df, hide_index=True, use_container_width=True)
