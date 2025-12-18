# streamlit_app.py
# Streamlit version of your VolumeHandControl.py (production-friendly)

import streamlit as st
import cv2
import time
import math
import numpy as np
import handTrackingModule as Htm

# -------- Windows Volume (pycaw) --------
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

devices = AudioUtilities.GetSpeakers()
volume = devices.EndpointVolume



minVol, maxVol, _ = volume.GetVolumeRange()

# -------- Streamlit UI --------
st.set_page_config(page_title="Gesture Volume Control", layout="wide")
st.title("🔊 Hand Gesture Volume Control (Streamlit)")

with st.sidebar:
    st.header("Controls")
    cam_index = st.number_input("Camera Index", 0, 3, 0)
    detection_conf = st.slider("Detection Confidence", 0.3, 0.9, 0.7)
    start = st.toggle("Start Camera")

status = st.empty()
frame_box = st.empty()

# -------- Main Logic --------
if start:
    cap = cv2.VideoCapture(int(cam_index))
    cap.set(3, 640)
    cap.set(4, 480)

    detector = Htm.handDetector(detectionCon=detection_conf)
    pTime = 0

    status.success("Camera Started")

    while start:
        success, img = cap.read()
        if not success:
            status.error("Camera not accessible")
            break

        img = cv2.flip(img, 1)
        img = detector.findHands(img)
        lmList = detector.findPosition(img, draw=False)

        if len(lmList) != 0:
            hand = lmList[0]
            x1, y1 = hand[4][1], hand[4][2]   # Thumb tip
            x2, y2 = hand[8][1], hand[8][2]   # Index tip

            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(img, (x1, y1), 10, (255, 255, 0), cv2.FILLED)
            cv2.circle(img, (x2, y2), 10, (255, 255, 0), cv2.FILLED)
            cv2.line(img, (x1, y1), (x2, y2), (255, 255, 0), 3)
            cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

            length = math.hypot(x2 - x1, y2 - y1)

            vol = np.interp(length, [30, 250], [minVol, maxVol])
            volPer = np.interp(length, [30, 250], [0, 100])
            volBar = np.interp(length, [30, 250], [375, 125])

            volume.SetMasterVolumeLevel(vol, None)

            # UI overlay
            cv2.rectangle(img, (30, 125), (65, 375), (255, 0, 255), 3)
            cv2.rectangle(img, (30, int(volBar)), (65, 375), (255, 0, 255), cv2.FILLED)
            cv2.putText(img, f"{int(volPer)}%", (30, 420),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 255), 2)

        # FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime) if cTime != pTime else 0
        pTime = cTime
        cv2.putText(img, f"FPS: {int(fps)}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        frame_box.image(img, channels="BGR", use_container_width=True)

    cap.release()
else:
    status.info("Enable 'Start Camera' to run the app")

# -------- Notes --------
# ✔ Uses your existing handTrackingModule.py
# ✔ Works on Windows (pycaw)
# ✔ Streamlit Cloud will NOT allow system volume control
