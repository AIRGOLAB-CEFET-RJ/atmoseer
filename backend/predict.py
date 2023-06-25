import torch
import torch.nn as nn
import pandas as pd
from pymongo import MongoClient
import sys
import os

# Obtém o caminho absoluto para o diretório "src"
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
# Adiciona o caminho "src" ao caminho do módulo Python
sys.path.append(src_path)
from train.ordinal_classification_net import OrdinalClassificationNet

pipeline_id = "A652_N"

client = MongoClient('mongodb://localhost:27017/')
db = client['db']

# Escolhendo coleção (será baseada no input do usuário)
#if(sounding):
#collection = db['soundings']
#if(era5):
#collection = db['era5']
#if(cors):
#collection = db['cors']
#if(inmet):
collection = db['inmets']

result = collection.find()
documentosSounding = list(result)

# Criação do dataFrame com dados do servidor
df = pd.DataFrame(documentosSounding)

client.close()

#print(df)

# Ordenar pelos campos datas pelos 6 dados mais recentes.
# Com intuito de organizar e como cada fonte de dados pode 
# ter diferentes nomes para o campo data, foi separado a
# ordenação por coleção.

if collection == db['inmets']:
    df['TIME'] = pd.to_datetime(df['TIME'])
    df = df.sort_values(by='TIME', ascending=False)

if collection == db['cors']:
    df['data'] = pd.to_datetime(df['data'])
    df = df.sort_values(by='data', ascending=False)

if collection == db['era5']:
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time', ascending=False)

if collection == db['sounding']:
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time', ascending=False)

# Criação de um dataFrame com as seis linhas mais recentes para predição

df_predict = df.head(6)
df_predict = df_predict.reset_index(drop=True)
print(df_predict)

# Cada tabela no banco de dados vem com alguns campos indesejáveis, devido a forma que ela 
# foi inserida provavelmente. Para cada tabela usamos o .iloc[:, 1:-1] para:
# ler todas aslinhas ':'
# começar após a primeira coluna '1'
# terminar na penúltima coluna '-1'

if collection == db['inmets']: x = df_predict.iloc[:, 1:-3].values
if collection == db['cors']: x = df_predict.iloc[:, 1:-1].values
if collection == db['era5']: x = df_predict.iloc[:, 1:].values
if collection == db['sounding']: x = df_predict.iloc[:, 1:-1].values

print(f"Shape of one test example: {x.shape}")
print("Model input:")
print(x)

# Definir as variáveis NUM_FEATURES e NUM_CLASSES
NUM_FEATURES = x.shape[1]
NUM_CLASSES = 5

# Cria uma instância do modelo
model = OrdinalClassificationNet(in_channels=NUM_FEATURES, num_classes=NUM_CLASSES)

#Chamada dinâmica do caminho do modelo
caminho_atual = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
model_path = caminho_atual + "\\predictModels" + "\\best_" + pipeline_id + "_OC.pt"
print(model_path)

#model_path = "C:\\Users\\eduar\\Documents\\GitHub\\atmoseerPCS\\backend\\predictModels\\best_A652_N_OC.pt"  #Caminho do modelo
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))

# Colocar modelo no modo de avaliação (inferência).
model.eval()

# Make prediction using the loaded model
with torch.no_grad():
    output = model.predict(x)
    print(output)

