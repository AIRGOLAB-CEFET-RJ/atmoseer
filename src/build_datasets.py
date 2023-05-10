import pandas as pd
import numpy as np
import sys
import pickle
from utils.near_stations import prox

from globals import *
import globals as globals

from util import find_contiguous_observation_blocks, add_missing_indicator_column
from utils.windowing import apply_windowing
import util as util
import math
import argparse
import rainfall_prediction as rp
from subsampling import apply_subsampling
import xarray as xr
import logging

# def format_for_binary_classification(y_train, y_val, y_test):
#     y_train_oc = map_to_binary_precipitation_levels(y_train)
#     y_val_oc = map_to_binary_precipitation_levels(y_val)
#     y_test_oc = map_to_binary_precipitation_levels(y_test)
#     return y_train_oc, y_val_oc, y_test_oc

# def format_for_ordinal_classification(y_train, y_val, y_test):
#     y_train_oc = map_to_precipitation_levels(y_train)
#     y_val_oc = map_to_precipitation_levels(y_val)
#     y_test_oc = map_to_precipitation_levels(y_test)
#     return y_train_oc, y_val_oc, y_test_oc

def apply_sliding_window(df: pd.DataFrame, target_idx: int):
    """
    This function applies the sliding window preprocessing technique to generate data and response 
    matrices (that is, X and y) from an input time series represented as a pandas DataFrame. This 
    DataFrame is supposed to have a datetime index that corresponds to the timestamps in the time series.

    @see: https://stackoverflow.com/questions/8269916/what-is-sliding-window-algorithm-examples

    Note that this function takes the eventual existence of gaps in the input time series 
    into account. In particular, the windowing operation is performed in each separate 
    contiguous block of observations.
    """
    contiguous_observation_blocks = list(
        find_contiguous_observation_blocks(df))

    is_first_block = True

    for block in contiguous_observation_blocks:
        start = block[0]
        end = block[1]

        # logging.info(df[start:end].shape)
        if df[start:end].shape[0] < globals.hyper_params_dict_bc["SLIDING_WINDOW_SIZE"] + 1:
            continue

        arr = np.array(df[start:end])
        X_block, y_block = apply_windowing(arr,
                                           initial_time_step=0,
                                           max_time_step=len(
                                               arr)-globals.hyper_params_dict_bc["SLIDING_WINDOW_SIZE"]-1,
                                           window_size=globals.hyper_params_dict_bc["SLIDING_WINDOW_SIZE"],
                                           target_idx=target_idx)
        y_block = y_block.reshape(-1, 1)
        if is_first_block:
            X = X_block
            y = y_block
            is_first_block = False
        else:
            X = np.concatenate((X, X_block), axis=0)
            y = np.concatenate((y, y_block), axis=0)

    return X, y

def get_NWP_data_for_weather_station(station_id, initial_datetime, final_datetime):
    df_stations = pd.read_csv("../data/ws/WeatherStations.csv")
    row = df_stations[df_stations["STATION_ID"] == station_id].iloc[0]
    station_latitude = row["VL_LATITUDE"]
    station_longitude = row["VL_LONGITUDE"]

    logging.info(f"Weather station {station_id} is located at lat/long = {station_latitude}/{station_longitude}")

    logging.info(f"Selecting NWP data between {initial_datetime} and {final_datetime}.")
    
    ds = xr.open_dataset("../data/NWP/ERA5.nc")
    logging.info(f"Size.0: {ds.sizes['time']}")

    # Get the minimum and maximum values of the 'time' coordinate
    # time_min = ds.coords['time'].min().item()
    # time_max = ds.coords['time'].max().item()
    # logging.info(f"Range of timestamps in the original NWP data: [{ds.time.min()}, {ds.time.max()}]")
    # logging.info(f"Range of timestamps in the original NWP data: [{time_min}, {time_max}]")
    time_min = ds.time.min().values
    time_max = ds.time.max().values
    logging.info(f"Range of timestamps in the original NWP data: [{time_min}, {time_max}]")

    # If we want to properly merge the two data sources, then we have to consider 
    # only the range of periods in which these data sources intersect.
    time_min = max(time_min, initial_datetime)
    time_max = min(time_max, final_datetime)
    logging.info(f"Range of timestamps to be selected: [{time_min}, {time_max}]")

    ds = ds.sel(time=slice(time_min, time_max))
    logging.info(f"Size.1: {ds.sizes['time']}")

    era5_data_at_200hPa = ds.sel(level=200, longitude=station_longitude, latitude=station_latitude, method="nearest")
    logging.info(f"Size.2: {era5_data_at_200hPa.sizes['time']}")

    era5_data_at_700hPa = ds.sel(level=700, longitude=station_longitude, latitude=station_latitude, method="nearest")
    logging.info(f"Size.3: {era5_data_at_700hPa.sizes['time']}")

    era5_data_at_1000hPa = ds.sel(level=1000, longitude=station_longitude, latitude=station_latitude, method="nearest")
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

    df_NWP_data_for_station = pd.DataFrame(
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

    # Drop rows with at least one NaN
    logging.info(f"Shape before dropping NaN values is {df_NWP_data_for_station.shape}")
    df_NWP_data_for_station = df_NWP_data_for_station.dropna(how='any')
    logging.info(f"Shape before dropping NaN values is {df_NWP_data_for_station.shape}")

    logging.info("Success!")

    #
    # Add index to dataframe using the timestamps.
    format_string = '%Y-%m-%d %H:%M:%S'
    df_NWP_data_for_station['Datetime'] = pd.to_datetime(df_NWP_data_for_station['time'], format=format_string)
    df_NWP_data_for_station = df_NWP_data_for_station.set_index(pd.DatetimeIndex(df_NWP_data_for_station['Datetime']))
    df_NWP_data_for_station = df_NWP_data_for_station.drop(['time', 'Datetime'], axis = 1)
    logging.info(f"Range of timestamps in the selected slice of NWP data: [{min(df_NWP_data_for_station.index)}, {max(df_NWP_data_for_station.index)}]")

    logging.info(df_NWP_data_for_station)

    assert (not df_NWP_data_for_station.isnull().values.any().any())

    return df_NWP_data_for_station
    
def generate_windowed_split(train_df, val_df, test_df, target_name):
    target_idx = train_df.columns.get_loc(target_name)
    logging.info(f"Position (index) of target variable {target_name}: {target_idx}")
    X_train, y_train = apply_sliding_window(train_df, target_idx)
    X_val, y_val = apply_sliding_window(val_df, target_idx)
    X_test, y_test = apply_sliding_window(test_df, target_idx)
    return X_train, y_train, X_val, y_val, X_test, y_test


def build_datasets(station_id: str, join_as_data_source: bool, join_nwp_data_source: bool, subsampling_procedure: str):
    '''
    This function joins a set of datasources to build datasets. These resulting datasets are used to fit the parameters of
    precipitation models down the AtmoSeer pipeline. Each datasource contributes with a group of features to build the datasets 
    that are going to be used for training and validating the predictions models.
    
    Notice that, when joining the user-specified data sources, there is always a station of interest, that is, a weather 
    station that will provide the values of the target variable (in our case, precipitation). It can even be the case that 
    the only user-specified data source is this weather station. 
    '''

    pipeline_id = station_id
    if join_nwp_data_source:
        pipeline_id = pipeline_id + '_N'
    if join_as_data_source:
        pipeline_id = pipeline_id + '_R'

    logging.info(f"Loading observations for weather station {station_id}...")
    df_ws = pd.read_parquet(WS_INMET_DATA_DIR + station_id + "_preprocessed.parquet.gzip")
    logging.info(f"Done! Shape = {df_ws.shape}.")

    ####
    # Apply a filtering step, with the purpose of disregarding all observations made between  
    # what we consider to be the drought period of a year (months of June, July, and August).
    ####
    logging.info(f"Applying month filtering...")
    shape_before_month_filtering = df_ws.shape
    df_ws = df_ws[df_ws.index.month.isin([9, 10, 11, 12, 1, 2, 3, 4, 5])].sort_index(ascending=True)
    shape_after_month_filtering = df_ws.shape
    logging.info(f"Done! Shapes before/after: {shape_before_month_filtering}/{shape_after_month_filtering}")

    assert (not df_ws.isnull().values.any().any())

    #####
    # Start with the mandatory datasource (i.e., the one represented by the chosen weather station) 
    # and sequentially join the other user-specified datasources.
    #####
    joined_df = df_ws
    min_datetime = min(joined_df.index)
    max_datetime = max(joined_df.index)

    if join_nwp_data_source:
        logging.info(f"Loading NWP (ERA5) data near the weather station {station_id}...")
        df_nwp_era5 = get_NWP_data_for_weather_station(station_id, min_datetime, max_datetime)
        logging.info(f"Done! Shape = {df_nwp_era5.shape}.")
        assert (not df_nwp_era5.isnull().values.any().any())

        joined_df = pd.merge(df_ws, df_nwp_era5, how='left', left_index=True, right_index=True)

        logging.info(f"NWP data successfully joined; resulting shape = {joined_df.shape}.")
        logging.info(df_ws.index.difference(joined_df.index).shape)
        logging.info(joined_df.index.difference(df_ws.index).shape)

        logging.info(df_nwp_era5.index.intersection(df_ws.index).shape)
        logging.info(df_nwp_era5.index.difference(df_ws.index).shape)
        logging.info(df_ws.index.difference(df_nwp_era5.index).shape)
        logging.info(df_ws.index.difference(df_nwp_era5.index))

        shape_before_dropna = joined_df.shape
        joined_df = joined_df.dropna()
        shape_after_dropna = joined_df.shape
        logging.info(f"Removed NaN rows in merge data; Shapes before/after dropna: {shape_before_dropna}/{shape_after_dropna}.")

    assert (not joined_df.isnull().values.any().any())

    if join_as_data_source:
        filename = AS_DATA_DIR + 'SBGL_indices_1997_2023.parquet.gzip'
        logging.info(f"Loading atmospheric sounding indices from {filename}...")
        df_as = pd.read_parquet(filename)
        logging.info(f"Done! Shape = {df_as.shape}.")

        format_string = '%Y-%m-%d %H:%M:%S'

        #
        # Add index to dataframe using the observation's timestamps.
        df_as['Datetime'] = pd.to_datetime(df_as['time'], format=format_string)
        df_as = df_as.set_index(pd.DatetimeIndex(df_as['Datetime']))
        logging.info(f"Range of timestamps in the atmospheric sounding data source: [{min(df_as.index)}, {max(df_as.index)}]")

        #
        # Remove time-related columns since now this information is in the index.
        df_as = df_as.drop(['time', 'Datetime'], axis = 1)

        joined_df = pd.merge(joined_df, df_as, how='left', left_index=True, right_index=True)

        logging.info(f"Atmospheric sounding data successfully joined; resulting shape: {joined_df.shape}.")

        joined_df = add_missing_indicator_column(joined_df, "asi_idx_missing")
        logging.info(f"Shape after adding missing indicator column: {joined_df.shape}.")

        logging.info(f"Doing interpolation to imput missing values on the sounding indices...")
        joined_df['cape'] = joined_df['cape'].interpolate(method='linear')
        joined_df['cin'] = joined_df['cin'].interpolate(method='linear')
        joined_df['lift'] = joined_df['lift'].interpolate(method='linear')
        joined_df['k'] = joined_df['k'].interpolate(method='linear')
        joined_df['total_totals'] = joined_df['total_totals'].interpolate(method='linear')
        joined_df['showalter'] = joined_df['showalter'].interpolate(method='linear')
        logging.info("Done!")
        
        # At the beggining of the joined dataframe, a few entries may remain with NaN values. The code below
        # gets rid of these entries.
        # see https://stackoverflow.com/questions/27905295/how-to-replace-nans-by-preceding-or-next-values-in-pandas-dataframe
        joined_df.fillna(method='bfill', inplace=True)

        assert (not joined_df.isnull().values.any().any())

        # TODO: data normalization 
        # TODO: implement interpolation
        # TODO: deal with missing values (see https://youtu.be/DKmDJJzayZw)
        # TODO: Imputing with MICE (see https://towardsdatascience.com/imputing-missing-data-with-simple-and-advanced-techniques-f5c7b157fb87)
        # TODO: use other sounding stations (?) (see tempo.inmet.gov.br/Sondagem/)

    #
    # Save train/val/test DataFrames for future error analisys.
    filename = DATASETS_DIR + pipeline_id + '.parquet.gzip'
    logging.info(f'Saving joined data source for pipeline {pipeline_id} to file {filename}.')
    joined_df.to_parquet(filename, compression='gzip')

    assert (not joined_df.isnull().values.any().any())

    #
    # Data splitting (train/val/test)
    # TODO: parameterize with user-defined splitting proportions.
    dict_splitting_proportions = {"train": 0.7, "val": 0.2, "test": 0.1}
    logging.info(f"Splitting train/val/test examples according to proportion {dict_splitting_proportions}.")
    assert (math.isclose(sum(dict_splitting_proportions.values()),1.0, abs_tol=1e-8))

    train_prob = dict_splitting_proportions["train"]
    val_prob = dict_splitting_proportions["val"]
    n = len(joined_df)
    
    train_upper_limit = int(n*train_prob)
    val_upper_limit = int(n*(train_prob+val_prob))
    logging.info(f"Ranges (train/val/test): ({0},{train_upper_limit})/({train_upper_limit},{val_upper_limit})/({val_upper_limit},{n})")

    df_train = joined_df[0:train_upper_limit]
    df_val = joined_df[train_upper_limit:val_upper_limit]
    df_test = joined_df[val_upper_limit:]

    assert (not df_train.isnull().values.any().any())
    assert (not df_val.isnull().values.any().any())
    assert (not df_test.isnull().values.any().any())

    logging.info(f'Done! Number of examples in each dataset (train/val/test): {len(df_train)}/{len(df_val)}/{len(df_test)}.')
    logging.info(f"Range of timestamps in the training dataset: [{min(df_train.index)}, {max(df_train.index)}]")
    logging.info(f"Range of timestamps in the validation dataset: [{min(df_val.index)}, {max(df_val.index)}]")
    logging.info(f"Range of timestamps in the test dataset: [{min(df_test.index)}, {max(df_test.index)}]")

    #
    # Save train/val/test DataFrames for future error analisys.
    logging.info(f'Saving each train/val/test dataset for pipeline {pipeline_id} as a parquet file.')
    df_train.to_parquet(DATASETS_DIR + pipeline_id + '_train.parquet.gzip', compression='gzip')
    df_val.to_parquet(DATASETS_DIR + pipeline_id + '_val.parquet.gzip', compression='gzip')
    df_test.to_parquet(DATASETS_DIR + pipeline_id + '_test.parquet.gzip', compression='gzip')

    assert (not df_train.isnull().values.any().any())
    assert (not df_val.isnull().values.any().any())
    assert (not df_test.isnull().values.any().any())

    #
    # Normalize the columns in train/val/test dataframes. This is done as a preparation step for appllying
    # the sliding window technique, since the target variable is going to be used as lag feature.
    # (see, e.g., https://www.mikulskibartosz.name/forecasting-time-series-using-lag-features/)
    # (see also https://datascience.stackexchange.com/questions/72480/what-is-lag-in-time-series-forecasting)
    logging.info('Normalizing the features in train/val/test dataframes.')
    _, target_name = util.get_relevant_variables(station_id)
    min_target_value_in_train, max_target_value_in_train = min(df_train[target_name]), max(df_train[target_name])
    min_target_value_in_val, max_target_value_in_val = min(df_val[target_name]), max(df_val[target_name])
    min_target_value_in_test, max_target_value_in_test = min(df_test[target_name]), max(df_test[target_name])
    df_train = util.min_max_normalize(df_train)
    df_val = util.min_max_normalize(df_val)
    df_test = util.min_max_normalize(df_test)

    assert (not df_train.isnull().values.any().any())
    assert (not df_val.isnull().values.any().any())
    assert (not df_test.isnull().values.any().any())

    #
    # Apply sliding windowing method to build examples (instances) of train/val/test datasets 
    logging.info('Applying sliding window to build train/val/test datasets.')
    X_train, y_train, X_val, y_val, X_test, y_test = generate_windowed_split(
        df_train, df_val, df_test, target_name=target_name)
    logging.info("Done! Resulting shapes:")
    logging.info(f' - (X_train/X_val/X_test): ({X_train.shape}/{X_val.shape}/{X_test.shape})')
    logging.info(f' - (y_train/y_val/y_test): ({y_train.shape}/{y_val.shape}/{y_test.shape})')

    assert not np.isnan(np.sum(X_train))
    assert not np.isnan(np.sum(X_val))
    assert not np.isnan(np.sum(X_test))
    assert not np.isnan(np.sum(y_train))
    assert not np.isnan(np.sum(y_val))
    assert not np.isnan(np.sum(y_test))

    #
    # Now, we restore the target variable to their original values. This is needed in case a multiclass
    # classification task is defined down the pipeline.
    logging.info('Restoring the target variable to their original values.')
    y_train = (y_train + min_target_value_in_train) * (max_target_value_in_train - min_target_value_in_train)
    y_val = (y_val + min_target_value_in_val) * (max_target_value_in_val - min_target_value_in_val)
    y_test = (y_test + min_target_value_in_test) * (max_target_value_in_test - min_target_value_in_test)
    logging.info('Min precipitation values (train/val/test): %.5f, %.5f, %.5f' %
          (np.min(y_train), np.min(y_val), np.min(y_test)))
    logging.info('Max precipitation values (train/val/test): %.5f, %.5f, %.5f' %
          (np.max(y_train), np.max(y_val), np.max(y_test)))

    if subsampling_procedure != "NONE":
        #
        # Subsampling
        logging.info('**********Subsampling************')
        logging.info(f'- Shapes before subsampling (y_train/y_val/y_test): {y_train.shape}, {y_val.shape}, {y_test.shape}')
        logging.info("Subsampling train data.")
        X_train, y_train = apply_subsampling(X_train, y_train, subsampling_procedure)
        logging.info("Subsampling val data.")

        X_val, y_val = apply_subsampling(X_val, y_val, "NEGATIVE")
        logging.info('- Min precipitation values (train/val/test) after subsampling: %.5f, %.5f, %.5f' %
              (np.min(y_train), np.min(y_val), np.min(y_test)))

        logging.info('- Max precipitation values (train/val/test) after subsampling: %.5f, %.5f, %.5f' %
            (np.max(y_train), np.max(y_val), np.max(y_test)))
        logging.info(f'- Shapes (y_train/y_val/y_test) after subsampling: {y_train.shape}, {y_val.shape}, {y_test.shape}')

    #
    # Write numpy arrays for train/val/test datast to a single pickle file
    logging.info(
        f'Number of examples (train/val/test): {len(X_train)}/{len(X_val)}/{len(X_test)}.')
    filename = DATASETS_DIR + pipeline_id + ".pickle"
    logging.info(f'Dumping train/val/test np arrays to pickle file {filename}.')
    file = open(filename, 'wb')
    ndarrays = (X_train, y_train, 
                X_val, y_val, 
                X_test, y_test)
    pickle.dump(ndarrays, file)
    logging.info('Done!')

def main(argv):
    parser = argparse.ArgumentParser(
        description="""This script builds the train/val/test datasets for a given weather station, by using the user-specified data sources.""")
    parser.add_argument('-s', '--station_id', type=str, required=True, help='station id')
    parser.add_argument('-d', '--datasources', type=str, help='data source spec')
    parser.add_argument('-sp', '--subsampling_procedure', type=str, default='NONE', help='Subsampling procedure do be applied.')
    args = parser.parse_args(argv[1:])

    station_id = args.station_id
    datasources = args.datasources
    subsampling_procedure = args.subsampling_procedure

    lst_subsampling_procedures = ["NONE", "NAIVE", "NEGATIVE"]
    if not (subsampling_procedure in lst_subsampling_procedures):
        print(f"Invalid subsampling procedure: {subsampling_procedure}. Valid values: {lst_subsampling_procedures}")
        parser.print_help()
        sys.exit(2)

    if not ((station_id in INMET_STATION_CODES_RJ) or (station_id in COR_STATION_NAMES_RJ)):
        print(f"Invalid station identifier: {station_id}")
        parser.print_help()
        sys.exit(2)

    fmt = "[%(levelname)s] %(funcName)s():%(lineno)i: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format = fmt)

    join_as_data_source = False
    join_nwp_data_source = False

    if datasources:
        if 'R' in datasources:
            join_as_data_source = True
        if 'N' in datasources:
            join_nwp_data_source = True

    assert(station_id is not None) and (station_id != "")
    build_datasets(station_id, join_as_data_source, join_nwp_data_source, subsampling_procedure)

if __name__ == "__main__":
    main(sys.argv)
