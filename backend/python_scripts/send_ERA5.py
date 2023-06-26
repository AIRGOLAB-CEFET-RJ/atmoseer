#  Programa para enviar o ERA5 para o banco de dados do MongoDB

#   Como a série histórica é gigantesca, pelo menos para outros anos,
# rodar esse programa apenas uma vez para preencher o banco.

#   ERA5 está sendo reanilizado como modelo númerico de predição, seus 
# dados estão atrasados 4 dias e são comumente usados para pesquisas de
# momentos passados

import cdsapi
from netCDF4 import Dataset
from pymongo import MongoClient
import xarray as xr
import logging
import pandas as pd

# Configurações da conexão com o MongoDB
uri = 'mongodb://127.0.0.1:27017'
dbName = 'db'
collectionName = 'era5'

# Função para salvar os dados no MongoDB
def saveDataToMongoDB(data):
    client = MongoClient(uri)
    db = client[dbName]
    collection = db[collectionName]

    # Inserir os dados no MongoDB
    collection.insert_many(data)
    print('Dados inseridos com sucesso no MongoDB')

    # Fechar a conexão com o MongoDB
    client.close()

# Fazer solicitação à API do CDS e salvar os dados no MongoDB
def retrieveData():
    c = cdsapi.Client()

    # Fazer a solicitação à API do CDS
    c.retrieve(
        "reanalysis-era5-pressure-levels",
    {
        "product_type": "reanalysis",
        "format": "netcdf",
        "variable": [
            "geopotential",
            "relative_humidity",
            "temperature",
            "u_component_of_wind",
            "v_component_of_wind",
        ],
        "pressure_level": [
            '200', '700', '1000'
        ],
        "year": [
            '2023',
        ],
        "month": [
            "01"
        ],
        "day": [
            "01",
            "02",
            "03",
            "04",
            "05",
            "06",
            "07",
            "08",
            "09",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
            "23",
            "24",
            "25",
            "26",
            "27",
            "28",
            "29",
            "30",
            "31",
        ],
        "time": [
            "00:00",
            "01:00",
            "02:00",
            "03:00",
            "04:00",
            "05:00",
            "06:00",
            "07:00",
            "08:00",
            "09:00",
            "10:00",
            "11:00",
            "12:00",
            "13:00",
            "14:00",
            "15:00",
            "16:00",
            "17:00",
            "18:00",
            "19:00",
            "20:00",
            "21:00",
            "22:00",
            "23:00",
        ],
        "area": [
            -22,
            -44,
            -23,
            -42,
        ],
    },
    "file.nc",
    )

    # Ler o arquivo .nc
    # Escollher o caminho do arquivo
    # dataset = Dataset('file.nc', 'r')
    ds = xr.open_dataset("backend\python_scripts\RJ_2022_2022.nc") 
    logging.info(f"Size.0: {ds.sizes['time']}")

    # Get the minimum and maximum values of the 'time' coordinate
    # time_min = ds.coords['time'].min().item()
    # time_max = ds.coords['time'].max().item()
    # logging.info(f"Range of timestamps in the original NWP data: [{ds.time.min()}, {ds.time.max()}]")
    # logging.info(f"Range of timestamps in the original NWP data: [{time_min}, {time_max}]")
    time_min = ds.time.min().values
    time_max = ds.time.max().values
    logging.info(f"Range of timestamps in the original NWP data: [{time_min}, {time_max}]")

    ds = ds.sel(time=slice(time_min, time_max))
    logging.info(f"Size.1: {ds.sizes['time']}")

    era5_data_at_200hPa = ds.sel(level=200, longitude= -22.9925, latitude=-43.233056, method="nearest")
    logging.info(f"Size.2: {era5_data_at_200hPa.sizes['time']}")

    era5_data_at_700hPa = ds.sel(level=700, longitude= -22.9925 , latitude=-43.233056, method="nearest")
    logging.info(f"Size.3: {era5_data_at_700hPa.sizes['time']}")

    era5_data_at_1000hPa = ds.sel(level=1000, longitude= -22.9925, latitude=-43.233056, method="nearest")
    logging.info(f"Size.4: {era5_data_at_1000hPa.sizes['time']}")

    logging.info(">>><<<")
    logging.info(type(era5_data_at_1000hPa.time))
    logging.info("-1-")
    logging.info(era5_data_at_200hPa.time.values)
    logging.info("-2-")
    logging.info(era5_data_at_200hPa.z.values)
    logging.info("-3-")
    logging.info(era5_data_at_700hPa.z.values.shape)
    logging.info("-4-")
    logging.info(era5_data_at_700hPa.time.values)
    logging.info("-5-")
    logging.info(era5_data_at_700hPa.z.values)
    logging.info("-6-")
    logging.info(era5_data_at_700hPa.z.values.shape)
    logging.info(">>><<<")

    df_NWP_ERA5 = pd.DataFrame( #Criação do dataframe com os valores do modelo númerico ERA5
        {
            "time": era5_data_at_1000hPa.time.values,
            
            "Geopotential_200": era5_data_at_200hPa.z,
            "Humidity_200": era5_data_at_200hPa.r,
            "Temperature_200": era5_data_at_200hPa.t,
            "WindU_200": era5_data_at_200hPa.u,
            "WindV_200": era5_data_at_200hPa.v,

            "Geopotential_700": era5_data_at_700hPa.z,
            "Humidity_700": era5_data_at_700hPa.r,
            "Temperature_700": era5_data_at_700hPa.t,
            "WindU_700": era5_data_at_700hPa.u,
            "WindV_700": era5_data_at_700hPa.v,

            "Geopotential_1000": era5_data_at_1000hPa.z,
            "Humidity_1000": era5_data_at_1000hPa.r,
            "Temperature_1000": era5_data_at_1000hPa.t,
            "WindU_1000": era5_data_at_1000hPa.u,
            "WindV_1000": era5_data_at_1000hPa.v
        }
    )

    # Salvar os dados no MongoDB
    saveDataToMongoDB(df_NWP_ERA5.to_dict(orient='records'))

    # Fechar o arquivo .nc
    ds.close()

# Executar a função para obter os dados e salvá-los no MongoDB
retrieveData()

