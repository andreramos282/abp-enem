# Front-end – EducaRadar

React + TypeScript + Vite + Tailwind CSS + Mapbox, baseado no protótipo do Figma. Layout responsivo: menu lateral no computador e navegação inferior no celular.

## Telas

| Rota | Tela |
|---|---|
| `#/login` | Login (visual; ainda sem autenticação) |
| `#/visao-geral` | Busca de município (IBGE), mapa, indicadores e escolas por risco |
| `#/nova-analise` | Formulário do perfil do aluno (opções vindas de `GET /api/opcoes`) |
| `#/resultado` | Probabilidade de risco, fatores e intervenções recomendadas |

## Como rodar

Requer Node.js 20+ e Python 3.11+ (para a API).

```bash
cd web
npm install
npm run dev        # sobe o front (5173) e a API (8000) juntos
```

Acesse `http://localhost:5173`. As chamadas para `/api` são encaminhadas para a API.

Para ver o mapa, crie o arquivo `.env` **na raiz do repositório** (copie de `.env.example`) com o seu token público do Mapbox:

```
VITE_MAPBOX_ACCESS_TOKEN=pk....
```

Sem o token, o resto do sistema funciona normalmente e o mapa mostra um aviso.

## Estrutura

```
src/
  App.tsx              rotas
  components/
    Layout.tsx         menu lateral (PC) e navegação inferior (celular)
    MapaMunicipio.tsx  mapa Mapbox com o limite do município
    ui.tsx             botões, cartões, campos, selos de risco
  lib/
    api.ts             tipos e chamadas da API (contrato em docs/api.md)
    ibge.ts            municípios e malhas do IBGE
    rotas.ts           roteamento por hash
    armazenamento.ts   última análise (sessionStorage)
  pages/               Login, VisaoGeral, NovaAnalise, Resultado
```

As cores e tamanhos do Figma estão em `src/index.css` (`@theme`).
