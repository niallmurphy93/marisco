# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/nc_template.ipynb.

# %% auto 0
__all__ = ['NCTemplater']

# %% ../nbs/api/nc_template.ipynb 3
from typing import Dict, Union
from copy import deepcopy
import re

from netCDF4 import Dataset
import numpy as np
import pandas as pd
from pathlib import Path
# from fastcore.basics import patch, store_attr
import fastcore.all as fc
from fastcore.basics import patch

from .utils import read_toml
from .configs import name2grp, get_cfgs

# %% ../nbs/api/nc_template.ipynb 5
class NCTemplater:
    "MARIS NetCDF template generator."
    def __init__(self, 
                 cdl_fname:Dict, # File name and path of the "Pseudo CDL" (`.toml`)
                 nuclide_vars_fname:str, # File name and path of MARIS nuclide lookup table containing variable names
                 tpl_fname:str, # File name and path of NetCDF4 file to be generated
                ):
        fc.store_attr()
        self.cdl = read_toml(cdl_fname)
        # self.dim = self.cdl['dim']
        self.dim = self.cdl['dim']
        self.enum_types = {}

# %% ../nbs/api/nc_template.ipynb 8
@patch
def nuclide_vars(
    self:NCTemplater,
    col_varnames:str='nc_name', # Column name in the Excel lookup file containing the NetCDF variable names
    col_stdnames:str='nusymbol', # Column name Excel lookup file containing the NetCDF standard names
    dtype:str='f4', # Default data type
    ) -> list[dict]: # List of nuclide variables (including their names and attributes)
    "Return the name of the radionuclide variables analysed."
    df = pd.read_excel(self.nuclide_vars_fname, index_col=0)
    df = df[df.nuclide != 'NOT AVAILABLE']
    var_names = df[col_varnames].tolist()
    std_names = df[col_stdnames].tolist()
    long_names = df[['nuclide', 'massnb']].apply(lambda row: ' '.join(row.values.astype(str)), 
                                                 axis=1).tolist()
    long_names = [name.capitalize() for name in long_names]

    return [{'name': n,
             'attrs': {
                 'long_name': ln,
                 'standard_name': sn
             },
             'dtype': dtype
            } for n, ln, sn in zip(*(var_names, long_names, std_names))]

# %% ../nbs/api/nc_template.ipynb 11
# @fc.patch
# def get_analytes(self:NCTemplater,
#                  col_varnames:str='nc_name', # Column name in the Excel lookup file containing the NetCDF variable names
#                  col_stdnames:str='nusymbol', # Column name Excel lookup file containing the NetCDF standard names
#                  dtype:str='f4', # Default type
#                 ):
#     "Return the name of the variables analysed"
#     df = pd.read_excel(self.vars_fname, index_col=0)
#     df = df[df.nuclide != 'NOT AVAILABLE']
#     var_names = df[col_varnames].tolist()
#     std_names = df[col_stdnames].tolist()
#     long_names = df[['nuclide', 'massnb']].apply(lambda row: ' '.join(row.values.astype(str)), 
#                                                  axis=1).tolist()
#     long_names = [name.capitalize() for name in long_names]

#     return [{'name': n,
#              'attrs': {
#                  'long_name': ln,
#                  'standard_name': sn
#              },
#              'dtype': dtype
#             } for n, ln, sn in zip(*(var_names, long_names, std_names))]

# %% ../nbs/api/nc_template.ipynb 12
@patch
def derive(
    self:NCTemplater,
    nuclide:dict, # Nuclide variable name and associated netcdf attributes
    suffix:dict,  # Naming rules as described in CDL (e.g `_unc`)
) -> dict: # Derived variable name and associated attributes
    "Derive NetCDF nuclide-dependent variable names & attributes as defined in CDL." 
    return {
        'name': nuclide['name'] + suffix['name'],
        'attrs': {key: nuclide['attrs'][key] + suffix['attrs'][key] for key in nuclide['attrs']},
        'dtype': suffix['dtype']  # Using dtype from suffix
        }

# %% ../nbs/api/nc_template.ipynb 23
# @fc.patch
# def create_variable(self:NCTemplater, 
#                nc, # NetCDF file
#                var:Dict, # Variable
#                dtype:Union[str, None]=None, # Type of the variable
#            ):
#     """Create NetCDF variable with proper types (standard and enums)"""
#     name = var['name']
#     attrs = var['attrs'].copy()
#     nc_var = nc.createVariable(name, 
#                                self.enum_types.get(dtype) or dtype, 
#                                self.dim['name'])
#     nc_var.setncatts(attrs)    
#     return nc

# %% ../nbs/api/nc_template.ipynb 25
# @fc.patch
# def generate(self:NCTemplater,
#              common_vars:list=['lon', 'lat', 'depth', 'time'], # Common variables
#             ):
#     "Generate CDL"
#     fname = Path(self.dest_dir)/self.tpl_fname
    
#     common_vars = self.cdl['vars']['defaults'].keys()
    
#     with Dataset(fname, 'w', format='NETCDF4') as nc:
#         # Create dataset attributes
#         nc.setncatts(self.cdl['global_attrs']) 
        
#         # Create Enum type    
#         for name, enum in enum_type_lut.items(): 
#             self.enum_types[name] = nc.createEnumType(np.uint16, name, enum)
        
#         # Create shared `sample` dimension
#         nc.createDimension(self.dim['name'], None)
        
#         # Create grps
#         grp_names = [v['name'] for k, v in self.cdl['grps'].items()]
#         for grp_name in grp_names:
#             grp = nc.createGroup(grp_name)

#             # Create 'dim' variable
#             #self.create_variable(grp, self.dim, 'i4')
#             self.create_variable(grp, self.dim)
            
#             # Create default variables
#             for var in self.cdl['vars']['defaults'].values(): 
#                 self.create_variable(grp, var)

#             # Create group-specific variables
#             if name2grp(grp_name) in self.cdl['vars']:
#                 for var in self.cdl['vars'][name2grp(grp_name)].values(): 
#                     self.create_variable(grp, var)
            
#             # Create analyte variables
#             for analyte in self.get_analytes():
#                 analyte['units'] = self.cdl['placeholder']
#                 self.create_variable(grp, analyte)
            
#                 # Derived uncertainty and detection limit variables
#                 for k, v in self.cdl['vars']['suffixes'].items():
#                     self.create_variable(grp, derive(analyte, v))
