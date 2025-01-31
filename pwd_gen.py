import tkinter
import customtkinter as ctk
import string
import random
import pyperclip
import requests
from tkinter import messagebox
from tkinter import PhotoImage
from PIL import Image, ImageTk

class GeneratePasswordPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color='#212c56')
        self.controller = controller

        # Load Images
        self.eye_img = self.load_resized_image("eye.png", (24, 24))  # Resize to 24x24 pixels
        self.lock_img = self.load_resized_image("lock.png", (24, 24))  # Resize to 24x24 pixels

        # Frame
        frame = ctk.CTkFrame(self, width=840, height=450, corner_radius=20, fg_color="#2b3564")
        frame.pack(expand=True, padx=20, pady=20)
        frame.place(x=25, y=20)

        # Title Label
        title_label = ctk.CTkLabel(frame, text="Generate Password", font=("Arial", 20, "bold"))
        title_label.place(x=340, y=20)

        # Special Characters Toggle
        self.special_chars_var = ctk.BooleanVar(value=True)
        self.special_chars_switch = ctk.CTkSwitch(frame, text="Symbols", progress_color="#32CD32", button_color="#e0e0e0", variable=self.special_chars_var)
        self.special_chars_switch.place(x=200, y=85)

        # Uppercase Letters Toggle
        self.cap_letters_var = ctk.BooleanVar(value=True)
        self.cap_letters_switch = ctk.CTkSwitch(frame, text="Uppercase", progress_color="#32CD32", button_color="#e0e0e0", variable=self.cap_letters_var)
        self.cap_letters_switch.place(x=373, y=85)

        # Numbers Toggle
        self.numbers_var = ctk.BooleanVar(value=True)
        self.numbers_switch = ctk.CTkSwitch(frame, text="Numbers", progress_color="#32CD32", button_color="#e0e0e0", variable=self.numbers_var)
        self.numbers_switch.place(x=533, y=85)

        # Password Length Label
        self.length_label = ctk.CTkLabel(frame, text="Length: 12", font=("Arial", 14))
        self.length_label.place(x=205, y=170)

        # Password Length Slider
        self.length_slider = ctk.CTkSlider(frame, from_=6, to=25, number_of_steps=19, width=337, fg_color="#cccccc", progress_color="#1e254b", button_color="#e0e0e0", command=self.update_length)
        self.length_slider.set(12)
        self.length_slider.place(x=300, y=175)

        # Password Strength Indicator
        self.strength_label = ctk.CTkLabel(frame, text="Strength: N/A", font=("Arial", 14))
        self.strength_label.place(x=205, y=232)

        self.strength_bar = ctk.CTkProgressBar(frame, width=373, fg_color="#e0e0e0",border_width=0,height=10,)
        self.strength_bar.set(0)
        self.strength_bar.place(x=205, y=263)

        # Password Text Field
        self.password_entry = ctk.CTkEntry(frame, width=385, height=40,corner_radius=10,border_width=2, border_color="#1e254b", fg_color="#697499", font=("Arial", 14), show="*")
        self.password_entry.place(x=200, y=265)

        # Visibility Button with Tooltip
        self.show_password_var = ctk.BooleanVar(value=False)
        self.toggle_visibility_button = ctk.CTkButton(frame, image=self.eye_img, text="", border_width=2, border_color="#697499", width=40, corner_radius=10, fg_color="#1e254b", height=40,command=self.toggle_visibility)
        self.toggle_visibility_button.place(x=590, y=265)

        # Tooltip Effect
        self.toggle_visibility_button.bind("<Enter>", self.show_tooltip)
        self.toggle_visibility_button.bind("<Leave>", self.hide_tooltip)

        # Generate Button
        generate_button = ctk.CTkButton(frame, text="Generate Password", width=60, height=40,border_color= "#697499",fg_color="#1e254b",border_width=2, corner_radius=60, command=self.generate_password)
        generate_button.place(x=200, y=355)

        # Copy Button
        self.copy_button = ctk.CTkButton(frame, text="Copy", width=165, height=40,border_color= "#697499",fg_color="#1e254b",border_width=2, corner_radius=60, command=self.copy_to_clipboard)
        self.copy_button.place(x=480, y=355)

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
            return

        word1, word2 = random.sample(words, 2)
        if not self.cap_letters_var.get():
            word1, word2 = word1.lower(), word2.lower()

        # Generate digits and symbols
        digits = ''.join(random.choices(string.digits, k=random.randint(1, 3))) if self.numbers_var.get() else ''
        special_chars = "!@#$%?"
        special_selection = ''.join(
            random.choices(special_chars, k=random.randint(1, 2))) if self.special_chars_var.get() else ''

        # Calculate the space needed for symbols and digits
        mandatory_length = len(special_selection) + len(digits)
        available_space = length - mandatory_length

        # Making sure it don't exceed the desired length
        if mandatory_length > length:
            # Reduce symbols and digits
            reduce_by = mandatory_length - length
            # Prioritize reducing symbols first
            if len(special_selection) >= reduce_by:
                special_selection = special_selection[:-reduce_by]
            else:
                reduce_by -= len(special_selection)
                special_selection = ''
                digits = digits[:-reduce_by] if len(digits) >= reduce_by else ''
            mandatory_length = len(special_selection) + len(digits)
            available_space = length - mandatory_length

        # Split available space between word1 and word2
        word1_max = min(len(word1), available_space)
        word2_max = max(0, available_space - word1_max)
        word1_part = word1[:word1_max]
        word2_part = word2[:word2_max]

        # Combine parts
        password = f"{word1_part}{special_selection}{digits}{word2_part}"

        # Fill remaining space with extra characters
        remaining_space = length - len(password)
        if remaining_space > 0:
            extra_chars = []
            letters = string.ascii_letters if self.cap_letters_var.get() else string.ascii_lowercase
            extra_chars.extend(letters)
            if self.numbers_var.get():
                extra_chars.extend(string.digits)
            if self.special_chars_var.get():
                extra_chars.extend(special_chars)
            # Ensure extra characters are available
            if extra_chars:
                extra = ''.join(random.choices(extra_chars, k=remaining_space))
                password += extra

        password = password[:length]

        # Making sure symbols/digits are included if toggled (in case they were truncated)
        if self.special_chars_var.get() and not any(c in special_chars for c in password):
            # Replace a random character with a symbol
            if len(password) > 0:
                pos = random.randint(0, len(password) - 1)
                password = password[:pos] + random.choice(special_chars) + password[pos + 1:]

        if self.numbers_var.get() and not any(c.isdigit() for c in password):
            # Replace a random character with a digit
            if len(password) > 0:
                pos = random.randint(0, len(password) - 1)
                password = password[:pos] + random.choice(string.digits) + password[pos + 1:]

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

    def load_resized_image(self, path, size):
        img = Image.open(path)
        img = img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)

    def toggle_visibility(self):
        if self.show_password_var.get():
            self.password_entry.configure(show="")
            self.show_password_var.set(False)
            self.toggle_visibility_button.configure(image=self.lock_img)  # Change to lock icon
        else:
            self.password_entry.configure(show="*")
            self.show_password_var.set(True)
            self.toggle_visibility_button.configure(image=self.eye_img)  # Change to eye icon

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