import { ArrowUp, LoaderCircle } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

interface ChatInputProps {
  onSubmit: (message: string) => void
  isLoading: boolean
}

export default function ChatInput({ onSubmit, isLoading }: ChatInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  useEffect(() => {
    const textarea = textareaRef.current

    if (!textarea) {
      return
    }

    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`
  }, [value])

  const handleSubmit = () => {
    const trimmedValue = value.trim()

    if (!trimmedValue || isLoading) {
      return
    }

    onSubmit(trimmedValue)
    setValue('')
  }

  return (
    <div className="rounded-[1.5rem] border border-slate-200 bg-white p-2 shadow-[0_12px_30px_rgba(15,23,42,0.08)]">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault()
            handleSubmit()
          }
        }}
        rows={1}
        placeholder="Ask your knowledge base..."
        className="max-h-[180px] w-full resize-none border-0 bg-transparent px-3 py-2 text-[15px] text-slate-700 placeholder:text-slate-400 focus:outline-none"
        aria-label="Message input"
        disabled={isLoading}
      />

      <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-2 pb-1 pt-3">
        <p className="text-[11px] text-slate-400">
          AI-generated responses may contain inaccuracies. Verify important information.
        </p>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white shadow-sm shadow-blue-200 transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400 disabled:shadow-none"
          aria-label="Send message"
        >
          {isLoading ? <LoaderCircle size={18} className="animate-spin" /> : <ArrowUp size={18} />}
        </button>
      </div>
    </div>
  )
}
