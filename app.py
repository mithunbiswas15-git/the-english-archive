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
    
    /* GLOBAL TYPOGRAPHY */
    html, body, [class*="css"] { 
        font-family: 'Libre Baskerville', serif; 
        color: #2c3e50;
        line-height: 1.6 !important; 
    }
    
    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, #1a5e63 0%, #0d2f31 100%);
        padding: 50px 20px;
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
        font-size: 2.8rem !important;
        color: #f4d03f !important;
        margin-bottom: 10px;
    }

    /* Article Cards */
    .article-card {
        background-color: #ffffff;
        padding: 35px;
        border-radius: 12px;
        border-left: 5px solid #1a5e63;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        overflow: auto;
    }

    /* Article Content Spacing */
    .article-body {
        line-height: 1.6;
        font-size: 1.05rem;
    }
    
    .article-body p {
        margin-bottom: 12px;
    }

    /* ENLARGED RESPONSIVE IMAGES: Right-float on PC, Stacked on Mobile */
    .article-body img {
        float: right;
        margin-left: 25px;
        margin-bottom: 15px;
        max-width: 500px; 
        width: 100%;
        height: auto;
        border-radius: 6px;
        border: 1px solid #e1dcc9;
        box-shadow: 6px 6px 18px rgba(0,0,0,0.1);
    }

    @media only screen and (max-width: 850px) {
        .article-body img {
            float: none !important;
            display: block !important;
            margin: 20px auto !important;
            max-width: 100% !important;
        }
    }

    /* Mission Box */
    .mission-container {
        border: 2px solid #b8860b;
        padding: 25px;
        margin-top: -55px;
        background: white;
        border-radius: 10px;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.5;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }

    /* Buttons */
    .stButton>button {
        background: #1a5e63;
        color: white;
        border-radius: 5px;
        font-family: 'Montserrat', sans-serif;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 1px;
    }
    
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
        st.markdown("""<div class="hero"><h1>The English Archive</h1><p style='letter-spacing: 2px; font-family:Montserrat;'>RECLAIMING THE MARGINS</p></div>""", unsafe_allow_html=True)
        search_query = st.text_input("🔍 Search", placeholder="Search for themes, authors, or paper codes...", label_visibility="collapsed")

        if not search_query:
            st.markdown(f"""<div class="mission-container"><p style="text-align: center; font-style: italic;">"At <b>The English Archive</b>, we believe that the pursuit of literature belongs to everyone. Education is a right, not a luxury."</p></div><br>""", unsafe_allow_html=True)

        query = "SELECT * FROM articles WHERE status='Published' ORDER BY id DESC"
        if search_query:
            query = f"SELECT * FROM articles WHERE status='Published' AND (title LIKE '%{search_query}%' OR content LIKE '%{search_query}%' OR syllabus LIKE '%{search_query}%') ORDER BY id DESC"
        
        articles = pd.read_sql_query(query, conn)
        
        if not articles.empty:
            for index, row in articles.iterrows():
                st.markdown(f"""
                    <div class="article-card">
                        <span style="color: #b8860b; font-weight: bold; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 2px;">{row['syllabus']}</span>
                        <h2 style="color: #1a5e63; margin-top: 5px; font-family: 'Montserrat'; font-weight: 600;">{row['title']}</h2>
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 15px 0;">
                        <div class="article-body">{row['content']}</div>
                        <p style="margin-top: 15px; font-size: 0.75rem; color: #999; font-family: 'Montserrat';">PUBLISHED: {row['date']}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            if search_query:
                st.warning("No matching manuscripts found.")

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
                        # Reset session state after saving
                        st.session_state.edit_title = ""; st.session_state.edit_content = ""; st.session_state.edit_syllabus = ""
                        st.session_state.admin_mode = "Manage Archive"
                        st.success("Manuscript successfully committed.")
                        st.rerun()
                
                if c2.button("Discard Changes"):
                    st.session_state.edit_title = ""; st.session_state.edit_content = ""; st.session_state.edit_syllabus = ""
                    st.session_state.admin_mode = "Manage Archive"
                    st.rerun()

            elif st.session_state.admin_mode == "Manage Archive":
                st.subheader("Master Repository")
                all_articles = pd.read_sql_query("SELECT id, title, syllabus, status FROM articles ORDER BY id DESC", conn)
                for idx, row in all_articles.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{row['title']}** ({row['syllabus']})")
                    
                    # SAFE EDIT: Loads data into state but does NOT delete yet
                    if c2.button("📝 Edit", key=f"e_{row['id']}"):
                        res = c.execute("SELECT * FROM articles WHERE id=?", (row['id'],)).fetchone()
                        st.session_state.edit_title = res[1]
                        st.session_state.edit_content = res[2]
                        st.session_state.edit_syllabus = res[3]
                        st.session_state.admin_mode = "Write New"
                        st.rerun()
                        
                    if c3.button("🗑️ Delete", key=f"d_{row['id']}"):
                        c.execute("DELETE FROM articles WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()

            elif st.session_state.admin_mode == "Feedback":
                st.subheader("Queries Inbox")
                fbs = pd.read_sql_query("SELECT * FROM feedback", conn)
                st.table(fbs)
            
            if st.button("Lock Repository"):
                st.session_state.logged_in = False
                st.rerun()

if __name__ == '__main__':
    main()