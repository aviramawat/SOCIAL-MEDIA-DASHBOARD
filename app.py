import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import os
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from fpdf import FPDF
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Social Media Dashboard", page_icon="📈", layout="wide")

# --- INITIALIZE SESSION STATE ---
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'dark'

# --- PRESTIGE STYLING SYSTEM ---
if st.session_state.get('theme', 'dark') == 'dark':
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        html, body, [class*="css"], .stApp {
            font-family: 'Outfit', sans-serif !important;
            background: linear-gradient(135deg, #0f1219 0%, #151821 100%) !important;
        }
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif !important;
        }
        h1 {
            background: linear-gradient(45deg, #ff7b00, #ffae00, #00d2ff, #0066ff);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: GradientText 10s ease infinite;
            font-weight: 800 !important;
            letter-spacing: -1px;
        }
        @keyframes GradientText {
            0% { background-position: 0% 50% }
            50% { background-position: 100% 50% }
            100% { background-position: 0% 50% }
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.02) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 20px 24px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25) !important;
            backdrop-filter: blur(8px) !important;
            transition: transform 0.3s ease, border-color 0.3s ease !important;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px) !important;
            border-color: rgba(255, 174, 0, 0.4) !important;
        }
        div.stButton > button {
            background: linear-gradient(90deg, #ff7b00 0%, #ffae00 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(255, 123, 0, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button:hover {
            transform: scale(1.03) !important;
            box-shadow: 0 6px 20px rgba(255, 123, 0, 0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        html, body, [class*="css"], .stApp {
            font-family: 'Outfit', sans-serif !important;
            background: linear-gradient(135deg, #f4f6fa 0%, #e9edf5 100%) !important;
        }
        h1, h2, h3 {
            font-family: 'Outfit', sans-serif !important;
        }
        h1 {
            background: linear-gradient(45deg, #ff5e00, #ff9900, #0099ff, #0044ff);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: GradientText 10s ease infinite;
            font-weight: 800 !important;
            letter-spacing: -1px;
        }
        @keyframes GradientText {
            0% { background-position: 0% 50% }
            50% { background-position: 100% 50% }
            100% { background-position: 0% 50% }
        }
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.8) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
            border-radius: 16px !important;
            padding: 20px 24px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.05) !important;
            backdrop-filter: blur(8px) !important;
            transition: transform 0.3s ease, border-color 0.3s ease !important;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px) !important;
            border-color: rgba(255, 94, 0, 0.4) !important;
        }
        div.stButton > button {
            background: linear-gradient(90deg, #ff5e00 0%, #ff9900 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 24px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(255, 94, 0, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button:hover {
            transform: scale(1.03) !important;
            box-shadow: 0 6px 20px rgba(255, 94, 0, 0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE MANAGEMENT ---
DB_PATH = os.path.join(os.path.dirname(__file__), 'social_dashboard.db')

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            followers INTEGER,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            saves INTEGER,
            impressions INTEGER,
            reach INTEGER,
            hashtag TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    conn.close()
    if row:
        user_id, stored_hash = row
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return user_id
    return None

def save_metrics_data(user_id, df):
    conn = get_connection()
    df_copy = df.copy()
    df_copy['user_id'] = user_id
    df_copy.to_sql('metrics', conn, if_exists='append', index=False)
    conn.close()

def get_metrics_data(user_id):
    conn = get_connection()
    query = "SELECT * FROM metrics WHERE user_id = ?"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df

# --- CHART VISUALIZATION ENGINE ---
def plot_engagement_trend(df, time_col='date'):
    fig = px.line(df, x=time_col, y=['likes', 'comments', 'shares', 'saves'],
                  title='Engagement Trends Over Time',
                  labels={'value': 'Count', 'variable': 'Engagement Type', time_col: 'Date'})
    fig.update_layout(template="plotly_dark" if st.session_state.get('theme', 'dark') == 'dark' else "plotly_white")
    return fig

def plot_follower_growth(df):
    fig = px.area(df, x='date', y='followers', title='Follower Growth')
    fig.update_layout(template="plotly_dark" if st.session_state.get('theme', 'dark') == 'dark' else "plotly_white")
    return fig

def plot_top_hashtags(df):
    hashtag_counts = df['hashtag'].value_counts().reset_index()
    hashtag_counts.columns = ['hashtag', 'count']
    fig = px.bar(hashtag_counts, x='hashtag', y='count', title='Top Used Hashtags',
                 color='count', color_continuous_scale='Viridis')
    fig.update_layout(template="plotly_dark" if st.session_state.get('theme', 'dark') == 'dark' else "plotly_white")
    return fig

def generate_wordcloud(df):
    text = " ".join(str(hashtag) for hashtag in df.hashtag.dropna())
    wordcloud = WordCloud(width=800, height=400, background_color='black').generate(text)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    return fig

def plot_engagement_breakdown(df):
    totals = df[['likes', 'comments', 'shares', 'saves']].sum()
    fig = px.pie(names=totals.index, values=totals.values, title='Engagement Breakdown')
    fig.update_layout(template="plotly_dark" if st.session_state.get('theme', 'dark') == 'dark' else "plotly_white")
    return fig

# --- AUTHENTICATION UI ---
def login_register_ui():
    if st.session_state['user_id'] is not None:
        return True

    st.markdown("<h1 style='text-align: center;'>Social Media Analytics Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Please Login or Register</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login"):
                if login_username and login_password:
                    user_id = verify_user(login_username, login_password)
                    if user_id:
                        st.session_state['user_id'] = user_id
                        st.session_state['username'] = login_username
                        st.success(f"Welcome back, {login_username}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.warning("Please enter both username and password.")

        with tab2:
            st.subheader("Register")
            reg_username = st.text_input("Username", key="reg_user")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_conf")
            
            if st.button("Register"):
                if reg_username and reg_password and reg_confirm:
                    if reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    else:
                        success = create_user(reg_username, reg_password)
                        if success:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error("Username already exists.")
                else:
                    st.warning("Please fill out all fields.")
    
    return False

def logout_ui():
    if st.sidebar.button("Logout"):
        st.session_state['user_id'] = None
        st.session_state['username'] = None
        st.rerun()

# --- ANALYTICS VIEWS ENGINE ---
def view_dashboard(df):
    st.title("Main Dashboard")
    if df.empty:
        st.info("No data available. Please upload your CSV data from the Settings page.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        
        total_followers = df['followers'].iloc[-1] if not df.empty else 0
        total_likes = df['likes'].sum()
        total_comments = df['comments'].sum()
        
        total_engagements = df[['likes', 'comments', 'shares', 'saves']].sum().sum()
        total_impressions = df['impressions'].sum()
        engagement_rate = (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
        
        col1.metric("Total Followers", f"{total_followers:,}")
        col2.metric("Total Likes", f"{total_likes:,}")
        col3.metric("Total Comments", f"{total_comments:,}")
        col4.metric("Engagement Rate", f"{engagement_rate:.2f}%")
        
        st.markdown("---")
        st.subheader("Recent Activity Data")
        st.dataframe(df.sort_values(by='date', ascending=False).head(10), use_container_width=True)

def view_engagement(df):
    st.title("Engagement Analytics")
    if df.empty:
        st.info("No data available. Please upload your CSV data from the Settings page.")
    else:
        resample_option = st.radio("Select Timeframe", ["Daily", "Weekly", "Monthly"], horizontal=True)
        
        df_chart = df.copy()
        if resample_option == "Weekly":
            df_chart = df_chart.resample('W-Mon', on='date').sum().reset_index()
        elif resample_option == "Monthly":
            df_chart = df_chart.resample('M', on='date').sum().reset_index()
        
        st.plotly_chart(plot_engagement_trend(df_chart), use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Engagement Breakdown")
            st.plotly_chart(plot_engagement_breakdown(df), use_container_width=True)
        
        with col2:
            st.subheader("Metrics Detail")
            st.dataframe(df[['date', 'likes', 'comments', 'shares', 'saves']].sort_values(by='date', ascending=False), use_container_width=True)

def view_followers(df):
    st.title("Follower Tracking")
    if df.empty:
        st.info("No data available. Please upload your CSV data from the Settings page.")
    else:
        col1, col2 = st.columns(2)
        
        current_followers = df['followers'].iloc[-1]
        previous_followers = df['followers'].iloc[-2] if len(df) > 1 else current_followers
        growth = current_followers - previous_followers
        
        col1.metric("Current Followers", f"{current_followers:,}", delta=int(growth))
        
        st.plotly_chart(plot_follower_growth(df), use_container_width=True)

def view_hashtags(df):
    st.title("Hashtag Analysis")
    if df.empty:
        st.info("No data available. Please upload your CSV data from the Settings page.")
    else:
        st.subheader("Top Performing Hashtags")
        st.plotly_chart(plot_top_hashtags(df), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Hashtag Word Cloud")
        fig = generate_wordcloud(df)
        st.pyplot(fig)

def view_reports(df):
    st.title("Growth Reports")
    if df.empty:
        st.info("No data available to generate reports.")
    else:
        st.subheader("Export Data to CSV")
        
        @st.cache_data
        def convert_df(df_in):
            return df_in.to_csv(index=False).encode('utf-8')
            
        csv = convert_df(df)
        
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='social_media_data.csv',
            mime='text/csv',
        )
        
        st.markdown("---")
        st.subheader("Generate PDF Report")
        
        if st.button("Generate Summary PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, "Social Media Analytics Report", new_x="LMARGIN", new_y="NEXT", align='C')
            
            pdf.set_font("helvetica", "", 12)
            pdf.ln(10)
            
            total_followers = df['followers'].iloc[-1]
            total_likes = df['likes'].sum()
            total_comments = df['comments'].sum()
            
            pdf.cell(0, 10, f"Total Followers: {total_followers}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 10, f"Total Likes: {total_likes}", new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 10, f"Total Comments: {total_comments}", new_x="LMARGIN", new_y="NEXT")
            
            pdf_output = "report.pdf"
            pdf.output(pdf_output)
            
            with open(pdf_output, "rb") as f:
                pdf_bytes = f.read()
                
            st.download_button(
                label="Download PDF Report",
                data=pdf_bytes,
                file_name="social_media_report.pdf",
                mime="application/pdf"
            )
            
            if os.path.exists(pdf_output):
                os.remove(pdf_output)

def view_settings(user_id):
    st.title("Settings")
    
    st.subheader("Data Upload")
    st.markdown("Upload your social media metrics CSV file. The file should contain the following columns: `date, followers, likes, comments, shares, saves, impressions, reach, hashtag`")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            required_columns = ['date', 'followers', 'likes', 'comments', 'shares', 'saves', 'impressions', 'reach', 'hashtag']
            if all(col in df.columns for col in required_columns):
                if st.button("Upload to Database"):
                    save_metrics_data(user_id, df)
                    st.success("Data successfully uploaded to the database!")
                    st.balloons()
            else:
                st.error(f"Missing required columns. Please ensure the CSV has: {', '.join(required_columns)}")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    st.markdown("---")
    st.subheader("Appearance")
    theme = st.selectbox("Select Theme", ["Dark", "Light"], index=0 if st.session_state.get('theme', 'dark') == 'dark' else 1)
    if theme:
        st.session_state['theme'] = theme.lower()
        # st.info(f"Theme set to {theme}. Plots will update on the next render.")

# --- MAIN CONTROLLER ROUTING ---
init_db()

if st.session_state['user_id'] is None:
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

is_logged_in = login_register_ui()

if is_logged_in:
    st.sidebar.title(f"Welcome, {st.session_state.get('username')}!")
    
    menu_selection = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard Overview",
            "Engagement Analytics",
            "Follower Tracking",
            "Hashtag Analysis",
            "Growth Reports",
            "Settings"
        ]
    )
    
    st.sidebar.markdown("---")
    logout_ui()
    
    df = get_metrics_data(st.session_state['user_id'])
    
    if menu_selection == "Dashboard Overview":
        view_dashboard(df)
    elif menu_selection == "Engagement Analytics":
        view_engagement(df)
    elif menu_selection == "Follower Tracking":
        view_followers(df)
    elif menu_selection == "Hashtag Analysis":
        view_hashtags(df)
    elif menu_selection == "Growth Reports":
        view_reports(df)
    elif menu_selection == "Settings":
        view_settings(st.session_state['user_id'])
