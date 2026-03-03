import streamlit as st
import time
from core.database import supabase
from core.auth import logout_user
from core.cache import force_clear_cache

# 1. Security Check
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

user_id = st.session_state["user"].id

# 2. Unified Navigation Menu
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

st.title("⚙️ Profile & Skill Settings")
st.write("Update your career trajectory. The AI will immediately adapt your roadmaps and scores.")

# 3. Fetch Current Data
try:
    prof_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
    skill_res = supabase.table("skill_matrix").select("*").eq("id", user_id).execute()
    
    if not prof_res.data or not skill_res.data:
        st.error("Data missing. Please return to onboarding.")
        st.stop()
        
    p_data = prof_res.data[0]
    s_data = skill_res.data[0]
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# 4. The Unified Edit Form
with st.form("edit_master_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Career Ambition")
        new_role = st.selectbox(
            "Target Role", 
            ["SDE", "ML Engineer", "Data Scientist", "DevOps", "Full Stack", "Competitive Programmer"],
            index=["SDE", "ML Engineer", "Data Scientist", "DevOps", "Full Stack", "Competitive Programmer"].index(p_data.get('target_role', 'SDE'))
        )
        new_eco = st.selectbox(
            "Target Ecosystem", 
            ["FAANG/Big Tech", "Product-Based Startups", "Service-Based Companies"],
            index=["FAANG/Big Tech", "Product-Based Startups", "Service-Based Companies"].index(p_data.get('target_ecosystem', 'FAANG/Big Tech'))
        )
        new_tone = st.selectbox(
            "Preferred Branding Tone", 
            ["Professional", "Energetic", "Authoritative", "Empathetic", "Witty"],
            index=["Professional", "Energetic", "Authoritative", "Empathetic", "Witty"].index(p_data.get('voice_tone', 'Professional'))
        )

    with col2:
        st.subheader("Technical DNA")
        new_dsa = st.slider("DSA", 1, 5, s_data.get('dsa', 3))
        new_oops = st.slider("OOPS", 1, 5, s_data.get('oops', 3))
        new_dbms = st.slider("DBMS", 1, 5, s_data.get('dbms', 3))
        new_os = st.slider("OS", 1, 5, s_data.get('os', 3))
        new_sys = st.slider("System Design", 1, 5, s_data.get('system_design', 1))

    # Single submit button at the bottom of the form
    st.divider()
    submitted = st.form_submit_button("Save All Settings", type="primary", use_container_width=True)

    if submitted:
        with st.spinner("Syncing to database..."):
            try:
                # Update Profiles
                supabase.table("profiles").update({
                    "target_role": new_role,
                    "target_ecosystem": new_eco,
                    "voice_tone": new_tone
                }).eq("id", user_id).execute()
                
                # Update Skills
                supabase.table("skill_matrix").update({
                    "dsa": new_dsa,
                    "oops": new_oops,
                    "dbms": new_dbms,
                    "os": new_os,
                    "system_design": new_sys
                }).eq("id", user_id).execute()
                
                # Show success message and pause before refreshing
                st.success("✅ Profile and Skills updated successfully! Dashboard metrics recalculated.")
                time.sleep(1.5) 
                st.rerun()
                
            except Exception as e:
                st.error(f"Update failed: {e}")