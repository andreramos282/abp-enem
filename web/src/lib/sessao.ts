import { useSyncExternalStore } from 'react'

// Sessão do usuário logado: token JWT e dados básicos, guardados no navegador.
// localStorage pode falhar (aba anônima, bloqueio), então há uma cópia em memória.

export interface Usuario {
  id: number
  nome: string
  email: string
  cargo: string
}

export interface Sessao {
  token: string
  usuario: Usuario
}

const CHAVE = 'abp-enem:sessao'
let emMemoria: Sessao | null | undefined
const ouvintes = new Set<() => void>()

function avisar() {
  ouvintes.forEach((ouvinte) => ouvinte())
}

// Hook: a tela desenha de novo quando alguém entra ou sai.
export function useSessao(): Sessao | null {
  return useSyncExternalStore((ouvinte) => {
    ouvintes.add(ouvinte)
    return () => ouvintes.delete(ouvinte)
  }, lerSessao)
}

export function lerSessao(): Sessao | null {
  if (emMemoria !== undefined) return emMemoria
  try {
    const bruto = localStorage.getItem(CHAVE)
    const lida = bruto ? (JSON.parse(bruto) as Partial<Sessao>) : null
    emMemoria = lida?.token && lida.usuario ? (lida as Sessao) : null
  } catch {
    emMemoria = null
  }
  return emMemoria
}

export function salvarSessao(sessao: Sessao) {
  emMemoria = sessao
  try {
    localStorage.setItem(CHAVE, JSON.stringify(sessao))
  } catch {
    /* sem armazenamento: segue só em memória */
  }
  avisar()
}

export function encerrarSessao() {
  emMemoria = null
  try {
    localStorage.removeItem(CHAVE)
    sessionStorage.clear()
  } catch {
    /* nada a limpar */
  }
  avisar()
}

export function iniciais(nome: string) {
  const partes = nome.trim().split(/\s+/).filter(Boolean)
  return (
    ((partes[0]?.[0] ?? '') + (partes.length > 1 ? (partes[partes.length - 1]?.[0] ?? '') : '')).toUpperCase() || '?'
  )
}
