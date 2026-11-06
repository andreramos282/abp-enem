# Dados

Os arquivos de dados **não vão para o git** (são grandes demais). Cada pessoa baixa na própria máquina.

## Microdados do ENEM 2023

1. Baixe em: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem
2. Extraia o `.zip` e copie `DADOS/MICRODADOS_ENEM_2023.csv` para esta pasta.
3. O arquivo usa separador `;` e codificação `latin-1`.
4. Antes de usar, confira no dicionário (pasta `DICIONÁRIO`) se os códigos batem com `ml/colunas_2023.py`.

## Amostra do projeto

A amostra usada por todo o grupo já está aqui: `amostra_enem_2023.parquet` (399.998 concluintes, 8 MB, gerada com `python -m ml.preparar_dados`). Ela é usada pela API no painel do município e pelo treino.
