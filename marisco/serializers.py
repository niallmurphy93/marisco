# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/serializers.ipynb.

# %% auto 0
__all__ = ['NetCDFEncoder']

# %% ../nbs/api/serializers.ipynb 3
from netCDF4 import Dataset
import pandas as pd
from typing import Dict, Callable
import pandas as pd
from fastcore.basics import patch, store_attr

# %% ../nbs/api/serializers.ipynb 4
class NetCDFEncoder:
    "MARIS NetCDF encoder."
    def __init__(self, 
                 dfs:dict[pd.DataFrame], # dict of Dataframes to encode with group name as key {'sediment': df_sed, ...}
                 src_fname:str, # File name and path to the MARIS CDL template
                 dest_fname:str, # Name of output file to produce
                 global_attrs:Dict, # Global attributes
                 ):
        store_attr()
        self.enum_types = {}

# %% ../nbs/api/serializers.ipynb 7
@patch 
def copy_global_attributes(self:NetCDFEncoder):
    self.dest.setncatts(self.src.__dict__)
    self.dest.setncatts(self.global_attrs)

# %% ../nbs/api/serializers.ipynb 8
@patch 
def copy_enums(self:NetCDFEncoder):
    "Copy enumeration type from src NetCDF if required"
    print(self.src.enumtypes)

# %% ../nbs/api/serializers.ipynb 9
@patch
def copy_dimensions(self:NetCDFEncoder):
    for name, dimension in self.src.dimensions.items():
        self.dest.createDimension(name, (len(dimension) if not dimension.isunlimited() else None))

# %% ../nbs/api/serializers.ipynb 10
@patch
def process_groups(self:NetCDFEncoder):
    for grp_name, df in self.dfs.items():
        self.process_group(grp_name, df)

# %% ../nbs/api/serializers.ipynb 11
@patch
def process_group(self:NetCDFEncoder, group_name, df):
    group_dest = self.dest.createGroup(group_name)
    self.copy_variables(group_name, df, group_dest)

# %% ../nbs/api/serializers.ipynb 12
@patch
def copy_variables(self:NetCDFEncoder, group_name, df, group_dest):
    for var_name, var_src in self.src.groups[group_name].variables.items():
        if var_name in df.reset_index().columns:
            # self.copy_enums()
            self.copy_variable(var_name, var_src, df, group_dest)

# %% ../nbs/api/serializers.ipynb 13
@patch
def copy_variable(self:NetCDFEncoder, var_name, var_src, df, group_dest):
    dtype_name = var_src.datatype.name
    enums_src = self.src.enumtypes
    if dtype_name in enums_src: self._copy_enum_type_if_needed(dtype_name)   
    self._create_and_copy_variable(var_name, var_src, df, group_dest, dtype_name)
    self.copy_variable_attributes(var_name, var_src, group_dest)

# %% ../nbs/api/serializers.ipynb 14
@patch
def _create_and_copy_variable(self:NetCDFEncoder, var_name, var_src, df, group_dest, dtype_name):
    variable_type = self.enum_types.get(dtype_name, var_src.datatype)
    group_dest.createVariable(var_name, variable_type, var_src.dimensions, compression='zlib', complevel=9)
    
    df_sanitized = self.cast_verbose_rf(df, var_name)
    group_dest[var_name][:] = df_sanitized.values

# %% ../nbs/api/serializers.ipynb 15
@patch
def _copy_enum_type_if_needed(self:NetCDFEncoder, dtype_name):
    if dtype_name not in self.enum_types:
        enum_info = self.src.enumtypes[dtype_name]
        self.enum_types[dtype_name] = self.dest.createEnumType(enum_info.dtype, enum_info.name, enum_info.enum_dict)

# %% ../nbs/api/serializers.ipynb 16
@patch
def copy_variable_attributes(self:NetCDFEncoder, var_name, var_src, group_dest):
    group_dest[var_name].setncatts(var_src.__dict__)
    # group_name = group_dest.path.split('/')[-1]
    # if (hasattr(var_src, 'units') and var_src.units == '_to_be_filled_in_'):
    #     group_dest[var_name].units = self.units_fn(group_name, var_name)

# %% ../nbs/api/serializers.ipynb 17
@patch
def cast_verbose_rf(self:NetCDFEncoder, 
                    df, 
                    col):
    """
    Try to cast df column to numeric type:
        - Silently coerce to nan if not possible
        - But log when it failed
    """
    n_before = sum(df.reset_index()[col].notna())
    df_after = pd.to_numeric(df.reset_index()[col],
                                    errors='coerce', downcast=None)
    n_after = sum(df_after.notna())
    if n_before != n_after: 
        print(f'Failed to convert type of {col} in {n_before - n_after} occurences')
    
    return df_after

# %% ../nbs/api/serializers.ipynb 18
@patch
def encode(self:NetCDFEncoder):
    "Encode MARIS NetCDF based on template and dataframes."
    with Dataset(self.src_fname, format='NETCDF4') as self.src, Dataset(self.dest_fname, 'w', format='NETCDF4') as self.dest:
        self.copy_global_attributes()
        self.copy_dimensions()
        self.process_groups()
