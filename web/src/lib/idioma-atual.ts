import { LOCALE, type Idioma } from './i18n'

// Idioma atual fora do React (usado na formatação de números e nas chamadas da API).
// É atualizado pelo ProvedorPreferencias.
let idiomaAtual: Idioma = 'pt'

export const definirIdiomaAtual = (idioma: Idioma) => {
  idiomaAtual = idioma
}
export const obterIdioma = () => idiomaAtual
export const obterLocale = () => LOCALE[idiomaAtual]
