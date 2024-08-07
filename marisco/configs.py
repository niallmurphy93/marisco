# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/configs.ipynb.

# %% auto 0
__all__ = ['CFG_FNAME', 'CDL_FNAME', 'NUCLIDE_LOOKUP_FNAME', 'MARISCO_CFG_DIRNAME', 'CONFIGS', 'CONFIGS_CDL',
           'NETCDF_TO_PYTHON_TYPE', 'base_path', 'cfg', 'nuc_lut_path', 'lut_path', 'cache_path', 'cdl_cfg',
           'species_lut_path', 'bodyparts_lut_path', 'biogroup_lut_path', 'sediments_lut_path', 'unit_lut_path',
           'detection_limit_lut_path', 'filtered_lut_path', 'area_lut_path', 'name2grp', 'nc_tpl_name', 'nc_tpl_path',
           'sanitize', 'get_lut', 'Enums', 'get_enum_dicts']

# %% ../nbs/api/configs.ipynb 2
from pathlib import Path
import re
from functools import partial

from .inout import read_toml, write_toml
import pandas as pd

import fastcore.all as fc

# %% ../nbs/api/configs.ipynb 4
CFG_FNAME = 'configs.toml'
CDL_FNAME = 'cdl.toml'
NUCLIDE_LOOKUP_FNAME = 'dbo_nuclide.xlsx'
MARISCO_CFG_DIRNAME = '.marisco'

# %% ../nbs/api/configs.ipynb 5
def base_path(): return Path.home() / MARISCO_CFG_DIRNAME

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
        'lut': str(base_path() / 'lut'), # Look-up tables
        'cache': str(base_path() / 'cache'), # Cache (e.f WoRMS species)
        'tmp': str(base_path() / 'tmp')
    },
    'paths': {
        'luts': 'nbs/files/lut'
    },
    'units': {
        'time': 'seconds since 1970-01-01 00:00:00.0'
    },
    'zotero': {
        'api_key': '7nuMByrm19RP7reiQtYJwgPk',
        'lib_id': '2432820'
    }
}

# %% ../nbs/api/configs.ipynb 12
def cfg(): return read_toml(base_path() / CFG_FNAME)

# %% ../nbs/api/configs.ipynb 13
def nuc_lut_path(): return Path(cfg()['dirs']['lut']) / NUCLIDE_LOOKUP_FNAME

# %% ../nbs/api/configs.ipynb 14
def lut_path(): return Path(cfg()['dirs']['lut'])

# %% ../nbs/api/configs.ipynb 15
def cache_path(): return Path(cfg()['dirs']['cache'])

# %% ../nbs/api/configs.ipynb 16
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
        # Do not update keys. Only values if required
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
            'smp_depth': {
                'name': 'smp_depth',
                'attrs': {
                    'long_name': 'Sample depth below seal level',
                    'standard_name': 'sample_depth_below_sea_floor',
                    'units': 'm',
                    'axis': 'Z'
                },
                'dtype': 'f4'
            },
            'tot_depth': {
                'name': 'tot_depth',
                'attrs': {
                    'long_name': 'Total depth below seal level',
                    'standard_name': 'total_depth_below_sea_floor',
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
            'area': {
                'name': 'area',
                'attrs': {
                    'long_name': 'Marine area/region id',
                    'standard_name': 'area_id'
                },
                'dtype': 'area_t'
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
            },
            'species': {
                'name': 'species',
                'attrs': {  
                    'long_name': 'Species',
                    'standard_name': 'species'
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
                'dtype': 'dl_t'
            },
            'volume': {
                'name': '_vol',
                'attrs': {
                    'long_name': ' volume',
                    'standard_name': '_volume'
                },
                'dtype': 'f4'
            },
            'salinity': {
                'name': '_sal',
                'attrs': {
                    'long_name': ' salinity',
                    'standard_name': '_sal'
                },
                'dtype': 'f4'
            },
            'temperature': {
                'name': '_temp',
                'attrs': {
                    'long_name': ' temperature',
                    'standard_name': '_temp'
                },
                'dtype': 'f4'
            },
            'filtered': {
                'name': '_filt',
                'attrs': {
                    'long_name': ' filtered',
                    'standard_name': '_filtered'
                },
                'dtype': 'filt_t'
            },
            'counting_method': {
                'name': '_counmet',
                'attrs': {
                    'long_name': ' counting method',
                    'standard_name': '_counting_method'
                },
                'dtype': 'counmet_t'
            },
            'sampling_method': {
                'name': '_sampmet',
                'attrs': {
                    'long_name': ' sampling method',
                    'standard_name': '_sampling_method'
                },
                'dtype': 'sampmet_t'
            },
            'preparation_method': {
                'name': '_prepmet',
                'attrs': {
                    'long_name': ' preparation method',
                    'standard_name': '_preparation_method'
                },
                'dtype': 'prepmet_t'
            },
            'unit': {
                'name': '_unit',
                'attrs': {
                    'long_name': ' unit',
                    'standard_name': '_unit'
                },
                'dtype': 'unit_t'
            }
        }
    },
    'enums': [
        {
            'name': 'area_t', 
            'fname': 'dbo_area.xlsx', 
            'key': 'displayName', 
            'value':'areaId'
        },
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
            'fname': 'dbo_species_cleaned.xlsx', 
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
            'name': 'unit_t', 
            'fname': 'dbo_unit.xlsx', 
            'key': 'unit_sanitized', 
            'value':'unit_id'
        },
        {
            'name': 'dl_t', 
            'fname': 'dbo_detectlimit.xlsx', 
            'key': 'name_sanitized', 
            'value':'id'
        },
        {
            'name': 'filt_t', 
            'fname': 'dbo_filtered.xlsx', 
            'key': 'name',
            'value':'id'
        },
        {
            'name': 'counmet_t', 
            'fname': 'dbo_counmet.xlsx', 
            'key': 'counmet',
            'value':'counmet_id'
        },
        {
            'name': 'sampmet_t', 
            'fname': 'dbo_sampmet.xlsx', 
            'key': 'sampmet',
            'value':'sampmet_id'
        },
        {
            'name': 'prepmet_t', 
            'fname': 'dbo_prepmet.xlsx', 
            'key': 'prepmet',
            'value':'prepmet_id'
        }
        ]
}

# %% ../nbs/api/configs.ipynb 19
def cdl_cfg(): return read_toml(base_path() / CDL_FNAME)

# %% ../nbs/api/configs.ipynb 20
def species_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'species_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 21
def bodyparts_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'body_part_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 22
def biogroup_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'bio_group_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 23
def sediments_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'sed_type_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 24
def unit_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'unit_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 25
def detection_limit_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'dl_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 26
def filtered_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'filt_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 27
def area_lut_path():
    src_dir = lut_path()
    fname = [enum for enum in cdl_cfg()['enums'] if enum['name'] == 'area_t'][0]['fname']
    return src_dir / fname

# %% ../nbs/api/configs.ipynb 29
NETCDF_TO_PYTHON_TYPE = {
    'u8': int,
    'f4': float
    }

# %% ../nbs/api/configs.ipynb 30
def name2grp(
    name:str, # Name of the group
    cdl:dict, # CDL configuration
    ):
    # Reverse `cdl.toml` config group dict so that group config key can be retrieve based on its name
    return {v['name']:k  for k, v in cdl['grps'].items()}[name]

# %% ../nbs/api/configs.ipynb 33
def nc_tpl_name():
    p = base_path()
    return read_toml(p / 'configs.toml')['names']['nc_template']

# %% ../nbs/api/configs.ipynb 34
def nc_tpl_path():
    "Return the name of the MARIS NetCDF template as defined in `configs.toml`"
    p = base_path()
    return p / read_toml(p / 'configs.toml')['names']['nc_template']

# %% ../nbs/api/configs.ipynb 36
def sanitize(s:str # String to sanitize
             ) -> str:
    """
    Sanitize dictionary key to comply with NetCDF enumeration type: 
    
        - remove `(`, `)`, `.`, `/`, `-`  
        - strip the string
    """
    s = re.sub(r'[().]', '', s)
    return re.sub(r'[/-]', ' ', s).strip() 

# %% ../nbs/api/configs.ipynb 40
def get_lut(src_dir:str, # Directory containing lookup tables
            fname:str, # Excel file lookup table name
            key:str, # Excel file column name to be used as dict keys 
            value:str, # Excel file column name to be used as dict values 
            do_sanitize:bool=True # Sanitization required?
            ) -> dict: # MARIS lookup table
    "Convert MARIS db lookup table excel file to dictionary `{'name': id, ...}`."
    fname = Path(src_dir) / fname
    df = pd.read_excel(fname, usecols=[key, value]).dropna(subset=value)
    df[value] = df[value].astype('int')
    df = df.set_index(key)
    lut = df[value].to_dict()
    if do_sanitize: lut = {sanitize(k): v for k, v in lut.items()}
    return lut

# %% ../nbs/api/configs.ipynb 43
class Enums():
    "Return dictionaries of MARIS NetCDF's enumeration types"
    def __init__(self, 
               lut_src_dir:str,
               cdl_enums:dict
               ):
        fc.store_attr()
        self.types = self.lookup()
        
    def filter(self, name, values):
        return {name: id for name, id in self.types[name].items() if id in values}
    
    def lookup(self):
        types = {}
        for enum in self.cdl_enums:
            name, fname, key, value = enum.values()
            lut = get_lut(self.lut_src_dir, fname, key=key, value=value)
            types[name] = lut
        return types

# %% ../nbs/api/configs.ipynb 49
def get_enum_dicts(
    lut_src_dir:str,
    cdl_enums:dict,
    **kwargs
    ):
    "Return a dict of NetCDF enumeration types"
    enum_types = {}
    for enum in cdl_enums:
        name, fname, key, value = enum.values()
        lut = get_lut(lut_src_dir, fname, key=key, value=value, **kwargs)
        enum_types[name] = lut
        
    return enum_types
