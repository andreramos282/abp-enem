# Contrato da API

Base em desenvolvimento: `http://127.0.0.1:8000` · Documentação interativa: `/docs`

> Enquanto `USAR_MOCK=true`, as respostas são **simuladas** (campo `"modelo": "mock"`).
> O formato é o definitivo: quando o modelo real entrar, só os valores mudam.

Os códigos (`"C"`, `2`...) seguem o dicionário dos microdados do ENEM 2023.
O front não deve fixar esses valores no código: busque-os em `GET /api/opcoes`.

**Idioma:** `GET /api/opcoes` e `POST /api/prever` aceitam `?idioma=pt` (padrão) ou `?idioma=en`.
Só os textos mudam (rótulos e descrições dos fatores); códigos e números são os mesmos nos dois idiomas.

---

## `GET /api/health`
```json
{ "status": "ok", "modelo": "mock" }
```

## `GET /api/opcoes?idioma=pt`
Lista os campos do formulário "Nova análise" com suas opções.
```json
{
  "campos": [
    {
      "campo": "renda_familiar",
      "rotulo": "Renda familiar mensal",
      "opcoes": [
        { "valor": "A", "rotulo": "Nenhuma renda" },
        { "valor": "B", "rotulo": "Até R$ 1.320,00" }
      ]
    }
  ]
}
```

## `POST /api/prever?idioma=pt`
Estima o risco de um aluno ficar no **quartil inferior** de desempenho no ENEM.
**Nenhuma nota é enviada.** Campos extras são rejeitados (`422`).

Requisição:
```json
{
  "escolaridade_pai": "C",
  "escolaridade_mae": "D",
  "ocupacao_pai": "C",
  "ocupacao_mae": "B",
  "pessoas_residencia": 4,
  "renda_familiar": "C",
  "computador": "A",
  "internet": "B",
  "tipo_escola": 2,
  "rede_escola": 2,
  "localizacao_escola": 1,
  "uf_escola": "SP",
  "faixa_etaria": 2,
  "bens": { "Q008": "B", "Q010": "A" }
}
```
`bens` é opcional (itens Q007 a Q023).

Resposta:
```json
{
  "probabilidade_risco": 0.5444,
  "nivel_risco": "alto",
  "fatores": [
    { "variavel": "computador", "descricao": "Não possui computador em casa", "impacto": 11.2 },
    { "variavel": "internet", "descricao": "Possui acesso à internet em casa", "impacto": -3.7 }
  ],
  "modelo": "mock"
}
```
- `nivel_risco`: `alto` (≥ 50%), `medio` (≥ 25%), `baixo` (< 25%).
- `impacto`: pontos percentuais. Positivo aumenta o risco; negativo reduz.

## `POST /api/municipios/analytics`
Mesmo formato do protótipo do mapa (EduPredict AI).

Requisição:
```json
{ "municipio": "Jacareí", "uf": "SP" }
```
Resposta:
```json
{
  "municipio": "Jacareí",
  "uf": "SP",
  "estatisticas_gerais": {
    "total_alunos_avaliados": 433,
    "total_escolas_unicas": 12,
    "media_geral": 546.07,
    "percentual_risco_municipio": 38.67
  },
  "escolas": [
    {
      "co_escola": 35012345,
      "total_alunos_escola": 41,
      "media_escola": 498.2,
      "percentual_risco_escola": 61.0,
      "status_alerta": "ALTO_RISCO"
    }
  ],
  "modelo": "mock"
}
```

## Erros
| Código | Quando |
|---|---|
| `422` | Campo faltando, valor fora das opções, UF inválida, campo extra (ex.: uma nota) ou idioma diferente de `pt`/`en` |
