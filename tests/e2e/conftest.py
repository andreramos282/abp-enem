"""Testes de ponta a ponta: sobe a API servindo o site compilado (web/dist) e usa um navegador de verdade.

Rodar:
    cd web && npm run build && cd ..
    pip install playwright && python -m playwright install chromium
    pytest -m e2e
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
EMAIL, SENHA = "e2e@edupredict.dev", "senha-do-teste-e2e"


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    if not (RAIZ / "web" / "dist" / "index.html").is_file():
        pytest.skip("Site não compilado: rode npm run build em web/.")
    pytest.importorskip("playwright")
    porta = _porta_livre()
    env = {
        **os.environ,
        "MODO_PREDITOR": "mock",
        "DATABASE_URL": f"sqlite:///{tmp_path_factory.mktemp('banco') / 'e2e.db'}",
        "JWT_SECRET": "segredo-dos-testes-e2e-com-pelo-menos-32-caracteres",
        "ADMIN_EMAIL": EMAIL,
        "ADMIN_SENHA": SENHA,
        "ADMIN_NOME": "Teste Automático",
    }
    processo = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--port", str(porta)],
        cwd=RAIZ,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{porta}"
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{url}/api/health", timeout=1)
            break
        except OSError:
            time.sleep(0.5)
    else:
        processo.terminate()
        pytest.fail("A API não subiu.")
    yield url
    processo.terminate()
    processo.wait(timeout=10)


@pytest.fixture(scope="session")
def navegador():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def pagina(navegador, site):
    contexto = navegador.new_context(locale="pt-BR", viewport={"width": 1280, "height": 900})
    pagina = contexto.new_page()
    pagina.set_default_timeout(15_000)
    yield pagina
    contexto.close()


@pytest.fixture
def celular(navegador, site):
    contexto = navegador.new_context(locale="pt-BR", viewport={"width": 390, "height": 844}, is_mobile=True)
    pagina = contexto.new_page()
    pagina.set_default_timeout(15_000)
    yield pagina
    contexto.close()


def entrar(pagina, site: str, email: str = EMAIL, senha: str = SENHA) -> None:
    pagina.goto(site)
    pagina.fill("#email", email)
    pagina.fill("#senha", senha)
    pagina.get_by_role("button", name="Entrar").click()
