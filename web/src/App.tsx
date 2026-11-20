import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { ProvedorPreferencias } from './lib/preferencias'
import { usePreferencias } from './lib/usePreferencias'
import { useRota } from './lib/rotas'
import { Login } from './pages/Login'
import { NovaAnalise } from './pages/NovaAnalise'
import { Resultado } from './pages/Resultado'
import { Lote } from './pages/Lote'
import { Historico } from './pages/Historico'
import { Sobre } from './pages/Sobre'
import { useSessao } from './lib/sessao'
import { VisaoGeral } from './pages/VisaoGeral'

function Rotas() {
  const rota = useRota()
  const { t } = usePreferencias()
  const sessao = useSessao()

  useEffect(() => {
    document.title = `${t.titulos[rota]} · ${t.marca}`
  }, [rota, t])

  // Sem login, qualquer página leva à tela de entrada.
  if (rota === 'login' || !sessao) return <Login />

  return (
    <Layout rota={rota}>
      {rota === 'visao-geral' && <VisaoGeral />}
      {rota === 'nova-analise' && <NovaAnalise />}
      {rota === 'resultado' && <Resultado />}
      {rota === 'lote' && <Lote />}
      {rota === 'historico' && <Historico />}
      {rota === 'sobre' && <Sobre />}
    </Layout>
  )
}

export default function App() {
  return (
    <ProvedorPreferencias>
      <Rotas />
    </ProvedorPreferencias>
  )
}
