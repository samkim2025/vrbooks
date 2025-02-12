import streamlit as st
import torch
import numpy as np
from diffusers import StableDiffusionPipeline
import torch.nn.functional as F
from PIL import Image
import io
import zipfile

# ------------------------------------------------------------------------------
# SECTION 1: PAGE CONFIGURATION & SESSION STATE INITIALIZATION
# ------------------------------------------------------------------------------

st.set_page_config(page_title="VR Storyteller", layout="wide")

# Initialize session state variables if not already set
if 'project_title' not in st.session_state:
    st.session_state.project_title = ""
if 'pages' not in st.session_state:
    # Each page is a dict with: 'prompt' (str), 'scene' (Image), 'approved' (bool)
    st.session_state.pages = []
if 'current_page_index' not in st.session_state:
    st.session_state.current_page_index = 0
if 'project_confirmed' not in st.session_state:
    st.session_state.project_confirmed = False

# ------------------------------------------------------------------------------
# SECTION 2: MODEL LOADING FUNCTIONS (CACHED)
# ------------------------------------------------------------------------------

@st.cache_resource
def load_sd_pipeline():
    """
    Loads the Stable Diffusion pipeline.
    If a GPU is available, it uses half precision for faster inference.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(
        "CompVis/stable-diffusion-v1-4",
        torch_dtype=dtype
    )
    pipe = pipe.to(device)
    return pipe

@st.cache_resource
def load_midas():
    """
    Loads the MiDaS model (using the small version) for depth estimation.
    Also returns the associated image transform.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
    midas.to(device)
    midas.eval()
    transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
    transform = transforms.small_transform
    return midas, transform

# ------------------------------------------------------------------------------
# SECTION 3: ACTUAL SCENE GENERATION FUNCTION
# ------------------------------------------------------------------------------

def generate_scene(prompt: str) -> Image.Image:
    """
    Generate a pseudo-3D scene from a text prompt using AI.
    
    Steps:
      1. Generate a 2D image from text using Stable Diffusion.
      2. Estimate a depth map from the generated image using MiDaS.
      3. Apply a simple warp effect to the image based on the depth map
         to simulate a 3D perspective shift.
    
    Returns:
      A PIL Image representing the generated "3D" scene.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    with st.spinner("Loading AI models, please wait..."):
        pipe = load_sd_pipeline()
        midas, trans
