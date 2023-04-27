import pandas as pd
import numpy as np
import sys
import pickle
from utils.near_stations import prox
from globals import *
from util import find_contiguous_observation_blocks
from utils.windowing import apply_windowing
import util as util
import math
import argparse
import rainfall_prediction as rp
from subsampling import apply_subsampling

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

def generate_windowed(df: pd.DataFrame, target_idx: int):
    """
    This function applies the sliding window preprocessing technique to generate data an response matrices 
    from an input time series represented as a pandas DataFrame. This DataFrame is supposed to have
    a datetime index that corresponds to the timestamps in the time series.

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

        # print(df[start:end].shape)
        if df[start:end].shape[0] < TIME_WINDOW_SIZE + 1:
            continue

        arr = np.array(df[start:end])
        X_block, y_block = apply_windowing(arr,
                                           initial_time_step=0,
                                           max_time_step=len(
                                               arr)-TIME_WINDOW_SIZE-1,
                                           window_size=TIME_WINDOW_SIZE,
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


def generate_windowed_split(train_df, val_df, test_df, target_name):
    target_idx = train_df.columns.get_loc(target_name)
    print(f"Position (index) of target variable {target_name}: {target_idx}")
    X_train, y_train = generate_windowed(train_df, target_idx)
    X_val, y_val = generate_windowed(val_df, target_idx)
    X_test, y_test = generate_windowed(test_df, target_idx)
    return X_train, y_train, X_val, y_val, X_test, y_test


def build_datasets(station_id: str, join_sounding_data_source: bool, join_numerical_model_data_source: bool, num_neighbors: int =0):
    '''
    This function joins a set of datasources to build datasets. These resulting datasets are used to fit the parameters of
    precipitation models down the AtmoSeer pipeline. Each datasource contributes with a group of features to build the datasets 
    that are going to be used for training and validating the predictions models.
    
    Notice that, when joining the user-specified data sources, there is always a station of interest, that is, a weather 
    station that will provide the values of the target variable (in our case, precipitation). It can even be the case that 
    the only user-specified data source is this weather station. 
    '''

    pipeline_id = station_id
    if join_numerical_model_data_source:
        pipeline_id = pipeline_id + '_N'
    if join_sounding_data_source:
        pipeline_id = pipeline_id + '_R'

    if num_neighbors > 0:
        pipeline_id = pipeline_id + '_NN' + str(num_neighbors)

    print(f"Loading observations for weather station {station_id}...", end= "")
    df_ws = pd.read_parquet("../data/gauge/" + station_id + "_2007_2023_preprocessed.parquet.gzip")
    print(f"Done! Shape = {df_ws.shape}.")
    # df_ws = pd.read_parquet(
    #     '../data/gauge/A652_2007_2023_preprocessed.parquet.gzip')

    ####
    # Apply a filtering step (e.g., to disregard all observations made between what we 
    # consider to be the drought period (months of June, July, and August).
    ####
    print(f"Applying month filtering...", end=' ')
    shape_before_month_filtering = df_ws.shape
    df_ws = df_ws[df_ws.index.month.isin([9, 10, 11, 12, 1, 2, 3, 4, 5])].sort_index(ascending=True)
    shape_after_month_filtering = df_ws.shape
    print(f"Done! Shapes before/after: {shape_before_month_filtering}/{shape_after_month_filtering}")

    assert (not df_ws.isnull().values.any().any())

    #####
    # Start with the mandatory datasource (i.e., the one represented by the chosen weather station) 
    # and sequentially join the other user-specified datasources.
    #####
    joined_df = df_ws

    if join_numerical_model_data_source:
        print(f"Loading NWP (ERA5) datasource...", end= "")
        df_nwp_era5 = pd.read_parquet('../data/NWP/ERA5_A652_1997_2023_preprocessed.parquet.gzip')
        print(f"Done! Shape = {df_nwp_era5.shape}.")
        assert (not df_nwp_era5.isnull().values.any().any())
        print(f"NWP data loaded. Shape = {df_nwp_era5.shape}.")
        joined_df = pd.merge(df_ws, df_nwp_era5, how='left', left_index=True, right_index=True)
        # merged_df = merged_df.join(df_nwp_era5)

        print(f"NWP data successfully joined; resulting shape = {joined_df.shape}.")
        print(df_ws.index.difference(joined_df.index).shape)
        print(joined_df.index.difference(df_ws.index).shape)

        print(df_nwp_era5.index.intersection(df_ws.index).shape)
        print(df_nwp_era5.index.difference(df_ws.index).shape)
        print(df_ws.index.difference(df_nwp_era5.index).shape)
        print(df_ws.index.difference(df_nwp_era5.index))

        shape_before_dropna = joined_df.shape
        joined_df = joined_df.dropna()
        shape_after_dropna = joined_df.shape
        print(f"Removed NaN rows in merge data; Shapes before/after dropna: {shape_before_dropna}/{shape_after_dropna}.")
        # assert(merged_df.shape[0] == df_ws.shape[0])

    assert (not joined_df.isnull().values.any().any())

    if join_sounding_data_source:
        print(f"Loading sounding datasource...", end= "")
        df_sounding = pd.read_parquet('../data/sounding/SBGL_indices_1997_2023_preprocessed.parquet.gzip')
        print(f"Done! Shape = {df_sounding.shape}.")

        joined_df = pd.merge(joined_df, df_sounding, how='left', left_index=True, right_index=True)
        print(f"Sounding data successfully joined; resulting shape = {joined_df.shape}.")

        print(f"Doing interpolation to imput missing values on the sounding indices...", end= "")
        joined_df['cape'] = joined_df['cape'].interpolate(method='linear')
        joined_df['cin'] = joined_df['cin'].interpolate(method='linear')
        joined_df['lift'] = joined_df['lift'].interpolate(method='linear')
        joined_df['k'] = joined_df['k'].interpolate(method='linear')
        joined_df['total_totals'] = joined_df['total_totals'].interpolate(method='linear')
        joined_df['showalter'] = joined_df['showalter'].interpolate(method='linear')
        print("Done!")
        
        # At the beggining of the joined dataframe, a few entries may remain with NaN values. The code below
        # gets rid of these entries.
        # see https://stackoverflow.com/questions/27905295/how-to-replace-nans-by-preceding-or-next-values-in-pandas-dataframe
        joined_df.fillna(method='bfill', inplace=True)

        # TODO: data normalization 
        # TODO: implement interpolation
        # TODO: deal with missing values (see https://youtu.be/DKmDJJzayZw)
        # TODO: Imputing with MICE (see https://towardsdatascience.com/imputing-missing-data-with-simple-and-advanced-techniques-f5c7b157fb87)
        # TODO: use other sounding stations (?) (see tempo.inmet.gov.br/Sondagem/)

    if num_neighbors != 0:
        pass

    #
    # Save train/val/test DataFrames for future error analisys.
    filename = '../data/datasets/' + pipeline_id + '.parquet.gzip'
    print(f'Saving joined data source for pipeline {pipeline_id} to file {filename}.')
    joined_df.to_parquet(filename, compression='gzip')

    assert (not joined_df.isnull().values.any().any())

    #
    # Data splitting (train/val/test)
    # TODO: parameterize with user-defined splitting proportions.
    dict_splitting_proportions = {"train": 0.7, "val": 0.2, "test": 0.1}
    print(f"Splitting train/val/test examples according to proportion {dict_splitting_proportions}.")
    assert (math.isclose(sum(dict_splitting_proportions.values()),1.0, abs_tol=1e-8))

    train_prob = dict_splitting_proportions["train"]
    val_prob = dict_splitting_proportions["val"]
    n = len(joined_df)
    
    train_upper_limit = int(n*train_prob)
    val_upper_limit = int(n*(train_prob+val_prob))
    print(f"Ranges (train/val/test): ({0},{train_upper_limit})/({train_upper_limit},{val_upper_limit})/({val_upper_limit},{n})")

    df_train = joined_df[0:train_upper_limit]
    df_val = joined_df[train_upper_limit:val_upper_limit]
    df_test = joined_df[val_upper_limit:]
    assert (not df_train.isnull().values.any().any())
    assert (not df_val.isnull().values.any().any())
    assert (not df_test.isnull().values.any().any())
    print(f'Done! Number of examples in each part (train/val/test): {len(df_train)}/{len(df_val)}/{len(df_test)}.')

    #
    # Save train/val/test DataFrames for future error analisys.
    print(f'Saving each train/val/test dataset for pipeline {pipeline_id} as a parquet file.')
    df_train.to_parquet('../data/datasets/' + pipeline_id + '_train.parquet.gzip', compression='gzip')
    df_val.to_parquet('../data/datasets/' + pipeline_id + '_val.parquet.gzip', compression='gzip')
    df_test.to_parquet('../data/datasets/' + pipeline_id + '_test.parquet.gzip', compression='gzip')

    #
    # Normalize the columns in train/val/test dataframes. This is done as a preparation step for appllying
    # the sliding window technique, since the target variable is going to be used as lag feature.
    # (see, e.g., https://www.mikulskibartosz.name/forecasting-time-series-using-lag-features/)
    # (see also https://datascience.stackexchange.com/questions/72480/what-is-lag-in-time-series-forecasting)
    print('Normalizing the features in train/val/test dataframes.')
    _, target_name = util.get_relevant_variables(station_id)
    min_target_value_in_train, max_target_value_in_train = min(df_train[target_name]), max(df_train[target_name])
    min_target_value_in_val, max_target_value_in_val = min(df_val[target_name]), max(df_val[target_name])
    min_target_value_in_test, max_target_value_in_test = min(df_test[target_name]), max(df_test[target_name])
    df_train = util.min_max_normalize(df_train)
    df_val = util.min_max_normalize(df_val)
    df_test = util.min_max_normalize(df_test)

    #
    # Apply sliding windowing method to build examples (instances) of train/val/test datasets 
    print('Applying sliding window to build train/val/test datasets.')
    X_train, y_train, X_val, y_val, X_test, y_test = generate_windowed_split(
        df_train, df_val, df_test, target_name=target_name)
    print("Done! Resulting shapes:")
    print(f' - (X_train/X_val/X_test): ({X_train.shape}/{X_val.shape}/{X_test.shape})')
    print(f' - (y_train/y_val/y_test): ({y_train.shape}/{y_val.shape}/{y_test.shape})')

    #
    # Now, we restore the target variable to their original values. This is needed in case a multiclass
    # classification task is defined down the pipeline.
    print('Restoring the target variable to their original values.')
    y_train = (y_train + min_target_value_in_train) * (max_target_value_in_train - min_target_value_in_train)
    y_val = (y_val + min_target_value_in_val) * (max_target_value_in_val - min_target_value_in_val)
    y_test = (y_test + min_target_value_in_test) * (max_target_value_in_test - min_target_value_in_test)
    print('Min precipitation values (train/val/test): %.5f, %.5f, %.5f' %
          (np.min(y_train), np.min(y_val), np.min(y_test)))
    print('Max precipitation values (train/val/test): %.5f, %.5f, %.5f' %
          (np.max(y_train), np.max(y_val), np.max(y_test)))

    #
    # Subsampling

    print('**********Subsampling************')
    print(f'- Shapes before subsampling (Y_train/y_val/y_test): {y_train.shape}, {y_val.shape}, {y_test.shape}')

    print("Subsampling train data.")
    X_train, y_train = apply_subsampling(X_train, y_train, "NEGATIVE")
    print("Subsampling val data.")
    X_val, y_val = apply_subsampling(X_val, y_val, "NEGATIVE")
    # print("Subsampling test data.")
    # X_test, y_test = apply_naive_subsampling(X_test, y_test)

    print('- Min precipitation values (train/val/test) after subsampling: %.5f, %.5f, %.5f' %
          (np.min(y_train), np.min(y_val), np.min(y_test)))
    print('- Max precipitation values (train/val/test) after subsampling: %.5f, %.5f, %.5f' %
          (np.max(y_train), np.max(y_val), np.max(y_test)))
    print(f'- Shapes (y_train/y_val/y_test) after subsampling: {y_train.shape}, {y_val.shape}, {y_test.shape}')

    #
    # Write numpy arrays to a parquet file
    print(
        f'Number of examples (train/val/test): {len(X_train)}/{len(X_val)}/{len(X_test)}.')
    filename = '../data/datasets/' + pipeline_id + ".pickle"
    print(f'Dumping train/val/test np arrays to pickle file {filename}.', end = " ")
    file = open(filename, 'wb')
    ndarrays = (X_train, y_train, 
                X_val, y_val, 
                X_test, y_test)
    pickle.dump(ndarrays, file)
    print('Done!')

def main(argv):
    parser = argparse.ArgumentParser(
        description="""This script builds the train/val/test datasets from the user-specified data sources.""")
    parser.add_argument('-s', '--station_id', type=str, required=True, help='station id')
    parser.add_argument('-d', '--datasources', type=str, help='data source spec')
    parser.add_argument('-n', '--num_neighbors', type=int, default = 0, help='number of neighbors')
    args = parser.parse_args(argv[1:])

    station_id = args.station_id
    datasources = args.datasources
    num_neighbors = args.num_neighbors

    help_message = "Usage: {0} -s <station_id> -d <data_source_spec> -n <num_neighbors>".format(__file__)

    if not ((station_id in INMET_STATION_CODES_RJ) or (station_id in COR_STATION_NAMES_RJ)):
        print(f"Invalid station identifier: {station_id}")
        print(help_message)
        sys.exit(2)

    use_sounding_as_data_source = False
    use_NWP_model_as_data_source = False

    if datasources:
        if 'R' in datasources:
            use_sounding_as_data_source = True
        if 'N' in datasources:
            use_NWP_model_as_data_source = True

    assert(station_id is not None) and (station_id != "")
    build_datasets(station_id, use_sounding_as_data_source, use_NWP_model_as_data_source, num_neighbors=num_neighbors)

if __name__ == "__main__":
    main(sys.argv)
