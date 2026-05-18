import streamlit as st
import sqlite3
import os
import random
import re
import ast
import operator
import json
import csv
import PyPDF2
import wikipedia
import requests
from database import create_database, setup_product_database

# Set up page configurations
st.set_page_config(page_title="Smart ChatBot", page_icon="🤖", layout="wide")

# ---------------- Initialize Databases ----------------
if "db_initialized" not in st.session_state:
    create_database()
    setup_product_database()
    st.session_state["db_initialized"] = True

# ---------------- Load Intents ----------------
@st.cache_data
def load_intents():
    try:
        with open('intents.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("intents.json not found. Please ensure it is in the application directory.")
        return {"intents": []}

INTENTS = load_intents()
WEATHER_API_KEY = "8f72c5c0031647e19e261127250107"

# ---------------- Core Engine Logic ----------------
def get_weather(city):
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
        data = requests.get(url).json()
        if "error" in data:
            return f"Weather error: {data['error']['message']}"
        cond = data['current']['condition']['text']
        temp = data['current']['temp_c']
        loc = data['location']['name']
        return f"The weather in {loc} is {cond} with {temp}°C."
    except Exception:
        return "Failed to fetch weather info. Please check your network connection."

def safe_eval(expr):
    try:
        node = ast.parse(expr, mode='eval').body
        return eval_expr(node)
    except Exception:
        return "Invalid calculation or operation."

def eval_expr(node):
    ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg
    }
    if isinstance(node, ast.BinOp):
        return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
    elif isinstance(node, ast.UnaryOp):
        return ops[type(node.op)](eval_expr(node.operand))
    elif isinstance(node, ast.Constant):
        return node.value
    else:
        raise TypeError("Unsupported operation.")

def get_product_info(product_name):
    conn = sqlite3.connect("chatbot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            product_name, description, price, stock_count, category, brand, 
            color, size, material, average_rating, warranty_info,
            model_number, weight_kg, dimensions_cm, release_date
        FROM products WHERE lower(product_name) LIKE ?
    """, (f"%{product_name.lower()}%",))
    result = cursor.fetchone()
    conn.close()

    if result:
        return (f"**Product**: {result[0]}\n\n"
                f"**Description**: {result[1]}\n\n"
                f"**Price**: ₹{result[2]:.2f} | **Stock**: {result[3]} units\n\n"
                f"**Brand**: {result[5]} | **Category**: {result[4]}\n\n"
                f"**Rating**: {result[9]}/5 | **Model**: {result[11]}")
    return f"Sorry, I couldn't find any product information for '{product_name}'."

def get_intent(user_input):
    user_input_lower = user_input.lower()
    for intent_data in INTENTS['intents']:
        for pattern in intent_data['patterns']:
            placeholders = re.findall(r'\{\{(\w+)\}\}', pattern)
            regex_pattern_str = re.escape(pattern)
            for p in placeholders:
                regex_pattern_str = regex_pattern_str.replace(re.escape(f'{{{{{p}}}}}'), r'(?P<' + p + r'>.+)')
            regex_pattern = re.compile(regex_pattern_str, re.IGNORECASE)
            match = regex_pattern.match(user_input_lower)
            if match:
                entities = {k: v for k, v in match.groupdict().items() if v is not None}
                return intent_data['tag'], entities
            if not placeholders and user_input_lower == pattern.lower():
                return intent_data['tag'], {}
    return "unknown_intent", {}

def chatbot_response(user_input, active_mode):
    message = user_input.lower().strip()
    
    if active_mode == "Calculate":
        return f"Result: {safe_eval(user_input)}"
    elif active_mode == "Weather":
        return get_weather(user_input)

    intent, entities = get_intent(user_input)
    
    if intent == "greeting":
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'greeting'][0]['responses'])
    elif intent == "goodbye":
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'goodbye'][0]['responses'])
    elif intent == "faq_identity":
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'faq_identity'][0]['responses'])
    elif intent == "faq_eating":
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'faq_eating'][0]['responses'])
    elif intent == "gratitude":
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'gratitude'][0]['responses'])
    elif intent == "joke":
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'joke'][0]['responses'])
    elif intent == "GetProductInfo":
        return get_product_info(entities.get('product_name', message))
    elif intent == "Get Weather":
        return get_weather(entities.get('city', ''))
    else:
        conn = sqlite3.connect("chatbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM chatbot_data WHERE lower(input) = ?", (message,))
        db_result = cursor.fetchone()
        conn.close()
        if db_result:
            return db_result[0]
        return random.choice([r for r in INTENTS['intents'] if r['tag'] == 'unknown_intent'][0]['responses'])

# ---------------- Streamlit Web Interface ----------------
st.title("🤖 Smart ChatBot Workspace")

# Sidebar configurations
st.sidebar.header("Chat Controls & Features")
chat_mode = st.sidebar.radio("Select Operational Mode", ["General", "Calculate", "Weather"])

# Dedicated Product Search Section
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Quick Product Lookup")
prod_query = st.sidebar.text_input("Enter Product Name:")
if st.sidebar.button("Search Product") and prod_query:
    st.sidebar.info(get_product_info(prod_query))

# File Summary Upload Utilities
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Document Analyst")
uploaded_file = st.sidebar.file_uploader("Upload a file for analytical summary", type=["txt", "csv", "pdf"])

if uploaded_file is not None:
    filename = uploaded_file.name
    if filename.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8")
        st.sidebar.write(f"**Word Count**: {len(text.split())}")
        st.sidebar.text_area("Preview", text[:300])
    elif filename.endswith(".csv"):
        st.sidebar.write("CSV detected successfully.")
        # Streamlit handles dataframes beautifully natively
        import pandas as pd
        df = pd.read_csv(uploaded_file)
        st.sidebar.dataframe(df.head(3))
    elif filename.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        st.sidebar.write(f"**Total Pages**: {len(reader.pages)}")

# Main conversational log array setup
if "messages" not in st.session_state:
    st.session_state.messages = []

# Output the running message ledger
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Accepting current user prompt entries
if prompt := st.chat_input("Say something to the bot..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Process the text engine output response
    response = chatbot_response(prompt, chat_mode)
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Chat logs backup export download pipeline
if st.session_state.messages:
    chat_history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
    st.sidebar.download_button("💾 Export Current Chat Logs", chat_history_text, file_name="chat_history.txt")