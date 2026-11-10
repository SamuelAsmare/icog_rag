import SuggestionCard from './SuggestionCard'

const suggestions = [
  'What is ICog’s core AI focus?',
  'Who is the founder of ICOg Labs',
  'Summarize the main document insights.',
  'List at least 3  teams in ICog labs',
]

interface WelcomeScreenProps {
  onSuggestionClick: (question: string) => void
}

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="flex h-full items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <div className="w-full max-w-4xl">
        <div className="mx-auto max-w-2xl rounded-[2rem] border border-slate-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.9),rgba(248,250,252,0.95))] p-8 text-center shadow-[0_18px_60px_rgba(15,23,42,0.05)]">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#dbeafe,#eff6ff)] text-blue-600 shadow-sm">
            <span className="text-2xl">✦</span>
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            Ask ICog’s knowledge assistant
          </h1>
          <p className="mt-3 text-base text-slate-600 sm:text-lg">
            Search the attached knowledge base and get grounded answers from the ICog document library.
          </p>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {suggestions.map((suggestion) => (
            <SuggestionCard key={suggestion} text={suggestion} onClick={onSuggestionClick} />
          ))}
        </div>
      </div>
    </div>
  )
}
