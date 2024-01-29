# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/api/callbacks.ipynb.

# %% auto 0
__all__ = ['Callback', 'run_cbs', 'Transformer', 'EncodeTimeCB', 'SanitizeLonLatCB']

# %% ../nbs/api/callbacks.ipynb 2
import fastcore.all as fc
from operator import attrgetter
from cftime import date2num

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
        fc.store_attr()
        self.logs = []
        
    def callback(self):
        run_cbs(self.cbs, self)
        
    def __call__(self):
        self.callback()
        return self.dfs

# %% ../nbs/api/callbacks.ipynb 7
class EncodeTimeCB(Callback):
    "Encode time as `int` representing seconds since xxx"    
    def __init__(self, cfg): fc.store_attr()
    
    def __call__(self, tfm): 
        def format_time(x): return date2num(x, units=self.cfg['units']['time'])
        
        for k in tfm.dfs.keys():
            tfm.dfs[k]['time'] = tfm.dfs[k]['time'].apply(format_time)

# %% ../nbs/api/callbacks.ipynb 8
class SanitizeLonLatCB(Callback):
    "Drop row when both longitude & latitude equal 0"

    def __call__(self, tfm):
        tfm.dfs = {grp: (df[(df.lon != 0) & (df.lat != 0)])
                   for grp, df in tfm.dfs.items()}
