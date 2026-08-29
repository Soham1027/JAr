from faster_whisper import WhisperModel


class WhisperSTT:

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
    ):

        print(f"Loading Whisper model: {model_size}")

        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
        )

        print("✓ Whisper ready")

    def transcribe(self, audio_path: str) -> str:

        segments, info = self.model.transcribe(
            audio_path,
            language="en",
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "threshold": 0.3,
                "min_silence_duration_ms": 300,
                "speech_pad_ms": 500,
            },
            condition_on_previous_text=False,
            temperature=0.0,
            no_speech_threshold=0.45,
            initial_prompt=(
                "Jarvis, open Chrome, open Notepad, open VS Code, "
                "open Calculator, open Downloads."
            ),
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return text.strip()
