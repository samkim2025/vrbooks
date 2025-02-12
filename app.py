import streamlit as st
import torch
import numpy as np
from diffusers import StableDiffusionPipeline
import torch.nn.functional as F
from PIL import Image
import cv2

# ------------------------------------------------------------------------------
# CACHE THE MODELS FOR EFFICIENT REUSE
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
# IMPLEMENTATION OF generate_scene(prompt)
# ------------------------------------------------------------------------------

def generate_scene(prompt: str) -> Image.Image:
    """
    Generate a pseudo-3D scene from a text prompt.
    
    Steps:
      1. Generate a 2D image from text using Stable Diffusion.
      2. Estimate a depth map from the generated image using MiDaS.
      3. Apply a simple warp effect to the image based on the depth map
         to simulate a 3D perspective shift.
    
    Returns:
      A PIL Image representing the "3D" scene.
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    with st.spinner("Loading AI models, please wait..."):
        pipe = load_sd_pipeline()
        midas, transform = load_midas()

    # Step 1: Generate a 2D image from the text prompt.
    # (Note: using autocast for performance on GPU)
    with torch.autocast(device):
        result = pipe(prompt)
    image = result.images[0]
    image = image.convert("RGB")
    image_np = np.array(image)

    # Step 2: Estimate the depth map using MiDaS.
    input_batch = transform(image).to(device)
    with torch.no_grad():
        prediction = midas(input_batch)
        # Resize depth map to the same size as the image.
        prediction = F.interpolate(
            prediction.unsqueeze(1),
            size=image_np.shape[:2],
            mode="bicubic",
            align_corners=False
        ).squeeze()
    depth_map = prediction.cpu().numpy()

    # Normalize the depth map to the range [0, 255].
    depth_min, depth_max = depth_map.min(), depth_map.max()
    depth_map_norm = ((depth_map - depth_min) / (depth_max - depth_min) * 255).astype(np.uint8)

    # Step 3: Create a simple warp effect.
    # For each row in the image, compute a horizontal offset based on the average depth.
    height, width, _ = image_np.shape
    warped_image = np.zeros_like(image_np)
    for i in range(height):
        # Compute offset: deeper areas (brighter in depth_map_norm) get a larger offset.
        row_depth = depth_map_norm[i, :]
        offset = int(np.mean(row_depth) / 255 * 20)  # maximum offset of ~20 pixels
        if offset > 0:
            warped_image[i, offset:] = image_np[i, :-offset]
            warped_image[i, :offset] = image_np[i, 0:1]  # fill left gap with first column
        else:
            warped_image[i] = image_np[i]

    # Convert the warped image back to a PIL Image.
    warped_image_pil = Image.fromarray(warped_image)
    return warped_image_pil
