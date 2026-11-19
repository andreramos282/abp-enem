import { describe, expect, it } from 'vitest'
import { escreverCsv, lerCsv } from './csv'

describe('lerCsv', () => {
  it('lê ponto e vírgula, aspas e linhas vazias', () => {
    const { cabecalho, linhas } = lerCsv('\uFEFFIdentificador;uf_escola\r\n"Silva; Ana";SP\r\n\r\nB2;  RJ \r\n')
    expect(cabecalho).toEqual(['identificador', 'uf_escola'])
    expect(linhas).toEqual([
      { identificador: 'Silva; Ana', uf_escola: 'SP' },
      { identificador: 'B2', uf_escola: 'RJ' },
    ])
  })

  it('detecta vírgula e ignora células vazias', () => {
    expect(lerCsv('a,b\n1,\n').linhas).toEqual([{ a: '1' }])
  })
})

describe('escreverCsv', () => {
  it('escapa separador e aspas e volta igual na leitura', () => {
    const csv = escreverCsv(['nome', 'obs'], [['Ana "A"', 'x;y']])
    expect(lerCsv(csv).linhas).toEqual([{ nome: 'Ana "A"', obs: 'x;y' }])
  })
})
