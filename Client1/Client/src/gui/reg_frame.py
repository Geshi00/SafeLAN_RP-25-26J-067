import customtkinter as ctk
import time, re
from Client.src.logic.reg_engine import RegEngine
from config.client_settings import REQUIRED_SAMPLES 

class RegFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(
            master, fg_color="#FFFFFF", corner_radius=25, 
            width=540, height=820, border_width=1, border_color="#D1D9E6"
        )
        self.controller, self.engine, self.temp_events = controller, RegEngine(), []
        self.pack_propagate(False)
        self._setup_ui()

    def _setup_ui(self):
        # Branding Header
        ctk.CTkLabel(self, text="🧬", font=("Segoe UI", 85)).pack(pady=(60, 10), anchor="center")
        ctk.CTkLabel(self, text="Biometric Enrollment", font=("Segoe UI", 28, "bold"), text_color="#1A1C1E").pack(pady=(0, 20), anchor="center")

        # Inputs (Matches LoginFrame widths)
        self.u_entry = self._create_field("Username")
        self.e_entry = self._create_field("Email for Hand-Gesture MFA")
        self.p_entry = self._create_field("Set Password", show="*")
        self.p_entry.bind("<KeyRelease>", self.update_security_ui)
        
        self.strength_bar = ctk.CTkProgressBar(self, height=8, width=380, progress_color="#EA4335")
        self.strength_bar.set(0)
        self.strength_bar.pack(pady=5)
        
        self.p_conf = self._create_field("Confirm Password", show="*")

        self.prog_lbl = ctk.CTkLabel(self, text=f"DNA Captures: 0 / {REQUIRED_SAMPLES}", font=("Segoe UI", 18, "bold"), text_color="#004A7D")
        self.prog_lbl.pack(pady=(15, 5))

        self.input_box = ctk.CTkEntry(self, placeholder_text="Type Password Naturally & Press Enter", 
                                      width=380, height=55, fg_color="#FDFDFD", border_color="#0061A4", border_width=2)
        self.input_box.pack(pady=10)
        
        # DNA Binding
        self.input_box.bind("<KeyPress>", lambda e: self.temp_events.append({'k':e.keysym,'t':time.time(),'a':'p'}))
        self.input_box.bind("<KeyRelease>", lambda e: self.temp_events.append({'k':e.keysym,'t':time.time(),'a':'r'}))
        self.input_box.bind("<Return>", self.handle_sample)

        ctk.CTkButton(self, text="Cancel & Back", font=("Segoe UI", 13), fg_color="transparent", 
                      text_color="#4F4F4F", command=lambda: self.controller.show_frame("LoginFrame")).pack(pady=20)

    def _create_field(self, placeholder, **kwargs):
        e = ctk.CTkEntry(self, placeholder_text=placeholder, width=380, height=48, corner_radius=10, **kwargs)
        e.pack(pady=8)
        return e
    
    def update_security_ui(self, event):
        pwd = self.p_entry.get()
        rules = {"len": len(pwd) >= 8, "cap": bool(re.search(r'[A-Z]', pwd)), "num": bool(re.search(r'[0-9!@#$%^&*]', pwd))}
        score = sum(rules.values()) / 3
        self.strength_bar.set(score)
        self.strength_bar.configure(progress_color="#34A853" if score > 0.7 else "#FBBC04" if score > 0.3 else "#EA4335")

    def handle_sample(self, event):
        uid, email, target, typed = self.u_entry.get().strip(), self.e_entry.get().strip(), self.p_entry.get(), self.input_box.get()
        if not uid or not email or typed != target or len(target) < 8:
            self.input_box.configure(border_color="#E74C3C")
            self.temp_events.clear()
            self.input_box.delete(0, 'end')
            return 
        
        self.input_box.configure(border_color="#0061A4")
        count = self.engine.add_sample(self.temp_events)
        self.prog_lbl.configure(text=f"Captures: {count} / {REQUIRED_SAMPLES}")
        
        if self.engine.ready():
            if self.engine.save_and_train(uid, target, email): self.controller.show_frame("LoginFrame")
        
        self.temp_events.clear()
        self.input_box.delete(0, 'end')