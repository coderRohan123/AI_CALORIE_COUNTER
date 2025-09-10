# app.py - FINAL, TESTED, AND CORRECTED VERSION

# --- 1. IMPORTS ---
import os
import io
import re
import json
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1
from PIL import Image
import psycopg2
import sqlalchemy
from passlib.context import CryptContext
import google.generativeai as genai

# --- 2. CONFIGURATION & INITIALIZATION ---
load_dotenv()
st.set_page_config(page_title="AI Nutrition Platform", page_icon="🔬", layout="wide")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- 3. DATABASE & CORE FUNCTIONS ---
DB_URL = os.getenv("DATABASE_URL")
def get_db_connection():
    return psycopg2.connect(DB_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY, username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL, password_hash VARCHAR(255) NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            meal_title TEXT NOT NULL, analysis_text TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meal_nutrients (
            id SERIAL PRIMARY KEY, meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
            nutrient_name TEXT NOT NULL, amount NUMERIC(10, 3), unit VARCHAR(20),
            percent_dv NUMERIC(6, 2)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def hash_password(password: str) -> str: return pwd_context.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool: return pwd_context.verify(plain_password, hashed_password)

def create_user(username, email, password):
    hashed_password = hash_password(password)
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s);", (username, email, hashed_password))
        conn.commit(); return True
    except psycopg2.IntegrityError: return False
    finally: cur.close(); conn.close()

def authenticate_user(username, password):
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = %s;", (username,))
        result = cur.fetchone()
        if result and verify_password(password, result[1]): return result[0]
        return None
    finally: cur.close(); conn.close()

def add_meal_entry(user_id, meal_analysis):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO meals (user_id, meal_title, analysis_text, created_at) VALUES (%s, %s, %s, %s) RETURNING id;",
                        (user_id, meal_analysis['title'], meal_analysis['full_text'], datetime.now()))
            meal_id = cur.fetchone()[0]
            for nutrient in meal_analysis['nutrients']:
                cur.execute("INSERT INTO meal_nutrients (meal_id, nutrient_name, amount, unit, percent_dv) VALUES (%s, %s, %s, %s, %s);",
                            (meal_id, nutrient.get('nutrient'), nutrient.get('amount'), nutrient.get('unit'), nutrient.get('percent_dv')))
            conn.commit()
    finally: conn.close()

def get_user_data(user_id, start_date):
    conn = get_db_connection()
    query = """
        SELECT m.id, m.meal_title, m.created_at, n.nutrient_name, n.amount, n.unit
        FROM meals m JOIN meal_nutrients n ON m.id = n.meal_id
        WHERE m.user_id = %s AND m.created_at >= %s ORDER BY m.created_at DESC;
    """
    # Use engine instead of raw connection for pandas
    engine = sqlalchemy.create_engine(DB_URL)
    df = pd.read_sql_query(query, engine, params=(user_id, start_date))
    engine.dispose()
    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)
    return df

def clean_meal_title(title):
    """Clean meal title by removing prefixes like '1. Meal Title:' or 'Meal Title:'"""
    if not title:
        return "Untitled Meal"
    
    # Remove common prefixes
    cleaned = title.strip()
    
    # Remove numbered prefixes like "1. Meal Title:", "2. Meal Title:", etc.
    import re
    cleaned = re.sub(r'^\d+\.\s*Meal Title:\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove "Meal Title:" prefix
    cleaned = re.sub(r'^Meal Title:\s*', '', cleaned, flags=re.IGNORECASE)
    
    # Remove any remaining asterisks or markdown formatting
    cleaned = cleaned.replace('**', '').replace('*', '')
    
    return cleaned.strip() if cleaned.strip() else "Untitled Meal"

input_prompt="""
You are a world-class food scientist AI. Your task is to perform a comprehensive nutritional analysis of the meal in the image. Your response MUST strictly follow this structure:

1.  **Meal Title:** A descriptive title. Format: `Meal Title: [Your Title]`

2.  Provide a brief analysis with the following content (do not include section headers):
    - **Advantages:** 2-3 health benefits of this food
    - **Disadvantages:** 1-2 potential concerns or limitations
    
    ***Fun Fact:*** One interesting fact about this food (format this exactly as shown with triple asterisks for bold italic)

3.  Provide the nutritional data as a valid JSON array of objects, enclosed in triple backticks (do not include any text before the JSON).
    **CRITICAL RULE:** You MUST provide a value for EVERY nutrient in the list below. If the meal does not contain a nutrient or if data is unavailable, you MUST include it with an `amount` of 0. Do not omit any nutrient from this list.

    ```json
    [
      {"nutrient": "Calories", "amount": ..., "unit": "kcal"},
      {"nutrient": "Protein", "amount": ..., "unit": "g", "percent_dv": ...},
      {"nutrient": "Total Fat", "amount": ..., "unit": "g", "percent_dv": ...},
      {"nutrient": "Saturated Fat", "amount": ..., "unit": "g", "percent_dv": ...},
      {"nutrient": "Trans Fat", "amount": ..., "unit": "g"},
      {"nutrient": "Polyunsaturated Fat", "amount": ..., "unit": "g"},
      {"nutrient": "Monounsaturated Fat", "amount": ..., "unit": "g"},
      {"nutrient": "Cholesterol", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Carbohydrates", "amount": ..., "unit": "g", "percent_dv": ...},
      {"nutrient": "Dietary Fiber", "amount": ..., "unit": "g", "percent_dv": ...},
      {"nutrient": "Total Sugars", "amount": ..., "unit": "g"},
      {"nutrient": "Added Sugars", "amount": ..., "unit": "g", "percent_dv": ...},
      {"nutrient": "Sodium", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Potassium", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Calcium", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Iron", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Magnesium", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Phosphorus", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Zinc", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Copper", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Manganese", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Selenium", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin A", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin C", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Vitamin D", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin E", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Vitamin K", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Thiamin (B1)", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Riboflavin (B2)", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Niacin (B3)", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Vitamin B6", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Folate (B9)", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin B12", "amount": ..., "unit": "mcg", "percent_dv": ...}
    ]
    ```
      {"nutrient": "Zinc", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Copper", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Manganese", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Selenium", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin A", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin C", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Vitamin D", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin E", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Vitamin K", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Thiamin (B1)", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Riboflavin (B2)", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Niacin (B3)", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Vitamin B6", "amount": ..., "unit": "mg", "percent_dv": ...},
      {"nutrient": "Folate (B9)", "amount": ..., "unit": "mcg", "percent_dv": ...},
      {"nutrient": "Vitamin B12", "amount": ..., "unit": "mcg", "percent_dv": ...}
    ]
    ```
"""
def parse_summary_from_response(response_text):
    results = {}
    title_match = re.search(r"Meal Title: (.*)", response_text, re.IGNORECASE)
    if title_match:
        results['title'] = title_match.group(1).strip()
    else:
        lines = response_text.split('\n')
        first_meaningful_line = next((line for line in lines if line.strip()), "Untitled Meal")
        results['title'] = first_meaningful_line.strip().replace('**', '')
    results['full_text'] = response_text
    json_match = re.search(r"```json\n([\s\S]*?)\n```", response_text)
    if json_match:
        try: results['nutrients'] = json.loads(json_match.group(1))
        except json.JSONDecodeError: results['nutrients'] = []
    else: results['nutrients'] = []
    return results

def get_gemini_response(image_data, prompt):
    model = genai.GenerativeModel('gemini-2.5-flash'); return model.generate_content([image_data[0], prompt]).text

def setup_image_for_api(uploaded_file):
    if uploaded_file: return [{"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}]
    raise FileNotFoundError("No file uploaded.")

# --- SESSION STATE INITIALIZATION ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'user_id' not in st.session_state: 
    st.session_state.user_id = None
if 'username' not in st.session_state: 
    st.session_state.username = None
if 'page' not in st.session_state: 
    st.session_state.page = 'Analyzer'
if 'current_analysis' not in st.session_state: 
    st.session_state.current_analysis = None

# --- UI RENDERING FUNCTIONS ---
def render_analyzer_page():
    st.title("AI Nutrition Analyzer")
    st.markdown("Upload a picture of your meal for a complete A-to-Z nutritional breakdown.")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📤 Upload & Analysis")
        st.info("💡 **How it works:** Upload a photo of your meal and click 'Analyze' to get detailed nutritional information powered by AI.")
        uploaded_file = st.file_uploader("Upload Your Meal Image...", type=["jpg", "jpeg", "png"])
        
        if st.button("Analyze Meal", type="primary"):
            if uploaded_file:
                with st.spinner("Performing deep nutritional analysis... This may take a moment."):
                    try:
                        image_api_data = setup_image_for_api(uploaded_file)
                        response_text = get_gemini_response(image_api_data, input_prompt)
                        st.session_state['current_analysis'] = parse_summary_from_response(response_text)
                    except Exception as e:
                        st.error(f"An error occurred: {e}"); st.session_state['current_analysis'] = None
            else: st.warning("Please upload an image first.")
    
    with col2:
        # Display the uploaded image on the right side in medium size
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Your Meal Image", width=350)
        else:
            st.info("Upload an image to see preview here")
    if st.session_state['current_analysis']:
        st.divider()
        st.subheader("🍽️ Analysis Results")
        st.info("🤖 **AI Analysis:** Below you'll find the meal identification, nutritional breakdown, and complete vitamin/mineral profile detected from your image.")
        
        analysis = st.session_state['current_analysis']
        st.markdown(f"### {analysis.get('title')}")
        
        # Display the brief analysis text
        response_parts = analysis['full_text'].split('```json')
        if response_parts:
            # Get the text before the JSON section
            readable_text = response_parts[0]
            # Remove the meal title from the display text
            cleaned_text = readable_text.replace(f"Meal Title: {analysis.get('title')}", "").strip()
            if cleaned_text:
                st.markdown(cleaned_text)

        if analysis['nutrients']:
            df = pd.DataFrame(analysis['nutrients']).fillna(0)
            st.markdown("#### 📊 Complete Nutritional Profile")
            st.dataframe(df, width='stretch', height=500)
            
        if st.session_state['logged_in']:
            if st.button("Save to My Dashboard"):
                add_meal_entry(st.session_state['user_id'], analysis)
                st.success(f"'{analysis.get('title')}' saved!"); st.session_state['current_analysis'] = None

def render_dashboard_page():
    st.title(f"Nutrition Dashboard for {st.session_state['username']}")
    
    time_options = {
        "Last Day": timedelta(days=1), "Last 7 Days": timedelta(days=7),
        "Last 15 Days": timedelta(days=15), "Last 30 Days": timedelta(days=30),
        "Last 3 Months": timedelta(days=90), "Last 6 Months": timedelta(days=180),
        "Last 12 Months": timedelta(days=365), "All Time": None
    }
    selected_range_key = st.selectbox("Select Time Range", options=list(time_options.keys()), index=1)
    
    if time_options[selected_range_key]:
        start_date = datetime.now().date() - time_options[selected_range_key]
    else:
        start_date = datetime(1970, 1, 1).date()

    df = get_user_data(st.session_state['user_id'], start_date)

    if df.empty:
        st.info("No data found for this period. Analyze and save a meal to get started!"); return

    st.subheader(f"Data for: {selected_range_key}")
    st.info("📈 **Dashboard Overview:** Your nutritional data is summarized below. Charts show proportions and trends, while metrics display totals for the selected time period.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🍞 Macronutrient Distribution")
        st.caption("💡 Shows how your calories are distributed across protein, carbs, and fats as percentages.")
        # Get actual calories from database - this is the source of truth
        calories_df = df[df['nutrient_name'] == 'Calories']
        macros = ['Protein', 'Total Fat', 'Carbohydrates']
        macros_df = df[df['nutrient_name'].isin(macros)]
        
        if not macros_df.empty and not calories_df.empty:
            # Use database values directly - no manual calculation
            macro_totals_grams = macros_df.groupby('nutrient_name')['amount'].sum()
            total_db_calories = calories_df['amount'].sum()
            
            protein_grams = macro_totals_grams.get('Protein', 0)
            carbs_grams = macro_totals_grams.get('Carbohydrates', 0)
            fat_grams = macro_totals_grams.get('Total Fat', 0)
            
            # Calculate proportional calories based on database total
            total_macro_grams = protein_grams + carbs_grams + fat_grams
            
            if total_macro_grams > 0:
                # Distribute database calories proportionally based on gram ratios
                protein_ratio = protein_grams / total_macro_grams
                carbs_ratio = carbs_grams / total_macro_grams  
                fat_ratio = fat_grams / total_macro_grams
                
                protein_calories = total_db_calories * protein_ratio
                carbs_calories = total_db_calories * carbs_ratio
                fat_calories = total_db_calories * fat_ratio
                
                pie_data = pd.DataFrame({
                    'Macro': ['Protein', 'Carbohydrates', 'Fat'], 
                    'Calories': [protein_calories, carbs_calories, fat_calories],
                    'Grams': [protein_grams, carbs_grams, fat_grams],
                    'Tooltip': [
                        f'Protein: {protein_grams:.1f}g ({protein_calories:.0f} kcal)',
                        f'Carbohydrates: {carbs_grams:.1f}g ({carbs_calories:.0f} kcal)',
                        f'Fat: {fat_grams:.1f}g ({fat_calories:.0f} kcal)'
                    ]
                })
                pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50, outerRadius=100).encode(
                    theta=alt.Theta(field="Calories", type="quantitative", stack=True),
                    color=alt.Color(field="Macro", type="nominal", legend=alt.Legend(title="Macronutrient")),
                    tooltip=['Tooltip:N']
                ).properties(title=f"Macronutrient Breakdown (Total: {total_db_calories:.0f} kcal)")
                st.altair_chart(pie_chart, use_container_width=True)
            else: 
                st.info("No macronutrient gram data available for proportional distribution.")
        else: 
            st.info("No calorie or macronutrient data for this period.")

    with col2:
        st.markdown("#### 🍊 Vitamins Breakdown")
        st.caption("💡 Displays the distribution of essential vitamins you've consumed from your meals.")
        vitamins = ['Vitamin A', 'Vitamin C', 'Vitamin D', 'Vitamin E', 'Vitamin K', 
                   'Thiamin (B1)', 'Riboflavin (B2)', 'Niacin (B3)', 'Vitamin B6', 
                   'Folate (B9)', 'Vitamin B12']
        vitamins_df = df[df['nutrient_name'].isin(vitamins)]
        
        if not vitamins_df.empty:
            vitamin_totals = vitamins_df.groupby('nutrient_name')['amount'].sum().reset_index()
            # Filter out vitamins with zero values for cleaner chart
            vitamin_totals = vitamin_totals[vitamin_totals['amount'] > 0]
            
            if not vitamin_totals.empty:
                # Add proper units and create detailed tooltips
                def get_vitamin_unit(vitamin_name):
                    if vitamin_name in ['Vitamin A', 'Vitamin D', 'Vitamin K', 'Folate (B9)', 'Vitamin B12']:
                        return 'mcg'
                    else:
                        return 'mg'
                
                vitamin_totals['unit'] = vitamin_totals['nutrient_name'].apply(get_vitamin_unit)
                vitamin_totals['vitamin_short'] = vitamin_totals['nutrient_name'].str.replace(' \\(.*\\)', '', regex=True)
                vitamin_totals['tooltip'] = vitamin_totals.apply(
                    lambda row: f"{row['vitamin_short']}: {row['amount']:.2f} {row['unit']}", axis=1
                )
                
                vitamin_pie_chart = alt.Chart(vitamin_totals).mark_arc(innerRadius=50, outerRadius=100).encode(
                    theta=alt.Theta(field="amount", type="quantitative", stack=True),
                    color=alt.Color(field="vitamin_short", type="nominal", legend=alt.Legend(title="Vitamin Type")),
                    tooltip=['tooltip:N']
                ).properties(title="Vitamin Intake Distribution")
                st.altair_chart(vitamin_pie_chart, use_container_width=True)
                
                # Show vitamin summary with units
                st.markdown("**Vitamin Summary:**")
                vitamin_summary = ""
                for _, row in vitamin_totals.iterrows():
                    vitamin_summary += f"• {row['vitamin_short']}: {row['amount']:.2f} {row['unit']}\n"
                st.text(vitamin_summary)
                
            else: st.info("No vitamin data available for this period.")
        else: st.info("No vitamin data for this period.")
    
    # Move the key nutrient totals to a new row
    st.markdown("#### 🔢 Key Nutrient Totals")
    st.caption("💡 Your total intake of essential nutrients over the selected time period.")
    col3, col4, col5 = st.columns(3)
    with col3:
        key_nutrients = ['Calories', 'Protein']
        key_nutrients_df = df[df['nutrient_name'].isin(key_nutrients)]
        
        if not key_nutrients_df.empty:
            totals = key_nutrients_df.groupby('nutrient_name')['amount'].sum().reindex(key_nutrients).reset_index()
            for index, row in totals.iterrows():
                nutrient_name = row['nutrient_name']; total_amount = row['amount']
                if pd.notna(total_amount):
                    if nutrient_name == 'Calories': st.metric(f"Total {nutrient_name}", f"{total_amount:.0f} kcal")
                    else: st.metric(f"Total {nutrient_name}", f"{total_amount:.0f} g")
        else: st.info("No key nutrient data for this period.")
    
    with col4:
        key_nutrients2 = ['Total Fat', 'Carbohydrates']
        key_nutrients_df2 = df[df['nutrient_name'].isin(key_nutrients2)]
        
        if not key_nutrients_df2.empty:
            totals2 = key_nutrients_df2.groupby('nutrient_name')['amount'].sum().reindex(key_nutrients2).reset_index()
            for index, row in totals2.iterrows():
                nutrient_name = row['nutrient_name']; total_amount = row['amount']
                if pd.notna(total_amount):
                    st.metric(f"Total {nutrient_name}", f"{total_amount:.0f} g")
    
    with col5:
        key_nutrients3 = ['Dietary Fiber', 'Sodium']
        key_nutrients_df3 = df[df['nutrient_name'].isin(key_nutrients3)]
        
        if not key_nutrients_df3.empty:
            totals3 = key_nutrients_df3.groupby('nutrient_name')['amount'].sum().reindex(key_nutrients3).reset_index()
            for index, row in totals3.iterrows():
                nutrient_name = row['nutrient_name']; total_amount = row['amount']
                if pd.notna(total_amount):
                    if nutrient_name == 'Sodium': st.metric(f"Total {nutrient_name}", f"{total_amount:.0f} mg")
                    else: st.metric(f"Total {nutrient_name}", f"{total_amount:.0f} g")

    st.divider()
    
    st.subheader("📅 Recent Meals History")
    st.info("🍽️ **Meal History:** All the meals you've analyzed and saved are listed below with dates and times.")
    
    # Get unique meals with their details
    meals_query = """
        SELECT DISTINCT m.id, m.meal_title, m.created_at
        FROM meals m
        WHERE m.user_id = %s AND m.created_at >= %s 
        ORDER BY m.created_at DESC;
    """
    
    # Use engine instead of raw connection for pandas
    engine = sqlalchemy.create_engine(DB_URL)
    meals_df = pd.read_sql_query(meals_query, engine, params=(st.session_state['user_id'], start_date))
    engine.dispose()
    
    if not meals_df.empty:
        # Format the datetime for better display
        meals_df['created_at'] = pd.to_datetime(meals_df['created_at'])
        meals_df['Date'] = meals_df['created_at'].dt.strftime('%Y-%m-%d')
        meals_df['Time'] = meals_df['created_at'].dt.strftime('%H:%M')
        
        # Display meals in a nice format
        for index, meal in meals_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    clean_title = clean_meal_title(meal['meal_title'])
                    st.write(f"🍽️ **{clean_title}**")
                with col2:
                    st.write(f"📅 {meal['Date']}")
                with col3:
                    st.write(f"⏰ {meal['Time']}")
                st.divider()
    else:
        st.info("No meals saved in this time period. Start analyzing meals to build your history!")

    st.divider()
    
    st.subheader("📈 Nutrient Intake Over Time")
    st.info("📉 **Trend Analysis:** Select nutrients below to see how your daily intake changes over time. Great for tracking consistency!")
    all_nutrients = sorted(df['nutrient_name'].unique())
    
    selected_nutrients = st.multiselect("Select nutrients to chart:", all_nutrients, default=['Calories', 'Protein'])
    
    if selected_nutrients:
        chart_df = df[df['nutrient_name'].isin(selected_nutrients)].copy()  # Use .copy() to avoid warning
        chart_df['date'] = chart_df['created_at'].dt.date
        daily_chart_df = chart_df.groupby(['date', 'nutrient_name'])['amount'].sum().reset_index()
        chart = alt.Chart(daily_chart_df).mark_line(point=True).encode(
            x=alt.X('date:T', title='Date'), y=alt.Y('amount:Q', title='Total Daily Amount'),
            color='nutrient_name:N', tooltip=['date', 'nutrient_name', 'amount']
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

# --- SIDEBAR & PAGE ROUTING ---
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1 style='color: #ff6b35; margin-bottom: 5px;'>🔬 AI Nutrition</h1>
        <h3 style='color: #4a90e2; margin-top: 0;'>Platform</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.logged_in:
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #4a90e2, #7b68ee); 
                    padding: 15px; border-radius: 10px; text-align: center; margin: 20px 0;'>
            <h4 style='color: white; margin: 0;'>👋 Welcome back!</h4>
            <p style='color: #f0f0f0; margin: 5px 0 0 0; font-size: 16px;'><strong>{st.session_state.username}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📱 Navigation")
        if st.button("🔍 Food Analyzer", width='stretch', type="primary" if st.session_state.page == 'Analyzer' else "secondary"): 
            st.session_state.page = 'Analyzer'
        if st.button("📊 My Dashboard", width='stretch', type="primary" if st.session_state.page == 'Dashboard' else "secondary"): 
            st.session_state.page = 'Dashboard'
        
        st.markdown("---")
        
        if st.button("🚪 Logout", width='stretch', type="secondary"):
            for key in ['logged_in', 'user_id', 'username', 'current_analysis']: 
                st.session_state.pop(key, None)
            st.session_state.page = 'Analyzer'
            st.rerun()
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 15px; text-align: center; margin: 20px 0;'>
            <h4 style='color: white; margin: 0 0 10px 0;'>📊 Register to View Nutrient Dashboard</h4>
            <p style='color: #e6e6ff; margin: 0; font-size: 14px;'>Save all your meals and track nutrition over time</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("#### 🔑 Sign In")
            
            # Custom CSS for input styling
            st.markdown("""
            <style>
            .stTextInput > div > div > input {
                background-color: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
            }
            .stTextInput > div > div > input:focus {
                border-color: #4a90e2;
                box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
            }
            </style>
            """, unsafe_allow_html=True)
            
            username = st.text_input("👤 Username", placeholder="Enter your username", key="login_user", label_visibility="collapsed")
            password = st.text_input("🔒 Password", placeholder="Enter your password", type="password", key="login_pass", label_visibility="collapsed")
            
            col1, col2 = st.columns([1, 2])
            with col2:
                login_btn = st.form_submit_button("🚀 Login", width='stretch', type="primary")
            
            if login_btn:
                if username and password:
                    user_id = authenticate_user(username, password)
                    if user_id:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success("✅ Login successful!")
                        st.rerun()
                    else: 
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please fill in both fields")
        
        with st.expander("📝 New User? Sign Up Here", expanded=False):
            with st.form("signup_form"):
                st.markdown("#### ✨ Create Account")
                
                username = st.text_input("👤 Choose Username", placeholder="Pick a unique username", key="signup_user", label_visibility="collapsed")
                email = st.text_input("📧 Email Address", placeholder="your.email@example.com", key="signup_email", label_visibility="collapsed")
                password = st.text_input("🔒 Create Password", placeholder="Choose a strong password", type="password", key="signup_pass", label_visibility="collapsed")
                
                col1, col2 = st.columns([1, 2])
                with col2:
                    signup_btn = st.form_submit_button("🎉 Create Account", width='stretch', type="primary")
                
                if signup_btn:
                    if username and email and password:
                        if len(password) < 6:
                            st.error("❌ Password must be at least 6 characters long")
                        elif '@' not in email:
                            st.error("❌ Please enter a valid email address")
                        else:
                            if create_user(username, email, password): 
                                st.success("🎉 Account created successfully! Please log in above.")
                                st.balloons()
                            else: 
                                st.error("❌ Username or email already exists. Try different ones.")
                    else:
                        st.warning("⚠️ Please fill in all fields")

if st.session_state.page == 'Analyzer':
    render_analyzer_page()
elif st.session_state.page == 'Dashboard':
    if st.session_state.logged_in:
        render_dashboard_page()
    else:
        st.error("You must be logged in to view the dashboard.")
        render_analyzer_page()

# --- One-time DB setup ---
# if __name__ == '__main__':
#     init_db()
#     print("Database initialized with professional, normalized schema.")