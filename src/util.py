import pytz
from datetime import datetime, timedelta
import os
from metpy.calc import wind_components
from metpy.units import units
import numpy as np
import pandas as pd
from globals import *
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(point1, point2):
    """
    Calculates the Haversine distance between two points on the Earth's surface
    using their latitudes and longitudes.

    Parameters
    ----------
    point1 : tuple
        A tuple of two floats representing the latitude and longitude of the first point.
    point2 : tuple
        A tuple of two floats representing the latitude and longitude of the second point.

    Returns
    -------
    distance : float
        The Haversine distance between the two points, in kilometers.

    References
    ----------
    - Haversine formula: https://en.wikipedia.org/wiki/Haversine_formula
    - Earth's radius: https://en.wikipedia.org/wiki/Earth_radius

    """
    R = 6371  # Earth's radius in kilometers
    lat1, lon1 = point1
    lat2, lon2 = point2
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

def get_first_and_last_days_of_year(year: int):
    '''
    This  function takes a year as input and returns the first and last days of that year as datetime objects
    '''
    assert(year <= datetime.now().year)

    # Create datetime object for January 1 of the year
    first_day = datetime(year, 1, 1)

    # Calculate the last day of the year as January 1 of the following year minus one day
    last_day = datetime(year + 1, 1, 1) - timedelta(days=1)

    if year == datetime.now().year:
        last_day = min(last_day, datetime.now().today())

    return first_day, last_day

def min_max_normalize(df: pd.DataFrame):
    df = (df - df.min()) / (df.max() - df.min())
    return df

def is_posintstring(s):
    try:
        temp = int(s)
        if temp > 0:
            return True
        else:
            return False
    except ValueError:
        return False

def format_time(input_str):
    '''
    This function first converts the input string to an integer using the int function. 
    It then extracts the hours and minutes from the input integer using integer division and modulus operations. 
    Finally, it formats the output string using f-strings to ensure that both hours and minutes are represented with two digits.
    Usage examples:
        print(format_time("100"))   # Output: "01:00"
        print(format_time("1200"))  # Output: "12:00"
        print(format_time("2300"))  # Output: "23:00"
    '''
    # Convert input string to integer
    input_int = int(input_str)
    
    # Extract hours and minutes from the input integer
    hours = input_int // 100
    minutes = input_int % 100
    
    # Format the output string
    output_str = f"{hours:02}:{minutes:02}"
    
    return output_str

def utc_to_local_DEPRECATED(utc_string, local_tz, format_string):
    '''
    This function first converts the UTC string to a datetime object with timezone information 
    using strptime() and replace(). Then it converts the datetime object to the local timezone 
    using astimezone(). Finally, it formats the resulting datetime as a string in the same
    format as the input string.

    Here's an example usage of the function:
    
        utc_string = '1972-09-13 12:00:00'
        local_tz = 'America/Sao_Paulo'
        format_string = '%Y-%m-%d %H:%M'
        local_string = utc_to_local(utc_string, local_tz, format_string)
        print(local_string)

    '''
    # convert utc string to datetime object
    utc_dt = datetime.strptime(utc_string, format_string).replace(tzinfo=pytz.UTC)
    
    # convert to local timezone
    local_tz = pytz.timezone(local_tz)
    local_dt = utc_dt.astimezone(local_tz)
    
    # format as string and return
    return local_dt.strftime(format_string)

def transform_wind(wind_speed, wind_direction, comp_idx):
    """
    This function calculates either the U or V wind vector component from the speed and direction.
    comp_idx = 0 --> computes the U component
    comp_idx = 1 --> computes the V component
    (see https://unidata.github.io/MetPy/latest/api/generated/metpy.calc.wind_components.html)
    """
    assert(comp_idx == 0 or comp_idx == 1)
    return wind_components(wind_speed * units('m/s'), wind_direction * units.deg)[comp_idx].magnitude

def add_datetime_index(station_id, df):
    timestamp = None
    if station_id in INMET_STATION_CODES_RJ:
        df.HR_MEDICAO = df.HR_MEDICAO.apply(format_time) # e.g., 1800 --> 18:00
        timestamp = pd.to_datetime(df.DT_MEDICAO + ' ' + df.HR_MEDICAO)
    elif station_id in COR_STATION_NAMES_RJ:
        timestamp = pd.to_datetime(df.Dia + ' ' + df.Hora)
    assert timestamp is not None
    df = df.set_index(pd.DatetimeIndex(timestamp))
    return df

def add_wind_related_features(station_id, df):
    if station_id in INMET_STATION_CODES_RJ:
        df['wind_u'] = df.apply(lambda x: transform_wind(x.VEN_VEL, x.VEN_DIR, 0),axis=1)
        df['wind_v'] = df.apply(lambda x: transform_wind(x.VEN_VEL, x.VEN_DIR, 1),axis=1)
    elif station_id in COR_STATION_NAMES_RJ:
        df['wind_u'] = df.apply(lambda x: transform_wind(x.VelVento, x.DirVento, 0),axis=1)
        df['wind_v'] = df.apply(lambda x: transform_wind(x.VelVento, x.DirVento, 1),axis=1)
    return df

def add_hour_related_features(df):
    """
    Transforms a DataFrame's datetime index into two new columns representing the hour in sin and cosine form.
    (see https://datascience.stackexchange.com/questions/5990/what-is-a-good-way-to-transform-cyclic-ordinal-attributes)

    Args:
    - df: A pandas DataFrame with a datetime index.

    Returns:
    - The input pandas DataFrame with two new columns named 'hour_sin' and 'hour_cos' representing the hour in sin and cosine form.
    """
    dt = df.index
    hourfloat = dt.hour + dt.minute/60.0
    df['hour_sin'] = np.sin(2. * np.pi * hourfloat/24.)
    df['hour_cos'] = np.cos(2. * np.pi * hourfloat/24.)
    return df

def get_filename_and_extension(filename):
    """
    Given a filename, returns a tuple with the base filename and extension.
    """
    basename = os.path.basename(filename)
    filename_parts = os.path.splitext(basename)
    return filename_parts

def find_contiguous_observation_blocks(df: pd.DataFrame):
    """
    Given a list of timestamps, finds contiguous blocks of timestamps that are exactly one hour apart of each other.

    Args:
    - timestamp_range: A list-like object of pandas Timestamps.

    Yields:
    - A tuple representing a contiguous block of timestamps: (start, end).

    Usage example:
    >>> period_under_study = df['2007-05-18':'2007-05-31']
    >>> contiguous_observations = list(find_contiguous_observation_blocks(period_under_study))
    >>> print(len(contiguous_observations))
    >>> print(contiguous_observations)
    5
    [(Timestamp('2007-05-18 18:00:00'), Timestamp('2007-05-18 19:00:00')), 
     (Timestamp('2007-05-19 11:00:00'), Timestamp('2007-05-19 13:00:00')), 
     (Timestamp('2007-05-20 12:00:00'), Timestamp('2007-05-21 00:00:00')), 
     (Timestamp('2007-05-21 02:00:00'), Timestamp('2007-05-21 08:00:00')), 
     (Timestamp('2007-05-21 10:00:00'), Timestamp('2007-05-31 23:00:00'))]

    In this example, `timestamp_range` is a list of pandas Timestamps extracted from a DataFrame's 'Datetime' index.
    The function finds contiguous blocks of timestamps that are exactly one hour apart, and yields tuples representing these blocks.
    The `yield` statement produces a generator object, which can be converted to a list using the `list()` function.

    Returns:
    - None
    """
    timestamp_range = df.index
    assert (len(timestamp_range) > 1)
    first = last = timestamp_range[0]
    for n in timestamp_range[1:]:
        previous = n - timedelta(hours=1, minutes=0)
        if previous == last: # Part of the current block, bump the end
            last = n
        else: # Not part of the current block; yield current block and start a new one
            yield first, last
            first = last = n
    yield first, last # Yield the last block

def get_relevant_variables(station_id):
    if station_id in INMET_STATION_CODES_RJ:
        return ['TEM_MAX', 'PRE_MAX', 'UMD_MAX', 'wind_u', 'wind_v', 'hour_sin', 'hour_cos'], 'CHUVA'
    elif station_id in COR_STATION_NAMES_RJ:
        return ['Temperatura', 'Pressao', 'Umidade', 'wind_u', 'wind_v', 'hour_sin', 'hour_cos'], 'Chuva'
    return None
