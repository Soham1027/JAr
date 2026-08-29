import sys

from app.voice.tts import TextToSpeech

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():

    tts = TextToSpeech()

    tts.speak(
        "Hello. I am JARVIS. "
        "My voice system is working."
    )


if __name__ == "__main__":
    main()
