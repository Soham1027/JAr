import sys

from app.brain.agent import JarvisAgent
from app.config.settings import settings
from app.voice.voice_pipeline import VoicePipeline

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXIT_WORDS = {"exit", "quit", "stop", "goodbye", "bye"}


def main():

    jarvis = JarvisAgent()
    voice = VoicePipeline()

    print()
    print("=" * 60)
    print("                    JARVIS")
    print("=" * 60)
    print("Local AI Assistant")
    print(f"Model: {settings.ollama_model} (fallback: {settings.ollama_fallback_model})")
    print(f"Microphone: {voice.recorder.device_name()}")
    print()
    print("Press Enter to talk, or type your command and press Enter.")
    print("Type 'exit' to stop.")
    print("=" * 60)
    print()

    voice.speak("Ready.")

    while True:

        try:

            typed = input("You (Enter to talk): ").strip()

            if typed.lower() in EXIT_WORDS:
                voice.speak("Goodbye.")
                break

            if typed:
                user_input = typed
            else:
                user_input = voice.listen_fixed(duration=6)

                print()
                print("You said:", user_input or "(nothing)")

                if not user_input:
                    print("Try again, a bit louder.")
                    print()
                    continue

                if user_input.lower().strip(" .!?") in EXIT_WORDS:
                    voice.speak("Goodbye.")
                    break

            response = jarvis.ask(user_input)

            if not response:
                response = "I heard you."

            print()
            voice.speak(response)
            print()

        except KeyboardInterrupt:

            print("\nJARVIS: Goodbye.")
            break

        except Exception as error:

            print()
            print("JARVIS ERROR:")
            print(error)
            print()


if __name__ == "__main__":
    main()
