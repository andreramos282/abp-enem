// Leitura e escrita de CSV para a análise em lote (sem bibliotecas externas).

export interface TabelaCsv {
  cabecalho: string[]
  linhas: Array<Record<string, string>>
}

// Aceita ";" (padrão do Excel em português) ou ",", campos entre aspas e quebras de linha do Windows.
export function lerCsv(texto: string): TabelaCsv {
  const limpo = texto.replace(/^\uFEFF/, '')
  const primeira = limpo.split(/\r?\n/, 1)[0] ?? ''
  const separador = (primeira.match(/;/g)?.length ?? 0) >= (primeira.match(/,/g)?.length ?? 0) ? ';' : ','

  const registros: string[][] = []
  let campo = ''
  let registro: string[] = []
  let aspas = false
  for (let i = 0; i < limpo.length; i++) {
    const c = limpo[i]
    if (aspas) {
      if (c === '"' && limpo[i + 1] === '"') {
        campo += '"'
        i++
      } else if (c === '"') aspas = false
      else campo += c
    } else if (c === '"') aspas = true
    else if (c === separador) {
      registro.push(campo)
      campo = ''
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && limpo[i + 1] === '\n') i++
      registro.push(campo)
      registros.push(registro)
      registro = []
      campo = ''
    } else campo += c
  }
  if (campo || registro.length) {
    registro.push(campo)
    registros.push(registro)
  }

  const naoVazios = registros.filter((r) => r.some((v) => v.trim() !== ''))
  const cabecalho = (naoVazios[0] ?? []).map((c) => c.trim().toLowerCase())
  const linhas = naoVazios.slice(1).map((valores) => {
    const linha: Record<string, string> = {}
    cabecalho.forEach((coluna, i) => {
      const valor = (valores[i] ?? '').trim()
      if (coluna && valor !== '') linha[coluna] = valor
    })
    return linha
  })
  return { cabecalho, linhas }
}

function celula(valor: unknown): string {
  const texto = valor === null || valor === undefined ? '' : String(valor)
  return /[;"\n\r]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto
}

// Gera CSV com ";" e BOM, para abrir certo no Excel em português.
export function escreverCsv(cabecalho: string[], linhas: unknown[][]): string {
  return '\uFEFF' + [cabecalho, ...linhas].map((l) => l.map(celula).join(';')).join('\r\n') + '\r\n'
}

export function baixarArquivo(nome: string, conteudo: string, tipo = 'text/csv;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }))
  const link = document.createElement('a')
  link.href = url
  link.download = nome
  link.click()
  URL.revokeObjectURL(url)
}
