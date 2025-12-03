# translate/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils.translate import transcribe_audio_chunk

class TranscribeConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()
        await self.send(json.dumps({"status": "CONNECTED"}))

    async def receive(self, text_data=None, bytes_data=None):
        # 1. Handle Binary Audio Data (ArrayBuffer)
        if bytes_data:
            # Pass the raw binary data to the transcriber
            result = transcribe_audio_chunk(bytes_data)

            # Only send response if we got actual text back
            if result and result.get("text"):
                await self.send(json.dumps({
                    "text": result["text"],
                    "duration": result.get("duration", 0),
                    "word_count": result.get("word_count", 0),
                    "segments": result.get("segments", []),
                }))

        # 2. Handle Text Command Data (e.g., Stop signal)
        if text_data:
            try:
                data = json.loads(text_data)
                if data.get('type') == 'stop':
                    # Optional: reset internal buffers if you were accumulating audio
                    pass
            except json.JSONDecodeError:
                pass

    async def disconnect(self, close_code):
        pass