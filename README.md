Eye Lock System (AI Drowsiness Detection)
📌 Project Overview

This project is an AI-powered desktop safety system built using Python, OpenCV, and MediaPipe.

The application continuously monitors the user's eyes through a webcam.

Features
Detects whether both eyes are open or closed
Starts warning alerts if eyes remain closed for 5 seconds
Plays:
3 warning beeps
each beep lasts 2 seconds
1 second gap between beeps
Cancels lock immediately if the user opens eyes during alerts
Locks desktop if eyes remain closed during all alerts
Voice command support:
Say close to exit application
Real-time webcam interface
Cross-platform lock support via utils.py
