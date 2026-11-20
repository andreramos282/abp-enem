import { obterIdioma, obterLocale } from './idioma-atual'
import { TEXTOS } from './i18n'
import { navegar } from './rotas'
import { encerrarSessao, lerSessao, type Sessao, type Usuario } from './sessao'

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

export type CodigoErro = 'conexao' | 'invalido' | 'naoEncontrado' | 'servidor' | 'sessao'

export class ErroApi extends Error {
  constructor(readonly codigo: CodigoErro) {
    super(TEXTOS[obterIdioma()].erros[codigo])
  }
}

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  const url = `${caminho}${caminho.includes('?') ? '&' : '?'}idioma=${obterIdioma()}`
  const token = lerSessao()?.token
  let resposta: Response
  try {
    resposta = await fetch(url, {
      ...init,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init?.headers,
      },
    })
  } catch {
    throw new ErroApi('conexao')
  }
  if (resposta.status === 401 && token) {
    // Token vencido ou inválido: volta para o login.
    encerrarSessao()
    navegar('login')
    throw new ErroApi('sessao')
  }
  if (!resposta.ok) {
    throw new ErroApi(resposta.status === 422 ? 'invalido' : resposta.status === 404 ? 'naoEncontrado' : 'servidor')
  }
  if (resposta.status === 204) return undefined as T
  return (await resposta.json()) as T
}

// Login: devolve null se o e-mail ou a senha estiverem errados.
export async function entrar(email: string, senha: string): Promise<Sessao | null> {
  let resposta: Response
  try {
    resposta = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha }),
    })
  } catch {
    throw new ErroApi('conexao')
  }
  if (resposta.status === 401 || resposta.status === 422) return null
  if (!resposta.ok) throw new ErroApi('servidor')
  const dados = (await resposta.json()) as { token: string; usuario: Usuario }
  return { token: dados.token, usuario: dados.usuario }
}

export interface ItemHistorico {
  id: number
  criado_em: string
  perfil: Perfil
  previsao: Previsao
}

export interface ResumoModelo {
  modelo: string
  simulado: boolean
  treinado_em: string | null
  ano_dados: number | null
  alunos_amostra: number | null
  corte_media: number | null
  auc_teste: number | null
  recall_teste: number | null
  auc_outro_ano: number | null
  outro_ano: number | null
  calibracao_erro_medio: number | null
  importancia: Record<string, number>
}

export function buscarResumoModelo() {
  return requisitar<ResumoModelo>('/api/modelo')
}

export function buscarHistorico(limite = 100) {
  return requisitar<ItemHistorico[]>(`/api/historico?limite=${limite}`)
}

export function apagarAnalise(id: number) {
  return requisitar<void>(`/api/historico/${id}`, { method: 'DELETE' })
}

export function buscarOpcoes() {
  return requisitar<{ campos: Campo[] }>('/api/opcoes').then((r) => r.campos)
}

// salvar=false: só recalcula (ex.: trocar o idioma do resultado) sem criar outra entrada no histórico.
export function preverRisco(perfil: Perfil, salvar = true) {
  return requisitar<Previsao>(`/api/prever${salvar ? '' : '?salvar=false'}`, {
    method: 'POST',
    body: JSON.stringify(perfil),
  })
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
