import { NextResponse } from 'next/server'

// Simple mock endpoint so the UI can demo the recording workflow locally.
export async function POST(request) {
  try {
    const formData = await request.formData()
    const duration = parseFloat(formData.get('duration')) || 0

    // In a real app you would forward the audio blob in `formData.get('file')`
    // to your transcription provider here.
    const mockResponse = {
      text: 'hello how are you',
      duration: duration || 2.412,
      word_count: 4,
      segments: [
        { start: 0.0, end: 1.2, text: 'hello' },
        { start: 1.2, end: 2.4, text: 'how are you' },
      ],
    }

    return NextResponse.json(mockResponse)
  } catch (err) {
    console.error('Mock transcription failed:', err)
    return NextResponse.json({ message: 'Transcription failed' }, { status: 500 })
  }
}

