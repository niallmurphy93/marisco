# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/handlers/generic.ipynb.

# %% auto 0
__all__ = ['common_cols', 'coi_grp', 'renaming_rules', 'kw', 'load_data', 'rename_cols', 'RemapRdnNameCB', 'ParseTimeCB',
           'RenameColumnCB', 'ReshapeLongToWide', 'get_attrs', 'units_fn', 'encode']

# %% ../../nbs/handlers/generic.ipynb 4
import pandas as pd
from tqdm import tqdm
from functools import partial
import fastcore.all as fc

from pathlib import Path

from ..utils import (has_valid_varname, match_worms)
from ..callbacks import (Callback, Transformer,
                               EncodeTimeCB, SanitizeLonLatCB)

from ..metadata import (GlobAttrsFeeder, BboxCB,
                              DepthRangeCB, TimeRangeCB,
                              ZoteroCB, KeyValuePairCB)

from ..serializers import to_netcdf
from ..configs import get_nc_tpl_path, BASE_PATH, get_nuclides_lut

# %% ../../nbs/handlers/generic.ipynb 27
def load_data(fname):
    "Load generic MARIS data and return them as individual dataframe by sample type"
    dfs = {}
    df = pd.read_csv(fname)
    for name, group in df.groupby('samptype'):
        key = name.lower().replace(' ', '_')
        dfs[key] = group
    return dfs

def rename_cols(cols):
    "Flatten multiindex columns"
    new_cols = []
    for outer, inner in cols:
        if not inner:
            new_cols.append(outer)
        else:
            if outer == 'unc':
                new_cols.append(inner + '_' + outer)
            if outer == 'value':
                new_cols.append(inner)
    return new_cols

# %% ../../nbs/handlers/generic.ipynb 36
class RemapRdnNameCB(Callback):
    "Remap to MARIS radionuclide names"
    def __call__(self, tfm):
        lut = get_nuclides_lut()
        for k in tfm.dfs.keys():
            tfm.dfs[k]['nusymbol'].replace(lut, inplace=True)

# %% ../../nbs/handlers/generic.ipynb 39
class ParseTimeCB(Callback):
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['time'] = pd.to_datetime(tfm.dfs[k].begperiod, 
                                                format='%Y-%m-%d %H:%M:%S.%f')

# %% ../../nbs/handlers/generic.ipynb 57
# Define columns of interest by sample type
# coi_grp = {'seawater': ['NUCLIDE', 'VALUE_Bq/m³', 'ERROR%_m³', 'time',
#                         'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)'],
#            'sediment': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%_kg', 'time',
#                         'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)',
#                         'SEDI'],
#            'biota': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%', 'time',
#                      'SDEPTH', 'LATITUDE ddmmmm', 'LONGITUDE ddmmmm',
#                      'species_id', 'TISSUE']}

common_cols = ['area_id', 'lab_id', 'latitude', 'longitude', 'time',
               'totdepth', 'sampdepth', 'volume', 'salinity',
               'temperatur', 'nusymbol', 'activity', 'uncertaint', 'transect_id']

coi_grp = {'seawater': common_cols,
           'biota': common_cols + ['biogroup', 'taxondbid', 'bodypar_id',
                                   'species_id'],
           'sediment': common_cols + ['sedtype_id']
           }

# %% ../../nbs/handlers/generic.ipynb 58
# Define column names renaming rules
renaming_rules = {
    'latitude': 'lat',
    'longitude': 'lon',
    'totdepth': 'tot_depth',
    'sampdepth': 'depth',
    'temperatur': 'temp',
    'activity': 'value',
    'uncertaint': 'unc',
    
    # 'VALUE_Bq/m³': 'value',
    # 'VALUE_Bq/kg': 'value',
    # 'ERROR%_m³': 'unc',
    # 'ERROR%_kg': 'unc',
    # 'ERROR%': 'unc',
    # 'TDEPTH': 'depth',
    # 'SDEPTH': 'depth',
    # 'LATITUDE (dddddd)': 'lat',
    # 'LATITUDE ddmmmm': 'lat',
    # 'LONGITUDE (dddddd)': 'lon',
    # 'LONGITUDE ddmmmm': 'lon',
    # # group specific
    # 'TISSUE': 'body_part',
    # 'SEDI': 'sed_type'
}


# %% ../../nbs/handlers/generic.ipynb 59
class RenameColumnCB(Callback):
    def __init__(self,
                 coi=coi_grp,
                 renaming_rules=renaming_rules):
        fc.store_attr()

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            # Select cols of interest
            tfm.dfs[k] = tfm.dfs[k].loc[:, self.coi[k]]

            # Rename cols
            tfm.dfs[k].rename(columns=self.renaming_rules, inplace=True)

# %% ../../nbs/handlers/generic.ipynb 65
class ReshapeLongToWide(Callback):
    def __init__(self): fc.store_attr()

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            cols = ['nusymbol']
            vals = ['value', 'unc']
            idx = list(set(tfm.dfs[k].columns) -
                       set(cols + vals))  # All others

            tfm.dfs[k] = tfm.dfs[k].pivot_table(index=idx,
                                                columns=cols,
                                                values=vals).reset_index()

            # Flatten cols name
            tfm.dfs[k].columns = rename_cols(tfm.dfs[k].columns)

            # Set index
            tfm.dfs[k].index.name = 'sample'

# %% ../../nbs/handlers/generic.ipynb 85
kw = ['oceanography', 'Earth Science > Oceans > Ocean Chemistry> Radionuclides',
      'Earth Science > Human Dimensions > Environmental Impacts > Nuclear Radiation Exposure',
      'Earth Science > Oceans > Ocean Chemistry > Ocean Tracers, Earth Science > Oceans > Marine Sediments',
      'Earth Science > Oceans > Ocean Chemistry, Earth Science > Oceans > Sea Ice > Isotopes',
      'Earth Science > Oceans > Water Quality > Ocean Contaminants',
      'Earth Science > Biological Classification > Animals/Vertebrates > Fish',
      'Earth Science > Biosphere > Ecosystems > Marine Ecosystems',
      'Earth Science > Biological Classification > Animals/Invertebrates > Mollusks',
      'Earth Science > Biological Classification > Animals/Invertebrates > Arthropods > Crustaceans',
      'Earth Science > Biological Classification > Plants > Macroalgae (Seaweeds)']


# %% ../../nbs/handlers/generic.ipynb 86
def get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw):
    return GlobAttrsFeeder(tfm.dfs, cbs=[BboxCB(),
                                    DepthRangeCB(),
                                    TimeRangeCB(),
                                    ZoteroCB(zotero_key),
                                    KeyValuePairCB('keywords', ', '.join(kw)),
                                    KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))])()

# %% ../../nbs/handlers/generic.ipynb 89
def units_fn(grp_name):
    lut = {'seawater': 'Bq/m³',
           'sediment': 'Bq/kg',
           'biota': 'Bq/kg'}
    return lut[grp_name]


# %% ../../nbs/handlers/generic.ipynb 91
def encode(fname_in, fname_out, nc_tpl_path):
    dfs = load_data(fname_in)
    tfm = Transformer(dfs, cbs=[LowerStripRdnNameCB(),
                                RemapRdnNameCB(),
                                ParseTimeCB(),
                                NormalizeUncUnitCB(),
                                LookupBiotaSpeciesCB(partial(get_species_lut, fname_in)),
                                RenameColumnCB(),
                                ReshapeLongToWide(),
                                EncodeTimeCB(),
                                SanitizeLonLatCB()])
    
    dfs_tfm = tfm()
    attrs = get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw)
    to_netcdf(dfs_tfm, nc_tpl_path, fname_out, attrs, units_fn)