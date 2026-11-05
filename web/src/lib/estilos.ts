import type { NivelRisco } from './api'

/** Junta classes CSS, ignorando valores falsos. */
export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ')
}

/** Cor de fundo de cada nível de risco (tokens definidos em index.css). */
export const COR_NIVEL: Record<NivelRisco, string> = {
  alto: 'bg-risco-alto',
  medio: 'bg-risco-medio',
  baixo: 'bg-risco-baixo',
}
