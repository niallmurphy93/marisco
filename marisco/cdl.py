# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/cdl.ipynb.

# %% auto 0
__all__ = ['CONFIGS', 'CDL']

# %% ../nbs/api/cdl.ipynb 2
from netCDF4 import Dataset
import pandas as pd
from pathlib import Path
from fastcore.basics import patch, store_attr
from typing import Dict

# %% ../nbs/api/cdl.ipynb 3
CONFIGS = {
    'global_attr': {
        'description': 'Template description',
        'summary': 'Template summary',
        'keyword': 'MARIS other-key-words',
        'license': 'Common ...'
    },
    'var_attrs': {
        'sample': {
            'long_name': 'Sample ID of measurement'
        },
        'depth': {
            'long_name': 'Depth below seal level',
            'standard_name': 'depth_below_sea_floor',
            'units': 'm',
            'axis': 'Z'},
        'lon': {
            'long_name': 'Measurement longitude',
            'standard_name': 'longitude',
            'units': 'degrees_north',
            'axis': 'Y',
            '_CoordinateAxisType': 'Lon'
        },
        'lat': {
            'long_name': 'Measurement latitude',
            'standard_name': 'latitude',
            'units': 'degrees_east',
            'axis': 'X',
            '_CoordinateAxisType': 'Lat'
        },
        'time': {
            'long_name': 'Time of measurement',
            'standard_name': 'time',
            'units': 'seconds since 1970-01-01 00:00:00.0',
            'time_origin': '1970-01-01 00:00:00',
            'time_zone': 'UTC',
            'abbreviation': 'Date/Time',
            'axis': 'T',
            'calendar': 'gregorian'
        }
    },
    'placeholder': '_to_be_filled_in_',
    'uncertainty': {
        'long_name': ' uncertainty',
        'standard_name': '_uncertainty',
        'var_suffix': '_unc'
    },
    'detection_limit': {
        'long_name': ' detection limit',
        'standard_name': '_detection_limit',
        'var_suffix': '_dl'
    }
}

# %% ../nbs/api/cdl.ipynb 4
class CDL:
    def __init__(self, 
                 vars_fname:str, # File name and path of MARIS nuclide look up table
                 dest_dir:str, # Destination directory for generated CDL files
                 cfgs:Dict, # Configuration (default attributes, naming conventions, ...)
                 cdl_fname:str='maris-cdl.nc', # CDL file name
                ):
        store_attr()

# %% ../nbs/api/cdl.ipynb 5
@patch
def get_analytes(self:CDL,
                 col_varnames:str='nc_name', # Column name containing the NetCDF variable names
                 col_stdnames:str='nusymbol', # Column name containing the NetCDF standard names
                ):
    "Return the name of the variables analysed"
    df = pd.read_excel(self.vars_fname, index_col=0)
    df = df[df.nuclide != 'NOT AVAILABLE']
    var_names = df[col_varnames].tolist()
    std_names = df[col_stdnames].tolist()
    long_names = df[['nuclide', 'massnb']].apply(lambda row: ' '.join(row.values.astype(str)), 
                                                 axis=1).tolist()
    long_names = [name.capitalize() for name in long_names]

    return [{'name': n, 
             'attrs': {
                 'long_name': ln,
                 'standard_name': sn}} 
            for n, ln, sn in zip(*(var_names, long_names, std_names))]

# %% ../nbs/api/cdl.ipynb 6
@patch
def create_variable(self:CDL, 
               nc, # NetCDF file
               name:str, # Name of the variable
               attrs:dict, # Variable attributes
               dtype:str='f4', # Type of the variable
               dim:tuple=('sample',) # Dimension

           ):
    nc_var = nc.createVariable(name, dtype, dim)
    nc_var.setncatts(attrs)    
    return nc

# %% ../nbs/api/cdl.ipynb 7
@patch
def generate(self:CDL,
            common_vars:list=['lon', 'lat', 'depth', 'time'], # Common variables
            ):
    "Generate CDL"
    fname = Path(self.dest_dir)/self.cdl_fname
    with Dataset(fname, 'w', format='NETCDF3_CLASSIC') as nc:
        # Create dataset attributes
        nc.setncatts(self.cfgs['global_attr']) 
        
        # Create dim
        nc.createDimension('sample', None)
       
        # Create common variables
        self.create_variable(nc, 'sample', self.cfgs['var_attrs']['sample'], 'i4')
        for name in common_vars: self.create_variable(nc, name, self.cfgs['var_attrs'][name])
        
        # Create analyte variables
        for analyte in self.get_analytes():
            attrs = analyte['attrs']
            attrs['unit'] = self.cfgs['placeholder']

            self.create_variable(nc, analyte['name'], attrs)

            # Related uncertainty and detection limit
            for related_var in ['uncertainty', 'detection_limit']:
                cfg = self.cfgs[related_var]
                attrs['long_name'] += cfg['long_name']
                attrs['standard_name'] += cfg['standard_name']
                self.create_variable(nc, analyte['name'] + cfg['var_suffix'], attrs)
