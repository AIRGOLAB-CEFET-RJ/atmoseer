import pandas as pd
from pathlib import Path
import argparse
import sys
from globals import *
from util import *
import util as util
from sklearn.impute import KNNImputer

list_valid_datasource_combinations = ("R", "N", "R+N")

def preprocess_sounding_data(sounding_data_source):
    print(f"Loading datasource file ({sounding_data_source}).")
    df = pd.read_parquet(sounding_data_source)
    format_string = '%Y-%m-%d %H:%M:%S'

    #
    # Add index to dataframe using the observation's timestamps.
    df['Datetime'] = pd.to_datetime(df['time'], format=format_string)
    df = df.set_index(pd.DatetimeIndex(df['Datetime']))
    print(f"Range of timestamps after preprocessing {sounding_data_source}: [{min(df.index)}, {max(df.index)}]")

    #
    # Remove time-related columns since now this information is in the index.
    df = df.drop(['time', 'Datetime'], axis = 1)

    #
    # Save preprocessed data.
    filename_and_extension = get_filename_and_extension(sounding_data_source)
    filename = filename_and_extension[0] + '_preprocessed.parquet.gzip'
    print(f"Saving preprocessed data to {filename}")
    df.to_parquet(filename, compression='gzip')

def preprocess_numerical_model_data(numerical_model_data_source):
    print(f"Loading datasource file ({numerical_model_data_source}).")
    df = pd.read_csv(numerical_model_data_source)

    #
    # Add index to dataframe using the timestamps.
    format_string = '%Y-%m-%d %H:%M:%S'
    df['Datetime'] = pd.to_datetime(df['time'], format=format_string)
    df = df.set_index(pd.DatetimeIndex(df['Datetime']))
    df = df.drop(['time', 'Datetime', 'Unnamed: 0'], axis = 1)
    print(f"Range of timestamps after preprocessing {numerical_model_data_source}: [{min(df.index)}, {max(df.index)}]")

    df = util.min_max_normalize(df)

    #
    # Save preprocessed data.
    filename_and_extension = get_filename_and_extension(numerical_model_data_source)
    filename = filename_and_extension[0] + '_preprocessed.parquet.gzip'
    print(f"Saving preprocessed data to {filename}")
    df.to_parquet(filename, compression='gzip')

def preprocess_ws_datasource(station_id, ws_datasource):
    print(f"Loading datasource file ({ws_datasource}).")
    df = pd.read_csv(ws_datasource)

    #
    # Add index to dataframe using the timestamps.
    df = add_datetime_index(station_id, df)

    #
    # Drop observations in which the target variable is not defined.
    print(f"Dropping entries with null target.")
    n_obser_before_drop = len(df)
    df = df[df['CHUVA'].notna()]
    n_obser_after_drop = len(df)
    print(f"Number of observations before/after dropping entries with null target: {n_obser_before_drop}/{n_obser_after_drop}.")
    print(f"Range of timestamps after dropping entries with null target: [{min(df.index)}, {max(df.index)}]")

    #
    # Create wind-related features (U and V components of wind observations).
    df = add_wind_related_features(station_id, df)

    #
    # Create hour-related features (sin and cos components)
    df = add_hour_related_features(df)

    predictor_names, target_name = get_relevant_variables(station_id)
    print(f"Chosen predictors: {predictor_names}")
    print(f"Chosen target: {target_name}")
    df = df[predictor_names + [target_name]]

    #
    # Normalize the weather station data. This step is necessary here due to the next step, which deals with missing values.
    # Notice that we drop the target column before normalizing, to avoid some kind of data leakage.
    # (see https://stats.stackexchange.com/questions/214728/should-data-be-normalized-before-or-after-imputation-of-missing-data)
    print("Normalizing data before applying KNNImputer...", end='')
    target_column = df[target_name]
    df = df.drop(columns=[target_name], axis=1)
    df = min_max_normalize(df)
    print("Done!")

    # 
    # Imput missing values on some features.
    print(f"There are {df.isnull().sum().sum()} missing values in the weather station data. Going to fill them...", end = '')
    imputer = KNNImputer(n_neighbors=2)
    df[:] = imputer.fit_transform(df)
    assert (not df.isnull().values.any().any())
    print("Done!")

    #
    # Add the target column back to the DataFrame.
    df[target_name] = target_column

    #
    # Save preprocessed data to a parquet file.
    filename_and_extension = get_filename_and_extension(ws_datasource)
    filename = filename_and_extension[0] + '_preprocessed.parquet.gzip'
    print(f"Saving preprocessed data to {filename}")
    df.to_parquet(filename, compression='gzip')

def main(argv):
    parser = argparse.ArgumentParser(description='Preprocess weather station, sounding indices, and NWP data sources.')
    parser.add_argument('-s', '--station_id', required=True, choices=INMET_STATION_CODES_RJ + COR_STATION_NAMES_RJ, help='ID of the weather station to preprocess data for.')
    parser.add_argument('-d', '--datasources', required=True, choices=list_valid_datasource_combinations, help='Data sources to preprocess. Combination of R (sounding indices) and N (NWP data) allowed.')
    parser.add_argument('-n', '--neighbors', default=0, type=int, help='Number of neighbor weather stations to use.')
    args = parser.parse_args(argv[1:])
    
    sounding_indices_data_source = None
    numerical_model_data_source = None
    num_neighbors = args.neighbors
    
    if args.datasources.find('R') != -1:
        sounding_indices_data_source = '../data/sounding/SBGL_indices_1997_2023.parquet.gzip'
    if args.datasources.find('N') != -1:
        numerical_model_data_source = '../data/NWP/ERA5_A652_1997_2023.csv'

    print(f'Going to preprocess data sources according to user specification ({args.datasources})...')

    print('\n***Preprocessing weather station data***')
    ws_datasource = '../data/gauge/A652_2007_2023.csv'
    preprocess_ws_datasource(args.station_id, ws_datasource)
    
    if sounding_indices_data_source is not None:
        print('\n***Preprocessing sounding indices data***')
        preprocess_sounding_data(sounding_indices_data_source)

    if numerical_model_data_source is not None:
        print('\n***Preprocessing NWP data***')
        preprocess_numerical_model_data(numerical_model_data_source)

    print('Done!')

if __name__ == '__main__':
    main(sys.argv)
