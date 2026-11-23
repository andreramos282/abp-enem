import re

import pytest
from playwright.sync_api import expect

from tests.e2e.conftest import entrar

pytestmark = pytest.mark.e2e


def preencher_formulario(pagina) -> None:
    pagina.get_by_role("link", name="Nova análise").first.click()
    for campo in [
        "renda_familiar",
        "pessoas_residencia",
        "escolaridade_mae",
        "escolaridade_pai",
        "ocupacao_mae",
        "ocupacao_pai",
        "faixa_etaria",
        "cor_raca",
        "rede_escola",
        "uf_escola",
        "computador",
    ]:
        pagina.locator(f"#campo-{campo}").select_option(index=2)
    for texto in ["Urbana", "Não"]:
        pagina.locator("button").filter(has_text=re.compile(f"^{texto}$")).first.click()


def test_login_errado_mostra_erro(pagina, site):
    entrar(pagina, site, senha="senha-errada")
    expect(pagina.get_by_text("E-mail ou senha incorretos.")).to_be_visible()


def test_sem_login_qualquer_pagina_leva_ao_login(pagina, site):
    pagina.goto(f"{site}/#/historico")
    expect(pagina.locator("#email")).to_be_visible()


def test_analise_vai_para_o_historico_e_reabre(pagina, site):
    entrar(pagina, site)
    expect(pagina.get_by_role("heading", name="Visão geral")).to_be_visible()

    preencher_formulario(pagina)
    pagina.get_by_role("button", name="Calcular risco").click()
    expect(pagina.get_by_role("heading", name="Resultado da análise")).to_be_visible()
    expect(pagina.get_by_text("de risco")).to_be_visible()

    pagina.get_by_role("link", name="Histórico").first.click()
    linhas = pagina.get_by_role("button", name="Abrir")
    expect(linhas.first).to_be_visible()
    linhas.first.click()
    expect(pagina.get_by_role("heading", name="Resultado da análise")).to_be_visible()

    pagina.reload()  # a sessão continua depois de recarregar
    expect(pagina.get_by_role("heading", name="Resultado da análise")).to_be_visible()

    pagina.get_by_role("button", name="Sair").first.click()
    expect(pagina.locator("#email")).to_be_visible()


def test_formulario_exige_campos(pagina, site):
    entrar(pagina, site)
    pagina.get_by_role("link", name="Nova análise").first.click()
    pagina.get_by_role("button", name="Calcular risco").click()
    expect(pagina.get_by_text("Preencha este campo.").first).to_be_visible()
    expect(pagina.get_by_text("Sobre cor/raça e sexo")).to_be_visible()


def test_analise_em_lote(pagina, site, tmp_path):
    planilha = tmp_path / "turma.csv"
    planilha.write_text(
        "identificador;renda_familiar;pessoas_residencia;escolaridade_mae;escolaridade_pai;ocupacao_mae;"
        "ocupacao_pai;faixa_etaria;sexo;cor_raca;rede_escola;localizacao_escola;uf_escola;computador;internet\n"
        "aluno-01;B;4;C;B;B;C;2;F;3;2;1;SP;A;B\n"
        "aluno-02;B;4;C;B;B;C;2;F;3;2;1;XX;A;B\n",
        encoding="utf-8",
    )
    entrar(pagina, site)
    pagina.get_by_role("link", name="Análise em lote").first.click()
    pagina.set_input_files("#arquivo-lote", planilha)
    expect(pagina.get_by_text("turma.csv · 2 alunos")).to_be_visible()
    expect(pagina.get_by_text("aluno-01")).to_be_visible()
    expect(pagina.get_by_text("uf_escola: valor inválido (XX)")).to_be_visible()


def test_celular_menu_e_sobre(celular, site):
    entrar(celular, site)
    navegacao = celular.get_by_role("navigation", name="Menu principal").last
    expect(navegacao.get_by_role("link", name="Lote")).to_be_visible()
    celular.get_by_role("link", name="Sobre o modelo").click()
    expect(celular.get_by_role("heading", name="Sobre o modelo")).to_be_visible()
    expect(celular.get_by_text("Limitações")).to_be_visible()
    largura = celular.evaluate("document.documentElement.scrollWidth")
    assert largura <= 390, "a página não pode ter rolagem lateral no celular"
