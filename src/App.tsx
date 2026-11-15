import { useState } from 'react'
import type { ReactNode } from 'react'
import GameWindow from './GameWindow'

const SPRITE_URL = `${import.meta.env.BASE_URL}index.png`

interface NavItem {
  href: string
  label: string
  current?: boolean
  icon: ReactNode
}

interface IconProps {
  children: ReactNode
  className?: string
}

const NAV_ITEMS: NavItem[] = [
  {
    href: '#resumen',
    label: 'Resumen',
    current: true,
    icon: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
  },
  {
    href: '#ficha',
    label: 'Ficha',
    icon: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 16v-4M12 8h.01" />
      </>
    ),
  },
  {
    href: '#como-jugar',
    label: 'Cómo jugar',
    icon: (
      <>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),
  },
]

function Icon({ children, className = 'icon' }: IconProps) {
  return (
    <svg
      className={className}
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

function PlayIcon(): ReactNode {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M8 5.5v13a1 1 0 0 0 1.52.85l10-6.5a1 1 0 0 0 0-1.7l-10-6.5A1 1 0 0 0 8 5.5Z" fill="currentColor" />
    </svg>
  )
}

export default function App() {
  const [gameOpen, setGameOpen] = useState(false)

  const openGame = () => setGameOpen(true)
  const closeGame = () => setGameOpen(false)

  return (
    <div className="app-shell">
      <aside className="sidebar glass">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <PlayIcon />
          </span>
          <span className="brand-copy">
            <span className="brand-name">Arcade</span>
            <span className="brand-sub">Godot game player</span>
          </span>
        </div>

        <nav className="nav" aria-label="Secciones">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.href}
              className="nav-link"
              href={item.href}
              aria-current={item.current ? 'page' : undefined}
            >
              <Icon className="nav-icon">{item.icon}</Icon>
              <span>{item.label}</span>
            </a>
          ))}
        </nav>

        <div className="sidebar-note">
          <p className="status-line">
            <span className="status-dot" aria-hidden="true" />
            Modo local
          </p>
          <p>Todo se ejecuta en tu navegador. La primera carga descarga unos 125 MB.</p>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar glass">
          <div>
            <p className="topbar-eyebrow">Arcade / Biblioteca</p>
            <h1 className="topbar-title">Centro de juegos</h1>
          </div>
          <span className="status-chip">
            <span className="status-dot" aria-hidden="true" />
            Listo para jugar
          </span>
        </header>

        <main className="content">
          <div className="main-column">
            <section className="hero glass" id="resumen" aria-labelledby="game-title">
              <div className="hero-copy">
                <span className="hero-eyebrow">
                  <span className="status-dot status-dot--blue" aria-hidden="true" />
                  Juego web · Godot
                </span>
                <h2 className="hero-title" id="game-title">Test1</h2>
                <p className="hero-lead">
                  Una experiencia jugable creada con Godot y exportada para el navegador.
                  Ábrela en una ventana flotante, sin salir de esta página.
                </p>

                <div className="hero-actions">
                  <button className="btn btn-primary" type="button" onClick={openGame}>
                    <PlayIcon />
                    Iniciar juego
                  </button>
                  <a className="btn btn-secondary" href="#ficha">
                    Ver ficha
                  </a>
                </div>

                <div className="meta-row" aria-label="Características técnicas">
                  <span className="meta-chip">
                    <Icon><rect x="4" y="4" width="16" height="16" rx="4" /></Icon>
                    Godot
                  </span>
                  <span className="meta-chip">
                    <Icon><path d="M4 7h16M4 12h16M4 17h10" /></Icon>
                    WebGL 2.0
                  </span>
                  <span className="meta-chip">
                    <Icon><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a15 15 0 0 1 0 18 15 15 0 0 1 0-18Z" /></Icon>
                    Export web
                  </span>
                </div>
              </div>

              <button
                className="preview"
                type="button"
                onClick={openGame}
                aria-label="Abrir Test1 en una ventana"
              >
                <img src={SPRITE_URL} alt="" />
                <span className="preview-badge">Vista previa</span>
                <span className="preview-play" aria-hidden="true">
                  <PlayIcon />
                </span>
                <span className="preview-footer">
                  <span>Abrir ventana del juego</span>
                  <Icon><path d="M7 17 17 7M9 7h8v8" /></Icon>
                </span>
              </button>
            </section>

            <footer className="page-foot">
              <span>Test1 · Godot Web Export</span>
              <span>Optimizado para jugar en el navegador</span>
            </footer>
          </div>

          <aside className="side-panel" aria-label="Detalles del juego">
            <section className="panel glass" id="ficha">
              <h2 className="panel-title">Ficha del juego</h2>
              <dl className="spec-list">
                <div className="spec-row">
                  <dt>Motor</dt>
                  <dd>Godot</dd>
                </div>
                <div className="spec-row">
                  <dt>Renderizado</dt>
                  <dd>WebGL 2.0</dd>
                </div>
                <div className="spec-row">
                  <dt>Distribución</dt>
                  <dd>Web</dd>
                </div>
                <div className="spec-row">
                  <dt>Descarga inicial</dt>
                  <dd>≈ 125 MB</dd>
                </div>
              </dl>
              <p className="panel-note">
                El navegador puede reutilizar los archivos en caché en las siguientes partidas.
              </p>
            </section>

            <section className="panel glass" id="como-jugar">
              <h2 className="panel-title">Cómo jugar</h2>
              <ol className="steps">
                <li>
                  <span className="step-index" aria-hidden="true">1</span>
                  <span>Pulsa <strong>Iniciar juego</strong> para abrir la ventana.</span>
                </li>
                <li>
                  <span className="step-index" aria-hidden="true">2</span>
                  <span>Espera a que el motor termine de cargar.</span>
                </li>
                <li>
                  <span className="step-index" aria-hidden="true">3</span>
                  <span>Usa la pantalla completa para una mejor experiencia.</span>
                </li>
              </ol>
            </section>
          </aside>
        </main>
      </div>

      {gameOpen && <GameWindow onClose={closeGame} />}
    </div>
  )
}
