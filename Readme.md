# 🍎 AI Calorie Counter

> **Snap a photo of your food and instantly know exactly what nutrients you're eating!**

Tired of guessing calories? Just take a picture and let AI do the heavy lifting! This smart app analyzes your food photos and gives you detailed nutritional information in seconds.

![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF6B6B?style=for-the-badge&logo=streamlit)
![Google AI](https://img.shields.io/badge/Google%20AI-4285F4?style=for-the-badge&logo=google)

## 🌟 What This App Does

**Take a picture of your meal → Get instant nutritional breakdown → Track your health journey!**

### ✨ Core Features:
- 📸 **Photo Analysis** - Upload any food image and get detailed nutrition info in under 3 seconds
- 🥗 **Smart Recognition** - Identifies multiple foods in one photo (pizza + salad + drink? No problem!)
- 📊 **Complete Breakdown** - See calories, protein, carbs, fats, vitamins, minerals - all 32+ nutrients
- 💾 **Personal Tracking** - Create an account to save meals and build your nutrition history
- 📈 **Visual Dashboard** - Beautiful pie charts showing your macro and vitamin intake
- 📅 **Time Analysis** - Track your eating patterns over days, weeks, or months
- 🍽️ **Meal Memory** - Browse your food history with clean, organized meal titles

## 🚀 Quick Start Guide

### 📋 What You'll Need
- Python 3.8 or higher
- A Google AI API key (free to get!)
- A database connection (Neon DB, PostgreSQL, or any compatible database)

### 🔧 Installation Steps

#### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/AI_CALORIE_COUNTER.git
cd AI_CALORIE_COUNTER
```

#### 2️⃣ Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux  
python3 -m venv venv
source venv/bin/activate
```

#### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4️⃣ Set Up Environment Variables
Create a `.env` file in your project folder:
```env
GOOGLE_API_KEY=your_google_ai_api_key_here
DATABASE_URL=your_database_url_here
```

**🔑 Getting Your Google AI API Key (It's Free!):**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key" 
4. Copy the key and paste it in your `.env` file
5. You get generous free usage - perfect for personal nutrition tracking!

**💾 Setting Up Your Database:**
- **Easy Option:** Use [Neon DB](https://neon.tech) - free PostgreSQL hosting
- **Local Option:** Install PostgreSQL locally
- **Other Options:** Any PostgreSQL-compatible database will work

#### 5️⃣ Run the App
```bash
streamlit run app.py
```

🎉 **That's it!** Your app will open at `http://localhost:8501` (Streamlit's default port)

> **First Time Setup Tip:** The app will automatically create the necessary database tables when you first run it!

## 📖 How to Use

### 🍕 Analyze Your Food
1. **Upload Image** - Click "Upload Your Meal Image" and select a food photo
2. **Click Analyze** - Hit the "Analyze Meal" button
3. **Get Results** - See instant nutritional breakdown with detailed charts!

### 👤 Why Create an Account?
- **Save Your Meals** - Build a personal food diary with every meal analyzed
- **See Progress** - Watch your nutrition patterns evolve with interactive charts
- **Time Travel** - Compare your eating habits from last week, month, or year
- **Clean Meal Titles** - See just the dish names without formatting clutter
- **Secure & Private** - Your data is safely encrypted and stored

### 📊 Dashboard Features
- **🥗 Macronutrient Pie Chart** - See your protein, carbs, and fat distribution
- **🌈 Vitamin Breakdown** - Track your vitamin intake across all types
- **📈 Time-based Analysis** - Choose from different time ranges (1 day to 1 year)
- **🍽️ Meal History** - Browse all your saved meals with dates and times

## 🛠️ Built With

- **🖼️ Web Interface:** Streamlit - makes Python apps feel like modern web apps
- **🤖 AI Brain:** Google Generative AI (Gemini 2.5 Flash) - the smart food recognition
- **💾 Database:** PostgreSQL + SQLAlchemy - reliable data storage and pandas integration
- **📊 Charts:** Altair - those beautiful interactive pie charts you'll love
- **🔒 Security:** Passlib + bcrypt - your passwords are properly protected
- **🎨 Design:** Custom CSS - clean, modern interface that's easy on the eyes

## 📁 Project Structure

```
AI_CALORIE_COUNTER/
│
├── 📄 app.py              # Main application file
├── 📄 requirements.txt    # Python dependencies
├── 📄 .env               # Environment variables (create this)
├── 📄 README.md          # This awesome guide!
└── 📁 venv/              # Virtual environment (created during setup)
```

## 📦 Key Dependencies

**Main Libraries:**
- `streamlit` - Powers the web interface
- `google-generativeai` - The AI that recognizes your food
- `pandas` + `altair` - Data handling and beautiful charts
- `psycopg2-binary` + `sqlalchemy` - Database connections (both raw and pandas-friendly)
- `passlib[bcrypt]` - Keeps your account secure
- `python-dotenv` - Manages your API keys safely

*All versions are specified in `requirements.txt` for consistent installation.*

## 🎯 Features in Detail

### 🔍 AI Analysis Power
- **Multi-Food Detection** - Pizza with a side salad? It sees everything in one shot
- **32+ Nutrients** - From basic calories to detailed vitamins and minerals
- **Lightning Fast** - Get results in 2-3 seconds, not minutes
- **Real-World Accurate** - Trained on diverse food images for reliable estimates

### 📊 Dashboard That Actually Helps
- **Smart Charts** - Hover over any section to see exact amounts and percentages
- **Macro & Vitamin Views** - See your protein/carbs/fat split AND vitamin intake
- **Flexible Time Ranges** - Yesterday, last week, last month, or all-time analysis
- **Clean Meal Display** - Just dish names, no confusing formatting

### 💾 Your Personal Food Journey
- **Secure Login** - Your nutrition data stays private
- **Meal Memory** - Every analyzed meal saved with date and time
- **Trend Tracking** - Watch your eating habits improve over time
- **Database Accuracy** - All calculations use the database as the source of truth

## 🆘 Troubleshooting

**🚨 Common Issues:**

**"Module not found" error?**
- Make sure your virtual environment is activated
- Run `pip install -r requirements.txt` again

**"API key not found" error?**
- Check your `.env` file exists and has the correct Google AI API key
- Make sure there are no extra spaces around the key

**App won't start?**
- Make sure you're in the correct directory (`AI_CALORIE_COUNTER`)
- Check that port 8501 isn't being used by another app
- Try running `streamlit run app.py --server.port 8502` to use a different port

**Database connection issues?**
- Verify your `DATABASE_URL` in the `.env` file
- Make sure your database is running and accessible

## 🤝 Contributing

Found a bug? Have a cool feature idea? 
1. Fork the repo
2. Create your feature branch
3. Make your awesome changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Google AI for providing the amazing Generative AI API
- Streamlit team for the fantastic web framework
- The open-source community for all the incredible tools

---

## 🎯 Perfect For:
- **Health Enthusiasts** - Track your nutrition goals with precision
- **Fitness Folks** - Monitor your macro intake for better results
- **Curious Eaters** - Learn what's really in your favorite foods
- **Busy People** - Quick nutrition info without manual calorie counting
- **Data Lovers** - Beautiful charts and trends of your eating habits

**🎉 Ready to start your nutrition journey? Upload a food photo and watch the AI work its magic!**

*Made with ❤️ and tested on countless food photos (yes, we ate a lot of pizza for science)*