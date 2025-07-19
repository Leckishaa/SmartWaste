from cvzone.ClassificationModule import Classifier
import cv2
import numpy as np
import sqlite3
import os
import qrcode
from datetime import datetime

#Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'waste.db')
USER_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dashboard', 'current_user.txt'))
print("📂 Reading current user from:", USER_FILE)
MODEL_PATH = 'Resources/converted_keras/keras_model.h5'
LABELS_PATH = 'Resources/converted_keras/labels.txt'
BACKGROUND_IMG = 'Resources/SmartWasteBG.png'
QR_PATH = 'static/qr/system_qr.png'

#Generated QR to go to the login page only work if you put on PythonAnywhere okayyy!
qr = qrcode.make("http://localhost:5000/")
os.makedirs("static/qr", exist_ok=True)
qr.save(QR_PATH)

# Webcam and classifier
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Failed to open webcam.")
    exit()

classifier = Classifier(MODEL_PATH, LABELS_PATH)
imgBackground = cv2.imread(BACKGROUND_IMG)

# Load class labels
with open(LABELS_PATH, "r") as f:
    class_labels = [line.strip() for line in f.readlines()]

#Ensure the upload and database folders exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('database', exist_ok=True)




def get_current_user():
    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            data = f.read().strip().split(",")
            if len(data) == 3:
                print(f"👤 Current user loaded: {data}")
                return data[0], data[1], data[2]  # student_id, name, role
            else:
                raise ValueError("Incomplete user data")
    except Exception as e:
        print(f"⚠️ No user found, defaulting to Guest. ({e})")
        return "unknown", "Guest", "student"



#Points mapping but not working sia whyyyyyyyyy:( Lecky change dis
points_map = {
    "plastic": 5,
    "paper": 4,
    "glass": 3,
    "cardboard": 3,
    "tin": 2,
    "general": 1,
    "nothing": 0
}

# not so cute button
button_coords = (1020, 600, 1220, 640)  # (x1, y1, x2, y2)
label = "none"
confidence = 0

# Database hihihi
def save_to_db(filename, user_id, user_name, label, user_type):
    points = points_map.get(label.lower(), 0)  # Correct point distribution
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            student_name TEXT,
            predicted_label TEXT,
            points INTEGER,
            user_type TEXT,
            date_submitted TIMESTAMP
        )
    ''')
    cursor.execute('''
        INSERT INTO submissions (student_id, student_name, predicted_label, points, user_type, date_submitted)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, user_name, label, points, user_type, datetime.now()))
    conn.commit()
    conn.close()


# to click button okayyy
SCALE_X = 0.7
SCALE_Y = 0.7

def click_event(event, x, y, flags, param):
    global label, confidence
    real_x = int(x / SCALE_X)
    real_y = int(y / SCALE_Y)

    if event == cv2.EVENT_LBUTTONDOWN:
        if button_coords[0] <= real_x <= button_coords[2] and button_coords[1] <= real_y <= button_coords[3]:
            # ✅ read current user before saving
            user_id, user_name, user_type = get_current_user()

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            img_path = f'uploads/waste_{timestamp}.jpg'
            cv2.imwrite(img_path, img)

            save_to_db(os.path.basename(img_path), user_id, user_name, label, user_type)
            print(f"🗑️ Captured & saved: {label} ({confidence}%) by {user_type} {user_name}")


# Main loop
print("🟢 Tap 'Capture' on screen to save. Press 'Q' to quit.")

while True:
    success, img = cap.read()
    if not success:
        print("❌ Camera not detected.")
        break

    imgResize = cv2.resize(img, (419, 306))
    prediction, index = classifier.getPrediction(img)

    try:
        label = class_labels[index]
        confidence = round(float(prediction[1]) * 100, 2)
    except Exception as e:
        print("Prediction error:", e)
        continue

    # Display webcam on background
    imgBackground[290:290 + 306, 50:50 + 419] = imgResize

    # Display prediction
    cv2.rectangle(imgBackground, (45, 590), (600, 630), (0, 0, 0), -1)
    cv2.putText(imgBackground, f"{label.upper()} ({confidence}%)", (50, 620),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # to display da QR code hmmmmmm
    qr_img = cv2.imread(QR_PATH)
    if qr_img is not None:
        qr_resized = cv2.resize(qr_img, (150, 150))
        imgBackground[290:440, 1050:1200] = qr_resized

    # Draw capture button next to QR
    cv2.rectangle(imgBackground, (button_coords[0], button_coords[1]), (button_coords[2], button_coords[3]),
                  (0, 255, 0), -1)
    cv2.putText(imgBackground, "Capture", (button_coords[0] + 20, button_coords[1] + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    # Show webcam feed + SmartWasteCam
    cv2.imshow("Live Feed", img)
    imgDisplay = cv2.resize(imgBackground, None, fx=SCALE_X, fy=SCALE_Y)
    cv2.imshow("SmartWasteCam", imgDisplay)

    # Touch/click events for SmartWasteCam
    cv2.setMouseCallback("SmartWasteCam", click_event)

    key = cv2.waitKey(1)
    if key == ord('q'):
        print(" Exiting...")
        break

cap.release()
cv2.destroyAllWindows()










