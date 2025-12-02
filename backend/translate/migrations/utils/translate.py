import sounddevice as sd
import numpy as np
import queue
import requests
import io
from scipy.io.wavfile import write
import base64
import os

# ===============================
# CONFIG
# ===============================
HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_ID = "openai/whisper-large-v3"

API_URL = f"https://router.huggingface.co/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 2   # seconds per API call
CHUNK_SIZE = SAMPLE_RATE * CHUNK_DURATION

audio_queue = queue.Queue()

# ===============================
# AUTOMATIC MICROPHONE SELECTION
# ===============================
def get_first_input_device():
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"Using input device #{i}: {dev['name']}")
            return i
    raise RuntimeError("No input device with channels > 0 found.")

device_index = get_first_input_device()

# ===============================
# AUDIO CALLBACK
# ===============================
def audio_callback(indata, frames, time, status):
    if status:
        print("Audio error:", status)
    audio_queue.put(indata.copy())

# ===============================
# CALL HUGGINGFACE API
# ===============================
def transcribe_chunk(pcm16):
    try:
        wav_io = io.BytesIO()
        write(wav_io, SAMPLE_RATE, pcm16)
        wav_io.seek(0)
        audio_bytes = wav_io.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        payload = {"inputs": audio_b64}

        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json=payload,
            timeout=60
        )

        resp = response.json()
        if "error" in resp:
            print("HF Error:", resp["error"])
            return ""
        return resp.get("text", "")

    except Exception as e:
        print("Request failed:", e)
        return ""

# ===============================
# MAIN LOOP
# ===============================
def main():
    print("\n🎤 Real-time Speech-to-Text using HuggingFace API")
    print("No model is downloaded locally.")
    print("Press CTRL+C to stop.\n")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        callback=audio_callback,
        device=device_index
    ):

        audio_buffer = np.zeros((0, CHANNELS), dtype=np.float32)

        while True:
            try:
                # read chunk from microphone queue
                chunk = audio_queue.get()
                audio_buffer = np.concatenate((audio_buffer, chunk))

                if len(audio_buffer) >= CHUNK_SIZE:
                    # take a full 2-second chunk
                    current = audio_buffer[:CHUNK_SIZE]
                    audio_buffer = audio_buffer[CHUNK_SIZE:]

                    # convert float32 → PCM16
                    pcm16 = (current.flatten() * 32767).astype(np.int16)

                    # send to HuggingFace
                    text = transcribe_chunk(pcm16)
                    if text:
                        print("🟢", text)

            except KeyboardInterrupt:
                print("\n🛑 Stopped.")
                break

if __name__ == "__main__":
    main()
