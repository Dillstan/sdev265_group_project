import customtkinter as ctk

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        ctk.CTkFrame.__init__(self, parent, fg_color='#212c56')
        button = ctk.CTkButton(self, text='Settings')
        button.place(x=50, y=100)

        # Frame
        frame = ctk.CTkFrame(self, width=840, height=450, corner_radius=20, fg_color="#2b3564")
        frame.pack(expand=True, padx=20, pady=20)
        frame.place(x=25, y=20)