import { obterIdioma, obterLocale } from './idioma-atual'
import { TEXTOS } from './i18n'

// Tipos e chamadas da API. Segue o contrato em docs/api.md.

export type NivelRisco = 'alto' | 'medio' | 'baixo'

export interface Perfil {
  escolaridade_pai: string
  escolaridade_mae: string
  ocupacao_pai: string
  ocupacao_mae: string
  pessoas_residencia: number
  renda_familiar: string
  computador: string
  internet: string
  tipo_escola: number
  rede_escola: number
  localizacao_escola: number
  uf_escola: string
  faixa_etaria: number
  cor_raca?: number
  sexo?: string
}

export interface Fator {
  variavel: string
  descricao: string
  impacto: number
  // acao: a escola ou a família podem atuar; contexto: o aluno não muda (cor/raça, sexo, região)
  tipo?: 'acao' | 'contexto'
}

export interface Previsao {
  probabilidade_risco: number
  nivel_risco: NivelRisco
  fatores: Fator[]
  acompanhamento_recomendado?: boolean | null
  modelo: string
}

export interface Opcao {
  valor: string | number
  rotulo: string
}

export interface Campo {
  campo: keyof Perfil
  rotulo: string
  opcoes: Opcao[]
}

export interface EscolaResumo {
  co_escola: number
  total_alunos_escola: number
  media_escola: number
  percentual_risco_escola: number
  status_alerta: 'ALTO_RISCO' | 'MEDIO_RISCO' | 'BAIXO_RISCO'
}

export interface AnaliseMunicipio {
  municipio: string
  uf: string
  estatisticas_gerais: {
    total_alunos_avaliados: number
    total_escolas_unicas: number
    media_geral: number
    percentual_risco_municipio: number
  }
  escolas: EscolaResumo[]
  comparacao?: Comparacao | null
  por_rede?: RiscoPorRede[]
  modelo: string
}

export interface Comparacao {
  percentual_risco_uf: number
  percentual_risco_brasil: number
  media_uf: number
  media_brasil: number
}

export interface RiscoPorRede {
  rede_escola: number
  rotulo: string
  total_alunos: number
  percentual_risco: number
  media: number
}

export interface ResultadoLote {
  linha: number
  identificador: string | null
  probabilidade_risco: number | null
  nivel_risco: NivelRisco | null
  acompanhamento_recomendado: boolean | null
  erro: string | null
}

export const MAX_LOTE = 1000

export type CodigoErro = 'conexao' | 'invalido' | 'naoEncontrado' | 'servidor'

export class ErroApi extends Error {
  constructor(readonly codigo: CodigoErro) {
    super(TEXTOS[obterIdioma()].erros[codigo])
  }
}

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  const url = `${caminho}${caminho.includes('?') ? '&' : '?'}idioma=${obterIdioma()}`
  let resposta: Response
  try {
    resposta = await fetch(url, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ErroApi('conexao')
  }
  if (!resposta.ok) {
    throw new ErroApi(resposta.status === 422 ? 'invalido' : resposta.status === 404 ? 'naoEncontrado' : 'servidor')
  }
  return (await resposta.json()) as T
}

export function buscarOpcoes() {
  return requisitar<{ campos: Campo[] }>('/api/opcoes').then((r) => r.campos)
}

export function preverRisco(perfil: Perfil) {
  return requisitar<Previsao>('/api/prever', { method: 'POST', body: JSON.stringify(perfil) })
}

export function preverLote(alunos: Array<Record<string, string | number>>) {
  return requisitar<{ resultados: ResultadoLote[]; modelo: string }>('/api/prever/lote', {
    method: 'POST',
    body: JSON.stringify({ alunos }),
  })
}

export function analisarMunicipio(municipio: string, uf: string) {
  return requisitar<AnaliseMunicipio>('/api/municipios/analytics', {
    method: 'POST',
    body: JSON.stringify({ municipio, uf }),
  })
}

export function nivelDaEscola(status: EscolaResumo['status_alerta']): NivelRisco {
  return status === 'ALTO_RISCO' ? 'alto' : status === 'MEDIO_RISCO' ? 'medio' : 'baixo'
}

export function formatarNumero(valor: number, casas = 0) {
  return valor.toLocaleString(obterLocale(), { minimumFractionDigits: casas, maximumFractionDigits: casas })
}
