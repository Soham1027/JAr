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

        if not audio_path:
            return ""

        return self.whisper.transcribe(audio_path)

    def speak(self, text: str):

        self.tts.speak(text)
        time.sleep(0.5)
