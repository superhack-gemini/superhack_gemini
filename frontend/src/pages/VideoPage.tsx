import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { getTaskStatus } from '../services/narrativeService'

interface VideoState {
  title: string
  description: string
  videoUrl: string
}

export function VideoPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  
  // Get video info from navigation state or fetch it
  const passedState = location.state as VideoState | null
  const [video, setVideo] = useState<VideoState | null>(passedState)
  const [loading, setLoading] = useState(!passedState)
  const [error, setError] = useState('')

  useEffect(() => {
    if (passedState || !taskId) return

    // Fetch video info if not passed via navigation
    const fetchVideo = async () => {
      try {
        const status = await getTaskStatus(taskId)
        if (status.status === 'completed' && status.videoUrl) {
          setVideo({
            title: status.prompt || 'Sports Narrative',
            description: 'Generated broadcast narrative',
            videoUrl: status.videoUrl,
          })
        } else {
          setError('Video not ready yet')
        }
      } catch (err) {
        setError('Failed to load video')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchVideo()
  }, [taskId, passedState])

  const handleBack = () => {
    navigate('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-2 border-sky-500/20 border-t-sky-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading video...</p>
        </div>
      </div>
    )
  }

  if (error || !video) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Video not found'}</p>
          <button
            onClick={handleBack}
            className="px-6 py-3 rounded-full border border-white/20 text-white hover:bg-white/5"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Background effects */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-64 left-1/2 h-[640px] w-[640px] -translate-x-1/2 rounded-full bg-sky-500/10 blur-[200px]" />
        <div className="absolute -bottom-40 left-[-140px] h-[520px] w-[520px] rounded-full bg-indigo-500/10 blur-[190px]" />
        <div className="absolute right-[-80px] top-1/4 h-[520px] w-[520px] rounded-full bg-violet-500/10 blur-[210px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(15,23,42,0.7),_transparent_62%)]" />
      </div>

      <main className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-12">
        {/* Header */}
        <header className="flex items-center justify-between text-sm text-slate-300 mb-8">
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
          <button
            onClick={handleBack}
            className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium uppercase tracking-[0.28em] text-white/80 hover:border-white/20 hover:bg-white/10 transition"
          >
            ← New Broadcast
          </button>
        </header>

        {/* Video Content */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: 'easeInOut' }}
          className="flex-1 flex flex-col gap-8"
        >
          {/* Title Section */}
          <div className="space-y-3">
            <p className="text-xs uppercase tracking-[0.35em] text-sky-200/80">
              Featured Replay
            </p>
            <h1 className="text-3xl font-semibold text-white md:text-5xl">
              {video.title}
            </h1>
            <p className="max-w-3xl text-sm text-slate-300 md:text-base">
              {video.description}
            </p>
          </div>

          {/* Video Player */}
          <div className="broadcast-frame rounded-3xl border border-white/10 bg-white/5 p-2 shadow-[0_30px_120px_rgba(5,10,25,0.7)] backdrop-blur-2xl overflow-hidden">
            <div className="replay-frame overflow-hidden rounded-2xl border border-white/10 bg-slate-950/60 shadow-[0_30px_80px_rgba(5,10,25,0.75)]">
              <div className="relative">
                <span className="absolute top-4 left-4 z-10 rounded-full bg-red-600 px-3 py-1 text-[10px] font-bold uppercase tracking-widest text-white shadow-lg">
                  FEATURED REPLAY
                </span>
                <video
                  className="aspect-video w-full"
                  controls
                  autoPlay
                  preload="metadata"
                  src={video.videoUrl}
                >
                  Your browser does not support the video tag.
                </video>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={handleBack}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-sky-400 via-indigo-300 to-violet-300 px-6 py-3 text-sm font-semibold text-slate-950 shadow-[0_12px_30px_rgba(56,189,248,0.35)] transition hover:brightness-110"
            >
              <svg
                className="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M3.5 12h7.5" />
                <path d="M11 12l-2.2-2.2" />
                <path d="M11 12l-2.2 2.2" />
                <path d="M11 12h9.5" />
              </svg>
              Create Another Broadcast
            </button>
            
            {video.videoUrl && (
              <a
                href={video.videoUrl}
                download
                className="inline-flex items-center justify-center gap-2 rounded-full border border-white/20 px-6 py-3 text-sm font-semibold text-white transition hover:border-white/40 hover:bg-white/5"
              >
                <svg
                  className="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="7,10 12,15 17,10" />
                  <line x1="12" y1="15" x2="12" y2="3" />
                </svg>
                Download Video
              </a>
            )}
            
            <span className="text-xs text-slate-400">
              Task ID: {taskId}
            </span>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
