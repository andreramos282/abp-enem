import os

# Os testes da API usam sempre os dados simulados, mesmo que exista um modelo treinado em models/.
# O teste do modelo real (test_ml.py) define as próprias variáveis.
os.environ.setdefault("MODO_PREDITOR", "mock")
