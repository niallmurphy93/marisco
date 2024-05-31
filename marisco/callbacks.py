# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/callbacks.ipynb.

# %% auto 0
__all__ = ['Callback', 'run_cbs', 'Transformer', 'EncodeTimeCB', 'SanitizeLonLatCB']

# %% ../nbs/api/callbacks.ipynb 2
import copy
import fastcore.all as fc
from operator import attrgetter
from cftime import date2num
import numpy as np

from .configs import cfg

# %% ../nbs/api/callbacks.ipynb 4
class Callback(): order = 0

# %% ../nbs/api/callbacks.ipynb 5
def run_cbs(cbs, obj=None):
    for cb in sorted(cbs, key=attrgetter('order')):
        if cb.__doc__: obj.logs.append(cb.__doc__)
        cb(obj)

# %% ../nbs/api/callbacks.ipynb 6
class Transformer():
    def __init__(self, dfs, cbs=None): 
        self.cbs = cbs
        self.dfs = {k: v.copy() for k, v in dfs.items()}
        self.logs = []
        
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

# %% ../nbs/api/callbacks.ipynb 11
class EncodeTimeCB(Callback):
    "Encode time as `int` representing seconds since xxx"    
    def __init__(self, cfg): fc.store_attr()
    def __call__(self, tfm): 
        def format_time(x): return date2num(x, units=self.cfg['units']['time'])
        
        for k in tfm.dfs.keys():
            tfm.dfs[k]['time'] = tfm.dfs[k]['time'].apply(format_time)

# %% ../nbs/api/callbacks.ipynb 12
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
