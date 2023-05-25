import pandas as pd
from pymongo import MongoClient

df = pd.read_parquet('C:\\Users\\eduar\\Downloads\\ws_alertario.parquet.gzip') #Mexer aqui para o caminho do arquivo

#print(df1)
#ocorrencia = df1['station'].unique()
#print(ocorrencia)

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