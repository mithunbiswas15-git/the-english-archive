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

# --- THE BEAUTIFIED THEME ---
st.set_page_config(page_title="The English Archive", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville&family=Montserrat:wght@300;600&display=swap');
    .main { background-color: #fdfaf3; }
    
    /* Hero Header */
    .hero {
        background: linear-gradient(135deg, #1a5e63 0%, #0d2f31 100%);
        padding: 50px 20px;
        border-radius: 15px;
        text-align: center;
        color: #ffffff;
        margin-bottom: 30px;
    }
    .hero h1 { 
        font-family: 'Montserrat', sans-serif;
        letter-spacing: 5px;
        font-size: 2.5rem !important;
        color: #f4d03f !important;
    }

    /* Summary Card Styling */
    .summary-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 10px;
        border-top: 4px solid #b8860b;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        height: 180px;
    }
    
    /* Full Article Styling */
    .full-article {
        background-color: #ffffff;
        padding: 50px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        line-height: 1.9;
        font-family: 'Libre Baskerville', serif;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- SESSION STATE FOR NAVIGATION ---
    if 'viewing_article' not in st.session_state: st.session_state.viewing_article = None
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'admin_mode' not in st.session_state: st.session_state.admin_mode = "Manage Archive"

    # --- TOP NAVIGATION ---
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        choice = st.segmented_control("Nav", ["🏠 Archive", "🔐 Repository"], default="🏠 Archive", key="main_nav", label_visibility="collapsed")
    
    # If user switches to Admin, reset article view
    if choice == "🔐 Repository": st.session_state.viewing_article = None

    st.markdown("<br>", unsafe_allow_html=True)

    # --- PUBLIC VIEW ---
    if choice == "🏠 Archive":
        
        # --- CASE 1: READING A SPECIFIC ARTICLE ---
        if st.session_state.viewing_article:
            art_id = st.session_state.viewing_article
            row = c.execute("SELECT * FROM articles WHERE id=?", (art_id,)).fetchone()
            
            if st.button("← Back to Archive"):
                st.session_state.viewing_article = None
                st.rerun()
            
            st.markdown(f"""
                <div class="full-article">
                    <p style="color:#b8860b; font-weight:bold; letter-spacing:2px;">{row[3]}</p>
                    <h1 style="color:#1a5e63; font-family:Montserrat;">{row[1]}</h1>
                    <p style="color:#999; font-size:0.8rem;">Published: {row[5]}</p>
                    <hr>
                    <div style="font-size:1.1rem;">{row[2]}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Feedback Form inside the article
            with st.expander("💬 Submit a Critique or Query"):
                with st.form(key=f"fb_{row[0]}"):
                    msg = st.text_area("Your message (Private)")
                    if st.form_submit_button("Submit"):
                        c.execute('INSERT INTO feedback (article_id, student_info, message, date) VALUES (?,?,?,?)', 
                                 (row[0], "Anonymous", msg, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.success("Sent.")

        # --- CASE 2: BROWSING THE LIST ---
        else:
            st.markdown("""<div class="hero"><h1>The English Archive</h1><p>RECLAIMING THE MARGINS</p></div>""", unsafe_allow_html=True)
            
            search_query = st.text_input("🔍 Search Archive", placeholder="Search for themes, authors, or paper codes...", label_visibility="collapsed")
            
            query = "SELECT id, title, syllabus, date FROM articles WHERE status='Published' ORDER BY id DESC"
            if search_query:
                query = f"SELECT id, title, syllabus, date FROM articles WHERE status='Published' AND (title LIKE '%{search_query}%' OR syllabus LIKE '%{search_query}%') ORDER BY id DESC"
            
            articles_df = pd.read_sql_query(query, conn)
            
            if not articles_df.empty:
                # Create a 2-column grid for cards
                cols = st.columns(2)
                for index, row in articles_df.iterrows():
                    with cols[index % 2]:
                        st.markdown(f"""
                            <div class="summary-card">
                                <span style="color:#b8860b; font-size:0.8rem; font-weight:bold;">{row['syllabus']}</span>
                                <h3 style="color:#1a5e63; margin-top:5px; font-family:Montserrat;">{row['title']}</h3>
                                <p style="color:#666; font-size:0.8rem;">Date: {row['date']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Read Manuscript", key=f"view_{row['id']}"):
                            st.session_state.viewing_article = row['id']
                            st.rerun()
            else:
                st.info("No matching manuscripts found.")

    # --- ADMIN VIEW ---
    elif choice == "🔐 Repository":
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.markdown("### Secure Access")
                pwd = st.text_input("Key", type='password')
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
                t = st.text_input("Title")
                s = st.text_input("Paper Code")
                con = st_quill(html=True)
                stat = st.selectbox("Status", ["Draft", "Published"])
                if st.button("Commit"):
                    c.execute('INSERT INTO articles (title, content, syllabus, status, date) VALUES (?,?,?,?,?)', (t, con, s, stat, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    st.session_state.admin_mode = "Manage Archive"
                    st.rerun()

            elif st.session_state.admin_mode == "Manage Archive":
                all_arts = pd.read_sql_query("SELECT id, title, syllabus FROM articles", conn)
                for idx, r in all_arts.iterrows():
                    c1, c2, c3 = st.columns([3,1,1])
                    c1.write(f"**{r['title']}**")
                    if c2.button("📝", key=f"e_{r['id']}"):
                        res = c.execute("SELECT * FROM articles WHERE id=?", (r['id'],)).fetchone()
                        # Load data for edit and delete old
                        st.session_state.admin_mode = "Write New"
                        c.execute("DELETE FROM articles WHERE id=?", (r['id'],))
                        conn.commit()
                        st.rerun()
                    if c3.button("🗑️", key=f"d_{r['id']}"):
                        c.execute("DELETE FROM articles WHERE id=?", (r['id'],))
                        conn.commit(); st.rerun()

if __name__ == '__main__':
    main()