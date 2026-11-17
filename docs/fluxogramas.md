# Fluxogramas: análise de dados e base de dados

Os diagramas abaixo são escritos em [Mermaid](https://mermaid.js.org/) e o GitHub desenha sozinho.
Para alterar, edite o texto do bloco `mermaid` (dá para testar em <https://mermaid.live>).

## 1. Fluxo da análise de dados e do modelo

Do arquivo do INEP até o modelo usado pela aplicação. Números da execução registrada em `models/metadados.json`.

```mermaid
flowchart TD
    edicao{"Qual edição do ENEM usar?"}
    descarta["2024/2025 descartado: perfil e notas sem chave"]
    inep[("Microdados ENEM 2023 - 1,7 GB")]

    subgraph prep ["Preparação dos dados (ml/preparar_dados.py)"]
        filtro["Filtro: concluintes, 4 provas, redação válida"]
        pop[("População: 1.008.062 alunos")]
        amostra["Amostra estratificada: região x tipo de escola"]
        parquet[("Amostra: 399.998 alunos (Parquet)")]
    end

    eda["Análise exploratória (ml/eda.py)"]
    edaOut[/"Gráficos e tabelas em docs/eda"/]
    feat["Engenharia de variáveis (ml/features.py)"]

    subgraph model ["Modelagem (ml/treinar.py)"]
        divisao["Divisão 70/10/20 estratificada"]
        alvo{"Média das notas abaixo de 481,0?"}
        risco["Classe 1: em risco"]
        semRisco["Classe 0: fora de risco"]
        treino["GridSearchCV 5 folds: 5 modelos"]
        limiar["Limiar na validação: 0,27"]
        teste["Teste: AUC, F1, viés, teste sem Nordeste"]
    end

    final["Modelo final: MLP (64, 32), AUC 0,760"]
    artefatos[/"models: pipeline.pkl, metadados.json, relatório"/]
    api["API FastAPI"]
    front(["Front-end React"])

    edicao -->|"2024 em diante"| descarta
    edicao -->|"2023"| inep
    inep --> filtro --> pop --> amostra --> parquet
    parquet --> eda --> edaOut
    parquet --> feat --> divisao --> alvo
    alvo -->|"Sim"| risco
    alvo -->|"Não"| semRisco
    risco & semRisco --> treino
    treino --> limiar --> teste --> final --> artefatos --> api --> front

    style prep fill:#C6FAF6,stroke:#5AD8CC
    style model fill:#C2E5FF,stroke:#3DADFF
    style edicao fill:#FFECBD,stroke:#FFC943
    style alvo fill:#FFECBD,stroke:#FFC943
    style descarta fill:#D9D9D9,stroke:#B3B3B3
    style risco fill:#FFCDC2,stroke:#FF7556
    style semRisco fill:#CDF4D3,stroke:#66D575
    style final fill:#CDF4D3,stroke:#66D575
    style api fill:#DCCCFF,stroke:#874FFF
    style front fill:#DCCCFF,stroke:#874FFF
```

Regras que valem em todo o fluxo:

- O corte de 481,0 (quartil inferior) é calculado só no conjunto de ajuste, para não vazar informação do teste.
- As notas nunca entram como entrada do modelo: só formam o alvo.
- Cor/raça e sexo ficam fora do modelo e são usados só na análise de viés.

## 2. Estrutura da base de dados

O projeto não usa banco relacional: a base são arquivos em camadas, e a API lê a camada analítica.

```mermaid
flowchart LR
    subgraph local ["Fora do git (computador / Drive)"]
        bruta[("Bruta: CSV do INEP, 1,7 GB")]
        filtrada[("Filtrada: CSV 112 MB, 1.008.062 linhas")]
    end

    subgraph repo ["No repositório"]
        dicionario["Dicionário: ml/colunas_2023.py"]
        analitica[("Analítica: Parquet 8 MB, 399.998 linhas")]
        modelo[("Modelo: models/")]
    end

    subgraph app ["Aplicação (Docker no Render)"]
        api["API FastAPI"]
        front(["Front-end React"])
    end

    ibge["IBGE: municípios e malhas"]
    mapbox["Mapbox: mapa base"]

    bruta -->|"filtra"| filtrada
    filtrada -->|"amostra"| analitica
    analitica -->|"treina"| modelo
    dicionario -.->|"nomes das colunas"| analitica
    modelo -->|"/api/prever"| api
    analitica -->|"/api/municipios/analytics"| api
    dicionario -->|"/api/opcoes"| api
    api -->|"JSON"| front
    ibge -.-> front
    mapbox -.-> front

    style local fill:#F5F5F5,stroke:#B3B3B3
    style repo fill:#C6FAF6,stroke:#5AD8CC
    style app fill:#DCCCFF,stroke:#874FFF
```

- A API lê do Parquet só as colunas que usa e guarda textos como categorias: cerca de 30 MB em memória, dentro do limite de 512 MB do plano gratuito do Render.
- Os microdados do INEP são anônimos e as análises feitas na tela não são gravadas.
