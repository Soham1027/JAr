import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd


class AudioRecorder:

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_seconds = 0.1

        try:
            device = sd.query_devices(kind="input")
            print(f"Microphone: {device['name']}")
        except Exception:
            pass

    def record(
        self,
        output_path: str = "data/recording.wav",
        duration: int = 5,
    ) -> str:

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        print()
        print("🎤 Listening...")

        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
        )

        sd.wait()

        self._write_wav(output, self._normalize(audio))
        print("✓ Recording complete")

        return str(output)

    def record_until_silence(
        self,
        output_path: str = "data/recording.wav",
        max_duration: float = 12,
        silence_seconds: float = 1.0,
        start_timeout: float = 10,
    ) -> str | None:

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        chunk_size = int(self.sample_rate * self.chunk_seconds)
        threshold = self._noise_threshold(chunk_size)

        print()
        print("🎤 Listening... speak now")

        frames: list[np.ndarray] = []
        speaking = False
        silence_chunks = 0
        needed_silence = int(silence_seconds / self.chunk_seconds)
        max_chunks = int(max_duration / self.chunk_seconds)
        wait_chunks = int(start_timeout / self.chunk_seconds)

        for index in range(max_chunks):
            block = sd.rec(
                chunk_size,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()

            level = self._rms(block)

            if not speaking:
                if level >= threshold:
                    speaking = True
                    frames.append(block)
                    silence_chunks = 0
                elif index >= wait_chunks:
                    print("I didn't hear anything. Speak a bit louder.")
                    return None
                continue

            frames.append(block)

            if level < threshold:
                silence_chunks += 1
                if silence_chunks >= needed_silence:
                    break
            else:
                silence_chunks = 0

        if not frames:
            print("I didn't hear anything. Speak a bit louder.")
            return None

        audio = np.concatenate(frames)
        self._write_wav(output, self._normalize(audio))
        print("✓ Recording complete")

        return str(output)

    def _noise_threshold(self, chunk_size: int) -> float:
        time.sleep(0.25)

        samples = []
        for _ in range(5):
            block = sd.rec(
                chunk_size,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()
            samples.append(self._rms(block))

        noise_floor = float(np.median(samples))
        return max(noise_floor * 3.5, 180)

    def _rms(self, audio: np.ndarray) -> float:
        data = audio.astype(np.float32)
        if data.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(data))))

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        data = audio.astype(np.float32)
        peak = float(np.max(np.abs(data))) if data.size else 0.0

        if peak < 40:
            return audio.astype(np.int16)

        gain = min((32767 * 0.85) / peak, 10.0)
        boosted = np.clip(data * gain, -32768, 32767)
        return boosted.astype(np.int16)

    def _write_wav(self, output: Path, audio: np.ndarray) -> None:
        with wave.open(str(output), "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio.tobytes())
