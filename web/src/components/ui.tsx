import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { ChevronDown, FlaskConical, LoaderCircle } from 'lucide-react'
import { ROTULO_NIVEL, type NivelRisco } from '../lib/api'

export function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ')
}

export function Cartao({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <section className={cx('rounded-2xl border border-borda bg-white shadow-cartao', className)}>
      {children}
    </section>
  )
}

export function TituloCartao({ titulo, subtitulo, acao }: { titulo: string; subtitulo?: string; acao?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="min-w-0">
        <h2 className="text-base font-semibold text-texto">{titulo}</h2>
        {subtitulo && <p className="mt-1 text-sm text-suave">{subtitulo}</p>}
      </div>
      {acao}
    </div>
  )
}

type VarianteBotao = 'primario' | 'secundario'

export function Botao({
  variante = 'primario',
  carregando = false,
  className,
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: VarianteBotao; carregando?: boolean }) {
  return (
    <button
      {...props}
      disabled={disabled || carregando}
      className={cx(
        'inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-5 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
        variante === 'primario'
          ? 'bg-primaria text-white shadow-[0_4px_12px_rgb(79_70_229/0.25)] hover:bg-primaria-escura'
          : 'border border-borda bg-white text-texto hover:bg-slate-50',
        className,
      )}
    >
      {carregando && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  )
}

const ESTILO_NIVEL: Record<NivelRisco, string> = {
  alto: 'bg-risco-alto-claro text-red-700',
  medio: 'bg-risco-medio-claro text-amber-700',
  baixo: 'bg-risco-baixo-claro text-green-700',
}

const COR_PONTO: Record<NivelRisco, string> = {
  alto: 'bg-risco-alto',
  medio: 'bg-risco-medio',
  baixo: 'bg-risco-baixo',
}

export function BadgeRisco({ nivel }: { nivel: NivelRisco }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold',
        ESTILO_NIVEL[nivel],
      )}
    >
      <span className={cx('size-1.5 rounded-full', COR_PONTO[nivel])} aria-hidden />
      {ROTULO_NIVEL[nivel]}
    </span>
  )
}

export function Kpi({
  titulo,
  valor,
  detalhe,
  tom = 'neutro',
  icone,
}: {
  titulo: string
  valor: string
  detalhe?: string
  tom?: 'neutro' | 'alto' | 'baixo'
  icone?: ReactNode
}) {
  return (
    <Cartao className="p-4 sm:p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-suave sm:text-sm">{titulo}</p>
        {icone && <span className="text-suave">{icone}</span>}
      </div>
      <p className="mt-2 text-2xl font-bold tracking-tight text-texto sm:text-[28px]">{valor}</p>
      {detalhe && (
        <p
          className={cx(
            'mt-1 text-xs font-medium',
            tom === 'alto' ? 'text-risco-alto' : tom === 'baixo' ? 'text-risco-baixo' : 'text-suave',
          )}
        >
          {detalhe}
        </p>
      )}
    </Cartao>
  )
}

export function CampoSelecao({
  id,
  rotulo,
  valor,
  opcoes,
  erro,
  onChange,
}: {
  id: string
  rotulo: string
  valor: string
  opcoes: Array<{ valor: string | number; rotulo: string }>
  erro?: string
  onChange: (valor: string) => void
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] font-medium text-texto-2">
        {rotulo}
      </label>
      <div className="relative">
        <select
          id={id}
          value={valor}
          onChange={(e) => onChange(e.target.value)}
          aria-invalid={Boolean(erro)}
          aria-describedby={erro ? `${id}-erro` : undefined}
          className={cx(
            'min-h-11 w-full appearance-none rounded-xl border bg-white py-2.5 pl-3.5 pr-10 text-sm text-texto',
            valor === '' && 'text-suave',
            erro ? 'border-risco-alto' : 'border-borda',
          )}
        >
          <option value="" disabled>
            Selecione…
          </option>
          {opcoes.map((opcao) => (
            <option key={String(opcao.valor)} value={String(opcao.valor)}>
              {opcao.rotulo}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-suave"
          aria-hidden
        />
      </div>
      {erro && (
        <p id={`${id}-erro`} className="text-xs font-medium text-risco-alto">
          {erro}
        </p>
      )}
    </div>
  )
}

export function Segmentado({
  id,
  rotulo,
  valor,
  opcoes,
  erro,
  onChange,
}: {
  id: string
  rotulo: string
  valor: string
  opcoes: Array<{ valor: string; rotulo: string }>
  erro?: string
  onChange: (valor: string) => void
}) {
  return (
    <fieldset className="flex flex-col gap-1.5">
      <legend id={id} className="mb-1.5 text-[13px] font-medium text-texto-2">
        {rotulo}
      </legend>
      <div
        role="radiogroup"
        aria-labelledby={id}
        className={cx('flex gap-1 rounded-xl bg-slate-100 p-1', erro && 'ring-1 ring-risco-alto')}
      >
        {opcoes.map((opcao) => {
          const ativo = opcao.valor === valor
          return (
            <button
              key={opcao.valor}
              type="button"
              role="radio"
              aria-checked={ativo}
              onClick={() => onChange(opcao.valor)}
              className={cx(
                'min-h-10 flex-1 rounded-lg px-4 text-sm transition-colors',
                ativo ? 'bg-white font-semibold text-texto shadow-sm' : 'font-medium text-suave hover:text-texto',
              )}
            >
              {opcao.rotulo}
            </button>
          )
        })}
      </div>
      {erro && <p className="text-xs font-medium text-risco-alto">{erro}</p>}
    </fieldset>
  )
}

export function AvisoMock({ modelo }: { modelo?: string }) {
  if (modelo !== 'mock') return null
  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <FlaskConical className="mt-0.5 size-4 shrink-0" aria-hidden />
      <p>
        <strong className="font-semibold">Dados simulados.</strong> O modelo ainda está em treinamento; estes
        valores servem apenas para testar a interface.
      </p>
    </div>
  )
}

export function Carregando({ texto }: { texto: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-suave">
      <LoaderCircle className="size-5 animate-spin" aria-hidden />
      {texto}
    </div>
  )
}

export function MensagemErro({ texto, onTentarNovamente }: { texto: string; onTentarNovamente?: () => void }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between">
      <p>{texto}</p>
      {onTentarNovamente && (
        <button type="button" onClick={onTentarNovamente} className="font-semibold underline underline-offset-2">
          Tentar novamente
        </button>
      )}
    </div>
  )
}
