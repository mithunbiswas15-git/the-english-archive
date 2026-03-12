import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_quill import st_quill

# --- DATABASE SETUP ---
conn = sqlite3.connect('lit_archive.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY, title TEXT, content TEXT, syllabus TEXT, status TEXT, date TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, article_id INTEGER, student_info TEXT, message TEXT, date TEXT)')
conn.commit()

# --- THE BEAUTIFIED SCHOLARLY THEME ---
st.set_page_config(page_title="The English Archive", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Montserrat:wght@300;600&display=swap');

    .main { background-color: #fdfaf3; }
    
    /* Typography */
    html, body, [class*="css"]  {
        font-family: 'Libre Baskerville', serif;
        color: #2c3e50;
    }
    
    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, #1a5e63 0%, #0d2f31 100%);
        padding: 60px 20px;
        border-radius: 15px;
        text-align: center;
        color: #ffffff;
        margin-bottom: 40px;
        box-shadow: 0 10px 30px rgba(26, 94, 99, 0.2);
    }
    
    .hero h1 { 
        font-family: 'Montserrat', sans-serif;
        font-weight: 600;
        letter-spacing: 5px;
        text-transform: uppercase;
        font-size: 3rem !important;
        color: #f4d03f !important; /* Gold Title */
        margin-bottom: 10px;
    }

    /* Article Cards */
    .article-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 12px;
        border-left: 5px solid #1a5e63;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    
    .article-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }

    /* Mission Box */
    .mission-container {
        border: 2px solid #b8860b;
        padding: 30px;
        margin-top: -60px;
        background: white;
        border-radius: 10px;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }

    /* Buttons */
    .stButton>button {
        background: #1a5e63;
        color: white;
        border-radius: 5px;
        padding: 10px 25px;
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
        border: none;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background: #b8860b;
        color: white;
    }

    /* Hide Sidebar */
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- SESSION STATE ---
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'admin_mode' not in st.session_state: st.session_state.admin_mode = "Manage Archive"
    if 'edit_title' not in st.session_state: st.session_state.edit_title = ""
    if 'edit_syllabus' not in st.session_state: st.session_state.edit_syllabus = ""
    if 'edit_content' not in st.session_state: st.session_state.edit_content = ""

    # --- NAVIGATION ---
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        choice = st.segmented_control("Nav", ["🏠 Archive", "🔐 Repository"], default="🏠 Archive", key="main_nav", label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- PUBLIC VIEW ---
    if choice == "🏠 Archive":
        # Hero Section
        st.markdown("""
            <div class="hero">
                <h1>The English Archive</h1>
                <p style='letter-spacing: 2px; font-family:Montserrat; font-weight:300;'>RECLAIMING THE MARGINS</p>
            </div>
        """, unsafe_allow_html=True)

        search_query = st.text_input("🔍 Search Archive", placeholder="Search for themes, authors, or paper codes...", label_visibility="collapsed")

        # Mission Box
        if not search_query:
            st.markdown(f"""
            <div class="mission-container">
                <p style="font-size: 1.1rem; text-align: center; color: #2c3e50; font-style: italic; line-height: 1.6;">
                    "At <b>The English Archive</b>, we believe that the pursuit of literature belongs to everyone. 
                    We endeavour to provide affordable, curated notes specifically designed for 
                    <b>BA English Honours</b> students. Education is a right, not a luxury."
                </p>
            </div>
            <br><br>
            """, unsafe_allow_html=True)

        # Fetch articles
        if search_query:
            query = f"SELECT * FROM articles WHERE status='Published' AND (title LIKE '%{search_query}%' OR content LIKE '%{search_query}%' OR syllabus LIKE '%{search_query}%') ORDER BY id DESC"
        else:
            query = "SELECT * FROM articles WHERE status='Published' ORDER BY id DESC"
        
        articles = pd.read_sql_query(query, conn)
        
        for index, row in articles.iterrows():
            st.markdown(f"""
                <div class="article-card">
                    <span style="color: #b8860b; font-weight: bold; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 2px;">{row['syllabus']}</span>
                    <h2 style="color: #1a5e63; margin-top: 5px; font-family: 'Montserrat'; font-weight: 600;">{row['title']}</h2>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <div style="line-height: 1.8;">{row['content']}</div>
                    <p style="margin-top: 20px; font-size: 0.8rem; color: #999;">Published on: {row['date']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("💬 Submit a Critique"):
                with st.form(key=f"fb_{row['id']}"):
                    info = st.text_input("Institution (Optional)")
                    msg = st.text_area("Your message")
                    if st.form_submit_button("Send"):
                        sender = info if info else "Anonymous"
                        c.execute('INSERT INTO feedback (article_id, student_info, message, date) VALUES (?,?,?,?)', (row['id'], sender, msg, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("Sent.")

    # --- ADMIN VIEW ---
    elif choice == "🔐 Repository":
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.markdown("### Secure Access")
                pwd = st.text_input("Repository Key", type='password')
                if st.button("Unlock"):
                    if pwd == "mithun2026":
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Access Denied")
        else:
            def update_mode(): st.session_state.admin_mode = st.session_state.nav_pill
            admin_nav = st.pills("Controls", ["Manage Archive", "Write New", "Feedback"], selection_mode="single", key="nav_pill", on_change=update_mode, default=st.session_state.admin_mode)
            st.divider()

            if st.session_state.admin_mode == "Write New":
                st.subheader("Compose Manuscript")
                edit_title = st.text_input("Title", value=st.session_state.edit_title)
                edit_syllabus = st.text_input("Paper Code", value=st.session_state.edit_syllabus)
                edit_content = st_quill(value=st.session_state.edit_content, html=True)
                status = st.selectbox("Status", ["Draft", "Published"])
                
                c1, c2 = st.columns(2)
                if c1.button("Commit to Archive"):
                    if edit_title and edit_content:
                        c.execute('INSERT INTO articles (title, content, syllabus, status, date) VALUES (?,?,?,?,?)', (edit_title, edit_content, edit_syllabus, status, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.session_state.edit_title = ""; st.session_state.edit_content = ""; st.session_state.edit_syllabus = ""
                        st.session_state.admin_mode = "Manage Archive"
                        st.rerun()
                
                if c2.button("Discard"):
                    st.session_state.edit_title = ""; st.session_state.edit_content = ""; st.session_state.edit_syllabus = ""
                    st.session_state.admin_mode = "Manage Archive"
                    st.rerun()

            elif st.session_state.admin_mode == "Manage Archive":
                all_articles = pd.read_sql_query("SELECT id, title, syllabus, status FROM articles ORDER BY id DESC", conn)
                for idx, row in all_articles.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{row['title']}** ({row['syllabus']})")
                    if c2.button("📝 Edit", key=f"e_{row['id']}"):
                        res = c.execute("SELECT * FROM articles WHERE id=?", (row['id'],)).fetchone()
                        st.session_state.edit_title = res[1]; st.session_state.edit_content = res[2]; st.session_state.edit_syllabus = res[3]
                        c.execute("DELETE FROM articles WHERE id=?", (row['id'],)); conn.commit()
                        st.session_state.admin_mode = "Write New"; st.rerun()
                    if c3.button("🗑️ Delete", key=f"d_{row['id']}"):
                        c.execute("DELETE FROM articles WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

            elif st.session_state.admin_mode == "Feedback":
                st.table(pd.read_sql_query("SELECT * FROM feedback", conn))
            
            if st.button("Lock Repository"):
                st.session_state.logged_in = False
                st.rerun()

if __name__ == '__main__':
    main()