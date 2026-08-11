import { useLocation } from 'react-router-dom'
import { useStore } from '../../store'
import BrandMark from './BrandMark'
import { isChatEnabledForRoute } from './chatPresets'

export default function AskFaberAIButton() {
  const toggle = useStore((s) => s.toggle)
  const location = useLocation()

  if (!isChatEnabledForRoute(location.pathname)) return null

  return (
    <button className="ask-faber-btn" type="button" onClick={toggle}>
      <BrandMark size={18} variant="white" />
      Ask Faber AI
    </button>
  )
}
