
  # OpsPulse Dashboard

  A web-based operational monitoring dashboard built with Python and Streamlit for NexGen Digital Solutions. Developed as the IT599 capstone project at Purdue Global (IT Specialist track).

  ## What it does

  OpsPulse consolidates five key signals into a single browser-based view:

  - **Service Health** — live up / degraded / down status for monitored services
  - **API Latency** — p50 / p95 / p99 percentile trends and error rates
  - **Resource Utilization** — CPU, memory, and disk usage per host
  - **Deployment Events** — recent deployments with version and outcome

  Role-based access control (viewer, operator, administrator) is enforced across all pages.

  ## Stack

  - Python 3.11+
  - Streamlit
  - SQLite (prototype)
  - Plotly

  ## Quick start

  ```bash
  pip install streamlit plotly pandas
  python -m opspulse.seed
  streamlit run streamlit_app.py

  App runs on http://localhost:8501

  Demo accounts

  ┌──────────┬─────────────┬────────────────────┐
  │ Username │  Password   │        Role        │
  ├──────────┼─────────────┼────────────────────┤
  │ viewer   │ viewer123   │ Read-only          │
  ├──────────┼─────────────┼────────────────────┤
  │ operator │ operator123 │ Read + mute alerts │
  ├──────────┼─────────────┼────────────────────┤
  │ admin    │ admin123    │ Full access        │
  └──────────┴─────────────┴────────────────────┘

  Project layout

  OpsPulse/
  ├── streamlit_app.py        # home page / entry point
  ├── opspulse/
  │   ├── __init__.py
  │   ├── auth.py             # session-based login
  │   ├── db.py               # SQLite schema and connection
  │   └── seed.py             # mock telemetry generator (10 days)
  └── pages/
      ├── 1_Service_Health.py
      ├── 2_API_Latency.py
      ├── 3_Resources.py
      └── 4_Deployments.py

  Author

  Rohan Rudraraju — IT599 Capstone, Purdue Global MSIT, 2026
