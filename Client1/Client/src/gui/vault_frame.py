import customtkinter as ctk
from tkinter import filedialog, messagebox
from Client.src.logic.vault_engine import VaultEngine

class VaultFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="#F5F6F7", corner_radius=0)
        self.controller = controller
        self.engine = VaultEngine()
        self.username = "Unknown"
        self.all_files = [] 

        self.pack_propagate(False)
        self._setup_ui()

    def _setup_ui(self):
        # --- 1. TOOLBAR ---
        self.toolbar = ctk.CTkFrame(self, fg_color="#FFFFFF", height=100, corner_radius=15, border_width=1, border_color="#D1D9E6")
        self.toolbar.pack(fill="x", padx=30, pady=(30, 10))
        self.toolbar.pack_propagate(False)

        ctk.CTkLabel(self.toolbar, text="Network Vault", font=("Segoe UI", 24, "bold")).pack(side="left", padx=25)

        self.up_btn = ctk.CTkButton(self.toolbar, text="+ Share Resource", width=140, height=35, 
                                     fg_color="#1A73E8", font=("Segoe UI", 12, "bold"), command=self._upload_action)
        self.up_btn.pack(side="right", padx=25)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search_query)
        self.search_bar = ctk.CTkEntry(self.toolbar, placeholder_text="🔍 Search public & private files...", 
                                        width=300, height=35, textvariable=self.search_var)
        self.search_bar.pack(side="right")

        # --- 2. STATS BAR ---
        self.stats_bar = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.stats_bar.pack(fill="x", padx=35, pady=5)
        self.count_lbl = ctk.CTkLabel(self.stats_bar, text="Items: 0", font=("Segoe UI", 12), text_color="#5F6368")
        self.count_lbl.pack(side="left")
        self.size_lbl = ctk.CTkLabel(self.stats_bar, text="Vault Size: 0 KB", font=("Segoe UI", 12), text_color="#5F6368")
        self.size_lbl.pack(side="left", padx=20)

        # --- 3. EXPLORER BOX ---
        self.explorer_box = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#D1D9E6")
        self.explorer_box.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        h_row = ctk.CTkFrame(self.explorer_box, fg_color="#F1F2F6", height=40, corner_radius=5)
        h_row.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(h_row, text="Scope", font=("Segoe UI", 11, "bold"), text_color="#5F6368").pack(side="left", padx=(20, 10))
        ctk.CTkLabel(h_row, text="Resource Name", font=("Segoe UI", 12, "bold"), text_color="#5F6368").pack(side="left", padx=20)
        ctk.CTkLabel(h_row, text="Actions", font=("Segoe UI", 12, "bold"), text_color="#5F6368").pack(side="right", padx=60)

        self.file_scroll = ctk.CTkScrollableFrame(self.explorer_box, fg_color="transparent")
        self.file_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh(self):
        data = self.engine.get_vault_data(self.username)
        self.all_files = data["files"]
        self.count_lbl.configure(text=f"Visible Items: {data['count']}")
        self.size_lbl.configure(text=f"Total Storage: {data['total_kb']:.1f} KB")
        self._render_list(self.all_files)

    def _render_list(self, file_list):
        for w in self.file_scroll.winfo_children(): w.destroy()
        
        if not file_list:
            ctk.CTkLabel(self.file_scroll, text="No accessible files found.", font=("Segoe UI", 13), text_color="#9AA0A6").pack(pady=40)
            return

        for f in file_list:
            row = ctk.CTkFrame(self.file_scroll, fg_color="#F8F9FA", height=55, corner_radius=8)
            row.pack(fill="x", pady=3); row.pack_propagate(False)
            
            # Privacy Indicator
            is_public = f.get('target', 'PUBLIC') == 'PUBLIC'
            icon = "🌐" if is_public else "🔐"
            scope_txt = "PUBLIC" if is_public else f"TO: {f.get('target')}"
            
            ctk.CTkLabel(row, text=icon, font=("Segoe UI", 14)).pack(side="left", padx=(15, 5))
            ctk.CTkLabel(row, text=scope_txt, font=("Segoe UI", 9, "bold"), text_color="#7F8C8D", width=60).pack(side="left")
            
            # File Info
            ctk.CTkLabel(row, text=f["name"], font=("Segoe UI", 13, "bold"), text_color="#1A1C1E").pack(side="left", padx=20)
            ctk.CTkLabel(row, text=f["size"], font=("Segoe UI", 11), text_color="#5F6368").pack(side="left", padx=10)
            
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(side="right", padx=15)
            
            ctk.CTkButton(btns, text="⬇", width=35, height=32, font=("Segoe UI", 16),
                          fg_color="#E8F0FE", text_color="#1A73E8", command=lambda n=f["name"]: self._download_action(n)).pack(side="left", padx=2)
            
            ctk.CTkButton(btns, text="🗑", width=35, height=32, font=("Segoe UI", 16),
                          fg_color="#FDECEA", text_color="#E74C3C", command=lambda n=f["name"]: self._delete_action(n)).pack(side="left", padx=2)

    def _on_search_query(self, *args):
        query = self.search_var.get().lower()
        filtered = [f for f in self.all_files if query in f["name"].lower()]
        self._render_list(filtered)

    def _upload_action(self):
        path = filedialog.askopenfilename()
        if not path: return

        # Target Selection Dialog
        dialog = ctk.CTkInputDialog(text="Enter 'PUBLIC' or a specific Username:", title="Share Settings")
        target = dialog.get_input()
        
        if target is None: return # User cancelled
        target = target.strip().upper() if target.strip() else "PUBLIC"

        if self.engine.upload_file(path, self.username, target):
            self.refresh()
        else:
            messagebox.showerror("Vault Error", "Upload failed. Check server status.")

    def _download_action(self, filename):
        path = filedialog.asksaveasfilename(initialfile=filename)
        if path and self.engine.download_file(filename, path):
            messagebox.showinfo("SafeLAN", f"Successfully saved {filename}")

    def _delete_action(self, filename):
        if messagebox.askyesno("Confirm", f"Remove '{filename}'?"):
            if self.engine.delete_file(filename): self.refresh()

    def set_user(self, username):
        self.username = username.upper()
        self.refresh()