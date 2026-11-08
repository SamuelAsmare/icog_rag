import type { ChatResponse } from '../types/chat'

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:4000').replace(/\/$/, '')

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const errorData = await response.json()

    if (typeof errorData?.message === 'string') {
      return errorData.message
    }

    if (typeof errorData?.error === 'string') {
      return errorData.error
    }

    return `The server returned an error (${response.status}).`
  } catch {
    return `The server returned an error (${response.status}).`
  }
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    })

    if (!response.ok) {
      throw new Error(await parseErrorMessage(response))
    }

    const data = (await response.json()) as Partial<ChatResponse>

    if (typeof data.answer !== 'string') {
      throw new Error('The AI service returned an invalid response.')
    }

    return {
      answer: data.answer,
      sources: Array.isArray(data.sources)
        ? data.sources.filter((source): source is string => typeof source === 'string')
        : [],
    }
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(error.message || 'Unable to connect to the AI service right now.')
    }

    throw new Error('Unable to connect to the AI service right now.')
  }
}
