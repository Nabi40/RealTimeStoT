# translate/consumers.py
# translate/consumers.py
import json
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils.translate import transcribe_audio_chunk

class TranscribeConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_buffer = b""
        
        # Audio Settings
        self.SAMPLE_RATE = 16000
        self.BYTES_PER_SEC = 32000 
        
        # SETTING: How much audio to process at once?
        # 1.5 seconds = 48000 bytes. 
        # This gives the AI enough context to understand the full word/sentence.
        self.CHUNK_SIZE = 48000 
        
        # SETTING: Overlap
        # Keep the last 0.5 seconds to ensure words aren't cut in half.
        self.OVERLAP_SIZE = 16000 

    async def connect(self):
        await self.accept()
        print("✅ Connected: Base Model + Smart Overlap")
        await self.send(json.dumps({"status": "CONNECTED"}))

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            # 1. Add new data to buffer
            self.audio_buffer += bytes_data

            # 2. Check if we have enough data (1.5 seconds)
            if len(self.audio_buffer) >= self.CHUNK_SIZE:
                
                # 3. Transcribe the current buffer
                result = transcribe_audio_chunk(self.audio_buffer)
                
                # 4. Handle Result
                if result and result.get("text"):
                    print(f"💬 {result['text']}")
                    await self.send(json.dumps({"text": result["text"]}))
                
                # 5. SMART OVERLAP (The Magic Fix)
                # Instead of clearing the buffer (self.audio_buffer = b""),
                # we keep the last 0.5 seconds. 
                # If you said "Amaz-ing", the "ing" stays in the buffer 
                # and joins the next chunk to become "ing day" -> "Amazing day".
                self.audio_buffer = self.audio_buffer[-self.OVERLAP_SIZE:]

    async def disconnect(self, close_code):
        pass