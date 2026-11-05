import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { LOCALE, TEXTOS, type Idioma, type Textos } from './i18n'

export type Tema = 'claro' | 'escuro'

interface Preferencias {
  idioma: Idioma
  tema: Tema
  t: Textos
  setIdioma: (idioma: Idioma) => void
  alternarTema: () => void
}

const CHAVE_IDIOMA = 'abp-enem:idioma'
const CHAVE_TEMA = 'abp-enem:tema'

// localStorage pode falhar (aba anônima, bloqueio); a página continua funcionando sem ele.
function ler(chave: string) {
  try {
    return localStorage.getItem(chave)
  } catch {
    return null
  }
}

function gravar(chave: string, valor: string) {
  try {
    localStorage.setItem(chave, valor)
  } catch {
    /* sem persistência */
  }
}

function idiomaInicial(): Idioma {
  const salvo = ler(CHAVE_IDIOMA)
  if (salvo === 'pt' || salvo === 'en') return salvo
  return navigator.language?.toLowerCase().startsWith('pt') === false ? 'en' : 'pt'
}

function temaInicial(): Tema {
  const salvo = ler(CHAVE_TEMA)
  if (salvo === 'claro' || salvo === 'escuro') return salvo
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'escuro' : 'claro'
}

// Idioma atual fora do React (usado na formatação de números e nas chamadas da API).
let idiomaAtual: Idioma = 'pt'
export const obterIdioma = () => idiomaAtual
export const obterLocale = () => LOCALE[idiomaAtual]

const Contexto = createContext<Preferencias | null>(null)

export function ProvedorPreferencias({ children }: { children: ReactNode }) {
  const [idioma, setIdioma] = useState<Idioma>(idiomaInicial)
  const [tema, setTema] = useState<Tema>(temaInicial)
  idiomaAtual = idioma

  useEffect(() => {
    gravar(CHAVE_IDIOMA, idioma)
    document.documentElement.lang = LOCALE[idioma]
  }, [idioma])

  useEffect(() => {
    gravar(CHAVE_TEMA, tema)
    const raiz = document.documentElement
    raiz.dataset.theme = tema === 'escuro' ? 'dark' : 'light'
    raiz.style.colorScheme = tema === 'escuro' ? 'dark' : 'light'
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', tema === 'escuro' ? '#0b1120' : '#4f46e5')
  }, [tema])

  const valor = useMemo<Preferencias>(
    () => ({
      idioma,
      tema,
      t: TEXTOS[idioma],
      setIdioma,
      alternarTema: () => setTema((atual) => (atual === 'escuro' ? 'claro' : 'escuro')),
    }),
    [idioma, tema],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

export function usePreferencias() {
  const contexto = useContext(Contexto)
  if (!contexto) throw new Error('usePreferencias deve ser usado dentro de ProvedorPreferencias')
  return contexto
}
