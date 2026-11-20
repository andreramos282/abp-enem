import { useRef, useState, type ChangeEvent } from 'react'
import { AlertTriangle, Download, FileSpreadsheet, Lock, Upload, Users } from 'lucide-react'
import {
  buscarOpcoes,
  formatarNumero,
  MAX_LOTE,
  preverLote,
  type NivelRisco,
  type Perfil,
  type ResultadoLote,
} from '../lib/api'
import { baixarArquivo, escreverCsv, lerCsv } from '../lib/csv'
import { montarPerfil, type Valores } from '../lib/perfil'
import { usePreferencias } from '../lib/usePreferencias'
import { CabecalhoPagina } from '../components/Layout'
import { AvisoMock, BadgeRisco, Botao, Carregando, Cartao, Kpi, MensagemErro, TituloCartao } from '../components/ui'
import { cx } from '../lib/estilos'

// Colunas da planilha, na ordem do formulário. tipo_escola é deduzido da rede (ver lib/perfil.ts).
const COLUNAS: Array<keyof Perfil> = [
  'renda_familiar',
  'pessoas_residencia',
  'escolaridade_mae',
  'escolaridade_pai',
  'ocupacao_mae',
  'ocupacao_pai',
  'faixa_etaria',
  'sexo',
  'cor_raca',
  'rede_escola',
  'localizacao_escola',
  'uf_escola',
  'computador',
  'internet',
]
const EXEMPLOS = [
  ['aluno-01', 'B', '4', 'C', 'B', 'B', 'C', '2', 'F', '3', '2', '1', 'SP', 'A', 'B'],
  ['aluno-02', 'G', '3', 'F', 'E', 'D', 'D', '2', 'M', '1', '4', '1', 'SP', 'C', 'B'],
]

interface Envio {
  arquivo: string
  resultados: ResultadoLote[]
  modelo: string
}

export function Lote() {
  const { t } = usePreferencias()
  const entrada = useRef<HTMLInputElement>(null)
  const [envio, setEnvio] = useState<Envio | null>(null)
  const [processando, setProcessando] = useState(false)
  const [erro, setErro] = useState('')

  function baixarModelo() {
    baixarArquivo('modelo_analise_lote.csv', escreverCsv(['identificador', ...COLUNAS], EXEMPLOS))
  }

  async function baixarLegenda() {
    try {
      const campos = await buscarOpcoes()
      const linhas = campos
        .filter((c) => COLUNAS.includes(c.campo))
        .flatMap((c) => c.opcoes.map((o) => [c.campo, c.rotulo, o.valor, o.rotulo]))
      baixarArquivo('legenda_codigos.csv', escreverCsv(['coluna', 'pergunta', 'codigo', 'resposta'], linhas))
    } catch (e) {
      setErro(e instanceof Error ? e.message : t.lote.erroArquivo)
    }
  }

  async function enviar(evento: ChangeEvent<HTMLInputElement>) {
    const arquivo = evento.target.files?.[0]
    evento.target.value = ''
    if (!arquivo) return
    setErro('')
    setEnvio(null)

    let linhas: Array<Record<string, string>>
    try {
      linhas = lerCsv(await arquivo.text()).linhas
    } catch {
      setErro(t.lote.erroArquivo)
      return
    }
    if (linhas.length === 0) return setErro(t.lote.vazio)
    if (linhas.length > MAX_LOTE) return setErro(t.lote.excesso(formatarNumero(MAX_LOTE)))

    const alunos = linhas.map((linha) => {
      const valores: Valores = {}
      for (const coluna of COLUNAS) if (linha[coluna] !== undefined) valores[coluna] = linha[coluna]
      const perfil = montarPerfil(valores) as unknown as Record<string, string | number>
      return linha.identificador ? { ...perfil, identificador: linha.identificador } : perfil
    })

    setProcessando(true)
    try {
      const resposta = await preverLote(alunos)
      setEnvio({ arquivo: arquivo.name, ...resposta })
    } catch (e) {
      setErro(e instanceof Error ? e.message : t.lote.erroArquivo)
    } finally {
      setProcessando(false)
    }
  }

  function baixarResultado() {
    if (!envio) return
    baixarArquivo(
      'resultado_analise_lote.csv',
      escreverCsv(
        ['linha', 'identificador', 'probabilidade_risco', 'nivel_risco', 'acompanhamento_recomendado', 'erro'],
        envio.resultados.map((r) => [
          r.linha,
          r.identificador,
          r.probabilidade_risco === null ? '' : formatarNumero(r.probabilidade_risco * 100, 1),
          r.nivel_risco,
          r.acompanhamento_recomendado === null ? '' : r.acompanhamento_recomendado ? t.lote.sim : t.lote.nao,
          r.erro,
        ]),
      ),
    )
  }

  const contagem = (nivel: NivelRisco) => envio?.resultados.filter((r) => r.nivel_risco === nivel).length ?? 0
  const erros = envio?.resultados.filter((r) => r.erro).length ?? 0

  return (
    <>
      <CabecalhoPagina titulo={t.lote.titulo} subtitulo={t.lote.subtitulo} />

      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <Cartao className="flex flex-col gap-4 p-5 sm:p-6">
          <Passo numero={1} titulo={t.lote.passo1} texto={t.lote.passo1Texto} />
          <div className="flex flex-col gap-2 sm:flex-row">
            <Botao variante="secundario" onClick={baixarModelo}>
              <Download className="size-4" aria-hidden />
              {t.lote.baixarModelo}
            </Botao>
            <Botao variante="secundario" onClick={() => void baixarLegenda()}>
              <FileSpreadsheet className="size-4" aria-hidden />
              {t.lote.baixarLegenda}
            </Botao>
          </div>
        </Cartao>
        <Cartao className="flex flex-col gap-4 p-5 sm:p-6">
          <Passo numero={2} titulo={t.lote.passo2} texto={t.lote.passo2Texto(formatarNumero(MAX_LOTE))} />
          <input
            ref={entrada}
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            id="arquivo-lote"
            onChange={(e) => void enviar(e)}
          />
          <Botao onClick={() => entrada.current?.click()} carregando={processando}>
            <Upload className="size-4" aria-hidden />
            {t.lote.escolher}
          </Botao>
          <p className="flex items-start gap-2 text-xs text-suave">
            <Lock className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            {t.lote.privacidade}
          </p>
        </Cartao>
      </div>

      {erro && (
        <div className="mb-6">
          <MensagemErro texto={erro} />
        </div>
      )}
      {processando && <Carregando texto={t.lote.processando} />}

      {envio && (
        <>
          <div className="mb-4">
            <AvisoMock modelo={envio.modelo} />
          </div>
          <div className="mb-6 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
            <Kpi
              titulo={t.visao.kpiAlunos}
              valor={formatarNumero(envio.resultados.length)}
              icone={<Users className="size-4" aria-hidden />}
            />
            <Kpi titulo={t.visao.faixaAlta} valor={formatarNumero(contagem('alto'))} tom="alto" />
            <Kpi titulo={t.visao.faixaMedia} valor={formatarNumero(contagem('medio'))} />
            <Kpi
              titulo={t.lote.totalErros}
              valor={formatarNumero(erros)}
              tom={erros > 0 ? 'alto' : 'neutro'}
              icone={<AlertTriangle className="size-4" aria-hidden />}
            />
          </div>

          <Cartao className="overflow-hidden">
            <div className="p-5 sm:p-6">
              <TituloCartao
                titulo={t.lote.resumo(envio.arquivo, envio.resultados.length)}
                acao={
                  <Botao variante="secundario" onClick={baixarResultado}>
                    <Download className="size-4" aria-hidden />
                    {t.lote.baixarResultado}
                  </Botao>
                }
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px] text-sm">
                <thead className="bg-superficie-2 text-left text-[11px] font-semibold tracking-wider text-fraco">
                  <tr>
                    <th className="px-6 py-2.5 font-semibold">{t.lote.colLinha}</th>
                    <th className="px-4 py-2.5 font-semibold">{t.lote.colIdentificador}</th>
                    <th className="px-4 py-2.5 text-right font-semibold">{t.lote.colRisco}</th>
                    <th className="px-4 py-2.5 font-semibold">{t.lote.colNivel}</th>
                    <th className="px-6 py-2.5 font-semibold">{t.lote.colAcompanhamento}</th>
                  </tr>
                </thead>
                <tbody>
                  {envio.resultados.map((r) => (
                    <tr key={r.linha} className="border-t border-borda align-top">
                      <td className="px-6 py-3 tabular-nums text-suave">{r.linha}</td>
                      <td className="px-4 py-3 font-medium">{r.identificador ?? '—'}</td>
                      {r.erro ? (
                        <td colSpan={3} className="px-4 py-3 text-xs text-risco-alto-texto">
                          <strong>{t.lote.colErro}:</strong> {r.erro}
                        </td>
                      ) : (
                        <>
                          <td className="px-4 py-3 text-right font-semibold tabular-nums">
                            {formatarNumero((r.probabilidade_risco ?? 0) * 100, 1)}%
                          </td>
                          <td className="px-4 py-3">{r.nivel_risco && <BadgeRisco nivel={r.nivel_risco} />}</td>
                          <td
                            className={cx(
                              'px-6 py-3',
                              r.acompanhamento_recomendado ? 'font-semibold text-risco-alto-texto' : 'text-suave',
                            )}
                          >
                            {r.acompanhamento_recomendado === null
                              ? '—'
                              : r.acompanhamento_recomendado
                                ? t.lote.sim
                                : t.lote.nao}
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Cartao>
        </>
      )}
    </>
  )
}

function Passo({ numero, titulo, texto }: { numero: number; titulo: string; texto: string }) {
  return (
    <div className="flex gap-3">
      <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-primaria-clara text-sm font-bold text-primaria-texto">
        {numero}
      </span>
      <span>
        <span className="block text-base font-semibold">{titulo}</span>
        <span className="block text-[13px] text-suave">{texto}</span>
      </span>
    </div>
  )
}
