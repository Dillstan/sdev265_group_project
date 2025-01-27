import customtkinter as ctk
from PIL import Image, ImageTk
from CTkMessagebox import CTkMessagebox

# ATT KOBE:
## RANDOM PASSWORD GEN - STRING OF NUMBERS AND LETTERS "STRONG" PASSWORD"

# DESCRIPTION FOR PASSWORD

#







##
class Main(ctk.CTk):
    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        self.wm_title('Main | Password Manager')
        self.geometry('1000x600')
        self._set_appearance_mode('dark')
        self.resizable(False, False)
        self.wm_iconbitmap('appicon.ico')
        self.eval("tk::PlaceWindow . center")

        # CREATES AND PLACES FRAME FOR PAGES ON THE RIGHT SIDE
        container = ctk.CTkFrame(self, height=580, width=740, fg_color="red")
        container.place(x=250, y=10)

        self.frames = {}

        for F in (HomePage, StoredPasswordsPage, SettingsPage, AIPage):
            frame = F(container, self)
            frame.configure(height=580, width=740)

            self.frames[F] = frame
            frame.place(x=0, y=0)

        self.show_frames(HomePage)

    def show_frames(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color="red")

        button = ctk.CTkButton(self, text='Home Page | Click For Stored Passwords', command=lambda: controller.show_frames(StoredPasswordsPage))
        button.place(x=50, y=100)

class StoredPasswordsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color="blue")

        button = ctk.CTkButton(self, text='Stored Passwords | Click For Settings', command=lambda: controller.show_frames(SettingsPage))
        button.place(x=50, y=100)

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color="black")
        button = ctk.CTkButton(self, text='Settings | Click to to AI Page', command=lambda: controller.show_frames(AIPage))
        button.place(x=50, y=100)

class AIPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color="green")
        button = ctk.CTkButton(self, text="AI Page | Click to go back to home page", command=lambda: controller.show_frames(HomePage))



if __name__ == '__main__':
    app = Main()
    app.mainloop()