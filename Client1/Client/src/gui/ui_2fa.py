import customtkinter as ctk
import threading, cv2, os, time
from PIL import Image
# Absolute imports for package reliability
from Client.src.logic.hand_vision import HandDigitRecognizer
from config.client_settings import GESTURE_HOLD_SECONDS

class TwoFAWindow(ctk.CTkFrame):
    def __init__(self, master, controller, username, otp_code):
        super().__init__(
            master, fg_color="#FFFFFF", corner_radius=25,
            width=850, height=720, border_width=1, border_color="#D1D9E6"
        )
        self.controller, self.otp, self.idx = controller, str(otp_code), 0
        self.running = False
        self.pack_propagate(False)
        
        # Correct pathing for the model asset
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../models/hand_landmarker.task")
        self.recognizer = HandDigitRecognizer(os.path.abspath(path))

        self._setup_modern_ui()

    def _setup_modern_ui(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(30, 15), fill="x")

        ctk.CTkLabel(self.header_frame, text="Secure Gesture Verification", 
                     font=("Segoe UI", 32, "bold"), text_color="#1A1C1E").pack()
        
        instruction_text = f"Hold gestures for {GESTURE_HOLD_SECONDS} seconds. UI stays silent for security."
        ctk.CTkLabel(self.header_frame, text=instruction_text, 
                     font=("Segoe UI", 14), text_color="#5F6368").pack(pady=(5, 0))

        self.otp_container = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=15, height=100)
        self.otp_container.pack(pady=10, padx=80, fill="x")
        self.otp_container.pack_propagate(False)

        self.digit_slots, self.digit_labels = [], []
        slot_inner_frame = ctk.CTkFrame(self.otp_container, fg_color="transparent")
        slot_inner_frame.place(relx=0.5, rely=0.5, anchor="center")

        for _ in range(len(self.otp)):
            slot_frame = ctk.CTkFrame(slot_inner_frame, width=65, height=65, corner_radius=12, fg_color="#E8EAED")
            slot_frame.pack(side="left", padx=10)
            slot_frame.pack_propagate(False)
            
            lbl = ctk.CTkLabel(slot_frame, text="?", font=("Consolas", 32, "bold"), text_color="#BDC3C7")
            lbl.place(relx=0.5, rely=0.5, anchor="center")
            
            self.digit_slots.append(slot_frame)
            self.digit_labels.append(lbl)
        
        self._update_slot_visuals()

        self.cam_card = ctk.CTkFrame(self, fg_color="#000000", corner_radius=20, border_width=2, border_color="#E8EAED")
        self.cam_card.pack(pady=10, padx=40, expand=True, fill="both")
        self.cam_card.pack_propagate(False)

        self.video_label = ctk.CTkLabel(self.cam_card, text="Initializing Camera...", text_color="#FFFFFF")
        self.video_label.pack(expand=True, fill="both")

        self.progress_bar = ctk.CTkProgressBar(self.cam_card, height=10, corner_radius=0, 
                                               fg_color="#333333", progress_color="#1A73E8")
        self.progress_bar.pack(side="bottom", fill="x")
        self.progress_bar.set(0)

        self.live_lbl = ctk.CTkLabel(self, text="Waiting for hand...", 
                                     font=("Segoe UI", 16, "bold"), text_color="#1A73E8")
        self.live_lbl.pack(pady=15)

    def _update_slot_visuals(self):
        for i, (slot, lbl) in enumerate(zip(self.digit_slots, self.digit_labels)):
            if i < self.idx:
                slot.configure(fg_color="#27AE60", border_width=0)
                lbl.configure(text=f"{self.otp[i]}", text_color="#FFFFFF")
            elif i == self.idx:
                slot.configure(fg_color="#D6EAF8", border_width=2, border_color="#1A73E8")
                lbl.configure(text="?", text_color="#1A73E8")
            else:
                slot.configure(fg_color="#E8EAED", border_width=0)
                lbl.configure(text="?", text_color="#BDC3C7")

    def activate(self):
        threading.Thread(target=self._async_init, daemon=True).start()

    def _async_init(self):
        if self.recognizer.start_session():
            self.running = True
            threading.Thread(target=self.camera_loop, daemon=True).start()

    def camera_loop(self):
        while self.running:
            frame, digit, confirmed, progress = self.recognizer.get_processed_data()
            if frame is None: continue

            self.after(0, lambda p=progress: self.progress_bar.set(p))

            if digit is not None:
                # Privacy Logic: No numeric feedback
                self.after(0, lambda: self.live_lbl.configure(
                    text="Hand Detected: Analyzing steady gesture...", text_color="#1A73E8"))
                
                if str(digit) == self.otp[self.idx]:
                    if confirmed:
                        if self.idx + 1 == len(self.otp):
                            self.after(0, self._final_step)
                            return
                        else:
                            self.after(0, self._on_digit_match)
            else:
                self.after(0, lambda: self.live_lbl.configure(
                    text="Searching for hands...", text_color="#5F6368"))

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 430))
            self.after(0, lambda im=ctk_img: self.video_label.configure(image=im, text=""))

    def _on_digit_match(self):
        self.idx += 1
        self.recognizer.active_digit = None
        self.recognizer.hold_start_time = 0
        self._update_slot_visuals()

    def _final_step(self):
        self.idx += 1
        self._update_slot_visuals()
        self.after(1000, self.finish)

    def finish(self):
        if not self.running: return
        self.running = False
        self.recognizer.close()
        if self.controller.current_user_data:
            self.controller.current_user_data["status"] = "SUCCESS"
            self.after(0, lambda: self.controller.show_frame("DashboardFrame"))

    def destroy(self):
        self.running = False
        self.recognizer.close()
        super().destroy()