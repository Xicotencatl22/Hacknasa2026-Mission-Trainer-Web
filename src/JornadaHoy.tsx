import { useEffect, useState } from 'react'

// Misiones de la jornada de hoy: salen de la función `jornada_del_dia` de Supabase,
// la misma que usa el relay para mandarlas al juego. Son iguales para todas las salas.
const SUPABASE_URL = 'https://nsaeswvffgfxueftnqda.supabase.co'
const SUPABASE_KEY = 'sb_publishable_NlUgFetEGekxx4395OD_Kg_YGt6Emxg'

interface Mision {
  mision_id: string
  tipo: string
  titulo: string
  dificultad: string
  fecha: string
  simulacro: boolean
}

interface Jornada {
  fecha: string
  misiones: Mision[]
}

const NOMBRE_TIPO: Record<string, string> = {
  CME: 'Eyección de masa coronal',
  FLR: 'Fulguración solar',
  GST: 'Tormenta geomagnética',
  SEP: 'Partículas solares',
  IPS: 'Choque interplanetario',
}

function fechaLegible(iso: string): string {
  const [a, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(a, m - 1, d)).toLocaleDateString('es-MX', {
    weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC',
  })
}

export default function JornadaHoy() {
  const [jornada, setJornada] = useState<Jornada | null>(null)

  useEffect(() => {
    let vivo = true
    fetch(`${SUPABASE_URL}/rest/v1/rpc/jornada_del_dia`, {
      method: 'POST',
      headers: {
        apikey: SUPABASE_KEY,
        Authorization: `Bearer ${SUPABASE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: '{}',
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((j: Jornada | null) => {
        if (vivo && j && Array.isArray(j.misiones)) setJornada(j)
      })
      .catch(() => {})
    return () => {
      vivo = false
    }
  }, [])

  if (!jornada || jornada.misiones.length === 0) return null

  return (
    <div className="jornada glass">
      <div className="jornada-cabecera">
        <h3 className="jornada-titulo">Jornada de hoy</h3>
        <span className="jornada-fecha">{fechaLegible(jornada.fecha)}</span>
      </div>
      <p className="jornada-texto">
        Las mismas misiones para todas las salas, con el clima espacial real de los últimos
        días. Complétalas todas en el juego para ganar el bono de jornada.
      </p>
      <ol className="jornada-lista">
        {jornada.misiones.map((m) => (
          <li key={m.mision_id} className="jornada-mision">
            <span className={`jornada-tipo jornada-tipo-${m.tipo.toLowerCase()}`}>{m.tipo}</span>
            <span className="jornada-mision-texto">
              <strong>{m.titulo}</strong>
              <small>
                {NOMBRE_TIPO[m.tipo] ?? m.tipo} · {m.simulacro ? 'Simulacro' : m.fecha} · {m.dificultad}
              </small>
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
