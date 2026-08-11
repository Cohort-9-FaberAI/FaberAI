import { useState, useEffect } from 'react'
import { useGLTF } from '@react-three/drei'

const DEFAULT_ASSETS = [
  '/logo-full.svg',
  '/logo-full-white.svg',
  '/logo-white.svg',
  '/logo.svg',
  '/icons.svg',
  '/logo.glb',
]

// Preload the CAD model immediately so React Three Fiber mounts with zero lag
useGLTF.preload('/logo.glb')

export function useAssetPreloader(assets: string[] = DEFAULT_ASSETS) {
  const [progress, setProgress] = useState(0)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let isCancelled = false
    const totalItems = assets.length + 1 // +1 for fonts resolution
    let completedCount = 0

    const updateProgress = () => {
      completedCount++
      if (!isCancelled) {
        const currentPercent = Math.min(100, Math.round((completedCount / totalItems) * 100))
        setProgress(currentPercent)

        if (completedCount >= totalItems) {
          // Allow visual progress bar to smoothly finish reaching 100% before unmounting
          window.setTimeout(() => {
            if (!isCancelled) {
              setIsLoading(false)
            }
          }, 450)
        }
      }
    }

    const loadAsset = async (src: string) => {
      try {
        if (src.endsWith('.svg') || src.match(/\.(png|jpg|jpeg|webp)$/i)) {
          const img = new Image()
          img.src = src
          await img.decode()
        } else if (src.endsWith('.glb')) {
          // Ensure file fetch completes into browser disk/memory cache
          await fetch(src, { cache: 'force-cache' })
        } else {
          await fetch(src, { cache: 'force-cache' })
        }
      } catch (e) {
        // Prevent broken asset fetch from stranding the user indefinitely
        console.warn(`Asset preloading check failed for: ${src}`, e)
      } finally {
        updateProgress()
      }
    }

    const executePreload = async () => {
      const fontsPromise =
        'fonts' in document ? document.fonts.ready.catch(() => undefined) : Promise.resolve()

      fontsPromise.finally(() => updateProgress())
      assets.forEach((src) => loadAsset(src))
    }

    executePreload()

    return () => {
      isCancelled = true
    }
  }, [assets])

  return { progress, isLoading }
}
