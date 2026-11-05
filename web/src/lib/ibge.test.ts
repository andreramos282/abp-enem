import { describe, expect, it } from 'vitest'
import { calcularLimites, filtrarMunicipios, normalizar, type Municipio } from './ibge'

const LISTA: Municipio[] = [
  { id: 1, nome: 'Jacareí', uf: 'SP' },
  { id: 2, nome: 'São José dos Campos', uf: 'SP' },
  { id: 3, nome: 'Jacarezinho', uf: 'PR' },
  { id: 4, nome: 'Bom Jesus do Jacaré', uf: 'MG' },
]

describe('filtrarMunicipios', () => {
  it('ignora acentos e maiúsculas', () => {
    expect(normalizar('JacAREÍ')).toBe('jacarei')
    expect(filtrarMunicipios(LISTA, 'jacarei').map((m) => m.id)).toEqual([1])
  })

  it('mostra primeiro quem começa com o termo', () => {
    expect(filtrarMunicipios(LISTA, 'jacar').map((m) => m.id)).toEqual([1, 3, 4])
  })

  it('exige pelo menos 2 letras', () => {
    expect(filtrarMunicipios(LISTA, 'j')).toEqual([])
  })
})

describe('calcularLimites', () => {
  it('calcula a caixa de um polígono', () => {
    const limites = calcularLimites({
      type: 'Polygon',
      coordinates: [
        [
          [-46, -23],
          [-45.5, -23.4],
          [-45.8, -22.9],
          [-46, -23],
        ],
      ],
    })
    expect(limites).toEqual([
      [-46, -23.4],
      [-45.5, -22.9],
    ])
  })
})
