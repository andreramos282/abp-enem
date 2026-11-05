import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { AlertTriangle, BarChart3, ClipboardPlus, School, Search, Users, X } from 'lucide-react'
import {
  analisarMunicipio,
  formatarNumero,
  nivelDaEscola,
  type AnaliseMunicipio,
  type EscolaResumo,
  type NivelRisco,
} from '../lib/api'
import { carregarMalha, carregarMunicipios, filtrarMunicipios, type Malha, type Municipio } from '../lib/ibge'
import { usePreferencias } from '../lib/preferencias'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { MapaMunicipio } from '../components/MapaMunicipio'
import {
  AvisoMock,
  BadgeRisco,
  Botao,
  COR_NIVEL,
  Carregando,
  Cartao,
  Kpi,
  MensagemErro,
  TituloCartao,
  cx,
} from '../components/ui'

const ESCOLAS_INICIAIS = 8

export function VisaoGeral() {
  const { t } = usePreferencias()
  const [busca, setBusca] = useState('')
  const [municipios, setMunicipios] = useState<Municipio[]>([])
  const [sugestoes, setSugestoes] = useState<Municipio[]>([])
  const [listaAberta, setListaAberta] = useState(false)
  const [destaque, setDestaque] = useState(0)
  const [erroBusca, setErroBusca] = useState(false)
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
      .catch(() => setErroBusca(true))
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
      if (id === requisicao.current) setErroAnalise(e instanceof Error ? e.message : t.visao.erroAnalise)
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
        titulo={t.visao.titulo}
        subtitulo={t.visao.subtitulo}
        acoes={
          <Botao onClick={() => navegar('nova-analise')} className="w-full sm:w-auto">
            <ClipboardPlus className="size-4" aria-hidden />
            {t.nav.novaAnalise}
          </Botao>
        }
      />

      {/* Busca */}
      <div className="relative mb-6">
        <label htmlFor="busca-municipio" className="sr-only">
          {t.visao.buscar}
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
          placeholder={t.visao.buscarExemplo}
          value={busca}
          onChange={(e) => {
            setBusca(e.target.value)
            setListaAberta(true)
            setErroBusca(false)
          }}
          onFocus={() => setListaAberta(true)}
          onBlur={() => window.setTimeout(() => setListaAberta(false), 150)}
          onKeyDown={teclado}
          className="min-h-13 w-full rounded-2xl border border-borda bg-superficie pl-12 pr-12 text-base text-texto shadow-cartao placeholder:text-fraco"
        />
        {busca && (
          <button
            type="button"
            onClick={limpar}
            className="absolute right-3 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-lg text-suave hover:bg-superficie-2"
            aria-label={t.visao.limpar}
          >
            <X className="size-4" aria-hidden />
          </button>
        )}
        {listaAberta && sugestoes.length > 0 && (
          <ul
            id="sugestoes-municipio"
            role="listbox"
            className="absolute inset-x-0 top-full z-30 mt-2 max-h-80 overflow-auto rounded-2xl border border-borda bg-superficie p-1.5 shadow-lg"
          >
            {sugestoes.map((m, i) => (
              <li key={m.id} role="option" aria-selected={i === destaque}>
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => void selecionar(m)}
                  className={cx(
                    'flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm',
                    i === destaque ? 'bg-primaria-clara text-primaria-texto' : 'hover:bg-superficie-2',
                  )}
                >
                  <span className="font-medium">{m.nome}</span>
                  <span className="text-xs text-suave">{m.uf}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {erroBusca && <p className="mt-2 text-sm text-risco-alto">{t.erros.municipios}</p>}
      </div>

      {analise && (
        <div className="mb-6">
          <AvisoMock modelo={analise.modelo} />
        </div>
      )}

      {/* Indicadores */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
        <Kpi
          titulo={t.visao.kpiRisco}
          valor={stats ? `${formatarNumero(stats.percentual_risco_municipio, 1)}%` : '—'}
          detalhe={stats ? t.visao.kpiRiscoDetalhe : t.visao.kpiSelecione}
          tom={stats && stats.percentual_risco_municipio >= 50 ? 'alto' : 'neutro'}
          icone={<AlertTriangle className="size-4" aria-hidden />}
        />
        <Kpi
          titulo={t.visao.kpiAlunos}
          valor={stats ? formatarNumero(stats.total_alunos_avaliados) : '—'}
          icone={<Users className="size-4" aria-hidden />}
        />
        <Kpi
          titulo={t.visao.kpiMedia}
          valor={stats ? formatarNumero(stats.media_geral, 1) : '—'}
          detalhe={stats ? t.visao.kpiMediaDetalhe : undefined}
          icone={<BarChart3 className="size-4" aria-hidden />}
        />
        <Kpi
          titulo={t.visao.kpiEscolas}
          valor={stats ? t.visao.deTotal(escolasAltoRisco, stats.total_escolas_unicas) : '—'}
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
          <TituloCartao titulo={t.visao.distribuicaoTitulo} subtitulo={t.visao.distribuicaoSub} />
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
              titulo={t.visao.escolasTitulo}
              subtitulo={t.visao.escolasSub(analise.escolas.length, analise.municipio, analise.uf)}
            />
          </div>
          <TabelaEscolas escolas={verTodas ? analise.escolas : analise.escolas.slice(0, ESCOLAS_INICIAIS)} />
          {analise.escolas.length > ESCOLAS_INICIAIS && (
            <div className="border-t border-borda p-3 text-center">
              <button
                type="button"
                onClick={() => setVerTodas((v) => !v)}
                className="min-h-10 rounded-lg px-4 text-sm font-semibold text-primaria-texto hover:bg-primaria-clara"
              >
                {verTodas ? t.visao.verMenos : t.visao.verTodas(analise.escolas.length)}
              </button>
            </div>
          )}
        </Cartao>
      )}
    </>
  )
}

function SemMunicipio({ carregando }: { carregando: boolean }) {
  const { t } = usePreferencias()
  if (carregando) return <Carregando texto={t.visao.analisando} />
  return (
    <div className="flex h-full min-h-40 flex-col items-center justify-center gap-2 text-center">
      <Search className="size-6 text-fraco" aria-hidden />
      <p className="max-w-56 text-sm text-suave">{t.visao.vazio}</p>
    </div>
  )
}

function DistribuicaoRisco({ escolas }: { escolas: EscolaResumo[] }) {
  const { t } = usePreferencias()
  const total = escolas.length || 1
  const faixas: Array<{ nivel: NivelRisco; rotulo: string }> = [
    { nivel: 'alto', rotulo: t.visao.faixaAlta },
    { nivel: 'medio', rotulo: t.visao.faixaMedia },
    { nivel: 'baixo', rotulo: t.visao.faixaBaixa },
  ]
  const grupos = faixas.map((f) => ({
    ...f,
    qtd: escolas.filter((e) => nivelDaEscola(e.status_alerta) === f.nivel).length,
  }))

  return (
    <div className="mt-6 flex flex-col gap-5">
      <div className="flex h-3 overflow-hidden rounded-full bg-trilho" aria-hidden>
        {grupos.map((g) => (
          <div key={g.nivel} className={COR_NIVEL[g.nivel]} style={{ width: `${(g.qtd / total) * 100}%` }} />
        ))}
      </div>
      <ul className="flex flex-col gap-4">
        {grupos.map((g) => (
          <li key={g.nivel} className="flex items-center gap-3">
            <span className={cx('size-2.5 shrink-0 rounded-full', COR_NIVEL[g.nivel])} aria-hidden />
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
  const { t } = usePreferencias()
  return (
    <>
      {/* Computador: tabela */}
      <div className="hidden md:block">
        <table className="w-full text-sm">
          <thead className="bg-superficie-2 text-left text-[11px] font-semibold tracking-wider text-fraco">
            <tr>
              <th className="px-6 py-2.5 font-semibold">{t.visao.colEscola}</th>
              <th className="px-4 py-2.5 text-right font-semibold">{t.visao.colAlunos}</th>
              <th className="px-4 py-2.5 text-right font-semibold">{t.visao.colMedia}</th>
              <th className="px-4 py-2.5 font-semibold">{t.visao.colRisco}</th>
              <th className="px-6 py-2.5 font-semibold">{t.visao.colNivel}</th>
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
              {t.visao.alunosMedia(e.total_alunos_escola, formatarNumero(e.media_escola, 1))}
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
  const nivel: NivelRisco = valor >= 50 ? 'alto' : valor >= 25 ? 'medio' : 'baixo'
  return (
    <div className="flex items-center gap-3">
      <div className="h-2 min-w-20 flex-1 overflow-hidden rounded-full bg-trilho">
        <div className={cx('h-full rounded-full', COR_NIVEL[nivel])} style={{ width: `${Math.min(100, valor)}%` }} />
      </div>
      <span className="w-12 text-right text-sm font-semibold tabular-nums">{formatarNumero(valor, 1)}%</span>
    </div>
  )
}
