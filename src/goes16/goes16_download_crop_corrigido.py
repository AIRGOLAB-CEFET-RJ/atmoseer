
import argparse
import logging
import os
import time
from datetime import datetime, timedelta

import boto3
import netCDF4 as nc
from botocore import UNSIGNED
from botocore.client import Config

s3 = boto3.client(
    "s3",
    config=Config(signature_version=UNSIGNED, max_pool_connections=20)
)

BUCKET = "noaa-goes16"
cropped_dict = {}

def build_extent():
    return [-75.0, -35.0, -30.0, 5.0]

def get_julian_day(date):
    return date.strftime("%j")

def list_hour_files(product, date, hour):
    year = date.strftime("%Y")
    julian_day = get_julian_day(date)
    prefix = f"{product}/{year}/{julian_day}/{hour:02d}/"

    logging.info("Listando arquivos em %s", prefix)
    resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    files = [obj["Key"] for obj in resp.get("Contents", [])]
    logging.info("Hora %02d: %d arquivo(s) encontrado(s)", hour, len(files))
    return prefix, files

def filter_files_for_product(files, product, channel=None):
    filtered = [f for f in files if product in os.path.basename(f)]

    if product == "ABI-L2-CMIPF" and channel is not None:
        token = f"M6C{int(channel):02d}"
        filtered = [f for f in filtered if token in os.path.basename(f)]

    filtered = sorted(filtered)
    logging.info("Após filtro: %d arquivo(s)", len(filtered))
    return filtered

def crop_full_disk(full_disk_filename, spatial_resolution, variable_names, extent):
    cropped_content_dict = {}

    for var in variable_names:
        try:
            with nc.Dataset(full_disk_filename, "r") as ds:
                data = ds.variables[var][:].copy()

                dtime = ds.time_coverage_start
                dtime = datetime.strptime(dtime, "%Y-%m-%dT%H:%M:%S.%fZ")
                key = dtime.strftime("%Y_%m_%d_%H_%M")

                cropped_content_dict[f"{var}_{key}"] = data
                logging.info("Variável %s lida com shape %s", var, data.shape)

        except Exception as e:
            logging.warning("Erro ao ler variável %s: %s", var, e)

    return cropped_content_dict

def download_and_crop_full_disk(remote_path, local_path, spatial_resolution, variable_names):
    global cropped_dict

    try:
        logging.info("Baixando: %s", os.path.basename(remote_path))
        s3.download_file(BUCKET, remote_path, local_path)
        logging.info("Download concluído: %s", os.path.basename(remote_path))

        cropped_content = crop_full_disk(
            full_disk_filename=local_path,
            spatial_resolution=spatial_resolution,
            variable_names=variable_names,
            extent=build_extent(),
        )

        cropped_dict.update(cropped_content)
        logging.info("Conteúdo acumulado: %d variável(is)", len(cropped_dict))

    except Exception as e:
        logging.exception("Erro ao baixar/processar %s: %s", os.path.basename(remote_path), e)

    finally:
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

def process_goes16_data_for_hour(product, date, hour, channel, download_dir, spatial_resolution, variable_names):
    prefix, files = list_hour_files(product, date, hour)
    selected_files = filter_files_for_product(files, product, channel)

    if not selected_files:
        logging.info("Hora %02d: nenhum arquivo selecionado", hour)
        return

    # diagnóstico: processa só 1 arquivo por hora
    selected_files = selected_files[:1]

    for remote_path in selected_files:
        local_path = os.path.join(download_dir, os.path.basename(remote_path))
        download_and_crop_full_disk(
            remote_path,
            local_path,
            spatial_resolution,
            variable_names,
        )

def process_goes16_data_for_day(date, product, channel, download_dir, spatial_resolution, variable_names):
    # diagnóstico: limita a 2 horas para não travar no teste
    for hour in range(2):
        logging.info("Processando hora %02d", hour)
        process_goes16_data_for_hour(
            product,
            date,
            hour,
            channel,
            download_dir,
            spatial_resolution,
            variable_names,
        )

def save_to_netcdf(cropped_dict, filename):
    if not cropped_dict:
        logging.warning("Nenhum dado para salvar em %s", filename)
        return

    with nc.Dataset(filename, "w", format="NETCDF4") as dataset:
        first = True

        for key, data_array in cropped_dict.items():
            if first:
                dataset.createDimension("x", data_array.shape[0])
                dataset.createDimension("y", data_array.shape[1])
                first = False

            var = dataset.createVariable(key, "f4", ("x", "y"))
            var[:] = data_array

    logging.info("Arquivo salvo em %s", filename)

def process_goes16_data_for_period(
    start_date,
    end_date,
    ignored_months,
    product,
    channel,
    download_dir,
    crop_dir,
    spatial_resolution,
    variable_names,
):
    global cropped_dict

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(crop_dir, exist_ok=True)

    current_date = start_date
    while current_date <= end_date:
        day = current_date.strftime("%Y_%m_%d")
        filename = f"{product}_C{channel}_{day}.nc"
        output = os.path.join(crop_dir, filename)

        logging.info("Processando %s", day)
        cropped_dict = {}

        process_goes16_data_for_day(
            current_date,
            product,
            channel,
            download_dir,
            spatial_resolution,
            variable_names,
        )

        save_to_netcdf(cropped_dict, output)
        current_date += timedelta(days=1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--start_date", required=True)
    parser.add_argument("--end_date", required=True)
    parser.add_argument("--product", default="ABI-L2-CMIPF")
    parser.add_argument("--channel", type=int, default=13)
    parser.add_argument("--download_dir", default="./downloads")
    parser.add_argument("--crop_dir", required=True)
    parser.add_argument("--spatial_resolution", type=float, required=True)
    parser.add_argument("--vars", nargs="+", required=True)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    start = time.time()

    process_goes16_data_for_period(
        start_date,
        end_date,
        [],
        args.product,
        args.channel,
        args.download_dir,
        args.crop_dir,
        args.spatial_resolution,
        args.vars,
    )

    print(f"Tempo total: {(time.time() - start)/60:.2f} minutos")
