import { createContext, useContext } from 'react'
import type { Idioma, Textos } from './i18n'

export type Tema = 'claro' | 'escuro'

export interface Preferencias {
  idioma: Idioma
  tema: Tema
  t: Textos
  setIdioma: (idioma: Idioma) => void
  alternarTema: () => void
}

export const ContextoPreferencias = createContext<Preferencias | null>(null)

/** Idioma, tema e textos traduzidos. Use dentro de <ProvedorPreferencias>. */
export function usePreferencias() {
  const contexto = useContext(ContextoPreferencias)
  if (!contexto) throw new Error('usePreferencias deve ser usado dentro de ProvedorPreferencias')
  return contexto
}
