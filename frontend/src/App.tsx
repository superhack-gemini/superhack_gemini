import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { generateNarrative, type VideoResult } from './services/narrativeService'

type AppState = 'idle' | 'generating' | 'complete'

const steps = [
  'Collecting game footage...',
  'Generating commentary...',
  'Stitching final narrative...',
]

const progressValues = [0.25, 0.6, 0.9]
const phaseDurations = [1400, 1400, 1400]

function App() {
  const [prompt, setPrompt] = useState('')
  const [state, setState] = useState<AppState>('idle')
  const [activeStep, setActiveStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<VideoResult | null>(null)
  const [error, setError] = useState('')
  const timeoutRef = useRef<number[]>([])

  const clearTimers = () => {
    timeoutRef.current.forEach((timeoutId) => clearTimeout(timeoutId))
    timeoutRef.current = []
  }

  useEffect(() => {
    return () => clearTimers()
  }, [])

  const startProgressSimulation = () => {
    clearTimers()
    setActiveStep(0)
    setProgress(progressValues[0])

    let elapsed = 0
    phaseDurations.slice(0, steps.length - 1).forEach((duration, index) => {
      elapsed += duration
      const timeoutId = window.setTimeout(() => {
        setActiveStep(index + 1)
        setProgress(progressValues[index + 1] ?? 0.9)
      }, elapsed)
      timeoutRef.current.push(timeoutId)
    })
  }

  const handleGenerate = async () => {
    const trimmed = prompt.trim()
    if (!trimmed) {
      setError('Please enter a prompt to generate a narrative.')
      return
    }

    setError('')
    setState('generating')
    setResult(null)
    startProgressSimulation()

    try {
      const response = await generateNarrative(trimmed)
      setResult(response)
      setProgress(1)
      setState('complete')
      setActiveStep(steps.length - 1)
    } finally {
      clearTimers()
    }
  }

  const handleReset = () => {
    clearTimers()
    setPrompt('')
    setResult(null)
    setProgress(0)
    setActiveStep(0)
    setState('idle')
    setError('')
  }

  const isGenerating = state === 'generating'
  const isComplete = state === 'complete'

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="relative min-h-screen overflow-hidden">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -top-40 left-1/2 h-[520px] w-[520px] -translate-x-1/2 rounded-full bg-indigo-500/20 blur-[160px]" />
          <div className="absolute bottom-0 right-0 h-[420px] w-[420px] rounded-full bg-emerald-400/10 blur-[160px]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(15,23,42,0.4),_transparent_55%)]" />
        </div>

        <main className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-12">
          <header className="flex items-center justify-between text-sm text-slate-300">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-sm font-semibold">
                GS
              </span>
              <div className="flex flex-col">
                <span className="text-xs uppercase tracking-[0.3em] text-emerald-300/80">
                  Gemini Sports
                </span>
                <span className="text-base font-semibold text-white">
                  Narrative Studio
                </span>
              </div>
            </div>
            <span className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white/80 md:inline-flex">
              Premium mock experience
            </span>
          </header>

          <section className="flex flex-1 flex-col justify-center gap-10">
            {!isComplete && (
              <div className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur-xl">
                <div className="space-y-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-emerald-300/80">
                    Prompt
                  </p>
                  <h1 className="text-3xl font-semibold text-white md:text-4xl">
                    Generate a cinematic sports narrative in seconds.
                  </h1>
                  <p className="max-w-2xl text-sm text-slate-300 md:text-base">
                    Ask for a highlight story, tactical breakdown, or legendary
                    comeback. We will simulate sourcing footage, voiceover, and
                    the final edit.
                  </p>
                </div>

                <div className="mt-6 space-y-4">
                  <textarea
                    className="min-h-[140px] w-full resize-none rounded-2xl border border-white/10 bg-slate-950/40 p-4 text-lg text-white placeholder:text-slate-500 focus:border-emerald-300/60 focus:outline-none focus:ring-2 focus:ring-emerald-300/20"
                    placeholder="Ask for a Super Bowl story…"
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                    disabled={isGenerating}
                  />
                  {error && (
                    <p className="text-sm text-rose-300">{error}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-4">
                    <button
                      className="inline-flex items-center justify-center rounded-full bg-gradient-to-r from-emerald-400 via-emerald-300 to-teal-300 px-6 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                      onClick={handleGenerate}
                      disabled={isGenerating}
                    >
                      {isGenerating ? 'Generating…' : 'Generate'}
                    </button>
                    <p className="text-xs text-slate-400">
                      Full-screen cinematic output • 16:9 hero card
                    </p>
                  </div>
                </div>
              </div>
            )}

            <AnimatePresence mode="wait">
              {isGenerating && (
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  className="rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl"
                >
                  <div className="flex flex-col gap-6">
                    <div className="space-y-2">
                      <p className="text-xs uppercase tracking-[0.3em] text-emerald-300/80">
                        Generation
                      </p>
                      <h2 className="text-2xl font-semibold text-white">
                        {steps[activeStep]}
                      </h2>
                    </div>
                    <div className="space-y-4">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-300"
                          animate={{ width: `${Math.round(progress * 100)}%` }}
                          transition={{ duration: 0.4 }}
                        />
                      </div>
                      <div className="grid gap-3 md:grid-cols-3">
                        {steps.map((step, index) => (
                          <div
                            key={step}
                            className={`flex items-center gap-2 rounded-2xl border px-3 py-2 text-xs font-medium ${
                              index === activeStep
                                ? 'border-emerald-300/40 bg-emerald-300/10 text-emerald-100'
                                : index < activeStep
                                  ? 'border-emerald-300/20 bg-white/5 text-white/70'
                                  : 'border-white/10 bg-white/5 text-white/50'
                            }`}
                          >
                            <span
                              className={`h-2 w-2 rounded-full ${
                                index <= activeStep
                                  ? 'bg-emerald-300'
                                  : 'bg-white/30'
                              }`}
                            />
                            {step}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            <AnimatePresence mode="wait">
              {isComplete && result && (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, scale: 0.98, y: 12 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.98, y: -12 }}
                  transition={{ duration: 0.4 }}
                  className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-black/40 backdrop-blur-xl"
                >
                  <div className="flex flex-col gap-6">
                    <div className="space-y-2">
                      <p className="text-xs uppercase tracking-[0.3em] text-emerald-300/80">
                        Final Narrative
                      </p>
                      <h2 className="text-3xl font-semibold text-white md:text-4xl">
                        {result.title}
                      </h2>
                      <p className="max-w-3xl text-sm text-slate-300 md:text-base">
                        {result.description}
                      </p>
                    </div>
                    <div className="overflow-hidden rounded-3xl border border-white/10 bg-slate-950/60">
                      <video
                        className="aspect-video w-full"
                        controls
                        preload="metadata"
                        src={result.videoUrl}
                      />
                    </div>
                    <div className="flex flex-wrap items-center gap-4">
                      <button
                        className="inline-flex items-center justify-center rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:border-white/40"
                        onClick={handleReset}
                      >
                        Generate another
                      </button>
                      <span className="text-xs text-slate-400">
                        Ready for API swap • Mocked locally
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </section>
        </main>
      </div>
    </div>
  )
}

export default App
