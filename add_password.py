import customtkinter as ctk
from PIL import Image, ImageTk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
import subprocess
from tkinter import messagebox
import sqlite3
import os
import keyring  #keyring library

class AddDialogue(ctk.CTk):
    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        # Create the main window
        #self.top = add_password.top = tk.Toplevel(parent)
        self.title("Add Account | Password Manager")
        self.geometry("300x310")
        self.iconbitmap(r"appicon.ico")
        self.resizable(False, False)
        self.eval("tk::PlaceWindow . center")
        self.configure(fg_color="#212c56")

        account_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text="Account Name",
                                     placeholder_text_color="white",height=40,corner_radius=10,border_width=2,
                                     border_color="#1e254b", fg_color="#697499")
        account_entry.place(x=50, y=20)

        website_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Website URL',
                                     placeholder_text_color='white',height=40,corner_radius=10,border_width=2,
                                     border_color="#1e254b", fg_color="#697499")
        website_entry.place(x=50, y=65)

        email_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Email',
                                   placeholder_text_color='white',height=40,corner_radius=10,border_width=2,
                                   border_color="#1e254b", fg_color="#697499")
        email_entry.place(x=50, y=110)

        username_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Username',
                                      placeholder_text_color='white',height=40,corner_radius=10,border_width=2,
                                      border_color="#1e254b", fg_color="#697499")
        username_entry.place(x=50, y=155)

        password_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Password',
                                      placeholder_text_color='white',height=40,corner_radius=10,border_width=2,
                                      border_color="#1e254b", fg_color="#697499")
        password_entry.place(x=50, y=200)

        # CREATES AND PLACES THE SAVE BUTTON
        login_button = ctk.CTkButton(
            self, text="Save Account", width=200,
            font=("Arial", 20), height=40,border_color= "#697499",fg_color="#1e254b",border_width=2, corner_radius=20,
            command=lambda: create_password()
        )
        login_button.place(x=50, y=250)


        def create_password():
            account = account_entry.get()
            website = website_entry.get()
            email = email_entry.get()
            username = username_entry.get()
            password = password_entry.get()

            if not password:
                messagebox.showerror("Error", "Please enter a password!")
                return

            try:
                conn = sqlite3.connect('appdata.db')
                mycursor = conn.cursor()
                print("Connection established")

            except sqlite3.Error as e:
                messagebox.showerror("Connection Error", f"Database connection failed: {str(e)}")
                return

            try:
                command = ("""
                    CREATE TABLE IF NOT EXISTS saved_accounts (
                        entry_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id          INTEGER NOT NULL
                            REFERENCES users (user_id)
                                ON DELETE CASCADE,
                        account_name     TEXT NOT NULL,
                        website_url      TEXT,
                        associated_email TEXT NOT NULL,
                        keyring_service  TEXT,
                        keyring_username TEXT,
                        created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                        username         VARCHAR(50),
                        logo             BLOB,
                        favorite        Boolean DEFAULT FALSE
                    );

                    CREATE INDEX IF NOT EXISTS idx_user_accounts
                        ON saved_accounts (user_id);
                """)

                mycursor.executescript(command)

            except sqlite3.Error as e:

                messagebox.showerror("Database Error", f"Error creating table: {str(e)}")
                conn.close()
                return

            try:

                command = "SELECT * FROM users WHERE logged_in = 1"

                mycursor.execute(command)
                result = mycursor.fetchone()

                if not result:
                    messagebox.showerror("Error", "No logged-in user found.")
                    conn.close()
                    return

                keyring_service = f"PasswordManager-{account}"
                keyring_username = username if username else email

                keyring.set_password(keyring_service, keyring_username, password)

                command = """
                    INSERT INTO saved_accounts (
                        user_id, account_name, website_url, 
                        associated_email, keyring_service, keyring_username, username
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """

                mycursor.execute(command, (
                    result[0],
                    account,
                    website,
                    email,
                    keyring_service,
                    keyring_username,
                    username
                ))

                conn.commit()
                conn.close()

                messagebox.showinfo("Password Creation", "New account has been stored successfully!")
                self.grab_release()
                self.destroy()

            except sqlite3.Error as e:
                conn.close()
                messagebox.showerror("Database Error", str(e))
