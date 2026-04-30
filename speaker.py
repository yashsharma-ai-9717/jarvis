"""
speaker.py — Text-to-Speech Module for Jarvis
Converts text responses into spoken audio using the
pyttsx3 offline TTS engine (no internet required).
"""

# pyttsx3: offline text-to-speech engine that works on Windows, macOS, and Linux
import pyttsx3


# Initialize the TTS engine once at module level
# so it doesn't get re-created every time speak() is called.
engine = pyttsx3.init()

# --- Voice Configuration ---

# Get the list of available voices on the system
voices = engine.getProperty("voices")

# voices[0] = male voice (default), voices[1] = female voice (if available)
# Change index to 1 for a female voice
engine.setProperty("voice", voices[0].id)

# Set speech rate (words per minute)
# Default is ~200 wpm which feels too fast.
# 160-175 wpm is a comfortable, natural speed.
engine.setProperty("rate", 170)

# Set volume level (0.0 to 1.0)
engine.setProperty("volume", 1.0)


def speak(text):
    """
    Prints the given text to the console and then
    speaks it out loud using the pyttsx3 engine.

    Args:
        text (str): The message Jarvis should say.
    """

    # Print the response so the user can also read it
    print(f"Jarvis: {text}")

    # Queue the text for the TTS engine to speak
    engine.say(text)

    # Block and process all queued speech before returning.
    # Without this, the function would exit before finishing speaking.
    engine.runAndWait()
