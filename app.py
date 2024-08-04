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
st.set_page_config(page_title="Chef's Fridge Recipe Generator", layout="wide")

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
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Fridge Contents")
        image_option = st.radio("Choose an option:", ("Take a Picture", "Upload an Image"))
        
        if image_option == "Take a Picture":
            camera_image = st.camera_input("Take a picture of your fridge contents")
            if camera_image:
                st.session_state.current_image = Image.open(camera_image)
        else:
            uploaded_file = st.file_uploader("Upload fridge image", type=["jpg", "jpeg", "png"])
            if uploaded_file:
                st.session_state.current_image = Image.open(uploaded_file)
        
        if 'current_image' in st.session_state:
            st.image(st.session_state.current_image, caption='Fridge Contents', use_column_width=True)
            
            if st.button('Identify Ingredients'):
                with st.spinner('Analyzing fridge contents...'):
                    identified_items = identify_items(st.session_state.current_image)
                    st.session_state.ingredients = identified_items
    
    with col2:
        st.header("Ingredients and Recipe")
        
        if 'ingredients' in st.session_state:
            st.subheader("Identified Ingredients")
            ingredients = st.text_area("Edit, add, or remove ingredients:",
                                       value='\n'.join(st.session_state.ingredients))
            st.session_state.ingredients = [item.strip() for item in ingredients.split('\n') if item.strip()]
            
            st.subheader("Final Ingredient List")
            st.write(", ".join(st.session_state.ingredients))
            
            if st.button('Generate Recipe'):
                with st.spinner('Crafting your recipe...'):
                    recipe = generate_recipe(st.session_state.ingredients)
                    st.subheader("Your Recipe")
                    st.write(recipe)
        else:
            st.info("Take or upload a picture of your fridge contents, then click 'Identify Ingredients' to start.")

if __name__ == "__main__":
    main()
