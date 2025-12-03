"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  connectWebsocket,
  getActiveSocket,
  sendStopSignal,
} from "./audioClient";

// --- Helper: Convert Float32 (Browser) to Int16 (Backend) ---
const float32ToInt16 = (float32Array) => {
  const int16Array = new Int16Array(float32Array.length);
  for (let i = 0; i < float32Array.length; i++) {
    let s = Math.max(-1, Math.min(1, float32Array[i])); // Clamp
    s = s < 0 ? s * 0x8000 : s * 0x7fff; // Scale
    int16Array[i] = s;
  }
  return int16Array.buffer;
};

const processPayload = (payload, fallbackDuration = 0) => {
  const text = payload.text ?? payload.transcript ?? "";
  const durationRaw = payload.duration ?? payload.durationSeconds;
  const duration =
    typeof durationRaw === "number"
      ? durationRaw
      : parseFloat(durationRaw ?? "") || fallbackDuration;

  const wordCountFromText =
    typeof text === "string" && text.trim().length > 0
      ? text.trim().split(/\s+/).length
      : 0;

  return {
    text,
    duration,
    word_count: payload.word_count ?? payload.wordCount ?? wordCountFromText,
    segments: payload.segments ?? [],
    timestamp: payload.timestamp ?? "",
  };
};

export default function Text() {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [wsReady, setWsReady] = useState(false);

  // Refs for AudioContext management
  const audioContextRef = useRef(null);
  const streamRef = useRef(null);
  const processorRef = useRef(null);
  const inputSourceRef = useRef(null);

  const timerRef = useRef(null);
  const wsRef = useRef(null);
  const elapsedRef = useRef(0);

  useEffect(() => {
    let isMounted = true;

    connectWebsocket((payload) => {
      setResult((prev) =>
        processPayload(payload, prev?.duration ?? elapsedRef.current)
      );
    })
      .then((ws) => {
        if (!isMounted) return;
        wsRef.current = ws;
        setWsReady(true);
      })
      .catch((err) => {
        console.error("WebSocket connection failed", err);
        if (isMounted) setWsReady(false);
      });

    return () => {
      isMounted = false;
      stopRecording(); // Cleanup on unmount
    };
  }, []);

  useEffect(() => {
    elapsedRef.current = elapsed;
  }, [elapsed]);

  const clearSession = () => {
    setResult(null);
    setElapsed(0);
    elapsedRef.current = 0;
  };

  const startRecording = async () => {
    clearSession();

    const socket = getActiveSocket();
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      alert("WebSocket connection is not ready yet. Please try again.");
      return;
    }

    try {
      // 1. Get Microphone Stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000, // Try to request 16k
          channelCount: 1,
          echoCancellation: true,
          autoGainControl: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;

      // 2. Initialize AudioContext
      const audioContext = new (window.AudioContext ||
        window.webkitAudioContext)({
        sampleRate: 16000, // Force 16k context if possible
      });
      audioContextRef.current = audioContext;

      // 3. Create Source
      const source = audioContext.createMediaStreamSource(stream);
      inputSourceRef.current = source;

      // 4. Create Processor (BufferSize, InputChannels, OutputChannels)
      // Buffer size 4096 gives ~0.25s chunks at 16kHz
      const processor = audioContext.createScriptProcessor(2048, 1, 1);
      processorRef.current = processor;

      // 5. Handle Audio Data
      processor.onaudioprocess = (e) => {
        if (!isRecording && socket.readyState !== WebSocket.OPEN) return;

        const inputData = e.inputBuffer.getChannelData(0); // Raw Float32
        
        // Convert to Int16 PCM
        const pcmData = float32ToInt16(inputData);

        // Send to Backend
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(pcmData);
        }
      };

      // 6. Connect the graph
      source.connect(processor);
      processor.connect(audioContext.destination); // Required for script processor to run

      setIsRecording(true);
      timerRef.current = setInterval(() => {
        setElapsed((s) => s + 1);
      }, 1000);
    } catch (err) {
      console.error(err);
      alert("Could not start recording: " + (err.message || err));
    }
  };

  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }

    setIsRecording(false);

    // Stop Audio Context & Processor
    if (inputSourceRef.current) {
      inputSourceRef.current.disconnect();
      inputSourceRef.current = null;
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop Stream Tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    sendStopSignal();
  };

  const toggleRecording = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  const formatTime = (s) => {
    const mm = String(Math.floor(s / 60)).padStart(2, "0");
    const ss = String(s % 60).padStart(2, "0");
    return `${mm}:${ss}`;
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-gray-100 border border-gray-300 rounded-t-lg px-4 py-2 flex items-center shadow-sm">
        <h2 className="text-lg text-black font-semibold">
          Turn your voice in Text
        </h2>
      </div>

      <div
        className="relative bg-white border border-gray-300 rounded-b-lg overflow-hidden shadow-lg"
        style={{ height: 420 }}
      >
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage:
              "radial-gradient(circle at 10px 10px, rgba(0,0,0,0.03) 1px, transparent 1px)",
            opacity: 0.6,
          }}
        />

        <div className="relative z-10 h-full flex flex-col justify-between">
          <div className="p-6 overflow-auto space-y-6">
            <div className="flex justify-center items-center space-x-4">
              <div className="bg-gray-100 flex justify-center items-center text-gray-900 rounded-xl p-4 max-w-xl shadow">
                <div className="text-sm">
                  Hi, welcome to Turn your voice in Text! Go ahead and send me a
                  message. <span className="ml-1">😊</span>
                </div>
                <span className="absolute right-6 text-xs text-gray-500">
                  12:45
                </span>
              </div>
            </div>

            <div className="flex items-start justify-end space-x-4"></div>
          </div>

          <div className="px-4 py-3 bg-gray-200 border-t border-gray-300">
            <div className="max-w-full mx-auto flex items-center gap-3">
              <input
                aria-label="Message"
                className="flex-1 bg-white placeholder-gray-400 rounded-lg px-4 py-3 shadow-inner focus:outline-none"
                placeholder="Enter your message..."
              />

              <button
                type="button"
                disabled={!wsReady}
                aria-pressed={isRecording}
                onClick={toggleRecording}
                className={`${
                  isRecording
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-green-500 hover:bg-green-600"
                } ${
                  !wsReady ? "opacity-50 cursor-not-allowed" : ""
                } text-white rounded-lg p-3 flex items-center justify-center shadow-md`}
                title={
                  !wsReady
                    ? "Connecting to server..."
                    : isRecording
                    ? "Stop session"
                    : "Start session"
                }
              >
                {isRecording ? (
                  <div className="flex items-center gap-2">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <rect x="6" y="6" width="12" height="12" rx="2" />
                    </svg>
                    <span className="text-sm font-mono">
                      {formatTime(elapsed)}
                    </span>
                  </div>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 3v18" stroke="currentColor" />
                    <path d="M5 8c0 7 2 9 7 9s7-2 7-9" stroke="currentColor" />
                  </svg>
                )}
              </button>
            </div>

            {result && (
              <div className="mt-3 bg-white p-3 rounded-md shadow-inner text-sm text-gray-800">
                <div className="font-medium">Transcription result</div>
                <div className="mt-1 text-gray-700">{result.text}</div>
                <div className="mt-2 text-xs text-gray-500">
                  Duration: {result.duration}s • Words: {result.word_count} •{" "}
                  {result.timestamp}
                </div>

                {Array.isArray(result.segments) &&
                  result.segments.length > 0 && (
                    <div className="mt-2 text-xs text-gray-600">
                      <div className="font-semibold">Segments</div>
                      <ul className="list-disc pl-5">
                        {result.segments.map((s, i) => (
                          <li key={i}>
                            [{s.start} - {s.end}] {s.text}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}