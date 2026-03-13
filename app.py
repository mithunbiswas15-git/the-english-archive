import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from streamlit_quill import st_quill

# --- DATABASE SETUP ---
conn = sqlite3.connect('lit_archive.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS articles (id INTEGER PRIMARY KEY, title TEXT, content TEXT, syllabus TEXT, status TEXT, date TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY, article_id INTEGER, student_info TEXT, message TEXT, date TEXT)')
conn.commit()

# --- HELPER FUNCTIONS ---
def get_thumbnail(html_content):
    img_match = re.search(r'<img [^>]*src="([^"]+)"', html_content)
    return img_match.group(1) if img_match else None

def get_text_snippet(html_content, length=150): # Longer snippet for horizontal view
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    return clean_text[:length] + "..." if len(clean_text) > length else clean_text

# --- THE BEAUTIFIED THEME ---
st.set_page_config(page_title="The English Archive", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville&family=Montserrat:wght@300;600&display=swap');
    .main { background-color: #fdfaf3; }
    
    .hero {
        background: linear-gradient(135deg, #1a5e63 0%, #0d2f31 100%);
        padding: 40px 20px;
        border-radius: 15px;
        text-align: center;
        color: #ffffff;
        margin-bottom: 30px;
    }
    .hero h1 { font-family: 'Montserrat', sans-serif; letter-spacing: 5px; font-size: 2.2rem !important; color: #f4d03f !important; }

    /* Horizontal Card Styling */
    .horizontal-card {
        display: flex;
        background-color: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        margin-bottom: 20px;
        border: 1px solid #eee;
        transition: 0.3s;
        min-height: 180px;
    }
    .horizontal-card:hover { transform: translateX(5px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
    
    .card-text {
        flex: 2;
        padding: 25px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .card-img {
        flex: 1;
        background-size: cover;
        background-position: center;
        min-width: 200px;
    }
    
    .full-article {
        background-color: #ffffff;
        padding: 50px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        line-height: 1.9;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    if 'viewing_article' not in st.session_state: st.session_state.viewing_article = None
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'admin_mode' not in st.session_state: st.session_state.admin_mode = "Manage Archive"

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        choice = st.segmented_control("Nav", ["🏠 Archive", "🔐 Repository"], default="🏠 Archive", key="main_nav", label_visibility="collapsed")
    
    if choice == "🔐 Repository": st.session_state.viewing_article = None
    st.markdown("<br>", unsafe_allow_html=True)

    # --- PUBLIC VIEW ---
    if choice == "🏠 Archive":
        if st.session_state.viewing_article:
            # --- ARTICLE DETAIL ---
            art_id = st.session_state.viewing_article
            row = c.execute("SELECT * FROM articles WHERE id=?", (art_id,)).fetchone()
            if st.button("← Back to Archive"):
                st.session_state.viewing_article = None
                st.rerun()
            
            st.markdown(f"""
                <div class="full-article">
                    <p style="color:#b8860b; font-weight:bold; letter-spacing:2px; font-size:0.8rem;">{row[3]}</p>
                    <h1 style="color:#1a5e63; font-family:Montserrat;">{row[1]}</h1>
                    <hr style="margin: 25px 0; opacity: 0.2;">
                    <div style="font-size:1.15rem; font-family:'Libre Baskerville';">{row[2]}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # --- ARCHIVE LIST ---
            st.markdown("""<div class="hero"><h1>The English Archive</h1><p>RECLAIMING THE MARGINS</p></div>""", unsafe_allow_html=True)
            search_query = st.text_input("🔍 Search Archive", placeholder="Filter by title, author, or paper code...", label_visibility="collapsed")
            
            query = "SELECT * FROM articles WHERE status='Published' ORDER BY id DESC"
            if search_query:
                query = f"SELECT * FROM articles WHERE status='Published' AND (title LIKE '%{search_query}%' OR syllabus LIKE '%{search_query}%') ORDER BY id DESC"
            
            articles_df = pd.read_sql_query(query, conn)
            
            if not articles_df.empty:
                # One column for horizontal cards
                for index, row in articles_df.iterrows():
                    thumb = get_thumbnail(row['content'])
                    snippet = get_text_snippet(row['content'], 180)
                    
                    # Custom Flexbox Container for the Card
                    st.markdown(f"""
                    <div class="horizontal-card">
                        <div class="card-text">
                            <span style="color:#b8860b; font-size:0.75rem; font-weight:bold; letter-spacing:1px;">{row['syllabus']}</span>
                            <h3 style="color:#1a5e63; margin: 8px 0; font-family:Montserrat; font-weight:600;">{row['title']}</h3>
                            <p style="color:#555; font-size:0.9rem; line-height:1.5;">{snippet}</p>
                        </div>
                        {f'<div class="card-img" style="background-image: url({thumb});"></div>' if thumb else '<div class="card-img" style="background-color:#f4f1e6;"></div>'}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Invisible Button Overlay Trick or Standard Button
                    if st.button(f"Read Full Manuscript: {row['title']}", key=f"v_{row['id']}", use_container_width=True):
                        st.session_state.viewing_article = row['id']
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("No records found.")

    # --- ADMIN VIEW ---
    elif choice == "🔐 Repository":
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                pwd = st.text_input("Access Key", type='password')
                if st.button("Unlock"):
                    if pwd == "mithun2026": st.session_state.logged_in = True; st.rerun()
        else:
            def update_mode(): st.session_state.admin_mode = st.session_state.nav_pill
            st.pills("Controls", ["Manage Archive", "Write New", "Feedback"], key="nav_pill", on_change=update_mode, default=st.session_state.admin_mode)
            
            if st.session_state.admin_mode == "Write New":
                t = st.text_input("Title")
                s = st.text_input("Syllabus")
                con = st_quill(html=True)
                if st.button("Commit"):
                    c.execute('INSERT INTO articles (title, content, syllabus, status, date) VALUES (?,?,?,?,?)', (t, con, s, "Published", datetime.now().strftime("%Y-%m-%d")))
                    conn.commit(); st.session_state.admin_mode = "Manage Archive"; st.rerun()
            elif st.session_state.admin_mode == "Manage Archive":
                for idx, r in pd.read_sql_query("SELECT id, title FROM articles", conn).iterrows():
                    c1, c2 = st.columns([4,1])
                    c1.write(r['title'])
                    if c2.button("🗑️", key=f"d_{r['id']}"):
                        c.execute("DELETE FROM articles WHERE id=?", (r['id'],)); conn.commit(); st.rerun()
            if st.button("Lock"): st.session_state.logged_in = False; st.rerun()

if __name__ == '__main__':
    main()