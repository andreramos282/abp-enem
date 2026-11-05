# Modelos

O modelo final será salvo aqui como `pipeline.pkl`: um único `Pipeline` do scikit-learn com o pré-processamento e o classificador, carregado pela API.

Arquivos `.pkl` não vão para o git. Junto do modelo, registre em `models/metadados.json`: data do treino, versão do scikit-learn, variáveis usadas, corte do quartil e métricas no teste.
