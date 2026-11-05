import { BookOpen, ClipboardPlus, Home, Monitor, Printer, School, Users, Wifi } from 'lucide-react'
import { formatarNumero, type Fator, type NivelRisco } from '../lib/api'
import { lerAnalise } from '../lib/armazenamento'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { AvisoMock, BadgeRisco, Botao, Cartao, TituloCartao, cx } from '../components/ui'

const COR_NIVEL: Record<NivelRisco, string> = {
  alto: '#dc2626',
  medio: '#d97706',
  baixo: '#16a34a',
}

interface Recomendacao {
  titulo: string
  descricao: string
  icone: typeof BookOpen
}

// Intervenções sugeridas para cada fator que aumenta o risco.
const RECOMENDACOES: Record<string, Recomendacao> = {
  computador: {
    titulo: 'Acesso a computadores na escola',
    descricao: 'Liberar o laboratório de informática no contraturno para simulados e plataformas de estudo on-line.',
    icone: Monitor,
  },
  internet: {
    titulo: 'Conectividade para estudo',
    descricao: 'Indicar programas de internet para estudantes e disponibilizar Wi-Fi da escola fora do horário de aula.',
    icone: Wifi,
  },
  renda_per_capita: {
    titulo: 'Apoio socioeconômico',
    descricao: 'Encaminhar a família a programas de assistência e garantir isenção de taxas e transporte para a prova.',
    icone: Home,
  },
  escolaridade_mae: {
    titulo: 'Acompanhamento com a família',
    descricao: 'Reuniões periódicas para orientar a família sobre a rotina de estudos e o calendário do ENEM.',
    icone: Users,
  },
  escolaridade_pai: {
    titulo: 'Acompanhamento com a família',
    descricao: 'Reuniões periódicas para orientar a família sobre a rotina de estudos e o calendário do ENEM.',
    icone: Users,
  },
  rede_escola: {
    titulo: 'Reforço em Matemática e Linguagens',
    descricao: 'Grupos de estudo semanais com foco nas áreas de maior peso na nota do ENEM.',
    icone: BookOpen,
  },
  localizacao_escola: {
    titulo: 'Preparatório itinerante',
    descricao: 'Levar aulões e simulados até escolas da zona rural, com material impresso para estudo em casa.',
    icone: School,
  },
  faixa_etaria: {
    titulo: 'Plano de recuperação de aprendizagem',
    descricao: 'Avaliar defasagens acumuladas e montar um plano individual de revisão dos conteúdos básicos.',
    icone: BookOpen,
  },
}

function recomendacoesPara(fatores: Fator[]) {
  const vistas = new Set<string>()
  const lista: Array<Recomendacao & { prioridade: 'alta' | 'media' }> = []
  for (const fator of fatores) {
    const rec = RECOMENDACOES[fator.variavel]
    if (!rec || fator.impacto <= 0 || vistas.has(rec.titulo)) continue
    vistas.add(rec.titulo)
    lista.push({ ...rec, prioridade: fator.impacto >= 8 ? 'alta' : 'media' })
  }
  return lista.slice(0, 3)
}

function Medidor({ valor, nivel }: { valor: number; nivel: NivelRisco }) {
  const raio = 80
  const circunferencia = 2 * Math.PI * raio
  return (
    <div className="relative size-48 sm:size-52">
      <svg viewBox="0 0 200 200" className="size-full -rotate-90" aria-hidden>
        <circle cx="100" cy="100" r={raio} fill="none" stroke="#eef2ff" strokeWidth="16" />
        <circle
          cx="100"
          cy="100"
          r={raio}
          fill="none"
          stroke={COR_NIVEL[nivel]}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={`${valor * circunferencia} ${circunferencia}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-bold tracking-tight sm:text-[44px]">{formatarNumero(valor * 100)}%</span>
        <span className="text-[13px] font-medium text-suave">de risco</span>
      </div>
    </div>
  )
}

export function Resultado() {
  const analise = lerAnalise()

  if (!analise) {
    return (
      <>
        <CabecalhoPagina titulo="Resultado da análise" />
        <Cartao className="flex flex-col items-center gap-4 p-10 text-center">
          <ClipboardPlus className="size-10 text-primaria" aria-hidden />
          <p className="max-w-sm text-sm text-suave">Nenhuma análise feita ainda. Preencha o perfil de um aluno para ver o resultado.</p>
          <Botao onClick={() => navegar('nova-analise')}>Fazer uma análise</Botao>
        </Cartao>
      </>
    )
  }

  const { previsao, rotulos } = analise
  const maiorImpacto = Math.max(...previsao.fatores.map((f) => Math.abs(f.impacto)), 1)
  const recomendacoes = recomendacoesPara(previsao.fatores)
  const resumo = [rotulos.rede_escola && `Rede ${rotulos.rede_escola.toLowerCase()}`, rotulos.renda_familiar, rotulos.uf_escola]
    .filter(Boolean)
    .join(' · ')

  return (
    <>
      <CabecalhoPagina
        voltar={{ rota: 'nova-analise', rotulo: 'Voltar para o formulário' }}
        titulo="Resultado da análise"
        subtitulo={resumo ? `Perfil: ${resumo}` : undefined}
        acoes={
          <>
            <Botao variante="secundario" onClick={() => window.print()} className="flex-1 sm:flex-none">
              <Printer className="size-4" aria-hidden />
              Imprimir
            </Botao>
            <Botao onClick={() => navegar('nova-analise')} className="flex-1 sm:flex-none">
              Nova análise
            </Botao>
          </>
        }
      />

      <div className="mb-6">
        <AvisoMock modelo={previsao.modelo} />
      </div>

      <div className="mb-6 grid items-start gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
        <Cartao className="flex flex-col items-center gap-5 p-6 sm:p-7">
          <p className="text-sm font-medium text-suave">Probabilidade de baixo desempenho</p>
          <Medidor valor={previsao.probabilidade_risco} nivel={previsao.nivel_risco} />
          <BadgeRisco nivel={previsao.nivel_risco} />
          <p className="text-center text-xs leading-relaxed text-suave">
            Chance estimada de o aluno ficar entre os 25% com menor média no ENEM.
          </p>
        </Cartao>

        <Cartao className="p-5 sm:p-7">
          <TituloCartao
            titulo="O que mais pesa nesta previsão"
            subtitulo="Contribuição de cada característica, em pontos percentuais"
          />
          <ul className="mt-6 flex flex-col gap-5">
            {previsao.fatores.map((fator) => {
              const aumenta = fator.impacto > 0
              return (
                <li key={fator.variavel} className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_200px_72px] sm:items-center sm:gap-4">
                  <span className="text-sm font-medium text-texto-2">{fator.descricao}</span>
                  <div className="flex items-center gap-3 sm:contents">
                    <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className={cx('h-full rounded-full', aumenta ? 'bg-risco-alto' : 'bg-risco-baixo')}
                        style={{ width: `${(Math.abs(fator.impacto) / maiorImpacto) * 100}%` }}
                      />
                    </div>
                    <span
                      className={cx(
                        'w-18 text-right text-sm font-semibold tabular-nums',
                        aumenta ? 'text-risco-alto' : 'text-risco-baixo',
                      )}
                    >
                      {aumenta ? '+' : '−'}
                      {formatarNumero(Math.abs(fator.impacto), 1)} p.p.
                    </span>
                  </div>
                </li>
              )
            })}
          </ul>
          <div className="mt-6 flex flex-wrap gap-5 text-xs font-medium text-suave">
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-risco-alto" aria-hidden /> Aumenta o risco
            </span>
            <span className="flex items-center gap-1.5">
              <span className="size-2 rounded-full bg-risco-baixo" aria-hidden /> Reduz o risco
            </span>
          </div>
        </Cartao>
      </div>

      {recomendacoes.length > 0 && (
        <Cartao className="p-5 sm:p-7">
          <TituloCartao
            titulo="Intervenções pedagógicas recomendadas"
            subtitulo="Ações sugeridas a partir dos fatores que mais aumentam o risco deste perfil"
          />
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {recomendacoes.map(({ titulo, descricao, icone: Icone, prioridade }) => (
              <article key={titulo} className="flex flex-col gap-3 rounded-xl border border-borda bg-slate-50 p-5">
                <div className="flex items-center justify-between">
                  <span className="grid size-10 place-items-center rounded-[10px] bg-primaria-clara text-primaria">
                    <Icone className="size-5" aria-hidden />
                  </span>
                  <span
                    className={cx(
                      'text-xs font-semibold',
                      prioridade === 'alta' ? 'text-red-700' : 'text-amber-700',
                    )}
                  >
                    Prioridade {prioridade === 'alta' ? 'alta' : 'média'}
                  </span>
                </div>
                <h3 className="text-[15px] font-semibold">{titulo}</h3>
                <p className="text-[13px] leading-relaxed text-suave">{descricao}</p>
              </article>
            ))}
          </div>
        </Cartao>
      )}
    </>
  )
}
