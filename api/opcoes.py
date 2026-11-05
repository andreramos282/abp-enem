"""Opções do formulário "Nova análise" em português ou inglês."""

from __future__ import annotations

from ml import colunas_2023 as c

from .schemas import Campo, Opcao, OpcoesFormulario
from .traducoes import OPCOES, ROTULOS_CAMPOS, Idioma


def montar_opcoes(idioma: Idioma = "pt") -> OpcoesFormulario:
    rotulos = ROTULOS_CAMPOS[idioma]
    opcoes = OPCOES[idioma]
    mapas: dict[str, dict] = {
        "renda_familiar": opcoes["renda_familiar"],
        "pessoas_residencia": opcoes["pessoas"],
        "escolaridade_mae": opcoes["escolaridade"],
        "escolaridade_pai": opcoes["escolaridade"],
        "ocupacao_mae": opcoes["ocupacao"],
        "ocupacao_pai": opcoes["ocupacao"],
        "computador": opcoes["computador"],
        "internet": opcoes["internet"],
        "tipo_escola": opcoes["tipo_escola"],
        "rede_escola": opcoes["rede_escola"],
        "localizacao_escola": opcoes["localizacao_escola"],
        "uf_escola": {uf: uf for uf in c.UFS},
        "faixa_etaria": opcoes["faixa_etaria"],
    }
    return OpcoesFormulario(
        campos=[
            Campo(
                campo=campo,
                rotulo=rotulos[campo],
                opcoes=[Opcao(valor=valor, rotulo=texto) for valor, texto in mapa.items()],
            )
            for campo, mapa in mapas.items()
        ]
    )
