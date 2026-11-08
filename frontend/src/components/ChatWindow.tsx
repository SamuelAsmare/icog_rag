import { LoaderCircle, Sparkles } from 'lucide-react'
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

export default function ChatWindow({ conversation, isLoading, error, onSendMessage, onSuggestionClick }: ChatWindowProps) {
  const hasMessages = Boolean(conversation && conversation.messages.length > 0)

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4 sm:px-6 lg:px-8">
        {error && (
          <div className="mx-auto mb-4 max-w-4xl rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
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
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-900 text-white shadow-sm">
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
          <WelcomeScreen onSuggestionClick={onSuggestionClick} />
        )}
      </div>

      <div className="border-t border-slate-200 bg-slate-50/80 px-4 pb-4 pt-3 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl">
          <ChatInput onSubmit={onSendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  )
}
