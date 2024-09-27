import pyaudio
from cvzone.HandTrackingModule import HandDetector
import cv2
import speech_recognition as sr
import pyttsx3
import tkinter as tk
from tkinter import Canvas, Button, Text
from PIL import Image, ImageTk

# Initialize the text-to-speech engine
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 120)

# Initialize the HandDetector class
detector = HandDetector(staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.5, minTrackCon=0.5)
cap = None

def update_message(message):
    """Update the canvas with the given message."""
    text_box.config(state=tk.NORMAL)
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, message)
    text_box.config(state=tk.DISABLED)

def recognize_speech():
    """Function to recognize speech from the microphone."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            update_message("Listening...")
            audio_text = r.listen(source)
            update_message("Recognizing...")
            return r.recognize_google(audio_text)
    except sr.UnknownValueError:
        return "Sorry, I did not understand the audio."
    except sr.RequestError:
        return "Sorry, there was an error with the speech recognition service."

def start_speech_recognition():
    """Start the speech recognition."""
    speech_text = recognize_speech()
    update_message(f"You said: {speech_text}")

def start_camera():
    """Start the webcam capture."""
    global cap
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        update_message("Error: Unable to access the camera.")
        return
    update_message("Camera started. Use gestures!")
    # Set the frame width and height for performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Reduced frame width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Reduced frame height
    update_frame()

def detect_gesture(fingers):
    """Function to detect hand gestures based on finger states."""
    gestures = {
        (1, 0, 0, 0, 0): "Thumbs Up",
        (0, 1, 1, 1, 1): "Peace Sign",
        (1, 1, 1, 1, 1): "All Fingers Up",
        (1, 1, 0, 0, 1): "Good Bye",


    }
    gesture = gestures.get(tuple(fingers), "Unknown Gesture")
    update_message(gesture)

    if gesture != "Unknown Gesture":
        engine.say(gesture)
        engine.runAndWait()

    return gesture

def update_frame():
    """Function to capture frame and update the Tkinter canvas."""
    global cap
    if cap is None or not cap.isOpened():
        return

    success, img = cap.read()
    if not success:
        update_message("Failed to capture image")
        return

    # Resize the image for faster processing
    img = cv2.resize(img, (640, 480))
    hands, img = detector.findHands(img, draw=True, flipType=True)

    if hands:
        hand1 = hands[0]
        fingers1 = detector.fingersUp(hand1)
        detect_gesture(fingers1)

        if len(hands) == 2:
            hand2 = hands[1]
            fingers2 = detector.fingersUp(hand2)
            detect_gesture(fingers2)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    img_tk = ImageTk.PhotoImage(image=img_pil)

    camera_canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
    camera_canvas.img_tk = img_tk  # Keep a reference to avoid garbage collection

    window.after(30, update_frame)  # Call this function again after 30ms

def stop_camera():
    """Stop the webcam capture."""
    global cap
    if cap is not None:
        cap.release()
        cap = None
        update_message("Camera stopped.")

def on_stop():
    """Stop the application gracefully."""
    stop_camera()
    window.quit()

# Initialize the main Tkinter window
window = tk.Tk()
window.title("Hand Gesture Recognition")

# Create frames for layout
left_frame = tk.Frame(window)
left_frame.pack(side=tk.LEFT)

right_frame = tk.Frame(window)
right_frame.pack(side=tk.RIGHT)

# Create a canvas to display the video feed
camera_canvas = Canvas(left_frame, width=640, height=480)
camera_canvas.pack()

# Create a text box to display gesture information
text_box = Text(right_frame, height=20, width=50, bg='lightgrey', font=('Arial', 12))
text_box.pack()

# Create buttons
start_button = Button(right_frame, text="Start Speech Recognition", command=start_speech_recognition, font=("Arial", 14))
start_button.pack(pady=5)

camera_button = Button(right_frame, text="Start Camera Capture", command=start_camera, font=("Arial", 14))
camera_button.pack(pady=5)

stop_button = Button(right_frame, text="Stop Application", command=on_stop, font=("Arial", 14))
stop_button.pack(pady=5)

# Start the Tkinter main loop
window.mainloop()

# Release the video capture when the window is closed
if cap is not None:
    cap.release()
cv2.destroyAllWindows()
