# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/serializers.ipynb.

# %% auto 0
__all__ = ['cast_verbose', 'to_netcdf', 'to_csv']

# %% ../nbs/api/serializers.ipynb 2
from netCDF4 import Dataset
from cftime import num2date
import pandas as pd
from typing import Dict, Callable
import re

# %% ../nbs/api/serializers.ipynb 3
def cast_verbose(df, col):
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

# %% ../nbs/api/serializers.ipynb 6
# Link to possible refactoring: https://chat.openai.com/share/5853317b-e102-427f-ba72-3fc6445f4368
def to_netcdf(
    dfs:dict[pd.DataFrame], # dict of Dataframes to encode with group name as key {'sediment': df_sed, ...}
    fname_cdl:str, # File name and path to the MARIS CDL template
    fname_output:str, # Name of output file to produce
    global_attrs:Dict, # Global attributes
    units_fn:Callable, # (group, variable) -> unit look up function
):
    "Encode MARIS dataset (provided as Pandas DataFrame) to NetCDF file"
    with Dataset(fname_cdl, format='NETCDF4') as src, Dataset(fname_output, 'w', format='NETCDF4') as dst:
        # copy global attributes all at once via dictionary
        dst.setncatts(src.__dict__)
        dst.setncatts(global_attrs) 
        # copy dimensions
        for name, dimension in src.dimensions.items():
            dst.createDimension(
                name, (len(dimension) if not dimension.isunlimited() else None))

        # copy groups
        for grp_name, df in dfs.items():
            # TBD: asserting group name
            grp_dest = dst.createGroup(grp_name)
        
            n_before = 0
            n_after = 0
            
            # copy all variables of interest and fill them
            for name_var_src, var_src in src.groups[grp_name].variables.items():
                # Only if source variable is in destination
                if name_var_src in df.reset_index().columns:
                    # x = grp_dest.createVariable(name_var_src, var_src.datatype, var_src.dimensions,
                    grp_dest.createVariable(name_var_src, var_src.datatype, var_src.dimensions,
                                            compression='zlib', complevel=9)
                        
                    df_sanitized = cast_verbose(df, name_var_src)
                    grp_dest[name_var_src][:] = df_sanitized.values
                    
                    # copy variable attributes all at once via dictionary
                    grp_dest[name_var_src].setncatts(src.groups[grp_name][name_var_src].__dict__)
                    if (hasattr(src.groups[grp_name][name_var_src], 'units') and
                        src.groups[grp_name][name_var_src].units == '_to_be_filled_in_'):
                        grp_dest[name_var_src].units = units_fn(grp_name, name_var_src)

# %% ../nbs/api/serializers.ipynb 7
def to_csv(
    fname_nc:str,
    fname_output:str):
    "Convert MARIS NetCDF filer to `.csv`"
    fname_nc = './files/nc/tepco-sediments.nc'
    data_dict = {}
    with Dataset(fname_nc) as nc:
        # global attrs
        for name in nc.ncattrs():
            pass
            #print(name)
        # list of vars   
        for name in nc.variables:
            #print(name)
            variable = nc[name]
            data_dict[name] = variable[:]
    return pd.DataFrame(data_dict)

#df = to_csv('./files/nc/tepco-sediments.nc', '')
