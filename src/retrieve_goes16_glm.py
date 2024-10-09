import s3fs
import numpy as np
import os
import shutil
from datetime import datetime, timedelta
from netCDF4 import Dataset
import sys
import argparse

# Definir limites de coordenadas de interesse
lon_min, lon_max = -45.05290312102409, -42.35676996062447
lat_min, lat_max = -23.801876626302175, -21.699774257353113

# Diretório de saída
output_directory = "data/goes16/glm_files/"

def create_directory(directory):
    """Cria o diretório se ele não existir."""
    os.makedirs(directory, exist_ok=True)
    print(f"Diretório {directory} criado (ou já existia).")


def clear_directory(directory):
    """Limpa o diretório de saída e cria novamente."""
    if os.path.exists(directory):
        shutil.rmtree(directory)
        print(f"Diretório {directory} limpo.")
    create_directory(directory)

def download_files(start_date, end_date):
    """Baixa os arquivos GLM para um intervalo de datas especificado e faz o crop por coordenadas."""
    current_date = start_date
    fs = s3fs.S3FileSystem(anon=True)

    while current_date <= end_date:
        year = current_date.year
        day_of_year = current_date.timetuple().tm_yday 
        bucket_path = f'noaa-goes16/GLM-L2-LCFA/{year}/{day_of_year:03d}/'

        print(f"Buscando arquivos para {current_date.strftime('%Y-%m-%d')} (dia {day_of_year})")
        
        # Diretório de saída específico para o dia atual
        day_output_directory = os.path.join(output_directory, current_date.strftime('%Y-%m-%d'))
        clear_directory(day_output_directory)

        # Iterar pelas subpastas de cada hora (00 a 23)
        files = []
        for hour in range(24):
            hour_path = bucket_path + f"{hour:02d}/"  
            try:
                hourly_files = fs.ls(hour_path)
                files.extend(hourly_files)  
            except FileNotFoundError:
                print(f"Hora {hour:02d} não encontrada no bucket. Pulando...")

        print(f"Total de arquivos encontrados para {current_date.strftime('%Y-%m-%d')}: {len(files)}")

        for file in files:
            file_name = file.split('/')[-1]
            local_file_path = os.path.join(day_output_directory, file_name)
            print(f"Baixando: {file} para {local_file_path}")
            fs.get(file, local_file_path)
            filter_by_coordinates(local_file_path)

        print(f"Download e filtro para {current_date.strftime('%Y-%m-%d')} concluídos.")
        current_date += timedelta(days=1)

def filter_by_coordinates(file_path):
    """Filtra os eventos GLM de um arquivo NetCDF com base nas coordenadas fornecidas."""
    dataset = None
    try:
        dataset = Dataset(file_path, 'r')

        longitudes = dataset.variables['flash_lon'][:]
        latitudes = dataset.variables['flash_lat'][:]

        print(f"Longitude mínima: {longitudes.min()}, máxima: {longitudes.max()}")
        print(f"Latitude mínima: {latitudes.min()}, máxima: {latitudes.max()}")

        mask = (
            (longitudes >= lon_min) & (longitudes <= lon_max) &
            (latitudes >= lat_min) & (latitudes <= lat_max)
        )

        if np.sum(mask) == 0:
            print(f"Nenhum evento dentro do filtro encontrado em {file_path}. Removendo arquivo.")
            dataset.close()
            os.remove(file_path)
        else:
            print(f"Eventos dentro do filtro encontrados no arquivo {file_path}.")
        
    except Exception as e:
        print(f"Erro ao filtrar o arquivo {file_path}: {e}")


def main(argv):
    parser = argparse.ArgumentParser(description='Download e filtro de arquivos GLM por coordenadas.')
    parser.add_argument('-b', '--start_date', required=True, help='Data de início no formato YYYY-MM-DD')
    parser.add_argument('-e', '--end_date', required=True, help='Data de término no formato YYYY-MM-DD')
    args = parser.parse_args(argv[1:])

    # Converter as strings de data para objetos datetime
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    # Verificar se a data de início é menor ou igual à data de término
    assert start_date <= end_date, "A data de início deve ser anterior ou igual à data de término."

    # Iniciar o processo de download e filtro
    download_files(start_date, end_date)

if __name__ == "__main__":
    main(sys.argv)
