import customtkinter as ctk
import sqlite3
import datetime
import webbrowser
from io import BytesIO
from PIL import Image, ImageDraw
from tkinter import filedialog, messagebox
import tkinter as tk
import hashlib
import keyring  # keyring import

# cache for processed images
logo_image_cache = {}

# Crop/resize/round an image from BLOB
def process_logo_image(logo_blob, target_size, corner_radius=20, background_color=None):
    blob_hash = hashlib.md5(logo_blob).hexdigest()
    key = (blob_hash, target_size, corner_radius, background_color)
    if key in logo_image_cache:
        return logo_image_cache[key]

    image_data = BytesIO(logo_blob)
    img = Image.open(image_data)
    if img.mode != "RGB":
        img = img.convert("RGB")

    width, height = img.size
    if width != height:
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        img = img.crop((left, top, left + side, top + side))

    img = img.resize(target_size, Image.LANCZOS)
    img = img.convert("RGBA")

    # Rounded mask
    mask = Image.new("L", target_size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, target_size[0], target_size[1]), radius=corner_radius, fill=255)
    img.putalpha(mask)

    if background_color is not None:
        background = Image.new("RGBA", target_size, background_color)
        img = Image.alpha_composite(background, img)

    logo_image_cache[key] = img
    return img


class StoredPasswordsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color='#212c56')  # Main background
        self.controller = controller
        self.account_frames = {}

        # Database connection
        self.conn = sqlite3.connect("appdata.db")
        self.conn.row_factory = sqlite3.Row

        # FAVORITE ICONS
        self.fav_on_img = ctk.CTkImage(
            light_image=Image.open("resources/fav_on.png"),
            dark_image=Image.open("resources/fav_on.png"),
            size=(20, 20)
        )
        self.fav_off_img = ctk.CTkImage(
            light_image=Image.open("resources/fav_off.png"),
            dark_image=Image.open("resources/fav_off.png"),
            size=(20, 20)
        )

        # Left Panel
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, width=200, height=410, corner_radius=20, fg_color="#2b3564"
        )
        self.scrollable_frame.grid(row=0, column=0, padx=(25, 12), pady=20)

        # Search
        self.search_bar = ctk.CTkEntry(
            self.scrollable_frame,
            placeholder_text="Search account...",
            fg_color="#3e4a89",
            height=30
        )
        self.search_bar.pack(fill="x", padx=(5, 10), pady=(10, 5))
        self.search_bar.bind("<KeyRelease>", self.on_search)

        self.accounts_container = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        self.accounts_container.pack(fill="both", expand=True)

        # Right panel display accounts details
        self.regular_frame = ctk.CTkFrame(
            self, width=580, height=450, corner_radius=20, fg_color="#2b3564"
        )
        self.regular_frame.grid(row=0, column=1, padx=(12, 25), pady=20)
        self.regular_frame.grid_propagate(False)

        self.default_label = ctk.CTkLabel(
            self.regular_frame,
            text="Select an account to view details",
            font=("Helvetica", 18),
            fg_color="transparent",
            text_color="white"
        )
        self.default_label.place(relx=0.5, rely=0.5, anchor="center")

        self.current_account_id = None
        self.current_logo_blob = None
        self.edit_entries = {}
        self.password_visible = False
        self.edit_password_visible = False

        # Start auto refresh
        self.populate_saved_accounts()
        self.auto_refresh_accounts(interval=2000)  # Auto refresh every 2 seconds

    def auto_refresh_accounts(self, interval=2000):
        self.populate_saved_accounts(self.search_bar.get())
        self.after(interval, lambda: self.auto_refresh_accounts(interval))

    def on_search(self, event):
        search_text = self.search_bar.get()
        self.populate_saved_accounts(search_text)

    def populate_saved_accounts(self, search_text=""):
        cursor = self.conn.cursor()
        query = """
            SELECT entry_id, account_name, website_url, associated_email,
                   keyring_service, keyring_username, created_at, username, logo,
                   favorite
            FROM saved_accounts
            WHERE user_id = ?
        """
        params = [self.controller.current_user_id]
        if search_text:
            query += " AND account_name LIKE ?"
            params.append(f"%{search_text}%")
        try:
            cursor.execute(query, params)
            accounts = cursor.fetchall()
        except sqlite3.OperationalError as e:
            # If the table does not exist
            if "no such table" in str(e):
                self.display_no_accounts_message()
                return
            else:
                raise

        # Create a dict of current accounts from DB (keyed by entry_id)
        new_accounts = {account["entry_id"]: account for account in accounts}

        # Remove widgets for accounts that no longer exist
        for entry_id in list(self.account_frames.keys()):
            if entry_id not in new_accounts:
                self.account_frames[entry_id].destroy()
                del self.account_frames[entry_id]

        # Update existing widgets and create new ones if necessary
        for account in accounts:
            entry_id = account["entry_id"]
            account_name = account["account_name"]
            website_url = account["website_url"]
            associated_email = account["associated_email"]
            keyring_service = account["keyring_service"]
            keyring_username = account["keyring_username"]
            created_at = account["created_at"]
            username = account["username"]
            logo_blob = account["logo"]
            favorite_value = account["favorite"]  # 0 or 1
            is_favorite = bool(favorite_value)

            # Retrieve password from keyring
            if keyring_service and keyring_username:
                account_password = keyring.get_password(keyring_service, keyring_username) or ""
            else:
                account_password = ""

            a = (
                entry_id, account_name, website_url, associated_email,
                account_password, created_at, username, logo_blob,
                keyring_service, keyring_username, is_favorite
            )

            abbreviation = account_name[:2].upper()
            default_color = "#3e4a89"
            selected_color = "#536dff"
            container_color = selected_color if self.current_account_id == entry_id else default_color

            if entry_id in self.account_frames:
                # Update existing widget properties
                account_frame = self.account_frames[entry_id]
                account_frame.configure(fg_color=container_color)
                if hasattr(account_frame, 'account_label'):
                    account_frame.account_label.configure(text=account_name)
                if hasattr(account_frame, 'favorite_button'):
                    account_frame.favorite_button.configure(
                        image=self.fav_on_img if is_favorite else self.fav_off_img,
                        hover_color=container_color
                    )
                if hasattr(account_frame, 'logo_label'):
                    if logo_blob:
                        try:
                            target_size = (40, 40)
                            img = process_logo_image(logo_blob, target_size, corner_radius=20, background_color=container_color)
                            logo_img_small = ctk.CTkImage(light_image=img, dark_image=img, size=target_size)
                            # Clear text when logo image is available
                            account_frame.logo_label.configure(image=logo_img_small, text="")
                            account_frame.logo_label.image = logo_img_small
                        except Exception as e:
                            print("Error processing logo:", e)
                            account_frame.logo_label.configure(text=abbreviation)
                    else:
                        account_frame.logo_label.configure(text=abbreviation)
            else:
                # Each account row
                account_frame = ctk.CTkFrame(
                    self.accounts_container,
                    height=40,
                    corner_radius=10,
                    fg_color=container_color
                )
                account_frame.pack(fill="x", padx=(3, 10), pady=2)
                self.account_frames[entry_id] = account_frame

                # Press animations
                account_frame.bind("<ButtonPress-1>", lambda e, f=account_frame: f.pack_configure(padx=(6, 10)))
                account_frame.bind("<ButtonRelease-1>", lambda e, f=account_frame: f.pack_configure(padx=(3, 10)))
                account_frame.bind("<Button-1>", lambda e, ac=a: self.display_account_details_view(ac))

                # Logo
                logo_frame = ctk.CTkFrame(
                    account_frame, width=40, height=40, corner_radius=20, fg_color="#1f1f1f"
                )
                logo_frame.pack(side="left", padx=5, pady=5)
                logo_frame.grid_propagate(False)

                if logo_blob:
                    try:
                        target_size = (40, 40)
                        img = process_logo_image(logo_blob, target_size, corner_radius=20, background_color=container_color)
                        logo_img_small = ctk.CTkImage(light_image=img, dark_image=img, size=target_size)
                        logo_label = ctk.CTkLabel(logo_frame, image=logo_img_small, text="")
                        logo_label.image = logo_img_small
                        logo_label.pack(expand=True, fill="both")
                    except Exception as e:
                        print("Error processing logo:", e)
                        logo_label = ctk.CTkLabel(
                            logo_frame,
                            text=abbreviation,
                            font=("Helvetica", 20, "bold"),
                            fg_color="transparent",
                            text_color="white"
                        )
                        logo_label.place(relx=0.5, rely=0.5, anchor="center")
                else:
                    # If no logo show abbreviation
                    logo_label = ctk.CTkLabel(
                        logo_frame,
                        text=abbreviation,
                        font=("Helvetica", 20, "bold"),
                        fg_color="transparent",
                        text_color="white"
                    )
                    logo_label.place(relx=0.5, rely=0.5, anchor="center")
                # Save a reference to update later
                account_frame.logo_label = logo_label

                # Account Label
                account_label = ctk.CTkLabel(
                    account_frame,
                    text=account_name,
                    font=("Helvetica", 16),
                    fg_color="transparent",
                    text_color="white"
                )
                account_label.pack(side="left", padx=(15, 10), pady=5)
                account_label.bind("<Button-1>", lambda e, ac=a: self.display_account_details_view(ac))
                account_frame.account_label = account_label

                # Favorite Toggle
                favorite_button = ctk.CTkButton(
                    account_frame,
                    text="",
                    image=self.fav_on_img if is_favorite else self.fav_off_img,
                    fg_color="transparent",
                    hover_color=container_color,
                    width=30,
                    height=30,
                    command=lambda e_id=entry_id, curr=is_favorite: self.toggle_favorite(e_id, not curr)
                )
                favorite_button.pack(side="right", padx=(0, 10), pady=5)
                account_frame.favorite_button = favorite_button

                # Bind detail view to label/logo
                for widget in (account_label, logo_frame, logo_label):
                    widget.bind("<Button-1>", lambda e, ac=a: self.display_account_details_view(ac))

    def display_no_accounts_message(self):
        for widget in self.regular_frame.winfo_children():
            widget.destroy()
        message_label = ctk.CTkLabel(
            self.regular_frame,
            text="No account has been stored.",
            font=("Helvetica", 18),
            fg_color="transparent",
            text_color="white"
        )
        message_label.place(relx=0.5, rely=0.5, anchor="center")

    def toggle_favorite(self, entry_id, new_favorite_state):
        val_to_store = 1 if new_favorite_state else 0
        cursor = self.conn.cursor()
        cursor.execute("UPDATE saved_accounts SET favorite = ? WHERE entry_id = ?", (val_to_store, entry_id))
        self.conn.commit()

        # Refresh left panel
        self.populate_saved_accounts()

        # If toggled the currently displayed account refresh detail view
        if entry_id == self.current_account_id:
            cursor.execute("""
                SELECT entry_id, account_name, website_url, associated_email,
                       keyring_service, keyring_username, created_at, username, logo,
                       favorite
                FROM saved_accounts
                WHERE entry_id = ?
            """, (entry_id,))
            row = cursor.fetchone()
            if row:
                updated_fav = bool(row["favorite"])
                if row["keyring_service"] and row["keyring_username"]:
                    pwd = keyring.get_password(row["keyring_service"], row["keyring_username"]) or ""
                else:
                    pwd = ""
                account_tuple = (
                    row["entry_id"],
                    row["account_name"],
                    row["website_url"],
                    row["associated_email"],
                    pwd,
                    row["created_at"],
                    row["username"],
                    row["logo"],
                    row["keyring_service"],
                    row["keyring_username"],
                    updated_fav
                )
                self.display_account_details_view(account_tuple)

    def open_website(self, url):
        if url:
            webbrowser.open(url)

    def display_account_details_view(self, account):
        (entry_id, account_name, website_url, associated_email,
         account_password, created_at, username, logo_blob,
         keyring_service, keyring_username, is_favorite) = account

        self.current_account_id = entry_id
        self.current_logo_blob = logo_blob
        self.password_visible = False

        # Highlight selected account on left panel
        for aid, frame in self.account_frames.items():
            frame.configure(fg_color="#536dff" if aid == self.current_account_id else "#3e4a89")

        # Clear right panel
        for widget in self.regular_frame.winfo_children():
            widget.destroy()

        details_frame = ctk.CTkFrame(
            self.regular_frame, width=560, height=430, corner_radius=20, fg_color="#2b3564"
        )
        details_frame.place(x=10, y=10)
        details_frame.grid_propagate(False)

        fav_button_details = ctk.CTkButton(
            details_frame,
            text="",
            image=self.fav_on_img if is_favorite else self.fav_off_img,
            fg_color="transparent",
            hover_color="#2b3564",
            width=30,
            height=30,
            command=lambda e_id=entry_id, curr=is_favorite: self.toggle_favorite(e_id, not curr)
        )
        fav_button_details.place(relx=0.95, rely=0.05, anchor="ne")

        content_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        content_frame.place(relwidth=1, relheight=1)
        content_frame.grid_rowconfigure(0, weight=0)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_rowconfigure(2, weight=0)
        content_frame.grid_columnconfigure(0, weight=1)

        # Logo or abbreviation
        if logo_blob:
            try:
                target_size = (80, 80)
                img = process_logo_image(logo_blob, target_size, corner_radius=20)
                self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=target_size)
                logo_label = ctk.CTkLabel(content_frame, image=self.logo_img, text="")
                logo_label.grid(row=0, column=0, columnspan=3, pady=(15, 10))
            except Exception as e:
                print("Error processing logo:", e)
                self._display_abbreviated_logo(content_frame, account_name, (80, 80), row=0)
        else:
            self._display_abbreviated_logo(content_frame, account_name, (80, 80), row=0)

        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        info_frame.grid_columnconfigure(0, weight=0)
        info_frame.grid_columnconfigure(1, weight=1)

        fl = ctk.CTkLabel(info_frame, text="Account Name:", font=("Helvetica", 16), width=140,
                          fg_color="transparent", text_color="white", anchor="e")
        fl.grid(row=0, column=0, sticky="e", padx=(0, 10), pady=3)
        vl = ctk.CTkLabel(info_frame, text=account_name, font=("Helvetica", 16),
                          fg_color="transparent", text_color="#d1d1d1", anchor="w")
        vl.grid(row=0, column=1, sticky="w", pady=3)

        fl = ctk.CTkLabel(info_frame, text="Website URL:", font=("Helvetica", 16), width=140,
                          fg_color="transparent", text_color="white", anchor="e")
        fl.grid(row=1, column=0, sticky="e", padx=(0, 10), pady=3)
        website_text = website_url if website_url else "N/A"
        vl = ctk.CTkLabel(info_frame, text=website_text, font=("Helvetica", 16, "underline"),
                          fg_color="transparent", text_color="#3399ff", anchor="w", cursor="hand2")
        vl.grid(row=1, column=1, sticky="w", pady=3)
        if website_url:
            vl.bind("<Button-1>", lambda e, url=website_url: self.open_website(url))

        fl = ctk.CTkLabel(info_frame, text="Email:", font=("Helvetica", 16), width=140,
                          fg_color="transparent", text_color="white", anchor="e")
        fl.grid(row=2, column=0, sticky="e", padx=(0, 10), pady=3)
        vl = ctk.CTkLabel(info_frame, text=associated_email, font=("Helvetica", 16),
                          fg_color="transparent", text_color="#d1d1d1", anchor="w")
        vl.grid(row=2, column=1, sticky="w", pady=3)

        fl = ctk.CTkLabel(info_frame, text="Username:", font=("Helvetica", 16), width=140,
                          fg_color="transparent", text_color="white", anchor="e")
        fl.grid(row=3, column=0, sticky="e", padx=(0, 10), pady=3)
        self.username_entry_view = ctk.CTkEntry(
            info_frame, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10
        )
        self.username_entry_view.insert(0, username if username else "")
        self.username_entry_view.configure(state="readonly")
        self.username_entry_view.update_idletasks()
        self.username_entry_view.grid(row=3, column=1, sticky="w", pady=3)

        copy_username_button = ctk.CTkButton(
            info_frame, text="Copy", border_color="#697499", fg_color="#1e254b",
            border_width=2, width=50, command=self.copy_username
        )
        copy_username_button.grid(row=3, column=2, sticky="w", padx=(10, 0), pady=3)

        fl = ctk.CTkLabel(info_frame, text="Password:", font=("Helvetica", 16), width=140,
                          fg_color="transparent", text_color="white", anchor="e")
        fl.grid(row=4, column=0, sticky="e", padx=(0, 10), pady=3)
        self.password_entry_view = ctk.CTkEntry(
            info_frame, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10, show="*"
        )
        self.password_entry_view.insert(0, account_password)
        self.password_entry_view.configure(state="readonly")
        self.password_entry_view.update_idletasks()
        self.password_entry_view.grid(row=4, column=1, sticky="w", pady=3)

        password_buttons_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        password_buttons_frame.grid(row=4, column=2, sticky="w", padx=(10, 0), pady=3)

        self.password_toggle_button = ctk.CTkButton(
            password_buttons_frame, text="Show", border_color="#697499", fg_color="#1e254b",
            border_width=2, width=50, command=self.toggle_password_visibility
        )
        self.password_toggle_button.pack(side="left", padx=(0, 5))

        copy_password_button = ctk.CTkButton(
            password_buttons_frame, text="Copy", border_color="#697499", fg_color="#1e254b",
            border_width=2, width=50, command=self.copy_password
        )
        copy_password_button.pack(side="left")

        fl = ctk.CTkLabel(info_frame, text="Last Updated:", font=("Helvetica", 16), width=140,
                          fg_color="transparent", text_color="white", anchor="e")
        fl.grid(row=5, column=0, sticky="e", padx=(0, 10), pady=3)
        try:
            dt = datetime.datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
            formatted_date = dt.strftime("%m-%d-%Y")
        except Exception:
            formatted_date = created_at
        vl = ctk.CTkLabel(
            info_frame, text=formatted_date, font=("Helvetica", 16),
            fg_color="transparent", text_color="#d1d1d1", anchor="w"
        )
        vl.grid(row=5, column=1, sticky="w", pady=3)

        # Buttons (Edit / Delete)
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, columnspan=3, pady=(10, 15))
        buttons_frame.grid_columnconfigure((0, 1), weight=1)

        edit_button = ctk.CTkButton(
            buttons_frame, text="Edit", border_color="#697499", fg_color="#1e254b",
            border_width=2, height=40, corner_radius=20, width=100,
            command=lambda: self.display_account_details_edit(account)
        )
        edit_button.grid(row=0, column=0, padx=10)

        delete_button = ctk.CTkButton(
            buttons_frame, text="Delete", border_color="#697499", fg_color="#b22222",
            border_width=2, height=40, corner_radius=20, width=100,
            command=lambda: self.delete_account(account)
        )
        delete_button.grid(row=0, column=1, padx=10)

    def _display_abbreviated_logo(self, parent, account_name, size=(80, 80), row=0):
        abbreviation = account_name[:2].upper()
        logo_container = ctk.CTkFrame(parent, fg_color="transparent")
        logo_container.grid(row=row, column=0, columnspan=3, pady=(15, 10))
        logo_frame = ctk.CTkFrame(
            logo_container,
            width=size[0],
            height=size[1],
            corner_radius=size[0] // 2,
            fg_color="#1f1f1f"
        )
        logo_frame.grid(row=0, column=0)
        abbrev_label = ctk.CTkLabel(
            logo_frame,
            text=abbreviation,
            font=("Helvetica", size[0] // 5, "bold"),
            fg_color="transparent",
            text_color="white"
        )
        abbrev_label.place(relx=0.5, rely=0.5, anchor="center")

    def display_account_details_edit(self, account):
        (entry_id, account_name, website_url, associated_email,
         account_password, created_at, username, logo_blob,
         keyring_service, keyring_username, is_favorite) = account

        self.current_account_id = entry_id
        self.current_logo_blob = logo_blob

        for widget in self.regular_frame.winfo_children():
            widget.destroy()

        details_frame = ctk.CTkFrame(
            self.regular_frame, width=560, height=430, corner_radius=20, fg_color="#2b3564"
        )
        details_frame.place(x=10, y=10)
        details_frame.grid_propagate(False)

        fav_button_details = ctk.CTkButton(
            details_frame,
            text="",
            image=self.fav_on_img if is_favorite else self.fav_off_img,
            fg_color="transparent",
            hover_color="#2b3564",
            width=30,
            height=30,
            command=lambda e_id=entry_id, curr=is_favorite: self.toggle_favorite(e_id, not curr)
        )
        fav_button_details.place(relx=0.95, rely=0.05, anchor="ne")

        content_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        content_frame.place(relwidth=1, relheight=1)
        content_frame.grid_rowconfigure(0, weight=0)
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        logo_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        logo_container.grid(row=0, column=0, pady=(10, 5), padx=(30, 0))
        logo_container.grid_columnconfigure(0, weight=1)

        if logo_blob:
            try:
                target_size = (60, 60)
                img = process_logo_image(logo_blob, target_size, corner_radius=20)
                self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=target_size)
                logo_label = ctk.CTkLabel(logo_container, image=self.logo_img, text="")
                logo_label.grid(row=0, column=0, padx=5)
            except Exception as e:
                print("Error processing logo in edit mode:", e)
                self._display_abbreviated_logo(logo_container, account_name, (60, 60), row=0)
        else:
            self._display_abbreviated_logo(logo_container, account_name, (60, 60), row=0)

        change_logo_button = ctk.CTkButton(
            logo_container,
            text="Change Logo",
            border_color="#697499",
            fg_color="#1e254b",
            border_width=2,
            height=30,
            width=60,
            corner_radius=20,
            command=self.change_logo
        )
        change_logo_button.grid(row=1, column=0, pady=3)

        form_frame = ctk.CTkFrame(content_frame, fg_color="#2b3564", corner_radius=20)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        form_frame.grid_columnconfigure(0, weight=0)
        form_frame.grid_columnconfigure(1, weight=1)

        field_label_font = ("Helvetica", 16)
        entry_font = ("Helvetica", 16)
        field_label_color = "white"
        label_width = 140

        self.edit_entries.clear()

        # Account Name
        fl = ctk.CTkLabel(
            form_frame, text="Account Name:", font=field_label_font, width=label_width,
            fg_color="transparent", text_color=field_label_color, anchor="e"
        )
        fl.grid(row=0, column=0, sticky="e", padx=(0, 10), pady=3)
        self.edit_entries["account_name"] = ctk.CTkEntry(
            form_frame, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10, font=entry_font
        )
        self.edit_entries["account_name"].insert(0, account_name)
        self.edit_entries["account_name"].grid(row=0, column=1, sticky="w", pady=3)

        # Website URL
        fl = ctk.CTkLabel(
            form_frame, text="Website URL:", font=field_label_font, width=label_width,
            fg_color="transparent", text_color=field_label_color, anchor="e"
        )
        fl.grid(row=1, column=0, sticky="e", padx=(0, 10), pady=3)
        self.edit_entries["website_url"] = ctk.CTkEntry(
            form_frame, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10, font=entry_font
        )
        self.edit_entries["website_url"].insert(0, website_url if website_url else "")
        self.edit_entries["website_url"].grid(row=1, column=1, sticky="w", pady=3)

        # Email
        fl = ctk.CTkLabel(
            form_frame, text="Email:", font=field_label_font, width=label_width,
            fg_color="transparent", text_color=field_label_color, anchor="e"
        )
        fl.grid(row=2, column=0, sticky="e", padx=(0, 10), pady=3)
        self.edit_entries["email"] = ctk.CTkEntry(
            form_frame, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10, font=entry_font
        )
        self.edit_entries["email"].insert(0, associated_email)
        self.edit_entries["email"].grid(row=2, column=1, sticky="w", pady=3)

        # Username
        fl = ctk.CTkLabel(
            form_frame, text="Username:", font=field_label_font, width=label_width,
            fg_color="transparent", text_color=field_label_color, anchor="e"
        )
        fl.grid(row=3, column=0, sticky="e", padx=(0, 10), pady=3)
        self.edit_entries["username"] = ctk.CTkEntry(
            form_frame, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10, font=entry_font
        )
        self.edit_entries["username"].insert(0, username if username else "")
        self.edit_entries["username"].grid(row=3, column=1, sticky="w", pady=3)

        # Password
        fl = ctk.CTkLabel(
            form_frame, text="Password:", font=field_label_font, width=label_width,
            fg_color="transparent", text_color=field_label_color, anchor="e"
        )
        fl.grid(row=4, column=0, sticky="e", padx=(0, 10), pady=3)
        password_container = ctk.CTkFrame(form_frame, fg_color="transparent")
        password_container.grid(row=4, column=1, sticky="w", pady=3)

        self.edit_entries["password"] = ctk.CTkEntry(
            password_container, width=300, height=30, border_color="#1e254b", fg_color="#3e4a89",
            border_width=2, corner_radius=10, font=entry_font, show="*"
        )
        self.edit_entries["password"].insert(0, account_password)
        self.edit_entries["password"].grid(row=0, column=0, sticky="w")

        self.edit_password_toggle_button = ctk.CTkButton(
            password_container, text="Show", border_color="#697499", fg_color="#1e254b",
            border_width=2, width=50, command=self.toggle_edit_password_visibility
        )
        self.edit_password_toggle_button.grid(row=0, column=1, padx=(10, 0))

        self.edit_password_visible = False

        fl = ctk.CTkLabel(
            form_frame, text="Last Updated:", font=field_label_font, width=label_width,
            fg_color="transparent", text_color=field_label_color, anchor="e"
        )
        fl.grid(row=5, column=0, sticky="e", padx=(0, 10), pady=3)
        current_date = datetime.datetime.now().strftime("%m-%d-%Y")
        vl = ctk.CTkLabel(
            form_frame, text=current_date, font=field_label_font,
            fg_color="transparent", text_color="#d1d1d1", anchor="w"
        )
        vl.grid(row=5, column=1, sticky="w", pady=3)

        # Save/Cancel
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.grid(row=6, column=1, pady=(10, 15), sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=0)
        buttons_frame.grid_columnconfigure(1, weight=0)

        save_button = ctk.CTkButton(
            buttons_frame,
            text="Save Changes",
            border_color="#697499",
            fg_color="#1e254b",
            border_width=2,
            height=40,
            corner_radius=20,
            command=self.update_account
        )
        save_button.grid(row=0, column=0)

        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            border_color="#697499",
            fg_color="#1e254b",
            border_width=2,
            height=40,
            corner_radius=20,
            command=lambda: self.display_account_details_view(account)
        )
        cancel_button.grid(row=0, column=1, padx=(20, 0))

    def toggle_edit_password_visibility(self):
        if self.edit_password_visible:
            self.edit_entries["password"].configure(show="*")
            self.edit_password_toggle_button.configure(text="Show")
            self.edit_password_visible = False
        else:
            self.edit_entries["password"].configure(show="")
            self.edit_password_toggle_button.configure(text="Hide")
            self.edit_password_visible = True

    def change_logo(self):
        file_path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[
                ("PNG", "*.png"), ("JPEG", "*.jpg"), ("JPEG", "*.jpeg"),
                ("GIF", "*.gif"), ("BMP", "*.bmp"), ("WebP", "*.webp"), ("TIFF", "*.tiff")
            ]
        )
        print("File dialog returned:", file_path)
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    self.current_logo_blob = f.read()
                print("Logo blob length:", len(self.current_logo_blob))

                target_size = (100, 100)
                img = process_logo_image(self.current_logo_blob, target_size, corner_radius=20)
                self.logo_img = ctk.CTkImage(light_image=img, dark_image=img, size=target_size)

                # Update the existing label with new image preview
                for widget in self.regular_frame.winfo_children():
                    if isinstance(widget, ctk.CTkLabel) and hasattr(widget, "image"):
                        widget.configure(image=self.logo_img, text="")
                        widget.image = self.logo_img
                        print("Logo updated successfully.")
                        break
            except Exception as e:
                print("Error updating logo preview:", e)

    def update_account(self):
        updated_account_name = self.edit_entries["account_name"].get()
        updated_website_url = self.edit_entries["website_url"].get()
        updated_email = self.edit_entries["email"].get()
        updated_username = self.edit_entries["username"].get()
        updated_password = self.edit_entries["password"].get()
        updated_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = self.conn.cursor()
        # Fetch old keyring references
        cursor.execute(
            "SELECT keyring_service, keyring_username FROM saved_accounts WHERE entry_id = ?",
            (self.current_account_id,)
        )
        old_keyring_data = cursor.fetchone()
        old_service = old_keyring_data["keyring_service"] if old_keyring_data else None
        old_username = old_keyring_data["keyring_username"] if old_keyring_data else None

        # Delete old password from keyring
        if old_service and old_username:
            try:
                keyring.delete_password(old_service, old_username)
            except keyring.errors.PasswordDeleteError as e:
                print(f"Error deleting old password: {e}")

        # Generate new keyring references
        keyring_service = f"PasswordManager-{updated_account_name}"
        keyring_username = updated_username if updated_username else updated_email

        # Save new password
        keyring.set_password(keyring_service, keyring_username, updated_password)

        # Update DB
        cursor.execute(
            """
            UPDATE saved_accounts
            SET account_name = ?,
                website_url = ?,
                associated_email = ?,
                keyring_service = ?,
                keyring_username = ?,
                username = ?,
                created_at = ?,
                logo = ?
            WHERE entry_id = ?
            """,
            (
                updated_account_name,
                updated_website_url,
                updated_email,
                keyring_service,
                keyring_username,
                updated_username,
                updated_datetime,
                sqlite3.Binary(self.current_logo_blob) if self.current_logo_blob else None,
                self.current_account_id
            )
        )
        self.conn.commit()

        # Refresh UI
        self.populate_saved_accounts()

        # Build updated tuple
        cursor.execute("""
            SELECT favorite FROM saved_accounts WHERE entry_id = ?
        """, (self.current_account_id,))
        fav_row = cursor.fetchone()
        is_fav = bool(fav_row["favorite"]) if fav_row else False

        new_password = keyring.get_password(keyring_service, keyring_username) or ""
        updated_account = (
            self.current_account_id,
            updated_account_name,
            updated_website_url,
            updated_email,
            new_password,
            updated_datetime,
            updated_username,
            self.current_logo_blob,
            keyring_service,
            keyring_username,
            is_fav
        )
        self.display_account_details_view(updated_account)

    def delete_account(self, account):
        confirm = messagebox.askyesno("Delete Account", "Are you sure you want to delete this account?")
        if confirm:
            (entry_id, account_name, website_url, associated_email,
             account_password, created_at, username, logo_blob,
             keyring_service, keyring_username, is_favorite) = account

            try:
                if keyring_service and keyring_username:
                    try:
                        keyring.delete_password(keyring_service, keyring_username)
                    except keyring.errors.PasswordDeleteError as e:
                        print(f"Error deleting keyring entry: {e}")

                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM saved_accounts WHERE entry_id = ?", (entry_id,))
                self.conn.commit()

            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while deleting the account:\n{e}")

            self.populate_saved_accounts()

            # Clear right panel
            for widget in self.regular_frame.winfo_children():
                widget.destroy()

            self.default_label = ctk.CTkLabel(
                self.regular_frame,
                text="Select an account to view details",
                font=("Helvetica", 18),
                fg_color="transparent",
                text_color="white"
            )
            self.default_label.place(relx=0.5, rely=0.5, anchor="center")
            self.after(0, lambda: messagebox.showinfo("Account Deleted", "The account was successfully deleted."))

    def copy_username(self):
        username = self.username_entry_view.get()
        top = self.winfo_toplevel()
        top.clipboard_clear()
        top.clipboard_append(username)

    def copy_password(self):
        password = self.password_entry_view.get()
        top = self.winfo_toplevel()
        top.clipboard_clear()
        top.clipboard_append(password)

    def toggle_password_visibility(self):
        if self.password_visible:
            self.password_entry_view.configure(show="*")
            self.password_toggle_button.configure(text="Show")
            self.password_visible = False
        else:
            self.password_entry_view.configure(show="")
            self.password_toggle_button.configure(text="Hide")
            self.password_visible = True
