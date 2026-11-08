import {
  LogOut,
  MessageSquareText,
  Plus,
  Settings,
  Sparkles,
  Trash2,
  User,
} from 'lucide-react'
import type { Conversation } from '../types/chat'

interface SidebarProps {
  conversations: Conversation[]
  activeConversationId: string | null
  isCollapsed: boolean
  isOpen: boolean
  showSettings: boolean
  onToggleCollapse: () => void
  onCloseMobile: () => void
  onSelectConversation: (id: string) => void
  onNewChat: () => void
  onDeleteConversation: (id: string) => void
  onToggleSettings: () => void
}

export default function Sidebar({
  conversations,
  activeConversationId,
  isCollapsed,
  isOpen,
  showSettings,
  onToggleCollapse,
  onCloseMobile,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  onToggleSettings,
}: SidebarProps) {
  const sidebarWidthClasses = isCollapsed ? 'w-[88px]' : 'w-[290px]'

  return (
    <>
      <div
        className={`fixed inset-y-0 left-0 z-40 flex transform border-r border-slate-200 bg-slate-50/95 shadow-xl backdrop-blur-sm transition-transform duration-200 ease-out lg:static lg:shadow-none ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${sidebarWidthClasses}`}
      >
        <div className="flex h-full min-h-0 w-full flex-col">
          <div className={`flex items-center border-b border-slate-200 px-3 py-4 ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-sm font-semibold text-white shadow-sm shadow-blue-200">
                K
              </div>
              {!isCollapsed && <span className="text-lg font-semibold text-slate-900">Knowly AI</span>}
            </div>
            <button
              type="button"
              onClick={onToggleCollapse}
              className="hidden h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:border-slate-300 hover:text-slate-900 lg:flex"
              aria-label="Toggle sidebar"
            >
              <Sparkles size={16} />
            </button>
          </div>

          <div className={`px-3 py-3 ${isCollapsed ? 'px-2' : ''}`}>
            <button
              type="button"
              onClick={onNewChat}
              className={`flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-3 py-2.5 text-sm font-medium text-white shadow-sm shadow-blue-200 transition hover:bg-blue-500 ${
                isCollapsed ? 'px-2' : ''
              }`}
            >
              <Plus size={16} />
              {!isCollapsed && 'New Chat'}
            </button>
          </div>

          <div className={`flex-1 overflow-hidden ${isCollapsed ? 'px-1' : 'px-3'}`}>
            {!isCollapsed && (
              <div className="mb-3 flex items-center justify-between px-2 text-[11px] font-medium uppercase tracking-[0.2em] text-slate-400">
                <span>Recent</span>
              </div>
            )}

            <div className="space-y-2 overflow-y-auto pr-1">
              {conversations.map((conversation) => {
                const isSelected = activeConversationId === conversation.id

                return (
                  <div
                    key={conversation.id}
                    className={`group flex items-center gap-2 rounded-xl border px-2 py-2 transition ${
                      isSelected
                        ? 'border-blue-200 bg-blue-50 text-blue-700'
                        : 'border-transparent bg-transparent text-slate-600 hover:border-slate-200 hover:bg-white'
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        onSelectConversation(conversation.id)
                        onCloseMobile()
                      }}
                      className="flex min-w-0 flex-1 items-center gap-2 text-left"
                    >
                      <div
                        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                          isSelected ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'
                        }`}
                      >
                        <MessageSquareText size={15} />
                      </div>

                      {!isCollapsed && (
                        <span className="truncate text-sm font-medium">{conversation.title}</span>
                      )}
                    </button>

                    {!isCollapsed && (
                      <button
                        type="button"
                        onClick={() => onDeleteConversation(conversation.id)}
                        className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 opacity-0 transition hover:bg-slate-100 hover:text-red-500 group-hover:opacity-100"
                        aria-label={`Delete ${conversation.title}`}
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          <div className="border-t border-slate-200 px-3 py-3">
            {showSettings && !isCollapsed && (
              <div className="mb-3 rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600 shadow-sm">
                <div className="flex items-center justify-between py-1">
                  <span>Model</span>
                  <span className="font-medium text-slate-800">GPT-4o mini</span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span>Knowledge base</span>
                  <span className="font-medium text-slate-800">Active</span>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={onToggleSettings}
              className={`flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 ${
                isCollapsed ? 'justify-center px-2' : ''
              }`}
            >
              <Settings size={16} />
              {!isCollapsed && 'Settings'}
            </button>

            <div className={`mt-3 flex items-center gap-3 rounded-xl bg-white px-3 py-2.5 ${isCollapsed ? 'justify-center px-2' : ''}`}>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-xs font-semibold text-white">
                <User size={16} />
              </div>
              {!isCollapsed && (
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-900">Maya Chen</p>
                  <p className="truncate text-xs text-slate-500">Research lead</p>
                </div>
              )}
              {!isCollapsed && (
                <button type="button" className="text-slate-400 transition hover:text-slate-700" aria-label="Sign out">
                  <LogOut size={16} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
