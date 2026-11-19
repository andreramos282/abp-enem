from fastapi.testclient import TestClient

from api.auth import conferir_senha, criar_token, gerar_hash, ler_token
from api.main import app
from tests.test_api import PERFIL

LOGIN = {"email": "teste@edupredict.dev", "senha": "senha-de-teste"}


def entrar(cliente: TestClient) -> dict[str, str]:
    resposta = cliente.post("/api/auth/login", json=LOGIN)
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['token']}"}


def test_hash_de_senha():
    guardado = gerar_hash("abc12345")
    assert guardado.startswith("scrypt$") and "abc12345" not in guardado
    assert conferir_senha("abc12345", guardado)
    assert not conferir_senha("errada", guardado)
    assert not conferir_senha("abc12345", "formato-invalido")


def test_token_vencido_ou_de_outro_segredo():
    a, b = "a" * 32, "b" * 32
    assert ler_token(criar_token(7, a, 1), a) == 7
    assert ler_token(criar_token(7, a, 1), b) is None
    assert ler_token(criar_token(7, a, -1), a) is None


def test_login_e_usuario_atual():
    with TestClient(app) as c:
        assert c.post("/api/auth/login", json={**LOGIN, "senha": "errada"}).status_code == 401
        assert c.post("/api/auth/login", json={**LOGIN, "email": "TESTE@edupredict.dev "}).status_code == 200
        cabecalho = entrar(c)
        assert c.get("/api/auth/eu", headers=cabecalho).json()["email"] == LOGIN["email"]
        assert c.get("/api/auth/eu").status_code == 401
        assert c.get("/api/auth/eu", headers={"Authorization": "Bearer invalido"}).status_code == 401


def test_previsao_com_login_vai_para_o_historico():
    with TestClient(app) as c:
        assert c.get("/api/historico").status_code == 401
        cabecalho = entrar(c)
        antes = len(c.get("/api/historico", headers=cabecalho).json())

        c.post("/api/prever", json=PERFIL)  # sem login: não salva
        c.post("/api/prever?salvar=false", json=PERFIL, headers=cabecalho)  # só recalcula
        previsao = c.post("/api/prever", json={**PERFIL, "uf_escola": "BA"}, headers=cabecalho).json()

        historico = c.get("/api/historico", headers=cabecalho).json()
        assert len(historico) == antes + 1
        assert historico[0]["perfil"]["uf_escola"] == "BA"
        assert historico[0]["previsao"]["probabilidade_risco"] == previsao["probabilidade_risco"]

        analise_id = historico[0]["id"]
        assert c.delete(f"/api/historico/{analise_id}").status_code == 401
        assert c.delete(f"/api/historico/{analise_id}", headers=cabecalho).status_code == 204
        assert c.delete(f"/api/historico/{analise_id}", headers=cabecalho).status_code == 404
