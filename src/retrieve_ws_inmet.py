import pandas as pd
import sys, getopt
from datetime import datetime
from util import is_posintstring
from globals import *

def import_from_station(station_id, beginning_year, end_year, api_token):

    current_date = datetime.now()
    current_year = current_date.year
    end_year = min(end_year, current_year)

    years = list(range(beginning_year, end_year + 1))
    df_inmet_stations = pd.read_json(API_BASE_URL + '/estacoes/T')
    station_row = df_inmet_stations[df_inmet_stations['CD_ESTACAO'] == station_id]
    df_observations_for_all_years = None
    print(f"Downloading observations from weather station {station_id}...")
    for year in years:
        print(f"Downloading observations for year {year}...")

        if year == end_year:
            datetime_str = str(end_year) + '-12-31'
            last_date_of_the_end_year = datetime.strptime(datetime_str, '%Y-%m-%d')
            end_date = min(last_date_of_the_end_year, current_date)
            end_date_str = end_date.strftime("%Y-%m-%d")
            query_str = API_BASE_URL + '/token/estacao/' + str(year) + '-01-01/' + end_date_str + '/' + station_id + "/" + api_token
        else:
            query_str = API_BASE_URL + '/token/estacao/' + str(year) + '-01-01/' + str(year) + '-12-31/' + station_id + "/" + api_token

        print(f"Query to be sent to server: {query_str}")

        df_observations_for_a_year = pd.read_json(query_str)
        if df_observations_for_all_years is None:
            temp = [df_observations_for_a_year]
        else:
            temp = [df_observations_for_all_years, df_observations_for_a_year]
        df_observations_for_all_years = pd.concat(temp)
    filename = '../data/gauge/' + station_row['CD_ESTACAO'].iloc[0] + '_'+ str(beginning_year) +'_'+ str(end_year) +'.csv'
    print(f"Done! Saving dowloaded content to '{filename}'.")
    df_observations_for_all_years.to_csv(filename)

def import_data(station_code, initial_year, final_year, api_token):
    if station_code == "all":
        df_inmet_stations = pd.read_json(API_BASE_URL + '/estacoes/T')
        station_row = df_inmet_stations[df_inmet_stations['CD_ESTACAO'].isin(INMET_STATION_CODES_RJ)]
        for j in list(range(0, len(station_row))):
            station_code = station_row['CD_ESTACAO'].iloc[j]
            import_from_station(station_code, initial_year, final_year, api_token)
    else:
        import_from_station(station_code, initial_year, final_year, api_token)

def main(argv):
    station_code = ""

    start_year = 1997
    end_year = datetime.now().year

    help_message = "{0} -s <station_id> -b <begin> -e <end> -t <api_token>".format(argv[0])
    
    try:
        opts, args = getopt.getopt(argv[1:], "hs:b:e:t:", ["help", "station=", "begin=", "end=", "api_token="])
    except:
        print(help_message)
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_message)
            sys.exit(2)
        elif opt in ("-t", "--api_token"):
            api_token = arg
        elif opt in ("-s", "--station"):
            station_code = arg
            if not ((station_code == "all") or (station_code in INMET_STATION_CODES_RJ)):
                print(help_message)
                sys.exit(2)
        elif opt in ("-b", "--begin"):
            if not is_posintstring(arg):
                sys.exit("Argument start_year must be an integer. Exit.")
            start_year = int(arg)
        elif opt in ("-e", "--end"):
            if not is_posintstring(arg):
                sys.exit("Argument end_year must be an integer. Exit.")
            end_year = int(arg)

    assert (api_token is not None) and (api_token != '')
    assert (station_code is not None) and (station_code != '')
    assert (start_year <= end_year)

    import_data(station_code, start_year, end_year, api_token)


if __name__ == "__main__":
    main(sys.argv)


