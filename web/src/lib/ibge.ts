// Municípios e malhas territoriais da API pública do IBGE.
// Adaptado do primeiro protótipo do projeto (jvrb/edupredict_ai).
import type { Feature, FeatureCollection, Geometry, Position } from 'geojson'

export interface Municipio {
  id: number
  nome: string
  uf: string
}

export type Malha = FeatureCollection<Geometry, Record<string, unknown>>
export type Limites = [[number, number], [number, number]]

const URL_MUNICIPIOS = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome'
const URL_MALHAS = 'https://servicodados.ibge.gov.br/api/v3/malhas/municipios'

interface MunicipioIbge {
  id: number
  nome: string
  microrregiao?: { mesorregiao?: { UF?: { sigla: string } } }
  'regiao-imediata'?: { 'regiao-intermediaria'?: { UF?: { sigla: string } } }
}

let cache: Promise<Municipio[]> | null = null

export function carregarMunicipios(): Promise<Municipio[]> {
  cache ??= fetch(URL_MUNICIPIOS)
    .then((resposta) => {
      if (!resposta.ok) throw new Error('Não foi possível carregar a lista de municípios do IBGE.')
      return resposta.json() as Promise<MunicipioIbge[]>
    })
    .then((dados) =>
      dados.map((m) => ({
        id: m.id,
        nome: m.nome,
        uf: m.microrregiao?.mesorregiao?.UF?.sigla ?? m['regiao-imediata']?.['regiao-intermediaria']?.UF?.sigla ?? '',
      })),
    )
    .catch((erro: unknown) => {
      cache = null
      throw erro
    })
  return cache
}

export function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('pt-BR')
}

export function filtrarMunicipios(lista: Municipio[], busca: string, limite = 8) {
  const termo = normalizar(busca.trim())
  if (termo.length < 2) return []
  const comeca: Municipio[] = []
  const contem: Municipio[] = []
  for (const m of lista) {
    const nome = normalizar(m.nome)
    if (nome.startsWith(termo)) comeca.push(m)
    else if (nome.includes(termo)) contem.push(m)
    if (comeca.length >= limite) break
  }
  return [...comeca, ...contem].slice(0, limite)
}

export async function carregarMalha(id: number): Promise<Malha> {
  const params = new URLSearchParams({ formato: 'application/vnd.geo+json', qualidade: 'maxima' })
  const resposta = await fetch(`${URL_MALHAS}/${id}?${params}`)
  if (!resposta.ok) throw new Error('Não foi possível carregar o limite do município.')

  const dados = (await resposta.json()) as Malha | Feature<Geometry, Record<string, unknown>>
  const features = dados.type === 'Feature' ? [dados] : dados.features
  if (!features?.length || !features[0].geometry) {
    throw new Error('Limite do município inválido.')
  }
  return { type: 'FeatureCollection', features }
}

export function calcularLimites(geometria: Geometry): Limites | null {
  let oeste = Infinity
  let sul = Infinity
  let leste = -Infinity
  let norte = -Infinity

  const visitar = (valor: unknown): void => {
    if (!Array.isArray(valor)) return
    if (valor.length >= 2 && typeof valor[0] === 'number' && typeof valor[1] === 'number') {
      const [lon, lat] = valor as Position
      oeste = Math.min(oeste, lon)
      sul = Math.min(sul, lat)
      leste = Math.max(leste, lon)
      norte = Math.max(norte, lat)
      return
    }
    valor.forEach(visitar)
  }

  if (geometria.type === 'GeometryCollection') {
    geometria.geometries.forEach((g) => {
      const l = calcularLimites(g)
      if (l) visitar([l[0], l[1]])
    })
  } else {
    visitar(geometria.coordinates)
  }

  return Number.isFinite(oeste)
    ? [
        [oeste, sul],
        [leste, norte],
      ]
    : null
}
