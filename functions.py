import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import requests, ast, operator, datetime, wikipedia, sqlite3, os, random
import pyttsx3, speech_recognition as sr
from faker import Faker
import json
import csv
import PyPDF2
import webbrowser
import threading
import re 
import io # Import io for StringIO

# Global variables for GUI elements (will be set in main.py)
root = None
chat_log = None
entry = None
product_search_entry = None
mode_btn_frame = None
action_frame = None
theme_btn = None
current_frame = None

# Global for theme state
THEME = "dark"

# --- Constants and Configurations ---
# Vibrant Theme Palette
VIBRANT_THEME_COLORS = {
    "main_bg": "#1A2B3C",        # Deep Blue-Gray
    "splash_bg": "#2C3E50",      # Darker Blue-Gray for splash
    "chat_bg": "#2A3C4E",        # Slightly lighter than main_bg for chat log
    "text_color": "#ECF0F0",     # Light Gray (Almost White)
    "user_text": "#85C1E9",      # Light Sky Blue
    "bot_text": "#58D68D",       # Vibrant Green
    "input_bg": "#34495E",       # Medium Blue-Gray
    "input_fg": "#ECF0F1",       # Light Gray
    "button_bg": "#3498DB",      # Bright Blue
    "button_fg": "#FFFFFF",      # White
    "mode_info": "#F1C40F",      # Bright Yellow
    "border_color": "#7F8C8D",   # Grayish Blue for borders
    "accent_color": "#E74C3C"    # Red accent for active states/errors
}

# Fonts
MAIN_FONT = ("Arial", 11)
CHAT_FONT = ("Consolas", 11) # Often good for monospace chat
ENTRY_FONT = ("Arial", 11)
BUTTON_FONT = ("Arial", 9, "bold")
MODE_FONT = ("Arial", 10, "italic")

# Regex for URL detection (more robust for general URLs)
URL_REGEX = r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"

# Chatbot Engine Configuration
WEATHER_API_KEY = "8f72c5c0031647e19e261127250107"
MODE = "general"
engine = pyttsx3.init()

# Load intents from JSON file
INTENTS = {}
try:
    with open('intents.json', 'r', encoding='utf-8') as file:
        INTENTS = json.load(file)
except FileNotFoundError:
    messagebox.showerror("Error", "intents.json not found. Please ensure the file is in the same directory.")
    exit() # Exit if intents.json is critical for operation

# ---------------- File Analysis - Summarization ----------------
def summarize_file(filepath):
    """Summarizes the content of a given text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
            summary_lines = lines[:5] if len(lines) > 5 else lines
            summary = "\n".join(summary_lines)
            word_count = len(content.split())
            char_count = len(content)
            return (f"File: {os.path.basename(filepath)}\n"
                    f"Word count: {word_count}\n"
                    f"Character count: {char_count}\n"
                    f"First few lines:\n{summary}\n"
                    f"Content defined as: Text document. Likely contains general information or notes.")
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except UnicodeDecodeError: # Added for explicit encoding error
        return f"Error: Could not read text file {filepath} due to incorrect encoding. Try saving it as UTF-8."
    except Exception as e:
        return f"Error reading file {filepath}: {e}"

def summarize_csv(filepath):
    """Summarizes the content of a given CSV file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader) # Read all rows into a list
            if not rows:
                return "CSV file is empty."
            
            header = rows[0]
            num_rows = len(rows) - 1 # Exclude header for count of data rows
            num_columns = len(header)
            
            summary_info = (f"File: {os.path.basename(filepath)}\n"
                            f"Content type: Comma Separated Values (CSV)\n"
                            f"Number of rows (excluding header): {num_rows}\n"
                            f"Number of columns: {num_columns}\n"
                            f"Headers: {', '.join(header)}\n")
            
            # Display first few data rows
            data_preview = []
            for i, row in enumerate(rows[1:]): # Start from the first data row (after header)
                if i < 3: # Display up to 3 data rows
                    data_preview.append(f"Row {i+1}: {', '.join(row)}")
                else:
                    break
            
            if data_preview:
                summary_info += "First few data rows:\n" + "\n".join(data_preview)
            
            return summary_info
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except UnicodeDecodeError: # Added for explicit encoding error
        return f"Error: Could not read CSV file {filepath} due to incorrect encoding. Try saving it as UTF-8."
    except Exception as e:
        return f"Error reading CSV file {filepath}: {e}"

def summarize_pdf(filepath):
    """Extracts text from a PDF and provides a summary."""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            text_content = ""
            for i in range(min(num_pages, 2)): # Extract text from first 2 pages for summary
                text_content += reader.pages[i].extract_text() or ""
            
            words = text_content.split()
            summary_text = " ".join(words[:100]) + "..." if len(words) > 100 else text_content
            
            return (f"File: {os.path.basename(filepath)}\n"
                    f"Content type: PDF Document\n"
                    f"Number of pages: {num_pages}\n"
                    f"Summary of first pages:\n{summary_text}\n"
                    f"Content defined as: Portable Document Format. May contain text, images, and other multimedia elements.")
    except PyPDF2.errors.PdfReadError:
        return f"Error: Could not read PDF file {filepath}. It might be corrupted or encrypted."
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except Exception as e:
        return f"Error processing PDF file {filepath}: {e}"

def open_and_summarize_file():
    """Opens a file dialog, reads the selected file, and summarizes its content."""
    filepath = filedialog.askopenfilename(
        title="Select a file to summarize",
        filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("PDF files", "*.pdf"),
                   ("All files", "*.*")]
    )
    if filepath:
        file_extension = os.path.splitext(filepath)[1].lower()
        if file_extension == '.csv':
            summary = summarize_csv(filepath)
        elif file_extension == '.txt':
            summary = summarize_file(filepath)
        elif file_extension == '.pdf':
            summary = summarize_pdf(filepath)
        else:
            summary = "I can only summarize .txt, .csv, and .pdf files at the moment."
        
        chat_log.config(state=tk.NORMAL)
        chat_log.insert(tk.END, f"Bot (File Summary):\n{summary}\n\n", "bot_tag")
        chat_log.tag_config("bot_tag", foreground=VIBRANT_THEME_COLORS["bot_text"])
        chat_log.config(state=tk.DISABLED)
        chat_log.yview(tk.END)
        speak("Here is the summary of the file you selected.")

# ---------------- File Analysis - Reading Content ----------------
def read_file_content(filepath):
    """Reads the full content of a given text, CSV, or PDF file."""
    file_extension = os.path.splitext(filepath)[1].lower()
    content = ""
    try:
        if file_extension == '.txt':
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            return f"Content of {os.path.basename(filepath)}:\n\n{content}"
        
        elif file_extension == '.csv':
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                # Use csv.StringIO for better handling if content might be large
                output = io.StringIO()
                writer = csv.writer(output)
                for row in reader:
                    writer.writerow(row)
                content = output.getvalue()
            return f"Content of {os.path.basename(filepath)}:\n\n{content}"
            
        elif file_extension == '.pdf':
            with open(filepath, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    content += reader.pages[page_num].extract_text() or ""
            if not content.strip():
                return f"Content of {os.path.basename(filepath)}:\n\n(No readable text found in PDF or PDF is empty.)"
            return f"Content of {os.path.basename(filepath)}:\n\n{content}"
            
        else:
            return "I can only read .txt, .csv, and .pdf files."
            
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except PyPDF2.errors.PdfReadError:
        return f"Error: Could not read PDF file {filepath}. It might be corrupted or encrypted."
    except UnicodeDecodeError: # Added for explicit encoding error
        return f"Error: Could not read file {filepath} due to incorrect encoding. Try saving it as UTF-8."
    except Exception as e:
        return f"Error reading file {filepath}: {e}"

def open_and_read_file():
    """Opens a file dialog, reads the selected file's content, and displays it."""
    filepath = filedialog.askopenfilename(
        title="Select a file to read",
        filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("PDF files", "*.pdf"),
                   ("All files", "*.*")]
    )
    if filepath:
        file_content = read_file_content(filepath)
        chat_log.config(state=tk.NORMAL)
        chat_log.insert(tk.END, f"Bot (File Content):\n{file_content}\n\n", "bot_tag")
        chat_log.tag_config("bot_tag", foreground=VIBRANT_THEME_COLORS["bot_text"])
        chat_log.config(state=tk.DISABLED)
        chat_log.yview(tk.END)
        speak("Here is the content of the file you selected.")

# ---------------- Website Link Function ----------------
def open_website_link(query):
    """
    Constructs a URL based on the query and opens it in the default web browser.
    """
    query_lower = query.lower().strip()
    url = ""

    # Prioritize direct URLs
    if query_lower.startswith("http://") or query_lower.startswith("https://"):
        url = query_lower
    elif "." in query_lower and " " not in query_lower: # Simple check for domain-like input
        url = f"https://www.{query_lower}"
    # Specific website mappings
    elif "google" in query_lower:
        url = "https://www.google.com"
    elif "youtube" in query_lower:
        url = "https://www.youtube.com" # Corrected YouTube URL
    elif "wikipedia" in query_lower:
        url = "https://www.wikipedia.org"
    elif "amazon" in query_lower:
        url = "https://www.amazon.com"
    elif "facebook" in query_lower:
        url = "https://www.facebook.com"
    elif "twitter" in query_lower or "x.com" in query_lower:
        url = "https://x.com"
    elif "github" in query_lower:
        url = "https://github.com"
    elif "stackoverflow" in query_lower:
        url = "https://stackoverflow.com"
    else:
        # Default to a Google search
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    try:
        webbrowser.open_new_tab(url)
        return f"Opening {query} in your web browser. URL: {url}" 
    except Exception as e:
        return f"Sorry, I couldn't open the link for '{query}'. Error: {e}"

# ---------------- Feature Handlers (Existing) ----------------
def get_wikipedia_summary(query):
    try:
        return wikipedia.summary(query, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        return "Sorry, I am unable to understand this." # Updated as requested
    except wikipedia.exceptions.PageError:
        return "Sorry, I couldn't find anything on that topic."
    except Exception:
        return "Sorry, I am unable to understand this."

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
    except requests.exceptions.RequestException:
        return "Failed to fetch weather info. Please check your internet connection."
    except Exception:
        return "An unexpected error occurred while fetching weather info."

def safe_eval(expr):
    try:
        node = ast.parse(expr, mode='eval').body
        return eval_expr(node)
    except (SyntaxError, TypeError, ZeroDivisionError):
        return "Invalid calculation or operation."
    except Exception:
        return "An unexpected error occurred during calculation."

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

# ---------------- Product Information Retrieval (Updated to show new fields) ----------------
def get_product_info(product_name):
    conn = sqlite3.connect("chatbot_data.db")
    cursor = conn.cursor()
    # Select all fields, including the new ones
    cursor.execute("""
        SELECT 
            product_name, description, price, stock_count, category, brand, 
            color, size, material, average_rating, warranty_info,
            model_number, weight_kg, dimensions_cm, release_date
        FROM products
        WHERE lower(product_name) LIKE ?
    """, (f"%{product_name.lower()}%",))
    result = cursor.fetchone()
    conn.close()

    if result:
        (pname, desc, price, stock, category, brand, color, size, material, 
         rating, warranty, model, weight, dimensions, release_date) = result
        
        info = f"Product: {pname}\n" \
               f"Description: {desc}\n" \
               f"Price: ₹{price:.2f}\n" \
               f"Stock: {stock} units\n" \
               f"Category: {category}\n" \
               f"Brand: {brand}\n" \
               f"Color: {color}\n" \
               f"Size: {size}\n" \
               f"Material: {material}\n" \
               f"Rating: {rating}/5\n" \
               f"Warranty: {warranty}\n" \
               f"Model No.: {model}\n" \
               f"Weight: {weight} kg\n" \
               f"Dimensions: {dimensions} cm\n" \
               f"Release Date: {release_date}"
        return info
    else:
        return f"Sorry, I couldn't find any product information for '{product_name}'. Please try a different name or a more general search."


# ---------------- Intent Recognition (Improved with Regex) ----------------
def get_intent(user_input):
    user_input_lower = user_input.lower()

    for intent_data in INTENTS['intents']:
        for pattern in intent_data['patterns']:
            # Convert placeholder patterns to regex
            # e.g., "what is the weather in {{city}}" -> r"what is the weather in (?P<city>.+)"
            # e.g., "search for {{product_name}} branded products" -> r"search for (?P<product_name>.+) branded products"

            # Find all placeholders in the pattern
            placeholders = re.findall(r'\{\{(\w+)\}\}', pattern)
            
            # Create a regex pattern from the intent pattern
            regex_pattern_str = re.escape(pattern) # Escape special regex characters
            for p in placeholders:
                regex_pattern_str = regex_pattern_str.replace(re.escape(f'{{{{{p}}}}}'), r'(?P<' + p + r'>.+)')
            
            # Compile the regex for case-insensitive matching
            regex_pattern = re.compile(regex_pattern_str, re.IGNORECASE)
            
            match = regex_pattern.match(user_input_lower)
            if match:
                # Extract entities from named groups
                entities = {k: v for k, v in match.groupdict().items() if v is not None}
                return intent_data['tag'], entities
            
            # If no placeholders, check for exact match
            if not placeholders and user_input_lower == pattern.lower():
                return intent_data['tag'], {}

    return "unknown_intent", {}

# ---------------- Chatbot Response Logic ----------------
def chatbot_response(user_input):
    global MODE
    message = user_input.lower().strip()
    
    # Check for hardcoded mode changes first
    if "general mode" in message or "switch to general" in message:
        set_mode("general")
        return "Switched to General chat mode."
    elif "calculate mode" in message or "switch to calculate" in message:
        set_mode("calculate")
        return "Switched to Calculator mode. Enter your calculations directly."
    elif "weather mode" in message or "switch to weather" in message:
        set_mode("weather")
        return "Switched to Weather mode. Just tell me the city name."

    # Handle current mode
    if MODE == "calculate":
        return f"Result: {safe_eval(user_input)}"
    elif MODE == "weather":
        return get_weather(user_input)

    # If not in a special mode, or if special mode message was for switching, proceed with intent recognition
    intent, entities = get_intent(user_input)
    response = ""

    if intent == "greeting":
        response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'greeting'][0]['responses'])
    elif intent == "goodbye":
        response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'goodbye'][0]['responses'])
    elif intent == "faq_identity":
        response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'faq_identity'][0]['responses'])
    elif intent == "faq_eating":
        response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'faq_eating'][0]['responses'])
    elif intent == "gratitude":
        response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'gratitude'][0]['responses'])
    elif intent == "joke":
        response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'joke'][0]['responses'])
    elif intent == "search_brand":
        brand = entities.get('brand')
        if brand:
            conn = sqlite3.connect("chatbot_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, price FROM products WHERE lower(brand) LIKE ?", (f"%{brand.lower()}%",))
            results = cursor.fetchall()
            conn.close()
            if results:
                top = "\n".join([f"{name} - ₹{price}" for name, price in results[:5]])
                response = f"Top results for brand '{brand}':\n{top}"
            else:
                response = f"No products found for brand '{brand}'."
        else:
            response = "Please specify a brand to search for."
    elif intent == "search_category":
        category = entities.get('category')
        if category:
            conn = sqlite3.connect("chatbot_data.db")
            cursor = conn.cursor()
            cursor.execute("SELECT product_name, price FROM products WHERE lower(category) LIKE ?", (f"%{category.lower()}%",))
            results = cursor.fetchall()
            conn.close()
            if results:
                top = "\n".join([f"{name} - ₹{price}" for name, price in results[:5]])
                response = f"Top results for category '{category}':\n{top}"
            else:
                response = f"No products found in category '{category}'."
        else:
            response = "Please specify a category to search for."
    elif intent == "GetProductInfo":
        product_name = entities.get('product_name')
        if product_name:
            response = get_product_info(product_name)
        else:
            # Fallback for general product queries not caught by specific intent patterns
            prod_conn = sqlite3.connect("chatbot_data.db")
            prod_cursor = prod_conn.cursor()
            prod_cursor.execute("SELECT product_name, price, description FROM products WHERE lower(product_name) LIKE ?", (f"%{message}%",))
            prod_result = prod_cursor.fetchone()
            prod_conn.close()
            if prod_result:
                pname, price, desc = prod_result
                response = f"{pname}\nPrice: ₹{price}\nDetails: {desc}"
            else:
                response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'unknown_intent'][0]['responses'])
    elif intent == "Get Weather":
        city = entities.get('city')
        if city:
            response = get_weather(city)
        else:
            response = "Please specify a city for weather information."
    elif intent == "Country Info":
        country = entities.get('country')
        if country:
            response = get_wikipedia_summary(country)
        else:
            response = "Please specify a country for information."
    elif intent == "website_open":
        site_name = entities.get('site_name')
        if site_name:
            response = open_website_link(site_name)
        else:
            response = "Please tell me which website you'd like to open."
    else: # If intent is "unknown_intent" or no specific intent was matched
        conn = sqlite3.connect("chatbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT response FROM chatbot_data WHERE lower(input) = ?", (message,))
        db_result = cursor.fetchone()
        
        if db_result:
            response = db_result[0]
        else:
            response = get_wikipedia_summary(message)
            if "Sorry, I couldn't find anything" in response or "Sorry, I am unable to understand this" in response:
                response = random.choice([r for r in INTENTS['intents'] if r['tag'] == 'unknown_intent'][0]['responses'])
        conn.close()

    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_logs (user_input, bot_response) VALUES (?, ?)", (user_input, response))
    conn.commit()
    conn.close()
    return response

# ---------------- GUI Functions (Need to be updated to use global widgets) ----------------

def show_frame(frame_to_show):
    """Destroys the current frame and packs the new one."""
    global current_frame
    if current_frame:
        current_frame.destroy()
    current_frame = frame_to_show
    current_frame.pack(fill=tk.BOTH, expand=True)

def fade_in(window, alpha):
    """Gradually increases window transparency for a fade-in effect."""
    if alpha < 1.0:
        alpha += 0.05 
        window.attributes("-alpha", alpha)
        window.after(50, fade_in, window, alpha) 
    else:
        window.attributes("-alpha", 1.0) 

def create_splash_screen():
    """Creates and displays the initial splash screen with buttons."""
    splash_frame = tk.Frame(root, bg=VIBRANT_THEME_COLORS["splash_bg"])

    tk.Label(splash_frame, text="Welcome to Smart ChatBot!",
             font=("Arial", 24, "bold"), fg=VIBRANT_THEME_COLORS["text_color"],
             bg=VIBRANT_THEME_COLORS["splash_bg"]).pack(pady=50)

    # Buttons for splash screen
    button_style = {
        "font": ("Arial", 16, "bold"),
        "width": 20,
        "height": 2,
        "relief": "raised",
        "borderwidth": 0,
        "fg": VIBRANT_THEME_COLORS["button_fg"]
    }

    tk.Button(splash_frame, text="Start Chat",
              bg=VIBRANT_THEME_COLORS["button_bg"],
              activebackground=VIBRANT_THEME_COLORS["accent_color"],
              activeforeground=VIBRANT_THEME_COLORS["button_fg"],
              command=create_chat_interface, **button_style).pack(pady=10)

    tk.Button(splash_frame, text="About Chatbot",
              bg=VIBRANT_THEME_COLORS["button_bg"],
              activebackground=VIBRANT_THEME_COLORS["accent_color"],
              activeforeground=VIBRANT_THEME_COLORS["button_fg"],
              command=show_about_dialog, **button_style).pack(pady=10)

    tk.Button(splash_frame, text="Exit",
              bg=VIBRANT_THEME_COLORS["accent_color"], 
              activebackground=VIBRANT_THEME_COLORS["button_bg"],
              activeforeground=VIBRANT_THEME_COLORS["button_fg"],
              command=root.quit, **button_style).pack(pady=10)

    show_frame(splash_frame)

def create_chat_interface():
    """Creates and displays the main chat interface."""
    global chat_log, entry, product_search_entry, mode_btn_frame, action_frame, theme_btn 

    chat_frame = tk.Frame(root, bg=VIBRANT_THEME_COLORS["main_bg"])

    # Chat Log Area
    chat_log = scrolledtext.ScrolledText(chat_frame, state=tk.DISABLED, wrap=tk.WORD,
                                         font=CHAT_FONT,
                                         bg=VIBRANT_THEME_COLORS["chat_bg"], 
                                         fg=VIBRANT_THEME_COLORS["text_color"],
                                         insertbackground=VIBRANT_THEME_COLORS["input_fg"],
                                         borderwidth=1, relief="flat",
                                         highlightbackground=VIBRANT_THEME_COLORS["border_color"],
                                         highlightthickness=1)
    chat_log.pack(padx=15, pady=15, fill=tk.BOTH, expand=True)

    # Define tags for chat messages and links
    chat_log.tag_config("user_tag", foreground=VIBRANT_THEME_COLORS["user_text"])
    chat_log.tag_config("bot_tag", foreground=VIBRANT_THEME_COLORS["bot_text"])
    chat_log.tag_config("mode_tag", foreground=VIBRANT_THEME_COLORS["mode_info"], font=MODE_FONT)
    chat_log.tag_config("link", foreground="blue", underline=True) 
    chat_log.tag_bind("link", "<Button-1>", open_link_from_chat)

    # Product Search Frame
    product_search_frame = tk.Frame(chat_frame, bg=VIBRANT_THEME_COLORS["main_bg"])
    product_search_frame.pack(padx=15, pady=(5, 5), fill=tk.X)

    tk.Label(product_search_frame, text="Product Name:", font=ENTRY_FONT,
             bg=VIBRANT_THEME_COLORS["main_bg"], fg=VIBRANT_THEME_COLORS["text_color"]).pack(side=tk.LEFT, padx=(0, 5))

    product_search_entry = tk.Entry(product_search_frame, font=ENTRY_FONT,
                                     bg=VIBRANT_THEME_COLORS["input_bg"],
                                     fg=VIBRANT_THEME_COLORS["input_fg"],
                                     insertbackground=VIBRANT_THEME_COLORS["input_fg"],
                                     relief="flat", borderwidth=1,
                                     highlightbackground=VIBRANT_THEME_COLORS["border_color"],
                                     highlightthickness=1)
    product_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
    product_search_entry.bind("<Return>", lambda event: search_product_gui()) 

    tk.Button(product_search_frame, text="Search Product", font=BUTTON_FONT,
              bg=VIBRANT_THEME_COLORS["button_bg"], fg=VIBRANT_THEME_COLORS["button_fg"],
              relief="raised", borderwidth=0, activebackground=VIBRANT_THEME_COLORS["accent_color"],
              command=search_product_gui).pack(side=tk.RIGHT, padx=(5, 0))

    # Input Entry (General Chat)
    entry = tk.Entry(chat_frame, font=ENTRY_FONT,
                     bg=VIBRANT_THEME_COLORS["input_bg"],
                     fg=VIBRANT_THEME_COLORS["input_fg"],
                     insertbackground=VIBRANT_THEME_COLORS["input_fg"],
                     relief="flat", borderwidth=1,
                     highlightbackground=VIBRANT_THEME_COLORS["border_color"],
                     highlightthickness=1)
    entry.pack(padx=15, pady=(0, 10), fill=tk.X, ipady=5)
    entry.focus() 

    # Mode Buttons Frame
    mode_btn_frame = tk.Frame(chat_frame, bg=VIBRANT_THEME_COLORS["main_bg"])
    mode_btn_frame.pack(pady=(0, 10))

    button_common_style = {
        "font": BUTTON_FONT,
        "bg": VIBRANT_THEME_COLORS["button_bg"],
        "fg": VIBRANT_THEME_COLORS["button_fg"],
        "relief": "raised",
        "borderwidth": 0,
        "activebackground": VIBRANT_THEME_COLORS["accent_color"],
        "activeforeground": VIBRANT_THEME_COLORS["button_fg"]
    }

    tk.Button(mode_btn_frame, text="General", width=12,
              command=lambda: set_mode("general"), **button_common_style).grid(row=0, column=0, padx=5, pady=2)
    tk.Button(mode_btn_frame, text="Calculate", width=12,
              command=lambda: set_mode("calculate"), **button_common_style).grid(row=0, column=1, padx=5, pady=2)
    tk.Button(mode_btn_frame, text="Weather", width=12,
              command=lambda: set_mode("weather"), **button_common_style).grid(row=0, column=2, padx=5, pady=2)

    # Action Buttons Frame
    action_frame = tk.Frame(chat_frame, bg=VIBRANT_THEME_COLORS["main_bg"])
    action_frame.pack(pady=(0, 15))

    tk.Button(action_frame, text="Send", **button_common_style,
              command=send_message).grid(row=0, column=0, padx=4, pady=2)
    tk.Button(action_frame, text="🎤 Voice Input", **button_common_style,
              command=voice_input).grid(row=0, column=1, padx=4, pady=2)
    tk.Button(action_frame, text="🔊 Speak Text", **button_common_style,
              command=lambda: speak(entry.get())).grid(row=0, column=2, padx=4, pady=2)

    tk.Button(action_frame, text="📁 Summarize File", **button_common_style,
              command=open_and_summarize_file).grid(row=1, column=0, padx=4, pady=2)
    tk.Button(action_frame, text="📄 Read File", **button_common_style,
              command=open_and_read_file).grid(row=1, column=1, padx=4, pady=2)
    tk.Button(action_frame, text="💾 Export Chat", **button_common_style,
              command=export_chat).grid(row=1, column=2, padx=4, pady=2)

    theme_btn = tk.Button(chat_frame, text="☀️ Toggle Theme", **button_common_style,
                          command=lambda: toggle_theme())
    theme_btn.pack(pady=(0, 10))

    show_frame(chat_frame)
    entry.bind("<Return>", lambda event: send_message()) 
    root.bind("<F11>", toggle_theme) 

def search_product_gui():
    """Handles the product search initiated from the dedicated search bar."""
    product_query = product_search_entry.get().strip()
    if not product_query:
        messagebox.showwarning("Input Error", "Please enter a product name to search.")
        return

    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, f"You (Product Search): {product_query}\n", "user_tag")
    
    response = get_product_info(product_query)
    
    chat_log.insert(tk.END, "Bot (Product Info): ", "bot_tag")
    chat_log.insert(tk.END, response + "\n\n", "bot_tag")
    
    chat_log.config(state=tk.DISABLED)
    chat_log.yview(tk.END)
    product_search_entry.delete(0, tk.END) 
    speak(response) 

def show_about_dialog():
    """Displays an 'About' message box."""
    messagebox.showinfo("About Smart ChatBot",
                         "Smart ChatBot v1.0\n\n"
                         "Developed to assist with general queries, calculations, "
                         "weather information, product lookups, file summarization, "
                         "and web Browse.\n\n"
                         "Features:\n"
                         "- General conversational responses\n"
                         "- Mathematical calculations\n"
                         "- Current weather information\n"
                         "- Product database search\n"
                         "- Text, CSV, and PDF file summarization/reading\n"
                         "- Web link opening\n"
                         "- Voice input and text-to-speech output\n"
                         "- Dark/Light theme toggle\n"
                         "- Chat export\n\n"
                         "Enjoy!")

def open_link_from_chat(event):
    """Callback for clickable links in the chat log."""
    try:
        index = chat_log.index(f"@{event.x},{event.y}")
        
        if "link" in chat_log.tag_names(index):
            all_link_ranges = chat_log.tag_ranges("link")
            clicked_link_range = None

            for i in range(0, len(all_link_ranges), 2):
                start = all_link_ranges[i]
                end = all_link_ranges[i+1]
                if chat_log.compare(index, ">=", start) and chat_log.compare(index, "<", end):
                    clicked_link_range = (start, end)
                    break
            
            if clicked_link_range:
                url = chat_log.get(clicked_link_range[0], clicked_link_range[1])
                if url:
                    webbrowser.open_new_tab(url)
    except Exception as e:
        print(f"Error opening link: {e}") 

def send_message():
    user_input = entry.get().strip()
    if not user_input:
        return
    
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, f"You: {user_input}\n", "user_tag")
    
    response = chatbot_response(user_input)
    
    chat_log.insert(tk.END, "Bot: ", "bot_tag") 
    
    matches = list(re.finditer(URL_REGEX, response))
    current_pos = 0

    for match in matches:
        if match.start() > current_pos:
            chat_log.insert(tk.END, response[current_pos:match.start()], "bot_tag")
        
        chat_log.insert(tk.END, match.group(0), ("bot_tag", "link"))
        
        current_pos = match.end()

    if current_pos < len(response):
        chat_log.insert(tk.END, response[current_pos:], "bot_tag")

    chat_log.insert(tk.END, "\n\n", "bot_tag")
    
    chat_log.config(state=tk.DISABLED)
    chat_log.yview(tk.END)
    entry.delete(0, tk.END)
    speak(response)

def export_chat():
    try:
        filename = datetime.datetime.now().strftime("chat_%Y%m%d_%H%M.txt")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(chat_log.get("1.0", tk.END).strip())
        messagebox.showinfo("Exported", f"Chat saved as {filename}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def set_mode(new_mode):
    global MODE
    MODE = new_mode
    message = f"Chat mode set to: {MODE.capitalize()}\n"
    chat_log.config(state=tk.NORMAL)
    chat_log.insert(tk.END, message, "mode_tag")
    chat_log.config(state=tk.DISABLED)
    chat_log.yview(tk.END)
    speak(message)


# ---------------- Voice ----------------
def speak(text):
    def run_speak():
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS Thread Error: {e}")

    speak_thread = threading.Thread(target=run_speak)
    speak_thread.daemon = True
    speak_thread.start()

def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Listening...")
        try:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            entry.delete(0, tk.END)
            entry.insert(0, text)
            send_message()
        except sr.UnknownValueError:
            speak("Could not understand audio.")
        except sr.RequestError as e:
            speak(f"Speech recognition service error; {e}")
        except Exception:
            speak("An unexpected error occurred during voice input.")

# ---------------- Theme Toggle Function ----------------
def toggle_theme(event=None): 
    global THEME

    if THEME == "dark":
        THEME = "light"
        # Define light theme specific colors for widgets
        main_bg_color = "white"
        chat_log_bg = "white"
        text_color = "black"
        user_text_color = "blue"
        bot_text_color = "darkgreen"
        input_bg = "white"
        input_fg = "black"
        button_bg = "#E0E0E0" 
        button_fg = "black"
        button_active_bg = "#CCCCCC" 
        widget_border_color = "#CCCCCC" 
        theme_btn.config(text="🌙 Toggle Theme")
        
    else: # Switching to dark theme
        THEME = "dark"
        # Define dark theme specific colors for widgets from the palette
        main_bg_color = VIBRANT_THEME_COLORS["main_bg"]
        chat_log_bg = VIBRANT_THEME_COLORS["chat_bg"]
        text_color = VIBRANT_THEME_COLORS["text_color"]
        user_text_color = VIBRANT_THEME_COLORS["user_text"]
        bot_text_color = VIBRANT_THEME_COLORS["bot_text"]
        input_bg = VIBRANT_THEME_COLORS["input_bg"]
        input_fg = VIBRANT_THEME_COLORS["input_fg"]
        button_bg = VIBRANT_THEME_COLORS["button_bg"]
        button_fg = VIBRANT_THEME_COLORS["button_fg"]
        button_active_bg = VIBRANT_THEME_COLORS["accent_color"]
        widget_border_color = VIBRANT_THEME_COLORS["border_color"]
        theme_btn.config(text="☀️ Toggle Theme")

    # Apply determined colors to root and widgets
    root.configure(bg=main_bg_color)
    
    chat_log.configure(bg=chat_log_bg, 
                       fg=text_color, 
                       insertbackground=input_fg, 
                       highlightbackground=widget_border_color)
    
    # Update tag colors
    chat_log.tag_config("user_tag", foreground=user_text_color)
    chat_log.tag_config("bot_tag", foreground=bot_text_color)
    chat_log.tag_config("mode_tag", foreground=VIBRANT_THEME_COLORS["mode_info"] if THEME == "dark" else "purple") 
    chat_log.tag_config("link", foreground="blue", underline=True) 

    entry.configure(bg=input_bg, 
                    fg=input_fg, 
                    insertbackground=input_fg, 
                    highlightbackground=widget_border_color)
    
    # Update product search entry
    if product_search_entry: 
        product_search_entry.configure(bg=input_bg, 
                                       fg=input_fg, 
                                       insertbackground=input_fg, 
                                       highlightbackground=widget_border_color)

    # Update colors for mode buttons
    if mode_btn_frame: 
        for btn in mode_btn_frame.winfo_children():
            btn.config(bg=button_bg, fg=button_fg, activebackground=button_active_bg)
    
    # Update colors for action buttons
    if action_frame: 
        for btn in action_frame.winfo_children():
            btn.config(bg=button_bg, fg=button_fg, activebackground=button_active_bg)

    # Update theme button itself
    theme_btn.config(bg=button_bg, fg=button_fg, activebackground=button_active_bg)