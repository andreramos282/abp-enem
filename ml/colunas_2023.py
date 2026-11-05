"""Mapeamento das colunas dos microdados do ENEM 2023.

Este é o ÚNICO lugar do projeto que conhece os nomes originais do INEP
(Q001, TP_ESCOLA...). O resto do código usa os nomes com significado
(escolaridade_mae, renda_familiar...). Para usar outro ano (ex.: 2025),
basta criar um arquivo equivalente, como colunas_2025.py.

ATENÇÃO: confira os códigos e rótulos com o dicionário oficial do ENEM 2023
(pasta DICIONÁRIO dos microdados) antes de treinar o modelo.
"""

ANO = 2023
RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# Entradas do modelo: nome no projeto -> coluna nos microdados
# ---------------------------------------------------------------------------
VARIAVEIS = {
    "escolaridade_pai": "Q001",
    "escolaridade_mae": "Q002",
    "ocupacao_pai": "Q003",
    "ocupacao_mae": "Q004",
    "pessoas_residencia": "Q005",
    "renda_familiar": "Q006",
    "computador": "Q024",
    "internet": "Q025",
    "tipo_escola": "TP_ESCOLA",
    "rede_escola": "TP_DEPENDENCIA_ADM_ESC",
    "localizacao_escola": "TP_LOCALIZACAO_ESC",
    "uf_escola": "SG_UF_ESC",
    "faixa_etaria": "TP_FAIXA_ETARIA",
}

# Itens de bens da casa (Q007 a Q023). Viram um único "indice_bens".
BENS = [f"Q{n:03d}" for n in range(7, 24)]

# Usadas só na análise de viés. NUNCA entram como entrada do modelo.
VARIAVEIS_ANALISE_VIES = {"cor_raca": "TP_COR_RACA", "sexo": "TP_SEXO"}

# ---------------------------------------------------------------------------
# Alvo e população
# ---------------------------------------------------------------------------
NOTAS = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]
PRESENCAS = ["TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"]
STATUS_REDACAO = "TP_STATUS_REDACAO"
SITUACAO_CONCLUSAO = "TP_ST_CONCLUSAO"

CONCLUINTE = 2            # TP_ST_CONCLUSAO = 2 -> concluindo o ensino médio no ano
PRESENTE = 1              # TP_PRESENCA_* = 1 -> presente na prova
REDACAO_VALIDA = 1        # TP_STATUS_REDACAO = 1 -> sem problemas
QUANTIL_RISCO = 0.25      # alvo = 1 se a média das 5 notas ficar no quartil inferior

# As notas servem SOMENTE para criar o alvo. Nunca use como entrada do modelo.
COLUNAS_PROIBIDAS_NA_ENTRADA = NOTAS + PRESENCAS + [STATUS_REDACAO]

# ---------------------------------------------------------------------------
# Códigos e rótulos (usados no formulário do front e na API)
# ---------------------------------------------------------------------------
ESCOLARIDADE = {
    "A": "Nunca estudou",
    "B": "Não completou o 5º ano do fundamental",
    "C": "Completou o 5º ano, mas não o 9º ano",
    "D": "Completou o 9º ano, mas não o ensino médio",
    "E": "Completou o ensino médio, mas não a faculdade",
    "F": "Completou a faculdade, mas não a pós-graduação",
    "G": "Completou a pós-graduação",
    "H": "Não sei",
}

OCUPACAO = {
    "A": "Grupo 1 – lavrador, agricultor, pescador e afins",
    "B": "Grupo 2 – diarista, vendedor, porteiro, auxiliar e afins",
    "C": "Grupo 3 – padeiro, motorista, eletricista, pedreiro e afins",
    "D": "Grupo 4 – professor de ensino básico, técnico, policial e afins",
    "E": "Grupo 5 – médico, engenheiro, professor universitário, empresário e afins",
    "F": "Não sei",
}

# Faixas de renda familiar mensal do ENEM 2023 (salário mínimo de R$ 1.320).
RENDA_FAMILIAR = {
    "A": "Nenhuma renda",
    "B": "Até R$ 1.320,00",
    "C": "De R$ 1.320,01 até R$ 1.980,00",
    "D": "De R$ 1.980,01 até R$ 2.640,00",
    "E": "De R$ 2.640,01 até R$ 3.300,00",
    "F": "De R$ 3.300,01 até R$ 3.960,00",
    "G": "De R$ 3.960,01 até R$ 5.280,00",
    "H": "De R$ 5.280,01 até R$ 6.600,00",
    "I": "De R$ 6.600,01 até R$ 7.920,00",
    "J": "De R$ 7.920,01 até R$ 9.240,00",
    "K": "De R$ 9.240,01 até R$ 10.560,00",
    "L": "De R$ 10.560,01 até R$ 11.880,00",
    "M": "De R$ 11.880,01 até R$ 13.200,00",
    "N": "De R$ 13.200,01 até R$ 15.840,00",
    "O": "De R$ 15.840,01 até R$ 19.800,00",
    "P": "De R$ 19.800,01 até R$ 26.400,00",
    "Q": "Acima de R$ 26.400,00",
}

# Valor aproximado (meio da faixa, em R$) para calcular a renda per capita.
RENDA_VALOR_MEDIO = {
    "A": 0, "B": 660, "C": 1650, "D": 2310, "E": 2970, "F": 3630, "G": 4620,
    "H": 5940, "I": 7260, "J": 8580, "K": 9900, "L": 11220, "M": 12540,
    "N": 14520, "O": 17820, "P": 23100, "Q": 30000,
}

COMPUTADOR = {"A": "Não", "B": "Sim, um", "C": "Sim, dois", "D": "Sim, três", "E": "Sim, quatro ou mais"}
INTERNET = {"A": "Não", "B": "Sim"}

TIPO_ESCOLA = {1: "Não respondeu", 2: "Pública", 3: "Privada"}
REDE_ESCOLA = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
LOCALIZACAO_ESCOLA = {1: "Urbana", 2: "Rural"}

FAIXA_ETARIA = {
    1: "Menor de 17 anos", 2: "17 anos", 3: "18 anos", 4: "19 anos", 5: "20 anos",
    6: "21 anos", 7: "22 anos", 8: "23 anos", 9: "24 anos", 10: "25 anos",
    11: "Entre 26 e 30 anos", 12: "Entre 31 e 35 anos", 13: "Entre 36 e 40 anos",
    14: "Entre 41 e 45 anos", 15: "Entre 46 e 50 anos", 16: "Entre 51 e 55 anos",
    17: "Entre 56 e 60 anos", 18: "Entre 61 e 65 anos", 19: "Entre 66 e 70 anos",
    20: "Maior de 70 anos",
}

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

REGIAO_POR_UF = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
}
