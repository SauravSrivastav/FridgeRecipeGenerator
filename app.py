import streamlit as st
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page config
st.set_page_config(page_title="Chef's Fridge Recipe Generator", layout="centered")

def identify_items(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    try:
        response = client.chat.completions.create(
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
        
        items = response.choices[0].message.content.split(',')
        return [item.strip() for item in items]
    except Exception as e:
        st.error(f"An error occurred while identifying items: {str(e)}")
        return []

def generate_recipe(items):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"Create a recipe using these ingredients: {', '.join(items)}. Provide the recipe name, ingredients with quantities, and step-by-step instructions."
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred while generating the recipe: {str(e)}")
        return "Unable to generate recipe. Please try again."

def main():
    st.title("Chef's Fridge Recipe Generator")
    
    uploaded_file = st.file_uploader("Upload fridge image", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Fridge Contents', use_column_width=True)
        
        if st.button('Identify Ingredients'):
            with st.spinner('Analyzing fridge contents...'):
                identified_items = identify_items(image)
                st.session_state.identified_items = identified_items
    
    if 'identified_items' in st.session_state and st.session_state.identified_items:
        st.subheader("Available Ingredients")
        st.write(", ".join(st.session_state.identified_items))
        
        selected_items = st.multiselect(
            "Select ingredients for your recipe:",
            st.session_state.identified_items,
            default=st.session_state.identified_items
        )
        
        if st.button('Generate Recipe'):
            if selected_items:
                with st.spinner('Crafting your recipe...'):
                    recipe = generate_recipe(selected_items)
                    st.subheader("Your Recipe")
                    st.write(recipe)
            else:
                st.warning("Please select at least one ingredient.")
    else:
        st.info("Upload an image and identify ingredients to generate a recipe.")

if __name__ == "__main__":
    main()
