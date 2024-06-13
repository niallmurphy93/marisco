# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/handlers/helcom.ipynb.

# %% auto 0
__all__ = ['varnames_lut_updates', 'coi_units_unc', 'unmatched_fixes_biota_species', 'get_maris_species',
           'unmatched_fixes_biota_tissues', 'get_maris_bodypart', 'unmatched_fixes_sediments', 'get_maris_sediments',
           'renaming_unit_rules', 'coi_grp', 'kw', 'load_data', 'rename_cols', 'LowerStripRdnNameCB',
           'get_unique_nuclides', 'get_varnames_lut', 'RemapRdnNameCB', 'ParseTimeCB', 'fix_units',
           'NormalizeUncUnitCB', 'get_maris_lut', 'LookupBiotaSpeciesCB', 'LookupBiotaBodyPartCB', 'LookupSedimentCB',
           'get_biogroup_lut', 'LookupBiogroupCB', 'LookupUnitCB', 'get_renaming_rules', 'RenameColumnCB',
           'ReshapeLongToWide', 'get_attrs', 'encode']

# %% ../../nbs/handlers/helcom.ipynb 6
import pandas as pd # Python package that provides fast, flexible, and expressive data structures.
import numpy as np
from tqdm import tqdm # Python Progress Bar Library
from functools import partial # Function which Return a new partial object which when called will behave like func called with the positional arguments args and keyword arguments keywords
import fastcore.all as fc # package that brings fastcore functionality, see https://fastcore.fast.ai/.
from pathlib import Path # This module offers classes representing filesystem paths
from dataclasses import asdict

from ..utils import (has_valid_varname, match_worms, match_maris_lut, Match)
from ..callbacks import (Callback, Transformer, EncodeTimeCB, SanitizeLonLatCB)
from ..metadata import (GlobAttrsFeeder, BboxCB, DepthRangeCB, TimeRangeCB, ZoteroCB, KeyValuePairCB)
from ..configs import (base_path, nc_tpl_path, cfg, cache_path, cdl_cfg,
                             species_lut_path, sediments_lut_path, bodyparts_lut_path)
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

# %% ../../nbs/handlers/helcom.ipynb 24
class LowerStripRdnNameCB(Callback):
    "Convert nuclide names to lowercase & strip any trailing space(s)"
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['NUCLIDE'] = tfm.dfs[k]['NUCLIDE'].apply(
                lambda x: x.lower().strip())

# %% ../../nbs/handlers/helcom.ipynb 28
def get_unique_nuclides(dfs):
    "Get list of unique radionuclide types measured across samples."
    nuclides = []
    for k in dfs.keys():
        nuclides += dfs[k]['NUCLIDE'].unique().tolist()
    return nuclides

# %% ../../nbs/handlers/helcom.ipynb 32
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

# %% ../../nbs/handlers/helcom.ipynb 34
def get_varnames_lut(dfs, lut=varnames_lut_updates):
    lut = {n: n for n in set(get_unique_nuclides(dfs))}
    lut.update(varnames_lut_updates)
    return lut

# %% ../../nbs/handlers/helcom.ipynb 36
class RemapRdnNameCB(Callback):
    "Remap to MARIS radionuclide names."
    def __init__(self,
                 fn_lut=partial(get_varnames_lut, lut=varnames_lut_updates)):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut(tfm.dfs)
        for k in tfm.dfs.keys():
            tfm.dfs[k]['NUCLIDE'].replace(lut, inplace=True)

# %% ../../nbs/handlers/helcom.ipynb 43
class ParseTimeCB(Callback):
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['time'] = pd.to_datetime(tfm.dfs[k].DATE, 
                                                format='%m/%d/%y %H:%M:%S')

# %% ../../nbs/handlers/helcom.ipynb 46
# Make measurement and uncertainty units consistent
def fix_units(df, meas_col, unc_col):
    return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 48
# Columns of interest
coi_units_unc = [('seawater', 'VALUE_Bq/m³', 'ERROR%_m³'),
                 ('biota', 'VALUE_Bq/kg', 'ERROR%'),
                 ('sediment', 'VALUE_Bq/kg', 'ERROR%_kg')]

# %% ../../nbs/handlers/helcom.ipynb 50
class NormalizeUncUnitCB(Callback):
    "Convert from relative error % to uncertainty of activity unit"
    def __init__(self, coi=coi_units_unc): fc.store_attr()

    def __call__(self, tfm):
        for grp, val, unc in self.coi:
            tfm.dfs[grp][unc] = self.fix_units(tfm.dfs[grp], val, unc)

    def fix_units(self, df, meas_col, unc_col):
        return df.apply(lambda row: row[unc_col] * row[meas_col]/100, axis=1)

# %% ../../nbs/handlers/helcom.ipynb 57
def get_maris_lut(fname_in, 
                  fname_cache, # For instance 'species_helcom.pkl'
                  data_provider_lut:str, # Data provider lookup table name
                  data_provider_id_col:str, # Data provider lookup column id of interest
                  data_provider_name_col:str, # Data provider lookup column name of interest
                  maris_lut:str, # MARIS source lookup table name and path
                  maris_id: str, # Id of MARIS lookup table nomenclature item to match
                  maris_name: str, # Name of MARIS lookup table nomenclature item to match
                  unmatched_fixes={},
                  as_dataframe=False,
                  overwrite=False
                 ):
    fname_cache = cache_path() / fname_cache
    lut = {}
    df = pd.read_csv(Path(fname_in) / data_provider_lut)
    if overwrite or (not fname_cache.exists()):
        for _, row in tqdm(df.iterrows(), total=len(df)):

            # Fix if unmatched
            has_to_be_fixed = row[data_provider_id_col] in unmatched_fixes            
            name_to_match = unmatched_fixes[row[data_provider_id_col]] if has_to_be_fixed else row[data_provider_name_col]

            # Match
            result = match_maris_lut(maris_lut, name_to_match, maris_id, maris_name)
            match = Match(result.iloc[0][maris_id], result.iloc[0][maris_name], 
                          row[data_provider_name_col], result.iloc[0]['score'])
            
            lut[row[data_provider_id_col]] = match
        fc.save_pickle(fname_cache, lut)
    else:
        lut = fc.load_pickle(fname_cache)

    if as_dataframe:
        df_lut = pd.DataFrame({k: asdict(v) for k, v in lut.items()}).transpose()
        df_lut.index.name = 'source_id'
        return df_lut.sort_values(by='match_score', ascending=False)
    else:
        return lut

# %% ../../nbs/handlers/helcom.ipynb 58
unmatched_fixes_biota_species = {
    'CARD EDU': 'Cerastoderma edule',
    'LAMI SAC': 'Saccharina latissima',
    'PSET MAX': 'Scophthalmus maximus',
    'STIZ LUC': 'Sander luciopercas'}

# %% ../../nbs/handlers/helcom.ipynb 64
class LookupBiotaSpeciesCB(Callback):
    """
    Biota species remapped to MARIS db:
        CARD EDU: Cerastoderma edule
        LAMI SAC: Saccharina latissima
        PSET MAX: Scophthalmus maximus
        STIZ LUC: Sander luciopercas
    """
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['species'] = tfm.dfs['biota']['RUBIN'].apply(lambda x: lut[x.strip()].matched_id)

# %% ../../nbs/handlers/helcom.ipynb 65
get_maris_species = partial(get_maris_lut,
                            fname_in, fname_cache='species_helcom.pkl', 
                            data_provider_lut='RUBIN_NAME.csv',
                            data_provider_id_col='RUBIN',
                            data_provider_name_col='SCIENTIFIC NAME',
                            maris_lut=species_lut_path(),
                            maris_id='species_id',
                            maris_name='species',
                            unmatched_fixes=unmatched_fixes_biota_species,
                            as_dataframe=False,
                            overwrite=False)

# %% ../../nbs/handlers/helcom.ipynb 69
unmatched_fixes_biota_tissues = {
    3: 'Whole animal eviscerated without head',
    12: 'Viscera',
    8: 'Skin'}

# %% ../../nbs/handlers/helcom.ipynb 72
class LookupBiotaBodyPartCB(Callback):
    """
    Update bodypart id based on MARIS dbo_bodypar.xlsx:
        - 3: 'Whole animal eviscerated without head',
        - 12: 'Viscera',
        - 8: 'Skin'
    """
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['body_part'] = tfm.dfs['biota']['TISSUE'].apply(lambda x: lut[x].matched_id)

# %% ../../nbs/handlers/helcom.ipynb 74
get_maris_bodypart = partial(get_maris_lut,
                             fname_in,
                             fname_cache='tissues_helcom.pkl', 
                             data_provider_lut='TISSUE.csv',
                             data_provider_id_col='TISSUE',
                             data_provider_name_col='TISSUE_DESCRIPTION',
                             maris_lut=bodyparts_lut_path(),
                             maris_id='bodypar_id',
                             maris_name='bodypar',
                             unmatched_fixes=unmatched_fixes_biota_tissues)

# %% ../../nbs/handlers/helcom.ipynb 78
unmatched_fixes_sediments = {
    #np.nan: 'Not applicable',
    -99: '(Not available)'
}

# %% ../../nbs/handlers/helcom.ipynb 81
get_maris_sediments = partial(
    get_maris_lut,
    fname_in, 
    fname_cache='sediments_helcom.pkl', 
    data_provider_lut='SEDIMENT_TYPE.csv',
    data_provider_id_col='SEDI',
    data_provider_name_col='SEDIMENT TYPE',
    maris_lut=sediments_lut_path(),
    maris_id='sedtype_id',
    maris_name='sedtype',
    unmatched_fixes=unmatched_fixes_sediments)

# %% ../../nbs/handlers/helcom.ipynb 82
class LookupSedimentCB(Callback):
    """
    Update sediment id  based on MARIS dbo_sedtype.xlsx
        -99: '(Not available)'
        - na: '(Not available)'
        - 56: '(Not available)'
        - 73: '(Not available)'
    """
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()

        # To check with Helcom
        tfm.dfs['sediment']['SEDI'] = dfs['sediment']['SEDI'].fillna(-99).astype('int')
        tfm.dfs['sediment']['SEDI'].replace(56, -99, inplace=True)
        tfm.dfs['sediment']['SEDI'].replace(73, -99, inplace=True)
        
        tfm.dfs['sediment']['sed_type'] = tfm.dfs['sediment']['SEDI'].apply(lambda x: lut[x].matched_id)

# %% ../../nbs/handlers/helcom.ipynb 86
def get_biogroup_lut(maris_lut):
    species = pd.read_excel(maris_lut)
    return species[['species_id', 'biogroup_id']].set_index('species_id').to_dict()['biogroup_id']

# %% ../../nbs/handlers/helcom.ipynb 87
class LookupBiogroupCB(Callback):
    """
    Update biogroup id  based on MARIS dbo_species.xlsx
    """
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()
        tfm.dfs['biota']['bio_group'] = tfm.dfs['biota']['species'].apply(lambda x: lut[x])

# %% ../../nbs/handlers/helcom.ipynb 90
# Define unit names renaming rules
renaming_unit_rules = {'VALUE_Bq/m³': 1, #'Bq/m3'
                       'VALUE_Bq/kg': 3 } #'Bq/kg'

# %% ../../nbs/handlers/helcom.ipynb 91
class LookupUnitCB(Callback):
    def __init__(self,
                 renaming_unit_rules=renaming_unit_rules):
        fc.store_attr()
    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            for k,v in self.renaming_unit_rules.items():
                if k in tfm.dfs[grp].columns:
                    tfm.dfs[grp]['unit'] = np.where(tfm.dfs[grp].loc[:,k].notna(), np.int64(v), np.int64(0))


# %% ../../nbs/handlers/helcom.ipynb 94
# Define columns of interest by sample type
coi_grp = {'seawater': ['NUCLIDE', 'VALUE_Bq/m³', 'ERROR%_m³', 'time',
                        'SDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)','unit', 'SALIN', 'TTEMP'],
           'sediment': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%_kg', 'time',
                        'TDEPTH', 'LATITUDE (dddddd)', 'LONGITUDE (dddddd)',
                        'sed_type','unit'],
           'biota': ['NUCLIDE', 'VALUE_Bq/kg', 'ERROR%', 'time',
                     'SDEPTH', 'LATITUDE ddmmmm', 'LONGITUDE ddmmmm',
                     'species', 'body_part','unit', 'bio_group']}

# %% ../../nbs/handlers/helcom.ipynb 95
def get_renaming_rules():
    vars = cdl_cfg()['vars']
    # Define column names renaming rules
    return {
        'NUCLIDE': 'nuclide',
        'VALUE_Bq/m³': 'value',
        'VALUE_Bq/kg': 'value',
        'ERROR%_m³': vars['suffixes']['uncertainty']['name'],
        'ERROR%_kg': vars['suffixes']['uncertainty']['name'],
        'ERROR%': vars['suffixes']['uncertainty']['name'],
        'SDEPTH': vars['defaults']['depth']['name'],
        'TDEPTH': vars['defaults']['depth']['name'],
        'LATITUDE (dddddd)': vars['defaults']['lat']['name'],
        'LATITUDE ddmmmm': vars['defaults']['lat']['name'],
        'LONGITUDE (dddddd)': vars['defaults']['lon']['name'],
        'LONGITUDE ddmmmm': vars['defaults']['lon']['name'],
        'SALIN': vars['suffixes']['salinity']['name'],
        'TTEMP': vars['suffixes']['temperature']['name'],
    }

# %% ../../nbs/handlers/helcom.ipynb 96
# Define column names renaming rules
#renaming_rules = {
#    'NUCLIDE': 'nuclide',
#    'VALUE_Bq/m³': 'value',
#    'VALUE_Bq/kg': 'value',
#    'ERROR%_m³': vars['suffixes']['uncertainty']['name'],
#    'ERROR%_kg': vars['suffixes']['uncertainty']['name'],
#    #'ERROR%': 'vars['suffixes']['uncertainty']['name'],
#    'SDEPTH': vars['defaults']['depth']['name'],
#    'LATITUDE (dddddd)': vars['defaults']['lat']['name'],
#    'LATITUDE ddmmmm': vars['defaults']['lat']['name'],
#    'LONGITUDE (dddddd)': vars['defaults']['lon']['name'],
#    'LONGITUDE ddmmmm': vars['defaults']['lon']['name'],
#    'SALIN': vars['suffixes']['salinity']['name'],
#    'TTEMP': vars['suffixes']['temperature']['name'],
#}


# %% ../../nbs/handlers/helcom.ipynb 97
class RenameColumnCB(Callback):
    def __init__(self,
                 coi,
                 fn_renaming_rules,
                ):
        fc.store_attr()

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            # Select cols of interest
            tfm.dfs[k] = tfm.dfs[k].loc[:, self.coi[k]]

            # Rename cols
            tfm.dfs[k].rename(columns=self.fn_renaming_rules(), inplace=True)

# %% ../../nbs/handlers/helcom.ipynb 100
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

# %% ../../nbs/handlers/helcom.ipynb 113
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


# %% ../../nbs/handlers/helcom.ipynb 114
def get_attrs(tfm, zotero_key='26VMZZ2Q', kw=kw):
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(cfg()),
        ZoteroCB(zotero_key, cfg=cfg()),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()

# %% ../../nbs/handlers/helcom.ipynb 120
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
