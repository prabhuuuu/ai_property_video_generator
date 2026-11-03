# EstateMotion AI — Property Video Studio

A Streamlit application that transforms property details and uploaded photos into cinematic promotional MP4 listing videos. Combines **Groq Chat Completions** for structured scene planning and copywriting with **Hugging Face Inference Providers** for AI video generation, composed via **MoviePy and FFmpeg**.

---

## Architecture & Features

- **Streamlit Property Studio**: Clean interface for property metadata (Name, Location, Price, Highlights, Contact CTA, Duration, Style) and multi-photo uploads.
- **Dual Video Generation Modes**:
  - ⚡ **AI-Generated Footage**: Synthesizes video clips using Hugging Face video models (`Lightricks/LTX-Video` via providers like `fal-ai`, `replicate`, or `hf-inference`).
  - 🎬 **Cinematic Photo Motion**: High-definition Ken Burns photo animation with smooth directional camera pans, zooms, and glassmorphism captions.
- **Groq LLM Copywriting**: Produces structured scene plans, captions, voiceover scripts, and outro CTAs grounded strictly in provided property facts.
- **MoviePy & FFmpeg Video Composition**: Composites video footage/animated photos with luxury typography, floating glassmorphism cards, animated progress bar, and a dedicated closing CTA outro card.
- **API Key Configuration**: Accepts keys directly in `.env` or live in the Streamlit sidebar with immediate status verification.

---

## Tech Stack

- **Frontend**: Streamlit
- **LLM / Scene Planning**: Groq Chat Completions API (`llama-3.3-70b-versatile`)
- **AI Video Generation**: Hugging Face Inference API / Providers (`huggingface_hub`)
- **Video Rendering & Composition**: MoviePy 2.x + Pillow + FFmpeg
- **Configuration**: `python-dotenv` and `.env`

---

## API Configuration

A template `.env` file is provided in the project root:

```env
# Groq API Configuration (for structured scene planning)
# Get a key from https://console.groq.com/keys
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile

# Hugging Face Configuration (for AI video generation)
# Get a token from https://huggingface.co/settings/tokens
HF_TOKEN=
HF_MODEL=Lightricks/LTX-Video
HF_PROVIDER=fal-ai
```

> **Note:** You can also insert or update your API keys directly in the Streamlit sidebar at any time.

---

## Quick Start

### 1. Activate Environment & Install Dependencies

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure API Keys

Open `.env` and insert your `GROQ_API_KEY` and `HF_TOKEN`.

### 3. Launch the Application

```powershell
streamlit run app.py
```

---

## Workflow Guide

1. **Enter API Keys**: Input your Groq API Key and Hugging Face Token in `.env` or the sidebar and click **Check API Status**.
2. **Fill Property Details**: Provide Property Name, Location, Price, Type, Highlights, and Contact CTA.
3. **Upload Photos**: Upload 4–8 property images.
4. **Select Mode**:
   - Select **AI-Generated Footage** to generate AI video scenes with Hugging Face.
   - Select **Cinematic Photo Motion** for instant, high-definition photo animation.
5. **Generate & Preview**: Click **Generate Property Video**. Watch the real-time generation steps, preview the MP4, download the video, and inspect the raw scene plan JSON.
