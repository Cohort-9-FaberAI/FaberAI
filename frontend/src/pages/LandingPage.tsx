import { useEffect, useRef, useState } from 'react'
import { LuArrowRight, LuMenu, LuMoon, LuSun, LuX } from 'react-icons/lu'
import { Link } from 'react-router-dom'
import '../components/landing/LandingStyles.css'
import { DemoViewer } from '../components/landing/DemoViewer'
import { HeroViewer } from '../components/landing/HeroViewer'
import {
  CredibilityStrip,
  FinalCtaSection,
  FooterSection,
  ProcessComparisonSection,
  ProductProofSection,
  WorkflowSection,
} from '../components/landing/LandingSections'
import { ReportShowcase } from '../components/landing/ReportShowcase'
import BrandMark from '../components/layout/BrandMark'
import { useAssetPreloader } from '../hooks/useAssetPreloader'
import { useStore } from '../store'

const LANDING_ASSETS = [
  '/logo-full.svg',
  '/logo-full-white.svg',
  '/logo-white.svg',
  '/logo.svg',
  '/logo.glb',
  '/logo.stl',
  '/faberai-sample-part.stl',
  '/report/page-0.jpg',
  '/report/page-1.jpg',
  '/report/page-2.jpg',
  '/report/page-3.jpg',
  '/report/page-4.jpg',
  '/report/page-5.jpg',
]

const navLinks = [
  ['Product', '#product'],
  ['How it works', '#workflow'],
  ['Sample report', '#report'],
  ['Processes', '#processes'],
]

export default function LandingPage() {
  const rootRef = useRef<HTMLDivElement>(null)
  const { progress, isLoading } = useAssetPreloader(LANDING_ASSETS)
  const theme = useStore((state) => state.theme)
  const toggleTheme = useStore((state) => state.toggleTheme)
  const [navScrolled, setNavScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const root = rootRef.current
    if (!root) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('is-visible')
        })
      },
      { root, threshold: 0.08, rootMargin: '0px 0px -6% 0px' },
    )

    const observeElements = () => {
      root
        .querySelectorAll('.reveal:not(.is-visible)')
        .forEach((element) => observer.observe(element))
    }

    observeElements()
    const frame = window.requestAnimationFrame(observeElements)
    return () => {
      window.cancelAnimationFrame(frame)
      observer.disconnect()
    }
  }, [isLoading])

  const handleScroll = () => {
    setNavScrolled((rootRef.current?.scrollTop ?? 0) > 24)
  }

  const closeMenu = () => setMobileMenuOpen(false)

  return (
    <div className="faber-landing-root" ref={rootRef} onScroll={handleScroll}>
      {isLoading && (
        <div className="landing-loader" role="status" aria-label={`Loading FaberAI ${progress}%`}>
          <BrandMark size={70} variant="full" />
          <div className="landing-loader-track">
            <span style={{ width: `${progress}%` }} />
          </div>
          <small>{progress}%</small>
        </div>
      )}

      <nav
        className={`landing-nav ${navScrolled ? 'is-scrolled' : ''}`}
        aria-label="Main navigation"
      >
        <div className="landing-wrap landing-nav-inner">
          <a
            className="landing-nav-brand"
            href="#top"
            onClick={closeMenu}
            aria-label="FaberAI home"
          >
            <BrandMark size={30} variant="full" />
          </a>

          <div className={`landing-nav-links ${mobileMenuOpen ? 'is-open' : ''}`}>
            {navLinks.map(([label, href]) => (
              <a href={href} key={href} onClick={closeMenu}>
                {label}
              </a>
            ))}
          </div>

          <div className="landing-nav-actions">
            <button
              className="landing-icon-button"
              type="button"
              onClick={toggleTheme}
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? <LuSun /> : <LuMoon />}
            </button>
            <Link className="landing-button landing-button-primary landing-nav-cta" to="/login">
              Analyze a part <LuArrowRight />
            </Link>
            <button
              className="landing-icon-button landing-menu-button"
              type="button"
              onClick={() => setMobileMenuOpen((open) => !open)}
              aria-label={mobileMenuOpen ? 'Close navigation' : 'Open navigation'}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <LuX /> : <LuMenu />}
            </button>
          </div>
        </div>
      </nav>

      <main>
        <HeroViewer />
        <CredibilityStrip />
        <DemoViewer />
        <WorkflowSection />
        <ProductProofSection />
        <ProcessComparisonSection />
        <ReportShowcase />
        <FinalCtaSection />
      </main>

      <FooterSection />
    </div>
  )
}
