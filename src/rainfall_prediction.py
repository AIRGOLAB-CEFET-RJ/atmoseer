import numpy as np
from enum import Enum
from sklearn.preprocessing import OneHotEncoder

class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class PredictionTask(ExtendedEnum):
    REGRESSION = 'REGRESSION'
    ORDINAL_CLASSIFICATION = 'ORDINAL_CLASSIFICATION'
    BINARY_CLASSIFICATION = 'BINARY_CLASSIFICATION'

class DichotomousRainfallLevel(Enum):
    NO_RAIN = 0
    RAIN = 1

class RainfallLevel(Enum):
    NONE = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    EXTREME = 4


def ordinal_encoding(x):
    if x == RainfallLevel.NONE.value:
        return np.array([1, 0, 0, 0, 0])
    elif x == RainfallLevel.WEAK.value:
        return np.array([1, 1, 0, 0, 0])
    elif x == RainfallLevel.MODERATE.value:
        return np.array([1, 1, 1, 0, 0])
    elif x == RainfallLevel.STRONG.value:
        return np.array([1, 1, 1, 1, 0])
    elif x == RainfallLevel.EXTREME.value:
        return np.array([1, 1, 1, 1, 1])


def onehotencoding_to_binarylabels(one_hot_array):
    """
    Converts a numpy array of binary one-hot-encoded values to their corresponding labels.

    For example:
    one_hot_array = np.array([[1, 0], [0, 1], [0, 1]])
    binary_labels = onehotencoding_to_binarylabels(one_hot_array)
    print(binary_labels)

    This will output:
    [0, 1, 1]
    """
    binary_labels = []
    for row in one_hot_array:
        binary_labels.append(np.argmax(row))
    return binary_labels

def ordinalencoding_to_multiclasslabels(pred: np.ndarray):
    """
    Convert ordinal predictions to class labels, e.g.

    [0.9, 0.1, 0.1, 0.1] -> 0
    [0.9, 0.9, 0.1, 0.1] -> 1
    [0.9, 0.9, 0.9, 0.1] -> 2
    etc.
    """
    return (pred > 0.5).cumprod(axis=1).sum(axis=1) - 1


# def precipitationvalues_to_binaryonehotencoding(y):
#     y_levels = map_to_binary_precipitation_levels(y)

#     # Create an instance of the OneHotEncoder class
#     encoder = OneHotEncoder()

#     # Fit and transform the reshaped array using the encoder
#     one_hot_encoded_y = encoder.fit_transform(y_levels)

#     # Convert the one hot encoded array to a numpy array
#     one_hot_encoded_y = one_hot_encoded_y.toarray()

#     return one_hot_encoded_y

def precipitationvalues_to_binary_encoding(y):
    return map_to_binary_precipitation_levels(y)

def precipitationvalues_to_ordinalencoding(y):
    # none, weak, moderate, strong, extreme = get_events_per_precipitation_level(y)
    # y_class = np.zeros_like(y)
    # y_class[none] = RainfallLevel.NONE
    # y_class[weak] = RainfallLevel.WEAK
    # y_class[moderate] = RainfallLevel.MODERATE
    # y_class[strong] = RainfallLevel.STRONG
    # y_class[extreme] = RainfallLevel.EXTREME

    y_levels = map_to_precipitation_levels(y)
    y = np.array(list(map(ordinal_encoding, y_levels)))
    return y


def get_events_per_precipitation_level(y):
    # see http://alertario.rio.rj.gov.br/previsao-do-tempo/termosmet/
    no_rain = np.where(np.any(y <= 0., axis=1))
    weak_rain = np.where(np.any((y > 0.) & (y <= 5.), axis=1))
    moderate_rain = np.where(np.any((y > 5.) & (y <= 25.), axis=1))
    strong_rain = np.where(np.any((y > 25.) & (y <= 50.), axis=1))
    extreme_rain = np.where(np.any(y > 50., axis=1))
    return no_rain, weak_rain, moderate_rain, strong_rain, extreme_rain


def map_to_binary_precipitation_levels(y):
    none_idx, weak_idx, moderate_idx, strong_idx, extreme_idx = get_events_per_precipitation_level(y)
    y_levels = np.zeros_like(y)
    y_levels[none_idx] = DichotomousRainfallLevel.NO_RAIN.value
    y_levels[weak_idx] = y_levels[strong_idx] = y_levels[moderate_idx] = y_levels[extreme_idx] = DichotomousRainfallLevel.RAIN.value
    return y_levels


def map_to_precipitation_levels(y):
    none_idx, weak_idx, moderate_idx, strong_idx, extreme_idx = get_events_per_precipitation_level(y)
    y_levels = np.zeros_like(y)
    y_levels[none_idx] = RainfallLevel.NONE.value
    y_levels[weak_idx] = RainfallLevel.WEAK.value
    y_levels[strong_idx] = RainfallLevel.STRONG.value
    y_levels[moderate_idx] = RainfallLevel.MODERATE.value
    y_levels[extreme_idx] = RainfallLevel.EXTREME.value
    return y_levels
