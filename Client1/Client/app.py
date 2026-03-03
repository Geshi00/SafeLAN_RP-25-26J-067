import sys
import os

# This line adds "SecureLAN" to the Python search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import customtkinter as ctk
import time
from tkinter import messagebox

# Use the full path starting from the root
from logic.dna_engine import extract_14_features
from api_handler import SafeLAN_API
from logic.context_util import get_local_context

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SafeLANApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SafeLAN-Auth | Biometric Gateway")
        self.geometry("400x500")
        
        self.api = SafeLAN_API()
        self.keystrokes = []
        
        self.init_ui()

    def init_ui(self):
        self.label = ctk.CTkLabel(self, text="SafeLAN Biometric Login", font=("Roboto", 20))
        self.label.pack(pady=30)

        self.user_entry = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.user_entry.pack(pady=10)

        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250)
        self.pass_entry.pack(pady=10)
        self.pass_entry.bind("<KeyPress>", self.record_key)
        self.pass_entry.bind("<KeyRelease>", self.record_key)

        self.login_btn = ctk.CTkButton(self, text="Authenticate", command=self.handle_login)
        self.login_btn.pack(pady=20)

        self.status_label = ctk.CTkLabel(self, text="System Ready", text_color="gray")
        self.status_label.pack(pady=10)

    def record_key(self, event):
        # Capture precise timestamp and action
        action = 'p' if event.type == '2' else 'r'
        self.keystrokes.append({
            'k': event.keysym,
            't': time.time(),
            'a': action
        })

    def handle_login(self):
        username = self.user_entry.get()
        password = self.pass_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Error", "Please enter all credentials")
            return

        # 1. Feature Extraction (The 14 Dimensions)
        dna_features = extract_14_features(self.keystrokes)
        
        if not dna_features:
            messagebox.showerror("Error", "Typing pattern too short. Please type normally.")
            self.keystrokes = []
            return

        # 2. Local Model Check (Simplified score for demo)
        # In a full flow, you'd load the .pkl here. 
        # For now, we send the raw data to the server for the TI decision.
        self.status_label.configure(text="Verifying Trust Index...", text_color="yellow")
        
        # 3. Server Verification via API Handler
        # We pass a dummy svm_score of 0.05 for testing the TI logic
        try:
            result = self.api.verify_request(username, password, 0.05, dna_features)
            
            if result['status'] == "SUCCESS":
                self.status_label.configure(text=f"SUCCESS: TI {result['trust_index']}", text_color="green")
                messagebox.showinfo("Access Granted", f"Welcome {username}!\nTrust Index: {result['trust_index']}")
            elif result['status'] == "CHALLENGE":
                self.status_label.configure(text="MFA CHALLENGE REQUIRED", text_color="orange")
                messagebox.showwarning("Step-up Auth", "Biometrics marginal. Please complete Gesture MFA.")
            else:
                self.status_label.configure(text="ACCESS DENIED", text_color="red")
                messagebox.showerror("Denied", "Identity could not be verified.")
        
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not reach server: {e}")
        
        # Reset for next attempt
        self.keystrokes = []
        self.pass_entry.delete(0, 'end')

if __name__ == "__main__":
    app = SafeLANApp()
    app.mainloop()