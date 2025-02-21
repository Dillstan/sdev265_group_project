import sys
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from subprocess import call
import sqlite3
from CTkToolTip import CTkToolTip
from add_password import AddDialogue
from database import create_database
import keyring

if sys.platform == "darwin":
    try:
        from keyring.backends.macOS import Keychain
        keyring.set_keyring(Keychain())
        print("Using macOS Keychain backend.")
    except Exception as e:
        print("Could not set macOS Keychain backend:", e)
elif sys.platform.startswith("win"):
    try:
        from keyring.backends.Windows import WinVaultKeyring
        keyring.set_keyring(WinVaultKeyring())
        print("Using Windows Credential Manager backend.")
    except Exception as e:
        print("Could not set Windows Credential Manager backend:", e)
elif sys.platform.startswith("linux"):
    try:
        from keyring.backends.SecretService import Keyring as SecretServiceKeyring
        keyring.set_keyring(SecretServiceKeyring())
        print("Using Secret Service backend for Linux.")
    except Exception as e:
        print("Could not set Secret Service backend:", e)

# Fallback in case none of the above worked
try:
    from keyrings.alt.file import PlaintextKeyring
    keyring.set_keyring(PlaintextKeyring())
    print("Using PlaintextKeyring as fallback.")
except Exception as e:
    print("Failed to set fallback keyring:", e)

def sign_out():
    users = sqlite3.connect('appdata.db')
    mycursor = users.cursor()

    command = "update users set logged_in = 0 where logged_in = ?"
    mycursor.execute(command, (1,))
    users.commit()
    users.close()

    messagebox.showinfo("Sign Out", "Signing out...", parent=app)

    app.after(100, lambda: (app.destroy(), call(['python', 'login.py'])))

def cursor_on_hover(button):
    button.configure(cursor='hand2')

def reset_cursor_on_leave(button):
    button.configure(cursor='none')

# Fetch Current user_id from users table from appdata.db
def fetch_current_user(database):
    try:

        users = sqlite3.connect(database)
        mycursor = users.cursor()

        command = "select * from users where logged_in = 1"
        mycursor.execute(command)

        result = mycursor.fetchone()
        # result[0] = current user id
        logged_in_user = result[0]

        return logged_in_user

    except:
        logged_in_user = "current_user"

        return logged_in_user

# Fetch current username at index 1 from appdata.dk -> saved_accounts
def fetch_current_username(database):
    try:
        connection = sqlite3.connect(database)
        mycursor = connection.cursor()
        command = "SELECT username FROM users WHERE logged_in = 1"
        mycursor.execute(command)
        result = mycursor.fetchone()
        connection.close()

        if result is not None:
            return result[0]  # The username
        else:
            return "User"
    except Exception as e:
        print("Error fetching current username:", e)
        return "User"

def exit_button(window):
    users = sqlite3.connect("appdata.db")
    mycursor = users.cursor()

    command = "update users set logged_in = 0 where logged_in = 1"
    mycursor.execute(command)
    users.commit()
    users.close()

    window.destroy()

def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

class Main(ctk.CTk):

    def show_frames(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        self.wm_title('Password Manager')
        self.geometry('1000x600')
        self._set_appearance_mode('dark')
        self.resizable(False, False)
        self.wm_iconbitmap('appicon.ico')
        self.eval("tk::PlaceWindow . center")
        self.protocol("WM_DELETE_WINDOW", lambda: exit_button(self))
        self.configure(fg_color='#212c56')

        # Set the current_user_id on this controller
        self.current_user_id = fetch_current_user('appdata.db')
        print(f"Main: current_user_id = {self.current_user_id}")  # Debug print

        # CREATES AND PLACES FRAME FOR PAGES ON THE RIGHT SIDE
        container = ctk.CTkFrame(self, height=500, width=900, fg_color="#212c56")
        container.place(x=100, y=100)

        self.frames = {}

        for F in (StoredPasswordsPage,FavoritesPage,infoPage,GeneratePasswordPage, SettingsPage):
            frame = F(container, self)
            frame.configure(height=500, width=900)

            self.frames[F] = frame
            frame.place(x=0, y=0)

        # Initial startup page
        self.show_frames(FavoritesPage)

        # ----------------- TOOLBAR BASE ----------------------- #
        toolbar_top = ctk.CTkFrame(self, height=60, width=60, fg_color='#151c36')
        toolbar_top.place(x=15, y=60)

        toolbar_middle = ctk.CTkFrame(self, height=300, width=60, fg_color='#151c36')
        toolbar_middle.place(x=15, y=140)

        toolbar_bottom = ctk.CTkFrame(self, height=60, width=60, fg_color='#151c36')
        toolbar_bottom.place(x=15, y=460)

        separator_line = ctk.CTkFrame(self, height=600, width=2, fg_color="#151c36")
        separator_line.place(x=90, y=0)

        tool_button_divider_info = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        tool_button_divider_info.place(x=15, y=200)

        tool_button_divider_favorites = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        tool_button_divider_favorites.place(x=15, y=260)

        tool_button_divider_stored_passwords = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        tool_button_divider_stored_passwords.place(x=15, y=320)

        tool_button_divider_generate_passwords = ctk.CTkFrame(self, height=2, width=60, fg_color='#333a55')
        tool_button_divider_generate_passwords.place(x=15, y=380)

        # ----------------- TOOLBAR ICONS ----------------------- #
        info_icon = ctk.CTkImage(Image.open('toolbar_icons/info_icon.png'))
        info_icon._size = 40, 40

        favorite_icon = ctk.CTkImage(Image.open('toolbar_icons/star_icon.png'))
        favorite_icon._size = 40, 40

        stored_password_icon = ctk.CTkImage(Image.open('toolbar_icons/stored_passwords_icon.png'))
        stored_password_icon._size = 40, 40

        generate_password_icon = ctk.CTkImage(Image.open('toolbar_icons/generate_icon.png'))
        generate_password_icon._size = 40, 40

        user_icon = ctk.CTkImage(Image.open('toolbar_icons/settings.png'))
        user_icon._size = 40, 40

        add_icon = ctk.CTkImage(Image.open('toolbar_icons/add_icon.png'))
        add_icon._size = 40, 40

        toolbar_logo = ctk.CTkImage(Image.open('resources/main_menu_logo.png'))
        toolbar_logo._size = 50, 50

        # ----------------- TOOLBAR IMAGE HOLDERS & BUTTONS ----------------------- #
        favorite_icon_button = ctk.CTkButton(toolbar_middle, height=60, width=60, image=favorite_icon,
                                             fg_color='transparent', text='', hover=False,
                                             command=lambda: self.show_frames(FavoritesPage))
        favorite_icon_button.place(x=0, y=3)

        stored_passwords_icon_button = ctk.CTkButton(toolbar_middle, height=60, width=60, image=stored_password_icon,
                                                     fg_color='transparent', text='', hover=False,
                                                     command=lambda: self.show_frames(StoredPasswordsPage))
        stored_passwords_icon_button.place(x=0, y=63)

        generate_password_icon_button = ctk.CTkButton(toolbar_middle, height=60, width=60, image=generate_password_icon,
                                                      fg_color='transparent', text='', hover=False,
                                                      command=lambda: self.show_frames(GeneratePasswordPage))
        generate_password_icon_button.place(x=0, y=123)

        info_icon_button = ctk.CTkButton(toolbar_middle, height=60, width=60, image=info_icon, fg_color='transparent',
                                         text='', hover=False, command=lambda: self.show_frames(infoPage))
        info_icon_button.place(x=0, y=183)

        user_icon_button = ctk.CTkButton(toolbar_middle, height=40, width=40, image=user_icon, fg_color='transparent',
                                         text='', hover=False, command=lambda: self.show_frames(SettingsPage))
        user_icon_button.place(x=2, y=248)

        add_icon_button = ctk.CTkButton(toolbar_bottom, height=40, width=40, image=add_icon, fg_color='transparent',
                                        text='', hover=False, command=lambda: add_password())
        add_icon_button.place(x=2, y=6)

        toolbar_logo_label = ctk.CTkLabel(toolbar_top, text='', image=toolbar_logo)
        toolbar_logo_label.place(x=5, y=5)

        # ----------------- TOOLBAR MISC FUNCTIONALITY ----------------------- #
        info_icon_button.bind('<Enter>', lambda event: cursor_on_hover(info_icon_button))
        info_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(info_icon_button))

        add_icon_button.bind('<Enter>', lambda event: cursor_on_hover(add_icon_button))
        add_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(add_icon_button))

        favorite_icon_button.bind('<Enter>', lambda event: cursor_on_hover(favorite_icon_button))
        favorite_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(favorite_icon_button))

        stored_passwords_icon_button.bind('<Enter>', lambda event: cursor_on_hover(stored_passwords_icon_button))
        stored_passwords_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(stored_passwords_icon_button))

        generate_password_icon_button.bind('<Enter>', lambda event: cursor_on_hover(generate_password_icon_button))
        generate_password_icon_button.bind('<Leave>',
                                           lambda event: reset_cursor_on_leave(generate_password_icon_button))

        user_icon_button.bind('<Enter>', lambda event: cursor_on_hover(user_icon_button))
        user_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(user_icon_button))

        # ----------------- TOP BAR --------------------- #

        top_bar = ctk.CTkFrame(self, height=90, width=900, fg_color='#212c56')
        top_bar.place(x=99, y=5)

        settings_icon = ctk.CTkImage(Image.open('toolbar_icons/settings_icon.png'))
        settings_icon._size = 35, 35

        settings_icon_button = ctk.CTkButton(top_bar, image=settings_icon, fg_color='transparent', text='', hover=False,
                                             command=lambda: self.show_frames(SettingsPage))
        settings_icon_button.place(x=740, y=25)

        settings_icon_button.bind('<Enter>', lambda event: cursor_on_hover(settings_icon_button))
        settings_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(settings_icon_button))

        settings_text = ctk.CTkLabel(top_bar, text='Settings', font=('Helvetica', 10))
        settings_text.place(x=790, y=65)

        sign_out_icon = ctk.CTkImage(Image.open('toolbar_icons/sign_out_icon.png'))
        sign_out_icon._size = 33, 33

        sign_out_icon_button = ctk.CTkButton(top_bar, image=sign_out_icon, command=sign_out, fg_color='transparent',
                                             text='', hover=False, height=30, width=30)
        sign_out_icon_button.place(x=840, y=25)

        sign_out_text = ctk.CTkLabel(top_bar, text='Sign Out', font=('Helvetica', 10))
        sign_out_text.place(x=840, y=65)

        sign_out_icon_button.bind('<Enter>', lambda event: cursor_on_hover(sign_out_icon_button))
        sign_out_icon_button.bind('<Leave>', lambda event: reset_cursor_on_leave(sign_out_icon_button))

        greeting_label = ctk.CTkLabel(top_bar, text='Hello,', font=("Great Vibes", 26, "bold"), width=200)
        greeting_label.place(x=40, y=10)

        current_user = fetch_current_username('appdata.db')

        current_user_label = ctk.CTkLabel(top_bar, text=current_user, font=("Lucida Sans", 20), width=200)
        current_user_label.place_configure(x=100, y=65)

        profile_picture = ctk.CTkImage(Image.open('resources/profile_picture.png'))
        profile_picture._size = 100, 100

        profile_picture_label = ctk.CTkLabel(top_bar, text='', image=profile_picture, )
        profile_picture_label.place(x=0, y=0)

        # -------------------- TOOLTIPS ------------------- #
        info_tooltip = CTkToolTip(info_icon_button, message='Info', delay=0.1)

        favorites_tooltip = CTkToolTip(favorite_icon_button, message='Favorites', delay=0.1)

        stored_passwords_tooltip = CTkToolTip(stored_passwords_icon_button, message='Stored Accounts', delay=0.1)

        generate_password_tooltip = CTkToolTip(generate_password_icon_button, message='Generate Password', delay=0.1)

        user_tooltip = CTkToolTip(user_icon_button, message='My Account', delay=0.1)

        add_tooltip = CTkToolTip(add_icon_button, message='Add New Account', delay=0.1)

        def add_password():
            input_dialog = AddDialogue()
            input_dialog.grab_set()
            app.wait_window(input_dialog)
            StoredPasswordsPage.populate_saved_accounts(self=self.frames[StoredPasswordsPage])

from infoPage import infoPage

from password_Vault import StoredPasswordsPage

from favoritePage import FavoritesPage

from SettingsPage import SettingsPage

from pwd_gen import GeneratePasswordPage

if __name__ == '__main__':
    create_database()
    app = Main()
    app.mainloop()
