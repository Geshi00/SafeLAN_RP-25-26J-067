import customtkinter as ctk
import time
from tkinter import messagebox
from Client.src.logic.auth_engine import AuthEngine

class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(
            master, fg_color="#FFFFFF", corner_radius=25,
            width=540, height=820, border_width=1, border_color="#D1D9E6"
        )
        self.controller = controller
        self.auth_engine = AuthEngine() 
        self.temp_events = []
        self.is_password_hidden = True

        self.pack_propagate(False) # Maintains card size
        self._setup_ui()

    def _setup_ui(self):
        # Settings Icon
        ctk.CTkButton(self, text="⚙️", width=40, height=40, fg_color="transparent", 
                      text_color="#5F6368", font=("Segoe UI", 24), 
                      command=lambda: self.controller.show_frame("SettingsFrame")).place(x=20, y=20)

        # Centered Branding
        self.logo_lbl = ctk.CTkLabel(self, text="🛡️", font=("Segoe UI", 100))
        self.logo_lbl.pack(pady=(80, 10), anchor="center")

        self.title_lbl = ctk.CTkLabel(self, text="SafeLAN Gateway", font=("Segoe UI", 32, "bold"), text_color="#1A1C1E")
        self.title_lbl.pack(pady=(0, 50), anchor="center")

        # Inputs
        self.u_entry = ctk.CTkEntry(self, placeholder_text="Username", width=380, height=55, border_width=2, corner_radius=10)
        self.u_entry.pack(pady=12, anchor="center")

        self.pw_box = ctk.CTkFrame(self, fg_color="#FDFDFD", border_color="#C4C7C5", border_width=2, width=380, height=55, corner_radius=10)
        self.pw_box.pack(pady=12, anchor="center")
        self.pw_box.pack_propagate(False)

        self.p_entry = ctk.CTkEntry(self.pw_box, placeholder_text="Enter Password", show="*", fg_color="transparent", border_width=0, width=310, height=50)
        self.p_entry.pack(side="left", padx=10)

        self.toggle_btn = ctk.CTkButton(self.pw_box, text="👁", width=40, fg_color="transparent", text_color="#1A1C1E", command=self.toggle_password)
        self.toggle_btn.pack(side="right", padx=5)

        # DNA Binding
        self.p_entry.bind("<KeyPress>", self._record_event)
        self.p_entry.bind("<KeyRelease>", self._record_event)
        self.p_entry.bind("<Return>", lambda e: self.handle_verify())

        self.status_lbl = ctk.CTkLabel(self, text="", font=("Segoe UI", 13, "italic"))
        self.status_lbl.pack(pady=5, anchor="center")

        self.login_btn = ctk.CTkButton(self, text="Authorize & Unlock", font=("Segoe UI", 18, "bold"), width=380, height=60, fg_color="#0061A4", corner_radius=12, command=self.handle_verify)
        self.login_btn.pack(pady=(25, 10), anchor="center")

        ctk.CTkButton(self, text="Enroll New Profile", font=("Segoe UI", 14), fg_color="transparent", text_color="#0061A4", command=lambda: self.controller.show_frame("RegFrame")).pack(pady=5, anchor="center")

    def _record_event(self, event):
        action = 'p' if event.type == '2' else 'r'
        self.temp_events.append({'k': event.keysym, 't': time.time(), 'a': action})

    def toggle_password(self):
        self.is_password_hidden = not self.is_password_hidden
        self.p_entry.configure(show="*" if self.is_password_hidden else "")

    def handle_verify(self):
        uid, pwd = self.u_entry.get().strip(), self.p_entry.get()
        if not uid or not pwd: return

        if len(self.temp_events) < 12:
            self.status_lbl.configure(text="Typing data too short. Try again.", text_color="#E74C3C")
            self.temp_events.clear()
            self.p_entry.delete(0, 'end')
            return

        self.status_lbl.configure(text="Analyzing Biometrics...", text_color="#1A73E8")
        self.update_idletasks()

        events_copy, _ = list(self.temp_events), self.temp_events.clear()
        res = self.auth_engine.verify(uid, events_copy, pwd)
        
        if res.get("status") in ["SUCCESS", "CHALLENGE"]:
            self.pw_box.configure(border_color="#27AE60")
            res["username"] = uid
            self.after(600, lambda: self.controller.login_success(res))
        else:
            self._handle_failure(res.get("status", "OFFLINE"))

    def _handle_failure(self, status):
        self.pw_box.configure(border_color="#E74C3C")
        self.status_lbl.configure(text="Access Denied ❌", text_color="#E74C3C")
        messagebox.showerror("Denied", f"Authentication Failed: {status}")
        self.p_entry.delete(0, "end")
        self.temp_events.clear()
        self.after(1000, lambda: self.pw_box.configure(border_color="#C4C7C5"))