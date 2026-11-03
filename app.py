import os
from pathlib import Path
import json
import uuid
import streamlit as st
from dotenv import load_dotenv

import importlib
import services.prompts
import services.video
import services.hf_video

# Force reload service modules to prevent stale memory cache in running Streamlit server
importlib.reload(services.prompts)
importlib.reload(services.video)
importlib.reload(services.hf_video)

from services.prompts import generate_scene_plan
from services.video import render_video
from services.hf_video import generate_hf_footage, verify_hf_token

# Load environment variables, overriding to pick up edits in .env dynamically
load_dotenv(override=True)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VIDEO_DIR = DATA_DIR / "videos"
PROMPT_DIR = DATA_DIR / "prompts"
for p in (UPLOAD_DIR, VIDEO_DIR, PROMPT_DIR):
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="EstateMotion AI — Property Video Studio", page_icon="🏡", layout="wide")

# Modern, luxury styling
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1400px;}
.hero {
    padding: 1.8rem 2rem; 
    border-radius: 20px; 
    background: linear-gradient(135deg, #0c1827 0%, #173344 60%, #1f4751 100%); 
    color: white; 
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    border: 1px solid rgba(255,255,255,0.08);
}
.hero h1 {font-size: 2.2rem; font-weight: 700; margin-bottom: 0.4rem; color: #ffffff;}
.hero p {color: #d2e4e4; font-size: 1.05rem; margin-bottom: 0;}
.badge-ai {
    display: inline-block;
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid #10b981;
    color: #34d399;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
}
.badge-photo {
    display: inline-block;
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid #3b82f6;
    color: #60a5fa;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
}
.api-card {
    background: #0f1c29;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR: API KEY TEMPLATES & SETTINGS -----------------
with st.sidebar:
    st.markdown("## 🏡 EstateMotion AI")
    st.caption("AI-Powered Real Estate Video Studio")
    st.divider()

    st.markdown("### 🔑 API Configuration")
    st.caption("Insert your API keys below or in your `.env` file.")

    # Groq API Configuration
    st.markdown("#### ⚡ Groq (Scene Planning LLM)")
    env_groq_key = os.getenv("GROQ_API_KEY", "")
    groq_api_key = st.text_input(
        "Groq API Key",
        value=env_groq_key,
        type="password",
        placeholder="gsk_...",
        help="Obtain from https://console.groq.com/keys"
    )
    groq_model = st.selectbox(
        "Groq Model",
        ["openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"],
        index=0,
        help="Basic Groq model for real estate copywriting and scene planning"
    )

    st.markdown("---")

    # Hugging Face Video API Configuration
    st.markdown("#### 🎬 Hugging Face (AI Video)")
    env_hf_token = os.getenv("HF_TOKEN", "")
    hf_token = st.text_input(
        "Hugging Face Token",
        value=env_hf_token,
        type="password",
        placeholder="hf_...",
        help="Obtain from https://huggingface.co/settings/tokens"
    )
    hf_model = st.text_input(
        "HF Video Model",
        value=os.getenv("HF_MODEL", "Lightricks/LTX-Video"),
        help="Recommended: Lightricks/LTX-Video or stabilityai/stable-video-diffusion-img2vid-xt"
    )
    hf_provider = st.selectbox(
        "HF Inference Provider",
        ["auto", "replicate", "hf-inference", "fal-ai"],
        index=0,
        help="Routing provider for Hugging Face Inference ('auto' dynamically picks the active provider)"
    )

    # Sync into environment
    if groq_api_key.strip():
        os.environ["GROQ_API_KEY"] = groq_api_key.strip()
    if groq_model.strip():
        os.environ["GROQ_MODEL"] = groq_model.strip()
    if hf_token.strip():
        os.environ["HF_TOKEN"] = hf_token.strip()
    if hf_model.strip():
        os.environ["HF_MODEL"] = hf_model.strip()
    if hf_provider.strip():
        os.environ["HF_PROVIDER"] = hf_provider.strip()

    # API Status Check Button
    if st.button("🔍 Check API Status", use_container_width=True):
        col_g, col_h = st.columns(2)
        with col_g:
            if groq_api_key.strip():
                st.success("Groq Key: Set")
            else:
                st.warning("Groq: Not set")
        with col_h:
            if hf_token.strip():
                valid, msg = verify_hf_token(hf_token.strip())
                if valid:
                    st.success("HF: Verified")
                else:
                    st.warning(f"HF: {msg}")
            else:
                st.info("HF: Not set")

    st.divider()
    st.caption("Output Specs: 1080×1920 (9:16 Vertical Reel) · H.264 MP4")


# ----------------- MAIN STUDIO INTERFACE -----------------
st.markdown("""
<div class="hero">
  <h1>Generate AI Property Videos</h1>
  <p>Input listing details, upload property photos, and let Groq + Hugging Face compose a cinematic real-estate promotional film.</p>
</div>
""", unsafe_allow_html=True)

left_col, right_col = st.columns([1.05, 0.95], gap="large")

with left_col:
    st.subheader("01 · Property Details")
    
    with st.form("property_video_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Property Name *", placeholder="e.g. Palm Grove Villa")
        with c2:
            location = st.text_input("Location *", placeholder="e.g. Beverly Hills / Sector 85")

        c3, c4 = st.columns(2)
        with c3:
            price = st.text_input("Price / Starting From", placeholder="e.g. $1,450,000 / ₹2.5 Cr")
        with c4:
            property_type = st.selectbox(
                "Property Type",
                ["Luxury Villa", "Apartment / Penthouse", "Modern House", "Residential Plot", "Commercial Space", "Estate"]
            )

        features = st.text_area(
            "Key Highlights & Amenities",
            placeholder="e.g. 4 Bedrooms, Infinity Pool, Italian Marble Flooring, Panoramic Sunset Views, Smart Automation",
            help="Comma-separated or line-separated features for the AI scriptwriter."
        )

        contact = st.text_input(
            "Contact Details / Outro CTA",
            placeholder="e.g. Call +1 (555) 019-2834 or visit palmresidences.com"
        )

        c5, c6 = st.columns(2)
        with c5:
            style = st.selectbox(
                "Visual Style",
                ["Premium Cinematic", "Warm & Welcoming", "Architectural Modern", "Energetic Commercial"]
            )
        with c6:
            duration = st.select_slider(
                "Target Duration (seconds)",
                options=[15, 20, 25, 30, 35, 40],
                value=25
            )

        # Video Generation Mode Selection
        video_mode = st.radio(
            "Video Generation Mode",
            [
                "⚡ AI-Generated Footage (Hugging Face + Groq)",
                "🎬 Cinematic Photo Motion (Ken Burns Motion + Groq)"
            ],
            index=0,
            help="Choose 'AI-Generated Footage' to synthesize video clips with Hugging Face, or 'Cinematic Photo Motion' for high-quality animated photo transitions."
        )

        uploaded_files = st.file_uploader(
            "Upload Property Photos * (4–8 photos recommended)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True
        )

        submit_btn = st.form_submit_button("🚀 Generate Property Video", type="primary", use_container_width=True)

with right_col:
    st.subheader("02 · Preview & Generation Output")
    
    # Photo Previews
    if uploaded_files:
        st.write(f"**{len(uploaded_files)} photos ready for processing**")
        preview_grid = st.columns(3)
        for i, f in enumerate(uploaded_files[:6]):
            with preview_grid[i % 3]:
                st.image(f, caption=f"Photo {i+1}", use_container_width=True)
        if len(uploaded_files) < 3:
            st.warning("Adding 4 or more photos produces a richer multi-scene video.")
    else:
        st.info("Upload property photos on the left to see thumbnails and generate the video.")


# ----------------- GENERATION PROCESS -----------------
if submit_btn:
    if not name.strip() or not location.strip():
        st.error("Please enter both the Property Name and Location.")
    elif not uploaded_files:
        st.error("Please upload at least one property photo.")
    else:
        property_id = "prop_" + uuid.uuid4().hex[:10]
        prop_upload_dir = UPLOAD_DIR / property_id
        prop_upload_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded photos locally for rendering
        saved_image_paths = []
        for i, item in enumerate(uploaded_files[:8]):
            ext = Path(item.name).suffix.lower() or ".jpg"
            img_file = prop_upload_dir / f"photo_{i+1}{ext}"
            img_file.write_bytes(item.getvalue())
            saved_image_paths.append(str(img_file.relative_to(BASE_DIR)))

        property_data = {
            "property_id": property_id,
            "name": name.strip(),
            "location": location.strip(),
            "price": price.strip(),
            "property_type": property_type,
            "features": [x.strip() for x in features.replace("\n", ",").split(",") if x.strip()],
            "contact": contact.strip(),
            "style": style,
            "duration": int(duration),
            "image_paths": saved_image_paths
        }

        use_hf = "AI-Generated Footage" in video_mode
        actual_mode = "hf_video" if use_hf else "photo_motion"

        with st.status("🎬 Producing Property Film...", expanded=True) as status_box:
            # Step 1: Groq Scene Plan Generation
            st.write("📝 **Step 1/3:** Writing scene plan and script with Groq LLM...")
            try:
                scene_plan = generate_scene_plan(
                    property_data,
                    api_key=groq_api_key.strip(),
                    model=groq_model.strip()
                )
            except TypeError:
                scene_plan = generate_scene_plan(property_data)
            
            # Save prompt JSON
            prompt_file = PROMPT_DIR / f"{property_id}.json"
            prompt_file.write_text(json.dumps(scene_plan, indent=2, ensure_ascii=False), encoding="utf-8")
            st.write(f"• Script status: *{scene_plan.get('status_note', 'Plan generated')}*")

            # Step 2: Hugging Face Video Generation (if selected)
            hf_clips = {}
            if use_hf:
                st.write(f"🤖 **Step 2/3:** Calling Hugging Face Video API (`{hf_model}` via `{hf_provider}`)...")
                hf_output_dir = VIDEO_DIR / property_id / "hf_clips"
                hf_result = generate_hf_footage(
                    plan=scene_plan,
                    property_data=property_data,
                    base_dir=BASE_DIR,
                    output_dir=hf_output_dir,
                    token=hf_token.strip(),
                    model=hf_model.strip(),
                    provider=hf_provider.strip(),
                    max_scenes=2  # Key scenes synthesized with AI video
                )
                
                if hf_result.get("success"):
                    hf_clips = hf_result.get("clips", {})
                    st.write(f"• ✨ {hf_result.get('message')}")
                    actual_mode = "hf_video"
                else:
                    st.warning(f"• Hugging Face note: {hf_result.get('message')}. Rendering with cinematic photo motion.")
                    actual_mode = "photo_motion"
            else:
                st.write("🎬 **Step 2/3:** Using high-definition photo animation with smooth Ken Burns motion.")
                actual_mode = "photo_motion"

            # Step 3: MoviePy Video Composition
            st.write("🎞️ **Step 3/3:** Composing final video, animated captions, branding, and CTA outro card...")
            final_video_path = VIDEO_DIR / f"{property_id}.mp4"
            try:
                render_video(
                    property_data=property_data,
                    plan=scene_plan,
                    base_dir=BASE_DIR,
                    output_path=final_video_path,
                    hf_clips=hf_clips
                )
                status_box.update(label="✅ Property Video Generated Successfully!", state="complete", expanded=False)
                
                # Display prominently in main view right below status
                st.markdown("---")
                st.subheader("🎬 Generated Property Video")
                
                badge_html = '<span class="badge-ai">✨ AI-GENERATED FOOTAGE (Hugging Face)</span>' if actual_mode == "hf_video" else '<span class="badge-photo">🎬 CINEMATIC PHOTO MOTION</span>'
                st.markdown(badge_html, unsafe_allow_html=True)
                st.write("")
                
                v_col1, v_col2 = st.columns([1.2, 0.8])
                with v_col1:
                    st.video(str(final_video_path))
                    st.download_button(
                        label="⬇️ Download MP4 Video",
                        data=final_video_path.read_bytes(),
                        file_name=f"{name.replace(' ', '_')}_video.mp4",
                        mime="video/mp4",
                        type="primary",
                        use_container_width=True
                    )
                with v_col2:
                    st.success("✅ Video rendered successfully!")
                    st.write(f"**Title:** {scene_plan.get('title', name)}")
                    st.write(f"**Duration:** ~{property_data.get('duration', 25)} seconds")
                    st.write(f"**Scenes:** {len(scene_plan.get('scenes', []))} + Closing CTA Outro")
                    with st.expander("🔍 View Scene Plan JSON"):
                        st.json(scene_plan)

                # Also update right preview column
                with right_col:
                    st.success("Video ready below!")

            except Exception as e:
                status_box.update(label="❌ Video Composition Error", state="error", expanded=True)
                st.error(f"Render failed: {e}")
                st.caption("Ensure FFmpeg is installed and accessible on PATH.")
