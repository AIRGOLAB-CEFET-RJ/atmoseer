import sys
from datetime import datetime
import time
import cdsapi
from pathlib import Path
import xarray as xr
import argparse
import sys
from enum import Enum
import globals as globals

"""
    For using the CDS API to download ERA-5 data consult: https://cds.climate.copernicus.eu/api-how-to
"""

# North -22°, West -44°, South -23°, East -42°
REGION_OF_INTEREST = [-22, -44, -23, -42]

class Months(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

def get_data(start_year, end_year):

    end_year = min([end_year, datetime.today().year])

    file = "RJ_" + str(start_year) + "_" + str(end_year)

    file_exist = Path(globals.NWP_DATA_DIR + "ERA5/" + file + ".nc")

    months = range(Months.JANUARY.value, Months.DECEMBER.value+1)

    if file_exist.is_file():
        ds = xr.open_dataset(globals.NWP_DATA_DIR + "ERA5/" + file + ".nc")
    else:
        c = cdsapi.Client()
        years = list(map(str, range(int(start_year), int(end_year) + 1)))
        for year in years:
            for month in months:
                print(f"Downloading ERA5 data at month {month} of year {year}...", end="")
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
                                "v_component_of_wind"
                            ],
                            "pressure_level": [
                                '200', '700', '1000'
                            ],
                            "year": [
                                year,
                            ],
                            "month": [
                                str(month)
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
                            "area": REGION_OF_INTEREST,
                        },
                        globals.NWP_DATA_DIR + "ERA5/RJ_" + year + "_" + str(month) + ".nc",
                    )
                    print("Done!")
                except Exception as e:
                    print(f"Unexpected error! {repr(e)}")
                    sys.exit(2)

        ds = None
        for year in years:
            for month in months:
                if ds is None:
                    ds = xr.open_dataset(globals.NWP_DATA_DIR + "ERA5/RJ_" + year + "_" + str(month) + ".nc")
                else:
                    ds_aux = xr.open_dataset(globals.NWP_DATA_DIR + "ERA5/RJ_" + year + "_" + str(month) + ".nc")
                    ds = ds.merge(ds_aux)

        print(f"Done!", end="")
        filename = globals.NWP_DATA_DIR + "ERA5/" + file + ".nc"
        print(f"Saving dowloaded data to {filename}")
        ds.to_netcdf(filename)

def main(argv):
    parser = argparse.ArgumentParser(description='Retrieve ERA5 data between two given years.')
    parser.add_argument('-b', '--start_year', type=int, required=True, help='Start year')
    parser.add_argument('-e', '--end_year', type=int, required=True, help='End year')

    args = parser.parse_args(argv[1:])

    start_year = args.start_year
    end_year = args.end_year

    # ERA5 data goes back to the year 1940. 
    # see https://cds.climate.copernicus.eu/cdsapp#!/dataset/reanalysis-era5-pressure-levels?tab=overview
    assert start_year >= 1940 

    assert start_year <= end_year

    get_data(start_year, end_year)

if __name__ == "__main__":
    main(sys.argv)

