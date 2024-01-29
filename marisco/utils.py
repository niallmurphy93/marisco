# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/utils.ipynb.

# %% auto 0
__all__ = ['Callback', 'run_cbs', 'Transformer', 'has_valid_varname', 'write_toml', 'read_toml', 'get_bbox',
           'download_files_in_folder', 'download_file', 'match_worms']

# %% ../nbs/api/utils.ipynb 2
from pathlib import Path
from netCDF4 import Dataset
from fastcore.test import test_eq
import fastcore.all as fc
import pandas as pd
import numpy as np
import requests
import tomli_w
import tomli
from shapely import MultiPoint
from operator import attrgetter

# %% ../nbs/api/utils.ipynb 4
class Callback(): order = 0

# %% ../nbs/api/utils.ipynb 5
def run_cbs(cbs, obj=None):
    for cb in sorted(cbs, key=attrgetter('order')):
        if cb.__doc__: obj.logs.append(cb.__doc__)
        cb(obj)

# %% ../nbs/api/utils.ipynb 6
class Transformer():
    def __init__(self, dfs, cbs=None): 
        fc.store_attr()
        self.logs = []
        
    def callback(self):
        run_cbs(self.cbs, self)
        
    def __call__(self):
        self.callback()
        return self.dfs

# %% ../nbs/api/utils.ipynb 8
def has_valid_varname(
    var_names:list, # variable (nuclide) names
    cdl_path:str, # Path to MARIS CDL file (point of truth)
):
    "Check that proposed variable names are in MARIS CDL"
    has_valid = True
    with Dataset(cdl_path) as nc:
        grp = nc.groups[list(nc.groups.keys())[0]] # get any group
        for name in var_names:
            if name not in grp.variables.keys():
                has_valid = False
                print(f'"{name}" variable name not found in MARIS CDL')
    
    return has_valid

# %% ../nbs/api/utils.ipynb 12
def write_toml(fname, cfg):
    print(f'Creating {fname}')
    with open(fname, "wb") as f:
        tomli_w.dump(cfg, f)

# %% ../nbs/api/utils.ipynb 13
def read_toml(fname):
    with open(fname, "rb") as f:
        config = tomli.load(f)
    return config

# %% ../nbs/api/utils.ipynb 15
def get_bbox(df,
             coord_cols=('lon', 'lat')
            ):
    arr = []
    x, y = coord_cols
    for index, row in df.iterrows():
        arr.append((row[x], row[y]))
    return MultiPoint(arr).envelope

# %% ../nbs/api/utils.ipynb 20
def download_files_in_folder(owner:str, 
                             repo:str, 
                             src_dir:str, 
                             dest_dir:str
                             ):
    "Make a GET request to the GitHub API to get the contents of the folder"
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{src_dir}"
    response = requests.get(url)

    if response.status_code == 200:
        contents = response.json()

        # Iterate over the files and download them
        for item in contents:
            if item["type"] == "file":
                fname = item["name"]
                download_file(owner, repo, src_dir, dest_dir, fname)
    else:
        print(f"Error: {response.status_code}")

def download_file(owner, repo, src_dir, dest_dir, fname):
    # Make a GET request to the GitHub API to get the raw file contents
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{src_dir}/{fname}"
    response = requests.get(url)

    if response.status_code == 200:
        # Save the file locally
        with open(Path(dest_dir) / fname, "wb") as file:
            file.write(response.content)
        print(f"{fname} downloaded successfully.")
    else:
        print(f"Error: {response.status_code}")

# %% ../nbs/api/utils.ipynb 22
def match_worms(
    name:str # Name of species to look up in WoRMS
    ):
    "Lookup `name` in WoRMS (fuzzy match)"
    url = 'https://www.marinespecies.org/rest/AphiaRecordsByMatchNames'
    params = {
        'scientificnames[]': [name],
        'marine_only': 'true'
    }
    headers = {
        'accept': 'application/json'
    }
    
    response = requests.get(url, params=params, headers=headers)
    
    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return -1
