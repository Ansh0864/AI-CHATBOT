import sqlite3
import os
import random
from faker import Faker

# ---------------- Main Chatbot Database ----------------
def create_database():
    db_file = "chatbot.db"
    if not os.path.exists(db_file):
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chatbot_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            input TEXT NOT NULL,
            response TEXT NOT NULL
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        dummy_data = [
            ('greetings', 'hello', 'Hi there! How can I help you today?'),
            ('greetings', 'hi', 'Hello! What can I do for you?'),
            ('greetings', 'hey','Hey!'),
            ('greetings','how are you','Im just a bot, but thanks for asking!'),
            ('farewells', 'bye', 'Goodbye! Have a nice day!'),
            ('farewells','thanks','Anytime!'),
            ('farewells','thank you','You are welcome!'),
            ('faq', 'what is your name', 'Im a smart chatbot.'),
            ('what do you want to eat','I dont eat. I am a bot!'),
            ('jokes', 'tell me a joke', "Why don’t scientists trust atoms? They make up everything!")
        ]
        cursor.executemany("INSERT INTO chatbot_data (category, input, response) VALUES (?, ?, ?)", dummy_data)
        conn.commit()
        conn.close()

# ---------------- Product Database (Expanded) ----------------
def setup_product_database():
    conn = sqlite3.connect("chatbot_data.db")
    cursor = conn.cursor()

    # Drop table if it exists to ensure a clean slate for new data
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL UNIQUE,
            description TEXT,
            price REAL,
            stock_count INTEGER,
            category TEXT,
            brand TEXT,
            color TEXT,
            size TEXT,
            material TEXT,
            average_rating REAL,
            warranty_info TEXT,
            model_number TEXT,    -- New field
            weight_kg REAL,      -- New field
            dimensions_cm TEXT,  -- New field (e.g., "10x5x2")
            release_date TEXT    -- New field (e.g., "YYYY-MM-DD")
        )""")

    fake = Faker()

    # Expanded Categories and Product Types
    categories = [
        "Electronics", "Apparel", "Books", "Home & Kitchen", "Sports & Outdoors",
        "Beauty & Personal Care", "Toys & Games", "Automotive"
    ]
    product_types = {
        "Electronics": ["Laptop", "Smartphone", "Headphones", "Smartwatch", "Camera", "Gaming Console"],
        "Apparel": ["T-Shirt", "Sneakers", "Jacket", "Jeans", "Dress", "Hoodie"],
        "Books": ["Novel", "Cookbook", "Science Fiction", "Biography", "Children's Book"],
        "Home & Kitchen": ["Coffee Maker", "Blender", "Vacuum Cleaner", "Dinnerware Set", "Lamp"],
        "Sports & Outdoors": ["Yoga Mat", "Running Shoes", "Tent", "Bicycle", "Dumbbells"],
        "Beauty & Personal Care": ["Shampoo", "Face Cream", "Perfume", "Hair Dryer", "Electric Toothbrush"],
        "Toys & Games": ["Action Figure", "Board Game", "Building Blocks", "Puzzle", "Remote Control Car"],
        "Automotive": ["Car Charger", "Dash Cam", "Tire Pressure Gauge", "Car Seat Cover"]
    }
    
    # Expanded Brands
    brands = [
        "Sony", "Apple", "Nike", "Samsung", "Dell", "Adidas", "Microsoft", "Google",
        "HP", "Lenovo", "Bose", "JBL", "Logitech", "Philips", "LG", "Whirlpool",
        "Electrolux", "KitchenAid", "Columbia", "The North Face", "L'Oréal", "Gillette",
        "LEGO", "Mattel", "Hasbro", "Bosch", "Snap-on"
    ]
    
    # Expanded Attributes
    colors = ["Black", "White", "Blue", "Red", "Green", "Silver", "Gold", "Pink", "Grey"]
    sizes = ["Small", "Medium", "Large", "X-Large", "One Size", "S", "M", "L", "XL"]
    materials = ["Plastic", "Metal", "Cotton", "Polyester", "Wood", "Glass", "Ceramic", "Leather"]
    warranty_info = ["1-year", "2-year", "3-year", "Lifetime Limited", "No warranty", "6-months"]

    products = []
    num_products = 500 # Increase the number of dummy products for a larger database

    for i in range(num_products):
        category = random.choice(categories)
        ptype = random.choice(product_types[category])
        brand = random.choice(brands)
        
        # Ensure unique product names by adding a unique identifier
        name_suffix = f"_{random.randint(1000, 9999)}_{fake.word().capitalize()}"
        product_name = f"{brand} {ptype} {name_suffix}"
        
        # Check for uniqueness, although the suffix should help
        if product_name in [p[1] for p in products]:
            continue

        product = (
            i + 1,
            product_name,
            fake.paragraph(nb_sentences=3, variable_nb_sentences=True), # More descriptive description
            round(random.uniform(20.0, 5000.0), 2), # Wider price range
            random.randint(0, 500), # Wider stock range
            category,
            brand,
            random.choice(colors),
            random.choice(sizes),
            random.choice(materials),
            round(random.uniform(1.0, 5.0), 1), # Rating from 1.0 to 5.0
            random.choice(warranty_info),
            fake.bothify(text='????-######'), # Model Number (e.g., ABCD-123456)
            round(random.uniform(0.1, 10.0), 2), # Weight in kg
            f"{random.randint(1, 100)}x{random.randint(1, 100)}x{random.randint(1, 50)}", # Dimensions
            fake.date_between(start_date='-5y', end_date='today').isoformat() # Release Date
        )
        products.append(product)

    cursor.executemany("""
        INSERT INTO products (
            id, product_name, description, price, stock_count, category,
            brand, color, size, material, average_rating, warranty_info,
            model_number, weight_kg, dimensions_cm, release_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)
    
    conn.commit()
    conn.close()
    print(f"Product database created/updated with {num_products} dummy products.")