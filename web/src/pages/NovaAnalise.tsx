import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Check, Info, Lock } from 'lucide-react'
import { buscarOpcoes, preverRisco, type Campo, type Perfil } from '../lib/api'
import { salvarAnalise } from '../lib/armazenamento'
import { navegar } from '../lib/rotas'
import { CabecalhoPagina } from '../components/Layout'
import { Botao, CampoSelecao, Carregando, Cartao, MensagemErro, Segmentado } from '../components/ui'

type Valores = Partial<Record<keyof Perfil, string>>

interface Secao {
  titulo: string
  descricao: string
  campos: Array<keyof Perfil>
}

// tipo_escola não aparece: é derivado da rede (federal/estadual/municipal = pública).
const SECOES: Secao[] = [
  {
    titulo: 'Perfil socioeconômico',
    descricao: 'Renda e contexto familiar do aluno',
    campos: ['renda_familiar', 'pessoas_residencia', 'escolaridade_mae', 'escolaridade_pai', 'ocupacao_mae', 'ocupacao_pai', 'faixa_etaria'],
  },
  {
    titulo: 'Escola',
    descricao: 'Onde o aluno cursa o ensino médio',
    campos: ['rede_escola', 'localizacao_escola', 'uf_escola'],
  },
  {
    titulo: 'Recursos em casa',
    descricao: 'Estrutura de estudo disponível no domicílio',
    campos: ['computador', 'internet'],
  },
]

const CAMPOS_NUMERICOS: Array<keyof Perfil> = [
  'pessoas_residencia',
  'tipo_escola',
  'rede_escola',
  'localizacao_escola',
  'faixa_etaria',
]

const SEGMENTADOS: Array<keyof Perfil> = ['internet', 'localizacao_escola']

function montarPerfil(valores: Valores): Perfil {
  const rede = Number(valores.rede_escola)
  const perfil: Record<string, string | number> = { ...valores, tipo_escola: rede === 4 ? 3 : 2 }
  for (const campo of CAMPOS_NUMERICOS) perfil[campo] = Number(perfil[campo])
  return perfil as unknown as Perfil
}

export function NovaAnalise() {
  const [campos, setCampos] = useState<Campo[] | null>(null)
  const [erroCarregar, setErroCarregar] = useState('')
  const [valores, setValores] = useState<Valores>({})
  const [erros, setErros] = useState<Valores>({})
  const [enviando, setEnviando] = useState(false)
  const [erroEnvio, setErroEnvio] = useState('')

  function carregar() {
    setErroCarregar('')
    buscarOpcoes()
      .then(setCampos)
      .catch((e: unknown) => setErroCarregar(e instanceof Error ? e.message : 'Erro ao carregar o formulário.'))
  }

  useEffect(carregar, [])

  const porCampo = useMemo(() => new Map(campos?.map((c) => [c.campo, c] as const)), [campos])
  const obrigatorios = SECOES.flatMap((s) => s.campos)
  const preenchidas = SECOES.map((s) => s.campos.every((c) => valores[c]))

  function alterar(campo: keyof Perfil, valor: string) {
    setValores((v) => ({ ...v, [campo]: valor }))
    setErros((e) => ({ ...e, [campo]: undefined }))
  }

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    const faltando: Valores = {}
    for (const campo of obrigatorios) if (!valores[campo]) faltando[campo] = 'Preencha este campo.'
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
      const rotulos: Valores = {}
      for (const campo of obrigatorios) {
        const opcao = porCampo.get(campo)?.opcoes.find((o) => String(o.valor) === valores[campo])
        if (opcao) rotulos[campo] = opcao.rotulo
      }
      salvarAnalise({ perfil, rotulos, previsao })
      navegar('resultado')
    } catch (e) {
      setErroEnvio(e instanceof Error ? e.message : 'Erro ao calcular o risco.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <CabecalhoPagina
        voltar={{ rota: 'visao-geral', rotulo: 'Voltar para a visão geral' }}
        titulo="Nova análise de aluno"
        subtitulo="Preencha o perfil para estimar o risco de baixo desempenho no ENEM. Leva menos de 1 minuto."
      />

      {/* Etapas */}
      <ol className="-mx-4 mb-6 flex gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:gap-3 sm:px-0">
        {SECOES.map((secao, i) => (
          <li key={secao.titulo} className="flex shrink-0 items-center gap-2">
            {i > 0 && <span className="h-0.5 w-6 bg-primaria-borda sm:w-10" aria-hidden />}
            <span
              className={
                preenchidas[i]
                  ? 'grid size-7 place-items-center rounded-full bg-risco-baixo text-white'
                  : 'grid size-7 place-items-center rounded-full bg-primaria text-[13px] font-semibold text-white'
              }
            >
              {preenchidas[i] ? <Check className="size-4" aria-label="Concluída" /> : i + 1}
            </span>
            <span className="text-sm font-medium">{secao.titulo}</span>
          </li>
        ))}
      </ol>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Cartao className="p-5 sm:p-7">
          {erroCarregar ? (
            <MensagemErro texto={erroCarregar} onTentarNovamente={carregar} />
          ) : !campos ? (
            <Carregando texto="Carregando formulário…" />
          ) : (
            <form onSubmit={enviar} noValidate className="flex flex-col gap-7">
              {SECOES.map((secao, i) => (
                <fieldset key={secao.titulo} className="flex flex-col gap-5 border-b border-borda pb-7 last-of-type:border-0 last-of-type:pb-0">
                  <legend className="mb-5 flex items-center gap-3">
                    <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primaria-clara text-sm font-bold text-primaria">
                      {i + 1}
                    </span>
                    <span>
                      <span className="block text-base font-semibold">{secao.titulo}</span>
                      <span className="block text-[13px] text-suave">{secao.descricao}</span>
                    </span>
                  </legend>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {secao.campos.map((nome) => {
                      const campo = porCampo.get(nome)
                      if (!campo) return null
                      const props = {
                        id: `campo-${nome}`,
                        rotulo: campo.rotulo,
                        valor: valores[nome] ?? '',
                        erro: erros[nome],
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
                  Os dados são anônimos e usados apenas para a previsão.
                </p>
                <Botao type="button" variante="secundario" onClick={() => navegar('visao-geral')}>
                  Cancelar
                </Botao>
                <Botao type="submit" carregando={enviando}>
                  Calcular risco
                </Botao>
              </div>
            </form>
          )}
        </Cartao>

        <Cartao className="p-5 sm:p-6 lg:sticky lg:top-8">
          <span className="grid size-10 place-items-center rounded-[10px] bg-primaria-clara text-primaria">
            <Info className="size-5" aria-hidden />
          </span>
          <h2 className="mt-4 text-base font-semibold">Como o risco é calculado</h2>
          <p className="mt-2 text-sm leading-relaxed text-texto-2">
            Um modelo de aprendizado de máquina treinado com os microdados do ENEM 2023 compara este perfil com o de
            alunos concluintes e estima a chance de o aluno ficar entre os 25% com menor desempenho.
          </p>
          <ul className="mt-4 flex flex-col gap-2.5 text-sm text-texto-2">
            {[
              'Usa só renda, família, escola e recursos em casa',
              'Nenhuma nota é usada como entrada',
              'Mostra os fatores que mais pesam no resultado',
            ].map((item) => (
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
