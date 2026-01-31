
import { GoogleGenAI } from "@google/genai";
import { BroadcastScript } from "../types";

export class GeminiService {
  /**
   * Helper to perform an API call with exponential backoff retries.
   * Useful for handling transient 503 "model overloaded" or 429 "too many requests" errors.
   */
  private static async withRetry<T>(fn: () => Promise<T>, maxRetries = 3): Promise<T> {
    let lastError: any;
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (error: any) {
        lastError = error;
        const isOverloaded = error?.message?.toLowerCase().includes('overloaded') || error?.status === 503;
        const isRateLimited = error?.message?.toLowerCase().includes('rate limit') || error?.status === 429;
        
        if (isOverloaded || isRateLimited) {
          const delay = Math.pow(2, i) * 1000 + Math.random() * 1000;
          console.warn(`Model busy/overloaded. Retrying in ${Math.round(delay)}ms... (Attempt ${i + 1}/${maxRetries})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        throw error;
      }
    }
    throw lastError;
  }

  /**
   * Refines the script to fit the cinematic requirements and duration.
   */
  static async refineScript(script: BroadcastScript): Promise<string> {
    return this.withRetry(async () => {
      // Create a fresh instance right before the call to ensure updated API key state
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const { ai_segment } = script;
      
      const dialogueSummary = ai_segment.dialogue
        .map(d => `${d.speaker}: "${d.text}" (${d.delivery || 'natural'})`)
        .join('; ');

      const prompt = `Act as a cinematic director for a sports documentary. 
      Transform this broadcast segment into a highly detailed visual prompt for an AI video generator.
      
      STRICT REQUIREMENTS:
      1. DURATION: Must be exactly ${ai_segment.duration_seconds} seconds.
      2. DIALOGUE: Characters MUST speak these lines: ${dialogueSummary}.
      3. MOOD: ${ai_segment.mood}.
      4. VISUALS: ${ai_segment.visual_description}.
      5. CAMERA: ${ai_segment.camera_notes}.
      6. STYLE: Organic, 35mm film aesthetic, professional studio lighting. NO CGI feel.
      
      Return a single descriptive paragraph focused on natural performances and facial micro-expressions.`;

      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: prompt,
      });
      
      return response.text || "";
    });
  }

  /**
   * Generates a video using Veo 3.1 with a focus on realism and consistency.
   */
  static async generateBroadcasterVideo(
    refinedPrompt: string, 
    onProgress: (status: string) => void
  ): Promise<string> {
    // Create a fresh instance right before the call
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    
    const talentConsistency = `
      TALENT PROFILES (LOCKED):
      - Lead Anchor (Marcus): Distinguished man, late 40s, charcoal suit.
      - Analyst (Sarah): Professional woman, early 30s, emerald green blazer.
      
      SETTING:
      Realistic sports studio. Soft-focus background monitors. Documentary lighting.
    `;

    const fullPrompt = `${talentConsistency} \n\nSCENE ACTION: ${refinedPrompt}`;

    onProgress("Connecting to cinematic engine...");

    // Initial request with retry
    let operation = await this.withRetry(async () => {
      return await ai.models.generateVideos({
        model: 'veo-3.1-fast-generate-preview',
        prompt: fullPrompt,
        config: {
          numberOfVideos: 1,
          resolution: '1080p',
          aspectRatio: '16:9'
        }
      });
    });

    // Polling doesn't usually overload the same way as generation requests, 
    // but we add a safety layer to getVideosOperation.
    while (!operation.done) {
      await new Promise(resolve => setTimeout(resolve, 8000));
      onProgress("Capturing organic talent performance... (45-60s)");
      
      operation = await this.withRetry(async () => {
        return await ai.operations.getVideosOperation({ operation: operation });
      });
    }

    const downloadLink = operation.response?.generatedVideos?.[0]?.video?.uri;
    if (!downloadLink) throw new Error("No video URI returned. The model might be under extreme load.");

    onProgress("Processing video stream...");
    const videoResponse = await fetch(`${downloadLink}&key=${process.env.API_KEY}`);
    const blob = await videoResponse.blob();
    return URL.createObjectURL(blob);
  }
}
