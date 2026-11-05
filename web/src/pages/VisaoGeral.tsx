import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { AlertTriangle, BarChart3, ClipboardPlus, School, Search, Users, X } from 'lucide-react'
import {
  analisarMunicipio,
  formatarNumero,
  nivelDaEscola,
  type AnaliseMunicipio,
  type EscolaResumo,
} from '../lib/api'
import { carregarMalha, carregarMunicipios, filtrarMunicipios, type Malha, type Municipio } from '../lib/ibge'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { MapaMunicipio } from '../components/MapaMunicipio'
import {
  AvisoMock,
  BadgeRisco,
  Botao,
  Carregando,
  Cartao,
  Kpi,
  MensagemErro,
  TituloCartao,
  cx,
} from '../components/ui'

const ESCOLAS_INICIAIS = 8

export function VisaoGeral() {
  const [busca, setBusca] = useState('')
  const [municipios, setMunicipios] = useState<Municipio[]>([])
  const [sugestoes, setSugestoes] = useState<Municipio[]>([])
  const [listaAberta, setListaAberta] = useState(false)
  const [destaque, setDestaque] = useState(0)
  const [erroBusca, setErroBusca] = useState('')
  const [selecionado, setSelecionado] = useState<Municipio | null>(null)
  const [malha, setMalha] = useState<Malha | null>(null)
  const [analise, setAnalise] = useState<AnaliseMunicipio | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erroAnalise, setErroAnalise] = useState('')
  const [verTodas, setVerTodas] = useState(false)
  const requisicao = useRef(0)

  useEffect(() => {
    if (busca.trim().length < 2 || municipios.length > 0) return
    carregarMunicipios()
      .then(setMunicipios)
      .catch((e: unknown) => setErroBusca(e instanceof Error ? e.message : 'Erro ao buscar municípios.'))
  }, [busca, municipios.length])

  useEffect(() => {
    setSugestoes(filtrarMunicipios(municipios, busca))
    setDestaque(0)
  }, [busca, municipios])

  async function selecionar(municipio: Municipio) {
    const id = ++requisicao.current
    setSelecionado(municipio)
    setBusca(`${municipio.nome} – ${municipio.uf}`)
    setListaAberta(false)
    setAnalise(null)
    setErroAnalise('')
    setVerTodas(false)
    setCarregando(true)

    carregarMalha(municipio.id)
      .then((m) => id === requisicao.current && setMalha(m))
      .catch(() => id === requisicao.current && setMalha(null))

    try {
      const resultado = await analisarMunicipio(municipio.nome, municipio.uf)
      if (id === requisicao.current) setAnalise(resultado)
    } catch (e) {
      if (id === requisicao.current) setErroAnalise(e instanceof Error ? e.message : 'Erro ao analisar o município.')
    } finally {
      if (id === requisicao.current) setCarregando(false)
    }
  }

  function limpar() {
    requisicao.current++
    setBusca('')
    setSelecionado(null)
    setMalha(null)
    setAnalise(null)
    setErroAnalise('')
    setCarregando(false)
  }

  function teclado(e: KeyboardEvent<HTMLInputElement>) {
    if (!listaAberta || sugestoes.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setDestaque((d) => (d + 1) % sugestoes.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setDestaque((d) => (d - 1 + sugestoes.length) % sugestoes.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      void selecionar(sugestoes[destaque])
    } else if (e.key === 'Escape') {
      setListaAberta(false)
    }
  }

  const stats = analise?.estatisticas_gerais
  const escolasAltoRisco = analise?.escolas.filter((e) => e.status_alerta === 'ALTO_RISCO').length ?? 0

  return (
    <>
      <CabecalhoPagina
        titulo="Visão geral"
        subtitulo="Busque um município para ver o risco de baixo desempenho no ENEM por escola."
        acoes={
          <Botao onClick={() => navegar('nova-analise')} className="w-full sm:w-auto">
            <ClipboardPlus className="size-4" aria-hidden />
            Nova análise
          </Botao>
        }
      />

      {/* Busca */}
      <div className="relative mb-6">
        <label htmlFor="busca-municipio" className="sr-only">
          Buscar município
        </label>
        <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-suave" aria-hidden />
        <input
          id="busca-municipio"
          type="text"
          role="combobox"
          aria-expanded={listaAberta && sugestoes.length > 0}
          aria-controls="sugestoes-municipio"
          aria-autocomplete="list"
          autoComplete="off"
          placeholder="Buscar município (ex.: Jacareí)"
          value={busca}
          onChange={(e) => {
            setBusca(e.target.value)
            setListaAberta(true)
            setErroBusca('')
          }}
          onFocus={() => setListaAberta(true)}
          onBlur={() => window.setTimeout(() => setListaAberta(false), 150)}
          onKeyDown={teclado}
          className="min-h-13 w-full rounded-2xl border border-borda bg-white pl-12 pr-12 text-base shadow-cartao placeholder:text-slate-400"
        />
        {busca && (
          <button
            type="button"
            onClick={limpar}
            className="absolute right-3 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-lg text-suave hover:bg-slate-50"
            aria-label="Limpar busca"
          >
            <X className="size-4" aria-hidden />
          </button>
        )}
        {listaAberta && sugestoes.length > 0 && (
          <ul
            id="sugestoes-municipio"
            role="listbox"
            className="absolute inset-x-0 top-full z-30 mt-2 max-h-80 overflow-auto rounded-2xl border border-borda bg-white p-1.5 shadow-lg"
          >
            {sugestoes.map((m, i) => (
              <li key={m.id} role="option" aria-selected={i === destaque}>
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => void selecionar(m)}
                  className={cx(
                    'flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm',
                    i === destaque ? 'bg-primaria-clara text-primaria' : 'hover:bg-slate-50',
                  )}
                >
                  <span className="font-medium">{m.nome}</span>
                  <span className="text-xs text-suave">{m.uf}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {erroBusca && <p className="mt-2 text-sm text-risco-alto">{erroBusca}</p>}
      </div>

      {analise && (
        <div className="mb-6">
          <AvisoMock modelo={analise.modelo} />
        </div>
      )}

      {/* Indicadores */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
        <Kpi
          titulo="Risco previsto"
          valor={stats ? `${formatarNumero(stats.percentual_risco_municipio, 1)}%` : '—'}
          detalhe={stats ? 'dos alunos avaliados' : 'Selecione um município'}
          tom={stats && stats.percentual_risco_municipio >= 50 ? 'alto' : 'neutro'}
          icone={<AlertTriangle className="size-4" aria-hidden />}
        />
        <Kpi
          titulo="Alunos avaliados"
          valor={stats ? formatarNumero(stats.total_alunos_avaliados) : '—'}
          icone={<Users className="size-4" aria-hidden />}
        />
        <Kpi
          titulo="Média geral das notas"
          valor={stats ? formatarNumero(stats.media_geral, 1) : '—'}
          detalhe={stats ? 'média observada (não prevista)' : undefined}
          icone={<BarChart3 className="size-4" aria-hidden />}
        />
        <Kpi
          titulo="Escolas em alto risco"
          valor={stats ? `${escolasAltoRisco} de ${stats.total_escolas_unicas}` : '—'}
          tom={escolasAltoRisco > 0 ? 'alto' : 'neutro'}
          icone={<School className="size-4" aria-hidden />}
        />
      </div>

      {/* Mapa + distribuição */}
      <div className="mb-6 grid gap-4 lg:grid-cols-5">
        <Cartao className="h-72 overflow-hidden p-1.5 sm:h-96 lg:col-span-3">
          <MapaMunicipio malha={malha} nome={selecionado ? `${selecionado.nome} – ${selecionado.uf}` : undefined} />
        </Cartao>
        <Cartao className="p-5 sm:p-6 lg:col-span-2">
          <TituloCartao titulo="Escolas por nível de risco" subtitulo="% de alunos classificados em risco em cada escola" />
          {analise ? <DistribuicaoRisco escolas={analise.escolas} /> : <SemMunicipio carregando={carregando} />}
        </Cartao>
      </div>

      {erroAnalise && (
        <div className="mb-6">
          <MensagemErro texto={erroAnalise} onTentarNovamente={selecionado ? () => void selecionar(selecionado) : undefined} />
        </div>
      )}

      {/* Escolas */}
      {analise && (
        <Cartao className="overflow-hidden">
          <div className="p-5 sm:p-6">
            <TituloCartao
              titulo="Escolas prioritárias para intervenção"
              subtitulo={`${analise.escolas.length} escolas em ${analise.municipio} – ${analise.uf}, ordenadas pelo risco`}
            />
          </div>
          <TabelaEscolas escolas={verTodas ? analise.escolas : analise.escolas.slice(0, ESCOLAS_INICIAIS)} />
          {analise.escolas.length > ESCOLAS_INICIAIS && (
            <div className="border-t border-borda p-3 text-center">
              <button
                type="button"
                onClick={() => setVerTodas((v) => !v)}
                className="min-h-10 rounded-lg px-4 text-sm font-semibold text-primaria hover:bg-primaria-clara"
              >
                {verTodas ? 'Mostrar menos' : `Ver todas as ${analise.escolas.length} escolas`}
              </button>
            </div>
          )}
        </Cartao>
      )}
    </>
  )
}

function SemMunicipio({ carregando }: { carregando: boolean }) {
  if (carregando) return <Carregando texto="Analisando município…" />
  return (
    <div className="flex h-full min-h-40 flex-col items-center justify-center gap-2 text-center">
      <Search className="size-6 text-slate-300" aria-hidden />
      <p className="max-w-56 text-sm text-suave">Busque um município acima para ver a distribuição das escolas.</p>
    </div>
  )
}

function DistribuicaoRisco({ escolas }: { escolas: EscolaResumo[] }) {
  const total = escolas.length || 1
  const grupos = [
    { nivel: 'alto' as const, rotulo: 'Risco alto (≥ 50%)', cor: 'bg-risco-alto' },
    { nivel: 'medio' as const, rotulo: 'Risco médio (25–50%)', cor: 'bg-risco-medio' },
    { nivel: 'baixo' as const, rotulo: 'Risco baixo (< 25%)', cor: 'bg-risco-baixo' },
  ].map((g) => ({ ...g, qtd: escolas.filter((e) => nivelDaEscola(e.status_alerta) === g.nivel).length }))

  return (
    <div className="mt-6 flex flex-col gap-5">
      <div className="flex h-3 overflow-hidden rounded-full bg-slate-100" aria-hidden>
        {grupos.map((g) => (
          <div key={g.nivel} className={g.cor} style={{ width: `${(g.qtd / total) * 100}%` }} />
        ))}
      </div>
      <ul className="flex flex-col gap-4">
        {grupos.map((g) => (
          <li key={g.nivel} className="flex items-center gap-3">
            <span className={cx('size-2.5 shrink-0 rounded-full', g.cor)} aria-hidden />
            <span className="flex-1 text-sm text-texto-2">{g.rotulo}</span>
            <span className="text-sm font-semibold tabular-nums">
              {g.qtd} <span className="font-normal text-suave">({formatarNumero((g.qtd / total) * 100)}%)</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function TabelaEscolas({ escolas }: { escolas: EscolaResumo[] }) {
  return (
    <>
      {/* Computador: tabela */}
      <div className="hidden md:block">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-[11px] font-semibold tracking-wider text-slate-400">
            <tr>
              <th className="px-6 py-2.5 font-semibold">ESCOLA (CÓDIGO INEP)</th>
              <th className="px-4 py-2.5 text-right font-semibold">ALUNOS</th>
              <th className="px-4 py-2.5 text-right font-semibold">MÉDIA OBSERVADA</th>
              <th className="px-4 py-2.5 font-semibold">ALUNOS EM RISCO</th>
              <th className="px-6 py-2.5 font-semibold">NÍVEL</th>
            </tr>
          </thead>
          <tbody>
            {escolas.map((e) => (
              <tr key={e.co_escola} className="border-t border-borda">
                <td className="px-6 py-3.5 font-medium">{e.co_escola}</td>
                <td className="px-4 py-3.5 text-right tabular-nums text-texto-2">{e.total_alunos_escola}</td>
                <td className="px-4 py-3.5 text-right tabular-nums text-texto-2">{formatarNumero(e.media_escola, 1)}</td>
                <td className="px-4 py-3.5">
                  <BarraPercentual valor={e.percentual_risco_escola} />
                </td>
                <td className="px-6 py-3.5">
                  <BadgeRisco nivel={nivelDaEscola(e.status_alerta)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Celular: cartões */}
      <ul className="flex flex-col gap-3 px-4 pb-4 md:hidden">
        {escolas.map((e) => (
          <li key={e.co_escola} className="rounded-xl border border-borda p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold">{e.co_escola}</span>
              <BadgeRisco nivel={nivelDaEscola(e.status_alerta)} />
            </div>
            <p className="mt-1 text-xs text-suave">
              {e.total_alunos_escola} alunos · média {formatarNumero(e.media_escola, 1)}
            </p>
            <div className="mt-3">
              <BarraPercentual valor={e.percentual_risco_escola} />
            </div>
          </li>
        ))}
      </ul>
    </>
  )
}

function BarraPercentual({ valor }: { valor: number }) {
  const cor = valor >= 50 ? 'bg-risco-alto' : valor >= 25 ? 'bg-risco-medio' : 'bg-risco-baixo'
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 min-w-20 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={cx('h-full rounded-full', cor)} style={{ width: `${Math.min(100, valor)}%` }} />
      </div>
      <span className="w-12 text-right text-sm font-semibold tabular-nums">{formatarNumero(valor, 1)}%</span>
    </div>
  )
}
