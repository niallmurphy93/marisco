# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/handlers/helcom.ipynb.

# %% auto 0
__all__ = ['varnames_lut_updates', 'coi_units_unc', 'coi_grp', 'renaming_rules', 'kw', 'load_data', 'rename_cols',
           'LowerStripRdnNameCB', 'get_unique_nuclides', 'get_varnames_lut', 'RemapRdnNameCB', 'ParseTimeCB',
           'fix_units', 'NormalizeUncUnitCB', 'get_maris_species', 'get_worms_species', 'LookupBiotaSpeciesCB',
           'get_bodypart', 'LookupBiotaBodyPartCB', 'get_sediment', 'LookupSedimentCB', 'RenameColumnCB',
           'ReshapeLongToWide', 'get_attrs', 'encode']

# %% ../../nbs/handlers/helcom.ipynb 4
import pandas as pd
from tqdm import tqdm
from functools import partial
import fastcore.all as fc

from pathlib import Path

from ..utils import (has_valid_varname, match_worms, 
                           match_maris_species, match_maris_sediment)
from ..callbacks import (Callback, Transformer,
                               EncodeTimeCB, SanitizeLonLatCB)

from ..metadata import (GlobAttrsFeeder, BboxCB,
                              DepthRangeCB, TimeRangeCB,
                              ZoteroCB, KeyValuePairCB)

from ..configs import base_path, nc_tpl_path, cfg, cache_path
from ..serializers import NetCDFEncoder

# %% ../../nbs/handlers/helcom.ipynb 8
def load_data(src_dir,
                smp_types=['SEA', 'SED', 'BIO']):
    "Load HELCOM data and return them as individual dataframe by sample type"
    dfs = {}
    lut_smp_type = {'SEA': 'seawater', 'SED': 'sediment', 'BIO': 'biota'}
    for smp_type in smp_types:
        fname_meas = smp_type + '02.csv'
        fname_smp = smp_type + '01.csv'
        df = pd.merge(pd.read_csv(Path(src_dir)/fname_meas),  # measurements
                      pd.read_csv(Path(src_dir)/fname_smp),  # sample
                      on='KEY', how='left')
        dfs[lut_smp_type[smp_type]] = df
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

# %% ../../nbs/handlers/helcom.ipynb 17
class LowerStripRdnNameCB(Callback):
    "Convert nuclide names to lowercase & strip any trailing space(s)"

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['NUCLIDE'] = tfm.dfs[k]['NUCLIDE'].apply(
                lambda x: x.lower().strip())

# %% ../../nbs/handlers/helcom.ipynb 20
def get_unique_nuclides(dfs):
    "Get list of unique radionuclide types measured across samples."
    nuclides = []
    for k in dfs.keys():
        nuclides += dfs[k]['NUCLIDE'].unique().tolist()
    return nuclides

# %% ../../nbs/handlers/helcom.ipynb 22
varnames_lut_updates = {
    'k-40': 'k40',
    'cm243244': 'cm243_244_tot',
    'cs134137': 'cs134_137_tot',
    'pu239240': 'pu239_240_tot',
    'pu238240': 'pu238_240_tot'}


# %% ../../nbs/handlers/helcom.ipynb 23
def get_varnames_lut(dfs, lut=varnames_lut_updates):
    lut = {n: n for n in set(get_unique_nuclides(dfs))}
    lut.update(varnames_lut_updates)
    return lut


# %% ../../nbs/handlers/helcom.ipynb 25
class RemapRdnNameCB(Callback):
    "Remap to MARIS radionuclide names."
    def __init__(self,
                 fn_lut=partial(get_varnames_lut, lut=varnames_lut_updates)):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut(tfm.dfs)
        for k in tfm.dfs.keys():
            tfm.dfs[k]['NUCLIDE'].replace(lut, inplace=True)

# %% ../../nbs/handlers/helcom.ipynb 29
class ParseTimeCB(Callback):
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['time'] = pd.to_datetime(tfm.dfs[k].DATE, 
                                                format='%m/%d/%y %H:%M:%S')

# %% ../../nbs/handlers/helcom.ipynb 32
# Make measurement and uncertainty units consistent
def fix_units(df, meas_col, unc_col):
    return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 33
# Columns of interest
coi_units_unc = [('seawater', 'VALUE_Bq/m³', 'ERROR%_m³'),
                 ('biota', 'VALUE_Bq/kg', 'ERROR%'),
                 ('sediment', 'VALUE_Bq/kg', 'ERROR%_kg')]

# %% ../../nbs/handlers/helcom.ipynb 34
class NormalizeUncUnitCB(Callback):
    "Convert uncertainty from % to activity unit"

    def __init__(self, coi=coi_units_unc): fc.store_attr()

    def __call__(self, tfm):
        for grp, val, unc in self.coi:
            tfm.dfs[grp][unc] = self.fix_units(tfm.dfs[grp], val, unc)

    def fix_units(self, df, meas_col, unc_col):
        return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 35
class NormalizeUncUnitCB(Callback):
    "Convert uncertainty from % to activity unit"

    def __init__(self, coi=coi_units_unc): fc.store_attr()

    def __call__(self, tfm):
        for grp, val, unc in self.coi:
            tfm.dfs[grp][unc] = self.fix_units(tfm.dfs[grp], val, unc)

    def fix_units(self, df, meas_col, unc_col):
        return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 41
def get_maris_species(fname_in, fname_cache, overwrite=False, verbose=False):
    fname_cache = cache_path() / fname_cache
    lut = {}
    df = pd.read_csv(Path(fname_in) / 'RUBIN_NAME.csv')
    
    if overwrite or (not fname_cache.exists()):
        if verbose: print('Source:Destination')    
        for _, row in tqdm(df.iterrows(), total=df.shape[0]):
            match = match_maris_species(row['SCIENTIFIC NAME'])
            lut[row['RUBIN']] = {'id': match.iloc[0]['species_id'], 'name': match.iloc[0]['species']}
            if verbose: print(f'{row["SCIENTIFIC NAME"]}: {match.iloc[0]["species"]}')
        fc.save_pickle(fname_cache, lut)
    else:
        lut = fc.load_pickle(fname_cache)
        
    return lut        

# %% ../../nbs/handlers/helcom.ipynb 43
def get_worms_species(fname_in, fname_cache, overwrite=False):
    fname_cache = cache_path() / fname_cache
    lut = {}

    if overwrite or (not fname_cache.exists()):
        df = pd.read_csv(Path(fname_in) / 'RUBIN_NAME.csv')
        
        for _, row in tqdm(df[['RUBIN', 'SCIENTIFIC NAME']].iterrows(), total=df.shape[0]):
            res = match_worms(row['SCIENTIFIC NAME'])
            if (res == -1):
                print(f"No match for {row['RUBIN']} ({row['SCIENTIFIC NAME']})")
                id = -1
                lut[row['RUBIN']] = {'id': id, 'name': '', 'status': '', 'match_type': ''}
            else:
                if len(res[0]) > 1:
                    print(f"Several matches for {row['RUBIN']} ({row['SCIENTIFIC NAME']})")
                    
                id, name, status, match_type = [res[0][0].get(key) 
                                                for key in ['AphiaID', 'scientificname', 'status', 'match_type']]        
                
                lut[row['RUBIN']] = {'id': id, 'name': name, 'status': status, 'match_type': match_type}
        fc.save_pickle(fname_cache, lut)
    else:
        lut = fc.load_pickle(fname_cache)
        
    return lut

# %% ../../nbs/handlers/helcom.ipynb 45
class LookupBiotaSpeciesCB(Callback):
    'Match species with MARIS database.'
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['species_id'] = tfm.dfs['biota']['RUBIN'].apply(
            lambda x: lut[x.strip()]['id'])

# %% ../../nbs/handlers/helcom.ipynb 49
def get_bodypart():
    "Naive lut - TO BE REFACTORED"
    return {
        5: 52, 1: 1,
        41: 1, 3: 3,
        51: 54, 43: 19,
        42: 59, 12: 20,
        10: 7, 18: 25,
        52: 55, 20: 38,
        8: 12, 54: 57,
        53: 56}

# %% ../../nbs/handlers/helcom.ipynb 50
class LookupBiotaBodyPartCB(Callback):
    'Update bodypart id based on MARIS dbo_bodypar.xlsx'
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['body_part'] = tfm.dfs['biota']['TISSUE'].apply(lambda x: lut[x])

# %% ../../nbs/handlers/helcom.ipynb 55
def get_sediment(verbose=False):
    lut = {}
    if verbose: print('Source:Destination')
    df_sediment = pd.read_csv(Path(fname_in) / 'SEDIMENT_TYPE.csv')
    for _, row in df_sediment.iterrows():
        match = match_maris_sediment(row['SEDIMENT TYPE'])
        lut[row['SEDI']] = match.iloc[0,0]
        if verbose: print(f'({row["SEDI"]}) {row["SEDIMENT TYPE"]}: ({match.iloc[0,0]}) {match.iloc[0,1]}')
    return lut        

# %% ../../nbs/handlers/helcom.ipynb 60
class LookupSedimentCB(Callback):
    'Update sediment id  based on MARIS dbo_sedtype.xlsx'
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['sediment']['SEDI'] = dfs['sediment']['SEDI'].fillna(-99).astype('int')
        # To check with Helcom
        tfm.dfs['sediment']['SEDI'].replace(56, -99, inplace=True)
        tfm.dfs['sediment']['SEDI'].replace(73, -99, inplace=True)
        tfm.dfs['sediment']['sed_type'] = tfm.dfs['sediment']['SEDI'].apply(lambda x: lut[x])

# %% ../../nbs/handlers/helcom.ipynb 63
# Define columns of interest by sample type
coi_grp = {'seawater': ['NUCLIDE', 'VALUE_Bq/m³', 'ERROR%_m³', 'time',
                        'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)'],
           'sediment': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%_kg', 'time',
                        'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)',
                        'sed_type'],
           'biota': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%', 'time',
                     'SDEPTH', 'LATITUDE ddmmmm', 'LONGITUDE ddmmmm',
                     'species_id', 'body_part']}


# %% ../../nbs/handlers/helcom.ipynb 64
# Define column names renaming rules
renaming_rules = {
    'NUCLIDE': 'nuclide',
    'VALUE_Bq/m³': 'value',
    'VALUE_Bq/kg': 'value',
    'ERROR%_m³': 'unc',
    'ERROR%_kg': 'unc',
    'ERROR%': 'unc',
    'TDEPTH': 'depth',
    'SDEPTH': 'depth',
    'LATITUDE (dddddd)': 'lat',
    'LATITUDE ddmmmm': 'lat',
    'LONGITUDE (dddddd)': 'lon',
    'LONGITUDE ddmmmm': 'lon'
}


# %% ../../nbs/handlers/helcom.ipynb 65
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

# %% ../../nbs/handlers/helcom.ipynb 68
class ReshapeLongToWide(Callback):
    def __init__(self): fc.store_attr()

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            cols = ['nuclide']
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

# %% ../../nbs/handlers/helcom.ipynb 78
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


# %% ../../nbs/handlers/helcom.ipynb 79
def get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw):
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(cfg()),
        ZoteroCB(zotero_key, cfg=cfg()),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()

# %% ../../nbs/handlers/helcom.ipynb 84
def encode(fname_in, fname_out, nc_tpl_path, **kwargs):
    dfs = load_data(fname_in)
    tfm = Transformer(dfs, cbs=[
        LowerStripRdnNameCB(),
        RemapRdnNameCB(),
        ParseTimeCB(),
        NormalizeUncUnitCB(),
        LookupBiotaSpeciesCB(partial(get_maris_species, 
                                     fname_in, 'species_helcom.pkl')),
        LookupBiotaBodyPartCB(get_bodypart),
        LookupSedimentCB(get_sediment),
        RenameColumnCB(),
        ReshapeLongToWide(),
        EncodeTimeCB(cfg()),
        SanitizeLonLatCB()])
    
    species_lut = get_maris_species(fname_in, 'species_helcom.pkl')
    enums_xtra = {
        'species_t': {info['name']: info['id'] 
                      for info in species_lut.values() if info['name'] != ''}
    }
    
    encoder = NetCDFEncoder(tfm(), 
                            src_fname=nc_tpl_path,
                            dest_fname=fname_out, 
                            global_attrs=get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw),
                            enums_xtra=enums_xtra,
                            **kwargs)
    encoder.encode()
