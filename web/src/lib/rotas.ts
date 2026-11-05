import { useEffect, useState } from 'react'

// Roteamento simples por hash (#/rota): funciona em qualquer servidor estático.
export type Rota = 'login' | 'visao-geral' | 'nova-analise' | 'resultado'

const ROTAS: Rota[] = ['login', 'visao-geral', 'nova-analise', 'resultado']

function lerRota(): Rota {
  const atual = window.location.hash.replace(/^#\/?/, '') as Rota
  return ROTAS.includes(atual) ? atual : 'visao-geral'
}

export function navegar(rota: Rota) {
  window.location.hash = `/${rota}`
}

export function useRota(): Rota {
  const [rota, setRota] = useState<Rota>(lerRota)

  useEffect(() => {
    const atualizar = () => {
      setRota(lerRota())
      window.scrollTo({ top: 0 })
    }
    window.addEventListener('hashchange', atualizar)
    return () => window.removeEventListener('hashchange', atualizar)
  }, [])

  return rota
}
