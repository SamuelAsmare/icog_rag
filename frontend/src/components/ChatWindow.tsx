import { LoaderCircle, Sparkles } from 'lucide-react'
import { useEffect, useRef } from 'react'
import type { Conversation } from '../types/chat'
import ChatInput from './ChatInput'
import MessageBubble from './MessageBubble'
import WelcomeScreen from './WelcomeScreen'

interface ChatWindowProps {
  conversation: Conversation | null
  isLoading: boolean
  error: string | null
  onSendMessage: (message: string) => void
  onSuggestionClick: (message: string) => void
}

const AUTO_SCROLL_OFFSET = 120

export default function ChatWindow({ conversation, isLoading, error, onSendMessage, onSuggestionClick }: ChatWindowProps) {
  const hasMessages = Boolean(conversation && conversation.messages.length > 0)
  const scrollContainerRef = useRef<HTMLDivElement | null>(null)
  const shouldScrollOnNewMessageRef = useRef(false)

  const isNearBottom = (container: HTMLDivElement) => {
    return container.scrollHeight - container.scrollTop - container.clientHeight <= AUTO_SCROLL_OFFSET
  }

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    const container = scrollContainerRef.current

    if (!container) {
      return
    }

    container.scrollTo({
      top: container.scrollHeight,
      behavior,
    })
  }

  useEffect(() => {
    const container = scrollContainerRef.current

    if (!container || (!hasMessages && !isLoading)) {
      return
    }

    const shouldAutoScroll = shouldScrollOnNewMessageRef.current || isNearBottom(container)

    if (!shouldAutoScroll) {
      return
    }

    const frameId = window.requestAnimationFrame(() => scrollToBottom('smooth'))
    shouldScrollOnNewMessageRef.current = false

    return () => window.cancelAnimationFrame(frameId)
  }, [conversation?.messages, hasMessages, isLoading])

  const handleSubmit = (message: string) => {
    shouldScrollOnNewMessageRef.current = true
    onSendMessage(message)
  }

  const handleSuggestionSubmit = (message: string) => {
    shouldScrollOnNewMessageRef.current = true
    onSuggestionClick(message)
  }

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.06),_transparent_35%)]">
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-4 pb-6 pt-5 sm:px-6 lg:px-8">
        {error && (
          <div className="mx-auto mb-4 max-w-4xl rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 shadow-sm">
            {error}
          </div>
        )}

        {hasMessages ? (
          <div className="mx-auto max-w-4xl space-y-5 pb-4">
            {conversation?.messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {isLoading && (
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[linear-gradient(135deg,#0f172a,#334155)] text-white shadow-sm">
                  <Sparkles size={16} />
                </div>
                <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
                  <LoaderCircle size={15} className="animate-spin text-blue-600" />
                  Thinking...
                </div>
              </div>
            )}
          </div>
        ) : (
          <WelcomeScreen onSuggestionClick={handleSuggestionSubmit} />
        )}
      </div>

      <div className="border-t border-slate-200/80 bg-slate-50/70 px-4 pb-4 pt-3 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <ChatInput onSubmit={handleSubmit} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}
