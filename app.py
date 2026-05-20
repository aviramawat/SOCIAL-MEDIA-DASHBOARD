import streamlit as st
from database.db_manager import init_db
from components.auth import login_register_ui, logout_ui

st.set_page_config(page_title="Social Media Dashboard", page_icon="📈", layout="wide")

# Initialize database
init_db()

# Check authentication
is_logged_in = login_register_ui()

if is_logged_in:
    st.sidebar.title(f"User: {st.session_state.get('username')}")
    logout_ui()
    
    st.success("You are logged in! Please select a page from the sidebar to view your analytics.")
    
    # Hide the default app.py page content when logged in, since we use multipage
    # But we can also show a quick welcome or redirect
    st.markdown("### Welcome to the Social Media Analytics Dashboard!")
    st.markdown("Use the navigation menu on the left to explore your engagement, followers, and hashtags.")
else:
    # If not logged in, hide the sidebar pages using CSS or Streamlit config
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
