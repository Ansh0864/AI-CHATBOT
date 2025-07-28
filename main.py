import tkinter as tk
from tkinter import messagebox
from functions import (
    create_splash_screen, fade_in, 
    VIBRANT_THEME_COLORS, 
    chat_log, entry, product_search_entry, mode_btn_frame, action_frame, theme_btn # Import globals for linking
)
import functions as func_module # Import functions module to access its globals
from database import create_database, setup_product_database

# ---------------- Main Application Setup ----------------
if __name__ == "__main__":
    # Initialize databases
    create_database()
    setup_product_database()

    # Tkinter root window setup
    func_module.root = tk.Tk() # Link the global root in functions.py
    func_module.root.title("Smart ChatBot")
    func_module.root.geometry("600x700") 
    func_module.root.resizable(True, True) 
    func_module.root.attributes("-alpha", 0.0) 

    # Initial setup of root background (before fade-in)
    func_module.root.configure(bg=VIBRANT_THEME_COLORS["main_bg"])

    # Create and show the splash screen first
    func_module.create_splash_screen()

    # Start the fade-in animation
    func_module.root.after(100, fade_in, func_module.root, 0.0) 

    func_module.root.mainloop()