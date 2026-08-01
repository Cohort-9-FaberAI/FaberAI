import { useStore } from '../../store'
import BrandMark from './BrandMark'

export default function AskFaberAIButton() {
  const toggle = useStore((s) => s.toggle)

  return (
    <button className="ask-faber-btn" type="button" onClick={toggle}>
      <BrandMark size={18} />
      Ask Faber AI
    </button>
  )
}
