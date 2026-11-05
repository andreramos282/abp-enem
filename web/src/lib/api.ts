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
}

export interface Fator {
  variavel: string
  descricao: string
  impacto: number
}

export interface Previsao {
  probabilidade_risco: number
  nivel_risco: NivelRisco
  fatores: Fator[]
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
  modelo: string
}

export class ErroApi extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

async function requisitar<T>(caminho: string, init?: RequestInit): Promise<T> {
  let resposta: Response
  try {
    resposta = await fetch(caminho, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ErroApi('Não foi possível conectar à API. Verifique se ela está rodando.', 0)
  }
  if (!resposta.ok) {
    const mensagem =
      resposta.status === 422
        ? 'Alguns dados enviados são inválidos. Revise o formulário.'
        : resposta.status === 404
          ? 'Nenhum dado encontrado.'
          : 'A API respondeu com erro. Tente novamente.'
    throw new ErroApi(mensagem, resposta.status)
  }
  return (await resposta.json()) as T
}

export function buscarOpcoes() {
  return requisitar<{ campos: Campo[] }>('/api/opcoes').then((r) => r.campos)
}

export function preverRisco(perfil: Perfil) {
  return requisitar<Previsao>('/api/prever', { method: 'POST', body: JSON.stringify(perfil) })
}

export function analisarMunicipio(municipio: string, uf: string) {
  return requisitar<AnaliseMunicipio>('/api/municipios/analytics', {
    method: 'POST',
    body: JSON.stringify({ municipio, uf }),
  })
}

export const ROTULO_NIVEL: Record<NivelRisco, string> = {
  alto: 'Risco alto',
  medio: 'Risco médio',
  baixo: 'Risco baixo',
}

export function nivelDaEscola(status: EscolaResumo['status_alerta']): NivelRisco {
  return status === 'ALTO_RISCO' ? 'alto' : status === 'MEDIO_RISCO' ? 'medio' : 'baixo'
}

export function formatarNumero(valor: number, casas = 0) {
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas })
}
