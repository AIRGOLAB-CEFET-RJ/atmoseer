import s3fs
import numpy as np
import os
import shutil
from datetime import datetime, timedelta
from netCDF4 import Dataset
import sys
import argparse
import tenacity
import concurrent.futures

# Definir limites de coordenadas de interesse
lon_min, lon_max = -43.7, -43
lat_min, lat_max = -23.2, -22.7

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


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(FileNotFoundError),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(5)
)
def safe_ls(fs, path):
    """Função segura para listar arquivos usando tenacity."""
    return fs.ls(path)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(OSError),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(5)
)
def safe_get(fs, remote_path, local_path):
    """Função segura para baixar arquivos usando tenacity."""
    fs.get(remote_path, local_path)


@tenacity.retry(
    retry=tenacity.retry_if_exception_type(Exception),
    wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
    stop=tenacity.stop_after_attempt(5)
)
def safe_filter(file_path):
    """Função que aplica o filtro de coordenadas de forma segura."""
    filter_by_coordinates(file_path)


def download_files_parallel(files):
    """Faz o download dos arquivos em paralelo usando ThreadPoolExecutor."""
    fs = s3fs.S3FileSystem(anon=True)

    def process_file(file):
        """Função para baixar e filtrar arquivos."""
        filename = f"{output_directory}/{file.split('/')[-1]}"

        # Criar diretório antes de baixar o arquivo
        create_directory(os.path.dirname(filename))

        try:
            print(f"Baixando: {file} para {filename}")
            safe_get(fs, file, filename)  # Download com retry usando tenacity
            safe_filter(filename)  # Aplicar filtro após download com retry
        except Exception as e:
            print(f"Erro ao processar o arquivo {file}: {str(e)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_file, files)


def download_files(start_date, end_date):
    """Baixa os arquivos GLM para um intervalo de datas especificado e faz o crop por coordenadas."""
    current_date = start_date
    fs = s3fs.S3FileSystem(anon=True)

    while current_date <= end_date:
        year = current_date.year
        day_of_year = current_date.timetuple().tm_yday  # Dia do ano
        bucket_path = f'noaa-goes16/GLM-L2-LCFA/{year}/{day_of_year:03d}/'

        print(f"Buscando arquivos para {current_date.strftime('%Y-%m-%d')} (dia {day_of_year})")

        # Criar diretório de saída específico para o dia atual dentro do novo diretório
        day_output_directory = os.path.join(output_directory, current_date.strftime('%Y-%m-%d'))
        clear_directory(day_output_directory)

        # Iterar pelas subpastas de cada hora (00 a 23)
        files = []
        for hour in range(24):
            hour_path = bucket_path + f"{hour:02d}/"
            try:
                hourly_files = safe_ls(fs, hour_path)
                files.extend(hourly_files)
            except FileNotFoundError:
                print(f"Hora {hour:02d} não encontrada no bucket. Pulando...")

        print(f"Total de arquivos encontrados para {current_date.strftime('%Y-%m-%d')}: {len(files)}")

        # Fazer o download em paralelo
        if files:
            download_files_parallel(files)

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

    finally:
        if dataset:
            dataset.close()

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