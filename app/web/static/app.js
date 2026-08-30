const log = document.getElementById("log");
const input = document.getElementById("input");
const composer = document.getElementById("composer");
const micButton = document.getElementById("mic");
const sendButton = document.getElementById("send");
const orb = document.getElementById("orb");
const statusText = document.getElementById("status");
const modelPill = document.getElementById("model-pill");
const bars = Array.from(document.querySelectorAll("#bars span"));

let recorder = null;
let chunks = [];
let stream = null;
let meterTimer = null;
let busy = false;

init();

async function init() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    modelPill.textContent = data.model;
  } catch {
    modelPill.textContent = "offline";
  }
}

function setStatus(text, mode) {
  statusText.textContent = text;
  orb.classList.toggle("listening", mode === "listening");
  orb.classList.toggle("thinking", mode === "thinking");
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  micButton.disabled = value;
}

function addMessage(who, text, isError) {
  const wrap = document.createElement("div");
  wrap.className = "msg " + (who === "You" ? "you" : "jarvis") + (isError ? " error" : "");

  const label = document.createElement("div");
  label.className = "who";
  label.textContent = who;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  wrap.append(label, bubble);
  log.append(wrap);
  log.scrollTop = log.scrollHeight;

  return wrap;
}

function addTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg jarvis";
  wrap.innerHTML =
    '<div class="who">JARVIS</div>' +
    '<div class="bubble typing"><span></span><span></span><span></span></div>';
  log.append(wrap);
  log.scrollTop = log.scrollHeight;
  return wrap;
}

function speak(text) {
  if (!("speechSynthesis" in window) || !text) return;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.02;
  utterance.pitch = 1;

  const preferred = window.speechSynthesis
    .getVoices()
    .find((voice) => /david|mark|google uk english male|daniel/i.test(voice.name));

  if (preferred) utterance.voice = preferred;

  utterance.onstart = () => setStatus("Speaking", "thinking");
  utterance.onend = () => setStatus("Ready", null);

  window.speechSynthesis.speak(utterance);
}

async function send(message) {
  if (!message || busy) return;

  addMessage("You", message);
  input.value = "";

  setBusy(true);
  setStatus("Thinking", "thinking");
  const typing = addTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    typing.remove();

    if (data.error) {
      addMessage("JARVIS", data.error, true);
      setStatus("Error", null);
    } else {
      addMessage("JARVIS", data.reply);
      speak(data.reply);
    }
  } catch (error) {
    typing.remove();
    addMessage("JARVIS", "Cannot reach the server.", true);
    setStatus("Offline", null);
  } finally {
    setBusy(false);
  }
}

composer.addEventListener("submit", (event) => {
  event.preventDefault();
  send(input.value.trim());
});

document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => send(chip.dataset.cmd));
});

document.getElementById("reset").addEventListener("click", async () => {
  await fetch("/api/reset", { method: "POST" });
  log.innerHTML = "";
  addMessage("JARVIS", "Conversation cleared.");
});

micButton.addEventListener("click", () => {
  if (recorder && recorder.state === "recording") {
    stopRecording();
  } else {
    startRecording();
  }
});

orb.addEventListener("click", () => micButton.click());

async function startRecording() {
  if (busy) return;

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
    });
  } catch {
    addMessage("JARVIS", "Microphone permission was denied.", true);
    return;
  }

  window.speechSynthesis.cancel();

  chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.onstop = handleRecordingStop;
  recorder.start();

  micButton.classList.add("recording");
  setStatus("Listening", "listening");
  startMeter();
}

function stopRecording() {
  if (recorder && recorder.state === "recording") recorder.stop();

  micButton.classList.remove("recording");
  stopMeter();
}

async function handleRecordingStop() {
  stream.getTracks().forEach((track) => track.stop());

  const blob = new Blob(chunks, { type: "audio/webm" });

  if (blob.size < 2000) {
    setStatus("Ready", null);
    addMessage("JARVIS", "That clip was too short.", true);
    return;
  }

  setBusy(true);
  setStatus("Transcribing", "thinking");

  const form = new FormData();
  form.append("audio", blob, "clip.webm");

  const typing = addTyping();

  try {
    const response = await fetch("/api/voice", { method: "POST", body: form });
    const data = await response.json();
    typing.remove();

    if (data.text) addMessage("You", data.text);

    if (data.error) {
      addMessage("JARVIS", data.error, true);
      setStatus("Ready", null);
    } else {
      addMessage("JARVIS", data.reply);
      speak(data.reply);
    }
  } catch {
    typing.remove();
    addMessage("JARVIS", "Cannot reach the server.", true);
    setStatus("Offline", null);
  } finally {
    setBusy(false);
  }
}

function startMeter() {
  const context = new AudioContext();
  const source = context.createMediaStreamSource(stream);
  const analyser = context.createAnalyser();
  analyser.fftSize = 64;
  source.connect(analyser);

  const data = new Uint8Array(analyser.frequencyBinCount);

  meterTimer = setInterval(() => {
    analyser.getByteFrequencyData(data);

    bars.forEach((bar, index) => {
      const value = data[index + 2] || 0;
      bar.style.height = 6 + (value / 255) * 28 + "px";
    });
  }, 80);

  meterTimer.context = context;
}

function stopMeter() {
  if (!meterTimer) return;

  clearInterval(meterTimer);
  if (meterTimer.context) meterTimer.context.close();
  meterTimer = null;

  bars.forEach((bar) => (bar.style.height = "6px"));
}

window.addEventListener("keydown", (event) => {
  if (event.code === "Space" && document.activeElement !== input) {
    event.preventDefault();
    micButton.click();
  }
});
