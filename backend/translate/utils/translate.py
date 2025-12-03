# import sounddevice as sd
# import numpy as np
# import queue
# import time
# from faster_whisper import WhisperModel

# # ===============================
# # CONFIGURATION
# # ===============================
# # Model sizes: "tiny", "base", "small", "medium", "large-v3"
# # "tiny" or "base" is recommended for real-time CPU usage.
# MODEL_SIZE = "base" 
# DEVICE = "cpu"
# COMPUTE_TYPE = "int8"  # "int8" is lighter and faster on CPU than "float32"

# SAMPLE_RATE = 16000
# CHANNELS = 1
# # How often to process audio (seconds). 
# # Lower = faster response but higher CPU load.
# TRANSCRIBE_INTERVAL = 2.0 

# audio_queue = queue.Queue()

# # ===============================
# # LOAD MODEL
# # ===============================
# print(f"⏳ Loading local Whisper model: '{MODEL_SIZE}' ({DEVICE})...")
# print("   (This involves downloading the model on the first run)")

# try:
#     model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
#     print("✅ Model loaded successfully!")
# except Exception as e:
#     print(f"❌ Error loading model: {e}")
#     exit(1)

# # ===============================
# # AUDIO HANDLING
# # ===============================
# def audio_callback(indata, frames, time, status):
#     if status:
#         print(f"Audio error: {status}")
#     audio_queue.put(indata.copy())

# def get_input_device():
#     try:
#         # Prefer a device with 'Microphone' in the name if possible
#         devices = sd.query_devices()
#         for i, dev in enumerate(devices):
#             if dev['max_input_channels'] > 0:
#                 return i
#         return None
#     except:
#         return None

# # ===============================
# # MAIN LOOP
# # ===============================
# def main():
#     device_idx = get_input_device()
#     print(f"\n🎤 Starting Local Transcription ({MODEL_SIZE} model)")
#     print("   No internet required. Processing on CPU.")
#     print("   Press CTRL+C to stop.\n")

#     audio_buffer = np.array([], dtype=np.float32)
    
#     # We accumulate audio and process it in chunks
#     # To simulate a continuous stream, real production apps use VAD (Voice Activity Detection)
#     # This loop is a simple implementation that cuts every X seconds.

#     try:
#         with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, 
#                             callback=audio_callback, device=device_idx):
            
#             while True:
#                 # 1. Accumulate audio from queue
#                 while not audio_queue.empty():
#                     chunk = audio_queue.get()
#                     # Flatten to 1D array
#                     chunk = chunk.flatten()
#                     audio_buffer = np.concatenate((audio_buffer, chunk))

#                 # 2. Process if buffer is long enough
#                 if len(audio_buffer) >= SAMPLE_RATE * TRANSCRIBE_INTERVAL:
#                     # Isolate the chunk to process
#                     process_chunk = audio_buffer[:int(SAMPLE_RATE * TRANSCRIBE_INTERVAL)]
                    
#                     # Keep the rest in buffer (or overlap if needed)
#                     # For simple streaming, we just clear processed audio
#                     audio_buffer = audio_buffer[int(SAMPLE_RATE * TRANSCRIBE_INTERVAL):]

#                     # 3. Check for silence (simple energy threshold)
#                     # prevents processing empty background noise
#                     if np.abs(process_chunk).mean() > 0.01:
                        
#                         # 4. Transcribe
#                         # faster-whisper accepts numpy arrays directly
#                         segments, info = model.transcribe(
#                             process_chunk, 
#                             beam_size=5, 
#                             language="en",
#                             vad_filter=True, # Built-in Voice Activity Detection
#                             vad_parameters=dict(min_silence_duration_ms=500)
#                         )

#                         for segment in segments:
#                             print(f"🟢 {segment.text.strip()}")
                    
#                 time.sleep(0.1)

#     except KeyboardInterrupt:
#         print("\n🛑 Stopped.")
#     except Exception as e:
#         print(f"\n❌ Error: {e}")

# if __name__ == "__main__":
#     main()




# translate/utils/translate.py
# translate/utils/translate.py
import numpy as np
from faster_whisper import WhisperModel

# CHANGE 1: Use 'base.en' instead of 'tiny.en'
# 'base.en' is much smarter at understanding context and accents.
model = WhisperModel("base.en", device="cpu", compute_type="int8")

def transcribe_audio_chunk(bytes_data):
    try:
        # Convert to Float32
        audio_array = np.frombuffer(bytes_data, dtype=np.int16).astype(np.float32) / 32768.0

        # CHANGE 2: Add 'vad_filter=True'
        # Faster-Whisper has built-in VAD (Voice Activity Detection).
        # This prevents it from trying to transcribe breathing or fan noise.
        segments, info = model.transcribe(
            audio_array, 
            beam_size=1, 
            language="en", 
            condition_on_previous_text=False,
            vad_filter=True, # <--- Enable built-in silence filtering
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        full_text = " ".join([seg.text for seg in segments]).strip()

        if not full_text:
            return None

        return {
            "text": full_text,
            "duration": info.duration,
            "word_count": len(full_text.split()),
            "segments": []
        }

    except Exception as e:
        print(f"Error: {e}")
        return None