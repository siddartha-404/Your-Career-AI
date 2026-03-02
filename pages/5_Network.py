import streamlit as st
import requests
import json
import urllib.parse
from core.database import supabase
from utils.engine import get_gemini_response
from core.key_manager import key_manager
from core.auth import logout_user
from core.auth import logout_user
from core.cache import force_clear_cache

# 1. Security Check
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

# --- INITIALIZE ROUND ROBIN STATE ---
if "serper_index" not in st.session_state:
    st.session_state.serper_index = 0
    
user_id = st.session_state["user"].id



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

st.title("🤝 Connection Hub")
st.write("Discover industry leaders and let AI generate your personalized outreach pitches.")

# --- THE MEMORY ENGINE ---
if "live_mentors" not in st.session_state:
    st.session_state.live_mentors = []
if "network_refinements" not in st.session_state:
    st.session_state.network_refinements = []

# 3. Fetch User Context from Cache
from core.cache import get_cached_profile
user_id = st.session_state["user"].id
try:
    profile_data = get_cached_profile(user_id)
    if not profile_data:
        st.error("Profile data missing. Please complete Onboarding.")
        st.stop()
    user_profile = profile_data[0]
    target_role = user_profile['target_role']
    target_eco = user_profile['target_ecosystem']
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# 4. Agentic Search Logic
def search_mentors(role, eco, strategy):
    # Phase 1: AI generates optimal search query
    query_prompt = f"Generate a strict Google search query to find LinkedIn profiles of professionals. Target: {role} at {eco}. Strategy: {strategy}. Return ONLY the search string, no quotes. Example: site:linkedin.com/in/ 'Senior Software Engineer' 'Google'."
    search_query = get_gemini_response(query_prompt).strip()
    
    # Phase 2: Serper.ai execution via Round Robin
    try:
        serper_key = key_manager.get_next_serper_key()
    except Exception as e:
        st.error(str(e))
        return None

    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": search_query, "num": 1}) # Fetch 4 profiles for a good UI grid
    headers = {
        'X-API-KEY': serper_key,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json().get('organic', [])
    except Exception as e:
        st.error(f"Network request failed: {e}")
        return None

# 5. UI Preferences & Generation
with st.container(border=True):
    st.write("**Step 1: Set Networking Strategy**")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        net_strategy = st.selectbox("Search Focus", ["Direct Role Match (Seniors)", "Technical Recruiters / HR", "Startup Founders / CTOs"])
    with col_s2:
        pitch_tone = st.selectbox("Pitch Tone", ["Curious Student", "Aggressive Value-Add", "Polite & Professional"])
        
    if st.button("Find Matching Mentors", type="primary", use_container_width=True):
        with st.spinner("Executing Real-Time RAG Pipeline via Google Search..."):
            raw_mentors = search_mentors(target_role, target_eco, net_strategy)
            
            if not raw_mentors:
                st.error("Search Engine API failed. Check your Serper API keys.")
            else:
                st.session_state.live_mentors = [] # Clear old results
                
                for m in raw_mentors:
                    raw_title = m.get('title', 'LinkedIn Member').replace('- LinkedIn', '').strip()
                    # Parse Name and Role from Google Title
                    title_parts = raw_title.split(' - ')
                    name = title_parts[0] if len(title_parts) > 0 else "Professional"
                    role_info = " - ".join(title_parts[1:]) if len(title_parts) > 1 else "Industry Professional"
                    
                    link = m.get('link', '#')
                    snippet = m.get('snippet', 'No snippet available.')
                    
                    # AI Pitch Generation
                    pitch_prompt = f"Write a 1-sentence personalized LinkedIn connection request pitch to {name}, who is a {role_info}. The user is a student aiming for a {target_role} role. Tone: {pitch_tone}. Context from their profile: '{snippet}'. Keep it under 20 words."
                    
                    if st.session_state.network_refinements:
                        pitch_prompt += f" Apply this feedback to the pitch: {st.session_state.network_refinements[-1]}"
                        
                    pitch = get_gemini_response(pitch_prompt)
                    
                    st.session_state.live_mentors.append({
                        "name": name,
                        "role": role_info,
                        "link": link,
                        "pitch": pitch
                    })
                st.rerun()

# 6. Result Dashboard & Feedback Loop
if st.session_state.live_mentors:
    st.divider()
    st.subheader(f"📡 Discovered {len(st.session_state.live_mentors)} Active Leaders")
    
    for i, mentor in enumerate(st.session_state.live_mentors):
        with st.container(border=True):
            card_col1, card_col2 = st.columns([1, 4])
            
            with card_col1:
                # Dynamic Avatar Generation
                safe_name = urllib.parse.quote(mentor['name'])
                avatar_url = f"https://ui-avatars.com/api/?name={safe_name}&background=random&color=fff&size=128&bold=true"
                st.image(avatar_url, use_container_width=True)
                
            with card_col2:
                st.subheader(mentor['name'])
                st.caption(mentor['role'])
                st.write(f"**AI Synergy Pitch:** {mentor['pitch']}")
                
                # Action Buttons side-by-side
                act_col1, act_col2 = st.columns([1, 1])
                with act_col1:
                    st.link_button("View Profile", mentor['link'], use_container_width=True)
                with act_col2:
                    if st.button("👍 Good Pitch", key=f"good_{i}", use_container_width=True):
                        try:
                            supabase.table("feedback_history").insert({
                                "user_id": user_id,
                                "feature_name": "Connection Hub Pitch",
                                "is_helpful": True,
                                "missing_element": "None"
                            }).execute()
                            st.toast("Feedback logged!")
                        except:
                            pass

    # Universal RAG Feedback
    st.write("---")
    with st.popover("👎 Pitches need adjustment?", use_container_width=True):
        refinement = st.text_input("How should the AI adjust the next batch of pitches?")
        if st.button("Log Feedback"):
            if refinement:
                st.session_state.network_refinements.append(refinement)
                try:
                    supabase.table("feedback_history").insert({
                        "user_id": user_id,
                        "feature_name": "Connection Hub Pitch",
                        "is_helpful": False,
                        "missing_element": refinement
                    }).execute()
                except:
                    pass
                st.info("Feedback logged. Click 'Find Matching Mentors' to generate a new batch with these rules.")