# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/configs.ipynb.

# %% auto 0
__all__ = ['BASE_PATH', 'CONFIGS', 'CONFIGS_CDL', 'name2grp', 'get_nc_tpl_path', 'get_cfgs']

# %% ../nbs/api/configs.ipynb 1
from pathlib import Path
from .utils import read_toml, write_toml

# %% ../nbs/api/configs.ipynb 2
BASE_PATH = Path.home() / '.marisco'

# %% ../nbs/api/configs.ipynb 3
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

# %% ../nbs/api/configs.ipynb 4
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
        'dtype': 'i4'
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
                #'dtype': BIO_GROUP_TYPE
                #'dtype': 'bio_group_t'
                'dtype': 'f4'
            },
            'species_id': {
                'name': 'species_id',
                'attrs': {  
                    'long_name': 'Species ID',
                    'standard_name': 'AphiaID'
                },
                'dtype': 'u8'
            },
            'body_part': {
                'name': 'body_part',
                'attrs': {
                    'long_name': 'Body part',
                    'standard_name': 'body_part_tbd'
                },
                #'dtype': BODY_PART_TYPE
                'dtype': 'f4'
                
            }
        },
        'sed': {
            'sed_type': {
                'name': 'sed_type',
                'attrs': {
                    'long_name': 'Sediment type',
                    'standard_name': 'sediment_type_tbd'
                },
                #'dtype': SED_TYPE
                'dtype': 'f4'
            }
        },
        'suffixes':  {
            'uncertainty': {
                'name': '_unc',
                'attrs': {
                    'long_name': ' uncertainty',
                    'standard_name': '_uncertainty'
                }
            },
            'detection_limit': {
                'name': '_dl',
                'attrs': {
                    'long_name': ' detection limit',
                    'standard_name': '_detection_limit'
                }
            }
        }
    }
}

# %% ../nbs/api/configs.ipynb 5
name2grp = lambda x: {v['name']:k  for k, v in CONFIGS_CDL['grps'].items()}[x]

# %% ../nbs/api/configs.ipynb 6
def get_nc_tpl_path():
    return BASE_PATH / read_toml(BASE_PATH / 'configs.toml')['names']['nc_template']

# %% ../nbs/api/configs.ipynb 8
def get_cfgs(key=None):
    cfgs = read_toml(BASE_PATH / 'configs.toml')
    return cfgs if key is None else cfgs[key]
