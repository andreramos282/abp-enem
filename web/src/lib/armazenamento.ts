import type { Perfil, Previsao } from './api'
import type { Idioma } from './i18n'
import type { Valores } from './perfil'

// Guarda a última análise para a tela de resultado sobreviver a um F5.
// sessionStorage pode falhar (aba anônima, bloqueio), então há uma cópia em memória.
export interface UltimaAnalise {
  perfil: Perfil
  valores: Valores
  rotulos: Valores
  previsao: Previsao
  idioma: Idioma
}

const CHAVE = 'abp-enem:ultima-analise'
let emMemoria: UltimaAnalise | null = null

export function salvarAnalise(analise: UltimaAnalise) {
  emMemoria = analise
  try {
    sessionStorage.setItem(CHAVE, JSON.stringify(analise))
  } catch {
    /* sem armazenamento: segue só em memória */
  }
}

export function lerAnalise(): UltimaAnalise | null {
  if (emMemoria) return emMemoria
  try {
    const bruto = sessionStorage.getItem(CHAVE)
    const lida = bruto ? (JSON.parse(bruto) as Partial<UltimaAnalise>) : null
    emMemoria = lida?.perfil && lida.previsao && lida.valores ? (lida as UltimaAnalise) : null
  } catch {
    emMemoria = null
  }
  return emMemoria
}
