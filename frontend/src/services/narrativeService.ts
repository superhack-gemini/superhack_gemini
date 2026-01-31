export interface VideoResult {
  title: string
  description: string
  videoUrl: string
}

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

export const generateNarrative = async (prompt: string): Promise<VideoResult> => {
  await wait(4200)

  return {
    title: buildTitle(prompt),
    description: buildDescription(prompt),
    videoUrl: DEFAULT_VIDEO,
  }
}
