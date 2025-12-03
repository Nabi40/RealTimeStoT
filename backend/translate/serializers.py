# translate/serializers.py
from rest_framework import serializers

class AudioChunkSerializer(serializers.Serializer):
    audio = serializers.FileField(required=True)
