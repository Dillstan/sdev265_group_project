import customtkinter as ctk
from PIL import Image, ImageTk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
import subprocess
from tkinter import messagebox
import argon2
import sqlite3
import os


class AddDialogue(ctk.CTk):
    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        # Create the main window
        #self.top = add_password.top = tk.Toplevel(parent)
        self.title("Add Password | Password Manager")
        self.geometry("400x240")
        self.iconbitmap(r"appicon.ico")
        self.resizable(False, False)
        self.eval("tk::PlaceWindow . center")
        self.configure(fg_color="#212c56")

        account_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text="Account Name", placeholder_text_color="white")
        account_entry.place(x=100, y=20)

        website_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Website URL', placeholder_text_color='white')
        website_entry.place(x=100, y=55)

        email_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Email', placeholder_text_color='white')
        email_entry.place(x=100, y=90)

        username_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Username', placeholder_text_color='white')
        username_entry.place(x=100, y=125)

        password_entry = ctk.CTkEntry(self, font=("Arial", 15, "bold"), width=200, placeholder_text='Password', placeholder_text_color='white')
        password_entry.place(x=100, y=160)

        # CREATES AND PLACES THE SAVE BUTTON
        login_button = ctk.CTkButton(self, text="Save Password", width=200,
                                     font=("Arial", 20), fg_color="#4287f5", hover_color="#0a64f5",
                                     command=lambda: create_password())
        login_button.place(x=100, y=195)


        def create_password():
            account = account_entry.get()
            website = website_entry.get()
            email = email_entry.get()
            username = username_entry.get()
            password = password_entry.get()

            if (password == "" or password == "Password"):
                messagebox.showerror("Error", "Please enter a password!")
                return

            try:
                conn = sqlite3.connect('appdata.db')
                mycursor = conn.cursor()
                print("Connection established")

            except:
                messagebox.showerror("Connection Error", "Connection not established")
                return

            try:
                command = ("""
                    create table main.saved_accounts (
                        entry_id         INTEGER
                            primary key autoincrement,
                        user_id          INTEGER not null
                            references main.users_old (user_id)
                                on delete cascade,
                        account_name     TEXT    not null,
                        website_url      TEXT,
                        associated_email TEXT    not null,
                        account_password TEXT    not null,
                        created_at       DATETIME default CURRENT_TIMESTAMP,
                        username         varchar(50),
                        logo             BLOB);
                    
                create index main.idx_user_accounts
                    on main.saved_accounts (user_id);
                            """)

                mycursor.execute(command)

            except:
                command = "select * from users where logged_in = 1"

                mycursor.execute(command)
                result = mycursor.fetchone()

                command = "insert into saved_accounts (user_id, account_name, website_url, associated_email, account_password, username) values (?, ?, ?, ?, ?, ?)"

                # user_id, account_name, website_url, associated_email, account_password, username

                mycursor.execute(command, (result[0], account, website, email, password, username))
                conn.commit()
                conn.close()
                messagebox.showinfo("Password Creation", "New password has been created successfully!")
                self.grab_release()
                self.destroy()
