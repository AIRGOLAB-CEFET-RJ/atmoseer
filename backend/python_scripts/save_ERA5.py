import cdsapi
from datetime import datetime, timedelta

c = cdsapi.Client()
current_date = datetime.now() - timedelta(days=5) #Os dados do ERA5 estão 5 dias atrasados
current_year = current_date.year
current_month = current_date.month
current_day = current_date.day
current_time = current_date.hour

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
            '200', '700', '1000'
        ],
        "year": [
            str(current_year)
        ],
        "month": [
            str(current_month)
        ],
        "day": [
            str(current_day)
        ],
        "time": [
            str(current_time) + ":00"
        ],
        "area": [
            -22,
            -44,
            -23,
            -42,
        ],
    },
    "file.nc",
)