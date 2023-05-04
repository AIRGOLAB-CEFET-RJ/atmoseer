'''
This script merges the train/val/test datasets from two or more user-specified weather stations
'''

import argparse
from globals import *
import sys
import pickle
import numpy as np
import pandas as pd
from util import haversine_distance

def get_pos_class_ratio(y):
    pos_examples_idxs = np.where(y > 0)[0]
    return len(pos_examples_idxs)/len(y)

def main(argv):
    parser = argparse.ArgumentParser(
        description="""This script builds the train/val/test datasets for a given weather station, 
        by using the user-specified data sources.""", prog=sys.argv[0])
    # Add an argument to accept the station of interest
    parser.add_argument('-s', '--station_id', type=str, required=True, help='id for station of interest')
    # Add an argument to accept the pipeline identifier
    parser.add_argument('-p', '--pipeline_id', type=str, required=True, help='one or more weather station identifiers')
    # Add an argument to accept one or more identifiers
    parser.add_argument('-i', '--identifiers', type=str, nargs='+', help='IDs of one or more weather stations to merge.')

    use_only_pos_examples = False

    # Parse the arguments
    args = parser.parse_args()

    # Access the list of identifiers
    soi_pipeline_id = args.pipeline_id
    soi_id = args.station_id
    identifiers = args.identifiers

    if not ((soi_id in INMET_STATION_CODES_RJ) or (soi_id in COR_STATION_NAMES_RJ)):
        print(f"Invalid station identifier: {soi_id}")
        parser.print_help()
        sys.exit(2)

    #
    # Load numpy arrays (stored in a pickle file) for the WSoI (weather station of interest).
    filename = DATASETS_DIR + soi_pipeline_id + ".pickle"
    print(f"Loading train/val/test datasets from {filename} for WSoI.")
    file = open(filename, 'rb')
    (X_train, y_train, X_val, y_val, X_test, y_test) = pickle.load(file)
    print(f'Number of examples (train/val/test): {len(X_train)}/{len(X_val)}/{len(X_test)}.')
    print(f"Min values of train/val/test data matrices: {min(X_train.reshape(-1,1))}/{min(X_val.reshape(-1,1))}/{min(X_test.reshape(-1,1))}")
    print(f"Max values in the train/val/test data matrices: {max(X_train.reshape(-1,1))}/{max(X_val.reshape(-1,1))}/{max(X_test.reshape(-1,1))}")
    print(F"Ratio of pos examples in the training set: {get_pos_class_ratio(y_train):.2f}")
    print()
    
    merged_X_train = X_train
    merged_y_train = y_train
    merged_X_val = X_val
    merged_y_val = y_val
    merged_X_test = X_test
    merged_y_test = y_test
    
    df_stations = pd.read_csv("../data/ws/INMET_WS_Stations.csv")
    row = df_stations[df_stations["STATION_ID"] == soi_id].iloc[0]
    soi_lat_long = (row["VL_LATITUDE"], row["VL_LONGITUDE"])

    for ws_id in identifiers:
        print(f"Merging data from weather station {ws_id}...", end="")

        row = df_stations[df_stations["STATION_ID"] == ws_id].iloc[0]
        station_lat_long = (row["VL_LATITUDE"], row["VL_LONGITUDE"])
        dist = haversine_distance(station_lat_long, soi_lat_long)
        print(f"Distance from station of interest is {dist:.2f} Km.")

        pipeline_id = soi_pipeline_id.replace(soi_id, ws_id)
        filename = DATASETS_DIR + pipeline_id + ".pickle"
        print(f"Loading train/val/test datasets from {filename}.")
        file = open(filename, 'rb')

        (X_train, y_train, X_val, y_val, X_test, y_test) = pickle.load(file)
        print(f'Number of examples (train/val/test): {len(X_train)}/{len(X_val)}/{len(X_test)}.')
        print(f"Min values of train/val/test data matrices: {min(X_train.reshape(-1,1))}/{min(X_val.reshape(-1,1))}/{min(X_test.reshape(-1,1))}")
        print(f"Max values of train/val/test data matrices: {max(X_train.reshape(-1,1))}/{max(X_val.reshape(-1,1))}/{max(X_test.reshape(-1,1))}")
        print(F"Ratio of pos examples in the training set: {get_pos_class_ratio(y_train):.2f}")


        if use_only_pos_examples:
            y_train_gt_zero_idxs = np.where(y_train > 0)[0]
            X_train = X_train[y_train_gt_zero_idxs]
            y_train = y_train[y_train_gt_zero_idxs]
            
            y_val_gt_zero_idxs = np.where(y_val > 0)[0]
            X_val = X_val[y_val_gt_zero_idxs]
            y_val = y_val[y_val_gt_zero_idxs]

            merged_X_train = np.concatenate((merged_X_train, X_train))
            merged_y_train = np.concatenate((merged_y_train, y_train))
            merged_X_val = np.concatenate((merged_X_val, X_val))
            merged_y_val = np.concatenate((merged_y_val, y_val))

            print(f'Number of posisitve examples (train/val): {len(X_train)}/{len(X_val)}.')
        else:
            merged_X_train = np.concatenate((merged_X_train, X_train))
            merged_y_train = np.concatenate((merged_y_train, y_train))
            merged_X_val = np.concatenate((merged_X_val, X_val))
            merged_y_val = np.concatenate((merged_y_val, y_val))

        print()

    #
    # Write resulting merged numpy arrays for train/val/test datasets to a single pickle file
    print(f'Number of examples in the merged datasets (train/val/test): {len(merged_X_train)}/{len(merged_X_val)}/{len(merged_X_test)}.')
    print(F"Ratio of pos examples in the merged training set: {get_pos_class_ratio(merged_y_train):.2f}")
    merge_list = "_".join(identifiers)
    filename = DATASETS_DIR + soi_pipeline_id + "_" + merge_list + ".pickle"
    print(f'Dumping merged train/val/test np arrays to pickle file {filename}.', end = " ")
    file = open(filename, 'wb')
    ndarrays = (merged_X_train, merged_y_train, 
                merged_X_val, merged_y_val, 
                merged_X_test, merged_y_test)
    pickle.dump(ndarrays, file)
    print('Done!')

if __name__ == "__main__":
    main(sys.argv)
