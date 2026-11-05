"""Textos da API em português (padrão) e inglês.

Os rótulos em português ficam em ml/colunas_2023.py (seguem o dicionário do INEP).
Aqui ficam os rótulos em inglês e os textos gerados pela API.
"""

from __future__ import annotations

from typing import Literal

from ml import colunas_2023 as c

Idioma = Literal["pt", "en"]

ROTULOS_CAMPOS: dict[Idioma, dict[str, str]] = {
    "pt": {
        "renda_familiar": "Renda familiar mensal",
        "pessoas_residencia": "Pessoas na residência",
        "escolaridade_mae": "Escolaridade da mãe",
        "escolaridade_pai": "Escolaridade do pai",
        "ocupacao_mae": "Ocupação da mãe",
        "ocupacao_pai": "Ocupação do pai",
        "computador": "Computador em casa",
        "internet": "Acesso à internet em casa",
        "tipo_escola": "Tipo de escola",
        "rede_escola": "Rede da escola",
        "localizacao_escola": "Localização da escola",
        "uf_escola": "Estado (UF)",
        "faixa_etaria": "Faixa etária",
    },
    "en": {
        "renda_familiar": "Monthly family income",
        "pessoas_residencia": "People in the household",
        "escolaridade_mae": "Mother's education",
        "escolaridade_pai": "Father's education",
        "ocupacao_mae": "Mother's occupation",
        "ocupacao_pai": "Father's occupation",
        "computador": "Computer at home",
        "internet": "Internet access at home",
        "tipo_escola": "School type",
        "rede_escola": "School network",
        "localizacao_escola": "School location",
        "uf_escola": "State (UF)",
        "faixa_etaria": "Age group",
    },
}

_ESCOLARIDADE_EN = {
    "A": "Never attended school",
    "B": "Did not complete 5th grade",
    "C": "Completed 5th grade, but not 9th grade",
    "D": "Completed 9th grade, but not high school",
    "E": "Completed high school, but not college",
    "F": "Completed college, but not graduate school",
    "G": "Completed graduate school",
    "H": "Don't know",
}

_OCUPACAO_EN = {
    "A": "Group 1 – farmer, fisher and similar",
    "B": "Group 2 – cleaner, salesperson, doorman, assistant and similar",
    "C": "Group 3 – baker, driver, electrician, bricklayer and similar",
    "D": "Group 4 – schoolteacher, technician, police officer and similar",
    "E": "Group 5 – doctor, engineer, professor, business owner and similar",
    "F": "Don't know",
}


def _renda_en() -> dict[str, str]:
    # Mesmas faixas do ENEM 2023, com a formatação de moeda em inglês.
    limites = [1320, 1980, 2640, 3300, 3960, 5280, 6600, 7920, 9240, 10560, 11880, 13200, 15840, 19800, 26400]
    rotulos = {"A": "No income", "B": "Up to R$ 1,320.00"}
    for codigo, minimo, maximo in zip("CDEFGHIJKLMNOP", limites, limites[1:]):
        rotulos[codigo] = f"R$ {minimo + 0.01:,.2f} to R$ {maximo:,.2f}"
    rotulos["Q"] = "Above R$ 26,400.00"
    return rotulos


_FAIXA_ETARIA_EN = {
    1: "Under 17", **{n: f"{n + 15} years old" for n in range(2, 11)},
    11: "26 to 30", 12: "31 to 35", 13: "36 to 40", 14: "41 to 45", 15: "46 to 50",
    16: "51 to 55", 17: "56 to 60", 18: "61 to 65", 19: "66 to 70", 20: "Over 70",
}

OPCOES: dict[Idioma, dict[str, dict]] = {
    "pt": {
        "renda_familiar": c.RENDA_FAMILIAR,
        "escolaridade": c.ESCOLARIDADE,
        "ocupacao": c.OCUPACAO,
        "computador": c.COMPUTADOR,
        "internet": c.INTERNET,
        "tipo_escola": c.TIPO_ESCOLA,
        "rede_escola": c.REDE_ESCOLA,
        "localizacao_escola": c.LOCALIZACAO_ESCOLA,
        "faixa_etaria": c.FAIXA_ETARIA,
        "pessoas": {n: f"{n} pessoa" if n == 1 else f"{n} pessoas" for n in range(1, 21)},
    },
    "en": {
        "renda_familiar": _renda_en(),
        "escolaridade": _ESCOLARIDADE_EN,
        "ocupacao": _OCUPACAO_EN,
        "computador": {"A": "No", "B": "Yes, one", "C": "Yes, two", "D": "Yes, three", "E": "Yes, four or more"},
        "internet": {"A": "No", "B": "Yes"},
        "tipo_escola": {1: "No answer", 2: "Public", 3: "Private"},
        "rede_escola": {1: "Federal", 2: "State", 3: "Municipal", 4: "Private"},
        "localizacao_escola": {1: "Urban", 2: "Rural"},
        "faixa_etaria": _FAIXA_ETARIA_EN,
        "pessoas": {n: f"{n} person" if n == 1 else f"{n} people" for n in range(1, 21)},
    },
}

# Frases dos fatores da previsão. {valor} recebe o rótulo da resposta (em minúsculas quando indicado).
FATORES: dict[Idioma, dict[str, str]] = {
    "pt": {
        "renda_per_capita": "Renda per capita de aproximadamente R$ {valor}",
        "escolaridade_mae": "Escolaridade da mãe: {valor}",
        "escolaridade_pai": "Escolaridade do pai: {valor}",
        "sem_computador": "Não possui computador em casa",
        "com_computador": "Possui computador em casa",
        "sem_internet": "Sem acesso à internet em casa",
        "com_internet": "Possui acesso à internet em casa",
        "rede_escola": "Rede da escola: {valor}",
        "localizacao_escola": "Escola em área {valor}",
        "faixa_etaria": "Faixa etária: {valor}",
        "ocupacao_mae": "Ocupação da mãe: {valor}",
        "ocupacao_pai": "Ocupação do pai: {valor}",
        "regiao": "Escola na região {valor}",
        "bens": "Bens e conforto no domicílio",
    },
    "en": {
        "renda_per_capita": "Per capita income of about R$ {valor}",
        "escolaridade_mae": "Mother's education: {valor}",
        "escolaridade_pai": "Father's education: {valor}",
        "sem_computador": "No computer at home",
        "com_computador": "Has a computer at home",
        "sem_internet": "No internet access at home",
        "com_internet": "Has internet access at home",
        "rede_escola": "School network: {valor}",
        "localizacao_escola": "School in a {valor} area",
        "faixa_etaria": "Age group: {valor}",
        "ocupacao_mae": "Mother's occupation: {valor}",
        "ocupacao_pai": "Father's occupation: {valor}",
        "regiao": "School in the {valor} region",
        "bens": "Household goods and comfort",
    },
}


REGIOES: dict[Idioma, dict[str, str]] = {
    "pt": {r: r for r in ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]},
    "en": {"Norte": "North", "Nordeste": "Northeast", "Centro-Oeste": "Central-West", "Sudeste": "Southeast", "Sul": "South"},
}


def formatar_reais(valor: float, idioma: Idioma) -> str:
    texto = f"{valor:,.0f}"
    return texto.replace(",", ".") if idioma == "pt" else texto
