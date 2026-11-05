import { useEffect, useRef, useState } from 'react'
import type { Map as MapboxMap } from 'mapbox-gl'
import { MapPinned } from 'lucide-react'
import { calcularLimites, type Malha } from '../lib/ibge'
import { usePreferencias, type Tema } from '../lib/preferencias'

const TOKEN = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN
const FONTE = 'limite-municipio'
const CAMADA_LINHA = 'limite-municipio-linha'
const CAMADA_PREENCHIMENTO = 'limite-municipio-preenchimento'

const estilo = (tema: Tema) => `mapbox://styles/mapbox/${tema === 'escuro' ? 'dark' : 'light'}-v11`
const cor = (tema: Tema) => (tema === 'escuro' ? '#818cf8' : '#4f46e5')

// Mapa do Mapbox com o limite oficial do município (adaptado do protótipo EduPredict AI).
export function MapaMunicipio({ malha, nome }: { malha: Malha | null; nome?: string }) {
  const { tema, t } = usePreferencias()
  const container = useRef<HTMLDivElement>(null)
  const mapa = useRef<MapboxMap | null>(null)
  const temaDoMapa = useRef<Tema>(tema)
  const [pronto, setPronto] = useState(false)
  const [erro, setErro] = useState(false)

  useEffect(() => {
    if (!TOKEN || !container.current) return
    let descartado = false

    void import('mapbox-gl')
      .then(({ default: mapboxgl }) => {
        if (descartado || !container.current) return
        mapboxgl.accessToken = TOKEN
        const instancia = new mapboxgl.Map({
          container: container.current,
          style: estilo(temaDoMapa.current),
          center: [-52, -14],
          zoom: 3.2,
          minZoom: 2.5,
          maxZoom: 14,
          maxBounds: [
            [-80, -38],
            [-28, 9],
          ],
          attributionControl: false,
          cooperativeGestures: true,
        })
        instancia.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right')
        instancia.addControl(new mapboxgl.AttributionControl({ compact: true }), 'bottom-left')
        instancia.on('load', () => setPronto(true))
        instancia.on('error', () => setErro(true))
        mapa.current = instancia
      })
      .catch(() => setErro(true))

    return () => {
      descartado = true
      mapa.current?.remove()
      mapa.current = null
    }
  }, [])

  // Troca o estilo do mapa junto com o tema da página.
  useEffect(() => {
    const instancia = mapa.current
    if (!instancia || !pronto || temaDoMapa.current === tema) return
    temaDoMapa.current = tema
    setPronto(false)
    instancia.setStyle(estilo(tema))
    instancia.once('style.load', () => setPronto(true))
  }, [tema, pronto])

  useEffect(() => {
    const instancia = mapa.current
    if (!instancia || !pronto || !malha) return

    const fonte = instancia.getSource(FONTE)
    if (fonte && 'setData' in fonte) {
      fonte.setData(malha)
    } else {
      instancia.addSource(FONTE, { type: 'geojson', data: malha })
      instancia.addLayer({
        id: CAMADA_PREENCHIMENTO,
        type: 'fill',
        source: FONTE,
        paint: { 'fill-color': cor(temaDoMapa.current), 'fill-opacity': 0.1 },
      })
      instancia.addLayer({
        id: CAMADA_LINHA,
        type: 'line',
        source: FONTE,
        paint: { 'line-color': cor(temaDoMapa.current), 'line-width': 2 },
      })
    }

    const limites = malha.features[0] ? calcularLimites(malha.features[0].geometry) : null
    if (limites) instancia.fitBounds(limites, { padding: 40, maxZoom: 11.5, duration: 1000 })
  }, [malha, pronto])

  if (!TOKEN || erro) {
    return (
      <div className="flex h-full min-h-64 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-primaria-borda bg-primaria-clara/50 p-6 text-center">
        <MapPinned className="size-8 text-primaria-texto" aria-hidden />
        <div>
          <p className="text-sm font-semibold text-texto">{nome ?? t.mapa.indisponivel}</p>
          <p className="mx-auto mt-1 max-w-xs text-xs text-suave">{erro ? t.mapa.erro : t.mapa.semToken}</p>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={container}
      className="h-full min-h-64 w-full overflow-hidden rounded-2xl"
      role="region"
      aria-label={t.mapa.rotulo(nome)}
    />
  )
}
