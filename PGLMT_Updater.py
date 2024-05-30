"""
Name:       PGLMT - CPP Exporter
Purpose:    This script should be run to update the CPP cores and ET that are used for the PGLMT service. For CPPs to be 
            used with PGLMT, they must be state or federal listed species whose core polygons intersect a State Game Land.
            Here are the steps within the script:
            1. Filter ET for all state or federal listed species and get elsubids for qualifying species
            2. Create CPP core feature layer with ONLY elsubids that qualify for PGLMT
            3. Create SGL feature layer from PGC rest endpoint and buffer by 1 mile
            4. Select qualifying CPP cores that intersect the SGL layer
            5. Clip selected CPP cores to the 1 mile buffer on SGLs
            6. Delete features from the PGLMT Core Habitat layer in the PGLMT service
            7. Add updated set of CPP cores to the PGLMT Core Habitat layer in the PGLMT service
            8. Filter ET based on what species were included in the PGLMT Core Habitat layer
            9. Delete all ET records in the PGLMT ET service layer
            10. Add updated set of ET records to PGLMT ET service layer
            11. Fill related values in PGLMT ET service layer with reference table information (includes matrix values and habitat values)
            12. Update rank codes with rank descriptions in PGLMT ET service layer
            13. Update Y/N codes with Yes/No descriptions in PGLMT ET service layer
SETUP and LIMITATIONS:
            1. Need to set up WPC GIS Portal username and password variables in environment variables to run this on your computer
                - the first half of this video shows how to set up environment variables: https://www.youtube.com/watch?v=NDbr32xMUDQ&t=421s
                - when setting up environment variables, "Variable name" for your username and password should be "wpc_portal_username" and "wpc_gis_password" respectively 
                - when setting up environment variables, "Variable value" should be your personal username or password
                - if you change your WPC GIS Portal password, you will need to update your environment variables
            2. If a rest endpoint address changes, the url will need to be changed under the section where paths are defined
            3. For now, a direct connection must be made to the Pittsburgh network and you must have a connection to the WORKING VERSION of the PNHP .sde geodatabase that is named "PNHP_Working_pgh-gis0.sde" saved in your favorites
            4. This needs to be run with Python 3.xx interpreter that has access to ArcGIS licensing
WISH LIST ITEMS:
            1. Update PNHP data to use rest endpoints instead of direct connection to the .sde database - this needs to be done after moving the data to Portal            

Author:     Molly Moore
Created:    2024-05-10

Updated:
"""""

# import system modules
import os
import arcpy
import arcgis
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.features import FeatureSet
import pandas as pd

# load gis credentials from OS environment variables - need to set up Windows environment variables in order for this to work - see information in the script header for instructions
wpc_gis_username = os.environ.get("wpc_portal_username")
wpc_gis_password = os.environ.get("wpc_gis_password")
# this connects to GIS portal with username and password
gis = GIS("https://gis.waterlandlife.org/portal", wpc_gis_username, wpc_gis_password)

# define paths to datasets and urls for rest endpoints
workspace = r"C://Users//mmoore//AppData//Roaming//Esri//ArcGISPro//Favorites//PNHP_Working_pgh-gis0.sde" # for now, to access CPPs and Biotics ET,you must have a direct connection to the Pittsburgh network and a connection to the WORKING VERSION of the PNHP .sde geodatabase must be made and named "PNHP_Working_pgh-gis0.sde"
cpp_core = os.path.join(workspace,r"PNHP.DBO.CPPConservationPlanningPolygons//PNHP.DBO.CPP_Core")
biotics_et = os.path.join(workspace,r"PNHP.DBO.ET")
sgl_url = r"https://pgcmaps.pa.gov/arcgis/rest/services/PGC/NEW_PUBLIC/MapServer/17" # this is directly from the PGC public portal so should be most up to date SGLs and what we will use as the spatial layer in the Dashboard/Experience
pglmt_core_url = r"https://gis.waterlandlife.org/server/rest/services/Hosted/PGLMT/FeatureServer/0"
pglmt_et_url = r"https://gis.waterlandlife.org/server/rest/services/Hosted/PGLMT/FeatureServer/1"
BMP_matrix = r"https://gis.waterlandlife.org/server/rest/services/Hosted/PGLMT/FeatureServer/4"
species_habitats = r"https://gis.waterlandlife.org/server/rest/services/Hosted/PGLMT/FeatureServer/2"
rank_codes = r"https://gis.waterlandlife.org/server/rest/services/Hosted/PGLMT/FeatureServer/11"

# get feature layers from rest urls using the arcgis package
core_flayer = FeatureLayer(pglmt_core_url)
et_flayer = FeatureLayer(pglmt_et_url)

# make table view of only state and federal listed species from Biotics ET
state_listed_clause = "USESA = 'LE' OR USESA = 'LT' OR SPROT = 'PR' OR SPROT = 'PV' OR SPROT = 'TU' OR SPROT = 'PE' OR SPROT = 'PT' OR SPROT = 'PX' OR SPROT = 'PC'" # this is the query for all state and federal listed species codes
et_lyr = arcpy.MakeTableView_management(biotics_et,"et_lyr",state_listed_clause)

# create list of ELSUBIDs for state and federal listed species
state_listed_elsubids = sorted({row[0] for row in arcpy.da.SearchCursor(et_lyr,"ELSUBID")})

# create feature layer of CPP cores filtered by those that are state listed species
cpp_where_clause = "ELSUBID IN {0}".format(tuple(state_listed_elsubids)) # this is the query for CPPs whose ELSUBIDs are in the list created for state/federal listed species
cpp_core_lyr = arcpy.MakeFeatureLayer_management(cpp_core,"cpp_core_lyr",cpp_where_clause)

# create SGL feature layer from PGC rest endpoint
sgl = FeatureLayer(sgl_url) # create feature layer using arcgis package
sgl = sgl.query() # get features from feature layer
sgl_fc = sgl.save("memory", "sgl_fc") # save feature layer in memory workspace
# get albers custom spatial reference object and project SGL layer to albers
dessr = arcpy.Describe(cpp_core)
srr = dessr.spatialReference
sgl_project = arcpy.management.Project(sgl_fc, os.path.join("memory", "sgl_project"), srr)
# buffer the SGL layer by 1 mile to use as clip for CPPs
sgl_buffer = arcpy.analysis.PairwiseBuffer(sgl_project,os.path.join("memory","sgl_buffer"),"1 Mile")


# select state listed cores that intersect gamelands
arcpy.SelectLayerByLocation_management(cpp_core_lyr,"INTERSECT",sgl_project,"","NEW_SELECTION")
# clip CPP cores by buffered SGLs
cpp_core_clip = arcpy.analysis.PairwiseClip(cpp_core_lyr, sgl_buffer, os.path.join("memory","cpp_core_clip"))

######
###### this section deletes cpp cores and appends updated cpp cores to PGLMT service layer
# delete all features from PGLMT Core layer
core_flayer.delete_features(where="objectid > 0")

# create pandas spatial dataframe from CPP clip layer that we will use for updates
sdf = pd.DataFrame.spatial.from_featureclass(os.path.join("memory","cpp_core_clip"))
# deal with field name mismatches - if we change field names in feature service, then we will take this out
sdf.rename(columns={'ELSUBID':'elsubid', 'EO_ID':'eo_id', 'DrawnDate':'drawndate', 'BioticsExportDate':'bioticsexportdate', 'SpecID':'specid'}, inplace=True)
# limit fields in dataframe to reduce errors in fields that we aren't appending anyway
sdf = sdf[['elsubid','eo_id','drawndate','bioticsexportdate','specid','SHAPE']]
# fix null records in date field
sdf["bioticsexportdate"].fillna("01/01/1899", inplace = True)
# convert dataframe to feature set
fs = sdf.spatial.to_featureset()

# append selected state listed CPPs to PGLMT CPP layer
core_flayer.edit_features(adds = fs)
#########
#########

# create list of CPP ELSUBIDs to filter ET
PGLMT_elsubids = sorted({row[0] for row in arcpy.da.SearchCursor(cpp_core_lyr,"ELSUBID")})

# select ET records that have PGLMT CPP cores
et_where_clause = "ELSUBID IN {0}".format(tuple(PGLMT_elsubids))
et_view = arcpy.MakeTableView_management(biotics_et,"et_view",et_where_clause)

######
###### this section deletes et records and appends updated records to PGLMT service layer
# delete all records from PGLMT ET table
et_flayer.delete_features(where="objectid > 0")

# create pandas dataframe from ET view
fields = ['ELSUBID', 'ELCODE', 'SNAME', 'SCOMNAME', 'GRANK', 'SRANK', 'USESA', 'SPROT', 'SGCN', 'SENSITV_SP', 'EXPT_DATE']
sdf = pd.DataFrame((row for row in arcpy.da.SearchCursor("et_view", fields)), columns=fields)
# deal with field name mismatches - if we change field names in feature service, then we will take this out
sdf.rename(columns={'ELSUBID':'elsubid', 'ELCODE':'elcode', 'SNAME':'sname', 'SCOMNAME':'scomname', 'GRANK':'grank', 'SRANK':'srank', 'USESA':'usesa', 'SPROT':'sprot', 'SGCN':'sgcn', 'SENSITV_SP':'sensitv_sp', 'EXPT_DATE':'expt_date'}, inplace=True)
sdf = sdf[['elsubid','elcode','sname','scomname','grank','srank','usesa','sprot','sgcn','sensitv_sp','expt_date']]
# convert text field to date field
sdf['expt_date'] = pd.to_datetime(sdf['expt_date'])
# convert dataframe to feature set
fs = FeatureSet.from_dataframe(sdf)

# append selected state listed CPPs to PGLMT CPP layer
et_flayer.edit_features(adds = fs)
#######
#######

#### the section below is to fill related values from related tables - matrix and habitat tables
# define function to get dictionary of related table and fill target table with related values if keys match.
def FillRelated(related_table,related_key,related_info,target_table,target_key,target_info):
    related_dict = {}
    with arcpy.da.SearchCursor(related_table, [related_key,related_info]) as cursor:
        for row in cursor:
            related_dict[row[0]]=row[1]

    with arcpy.da.UpdateCursor(target_table,[target_key,target_info]) as cursor:
        for row in cursor:
            for k,v in related_dict.items():
                if k==row[0]:
                    row[1] = v
                    cursor.updateRow(row)

# fill PGLMT ET table with matrix values
matrix_values = ["forestry","fire","ag","whi","m_d","fed"]
for matrix in matrix_values:
    FillRelated(BMP_matrix,"elsubid",matrix,pglmt_et_url,"elsubid",matrix)

# fill PGLMT ET table with taxa and habitat values
FillRelated(species_habitats,"elsubid","taxa",pglmt_et_url,"elsubid","taxa_group")
FillRelated(species_habitats,"elsubid","habitat",pglmt_et_url,"elsubid","habitat")

# replace rank codes with descriptions from rank codes table
# create dictionary of rank codes and descriptions from rank code reference table
rank_dict = {}
with arcpy.da.SearchCursor(rank_codes, ["rank_abbr","rank_desc"]) as cursor:
    for row in cursor:
        rank_dict[row[0]] = row[1]

# fill rank descriptions based on rank abbreviations from rank codes reference
rank_fields = ["grank","srank","usesa","sprot"]
for field in rank_fields:
    with arcpy.da.UpdateCursor(pglmt_et_url,field) as cursor:
        for row in cursor:
            if row[0] is None:
                row[0] = "No Status"
            else:
                for k,v in rank_dict.items():
                    if k==row[0]:
                        row[0] = v
                        cursor.updateRow(row)

# update Y/N values to Yes/No descriptions in PGLMT ET
yes_fields = ["sgcn","sensitv_sp"]
for field in yes_fields:
    with arcpy.da.UpdateCursor(pglmt_et_url,field) as cursor:
        for row in cursor:
            if row[0] is None or row[0] == "N":
                row[0] = "No"
                cursor.updateRow(row)
            elif row[0] == "Y":
                row[0] = "Yes"
                cursor.updateRow(row)
            else:
                print("huh")
