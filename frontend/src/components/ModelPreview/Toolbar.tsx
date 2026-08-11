import { LuBox, LuExpand, LuLayers, LuShrink } from 'react-icons/lu'
import styles from './Toolbar.module.css'
import { useState } from 'react'

type ToolbarProps = {
  onFullScreenPressed?: () => void
  onXRayPressed?: (isXRayEnabled: boolean) => void
  isFullScreen?: boolean
}

export default function Toolbar({
  onFullScreenPressed,
  onXRayPressed,
  isFullScreen,
}: ToolbarProps) {
  const [isXRayEnabled, setXRayEnabled] = useState(false)

  return (
    <div className={styles.toolBar}>
      <div className={styles.fullscreenContainer}>
        <button
          type="button"
          title={isFullScreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          aria-label={isFullScreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          className={styles.btn}
          onClick={onFullScreenPressed}
        >
          {isFullScreen ? <LuShrink size={18} /> : <LuExpand size={18} />}
        </button>
      </div>

      <div className={styles.xRayContainer}>
        {
          <div className={styles.viewModeSelector}>
            <button
              type="button"
              className={`${styles.viewModeOption} ${!isXRayEnabled ? styles.activeOption : ''}`}
              onClick={() => {
                setXRayEnabled(false)
                if (onXRayPressed) onXRayPressed(false)
              }}
            >
              <LuBox size={16} />
              <span>Solid</span>
            </button>
            <button
              type="button"
              className={`${styles.viewModeOption} ${isXRayEnabled ? styles.activeOption : ''}`}
              onClick={() => {
                setXRayEnabled(true)
                if (onXRayPressed) onXRayPressed(true)
              }}
            >
              <LuLayers size={16} />
              <span>X-Ray</span>
            </button>
          </div>
        }
      </div>
    </div>
  )
}
