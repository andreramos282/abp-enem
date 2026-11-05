import { useEffect, useState } from 'react'
import { BookOpen, ClipboardPlus, Home, Monitor, Printer, School, Users, Wifi } from 'lucide-react'
import { buscarOpcoes, formatarNumero, preverRisco, type Fator, type NivelRisco } from '../lib/api'
import { lerAnalise, salvarAnalise, type UltimaAnalise } from '../lib/armazenamento'
import type { Textos } from '../lib/i18n'
import { rotulosDoPerfil } from '../lib/perfil'
import { usePreferencias } from '../lib/preferencias'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { AvisoMock, BadgeRisco, Botao, Cartao, TituloCartao, cx } from '../components/ui'

const COR_MEDIDOR: Record<NivelRisco, string> = {
  alto: 'var(--color-risco-alto)',
  medio: 'var(--color-risco-medio)',
  baixo: 'var(--color-risco-baixo)',
}

type ChaveRecomendacao = keyof Textos['resultado']['recomendacoes']

// Intervenção sugerida para cada fator que aumenta o risco.
const RECOMENDACAO_POR_FATOR: Record<string, { chave: ChaveRecomendacao; icone: typeof BookOpen }> = {
  computador: { chave: 'computador', icone: Monitor },
  internet: { chave: 'internet', icone: Wifi },
  renda_per_capita: { chave: 'renda', icone: Home },
  renda_familiar: { chave: 'renda', icone: Home },
  escolaridade_mae: { chave: 'familia', icone: Users },
  escolaridade_pai: { chave: 'familia', icone: Users },
  rede_escola: { chave: 'reforco', icone: BookOpen },
  localizacao_escola: { chave: 'rural', icone: School },
  faixa_etaria: { chave: 'recuperacao', icone: BookOpen },
}

function recomendacoesPara(fatores: Fator[]) {
  const vistas = new Set<ChaveRecomendacao>()
  const lista: Array<{ chave: ChaveRecomendacao; icone: typeof BookOpen; alta: boolean }> = []
  for (const fator of fatores) {
    const rec = RECOMENDACAO_POR_FATOR[fator.variavel]
    if (!rec || fator.impacto <= 0 || vistas.has(rec.chave)) continue
    vistas.add(rec.chave)
    lista.push({ ...rec, alta: fator.impacto >= 8 })
  }
  return lista.slice(0, 3)
}

function Medidor({ valor, nivel }: { valor: number; nivel: NivelRisco }) {
  const { t } = usePreferencias()
  const raio = 80
  const circunferencia = 2 * Math.PI * raio
  return (
    <div className="relative size-48 sm:size-52">
      <svg viewBox="0 0 200 200" className="size-full -rotate-90" aria-hidden>
        <circle cx="100" cy="100" r={raio} fill="none" stroke="var(--color-primaria-clara)" strokeWidth="16" />
        <circle
          cx="100"
          cy="100"
          r={raio}
          fill="none"
          stroke={COR_MEDIDOR[nivel]}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={`${valor * circunferencia} ${circunferencia}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold tracking-tight sm:text-[44px]">{formatarNumero(valor * 100)}%</span>
        <span className="text-[13px] font-medium text-suave">{t.resultado.deRisco}</span>
      </div>
    </div>
  )
}

export function Resultado() {
  const { t, idioma } = usePreferencias()
  const [analise, setAnalise] = useState<UltimaAnalise | null>(lerAnalise)
  const [atualizando, setAtualizando] = useState(false)

  // Se o idioma mudou depois da análise, pede de novo à API os textos no idioma atual.
  useEffect(() => {
    if (!analise || analise.idioma === idioma) return
    let cancelado = false
    setAtualizando(true)
    Promise.all([preverRisco(analise.perfil), buscarOpcoes()])
      .then(([previsao, campos]) => {
        if (cancelado) return
        const atualizada = { ...analise, previsao, idioma, rotulos: rotulosDoPerfil(campos, analise.valores) }
        salvarAnalise(atualizada)
        setAnalise(atualizada)
      })
      .catch(() => undefined)
      .finally(() => !cancelado && setAtualizando(false))
    return () => {
      cancelado = true
    }
  }, [analise, idioma])

  if (!analise) {
    return (
      <>
        <CabecalhoPagina titulo={t.resultado.titulo} />
        <Cartao className="flex flex-col items-center gap-4 p-10 text-center">
          <ClipboardPlus className="size-10 text-primaria-texto" aria-hidden />
          <p className="max-w-sm text-sm text-suave">{t.resultado.vazio}</p>
          <Botao onClick={() => navegar('nova-analise')}>{t.resultado.fazerAnalise}</Botao>
        </Cartao>
      </>
    )
  }

  const { previsao, rotulos } = analise
  const maiorImpacto = Math.max(...previsao.fatores.map((f) => Math.abs(f.impacto)), 1)
  const recomendacoes = recomendacoesPara(previsao.fatores)
  const resumo = [rotulos.rede_escola && t.resultado.rede(rotulos.rede_escola), rotulos.renda_familiar, rotulos.uf_escola]
    .filter(Boolean)
    .join(' · ')

  return (
    <>
      <CabecalhoPagina
        voltar={{ rota: 'nova-analise', rotulo: t.resultado.voltar }}
        titulo={t.resultado.titulo}
        subtitulo={resumo ? `${t.resultado.perfil}: ${resumo}` : undefined}
        acoes={
          <>
            <Botao variante="secundario" onClick={() => window.print()} className="flex-1 sm:flex-none">
              <Printer className="size-4" aria-hidden />
              {t.resultado.imprimir}
            </Botao>
            <Botao onClick={() => navegar('nova-analise')} className="flex-1 sm:flex-none">
              {t.resultado.novaAnalise}
            </Botao>
          </>
        }
      />

      <div className="mb-6 flex flex-col gap-3">
        <AvisoMock modelo={previsao.modelo} />
        {atualizando && (
          <p className="text-sm text-suave" role="status">
            {t.resultado.atualizando}
          </p>
        )}
      </div>

      <div className="mb-6 grid items-start gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Cartao className="flex flex-col items-center gap-5 p-6 sm:p-7">
          <p className="text-sm font-medium text-suave">{t.resultado.probabilidade}</p>
          <Medidor valor={previsao.probabilidade_risco} nivel={previsao.nivel_risco} />
          <BadgeRisco nivel={previsao.nivel_risco} />
          <p className="text-center text-xs leading-relaxed text-suave">{t.resultado.explicacao}</p>
        </Cartao>

        <Cartao className="p-5 sm:p-7">
          <TituloCartao titulo={t.resultado.fatoresTitulo} subtitulo={t.resultado.fatoresSub} />
          <ul className="mt-6 flex flex-col gap-5">
            {previsao.fatores.map((fator) => {
              const aumenta = fator.impacto > 0
              return (
                <li
                  key={fator.variavel}
                  className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_200px_80px] sm:items-center sm:gap-4"
                >
                  <span className="text-sm font-medium text-texto-2">{fator.descricao}</span>
                  <div className="flex items-center gap-3 sm:contents">
                    <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-trilho">
                      <div
                        className={cx('h-full rounded-full', aumenta ? 'bg-risco-alto' : 'bg-risco-baixo')}
                        style={{ width: `${(Math.abs(fator.impacto) / maiorImpacto) * 100}%` }}
                      />
                    </div>
                    <span
                      className={cx(
                        'w-20 text-right text-sm font-semibold tabular-nums',
                        aumenta ? 'text-risco-alto' : 'text-risco-baixo',
                      )}
                    >
                      {aumenta ? '+' : '−'}
                      {formatarNumero(Math.abs(fator.impacto), 1)} {t.resultado.pp}
                    </span>
                  </div>
                </li>
              )
            })}
          </ul>
          <div className="mt-6 flex flex-wrap gap-5 text-xs font-medium text-suave">
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-risco-alto" aria-hidden /> {t.resultado.aumenta}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-risco-baixo" aria-hidden /> {t.resultado.reduz}
            </span>
          </div>
        </Cartao>
      </div>

      {recomendacoes.length > 0 && (
        <Cartao className="p-5 sm:p-7">
          <TituloCartao titulo={t.resultado.recomendacoesTitulo} subtitulo={t.resultado.recomendacoesSub} />
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {recomendacoes.map(({ chave, icone: Icone, alta }) => {
              const texto = t.resultado.recomendacoes[chave]
              return (
                <article key={chave} className="flex flex-col gap-3 rounded-xl border border-borda bg-superficie-2 p-5">
                  <div className="flex items-center justify-between gap-2">
                    <span className="grid size-10 place-items-center rounded-[10px] bg-primaria-clara text-primaria-texto">
                      <Icone className="size-5" aria-hidden />
                    </span>
                    <span
                      className={cx('text-xs font-semibold', alta ? 'text-risco-alto-texto' : 'text-risco-medio-texto')}
                    >
                      {alta ? t.resultado.prioridadeAlta : t.resultado.prioridadeMedia}
                    </span>
                  </div>
                  <h3 className="text-[15px] font-semibold">{texto.titulo}</h3>
                  <p className="text-[13px] leading-relaxed text-suave">{texto.descricao}</p>
                </article>
              )
            })}
          </div>
        </Cartao>
      )}
    </>
  )
}
