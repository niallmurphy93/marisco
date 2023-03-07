# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/utils.ipynb.

# %% auto 0
__all__ = ['has_valid_varname', 'write_toml', 'read_toml', 'get_bbox', 'parametrize']

# %% ../nbs/api/utils.ipynb 2
from netCDF4 import Dataset
from fastcore.test import test_eq
import pandas as pd
import numpy as np
from typing import Dict
import tomli_w
import tomli
from shapely import MultiPoint, Polygon
import nbformat

# %% ../nbs/api/utils.ipynb 4
def has_valid_varname(
    var_names:Dict, # Look up table associating dataset variable names to standardized ones  
    cdl_path:str, # Path to MARIS CDL file (point of truth)
):
    "Check that proposed variable names are in MARIS CDL"
    has_valid = True
    with Dataset(cdl_path) as nc:
        grp = nc.groups[list(nc.groups.keys())[0]] # get any group
        for name in var_names.values():
            if name not in grp.variables.keys():
                has_valid = False
                print(f'"{name}" variable name not found in MARIS CDL')
    
    return has_valid

# %% ../nbs/api/utils.ipynb 8
def write_toml(fname, cfg):
    print(f'Creating {fname}')
    with open(fname, "wb") as f:
        tomli_w.dump(cfg, f)

# %% ../nbs/api/utils.ipynb 9
def read_toml(fname):
    with open(fname, "rb") as f:
        config = tomli.load(f)
    return config

# %% ../nbs/api/utils.ipynb 11
def get_bbox(df,
             coord_cols=('lon', 'lat')
            ):
    arr = []
    x, y = coord_cols
    for index, row in df.iterrows():
        arr.append((row[x], row[y]))
    return MultiPoint(arr).envelope

# %% ../nbs/api/utils.ipynb 16
def parametrize(notebook:str, # Notebook path
               ):
    "Add `parameters` notebook cell tag when seeing `#| params` special character"
    nb = nbformat.read(notebook, as_version=4)
    cell = [c for c in nb.cells if '#|params' in c.source.replace(' ', '')][0]
    cell.metadata = {'tags': ['parameters']}
    nbformat.write(nb, notebook)
