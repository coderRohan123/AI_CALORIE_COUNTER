# health management app
from dotenv import load_dotenv
load_dotenv()
import os
import streamlit as st
import google.generativeai as genai
from PIL import Image

# Load the .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Google Gemini model and get response
def get_gemini_response(input_text, image, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input_text, image[0], prompt])
    return response.text

def input_image_setup(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [
            {
                "mime_type": uploaded_file.type,
                "data": bytes_data
            }
        ]
        return image_parts
    else:
        raise FileNotFoundError("No file uploaded")

# Initialize Streamlit app
input_prompt = """
You are an expert nutritionist. Analyze the food items in the image and 
calculate the rough total calories. Even if u are unable to provide just give rough estimates.Provide details of each food item and their count if possible  with 
their calories in the following format:
1. item 1 - number of calories
2. item 2 - number of calories
...
"""

# Model deployment using Streamlit
st.set_page_config(page_title="AI Nutritionist App", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child {
        width: 300px;
        background-color: #f4a300; /* Saffron color */
        color: white;
        padding: 20px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child {
        width: 300px;
        margin-left: -300px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("AI Nutritionist App")
st.sidebar.markdown("---")
st.sidebar.subheader("Instructions")
st.sidebar.write("1. Upload an image of your meal.")
st.sidebar.write("2. Enter a prompt to analyze the image.")
st.sidebar.write("3. Click the 'Tell me the total calories' button.")

st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.write("This app uses AI to analyze food images and provide nutritional information.")

st.sidebar.markdown("---")
st.sidebar.subheader("Contact")
st.sidebar.write("For any questions or feedback, please contact us at rohanmallick016e@gmail.com")

st.sidebar.markdown("---")
st.sidebar.write("Made  by Rohan")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .stButton > button {
        background-color: #007bff;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #0056b3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI Nutritionist App")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    input_text = st.text_area("Input Prompt:", height=200)

with col2:
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
    image = ""

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)

submit = st.button("Tell me the total calories")

if submit:
    try:
        image_data = input_image_setup(uploaded_file)
        response = get_gemini_response(input_text, image_data, input_prompt)
        st.subheader("The response is:")
        st.write(response)
    except Exception as e:
        st.error(f"An error occurred: {e}")