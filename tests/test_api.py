from fastapi.testclient import TestClient

from api.main import app

PERFIL = {
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
}


def cliente() -> TestClient:
    return TestClient(app)


def test_health():
    with cliente() as c:
        resposta = c.get("/api/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_opcoes_tem_todos_os_campos_do_perfil():
    with cliente() as c:
        campos = {campo["campo"] for campo in c.get("/api/opcoes").json()["campos"]}
    assert campos == set(PERFIL)


def test_prever_retorna_formato_do_contrato():
    with cliente() as c:
        resposta = c.post("/api/prever", json=PERFIL)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert 0 <= corpo["probabilidade_risco"] <= 1
    assert corpo["nivel_risco"] in {"alto", "medio", "baixo"}
    assert corpo["fatores"] and {"variavel", "descricao", "impacto"} <= set(corpo["fatores"][0])


def test_prever_e_deterministico():
    with cliente() as c:
        a = c.post("/api/prever", json=PERFIL).json()
        b = c.post("/api/prever", json=PERFIL).json()
    assert a == b


def test_perfil_mais_vulneravel_tem_mais_risco():
    vulneravel = {**PERFIL, "renda_familiar": "B", "computador": "A", "internet": "A", "escolaridade_mae": "B"}
    favorecido = {**PERFIL, "renda_familiar": "O", "computador": "C", "internet": "B",
                  "escolaridade_mae": "G", "rede_escola": 4, "tipo_escola": 3}
    with cliente() as c:
        risco_v = c.post("/api/prever", json=vulneravel).json()["probabilidade_risco"]
        risco_f = c.post("/api/prever", json=favorecido).json()["probabilidade_risco"]
    assert risco_v > risco_f


def test_prever_rejeita_notas_na_entrada():
    with cliente() as c:
        resposta = c.post("/api/prever", json={**PERFIL, "NU_NOTA_MT": 600})
    assert resposta.status_code == 422


def test_prever_rejeita_uf_invalida():
    with cliente() as c:
        resposta = c.post("/api/prever", json={**PERFIL, "uf_escola": "XX"})
    assert resposta.status_code == 422


def test_municipio_analytics():
    with cliente() as c:
        resposta = c.post("/api/municipios/analytics", json={"municipio": "Jacareí", "uf": "sp"})
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["uf"] == "SP"
    assert corpo["estatisticas_gerais"]["total_escolas_unicas"] == len(corpo["escolas"])


def test_opcoes_em_ingles():
    with cliente() as c:
        campos = {campo["campo"]: campo for campo in c.get("/api/opcoes?idioma=en").json()["campos"]}
    assert campos["renda_familiar"]["rotulo"] == "Monthly family income"
    assert campos["internet"]["opcoes"] == [{"valor": "A", "rotulo": "No"}, {"valor": "B", "rotulo": "Yes"}]


def test_prever_em_ingles_mantem_numeros():
    with cliente() as c:
        pt = c.post("/api/prever", json=PERFIL).json()
        en = c.post("/api/prever?idioma=en", json=PERFIL).json()
    assert pt["probabilidade_risco"] == en["probabilidade_risco"]
    assert [f["variavel"] for f in pt["fatores"]] == [f["variavel"] for f in en["fatores"]]
    assert any(f["descricao"] == "No computer at home" for f in en["fatores"])


def test_idioma_invalido():
    with cliente() as c:
        assert c.get("/api/opcoes?idioma=es").status_code == 422
