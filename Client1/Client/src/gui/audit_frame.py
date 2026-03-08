import customtkinter as ctk
from tkinter import messagebox
import requests
import datetime

ADMIN_PASSWORD = "admin"

class AuditFrame(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="#F5F6F7", corner_radius=0)
        self.controller = controller
        self.api_base = getattr(controller, 'api_base', "http://127.0.0.1:8000")
        self.username = "Unknown"
        
        # State variables
        self.user_role = "" # 'admin' or 'user'
        self.search_mode = "" # 'user' or 'filename'
        self.search_query = ""
        
        # UI Pages container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        """Called every time the frame is shown."""
        if hasattr(self.controller, 'current_user_data') and self.controller.current_user_data:
            self.username = self.controller.current_user_data.get('username', 'Unknown').upper()
            self.user_role = self.controller.current_user_data.get('role', 'user')
        
        # Reset all stale widget references so no destroyed widget is accessed later
        self.scroll_frame = None
        self.blocks_lbl = None
        self.tx_lbl = None
        self.query_var = None
        self.query_dropdown = None
        self.search_mode = ""
        self.search_query = ""

        self.show_role_selection()

    def set_user(self, username, role="user"):
        self.username = username.upper()
        self.user_role = role

    def clear_container(self):
        """Destroy all child widgets cleanly."""
        for widget in self.container.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass

    def show_role_selection(self):
        self.clear_container()
        
        header = ctk.CTkFrame(self.container, fg_color="#FFFFFF", height=80, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="SafeLAN Blockchain Explorer", font=("Segoe UI", 24, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.pack(expand=True)
        
        ctk.CTkLabel(content, text="Select your access role to continue", font=("Segoe UI", 16), text_color="#1A1C1E").pack(pady=(0, 30))
        
        # Admin Card
        admin_btn = ctk.CTkButton(content, text="View Logs as Administrator", font=("Segoe UI", 14, "bold"), 
                                width=300, height=60, fg_color="#1A73E8", command=self.prompt_admin_password)
        admin_btn.pack(pady=10)
        
        # User Card
        user_btn = ctk.CTkButton(content, text="View Logs as User", font=("Segoe UI", 14, "bold"), 
                               width=300, height=60, fg_color="#1A73E8", command=lambda: self.set_role("user"))
        user_btn.pack(pady=10)
        
        ctk.CTkButton(self.container, text="← Back to Dashboard", fg_color="#1A1C1E", 
                    command=lambda: self.controller.show_frame("DashboardFrame")).pack(pady=20)

    def prompt_admin_password(self):
        # Using simple ctk input dialog for password
        dialog = ctk.CTkInputDialog(text="Enter administrator password:", title="Admin Auth")
        # Note: ctk input dialog doesn't natively support show='●' in all versions
        # but it's the most standard 'premium' way in ctk without custom classes.
        password = dialog.get_input()
        
        if password == ADMIN_PASSWORD:
            self.set_role("admin")
        elif password is not None:
            messagebox.showerror("Access Denied", "Incorrect password!")

    def set_role(self, role):
        self.user_role = role
        # We now want regular users to see the search mode selection too
        self.show_mode_selection()

    def show_mode_selection(self):
        self.clear_container()
        
        # Header with Access Level
        header = ctk.CTkFrame(self.container, fg_color="#FFFFFF", height=100, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="Search Transaction Logs", font=("Segoe UI", 24, "bold")).pack(pady=(20, 0))
        
        access_text = f"Access Level: {self.user_role.capitalize()}" if self.user_role else "Access Level: Unknown"
        access_color = "#E74C3C" if self.user_role == "admin" else "#27AE60"
        ctk.CTkLabel(header, text=access_text, 
                    font=("Segoe UI", 12, "bold"), text_color=access_color).pack()
        
        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.pack(expand=True, pady=40)
        
        # Search by User Card
        u_card = ctk.CTkFrame(content, fg_color="#E8F4F8", width=480, height=100, corner_radius=10, border_width=0)
        u_card.pack(pady=10)
        u_card.pack_propagate(False)
        ctk.CTkLabel(u_card, text="👤", font=("Segoe UI", 32)).pack(side="left", padx=(30, 20))
        ctk.CTkLabel(u_card, text="Search by Username", font=("Segoe UI", 16, "bold"), text_color="#000000").pack(side="left")
        ctk.CTkButton(u_card, text="Select", width=120, height=50, fg_color="#3498DB", font=("Segoe UI", 14, "bold"),
                    command=lambda: self.set_mode("user")).pack(side="right", padx=30)
        
        # Search by Filename Card
        f_card = ctk.CTkFrame(content, fg_color="#FEF5E7", width=480, height=100, corner_radius=10, border_width=0)
        f_card.pack(pady=10)
        f_card.pack_propagate(False)
        ctk.CTkLabel(f_card, text="📁", font=("Segoe UI", 32)).pack(side="left", padx=(30, 20))
        ctk.CTkLabel(f_card, text="Search by Filename", font=("Segoe UI", 16, "bold"), text_color="#000000").pack(side="left")
        ctk.CTkButton(f_card, text="Select", width=120, height=50, fg_color="#F39C12", font=("Segoe UI", 14, "bold"),
                    command=lambda: self.set_mode("filename")).pack(side="right", padx=30)
        
        ctk.CTkButton(content, text="← Back", fg_color="#1A1C1E", 
                    command=self.show_role_selection).pack(pady=20)

    def set_mode(self, mode):
        self.search_mode = mode
        self.show_query_input()

    def show_query_input(self):
        self.clear_container()
        
        header = ctk.CTkFrame(self.container, fg_color="#FFFFFF", height=80, corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text="Select Search Query", font=("Segoe UI", 20, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.pack(expand=True)
        
        icon = "👤" if self.search_mode == "user" else "📁"
        subtitle = "Select Username to search for" if self.search_mode == "user" else "Select file to view its history"
        
        ctk.CTkLabel(content, text=icon, font=("Segoe UI", 48)).pack(pady=10)
        ctk.CTkLabel(content, text=subtitle, font=("Segoe UI", 14, "bold")).pack(pady=5)
        
        # Discovery Fetching
        options = []
        try:
            if self.search_mode == "user":
                if self.user_role == "admin":
                    r = requests.get(f"{self.api_base}/users/all", timeout=3)
                    options = r.json()
                    if "PUBLIC" in options: 
                        options.remove("PUBLIC")
                    options.insert(0, "PUBLIC") # Add PUBLIC as first option
                else:
                    options = [self.username, "PUBLIC"]
            else:
                if self.user_role == "admin":
                    r = requests.get(f"{self.api_base}/files/all", timeout=3)
                    options = r.json()
                else:
                    # Regular user: get files visible to them using the correct endpoint
                    user_files = set()
                    
                    # Files currently visible to them in the vault (public + shared with them + their own)
                    r_list = requests.get(
                        f"{self.api_base}/files/list", 
                        params={"user": self.username},  # Server uses 'user' not 'username'
                        timeout=5
                    )
                    if r_list.status_code == 200:
                        for f in r_list.json():
                            if isinstance(f, dict) and "name" in f:
                                user_files.add(f["name"])
                            elif isinstance(f, str):
                                user_files.add(f)
                                
                    options = list(user_files)
                        
        except Exception as e:
            print(f"Discovery Error: {e}")
            options = ["Local Cache Only"]

        if not options:
            options = ["No items available"]

        self.query_var = ctk.StringVar(value=self.username if self.username in options else options[0] if options else "")
        self.query_dropdown = ctk.CTkComboBox(content, variable=self.query_var, values=options, width=350, height=45, state="readonly")
        self.query_dropdown.pack(pady=20)
        
        ctk.CTkButton(content, text="🔍 Search", font=("Segoe UI", 14, "bold"), 
                    width=200, height=50, command=self.execute_search).pack(pady=10)
        
        ctk.CTkButton(content, text="← Back", fg_color="#1A1C1E", 
                    command=self.show_mode_selection).pack(pady=10)

    def execute_search(self):
        query = self.query_var.get().strip()
        if not query or query in ["Loading...", "No data found", "No items available"]:
            messagebox.showwarning("Selection Required", "Please select a valid search query from the list")
            return
        
        self.search_query = query
        self.show_results()

    def show_results(self):
        self.clear_container()
        
        # Header
        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 5))
        
        ctk.CTkLabel(header, text="Audit Results", font=("Segoe UI", 24, "bold"), text_color="#1A1C1E").pack(side="left")
        
        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")
        
        ctk.CTkButton(btn_row, text="🔄 Refresh", width=100, command=self.refresh_logs, fg_color="#27AE60").pack(side="left", padx=5)
        if self.user_role == "admin":
            ctk.CTkButton(btn_row, text="New Search", width=120, command=self.show_mode_selection, fg_color="#1A73E8").pack(side="left", padx=5)
            ctk.CTkButton(btn_row, text="← Back", width=100, command=self.show_query_input, fg_color="#1A1C1E").pack(side="left", padx=5)
        else:
            # Allow regular user to back out to Role Selection in case they want to enter Admin pass
            ctk.CTkButton(btn_row, text="← Back", width=100, command=self.show_role_selection, fg_color="#1A1C1E").pack(side="left", padx=5)
        
        # Stats Row
        stats_row = ctk.CTkFrame(self.container, fg_color="transparent")
        stats_row.pack(fill="x", padx=40, pady=5)
        self.blocks_lbl = self._create_stat_card(stats_row, "TOTAL BLOCKS", "0")
        self.tx_lbl = self._create_stat_card(stats_row, "TOTAL TRANSACTIONS", "0")

        # Log List Container
        self.log_container = ctk.CTkFrame(self.container, fg_color="#FFFFFF", corner_radius=20, border_width=1, border_color="#D1D9E6")
        self.log_container.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Table Headers (Matched to User Photo)
        t_head = ctk.CTkFrame(self.log_container, fg_color="#2C3E50", height=40, corner_radius=0)
        t_head.pack(fill="x", padx=2, pady=(2, 0))
        t_head.pack_propagate(False)
        
        header_font = ("Segoe UI", 11, "bold")
        ctk.CTkLabel(t_head, text="Filename", font=header_font, text_color="white", width=200, anchor="center").pack(side="left", padx=5)
        ctk.CTkLabel(t_head, text="Sender", font=header_font, text_color="white", width=150, anchor="center").pack(side="left", padx=5)
        ctk.CTkLabel(t_head, text="Receiver", font=header_font, text_color="white", width=150, anchor="center").pack(side="left", padx=5)
        ctk.CTkLabel(t_head, text="Action", font=header_font, text_color="white", width=100, anchor="center").pack(side="left", padx=5)
        ctk.CTkLabel(t_head, text="Timestamp", font=header_font, text_color="white", width=160, anchor="center").pack(side="left", padx=5)
        ctk.CTkLabel(t_head, text="Hash", font=header_font, text_color="white", anchor="center").pack(side="left", padx=5, fill="x", expand=True)

        self.scroll_frame = ctk.CTkScrollableFrame(self.log_container, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.refresh_logs()

    def _create_stat_card(self, parent, title, value):
        card = ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=15, border_width=1, border_color="#D1D9E6", width=200, height=80)
        card.pack(side="left", padx=(0, 20))
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Segoe UI", 10, "bold"), text_color="#1A1C1E").pack(pady=(15, 0))
        lbl = ctk.CTkLabel(card, text=value, font=("Segoe UI", 24, "bold"), text_color="#1A1C1E")
        lbl.pack()
        return lbl

    def refresh_logs(self):
        # Only refresh if the results page components exist and are valid
        if not hasattr(self, 'scroll_frame') or self.scroll_frame is None:
            return
        if not self.scroll_frame.winfo_exists():
            return

        try:
            stats = requests.get(f"{self.api_base}/blockchain/stats").json()
            if self.blocks_lbl and self.blocks_lbl.winfo_exists():
                self.blocks_lbl.configure(text=str(stats.get("total_blocks", 0)))
            if self.tx_lbl and self.tx_lbl.winfo_exists():
                self.tx_lbl.configure(text=str(stats.get("total_transactions", 0)))
        except: pass

        for w in self.scroll_frame.winfo_children(): w.destroy()
        
        try:
            # Construct URL based on search mode
            if self.search_mode == 'user':
                url = f"{self.api_base}/logs/user/{self.search_query}"
            else:
                url = f"{self.api_base}/logs/filename/{self.search_query}"
            
            # Pass authorization context
            params = {
                "requesting_user_id": self.username,
                "role": self.user_role
            }
            
            # Fetch logs
            print(f"[DEBUG] AuditFrame: Requesting logs from {url} with params {params}")
            r = requests.get(url, params=params, timeout=5)
            print(f"[DEBUG] AuditFrame: Server returned {r.status_code}")
            if r.status_code != 200:
                raise Exception(f"Server returned {r.status_code}")
                
            all_tx = r.json()
            
            if not all_tx:
                ctk.CTkLabel(self.scroll_frame, text="No matching transactions found.", 
                           font=("Segoe UI", 12), text_color="#1A1C1E").pack(pady=20)
                return

            for tx in reversed(all_tx):
                row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=45)
                row.pack(fill="x", pady=2)
                row.pack_propagate(False)
                
                # Filename
                fname = tx.get('filename', tx.get('file_hash', 'N/A'))
                ctk.CTkLabel(row, text=fname, font=("Segoe UI", 11), text_color="#1A1C1E", width=200, anchor="center").pack(side="left", padx=5)
                
                # Sender
                sender = tx.get("sender", "SYSTEM")
                ctk.CTkLabel(row, text=sender, font=("Segoe UI", 11), text_color="#1A1C1E", width=150, anchor="center").pack(side="left", padx=5)
                
                # Receiver
                receiver = tx.get("receiver", "SERVER")
                ctk.CTkLabel(row, text=receiver, font=("Segoe UI", 11), text_color="#1A1C1E", width=150, anchor="center").pack(side="left", padx=5)
                
                # Action
                action = tx.get("action", "??")
                colors = {
                    "UPLOAD": "#1A73E8",   # Google Blue
                    "DOWNLOAD": "#27AE60", # Emerald Green
                    "DELETE": "#E74C3C",   # Alizarin Red
                    "MODIFY": "#F39C12",   # Orange
                    "OPEN": "#16A085",     # Green Sea
                    "SHARE": "#8E44AD",    # Wisteria Purple
                    "AUDIT": "#2C3E50"      # Midnight Blue
                }
                action_color = colors.get(action, "#5F6368")
                ctk.CTkLabel(row, text=action, font=("Segoe UI", 11, "bold"), text_color=action_color, width=100, anchor="center").pack(side="left", padx=5)
                
                # Timestamp
                dt = datetime.datetime.fromtimestamp(tx.get("timestamp", 0)).strftime('%Y-%m-%d %H:%M')
                ctk.CTkLabel(row, text=dt, font=("Consolas", 11), text_color="#1A1C1E", width=160, anchor="center").pack(side="left", padx=5)

                # Hash (File Hash)
                f_hash = tx.get("file_hash", tx.get("tx_id", "N/A"))
                truncated_f_hash = f_hash[:24] + "..." if len(f_hash) > 24 else f_hash
                ctk.CTkLabel(row, text=truncated_f_hash, font=("Consolas", 10), text_color="#5F6368", anchor="center").pack(side="left", padx=5, fill="x", expand=True)
                
                ctk.CTkFrame(self.scroll_frame, fg_color="#E8EAED", height=1).pack(fill="x", padx=15)
                
        except Exception as e:
            messagebox.showerror("Blockchain Error", f"Failed to fetch audit logs: {e}")
