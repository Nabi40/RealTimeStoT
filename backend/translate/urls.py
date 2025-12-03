from django.urls import path
from .views import RealTimeTranscribeAPIView


urlpatterns = [
    path("transcribe/", RealTimeTranscribeAPIView.as_view(), name="transcribe"),
]