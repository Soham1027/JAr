import time

from app.voice.recorder import AudioRecorder
from app.voice.whisper import WhisperSTT
from app.voice.tts import TextToSpeech


class VoicePipeline:

    def __init__(self):

        self.recorder = AudioRecorder()

        self.whisper = WhisperSTT(
            model_size="small",
            device="cpu",
            compute_type="int8",
        )

        self.tts = TextToSpeech()

    def listen(self) -> str:

        audio_path = self.recorder.record_until_silence()

        return self._transcribe(audio_path)

    def listen_fixed(self, duration: float = 6) -> str:

        audio_path = self.recorder.record_fixed(duration=duration)

        return self._transcribe(audio_path)

    def speak(self, text: str):

        self.tts.speak(text)
        time.sleep(0.4)

    def _transcribe(self, audio_path: str | None) -> str:

        if not audio_path:
            return ""

        print("Transcribing...")

        return self.whisper.transcribe(audio_path)
