/**
 * HeroCinematicBackground - Cinematic video background for landing hero section ONLY
 * 
 * IMPORTANT: This component is exclusively for the main landing/narrative input hero.
 * Do NOT use on video showcase, playback, results, or editor pages.
 * 
 * Features:
 * - Autoplay muted video loop of football gameplay footage
 * - Cinematic overlays: vignette, gradient, grain, color treatment
 * - Fallback gradient for slow connections or reduced motion preference
 * - Subtle parallax zoom effect for premium feel
 */

import { useEffect, useRef, useState } from 'react'

export function HeroCinematicBackground() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isVideoLoaded, setIsVideoLoaded] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleCanPlay = () => {
      setIsVideoLoaded(true)
    }

    video.addEventListener('canplay', handleCanPlay)
    
    // If video is already loaded (cached), trigger immediately
    if (video.readyState >= 3) {
      setIsVideoLoaded(true)
    }

    return () => {
      video.removeEventListener('canplay', handleCanPlay)
    }
  }, [])

  return (
    <div className="hero-cinematic-background pointer-events-none absolute inset-0 z-0">
      {/* Parallax container for subtle zoom effect */}
      <div className="hero-video-parallax">
        {/* Static fallback for mobile, slow connections, or reduced motion */}
        <div 
          className={`hero-video-fallback transition-opacity duration-700 ${
            isVideoLoaded ? 'opacity-0' : 'opacity-100'
          }`}
        />
        
        {/* Main video element */}
        <video
          ref={videoRef}
          className={`hero-video transition-opacity duration-700 ${
            isVideoLoaded ? 'opacity-100' : 'opacity-0'
          }`}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
        >
          <source src="/videos/hero-bg-2.mp4" type="video/mp4" />
        </video>
      </div>

      {/* Cinematic treatment overlays */}
      <div className="hero-video-overlay">
        {/* Dark vignette - focuses attention on center */}
        <div className="hero-video-vignette" />
        
        {/* Vertical gradient for text contrast */}
        <div className="hero-video-gradient" />
        
        {/* Film grain texture */}
        <div className="hero-video-grain" />
        
        {/* Color treatment overlay */}
        <div className="hero-video-color-treatment" />
      </div>
    </div>
  )
}
