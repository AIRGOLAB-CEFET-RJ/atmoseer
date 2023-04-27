# SUBSAMPLING_KEEP_RATIO = 0.1
# Number of examples (train/val/test): 13360/3441/1793.

# SUBSAMPLING_KEEP_RATIO = 0.01
# Number of examples (train/val/test): 7649/1753/969.

API_BASE_URL = "https://apitempo.inmet.gov.br"

# see https://portal.inmet.gov.br/paginas/catalogoaut
INMET_STATION_CODES_RJ = ('A636', 
                          'A621', 
                          'A602', 
                          'A652')

COR_STATION_NAMES_RJ = ('alto_da_boa_vista',
                        'guaratiba',
                        'iraja',
                        'jardim_botanico',
                        'riocentro',
                        'santa_cruz',
                        'sao_cristovao',
                        'vidigal')

TIME_WINDOW_SIZE = 6

# Observed variables for INMET weather stations:
# ,DC_NOME,
# PRE_INS,
# TEM_SEN,
# VL_LATITUDE,
# PRE_MAX,UF,
# RAD_GLO,
# PTO_INS,
# TEM_MIN,
# VL_LONGITUDE,
# UMD_MIN,
# PTO_MAX,
# VEN_DIR,
# DT_MEDICAO,
# CHUVA,
# PRE_MIN,
# UMD_MAX,
# VEN_VEL,
# PTO_MIN,
# TEM_MAX,
# TEN_BAT,
# VEN_RAJ,
# TEM_CPU,
# TEM_INS,
# UMD_INS,
# CD_ESTACAO,
# HR_MEDICAO