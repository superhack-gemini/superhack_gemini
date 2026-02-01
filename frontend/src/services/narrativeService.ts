export interface VideoResult {
  title: string
  description: string
  videoUrl: string
  taskId: string
}

// In development, Vite proxy routes /api/* to localhost:8000
// In production, set VITE_API_URL to your backend URL
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'
const POLL_INTERVAL_MS = 2000
const MAX_POLL_ATTEMPTS = 180 // 6 minutes max (video generation takes time)

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
  if (lowered.startsWith('why ')) {
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
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
  message: string
}

interface TaskStatusResponse {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  prompt: string | null
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
    body: JSON.stringify({ 
      prompt,
      duration_seconds: 150  // 2.5 minute video
    }),
  })

  if (!generateResponse.ok) {
    const errorText = await generateResponse.text()
    throw new Error(`Failed to start generation: ${generateResponse.statusText} - ${errorText}`)
  }

  const { task_id }: GenerateResponse = await generateResponse.json()
  console.log(`🎬 Started generation task: ${task_id}`)

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
    console.log(`📊 Poll ${attempts}: status=${taskStatus.status}`)

    if (taskStatus.status === 'completed') {
      // Video URL comes from backend as /videos/final/uuid.mp4
      // This works with both Vite proxy (dev) and production
      const videoUrl = taskStatus.videoUrl || ''
      
      console.log(`✅ Generation complete! Video: ${videoUrl}`)
      
      return {
        title: buildTitle(prompt),
        description: buildDescription(prompt),
        videoUrl,
        taskId: task_id,
      }
    }

    if (taskStatus.status === 'failed') {
      throw new Error(taskStatus.error || 'Video generation failed')
    }
  }

  throw new Error('Generation timed out after 6 minutes')
}

/**
 * Get the status of a generation task
 */
export const getTaskStatus = async (taskId: string): Promise<TaskStatusResponse> => {
  const response = await fetch(`${API_BASE_URL}/getvideo/${taskId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to get task status: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get the script for a completed task
 */
export const getScript = async (taskId: string): Promise<unknown> => {
  const response = await fetch(`${API_BASE_URL}/script/${taskId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to get script: ${response.statusText}`)
  }

  const data = await response.json()
  return data.script
}
