import type { ReactNode } from 'react'
import Ranking from './Ranking'

const GAME_URL = `${import.meta.env.BASE_URL}juego.html${window.location.search}`

interface IconProps {
  children: ReactNode
  className?: string
}

const NAV_ITEMS = [
  { href: '#proyecto', label: 'Proyecto' },
  { href: '#como-jugar', label: 'Cómo jugar' },
  { href: '#ranking', label: 'Ranking' },
]

const FACTS = [
  { label: 'Motor', value: 'Godot' },
  { label: 'Renderizado', value: 'WebGL 2.0' },
  { label: 'Distribución', value: 'Web' },
  { label: 'Primera carga', value: '≈ 58 MB' },
]

const STEPS = [
  {
    title: 'Pulsa Jugar',
    body: 'El botón te lleva al juego en esta misma pestaña, sin ventanas emergentes.',
  },
  {
    title: 'Espera la primera carga',
    body: 'El motor descarga unos 58 MB. Las siguientes partidas usan la caché del navegador.',
  },
  {
    title: 'Juega y vuelve',
    body: 'Cuando termines, el botón atrás del navegador te devuelve a esta presentación.',
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

function PlayIcon() {
  return (
    <svg className="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M8 5.5v13a1 1 0 0 0 1.52.85l10-6.5a1 1 0 0 0 0-1.7l-10-6.5A1 1 0 0 0 8 5.5Z"
        fill="currentColor"
      />
    </svg>
  )
}

function ArrowIcon() {
  return (
    <Icon>
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </Icon>
  )
}

function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <PlayIcon />
    </span>
  )
}

export default function App() {
  return (
    <div className="page">
      <header className="site-header glass">
        <div className="site-header-inner">
          <a className="brand" href="#inicio">
            <BrandMark />
            <span className="brand-copy">
              <span className="brand-name">Arcade</span>
              <span className="brand-sub">Godot web export</span>
            </span>
          </a>

          <nav className="site-nav" aria-label="Secciones de la presentación">
            {NAV_ITEMS.map((item) => (
              <a key={item.href} href={item.href}>
                {item.label}
              </a>
            ))}
          </nav>

          <a className="btn btn-primary btn-sm" href={GAME_URL}>
            <PlayIcon />
            Jugar
          </a>
        </div>
      </header>

      <main id="inicio">
        <div className="shell">
          <section className="hero" aria-labelledby="game-title">
            <div className="hero-copy">
              <p className="hero-eyebrow">
                <span className="eyebrow-dot" aria-hidden="true" />
                Presentación del proyecto
              </p>
              <h1 className="hero-title" id="game-title">Mision Trainer</h1>
              <p className="hero-lead">
                Una experiencia jugable creada con Godot y exportada para la web.
                Todo ocurre en tu navegador, sin instalaciones y sin salir de la pestaña.
              </p>

              <div className="hero-actions">
                <a className="btn btn-primary" href={GAME_URL}>
                  <PlayIcon />
                  Jugar ahora
                </a>
                <a className="btn btn-secondary" href="#como-jugar">
                  Cómo jugar
                </a>
              </div>

              <p className="hero-note">
                <ArrowIcon />
                El juego se abre en esta misma pestaña.
              </p>

              <div className="meta-row" aria-label="Características del juego">
                <span className="meta-chip">
                  <Icon><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4 7.5 8 4.5 8-4.5M12 12v9" /></Icon>
                  Godot
                </span>
                <span className="meta-chip">
                  <Icon><path d="M4 7h16M4 12h16M4 17h10" /></Icon>
                  WebGL 2.0
                </span>
                <span className="meta-chip">
                  <Icon><path d="M12 3v12M7 10l5 5 5-5" /><path d="M5 21h14" /></Icon>
                  ≈ 58 MB
                </span>
              </div>
            </div>

            <a className="stage glass" href={GAME_URL}>
              <span className="stage-screen">
                <span className="stage-chrome" aria-hidden="true">
                  <span className="stage-dots">
                    <i />
                    <i />
                    <i />
                  </span>
                  <span className="stage-chrome-label">mision-trainer.juego</span>
                  <span className="stage-status">
                    <i />
                    Listo
                  </span>
                </span>

                <span className="stage-body">
                  <span className="stage-play" aria-hidden="true">
                    <PlayIcon />
                  </span>
                  <span className="stage-kicker" aria-hidden="true">Godot web export</span>
                  <span className="stage-title">Entra en Mision Trainer</span>
                  <span className="stage-caption" aria-hidden="true">WebGL 2.0 · Una sola pestaña</span>
                  <span className="sr-only">, abrir el juego en esta pestaña</span>
                </span>

                <span className="stage-foot" aria-hidden="true">
                  <span>Abrir el juego</span>
                  <span className="stage-foot-cta">
                    Ahora
                    <ArrowIcon />
                  </span>
                </span>
              </span>
            </a>
          </section>

          <section className="facts glass" aria-label="Ficha técnica">
            {FACTS.map((fact) => (
              <div className="fact" key={fact.label}>
                <span className="fact-label">{fact.label}</span>
                <span className="fact-value">{fact.value}</span>
              </div>
            ))}
          </section>
        </div>

        <section className="section shell" id="proyecto" aria-labelledby="project-title">
          <div className="section-head">
            <p className="section-eyebrow">El proyecto</p>
            <h2 className="section-title" id="project-title">
              Pequeño, directo y hecho para la web.
            </h2>
            <p className="section-lead">
              Mision Trainer es una pieza experimental que lleva un proyecto de Godot al navegador
              sin pasar por una tienda ni por un instalador.
            </p>
          </div>

          <div className="project-grid">
            <article className="project-card project-card--feature glass">
              <span className="card-icon" aria-hidden="true">
                <Icon>
                  <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" />
                  <path d="m4 7.5 8 4.5 8-4.5M12 12v9" />
                </Icon>
              </span>
              <h3>Godot en el navegador</h3>
              <p>
                El proyecto nace en Godot y se exporta a WebAssembly para ejecutarse
                en el navegador, sin mantener una versión aparte.
              </p>
            </article>

            <article className="project-card glass">
              <span className="card-icon" aria-hidden="true">
                <Icon>
                  <circle cx="12" cy="12" r="9" />
                  <path d="M3 12h18M12 3a15 15 0 0 1 0 18 15 15 0 0 1 0-18Z" />
                </Icon>
              </span>
              <h3>Sin instalación</h3>
              <p>
                No hay tienda ni descarga de escritorio. Abres la página, pulsas jugar
                y el motor carga el juego.
              </p>
            </article>

            <article className="project-card glass">
              <span className="card-icon" aria-hidden="true">
                <Icon>
                  <rect x="3" y="4" width="18" height="16" rx="3" />
                  <path d="M8 4v3M16 4v3M3 9h18" />
                </Icon>
              </span>
              <h3>Una sola pestaña</h3>
              <p>
                El botón de jugar navega al juego en esta misma pestaña. Cuando
                termines, el botón atrás te devuelve aquí.
              </p>
            </article>
          </div>
        </section>

        <section className="section shell" id="como-jugar" aria-labelledby="how-title">
          <div className="section-head">
            <p className="section-eyebrow">Cómo jugar</p>
            <h2 className="section-title" id="how-title">
              Tres pasos y estás dentro.
            </h2>
            <p className="section-lead">
              No hay cuentas, controles que configurar ni descargas que esperar.
              Solo el juego y tu navegador.
            </p>
          </div>

          <ol className="steps">
            {STEPS.map((step, index) => (
              <li className="step glass" key={step.title}>
                <span className="step-index" aria-hidden="true">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </li>
            ))}
          </ol>

          <div className="cta-panel glass">
            <div className="cta-copy">
              <h2>Todo listo para jugar.</h2>
              <p>
                Pulsa el botón y empieza la partida. La primera carga tarda un poco más
                porque el navegador descarga el motor completo.
              </p>
            </div>
            <a className="btn btn-primary" href={GAME_URL}>
              <PlayIcon />
              Abrir Mision Trainer
              <ArrowIcon />
            </a>
          </div>
        </section>

        <Ranking />
      </main>

      <footer className="site-foot shell">
        <div className="foot-brand">
          <BrandMark />
          <span>Mision Trainer · Godot Web Export</span>
        </div>
        <div className="foot-meta">
          <span>Hecho para jugar en el navegador</span>
          <span>La partida se abre en esta pestaña</span>
        </div>
      </footer>
    </div>
  )
}
