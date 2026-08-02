import { useStore } from '../../store'

export default function AskFaberAIButton() {
  const toggle = useStore((s) => s.toggle)

  return (
    <button className="ask-faber-btn" type="button" onClick={toggle}>
      Ask Faber AI
    </button>
  )
}
