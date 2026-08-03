import customtkinter as ctk

class YesNoDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, left, center, right):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x150")

        # Center the pop-up relative to parent window
        self.lift()
        self.attributes("-topmost", True)
        self.grab_set() # Prevent clicking main window while open

        self.result = None

        # Message Label
        self.label = ctk.CTkLabel(self, text=message, wraplength=250)
        self.label.pack(pady=20, padx=20)

        # Button Container
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        # Action Buttons
        self.left_btn = ctk.CTkButton(self.btn_frame, text=f"{left}", width=90, command=self.on_left)
        self.left_btn.pack(side="left", padx=10, pady=20, expand=True, fill="both")

        self.center_btn = ctk.CTkButton(self.btn_frame, text=f"{center}", width=90, command=self.on_center)
        self.center_btn.pack(side="left", padx=10, pady=20, expand=True, fill="both")

        self.right_btn = ctk.CTkButton(self.btn_frame, text=f"{right}", width=90, command=self.on_right)
        self.right_btn.pack(side="left", padx=10, pady=20, expand=True, fill="both")

    def on_left(self):
        self.result = 'left'
        self.destroy()

    def on_center(self):
        self.result = 'center'
        self.destroy()

    def on_right(self):
        self.result = 'right'
        self.destroy()
