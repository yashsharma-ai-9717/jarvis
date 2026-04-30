"""
jarvis.py — Voice-Controlled PC Automation Assistant
=====================================================
A single-file version that combines all modules:
  • Speech Recognition (listen)
  • Text-to-Speech   (speak)
  • Command Execution (execute_command)
  • Main Loop         (greeting + listen → parse → act → respond)

Run:  python jarvis.py
Exit: say "stop jarvis" or "exit" or "goodbye"
"""

# ========================== IMPORTS ==========================

# speech_recognition: captures mic audio and converts to text via Google API
import speech_recognition as sr

# pyttsx3: offline text-to-speech engine (no internet needed)
import pyttsx3

# os: launch apps & system commands (shutdown, lock, etc.)
import os

# subprocess: start programs without blocking the assistant
import subprocess

# time: delays for safety countdowns and typing speed
import time

# datetime: get current hour for time-based greeting
import datetime

# pyautogui: GUI automation — screenshots, typing, mouse control
import pyautogui

# webbrowser: open URLs in the default browser
import webbrowser

# getpass: securely read password input without showing it on screen
import getpass

# psutil: system info — battery, CPU, RAM usage
import psutil

# platform: OS and hardware details
import platform

# random: pick random jokes / responses
import random

# ctypes: Windows API calls (volume control, etc.)
import ctypes

# shutil: high-level file operations (disk usage)
import shutil

# pathlib: modern path handling for file/folder operations
from pathlib import Path

# json: read/write memory data to a JSON file
import json

# threading: run timers, reminders, and pomodoro in the background
import threading

# socket: get local network IP address without any API
import socket

# re: regular expressions for parsing durations and file types
import re

# glob: (via pathlib) file searching is already available
# No extra import needed — pathlib.Path.rglob handles it.


# ======================== CONFIG ============================
# Set your password here (change it to whatever you like)
JARVIS_PASSWORD = "jarvis123"

# Maximum login attempts before Jarvis locks out
MAX_LOGIN_ATTEMPTS = 3


# ======================== TTS ENGINE ========================
# Initialize the text-to-speech engine ONCE at startup

engine = pyttsx3.init()

# Get available system voices
voices = engine.getProperty("voices")

# voices[0] = male, voices[1] = female (change index to switch)
engine.setProperty("voice", voices[0].id)

# 170 words per minute — natural conversational speed
engine.setProperty("rate", 170)

# Full volume (range: 0.0 to 1.0)
engine.setProperty("volume", 1.0)


# ======================== SPEAK =============================

def speak(text):
    """
    Prints the text to console and speaks it aloud.

    Args:
        text (str): The message Jarvis should say.
    """
    print(f"Jarvis: {text}")
    engine.say(text)
    engine.runAndWait()


# ======================== LISTEN ============================

def listen():
    """
    Captures audio from the microphone and converts it to
    a lowercase text string using Google Speech Recognition.

    Returns:
        str or None: Recognized command in lowercase, or None on failure.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("\nListening...")

        # Calibrate for 1 second of ambient noise
        recognizer.adjust_for_ambient_noise(source, duration=1)

        # Seconds of silence before a phrase is considered complete
        recognizer.pause_threshold = 1

        try:
            # timeout=5  → wait up to 5s for speech to start
            # phrase_time_limit=10 → max 10s per spoken phrase
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Recognizing...")

            # Send audio to Google's free speech API
            # Change "en-in" to "en-us" for US English
            command = recognizer.recognize_google(audio, language="en-in")
            command = command.lower()
            print(f"You said: {command}")
            return command

        except sr.WaitTimeoutError:
            # No speech detected within the timeout
            print("No speech detected. Timed out.")
            return None

        except sr.UnknownValueError:
            # Speech was heard but not understood
            print("Sorry, I could not understand that.")
            return None

        except sr.RequestError as e:
            # Network/API issue
            print(f"Speech Recognition service error: {e}")
            return None

        except Exception as e:
            print(f"Unexpected error: {e}")
            return None


# =================== CONFIRMATION ==========================

def confirm(action_name):
    """
    Asks the user to verbally confirm a dangerous action.
    Listens for 'yes' or 'no' via the microphone.

    Args:
        action_name (str): Description of the action (e.g., "shutdown").

    Returns:
        bool: True if user confirmed, False otherwise.
    """
    speak(f"Are you sure you want to {action_name}? Say yes or no.")

    # Listen for the user's confirmation
    response = listen()

    if response and "yes" in response:
        return True
    else:
        speak(f"{action_name.capitalize()} cancelled.")
        return False


# =================== PASSWORD PROTECTION ====================

def authenticate():
    """
    Asks the user for a password before starting Jarvis.
    Allows up to MAX_LOGIN_ATTEMPTS tries.

    Returns:
        bool: True if authentication succeeded, False if locked out.
    """
    print("\n" + "=" * 45)
    print("   JARVIS — Voice-Controlled PC Assistant")
    print("=" * 45)
    print(f"\nPlease enter your password to start Jarvis.")
    print(f"(You have {MAX_LOGIN_ATTEMPTS} attempts)\n")

    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        # getpass hides the password as the user types
        password = getpass.getpass(f"Attempt {attempt}/{MAX_LOGIN_ATTEMPTS} — Password: ")

        if password == JARVIS_PASSWORD:
            print("Access granted!\n")
            return True
        else:
            remaining = MAX_LOGIN_ATTEMPTS - attempt
            if remaining > 0:
                print(f"Wrong password. {remaining} attempt(s) remaining.\n")
            else:
                print("Too many failed attempts. Jarvis is locked.")
                return False

    return False


# =================== HELPER: SMART MATCH ====================

def _match(command, keywords):
    """
    Returns True if ANY keyword/phrase from the list is found
    inside the command string. Keeps matching logic DRY.

    Args:
        command  (str):  The user's voice command (lowercase).
        keywords (list): List of trigger phrases to check.

    Returns:
        bool
    """
    return any(kw in command for kw in keywords)


# =================== MEMORY SYSTEM ===========================
# Stores user preferences and facts in a JSON file so Jarvis
# can "remember" things across sessions.

# Path to the memory file (sits next to jarvis.py)
MEMORY_FILE = Path(__file__).parent / "memory.json"

# Path to the notes file (quick notes feature)
NOTES_FILE = Path(__file__).parent / "notes.txt"

# Path to the command history log
HISTORY_FILE = Path(__file__).parent / "history.log"


def load_memory():
    """
    Loads the memory dictionary from memory.json.
    If the file doesn't exist yet, returns an empty dict
    and creates the file automatically.

    Returns:
        dict: All stored key-value memories.
    """
    # If file doesn't exist, create it with an empty dict
    if not MEMORY_FILE.exists():
        save_memory({})
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # File is corrupted or unreadable — start fresh
        return {}


def save_memory(data):
    """
    Saves the memory dictionary to memory.json.
    Overwrites the entire file with the updated data.

    Args:
        data (dict): The full memory dictionary to save.
    """
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        # indent=4 makes the file human-readable
        json.dump(data, f, indent=4, ensure_ascii=False)


def remember_information(command):
    """
    Extracts a key-value pair from a 'remember that...' command
    and saves it to memory.json.

    Supported phrases:
        "remember that my name is Yash"
        "remember that my favorite browser is Chrome"
        "remember that I like Python"

    Args:
        command (str): The full voice command in lowercase.
    """
    # Remove the trigger phrase to get the raw fact
    # e.g. "remember that my name is yash" → "my name is yash"
    raw = ""
    for prefix in ["remember that ", "remember "]:
        if prefix in command:
            raw = command.split(prefix, 1)[1].strip()
            break

    if not raw:
        speak("Please tell me what to remember.")
        return

    # Try to split on " is " → key = "my name", value = "yash"
    if " is " in raw:
        key, value = raw.split(" is ", 1)
        key = key.strip()
        value = value.strip()

    # Handle "I like Python" → key = "i like", value = "python"
    elif " like " in raw:
        parts = raw.split(" like ", 1)
        key = "i like"
        value = parts[1].strip()

    else:
        # Fallback: store the whole phrase under a generic key
        key = "note"
        value = raw

    # Load existing memory, add the new entry, and save
    memory = load_memory()
    memory[key] = value
    save_memory(memory)

    speak(f"I will remember that {key} is {value}.")


def recall_information(command):
    """
    Looks up a stored memory based on the user's question.

    Supported phrases:
        "what is my name"
        "what is my favorite browser"
        "what do I like"
        "do you remember my name"

    Args:
        command (str): The full voice command in lowercase.
    """
    memory = load_memory()

    # If memory is completely empty
    if not memory:
        speak("I don't have any memories stored yet. "
              "You can say 'remember that' followed by a fact.")
        return

    # Extract the key the user is asking about
    # "what is my name" → key = "my name"
    # "what is my favorite browser" → key = "my favorite browser"
    search_key = ""
    for prefix in ["what is ", "what's ", "do you remember ",
                   "tell me ", "what do "]:
        if prefix in command:
            search_key = command.split(prefix, 1)[1].strip()
            # Remove trailing question marks
            search_key = search_key.rstrip("?")
            break

    # Special case: "what do i like" → look for key "i like"
    if "what do i like" in command or "what do you know about" in command:
        search_key = "i like"

    if not search_key:
        # If we can't parse the question, list all memories
        speak("Here's everything I remember:")
        for key, value in memory.items():
            speak(f"{key} is {value}.")
        return

    # Search for the key in memory (flexible matching)
    # First try exact match, then partial match
    if search_key in memory:
        speak(f"Your {search_key} is {memory[search_key]}.")
    else:
        # Try partial matching: "name" matches "my name"
        found = False
        for key, value in memory.items():
            if search_key in key or key in search_key:
                speak(f"Your {key} is {value}.")
                found = True
                break

        if not found:
            speak(f"I don't have that information yet. "
                  f"You can say 'remember that {search_key} is' "
                  f"followed by the answer.")


def forget_information(command):
    """
    Removes a specific memory or clears all memories.

    Supported phrases:
        "forget my name"
        "forget everything"
        "clear memory"

    Args:
        command (str): The full voice command in lowercase.
    """
    memory = load_memory()

    # Clear all memories
    if _match(command, ["forget everything", "clear memory", "clear all memory",
                        "erase memory", "delete all memory"]):
        if confirm("erase all my memories"):
            save_memory({})
            speak("All memories have been cleared.")
        return

    # Forget a specific item: "forget my name" → key = "my name"
    for prefix in ["forget ", "delete memory "]:
        if prefix in command:
            key = command.split(prefix, 1)[1].strip()
            break
    else:
        key = ""

    if not key:
        speak("Please tell me what to forget.")
        return

    # Try exact match, then partial
    if key in memory:
        del memory[key]
        save_memory(memory)
        speak(f"Done. I've forgotten {key}.")
    else:
        found = False
        for mem_key in list(memory.keys()):
            if key in mem_key or mem_key in key:
                del memory[mem_key]
                save_memory(memory)
                speak(f"Done. I've forgotten {mem_key}.")
                found = True
                break
        if not found:
            speak(f"I don't have any memory about '{key}'.")


# =================== TIMER & REMINDERS =======================

def _timer_callback(seconds, label):
    """Background callback: sleeps then announces timer is done."""
    time.sleep(seconds)
    speak(f"Timer complete! {label} is up.")


def set_timer(command):
    """
    Parses a voice command to set a countdown timer.
    Runs in a background thread so Jarvis keeps listening.

    Supported phrases:
        "set a timer for 5 minutes"
        "timer 30 seconds"
        "set timer for 2 hours"
    """
    numbers = re.findall(r'(\d+)', command)
    if not numbers:
        speak("Please specify a duration. For example: set a timer for 5 minutes.")
        return

    duration = int(numbers[0])

    if "hour" in command:
        seconds = duration * 3600
        label = f"{duration} hour"
    elif "second" in command:
        seconds = duration
        label = f"{duration} second"
    else:  # default to minutes
        seconds = duration * 60
        label = f"{duration} minute"

    speak(f"Setting a {label} timer. I'll let you know when it's done.")
    t = threading.Thread(target=_timer_callback, args=(seconds, label), daemon=True)
    t.start()


def _reminder_callback(seconds, message):
    """Background callback: sleeps then speaks the reminder."""
    time.sleep(seconds)
    speak(f"Reminder! {message}")


def set_reminder(command):
    """
    Parses a voice command to set a reminder.
    Runs in a background thread.

    Supported phrases:
        "remind me to call mom in 30 minutes"
        "remind me to drink water in 1 hour"
        "reminder to stretch in 10 minutes"
    """
    match = re.search(
        r'remind(?:er)?\s*(?:me)?\s*(?:to)?\s+(.+?)\s+in\s+(\d+)\s*(minute|minutes|hour|hours|second|seconds)',
        command
    )
    if match:
        task = match.group(1).strip()
        duration = int(match.group(2))
        unit = match.group(3)

        if "hour" in unit:
            seconds = duration * 3600
        elif "second" in unit:
            seconds = duration
        else:
            seconds = duration * 60

        speak(f"I'll remind you to {task} in {duration} {unit}.")
        t = threading.Thread(target=_reminder_callback, args=(seconds, task), daemon=True)
        t.start()
    else:
        speak("Please say something like: remind me to call mom in 30 minutes.")


# =================== NOTES SYSTEM ============================

def save_note(command):
    """
    Saves a quick note to notes.txt with a timestamp.

    Supported phrases:
        "take a note buy groceries"
        "note down call dentist tomorrow"
        "save note meeting at 3 pm"
    """
    note_text = ""
    for prefix in ["take a note ", "note down ", "save note ",
                   "write down ", "make a note "]:
        if prefix in command:
            note_text = command.split(prefix, 1)[1].strip()
            break

    if not note_text:
        speak("What should I note down?")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(NOTES_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {note_text}\n")

    speak(f"Note saved: {note_text}")


def read_notes():
    """Reads the last 5 saved notes aloud."""
    if not NOTES_FILE.exists():
        speak("You don't have any notes yet.")
        return

    with open(NOTES_FILE, "r", encoding="utf-8") as f:
        notes = f.readlines()

    if not notes:
        speak("Your notes file is empty.")
        return

    speak(f"You have {len(notes)} notes. Here are the latest:")
    for note in notes[-5:]:
        speak(note.strip())


def clear_notes():
    """Deletes all saved notes."""
    if NOTES_FILE.exists():
        NOTES_FILE.unlink()
    speak("All notes have been cleared.")


# =================== COMMAND HISTORY =========================

def log_command(command):
    """Appends a command to history.log with a timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {command}\n")


def show_history():
    """Reads and speaks the last 5 commands from history."""
    if not HISTORY_FILE.exists():
        speak("No command history yet.")
        return

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        speak("No command history yet.")
        return

    count = min(5, len(lines))
    speak(f"Your last {count} commands:")
    for line in lines[-5:]:
        speak(line.strip())


def clear_history():
    """Deletes the command history log."""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    speak("Command history cleared.")


# =================== SYSTEM UTILITIES ========================

def get_local_ip():
    """
    Returns the local network IP address by briefly
    connecting a UDP socket (no data is actually sent).
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Could not determine"


def get_wifi_status():
    """
    Checks Wi-Fi connection status using the Windows
    'netsh wlan show interfaces' command (no API needed).
    """
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        if "connected" in output.lower():
            for line in output.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    ssid = line.split(":", 1)[1].strip()
                    return f"Connected to {ssid}"
            return "Connected to Wi-Fi"
        else:
            return "Not connected to Wi-Fi"
    except Exception:
        return "Could not check Wi-Fi status"


def get_disk_usage():
    """
    Returns disk usage stats for the C:\\ drive
    using shutil (no API needed).
    """
    usage = shutil.disk_usage("C:\\")
    total_gb = round(usage.total / (1024 ** 3), 1)
    used_gb = round(usage.used / (1024 ** 3), 1)
    free_gb = round(usage.free / (1024 ** 3), 1)
    percent = round((usage.used / usage.total) * 100, 1)
    return total_gb, used_gb, free_gb, percent


def get_uptime():
    """
    Returns how long the PC has been running since last boot
    using psutil (no API needed).
    """
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours} hours and {minutes} minutes"


def kill_process(command):
    """
    Kills a running process by common name.
    Maps friendly names ("chrome") to executable names ("chrome.exe").
    """
    app_name = ""
    for prefix in ["close ", "kill ", "end ", "stop process ", "force close "]:
        if prefix in command:
            app_name = command.split(prefix, 1)[1].strip()
            break

    if not app_name:
        speak("Which application should I close?")
        return

    # Common friendly-name → process-name mapping
    process_map = {
        "chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calculatorapp.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "powerpoint": "powerpnt.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe",
        "task manager": "taskmgr.exe",
        "spotify": "spotify.exe",
        "discord": "discord.exe",
        "vlc": "vlc.exe",
        "vs code": "code.exe",
        "vscode": "code.exe",
    }

    proc_name = process_map.get(app_name.lower(), f"{app_name}.exe")

    killed = False
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == proc_name.lower():
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if killed:
        speak(f"{app_name} has been closed.")
    else:
        speak(f"Could not find {app_name} running.")


def find_files(command):
    """
    Searches Desktop, Documents, and Downloads for files
    matching a type (pdf, txt, etc.) using pathlib — no API.

    Supported phrases:
        "find pdf files"
        "search for txt files"
        "find all png files"
    """
    ext_match = re.search(
        r'(pdf|txt|docx?|xlsx?|pptx?|jpg|jpeg|png|gif|mp3|mp4|py|csv|zip|rar)\b',
        command
    )
    if ext_match:
        extension = ext_match.group(1)
    else:
        speak("Which file type should I search for? For example: find pdf files.")
        return

    search_dirs = [
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Downloads",
    ]

    found_files = []
    for search_dir in search_dirs:
        if search_dir.exists():
            found_files.extend(search_dir.rglob(f"*.{extension}"))

    if found_files:
        speak(f"Found {len(found_files)} {extension} files. Here are up to 10:")
        for f in found_files[:10]:
            speak(f"{f.name} — in {f.parent.name}")
    else:
        speak(f"No {extension} files found in Desktop, Documents, or Downloads.")


# =================== CLIPBOARD (no pip install) ==============

def copy_to_clipboard(text):
    """
    Copies text to the Windows clipboard using PowerShell.
    No third-party library needed.
    """
    try:
        # Escape single quotes for PowerShell
        safe_text = text.replace("'", "''")
        subprocess.run(
            ["powershell", "-command", f"Set-Clipboard -Value '{safe_text}'"],
            capture_output=True, timeout=5
        )
        speak(f"Copied to clipboard: {text}")
    except Exception:
        speak("Failed to copy to clipboard.")


def read_clipboard():
    """
    Reads text from the Windows clipboard using PowerShell.
    No third-party library needed.
    """
    try:
        result = subprocess.run(
            ["powershell", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=5
        )
        text = result.stdout.strip()
        if text:
            speak(f"Clipboard contains: {text}")
        else:
            speak("Clipboard is empty.")
        return text
    except Exception:
        speak("Could not read clipboard.")
        return None


# =================== POMODORO TIMER ==========================

def _pomodoro_worker():
    """Background worker: 25 min focus → 5 min break."""
    speak("Pomodoro started! Focus for 25 minutes.")
    time.sleep(25 * 60)
    speak("Time's up! Take a 5-minute break.")
    time.sleep(5 * 60)
    speak("Break is over! Ready for another Pomodoro?")


def start_pomodoro():
    """Launches a Pomodoro cycle in a background thread."""
    t = threading.Thread(target=_pomodoro_worker, daemon=True)
    t.start()


# =================== STARTUP ROUTINE =========================

def startup_routine():
    """
    A "good morning" routine that gives a quick briefing
    and opens commonly used apps — all offline / no API.
    """
    speak("Starting your morning routine.")

    # Time & date
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    today = datetime.datetime.now().strftime("%A, %B %d, %Y")
    speak(f"It is {current_time} on {today}.")

    # Battery
    battery = psutil.sensors_battery()
    if battery:
        speak(f"Battery is at {battery.percent} percent.")

    # CPU & RAM snapshot
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    speak(f"CPU usage is {cpu} percent. RAM usage is {mem.percent} percent.")

    # Open browser & email
    speak("Opening your browser and email.")
    webbrowser.open("https://mail.google.com")
    time.sleep(2)
    webbrowser.open("https://www.google.com")

    speak("Morning routine complete. What else can I do for you?")


# =================== JOKES LIST ==============================

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "I told my computer I needed a break. Now it won't stop sending me Kit-Kat ads.",
    "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
    "There are only 10 types of people — those who understand binary and those who don't.",
    "A SQL query walks into a bar, sees two tables, and asks: Can I join you?",
    "Why do Java developers wear glasses? Because they can't C sharp.",
    "My code works, I have no idea why. My code doesn't work, I have no idea why.",
    "What's a computer's favorite snack? Microchips!",
]


# =================== COMMAND HANDLER ========================

def execute_command(command):
    """
    Smart command handler — matches the user's voice command to
    an action using flexible keyword matching and executes it.

    Categories:
        🌐 Browser & Web
        💻 System Controls & Info
        📂 File & Folder Operations
        🎵 Media & Volume
        🖱  GUI Automation
        🧠 Personality & Fun

    Args:
        command (str): Recognized voice command in lowercase.

    Returns:
        bool: True if a command was matched, False otherwise.
    """

    # ==========================================================
    #  🌐 BROWSER & WEB
    # ==========================================================

    # --- Open browsers ---
    if _match(command, ["open chrome"]):
        speak("Opening Google Chrome.")
        os.startfile("chrome")

    elif _match(command, ["open edge", "open microsoft edge"]):
        speak("Opening Microsoft Edge.")
        os.startfile("msedge")

    elif _match(command, ["open browser", "open web browser"]):
        speak("Opening your default browser.")
        webbrowser.open("https://www.google.com")

    # --- Open specific websites ---
    elif _match(command, ["open youtube"]):
        speak("Opening YouTube.")
        webbrowser.open("https://www.youtube.com")

    elif _match(command, ["open gmail", "open mail", "open email"]):
        speak("Opening Gmail.")
        webbrowser.open("https://mail.google.com")

    elif _match(command, ["open github"]):
        speak("Opening GitHub.")
        webbrowser.open("https://github.com")

    elif _match(command, ["open linkedin"]):
        speak("Opening LinkedIn.")
        webbrowser.open("https://www.linkedin.com")

    elif _match(command, ["open instagram"]):
        speak("Opening Instagram.")
        webbrowser.open("https://www.instagram.com")

    elif _match(command, ["open whatsapp", "open whatsapp web"]):
        speak("Opening WhatsApp Web.")
        webbrowser.open("https://web.whatsapp.com")

    # --- Web search (flexible: "search for", "google", "look up") ---
    elif _match(command, ["search for", "google", "look up"]):
        # Extract the query from multiple possible phrasings
        for prefix in ["search for", "search google for", "google", "look up"]:
            if prefix in command:
                query = command.split(prefix, 1)[1].strip()
                break
        else:
            query = command  # fallback: use the whole command

        if query:
            speak(f"Searching Google for {query}.")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        else:
            speak("What should I search for?")

    # --- YouTube search / play ---
    elif _match(command, ["play", "search youtube for", "youtube search"]):
        for prefix in ["search youtube for", "youtube search", "play"]:
            if prefix in command:
                query = command.split(prefix, 1)[1].strip()
                break
        else:
            query = ""

        if query:
            speak(f"Searching YouTube for {query}.")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        else:
            speak("What should I play on YouTube?")

    # --- Open any website by name ---
    elif _match(command, ["open website", "go to website"]):
        url = command.split("website", 1)[1].strip()
        if not url.startswith("http"):
            url = "https://" + url
        speak(f"Opening {url}.")
        webbrowser.open(url)

    # ==========================================================
    #  💻 SYSTEM CONTROLS & INFO
    # ==========================================================

    # --- Shutdown (with confirmation) ---
    elif _match(command, ["shutdown", "shut down", "power off"]):
        if confirm("shutdown the system"):
            speak("Shutting down in 10 seconds. Press Ctrl+C to abort.")
            for i in range(10, 0, -1):
                print(f"Shutting down in {i}...")
                time.sleep(1)
            os.system("shutdown /s /t 0")

    # --- Restart (with confirmation) ---
    elif _match(command, ["restart", "reboot"]):
        if confirm("restart the system"):
            speak("Restarting in 10 seconds.")
            for i in range(10, 0, -1):
                print(f"Restarting in {i}...")
                time.sleep(1)
            os.system("shutdown /r /t 0")

    # --- Lock screen ---
    elif _match(command, ["lock computer", "lock screen", "lock my pc", "lock"]):
        speak("Locking the screen.")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    # --- Sleep mode ---
    elif _match(command, ["sleep mode", "put to sleep", "hibernate"]):
        speak("Putting the system to sleep.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    # --- Log out (with confirmation) ---
    elif _match(command, ["log out", "sign out"]):
        if confirm("log out"):
            speak("Logging out in 5 seconds.")
            time.sleep(5)
            os.system("shutdown /l")

    # --- Check battery ---
    elif _match(command, ["battery", "check battery", "battery status", "power status"]):
        battery = psutil.sensors_battery()
        if battery:
            percent = battery.percent
            plugged = "plugged in" if battery.power_plugged else "not plugged in"
            speak(f"Battery is at {percent} percent and {plugged}.")
        else:
            speak("Sorry, I could not detect a battery on this device.")

    # --- Check time ---
    elif _match(command, ["what time", "tell me the time", "check time", "current time"]):
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}.")

    # --- Check date ---
    elif _match(command, ["what is the date", "today's date", "check date", "current date", "what date"]):
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {today}.")

    # --- System info ---
    elif _match(command, ["system info", "system information", "about my computer", "pc info"]):
        sys_info = (
            f"System: {platform.system()} {platform.release()}\n"
            f"Machine: {platform.machine()}\n"
            f"Processor: {platform.processor()}\n"
            f"Computer Name: {platform.node()}"
        )
        print(sys_info)
        speak(f"You are running {platform.system()} {platform.release()} "
              f"on a {platform.machine()} machine named {platform.node()}.")

    # --- CPU usage ---
    elif _match(command, ["cpu usage", "cpu load", "processor usage", "check cpu"]):
        cpu = psutil.cpu_percent(interval=1)
        speak(f"Current CPU usage is {cpu} percent.")

    # --- Memory / RAM usage ---
    elif _match(command, ["memory usage", "ram usage", "check memory", "check ram"]):
        mem = psutil.virtual_memory()
        used_gb = round(mem.used / (1024 ** 3), 1)
        total_gb = round(mem.total / (1024 ** 3), 1)
        speak(f"Memory usage: {used_gb} GB used out of {total_gb} GB. "
              f"That's {mem.percent} percent.")

    # ==========================================================
    #  📂 FILE & FOLDER OPERATIONS
    # ==========================================================

    # --- Open common folders ---
    elif _match(command, ["open downloads"]):
        speak("Opening Downloads folder.")
        downloads_path = str(Path.home() / "Downloads")
        subprocess.Popen(f'explorer "{downloads_path}"')

    elif _match(command, ["open documents"]):
        speak("Opening Documents folder.")
        documents_path = str(Path.home() / "Documents")
        subprocess.Popen(f'explorer "{documents_path}"')

    elif _match(command, ["open desktop"]):
        speak("Opening Desktop folder.")
        # Use shell:Desktop which always resolves correctly (even on OneDrive)
        subprocess.Popen('explorer shell:Desktop')

    # --- Create new folder ---
    elif _match(command, ["create new folder", "make new folder", "create folder"]):
        # Extract folder name: "create new folder test" → "test"
        for prefix in ["create new folder", "make new folder", "create folder"]:
            if prefix in command:
                folder_name = command.split(prefix, 1)[1].strip()
                break
        else:
            folder_name = ""

        if not folder_name:
            folder_name = f"New_Folder_{int(time.time())}"

        folder_path = Path.home() / "Desktop" / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        speak(f"Folder '{folder_name}' created on your Desktop.")

    # --- Create new file ---
    elif _match(command, ["create new file", "make new file", "create file"]):
        for prefix in ["create new file", "make new file", "create file"]:
            if prefix in command:
                file_name = command.split(prefix, 1)[1].strip()
                break
        else:
            file_name = ""

        if not file_name:
            file_name = f"New_File_{int(time.time())}.txt"
        elif "." not in file_name:
            file_name += ".txt"  # default to .txt if no extension given

        file_path = Path.home() / "Desktop" / file_name
        file_path.touch()
        speak(f"File '{file_name}' created on your Desktop.")

    # --- Delete file (with confirmation) ---
    elif _match(command, ["delete file", "remove file"]):
        for prefix in ["delete file", "remove file"]:
            if prefix in command:
                file_name = command.split(prefix, 1)[1].strip()
                break
        else:
            file_name = ""

        if file_name:
            file_path = Path.home() / "Desktop" / file_name
            if file_path.exists():
                if confirm(f"delete the file '{file_name}'"):
                    file_path.unlink()
                    speak(f"File '{file_name}' has been deleted.")
            else:
                speak(f"File '{file_name}' was not found on the Desktop.")
        else:
            speak("Please tell me the file name to delete.")

    # --- Rename file ---
    elif _match(command, ["rename file"]):
        speak("I can rename files on your Desktop. Please say the old file name.")
        old_name = listen()
        if old_name:
            speak("Now say the new file name.")
            new_name = listen()
            if new_name:
                old_path = Path.home() / "Desktop" / old_name.strip()
                new_path = Path.home() / "Desktop" / new_name.strip()
                if old_path.exists():
                    old_path.rename(new_path)
                    speak(f"Renamed '{old_name}' to '{new_name}'.")
                else:
                    speak(f"File '{old_name}' was not found on the Desktop.")
            else:
                speak("I didn't catch the new name. Please try again.")
        else:
            speak("I didn't catch the file name. Please try again.")

    # --- Show current directory ---
    elif _match(command, ["current directory", "show directory", "where am i", "current folder"]):
        cwd = os.getcwd()
        speak(f"The current working directory is {cwd}.")

    # ==========================================================
    #  🎵 MEDIA & VOLUME CONTROLS
    # ==========================================================

    # --- Volume up ---
    elif _match(command, ["increase volume", "volume up", "louder", "turn up"]):
        speak("Increasing volume.")
        for _ in range(5):  # Press volume-up key 5 times
            pyautogui.press("volumeup")

    # --- Volume down ---
    elif _match(command, ["decrease volume", "volume down", "quieter", "turn down", "lower volume"]):
        speak("Decreasing volume.")
        for _ in range(5):  # Press volume-down key 5 times
            pyautogui.press("volumedown")

    # --- Mute ---
    elif _match(command, ["mute", "mute system", "unmute"]):
        speak("Toggling mute.")
        pyautogui.press("volumemute")

    # --- Play / pause music ---
    elif _match(command, ["pause music", "resume music", "play music", "pause song"]):
        pyautogui.press("playpause")  # Media play/pause key
        speak("Toggled play/pause.")

    # --- Next song ---
    elif _match(command, ["next song", "next track", "skip song"]):
        pyautogui.press("nexttrack")  # Media next-track key
        speak("Playing next track.")

    # --- Previous song ---
    elif _match(command, ["previous song", "previous track", "last song"]):
        pyautogui.press("prevtrack")  # Media previous-track key
        speak("Playing previous track.")

    # ==========================================================
    #  🖱 GUI AUTOMATION
    # ==========================================================

    # --- Screenshot ---
    elif _match(command, ["take screenshot", "screenshot", "capture screen", "screen capture"]):
        speak("Taking a screenshot.")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        speak(f"Screenshot saved as {filename}.")

    # --- Type text ---
    elif _match(command, ["type "]):
        text_to_type = command.split("type", 1)[1].strip()
        if text_to_type:
            speak(f"Typing: {text_to_type}")
            time.sleep(2)  # Let user click into the target window
            pyautogui.write(text_to_type, interval=0.05)
        else:
            speak("Please tell me what to type.")

    # --- Open apps ---
    elif _match(command, ["open notepad"]):
        speak("Opening Notepad.")
        os.startfile("notepad")

    elif _match(command, ["open calculator", "open calc"]):
        speak("Opening Calculator.")
        subprocess.Popen("calc")

    elif _match(command, ["open task manager"]):
        speak("Opening Task Manager.")
        os.system("taskmgr")

    elif _match(command, ["open command prompt", "open cmd", "open terminal"]):
        speak("Opening Command Prompt.")
        os.system("start cmd")

    elif _match(command, ["open vs code", "open vscode", "open visual studio code"]):
        speak("Opening Visual Studio Code.")
        os.system("code")

    elif _match(command, ["open file explorer", "open explorer", "open files"]):
        speak("Opening File Explorer.")
        os.startfile("explorer")

    # --- Scroll ---
    elif _match(command, ["scroll up"]):
        speak("Scrolling up.")
        pyautogui.scroll(5)  # Positive = scroll up

    elif _match(command, ["scroll down"]):
        speak("Scrolling down.")
        pyautogui.scroll(-5)  # Negative = scroll down

    # --- Window management ---
    elif _match(command, ["minimize window", "minimize this"]):
        speak("Minimizing the current window.")
        pyautogui.hotkey("win", "down")  # Win + Down = minimize

    elif _match(command, ["maximize window", "maximize this", "full screen"]):
        speak("Maximizing the current window.")
        pyautogui.hotkey("win", "up")  # Win + Up = maximize

    elif _match(command, ["switch window", "alt tab", "next window"]):
        speak("Switching window.")
        pyautogui.hotkey("alt", "tab")

    # ==========================================================
    #  🧠 MEMORY SYSTEM
    # ==========================================================

    # --- Remember something ---
    elif _match(command, ["remember that", "remember my", "remember i"]):
        remember_information(command)

    # ==========================================================
    #  ⏱ TIMERS, REMINDERS & POMODORO
    # ==========================================================

    # --- Set a timer ---
    elif _match(command, ["set a timer", "set timer", "timer for", "start timer"]):
        set_timer(command)

    # --- Set a reminder ---
    elif _match(command, ["remind me", "set a reminder", "reminder to"]):
        set_reminder(command)

    # --- Pomodoro ---
    elif _match(command, ["start pomodoro", "pomodoro timer", "focus mode", "pomodoro"]):
        start_pomodoro()

    # ==========================================================
    #  📝 NOTES
    # ==========================================================

    # --- Save a note ---
    elif _match(command, ["take a note", "note down", "save note", "write down", "make a note"]):
        save_note(command)

    # --- Read notes ---
    elif _match(command, ["read my notes", "show my notes", "read notes", "show notes"]):
        read_notes()

    # --- Clear notes ---
    elif _match(command, ["clear notes", "delete notes", "erase notes", "clear all notes"]):
        if confirm("clear all your notes"):
            clear_notes()

    # ==========================================================
    #  📋 CLIPBOARD
    # ==========================================================

    # --- Copy to clipboard ---
    elif _match(command, ["copy to clipboard", "copy this"]):
        for prefix in ["copy to clipboard ", "copy this "]:
            if prefix in command:
                text = command.split(prefix, 1)[1].strip()
                break
        else:
            text = ""
        if text:
            copy_to_clipboard(text)
        else:
            speak("What should I copy to the clipboard?")

    # --- Read clipboard ---
    elif _match(command, ["read clipboard", "what's on my clipboard",
                          "show clipboard", "paste clipboard", "what is on my clipboard"]):
        read_clipboard()

    # ==========================================================
    #  🔍 FILE SEARCH
    # ==========================================================

    elif _match(command, ["find files", "search for files", "find all",
                          "find pdf", "find txt", "find png", "find jpg",
                          "find doc", "find mp3", "find mp4", "search files"]):
        find_files(command)

    # ==========================================================
    #  🔧 EXTENDED SYSTEM UTILITIES
    # ==========================================================

    # --- Kill / close a running process ---
    elif _match(command, ["close chrome", "close notepad", "close edge",
                          "close firefox", "close vlc", "close spotify",
                          "close discord", "kill process", "kill ",
                          "force close", "end process"]):
        kill_process(command)

    # --- Disk usage ---
    elif _match(command, ["disk space", "disk usage", "storage space",
                          "check storage", "check disk", "free space"]):
        total, used, free, percent = get_disk_usage()
        speak(f"Disk C: {used} GB used out of {total} GB. "
              f"{free} GB free. That's {percent} percent used.")

    # --- Wi-Fi status ---
    elif _match(command, ["wifi status", "wi-fi status", "am i connected",
                          "check wifi", "check wi-fi", "internet status",
                          "wifi connection"]):
        status = get_wifi_status()
        speak(status)

    # --- IP address ---
    elif _match(command, ["my ip", "ip address", "what is my ip",
                          "local ip", "show ip"]):
        ip = get_local_ip()
        speak(f"Your local IP address is {ip}.")

    # --- System uptime ---
    elif _match(command, ["uptime", "how long has my pc been on",
                          "system uptime", "pc uptime", "how long running"]):
        up = get_uptime()
        speak(f"Your PC has been running for {up}.")

    # --- Command history ---
    elif _match(command, ["show history", "command history", "last commands",
                          "recent commands", "show my history"]):
        show_history()

    elif _match(command, ["clear history", "delete history", "erase history"]):
        if confirm("clear your command history"):
            clear_history()

    # --- Morning / startup routine ---
    elif _match(command, ["morning routine", "startup routine", "good morning routine",
                          "start my day", "daily routine"]):
        startup_routine()

    # --- Recall / ask about memory ---
    elif _match(command, ["what is my", "what's my", "do you remember",
                          "what do i like", "tell me my", "what do you know"]):
        recall_information(command)

    # --- Forget / clear memory ---
    elif _match(command, ["forget my", "forget everything", "clear memory",
                          "erase memory", "delete memory"]):
        forget_information(command)

    # --- Show all memories ---
    elif _match(command, ["show all memories", "list memories", "what do you remember",
                          "show memory"]):
        memory = load_memory()
        if memory:
            speak("Here's everything I remember:")
            for key, value in memory.items():
                speak(f"{key} is {value}.")
        else:
            speak("I don't have any memories stored yet.")

    # ==========================================================
    #  🧠 PERSONALITY & FUN
    # ==========================================================

    elif _match(command, ["who are you", "what is your name", "your name"]):
        speak("I am Jarvis, your personal voice-controlled PC assistant, "
              "built with Python by my creator.")

    elif _match(command, ["what can you do", "help me", "list commands", "your abilities"]):
        speak("Here's what I can do: "
              "Open apps and websites. Search Google and YouTube. "
              "Shutdown, restart, lock, or sleep. Check battery, CPU, RAM, disk, and Wi-Fi. "
              "Take screenshots, type text, scroll, and manage windows. "
              "Set timers, reminders, and Pomodoro focus sessions. "
              "Take notes and manage a clipboard. "
              "Search for files, close running apps, and check your IP address. "
              "Remember facts, tell jokes, and run a morning routine. "
              "Say 'show history' to see your recent commands!")

    elif _match(command, ["introduce yourself", "tell me about yourself"]):
        speak("Hello! I am Jarvis, a voice-activated assistant for Windows. "
              "I can automate your PC tasks, browse the web, manage files, "
              "and even tell you a joke. What would you like me to do?")

    elif _match(command, ["tell me a joke", "tell a joke", "joke", "make me laugh", "funny"]):
        joke = random.choice(JOKES)
        speak(joke)

    elif _match(command, ["thank you", "thanks", "thank"]):
        responses = ["You're welcome!", "Happy to help!",
                     "Anytime!", "No problem at all!"]
        speak(random.choice(responses))

    elif _match(command, ["good morning"]):
        speak("Good morning! Hope you have a wonderful day ahead.")

    elif _match(command, ["good night"]):
        speak("Good night! Sleep well and sweet dreams.")

    elif _match(command, ["how are you", "how do you do"]):
        speak("I'm running perfectly, thank you for asking! How can I help you?")

    elif _match(command, ["i love you"]):
        speak("That's sweet! I appreciate you too. Now, how can I help?")

    elif _match(command, ["hello", "hi jarvis", "hey jarvis", "hi "]):
        speak("Hello! What can I do for you?")

    # ==========================================================
    #  ❌ FALLBACK — command not recognized
    # ==========================================================

    else:
        speak("Sorry, I didn't recognize that command. "
              "Say 'what can you do' to hear my abilities.")
        return False

    return True


# =================== GREETING ===============================

def greet():
    """
    Greets the user based on the current time of day.
    """
    hour = datetime.datetime.now().hour

    if hour < 12:
        speak("Good morning! I am Jarvis. How can I help you today?")
    elif hour < 17:
        speak("Good afternoon! I am Jarvis. How can I help you today?")
    elif hour < 21:
        speak("Good evening! I am Jarvis. How can I help you today?")
    else:
        speak("Hello! It's late, but I am Jarvis, ready to help.")


# =================== MAIN LOOP ==============================

def main():
    """
    Entry point — authenticates the user, greets them, then enters
    an infinite listen → execute loop until "stop jarvis".
    """
    # Step 0: Password check — must pass before Jarvis starts
    if not authenticate():
        print("\n[Jarvis locked — exiting]")
        return  # Stop the program entirely

    # Step 1: Greet the user
    greet()

    # Step 2: Infinite loop — keep listening for commands
    while True:
        # Listen for a voice command
        command = listen()

        # If nothing was recognized, skip and listen again
        if command is None:
            continue

        # Check for exit phrases (say any of these to close Jarvis)
        exit_phrases = ["stop jarvis", "exit", "goodbye", "quit", "bye",
                        "close yourself", "close jarvis", "terminate",
                        "go to sleep", "shut up"]

        if any(phrase in command for phrase in exit_phrases):
            speak("Goodbye! Have a great day. Closing myself now.")
            break  # Exit the while loop and end the program

        # Log the command to history
        log_command(command)

        # Try to execute the recognized command
        execute_command(command)

    print("\n[Jarvis has been shut down]")


# Only run when this file is executed directly (not when imported)
if __name__ == "__main__":
    main()
