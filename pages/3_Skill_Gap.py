import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import joblib
from core.database import supabase
from utils.engine import get_gemini_response
from core.auth import logout_user
from core.cache import force_clear_cache

# 1. Security Check
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

# 2. Unified Custom Sidebar Navigation
with st.sidebar:
    st.title("Career AI Hub")
    st.page_link("pages/1_Dashboard.py", label="Dashboard", icon="🏠")
    st.page_link("pages/2_Branding.py", label="LinkedIn Optimizer", icon="✨")
    st.page_link("pages/3_Skill_Gap.py", label="Skill Gap Analyzer", icon="📊")
    st.page_link("pages/4_Scorecard.py", label="Viral Scorecard", icon="🔥")
    st.page_link("pages/5_Network.py", label="Connection Hub", icon="🤝")
    st.divider()
    
    # The Manual Clear Cache Button
    if st.button("🔄 Sync Data (Clear Cache)", use_container_width=True):
        force_clear_cache()
        st.success("Cache cleared. Data synced.")
        st.rerun()
        
    st.button("Logout", on_click=logout_user, use_container_width=True)

st.title("📊 Skill Gap Analyzer")
st.write("Compare your current technical DNA against your dream job requirements.")

# --- THE MEMORY ENGINE (Keeps roadmap on screen during feedback) ---
if "current_roadmap" not in st.session_state:
    st.session_state.current_roadmap = None
if "refinement_history" not in st.session_state:
    st.session_state.refinement_history = []

# 3. Fetch Contextual User Data from Cache
from core.cache import get_cached_skills, get_cached_profile

user_id = st.session_state["user"].id

try:
    # Fetch BOTH skills and profile from the cache
    skills_data = get_cached_skills(user_id)
    profile_data = get_cached_profile(user_id)
    
    if not skills_data or not profile_data:
        st.warning("Data missing. Please complete Onboarding first.")
        st.stop()
        
    user_skills = skills_data[0]
    user_profile = profile_data[0]
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

categories = ['DSA', 'OOPS', 'DBMS', 'OS', 'System Design']
user_values = [
    user_skills.get('dsa', 1), user_skills.get('oops', 1), user_skills.get('dbms', 1), 
    user_skills.get('os', 1), user_skills.get('system_design', 1)
]

# 4. Target Input
target_job = st.text_input("Where do you want to go next?", value=user_profile.get('target_role', 'SDE'))

if target_job:
    # --- DYNAMIC TARGET MAPPING LOGIC ---
    job_upper = target_job.upper()
    if "FRONTEND" in job_upper or "UI" in job_upper:
        target_values = [3, 3, 2, 2, 3] 
    elif "BACKEND" in job_upper:
        target_values = [4, 4, 5, 4, 4] 
    elif "DATA" in job_upper or "ML" in job_upper or "AI" in job_upper:
        target_values = [4, 3, 4, 3, 3] 
    elif "DEVOPS" in job_upper or "CLOUD" in job_upper:
        target_values = [3, 3, 4, 5, 4] 
    elif "FULL STACK" in job_upper:
        target_values = [4, 4, 4, 3, 4]
    elif "SDE" in job_upper or "GOOGLE" in job_upper or "MICROSOFT" in job_upper:
        target_values = [5, 4, 4, 4, 5]
    else:
        target_values = [4, 4, 4, 3, 3] # Default Baseline

    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("Visual Analysis")
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=user_values + [user_values[0]], theta=categories + [categories[0]], fill='toself', name='Your Skills', line_color='#3b82f6'))
            fig.add_trace(go.Scatterpolar(r=target_values + [target_values[0]], theta=categories + [categories[0]], fill='toself', name='Target Requirements', line_color='#10b981'))
            
            # CSS Overrides for Dark Mode Radar Chart
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5], gridcolor="rgba(255,255,255,0.2)")), 
                showlegend=True, 
                margin=dict(l=40, r=40, t=40, b=40),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            try:
                kmeans = joblib.load('ml_models/skill_clusterer.pkl')
                cluster_id = kmeans.predict([user_values])[0]
                
                # The 10 Persona Mapping Dictionary
                persona_map = {
                    0: "The Competitive Programmer",
                    1: "The Backend Architect",
                    2: "The DevOps / SRE",
                    3: "The Database Administrator",
                    4: "The Systems Programmer",
                    5: "The Core Generalist",
                    6: "The UI/Frontend Specialist",
                    7: "The Academic Beginner",
                    8: "The Enterprise Java Dev",
                    9: "The FAANG Unicorn"
                }
                
                detected_persona = persona_map.get(cluster_id, "Unknown Entity")
                
                st.markdown(f"### 🤖 ML Persona Detected:")
                st.info(f"**{detected_persona}**")
            except Exception as e:
                st.caption(f"ML Clusterer Offline: {e}")

    with col2:
        with st.container(border=True):
            st.subheader("Adaptive Roadmap Engine")
            
            # --- EXPLICIT PRE-PREFERENCE ---
            st.write("**Step 1: Set Generation Preferences**")
            strategy = st.selectbox("Learning Strategy", ["Project-Heavy Execution", "Theory & Fundamentals First", "Strict FAANG Interview Prep"])
            timeline = st.slider("Timeline (Months)", 1, 6, 3)
            
            gaps = {cat: (tgt - usr) for cat, usr, tgt in zip(categories, user_values, target_values) if tgt > usr}
            
            # Show a success message if they are strong, but DO NOT hide the button
            if not gaps:
                st.success("Your fundamentals match or exceed the requirements. Time to focus on advanced project execution.")
                gap_str = "None. Fundamentals are strong. Focus strictly on advanced project building and system design."
            else:
                gap_str = ", ".join([f"{k} (-{v})" for k, v in gaps.items()])
                
            # The button is now outside the if/else block. It always renders.
            if st.button("Generate Action Plan", type="primary", use_container_width=True):
                with st.spinner("Compiling personalized roadmap..."):
                    
                    prompt = f"User aims for '{target_job}'. Gaps: {gap_str}. Strategy: {strategy}. Timeline: {timeline} months. Generate a strict markdown checklist to advance their career. If there are no gaps, generate an advanced project roadmap. Keep it under 10 lines."
                    
                    # Inject past iterative feedback if it exists
                    if st.session_state.refinement_history:
                        prompt += f"\n\nCRITICAL INSTRUCTION - Adjust the output based on this user feedback: {st.session_state.refinement_history[-1]}"
                        
                    st.session_state.current_roadmap = get_gemini_response(prompt)
                    st.rerun()

# --- POST-GENERATION ITERATIVE FEEDBACK LOOP ---
if st.session_state.current_roadmap:
    st.divider()
    st.subheader("Your Custom Action Plan")
    with st.container(border=True):
        st.markdown(st.session_state.current_roadmap)
        
        st.write("---")
        st.write("**Step 2: AI Alignment Feedback**")
        fb_col1, fb_col2 = st.columns(2)
        
        with fb_col1:
            if st.button("👍 Perfect, Lock it in", use_container_width=True):
                try:
                    supabase.table("feedback_history").insert({
                        "user_id": user_id,
                        "feature_name": "Skill Gap Roadmap",
                        "is_helpful": True,
                        "missing_element": "None"
                    }).execute()
                    st.success("Roadmap saved and feedback logged to database!")
                    st.session_state.current_roadmap = None # Clear memory for next task
                    st.session_state.refinement_history = []
                    st.rerun()
                except Exception as e:
                    st.error(f"DB Error: {e}")
                    
        with fb_col2:
            with st.popover("👎 Needs Changes (Iterate)", use_container_width=True):
                refinement = st.text_input("What should I change? (e.g., 'Make it harder', 'Focus more on DBMS')")
                if st.button("Log Feedback & Prepare Regeneration"):
                    if refinement:
                        st.session_state.refinement_history.append(refinement)
                        try:
                            supabase.table("feedback_history").insert({
                                "user_id": user_id,
                                "feature_name": "Skill Gap Roadmap",
                                "is_helpful": False,
                                "missing_element": refinement
                            }).execute()
                        except:
                            pass
                        st.info("Feedback logged. Click 'Generate Action Plan' above to apply changes.")
                    else:
                        st.warning("Do not be lazy. Specify what to change.")