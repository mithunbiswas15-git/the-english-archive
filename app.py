import streamlit as st
from supabase import create_client, Client
import pandas as pd
import re
import os
from datetime import datetime
import time

# --- 1. RENDER-ONLY CONNECTION ---
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    st.error("Database credentials not found. Please add SUPABASE_URL and SUPABASE_KEY to Render Environment Variables.")
    st.stop()

supabase: Client = create_client(URL, KEY)

# --- 2. ADVANCED TURBO CACHING ---
@st.cache_data(ttl=3600)
def fetch_published_articles():
    try:
        # The app "thinks" here while fetching from Mumbai
        res = supabase.table("articles").select("id, title, syllabus, content").eq("status", "Published").order("id", desc=True).execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

# --- 3. HELPER FUNCTIONS ---
def get_thumbnail(html_content):
    img_match = re.search(r'src="([^"]+)"', html_content)
    return img_match.group(1) if img_match else None

def get_text_snippet(html_content, length=180):
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    return clean_text[:length] + "..." if len(clean_text) > length else clean_text

# --- 4. THEME & HEADER HIDING ---
st.set_page_config(page_title="The English Archive", layout="wide")

st.markdown("""
    <style>
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    .stDeployButton {display:none !important;}
    #MainMenu {visibility: hidden !important;}
    
    @import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville&family=Montserrat:wght@300;600&display=swap');
    .main { background-color: #fdfaf3; padding-top: 0px !important; }
    
    .hero {
        background: linear-gradient(135deg, #1a5e63 0%, #0d2f31 100%);
        padding: 60px 20px;
        border-radius: 15px;
        text-align: center;
        color: #ffffff;
        margin-bottom: 40px;
    }
    .hero h1 { font-family: 'Montserrat', sans-serif; letter-spacing: 6px; font-size: 2.8rem !important; color: #f4d03f !important; }

    .horizontal-card {
        display: flex;
        background-color: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        border: 1px solid #eee;
        min-height: 220px;
    }
    .card-text { flex: 2; padding: 35px; display: flex; flex-direction: column; justify-content: center; }
    .card-img { flex: 1; background-size: cover; background-position: center; min-width: 250px; background-color: #f4f1e6; }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- 5. SESSION MANAGEMENT ---
    if 'viewing_id' not in st.session_state: st.session_state.viewing_id = None
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    
    # --- 6. NAVIGATION ---
    query_params = st.query_params
    is_manager = query_params.get("access") == "manager"
    choice = st.segmented_control("Navigation", ["🏠 Archive", "🔐 Repository"], default="🏠 Archive") if is_manager else "🏠 Archive"

    # --- 7. PUBLIC ARCHIVE VIEW ---
    if choice == "🏠 Archive":
        if st.session_state.viewing_id:
            # Viewing a single article
            res = supabase.table("articles").select("*").eq("id", st.session_state.viewing_id).execute()
            if res.data:
                art = res.data[0]
                if st.button("← Back to Archive"): 
                    st.session_state.viewing_id = None
                    st.rerun()
                st.markdown(f'<div style="background:white; padding:40px; border-radius:15px;"><h1>{art["title"]}</h1>{art["content"]}</div>', unsafe_allow_html=True)
        else:
            # THE HERO BANNER (Loads Instantly)
            st.markdown('<div class="hero"><h1>The English Archive</h1><p>RECLAIMING THE MARGINS</p></div>', unsafe_allow_html=True)
            
            # THE LOADING ANIMATION
            with st.spinner("Retrieving manuscripts from the archive..."):
                df = fetch_published_articles()

            # The articles appear here once the spinner finishes
            if not df.empty:
                for _, row in df.iterrows():
                    thumb = get_thumbnail(row['content'])
                    snippet = get_text_snippet(row['content'])
                    st.markdown(f'''
                    <div class="horizontal-card">
                        <div class="card-text">
                            <span style="color:#b8860b; font-size:0.8rem; font-weight:bold;">{row["syllabus"]}</span>
                            <h3 style="color:#1a5e63; margin:12px 0;">{row["title"]}</h3>
                            <p style="color:#666;">{snippet}</p>
                        </div>
                        {f'<div class="card-img" style="background-image: url({thumb});"></div>' if thumb else '<div class="card-img"></div>'}
                    </div>
                    ''', unsafe_allow_html=True)
                    if st.button(f"Read Full Analysis: {row['title']}", key=f"btn_{row['id']}", use_container_width=True):
                        st.session_state.viewing_id = row['id']
                        st.rerun()
            else:
                st.info("The repository is currently being updated.")

    # --- 8. ADMIN REPOSITORY VIEW ---
    elif choice == "🔐 Repository":
        if not st.session_state.logged_in:
            if st.text_input("Master Entry Key", type="password") == "mithun2026":
                st.session_state.logged_in = True
                st.rerun()
        else:
            admin_opt = st.pills("Dashboard", ["View Records", "Draft New"], default="View Records")
            if admin_opt == "Draft New":
                t = st.text_input("Title")
                s = st.text_input("Syllabus")
                c = st.text_area("Content", height=300)
                if st.button("Save Manuscript"):
                    entry = {"title": t, "content": c, "syllabus": s, "status": "Published", "date": datetime.now().strftime("%Y-%m-%d")}
                    supabase.table("articles").insert(entry).execute()
                    st.cache_data.clear() # Reset memory so the new article shows up!
                    st.success("Saved!")
                    st.rerun()
            elif admin_opt == "View Records":
                res = supabase.table("articles").select("id, title").execute()
                for r in res.data:
                    st.write(f"ID: {r['id']} - {r['title']}")
                    if st.button(f"Delete {r['id']}", key=f"del_{r['id']}"):
                        supabase.table("articles").delete().eq("id", r['id']).execute()
                        st.cache_data.clear()
                        st.rerun()

if __name__ == '__main__':
    main()