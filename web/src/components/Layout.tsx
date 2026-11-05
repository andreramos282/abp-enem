import type { ReactNode } from 'react'
import { ClipboardPlus, FileText, GraduationCap, LayoutGrid, LogOut } from 'lucide-react'
import { navegar, type Rota } from '../lib/rotas'
import { lerAnalise } from '../lib/armazenamento'
import { cx } from './ui'

interface ItemMenu {
  rota: Rota
  rotulo: string
  rotuloCurto: string
  icone: typeof LayoutGrid
}

function itensMenu(): ItemMenu[] {
  const itens: ItemMenu[] = [
    { rota: 'visao-geral', rotulo: 'Visão geral', rotuloCurto: 'Visão geral', icone: LayoutGrid },
    { rota: 'nova-analise', rotulo: 'Nova análise', rotuloCurto: 'Analisar', icone: ClipboardPlus },
  ]
  if (lerAnalise()) {
    itens.push({ rota: 'resultado', rotulo: 'Último resultado', rotuloCurto: 'Resultado', icone: FileText })
  }
  return itens
}

export function Logo({ claro = false }: { claro?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span
        className={cx(
          'grid size-9 place-items-center rounded-[10px]',
          claro ? 'bg-white text-primaria' : 'bg-primaria text-white',
        )}
      >
        <GraduationCap className="size-5" aria-hidden />
      </span>
      <span className={cx('text-lg font-bold', claro ? 'text-white' : 'text-texto')}>EducaRadar</span>
    </div>
  )
}

export function Layout({ rota, children }: { rota: Rota; children: ReactNode }) {
  const itens = itensMenu()

  return (
    <div className="min-h-dvh lg:flex">
      {/* Menu lateral (computador) */}
      <aside className="sticky top-0 hidden print:hidden h-dvh w-62 shrink-0 flex-col border-r border-borda bg-white px-4 py-6 lg:flex">
        <div className="px-2 pb-6">
          <Logo />
        </div>
        <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400">MENU</p>
        <nav className="flex flex-col gap-1" aria-label="Menu principal">
          {itens.map(({ rota: destino, rotulo, icone: Icone }) => {
            const ativo = destino === rota
            return (
              <a
                key={destino}
                href={`#/${destino}`}
                aria-current={ativo ? 'page' : undefined}
                className={cx(
                  'flex items-center gap-3 rounded-[10px] px-3 py-2.5 text-sm transition-colors',
                  ativo ? 'bg-primaria-clara font-semibold text-primaria' : 'font-medium text-slate-600 hover:bg-slate-50',
                )}
              >
                <Icone className="size-5" aria-hidden />
                {rotulo}
              </a>
            )
          })}
        </nav>
        <div className="mt-auto border-t border-borda pt-4">
          <div className="flex items-center gap-3 px-2">
            <span className="grid size-9 place-items-center rounded-full bg-primaria-clara text-[13px] font-semibold text-primaria">
              AS
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">Ana Souza</p>
              <p className="truncate text-xs text-suave">Coordenação pedagógica</p>
            </div>
            <button
              type="button"
              onClick={() => navegar('login')}
              className="grid size-9 place-items-center rounded-lg text-suave hover:bg-slate-50 hover:text-texto"
              aria-label="Sair"
              title="Sair"
            >
              <LogOut className="size-4" aria-hidden />
            </button>
          </div>
        </div>
      </aside>

      {/* Cabeçalho (celular e tablet) */}
      <header className="sticky top-0 z-20 flex print:hidden items-center justify-between border-b border-borda bg-white/95 px-4 py-3 backdrop-blur lg:hidden">
        <Logo />
        <button
          type="button"
          onClick={() => navegar('login')}
          className="grid size-10 place-items-center rounded-lg text-suave hover:bg-slate-50"
          aria-label="Sair"
        >
          <LogOut className="size-5" aria-hidden />
        </button>
      </header>

      <main className="min-w-0 flex-1 px-4 pb-28 pt-5 sm:px-6 lg:px-10 lg:pb-10 lg:pt-8">
        <div className="mx-auto w-full max-w-6xl">{children}</div>
      </main>

      {/* Navegação inferior (celular e tablet) */}
      <nav
        className="fixed inset-x-0 bottom-0 z-20 print:hidden border-t border-borda bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"
        aria-label="Menu principal"
      >
        <div className="mx-auto flex max-w-md">
          {itens.map(({ rota: destino, rotuloCurto, icone: Icone }) => {
            const ativo = destino === rota
            return (
              <a
                key={destino}
                href={`#/${destino}`}
                aria-current={ativo ? 'page' : undefined}
                className={cx(
                  'flex min-h-16 flex-1 flex-col items-center justify-center gap-1 text-[11px]',
                  ativo ? 'font-semibold text-primaria' : 'font-medium text-suave',
                )}
              >
                <Icone className="size-5" aria-hidden />
                {rotuloCurto}
              </a>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

export function CabecalhoPagina({
  titulo,
  subtitulo,
  voltar,
  acoes,
}: {
  titulo: string
  subtitulo?: string
  voltar?: { rota: Rota; rotulo: string }
  acoes?: ReactNode
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        {voltar && (
          <a
            href={`#/${voltar.rota}`}
            className="mb-2 inline-flex items-center gap-1.5 text-sm font-medium text-primaria hover:underline"
          >
            ← {voltar.rotulo}
          </a>
        )}
        <h1 className="text-2xl font-bold tracking-tight sm:text-[26px]">{titulo}</h1>
        {subtitulo && <p className="mt-1.5 text-sm text-suave">{subtitulo}</p>}
      </div>
      {acoes && <div className="flex flex-wrap gap-2 sm:shrink-0">{acoes}</div>}
    </div>
  )
}
