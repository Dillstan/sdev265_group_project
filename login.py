import customtkinter as ctk
from PIL import Image, ImageTk
from CTkMessagebox import CTkMessagebox
import tkinter as tk
import subprocess
from tkinter import messagebox
import argon2
import sqlite3
import os

# REMOVES "PASSWORD" IN PASSWORD ENTRY
def password_enter(e):
    password_entry.delete(0, 'end')


# INSERTS "PASSWORD" INTO ENTRY BY DEFAULT
def password_leave(e):
    if password_entry.get() == '':
        password_entry.insert(0, 'Password')


# SENDS USER TO THE ACCOUNT CREATION SCREEN
# EXITS CURRENT WINDOW AND OPENS A DIFFERENT ONE
def register():
    login.destroy()
    subprocess.call(['python', 'register.py'])


# ADDS FUNCTIONALITY TO THE "EYE BUTTON"
# IMPLEMENTS THE ABILITY TO HIDE PASSWORD WHEN BUTTON IS CLICKED
def hide():
    global button_mode
    if button_mode:
        eye_button.configure(image=closedeye, activebackground="white")
        password_entry.configure(show="*")
        button_mode = False
    else:
        eye_button.configure(image=openeye, activebackground="white")
        password_entry.configure(show="")
        button_mode = True


# ALLOWS USER TO LOGIN TO THE APP
# GETS ENTERED USERNAME AND PASSWORD AND CHECKS IF THEY MEET CRITERIA
# IF THEY MEET THE REQUIREMENTS, THE APP CONNECTS TO THE DATABASE AND SEARCHES FOR A MATCHING USERNAME AND PASSWORD
# IF A MATCHING USERNAME AND PASSWORD ARE NOT FOUND, IT WILL NOT ALLOW YOU TO LOGIN
# IF A MATCHING USERNAME AND PASSWORD ARE FOUND, THE APP WILL ALLOW USER TO SUCCESSFULLY LOGIN

# RETURNS ENCRYPTED PASSWORD FROM DATABASE AND COMPARES IT TO THE PASSWORD ENTERED (BOOL)
# IF TRUE , THE LOGIN IS SUCCESSFUL
# IF FALSE, THE USER IS PROMPTED WITH "INVALID USERNAME OR PASSWORD"


def loginuser(event):
    # GETS THE USERNAME ENTERED
    username = username_entry.get()
    # GETS THE PASSWORD ENTERED
    password = password_entry.get()
    # INPUT VALIDATION
    # CHECKS THAT THE USER ENTERED A VALID USERNAME AND PASSWORD
    # CHECKS THAT THE USERNAME AND PASSWORD ENTRY ARE NOT EMPTY
    if (username == "" or username == "Username") or (password == "" or password == "Password"):
        CTkMessagebox(title="Error", message="Enter a valid username and password!", icon='warning', sound=True)

    else:

        # TRYS TO CONNECT TO THE DATABASE
        try:
            users = sqlite3.connect('appdata.db')
            mycursor = users.cursor()
            print("Connected to database!")

        # IF CONNECTION FAILS TO ESTABLISH,
        # AN ERROR MESSAGE POPS UP
        except:
            CTkMessagebox(title="Error", message="Database connection not established!", icon='warning')
            return

        # CREATES AN INSTANCE OF ARGON2
        ph = argon2.PasswordHasher()

        # SCANS THE DATABASE AND SEARCHES FOR A USERNAME THAT MATCHES THE ONE ENTERED
        command = "select * from users where Username = ?"

        # EXECUTES THE ABOVE COMMAND
        mycursor.execute(command, (username,))

        # RETURNS ONE ROW FROM THE RESULTSET
        myresult = mycursor.fetchone()

        # CHANGES LOGGED IN TO TRUE FOR THE ENTERED USERNAME
        command = "update users set LoggedIn = 1 where Username = ?"
        mycursor.execute(command, (username,))

        users.commit()
        users.close()
        # FOR DEBUG
        # print(myresult)
        # print(f'Password : {fetched_password}')

        # IF THE SCAN DOESN'T FIND A MATCH IN THE DATABASE,
        # AN ERROR MESSAGE READING "USERNAME DOESN'T EXIST!" WILL APPEAR
        if myresult is None:

            CTkMessagebox(title="Error", message="Username doesn't exist!", icon='warning', sound=True)

        else:
            try:
                # GETS THE STORED PASSWORD FOR THE ENTERED USERNAME
                fetched_password = myresult[2]
                # USES ARGON2 VERIFY METHOD TO COMPARE THE
                # STORED HASHED PASSWORD TO THE LITERAL STRING THAT WAS ENTERED.
                ph.verify(fetched_password, password)
                # PRINTS PASSWORD VERIFIED IN THE TERMINAL
                print('Password verified!')

                # EXITS THE LOGIN PAGE
                login.destroy()
                # LOADS THE MAIN PAGE
                # subprocess.call(['python.exe', 'main.py'])
                os.system('python main.py')



            except:
                CTkMessagebox(title="Error", message="Invalid username or password!", icon='warning', sound=True)
                print('Password verification failed!')


# ADDS SHARPNESS TO UI ON HIGH-RESOLUTION SCREENS
def enable_high_dpi_awareness():
    try:

        login.tk.call('tk', 'scaling', 2.0)

    except:
        pass


def exit_button(window):

    # CONNECTS TO THE DATABASE
    users = sqlite3.connect('appdata.db')

    # CREATES A CURSOR
    mycursor = users.cursor()

    # FOR THE ENTERED USER - CHANGES VALUE OF LOGGEDIN TO TRUE
    command = "update users set LoggedIn = 0 where LoggedIn = 1"

    # EXECUTES THE ABOVE COMMAND
    mycursor.execute(command)
    users.commit()
    users.close()

    # EXITS THE WINDOW
    window.destroy()


if __name__ == '__main__':
    # IMPORTS THE LOGIN SCREEN LOGO
    main_menu_logo = ctk.CTkImage(light_image=Image.open("main_menu_logo.png"),
                                  dark_image=Image.open("main_menu_logo.png"), size=(200, 200))

    # Create the main window
    login = ctk.CTk()
    login.title("Login | Password Manager")
    login.geometry("400x500")
    login.iconbitmap(r"appicon.ico")
    login.resizable(False, False)
    login.eval("tk::PlaceWindow . center")
    login.protocol("WM_DELETE_WINDOW", lambda: exit_button(login))
    login.configure(fg_color="#212c56")

    # Enable DPI scaling
    enable_high_dpi_awareness()

    # Set dark mode
    ctk.set_appearance_mode("dark")

    # CREATES AND PLACES THE LABEL THAT HOUSES THE LOGIN SCREEN LOGO
    icon_label = ctk.CTkLabel(login, text="", height=180, width=50, image=main_menu_logo)
    icon_label.place(x=100, y=20)

    # CREATES AND PLACES THE ENTRY FOR USERS TO ENTER THEIR USERNAME
    username_entry = ctk.CTkEntry(login, placeholder_text="Username",
                                  font=("Arial", 15, "bold"), placeholder_text_color="white", width=200)
    username_entry.bind("<Key-space>", lambda e: "break")
    username_entry.place(x=100, y=255)

    # IMPORTS THE USERNAME ICON
    name_icon = ctk.CTkImage(Image.open('name_icon.png'))
    name_icon._size = 25, 25

    # CREATES AND PLACES USERNAME ICON LABEL
    name_icon_label = ctk.CTkLabel(login, image=name_icon, text='')
    name_icon_label.place(x=70, y=255)

    # CREATES AND PLACES THE ENTRY FOR USERS TO ENTER THEIR PASSWORD
    password_entry = ctk.CTkEntry(login, font=("Arial", 15, "bold"), width=200, placeholder_text='Password', show='*', placeholder_text_color='white')
    # password_entry.insert(0, 'Password')
    password_entry.bind("<FocusIn>", password_enter)
    password_entry.bind("<FocusOut>", password_leave)
    password_entry.bind("<Key-space>", lambda e: "break")
    password_entry.place(x=100, y=290)

    # ALLOWS USER TO PRESS ENTER BUTTON TO LOGIN
    login.bind("<Return>", loginuser)

    # IMPORTS THE PASSWORD ICON
    pass_icon = ctk.CTkImage(Image.open('pass_icon.png'))
    pass_icon._size = 25, 25

    # CREATES AND PLACES USERNAME ICON LABEL
    pass_icon_label = ctk.CTkLabel(login, image=pass_icon, text='')
    pass_icon_label.place(x=71, y=290)

    # IMPORTS THE OPEN EYE BUTTON TO PASSWORD ENTRY
    openeye = Image.open("eye.png")
    openeye = openeye.resize((18, 18))
    openeye = ImageTk.PhotoImage(openeye)

    # IMPORTS THE CLOSED EYE BUTTON TO PASSWORD ENTRY
    closedeye = Image.open("lock.png")
    closedeye = closedeye.resize((18, 18))
    closedeye = ImageTk.PhotoImage(closedeye)

    button_mode = False

    # CREATES AND PLACES THE OPEN/CLOSED EYE BUTTON FOR PASSWORD ENTRY
    eye_button = tk.Button(login, image=closedeye, bd=0, bg="#343434", command=hide)
    eye_button.place(x=260, y=295)

    # CREATES AND PLACES THE LOGIN BUTTON
    login_button = ctk.CTkButton(login, text="Login",
                                 font=("Arial", 20), fg_color="#4287f5", hover_color="#0a64f5",
                                 command=lambda: loginuser(None))
    login_button.place(x=129, y=380)

    # CREATES AND PLACES THE REGISTER BUTTON
    register_button = ctk.CTkButton(login, text="Register",
                                    font=("Arial", 20), fg_color="#4287f5", hover_color="#0a64f5", command=register)
    register_button.place(x=129, y=420)

    login.mainloop()
