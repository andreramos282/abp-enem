import { describe, expect, it } from 'vitest'
import type { Campo } from './api'
import { montarPerfil, rotulosDoPerfil } from './perfil'

const VALORES = {
  escolaridade_pai: 'C',
  escolaridade_mae: 'D',
  ocupacao_pai: 'C',
  ocupacao_mae: 'B',
  pessoas_residencia: '4',
  renda_familiar: 'C',
  computador: 'A',
  internet: 'B',
  rede_escola: '2',
  localizacao_escola: '1',
  uf_escola: 'SP',
  faixa_etaria: '2',
}

describe('montarPerfil', () => {
  it('converte os campos numéricos', () => {
    const perfil = montarPerfil(VALORES)
    expect(perfil.pessoas_residencia).toBe(4)
    expect(perfil.rede_escola).toBe(2)
    expect(perfil.faixa_etaria).toBe(2)
    expect(perfil.renda_familiar).toBe('C')
  })

  it('deduz o tipo de escola pela rede', () => {
    expect(montarPerfil({ ...VALORES, rede_escola: '2' }).tipo_escola).toBe(2)
    expect(montarPerfil({ ...VALORES, rede_escola: '1' }).tipo_escola).toBe(2)
    expect(montarPerfil({ ...VALORES, rede_escola: '4' }).tipo_escola).toBe(3)
  })
})

describe('rotulosDoPerfil', () => {
  it('troca os códigos pelos rótulos das opções', () => {
    const campos: Campo[] = [
      {
        campo: 'internet',
        rotulo: 'Internet',
        opcoes: [
          { valor: 'A', rotulo: 'Não' },
          { valor: 'B', rotulo: 'Sim' },
        ],
      },
      { campo: 'rede_escola', rotulo: 'Rede', opcoes: [{ valor: 2, rotulo: 'Estadual' }] },
    ]
    expect(rotulosDoPerfil(campos, VALORES)).toEqual({ internet: 'Sim', rede_escola: 'Estadual' })
  })
})
