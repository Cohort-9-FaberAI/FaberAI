export const DEFAULT_ACCENT_HUE = 220
export const BRAND_SAT = 91
export const BRAND_LIT = 49
const TOOLPATH_SAT = 100
const TOOLPATH_LIT = 65
const INK_SAT = 81
const INK_LIT = 23

export function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  const hue = (((h % 360) + 360) % 360) / 360
  const sat = Math.min(100, Math.max(0, s)) / 100
  const light = Math.min(100, Math.max(0, l)) / 100
  const c = (1 - Math.abs(2 * light - 1)) * sat
  const hp = hue * 6
  const x = c * (1 - Math.abs((hp % 2) - 1))
  const m = light - c / 2

  let rgb: [number, number, number]
  if (hp < 1) rgb = [c, x, 0]
  else if (hp < 2) rgb = [x, c, 0]
  else if (hp < 3) rgb = [0, c, x]
  else if (hp < 4) rgb = [0, x, c]
  else if (hp < 5) rgb = [x, 0, c]
  else rgb = [c, 0, x]

  return [
    Math.round((rgb[0] + m) * 255),
    Math.round((rgb[1] + m) * 255),
    Math.round((rgb[2] + m) * 255),
  ]
}

function toHex(v: number): string {
  return v.toString(16).padStart(2, '0')
}

export function rgbToHex(r: number, g: number, b: number): string {
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

export function hslToHex(h: number, s = BRAND_SAT, l = BRAND_LIT): string {
  const [r, g, b] = hslToRgb(h, s, l)
  return rgbToHex(r, g, b)
}

export function hexToHue(hex: string): number {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex.trim())
  if (!match) return DEFAULT_ACCENT_HUE

  const value = parseInt(match[1], 16)
  const r = (value >> 16) & 255
  const g = (value >> 8) & 255
  const b = value & 255
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const delta = max - min
  if (delta === 0) return 0

  let h: number
  if (max === r) h = ((g - b) / delta) % 6
  else if (max === g) h = (b - r) / delta + 2
  else h = (r - g) / delta + 4

  return ((Math.round(h * 60) % 360) + 360) % 360
}

export function applyAccentHue(hue: number): void {
  const primary = hslToRgb(hue, BRAND_SAT, BRAND_LIT)
  const light = hslToRgb(hue, TOOLPATH_SAT, TOOLPATH_LIT)
  const ink = hslToRgb(hue, INK_SAT, INK_LIT)

  const root = document.documentElement
  root.style.setProperty('--brand-hue', String(Math.round(hue)))
  root.style.setProperty('--brand-rgb', `${primary[0]}, ${primary[1]}, ${primary[2]}`)
  root.style.setProperty('--brand-rgb-light', `${light[0]}, ${light[1]}, ${light[2]}`)
  root.style.setProperty('--brand-rgb-ink', `${ink[0]}, ${ink[1]}, ${ink[2]}`)
}
