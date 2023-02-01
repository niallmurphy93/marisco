# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/serializers.ipynb.

# %% auto 0
__all__ = ['to_netcdf', 'to_csv']

# %% ../nbs/api/serializers.ipynb 2
from netCDF4 import Dataset
from cftime import num2date, date2num
import pandas as pd
from typing import Dict, Callable
import re

# %% ../nbs/api/serializers.ipynb 3
def to_netcdf(
    dfs:dict[pd.DataFrame], # dict of Dataframes to encode with group name as key {'sediment': df_sed, ...}
    fname_cdl:str, # File name and path to the MARIS CDL template
    fname_output:str, # Name of output file to produce
    cfgs:Dict, # Config file containing global attributes
    units_fn:Callable, # (group, variable) -> unit look up function
):
    "Encode MARIS dataset (provided as Pandas DataFrame) to NetCDF file"
    with Dataset(fname_cdl, format='NETCDF4') as src, Dataset(fname_output, 'w', format='NETCDF4') as dst:
        # copy global attributes all at once via dictionary
        dst.setncatts(src.__dict__)

        dst.setncatts(cfgs['global_attr']) 
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
                if name_var_src in df.reset_index().columns:
                    x = grp_dest.createVariable(name_var_src, var_src.datatype, var_src.dimensions,
                                                compression='zlib', complevel=9)
                    # fill variables
                    # Sanitize
                    n_before += sum(df.reset_index()[name_var_src].notna())
                    df_sanitized = pd.to_numeric(df.reset_index()[name_var_src], 
                                                 errors='coerce', downcast=None)
                    n_after += sum(df_sanitized.notna())
                    grp_dest[name_var_src][:] = df_sanitized .values
                    # copy variable attributes all at once via dictionary
                    grp_dest[name_var_src].setncatts(src.groups[grp_name][name_var_src].__dict__)
                    if (hasattr(src.groups[grp_name][name_var_src], 'units') and
                        src.groups[grp_name][name_var_src].units == '_to_be_filled_in_'):
                        grp_dest[name_var_src].units = units_fn(grp_name, name_var_src)
            print(f'% of discarded data for grp {grp_name}: {100*(n_before - n_after)/n_before}')

# %% ../nbs/api/serializers.ipynb 4
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
