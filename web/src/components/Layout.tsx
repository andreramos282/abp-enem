import type { ReactNode } from 'react'
import { ClipboardPlus, FileText, GraduationCap, LayoutGrid, LogOut } from 'lucide-react'
import { navegar, type Rota } from '../lib/rotas'
import { lerAnalise } from '../lib/armazenamento'
import { usePreferencias } from '../lib/usePreferencias'
import { ControlesPreferencias } from './Preferencias'
import { cx } from '../lib/estilos'

interface ItemMenu {
  rota: Rota
  rotulo: string
  rotuloCurto: string
  icone: typeof LayoutGrid
}

export function Logo({ claro = false }: { claro?: boolean }) {
  const { t } = usePreferencias()
  return (
    <div className="flex items-center gap-2.5">
      <span
        className={cx(
          'grid size-9 place-items-center rounded-[10px]',
          claro ? 'bg-white text-[#4f46e5]' : 'bg-primaria text-white',
        )}
      >
        <GraduationCap className="size-5" aria-hidden />
      </span>
      <span className={cx('text-lg font-bold', claro ? 'text-white' : 'text-texto')}>{t.marca}</span>
    </div>
  )
}

export function Layout({ rota, children }: { rota: Rota; children: ReactNode }) {
  const { t } = usePreferencias()
  const itens: ItemMenu[] = [
    { rota: 'visao-geral', rotulo: t.nav.visaoGeral, rotuloCurto: t.nav.visaoGeral, icone: LayoutGrid },
    { rota: 'nova-analise', rotulo: t.nav.novaAnalise, rotuloCurto: t.nav.novaAnaliseCurto, icone: ClipboardPlus },
  ]
  if (lerAnalise()) {
    itens.push({ rota: 'resultado', rotulo: t.nav.resultado, rotuloCurto: t.nav.resultadoCurto, icone: FileText })
  }

  return (
    <div className="min-h-dvh lg:flex">
      {/* Menu lateral (computador) */}
      <aside className="sticky top-0 hidden h-dvh w-62 shrink-0 flex-col border-r border-borda bg-superficie px-4 py-6 print:hidden lg:flex">
        <div className="px-2 pb-6">
          <Logo />
        </div>
        <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-fraco">{t.menu}</p>
        <nav className="flex flex-col gap-1" aria-label={t.menuPrincipal}>
          {itens.map(({ rota: destino, rotulo, icone: Icone }) => {
            const ativo = destino === rota
            return (
              <a
                key={destino}
                href={`#/${destino}`}
                aria-current={ativo ? 'page' : undefined}
                className={cx(
                  'flex items-center gap-3 rounded-[10px] px-3 py-2.5 text-sm transition-colors',
                  ativo
                    ? 'bg-primaria-clara font-semibold text-primaria-texto'
                    : 'font-medium text-texto-menu hover:bg-superficie-2',
                )}
              >
                <Icone className="size-5" aria-hidden />
                {rotulo}
              </a>
            )
          })}
        </nav>
        <div className="mt-auto flex flex-col gap-4 border-t border-borda pt-4">
          <div className="px-2">
            <ControlesPreferencias />
          </div>
          <div className="flex items-center gap-3 px-2">
            <span className="grid size-9 place-items-center rounded-full bg-primaria-clara text-[13px] font-semibold text-primaria-texto">
              AS
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{t.usuario.nome}</p>
              <p className="truncate text-xs text-suave">{t.usuario.cargo}</p>
            </div>
            <button
              type="button"
              onClick={() => navegar('login')}
              className="grid size-9 place-items-center rounded-lg text-suave hover:bg-superficie-2 hover:text-texto"
              aria-label={t.sair}
              title={t.sair}
            >
              <LogOut className="size-4" aria-hidden />
            </button>
          </div>
        </div>
      </aside>

      {/* Cabeçalho (celular e tablet) */}
      <header className="sticky top-0 z-20 flex items-center justify-between gap-2 border-b border-borda bg-superficie/95 px-4 py-3 backdrop-blur print:hidden lg:hidden">
        <Logo />
        <div className="flex items-center gap-1">
          <ControlesPreferencias />
          <button
            type="button"
            onClick={() => navegar('login')}
            className="grid size-9 place-items-center rounded-lg text-suave hover:bg-superficie-2"
            aria-label={t.sair}
          >
            <LogOut className="size-5" aria-hidden />
          </button>
        </div>
      </header>

      <main className="min-w-0 flex-1 px-4 pb-28 pt-5 sm:px-6 lg:px-10 lg:pb-10 lg:pt-8">
        <div className="mx-auto w-full max-w-6xl">{children}</div>
      </main>

      {/* Navegação inferior (celular e tablet) */}
      <nav
        className="fixed inset-x-0 bottom-0 z-20 border-t border-borda bg-superficie/95 pb-[env(safe-area-inset-bottom)] backdrop-blur print:hidden lg:hidden"
        aria-label={t.menuPrincipal}
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
                  ativo ? 'font-semibold text-primaria-texto' : 'font-medium text-suave',
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
            className="mb-2 inline-flex items-center gap-1.5 text-sm font-medium text-primaria-texto hover:underline"
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
