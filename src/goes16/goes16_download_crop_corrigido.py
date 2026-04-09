# Script simplificado baseado no notebook (GOES-16 corrigido)

import s3fs
import xarray as xr
from datetime import datetime
import os

def listar_arquivos(product, year, julian_day, hour):
    fs = s3fs.S3FileSystem(anon=True)
    path = f"noaa-goes16/{product}/{year}/{julian_day:03d}/{hour:02d}/"
    return fs.ls(path)

def extrair_timestamp(nome):
    base = os.path.basename(nome)
    start = base.split("_s")[1].split("_")[0]
    return datetime.strptime(start, "%Y%j%H%M%S")

def encontrar_mais_proximo(arquivos, timestamp):
    return min(arquivos, key=lambda x: abs(extrair_timestamp(x) - timestamp))

def baixar_arquivo(fs, caminho, destino):
    fs.get(caminho, destino)

def processar(start_date, product, channel=None):
    fs = s3fs.S3FileSystem(anon=True)
    dt = datetime.strptime(start_date, "%Y-%m-%d")
    year = dt.year
    julian_day = dt.timetuple().tm_yday

    arquivos = listar_arquivos(product, year, julian_day, 0)

    if channel:
        arquivos = [a for a in arquivos if f"C{channel:02d}" in a]

    alvo = encontrar_mais_proximo(arquivos, dt)

    destino = "/content/temp.nc"
    baixar_arquivo(fs, alvo, destino)

    ds = xr.open_dataset(destino)
    print("time_coverage_start:", ds.attrs.get("time_coverage_start"))

if __name__ == "__main__":
    processar("2024-01-13", "ABI-L2-CMIPF", channel=13)
