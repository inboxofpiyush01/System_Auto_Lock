import ctypes
import os
import platform

def lock_system():
    system = platform.system()

    if system == "Windows":
        ctypes.windll.user32.LockWorkStation()

    elif system == "Darwin":  # macOS
        os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")

    elif system == "Linux":
        os.system("gnome-screensaver-command -l")