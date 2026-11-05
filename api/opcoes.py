"""Opções do formulário "Nova análise", geradas a partir de ml/colunas_2023.py."""

from __future__ import annotations

from ml import colunas_2023 as c

from .schemas import Campo, Opcao, OpcoesFormulario


def _campo(campo: str, rotulo: str, mapa: dict) -> Campo:
    return Campo(
        campo=campo,
        rotulo=rotulo,
        opcoes=[Opcao(valor=valor, rotulo=texto) for valor, texto in mapa.items()],
    )


def montar_opcoes() -> OpcoesFormulario:
    pessoas = {n: f"{n} pessoa" if n == 1 else f"{n} pessoas" for n in range(1, 21)}
    ufs = {uf: uf for uf in c.UFS}
    return OpcoesFormulario(
        campos=[
            _campo("renda_familiar", "Renda familiar mensal", c.RENDA_FAMILIAR),
            _campo("pessoas_residencia", "Pessoas na residência", pessoas),
            _campo("escolaridade_mae", "Escolaridade da mãe", c.ESCOLARIDADE),
            _campo("escolaridade_pai", "Escolaridade do pai", c.ESCOLARIDADE),
            _campo("ocupacao_mae", "Ocupação da mãe", c.OCUPACAO),
            _campo("ocupacao_pai", "Ocupação do pai", c.OCUPACAO),
            _campo("computador", "Computador em casa", c.COMPUTADOR),
            _campo("internet", "Acesso à internet em casa", c.INTERNET),
            _campo("tipo_escola", "Tipo de escola", c.TIPO_ESCOLA),
            _campo("rede_escola", "Rede da escola", c.REDE_ESCOLA),
            _campo("localizacao_escola", "Localização da escola", c.LOCALIZACAO_ESCOLA),
            _campo("uf_escola", "Estado (UF)", ufs),
            _campo("faixa_etaria", "Faixa etária", c.FAIXA_ETARIA),
        ]
    )
