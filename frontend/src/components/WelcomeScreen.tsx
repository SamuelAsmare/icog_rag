import SuggestionCard from './SuggestionCard'

const suggestions = [
  'What is database indexing?',
  'How does Redis improve application performance?',
  'Explain the difference between SQL and NoSQL.',
  'What is Retrieval-Augmented Generation?',
]

interface WelcomeScreenProps {
  onSuggestionClick: (question: string) => void
}

export default function WelcomeScreen({ onSuggestionClick }: WelcomeScreenProps) {
  return (
    <div className="flex h-full items-center justify-center px-4 py-10 sm:px-6 lg:px-8">
      <div className="w-full max-w-4xl">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl">
            What would you like to know?
          </h1>
          <p className="mt-3 text-base text-slate-600 sm:text-lg">
            Ask questions and get intelligent answers from your knowledge base.
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
