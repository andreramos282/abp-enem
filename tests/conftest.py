import os
import tempfile
from pathlib import Path

# Os testes da API usam sempre os dados simulados, mesmo que exista um modelo treinado em models/.
# O teste do modelo real (test_ml.py) define as próprias variáveis.
os.environ.setdefault("MODO_PREDITOR", "mock")

# Banco SQLite temporário e usuário fixo para os testes (nunca usa o banco de desenvolvimento).
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()) / 'teste.db'}"
os.environ["JWT_SECRET"] = "segredo-dos-testes-com-pelo-menos-32-caracteres"
os.environ["ADMIN_EMAIL"] = "teste@edupredict.dev"
os.environ["ADMIN_SENHA"] = "senha-de-teste"
