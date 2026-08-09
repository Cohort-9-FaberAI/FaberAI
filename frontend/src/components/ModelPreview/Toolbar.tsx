import { LuExpand, LuShrink } from 'react-icons/lu'
import styles from './Toolbar.module.css'

type ToolbarProps = {
  onFullScreenPressed?: () => void
  isFullScreen?: boolean
}

export default function Toolbar({ onFullScreenPressed, isFullScreen }: ToolbarProps) {
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
    </div>
  )
}
