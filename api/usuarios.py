"""Cadastro de usuários pelo terminal.

Uso:
    python -m api.usuarios criar professora@escola.sp.gov.br "Maria Lima" --cargo "Coordenação"
    python -m api.usuarios listar

A senha é pedida no terminal (não fica no histórico do shell). O banco é o mesmo da API
(DATABASE_URL ou o SQLite em data/edupredict.db).
"""

from __future__ import annotations

import argparse
import getpass

from sqlalchemy import select

from .auth import gerar_hash
from .banco import Banco, Usuario
from .config import carregar_configuracao


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    comandos = parser.add_subparsers(dest="comando", required=True)
    criar = comandos.add_parser("criar", help="Cria um usuário (ou troca a senha, se o e-mail já existir).")
    criar.add_argument("email")
    criar.add_argument("nome")
    criar.add_argument("--cargo", default="")
    comandos.add_parser("listar", help="Lista os usuários.")
    args = parser.parse_args()

    banco = Banco(carregar_configuracao().url_banco)
    banco.criar_tabelas()
    with banco.abrir() as sessao:
        if args.comando == "listar":
            for u in sessao.scalars(select(Usuario).order_by(Usuario.id)):
                print(f"{u.id:>4}  {u.email:<40} {u.nome} ({u.cargo})")
            return
        senha = getpass.getpass("Senha: ")
        if len(senha) < 8 or senha != getpass.getpass("Repita a senha: "):
            raise SystemExit("As senhas não conferem ou têm menos de 8 caracteres.")
        email = args.email.strip().lower()
        usuario = sessao.scalar(select(Usuario).where(Usuario.email == email))
        if usuario is None:
            sessao.add(Usuario(email=email, nome=args.nome, cargo=args.cargo, senha_hash=gerar_hash(senha)))
            print(f"Usuário {email} criado.")
        else:
            usuario.senha_hash = gerar_hash(senha)
            print(f"Senha de {email} atualizada.")
        sessao.commit()


if __name__ == "__main__":
    main()
