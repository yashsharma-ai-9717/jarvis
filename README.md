# Jarvis Voice Assistant

A simple Python-based voice assistant for Windows that listens to voice commands, performs system actions, and speaks responses.

## Features

- Voice recognition via `speech_recognition`
- Offline text-to-speech with `pyttsx3`
- System commands like opening apps, telling time, taking screenshots, and controlling volume
- Memory system to remember facts across sessions
- Password protection on startup
- Extensible command modules in `commands/`

## Requirements

- Python 3.8+
- Windows OS
- Microphone access

## Python Dependencies

- `speech_recognition`
- `pyttsx3`
- `pyaudio` or `sounddevice` (for microphone input)
- `pyautogui`
- `psutil`

Install dependencies with:

```bash
pip install speech_recognition pyttsx3 pyaudio pyautogui psutil
```

> If `pyaudio` fails to install, use a prebuilt wheel for Windows or install `sounddevice` and adjust the microphone backend accordingly.

## Usage

Run the assistant with:

```bash
python jarvis.py
```

When prompted, enter the startup password:

```text
jarvis123
```

Then speak commands clearly into your microphone.

## Default Password

- `jarvis123`

You can change the password by editing `jarvis.py` and updating the `JARVIS_PASSWORD` value.

## Project Structure

- `jarvis.py` — main assistant logic
- `commands/` — system command handlers
- `speech/` — speech listening and speaking helpers
- `utils/` — utility modules (if present)

## Notes

- The assistant uses Google Speech Recognition by default, so an internet connection is required for accurate voice-to-text conversion.
- For best results, use a quiet environment and speak clearly.
