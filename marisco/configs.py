# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/configs.ipynb.

# %% auto 0
__all__ = ['CFG_FNAME', 'CDL_FNAME', 'BASE_PATH', 'CONFIGS', 'CONFIGS_CDL', 'NETCDF_TO_PYTHON_TYPE', 'name2grp',
           'get_nc_tpl_path', 'get_cfgs', 'sanitize', 'get_lut', 'get_enum_dicts']

# %% ../nbs/api/configs.ipynb 2
from pathlib import Path
import re
from functools import partial

from .utils import read_toml, write_toml
import pandas as pd

import fastcore.all as fc

# %% ../nbs/api/configs.ipynb 4
CFG_FNAME = 'configs.toml'
CDL_FNAME = 'cdl.toml'

# %% ../nbs/api/configs.ipynb 5
BASE_PATH = Path.home() / '.marisco'

# %% ../nbs/api/configs.ipynb 8
CONFIGS = {
    'gh': {
        'owner': 'franckalbinet',
        'repo': 'marisco'
    },
    'names': {
        'nc_template': 'maris-template.nc'
    },
    'dirs': {
        'lut': str(BASE_PATH / 'lut'), # Look-up tables
        'tmp': str(BASE_PATH / 'tmp')
    },
    'paths': {
        'luts': 'nbs/files/lut'
    },
    'units': {
        'time': 'seconds since 1970-01-01 00:00:00.0'
    },
    'zotero': {
        'api_key': 'your-zotero-api-key',
        'lib_id': '2432820'
    }
}

# %% ../nbs/api/configs.ipynb 12
CONFIGS_CDL = { 
    'placeholder': '_to_be_filled_in_',
    'grps': {
        'sea': {
            'name': 'seawater'
        },
        'bio': {
            'name': 'biota'
        },
        'sed': {
            'name': 'sediment'
        },
        'sus': {
            'name': 'suspended-matter'
        }
    },
    'global_attrs': {
        'id': '', # zotero?
        'title': '',
        'summary': '',
        'keywords': '',
        'keywords_vocabulary': 'GCMD Science Keywords',
        'keywords_vocabulary_url': 'https://gcmd.earthdata.nasa.gov/static/kms/',
        'record': '',
        'featureType': '',
        'cdm_data_type': '',

        # Conventions
        'Conventions': 'CF-1.10 ACDD-1.3',

        # Publisher [ACDD1.3]
        'publisher_name': 'Paul MCGINNITY, Iolanda OSVATH, Florence DESCROIX-COMANDUCCI',
        'publisher_email': 'p.mc-ginnity@iaea.org, i.osvath@iaea.org, F.Descroix-Comanducci@iaea.org', 
        'publisher_url': 'https://maris.iaea.org',
        'publisher_institution': 'International Atomic Energy Agency - IAEA', 

        # Creator info [ACDD1.3]
        'creator_name': '',
        'institution': '',
        'metadata_link': '',
        'creator_email': '',
        'creator_url': '',
        'references': '',
        'license': ' '.join(['Without prejudice to the applicable Terms and Conditions', 
                             '(https://nucleus.iaea.org/Pages/Others/Disclaimer.aspx),',
                             'I hereby agree that any use of the data will contain appropriate',
                             'acknowledgement of the data source(s) and the IAEA Marine',
                             'Radioactivity Information System (MARIS).']),
        'comment': '',
        # Dataset info & coordinates [ACDD1.3]
        #'project': '', # Network long name
        #'platform': '', # Should be a long / full name
        'geospatial_lat_min': '', 
        'geospatial_lon_min': '',
        'geospatial_lat_max': '',
        'geospatial_lon_max': '',
        'geospatial_vertical_min': '',
        'geospatial_vertical_max': '',
        'geospatial_bounds': '', # wkt representation
        'geospatial_bounds_crs': 'EPSG:4326',

        # Time information
        'time_coverage_start': '',
        'time_coverage_end': '',
        #'time_coverage_resolution': '',
        'local_time_zone': '',
        'date_created': '',
        'date_modified': '',
        #
        # -- Additional metadata (custom to MARIS)
        #
        'publisher_postprocess_logs': ''
        },
    'dim': {
        'name': 'sample',
        'attrs': {
            'long_name': 'Sample ID of measurement'
        },
        'dtype': 'u8'
    },
    'vars': {    
        'defaults': {
            'lon': {
                'name': 'lon',
                'attrs': {
                    'long_name': 'Measurement longitude',
                    'standard_name': 'longitude',
                    'units': 'degrees_north',
                    'axis': 'Y',
                    '_CoordinateAxisType': 'Lon'
                },
                'dtype': 'f4'
            },
            'lat': {
                'name': 'lat',
                'attrs': {
                    'long_name': 'Measurement latitude',
                    'standard_name': 'latitude',
                    'units': 'degrees_east',
                    'axis': 'X',
                    '_CoordinateAxisType': 'Lat'
                },
                'dtype': 'f4'
            },
            'depth': {
                'name': 'depth',
                'attrs': {
                    'long_name': 'Depth below seal level',
                    'standard_name': 'depth_below_sea_floor',
                    'units': 'm',
                    'axis': 'Z'
                },
                'dtype': 'f4'
            },
            'time': {
                'name': 'time',
                'attrs': {
                    'long_name': 'Time of measurement',
                    'standard_name': 'time',
                    'units': 'seconds since 1970-01-01 00:00:00.0',
                    'time_origin': '1970-01-01 00:00:00',
                    'time_zone': 'UTC',
                    'abbreviation': 'Date/Time',
                    'axis': 'T',
                    'calendar': 'gregorian'
                },
                'dtype': 'u8',
            },
        },
        'bio': {
            'bio_group': {
                'name': 'bio_group',
                'attrs': {
                    'long_name': 'Biota group',
                    'standard_name': 'biota_group_tbd'
                },
                'dtype': 'bio_group_t'
                # 'dtype': 'f4'
            },
            'species_id': {
                'name': 'species_id',
                'attrs': {  
                    'long_name': 'Species ID',
                    'standard_name': 'AphiaID'
                },
                'dtype': 'species_t'
            },
            'body_part': {
                'name': 'body_part',
                'attrs': {
                    'long_name': 'Body part',
                    'standard_name': 'body_part_tbd'
                },
                'dtype': 'body_part_t' 
            }
        },
        'sed': {
            'sed_type': {
                'name': 'sed_type',
                'attrs': {
                    'long_name': 'Sediment type',
                    'standard_name': 'sediment_type_tbd'
                },
                'dtype': 'sed_type_t'
            }
        },
        'suffixes':  {
            'uncertainty': {
                'name': '_unc',
                'attrs': {
                    'long_name': ' uncertainty',
                    'standard_name': '_uncertainty'
                },
                'dtype': 'f4'
            },
            'detection_limit': {
                'name': '_dl',
                'attrs': {
                    'long_name': ' detection limit',
                    'standard_name': '_detection_limit'
                },
                'dtype': 'f4'
            },
            'volume': {
                'name': '_vol',
                'attrs': {
                    'long_name': ' volume',
                    'standard_name': '_volume'
                },
                'dtype': 'f4'
            },
            'filtered': {
                'name': '_filt',
                'attrs': {
                    'long_name': ' filtered',
                    'standard_name': '_filtered'
                },
                'dtype': 'f4'
            },
            'counting_method': {
                'name': '_counmet',
                'attrs': {
                    'long_name': ' counting method',
                    'standard_name': '_counting_method'
                },
                'dtype': 'f4'
            },
            'unit': {
                'name': '_unit',
                'attrs': {
                    'long_name': ' unit',
                    'standard_name': '_unit'
                },
                'dtype': 'f4'
            }
        }
    },
    'enums': [
        {
            'name': 'bio_group_t', 
            'fname': 'dbo_biogroup.xlsx', 
            'key': 'biogroup', 
            'value':'biogroup_id'
        },
        {
            'name': 'body_part_t', 
            'fname': 'dbo_bodypar.xlsx', 
            'key': 'bodypar', 
            'value':'bodypar_id'
        },
        {
            'name': 'species_t', 
            'fname': 'dbo_species.xlsx', 
            'key': 'species', 
            'value':'species_id'
        },
        {
            'name': 'sed_type_t', 
            'fname': 'dbo_sedtype.xlsx', 
            'key': 'sedtype', 
            'value':'sedtype_id'
        },
        {
            'name': 'dl_type_t', 
            'fname': 'dbo_detection.xlsx', 
            'key': 'detection_name', 
            'value':'detection_id'
        }
        ]
}

# %% ../nbs/api/configs.ipynb 16
NETCDF_TO_PYTHON_TYPE = {
    'u8': int,
    'f4': float
    }

# %% ../nbs/api/configs.ipynb 17
def name2grp(
    name:str, # Name of the group
    cdl_name:Path = BASE_PATH / CDL_FNAME, # Path to `cdl.toml` file 
    ):
    # Reverse `cdl.toml` config group dict so that group config key can be retrieve based on its name
    cfg = read_toml(cdl_name)['grps']
    return {v['name']:k  for k, v in cfg.items()}[name]

# %% ../nbs/api/configs.ipynb 20
def get_nc_tpl_path():
    "Return the name of the MARIS NetCDF template as defined in `configs.toml`"
    return BASE_PATH / read_toml(BASE_PATH / 'configs.toml')['names']['nc_template']

# %% ../nbs/api/configs.ipynb 22
def get_cfgs(
    key:str=None # `configs.toml` key of interest
    ) -> dict: # `configs.toml` file as dictionary
    "Lookup specific or all `configs.toml` properties."
    cfgs = read_toml(BASE_PATH / 'configs.toml')
    return cfgs if key is None else cfgs[key]

# %% ../nbs/api/configs.ipynb 25
def sanitize(s:str # String to sanitize
             ) -> str:
    """
    Sanitize dictionary key to comply with NetCDF enumeration type: 
    
        - remove `(`, `)`, `.`, `/`, `-`  
        - strip the string
    """
    s = re.sub(r'[().]', '', s)
    return re.sub(r'[/-]', ' ', s).strip() 

# %% ../nbs/api/configs.ipynb 29
def get_lut(src_dir:str, # Directory containing lookup tables
            fname:str, # Excel file lookup table name
            key:str, # Excel file column name to be used as dict keys 
            value:str, # Excel file column name to be used as dict values 
            do_sanitize:bool=True # Sanitization required?
            ) -> dict: # MARIS lookup table
    "Convert MARIS db lookup table excel file to dictionary `{'name': id, ...}`."
    fname = Path(src_dir) / fname
    lut = pd.read_excel(fname, index_col=key, usecols=[key, value])[value].to_dict()
    if do_sanitize:
        lut = {sanitize(k): v for k, v in lut.items()}
    return lut

# %% ../nbs/api/configs.ipynb 33
def get_enum_dicts(
    lut_src_dir:str = get_cfgs()['dirs']['lut'], # Directory containing lookup tables
    cdl_name:Path = BASE_PATH / CDL_FNAME, # Path to `cdl.toml` file
    ):
    "Return a dict of NetCDF enumeration types."
    enums_cfg = read_toml(cdl_name)['enums']
    enum_types = {}
    for enum in enums_cfg:
        name, fname, key, value = enum.values()
        lut = get_lut(lut_src_dir, fname, key=key, value=value)
        enum_types[name] = lut
        
    return enum_types
