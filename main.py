import cv2
import time
import numpy as np
import mediapipe as mp
import winsound
import threading
import speech_recognition as sr

from utils import lock_system

# ==========================================
# MEDIAPIPE SETUP
# ==========================================

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ==========================================
# EYE LANDMARKS
# ==========================================

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ==========================================
# SETTINGS
# ==========================================

EYE_CLOSED_THRESHOLD = 0.20

# Eyes closed duration before alert starts
LOCK_TRIGGER_TIME = 5

running = True

closed_start_time = None
warning_started = False

# ==========================================
# EYE ASPECT RATIO FUNCTION
# ==========================================

def eye_aspect_ratio(landmarks, eye_points, w, h):

    points = []

    for i in eye_points:

        x = int(landmarks[i].x * w)
        y = int(landmarks[i].y * h)

        points.append((x, y))

    # Vertical distances
    A = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    B = np.linalg.norm(np.array(points[2]) - np.array(points[4]))

    # Horizontal distance
    C = np.linalg.norm(np.array(points[0]) - np.array(points[3]))

    ear = (A + B) / (2.0 * C)

    return ear


# ==========================================
# CHECK IF BOTH EYES ARE CLOSED
# ==========================================

def are_eyes_closed(landmarks, w, h):

    left_ear = eye_aspect_ratio(
        landmarks,
        LEFT_EYE,
        w,
        h
    )

    right_ear = eye_aspect_ratio(
        landmarks,
        RIGHT_EYE,
        w,
        h
    )

    both_closed = (
        left_ear < EYE_CLOSED_THRESHOLD and
        right_ear < EYE_CLOSED_THRESHOLD
    )

    avg_ear = (left_ear + right_ear) / 2

    return both_closed, avg_ear


# ==========================================
# WARNING ALERT + LOCK SYSTEM
# ==========================================

def warning_and_lock(cap):

    global running

    print("\nWARNING ALERT STARTED")

    # New FaceMesh for alert phase
    local_face_mesh = mp_face_mesh.FaceMesh(
        refine_landmarks=True
    )

    for i in range(3):

        print(f"Alert Beep {i+1}/3")

        # ==========================================
        # PLAY 2 SECOND BEEP
        # ==========================================

        winsound.Beep(1000, 2000)

        # ==========================================
        # CHECK IF USER WOKE UP
        # ==========================================

        ret, frame = cap.read()

        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = local_face_mesh.process(rgb)

        if result.multi_face_landmarks:

            for face_landmarks in result.multi_face_landmarks:

                landmarks = face_landmarks.landmark

                both_closed, _ = are_eyes_closed(
                    landmarks,
                    w,
                    h
                )

                # ==========================================
                # USER OPENED EYES -> CANCEL LOCK
                # ==========================================

                if not both_closed:

                    print("Eyes reopened. Lock cancelled.\n")

                    return False

        # ==========================================
        # WAIT 1 SECOND BEFORE NEXT BEEP
        # ==========================================

        if i < 2:
            time.sleep(1)

    # ==========================================
    # FINAL LOCK
    # ==========================================

    print("Eyes remained closed.")
    print("LOCKING SYSTEM NOW\n")

    lock_system()

    return True


# ==========================================
# VOICE COMMAND LISTENER
# ==========================================

def voice_listener():

    global running

    recognizer = sr.Recognizer()

    microphone = sr.Microphone()

    while running:

        try:

            with microphone as source:

                recognizer.adjust_for_ambient_noise(source)

                print("Listening for 'close' command...")

                audio = recognizer.listen(source)

            command = recognizer.recognize_google(audio).lower()

            print("You said:", command)

            # ==========================================
            # EXIT APPLICATION
            # ==========================================

            if "close" in command:

                print("Exit command detected")

                running = False

                break

        except sr.UnknownValueError:
            pass

        except Exception as e:
            print("Voice Error:", e)


# ==========================================
# START VOICE THREAD
# ==========================================

voice_thread = threading.Thread(
    target=voice_listener
)

voice_thread.daemon = True

voice_thread.start()

# ==========================================
# START CAMERA
# ==========================================

cap = cv2.VideoCapture(0)

print("\n===================================")
print("Eye Lock System Started")
print("Close both eyes for 5 sec to trigger alert")
print("Say 'close' to exit")
print("===================================\n")

# ==========================================
# MAIN LOOP
# ==========================================

while running:

    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    result = face_mesh.process(rgb)

    status = "Eyes Open"

    avg_ear = 0

    if result.multi_face_landmarks:

        for face_landmarks in result.multi_face_landmarks:

            landmarks = face_landmarks.landmark

            both_closed, avg_ear = are_eyes_closed(
                landmarks,
                w,
                h
            )

            # ==========================================
            # DISPLAY EAR
            # ==========================================

            cv2.putText(
                frame,
                f"EAR: {avg_ear:.2f}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            # ==========================================
            # BOTH EYES CLOSED
            # ==========================================

            if both_closed:

                status = "Both Eyes Closed"

                if closed_start_time is None:

                    closed_start_time = time.time()

                elapsed = time.time() - closed_start_time

                cv2.putText(
                    frame,
                    f"Eyes Closed: {elapsed:.1f}s",
                    (20, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2
                )

                # ==========================================
                # START ALERT SYSTEM
                # ==========================================

                if elapsed >= LOCK_TRIGGER_TIME and not warning_started:

                    warning_started = True

                    cv2.putText(
                        frame,
                        "WARNING ALERT ACTIVE",
                        (20, 140),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )

                    cv2.imshow(
                        "Eye Lock System",
                        frame
                    )

                    cv2.waitKey(1)

                    # Start alert + conditional lock
                    warning_and_lock(cap)

                    closed_start_time = None
                    warning_started = False

            else:

                status = "Eyes Open"

                closed_start_time = None
                warning_started = False

            # ==========================================
            # DISPLAY STATUS
            # ==========================================

            cv2.putText(
                frame,
                status,
                (20, 190),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 0),
                2
            )

    # ==========================================
    # SHOW WINDOW
    # ==========================================

    cv2.imshow(
        "Eye Lock System",
        frame
    )

    key = cv2.waitKey(1)

    if key == ord('q'):

        running = False
        break

# ==========================================
# CLEANUP
# ==========================================

running = False

cap.release()

cv2.destroyAllWindows()

print("Application Closed")