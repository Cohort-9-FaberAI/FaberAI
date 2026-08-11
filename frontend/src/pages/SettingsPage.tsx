import { useNavigate } from 'react-router-dom'
import { useStore } from '../store'
import { DEFAULT_ACCENT_HUE, hexToHue, hslToHex } from '../lib/theme'

const PRESETS = [
  { hue: 220, label: 'Blue' },
  { hue: 165, label: 'Teal' },
  { hue: 145, label: 'Green' },
  { hue: 40, label: 'Amber' },
  { hue: 280, label: 'Purple' },
  { hue: 330, label: 'Rose' },
  { hue: 0, label: 'Red' },
]

export default function SettingsPage() {
  const theme = useStore((s) => s.theme)
  const setTheme = useStore((s) => s.setTheme)
  const accentHue = useStore((s) => s.accentHue)
  const setAccentHue = useStore((s) => s.setAccentHue)
  const userEmail = useStore((s) => s.userEmail)
  const setEmail = useStore((s) => s.setEmail)
  const navigate = useNavigate()

  function handleResetAccent() {
    setAccentHue(DEFAULT_ACCENT_HUE)
  }

  function handleSignOut() {
    setEmail(null)
    navigate('/login')
  }

  return (
    <div className="settings-page">
      <header className="settings-header">
        <p className="workflow-eyebrow">Settings</p>
        <h1 className="page-title">Preferences</h1>
        <p className="page-sub">Personalise how FaberAI looks and behaves for your account.</p>
      </header>

      <section className="settings-card">
        <div className="settings-card-title">
          <h2>Appearance</h2>
          <span>Theme brightness and accent colour</span>
        </div>

        <div className="settings-row">
          <div>
            <span className="settings-label">Theme</span>
            <p>Choose between dark and light surfaces.</p>
          </div>
          <div className="settings-segment" role="group" aria-label="Theme mode">
            <button
              type="button"
              className={theme === 'dark' ? 'active' : ''}
              onClick={() => setTheme('dark')}
            >
              Dark
            </button>
            <button
              type="button"
              className={theme === 'light' ? 'active' : ''}
              onClick={() => setTheme('light')}
            >
              Light
            </button>
          </div>
        </div>

        <div className="settings-row">
          <div>
            <span className="settings-label">Accent hue</span>
            <p>Pick the colour hue used across the theme.</p>
          </div>
          <div className="hue-picker">
            <div className="hue-picker-top">
              <input
                className="hue-range"
                type="range"
                min={0}
                max={360}
                step={1}
                value={accentHue}
                onChange={(e) => setAccentHue(Number(e.target.value))}
                aria-label="Accent hue slider"
              />
              <span
                className="hue-preview"
                style={{ background: hslToHex(accentHue) }}
                aria-hidden="true"
              />
              <input
                className="hue-color"
                type="color"
                value={hslToHex(accentHue)}
                onChange={(e) => setAccentHue(hexToHue(e.target.value))}
                aria-label="Pick accent colour"
              />
            </div>
            <div className="hue-swatches">
              {PRESETS.map((p) => (
                <button
                  key={p.hue}
                  type="button"
                  className={`hue-swatch${accentHue === p.hue ? ' active' : ''}`}
                  style={{ background: hslToHex(p.hue) }}
                  title={p.label}
                  aria-label={`${p.label} accent`}
                  onClick={() => setAccentHue(p.hue)}
                />
              ))}
              <button type="button" className="settings-reset-btn" onClick={handleResetAccent}>
                Reset
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-card-title">
          <h2>Account</h2>
          <span>Signed-in identity</span>
        </div>
        <div className="settings-row">
          <div>
            <span className="settings-label">Signed in as</span>
            <p className="settings-email">
              {userEmail ?? 'Guest — sign in to link projects to your account.'}
            </p>
          </div>
          <button
            type="button"
            className="settings-signout-btn"
            disabled={!userEmail}
            onClick={handleSignOut}
          >
            Sign out
          </button>
        </div>
      </section>
    </div>
  )
}
