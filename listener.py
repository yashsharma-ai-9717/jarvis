"""
listener.py — Voice Input Module for Jarvis
Captures audio from the microphone and converts it to text
using Google's free Speech Recognition API.
"""

# speech_recognition: provides access to microphone and speech-to-text engines
import speech_recognition as sr


def listen():
    """
    Listens to the user's voice through the microphone,
    converts it to text, and returns it as a lowercase string.

    Returns:
        str or None: The recognized command in lowercase,
                     or None if recognition failed.
    """

    # Create a Recognizer instance — this handles all the speech processing
    recognizer = sr.Recognizer()

    # Use the default system microphone as the audio source
    with sr.Microphone() as source:

        print("Listening...")

        # Adjust the recognizer's energy threshold based on ambient noise
        # so it can distinguish speech from background sounds.
        # duration=1 means it samples 1 second of ambient noise to calibrate.
        recognizer.adjust_for_ambient_noise(source, duration=1)

        # Set how long the recognizer waits for the user to start speaking (seconds).
        # If no speech is detected within this time, it raises WaitTimeoutError.
        # Set to None to wait indefinitely, or a number like 5 for a 5-second timeout.
        recognizer.pause_threshold = 1  # seconds of silence before phrase is considered complete

        try:
            # Capture audio from the microphone
            # timeout=5   → max seconds to wait for speech to START
            # phrase_time_limit=10 → max seconds the spoken phrase can last
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

            print("Recognizing...")

            # Send the captured audio to Google's free Speech Recognition API
            # language="en-in" uses Indian English; change to "en-us" for US English
            command = recognizer.recognize_google(audio, language="en-in")

            # Convert to lowercase for easier keyword matching later
            command = command.lower()
            print(f"User said: {command}")

            return command

        except sr.WaitTimeoutError:
            # User didn't say anything within the timeout window
            print("No speech detected. Timed out.")
            return None

        except sr.UnknownValueError:
            # Speech was detected but could not be understood
            print("Sorry, I could not understand that.")
            return None

        except sr.RequestError as e:
            # API was unreachable (no internet, service down, etc.)
            print(f"Speech Recognition service error: {e}")
            return None

        except Exception as e:
            # Catch-all for any other unexpected errors
            print(f"An unexpected error occurred: {e}")
            return None
