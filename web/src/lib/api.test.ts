import { afterEach, describe, expect, it } from 'vitest'
import { formatarNumero, nivelDaEscola } from './api'
import { definirIdiomaAtual } from './idioma-atual'

afterEach(() => definirIdiomaAtual('pt'))

describe('formatarNumero', () => {
  it('usa vírgula em português e ponto em inglês', () => {
    definirIdiomaAtual('pt')
    expect(formatarNumero(1234.5, 1)).toBe('1.234,5')
    definirIdiomaAtual('en')
    expect(formatarNumero(1234.5, 1)).toBe('1,234.5')
  })
})

describe('nivelDaEscola', () => {
  it('converte o status da API no nível de risco', () => {
    expect(nivelDaEscola('ALTO_RISCO')).toBe('alto')
    expect(nivelDaEscola('MEDIO_RISCO')).toBe('medio')
    expect(nivelDaEscola('BAIXO_RISCO')).toBe('baixo')
  })
})
