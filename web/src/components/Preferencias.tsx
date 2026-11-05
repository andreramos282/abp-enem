import { Moon, Sun } from 'lucide-react'
import type { Idioma } from '../lib/i18n'
import { usePreferencias } from '../lib/usePreferencias'
import { cx } from '../lib/estilos'

// Botões de idioma (PT/EN) e de tema (claro/escuro).
export function ControlesPreferencias({ sobreEscuro = false }: { sobreEscuro?: boolean }) {
  const { idioma, setIdioma, tema, alternarTema, t } = usePreferencias()
  const idiomas: Idioma[] = ['pt', 'en']

  return (
    <div className="flex items-center gap-2">
      <div
        role="radiogroup"
        aria-label={t.preferencias.idioma}
        className={cx('flex rounded-lg p-0.5', sobreEscuro ? 'bg-white/15' : 'bg-trilho')}
      >
        {idiomas.map((opcao) => {
          const ativo = opcao === idioma
          return (
            <button
              key={opcao}
              type="button"
              role="radio"
              aria-checked={ativo}
              lang={opcao === 'pt' ? 'pt-BR' : 'en'}
              onClick={() => setIdioma(opcao)}
              className={cx(
                'min-h-8 min-w-9 rounded-md px-2 text-xs font-semibold uppercase transition-colors',
                ativo
                  ? sobreEscuro
                    ? 'bg-white text-[#4f46e5]'
                    : 'bg-superficie text-texto shadow-sm'
                  : sobreEscuro
                    ? 'text-white/80 hover:text-white'
                    : 'text-suave hover:text-texto',
              )}
            >
              {opcao}
            </button>
          )
        })}
      </div>
      <button
        type="button"
        onClick={alternarTema}
        aria-label={tema === 'escuro' ? t.preferencias.temaClaro : t.preferencias.temaEscuro}
        title={tema === 'escuro' ? t.preferencias.temaClaro : t.preferencias.temaEscuro}
        className={cx(
          'grid size-9 place-items-center rounded-lg transition-colors',
          sobreEscuro ? 'bg-white/15 text-white hover:bg-white/25' : 'bg-trilho text-texto-2 hover:text-texto',
        )}
      >
        {tema === 'escuro' ? <Sun className="size-4" aria-hidden /> : <Moon className="size-4" aria-hidden />}
      </button>
    </div>
  )
}
