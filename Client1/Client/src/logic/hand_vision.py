import time, cv2, numpy as np, mediapipe as mp

class HandDigitRecognizer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.cap = None
        self.landmarker = None

    def start_session(self):
        """Loads AI and Hardware on-demand."""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened(): return False
            
            self.landmarker = mp.tasks.vision.HandLandmarker.create_from_options(
                mp.tasks.vision.HandLandmarkerOptions(
                    base_options=mp.tasks.BaseOptions(model_asset_path=self.model_path),
                    running_mode=mp.tasks.vision.RunningMode.VIDEO,
                    num_hands=2,
                    min_hand_detection_confidence=0.5
                )
            )
            self.start_time = time.time()
            return True
        except: return False

    def get_frame(self):
        if not self.cap or not self.cap.isOpened(): return None, None
        success, frame = self.cap.read()
        if not success: return None, None

        frame = cv2.flip(frame, 1) 
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        ts = int((time.time() - self.start_time) * 1000)
        result = self.landmarker.detect_for_video(mp_image, ts)

        digit = 0
        if result.hand_landmarks:
            for i, hand_lms in enumerate(result.hand_landmarks):
                handed = "Right"
                if result.handedness and len(result.handedness) > i:
                    handed = result.handedness[i][0].category_name
                
                digit += self._count_fingers(hand_lms, handed)

                # Visual Feedback: Draw dots on knuckles
                h, w, _ = frame.shape
                for p in hand_lms:
                    cv2.circle(frame, (int(p.x * w), int(p.y * h)), 2, (0, 255, 0), -1)

        return frame, digit

    def _count_fingers(self, lms, handedness):
        fingers = []
        # Thumb logic
        if handedness == "Left":
            fingers.append(1 if lms[4].x > lms[3].x else 0)
        else:
            fingers.append(1 if lms[4].x < lms[3].x else 0)
        # Finger logic
        for tip, pip in zip([8, 12, 16, 20], [6, 10, 14, 18]):
            fingers.append(1 if lms[tip].y < lms[pip].y else 0)
        return sum(fingers)

    def close(self):
        if self.cap: self.cap.release()
        if self.landmarker: self.landmarker.close()
        self.cap = self.landmarker = None