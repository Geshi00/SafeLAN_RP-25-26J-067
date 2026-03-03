import customtkinter as ctk
import threading, cv2, os, time
from PIL import Image
import numpy as np
from Client.src.logic.hand_vision import HandDigitRecognizer

class TwoFAWindow(ctk.CTkFrame):
    def __init__(self, master, controller, username, otp_code):
        super().__init__(
            master, 
            fg_color="#FFFFFF", 
            corner_radius=25,
            width=850, 
            height=700, 
            border_width=1, 
            border_color="#D1D9E6"
        )
        self.controller, self.otp, self.idx = controller, str(otp_code), 0
        self.running = False
        self.pack_propagate(False)
        
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../models/hand_landmarker.task")
        self.recognizer = HandDigitRecognizer(os.path.abspath(path))

        self._setup_modern_ui()

    def _setup_modern_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(40, 20), fill="x")

        ctk.CTkLabel(self.header_frame, text="Secure Gesture Verification", font=("Segoe UI", 32, "bold"), text_color="#1A1C1E").pack()
        ctk.CTkLabel(self.header_frame, text="Digits are hidden for security. Perform the sequence to unlock.", font=("Segoe UI", 14), text_color="#5F6368").pack(pady=(5, 0))

        # --- HIDDEN OTP SEQUENCE ---
        self.otp_container = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=15, height=120)
        self.otp_container.pack(pady=10, padx=100, fill="x")
        self.otp_container.pack_propagate(False)

        self.digit_slots = [] # List of frames
        self.digit_labels = [] # List of labels inside those frames
        
        slot_inner_frame = ctk.CTkFrame(self.otp_container, fg_color="transparent")
        slot_inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        for _ in range(len(self.otp)):
            # Create a Frame to act as the border/background container
            slot_frame = ctk.CTkFrame(
                slot_inner_frame, 
                width=70, 
                height=70, 
                corner_radius=12,
                fg_color="#E8EAED",
                border_width=0
            )
            slot_frame.pack(side="left", padx=12)
            slot_frame.pack_propagate(False)
            
            # The actual Label inside the frame
            lbl = ctk.CTkLabel(
                slot_frame, 
                text="?", 
                font=("Consolas", 36, "bold"), 
                text_color="#BDC3C7"
            )
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            self.digit_slots.append(slot_frame)
            self.digit_labels.append(lbl)
        
        self._update_slot_visuals()

        # Camera Display
        self.cam_card = ctk.CTkFrame(self, fg_color="#000000", corner_radius=20, border_width=2, border_color="#E8EAED")
        self.cam_card.pack(pady=20, padx=40, expand=True, fill="both")
        self.cam_card.pack_propagate(False)

        self.video_label = ctk.CTkLabel(self.cam_card, text="Accessing Camera...", text_color="#FFFFFF")
        self.video_label.pack(expand=True, fill="both")

        # Status Bar
        self.status_bar = ctk.CTkFrame(self, fg_color="#1A73E8", height=6, corner_radius=0)
        self.status_bar.pack(side="bottom", fill="x")
        
        self.live_lbl = ctk.CTkLabel(
            self, 
            text="Waiting for gesture...", 
            font=("Segoe UI", 16, "bold"), 
            text_color="#1A73E8"
        )
        self.live_lbl.pack(side="bottom", pady=15)

    def _update_slot_visuals(self):
        """Logic to switch styles on the container Frames and internal Labels."""
        for i, (slot, lbl) in enumerate(zip(self.digit_slots, self.digit_labels)):
            if i < self.idx:
                # Successfully entered digits: Green background
                slot.configure(fg_color="#27AE60", border_width=0)
                lbl.configure(text=f"{self.otp[i]}", text_color="#FFFFFF")
            elif i == self.idx:
                # Active slot: Blue border, light blue background
                slot.configure(fg_color="#D6EAF8", border_width=2, border_color="#1A73E8")
                lbl.configure(text="?", text_color="#1A73E8")
            else:
                # Future slots: Neutral grey
                slot.configure(fg_color="#E8EAED", border_width=0)
                lbl.configure(text="?", text_color="#BDC3C7")

    def _on_digit_match(self):
        self.idx += 1
        self._update_slot_visuals()
        if self.idx < len(self.otp):
            self.live_lbl.configure(text="Digit Accepted! Next gesture...", text_color="#27AE60")
        else:
            self.live_lbl.configure(text="MFA Complete. Accessing Vault...", text_color="#27AE60")
        self.after(800, lambda: self.live_lbl.configure(text_color="#1A73E8"))

    def activate(self):
        threading.Thread(target=self._async_init, daemon=True).start()

    def _async_init(self):
        if self.recognizer.start_session():
            self.running = True
            threading.Thread(target=self.camera_loop, daemon=True).start()

    def camera_loop(self):
        last_match_time = 0
        while self.running:
            frame, digit = self.recognizer.get_frame()
            if frame is None: continue

            if digit is not None and str(digit) == self.otp[self.idx]:
                if time.time() - last_match_time > 1.5:
                    last_match_time = time.time()
                    if self.idx + 1 == len(self.otp):
                        self.after(0, self._final_step)
                        return
                    else:
                        self.after(0, self._on_digit_match)

            frame = cv2.flip(frame, 1)
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
            self.after(0, lambda: self.video_label.configure(image=ctk_img, text=""))

    def _final_step(self):
        self.idx += 1
        self._update_slot_visuals()
        self.after(1000, self.finish)

    def finish(self):
        self.running = False
        self.recognizer.close()
        if self.controller.current_user_data:
            self.controller.current_user_data["status"] = "SUCCESS"
            self.after(0, lambda: self.controller.show_frame("DashboardFrame"))

    def destroy(self):
        self.running = False
        self.recognizer.close()
        super().destroy()