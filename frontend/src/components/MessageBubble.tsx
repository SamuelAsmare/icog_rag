import { Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import type { Message } from '../types/chat'

interface MessageBubbleProps {
  message: Message
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white shadow-sm">
          <Bot size={16} />
        </div>
      )}

      <div className={`max-w-[85%] rounded-2xl border px-4 py-3 shadow-sm ${isUser ? 'border-blue-100 bg-blue-50 text-slate-800' : 'border-slate-200 bg-white text-slate-700'}`}>
        <div className="markdown-content text-[15px] leading-7">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => <h1 className="mb-3 text-xl font-semibold text-slate-900">{children}</h1>,
              h2: ({ children }) => <h2 className="mb-3 text-lg font-semibold text-slate-900">{children}</h2>,
              h3: ({ children }) => <h3 className="mb-2 text-base font-semibold text-slate-900">{children}</h3>,
              p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
              ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-5">{children}</ul>,
              ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-5">{children}</ol>,
              li: ({ children }) => <li className="leading-7">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold text-slate-900">{children}</strong>,
              code: ({ inline, className, children, ...props }: any) => {
                const value = String(children).replace(/\n$/, '')
                const match = /language-(\w+)/.exec(className ?? '')

                if (inline) {
                  return (
                    <code className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[0.82em] text-slate-800" {...props}>
                      {value}
                    </code>
                  )
                }

                return match ? (
                  <SyntaxHighlighter
                    {...props}
                    style={oneLight}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{ margin: '0 0 1rem', borderRadius: '0.875rem', padding: '1rem', fontSize: '0.8rem' }}
                  >
                    {value}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {value}
                  </code>
                )
              },
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noreferrer" className="text-blue-600 underline underline-offset-2">
                  {children}
                </a>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>

      {isUser && (
        <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-600 text-white shadow-sm">
          <User size={16} />
        </div>
      )}
    </div>
  )
}
