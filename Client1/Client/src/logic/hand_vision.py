import time, cv2, numpy as np, mediapipe as mp
# Use Absolute Import from the project root
from config.client_settings import (
    REQUIRED_HANDS, 
    GESTURE_HOLD_SECONDS,
    MIN_DETECTION_CONFIDENCE
)

class HandDigitRecognizer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.cap = None
        self.landmarker = None
        
        # State variables
        self.active_digit = None
        self.hold_start_time = 0
        self.required_hold = GESTURE_HOLD_SECONDS
        self.session_start = 0

    def start_session(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened(): return False
            
            options = mp.tasks.vision.HandLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=self.model_path),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_hands=REQUIRED_HANDS,
                min_hand_detection_confidence=MIN_DETECTION_CONFIDENCE
            )
            self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)
            self.session_start = time.time()
            return True
        except: return False

    def get_processed_data(self):
        if not self.cap or not self.cap.isOpened() or not self.landmarker: 
            return None, None, False, 0
            
        success, frame = self.cap.read()
        if not success: return None, None, False, 0

        # No Mirroring for natural interaction
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int((time.time() - self.session_start) * 1000)
        
        try:
            result = self.landmarker.detect_for_video(mp_image, ts)
        except: return frame, None, False, 0

        total_digit = 0
        hand_detected = False

        if result.hand_landmarks:
            hand_detected = True
            for i, hand_lms in enumerate(result.hand_landmarks):
                # Correctly accessing handedness
                handedness = result.handedness[i][0].category_name
                total_digit += self._count_fingers(hand_lms, handedness)
                
                h, w, _ = frame.shape
                for p in hand_lms:
                    cv2.circle(frame, (int(p.x * w), int(p.y * h)), 3, (0, 255, 0), -1)

        confirmed = False
        progress = 0
        current_val = total_digit if hand_detected else None

        if current_val is not None:
            if current_val == self.active_digit:
                elapsed = time.time() - self.hold_start_time
                progress = min(elapsed / self.required_hold, 1.0)
                if elapsed >= self.required_hold:
                    confirmed = True
            else:
                self.active_digit = current_val
                self.hold_start_time = time.time()
        else:
            self.active_digit = None
            self.hold_start_time = 0

        return frame, current_val, confirmed, progress

    def _count_fingers(self, lms, handedness):
        fingers = []
        if handedness == "Left":
            fingers.append(1 if lms[4].x > lms[3].x else 0)
        else:
            fingers.append(1 if lms[4].x < lms[3].x else 0)
        for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
            fingers.append(1 if lms[tip].y < lms[pip].y else 0)
        return sum(fingers)

    def close(self):
        try:
            if self.cap: self.cap.release()
            if self.landmarker: self.landmarker.close()
            self.cap = self.landmarker = None
        except: pass