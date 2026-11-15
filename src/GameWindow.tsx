import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'

// Pasa los parámetros de la página (p. ej. ?mcp=1) al juego dentro del iframe
const GAME_URL = `${import.meta.env.BASE_URL}juego.html${window.location.search}`

interface IconProps {
  children: ReactNode
}

interface GameWindowProps {
  onClose: () => void
}

function Icon({ children }: IconProps) {
  return (
    <svg
      className="icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  )
}

export default function GameWindow({ onClose }: GameWindowProps) {
  const windowRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const [loaded, setLoaded] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    const previous = document.activeElement
    document.body.classList.add('is-locked')
    closeRef.current?.focus()

    return () => {
      document.body.classList.remove('is-locked')
      if (previous instanceof HTMLElement) previous.focus()
    }
  }, [])

  useEffect(() => {
    const onFullscreenChange = () => setIsFullscreen(Boolean(document.fullscreenElement))
    document.addEventListener('fullscreenchange', onFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', onFullscreenChange)
  }, [])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !document.fullscreenElement) onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  const reload = () => {
    setLoaded(false)
    setReloadKey((key) => key + 1)
  }

  const toggleFullscreen = async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen()
      } else {
        await windowRef.current?.requestFullscreen()
      }
    } catch (error) {
      console.error('No se pudo cambiar a pantalla completa.', error)
    }
  }

  return (
    <div
      className="game-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div
        className="game-window"
        role="dialog"
        aria-modal="true"
        aria-labelledby="game-window-title"
        ref={windowRef}
      >
        <header className="game-window-bar">
          <div className="game-window-heading">
            <span className="window-dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <div>
              <h2 className="game-window-title" id="game-window-title">Test1</h2>
              <p className="game-window-status">
                <span className={`status-dot ${loaded ? '' : 'status-dot--amber'}`} aria-hidden="true" />
                {loaded ? 'Ventana activa' : 'Cargando motor'}
              </p>
            </div>
          </div>

          <div className="game-window-actions">
            <a
              className="icon-btn"
              href={GAME_URL}
              target="_blank"
              rel="noreferrer"
              title="Abrir en una pestaña nueva"
              aria-label="Abrir el juego en una pestaña nueva"
            >
              <Icon>
                <path d="M14 4h6v6M20 4l-9 9" />
                <path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
              </Icon>
            </a>
            <button
              className="icon-btn"
              type="button"
              onClick={reload}
              title="Recargar juego"
              aria-label="Recargar juego"
            >
              <Icon>
                <path d="M20 11a8 8 0 1 0-2.34 5.66" />
                <path d="M20 4v7h-7" />
              </Icon>
            </button>
            <button
              className="icon-btn"
              type="button"
              onClick={toggleFullscreen}
              title="Pantalla completa"
              aria-label="Alternar pantalla completa"
              aria-pressed={isFullscreen}
            >
              {isFullscreen ? (
                <Icon>
                  <path d="M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5" />
                </Icon>
              ) : (
                <Icon>
                  <path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5" />
                </Icon>
              )}
            </button>
            <button
              className="icon-btn is-close"
              type="button"
              onClick={onClose}
              title="Cerrar juego"
              aria-label="Cerrar juego"
              ref={closeRef}
            >
              <Icon>
                <path d="M6 6l12 12M18 6 6 18" />
              </Icon>
            </button>
          </div>
        </header>

        <div className="game-window-body">
          {!loaded && (
            <div className="game-loading" role="status">
              <span className="spinner" aria-hidden="true" />
              <strong>Cargando Test1…</strong>
              <span>La primera carga descarga unos 125 MB.</span>
              <a href={GAME_URL} target="_blank" rel="noreferrer">
                Abrir en una pestaña si no carga
              </a>
            </div>
          )}
          <iframe
            key={reloadKey}
            className="game-frame"
            src={GAME_URL}
            title="Test1 — juego"
            allow="fullscreen; autoplay; gamepad; pointer-lock"
            allowFullScreen
            onLoad={() => setLoaded(true)}
          />
        </div>
      </div>
    </div>
  )
}
