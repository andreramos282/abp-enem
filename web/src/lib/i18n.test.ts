import { describe, expect, it } from 'vitest'
import { TEXTOS } from './i18n'

// Lista todas as chaves de um objeto de textos (ex.: "visao.titulo").
function chaves(objeto: object, prefixo = ''): string[] {
  return Object.entries(objeto).flatMap(([chave, valor]) => {
    const caminho = prefixo ? `${prefixo}.${chave}` : chave
    return valor && typeof valor === 'object' && !Array.isArray(valor) ? chaves(valor, caminho) : [caminho]
  })
}

describe('traduções', () => {
  it('português e inglês têm as mesmas chaves', () => {
    expect(chaves(TEXTOS.en).sort()).toEqual(chaves(TEXTOS.pt).sort())
  })

  it('nenhum texto está vazio', () => {
    for (const idioma of ['pt', 'en'] as const) {
      for (const caminho of chaves(TEXTOS[idioma])) {
        const valor = caminho.split('.').reduce<unknown>((o, k) => (o as Record<string, unknown>)[k], TEXTOS[idioma])
        if (typeof valor === 'string') expect(valor.trim(), `${idioma}: ${caminho}`).not.toBe('')
      }
    }
  })

  it('as etapas do formulário existem nos dois idiomas', () => {
    expect(TEXTOS.pt.form.secoes).toHaveLength(3)
    expect(TEXTOS.en.form.secoes).toHaveLength(3)
  })
})
