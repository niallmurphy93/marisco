# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/nc_template.ipynb.

# %% auto 0
__all__ = ['NCTemplater']

# %% ../nbs/api/nc_template.ipynb 3
from typing import Dict, Union, Callable
from copy import deepcopy
import re

import netCDF4
from netCDF4 import Dataset
import numpy as np
import pandas as pd
from pathlib import Path
import fastcore.all as fc
from fastcore.basics import patch

from .inout import read_toml
from .configs import name2grp, get_enum_dicts

# %% ../nbs/api/nc_template.ipynb 5
class NCTemplater:
    "MARIS NetCDF template generator."
    def __init__(self, 
                 cdl:Dict, # "Pseudo CDL" (`.toml`)
                 nuclide_vars_fname:str, # File name and path of MARIS nuclide lookup table containing variable names
                 tpl_fname:str, # File name and path of NetCDF4 file to be generated
                 enum_dicts:Dict, # MARIS NetCDF enumeration types
                 verbose=False
                ):
        fc.store_attr()
        self.dim = cdl['dim']
        self.enum_types = {}

# %% ../nbs/api/nc_template.ipynb 9
@patch
def nuclide_vars(
    self:NCTemplater,
    col_varnames:str='nc_name', # Column name in the Excel lookup file containing the NetCDF variable names
    col_stdnames:str='nusymbol', # Column name Excel lookup file containing the NetCDF standard names
    dtype:str='f4', # Default data type
    ) -> list[dict]: # List of nuclide variables (including their names and attributes)
    "Return the name of the radionuclide variables analysed."
    df = pd.read_excel(self.nuclide_vars_fname, index_col=0)
    
    df = df[(df.nuclide != 'NOT AVAILABLE') & (df.nuclide != 'NOT APPLICABLE')]
    # df = df[df.nuclide.isin(['NOT AVAILABLE', 'NOT APPLICABLE'])]
    
    return [
        {
            'name': n,
            'dtype': dtype,
            'attrs': {
                'long_name': f"{nuclide.capitalize()} {massnb}",
                'standard_name': sn,
            }
        }
        for n, nuclide, massnb, sn in zip(
            df[col_varnames],
            df['nuclide'].str.capitalize(),
            df['massnb'].astype(int),
            df[col_stdnames],
        )
    ]

# %% ../nbs/api/nc_template.ipynb 12
@patch
def derive(
    self:NCTemplater,
    nuclide:dict, # Nuclide variable name and associated netcdf attributes
    suffix:dict,  # Naming rules as described in CDL (e.g `_unc`)
) -> dict: # Derived variable name and associated attributes
    "Derive NetCDF nuclide-dependent variable names & attributes as defined in CDL." 
    return {
        # 'name': nuclide['name'] + '_' + suffix['name'],
        'name': nuclide['name'] + suffix['name'],
        'dtype': suffix['dtype'],  # Using dtype from suffix
        'attrs': {key: nuclide['attrs'][key] + suffix['attrs'][key] for key in nuclide['attrs']}
        }

# %% ../nbs/api/nc_template.ipynb 18
@patch
def create_enum_types(self:NCTemplater):
    "Create enumeration types"
    for name, enum in self.enum_dicts.items(): 
        if self.verbose: print(f'Creating {name} enumeration type')
        self.enum_types[name] = self.nc.createEnumType(np.int_, name, enum)

# %% ../nbs/api/nc_template.ipynb 19
@patch
def create_groups(self:NCTemplater):
    "Create NetCDF groups"
    grp_names = [v['name'] for k, v in self.cdl['grps'].items()]
    for grp_name in grp_names:
        grp = self.nc.createGroup(grp_name)
        self.create_variables(grp)

# %% ../nbs/api/nc_template.ipynb 20
@patch
def create_variables(self:NCTemplater, 
                     grp:netCDF4.Group, # NetCDF group
                     ):
        "Create variables"
        self.create_variable(grp, self.dim) # Dimension variable
        self.create_default_variables(grp)
        self.create_group_specific_variables(grp)
        self.create_analyte_variables(grp)

# %% ../nbs/api/nc_template.ipynb 21
@patch
def create_default_variables(self:NCTemplater, 
                             grp:netCDF4.Group, # NetCDF group
                             ):
        "Create Default variables"
        vars = self.cdl['vars']['defaults'].values()
        for var in vars: self.create_variable(grp, var)

# %% ../nbs/api/nc_template.ipynb 22
@patch
def create_group_specific_variables(self:NCTemplater, 
                             grp:netCDF4.Group, # NetCDF group
                             ):
        "Create group specific variables"
        vars = self.cdl['vars']
        for var in vars.get(name2grp(grp.name, self.cdl), {}).values(): 
            self.create_variable(grp, var)

# %% ../nbs/api/nc_template.ipynb 23
@patch
def create_analyte_variables(self:NCTemplater, 
                             grp:netCDF4.Group, # NetCDF group
                             ):
    "Create analyte variables and dependent one as uncertainty, detection limit, ..."    
    for var in self.nuclide_vars():
        self.create_variable(grp, var)
        for v in self.cdl['vars']['suffixes'].values(): 
            self.create_variable(grp, self.derive(var, v))

# %% ../nbs/api/nc_template.ipynb 24
@patch
def create_variable(self:NCTemplater, 
                    grp:netCDF4.Group, # NetCDF group
                    var:Dict, # Variable specificiation dict with `name`, `dtype` and `attrs` keys
                    ):
    "Create NetCDF variable with proper types (standard and enums)"
    name, dtype, attrs = var.values()
    nc_var = grp.createVariable(name, 
                                self.enum_types.get(dtype) or dtype, 
                                self.dim['name'])
    nc_var.setncatts(attrs) 

# %% ../nbs/api/nc_template.ipynb 27
@patch
def generate(self:NCTemplater):
    "Generate CDL"
    # with NetCDFWriter(self.tpl_fname) as self.nc:
    with Dataset(self.tpl_fname, 'w', format='NETCDF4') as self.nc:
        self.nc.setncatts(self.cdl['global_attrs']) 
        self.create_enum_types()
        self.nc.createDimension(self.dim['name'], None) 
        self.create_groups()
