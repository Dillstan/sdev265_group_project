import customtkinter as ctk

class infoPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color='#212c56')

        # Separator line
        separator_line = ctk.CTkFrame(self, height=500, width=2, fg_color="#151c36")
        separator_line.place(x=640, y=0)

        # Left side Information frame
        text_frame = ctk.CTkFrame(
            self,
            height=410,
            width=565,
            corner_radius=20,
            fg_color="#2b3564"
        )
        text_frame.place(x=25, y=20)

        info_text = (
            "Welcome to Password Manager, a secure solution designed to help you manage your sensitive account "
            "information with confidence. Our application leverages the Python Keyring library to ensure that your "
            "account details are stored safely and encrypted, guarding against unauthorized access. Additionally, "
            "your login credentials are protected through one-way hashing, meaning that your password is converted "
            "into an irreversible format, which enhances the overall security of your data.\n\n"
            "Keyring Integration:\n"
            "• On macOS, the application attempts to use the macOS Keychain to securely store your credentials. "
            "This native keychain provides robust encryption and secure access management, ensuring that your data "
            "remains protected by the system's own security mechanisms.\n\n"
            "• On Windows, the application utilizes the Windows Credential Vault to manage your sensitive information. "
            "The Credential Vault is designed to store credentials securely, integrating seamlessly with the Windows "
            "security infrastructure.\n\n"
            "• On Linux, Password Manager typically leverages the Secret Service API through backends like GNOME Keyring "
            "or KWallet. These services offer secure storage for your credentials by integrating with the desktop environment's "
            "security features. In the absence of such services, the application may fall back to an insecure plaintext keyring, "
            "so ensuring that you have a secure keyring service installed is highly recommended.\n\n"
            "Developed as a collaborative group project, Password Manager is dedicated to providing a robust and "
            "user-friendly platform where your privacy and digital security are our top priorities."
        )

        label = ctk.CTkLabel(
            text_frame,
            text=info_text,
            wraplength=550,
            justify="left",
            text_color="white"
        )
        label.pack(padx=20, pady=20)

        # Right side Key Features frame
        features_frame = ctk.CTkFrame(
            self,
            height=410,
            width=285,
            corner_radius=20,
            fg_color="#2b3564"
        )
        features_frame.place(x=660, y=20)

        # Title for the features section
        features_title = ctk.CTkLabel(
            features_frame,
            text="Key Features",
            font=("Arial", 20, "bold"),
            text_color="white"
        )
        features_title.pack(pady=(20, 10))

        # List of features
        features = [
            "• Secure Storage via \nKeyring Integration",
            "• Encryption & \nOne-Way Hashing",
            "• Cross-Platform Compatibility",
            "• User-Friendly Interface"
        ]

        for feature in features:
            feature_label = ctk.CTkLabel(
                features_frame,
                text=feature,
                text_color="white",
                anchor="w"
            )
            feature_label.pack(padx=20, pady=5, fill="x")
