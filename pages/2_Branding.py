import streamlit as st
import requests
import io
from PIL import Image
from core.database import supabase
from utils.engine import get_gemini_response
from core.auth import logout_user
from core.auth import logout_user
from core.cache import force_clear_cache

# 1. Security Check
if not st.session_state.get("authenticated", False):
    st.switch_page("app.py")

user_id = st.session_state["user"].id



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

st.title("✨ LinkedIn Identity Optimizer")
st.write("Transform your profile from a student resume into an MNC-ready professional identity.")

# --- THE MEMORY ENGINE ---
if "opt_headline" not in st.session_state:
    st.session_state.opt_headline = None
if "opt_about" not in st.session_state:
    st.session_state.opt_about = None
if "branding_refinements" not in st.session_state:
    st.session_state.branding_refinements = []

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
    target_ecosystem = user_profile['target_ecosystem']
    default_tone = user_profile['voice_tone']
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# 4. Input & Preferences Layout
with st.container(border=True):
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Current Presence")
        current_headline = st.text_area("Current Headline", placeholder="e.g., Student at RGUKT | Learning Python")
        current_about = st.text_area("About Section", placeholder="Paste your current about section here...", height=150)
        
    with col2:
        st.subheader("Optimization Settings")
        st.write("**Step 1: Set Generation Preferences**")
        active_tone = st.selectbox("Brand Tone", ["Professional", "Energetic", "Authoritative", "Empathetic", "Witty"], index=["Professional", "Energetic", "Authoritative", "Empathetic", "Witty"].index(default_tone))
        focus_area = st.selectbox("Primary Focus", ["Keyword Optimization (SEO)", "Storytelling & Journey", "Metric & Impact Driven"])
        
        analyze_profile = st.button("Generate Optimized Profile", type="primary", use_container_width=True)

# 5. Intelligence Layer (Text Optimization)
if analyze_profile:
    if not current_headline or not current_about:
        st.warning("Provide both your current headline and about section for a complete analysis.")
    else:
        with st.spinner("Analyzing profile and generating improvements..."):
            
            # Construct the Adaptive Prompt
            rewrite_prompt = f"""
            Rewrite this LinkedIn profile for a user targeting a {target_role} role at a {target_ecosystem}.
            Tone: {active_tone}. Focus Area: {focus_area}.
            
            Original Headline: {current_headline}
            Original About: {current_about}
            
            Format your response exactly like this:
            [NEW HEADLINE]
            (Write the new headline here)
            
            [NEW ABOUT]
            (Write the new about section here)
            """
            
            # Inject iterative feedback memory
            if st.session_state.branding_refinements:
                rewrite_prompt += f"\n\nCRITICAL INSTRUCTION - Adjust the output strictly based on this previous feedback: {st.session_state.branding_refinements[-1]}"
            
            rewrite_response = get_gemini_response(rewrite_prompt)
            
            try:
                st.session_state.opt_headline = rewrite_response.split("[NEW HEADLINE]")[1].split("[NEW ABOUT]")[0].strip()
                st.session_state.opt_about = rewrite_response.split("[NEW ABOUT]")[1].strip()
            except:
                st.session_state.opt_headline = "Error parsing AI response."
                st.session_state.opt_about = rewrite_response
            
            st.rerun()

# --- POST-GENERATION ITERATIVE FEEDBACK LOOP ---
if st.session_state.opt_headline and st.session_state.opt_about:
    st.divider()
    st.subheader("AI Suggested Improvements")
    
    with st.container(border=True):
        opt_col1, opt_col2 = st.columns(2)
        with opt_col1:
            st.text_area("Optimized Headline", value=st.session_state.opt_headline, height=100)
        with opt_col2:
            st.text_area("Optimized About Section", value=st.session_state.opt_about, height=250)
            
        st.write("---")
        st.write("**Step 2: AI Alignment Feedback**")
        fb_col1, fb_col2 = st.columns(2)
        
        with fb_col1:
            if st.button("👍 Looks great, save feedback", use_container_width=True):
                try:
                    supabase.table("feedback_history").insert({
                        "user_id": user_id,
                        "feature_name": "LinkedIn Optimizer",
                        "is_helpful": True,
                        "missing_element": "None"
                    }).execute()
                    st.success("Feedback logged! Copy your text and update your LinkedIn.")
                    # Clear memory so they can start a fresh generation later
                    st.session_state.opt_headline = None
                    st.session_state.opt_about = None
                    st.session_state.branding_refinements = []
                except Exception as e:
                    st.error(f"DB Error: {e}")
                    
        with fb_col2:
            with st.popover("👎 Needs Changes (Iterate)", use_container_width=True):
                refinement = st.text_input("What should I change? (e.g., 'Make the headline punchier', 'Shorter about section')")
                if st.button("Log Feedback & Prepare Regeneration", key="brand_regen"):
                    if refinement:
                        st.session_state.branding_refinements.append(refinement)
                        try:
                            supabase.table("feedback_history").insert({
                                "user_id": user_id,
                                "feature_name": "LinkedIn Optimizer",
                                "is_helpful": False,
                                "missing_element": refinement
                            }).execute()
                        except:
                            pass
                        st.info("Feedback logged. Click 'Generate Optimized Profile' above to apply changes.")
                    else:
                        st.warning("Specify what to change.")

# 6. Banner Studio (Un-indented so it always shows)
st.divider()
st.subheader("🎨 Banner Studio (Experimental)")
st.write("Generate a professional LinkedIn background banner to match your new personal brand.")

with st.container(border=True):
    banner_col1, banner_col2 = st.columns([1, 2])
    
    with banner_col1:
        banner_style = st.selectbox(
            "Visual Style", 
            ["Professional Blue Tech Modern", "Dark Mode Minimalist", "Creative Startup Vibrant", "Corporate Abstract"]
        )
        generate_img_btn = st.button("Generate Banner", type="secondary", use_container_width=True)
        
    with banner_col2:
        if generate_img_btn:
            with st.spinner("Calling Hugging Face Diffusion API (This may take 20-40 seconds)..."):
                
                API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
                headers = {"Authorization": f"Bearer {st.secrets.get('HF_TOKEN_1')}"}
            

                img_prompt = f"A professional LinkedIn background banner for a {target_role}, style: {banner_style}, high resolution, clean corporate aesthetic, abstract geometric shapes, no text, no words."
                
                try:
                    img_response = requests.post(API_URL, headers=headers, json={"inputs": img_prompt})
                    
                    if img_response.status_code == 200:
                        image = Image.open(io.BytesIO(img_response.content))
                        st.image(image, caption=f"Generated: {banner_style}", use_container_width=True)
                    else:
                        st.error(f"Image API Error: {img_response.status_code}. The model might be loading.")
                except Exception as e:
                    st.error(f"Failed to connect to image generator: {e}")
        else:
            st.info("Click 'Generate Banner' to create a custom background image. Warning: High latency.")