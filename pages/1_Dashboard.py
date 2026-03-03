
import streamlit as st
from core.database import supabase
from core.auth import logout_user
from core.cache import get_cached_profile, get_cached_skills
from core.auth import logout_user
from core.cache import force_clear_cache

# 1. Security Check: Kick them out if they bypassed the login page
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

user = st.session_state["user"]



# 2. Unified Custom Sidebar Navigation
with st.sidebar:
    st.title("Career AI Hub")
    st.page_link("pages/1_Dashboard.py", label="Dashboard", icon="🏠")
    st.page_link("pages/2_Branding.py", label="LinkedIn Optimizer", icon="✨")
    st.page_link("pages/3_Skill_Gap.py", label="Skill Gap Analyzer", icon="📊")
    st.page_link("pages/4_Scorecard.py", label="Viral Scorecard", icon="🔥")
    st.page_link("pages/5_Network.py", label="Connection Hub", icon="🤝")
    st.page_link("pages/6_Profile.py", label="Edit Profile", icon="👤")
    st.divider()
    
    # The Manual Clear Cache Button
    if st.button("🔄 Sync Data (Clear Cache)", use_container_width=True):
        force_clear_cache()
        st.success("Cache cleared. Data synced.")
        st.rerun()
        
    st.button("Logout", on_click=logout_user, use_container_width=True)

def check_profile_exists():
    """Checks if the user has already completed onboarding."""
    try:
        response = supabase.table("profiles").select("*").eq("id", user.id).execute()
        return len(response.data) > 0
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def show_onboarding():
    """The CSE Data Matrix Form """
    st.title("Step 1: Adaptive Onboarding ")
    st.write("Define your career trajectory. Our AI needs this context to personalize your experience. ")
    
    with st.form("onboarding_form"):
        st.subheader("A. Profile & Ambition ")
        col1, col2 = st.columns(2)
        with col1:
            college_year = st.selectbox("Year of Study", ["1st Year", "2nd Year", "3rd Year", "4th Year"]) 
            target_role = st.selectbox("Target Role", ["SDE", "ML Engineer", "Data Scientist", "DevOps", "Full Stack", "Competitive Programmer"]) 
        with col2:
            target_ecosystem = st.selectbox("Target Ecosystem", ["FAANG/Big Tech", "Product-Based Startups", "Service-Based Companies"])
            voice_tone = st.selectbox("Preferred Branding Tone", ["Professional", "Energetic", "Authoritative", "Empathetic", "Witty"])
            
        st.subheader("B. Technical DNA (1-5 Scale) ")
        st.write("Rate your core fundamentals honestly. False data leads to weak AI advice.")
        dsa = st.slider("Data Structures & Algorithms", 1, 5, 3)
        oops = st.slider("Object Oriented Programming", 1, 5, 3) 
        dbms = st.slider("Database Management (DBMS)", 1, 5, 3) 
        os = st.slider("Operating Systems", 1, 5, 3) 
        sys_design = st.slider("System Design", 1, 5, 1) 
        
        st.subheader("C. Professional Proof")
        project_depth = st.text_area("Project Depth", placeholder="Briefly describe your best 2 projects and their deployment status.")
        branding_confidence = st.slider("Branding Confidence (Ability to express skills)", 1, 10, 5)
        
        submitted = st.form_submit_button("Complete Setup & Generate Profile", type="primary")
        
        if submitted:
            if not project_depth:
                st.warning("Do not be lazy. Fill in your project depth.")
                return
                
            try:
                # Insert into profiles table [cite: 442]
                supabase.table("profiles").insert({
                    "id": user.id,
                    "college_year": college_year,
                    "target_role": target_role,
                    "target_ecosystem": target_ecosystem,
                    "voice_tone": voice_tone
                }).execute()
                
                # Insert into skill_matrix table [cite: 442]
                supabase.table("skill_matrix").insert({
                    "id": user.id,
                    "dsa": dsa,
                    "oops": oops,
                    "dbms": dbms,
                    "os": os,
                    "system_design": sys_design,
                    "project_depth": project_depth,
                    "branding_confidence": branding_confidence
                }).execute()
                
                st.success("Data ingested successfully. Building your dashboard...")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to save data: {e}. Check your Supabase Row Level Security (RLS) settings.")

def show_main_dashboard():
    """The actual dashboard with Live Widgets """
    st.title("Personal Branding Dashboard ")
    st.write("Optimized Career Growth Strategy & Presence. ")
    
    # Fetch User Context dynamically from Cache
    from core.cache import get_cached_profile, get_cached_skills
    try:
        prof_data_list = get_cached_profile(user.id)
        skill_data_list = get_cached_skills(user.id)
        
        if not prof_data_list or not skill_data_list:
            st.warning("Data sync error. Please re-run onboarding.")
            return

        prof_data = prof_data_list[0]
        skill_data = skill_data_list[0]
        
        target_role = prof_data['target_role']
        target_eco = prof_data['target_ecosystem']
    except Exception as e:
        st.error(f"Failed to load user data: {e}")
        return

    st.markdown(f"**Current Target:** {target_role} at {target_eco}")
    st.divider()

    # Z-Pattern Layout: 2x2 Grid architecture [cite: 116]
    col1, col2 = st.columns(2) 
    
    with col1:
        # Card 1: LinkedIn Optimizer [cite: 117]
        with st.container(border=True): 
            st.subheader("✨ LinkedIn Identity Optimizer")
            st.write("Your headline is your first impression. Our AI analyzes your experience against industry benchmarks.")
            st.caption(f"Configured Tone: {prof_data['voice_tone']}")
            if st.button("Optimize Profile →", key="btn_brand", use_container_width=True):
                st.switch_page("pages/2_Branding.py")
                
        # Card 3: Skill Gap Analyzer 
        with st.container(border=True):
            st.subheader("📊 Skill Gap Analyzer")
            
            # Calculate a quick MNC Readiness average based on the 1-5 scales
            core_avg = (skill_data['dsa'] + skill_data['oops'] + skill_data['dbms'] + skill_data['os'] + skill_data['system_design']) / 25.0 * 100
            st.write(f"Core Fundamentals Match: **{core_avg:.1f}%**")
            st.progress(core_avg / 100.0)
            
            if st.button("View Radar Chart →", key="btn_skills", use_container_width=True):
                st.switch_page("pages/3_Skill_Gap.py")

    with col2:
        # Card 2: Connection Hub [cite: 118]
        with st.container(border=True):
            st.subheader("🤝 Connection Hub")
            st.write("Personal branding isn't just about what you know, but who you know. Find mentors matching your 5-year goals. ")
            st.info(f"Targeting active professionals in: {target_eco}")
            if st.button("Find Mentors →", key="btn_network", use_container_width=True):
                st.switch_page("pages/5_Network.py")
                
        # Card 4: Viral Scorecard [cite: 120]
        with st.container(border=True): 
            st.subheader("🔥 MNC Readiness Score ")
            st.write("Predict the engagement probability of your technical posts before you publish them.")
            st.caption("Powered by Scikit-Learn Random Forest & Gemini ")
            if st.button("Analyze Draft →", key="btn_score", use_container_width=True):
                st.switch_page("pages/4_Scorecard.py")

# --- MAIN LOGIC ROUTER ---
if check_profile_exists():
    show_main_dashboard()
else:
    show_onboarding() 