import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, BarChart3, CalendarRange, Scale, ShieldCheck, Target, Users } from 'lucide-react'
import { buscarResumoModelo, formatarNumero, type ResumoModelo } from '../lib/api'
import { usePreferencias } from '../lib/usePreferencias'
import { CabecalhoPagina } from '../components/Layout'
import { Carregando, Cartao, Kpi, MensagemErro, TituloCartao } from '../components/ui'
import { cx } from '../lib/estilos'

// Grupos que descrevem o contexto do aluno (mesma regra do resultado): aparecem em outra cor.
const CONTEXTO = new Set(['Cor/raça', 'Sexo', 'Região'])

export function Sobre() {
  const { t } = usePreferencias()
  const [resumo, setResumo] = useState<ResumoModelo | null>(null)
  const [erro, setErro] = useState('')

  const carregar = useCallback(() => {
    setErro('')
    buscarResumoModelo()
      .then(setResumo)
      .catch((e: unknown) => setErro(e instanceof Error ? e.message : t.erros.servidor))
  }, [t])

  useEffect(() => {
    carregar()
  }, [carregar])

  const importancia = Object.entries(resumo?.importancia ?? {})
  const maior = Math.max(...importancia.map(([, v]) => v), 1)

  return (
    <>
      <CabecalhoPagina titulo={t.sobre.titulo} subtitulo={t.sobre.subtitulo} />

      {erro && (
        <div className="mb-6">
          <MensagemErro texto={erro} onTentarNovamente={carregar} />
        </div>
      )}
      {!resumo && !erro && <Carregando texto={t.sobre.carregando} />}
      {resumo?.simulado && <p className="mb-6 text-sm text-suave">{t.sobre.simulado}</p>}

      {resumo && !resumo.simulado && (
        <div className="mb-6 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
          <Kpi
            titulo={t.sobre.kpiAuc}
            valor={formatarNumero(resumo.auc_teste ?? 0, 3)}
            detalhe={t.sobre.kpiAucDetalhe}
            icone={<Target className="size-4" aria-hidden />}
          />
          <Kpi
            titulo={resumo.outro_ano ? t.sobre.kpiOutroAno(resumo.outro_ano) : t.sobre.kpiOutroAno(2022)}
            valor={resumo.auc_outro_ano ? formatarNumero(resumo.auc_outro_ano, 3) : '—'}
            detalhe={t.sobre.kpiOutroAnoDetalhe}
            icone={<CalendarRange className="size-4" aria-hidden />}
          />
          <Kpi
            titulo={t.sobre.kpiAlunos}
            valor={formatarNumero(resumo.alunos_amostra ?? 0)}
            detalhe={t.sobre.kpiAlunosDetalhe(resumo.ano_dados ?? 2023)}
            icone={<Users className="size-4" aria-hidden />}
          />
          <Kpi
            titulo={t.sobre.kpiCalibracao}
            valor={
              resumo.calibracao_erro_medio != null
                ? `${formatarNumero(resumo.calibracao_erro_medio * 100, 1)} ${t.resultado.pp}`
                : '—'
            }
            detalhe={t.sobre.kpiCalibracaoDetalhe}
            icone={<BarChart3 className="size-4" aria-hidden />}
          />
        </div>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <Cartao className="p-5 sm:p-7">
            <TituloCartao titulo={t.sobre.oQueFazTitulo} />
            <p className="mt-3 text-sm leading-relaxed text-texto-2">
              {t.sobre.oQueFaz(formatarNumero(resumo?.corte_media ?? 481, 1))}
            </p>
          </Cartao>
          <Cartao className="p-5 sm:p-7">
            <Titulo icone={Scale} texto={t.sobre.equidadeTitulo} />
            <p className="mt-3 text-sm leading-relaxed text-texto-2">{t.sobre.equidade}</p>
          </Cartao>
          <Cartao className="p-5 sm:p-7">
            <Titulo icone={AlertTriangle} texto={t.sobre.limitesTitulo} />
            <Lista itens={t.sobre.limites} />
          </Cartao>
          <Cartao className="p-5 sm:p-7">
            <Titulo icone={ShieldCheck} texto={t.sobre.privacidadeTitulo} />
            <Lista itens={t.sobre.privacidade} />
          </Cartao>
        </div>

        {importancia.length > 0 && (
          <Cartao className="p-5 sm:p-7">
            <TituloCartao titulo={t.sobre.pesoTitulo} subtitulo={t.sobre.pesoSub} />
            <ul className="mt-6 flex flex-col gap-4">
              {importancia.map(([grupo, valor]) => (
                <li key={grupo} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)_52px] items-center gap-3">
                  <span className="text-sm text-texto-2">{grupo}</span>
                  <div className="h-2.5 overflow-hidden rounded-full bg-trilho">
                    <div
                      className={cx('h-full rounded-full', CONTEXTO.has(grupo) ? 'bg-fraco' : 'bg-primaria')}
                      style={{ width: `${(valor / maior) * 100}%` }}
                    />
                  </div>
                  <span className="text-right text-sm font-semibold tabular-nums">{formatarNumero(valor, 1)}</span>
                </li>
              ))}
            </ul>
          </Cartao>
        )}
      </div>
    </>
  )
}

function Titulo({ icone: Icone, texto }: { icone: typeof Scale; texto: string }) {
  return (
    <h2 className="flex items-center gap-2.5 text-base font-semibold">
      <span className="grid size-8 place-items-center rounded-lg bg-primaria-clara text-primaria-texto">
        <Icone className="size-4" aria-hidden />
      </span>
      {texto}
    </h2>
  )
}

function Lista({ itens }: { itens: string[] }) {
  return (
    <ul className="mt-4 flex list-disc flex-col gap-2 pl-5 text-sm leading-relaxed text-texto-2">
      {itens.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}
