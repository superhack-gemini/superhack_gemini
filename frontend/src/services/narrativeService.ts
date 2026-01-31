export interface VideoResult {
  title: string
  description: string
  videoUrl: string
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const POLL_INTERVAL_MS = 1500
const MAX_POLL_ATTEMPTS = 120 // 3 minutes max

const DEFAULT_VIDEO =
  'https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const buildTitle = (prompt: string) => {
  const cleaned = prompt.trim().replace(/\s+/g, ' ').replace(/[?!.]+$/, '')
  if (!cleaned) {
    return 'Championship Narrative'
  }

  const lowered = cleaned.toLowerCase()
  if (lowered.startsWith('how did ')) {
    return `How ${cleaned.slice(8)}`
  }
  if (lowered.startsWith('how do ')) {
    return `How ${cleaned.slice(7)}`
  }

  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
}

const buildDescription = (prompt: string) => {
  const cleaned = prompt.trim().replace(/\s+/g, ' ')
  if (!cleaned) {
    return 'A cinematic recap built from key plays, crowd energy, and tactical momentum.'
  }
  return `A cinematic recap that breaks down ${cleaned.replace(/[?!.]+$/, '')}, highlighting defining drives, defensive stops, and the momentum swings that shaped the final score.`
}

interface GenerateResponse {
  task_id: string
  status: string
}

interface TaskStatusResponse {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  prompt: string
  script: unknown | null
  research_context: unknown | null
  videoUrl: string | null
  error: string | null
}

export const generateNarrative = async (prompt: string): Promise<VideoResult> => {
  // Step 1: Start generation task
  const generateResponse = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  })

  if (!generateResponse.ok) {
    throw new Error(`Failed to start generation: ${generateResponse.statusText}`)
  }

  const { task_id }: GenerateResponse = await generateResponse.json()

  // Step 2: Poll for completion
  let attempts = 0
  while (attempts < MAX_POLL_ATTEMPTS) {
    await wait(POLL_INTERVAL_MS)
    attempts++

    const statusResponse = await fetch(`${API_BASE_URL}/getvideo/${task_id}`)
    
    if (!statusResponse.ok) {
      throw new Error(`Failed to get task status: ${statusResponse.statusText}`)
    }

    const taskStatus: TaskStatusResponse = await statusResponse.json()

    if (taskStatus.status === 'completed') {
      return {
        title: buildTitle(prompt),
        description: buildDescription(prompt),
        videoUrl: taskStatus.videoUrl || DEFAULT_VIDEO,
      }
    }

    if (taskStatus.status === 'failed') {
      throw new Error(taskStatus.error || 'Video generation failed')
    }
  }

  throw new Error('Generation timed out')
}
