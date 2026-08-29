import sys

from app.voice.voice_pipeline import VoicePipeline

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():

    voice = VoicePipeline()

    print()
    print("=" * 60)
    print("JARVIS VOICE TEST")
    print("=" * 60)

    text = voice.listen()

    print()
    print("You:", text)

    if text:

        voice.speak(
            f"I heard you say: {text}"
        )


if __name__ == "__main__":
    main()
