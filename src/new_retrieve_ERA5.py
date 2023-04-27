import pandas as pd
import sys, getopt
from datetime import datetime
import time
import cdsapi
from pathlib import Path
import xarray as xr
import requests

"""
    For using the CDS API to download ERA-5 data consult: https://cds.climate.copernicus.eu/api-how-to
"""


def get_data(start_date, end_date):

    today = datetime.today()
    end_date = min([end_date, today.strftime("%Y")])

    file = "RJ_" + str(start_date) + "_" + str(end_date)

    file_exist = Path("../data/NWP/ERA5/" + file + ".nc")

    if file_exist.is_file():
        ds = xr.open_dataset("../data/NWP/ERA5/" + file + ".nc")
    else:
        c = cdsapi.Client()

        unsuccesfully_downloaded_probes = 0

        years = list(map(str, range(int(start_date), int(end_date) + 1)))
        for year in years:
            for pressure_level in ['200', '700', '1000']:
                print(f"Downloading pressure data at level {pressure_level}hPa for year {year}...", end="")
                try:
                    c.retrieve(
                        "reanalysis-era5-pressure-levels",
                        {
                            "product_type": "reanalysis",
                            "format": "netcdf",
                            "variable": [
                                "geopotential",
                                "relative_humidity",
                                "temperature",
                                "u_component_of_wind",
                                "v_component_of_wind",
                            ],
                            "pressure_level": [
                                pressure_level
                            ],
                            "year": [
                                year,
                            ],
                            "month": [
                                "01",
                                "02",
                                "03",
                                "04",
                                "05",
                                "06",
                                "07",
                                "08",
                                "09",
                                "10",
                                "11",
                                "12",
                            ],
                            "day": [
                                "01",
                                "02",
                                "03",
                                "04",
                                "05",
                                "06",
                                "07",
                                "08",
                                "09",
                                "10",
                                "11",
                                "12",
                                "13",
                                "14",
                                "15",
                                "16",
                                "17",
                                "18",
                                "19",
                                "20",
                                "21",
                                "22",
                                "23",
                                "24",
                                "25",
                                "26",
                                "27",
                                "28",
                                "29",
                                "30",
                                "31",
                            ],
                            "time": [
                                "00:00",
                                "01:00",
                                "02:00",
                                "03:00",
                                "04:00",
                                "05:00",
                                "06:00",
                                "07:00",
                                "08:00",
                                "09:00",
                                "10:00",
                                "11:00",
                                "12:00",
                                "13:00",
                                "14:00",
                                "15:00",
                                "16:00",
                                "17:00",
                                "18:00",
                                "19:00",
                                "20:00",
                                "21:00",
                                "22:00",
                                "23:00",
                            ],
                            "area": [
                                -22,
                                -44,
                                -23,
                                -42,
                            ],
                        },
                        "../data/NWP/ERA5/RJ_" + year + "_" + pressure_level + ".nc",
                    )
                    print("Done!")
                except Exception as e:
                    print(f"Unexpected error! {repr(e)}")
                    sys.exit(2)

        ds = None
        for year in years:
            for pressure_level in ['200', '700', '1000']:
                if ds == None:
                    ds = xr.open_dataset("../data/NWP/ERA5/RJ_" + year + "_" + pressure_level + ".nc")
                else:
                    ds_aux = xr.open_dataset("../data/NWP/ERA5/RJ_" + year + "_" + pressure_level +  + ".nc")
                    ds = ds.merge(ds_aux)

        print(f"Done! Number of unsuccesfully downloaded probes: {unsuccesfully_downloaded_probes}.")
        filename = "../data/NWP/ERA5/" + file + ".nc"
        print(f"Saving dowloaded data to {filename}")
        ds.to_netcdf(filename)


def main(argv):
    help_message = "Usage: {0} -b <start_year> -e <end_year>".format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hb:e:", ["help", "start_year=", "end_year="])
    except:
        print("Invalid arguments. Use -h or --help for more information.")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_message)
            sys.exit(2)
        elif opt in ("-b", "--start_date"):
            try:
                start_date = arg
            except ValueError:
                print("Invalid date format. Use -h or --help for more information.")
                sys.exit(2)
        elif opt in ("-e", "--end_date"):
            try:
                end_date = arg
            except ValueError:
                print("Invalid date format. Use -h or --help for more information.")
                sys.exit(2)

    assert start_date <= end_date

    get_data(start_date, end_date)


if __name__ == "__main__":
    main(sys.argv)
