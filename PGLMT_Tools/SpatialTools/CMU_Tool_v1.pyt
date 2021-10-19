#-------------------------------------------------------------------------------
# Name:        CMU Tool 1.0
# Purpose:
# Author:      Molly Moore
# Created:     10/13/2021
#-------------------------------------------------------------------------------

######################################################################################################################################################
## Import packages and define environment settings
######################################################################################################################################################

import arcpy,os,sys,string
from getpass import getuser
import sqlite3 as lite
import pandas as pd

arcpy.env.overwriteOutput = True
arcpy.env.transferDomains = True

######################################################################################################################################################
## Define universal variables and functions
######################################################################################################################################################

def element_type(elcode):
    """Takes ELCODE as input and returns CMU element type code."""
    if elcode.startswith('AAAA'):
        et = 'AAAA'
    elif elcode.startswith('AAAB'):
        et = 'AAAB'
    elif elcode.startswith('AB'):
        et = 'AB'
    elif elcode.startswith('AF'):
        et = 'AF'
    elif elcode.startswith('AM'):
        et = 'AM'
    elif elcode.startswith('AR'):
        et = 'AR'
    elif elcode.startswith('C') or elcode.startswith('H'):
        et = 'CGH'
    elif elcode.startswith('ICMAL'):
        et = 'ICMAL'
    elif elcode.startswith('ILARA'):
        et = 'ILARA'
    elif elcode.startswith('IZSPN'):
        et = 'IZSPN'
    elif elcode.startswith('IICOL02'):
        et = 'IICOL02'
    elif elcode.startswith('IICOL'):
        et = 'IICOL'
    elif elcode.startswith('IIEPH'):
        et = 'IIEPH'
    elif elcode.startswith('IIHYM'):
        et = 'IIHYM'
    elif elcode.startswith('IILEP'):
        et = 'IILEP'
    elif elcode.startswith('IILEY') or elcode.startswith('IILEW') or elcode.startswith('IILEV') or elcode.startswith('IILEU'):
        et = 'IILEY'
    elif elcode.startswith('IIODO'):
        et = 'IIODO'
    elif elcode.startswith('IIORT'):
        et = 'IIORT'
    elif elcode.startswith('IIPLE'):
        et = 'IIPLE'
    elif elcode.startswith('IITRI'):
        et = 'IITRI'
    elif elcode.startswith('IMBIV'):
        et = 'IMBIV'
    elif elcode.startswith('IMGAS'):
        et = 'IMGAS'
    elif elcode.startswith('I'):
        et = 'I'
    elif elcode.startswith('N'):
        et = 'N'
    elif elcode.startswith('P'):
        et = 'P'
    else:
        arcpy.AddMessage("Could not determine element type")
        et = None
    return et

######################################################################################################################################################
## Begin toolbox
######################################################################################################################################################

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "CMU Tools v1"
        self.alias = "CMU Tools v1"
        self.canRunInBackground = False
        self.tools = [CreateCMU,FillAttributes]

######################################################################################################################################################
## Begin create CMU tool - this tool creates the core and supporting CMUs and fills their initial attributes
######################################################################################################################################################

class CreateCMU(object):
    def __init__(self):
        self.label = "1 Create CMU"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        site_name = arcpy.Parameter(
            displayName = "Site Name",
            name = "site_name",
            datatype = "GPString",
            parameterType = "Required",
            direction = "Input")

        site_desc = arcpy.Parameter(
            displayName = "Site Description",
            name = "site_desc",
            datatype = "GPString",
            parameterType = "Optional",
            direction = "Input")

        cpp_core = arcpy.Parameter(
            displayName = "Selected CPP Core(s)",
            name = "cpp_core",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        cpp_core.value = r'CPP\CPP Core'

        params = [site_name,site_desc,cpp_core]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, params):
        return

    def updateMessages(self, params):
        return

    def execute(self, params, messages):

        site_name = params[0].valueAsText
        site_desc = params[1].valueAsText
        cpp_core = params[2].valueAsText

        mem_workspace = "memory"

        cmu = r"PGLMT_v2\\CMU"
        spec_tbl = r"PNHP.DBO.CMU_SpeciesTable"

        eo_reps = r'W:\\Heritage\\Heritage_Data\\Biotics_datasets.gdb\\eo_reps'

######################################################################################################################################################
## create CMU shape and get CMU attributes
######################################################################################################################################################

        desc = arcpy.Describe(cpp_core)
        if not desc.FIDSet == '':
            pass
        else:
            arcpy.AddWarning("No CPP Cores are selected. Please make a selection and try again.")
            sys.exit()

        desc = arcpy.Describe(cmu)
        if not desc.FIDSet == '':
            arcpy.AddWarning("There is currently a selection on the CMU layer. Please clear the selection and try again.")
            sys.exit()
        else:
            pass

        arcpy.AddMessage("......")
        # create list of eo ids for all selected CPPs that are current or approved
        with arcpy.da.SearchCursor(cpp_core,["EO_ID","Status"]) as cursor:
            eoids = sorted({row[0] for row in cursor if row[1] != "n"})
        # create list of eo ids for all selected CPPs that are not approved
        with arcpy.da.SearchCursor(cpp_core,["EO_ID","Status"]) as cursor:
            excluded_eoids = sorted({row[0]for row in cursor if row[1] == "n"})

        # add reporting messages about which CPPs are being excluded
        if excluded_eoids:
            arcpy.AddWarning("Selected CPPs with the following EO IDs are being excluded because they were marked as not approved: "+ ','.join([str(x) for x in excluded_eoids]))
        else:
            pass

        # add reporting messages about which CPPs are being included and exit with message if no selected CPPs are current or approved.
        if len(eoids) != 0:
            arcpy.AddMessage("Selected CPPs with the following EO IDs are being used to create this CMU: "+','.join([str(x) for x in eoids]))
            arcpy.AddMessage("......")
        else:
            arcpy.AddWarning("Your CPP selection does not include any current or approved CPPs and we cannot proceed. Goodbye.")
            sys.exit()

        # create sql query based on number of CPPs included in query.
        if len(eoids) > 1:
            sql_query = '"EO_ID" in {}'.format(tuple(eoids))
        else:
            sql_query = '"EO_ID" = {}'.format(eoids[0])

        arcpy.AddMessage("Creating and attributing CMU core for site: "+ site_name)
        arcpy.AddMessage("......")
        # create cpp_core layer from selected CPPs marked as current or approved and dissolve to create temporary CMU geometry
        cpp_core_lyr = arcpy.MakeFeatureLayer_management(cpp_core, "cpp_core_lyr", sql_query)
        temp_cmu = os.path.join(mem_workspace,"temp_cmu")
        temp_cmu = arcpy.Dissolve_management(cpp_core_lyr, temp_cmu)

        # get geometry token from cmu
        with arcpy.da.SearchCursor(temp_cmu,"SHAPE@") as cursor:
            for row in cursor:
                geom = row[0]

        # calculate CMU_JOIN_ID which includes network username and the next highest tiebreaker for that username padded to 6 places
        username = getuser().lower()
        where = '"CMU_JOIN_ID" LIKE'+"'%{0}%'".format(username)
        with arcpy.da.SearchCursor(cmu, 'CMU_JOIN_ID', where_clause = where) as cursor:
            join_ids = sorted({row[0] for row in cursor})
        if len(join_ids) == 0:
            cmu_join_id = username + '000001'
        else:
            t = join_ids[-1]
            tiebreak = str(int(t[-6:])+1).zfill(6)
            cmu_join_id = username + tiebreak

        # test for unsaved edits - alert user to unsaved edits and end script
        try:
            # open editing session and insert new CMU record
            values = [site_name,"D",site_desc,cmu_join_id,geom]
            fields = ["SITE_NAME","STATUS","BRIEF_DESC","CMU_JOIN_ID","SHAPE@"]
            with arcpy.da.InsertCursor(cmu,fields) as cursor:
                cursor.insertRow(values)
        except RuntimeError:
            arcpy.AddWarning("You have unsaved edits in your CMU layer. Please save or discard edits and try again.")
            sys.exit()

######################################################################################################################################################
## Insert species records into CMU species table
######################################################################################################################################################

        SpeciesInsert = []
        # report which EOs were included in CMU and add EO records to list to be inserted into CMU species table
        arcpy.AddMessage("The following species records have been added to the CMU Species Table for CMU with site name, "+site_name+":")
        for eoid in eoids:
            with arcpy.da.SearchCursor(eo_reps, ["ELCODE","ELSUBID","SNAME","SCOMNAME","EO_ID"], '"EO_ID" = {}'.format(eoid)) as cursor:
                for row in cursor:
                    values = tuple([row[0],row[1],row[2],row[3],element_type(row[0]),row[4],cmu_join_id])
                    arcpy.AddMessage(values)
                    SpeciesInsert.append(values)
        arcpy.AddMessage("......")

        # insert EO records into CMU species table
        for insert in SpeciesInsert:
            with arcpy.da.InsertCursor(spec_tbl, ["ELCODE","ELSUBID","SNAME","SCOMNAME","ELEMENT_TYPE","EO_ID","CMU_JOIN_ID"]) as cursor:
                cursor.insertRow(insert)

        # report about EOs that overlap the CMU, but were not included in the CMU species table
        eo_reps_full = arcpy.MakeFeatureLayer_management(eo_reps,"eo_reps_full")
        arcpy.SelectLayerByLocation_management(eo_reps_full,"INTERSECT",temp_cmu,selection_type="NEW_SELECTION")
        arcpy.AddWarning("The following EO rep records intersected your CMU, but do not have a CPP drawn:")
        with arcpy.da.SearchCursor(eo_reps_full,["EO_ID","SNAME","SCOMNAME","LASTOBS_YR","EORANK","EO_TRACK","EST_RA","PREC_BCD"]) as cursor:
            for row in cursor:
                if row[0] not in eoids:
                    arcpy.AddWarning(row)
                else:
                    pass

        arcpy.AddMessage("......")
        arcpy.AddMessage("The initial CMU was created for site name, "+site_name+". Please make any necessary manual edits. Once spatial edits are complete, don't forget to run step 2. Fill CMU Spatial Attributes")

######################################################################################################################################################
## Begin fill CMU spatial attributes tool which finishes attributes that depend on manual edits
######################################################################################################################################################

class FillAttributes(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2 Fill CMU Spatial Attributes"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        cmu = arcpy.Parameter(
            displayName = "Selected CMU Layer",
            name = "cmu",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")
        cmu.value = r"PGLMT_v2\\CMU"

        pgc_cover = arcpy.Parameter(
            displayName = "PGC Cover Type Layer",
            name = "pgc_cover",
            datatype = "GPFeatureLayer",
            parameterType = "Required",
            direction = "Input")

        params = [cmu,pgc_cover]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, params):
        return

    def updateMessages(self, params):
        return

    def execute(self, params, messages):

        cmu = params[0].valueAsText
        pgc_cover = params[1].valueAsText

        mem_workspace = "memory"

        # define paths
        username = getuser().lower()
        muni = r'C:\\Users\\'+username+r'\\AppData\\Roaming\\Esri\\ArcGISPro\\Favorites\\StateLayers.Default.pgh-gis0.sde\\StateLayers.DBO.Boundaries_Political\\StateLayers.DBO.PaMunicipalities'
        pgl = r'C:\\Users\\'+username+r'\\AppData\\Roaming\\Esri\\ArcGISPro\\Favorites\\StateLayers.Default.pgh-gis0.sde\\StateLayers.DBO.Protected_Lands\\StateLayers.DBO.PGC_StateGameland'
        boundaries_tbl = r"PNHP.DBO.CMU_PoliticalBoundaries"
        cover_tbl = r"PNHP.DBO.PGC_CoverTypes"

        # check for selection on CMU layer and exit if there is no selection
        desc = arcpy.Describe(cmu)
        if not desc.FIDSet == '':
            pass
        else:
            arcpy.AddWarning("No CMUs are selected. Please make a selection and try again.")
            sys.exit()

        # create list of CMU Join IDs for selected CMUs
        with arcpy.da.SearchCursor(cmu,["CMU_JOIN_ID"]) as cursor:
            cmu_selected = sorted({row[0] for row in cursor})

        # start loop to attribute each selected CMU
        for c in cmu_selected:
            arcpy.AddMessage("Attributing CMU: "+c)
            arcpy.AddMessage("......")
            # delete previous records in boundaries table if they have same CMU Join ID
            with arcpy.da.UpdateCursor(boundaries_tbl,["CMU_JOIN_ID"]) as cursor:
                for row in cursor:
                    if row[0] == c:
                        cursor.deleteRow()
            # delete previous records in PGC cover types table if they have same CMU Join ID
            with arcpy.da.UpdateCursor(cover_tbl,["CMU_JOIN_ID"]) as cursor:
                for row in cursor:
                    if row[0] == c:
                        cursor.deleteRow()

            # make feature layer of cmu join id in loop
            sql_query = "CMU_JOIN_ID = '{}'".format(c)
            cmu_lyr = arcpy.MakeFeatureLayer_management(cmu, "cmu_lyr", sql_query)

######################################################################################################################################################
## calculate acres for CMU
######################################################################################################################################################

            # test for unsaved edits - alert user to unsaved edits and end script
            try:
                with arcpy.da.UpdateCursor(cmu_lyr,["ACRES","SHAPE@"]) as cursor:
                    for row in cursor:
                        acres = round(row[1].getArea("GEODESIC","ACRES"),3)
                        row[0] = acres
                        arcpy.AddMessage(c +" Acres: "+str(acres))
                        arcpy.AddMessage("......")
                        cursor.updateRow(row)
            except RuntimeError:
                arcpy.AddWarning("You have unsaved edits in your CMU layer. Please save or discard edits and try again.")
                sys.exit()

######################################################################################################################################################
## attribute boundaries table
######################################################################################################################################################

            # attribute the counties and municipalities based on those that intersect the CMU
            boundary_union = arcpy.Intersect_analysis([muni,pgl],os.path.join(mem_workspace,"boundary_union"))
            boundary_union_lyr = arcpy.MakeFeatureLayer_management(boundary_union,"boundary_union_lyr")
            arcpy.SelectLayerByLocation_management(boundary_union_lyr,"INTERSECT",cmu_lyr,selection_type="NEW_SELECTION")
            MuniInsert = []
            with arcpy.da.SearchCursor(boundary_union_lyr,["CountyName","FullName","NAME"]) as cursor:
                for row in cursor:
                    values = tuple([row[0].title(),row[1],"SGL "+row[2],c])
                    MuniInsert.append(values)
            arcpy.AddMessage(c + " Boundaries: ")
            for insert in MuniInsert:
                with arcpy.da.InsertCursor(boundaries_tbl,["COUNTY","MUNICIPALITY","SGL","CMU_JOIN_ID"]) as cursor:
                    arcpy.AddMessage(insert)
                    cursor.insertRow(insert)
            arcpy.AddMessage("......")

######################################################################################################################################################
## attribute pgc cover table
######################################################################################################################################################

            # tabulate intersection to get percent and cover type that overlaps cmu
            tab_area = arcpy.TabulateIntersection_analysis(cmu_lyr,arcpy.Describe(cmu_lyr).OIDFieldName,pgc_cover,os.path.join(mem_workspace,"tab_area"),"COVER_TYPE")
            # insert name and percent overlap of protected lands
            CoverInsert = []
            with arcpy.da.SearchCursor(tab_area,["COVER_TYPE","PERCENTAGE"]) as cursor:
                for row in cursor:
                    if row[0] is None:
                        pass
                    else:
                        values = tuple([row[0],round(row[1],2),c])
                        CoverInsert.append(values)
            arcpy.AddMessage(c + " Cover Types: ")
            if CoverInsert:
                for insert in CoverInsert:
                    with arcpy.da.InsertCursor(cover_tbl,["COVER_TYPE","PERCENT_","CMU_JOIN_ID"]) as cursor:
                        arcpy.AddMessage(insert)
                        cursor.insertRow(insert)
            else:
                arcpy.AddMessage("No cover types overlap the CMU.")
            arcpy.AddMessage("#########################################################")
            arcpy.AddMessage("#########################################################")

######################################################################################################################################################
######################################################################################################################################################
