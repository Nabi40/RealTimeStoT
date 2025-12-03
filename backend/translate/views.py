from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AudioChunkSerializer
from .utils.translate import transcribe_audio_chunk

class RealTimeTranscribeAPIView(APIView):

    def post(self, request, *args, **kwargs):
        serializer = AudioChunkSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        audio_file = serializer.validated_data["audio"]
        audio_bytes = audio_file.read()

        result = transcribe_audio_chunk(audio_bytes)

        # FIX: Ensure we return a valid object even if VAD detects silence
        if not result:
            return Response({
                "text": "",
                "duration": 0.0,
                "word_count": 0,
                "segments": []
            }, status=status.HTTP_200_OK)

        return Response(result, status=status.HTTP_200_OK)