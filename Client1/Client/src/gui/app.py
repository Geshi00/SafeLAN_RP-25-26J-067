import sys, os, time
import customtkinter as ctk

# --- 1. DYNAMIC PATH INJECTION ---
current_file_path = os.path.abspath(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(current_file_path), "../../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

from Client.src.logic.config_mgr import load_server_config
from Client.src.gui.login_frame import LoginFrame
from Client.src.gui.reg_frame import RegFrame
from Client.src.gui.dashboard_frame import DashboardFrame
from Client.src.gui.vault_frame import VaultFrame
from Client.src.gui.settings_frame import SettingsFrame

class SafeLANApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SafeLAN | Unified Gateway")
        self.set_window_size(600, 880)
        
        config = load_server_config()
        self.api_base = f"http://{config['ip']}:{config['port']}"
        
        # ROOT GRID: Column 0 for Sidebar, Column 1 for Content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # RESTORED OLD COLORS: Dark Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color="#1A1C1E", corner_radius=0)
        self._setup_sidebar_content()

        # Main Display Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        # Internal Centering
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for F in (LoginFrame, RegFrame, DashboardFrame, VaultFrame, SettingsFrame):
            page_name = F.__name__
            frame = F(master=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="") 
            frame.grid_remove()

        self.current_user_data = None
        self.show_frame("LoginFrame")

    def show_mfa_challenge(self, auth_data):
        """Fixed method to handle step-up auth."""
        from Client.src.gui.ui_2fa import TwoFAWindow 
        self.sidebar.grid_forget()
        for f in self.frames.values(): f.grid_remove()
        
        self.set_window_size(1000, 850)
        mfa_frame = TwoFAWindow(self.container, self, auth_data['username'], auth_data.get('otp', '0000'))
        self.frames["TwoFAWindow"] = mfa_frame 
        mfa_frame.grid(row=0, column=0, sticky="")
        mfa_frame.tkraise()
        mfa_frame.activate()

    def show_frame(self, page_name):
        if "TwoFAWindow" in self.frames and page_name != "TwoFAWindow":
            self.frames["TwoFAWindow"].destroy()
            del self.frames["TwoFAWindow"]

        for f in self.frames.values(): f.grid_remove()

        frame = self.frames.get(page_name)
        if not frame: return

        if page_name in ["DashboardFrame", "VaultFrame"]:
            self.set_window_size(1150, 750)
            # GRID ALIGNMENT FIX
            self.sidebar.grid(row=0, column=0, sticky="nsew")
            self.container.grid(row=0, column=1, sticky="nsew", columnspan=1)
            frame.grid(row=0, column=0, sticky="nsew") 
        else:
            self.sidebar.grid_forget()
            self.container.grid(row=0, column=0, sticky="nsew", columnspan=2)
            self.set_window_size(600, 920 if page_name == "SettingsFrame" else 880)
            frame.grid(row=0, column=0, sticky="")

        if self.current_user_data and page_name == "DashboardFrame":
            frame.update_dashboard(self.current_user_data)
        
        frame.tkraise()

    def login_success(self, auth_data):
        self.current_user_data = auth_data
        status = auth_data.get("status")
        if status == "SUCCESS":
            self.show_frame("DashboardFrame")
        elif status == "CHALLENGE":
            self.show_mfa_challenge(auth_data)

    def set_window_size(self, width, height):
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def update_api_base(self, new_url):
        self.api_base = new_url
        for frame in self.frames.values():
            if hasattr(frame, 'api_base'): frame.api_base = new_url

    def logout(self):
        self.current_user_data = None
        self.show_frame("LoginFrame")

    def _setup_sidebar_content(self):
        ctk.CTkLabel(self.sidebar, text="🛡️", font=("Segoe UI", 50)).pack(pady=(40, 5))
        self._nav_btn("📊 Security Overview", lambda: self.show_frame("DashboardFrame"))
        self._nav_btn("📂 Network Vault", lambda: self.show_frame("VaultFrame"))
        self._nav_btn("⚙️ Settings", lambda: self.show_frame("SettingsFrame"))
        ctk.CTkButton(self.sidebar, text="Logout", fg_color="#E74C3C", command=self.logout).pack(side="bottom", fill="x", padx=20, pady=20)

    def _nav_btn(self, text, command):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", anchor="w", height=45, command=command, text_color="white")
        btn.pack(fill="x", padx=15, pady=5)
        return btn

if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = SafeLANApp()
    app.mainloop()