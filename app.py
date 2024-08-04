import streamlit as st
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Set up OpenAI client with the API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set page config
st.set_page_config(page_title="Chef's Fridge Recipe Generator", page_icon="🍳", layout="wide")

# Custom CSS for a more appealing and responsive look
st.markdown("""
    <style>
    .main {
        background-color: #f0f8ff;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .recipe-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    .stMultiSelect {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #2C3E50;
    }
    img {
        max-width: 100%;
        height: auto;
    }
    @media (max-width: 768px) {
        .main {
            padding: 5px;
        }
        .recipe-container {
            padding: 10px;
        }
    }
    </style>
""", unsafe_allow_html=True)

def identify_items(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "List all the food items you can see in this fridge image. Provide the list in a comma-separated format."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        )
        
        items = response.choices[0].message['content'].split(',')
        return [item.strip() for item in items]
    except Exception as e:
        st.error(f"An error occurred while identifying items: {str(e)}")
        return []

def generate_recipe(items):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"As a professional chef, create a gourmet recipe using these ingredients: {', '.join(items)}. Provide the recipe name, ingredients with quantities, and concise, professional step-by-step instructions."
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"An error occurred while generating the recipe: {str(e)}")
        return "Unable to generate recipe. Please try again."

def main():
    st.title("🍳 Chef's Fridge Recipe Generator")
    
    st.markdown("### 📸 Step 1: Upload a photo of your fridge contents")
    
    uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Fridge Contents', use_column_width=True)
        
        if st.button('🔍 Identify Ingredients'):
            with st.spinner('Analyzing fridge contents...'):
                identified_items = identify_items(image)
                st.session_state.identified_items = identified_items
                st.success(f"Identified {len(identified_items)} ingredients!")
    
    st.markdown("### 🥕 Step 2: Select ingredients for your recipe")
    if 'identified_items' in st.session_state and st.session_state.identified_items:
        selected_items = st.multiselect(
            "Available Ingredients:",
            st.session_state.identified_items,
            default=st.session_state.identified_items
        )
        
        if st.button('👨‍🍳 Generate Recipe'):
            if selected_items:
                with st.spinner('Crafting your gourmet recipe...'):
                    recipe = generate_recipe(selected_items)
                    st.markdown("## 🍽️ Your Gourmet Recipe")
                    st.markdown(f'<div class="recipe-container">{recipe}</div>', unsafe_allow_html=True)
            else:
                st.warning("⚠️ Please select at least one ingredient.")
    else:
        st.info("👆 Upload an image and identify ingredients to generate a recipe.")

    # Minimal footer
    st.markdown("---")
    st.markdown("Developed with ❤️ for professional chefs")

if __name__ == "__main__":
    main()
