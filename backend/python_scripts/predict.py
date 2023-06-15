import torch
import torch.nn as nn
import pandas as pd
from pymongo import MongoClient

import sys
import os
# Obtém o caminho absoluto para o diretório "src"
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
# Adiciona o caminho "src" ao caminho do módulo Python
sys.path.append(src_path)
from train.ordinal_classification_net import OrdinalClassificationNet

pipeline_id = "A652_N"

client = MongoClient('mongodb://localhost:27017/')
db = client['db']

# Escolhendo coleção
#if(sounding):
#if(era5):
#if(cor):
#if(inmet):
collection = db['soundings']

result = collection.find()
documentosSounding = list(result)

df = pd.DataFrame(documentosSounding)

client.close()

print(df)

df['time'] = pd.to_datetime(df['time'])
df = df.sort_values(by='time', ascending=False)
df_predict = df.head(6)
df_predict = df_predict.reset_index(drop=True)
print(df_predict)

x = df_predict.iloc[:, :-1].values
print(f"Shape of one test example: {x.shape}")
print("Model input:")
print(x)

# Definir as variáveis NUM_FEATURES e NUM_CLASSES
NUM_FEATURES = x.shape[1]
NUM_CLASSES = 5

#Create an instance of the model
model = OrdinalClassificationNet(in_channels=NUM_FEATURES, num_classes=NUM_CLASSES)

# Load the pretrained model weights from the file
model_path = "C:\\Users\\eduar\\Documents\\GitHub\\atmoseerPCS\\backend\\python_scripts\\best_A652_N_OC.pt" #Mudar caminho 
model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))

# Set the model in evaluation (inference) mode.
model.eval()

# Make prediction using the loaded model
with torch.no_grad():
    output = model.predict(x)
    print(output)

