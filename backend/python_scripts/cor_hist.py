#Programa para enviar o histórico do COR para o banco de dados do MongoDB
#Como a série histórica é gigantesca, rodar esse programa apenas uma vez para preencher o banco 

import pandas as pd
from pymongo import MongoClient

#Histórico COR estava contido num arquivo .parquet.gzip. Forma de ler abaixo
df = pd.read_parquet('Caminho do arquivo .parquet.gzip.')

uri = 'mongodb://127.0.0.1:27017'
dbName = 'db'
collectionName = 'cor'

dados = df.to_dict(orient='records')

# Função para salvar os dados no MongoDB
client = MongoClient(uri)
db = client[dbName]
collection = db[collectionName]

# Inserir os dados no MongoDB
collection.insert_many(dados)
print('Dados inseridos com sucesso no MongoDB')

# Fechar a conexão com o MongoDB
client.close()