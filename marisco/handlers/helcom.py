# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/handlers/helcom.ipynb.

# %% auto 0
__all__ = ['varnames_lut_updates', 'coi_units_unc', 'renaming_unit_rules', 'coi_grp', 'renaming_rules', 'kw', 'load_data',
           'rename_cols', 'LowerStripRdnNameCB', 'get_unique_nuclides', 'get_varnames_lut', 'RemapRdnNameCB',
           'ParseTimeCB', 'fix_units', 'NormalizeUncUnitCB', 'get_maris_species', 'get_worms_species',
           'LookupBiotaSpeciesCB', 'get_bodypart', 'LookupBiotaBodyPartCB', 'get_sediment', 'LookupSedimentCB',
           'LookupUnitCB', 'RenameColumnCB', 'ReshapeLongToWide', 'get_attrs', 'encode']

# %% ../../nbs/handlers/helcom.ipynb 6
import pandas as pd # Python package that provides fast, flexible, and expressive data structures.
import numpy as np
from tqdm import tqdm # Python Progress Bar Library
from functools import partial # Function which Return a new partial object which when called will behave like func called with the positional arguments args and keyword arguments keywords
import fastcore.all as fc # package that brings fastcore functionality, see https://fastcore.fast.ai/.
from pathlib import Path # This module offers classes representing filesystem paths


from ..utils import (has_valid_varname, match_worms, 
                           match_maris_species, match_maris_sediment)
from ..callbacks import (Callback, Transformer,
                               EncodeTimeCB, SanitizeLonLatCB)

from ..metadata import (GlobAttrsFeeder, BboxCB,
                              DepthRangeCB, TimeRangeCB,
                              ZoteroCB, KeyValuePairCB)

from ..configs import base_path, nc_tpl_path, cfg, cache_path
from ..serializers import NetCDFEncoder

# %% ../../nbs/handlers/helcom.ipynb 11
def load_data(src_dir,
                smp_types=['SEA', 'SED', 'BIO']):
    "Load HELCOM data and return the data in a dictionary of dataframes with the dictionary key as the sample type"
    dfs = {}
    lut_smp_type = {'SEA': 'seawater', 'SED': 'sediment', 'BIO': 'biota'}
    for smp_type in smp_types:
        fname_meas = smp_type + '02.csv' # measurement (i.e. radioactivity) information.
        fname_smp = smp_type + '01.csv' # sample information 
        df = pd.merge(pd.read_csv(Path(src_dir)/fname_meas),  # measurements
                      pd.read_csv(Path(src_dir)/fname_smp),  # sample
                      on='KEY', how='left')
        dfs[lut_smp_type[smp_type]] = df
    return dfs

# %% ../../nbs/handlers/helcom.ipynb 12
def rename_cols(cols):
    "Flatten multiindex columns"
    new_cols = []
    for outer, inner in cols:
        if not inner:
            new_cols.append(outer)
        else:
            if outer == 'unit':
                new_cols.append(inner + '_' + outer)
            if outer == 'unc':
                new_cols.append(inner + '_' + outer)
            if outer == 'value':
                new_cols.append(inner)
    return new_cols

# %% ../../nbs/handlers/helcom.ipynb 27
class LowerStripRdnNameCB(Callback):
    "Convert nuclide names to lowercase & strip any trailing space(s)"
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['NUCLIDE'] = tfm.dfs[k]['NUCLIDE'].apply(
                lambda x: x.lower().strip())

# %% ../../nbs/handlers/helcom.ipynb 31
def get_unique_nuclides(dfs):
    "Get list of unique radionuclide types measured across samples."
    nuclides = []
    for k in dfs.keys():
        nuclides += dfs[k]['NUCLIDE'].unique().tolist()
    return nuclides

# %% ../../nbs/handlers/helcom.ipynb 35
varnames_lut_updates = {
    'k-40': 'k40',
    'cm243244': 'cm243_244_tot',
    'cs134137': 'cs134_137_tot',
    'pu239240': 'pu239_240_tot',
    'pu238240': 'pu238_240_tot',
    'cs138': 'cs137',
    'cs139': 'cs137',
    'cs140': 'cs137',
    'cs141': 'cs137',
    'cs142': 'cs137',
    'cs143': 'cs137',
    'cs144': 'cs137',
    'cs145': 'cs137',
    'cs146': 'cs137'}

# %% ../../nbs/handlers/helcom.ipynb 37
def get_varnames_lut(dfs, lut=varnames_lut_updates):
    lut = {n: n for n in set(get_unique_nuclides(dfs))}
    lut.update(varnames_lut_updates)
    return lut

# %% ../../nbs/handlers/helcom.ipynb 39
class RemapRdnNameCB(Callback):
    "Remap to MARIS radionuclide names."
    def __init__(self,
                 fn_lut=partial(get_varnames_lut, lut=varnames_lut_updates)):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut(tfm.dfs)
        for k in tfm.dfs.keys():
            tfm.dfs[k]['NUCLIDE'].replace(lut, inplace=True)

# %% ../../nbs/handlers/helcom.ipynb 46
class ParseTimeCB(Callback):
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['time'] = pd.to_datetime(tfm.dfs[k].DATE, 
                                                format='%m/%d/%y %H:%M:%S')

# %% ../../nbs/handlers/helcom.ipynb 49
# Make measurement and uncertainty units consistent
def fix_units(df, meas_col, unc_col):
    return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 51
# Columns of interest
coi_units_unc = [('seawater', 'VALUE_Bq/m³', 'ERROR%_m³'),
                 ('biota', 'VALUE_Bq/kg', 'ERROR%'),
                 ('sediment', 'VALUE_Bq/kg', 'ERROR%_kg')]

# %% ../../nbs/handlers/helcom.ipynb 53
class NormalizeUncUnitCB(Callback):
    "Convert from relative error % to uncertainty of activity unit"
    def __init__(self, coi=coi_units_unc): fc.store_attr()

    def __call__(self, tfm):
        for grp, val, unc in self.coi:
            tfm.dfs[grp][unc] = self.fix_units(tfm.dfs[grp], val, unc)

    def fix_units(self, df, meas_col, unc_col):
        return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 59
def get_maris_species(fname_in, fname_cache, overwrite=False, verbose=False):
    fname_cache = cache_path() / fname_cache
    lut = {}
    df = pd.read_csv(Path(fname_in) / 'RUBIN_NAME.csv')
    
    if overwrite or (not fname_cache.exists()):
        if verbose:
            print('Source:Destination:Score')    
        for _, row in tqdm(df.iterrows(), total=df.shape[0]):
            match = match_maris_species(row['SCIENTIFIC NAME'])
            '''
            Include the source, destination and score in lut. 
            '''
            lut[row['RUBIN']] = {'id': match.iloc[0]['species_id'],'name': match.iloc[0]['species'],'source':  row["SCIENTIFIC NAME"], 'status':'marisco_cdl', 'match_type': match.iloc[0]['score']} 
            if verbose: 
                print(f'{row["SCIENTIFIC NAME"]}: {match.iloc[0]["species"]}: {match.iloc[0]["score"]}')
                # Return a verbose lut
                
        fc.save_pickle(fname_cache, lut)
    else:
        lut = fc.load_pickle(fname_cache)
        
    return lut    

# %% ../../nbs/handlers/helcom.ipynb 65
def get_worms_species(fname_in, fname_cache, load_lut=False, overwrite=False):
    fname_cache = cache_path() / fname_cache
    lut = {}

    if overwrite or (not fname_cache.exists()):
        df = pd.read_csv(Path(fname_in) / 'RUBIN_NAME.csv')
        
        if load_lut:
            '''
            open and read the LUT file
            '''
            lut = fc.load_pickle(fname_cache)
        
        for _, row in tqdm(df[['RUBIN', 'SCIENTIFIC NAME']].iterrows(), total=df.shape[0]):
            if load_lut:
                '''
                If row['RUBIN'] in LUT and match_type equals 0 then dont complete the lookup with WORMS. 
                '''
                if row['RUBIN'] in lut:
                    if lut[row['RUBIN']]['match_type'] == 0:
                        continue
            res = match_worms(row['SCIENTIFIC NAME'])
            if (res == -1):
                print(f"No match found for {row['RUBIN']} ({row['SCIENTIFIC NAME']})")
                id = -1 
                lut[row['RUBIN']] = {'id': id, 'name': '', 'source': row["SCIENTIFIC NAME"] ,'status': 'No match', 'match_type': 'No match', 'unacceptreason':'No match'}
            else:
                if len(res[0]) > 1:
                    print(f"Several matches for {row['RUBIN']} ({row['SCIENTIFIC NAME']})")
                    
                id, name, status, match_type,unacceptreason  = [res[0][0].get(key) 
                                                for key in ['AphiaID', 'scientificname', 'status', 'match_type','unacceptreason']]        
                
                lut[row['RUBIN']] = {'id': id, 'name': name, 'source': row["SCIENTIFIC NAME"] ,'status': status, 'match_type': match_type, 'unacceptreason':unacceptreason}
        fc.save_pickle(fname_cache, lut)
    else:
        lut = fc.load_pickle(fname_cache)
        
    return lut

# %% ../../nbs/handlers/helcom.ipynb 71
class LookupBiotaSpeciesCB(Callback):
    'Match species with MARIS database.'
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['species_id'] = tfm.dfs['biota']['RUBIN'].apply(
            lambda x: lut[x.strip()]['id'])
        # Remove data with a species_id of -1.
        tfm.dfs['biota']=tfm.dfs['biota'].drop(tfm.dfs['biota'][tfm.dfs['biota']['species_id'] == -1 ].index)

# %% ../../nbs/handlers/helcom.ipynb 75
def get_bodypart(verbose=False):
    "Naive lut - TO BE REFACTORED"
    lut={
        5: 52,
        1: 1,
        41: 1,
        3: 3,
        51: 54,
        43: 19,        
        42: 59,
        12: 20,
        10: 7,
        18: 25,
        52: 55,
        20: 38,
        8: 12,
        54: 57,
        53: 56,
        13:21}
    
    if verbose:
        marris_dbo_bodypar=pd.read_excel('../../nbs/files/lut/dbo_bodypar.xlsx')
        helcom_tissue=pd.read_csv('../../_data/accdb/mors/csv/TISSUE.csv')
        print ('marris_dbo_bodypar  :  helcom_tissue')
        for k, v in lut.items():
            print (str(helcom_tissue[helcom_tissue.TISSUE==int(k)].TISSUE_DESCRIPTION.values[0]) + '  :  ' + str(marris_dbo_bodypar[marris_dbo_bodypar.bodypar_id==v].bodypar.values[0]))   
    return lut

# %% ../../nbs/handlers/helcom.ipynb 76
class LookupBiotaBodyPartCB(Callback):
    'Update bodypart id based on MARIS dbo_bodypar.xlsx'
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['body_part'] = tfm.dfs['biota']['TISSUE'].apply(lambda x: lut[x])

# %% ../../nbs/handlers/helcom.ipynb 82
def get_sediment(verbose=False):
    lut = {}
    if verbose: print('Source:Destination')
    df_sediment = pd.read_csv(Path(fname_in) / 'SEDIMENT_TYPE.csv')
    
    for _, row in df_sediment.iterrows():
        match = match_maris_sediment(row['SEDIMENT TYPE'])
        lut[row['SEDI']] = match.iloc[0,0]
        if verbose: print(f'({row["SEDI"]}) {row["SEDIMENT TYPE"]}: ({match.iloc[0,0]}) {match.iloc[0,1]}')
    return lut   

# %% ../../nbs/handlers/helcom.ipynb 87
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

# %% ../../nbs/handlers/helcom.ipynb 91
# Define unit names renaming rules
renaming_unit_rules = { 'VALUE_Bq/m³': 1, #'Bq/m3'
                  'VALUE_Bq/kg': 3 #'Bq/kg'
                }
                  

# %% ../../nbs/handlers/helcom.ipynb 92
class LookupUnitCB(Callback):
    def __init__(self,
                 renaming_unit_rules=renaming_unit_rules):
        fc.store_attr()
    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            for k,v in self.renaming_unit_rules.items():
                if k in tfm.dfs[grp].columns:
                    tfm.dfs[grp]['unit'] = np.where(tfm.dfs[grp].loc[:,k].notna(), np.int64(v), np.int64(0))


# %% ../../nbs/handlers/helcom.ipynb 97
# Define columns of interest by sample type
coi_grp = {'seawater': ['NUCLIDE', 'VALUE_Bq/m³', 'ERROR%_m³', 'time',
                        'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)','unit'],
           'sediment': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%_kg', 'time',
                        'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)',
                        'sed_type','unit'],
           'biota': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%', 'time',
                     'SDEPTH', 'LATITUDE ddmmmm', 'LONGITUDE ddmmmm',
                     'species_id', 'body_part','unit']}


# %% ../../nbs/handlers/helcom.ipynb 98
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


# %% ../../nbs/handlers/helcom.ipynb 99
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

# %% ../../nbs/handlers/helcom.ipynb 104
class ReshapeLongToWide(Callback):
    def __init__(self): fc.store_attr()

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            cols = ['nuclide']
            #vals = ['value', 'unc']
            vals = ['value', 'unc', 'unit']
            
            idx = list(set(tfm.dfs[k].columns) -
                       set(cols + vals))  # All others

            tfm.dfs[k] = tfm.dfs[k].pivot_table(index=idx,
                                                columns=cols,
                                                values=vals).reset_index()
            
            # Flatten cols name
            tfm.dfs[k].columns = rename_cols(tfm.dfs[k].columns)
            
            # Update dtypes of unit
            date_cols = [col for col in tfm.dfs[k].columns if 'unit' in col]
            tfm.dfs[k][date_cols] = tfm.dfs[k][date_cols].fillna(0)
            tfm.dfs[k][date_cols] = tfm.dfs[k][date_cols].apply(lambda x: x.astype('int64'))
            
            #tfm.dfs[grp]['unit']=tfm.dfs[grp]['unit'].astype('int64')
            # Set index
            tfm.dfs[k].index.name = 'sample'

# %% ../../nbs/handlers/helcom.ipynb 117
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


# %% ../../nbs/handlers/helcom.ipynb 118
def get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw):
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(cfg()),
        ZoteroCB(zotero_key, cfg=cfg()),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()

# %% ../../nbs/handlers/helcom.ipynb 124
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
        LookupUnitCB(),        
        RenameColumnCB(),
        ReshapeLongToWide(),
        EncodeTimeCB(cfg()),
        SanitizeLonLatCB()
        ])
    
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
    return encoder
