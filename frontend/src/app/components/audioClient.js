// audioClient.js
let socket = null;

export const connectWebsocket = (onMessage, url = process.env.NEXT_PUBLIC_WS_URL) => {
  return new Promise((resolve, reject) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      resolve(socket);
      return;
    }

    socket = new WebSocket(url);
    
    // IMPORTANT: specific binary type for raw data handling
    socket.binaryType = 'arraybuffer';

    socket.onopen = () => {
      console.log('Connected to WebSocket');
      resolve(socket);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch (err) {
        console.error('Failed to parse transcription payload', err);
      }
    };

    socket.onerror = (err) => {
      console.error('WebSocket error', err);
      reject(err);
    };

    socket.onclose = () => {
      console.log('WebSocket closed');
      socket = null;
    };
  });
};

export const getActiveSocket = () => socket;

export const sendStopSignal = () => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    // We send control signals as text (JSON), not binary
    socket.send(JSON.stringify({ type: 'stop' }));
  }
};