import type { Campo, Perfil } from './api'

export type Valores = Partial<Record<keyof Perfil, string>>

const CAMPOS_NUMERICOS: Array<keyof Perfil> = [
  'pessoas_residencia',
  'tipo_escola',
  'rede_escola',
  'localizacao_escola',
  'faixa_etaria',
]

// Converte os valores do formulário (texto) no perfil enviado à API.
// tipo_escola é derivado da rede: federal/estadual/municipal = pública (2), privada = 3.
export function montarPerfil(valores: Valores): Perfil {
  const rede = Number(valores.rede_escola)
  const perfil: Record<string, string | number> = { ...valores, tipo_escola: rede === 4 ? 3 : 2 }
  for (const campo of CAMPOS_NUMERICOS) perfil[campo] = Number(perfil[campo])
  return perfil as unknown as Perfil
}

// Rótulos legíveis das respostas escolhidas, no idioma das opções recebidas.
export function rotulosDoPerfil(campos: Campo[], valores: Valores): Valores {
  const rotulos: Valores = {}
  for (const campo of campos) {
    const opcao = campo.opcoes.find((o) => String(o.valor) === valores[campo.campo])
    if (opcao) rotulos[campo.campo] = opcao.rotulo
  }
  return rotulos
}
