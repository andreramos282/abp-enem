import { useEffect } from 'react'
import { Layout } from './components/Layout'
import { ProvedorPreferencias } from './lib/preferencias'
import { usePreferencias } from './lib/usePreferencias'
import { useRota } from './lib/rotas'
import { Login } from './pages/Login'
import { NovaAnalise } from './pages/NovaAnalise'
import { Resultado } from './pages/Resultado'
import { VisaoGeral } from './pages/VisaoGeral'

function Rotas() {
  const rota = useRota()
  const { t } = usePreferencias()

  useEffect(() => {
    document.title = `${t.titulos[rota]} · ${t.marca}`
  }, [rota, t])

  if (rota === 'login') return <Login />

  return (
    <Layout rota={rota}>
      {rota === 'visao-geral' && <VisaoGeral />}
      {rota === 'nova-analise' && <NovaAnalise />}
      {rota === 'resultado' && <Resultado />}
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
