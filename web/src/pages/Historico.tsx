import { useCallback, useEffect, useState } from 'react'
import { ClipboardPlus, ExternalLink, Trash2 } from 'lucide-react'
import {
  apagarAnalise,
  buscarHistorico,
  buscarOpcoes,
  formatarNumero,
  type Campo,
  type ItemHistorico,
  type Perfil,
} from '../lib/api'
import { salvarAnalise } from '../lib/armazenamento'
import { obterLocale } from '../lib/idioma-atual'
import { rotulosDoPerfil, type Valores } from '../lib/perfil'
import { usePreferencias } from '../lib/usePreferencias'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { BadgeRisco, Botao, Carregando, Cartao, MensagemErro, TituloCartao } from '../components/ui'
import { cx } from '../lib/estilos'

// Respostas do perfil como texto, no mesmo formato do formulário.
function valoresDoPerfil(perfil: Perfil): Valores {
  const valores: Valores = {}
  for (const [campo, valor] of Object.entries(perfil)) {
    if (valor !== null && valor !== undefined && typeof valor !== 'object')
      valores[campo as keyof Perfil] = String(valor)
  }
  return valores
}

export function Historico() {
  const { t, idioma } = usePreferencias()
  const [itens, setItens] = useState<ItemHistorico[] | null>(null)
  const [campos, setCampos] = useState<Campo[]>([])
  const [erro, setErro] = useState('')
  const [confirmar, setConfirmar] = useState<number | null>(null)

  const carregar = useCallback(() => {
    setErro('')
    Promise.all([buscarHistorico(), buscarOpcoes()])
      .then(([historico, opcoes]) => {
        setItens(historico)
        setCampos(opcoes)
      })
      .catch((e: unknown) => setErro(e instanceof Error ? e.message : t.erros.servidor))
  }, [t])

  useEffect(() => {
    carregar()
  }, [carregar])

  function abrir(item: ItemHistorico) {
    const valores = valoresDoPerfil(item.perfil)
    salvarAnalise({
      perfil: item.perfil,
      valores,
      rotulos: rotulosDoPerfil(campos, valores),
      previsao: item.previsao,
      idioma,
    })
    navegar('resultado')
  }

  async function apagar(id: number) {
    if (confirmar !== id) {
      setConfirmar(id)
      return
    }
    try {
      await apagarAnalise(id)
      setItens((lista) => lista?.filter((i) => i.id !== id) ?? null)
    } catch (e) {
      setErro(e instanceof Error ? e.message : t.erros.servidor)
    } finally {
      setConfirmar(null)
    }
  }

  const data = (iso: string) => new Date(iso).toLocaleString(obterLocale(), { dateStyle: 'short', timeStyle: 'short' })
  const resumo = (perfil: Perfil) => {
    const r = rotulosDoPerfil(campos, valoresDoPerfil(perfil))
    return [r.rede_escola && t.resultado.rede(r.rede_escola), r.renda_familiar, r.uf_escola].filter(Boolean).join(' · ')
  }

  return (
    <>
      <CabecalhoPagina
        titulo={t.historico.titulo}
        subtitulo={t.historico.subtitulo}
        acoes={
          <Botao onClick={() => navegar('nova-analise')} className="w-full sm:w-auto">
            <ClipboardPlus className="size-4" aria-hidden />
            {t.nav.novaAnalise}
          </Botao>
        }
      />

      {erro && (
        <div className="mb-6">
          <MensagemErro texto={erro} onTentarNovamente={carregar} />
        </div>
      )}

      {!itens && !erro && <Carregando texto={t.historico.carregando} />}

      {itens && itens.length === 0 && (
        <Cartao className="flex flex-col items-center gap-4 p-10 text-center">
          <ClipboardPlus className="size-10 text-primaria-texto" aria-hidden />
          <p className="max-w-sm text-sm text-suave">{t.historico.vazio}</p>
        </Cartao>
      )}

      {itens && itens.length > 0 && (
        <Cartao className="overflow-hidden">
          <div className="p-5 sm:p-6">
            <TituloCartao titulo={t.historico.total(itens.length)} />
          </div>
          <ul className="divide-y divide-borda border-t border-borda">
            {itens.map((item) => (
              <li
                key={item.id}
                className="grid gap-3 px-5 py-4 sm:grid-cols-[140px_minmax(0,1fr)_90px_130px_auto] sm:items-center sm:px-6"
              >
                <span className="text-xs tabular-nums text-suave sm:text-sm">{data(item.criado_em)}</span>
                <span className="text-sm font-medium text-texto-2">{resumo(item.perfil)}</span>
                <span className="text-sm font-semibold tabular-nums">
                  {formatarNumero(item.previsao.probabilidade_risco * 100, 1)}%
                </span>
                <span>
                  <BadgeRisco nivel={item.previsao.nivel_risco} />
                </span>
                <span className="flex gap-2 sm:justify-end">
                  <Botao variante="secundario" onClick={() => abrir(item)}>
                    <ExternalLink className="size-4" aria-hidden />
                    {t.historico.abrir}
                  </Botao>
                  <button
                    type="button"
                    onClick={() => void apagar(item.id)}
                    onBlur={() => setConfirmar(null)}
                    className={cx(
                      'flex min-h-10 items-center gap-1.5 rounded-lg px-3 text-sm font-medium',
                      confirmar === item.id
                        ? 'bg-risco-alto-claro text-risco-alto-texto'
                        : 'text-suave hover:bg-superficie-2 hover:text-texto',
                    )}
                    aria-label={t.historico.apagar}
                  >
                    <Trash2 className="size-4" aria-hidden />
                    {confirmar === item.id ? (
                      t.historico.confirmarApagar
                    ) : (
                      <span className="sr-only">{t.historico.apagar}</span>
                    )}
                  </button>
                </span>
              </li>
            ))}
          </ul>
        </Cartao>
      )}
    </>
  )
}
