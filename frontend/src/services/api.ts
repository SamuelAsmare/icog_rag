import type { ChatResponse } from '../types/chat'

const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:4000').replace(/\/$/, '')

export interface UploadDocumentResponse {
  success: boolean
  message: string
  document_id?: string
  filename?: string
  page_count?: number
  chunk_count?: number
  storage_path?: string
}

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

export async function uploadDocument(file: File): Promise<UploadDocumentResponse> {
  const formData = new FormData()
  formData.append('file', file, file.name)

  const response = await fetch(`${API_URL}/api/documents`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response))
  }

  return (await response.json()) as UploadDocumentResponse
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  try {
    const questionResponse = await fetch(`${API_URL}/api/userquestion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question: message }),
    })

    if (!questionResponse.ok) {
      throw new Error(await parseErrorMessage(questionResponse))
    }

    const questionData = (await questionResponse.json()) as {
      request_id?: string
      sources?: Array<{ filename?: string; page_number?: number }>
    }

    const requestId = questionData.request_id
    if (!requestId) {
      throw new Error('The AI service did not return a request ID.')
    }

    const answerResponse = await fetch(`${API_URL}/api/answer?request_id=${encodeURIComponent(requestId)}`)

    if (!answerResponse.ok) {
      throw new Error(await parseErrorMessage(answerResponse))
    }

    const answerData = (await answerResponse.json()) as Partial<ChatResponse>

    if (typeof answerData.answer !== 'string') {
      throw new Error('The AI service returned an invalid response.')
    }

    return {
      answer: answerData.answer,
      sources: Array.isArray(answerData.sources)
        ? answerData.sources.filter((source): source is string => typeof source === 'string')
        : Array.isArray(questionData.sources)
          ? questionData.sources
              .filter((source) => typeof source.filename === 'string')
              .map((source) => `${source.filename} (page ${source.page_number ?? 'unknown'})`)
          : [],
    }
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(error.message || 'Unable to connect to the AI service right now.')
    }

    throw new Error('Unable to connect to the AI service right now.')
  }
}
