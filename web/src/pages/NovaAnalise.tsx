import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { Check, Info, Lock } from 'lucide-react'
import { buscarOpcoes, preverRisco, type Campo, type Perfil } from '../lib/api'
import { salvarAnalise } from '../lib/armazenamento'
import { montarPerfil, rotulosDoPerfil, type Valores } from '../lib/perfil'
import { usePreferencias } from '../lib/preferencias'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { Botao, CampoSelecao, Carregando, Cartao, MensagemErro, Segmentado, cx } from '../components/ui'

// Campos de cada etapa. tipo_escola não aparece: é derivado da rede (ver lib/perfil.ts).
const CAMPOS_POR_SECAO: Array<Array<keyof Perfil>> = [
  ['renda_familiar', 'pessoas_residencia', 'escolaridade_mae', 'escolaridade_pai', 'ocupacao_mae', 'ocupacao_pai', 'faixa_etaria'],
  ['rede_escola', 'localizacao_escola', 'uf_escola'],
  ['computador', 'internet'],
]
const OBRIGATORIOS = CAMPOS_POR_SECAO.flat()
const SEGMENTADOS: Array<keyof Perfil> = ['internet', 'localizacao_escola']

export function NovaAnalise() {
  const { t, idioma } = usePreferencias()
  const [campos, setCampos] = useState<Campo[] | null>(null)
  const [erroCarregar, setErroCarregar] = useState('')
  const [valores, setValores] = useState<Valores>({})
  const [erros, setErros] = useState<Valores>({})
  const [enviando, setEnviando] = useState(false)
  const [erroEnvio, setErroEnvio] = useState('')

  // Recarrega as opções quando o idioma muda (os rótulos vêm traduzidos da API).
  const carregar = useCallback(() => {
    setErroCarregar('')
    buscarOpcoes()
      .then(setCampos)
      .catch((e: unknown) => setErroCarregar(e instanceof Error ? e.message : t.form.erroCarregar))
  }, [t])

  useEffect(() => {
    carregar()
  }, [carregar])

  const porCampo = useMemo(() => new Map(campos?.map((c) => [c.campo, c] as const)), [campos])
  const preenchidas = CAMPOS_POR_SECAO.map((lista) => lista.every((c) => valores[c]))

  function alterar(campo: keyof Perfil, valor: string) {
    setValores((v) => ({ ...v, [campo]: valor }))
    setErros((e) => ({ ...e, [campo]: undefined }))
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    const faltando: Valores = {}
    for (const campo of OBRIGATORIOS) if (!valores[campo]) faltando[campo] = t.form.obrigatorio
    setErros(faltando)
    const primeiro = Object.keys(faltando)[0]
    if (primeiro) {
      document.getElementById(`campo-${primeiro}`)?.focus()
      return
    }

    setEnviando(true)
    setErroEnvio('')
    try {
      const perfil = montarPerfil(valores)
      const previsao = await preverRisco(perfil)
      salvarAnalise({ perfil, valores, rotulos: rotulosDoPerfil(campos ?? [], valores), previsao, idioma })
      navegar('resultado')
    } catch (e) {
      setErroEnvio(e instanceof Error ? e.message : t.form.erroEnvio)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <CabecalhoPagina
        voltar={{ rota: 'visao-geral', rotulo: t.form.voltar }}
        titulo={t.form.titulo}
        subtitulo={t.form.subtitulo}
      />

      {/* Etapas */}
      <ol className="mb-6 flex flex-wrap items-center gap-2 sm:gap-3">
        {t.form.secoes.map((secao, i) => (
          <li key={secao.titulo} className="flex shrink-0 items-center gap-2">
            {i > 0 && <span className="h-0.5 w-4 bg-primaria-borda sm:w-10" aria-hidden />}
            <span
              className={cx(
                'grid size-7 place-items-center rounded-full text-[13px] font-semibold text-white',
                preenchidas[i] ? 'bg-risco-baixo' : 'bg-primaria',
              )}
            >
              {preenchidas[i] ? <Check className="size-4" aria-label={t.form.etapaConcluida} /> : i + 1}
            </span>
            <span className="text-sm font-medium">
              <span className="sm:hidden">{secao.curto}</span>
              <span className="hidden sm:inline">{secao.titulo}</span>
            </span>
          </li>
        ))}
      </ol>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Cartao className="p-5 sm:p-7">
          {erroCarregar ? (
            <MensagemErro texto={erroCarregar} onTentarNovamente={carregar} />
          ) : !campos ? (
            <Carregando texto={t.form.carregando} />
          ) : (
            <form onSubmit={enviar} noValidate className="flex flex-col gap-7">
              {t.form.secoes.map((secao, i) => (
                <fieldset
                  key={secao.titulo}
                  className="flex flex-col gap-5 border-b border-borda pb-7 last-of-type:border-0 last-of-type:pb-0"
                >
                  <legend className="mb-5 flex items-center gap-3">
                    <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primaria-clara text-sm font-bold text-primaria-texto">
                      {i + 1}
                    </span>
                    <span>
                      <span className="block text-base font-semibold">{secao.titulo}</span>
                      <span className="block text-[13px] text-suave">{secao.descricao}</span>
                    </span>
                  </legend>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {CAMPOS_POR_SECAO[i].map((nome) => {
                      const campo = porCampo.get(nome)
                      if (!campo) return null
                      const props = {
                        id: `campo-${nome}`,
                        rotulo: campo.rotulo,
                        valor: valores[nome] ?? '',
                        erro: erros[nome] ? t.form.obrigatorio : undefined,
                        onChange: (v: string) => alterar(nome, v),
                      }
                      if (SEGMENTADOS.includes(nome)) {
                        return (
                          <Segmentado
                            key={nome}
                            {...props}
                            opcoes={campo.opcoes.map((o) => ({ valor: String(o.valor), rotulo: o.rotulo }))}
                          />
                        )
                      }
                      return <CampoSelecao key={nome} {...props} opcoes={campo.opcoes} />
                    })}
                  </div>
                </fieldset>
              ))}

              {erroEnvio && <MensagemErro texto={erroEnvio} />}

              <div className="flex flex-col-reverse gap-3 border-t border-borda pt-6 sm:flex-row sm:items-center">
                <p className="flex items-center gap-2 text-xs text-suave sm:flex-1">
                  <Lock className="size-3.5 shrink-0" aria-hidden />
                  {t.form.privacidade}
                </p>
                <Botao type="button" variante="secundario" onClick={() => navegar('visao-geral')}>
                  {t.form.cancelar}
                </Botao>
                <Botao type="submit" carregando={enviando}>
                  {t.form.calcular}
                </Botao>
              </div>
            </form>
          )}
        </Cartao>

        <Cartao className="p-5 sm:p-6 lg:sticky lg:top-8">
          <span className="grid size-10 place-items-center rounded-[10px] bg-primaria-clara text-primaria-texto">
            <Info className="size-5" aria-hidden />
          </span>
          <h2 className="mt-4 text-base font-semibold">{t.form.ajudaTitulo}</h2>
          <p className="mt-2 text-sm leading-relaxed text-texto-2">{t.form.ajudaTexto}</p>
          <ul className="mt-4 flex flex-col gap-2.5 text-sm text-texto-2">
            {t.form.ajudaItens.map((item) => (
              <li key={item} className="flex gap-2.5">
                <Check className="mt-0.5 size-4 shrink-0 text-risco-baixo" aria-hidden />
                {item}
              </li>
            ))}
          </ul>
        </Cartao>
      </div>
    </>
  )
}
