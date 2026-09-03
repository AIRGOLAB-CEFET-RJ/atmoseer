import pandas as pd
import sys
import requests
from datetime import datetime, timedelta
from config import globals
import os
import time

# Variáveis globais para armazenar token e sua validade
_auth_token = None
_token_expiry = None

def get_auth_token(username, password):
    """
    Obtém token de autenticação OAuth da API da ANA.
    Token tem validade de 15 minutos.
    
    Args:
        username: CPF ou CNPJ cadastrado
        password: Senha fornecida pela ANA
    
    Returns:
        Token de autenticação
    """
    global _auth_token, _token_expiry
    
    # Verificar se já temos um token válido
    if _auth_token and _token_expiry and datetime.now() < _token_expiry:
        return _auth_token
    
    print("Obtendo token de autenticação OAuth...")
    
    # Endpoint de autenticação OAuth
    auth_url = f"{globals.ANA_API_BASE_URL}/EstacoesTelemetricas/OAUth/v1"
    
    # Headers conforme documentação
    headers = {
        'identificador': username,
        'senha': password
    }
    
    try:
        response = requests.get(auth_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Token pode estar em 'tokenautenticacao' ou em 'items.tokenautenticacao'
            token = None
            if 'tokenautenticacao' in data:
                token = data['tokenautenticacao']
            elif 'items' in data and 'tokenautenticacao' in data['items']:
                token = data['items']['tokenautenticacao']
            
            if token:
                _auth_token = token
                # Token válido por 15 minutos, vamos renovar 1 minuto antes
                _token_expiry = datetime.now() + timedelta(minutes=14)
                print(f"OK - Token obtido com sucesso! Valido ate {_token_expiry.strftime('%H:%M:%S')}")
                return _auth_token
            else:
                print(f"Erro: Resposta não contém 'tokenautenticacao'")
                print(f"Resposta: {data}")
                return None
        else:
            print(f"Erro na autenticação (HTTP {response.status_code})")
            print(f"Resposta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição de autenticação: {e}")
        return None

def get_station_data(station_id, start_date, end_date, username, password, data_type=3):
    """
    Recupera dados de uma estação da ANA usando a API REST HidroWebService.
    
    Args:
        station_id: Código da estação (ex: '2243028')
        start_date: Data inicial no formato 'YYYY-MM-DD'
        end_date: Data final no formato 'YYYY-MM-DD'
        username: CPF ou CNPJ para autenticação
        password: Senha da API
        data_type: Tipo de dado (1=Vazão, 2=Chuva, 3=Chuva e Vazão)
    
    Returns:
        DataFrame com os dados da estação
    """
    # Obter token de autenticação
    token = get_auth_token(username, password)
    if not token:
        print("Erro: Não foi possível obter token de autenticação")
        return pd.DataFrame()
    
    # Headers com token de autenticação - tentar formato Bearer (padrão OAuth)
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    # DataFrames para armazenar os dados
    df_final = pd.DataFrame()
    
    # Buscar dados de CHUVA (data_type 2 ou 3)
    if data_type in [2, 3]:
        print("  > Buscando dados de precipitacao (chuva)...")
        url_chuva = f"{globals.ANA_API_BASE_URL}/EstacoesTelemetricas/HidroSerieChuva/v1"
        params_chuva = {
            'Código da Estação': int(station_id),  # Nome EXATO do Swagger
            'Tipo Filtro Data': 'DATA_LEITURA',
            'Data Inicial (yyyy-MM-dd)': start_date,
            'Data Final (yyyy-MM-dd)': end_date,
            'Horário Inicial (00:00:00)': '00:00:00',
            'Horário Final (23:59:59)': '23:59:59'
        }
        
        try:
            response = requests.get(url_chuva, params=params_chuva, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and isinstance(data['items'], list) and len(data['items']) > 0:
                    df_chuva = pd.DataFrame(data['items'])
                    print(f"  OK - {len(df_chuva)} registros de chuva obtidos")
                    df_final = df_chuva
                else:
                    print("  AVISO - Nenhum dado de chuva encontrado")
            else:
                print(f"  ERRO - HTTP {response.status_code} ao buscar chuva")
        except Exception as e:
            print(f"  ERRO - ao buscar chuva: {e}")
    
    # Buscar dados de VAZÃO (data_type 1 ou 3)
    if data_type in [1, 3]:
        print("  > Buscando dados de vazao...")
        url_vazao = f"{globals.ANA_API_BASE_URL}/EstacoesTelemetricas/HidroSerieVazao/v1"
        params_vazao = {
            'Código da Estação': int(station_id),  # Nome EXATO do Swagger
            'Tipo Filtro Data': 'DATA_LEITURA',
            'Data Inicial (yyyy-MM-dd)': start_date,
            'Data Final (yyyy-MM-dd)': end_date,
            'Horário Inicial (00:00:00)': '00:00:00',
            'Horário Final (23:59:59)': '23:59:59'
        }
        
        try:
            response = requests.get(url_vazao, params=params_vazao, headers=headers, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and isinstance(data['items'], list) and len(data['items']) > 0:
                    df_vazao = pd.DataFrame(data['items'])
                    print(f"  OK - {len(df_vazao)} registros de vazao obtidos")
                    
                    # Mesclar com dados de chuva se existirem
                    if not df_final.empty and 'Data' in df_final.columns and 'Data' in df_vazao.columns:
                        df_final = pd.merge(df_final, df_vazao, on='Data', how='outer')
                    elif df_final.empty:
                        df_final = df_vazao
                else:
                    print("  AVISO - Nenhum dado de vazao encontrado")
            else:
                print(f"  ERRO - HTTP {response.status_code} ao buscar vazao")
        except Exception as e:
            print(f"  ERRO - ao buscar vazao: {e}")
    
    return df_final

def retrieve_from_station(station_id, beginning_year, end_year, username, password, data_type=3):
    """
    Recupera dados de uma estação da ANA para um período de anos.
    
    Args:
        station_id: Código da estação (ex: '2243028')
        beginning_year: Ano inicial
        end_year: Ano final
        username: CPF ou CNPJ para autenticação
        password: Senha da API
        data_type: Tipo de dado (1=Vazão, 2=Chuva, 3=Ambos)
    """
    
    current_date = datetime.now()
    current_year = current_date.year
    end_year = min(end_year, current_year)
    
    years = list(range(beginning_year, end_year + 1))
    df_observations_for_all_years = None
    
    print(f"\n{'='*80}")
    print(f"Baixando observações da estação hidrológica {station_id}...")
    print(f"{'='*80}\n")
    
    # Criar diretório se não existir
    os.makedirs(globals.WS_ANA_DATA_DIR, exist_ok=True)
    
    for year in years:
        print(f"Baixando observações do ano {year}...")
        
        # Define as datas de início e fim
        start_date = f"{year}-01-01"
        
        if year == end_year:
            datetime_str = str(end_year) + '-12-31'
            last_date_of_the_end_year = datetime.strptime(datetime_str, '%Y-%m-%d')
            end_date_obj = min(last_date_of_the_end_year, current_date)
            end_date = end_date_obj.strftime("%Y-%m-%d")
        else:
            end_date = f"{year}-12-31"
        
        print(f"Período: {start_date} até {end_date}")
        
        # Fazer requisição
        df_observations_for_a_year = get_station_data(
            station_id, 
            start_date, 
            end_date,
            username,
            password,
            data_type
        )
        
        if not df_observations_for_a_year.empty:
            print(f"OK - Recebidos {len(df_observations_for_a_year)} registros para {year}")
            
            if df_observations_for_all_years is None:
                df_observations_for_all_years = df_observations_for_a_year
            else:
                df_observations_for_all_years = pd.concat(
                    [df_observations_for_all_years, df_observations_for_a_year],
                    ignore_index=True
                )
        else:
            print(f"AVISO - Nenhum dado retornado para o ano {year}")
        
        # Pequena pausa para não sobrecarregar a API
        time.sleep(1)
    
    # Salvar dados
    if df_observations_for_all_years is not None and not df_observations_for_all_years.empty:
        filename = os.path.join(globals.WS_ANA_DATA_DIR, f"{station_id}.parquet")
        print(f"\n{'='*80}")
        print(f"Pronto! Salvando conteúdo baixado em '{filename}'.")
        print(f"Total de registros: {len(df_observations_for_all_years)}")
        print(f"{'='*80}\n")
        df_observations_for_all_years.to_parquet(filename, index=False)
        
        # Mostrar preview dos dados
        print("Preview dos dados:")
        print(df_observations_for_all_years.head())
        print(f"\nColunas disponiveis: {list(df_observations_for_all_years.columns)}")
    else:
        print(f"\nAVISO - Nenhum dado foi coletado para a estacao {station_id}")

def retrieve_data(station_id, initial_year, final_year, username, password, data_type=3):
    """
    Recupera dados de uma ou todas as estações configuradas.
    
    Args:
        station_id: ID da estação ou "all" para todas
        initial_year: Ano inicial
        final_year: Ano final
        username: CPF ou CNPJ para autenticação
        password: Senha da API
        data_type: Tipo de dado (1=Vazão, 2=Chuva, 3=Ambos)
    """
    if station_id == "all":
        # Baixar dados de todas as estações configuradas (exceto 'all')
        stations_to_download = [s for s in globals.ANA_STATION_IDS if s != 'all']
        print(f"\nBaixando dados de {len(stations_to_download)} estações...")
        print(f"Período: {initial_year} a {final_year}")
        print(f"Tipo de dados: {data_type} (1=Vazão, 2=Chuva, 3=Ambos)\n")
        
        successful = 0
        failed = 0
        
        for i, station in enumerate(stations_to_download, 1):
            print(f"\n[{i}/{len(stations_to_download)}] Processando estação {station}...")
            try:
                retrieve_from_station(station, initial_year, final_year, username, password, data_type)
                successful += 1
            except Exception as e:
                print(f"ERRO - ao processar estacao {station}: {e}")
                failed += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"Resumo:")
        print(f"  OK - Bem-sucedidas: {successful}")
        print(f"  ERRO - Com erro: {failed}")
        print(f"  Total: {len(stations_to_download)}")
        print(f"{'='*80}")
    else:
        retrieve_from_station(station_id, initial_year, final_year, username, password, data_type)

import argparse

def main(argv):
    """
    Script principal para recuperar dados da ANA.
    
    Uso:
        python retrieve_ws_ana.py -u <username> -p <password> -s <station_id> -b <begin_year> -e <end_year> [-t <data_type>]
    
    Exemplos:
        # Baixar dados de uma estação específica (chuva e vazão)
        python retrieve_ws_ana.py -u SEU_CPF -p SUA_SENHA -s 2243028 -b 2020 -e 2024
        
        # Baixar apenas dados de chuva
        python retrieve_ws_ana.py -u SEU_CPF -p SUA_SENHA -s 2243028 -b 2020 -e 2024 -t 2
        
        # Baixar dados de todas as estações configuradas
        python retrieve_ws_ana.py -u SEU_CPF -p SUA_SENHA -s all -b 2020 -e 2024
    """
    
    parser = argparse.ArgumentParser(
        prog=argv[0],
        usage='{0} -u <username> -p <password> -s <station_id> -b <begin_year> -e <end_year> [-t <data_type>]'.format(argv[0]),
        description="""Este script fornece uma interface simples para recuperar observações 
        de estações hidrológicas da ANA (Agência Nacional de Águas e Saneamento Básico).
        
        API utilizada: HidroWeb Service (https://www.ana.gov.br/hidrowebservice/)
        Documentação: https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html#/
        
        IMPORTANTE: A API da ANA requer autenticação OAuth.
        Para obter credenciais (CPF/CNPJ e senha), envie e-mail para hidro@ana.gov.br
        com assunto "[SEU_CPF] - Solicitação de acesso à API HidroWebService"
        """
    )
    
    parser.add_argument(
        "-u", "--username",
        required=True,
        help="CPF ou CNPJ cadastrado na ANA",
        metavar=''
    )
    
    parser.add_argument(
        "-p", "--password",
        required=True,
        help="Senha fornecida pela ANA",
        metavar=''
    )
    
    parser.add_argument(
        "-s", "--station_id",
        required=True,
        help="Código da estação hidrológica ou 'all' para todas as estações configuradas",
        metavar=''
    )
    
    parser.add_argument(
        "-b", "--begin_year",
        type=int,
        required=True,
        help="Ano inicial (ex: 2020)",
        metavar=''
    )
    
    parser.add_argument(
        "-e", "--end_year",
        type=int,
        required=True,
        help="Ano final (ex: 2024)",
        metavar=''
    )
    
    parser.add_argument(
        "-t", "--data_type",
        type=int,
        default=3,
        choices=[1, 2, 3],
        help="Tipo de dados: 1=Vazão, 2=Chuva, 3=Ambos (padrão: 3)",
        metavar=''
    )
    
    args = parser.parse_args(argv[1:])
    
    username = args.username
    password = args.password
    station_id = args.station_id
    start_year = args.begin_year
    end_year = args.end_year
    data_type = args.data_type
    
    # Validações
    assert (username is not None) and (username != ''), "Username (CPF/CNPJ) é obrigatório"
    assert (password is not None) and (password != ''), "Password (senha) é obrigatório"
    assert (station_id is not None) and (station_id != ''), "Station ID é obrigatório"
    assert start_year <= end_year, "Ano inicial deve ser menor ou igual ao ano final"
    assert start_year >= 1900, "Ano inicial deve ser maior ou igual a 1900"
    assert end_year <= datetime.now().year, f"Ano final não pode ser maior que {datetime.now().year}"
    
    if station_id != "all" and station_id not in globals.ANA_STATION_IDS:
        print(f"\n⚠ Aviso: ID da estação '{station_id}' não está na lista de estações configuradas.")
        print(f"Estações disponíveis: {[s for s in globals.ANA_STATION_IDS if s != 'all']}")
        print("\nO script tentará baixar os dados mesmo assim.")
        print("Se a estação não existir, você receberá um erro da API.\n")
    
    data_type_names = {1: "Vazão", 2: "Chuva", 3: "Chuva e Vazão"}
    
    print("\n" + "=" * 80)
    print("RECUPERAÇÃO DE DADOS DA ANA - Agência Nacional de Águas")
    print("=" * 80)
    print(f"Usuário: {username}")
    print(f"Estação(ões): {station_id}")
    print(f"Período: {start_year} a {end_year}")
    print(f"Tipo de dados: {data_type_names.get(data_type, 'Desconhecido')}")
    print(f"Diretório de saída: {globals.WS_ANA_DATA_DIR}")
    print("=" * 80 + "\n")
    
    retrieve_data(station_id, start_year, end_year, username, password, data_type)
    
    print("\n" + "=" * 80)
    print("OK - Processamento concluido!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main(sys.argv)

