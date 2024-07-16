# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/handlers/netcdf_to_csv.ipynb.

# %% auto 0
__all__ = ['fname_in', 'fname_out', 'ref_id', 'netcdf4_to_df', 'ReshapeWideToLong', 'LookupTimeFromEncodedTime',
           'GetSampleTypeCB', 'get_nucnames_lut', 'LookupNuclideByIdCB', 'deg_to_dms', 'ConvertLonLatCB',
           'get_unitnames_lut', 'LookupUnitByIdCB', 'get_detectionlimitnames_lut', 'LookupValueTypeByIdCB',
           'get_species_lut', 'LookupSpeciesByIdCB', 'get_bodypart_lut', 'LookupBodypartByIdCB', 'get_sediments_lut',
           'LookupSedimentTypeByIdCB', 'get_renaming_rules_netcdf2OpenRefine', 'encode']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 4
from pathlib import Path # This module offers classes representing filesystem paths
import xarray as xr
from netCDF4 import Dataset
import pandas as pd
import xarray as xr
import numpy as np
from .callbacks import (Callback, Transformer,
                               EncodeTimeCB, SanitizeLonLatCB)
import fastcore.all as fc # package that brings fastcore functionality, see https://fastcore.fast.ai/.
from cftime import num2pydate 
from .configs import cfg, cdl_cfg, nuc_lut_path, unit_lut_path, detection_limit_lut_path, species_lut_path, bodyparts_lut_path, sediments_lut_path
from .serializers import OpenRefineCsvEncoder
from functools import reduce,partial

# %% ../nbs/handlers/netcdf_to_csv.ipynb 7
fname_in = '../../_data/output/100-HELCOM-MORS-2024.nc'
fname_out = '../../_data/output/helcom_from_netcdf.csv'
ref_id = 100 # OSPAR ref_id 191

# %% ../nbs/handlers/netcdf_to_csv.ipynb 9
def netcdf4_to_df(fname_in):  
    # Read nc file
    with Dataset(fname_in, "r", format='NETCDF4' ) as nc:
        # Read groups ('seawater', 'biota', 'sediment')
        groups= nc.groups.keys()
        # Read fill values 
        fill_value={}
        for group in groups:
            fill_value[group] = nc.groups[group].variables['sample'][:].fill_value
    
    # Create dictionary of dataframes
    dfs={}
    for group in groups:
        # Read dataset
        ds = xr.open_dataset(fname_in, group=group,  decode_times=False)
        # Create Pandas dataframe 
        dfs[group]=ds.to_dataframe()
        # If the index is not 'sample' then set the index to be 'sample'
        if dfs[group].index.name != 'sample':
            dfs[group].set_index("sample", inplace=True)
        # Drop the rows where 'sample' uses the fill_value.
        dfs[group]=dfs[group].drop(fill_value[group], axis=0, errors='ignore') 
    return(dfs)

# %% ../nbs/handlers/netcdf_to_csv.ipynb 15
class ReshapeWideToLong(Callback):
    "Convert data from wide to long with renamed columns."
    def __init__(self, columns='nuclide', values=['value']):
        fc.store_attr()
        # Retrieve all possible suffixes vars (e.g '_unc', '_dl', ...) from configs
        suff_cfg = [value['name'] for value in cdl_cfg()['vars']['suffixes'].values()]
        # Retrieve all possible nuclides
        nucs_cfg = pd.read_excel(nuc_lut_path())['nc_name'].to_list()
        nucs_cfg = [x for x in nucs_cfg if str(x) != 'nan'] # remove 'nan' from nuclide list
        # Retrieve all possible vars thats are not in vars suffixes
        self.vars_cfg=[x['name'] for var_key in cdl_cfg()['vars'].keys() for x in cdl_cfg()['vars'][var_key].values() if var_key != 'suffixes']
        # combine all possible nuclides with its suffixes.    
        value_name='value'
        derived_nucs_cols={value_name:nucs_cfg}     
        for suf in suff_cfg:
            derived_nucs_cols[suf]= [str(nuc)+str(suf) for nuc in nucs_cfg]
        self.derived_nucs_cols=derived_nucs_cols
           
    def melt(self, df):
        # Among all possible 'self.derived_nuc_cols' include the ones present in df.
        derived_nucs_cols={}
        for key,derived_nuc_cols in self.derived_nucs_cols.items():
            derived_nuc_cols = [col for col in derived_nuc_cols if col in df.columns]
            if derived_nuc_cols:
                derived_nucs_cols[key] = derived_nuc_cols
        
        # Among all possible 'self.vars_cfg' include the ones present in df.
        vars_cfg = [var for var in self.vars_cfg if var in df.columns]
        
        # Melt cols included in self.derived_nucs_cols        
        df=df.reset_index()  # Reset the index so 'sample' can be used with id_vars
        nuc_dfs={}

        for key,val in derived_nucs_cols.items():
            # Transpose nuclide_cols
            df_t=pd.melt(frame=df, id_vars=vars_cfg+['sample'], value_vars=val, var_name='nuclide', value_name=key)
            # Remove the key from thr nuclide columns (e.g '_unit', '_dl', etc.).
            df_t['nuclide']=df_t['nuclide'].str.replace(key, '')
            # Keep rows where 'key' value is not nan
            df_t=df_t[df_t[key].notna()]
            nuc_dfs[key]=df_t    
            
        # Merge dfs created from melt. 
        combine_on= vars_cfg + ['sample'] + ['nuclide']
        merged_df=reduce(lambda df1, df2: pd.merge(df1, df2,  how='left', left_on= combine_on, right_on = combine_on), nuc_dfs.values())
        
        # Keep rows where either value_name (i.e.Activity or MDA ) is not 'nan'.
        merged_df = merged_df[merged_df[['value']].notna().any(axis=1)]
                
        return (merged_df)
    
    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            tfm.dfs[grp] = self.melt(tfm.dfs[grp])


# %% ../nbs/handlers/netcdf_to_csv.ipynb 20
class LookupTimeFromEncodedTime(Callback):
    def __init__(self, cfg): fc.store_attr()
    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            tfm.dfs[grp]['Sampling start date'] = tfm.dfs[grp]['time'].apply(lambda row: self.format_date(row)) 
            tfm.dfs[grp]['Sampling start time'] = tfm.dfs[grp]['time'].apply(lambda row: self.format_time(row))
    
    def format_date(self, x): 
        date_time = num2pydate(x, units=self.cfg['units']['time'])
        date = date_time.strftime('%d-%b-%Y')
        return date
    
    def format_time(self, x): 
        date_time = num2pydate(x, units=self.cfg['units']['time'])
        time = date_time.strftime('%H:%M:%S') 
        return time

# %% ../nbs/handlers/netcdf_to_csv.ipynb 25
class GetSampleTypeCB(Callback):
    def __init__(self): fc.store_attr()
    def __call__(self, tfm):
        for k in tfm.dfs.keys():
            tfm.dfs[k]['Sample type'] = k.upper()
            

# %% ../nbs/handlers/netcdf_to_csv.ipynb 29
def get_nucnames_lut():
    df = pd.read_excel(nuc_lut_path(), usecols=['nc_name','nusymbol'])
    return df.set_index('nc_name').to_dict()['nusymbol']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 30
class LookupNuclideByIdCB(Callback):
    "Lookup MARIS nuclide_id."
    def __init__(self,
                 fn_lut=get_nucnames_lut):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut()
        for k in tfm.dfs.keys():
            tfm.dfs[k]['Nuclide'] = tfm.dfs[k]['nuclide'].replace(lut)
            tfm.dfs[k]['Nuclide']=tfm.dfs[k]['Nuclide'].str.strip()
            tfm.dfs[k]['Nuclide']=tfm.dfs[k]['Nuclide'].str.replace(',','_')
            
            

# %% ../nbs/handlers/netcdf_to_csv.ipynb 36
def deg_to_dms(deg, coordinate='lat'):
    """Convert from decimal degrees to degrees, minutes, seconds."""
    m, s = divmod(abs(deg)*3600, 60)
    d, m = divmod(m, 60)
    
    if deg < 0:
        if coordinate == 'lat':
            cord = 'S'
        elif coordinate == 'lon':
            cord = 'W'
    else:
        if coordinate == 'lat':
            cord = 'N' 
        elif coordinate == 'lon':
            cord = 'E'                       
        
    d, m = int(d), int(m)
    
    return pd.Series([d, m, s, cord])

# %% ../nbs/handlers/netcdf_to_csv.ipynb 37
class ConvertLonLatCB(Callback):
    "Convert from Longitude and Latitude DDD.DDDDD° to degrees, minutes, seconds and direction."
    def __init__(self, fn_convert=deg_to_dms):
        fc.store_attr()

    def __call__(self, tfm):
        for grp in tfm.dfs.keys():
            tfm.dfs[grp][['Latitude degrees','Latitude minutes','Latitude seconds','Latitude direction']] = tfm.dfs[grp]['lat'].apply(self.fn_convert, coordinate='lat')
            tfm.dfs[grp][['Longitude degrees','Longitude minutes','Longitude seconds','Longitude direction']] = tfm.dfs[grp]['lon'].apply(self.fn_convert, coordinate='lon')


# %% ../nbs/handlers/netcdf_to_csv.ipynb 42
def get_unitnames_lut():
    df = pd.read_excel(unit_lut_path(), usecols=['unit_id','unit'])
    return df.set_index('unit_id').to_dict()['unit']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 43
class LookupUnitByIdCB(Callback):
    "Lookup MARIS unit by unit_id."
    def __init__(self,
                 fn_lut=get_unitnames_lut):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut()
        for k in tfm.dfs.keys():
            tfm.dfs[k]['Unit'] = tfm.dfs[k]['_unit'].replace(lut)
                        

# %% ../nbs/handlers/netcdf_to_csv.ipynb 48
def get_detectionlimitnames_lut():
    df = pd.read_excel(detection_limit_lut_path(), usecols=['id','name'])
    return df.set_index('id').to_dict()['name']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 49
class LookupValueTypeByIdCB(Callback):
    "Lookup MARIS Value Type."
    def __init__(self,
                 fn_lut=get_detectionlimitnames_lut):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut()
        for k in tfm.dfs.keys():
            tfm.dfs[k]['Value type'] = tfm.dfs[k]['_dl'].replace(lut)
                        

# %% ../nbs/handlers/netcdf_to_csv.ipynb 56
def get_species_lut():
    df = pd.read_excel(species_lut_path(), usecols=['species_id','species'])
    return df.set_index('species_id').to_dict()['species']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 57
class LookupSpeciesByIdCB(Callback):
    "Lookup MARIS species by species_id."
    def __init__(self,
                 fn_lut=get_species_lut):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut()
        for k in tfm.dfs.keys():
            if 'species' in tfm.dfs[k].columns: 
                tfm.dfs[k]['Species'] = tfm.dfs[k]['species'].replace(lut)
                        

# %% ../nbs/handlers/netcdf_to_csv.ipynb 61
def get_bodypart_lut():
    df = pd.read_excel(bodyparts_lut_path(), usecols=['bodypar_id','bodypar'])
    return df.set_index('bodypar_id').to_dict()['bodypar']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 62
class LookupBodypartByIdCB(Callback):
    "Lookup MARIS bodypart by bodypar_id."
    def __init__(self,
                 fn_lut=get_bodypart_lut):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut()
        for k in tfm.dfs.keys():
            if 'body_part' in tfm.dfs[k].columns: 
                tfm.dfs[k]['Body part'] = tfm.dfs[k]['body_part'].replace(lut)
                        

# %% ../nbs/handlers/netcdf_to_csv.ipynb 66
def get_sediments_lut():
    df = pd.read_excel(sediments_lut_path(), usecols=['sedtype_id','sedtype'])
    return df.set_index('sedtype_id').to_dict()['sedtype']

# %% ../nbs/handlers/netcdf_to_csv.ipynb 67
class LookupSedimentTypeByIdCB(Callback):
    "Lookup MARIS sedtype by sedtype_id."
    def __init__(self,
                 fn_lut=get_sediments_lut):
        fc.store_attr()

    def __call__(self, tfm):
        lut = self.fn_lut()
        for k in tfm.dfs.keys():
            if 'sed_type' in tfm.dfs[k].columns: 
                tfm.dfs[k]['Sediment type'] = tfm.dfs[k]['sed_type'].replace(lut)
                        

# %% ../nbs/handlers/netcdf_to_csv.ipynb 71
# Define columns of interest (keys) and renaming rules (values).
def get_renaming_rules_netcdf2OpenRefine():
    vars = cdl_cfg()['vars']
    return {('seawater','biota', 'sediment') : {    
                                                        ## DEFAULT
                                                        'Sample type' : 'Sample type',
                                                        'Latitude degrees' : 'Latitude degrees',
                                                        'Latitude minutes' : 'Latitude minutes',
                                                        'Latitude seconds' : 'Latitude seconds',
                                                        'Latitude direction' : 'Latitude direction',
                                                        'Longitude degrees' : 'Longitude degrees',
                                                        'Longitude minutes' : 'Longitude minutes',
                                                        'Longitude seconds' : 'Longitude seconds', 
                                                        'Longitude direction' : 'Longitude direction', 
                                                        vars['defaults']['lat']['name'] : 'Latitude decimal',
                                                        vars['defaults']['lon']['name'] : 'Longitude decimal',
                                                        'Sampling start date' : 'Sampling start date',
                                                        'Sampling start time' : 'Sampling start time',
                                                        'Nuclide' : 'Nuclide',
                                                        'Value type': 'Value type',
                                                        'Unit' : 'Unit',
                                                        'value' : 'Activity or MDA',
                                                        vars['suffixes']['uncertainty']['name'] : 'Uncertainty',
                                                        #'data_provider_station_id' : 'Station ID',
                                                        #vars['defaults']['data_provider_sample_id']['name'] :'Sample ID',
                                                        #'profile_id' : 'Profile or transect ID',                                                        
                                                        #'Sampling method' : 'sampling_method'
                                                        #'Preparation method' : 'preparation_method'
                                                        #'Counting method' : 'counting_method'
                                                        #'Sample notes' : 'sample_notes'
                                                        #'Measurement notes' : 'measurement_notes'
                                                    },
                  ('seawater',) : {
                                ## SEAWATER
                                vars['defaults']['tot_depth']['name'] : 'Total depth',
                                vars['defaults']['smp_depth']['name'] : 'Sampling depth' ,
                                vars['suffixes']['salinity']['name'] : 'Salinity',
                                vars['suffixes']['temperature']['name'] : 'Temperature',
                                #vars['suffixes']['filtered']['name'] : 'Filtered' TODO: Include in NetCDF encoder. 
                                },
                  ('biota',) : { 
                                ## BIOTA
                                'Species' : 'Species',
                                'Body part' : 'Body part',
                                'bio_group' : vars['bio']['bio_group']['name'],
                                #'SDEPTH' : vars['defaults']['smp_depth']['name'],
                                #'dry_wet_ratio' : 'Dry/wet ratio'
                                #'Drying Method' : drying_method
                                
                                },
                  ('sediment',) : {
                                ## SEDIMENT
                                vars['defaults']['tot_depth']['name'] : 'Total depth',
                                'Sediment type' : 'Sediment type',
                                #'top' : 'Top',
                                #'bottom' : 'Bottom', 
                                #'dry_wet_ratio' : 'Dry/wet ratio'
                                #'Drying Method' : drying_method
                                }
                    }

# %% ../nbs/handlers/netcdf_to_csv.ipynb 76
def encode(fname_in, fname_out, ref_id=-1, **kwargs):
    dfs = netcdf4_to_df(fname_in)
    tfm = Transformer(dfs, cbs=[ReshapeWideToLong(),
                            LookupTimeFromEncodedTime(cfg()),
                            GetSampleTypeCB(),
                            LookupNuclideByIdCB(),
                            ConvertLonLatCB(), 
                            LookupUnitByIdCB(),
                            LookupValueTypeByIdCB(),
                            LookupSpeciesByIdCB(),
                            LookupBodypartByIdCB(),
                            LookupSedimentTypeByIdCB(),
                            SelectAndRenameColumnCB(get_renaming_rules_netcdf2OpenRefine)
                            ])
    
    encoder = OpenRefineCsvEncoder(tfm(), 
                            dest_fname=fname_out,
                            ref_id = ref_id,
                            **kwargs)
    encoder.encode()
    return encoder
