import sys

import pyttsx3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():

    engine = pyttsx3.init()

    voices = engine.getProperty("voices")

    print()
    print("=" * 60)
    print("AVAILABLE VOICES")
    print("=" * 60)

    for index, voice in enumerate(voices):

        print()
        print(f"Voice {index}")
        print("Name:", voice.name)
        print("ID:", voice.id)

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
