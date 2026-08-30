import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.brain.agent import JarvisAgent
from app.config.settings import settings

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="JARVIS")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

agent = JarvisAgent()
_whisper = None


class ChatRequest(BaseModel):
    message: str


def get_whisper():
    global _whisper

    if _whisper is None:
        from app.voice.whisper import WhisperSTT

        _whisper = WhisperSTT(
            model_size="small",
            device="cpu",
            compute_type="int8",
        )

    return _whisper


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status():
    return {
        "model": settings.ollama_model,
        "fallback": settings.ollama_fallback_model,
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    message = request.message.strip()

    if not message:
        return {"reply": "", "error": "Empty message."}

    try:
        return {"reply": agent.ask(message)}
    except Exception as error:
        return {"reply": "", "error": str(error)}


@app.post("/api/voice")
async def voice(audio: UploadFile = File(...)):
    data = await audio.read()

    if not data:
        return {"text": "", "reply": "", "error": "No audio received."}

    suffix = Path(audio.filename or "clip.webm").suffix or ".webm"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as clip:
        clip.write(data)
        clip_path = clip.name

    try:
        text = get_whisper().transcribe(clip_path)

        if not text:
            return {"text": "", "reply": "", "error": "I didn't catch that."}

        return {"text": text, "reply": agent.ask(text)}

    except Exception as error:
        return {"text": "", "reply": "", "error": str(error)}

    finally:
        Path(clip_path).unlink(missing_ok=True)


@app.post("/api/reset")
def reset():
    agent.messages = agent.messages[:1]
    return {"ok": True}
