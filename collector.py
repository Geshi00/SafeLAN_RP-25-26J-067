import time
import json
import os
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard


class SafeLANCollector5:
    def __init__(self):
        self.temp_events = []
        self.samples = []
        self.sample_count = 0
        self.session_target = 10 # collect 10 passwords in this session

        self.username = ""
        self.password = ""

        # ---------- GUI ----------
        self.root = tk.Tk()
        self.root.title("SafeLAN Enrollment (10 Passwords at a Time)")
        self.root.geometry("520x420")
        self.root.configure(padx=30, pady=30)

        self.setup_ui()

        # ---------- Keyboard Listener ----------
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

        self.root.mainloop()

    # ================= UI =================
    def setup_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True)

        tk.Label(self.frame, text="SafeLAN Biometric Enrollment",
                 font=("Arial", 15, "bold")).pack(pady=10)

        tk.Label(self.frame, text="Username").pack()
        self.user_entry = tk.Entry(self.frame, width=30, justify="center")
        self.user_entry.pack(pady=5)

        tk.Label(self.frame, text="Set Password").pack()
        self.pass_entry = tk.Entry(self.frame, width=30, justify="center", show="*")
        self.pass_entry.pack(pady=5)

        self.start_btn = tk.Button(
            self.frame,
            text=f"Start Enrollment ({self.session_target} Passwords)",
            bg="#27ae60",
            fg="white",
            command=self.start_enrollment
        )
        self.start_btn.pack(pady=15)

        self.status = tk.Label(self.frame, text="", font=("Arial", 11))
        self.status.pack(pady=10)

        self.input_box = tk.Entry(
            self.frame, width=32, font=("Arial", 14), justify="center"
        )
        self.input_box.bind("<Return>", self.validate_password)

    # ================= Enrollment =================
    def start_enrollment(self):
        self.username = self.user_entry.get().strip()
        self.password = self.pass_entry.get().strip()

        if not self.username or not self.password:
            messagebox.showwarning("Error", "Username and password required")
            return

        self.user_entry.config(state="disabled")
        self.pass_entry.config(state="disabled")
        self.start_btn.config(state="disabled")

        # Load previous data if exists
        self.raw_file_path = f"data/raw/{self.username}_raw.json"
        if os.path.exists(self.raw_file_path):
            with open(self.raw_file_path, "r") as f:
                old_data = json.load(f)
                self.samples = old_data.get("samples", [])
                self.password = old_data.get("password", self.password)
                self.sample_count = len(self.samples)
            self.status.config(
                text=f"Appending new samples. Total existing: {self.sample_count}"
            )
        else:
            self.status.config(
                text=f"Type the password {self.session_target} times\nSample: 0/{self.session_target}"
            )

        self.input_box.pack(pady=10)
        self.input_box.focus_set()

    # ================= Keyboard Capture =================
    def on_press(self, key):
        try:
            k = key.char if hasattr(key, "char") else str(key)
        except:
            k = str(key)
        self.temp_events.append({"k": k, "t": time.time(), "a": "p"})

    def on_release(self, key):
        try:
            k = key.char if hasattr(key, "char") else str(key)
        except:
            k = str(key)
        self.temp_events.append({"k": k, "t": time.time(), "a": "r"})

    # ================= Validation =================
    def validate_password(self, event):
        typed = self.input_box.get()

        if typed == self.password:
            clean_events = [
                e for e in self.temp_events
                if "enter" not in e["k"].lower()
            ]
            self.samples.append(clean_events)
            self.sample_count += 1

            self.status.config(
                text=f"Sample collected. Total samples: {self.sample_count}"
            )

            if len(self.samples) % self.session_target == 0:
                self.save_data()
                messagebox.showinfo(
                    "Session Complete",
                    f"{self.session_target} new samples added! Total samples: {self.sample_count}"
                )
                self.root.destroy()
                return
        else:
            messagebox.showwarning("Mismatch", "Password mismatch. Try again.")

        self.temp_events = []
        self.input_box.delete(0, tk.END)

    # ================= Save =================
    def save_data(self):
        os.makedirs("data/raw", exist_ok=True)
        out = {
            "username": self.username,
            "password": self.password,
            "samples": self.samples
        }
        with open(self.raw_file_path, "w") as f:
            json.dump(out, f, indent=2)


if __name__ == "__main__":
    SafeLANCollector5()
