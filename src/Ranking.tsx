import { useEffect, useState } from 'react'

// Ranking de salas: sale de la vista pública `ranking_salas` de Supabase, que llena el
// relay con cada evento de la NASA que termina en el juego. La clave publicable solo
// permite leer.
const SUPABASE_URL = 'https://nsaeswvffgfxueftnqda.supabase.co'
const SUPABASE_KEY = 'sb_publishable_NlUgFetEGekxx4395OD_Kg_YGt6Emxg'
const CONSULTA =
  '/rest/v1/ranking_salas?select=*&jugados=gt.0&order=superados.desc,mejor_tiempo_seg.asc.nullslast&limit=10'
const REFRESCO_MS = 30_000

interface FilaRanking {
  sala: string
  superados: number
  jugados: number
  mejor_tiempo_seg: string | number | null
  dano_promedio_pct: string | number | null
  ultima_vez: string
}

type Estado =
  | { tipo: 'cargando' }
  | { tipo: 'error' }
  | { tipo: 'listo'; filas: FilaRanking[] }

function numero(valor: string | number | null): number | null {
  if (valor === null || valor === undefined) return null
  const n = Number(valor)
  return Number.isFinite(n) ? n : null
}

function haceCuanto(fechaIso: string): string {
  const seg = Math.max(0, (Date.now() - new Date(fechaIso).getTime()) / 1000)
  if (seg < 60) return 'hace un momento'
  if (seg < 3600) return `hace ${Math.round(seg / 60)} min`
  if (seg < 86400) return `hace ${Math.round(seg / 3600)} h`
  return `hace ${Math.round(seg / 86400)} d`
}

export default function Ranking() {
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' })

  useEffect(() => {
    let vivo = true
    const cargar = async () => {
      try {
        const r = await fetch(SUPABASE_URL + CONSULTA, {
          headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` },
        })
        if (!r.ok) throw new Error(String(r.status))
        const filas = (await r.json()) as FilaRanking[]
        if (vivo) setEstado({ tipo: 'listo', filas })
      } catch {
        if (vivo) setEstado((previo) => (previo.tipo === 'listo' ? previo : { tipo: 'error' }))
      }
    }
    cargar()
    const id = window.setInterval(cargar, REFRESCO_MS)
    return () => {
      vivo = false
      window.clearInterval(id)
    }
  }, [])

  return (
    <section className="section shell" id="ranking" aria-labelledby="ranking-title">
      <div className="section-head">
        <p className="section-eyebrow">Ranking</p>
        <h2 className="section-title" id="ranking-title">
          ¿Quién resiste mejor el clima espacial?
        </h2>
        <p className="section-lead">
          Cada evento real de la NASA que termina en el juego suma aquí. Juega con
          <code className="ranking-code">?sala=TU_NOMBRE</code> al final de la dirección para
          aparecer en la tabla.
        </p>
      </div>

      <div className="ranking glass">
        {estado.tipo === 'cargando' && <p className="ranking-vacio">Cargando el ranking…</p>}
        {estado.tipo === 'error' && (
          <p className="ranking-vacio">No se pudo cargar el ranking. Inténtalo más tarde.</p>
        )}
        {estado.tipo === 'listo' && estado.filas.length === 0 && (
          <p className="ranking-vacio">Todavía no hay partidas. ¡Sé el primero en superar una tormenta solar!</p>
        )}
        {estado.tipo === 'listo' && estado.filas.length > 0 && (
          <table className="ranking-tabla">
            <thead>
              <tr>
                <th scope="col">#</th>
                <th scope="col">Sala</th>
                <th scope="col" className="num">Superados</th>
                <th scope="col" className="num">Jugados</th>
                <th scope="col" className="num">Mejor reparación</th>
                <th scope="col" className="num">Daño promedio</th>
                <th scope="col" className="num ranking-cuando">Última vez</th>
              </tr>
            </thead>
            <tbody>
              {estado.filas.map((fila, i) => {
                const tiempo = numero(fila.mejor_tiempo_seg)
                const dano = numero(fila.dano_promedio_pct)
                return (
                  <tr key={fila.sala}>
                    <td className="ranking-pos">{i + 1}</td>
                    <td className="ranking-sala">{fila.sala}</td>
                    <td className="num">{fila.superados}</td>
                    <td className="num">{fila.jugados}</td>
                    <td className="num">{tiempo === null ? '—' : `${tiempo.toFixed(1)} s`}</td>
                    <td className="num">{dano === null ? '—' : `${dano.toFixed(1)} %`}</td>
                    <td className="num ranking-cuando">{haceCuanto(fila.ultima_vez)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}
