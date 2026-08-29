import sys

from app.brain.agent import JarvisAgent
from app.config.settings import settings
from app.voice.voice_pipeline import VoicePipeline

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():

    jarvis = JarvisAgent()
    voice = VoicePipeline()

    print()
    print("=" * 60)
    print("                    JARVIS")
    print("=" * 60)
    print("Local AI Assistant")
    print(f"Model: {settings.ollama_model} (fallback: {settings.ollama_fallback_model})")
    print()
    print("Speak when you see Listening...")
    print("Say 'exit' or press Ctrl+C to stop.")
    print("=" * 60)
    print()

    voice.speak("Ready. I am listening.")

    while True:

        try:

            user_input = voice.listen()

            print()
            print("You:", user_input)
            print()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "stop", "goodbye"}:
                voice.speak("Goodbye.")
                break

            response = jarvis.ask(user_input)

            if not response:
                response = "I heard you."

            voice.speak(response)

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
