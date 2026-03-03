import customtkinter as ctk
import requests
import threading
from Client.src.logic.config_mgr import save_server_config, load_server_config

class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="#F0F2F5", corner_radius=0)
        self.controller = controller
        
        # Force centered grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._setup_ui()

    def _setup_ui(self):
        # Center Card Container
        self.card = ctk.CTkFrame(
            self, 
            fg_color="#FFFFFF", 
            corner_radius=25, 
            width=450, 
            height=620, # Fixed height
            border_width=1, 
            border_color="#E0E4E9"
        )
        self.card.grid(row=0, column=0, padx=20, pady=20)
        self.card.pack_propagate(False)

        # Header
        ctk.CTkLabel(self.card, text="⚙️", font=("Segoe UI", 60)).pack(pady=(40, 5))
        ctk.CTkLabel(self.card, text="Server Settings", font=("Segoe UI", 26, "bold"), text_color="#1A1C1E").pack()
        ctk.CTkLabel(self.card, text="Configure Gateway Endpoint", font=("Segoe UI", 14), text_color="#5F6368").pack(pady=(0, 30))

        config = load_server_config()

        # Inputs
        self._create_input_label("SERVER IP ADDRESS")
        self.ip_entry = ctk.CTkEntry(self.card, placeholder_text="e.g. 192.168.1.10", width=350, height=50, corner_radius=10, border_width=2)
        self.ip_entry.insert(0, config["ip"])
        self.ip_entry.pack(pady=(0, 20))

        self._create_input_label("COMMUNICATION PORT")
        self.port_entry = ctk.CTkEntry(self.card, placeholder_text="8000", width=350, height=50, corner_radius=10, border_width=2)
        self.port_entry.insert(0, config["port"])
        self.port_entry.pack(pady=(0, 35))

        # Status
        self.status_dot = ctk.CTkLabel(self.card, text="● Network Ready", font=("Segoe UI", 13, "bold"), text_color="#95A5A6")
        self.status_dot.pack(pady=5)

        # Buttons
        self.save_btn = ctk.CTkButton(
            self.card, text="Update Gateway", fg_color="#0061A4", hover_color="#004A7D",
            height=55, width=350, font=("Segoe UI", 16, "bold"), corner_radius=12,
            command=self._save_settings
        )
        self.save_btn.pack(pady=(10, 5))

        self.back_btn = ctk.CTkButton(
            self.card, text="Return to Entry Point", fg_color="transparent", text_color="#1A73E8", 
            font=("Segoe UI", 13, "bold"), hover_color="#F0F7FF",
            command=lambda: self.controller.show_frame("LoginFrame")
        )
        self.back_btn.pack(pady=10)

    def _create_input_label(self, text):
        lbl = ctk.CTkLabel(self.card, text=text, font=("Segoe UI", 11, "bold"), text_color="#7F8C8D")
        lbl.pack(anchor="w", padx=50)

    def _save_settings(self):
        ip, port = self.ip_entry.get().strip(), self.port_entry.get().strip()
        if ip and port:
            save_server_config(ip, port)
            new_url = f"http://{ip}:{port}"
            self.controller.update_api_base(new_url)
            self.save_btn.configure(fg_color="#27AE60", text="Settings Applied ✓")
            threading.Thread(target=self._check_connection, args=(new_url,), daemon=True).start()
            self.after(2000, lambda: self.save_btn.configure(fg_color="#0061A4", text="Update Gateway"))

    def _check_connection(self, url):
        try:
            r = requests.get(f"{url}/health", timeout=3)
            color = "#27AE60" if r.status_code == 200 else "#E74C3C"
            text = "● Connection Active" if r.status_code == 200 else "● Server Unreachable"
            self.after(0, lambda: self.status_dot.configure(text=text, text_color=color))
        except:
            self.after(0, lambda: self.status_dot.configure(text="● Server Unreachable", text_color="#E74C3C"))