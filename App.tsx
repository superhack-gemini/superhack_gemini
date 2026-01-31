
import React, { useState, useEffect } from 'react';
import { BroadcastScript, GenerationStatus, VideoResult } from './types';
import { GeminiService } from './services/geminiService';

const DEFAULT_SCRIPT: BroadcastScript = {
  "order": 1,
  "segment_type": "ai_generated",
  "ai_segment": {
    "segment_id": "intro_1",
    "segment_type": "intro",
    "duration_seconds": 6,
    "mood": "somber but professional",
    "visual_description": "Camera slowly pushes in on the lead anchor. Studio has soft, realistic lighting with a focus on the talent's expressions of disappointment.",
    "camera_notes": "Start wide, slow push to medium shot. Focus on facial micro-expressions.",
    "dialogue": [
      {
        "speaker": "Marcus Webb",
        "text": "The 49ers were supposed to be here. Instead, they're watching from home.",
        "delivery": "Somber, measured pace",
        "camera_direction": "Slow push in"
      },
      {
        "speaker": "Sarah Chen",
        "text": "What went wrong with the Faithful?",
        "delivery": "Direct and serious",
        "camera_direction": "Cut to close-up"
      }
    ],
    "graphics": ["LOWER THIRD: SPECIAL REPORT"]
  }
};

const App: React.FC = () => {
  const [jsonInput, setJsonInput] = useState(JSON.stringify(DEFAULT_SCRIPT, null, 2));
  const [status, setStatus] = useState<GenerationStatus>(GenerationStatus.IDLE);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [videoResult, setVideoResult] = useState<VideoResult | null>(null);
  const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    const checkApiKey = async () => {
      try {
        const selected = await (window as any).aistudio.hasSelectedApiKey();
        setHasApiKey(selected);
      } catch (e) {
        console.warn("API Key check skipped or failed", e);
      }
    };
    checkApiKey();
  }, []);

  const handleOpenKeySelector = async () => {
    try {
      await (window as any).aistudio.openSelectKey();
      setHasApiKey(true);
    } catch (e) {
      console.error("Failed to open key selector", e);
    }
  };

  const handleGenerate = async () => {
    setStatusMessage("");
    try {
      let script: BroadcastScript;
      try {
        script = JSON.parse(jsonInput);
      } catch (e: any) {
        throw new Error(`JSON Syntax Error: ${e.message}.`);
      }

      if (!hasApiKey) {
        await handleOpenKeySelector();
      }

      setStatus(GenerationStatus.REFINING);
      setStatusMessage(`Timing dialogue for ${script.ai_segment.duration_seconds}s...`);

      const refinedPrompt = await GeminiService.refineScript(script);
      
      setStatus(GenerationStatus.GENERATING_VIDEO);
      const videoUrl = await GeminiService.generateBroadcasterVideo(refinedPrompt, (msg) => {
        setStatusMessage(msg);
      });

      setVideoResult({ url: videoUrl });
      setStatus(GenerationStatus.COMPLETED);
    } catch (error: any) {
      console.error("Generation Error:", error);
      
      let message = error.message || "An unexpected production error occurred.";
      
      if (message.toLowerCase().includes("overloaded")) {
        message = "The AI Studio model is currently under heavy load (503 Overloaded). We've implemented automatic retries, but the server is still busy. Please wait a moment and try again.";
      } else if (message.includes("Requested entity was not found")) {
        setHasApiKey(false);
        message = "API Key error. Please re-select your key.";
      }

      setStatus(GenerationStatus.ERROR);
      setStatusMessage(message);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col antialiased">
      <header className="border-b border-neutral-800 bg-neutral-900/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="px-3 py-1 bg-blue-600 rounded text-[10px] font-black uppercase tracking-[0.2em]">
              PROD-VEO
            </div>
            <h1 className="text-xl font-light tracking-widest uppercase">
              Narrator <span className="font-bold text-blue-500">Agent</span>
            </h1>
          </div>
          <div className="flex items-center gap-6">
            {!hasApiKey && (
              <button 
                onClick={handleOpenKeySelector}
                className="text-xs font-semibold text-yellow-500 hover:text-yellow-400 transition-colors border border-yellow-500/20 px-4 py-1.5 rounded-full"
              >
                SELECT API KEY
              </button>
            )}
            <div className="h-4 w-px bg-neutral-800"></div>
            <div className="text-[10px] font-medium tracking-widest text-neutral-500 uppercase">
              Resilient Feed v3.2
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full p-6 md:p-10 grid grid-cols-1 lg:grid-cols-12 gap-10">
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div className="bg-neutral-900/50 border border-neutral-800 rounded-3xl p-6 shadow-2xl flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <label className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Segment JSON Definition</label>
              <button 
                onClick={() => setJsonInput(JSON.stringify(DEFAULT_SCRIPT, null, 2))}
                className="text-[10px] font-bold text-blue-500 hover:text-blue-400 transition-colors uppercase"
              >
                Load Default
              </button>
            </div>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              className="flex-1 bg-black/40 border border-neutral-800 rounded-2xl p-5 font-mono text-[12px] leading-relaxed text-blue-300 focus:outline-none focus:ring-1 focus:ring-blue-500/30 transition-all resize-none shadow-inner"
              spellCheck={false}
            />
          </div>

          <button
            onClick={handleGenerate}
            disabled={status === GenerationStatus.REFINING || status === GenerationStatus.GENERATING_VIDEO}
            className={`w-full py-5 rounded-2xl font-bold uppercase tracking-[0.2em] text-sm transition-all flex items-center justify-center gap-4 ${
              status === GenerationStatus.REFINING || status === GenerationStatus.GENERATING_VIDEO
                ? 'bg-neutral-800 text-neutral-600 cursor-not-allowed shadow-none'
                : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/10'
            }`}
          >
            {status === GenerationStatus.REFINING || status === GenerationStatus.GENERATING_VIDEO ? (
              <>
                <div className="w-4 h-4 border-2 border-neutral-600 border-t-white rounded-full animate-spin"></div>
                Rendering Asset
              </>
            ) : (
              <>Generate Broadcast Clip</>
            )}
          </button>
        </div>

        <div className="lg:col-span-7 flex flex-col h-full">
          <div className="bg-neutral-900 border border-neutral-800 rounded-3xl overflow-hidden shadow-2xl flex-1 flex flex-col">
            <div className="px-6 py-3 border-b border-neutral-800 flex items-center justify-between bg-black/20">
              <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-500">Live Preview Output</span>
              <div className="flex gap-2">
                <div className={`w-2 h-2 rounded-full ${status === GenerationStatus.ERROR ? 'bg-red-500' : 'bg-green-500 animate-pulse'}`}></div>
              </div>
            </div>

            <div className="flex-1 bg-black flex items-center justify-center relative overflow-hidden group">
              {status === GenerationStatus.IDLE && (
                <div className="text-center">
                  <p className="text-[10px] font-bold uppercase tracking-[0.4em] text-neutral-700">Studio Standby</p>
                </div>
              )}

              {(status === GenerationStatus.REFINING || status === GenerationStatus.GENERATING_VIDEO) && (
                <div className="text-center px-12">
                   <div className="w-20 h-20 border-2 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mx-auto mb-6"></div>
                  <h3 className="text-sm font-bold tracking-[0.2em] uppercase text-white mb-2">Generating Cinematic Clip</h3>
                  <p className="text-[11px] text-blue-400 font-mono italic tracking-wide">{statusMessage}</p>
                </div>
              )}

              {status === GenerationStatus.ERROR && (
                <div className="text-center p-10 max-w-md">
                  <div className="text-red-500 mb-4 flex justify-center">
                    <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-bold uppercase tracking-widest text-red-500 mb-3">Model Overloaded / Busy</h3>
                  <p className="text-[11px] text-neutral-400 leading-relaxed font-mono bg-neutral-950 p-6 rounded-xl border border-red-900/20 shadow-inner">
                    {statusMessage}
                  </p>
                  <div className="flex flex-col gap-3 mt-8">
                    <button 
                      onClick={handleGenerate}
                      className="px-6 py-3 bg-red-600/10 text-red-500 border border-red-500/20 rounded-xl text-[10px] font-bold uppercase tracking-widest hover:bg-red-600/20 transition-all"
                    >
                      Force Retry Now
                    </button>
                    <button 
                      onClick={() => setStatus(GenerationStatus.IDLE)}
                      className="text-[10px] font-bold text-neutral-600 hover:text-neutral-400 uppercase tracking-widest"
                    >
                      Reset Input
                    </button>
                  </div>
                </div>
              )}

              {videoResult && status === GenerationStatus.COMPLETED && (
                <div className="w-full h-full flex items-center justify-center bg-black">
                  <video 
                    src={videoResult.url} 
                    controls 
                    autoPlay 
                    loop
                    className="w-full h-full object-contain shadow-2xl shadow-blue-500/5"
                  />
                  <div className="absolute top-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a 
                      href={videoResult.url} 
                      download="narrator_segment.mp4"
                      className="px-4 py-2 bg-black/60 backdrop-blur-md border border-white/10 text-[10px] font-bold uppercase tracking-widest text-white rounded hover:bg-white/20 transition-all"
                    >
                      Export MP4
                    </a>
                  </div>
                </div>
              )}
            </div>

            <div className="p-8 border-t border-neutral-800 flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="flex -space-x-3">
                  {[1, 2].map(i => (
                    <div key={i} className="w-10 h-10 rounded-full bg-neutral-800 border-2 border-neutral-900 overflow-hidden ring-1 ring-white/10 shadow-lg shadow-black">
                      <img src={`https://picsum.photos/seed/sports${i}/100/100`} alt="Talent" className="w-full h-full object-cover grayscale opacity-80" />
                    </div>
                  ))}
                </div>
                <div>
                  <h4 className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">Locked Character Profiles</h4>
                  <p className="text-[9px] text-neutral-600 uppercase tracking-[0.1em] mt-1 italic">Consistency: Documentary-Grade</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-[9px] font-bold text-blue-500 uppercase tracking-widest opacity-60">Engine Protocol</div>
                <div className="text-[11px] font-mono text-neutral-500 mt-0.5">VEO-3.1-NARRATIVE</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="py-8 px-6 border-t border-neutral-900/50 text-center">
        <p className="text-[9px] font-bold text-neutral-700 uppercase tracking-[0.5em]">
          Automated Broadcast Continuity &bull; Narrative Segment Agent
        </p>
      </footer>
    </div>
  );
};

export default App;
