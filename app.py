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

# --- THE SCHOLARLY THEME ---
st.set_page_config(page_title="The English Archive", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fdfaf3; }
    .stMarkdown { font-family: 'Libre Baskerville', serif; color: #2c3e50; line-height: 1.9; }
    h1 { color: #1a5e63 !important; font-size: 2.8rem !important; text-align: center; margin-bottom: 5px; }
    .stButton>button { background-color: #1a5e63; color: white; border-radius: 2px; border: none; }
    [data-testid="stSidebar"] { display: none; }
    .about-section { 
        background-color: #f4f1e6; 
        padding: 40px; 
        border-radius: 8px; 
        border: 1px solid #e1dcc9;
        margin-bottom: 40px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .mission-text {
        font-size: 1.1rem; 
        max-width: 900px; 
        margin: 0 auto; 
        color: #2c3e50;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- SESSION STATE ---
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'admin_mode' not in st.session_state: st.session_state.admin_mode = "Manage Archive"
    if 'edit_title' not in st.session_state: st.session_state.edit_title = ""
    if 'edit_syllabus' not in st.session_state: st.session_state.edit_syllabus = ""
    if 'edit_content' not in st.session_state: st.session_state.edit_content = ""

    # --- TOP NAVIGATION ---
    menu_col1, menu_col2, menu_col3 = st.columns([1, 2, 1])
    with menu_col2:
        choice = st.segmented_control(
            "Navigation", 
            ["🏠 Public Archive", "🔐 Repository Access"], 
            default="🏠 Public Archive",
            key="main_nav"
        )
    
    st.divider()

    # --- PUBLIC VIEW ---
    if choice == "🏠 Public Archive":
        st.markdown("<h1>The English Archive</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#b8860b; letter-spacing:4px; font-weight:bold; margin-bottom:25px;'>RECLAIMING THE MARGINS</p>", unsafe_allow_html=True)
        
        # Search Box
        search_query = st.text_input("🔍 Search Archive", placeholder="Search for themes, authors, or paper codes...", label_visibility="collapsed")
        
        # --- MISSION SECTION ---
        if not search_query:
            with st.container():
                st.markdown(f"""
                <div class="about-section">
                    <h3 style="color:#1a5e63; font-family:'Montserrat'; margin-bottom:20px;">Our Mission</h3>
                    <p class="mission-text">
                        At <b>The English Archive</b>, we believe that the pursuit of literature belongs to everyone. 
                        We endeavour to provide affordable, curated notes specifically designed for 
                        <b>BA English Honours</b> students who may lack access to expensive study materials. 
                        Education is a right, not a luxury. By offering peer-reviewed content at an accessible price point, 
                        we aim to empower deserving students to reclaim their academic journey and find their voice 
                        in the "margins" of the literary canon.
                    </p>
                    <p style='font-size: 0.9rem; margin-top: 25px; color: #b8860b; font-weight: 600;'>CURATED BY THE EDITORIAL COLLECTIVE</p>
                </div>
                """, unsafe_allow_html=True)

        # Fetch data based on search
        if search_query:
            query = f"SELECT * FROM articles WHERE status='Published' AND (title LIKE '%{search_query}%' OR content LIKE '%{search_query}%' OR syllabus LIKE '%{search_query}%') ORDER BY id DESC"
        else:
            query = "SELECT * FROM articles WHERE status='Published' ORDER BY id DESC"
        
        articles = pd.read_sql_query(query, conn)
        
        if not articles.empty:
            for index, row in articles.iterrows():
                with st.container():
                    st.markdown(f"### {row['title']}")
                    st.caption(f"Paper: {row['syllabus']} | Published: {row['date']}")
                    st.markdown(row['content'], unsafe_allow_html=True)
                    
                    with st.expander("💬 Submit a Critique or Anonymous Query"):
                        with st.form(key=f"fb_{row['id']}"):
                            info = st.text_input("Institution (Optional)", placeholder="Leave blank to remain anonymous")
                            msg = st.text_area("Your message")
                            if st.form_submit_button("Submit"):
                                sender = info if info else "Anonymous Student"
                                c.execute('INSERT INTO feedback (article_id, student_info, message, date) VALUES (?,?,?,?)', 
                                         (row['id'], sender, msg, datetime.now().strftime("%Y-%m-%d")))
                                conn.commit()
                                st.success("Message received. Thank you for contributing to the archive.")
                st.divider()
        else:
            if search_query:
                st.warning("No records found for that search.")

    # --- ADMIN VIEW ---
    elif choice == "🔐 Repository Access":
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.markdown("### Secure Access")
                pwd = st.text_input("Enter Repository Key", type='password')
                if st.button("Unlock"):
                    if pwd == "mithun2026":
                        st.session_state.logged_in = True
                        st.rerun()
                    else: st.error("Access Denied")
        else:
            def update_mode():
                st.session_state.admin_mode = st.session_state.nav_pill
            
            admin_options = ["Manage Archive", "Write New", "Feedback"]
            st.pills("Repository Controls", admin_options, selection_mode="single", key="nav_pill", on_change=update_mode, default=st.session_state.admin_mode)
            st.divider()

            if st.session_state.admin_mode == "Write New":
                st.subheader("Compose Manuscript")
                edit_title = st.text_input("Title", value=st.session_state.edit_title)
                edit_syllabus = st.text_input("Paper Code", value=st.session_state.edit_syllabus)
                edit_content = st_quill(value=st.session_state.edit_content, html=True)
                status = st.selectbox("Status", ["Draft", "Published"])
                
                c_save, c_clear = st.columns(2)
                if c_save.button("Commit to Archive"):
                    if edit_title and edit_content:
                        c.execute('INSERT INTO articles (title, content, syllabus, status, date) VALUES (?,?,?,?,?)',
                                 (edit_title, edit_content, edit_syllabus, status, datetime.now().strftime("%Y-%m-%d")))
                        conn.commit()
                        st.session_state.edit_title = ""
                        st.session_state.edit_content = ""
                        st.session_state.edit_syllabus = ""
                        st.session_state.admin_mode = "Manage Archive"
                        st.success("Manuscript committed.")
                        st.rerun()
                
                if c_clear.button("Discard Changes"):
                    st.session_state.edit_title = ""
                    st.session_state.edit_content = ""
                    st.session_state.edit_syllabus = ""
                    st.session_state.admin_mode = "Manage Archive"
                    st.rerun()

            elif st.session_state.admin_mode == "Manage Archive":
                st.subheader("Master Repository")
                all_articles = pd.read_sql_query("SELECT id, title, syllabus, status FROM articles ORDER BY id DESC", conn)
                for idx, row in all_articles.iterrows():
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{row['title']}** ({row['syllabus']})")
                    if c2.button("📝 Edit", key=f"e_{row['id']}"):
                        res = c.execute("SELECT * FROM articles WHERE id=?", (row['id'],)).fetchone()
                        st.session_state.edit_title = res[1]
                        st.session_state.edit_content = res[2]
                        st.session_state.edit_syllabus = res[3]
                        c.execute("DELETE FROM articles WHERE id=?", (row['id'],))
                        conn.commit()
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