  # API Latency page - shows p50/p95/p99 trends and error rates per service

  import pandas as pd
  import plotly.express as px
  import streamlit as st

  from opspulse import auth
  from opspulse.db import connect

  st.set_page_config(page_title="OpsPulse — API Latency", page_icon="📈", layout="wide")

  sess = auth.require_login()
  auth.render_sidebar(sess)

  st.title("API Latency & Error Rate")
  st.caption("p50 / p95 / p99 over the last 10 days")

  with connect() as conn:
      services = pd.read_sql_query(
          "SELECT service_id, display_name FROM services ORDER BY display_name", conn
      )

  if services.empty:
      st.warning(
          "No latency data found. Run `python -m opspulse.seed` from the project "
          "root to seed mock data, then refresh."
      )
      st.stop()

  choice = st.selectbox(
      "Service",
      options=services["service_id"].tolist(),
      format_func=lambda sid: services.set_index("service_id").loc[sid, "display_name"],
  )

  with connect() as conn:
      df = pd.read_sql_query(
          """
          SELECT observed_at, p50_ms, p95_ms, p99_ms, error_rate
          FROM latency_samples
          WHERE service_id = ?
          ORDER BY observed_at
          """,
          conn,
          params=(choice,),
      )

  df["observed_at"] = pd.to_datetime(df["observed_at"])

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("p50 (current)", f"{df['p50_ms'].iloc[-1]:.0f} ms")
  c2.metric("p95 (current)", f"{df['p95_ms'].iloc[-1]:.0f} ms")
  c3.metric("p99 (current)", f"{df['p99_ms'].iloc[-1]:.0f} ms")
  c4.metric("Error rate (current)", f"{df['error_rate'].iloc[-1]:.2f} %")

  melted = df.melt(
      id_vars="observed_at",
      value_vars=["p50_ms", "p95_ms", "p99_ms"],
      var_name="percentile",
      value_name="latency_ms",
  )
  fig = px.line(
      melted,
      x="observed_at",
      y="latency_ms",
      color="percentile",
      labels={"observed_at": "Time (UTC)", "latency_ms": "Latency (ms)"},
      title=f"Latency percentiles — {services.set_index('service_id').loc[choice, 'display_name']}",
  )
  fig.update_layout(legend_title_text="", height=420, margin=dict(t=50, b=10))
  st.plotly_chart(fig, use_container_width=True)

  st.subheader("Error rate over time")
  err_fig = px.area(
      df,
      x="observed_at",
      y="error_rate",
      labels={"observed_at": "Time (UTC)", "error_rate": "Error rate (%)"},
  )
  err_fig.update_layout(height=300, margin=dict(t=20, b=10))
  st.plotly_chart(err_fig, use_container_width=True)

  st.info("Threshold alerting on p99 and error rate is planned as a future enhancement.")
