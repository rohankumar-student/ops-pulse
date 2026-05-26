  # Resources page - CPU, memory, disk per host over time

  import pandas as pd
  import plotly.express as px
  import streamlit as st

  from opspulse import auth
  from opspulse.db import connect

  st.set_page_config(page_title="OpsPulse — Resources", page_icon="🖥️", layout="wide")

  sess = auth.require_login()
  auth.render_sidebar(sess)

  st.title("Resource Utilization")
  st.caption("CPU / memory / disk per host")

  with connect() as conn:
      df = pd.read_sql_query(
          """
          SELECT host_id, observed_at, cpu_pct, mem_pct, disk_pct
          FROM host_resources
          ORDER BY host_id, observed_at
          """,
          conn,
      )

  if df.empty:
      st.warning(
          "No resource data found. Run `python -m opspulse.seed` from the project "
          "root to seed mock data, then refresh."
      )
      st.stop()

  df["observed_at"] = pd.to_datetime(df["observed_at"])

  latest = (
      df.sort_values("observed_at")
      .groupby("host_id")
      .tail(1)
      .reset_index(drop=True)
  )

  st.subheader("Current utilization (latest sample per host)")
  cols = st.columns(3)
  for i, row in latest.iterrows():
      col = cols[i % 3]
      with col:
          with st.container(border=True):
              st.markdown(f"**{row['host_id']}**")
              cc1, cc2, cc3 = st.columns(3)
              cc1.metric("CPU %",  f"{row['cpu_pct']:.0f}")
              cc2.metric("MEM %",  f"{row['mem_pct']:.0f}")
              cc3.metric("DISK %", f"{row['disk_pct']:.0f}")
              st.caption(f"observed {row['observed_at']}")

  st.divider()
  st.subheader("CPU trend (10-day)")
  fig = px.line(df, x="observed_at", y="cpu_pct", color="host_id",
                labels={"observed_at": "Time (UTC)", "cpu_pct": "CPU %"})
  fig.update_layout(height=380, legend_title_text="", margin=dict(t=20, b=10))
  st.plotly_chart(fig, use_container_width=True)

  st.info("Memory and disk trend charts coming in a future update.")
