import os
import sqlite3
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageDraw
from io import BytesIO
import hashlib
import keyring  # Used to retrieve passwords from the system keyring


# LOGO PROCESSING UTILITY
logo_image_cache = {}

# Dynamic path to logos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
fav_on = os.path.join(BASE_DIR, "resources/fav_on.png")
clipboard = os.path.join(BASE_DIR, "resources/Clipboard.png")

# Process logo images
def process_logo_image(logo_blob, target_size=(50, 50), corner_radius=25, background_color="#3e4a89"):
    if not logo_blob:
        return None

    blob_hash = hashlib.md5(logo_blob).hexdigest()
    key = (blob_hash, target_size, corner_radius, background_color)
    if key in logo_image_cache:
        return logo_image_cache[key]

    image_data = BytesIO(logo_blob)
    img = Image.open(image_data)
    if img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    if w != h:
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))

    img = img.resize(target_size, Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", target_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, target_size[0], target_size[1]), radius=corner_radius, fill=255)
    img.putalpha(mask)

    bg = Image.new("RGBA", target_size, background_color)
    img = Image.alpha_composite(bg, img)

    logo_image_cache[key] = img
    return img

# 6 Columns layout
class FavoritesPage(ctk.CTkFrame):
    def __init__(self, parent, controller, os=None):
        super().__init__(parent, fg_color='#212c56')
        self.controller = controller
        self.last_favorites_count = 0

        # Favorite toggle images
        self.fav_off_image = ctk.CTkImage(
            light_image=Image.open(fav_on),
            dark_image=Image.open(fav_on)
        )
        self.clipboard_image = ctk.CTkImage(
            light_image=Image.open(clipboard),
            dark_image=Image.open(clipboard)
        )

        # Scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, width=805, height=410, corner_radius=20, fg_color="#2b3564"
        )
        self.scrollable_frame.pack(expand=True, fill="both", padx=25, pady=20)

        self.fav_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent", corner_radius=10)
        self.fav_container.pack(expand=True, fill="both")

        for i in range(6):
            self.fav_container.grid_columnconfigure(i, weight=1)

        self.populate_favorites()
        self.auto_refresh_favorites()  # Start auto refreshing

#Loads favorite accounts and displays them in a grid layout.
    def populate_favorites(self):
        for w in self.fav_container.winfo_children():
            w.destroy()

        try:
            with sqlite3.connect("appdata.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT entry_id, account_name, website_url, associated_email,
                           keyring_service, keyring_username, created_at, username, logo, favorite, user_id
                    FROM saved_accounts
                    WHERE user_id=? AND favorite=1
                """, (self.controller.current_user_id,))
                records = cursor.fetchall()
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                self.display_no_favorites_message()
                self.last_favorites_count = 0
                return
            else:
                raise

        self.last_favorites_count = len(records)  # Update count tracker
        col_limit = 6
        row_idx = 0
        col_idx = 0

        for row in records:
            (entry_id, acct_name, website_url, email,
             keyring_service, keyring_username, created_at, username,
             logo_blob, favorite, user_id) = row

            card_frame = ctk.CTkFrame(
                self.fav_container, width=120, height=155,
                corner_radius=10, fg_color="#3e4a89"
            )
            card_frame.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="nsew")
            card_frame.grid_propagate(False)

            # Logo Frame (Circular)
            logo_frame = ctk.CTkFrame(card_frame, width=45, height=45, corner_radius=22, fg_color="#1f1f1f")
            logo_frame.pack(pady=5)
            logo_frame.grid_propagate(False)

            abbreviation = (acct_name[:2].upper() if acct_name else "??")
            if logo_blob:
                try:
                    circ_logo = process_logo_image(logo_blob, target_size=(45, 45), corner_radius=22)
                    ctk_img = ctk.CTkImage(light_image=circ_logo, dark_image=circ_logo, size=(45, 45))
                    logo_label = ctk.CTkLabel(logo_frame, text="", image=ctk_img)
                    logo_label.image = ctk_img
                    logo_label.pack(expand=True, fill="both")
                except Exception as e:
                    print("Error loading circular logo:", e)
                    self._show_abbrev(logo_frame, abbreviation)
            else:
                self._show_abbrev(logo_frame, abbreviation)

            # Account Name Label
            acct_label = ctk.CTkLabel(card_frame, text=acct_name if acct_name else "Untitled",
                                      font=("Helvetica", 11, "bold"), text_color="white")
            acct_label.pack(pady=1)

            # Unfavorite Button
            unfav_button = ctk.CTkButton(
                card_frame, text="", image=self.fav_off_image,
                fg_color="#3e4a89", hover_color="#3e4a89",
                width=25, corner_radius=10, command=lambda e=entry_id: self.unfavorite(e)
            )
            unfav_button.pack(pady=1)

            # Copy Username Button
            copy_user_btn = ctk.CTkButton(
                card_frame, text=" Username", image=self.clipboard_image,
                fg_color="#3e4a89", hover_color="#5a637a", border_color="#1e254b", border_width=1,
                width=95, height=25, corner_radius=10,
                command=lambda u=username: self.copy_to_clipboard(u)
            )
            copy_user_btn.pack(pady=1)

            # Copy Password Button
            # Retrieve it from the system keyring using keyring_service and keyring_username.
            copy_pass_btn = ctk.CTkButton(
                card_frame, text=" Password", image=self.clipboard_image,
                fg_color="#3e4a89", hover_color="#5a637a", border_color="#1e254b", border_width=1,
                width=95, height=25, corner_radius=10,
                command=lambda s=keyring_service, u=keyring_username: self.copy_password(s, u)
            )
            copy_pass_btn.pack(pady=(1, 5))

            col_idx += 1
            if col_idx >= col_limit:
                col_idx = 0
                row_idx += 1

# Shows an abbreviation if no logo is available.
    def _show_abbrev(self, parent, abbreviation):
        lbl = ctk.CTkLabel(parent, text=abbreviation, font=("Helvetica", 12, "bold"), text_color="white")
        lbl.place(relx=0.5, rely=0.5, anchor="center")

# Removes from favorites
    def unfavorite(self, entry_id):
        with sqlite3.connect("appdata.db") as conn:
            cur = conn.cursor()
            cur.execute("UPDATE saved_accounts SET favorite=0 WHERE entry_id=?", (entry_id,))
            conn.commit()
        self.populate_favorites()

# Copies text to clipboard
    def copy_to_clipboard(self, text):
        top = self.winfo_toplevel()
        top.clipboard_clear()
        top.clipboard_append(text)
        top.update()

# Retrieves the password from the system keyring using the provided service and username, then copies it to the clipboard.
    def copy_password(self, service, keyring_username):
        try:
            password = keyring.get_password(service, keyring_username)
            if password:
                self.copy_to_clipboard(password)
            else:
                messagebox.showerror("Error", "Password not found in keyring!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve password: {str(e)}")

# Checks if the database has new favorite records and updates UI if needed.
    def auto_refresh_favorites(self):
        try:
            with sqlite3.connect("appdata.db") as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM saved_accounts WHERE user_id=? AND favorite=1",
                               (self.controller.current_user_id,))
                current_count = cursor.fetchone()[0]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                current_count = 0
            else:
                raise

        if current_count != self.last_favorites_count:
            self.populate_favorites()

        self.after(2000, self.auto_refresh_favorites)  # Check every 2 seconds

# Display a message when there are no favorites or the table doesn't exist.
    def display_no_favorites_message(self):
        for w in self.fav_container.winfo_children():
            w.destroy()
        message_label = ctk.CTkLabel(
            self.fav_container,
            text="No favorite accounts stored.",
            font=("Helvetica", 18),
            fg_color="transparent",
            text_color="white"
        )
        message_label.pack(expand=True)
