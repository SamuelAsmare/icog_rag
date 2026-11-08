interface SuggestionCardProps {
  text: string
  onClick: (text: string) => void
}

export default function SuggestionCard({ text, onClick }: SuggestionCardProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(text)}
      className="rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-blue-200 hover:bg-blue-50 hover:shadow-sm"
    >
      <span className="text-sm font-medium text-slate-700">{text}</span>
    </button>
  )
}
