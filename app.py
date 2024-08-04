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
    
    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'input'
    
    # Step 1: Image Input
    if st.session_state.stage == 'input':
        st.header("Step 1: Fridge Image")
        input_option = st.radio("Choose input method:", ("Upload Image", "Take Picture"))
        
        if input_option == "Upload Image":
            uploaded_file = st.file_uploader("Upload fridge image", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                st.session_state.current_image = Image.open(uploaded_file)
                st.session_state.stage = 'identify'
        else:
            camera_image = st.camera_input("Take a picture of your fridge contents")
            if camera_image is not None:
                st.session_state.current_image = Image.open(camera_image)
                st.session_state.stage = 'identify'
    
    # Step 2: Ingredient Identification
    if st.session_state.stage == 'identify':
        st.header("Step 2: Identify Ingredients")
        st.image(st.session_state.current_image, caption='Fridge Contents', use_column_width=True)
        if st.button('Identify Ingredients'):
            with st.spinner('Analyzing fridge contents...'):
                identified_items = identify_items(st.session_state.current_image)
                st.session_state.identified_items = identified_items
                st.session_state.stage = 'confirm'
    
    # Step 3: Confirmation
    if st.session_state.stage == 'confirm':
        st.header("Step 3: Confirm Ingredients")
        st.write("Here are the identified ingredients. Are they correct?")
        st.write(", ".join(st.session_state.identified_items))
        col1, col2 = st.columns(2)
        if col1.button("Yes, these are correct"):
            st.session_state.stage = 'edit'
        if col2.button("No, I need to edit"):
            st.session_state.stage = 'edit'
    
    # Step 4: Editing
    if st.session_state.stage == 'edit':
        st.header("Step 4: Edit Ingredients")
        st.write("You can add or remove ingredients here:")
        
        # Edit existing ingredients
        edited_items = st.text_area("Current ingredients (one per line):", 
                                    value='\n'.join(st.session_state.identified_items))
        current_items = edited_items.split('\n')
        
        # Add new ingredients
        new_item = st.text_input("Add a new ingredient:")
        if st.button("Add Ingredient"):
            if new_item and new_item not in current_items:
                current_items.append(new_item)
        
        # Remove ingredients
        item_to_remove = st.selectbox("Select an ingredient to remove:", 
                                      [""] + current_items)
        if st.button("Remove Ingredient"):
            if item_to_remove in current_items:
                current_items.remove(item_to_remove)
        
        # Update the list of ingredients
        st.session_state.final_ingredients = [item.strip() for item in current_items if item.strip()]
        
        st.subheader("Final Ingredient List")
        st.write(", ".join(st.session_state.final_ingredients))
        
        if st.button("Proceed to Recipe Generation"):
            st.session_state.stage = 'generate'
    
    # Step 5: Recipe Generation
    if st.session_state.stage == 'generate':
        st.header("Step 5: Generate Recipe")
        if st.button('Generate Recipe'):
            with st.spinner('Crafting your recipe...'):
                recipe = generate_recipe(st.session_state.final_ingredients)
                st.subheader("Your Recipe")
                st.write(recipe)
        
        if st.button("Start Over"):
            st.session_state.clear()
            st.experimental_rerun()

if __name__ == "__main__":
    main()
