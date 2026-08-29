import sys

from app.voice.recorder import AudioRecorder
from app.voice.whisper import WhisperSTT

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():

    recorder = AudioRecorder()

    audio_path = recorder.record(
        duration=5
    )

    whisper = WhisperSTT(
        model_size="small",
        device="cpu",
        compute_type="int8",
    )

    text = whisper.transcribe(audio_path)

    print()
    print("=" * 50)
    print("TRANSCRIPTION")
    print("=" * 50)
    print(text)
    print("=" * 50)


if __name__ == "__main__":
    main()
