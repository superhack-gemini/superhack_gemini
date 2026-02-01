import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { HeroCinematicBackground } from './components/HeroCinematicBackground'
import { generateNarrative, type VideoResult } from './services/narrativeService'

type AppState = 'idle' | 'generating' | 'complete'

const steps = [
  'Researching Topic',
  'Generating Script',
  'Creating Video',
  'Final Assembly',
]

const progressValues = [0.15, 0.35, 0.65, 0.9]
const phaseDurations = [3000, 5000, 8000, 4000]

function App() {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [state, setState] = useState<AppState>('idle')
  const [activeStep, setActiveStep] = useState(0)
  const [progress, setProgress] = useState(0)
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
      setError('Enter a directive to begin the broadcast.')
      return
    }

    setError('')
    setState('generating')
    startProgressSimulation()

    try {
      const response: VideoResult = await generateNarrative(trimmed)
      
      // Redirect to video page with the result
      setProgress(1)
      clearTimers()
      
      // Navigate to video page with state
      navigate(`/video/${response.taskId}`, {
        state: {
          title: response.title,
          description: response.description,
          videoUrl: response.videoUrl,
        }
      })
    } catch (err) {
      clearTimers()
      setState('idle')
      setProgress(0)
      setActiveStep(0)
      setError(err instanceof Error ? err.message : 'Generation failed')
    }
  }

  const isGenerating = state === 'generating'

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="relative min-h-screen overflow-hidden">
        {/* Cinematic video background */}
        <HeroCinematicBackground />
        
        <div className="pointer-events-none absolute inset-0 aurora-bg">
          <div className="absolute -top-64 left-1/2 h-[640px] w-[640px] -translate-x-1/2 rounded-full bg-sky-500/10 blur-[200px]" />
          <div className="absolute -bottom-40 left-[-140px] h-[520px] w-[520px] rounded-full bg-indigo-500/10 blur-[190px]" />
          <div className="absolute right-[-80px] top-1/4 h-[520px] w-[520px] rounded-full bg-violet-500/10 blur-[210px]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(15,23,42,0.7),_transparent_62%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(120%_120%_at_10%_10%,_rgba(56,189,248,0.12),_transparent_55%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(120%_120%_at_90%_0%,_rgba(129,140,248,0.12),_transparent_60%)]" />
        </div>
        <div className="pointer-events-none absolute inset-0 field-lines" />
        <div className="pointer-events-none absolute inset-0 stadium-lights" />
        <div className="pointer-events-none absolute inset-0 cinematic-vignette" />
        <div className="pointer-events-none absolute inset-0 stadium-bloom" />
        <div className="pointer-events-none absolute inset-0 grain-overlay" />

        <main className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-12">
          <header className="flex items-center justify-between text-sm text-slate-300">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/10 text-sm font-semibold tracking-[0.12em] text-white/90">
                GS
              </span>
              <div className="flex flex-col">
                <span className="text-xs uppercase tracking-[0.32em] text-sky-200/80">
                  Gemini Sports
                </span>
                <span className="text-base font-semibold text-white">
                  Narrative Studio
                </span>
              </div>
            </div>
            <span className="hidden rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium uppercase tracking-[0.28em] text-white/80 md:inline-flex">
              Gemini 3 × Super Bowl Week
            </span>
          </header>

          <section className="flex flex-1 flex-col justify-center gap-10">
            {!isGenerating && (
              <div className="broadcast-frame hero-shell rounded-3xl border border-white/10 bg-white/5 p-8 shadow-[0_30px_120px_rgba(5,10,25,0.7)] backdrop-blur-2xl transition">
                <div className="hero-atmosphere" aria-hidden="true">
                  <div className="hero-crowd" />
                  <div className="hero-field-glow" />
                  <div className="hero-haze" />
                </div>
                <div className="space-y-3">
                  <h1 className="hero-headline text-3xl font-semibold text-white md:text-5xl">
                    Direct a Super Bowl narrative with Gemini 3.
                  </h1>
                  <p className="max-w-2xl text-sm text-slate-300 md:text-base">
                    Request a highlight sequence, tactical analysis, or legacy
                    recap. We will simulate footage sourcing, commentary, and
                    final edit.
                  </p>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="console-input">
                    <textarea
                      className="console-textarea min-h-[160px] w-full resize-none rounded-2xl border border-white/10 bg-slate-950/60 p-4 text-lg text-white placeholder:text-slate-500 shadow-[0_0_40px_rgba(15,23,42,0.6)] transition focus:border-sky-200/70 focus:outline-none focus:ring-2 focus:ring-sky-300/20"
                      placeholder="Describe the Super Bowl narrative you want..."
                      value={prompt}
                      onChange={(event) => setPrompt(event.target.value)}
                      disabled={isGenerating}
                    />
                  </div>
                  {error && (
                    <p className="text-sm text-rose-300">{error}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-4">
                    <button
                      className="cta-pulse inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-400 via-indigo-300 to-violet-300 px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_12px_30px_rgba(56,189,248,0.35)] transition hover:brightness-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-300/40 disabled:cursor-not-allowed disabled:opacity-60"
                      onClick={handleGenerate}
                      disabled={isGenerating}
                    >
                      <svg
                        className="h-4 w-4"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.4"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        aria-hidden="true"
                      >
                        <path d="M3.5 12h7.5" />
                        <path d="M11 12l-2.2-2.2" />
                        <path d="M11 12l-2.2 2.2" />
                        <path d="M11 12h9.5" />
                        <path d="M20.5 7.5c-1.4 1.2-3.2 2-5.4 2.4" />
                        <path d="M20.5 16.5c-1.4-1.2-3.2-2-5.4-2.4" />
                      </svg>
                      Begin Broadcast
                    </button>
                    <p className="text-xs text-slate-400">
                      Broadcast-ready output • 16:9 replay frame
                    </p>
                  </div>
                </div>
              </div>
            )}

            <AnimatePresence mode="wait">
              {isGenerating && (
                <motion.div
                  key="progress"
                  initial={{ opacity: 0, x: 24 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -24 }}
                  transition={{ duration: 0.5, ease: 'easeInOut' }}
                  className="broadcast-frame rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-2xl"
                >
                  <div className="flex flex-col gap-6">
                    <div className="space-y-2">
                      <p className="text-xs uppercase tracking-[0.35em] text-sky-200/80">
                        Live Broadcast
                      </p>
                      <div className="flex items-center gap-3">
                        <svg
                          className="h-5 w-5 text-sky-200/80 animate-pulse"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.4"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          aria-hidden="true"
                        >
                          <rect x="3.5" y="6" width="10.5" height="8" rx="2" />
                          <path d="M14 8l6.5-3.5v11L14 12" />
                          <circle cx="8.75" cy="10" r="1.8" />
                        </svg>
                        <h2 className="text-2xl font-semibold text-white">
                          {steps[activeStep]}
                        </h2>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="h-2 w-full overflow-hidden rounded-full bg-white/10">
                        <motion.div
                          className="h-full rounded-full bg-gradient-to-r from-sky-400 via-indigo-300 to-violet-300"
                          animate={{ width: `${Math.round(progress * 100)}%` }}
                          transition={{ duration: 0.8, ease: 'easeInOut' }}
                        />
                      </div>
                      <div className="grid gap-3 md:grid-cols-4">
                        {steps.map((step, index) => (
                          <div
                            key={step}
                            className={`flex items-center gap-2 rounded-2xl border px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] ${
                              index === activeStep
                                ? 'border-sky-200/50 bg-sky-300/10 text-sky-100'
                                : index < activeStep
                                  ? 'border-sky-200/20 bg-white/5 text-white/70'
                                  : 'border-white/10 bg-white/5 text-white/50'
                            }`}
                          >
                            <span
                              className={`h-2 w-2 rounded-full ${
                                index === activeStep
                                  ? 'bg-sky-300 animate-pulse'
                                  : index < activeStep
                                    ? 'bg-sky-300'
                                    : 'bg-white/30'
                              }`}
                            />
                            {step}
                          </div>
                        ))}
                      </div>
                      <p className="text-xs text-slate-400 text-center mt-4">
                        This may take a few minutes while we research, script, and generate your video...
                      </p>
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
