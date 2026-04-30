"""
system_commands.py — PC Automation Commands for Jarvis
Handles app launching, screenshots, typing, and system actions
using os (for launching apps) and pyautogui (for GUI automation).
"""

# os: run system-level commands like opening apps and shutting down
import os

# time: add delays (e.g., countdown before shutdown)
import time

# subprocess: launch programs without blocking the assistant
import subprocess

# pyautogui: automate keyboard/mouse actions (typing, screenshots)
import pyautogui

# Import the speak function so Jarvis can respond before executing
# Uses sys.path hack so this file works both as a module AND when run directly
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from speech.speaker import speak


def execute_command(command):
    """
    Takes a voice command string and executes the matching action.
    Uses simple if-elif keyword matching for beginner readability.

    Args:
        command (str): The recognized voice command in lowercase.

    Returns:
        bool: True if a command was matched, False otherwise.
    """

    # ----------------------------------------------------------------
    #  APP LAUNCHING
    # ----------------------------------------------------------------

    if "open chrome" in command:
        speak("Opening Google Chrome.")
        # os.startfile opens the default associated program on Windows
        os.startfile("chrome")
        return True

    elif "open notepad" in command:
        speak("Opening Notepad.")
        os.startfile("notepad")
        return True

    elif "open calculator" in command:
        speak("Opening Calculator.")
        subprocess.Popen("calc")
        return True

    elif "open vs code" in command or "open vscode" in command:
        speak("Opening Visual Studio Code.")
        # "code" is the CLI command for VS Code (must be in PATH)
        os.system("code")
        return True

    elif "open file explorer" in command or "open explorer" in command:
        speak("Opening File Explorer.")
        os.startfile("explorer")
        return True

    elif "open command prompt" in command or "open cmd" in command:
        speak("Opening Command Prompt.")
        os.system("start cmd")
        return True

    # ----------------------------------------------------------------
    #  SCREENSHOT
    # ----------------------------------------------------------------

    elif "take screenshot" in command or "screenshot" in command:
        speak("Taking a screenshot.")

        # Capture the entire screen
        screenshot = pyautogui.screenshot()

        # Save with a timestamp so filenames don't collide
        filename = f"screenshot_{int(time.time())}.png"
        screenshot.save(filename)

        speak(f"Screenshot saved as {filename}.")
        return True

    # ----------------------------------------------------------------
    #  TYPING (dictation mode)
    # ----------------------------------------------------------------

    elif "type" in command:
        # Extract everything after the word "type" as the text to type
        # Example: "type hello world" → text_to_type = "hello world"
        text_to_type = command.split("type", 1)[1].strip()

        if text_to_type:
            speak(f"Typing: {text_to_type}")

            # Small delay to let the user click into the target window
            time.sleep(2)

            # pyautogui.typewrite only supports basic ASCII characters
            # pyautogui.write handles Unicode and is more reliable
            pyautogui.write(text_to_type, interval=0.05)  # 50ms between each key
        else:
            speak("Please tell me what to type.")

        return True

    # ----------------------------------------------------------------
    #  SYSTEM CONTROLS
    # ----------------------------------------------------------------

    elif "shutdown" in command or "shut down" in command:
        speak("WARNING: The system will shut down in 10 seconds.")
        speak("Say 'cancel' or press Ctrl+C to abort.")

        # Safety countdown so the user can cancel if it was accidental
        for i in range(10, 0, -1):
            print(f"Shutting down in {i}...")
            time.sleep(1)

        # Windows shutdown command: /s = shutdown, /t 0 = immediately
        os.system("shutdown /s /t 0")
        return True

    elif "restart" in command:
        speak("WARNING: The system will restart in 10 seconds.")

        for i in range(10, 0, -1):
            print(f"Restarting in {i}...")
            time.sleep(1)

        # /r = restart
        os.system("shutdown /r /t 0")
        return True

    elif "lock" in command or "lock screen" in command:
        speak("Locking the screen.")
        # rundll32 call to lock the Windows workstation
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return True

    elif "log out" in command or "sign out" in command:
        speak("Logging out in 5 seconds.")
        time.sleep(5)
        os.system("shutdown /l")
        return True

    # ----------------------------------------------------------------
    #  NO MATCH FOUND
    # ----------------------------------------------------------------

    else:
        # Return False so the caller knows the command wasn't handled here
        return False
