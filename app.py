import streamlit as st
from PIL import Image
import io
import base64
import os
from dotenv import load_dotenv
from openai import OpenAI
import imagehash

# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page config
st.set_page_config(page_title="EKFC Flight Catering Recipe Generator", layout="wide")

def image_hash(image):
    return str(imagehash.average_hash(image))

def is_duplicate(new_image, existing_images):
    new_hash = image_hash(new_image)
    for img in existing_images:
        if image_hash(img) == new_hash:
            return True
    return False

def identify_items(images):
    all_items = []
    for image in images:
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
                            {"type": "text", "text": "List all the food items you can see in this image of airline catering ingredients. Provide the list in a comma-separated format."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=300
            )
            
            items = response.choices[0].message.content.split(',')
            all_items.extend([item.strip() for item in items])
        except Exception as e:
            st.error(f"An error occurred while identifying items: {str(e)}")
    
    return list(set(all_items))  # Remove duplicates

def generate_recipe(items, flight_type, class_type, dietary_requirements, destination):
    try:
        prompt = f"""Create a recipe suitable for {flight_type} flight catering in {class_type} class, 
        flying to {destination}. The recipe should meet these dietary requirements: {dietary_requirements}.
        Use these ingredients: {', '.join(items)}. 
        Consider factors like:
        - Ease of serving in-flight
        - Food safety and preservation for long flights
        - Cultural preferences of the destination
        - Appropriate portion sizes for airline meals
        - Minimal use of strong odors or messy foods
        
        Provide the recipe name, ingredients with quantities, step-by-step instructions, and any special 
        packaging or reheating instructions for flight attendants."""
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"An error occurred while generating the recipe: {str(e)}")
        return "Unable to generate recipe. Please try again."

def main():
    st.title("EKFC Flight Catering Recipe Generator")
    
    if 'images' not in st.session_state:
        st.session_state.images = []
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Ingredient Inventory")
        image_option = st.radio("Choose an option:", ("Take Pictures", "Upload Images"))
        
        if image_option == "Take Pictures":
            camera_image = st.camera_input("Take a picture of catering ingredients")
            if camera_image:
                new_image = Image.open(camera_image)
                if not is_duplicate(new_image, st.session_state.images):
                    st.session_state.images.append(new_image)
                    st.success("Image added successfully!")
        else:
            uploaded_files = st.file_uploader("Upload ingredient images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
            if uploaded_files:
                new_images = 0
                duplicates = 0
                for uploaded_file in uploaded_files:
                    new_image = Image.open(uploaded_file)
                    if not is_duplicate(new_image, st.session_state.images):
                        st.session_state.images.append(new_image)
                        new_images += 1
                    else:
                        duplicates += 1
                
                if new_images > 0:
                    st.success(f"{new_images} new image(s) added successfully!")
                if duplicates > 0:
                    st.info(f"{duplicates} duplicate image(s) were not added.")
        
        if st.session_state.images:
            st.subheader("Captured/Uploaded Images")
            for i, img in enumerate(st.session_state.images):
                st.image(img, caption=f'Ingredient Image {i+1}', use_column_width=True)
            
            if st.button('Clear All Images'):
                st.session_state.images = []
                st.experimental_rerun()
            
            if st.button('Identify Ingredients'):
                with st.spinner('Analyzing ingredient inventory...'):
                    identified_items = identify_items(st.session_state.images)
                    st.session_state.ingredients = identified_items
    
    with col2:
        st.header("Flight Menu Planning")
        
        if 'ingredients' in st.session_state:
            st.subheader("Identified Ingredients")
            ingredients = st.text_area("Edit, add, or remove ingredients:",
                                       value='\n'.join(st.session_state.ingredients))
            st.session_state.ingredients = [item.strip() for item in ingredients.split('\n') if item.strip()]
            
            st.subheader("Final Ingredient List")
            st.write(", ".join(st.session_state.ingredients))
            
            # Flight-specific options
            st.subheader("Flight Details")
            flight_type = st.selectbox("Flight Type:", ["International", "National", "Lounge Service"])
            class_type = st.selectbox("Class:", ["First Class", "Business Class", "Economy Class"])
            destination = st.text_input("Destination:")
            
            # Dietary Requirements
            st.subheader("Dietary Requirements")
            dietary_options = ["Standard", "Halal", "Kosher", "Vegetarian", "Vegan", "Gluten-Free", "Low-Sodium", "Diabetic"]
            dietary_requirements = st.multiselect("Select dietary requirements:", dietary_options)
            
            if st.button('Generate Flight Menu'):
                with st.spinner('Crafting your in-flight menu...'):
                    recipe = generate_recipe(st.session_state.ingredients, flight_type, class_type, 
                                             ", ".join(dietary_requirements), destination)
                    st.subheader("Your In-Flight Menu")
                    st.write(recipe)
        else:
            st.info("Take or upload pictures of catering ingredients, then click 'Identify Ingredients' to start.")

if __name__ == "__main__":
    main()
