# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/handlers/ospar.ipynb.

# %% auto 0
__all__ = ['varnames_lut_updates', 'unmatched_fixes_biota_species', 'get_maris_species', 'whole_animal_plant',
           'unmatched_fixes_biota_tissues', 'renaming_unit_rules', 'coi_grp', 'kw', 'load_data', 'rename_cols',
           'LowerStripRdnNameCB', 'get_unique_nuclides', 'get_varnames_lut', 'RemapRdnNameCB', 'ParseTimeCB',
           'get_maris_lut', 'LookupBiotaSpeciesCB', 'CorrectWholeBodyPart', 'LookupBiotaBodyPartCB', 'get_biogroup_lut',
           'LookupBiogroupCB', 'LookupUnitCB', 'RemapValueUncertaintyDetectionLimit', 'ConvertLonLat',
           'CompareDfsAndTfm', 'get_renaming_rules', 'RenameColumnCB', 'ReshapeLongToWide', 'get_attrs', 'enums_xtra',
           'encode']

# %% ../../nbs/handlers/ospar.ipynb 7
import pandas as pd # Python package that provides fast, flexible, and expressive data structures.
import numpy as np
from tqdm import tqdm # Python Progress Bar Library
from functools import partial # Function which Return a new partial object which when called will behave like func called with the positional arguments args and keyword arguments keywords
import fastcore.all as fc # package that brings fastcore functionality, see https://fastcore.fast.ai/.
from pathlib import Path # This module offers classes representing filesystem paths
from dataclasses import asdict
import re # provides regular expression matching operations

from ..utils import (has_valid_varname, match_worms, match_maris_lut, Match)
from ..callbacks import (Callback, Transformer, EncodeTimeCB, SanitizeLonLatCB)
from ..metadata import (GlobAttrsFeeder, BboxCB, DepthRangeCB, TimeRangeCB, ZoteroCB, KeyValuePairCB)
from ..configs import (nc_tpl_path, cfg, cache_path, cdl_cfg, Enums, lut_path,
                             species_lut_path, bodyparts_lut_path)
from ..serializers import NetCDFEncoder



# %% ../../nbs/handlers/ospar.ipynb 15
def load_data(src_dir,
                smp_types=['Seawater data', 'Biota data']):
    "Load OSPAR data and return them as an individual dataframe by sample type"
    '''
    Load data from the measurement files and sample information files found 
    in the src_dir (i.e. fname_in).
    Returns a dictionary of pandas' dataframes. The key to the dictionary is 
    the sample type (i.e lut_smp_type)
    '''    
    dfs = {}
    lut_smp_type = {'Seawater data': 'seawater', 'Biota data': 'biota'}
    for smp_type in smp_types:
        fname_meas = smp_type + '.csv' # measurement (i.e. radioactivity) information and sample information     
        df = pd.read_csv(Path(src_dir)/fname_meas, encoding='unicode_escape')
        dfs[lut_smp_type[smp_type]] = df
    return dfs

# %% ../../nbs/handlers/ospar.ipynb 17
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

# %% ../../nbs/handlers/ospar.ipynb 33
class LowerStripRdnNameCB(Callback):
    "Drop NaN nuclide names, convert nuclide names to lowercase, strip separators (e.g. `-`,`,`) and any trailing space(s)"
    def __init__(self, fn_format_rdn): fc.store_attr()
    def __call__(self, tfm):        
        # Apply condition to Nuclide col. 
        for k in tfm.dfs.keys():
            # drop nan values
            tfm.dfs[k] = tfm.dfs[k][tfm.dfs[k]['Nuclide'].notna()]
            # Apply condition
            tfm.dfs[k]['nuclide'] = tfm.dfs[k]['Nuclide'].apply(lambda x: self.fn_format_rdn(x))
                
                
    

# %% ../../nbs/handlers/ospar.ipynb 43
def get_unique_nuclides(dfs):
    "Get list of unique radionuclide types measured across samples."
    nuclides = []
    for k in dfs.keys():
        nuclides += dfs[k]['nuclide'].unique().tolist()
    return nuclides

# %% ../../nbs/handlers/ospar.ipynb 48
varnames_lut_updates = {
    'pu239240': 'pu239_240_tot'}

# %% ../../nbs/handlers/ospar.ipynb 50
def get_varnames_lut(dfs, lut=varnames_lut_updates):
    lut = {n: n for n in set(get_unique_nuclides(dfs))}
    lut.update(varnames_lut_updates)
    return lut

# %% ../../nbs/handlers/ospar.ipynb 54
class RemapRdnNameCB(Callback):
    "Remap to MARIS radionuclide names."
    def __init__(self,
                 fn_lut=partial(get_varnames_lut, lut=varnames_lut_updates)):
        fc.store_attr()
        
    def __call__(self, tfm):       
        # Replace 'Nuclide' vars according to lut. 
        lut = self.fn_lut(tfm.dfs)
        for k in tfm.dfs.keys():
            tfm.dfs[k]['nuclide'].replace(lut, inplace=True)


# %% ../../nbs/handlers/ospar.ipynb 61
class ParseTimeCB(Callback):
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            # drop nan values
            tfm.dfs[k] = tfm.dfs[k][tfm.dfs[k]['Sampling date'].notna()]            
            tfm.dfs[k]['time'] = pd.to_datetime(tfm.dfs[k]['Sampling date'], 
                                                format='%d/%m/%Y')
                

# %% ../../nbs/handlers/ospar.ipynb 67
def get_maris_lut(df_biota,
                  fname_cache, # For instance 'species_ospar.pkl'
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

    if overwrite or (not fname_cache.exists()):        
        df = pd.DataFrame({data_provider_name_col : df_biota[data_provider_name_col].unique()})
        for _, row in tqdm(df.iterrows(), total=len(df)):
            
            # Fix if unmatched
            has_to_be_fixed = row[data_provider_name_col] in unmatched_fixes       
            name_to_match = unmatched_fixes[row[data_provider_name_col]] if has_to_be_fixed else row[data_provider_name_col]

            # Match
            result = match_maris_lut(maris_lut, name_to_match, maris_id, maris_name)
            match = Match(result.iloc[0][maris_id], result.iloc[0][maris_name], 
                        row[data_provider_name_col], result.iloc[0]['score'])
                    
            lut[row[data_provider_name_col]] = match
            
        fc.save_pickle(fname_cache, lut)
    else:
        lut = fc.load_pickle(fname_cache)

    if as_dataframe:
        df_lut = pd.DataFrame({k: asdict(v) for k, v in lut.items()}).transpose()
        df_lut.index.name = 'source_id'
        return df_lut.sort_values(by='match_score', ascending=False)
    else:
        return lut

# %% ../../nbs/handlers/ospar.ipynb 68
# key equals name in dfs['biota']. 
# value equals replacement name to use in match_maris_lut (i.e. name_to_match)
unmatched_fixes_biota_species = {}

# %% ../../nbs/handlers/ospar.ipynb 76
# LookupBiotaSpeciesCB filters 'Not available'. 
unmatched_fixes_biota_species = {'RHODYMENIA PSEUDOPALAMATA & PALMARIA PALMATA': 'Not available', # mix
 'Mixture of green, red and brown algae': 'Not available', #mix 
 'Solea solea (S.vulgaris)': 'Solea solea',
 'SOLEA SOLEA (S.VULGARIS)': 'Solea solea',
 'CERASTODERMA (CARDIUM) EDULE': 'Cerastoderma edule',
 'Cerastoderma (Cardium) Edule': 'Cerastoderma edule',
 'MONODONTA LINEATA': 'Phorcus lineatus',
 'NUCELLA LAPILLUS': 'Not available', # Droped. In worms 'Nucella lapillus (Linnaeus, 1758)', 
 'DICENTRARCHUS (MORONE) LABRAX': 'Dicentrarchus labrax',
 'Pleuronectiformes [order]': 'Pleuronectiformes',
 'RAJIDAE/BATOIDEA': 'Not available', #mix 
 'PALMARIA PALMATA': 'Not available', # Droped. In worms 'Palmaria palmata (Linnaeus) F.Weber & D.Mohr, 1805',
 'Sepia spp.': 'Sepia',
 'Rhodymenia spp.': 'Rhodymenia',
 'unknown': 'Not available',
 'RAJA DIPTURUS BATIS': 'Dipturus batis',
 'Unknown': 'Not available',
 'Flatfish': 'Not available',
 'FUCUS SPP.': 'FUCUS',
 'Patella sp.': 'Patella',
 'Gadus sp.': 'Gadus',
 'FUCUS spp': 'FUCUS',
 'Tapes sp.': 'Tapes',
 'Thunnus sp.': 'Thunnus',
 'RHODYMENIA spp': 'RHODYMENIA',
 'Fucus sp.': 'Fucus',
 'PECTINIDAE': 'Not available', # Droped. In worms as PECTINIDAE is a family.
 'PLUERONECTES PLATESSA': 'Pleuronectes platessa',
 'Gaidropsarus argenteus': 'Gaidropsarus argentatus'}

# %% ../../nbs/handlers/ospar.ipynb 79
class LookupBiotaSpeciesCB(Callback):
    """
    Biota species remapped to MARIS db:

    """
    def __init__(self, fn_lut, unmatched_fixes_biota_species): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut(df_biota=tfm.dfs['biota'])      
        # Drop rows where 'Species' are 'nan'
        tfm.dfs['biota'] = tfm.dfs['biota'][tfm.dfs['biota']['Species'].notna()]
        # Drop row in the dfs['biota] where the unmatched_fixes_biota_species value is 'Not available'. 
        na_list = ['Not available']     
        na_biota_species = [k for k,v in self.unmatched_fixes_biota_species.items() if v in na_list]
        tfm.dfs['biota'] = tfm.dfs['biota'][~tfm.dfs['biota']['Species'].isin(na_biota_species)]
        # Perform lookup 
        tfm.dfs['biota']['species'] = tfm.dfs['biota']['Species'].apply(lambda x: lut[x].matched_id)
        

# %% ../../nbs/handlers/ospar.ipynb 80
get_maris_species = partial(get_maris_lut, 
                fname_cache='species_ospar.pkl', 
                data_provider_name_col='SCIENTIFIC NAME',
                maris_lut=species_lut_path(),
                maris_id='species_id',
                maris_name='species',
                unmatched_fixes=unmatched_fixes_biota_species,
                as_dataframe=False,
                overwrite=False)

# %% ../../nbs/handlers/ospar.ipynb 86
whole_animal_plant = {'whole' : ['Whole','WHOLE', 'WHOLE FISH', 'Whole fisk', 'Whole fish'],
                      'Whole animal' : ['Molluscs','Fish','FISH','molluscs','fish','MOLLUSCS'],
                      'Whole plant' : ['Seaweed','seaweed','SEAWEED'] }

# %% ../../nbs/handlers/ospar.ipynb 87
class CorrectWholeBodyPart(Callback):
    """
    Update bodypart labeled as 'whole' to either 'Whole animal' or 'Whole plant'.
    """
    
    def __init__(self, wap=whole_animal_plant): fc.store_attr()
    
    def __call__(self, tfm):        
        tfm.dfs['biota'] = self.correct_whole_body_part(tfm.dfs['biota'],self.wap)

    def correct_whole_body_part(self, df, wap):
        whole_list= wap['whole']
        animal_list = wap['Whole animal']
        plant_lst = wap['Whole plant']
        df['body_part']=df['Body Part']   
        df['body_part'].loc[(df['body_part'].isin(whole_list)) & (df['Biological group'].isin(animal_list))] = 'Whole animal'
        df['body_part'].loc[(df['body_part'].isin(whole_list)) & (df['Biological group'].isin(plant_lst))] = 'Whole plant'
        
        return df

# %% ../../nbs/handlers/ospar.ipynb 90
unmatched_fixes_biota_tissues = {}

# %% ../../nbs/handlers/ospar.ipynb 101
class LookupBiotaBodyPartCB(Callback):
    """
    Update bodypart id based on MARIS dbo_bodypar.xlsx:
        - 3: 'Whole animal eviscerated without head',
        - 12: 'Viscera',
        - 8: 'Skin'
    """
    def __init__(self, fn_lut, unmatched_fixes_biota_tissues): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut(df_biota=tfm.dfs['biota'])      
        # Drop rows where 'Species' are 'nan'
        tfm.dfs['biota']=tfm.dfs['biota'][tfm.dfs['biota']['body_part'].notna()]
        # Drop row in the dfs['biota] where the unmatched_fixes_biota_species value is 'Not available'. 
        na_list = ['Not available']     
        na_biota_tissues = [k for k,v in self.unmatched_fixes_biota_tissues.items() if v in na_list]
        tfm.dfs['biota'] = tfm.dfs['biota'][~tfm.dfs['biota']['body_part'].isin(na_biota_tissues)]
        # Perform lookup         
        tfm.dfs['biota']['body_part'] = tfm.dfs['biota']['body_part'].apply(lambda x: lut[x].matched_id)

# %% ../../nbs/handlers/ospar.ipynb 107
def get_biogroup_lut(maris_lut):
    species = pd.read_excel(maris_lut)
    return species[['species_id', 'biogroup_id']].set_index('species_id').to_dict()['biogroup_id']

# %% ../../nbs/handlers/ospar.ipynb 108
class LookupBiogroupCB(Callback):
    """
    Update biogroup id  based on MARIS dbo_species.xlsx
    """
    def __init__(self, fn_lut): fc.store_attr()
    def __call__(self, tfm):
        lut = self.fn_lut()        
        tfm.dfs['biota']['bio_group'] = tfm.dfs['biota']['species'].apply(lambda x: lut[x])

# %% ../../nbs/handlers/ospar.ipynb 118
# Define unit names renaming rules
renaming_unit_rules = {'Bq/l': 1, #'Bq/m3'
                       'Bq/L': 1,
                       'BQ/L': 1,
                       'Bq/kg f.w.': 5, # Bq/kgw
                       'Bq/kg.fw' : 5,
                       'Bq/kg fw' : 5,
                       'Bq/kg f.w' : 5 
                       } 

# %% ../../nbs/handlers/ospar.ipynb 120
class LookupUnitCB(Callback):
    def __init__(self,
                 lut=renaming_unit_rules):
        fc.store_attr()
    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            # Drop rows where 'Species' are 'nan'
            tfm.dfs[grp]=tfm.dfs[grp][tfm.dfs[grp]['Unit'].notna()]
            # Perform lookup  
            tfm.dfs[grp]['unit'] = tfm.dfs[grp]['Unit'].apply(lambda x: np.int64(self.lut[x]))

# %% ../../nbs/handlers/ospar.ipynb 127
class RemapValueUncertaintyDetectionLimit(Callback):
    "Remamp activity value, activity uncertainty and detection limit to MARIS format."
    def __init__(self):
        fc.store_attr()

    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            tfm.dfs[grp]['detection_limit'] = np.where(tfm.dfs[grp]['Value type'] == '<', tfm.dfs[grp]['Activity or MDA'] , np.NaN)
            tfm.dfs[grp]['value'] = np.where(tfm.dfs[grp]['Value type'] == '=', tfm.dfs[grp]['Activity or MDA'] , np.NaN)
            tfm.dfs[grp]['uncertainty'] = np.where(tfm.dfs[grp]['Value type'] == '=', tfm.dfs[grp]['Uncertainty'] , np.NaN)


# %% ../../nbs/handlers/ospar.ipynb 132
class ConvertLonLat(Callback):
    "Convert Longitude and Latitude values to DDD.DDDDD°"
    def __init__(self):
        fc.store_attr()

    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            tfm.dfs[grp]['latitude'] = np.where(tfm.dfs[grp]['LatDir'].isin(['S']), ((tfm.dfs[grp]['LatD'] + tfm.dfs[grp]['LatM']/60 + tfm.dfs[grp]['LatS'] /(60*60))* (-1)), (tfm.dfs[grp]['LatD'] + tfm.dfs[grp]['LatM']/60 + tfm.dfs[grp]['LatS'] /(60*60)))
            tfm.dfs[grp]['longitude'] = np.where(tfm.dfs[grp]['LongDir'].isin(['W']), ((tfm.dfs[grp]['LongD'] + tfm.dfs[grp]['LongM']/60 + tfm.dfs[grp]['LongS'] /(60*60))* (-1)), (tfm.dfs[grp]['LongD'] + tfm.dfs[grp]['LongM']/60 + tfm.dfs[grp]['LongS'] /(60*60)))

# %% ../../nbs/handlers/ospar.ipynb 139
class CompareDfsAndTfm(Callback):
    "Create a dfs of dropped data. Data included in the DFS not in the TFM"
    def __init__(self, dfs_compare):
        fc.store_attr()

    def __call__(self, tfm):
        tfm.dfs_dropped={}
        tfm.compare_stats={}
        for grp in tfm.dfs.keys():
            dfs_all = self.dfs_compare[grp].merge(tfm.dfs[grp], on=self.dfs_compare[grp].columns.to_list(), how='left', indicator=True)
            tfm.dfs_dropped[grp]=dfs_all[dfs_all['_merge'] == 'left_only']  
            tfm.compare_stats[grp]= {'Number of rows dfs:' : len(self.dfs_compare[grp].index),
                                     'Number of rows tfm.dfs:' : len(tfm.dfs[grp].index),
                                     'Number of dropped rows:' : len(tfm.dfs_dropped[grp].index),
                                     'Number of rows tfm.dfs + Number of dropped rows:' : len(tfm.dfs[grp].index) + len(tfm.dfs_dropped[grp].index)
                                    }
            
            
                        

# %% ../../nbs/handlers/ospar.ipynb 146
# Define columns of interest by sample type
coi_grp = {'seawater': ['nuclide', 'value', 'uncertainty','detection_limit','unit', 'time', 'Sampling depth',
                        'latitude', 'longitude'],
           'biota': ['nuclide', 'value', 'uncertainty','detection_limit','unit', 'time', 'latitude', 'longitude',
                     'species', 'body_part', 'bio_group']}

# %% ../../nbs/handlers/ospar.ipynb 149
def get_renaming_rules():
    vars = cdl_cfg()['vars']
    # Define column names renaming rules
    return {
        'uncertainty': vars['suffixes']['uncertainty']['name'],
        'Sampling depth': vars['defaults']['depth']['name'],
        #'Sampling depth': vars['defaults']['smp_depth']['name'],
        'latitude': vars['defaults']['lat']['name'],
        'longitude': vars['defaults']['lon']['name'],
        'unit': vars['suffixes']['unit']['name'],
        'detection_limit': vars['suffixes']['detection_limit']['name']
    }

# %% ../../nbs/handlers/ospar.ipynb 150
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

# %% ../../nbs/handlers/ospar.ipynb 155
class ReshapeLongToWide(Callback):
    "Convert data from long to wide with renamed columns."
    def __init__(self, columns='nuclide', values=['value']):
        fc.store_attr()
        # Retrieve all possible derived vars (e.g 'unc', 'dl', ...) from configs
        self.derived_cols = [value['name'] for value in cdl_cfg()['vars']['suffixes'].values()]
    
    def renamed_cols(self, cols):
        "Flatten columns name"
        return [inner if outer == "value" else f'{inner}{outer}'
                if inner else outer
                for outer, inner in cols]

    def pivot(self, df):
        # Among all possible 'derived cols' select the ones present in df
        derived_coi = [col for col in self.derived_cols if col in df.columns]
        
        df.reset_index(names='sample', inplace=True)
        
        idx = list(set(df.columns) - set([self.columns] + derived_coi + self.values))
        return df.pivot_table(index=idx,
                              columns=self.columns,
                              values=self.values + derived_coi,
                              fill_value=np.nan,
                              aggfunc=lambda x: x
                              ).reset_index()

    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k] = self.pivot(tfm.dfs[k])
            tfm.dfs[k].columns = self.renamed_cols(tfm.dfs[k].columns)

# %% ../../nbs/handlers/ospar.ipynb 163
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


# %% ../../nbs/handlers/ospar.ipynb 164
def get_attrs(tfm, zotero_key, kw=kw):
    return GlobAttrsFeeder(tfm.dfs, cbs=[
        BboxCB(),
        DepthRangeCB(),
        TimeRangeCB(cfg()),
        ZoteroCB(zotero_key, cfg=cfg()),
        KeyValuePairCB('keywords', ', '.join(kw)),
        KeyValuePairCB('publisher_postprocess_logs', ', '.join(tfm.logs))
        ])()

# %% ../../nbs/handlers/ospar.ipynb 168
def enums_xtra(tfm, vars):
    "Retrieve a subset of the lengthy enum as 'species_t' for instance"
    enums = Enums(lut_src_dir=lut_path(), cdl_enums=cdl_cfg()['enums'])
    xtras = {}
    for var in vars:
        unique_vals = tfm.unique(var)
        if unique_vals.any():
            xtras[f'{var}_t'] = enums.filter(f'{var}_t', unique_vals)
    return xtras

# %% ../../nbs/handlers/ospar.ipynb 170
def encode(fname_in, fname_out, nc_tpl_path, **kwargs):
    dfs = load_data(fname_in)
    tfm = Transformer(dfs, cbs=[LowerStripRdnNameCB(get_rdn_format),
                                RemapRdnNameCB(),
                                ParseTimeCB(),
                                LookupBiotaSpeciesCB(get_maris_species, unmatched_fixes_biota_species),
                                CorrectWholeBodyPart(),
                                LookupBiotaBodyPartCB(get_maris_bodypart, unmatched_fixes_biota_tissues),
                                LookupBiogroupCB(partial(get_biogroup_lut, species_lut_path())),
                                LookupUnitCB(renaming_unit_rules),
                                RemapValueUncertaintyDetectionLimit(),
                                ConvertLonLat(),
                                EncodeTimeCB(cfg()),
                                #CompareDfsAndTfm(dfs),
                                RenameColumnCB(coi_grp, get_renaming_rules),
                                ReshapeLongToWide(),
                                SanitizeLonLatCB()
                                ])
    tfm()
    encoder = NetCDFEncoder(tfm.dfs, 
                            src_fname=nc_tpl_path,
                            dest_fname=fname_out, 
                            global_attrs=get_attrs(tfm, zotero_key='LQRA4MMK', kw=kw),
                            verbose=kwargs.get('verbose', False),
                            enums_xtra=enums_xtra(tfm, vars=['species', 'body_part'])
                           )
    encoder.encode()
