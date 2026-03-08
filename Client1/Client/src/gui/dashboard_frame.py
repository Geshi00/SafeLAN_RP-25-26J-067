import customtkinter as ctk
from tkinter import filedialog, messagebox
import requests, os, threading

class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="#F5F6F7", corner_radius=0)
        self.controller = controller
        self.api_base = getattr(self.controller, 'api_base', "http://127.0.0.1:8000")
        self.username = "Unknown"
        self.role = "user"

        # Configure frame to expand content properly
        self._setup_main_content()

    def _setup_main_content(self):
        # Master container for all dashboard elements
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.pack(fill="both", expand=True, padx=40, pady=(30, 10))
        
        ctk.CTkLabel(self.main_area, text="Security Overview", 
                     font=("Segoe UI", 32, "bold"), text_color="#1A1C1E").pack(anchor="w", pady=(0, 20))

        # Metric Cards Row
        self.m_row = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.m_row.pack(fill="x", pady=10)
        
        # Cards use side="left" with fill="both" and expand=True to distribute space evenly
        self.ti_val = self._create_card(self.m_row, "TRUST INDEX", "#1A73E8")
        self.svm_val = self._create_card(self.m_row, "SVM SCORE", "#27AE60")
        self.ctx_val = self._create_card(self.m_row, "CONTEXT MATCH", "#1A1C1E")
        
        # Vault Quick-Access Area
        self.vault_container = ctk.CTkFrame(self.main_area, fg_color="#FFFFFF", corner_radius=20, 
                                            border_width=1, border_color="#D1D9E6")
        self.vault_container.pack(fill="both", expand=True, pady=20)
        
        v_head = ctk.CTkFrame(self.vault_container, fg_color="transparent")
        v_head.pack(fill="x", padx=25, pady=20)
        
        ctk.CTkLabel(v_head, text="Network Quick-Access", font=("Segoe UI", 20, "bold")).pack(side="left")
        
        if self.role != "admin":
            self.up_file_btn = ctk.CTkButton(v_head, text="+ Share File", width=120, command=self._upload)
            self.up_file_btn.pack(side="right")
        
        self.file_scroll = ctk.CTkScrollableFrame(self.vault_container, fg_color="transparent")
        self.file_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Footer Status Bar
        self.footer = ctk.CTkFrame(self, fg_color="#E8EAED", height=45, corner_radius=10)
        self.footer.pack(fill="x", padx=40, pady=(0, 20))
        self.footer.pack_propagate(False)
        
        ctk.CTkLabel(self.footer, text="●", text_color="#27AE60", font=("Segoe UI", 14)).pack(side="left", padx=(15, 5))
        self.u_identity_lbl = ctk.CTkLabel(self.footer, text="SESSION: INITIALIZING...", 
                                           font=("Consolas", 12, "bold"), text_color="#5F6368")
        self.u_identity_lbl.pack(side="left")

    def _create_card(self, parent, title, color):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=20, border_width=1, border_color="#D1D9E6")
        card.pack(side="left", padx=10, fill="both", expand=True)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 11, "bold"), text_color="#5F6368").pack(pady=(20, 2))
        lbl = ctk.CTkLabel(card, text="--", font=("Segoe UI", 34, "bold"), text_color=color)
        lbl.pack(pady=(0, 20))
        return lbl

    def update_dashboard(self, data):
        self.username = data.get('username', 'User').upper()
        self.role = data.get('role', 'user')
        self.u_identity_lbl.configure(text=f"AUTHORIZED SESSION: {self.username}", text_color="#27AE60")
        self.ti_val.configure(text=f"{data.get('trust_index', 0)}%")
        
        raw_svm = data.get('svm_score', 0.0)
        self.svm_val.configure(text=f"{float(raw_svm):.6f}")
        self.ctx_val.configure(text=f"{data.get('context_score', 0)}/100")
        
        # New: Hide share button if admin
        if hasattr(self, "up_file_btn"):
            if self.role == "admin":
                self.up_file_btn.pack_forget()
            else:
                self.up_file_btn.pack(side="right")
        
        self.refresh_vault()

    def refresh_vault(self):
        threading.Thread(target=self._async_refresh, daemon=True).start()

    def _async_refresh(self):
        try:
            r = requests.get(f"{self.api_base}/files/list", timeout=5)
            if r.status_code == 200:
                self.after(0, lambda: self._populate_files(r.json()))
        except: pass

    def _populate_files(self, files):
        for w in self.file_scroll.winfo_children(): w.destroy()
        for f in files[:8]: 
            row = ctk.CTkFrame(self.file_scroll, fg_color="#F8F9FA", corner_radius=10, height=55)
            row.pack(fill="x", pady=5); row.pack_propagate(False)
            ctk.CTkLabel(row, text="📄", font=("Segoe UI", 18)).pack(side="left", padx=15)
            ctk.CTkLabel(row, text=f["name"], font=("Segoe UI", 13, "bold")).pack(side="left")
            if self.role != "admin":
                actions = ctk.CTkFrame(row, fg_color="transparent")
                actions.pack(side="right", padx=15)
                # Removed the download button as per instruction
                ctk.CTkButton(actions, text="🗑", width=35, height=32, 
                              command=lambda n=f["name"]: self._delete(n)).pack(side="left", padx=2)

    def _upload(self):
        p = filedialog.askopenfilename()
        if p:
            def do():
                try:
                    # Prompt for target just like VaultFrame
                    target = "PUBLIC" 
                    # We'll use a simple prompt logic or just default to PUBLIC for dashboard quick upload
                    # To keep it simple but functional:
                    with open(p, "rb") as f:
                        requests.post(f"{self.api_base}/files/upload", 
                                      files={"file": (os.path.basename(p), f)}, 
                                      data={"owner": self.username, "role": self.role, "target": "PUBLIC"})
                    self.refresh_vault()
                except Exception as e: 
                    self.after(0, lambda: messagebox.showerror("Upload Error", str(e)))
            threading.Thread(target=do, daemon=True).start()

    def set_user(self, username, role="user"):
        self.username = username.upper()
        self.role = role
        self.refresh_vault()

    def _download(self, filename):
        save_path = filedialog.asksaveasfilename(initialfile=filename)
        if save_path:
            def do():
                try:
                    params = {"user": self.username, "role": self.role, "action": "DOWNLOAD"}
                    r = requests.get(f"{self.api_base}/files/download/{filename}", params=params, stream=True)
                    with open(save_path, 'wb') as f:
                        for chunk in r.iter_content(8192): f.write(chunk)
                    self.after(0, lambda: messagebox.showinfo("SafeLAN", f"Downloaded {filename}"))
                except Exception as e: 
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=do, daemon=True).start()

    def _delete(self, name):
        if messagebox.askyesno("Confirm", f"Delete {name}?"):
            requests.delete(f"{self.api_base}/files/delete/{name}", params={"user": self.username, "role": self.role})
            self.refresh_vault()