'''
This script merges the train/val/test datasets from two or more user-specified weather stations
'''

import argparse
from globals import *
import sys
import pickle
import numpy as np

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

    # Parse the arguments
    args = parser.parse_args()

    # Access the list of identifiers
    soi_pipeline_id = args.pipeline_id
    soi_id = args.station_id
    identifiers = args.identifiers

    help_message = "Usage: {0} -s <station_id> -d <data_source_spec> -n <num_neighbors>".format(__file__)

    if not ((soi_id in INMET_STATION_CODES_RJ) or (soi_id in COR_STATION_NAMES_RJ)):
        print(f"Invalid station identifier: {soi_id}")
        print(help_message)
        sys.exit(2)

    #
    # Load numpy arrays (stored in a pickle file) for the SoI (station of interest).
    filename = "../data/datasets/" + soi_pipeline_id + ".pickle"
    print(f"Loading train/val/test datasets from {filename}.")
    file = open(filename, 'rb')
    (X_train, y_train, X_val, y_val, X_test, y_test) = pickle.load(file)
    print(f"Shapes of train/val/test data matrices: {X_train.shape}/{X_val.shape}/{X_test.shape}")
    print(f"Min values of train/val/test data matrices: {min(X_train.reshape(-1,1))}/{min(X_val.reshape(-1,1))}/{min(X_test.reshape(-1,1))}")
    print(f"Max values of train/val/test data matrices: {max(X_train.reshape(-1,1))}/{max(X_val.reshape(-1,1))}/{max(X_test.reshape(-1,1))}")

    merged_X_train = X_train
    merged_y_train = y_train
    merged_X_val = X_val
    merged_y_val = y_val
    
    for ws_id in identifiers:
        print(f"Merging data from weather station {ws_id}...", end="")

        pipeline_id = soi_pipeline_id.replace(soi_id, ws_id)
        filename = "../data/datasets/" + pipeline_id + ".pickle"
        print(f"Loading train/val/test datasets from {filename}.")
        file = open(filename, 'rb')

        (X_train, y_train, X_val, y_val, X_test, y_test) = pickle.load(file)

        merged_X_train = np.concatenate((merged_X_train, X_train))
        merged_y_train = np.concatenate((merged_y_train, y_train))
        merged_X_val = np.concatenate((merged_X_val, X_val))
        merged_y_val = np.concatenate((merged_y_val, y_val))

    #
    # Write resulting merged numpy arrays for train/val/test datasets to a single pickle file
    print(f'Number of examples (train/val/test): {len(merged_X_train)}/{len(merged_X_val)}/{len(X_test)}.')
    merge_list = "_".join(identifiers)
    filename = '../data/datasets/' + soi_pipeline_id + "_" + merge_list + ".pickle"
    print(f'Dumping merged train/val/test np arrays to pickle file {filename}.', end = " ")
    file = open(filename, 'wb')
    ndarrays = (merged_X_train, merged_y_train, 
                merged_X_val, merged_y_val, 
                X_test, y_test)
    pickle.dump(ndarrays, file)
    print('Done!')

if __name__ == "__main__":
    main(sys.argv)
