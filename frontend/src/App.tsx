import { Menu, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useState } from 'react'
import AdminUploadPage from './components/AdminUploadPage'
import ChatWindow from './components/ChatWindow'
import Sidebar from './components/Sidebar'
import { useConversations } from './hooks/useConversations'
import { sendChatMessage } from './services/api'
import type { Message } from './types/chat'

function createAssistantMessage(content: string): Message {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content,
    createdAt: new Date().toISOString(),
  }
}

function generateConversationTitle(question: string): string {
  const words = question.trim().split(/\s+/).filter(Boolean)
  const title = words.slice(0, 4).join(' ')

  return title.length > 0 ? title : 'New chat'
}

function App() {
  const {
    conversations,
    activeConversation,
    activeConversationId,
    createNewConversation,
    selectConversation,
    deleteConversation,
    updateConversation,
  } = useConversations()

  const [isSidebarOpen, setSidebarOpen] = useState(false)
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [currentView, setCurrentView] = useState<'chat' | 'admin'>('chat')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSendMessage = async (message: string) => {
    const trimmedMessage = message.trim()

    if (!trimmedMessage || isLoading) {
      return
    }

    let conversationId = activeConversationId

    if (!conversationId) {
      const newConversation = createNewConversation()
      conversationId = newConversation.id
    }

    if (!conversationId) {
      return
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmedMessage,
      createdAt: new Date().toISOString(),
    }

    updateConversation(conversationId, (currentConversation) => ({
      ...currentConversation,
      title:
        currentConversation.title === 'New chat' || currentConversation.messages.length === 0
          ? generateConversationTitle(trimmedMessage)
          : currentConversation.title,
      updatedAt: new Date().toISOString(),
      messages: [...currentConversation.messages, userMessage],
    }))

    setError(null)
    setIsLoading(true)

    try {
      const response = await sendChatMessage(trimmedMessage)

      updateConversation(conversationId, (currentConversation) => ({
        ...currentConversation,
        updatedAt: new Date().toISOString(),
        messages: [...currentConversation.messages, createAssistantMessage(response.answer)],
      }))
    } catch (requestError) {
      const friendlyMessage =
        requestError instanceof Error
          ? requestError.message
          : 'The AI service is currently unavailable. Please try again in a moment.'

      setError(friendlyMessage)

      updateConversation(conversationId, (currentConversation) => ({
        ...currentConversation,
        updatedAt: new Date().toISOString(),
        messages: [
          ...currentConversation.messages,
          createAssistantMessage(
            "I couldn't reach the AI service right now. Please check the connection and try again.",
          ),
        ],
      }))
    } finally {
      setIsLoading(false)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    void handleSendMessage(suggestion)
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.12),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(16,185,129,0.10),_transparent_25%),linear-gradient(180deg,#f8fafc_0%,#eef5ff_100%)] text-slate-900 antialiased">
      <div className="mx-auto flex h-screen max-w-[1800px] overflow-hidden p-2 lg:p-4">
        <aside className="lg:flex">
          <Sidebar
            conversations={conversations}
            activeConversationId={activeConversationId}
            isCollapsed={isSidebarCollapsed}
            isOpen={isSidebarOpen}
            showSettings={showSettings}
            onToggleCollapse={() => setSidebarCollapsed((current) => !current)}
            onCloseMobile={() => setSidebarOpen(false)}
            onSelectConversation={(id) => {
              selectConversation(id)
              setCurrentView('chat')
              setSidebarOpen(false)
            }}
            onNewChat={() => {
              createNewConversation()
              setCurrentView('chat')
              setSidebarOpen(false)
            }}
            onDeleteConversation={(id) => deleteConversation(id)}
            onToggleSettings={() => setShowSettings((current) => !current)}
            onSelectAdminPage={() => {
              setCurrentView('admin')
              setSidebarOpen(false)
            }}
            currentView={currentView}
          />
        </aside>

        {isSidebarOpen && (
          <button
            type="button"
            aria-label="Close sidebar overlay"
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-30 bg-slate-900/20 lg:hidden"
          />
        )}

        <main className="relative flex min-w-0 flex-1 flex-col overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/85 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-sm">
          <header className="flex items-center justify-between border-b border-slate-200/90 bg-white/80 px-4 py-3 backdrop-blur-sm sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:border-slate-300 lg:hidden"
                aria-label="Open sidebar"
              >
                <Menu size={18} />
              </button>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSidebarCollapsed((current) => !current)}
                  className="hidden h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:border-slate-300 lg:inline-flex"
                  aria-label="Collapse sidebar"
                >
                  {isSidebarCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
                </button>

                <div>
                  <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-slate-400">
                    ICog AI
                  </p>
                  <h1 className="truncate text-base font-semibold text-slate-900 sm:text-lg">
                    {activeConversation?.title ?? 'ICOG RAG'}
                  </h1>
                </div>
              </div>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 shadow-sm shadow-emerald-100">
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
              Ready
            </div>
          </header>

          {currentView === 'admin' ? (
            <AdminUploadPage />
          ) : (
            <ChatWindow
              conversation={activeConversation}
              isLoading={isLoading}
              error={error}
              onSendMessage={handleSendMessage}
              onSuggestionClick={handleSuggestionClick}
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
