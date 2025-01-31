import customtkinter as ctk
import string
import random
import pyperclip
import requests
from tkinter import messagebox

class GeneratePasswordPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color='#212c56')
        self.controller = controller

        # Title Label
        title_label = ctk.CTkLabel(self, text="Generate Password", font=("Arial", 18, "bold"))
        title_label.place(x=205, y=15)

        # Special Characters Toggle
        self.special_chars_var = ctk.BooleanVar(value=True)
        self.special_chars_switch = ctk.CTkSwitch(self, text="Special Characters", progress_color="#2b5de4", button_color="#ffffff", variable=self.special_chars_var)
        self.special_chars_switch.place(x=200, y=70)

        # Capital Letters Toggle
        self.cap_letters_var = ctk.BooleanVar(value=True)
        self.cap_letters_switch = ctk.CTkSwitch(self, text="Capital Letters", progress_color="#2b5de4", button_color="#ffffff", variable=self.cap_letters_var)
        self.cap_letters_switch.place(x=500, y=70)

        # Password Length Label
        self.length_label = ctk.CTkLabel(self, text="Length: 12", font=("Arial", 14))
        self.length_label.place(x=205, y=150)

        # Password Length Slider
        self.length_slider = ctk.CTkSlider(self, from_=6, to=25, number_of_steps=19, width=337, fg_color="#333742", progress_color="#2b5de4", button_color="#ffffff", command=self.update_length)
        self.length_slider.set(12)
        self.length_slider.place(x=300, y=155)

        # Password Strength Indicator
        self.strength_label = ctk.CTkLabel(self, text="Strength: N/A", font=("Arial", 14))
        self.strength_label.place(x=205, y=220)

        self.strength_bar = ctk.CTkProgressBar(self, width=385, fg_color="#333742")
        self.strength_bar.set(0)
        self.strength_bar.place(x=205, y=250)

        # Password Text Field
        self.password_entry = ctk.CTkEntry(self, width=385, height=40, border_color="#203b85", fg_color="#333742", font=("Arial", 14), show="*")
        self.password_entry.place(x=205, y=265)

        # Visibility Button with Tooltip
        self.show_password_var = ctk.BooleanVar(value=False)
        self.toggle_visibility_button = ctk.CTkButton(self, text="👁️", width=40, fg_color="#b18a57", height=40, command=self.toggle_visibility)
        self.toggle_visibility_button.place(x=595, y=265)

        # Tooltip Effect
        self.toggle_visibility_button.bind("<Enter>", self.show_tooltip)
        self.toggle_visibility_button.bind("<Leave>", self.hide_tooltip)

        # Generate Button
        generate_button = ctk.CTkButton(self, text="Generate Password", width=60, height=40, command=self.generate_password)
        generate_button.place(x=205, y=355)

        # Copy Button (corrected to instance variable)
        self.copy_button = ctk.CTkButton(self, text="Copy", width=140, height=40, command=self.copy_to_clipboard)
        self.copy_button.place(x=500, y=355)

    def update_length(self, value):
        self.length_label.configure(text=f"Length: {int(value)}")

    def fetch_words(self):
        try:
            response = requests.get("https://api.datamuse.com/words?ml=common&max=50", timeout=5)
            if response.status_code == 200:
                words = [word["word"].capitalize() for word in response.json()]
                if len(words) < 2:
                    raise ValueError("Not enough words from API.")
                return words
            else:
                raise ValueError(f"API returned status code {response.status_code}")
        except Exception as e:
            messagebox.showwarning("Warning", "Password cannot be generated. Try again later.")
            return None

    def generate_password(self):
        length = int(self.length_slider.get())
        words = self.fetch_words()
        if not words or len(words) < 2:
            return  # Error already handled in fetch_words

        word1, word2 = random.sample(words, 2)
        if not self.cap_letters_var.get():
            word1, word2 = word1.lower(), word2.lower()

        # Generate digits
        digits = ''.join(random.choices(string.digits, k=random.randint(1, 3)))
        special_chars = "!@#$%?"
        special_selection = ''.join(random.choices(special_chars, k=random.randint(1, 2))) if self.special_chars_var.get() else ''

        password = f"{word1}{special_selection}{digits}{word2}"

        # Prepare extra characters based on toggles
        letters = string.ascii_letters if self.cap_letters_var.get() else string.ascii_lowercase
        if self.special_chars_var.get():
            extra_chars = letters + string.digits + special_chars
        else:
            extra_chars = letters + string.digits

        while len(password) < length:
            password += random.choice(extra_chars)
        password = password[:length]

        self.password_entry.delete(0, 'end')
        self.password_entry.insert(0, password)
        self.update_strength(password)

    def update_strength(self, password):
        length = len(password)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%?" for c in password)

        strength_index = sum([has_upper, has_lower, has_digit, has_special])

        if length > 14 and strength_index == 4:
            strength_index = 4  # Very strong
        elif length > 10 and strength_index >= 3:
            strength_index = 3  # Strong
        elif length > 8 and strength_index >= 2:
            strength_index = 2  # Moderate
        elif length > 6:
            strength_index = 1  # Weak
        else:
            strength_index = 0  # Very Weak

        strength_levels = ["Very Weak", "Weak", "Moderate", "Strong", "Very Strong"]
        strength_colors = ["#8B0000", "#FF0000", "#FFA500", "#32CD32", "#008000"]

        self.strength_label.configure(text=f"Strength: {strength_levels[strength_index]}")
        self.strength_bar.set((strength_index + 1) / 5)
        self.strength_bar.configure(progress_color=strength_colors[strength_index])

    def toggle_visibility(self):
        if self.show_password_var.get():
            self.password_entry.configure(show="*")
            self.show_password_var.set(False)
            self.toggle_visibility_button.configure(text="👁️")
        else:
            self.password_entry.configure(show="")
            self.show_password_var.set(True)
            self.toggle_visibility_button.configure(text="🔒")

    def show_tooltip(self, event):
        self.tooltip = ctk.CTkLabel(self, text="Show/Hide Password", font=("Arial", 12), fg_color="#333333", text_color="white", corner_radius=5)
        self.tooltip.place(x=580, y=310)

    def hide_tooltip(self, event):
        if hasattr(self, "tooltip"):
            self.tooltip.destroy()

    def copy_to_clipboard(self):
        password = self.password_entry.get()
        if password:
            pyperclip.copy(password)
            self.copy_button.configure(text="Copied!", fg_color="#32CD32")
            self.after(1500, lambda: self.copy_button.configure(text="Copy", fg_color="#b18a57"))
            messagebox.showinfo("Copied", "Password copied to clipboard!")