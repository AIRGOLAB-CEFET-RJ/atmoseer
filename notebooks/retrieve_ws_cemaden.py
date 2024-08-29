import datetime as dt
import pandas as pd
import requests
import argparse
import time

def start_data(uf, idestacao, start_date, end_date, output_file, log_file):
    start_datetime = dt.datetime.strptime(start_date, "%Y%m%d%H%M")
    end_datetime = dt.datetime.strptime(end_date, "%Y%m%d%H%M")

    current_datetime = start_datetime
    dataframes = []
    log_data = []
    error_log = []
    start_time = time.time()
    contador = 0

    while current_datetime <= end_datetime:
        try:
            formatted_date = current_datetime.strftime("%d/%m/%Y %H:%M")
            print("Baixando dados para:", formatted_date)
            
            url = f"http://sjc.salvar.cemaden.gov.br/resources/graficos/interativo/getJson2.php?uf={uf}&idestacao={idestacao}&datahoraUltimovalor={formatted_date.replace('/', '/')}"

            response = requests.get(url)
            response.raise_for_status()
            
            clima = response.json()

            if clima:
                df = pd.DataFrame(clima)
                dataframes.append(df)

                log_entry = {
                    "datahoraUltimovalor": formatted_date,
                    "Status": "Sucesso",
                }
                log_data.append(log_entry)
            else:
                log_entry = {
                    "datahoraUltimovalor": formatted_date,
                    "Status": "Erro: Sem dados",
                }
                log_data.append(log_entry)
            contador += 1

        except requests.exceptions.HTTPError as e:
            print(f"Erro HTTP: {e}")
            
            log_entry = {
                "datahoraUltimovalor": formatted_date,
                "Status": f"Erro HTTP: {e}",
            }
            error_log.append(log_entry)
            time.sleep(1800)

        current_datetime += dt.timedelta(hours=1)

    end_time = time.time()
    total_time = end_time - start_time
    
    final_df = pd.concat(dataframes, ignore_index=True)
    final_df.to_csv(output_file, index=False)

    log_df = pd.DataFrame(log_data)
    log_df.to_csv(log_file, index=False)

def argumentos():
    description = "Escolha o Estado, cidade e as datas de início e fim."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-e", "--estado", required=True, help="Estado")
    parser.add_argument("-c", "--idestacao", required=True, help="Cidade")
    parser.add_argument("-start", "--start_date", required=True, help="Data de início no formato AAAA-MM-DD HH:MM:SS")
    parser.add_argument("-end", "--end_date", required=True, help="Data de fim no formato AAAA-MM-DD HH:MM:SS")
    parser.add_argument("-o", "--output_file", required=True, help="Nome do arquivo de saída CSV")
    return parser.parse_args()

if __name__ == "__main__":
    args = argumentos()
    log_file = "log.csv"
    start_data(args.estado, args.idestacao, args.start_date, args.end_date, args.output_file, log_file)
