import { useCallback, useState } from 'react'
import type { Conversation } from '../types/chat'

const STORAGE_KEY = 'icog-rag-conversations-v1'

function createConversation(title = 'New chat'): Conversation {
  const now = new Date().toISOString()

  return {
    id: crypto.randomUUID(),
    title,
    messages: [],
    createdAt: now,
    updatedAt: now,
  }
}

function readStoredConversations(): Conversation[] {
  if (typeof window === 'undefined') {
    return []
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)

    if (!raw) {
      return []
    }

    const parsed = JSON.parse(raw) as Conversation[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function useConversations() {
  const [conversationState, setConversationState] = useState(() => {
    const stored = readStoredConversations()
    const initialConversations = stored.length > 0 ? stored : [createConversation()]

    return {
      conversations: initialConversations,
      activeConversationId: initialConversations[0]?.id ?? null,
    }
  })

  const { conversations, activeConversationId } = conversationState

  const persistConversations = useCallback((nextConversations: Conversation[]) => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextConversations))
    }
  }, [])

  const updateConversation = useCallback(
    (id: string, updater: (conversation: Conversation) => Conversation) => {
      setConversationState((current) => {
        const nextConversations = current.conversations.map((conversation) =>
          conversation.id === id ? updater(conversation) : conversation,
        )

        persistConversations(nextConversations)

        return {
          conversations: nextConversations,
          activeConversationId: current.activeConversationId,
        }
      })
    },
    [persistConversations],
  )

  const createNewConversation = useCallback((title = 'New chat') => {
    const nextConversation = createConversation(title)

    setConversationState((current) => {
      const nextConversations = [nextConversation, ...current.conversations]
      persistConversations(nextConversations)

      return {
        conversations: nextConversations,
        activeConversationId: nextConversation.id,
      }
    })

    return nextConversation
  }, [persistConversations])

  const selectConversation = useCallback((id: string) => {
    setConversationState((current) => ({
      ...current,
      activeConversationId: id,
    }))
  }, [])

  const deleteConversation = useCallback(
    (id: string) => {
      setConversationState((current) => {
        const nextConversations = current.conversations.filter((conversation) => conversation.id !== id)

        if (nextConversations.length === 0) {
          const replacement = createConversation()
          const saved = [replacement]
          persistConversations(saved)

          return {
            conversations: saved,
            activeConversationId: replacement.id,
          }
        }

        const nextActiveConversationId =
          current.activeConversationId === id ? nextConversations[0].id : current.activeConversationId

        persistConversations(nextConversations)

        return {
          conversations: nextConversations,
          activeConversationId: nextActiveConversationId,
        }
      })
    },
    [persistConversations],
  )

  const activeConversation =
    conversations.find((conversation) => conversation.id === activeConversationId) ?? conversations[0] ?? null

  return {
    conversations,
    activeConversationId,
    activeConversation,
    createNewConversation,
    selectConversation,
    deleteConversation,
    updateConversation,
  }
}
