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
        self.block_seconds = 0.05
        self.block_size = int(sample_rate * self.block_seconds)

    def device_name(self) -> str:
        try:
            return sd.query_devices(kind="input")["name"]
        except Exception:
            return "default input"

    def record(
        self,
        output_path: str = "data/recording.wav",
        duration: int = 5,
    ) -> str:

        output = self._prepare(output_path)

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

    def record_fixed(
        self,
        output_path: str = "data/recording.wav",
        duration: float = 6,
    ) -> str | None:

        output = self._prepare(output_path)
        frames = []

        print(f"🎤 Recording {int(duration)} seconds... speak now")

        with self._stream() as stream:
            for _ in range(int(duration / self.block_seconds)):
                block, _overflow = stream.read(self.block_size)
                frames.append(block.copy())
                self._meter(self._rms(block))

        print("\r" + " " * 60 + "\r", end="")

        return self._finish(output, frames)

    def record_until_silence(
        self,
        output_path: str = "data/recording.wav",
        max_duration: float = 15,
        silence_seconds: float = 1.2,
        start_timeout: float = 15,
    ) -> str | None:

        output = self._prepare(output_path)

        with self._stream() as stream:
            threshold = self._noise_threshold(stream)

            print()
            print("🎤 Listening... speak now")

            frames = []
            speaking = False
            silent_blocks = 0
            waited_blocks = 0

            needed_silence = int(silence_seconds / self.block_seconds)
            max_blocks = int(max_duration / self.block_seconds)
            wait_blocks = int(start_timeout / self.block_seconds)

            while len(frames) < max_blocks:
                block, _overflow = stream.read(self.block_size)
                block = block.copy()
                level = self._rms(block)
                self._meter(level)

                if not speaking:
                    frames.append(block)

                    if len(frames) > 10:
                        frames.pop(0)

                    if level >= threshold:
                        speaking = True
                        silent_blocks = 0
                        continue

                    waited_blocks += 1

                    if waited_blocks >= wait_blocks:
                        print("\r" + " " * 60 + "\r", end="")
                        print("I didn't hear anything.")
                        return None

                    continue

                frames.append(block)

                if level < threshold:
                    silent_blocks += 1
                    if silent_blocks >= needed_silence:
                        break
                else:
                    silent_blocks = 0

        print("\r" + " " * 60 + "\r", end="")

        if not speaking:
            print("I didn't hear anything.")
            return None

        return self._finish(output, frames)

    def _stream(self) -> sd.InputStream:
        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.block_size,
        )
        stream.start()
        return _StreamContext(stream)

    def _noise_threshold(self, stream) -> float:
        levels = []

        for _ in range(int(0.6 / self.block_seconds)):
            block, _overflow = stream.read(self.block_size)
            levels.append(self._rms(block))

        noise_floor = float(np.median(levels)) if levels else 0.0
        return max(noise_floor * 2.5, 60.0)

    def _meter(self, level: float) -> None:
        bars = int(min(level / 400.0, 1.0) * 20)
        print("\r  mic [" + "#" * bars + "-" * (20 - bars) + "]", end="")

    def _finish(self, output: Path, frames: list) -> str | None:
        if not frames:
            print("I didn't hear anything.")
            return None

        audio = np.concatenate(frames)

        if self._rms(audio) < 90:
            print("That was too quiet to understand.")
            return None

        self._write_wav(output, self._normalize(audio))
        print("✓ Recording complete")

        return str(output)

    def _prepare(self, output_path: str) -> Path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        return output

    def _rms(self, audio: np.ndarray) -> float:
        data = audio.astype(np.float32)

        if data.size == 0:
            return 0.0

        return float(np.sqrt(np.mean(np.square(data))))

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        data = audio.astype(np.float32)
        peak = float(np.max(np.abs(data))) if data.size else 0.0

        if peak < 20:
            return audio.astype(np.int16)

        gain = min((32767 * 0.9) / peak, 20.0)
        return np.clip(data * gain, -32768, 32767).astype(np.int16)

    def _write_wav(self, output: Path, audio: np.ndarray) -> None:
        with wave.open(str(output), "wb") as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio.tobytes())


class _StreamContext:

    def __init__(self, stream: sd.InputStream):
        self.stream = stream

    def __enter__(self):
        return self.stream

    def __exit__(self, *exc_info):
        self.stream.stop()
        self.stream.close()
        return False

    def read(self, frames):
        return self.stream.read(frames)
