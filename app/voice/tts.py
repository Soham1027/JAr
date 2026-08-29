import re
import sys


class TextToSpeech:

    def __init__(
        self,
        rate: int = 175,
        volume: float = 1.0,
        voice_id: str | None = None,
    ):
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self._sapi = None

        if sys.platform == "win32":
            self._init_sapi()

        if self._sapi is None:
            self._init_pyttsx3()

    def _init_sapi(self) -> None:
        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            voice.Volume = int(max(0.0, min(self.volume, 1.0)) * 100)
            voice.Rate = 1
            if self.voice_id:
                for candidate in voice.GetVoices():
                    if self.voice_id.lower() in candidate.GetDescription().lower():
                        voice.Voice = candidate
                        break
            self._sapi = voice
        except Exception:
            self._sapi = None

    def _init_pyttsx3(self) -> None:
        import pyttsx3

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", self.rate)
        self.engine.setProperty("volume", self.volume)
        if self.voice_id:
            self.engine.setProperty("voice", self.voice_id)

    def speak(self, text: str) -> None:
        spoken = self._clean(text)

        if not spoken:
            return

        print(f"JARVIS: {spoken}")

        try:
            import sounddevice as sd

            sd.stop()
        except Exception:
            pass

        if self._sapi is not None:
            self._sapi.Speak(spoken, 0)
            return

        self.engine.stop()
        self.engine.say(spoken)
        self.engine.runAndWait()

    def stop(self) -> None:
        if self._sapi is not None:
            self._sapi.Speak("", 2)
            return

        self.engine.stop()

    def get_voices(self):
        if self._sapi is not None:
            return [voice.GetDescription() for voice in self._sapi.GetVoices()]

        return self.engine.getProperty("voices")

    def _clean(self, text: str) -> str:
        spoken = (text or "").strip()
        spoken = re.sub(r"[*_`#]+", "", spoken)
        spoken = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", spoken)
        spoken = re.sub(r"https?://\S+", "", spoken)
        spoken = re.sub(r"\s+", " ", spoken).strip()
        return spoken
