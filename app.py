import streamlit as st
from supabase import create_client, Client
import pandas as pd
import re
import os
from datetime import datetime

# --- 1. UNIVERSAL CONNECTION ---
URL = st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
KEY = st.secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    st.error("Database credentials not found. Please check Render Environment Variables.")
    st.stop()

supabase: Client = create_client(URL, KEY)

# --- 2. TURBO CACHING ---
@st.cache_data(ttl=600)
def fetch_published_articles():
    try:
        res = supabase.table("articles").select("*").eq("status", "Published").order("id", desc=True).execute()
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

# --- 4. THEME & BRANDING ---
st.set_page_config(page_title="The English Archive", layout="wide")

# CSS to ONLY target the header elements
st.markdown("""
    <style>
    /* HIDE HEADER ELEMENTS ONLY */
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    .stDeployButton {display:none !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* TYPOGRAPHY & LAYOUT */
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
    
    .full-article {
        background-color: #ffffff;
        padding: 60px;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.05);
        line-height: 2;
        max-width: 900px;
        margin: 40px auto;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # --- 5. SESSION MANAGEMENT ---
    if 'viewing_id' not in st.session_state: st.session_state.viewing_id = None
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'admin_mode' not in st.session_state: st.session_state.admin_mode = "View Records"
    
    if 'edit_id' not in st.session_state: st.session_state.edit_id = None
    if 'f_title' not in st.session_state: st.session_state.f_title = ""
    if 'f_syllabus' not in st.session_state: st.session_state.f_syllabus = ""
    if 'f_content' not in st.session_state: st.session_state.f_content = ""

    # --- 6. NAVIGATION ---
    query_params = st.query_params
    is_manager = query_params.get("access") == "manager"

    if is_manager:
        choice = st.segmented_control("Website Manager Access", ["🏠 Archive", "🔐 Repository"], default="🏠 Archive")
    else:
        choice = "🏠 Archive"
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 7. PUBLIC ARCHIVE VIEW ---
    if choice == "🏠 Archive":
        if st.session_state.viewing_id:
            res = supabase.table("articles").select("*").eq("id", st.session_state.viewing_id).execute()
            if res.data:
                art = res.data[0]
                if st.button("← Back to Archive"): 
                    st.session_state.viewing_id = None
                    st.rerun()
                st.markdown(f'''
                    <div class="full-article">
                        <p style="color:#b8860b; font-weight:bold; letter-spacing:2px; font-size:0.9rem;">{art["syllabus"]}</p>
                        <h1 style="color:#1a5e63; font-family:Montserrat;">{art["title"]}</h1>
                        <hr style="opacity:0.1; margin:30px 0;">
                        <div style="font-family:'Libre Baskerville'; font-size:1.2rem;">{art["content"]}</div>
                    </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="hero"><h1>The English Archive</h1><p>RECLAIMING THE MARGINS</p></div>', unsafe_allow_html=True)
            df = fetch_published_articles()

            if not df.empty:
                for _, row in df.iterrows():
                    thumb = get_thumbnail(row['content'])
                    snippet = get_text_snippet(row['content'])
                    
                    st.markdown(f'''
                    <div class="horizontal-card">
                        <div class="card-text">
                            <span style="color:#b8860b; font-size:0.8rem; font-weight:bold;">{row["syllabus"]}</span>
                            <h3 style="color:#1a5e63; margin:12px 0; font-family:Montserrat; font-size:1.4rem;">{row["title"]}</h3>
                            <p style="color:#666; font-size:1rem;">{snippet}</p>
                        </div>
                        {f'<div class="card-img" style="background-image: url({thumb});"></div>' if thumb else '<div class="card-img"></div>'}
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    if st.button(f"Read Full Analysis: {row['title']}", key=f"btn_{row['id']}", use_container_width=True):
                        st.session_state.viewing_id = row['id']
                        st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("The repository is currently being updated.")

    # --- 8. ADMIN REPOSITORY VIEW ---
    elif choice == "🔐 Repository":
        if not st.session_state.logged_in:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.text_input("Master Entry Key", type="password") == "mithun2026":
                    st.session_state.logged_in = True
                    st.rerun()
        else:
            admin_opt = st.pills("Management Dashboard", ["View Records", "Draft New"], default=st.session_state.admin_mode)
            st.session_state.admin_mode = admin_opt

            if admin_opt == "Draft New":
                st.subheader("Manuscript Editor")
                t = st.text_input("Title", value=st.session_state.f_title)
                s = st.text_input("Syllabus Reference", value=st.session_state.f_syllabus)
                c_html = st.text_area("Content (HTML supported)", value=st.session_state.f_content, height=400)
                
                if st.button("Archive Manuscript"):
                    entry = {"title": t, "content": c_html, "syllabus": s, "status": "Published", "date": datetime.now().strftime("%Y-%m-%d")}
                    if st.session_state.edit_id:
                        supabase.table("articles").update(entry).eq("id", st.session_state.edit_id).execute()
                    else:
                        supabase.table("articles").insert(entry).execute()
                    
                    st.cache_data.clear() 
                    st.session_state.edit_id = None; st.session_state.f_title = ""; st.session_state.f_syllabus = ""; st.session_state.f_content = ""
                    st.session_state.admin_mode = "View Records"
                    st.success("Analysis Saved!")
                    st.rerun()

            elif admin_opt == "View Records":
                res = supabase.table("articles").select("id, title, syllabus").execute()
                if res.data:
                    for r in res.data:
                        c1, c2, c3 = st.columns([5, 1, 1])
                        c1.write(f"**{r['title']}** — *{r['syllabus']}*")
                        if c2.button("📝 Edit", key=f"edit_{r['id']}"):
                            full_res = supabase.table("articles").select("*").eq("id", r['id']).execute()
                            art = full_res.data[0]
                            st.session_state.edit_id = art['id']
                            st.session_state.f_title = art['title']; st.session_state.f_syllabus = art['syllabus']; st.session_state.f_content = art['content']
                            st.session_state.admin_mode = "Draft New"
                            st.rerun()
                        if c3.button("🗑️ Delete", key=f"del_{r['id']}"):
                            supabase.table("articles").delete().eq("id", r['id']).execute()
                            st.cache_data.clear()
                            st.rerun()
                
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()

if __name__ == '__main__':
    main()