  # auth.py - simple login/session handling for OpsPulse
  # using Streamlit session_state since this is a prototype
  # real deployment would need SSO or at minimum hashed credentials

  from dataclasses import dataclass

  import streamlit as st

  # hardcoded demo accounts - fine for capstone, not for production
  DEMO_USERS = {
      "viewer":   {"password": "viewer123",   "role": "viewer",        "display": "V. Viewer"},
      "operator": {"password": "operator123", "role": "operator",      "display": "O. Operator"},
      "admin":    {"password": "admin123",    "role": "administrator", "display": "A. Admin"},
  }


  @dataclass
  class Session:
      username: str
      role: str
      display: str


  def current():
      if not st.session_state.get("authenticated"):
          return None
      return Session(
          username=st.session_state.get("username", ""),
          role=st.session_state.get("role", "viewer"),
          display=st.session_state.get("display", ""),
      )


  def require_login():
      sess = current()
      if sess is None:
          _render_login()
          st.stop()
      return sess


  def _render_login():
      st.title("OpsPulse — Sign in")
      st.caption("Capstone demo. Use one of the seeded role accounts below.")
      with st.form("login", clear_on_submit=False):
          u = st.text_input("Username")
          p = st.text_input("Password", type="password")
          ok = st.form_submit_button("Sign in")
      if ok:
          record = DEMO_USERS.get(u)
          if record and record["password"] == p:
              st.session_state["authenticated"] = True
              st.session_state["username"] = u
              st.session_state["role"] = record["role"]
              st.session_state["display"] = record["display"]
              st.rerun()
          else:
              st.error("Invalid credentials.")
      with st.expander("Demo accounts"):
          st.markdown(
              "- **viewer / viewer123** — read-only\n"
              "- **operator / operator123** — read + mute alerts + edit thresholds\n"
              "- **admin / admin123** — full access incl. identity-mapped audit"
          )


  def render_sidebar(sess):
      with st.sidebar:
          st.markdown(f"**Signed in:** {sess.display}")
          st.markdown(f"**Role:** `{sess.role}`")
          if st.button("Sign out"):
              for k in ["authenticated", "username", "role", "display"]:
                  st.session_state.pop(k, None)
              st.rerun()
