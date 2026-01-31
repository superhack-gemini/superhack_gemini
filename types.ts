
export interface DialogueLine {
  speaker: string;
  text: string;
  delivery?: string;
  camera_direction?: string;
}

export interface AISegment {
  segment_id: string;
  segment_type: string;
  duration_seconds: number;
  mood: string;
  visual_description: string;
  camera_notes: string;
  dialogue: DialogueLine[];
  graphics: string[];
}

export interface BroadcastScript {
  order: number;
  segment_type: string;
  ai_segment: AISegment;
}

export enum GenerationStatus {
  IDLE = 'IDLE',
  REFINING = 'REFINING',
  GENERATING_VIDEO = 'GENERATING_VIDEO',
  FETCHING = 'FETCHING',
  COMPLETED = 'COMPLETED',
  ERROR = 'ERROR'
}

export interface VideoResult {
  url: string;
  thumbnail?: string;
}
