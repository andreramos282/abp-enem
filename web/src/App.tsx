import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { useRota, type Rota } from './lib/rotas'
import { Login } from './pages/Login'
import { NovaAnalise } from './pages/NovaAnalise'
import { Resultado } from './pages/Resultado'
import { VisaoGeral } from './pages/VisaoGeral'

const TITULOS: Record<Rota, string> = {
  login: 'Entrar',
  'visao-geral': 'Visão geral',
  'nova-analise': 'Nova análise',
  resultado: 'Resultado',
}

export default function App() {
  const rota = useRota()

  useEffect(() => {
    document.title = `${TITULOS[rota]} · EducaRadar`
  }, [rota])

  if (rota === 'login') return <Login />

  return (
    <Layout rota={rota}>
      {rota === 'visao-geral' && <VisaoGeral />}
      {rota === 'nova-analise' && <NovaAnalise />}
      {rota === 'resultado' && <Resultado />}
    </Layout>
  )
}
