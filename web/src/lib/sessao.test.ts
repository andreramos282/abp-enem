import { describe, expect, it } from 'vitest'
import { encerrarSessao, iniciais, lerSessao, salvarSessao } from './sessao'

describe('sessão', () => {
  it('guarda e encerra a sessão', () => {
    const sessao = { token: 'abc', usuario: { id: 1, nome: 'Ana Souza', email: 'a@b.c', cargo: '' } }
    salvarSessao(sessao)
    expect(lerSessao()).toEqual(sessao)
    encerrarSessao()
    expect(lerSessao()).toBeNull()
  })

  it('gera as iniciais do nome', () => {
    expect(iniciais('Ana Maria Souza')).toBe('AS')
    expect(iniciais('coordenação')).toBe('C')
    expect(iniciais('')).toBe('?')
  })
})
