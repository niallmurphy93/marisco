# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/callbacks.ipynb.

# %% auto 0
__all__ = ['Callback', 'run_cbs', 'Transformer', 'EncodeTimeCB', 'SanitizeLonLatCB']

# %% ../nbs/api/callbacks.ipynb 2
import copy
import fastcore.all as fc
from operator import attrgetter
from cftime import date2num
import numpy as np
import pandas as pd
from .configs import cfg

# %% ../nbs/api/callbacks.ipynb 3
class Callback(): order = 0

# %% ../nbs/api/callbacks.ipynb 4
def run_cbs(cbs, obj=None):
    for cb in sorted(cbs, key=attrgetter('order')):
        if cb.__doc__: obj.logs.append(cb.__doc__)
        cb(obj)

# %% ../nbs/api/callbacks.ipynb 5
class Transformer():
    def __init__(self, dfs, cbs=None): 
        self.cbs = cbs
        #self.dfs = {k: v.copy() for k, v in dfs.items()}

        self.dfs = self._copy(dfs)
        
        self.logs = []

    def _copy(self, dfs):
        if isinstance(dfs, dict):
            return {k: v.copy() for k, v in dfs.items()}
        else:
            return dfs.copy()
        
    def callback(self):
        run_cbs(self.cbs, self)
        
    def unique(self, col_name):
        "Distinct values of a specific column present in all groups"
        columns = [df.get(col_name) for df in self.dfs.values() if df.get(col_name) is not None]
        values = np.concatenate(columns) if columns else []
        return np.unique(values)
        
    def __call__(self):
        if self.cbs: self.callback()
        return self.dfs

# %% ../nbs/api/callbacks.ipynb 10
class EncodeTimeCB(Callback):
    "Encode time as `int` representing seconds since xxx"    
    def __init__(self, cfg , verbose=False): fc.store_attr()
    def __call__(self, tfm): 
        def format_time(x): 
            return date2num(x, units=self.cfg['units']['time'])
        
        for k in tfm.dfs.keys():
            # If invalid time entries.
            if tfm.dfs[k]['time'].isna().any():
                if self.verbose:
                    invalid_time_df=tfm.dfs[k][tfm.dfs[k]['time'].isna()]
                    print (f'{len(invalid_time_df.index)} of {len(tfm.dfs[k].index)} entries for `time` are invalid for {k}.')
                # Filter nan values
                tfm.dfs[k] = tfm.dfs[k][tfm.dfs[k]['time'].notna()]
            
            tfm.dfs[k]['time'] = tfm.dfs[k]['time'].apply(format_time)

# %% ../nbs/api/callbacks.ipynb 11
class SanitizeLonLatCB(Callback):
    "Drop row when both longitude & latitude equal 0. Drop unrealistic longitude & latitude values. Convert longitude & latitude `,` separator to `.` separator."
    def __init__(self, verbose=False): fc.store_attr()
    def __call__(self, tfm):
        for grp, df in tfm.dfs.items():
            " Convert `,` separator to `.` separator"
            df['lon'] = [float(str(x).replace(',', '.')) for x in df['lon']]
            df['lat'] = [float(str(x).replace(',', '.')) for x in df['lat']]
            
            # mask zero values
            mask_zeroes = (df.lon == 0) & (df.lat == 0) 
            nZeroes = mask_zeroes.sum()
            if nZeroes and self.verbose: 
                print(f'The "{grp}" group contains {nZeroes} data points whose (lon, lat) = (0, 0)')
            
            # mask gps out of bounds, goob. 
            mask_goob = (df.lon < -180) | (df.lon > 180) | (df.lat < -90) | (df.lat > 90)
            nGoob = mask_goob.sum()
            if nGoob and self.verbose: 
                print(f'The "{grp}" group contains {nGoob} data points whose lon or lat are unrealistic. Outside -90 to 90 for latitude and -180 to 180 for longitude.')
                
            tfm.dfs[grp] = df.loc[~(mask_zeroes | mask_goob)]
