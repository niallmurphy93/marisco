# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/serializers.ipynb.

# %% auto 0
__all__ = ['NetCDFEncoder', 'OpenRefineCsvEncoder']

# %% ../nbs/api/serializers.ipynb 3
import netCDF4
from netCDF4 import Dataset
import pandas as pd
from typing import Dict, Callable
import pandas as pd
import numpy as np
from fastcore.basics import patch, store_attr
import fastcore.all as fc
import os

# %% ../nbs/api/serializers.ipynb 5
class NetCDFEncoder:
    "MARIS NetCDF encoder."
    def __init__(self, 
                 dfs:dict[pd.DataFrame], # dict of Dataframes to encode with group name as key {'sediment': df_sed, ...}
                 src_fname:str, # File name and path to the MARIS CDL template
                 dest_fname:str, # Name of output file to produce
                 global_attrs:Dict, # Global attributes
                 enums_xtra:Dict={}, # Enumeration types to overwrite
                 verbose:bool=False, # Print currently written NetCDF group and variable names
                 ):
        store_attr()
        self.enum_types = {}

# %% ../nbs/api/serializers.ipynb 7
@patch 
def copy_global_attributes(self:NetCDFEncoder):
    "Update NetCDF template global attributes as specified by `global_attrs` argument."
    self.dest.setncatts(self.src.__dict__)
    for k, v in self.global_attrs.items(): self.dest.setncattr(k, v)

# %% ../nbs/api/serializers.ipynb 8
@patch
def copy_dimensions(self:NetCDFEncoder):
    for name, dimension in self.src.dimensions.items():
        self.dest.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

# %% ../nbs/api/serializers.ipynb 9
@patch
def process_groups(self:NetCDFEncoder):
    for grp_name, df in self.dfs.items():
        self.process_group(grp_name, df)

# %% ../nbs/api/serializers.ipynb 10
@patch
def process_group(self:NetCDFEncoder, group_name, df):
    group_dest = self.dest.createGroup(group_name)
    # Set the dimensions for each group
    group_dest.createDimension(group_name, len(df.index))
    
    self.copy_variables(group_name, df, group_dest)

# %% ../nbs/api/serializers.ipynb 11
@patch
def copy_variables(self:NetCDFEncoder, group_name, df, group_dest):
    for var_name, var_src in self.src.groups[group_name].variables.items():
        if var_name in df.reset_index().columns: 
            self.copy_variable(var_name, var_src, df, group_dest)

# %% ../nbs/api/serializers.ipynb 12
@patch
def copy_variable(self:NetCDFEncoder, var_name, var_src, df, group_dest):
    dtype_name = var_src.datatype.name
    enums_src = self.src.enumtypes
    if self.verbose: 
        print(80*'-')
        print(f'Group: {group_dest.name}, Variable: {var_name}')
    # If the type of the var is an enum (meaning present in the template src) then create it
    if dtype_name in enums_src: self.copy_enum_type(dtype_name) 
    self._create_and_copy_variable(var_name, var_src, df, group_dest, dtype_name)
    self.copy_variable_attributes(var_name, var_src, group_dest)

# %% ../nbs/api/serializers.ipynb 13
@patch
def _create_and_copy_variable(self:NetCDFEncoder, var_name, var_src, df, group_dest, dtype_name):
    variable_type = self.enum_types.get(dtype_name, var_src.datatype)
    group_dest.createVariable(var_name, variable_type, group_dest.dimensions, compression='zlib', complevel=9)
       
    isNotEnum = type(variable_type) != netCDF4._netCDF4.EnumType
    values = df[var_name].values
    group_dest[var_name][:] = values if isNotEnum else self.sanitize_if_enum_and_nan(values)

# %% ../nbs/api/serializers.ipynb 14
@patch
def sanitize_if_enum_and_nan(self:NetCDFEncoder, values, fill_value=-1):
    values[np.isnan(values)] = int(fill_value)
    values = values.astype(int)
    return values

# %% ../nbs/api/serializers.ipynb 15
@patch
def copy_enum_type(self:NetCDFEncoder, dtype_name):
    # if enum type not already created
    if dtype_name not in self.enum_types:
        enum_info = self.src.enumtypes[dtype_name]
        # If a subset of an enum is defined in enums_xtra (typically for the lengthy species_t)
        if enum_info.name in self.enums_xtra:
            # add "not applicable"
            enum_info.enum_dict = self.enums_xtra[enum_info.name]
            enum_info.enum_dict['Not applicable'] = -1 # TBD
        self.enum_types[dtype_name] = self.dest.createEnumType(enum_info.dtype, 
                                                               enum_info.name, 
                                                               enum_info.enum_dict)

# %% ../nbs/api/serializers.ipynb 16
@patch
def copy_variable_attributes(self:NetCDFEncoder, var_name, var_src, group_dest):
    group_dest[var_name].setncatts(var_src.__dict__)

# %% ../nbs/api/serializers.ipynb 18
@patch
def encode(self:NetCDFEncoder):
    "Encode MARIS NetCDF based on template and dataframes."
    with Dataset(self.src_fname, format='NETCDF4') as self.src, Dataset(self.dest_fname, 'w', format='NETCDF4') as self.dest:
        self.copy_global_attributes()
        self.copy_dimensions()
        self.process_groups()

# %% ../nbs/api/serializers.ipynb 26
class OpenRefineCsvEncoder:
    "OpenRefine CSV from NetCDF."
    def __init__(self, 
                 dfs:dict[pd.DataFrame], # dict of Dataframes to encode with group name as key {'sediment': df_sed, ...}
                 dest_fname:str, # Name of output file to produce
                 verbose:bool=False, # Print 
                 ):
        store_attr()

# %% ../nbs/api/serializers.ipynb 27
@patch
def process_groups_to_csv(self:OpenRefineCsvEncoder):
    for grp_name, df in self.dfs.items():
        self.process_group_to_csv(grp_name, df)

# %% ../nbs/api/serializers.ipynb 28
@patch
def process_group_to_csv(self:OpenRefineCsvEncoder, group_name, df):
    filename, file_extension=os.path.splitext(self.dest_fname)
    path = filename + '_' + group_name + file_extension
    df.to_csv ( path_or_buf= path, sep=',')

# %% ../nbs/api/serializers.ipynb 29
@patch
def encode(self:OpenRefineCsvEncoder):
    "Encode OpenRefine CSV based on dataframes from NetCDF."
    self.process_groups_to_csv()
