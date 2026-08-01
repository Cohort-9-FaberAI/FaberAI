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
        <button className={styles.btn} onClick={onFullScreenPressed}>
          {isFullScreen ? <LuShrink size={20} /> : <LuExpand size={20} />}
        </button>
      </div>
    </div>
  )
}
