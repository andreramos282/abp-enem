"""Teste de ponta a ponta com dados SINTÉTICOS no layout do ENEM 2023:
amostragem -> treino -> API com o modelo treinado."""

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from tests.sintetico import salvar
from tests.test_api import PERFIL


@pytest.fixture(scope="module")
def modelo_treinado(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("ml")
    micro = salvar(pasta / "MICRODADOS_ENEM_2023.csv", n=6000)
    amostra = pasta / "amostra.csv"
    subprocess.run(
        [sys.executable, "-m", "ml.preparar_dados", str(micro), "--tamanho", "3000", "--saida", str(amostra)],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ml.treinar",
            "--amostra",
            str(amostra),
            "--saida",
            str(pasta / "models"),
            "--modelos",
            "regressao_logistica",
            "mlp",
            "--amostra-grid",
            "2000",
            "--graficos",
            str(pasta / "graficos"),
        ],
        check=True,
    )
    return pasta / "models", amostra, pasta / "graficos"


def test_treino_gera_arquivos_e_metricas(modelo_treinado):
    pasta, _, graficos = modelo_treinado
    meta = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))
    assert (pasta / "pipeline.pkl").is_file() and (pasta / "relatorio_treino.md").is_file()
    assert meta["modelo"] in {"regressao_logistica", "mlp"}
    assert 0.2 < meta["alvo"]["taxa_risco_treino"] < 0.3
    assert meta["resultados"][meta["modelo"]]["teste"]["auc"] > 0.7
    assert not any(col.startswith("NU_NOTA") for col in meta["entradas"])
    assert {"cor_raca", "sexo"} <= set(meta["entradas"])


def test_testes_iniciais_e_graficos(modelo_treinado):
    pasta, _, graficos = modelo_treinado
    testes = json.loads((pasta / "metadados.json").read_text(encoding="utf-8"))["testes_iniciais"]
    regiao = testes["regiao"]
    assert regiao["regiao"] == "Nordeste"
    assert regiao["n_treino_sem"] < regiao["n_treino_com"]
    for chave in ("com_regiao", "sem_regiao"):
        assert regiao[chave]["na_regiao"]["auc"] is not None
    assert testes["cor_sexo"]["com"]["teste"]["auc"] and testes["cor_sexo"]["sem"]["teste"]["auc"]
    assert len(list(graficos.glob("*.png"))) >= 10


def test_api_com_modelo_real(modelo_treinado, monkeypatch):
    pasta, amostra, _ = modelo_treinado
    monkeypatch.setenv("MODO_PREDITOR", "modelo")
    monkeypatch.setenv("PASTA_MODELO", str(pasta))
    monkeypatch.setenv("CAMINHO_AMOSTRA", str(amostra))
    from api.main import app

    with TestClient(app) as cliente:
        assert cliente.get("/api/health").json()["modelo"] != "mock"

        vulneravel = {**PERFIL, "renda_familiar": "B", "computador": "A", "internet": "A", "escolaridade_mae": "B"}
        favorecido = {
            **PERFIL,
            "renda_familiar": "O",
            "computador": "C",
            "internet": "B",
            "escolaridade_mae": "G",
            "rede_escola": 4,
            "tipo_escola": 3,
        }
        p_v = cliente.post("/api/prever", json=vulneravel).json()
        p_f = cliente.post("/api/prever?idioma=en", json=favorecido).json()
        assert p_v["probabilidade_risco"] > p_f["probabilidade_risco"]
        assert p_v["fatores"], "a previsão deve trazer fatores"
        assert isinstance(p_v["acompanhamento_recomendado"], bool)

        municipio = cliente.post("/api/municipios/analytics", json={"municipio": "Jacareí", "uf": "SP"})
        assert municipio.status_code == 200
        dados = municipio.json()
        assert dados["estatisticas_gerais"]["total_alunos_avaliados"] > 0
        assert dados["comparacao"]["percentual_risco_uf"] > 0
        assert (
            sum(r["total_alunos"] for r in dados["por_rede"]) == dados["estatisticas_gerais"]["total_alunos_avaliados"]
        )

        lote = cliente.post("/api/prever/lote", json={"alunos": [vulneravel, favorecido]}).json()["resultados"]
        assert lote[0]["probabilidade_risco"] == p_v["probabilidade_risco"]
        assert all(isinstance(f["tipo"], str) for f in p_v["fatores"])

        inexistente = cliente.post("/api/municipios/analytics", json={"municipio": "Cidade Inexistente", "uf": "SP"})
        assert inexistente.status_code == 404


def test_teste_temporal_em_outro_ano(modelo_treinado, tmp_path):
    pasta, _, _ = modelo_treinado
    outro_ano = salvar(tmp_path / "MICRODADOS_ENEM_2022.csv", n=3000)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ml.teste_temporal",
            str(outro_ano),
            "--ano",
            "2022",
            "--modelo",
            str(pasta),
            "--graficos",
            str(tmp_path / "graficos"),
        ],
        check=True,
    )
    resultado = json.loads((pasta / "teste_temporal_2022.json").read_text(encoding="utf-8"))
    assert resultado["ano"] == 2022 and resultado["teste"]["auc"] > 0.6
    assert (tmp_path / "graficos" / "12_teste_temporal_2022.png").is_file()
