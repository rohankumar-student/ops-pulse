  # Deployments page - shows recent deployment events with version and outcome
  # engineer-level attribution is admin-only per the RBAC policy

  import pandas as pd
  import streamlit as st

  from opspulse import auth
  from opspulse.db import connect

  st.set_page_config(page_title="OpsPulse — Deployments", page_icon="🚀", layout="wide")

  sess = auth.require_login()
  auth.render_sidebar(sess)

  st.title("Deployment Events")
  st.caption("Recent deployments, version, and outcome")

  with connect() as conn:
      df = pd.read_sql_query(
          """
          SELECT d.deploy_id, d.deployed_at, s.display_name AS service,
                 d.version, d.outcome
          FROM deployments d
          JOIN services s ON s.service_id = d.service_id
          ORDER BY d.deployed_at DESC
          """,
          conn,
      )

  if df.empty:
      st.warning(
          "No deployment data found. Run `python -m opspulse.seed` from the "
          "project root to seed mock data, then refresh."
      )
      st.stop()

  counts = df["outcome"].value_counts().reindex(
      ["success", "rolled_back", "failed"], fill_value=0
  )
  c1, c2, c3 = st.columns(3)
  c1.metric("Successful", int(counts["success"]))
  c2.metric("Rolled back", int(counts["rolled_back"]))
  c3.metric("Failed", int(counts["failed"]))

  st.dataframe(df, hide_index=True, use_container_width=True)

  if sess.role == "administrator":
      st.success("Administrator view: engineer attribution will be available once the audit log is wired up.")
  else:
      st.info("Engineer-level attribution is restricted to administrator accounts.")
