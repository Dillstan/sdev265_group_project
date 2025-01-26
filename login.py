import customtkinter as ctk
from PIL import Image, ImageTk
from CTkMessagebox import CTkMessagebox

if __name__ == '__main__':
    login = ctk.CTk()
    login.title("Password Manager | Login")
    login.geometry("400x500")
    login.iconbitmap("appicon.ico")
    login.resizable(False, False)
    login.eval("tk::PlaceWindow . center")


    login.mainloop()