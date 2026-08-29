import re

from faster_whisper import WhisperModel


# Whisper invents these on silence or background noise.
HALLUCINATIONS = {
    "thank you",
    "thank you.",
    "thanks for watching",
    "thank you for watching",
    "thank you for watching.",
    "you",
    "bye",
    ".",
    "subtitles by the amara.org community",
    "please subscribe",
}


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
            vad_filter=False,
            condition_on_previous_text=False,
            temperature=[0.0, 0.2, 0.4],
            no_speech_threshold=0.7,
            log_prob_threshold=-1.5,
            initial_prompt=(
                "Jarvis, open Chrome. Open Notepad. Open VS Code. "
                "Open Calculator. Open Downloads. What time is it?"
            ),
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        ).strip()

        if self._is_hallucination(text):
            return ""

        return text

    def _is_hallucination(self, text: str) -> bool:
        cleaned = re.sub(r"[^a-z0-9.\s]", "", text.lower()).strip()

        return cleaned in HALLUCINATIONS
