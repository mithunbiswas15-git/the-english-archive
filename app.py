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

# --- HELPER FUNCTIONS FOR GRID ---
def get_thumbnail(html_content):
    # Searches for the first <img> tag src in the HTML
    img_match = re.search(r'<img [^>]*src="([^"]+)"', html_content)
    return img_match.group(1) if img_match else None

def get_text_snippet(html_content, length=100):
    # Removes HTML tags to get clean text for the teaser
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
        padding: 50px 20px;
        border-radius: 15px;
        text-align: center;
        color: #ffffff;
        margin-bottom: 30px;
    }
    .hero h1 { font-family: 'Montserrat', sans-serif; letter-spacing: 5px; font-size: 2.5rem !important; color: #f4d03f !important; }

    /* Modern Grid Card */
    .summary-card {
        background-color: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        transition: 0.3s;
        border: 1px solid #eee;
    }
    .summary-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
    
    .card-content { padding: 20px; }
    .thumbnail-area {
        width: 100%;
        height: 150px;
        background-color: #f0f0f0;
        background-size: cover;
        background-position: center;
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
            # --- FULL ARTICLE VIEW ---
            art_id = st.session_state.viewing_article
            row = c.execute("SELECT * FROM articles WHERE id=?", (art_id,)).fetchone()
            if st.button("← Back to Archive"):
                st.session_state.viewing_article = None
                st.rerun()
            
            st.markdown(f"""
                <div class="full-article">
                    <p style="color:#b8860b; font-weight:bold; letter-spacing:2px;">{row[3]}</p>
                    <h1 style="color:#1a5e63; font-family:Montserrat;">{row[1]}</h1>
                    <hr>
                    <div style="font-size:1.15rem; font-family:'Libre Baskerville';">{row[2]}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            # --- GRID VIEW ---
            st.markdown("""<div class="hero"><h1>The English Archive</h1><p>RECLAIMING THE MARGINS</p></div>""", unsafe_allow_html=True)
            search_query = st.text_input("🔍 Search Archive", placeholder="Filter manuscripts...", label_visibility="collapsed")
            
            query = "SELECT * FROM articles WHERE status='Published' ORDER BY id DESC"
            if search_query:
                query = f"SELECT * FROM articles WHERE status='Published' AND (title LIKE '%{search_query}%' OR syllabus LIKE '%{search_query}%') ORDER BY id DESC"
            
            articles_df = pd.read_sql_query(query, conn)
            
            if not articles_df.empty:
                cols = st.columns(3) # 3-column grid looks better with thumbnails
                for index, row in articles_df.iterrows():
                    thumb = get_thumbnail(row['content'])
                    snippet = get_text_snippet(row['content'], 80)
                    
                    with cols[index % 3]:
                        # Card Image
                        if thumb:
                            st.markdown(f'<div class="summary-card"><div class="thumbnail-area" style="background-image: url({thumb});"></div>', unsafe_allow_html=True)
                        else:
                            # Fallback if no image exists
                            st.markdown(f'<div class="summary-card"><div class="thumbnail-area" style="background-color: #1a5e63; opacity: 0.1;"></div>', unsafe_allow_html=True)
                        
                        # Card Text
                        st.markdown(f"""
                            <div class="card-content">
                                <span style="color:#b8860b; font-size:0.7rem; font-weight:bold;">{row['syllabus']}</span>
                                <h4 style="color:#1a5e63; margin: 5px 0; font-family:Montserrat;">{row['title']}</h4>
                                <p style="color:#666; font-size:0.85rem; line-height:1.4;">{snippet}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Read More", key=f"v_{row['id']}", use_container_width=True):
                            st.session_state.viewing_article = row['id']
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    # --- ADMIN VIEW (Simplified for space) ---
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
            elif st.session_state.admin_mode == "Feedback":
                st.table(pd.read_sql_query("SELECT * FROM feedback", conn))
            if st.button("Lock"): st.session_state.logged_in = False; st.rerun()

if __name__ == '__main__':
    main()