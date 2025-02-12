import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

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
# SECTION 2: UTILITY FUNCTIONS
# ------------------------------------------------------------------------------

def generate_scene(prompt):
    """
    Dummy scene generation function.
    For now, creates a placeholder image with the prompt text overlay.
    Replace with your AI text-to-3D pipeline later.
    """
    # Create a blank image
    width, height = 640, 480
    img = Image.new('RGB', (width, height), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    
    # Prepare prompt text (limited to 50 characters for display)
    display_text = f"Scene for: {prompt[:50]}..." if prompt else "No prompt provided"
    
    # Draw text (centered roughly)
    text_position = (20, height // 2 - 10)
    d.text(text_position, display_text, fill=(255, 255, 0))
    
    return img

def add_new_page():
    """
    Adds a new blank page to the project.
    """
    new_page = {'prompt': "", 'scene': None, 'approved': False}
    st.session_state.pages.append(new_page)
    st.session_state.current_page_index = len(st.session_state.pages) - 1

def update_scene_for_current_page():
    """
    Generate and update the scene for the current page.
    """
    current_page = st.session_state.pages[st.session_state.current_page_index]
    prompt = current_page.get('prompt', "")
    if prompt:
        current_page['scene'] = generate_scene(prompt)
    else:
        st.warning("Enter a prompt before generating a scene.")

def approve_current_page(approval=True):
    """
    Mark the current page as approved or not approved.
    """
    st.session_state.pages[st.session_state.current_page_index]['approved'] = approval

def confirm_project():
    """
    Mark the project as confirmed (compiling the approved pages).
    """
    # In a future version, you can add additional processing to create a VR book.
    st.session_state.project_confirmed = True

def navigate_page(delta):
    """
    Navigate between pages by changing the current page index.
    """
    new_index = st.session_state.current_page_index + delta
    if 0 <= new_index < len(st.session_state.pages):
        st.session_state.current_page_index = new_index
    else:
        st.warning("No more pages in that direction.")

# ------------------------------------------------------------------------------
# SECTION 3: STREAMLIT INTERFACE
# ------------------------------------------------------------------------------

def main():
    st.title("VR Storyteller: Create Your Immersive VR Experience")
    
    # Sidebar for project-level controls
    with st.sidebar:
        st.header("Project Settings")
        st.session_state.project_title = st.text_input("Project Title", st.session_state.project_title)
        
        st.markdown("### Page Management")
        if st.button("Add New Page"):
            add_new_page()
        st.markdown("---")
        
        if st.session_state.pages:
            st.write(f"Current Page: {st.session_state.current_page_index + 1} of {len(st.session_state.pages)}")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous Page"):
                    navigate_page(-1)
            with col2:
                if st.button("Next Page →"):
                    navigate_page(1)
    
    st.markdown("---")
    
    # Main area for page content
    if st.session_state.pages:
        current_page = st.session_state.pages[st.session_state.current_page_index]
        
        st.header(f"Page {st.session_state.current_page_index + 1}")
        # Text input for scene prompt
        new_prompt = st.text_area("Enter your scene description (text prompt)", value=current_page.get('prompt', ""), height=150)
        # Update the prompt in the session state
        current_page['prompt'] = new_prompt
        
        col_gen, col_app = st.columns(2)
        with col_gen:
            if st.button("Generate Scene"):
                update_scene_for_current_page()
        with col_app:
            if st.button("Approve Scene"):
                approve_current_page(True)
                st.success("Scene approved!")
            if st.button("Reject Scene"):
                approve_current_page(False)
                st.info("Scene rejected. You can regenerate it.")
        
        st.markdown("---")
        
        # Display the generated scene, if available
        if current_page.get('scene'):
            st.image(current_page['scene'], caption="Generated Scene Preview", use_column_width=True)
        else:
            st.info("Scene preview will appear here after generation.")
    
    else:
        st.info("No pages yet. Use the sidebar button to add a new page.")
    
    st.markdown("---")
    
    # Final project confirmation
    if st.button("Confirm Project (Compile Book)"):
        # Ensure at least one page exists and has an approved scene
        if st.session_state.pages and any(p.get('approved') for p in st.session_state.pages):
            confirm_project()
            st.success("Project confirmed! Your VR 'book' is ready for the next step.")
            display_compiled_project()
        else:
            st.error("Please ensure at least one page has an approved scene before confirming.")

def display_compiled_project():
    """
    Display the compiled VR book.
    In a future iteration, this could export a VR executable or launch a VR preview.
    """
    st.header("Compiled VR Book")
    st.write(f"Project Title: {st.session_state.project_title}")
    st.markdown("---")
    for idx, page in enumerate(st.session_state.pages):
        st.subheader(f"Page {idx + 1}")
        st.write("Prompt:", page.get('prompt', ''))
        if page.get('scene'):
            st.image(page['scene'], caption="Scene Preview", use_column_width=True)
        else:
            st.write("No scene generated for this page.")
        st.write("Approved:" , "Yes" if page.get('approved') else "No")
        st.markdown("---")
    
    st.info("This is a preview of your compiled VR book. In the final version, you would be able to launch this experience on a VR headset.")

# ------------------------------------------------------------------------------
# SECTION 4: RUN THE APP
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
