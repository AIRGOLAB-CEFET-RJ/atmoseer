import torch
import torch.nn as nn
import pandas as pd
from pymongo import MongoClient
import sys
import os
from dateutil.parser import parse
from metpy.calc import wind_components
from metpy.units import units
import numpy as np

def transform_wind(wind_speed, wind_direction, comp_idx): #Função retirada do src\util.py --> Precisa para tratativas nos dados
    assert(comp_idx == 0 or comp_idx == 1)
    return wind_components(wind_speed * units('m/s'), wind_direction * units.deg)[comp_idx].magnitude

# Obtém o caminho absoluto para o diretório "src"
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
# Adiciona o caminho "src" ao caminho do módulo Python
sys.path.append(src_path)
from train.ordinal_classification_net import OrdinalClassificationNet

# Definir estação (input do usuário)
##### A SER IMPLEMENTADO #####
pipeline_id = "A652_N"

client = MongoClient('mongodb://localhost:27017/')
db = client['db']

# Escolhendo coleção (baseada em input do usuário)
##### A SER IMPLEMENTADO #####
#if(sounding):
collectionSounding = db['soundings']
#if(era5):
collectionERA5 = db['era5']
#if(cors):
collectionCors = db['cors']
#if(inmet):
collectionInmet = db['inmets']


# Documentos com os dados
#ERA5
resultERA5 = collectionERA5.find()
documentosERA5 = list(resultERA5)
#Inmet
resultInmet = collectionInmet.find()
documentosInmet = list(resultInmet)

# Criação do dataFrame com dados do servidor
df_era5 = pd.DataFrame(documentosERA5)
df_inmet = pd.DataFrame(documentosInmet)

client.close()

##### TRATATIVAS NOS DADOS #####
# Correpondência com os campos do modelo e ordenação

if collectionInmet == db['inmets']:
    #Ordenação valores mais recentes
    df_inmet['TIME'] = pd.to_datetime(df_inmet['TIME'])
    df_inmet = df_inmet[df_inmet['COD_ESTACAO'] == 'A652'] # Busca apenas a estação desejada
    df_inmet = df_inmet.dropna(how='any') # Sem valores nulos (lixo no banco de dados)
    df_inmet = df_inmet.sort_values(by='TIME', ascending=False)

    df_inmet = df_inmet.head(6) #Pegar os 6 mais novos
    print(df_inmet)
    # Adição dos campos para o modelo
    df_inmet['wind_u'] = df_inmet.apply(lambda x: transform_wind(x.VEN_VEL, x.VEN_DIR, 0),axis=1)
    df_inmet['wind_v'] = df_inmet.apply(lambda x: transform_wind(x.VEN_VEL, x.VEN_DIR, 1),axis=1)

    #dt = df_inmet.TIME
    #hourfloat = dt.hour + dt.minute/60.0
    df_inmet['hour_sin'] = np.sin(2. * np.pi * 2./24.)
    df_inmet['hour_cos'] = np.cos(2. * np.pi * 2./24.)



#if collectionCors == db['cors']:
#    df['data'] = pd.to_datetime(df['data'])
#    df = df.sort_values(by='data', ascending=False)

if collectionERA5 == db['era5']:
    df_era5['time'] = pd.to_datetime(df_era5['time'])
    df_era5 = df_era5.sort_values(by='time', ascending=False)
    df_era5 = df_era5.dropna(how='any') # Sem valores nulos (lixo no banco de dados)
    
    df_era5 = df_era5.head(6) #Pegar os 6 mais novos
    print(df_era5)

#if collectionSounding == db['sounding']:
#    df['time'] = pd.to_datetime(df['time'])
#    df = df.sort_values(by='time', ascending=False)

# Montar o df do tamanho correto, com as colunas corretas
colunas_inmet = ['TEM_MAX', 'PRE_MAX', 'UMD_MAX', 'wind_u', 'wind_v', 'hour_sin', 'hour_cos', 'CHUVA']
colunas_era5 = ['Geopotential_200', 'Humidity_200', 'Temperature_200', 'WindU_200', 'WindV_200',
                'Geopotential_700', 'Humidity_700', 'Temperature_700', 'WindU_700', 'WindV_700',
                'Geopotential_1000', 'Humidity_1000', 'Temperature_1000', 'WindU_1000', 'WindV_1000']

df_inmet = df_inmet[colunas_inmet]
df_era5 = df_era5[colunas_era5]

df_inmet = df_inmet.reset_index()
df_era5 = df_era5.reset_index()

# Concatenar dataframes
df_model = pd.concat([df_inmet, df_era5], axis=1)

# Criação de um dataFrame com as seis linhas mais recentes para predição
df_predict = df_model.head(6)
df_predict = df_predict.reset_index(drop=True)

# Cada tabela no banco de dados vem com alguns campos indesejáveis, devido a forma que ela 
# foi inserida provavelmente. Para cada tabela usamos o .iloc[:, 1:-1] para:
# ler todas aslinhas ':'
# começar após a primeira coluna '1'
# terminar na penúltima coluna '-1'
df_predict = df_predict.iloc[:, 1:8].join(df_predict.iloc[:, 9:])

x = df_predict.values

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

