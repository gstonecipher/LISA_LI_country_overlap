# -*- coding: utf-8 -*-
"""
Created on Tue Dec 14 23:52:19 2021

@author: grace

This script replicates the Linear Infrastructure Safeguards for Asia (LISA) project spatial
analysis at the country level
"""

import arcpy
from arcpy.sa import Int
import pandas as pd

arcpy.env.overwriteOutput = True
arcpy.env.workspace =r"C:\Users\grace\OneDrive\Documents\1_PSU\GEOG485\FinalProject" #set workspace

#Input country of interest
#Country should be one of the following: 'Afghanistan', 'Bangladesh', 'Bhutan', 'BruneiDarussalam', 'Cambodia', 
#'China', 'India', 'Indonesia', 'Japan', 'Kazakhstan', 'Kyrgyzstan', 'Laos', 'Malaysia', 'Mongolia', 'Myanmar', 
#'Nepal', 'NorthKorea', 'Pakistan', 'Philippines', 'SouthKorea', 'SriLanka', 'Tajikistan', 'Thailand', 
#'TimorLeste', 'Turkmenistan', 'Uzbekistan', 'Vietnam'
countryInput = 'SriLanka'

# import feature classes and rasters
liFC = "proposed_linear_infrastructure.shp"
countriesFC = "final_asian_countries_formatted.shp"
paFC = "WDPA_1a_1b_2.shp"
bio70Rast = "national_large_biodiversity_cores_70th_percentile.tif"
bio80Rast = "national_large_biodiversity_cores_80th_percentile.tif"
bio90Rast = "national_large_biodiversity_cores_90th_percentile.tif"

motorwayRoads = "merged_OSM_motorway_roads_Asia.shp"
primaryRoads = "merged_OSM_primary_roads_Asia.shp" 
trunkRoads = "merged_OSM_trunk_roads_Asia.shp"

#create list of all asian countries
asianCountries = []

with arcpy.da.SearchCursor(countriesFC, ("COUNTRY")) as cursor:
    for row in cursor: 
        if row[0] != "Singapore": #Singapore doesn't have hotspots -too small
            asianCountries.append(row[0])
del cursor

# sort list alphabetically
asianCountries.sort()


# check if user input country is valid
if countryInput not in asianCountries:
    print("Country is either not valid or not in the study area. Please try again.")
    
#create where clause based on country index
countryIndex = asianCountries.index(countryInput) + 1
countryWhereIndex = "Id = " + str(countryIndex)

    
## CLIP ALL INPUTS AND PLACE IN NEW FOLDERS
#try: 
# create new folder in workspace to hold country specific outputs
arcpy.management.CreateFolder(arcpy.env.workspace, countryInput + "_LISA_Data")
folder = countryInput + "_LISA_Data\\"

#create where clause for country selection
countryWhereClause = "COUNTRY = '" + countryInput + "'"



#select country of interest by attribute
countrySelection = arcpy.SelectLayerByAttribute_management(countriesFC, "NEW_SELECTION", countryWhereClause)

#create new feature layer of country, add to new folder
arcpy.management.CopyFeatures(countrySelection, folder + countryInput + ".shp") 

#clip li layer to country and add to new folder
arcpy.analysis.Clip(liFC, countrySelection, folder + countryInput + "_liFC.shp")
liPath = folder + countryInput + "_liFC.shp"
#add geometry (length) to each feature
arcpy.management.CalculateGeometryAttributes(liPath, [["Length_km","LENGTH"]], "KILOMETERS")

#clip PA layer to country and add to new folder
arcpy.analysis.Clip(paFC, countrySelection, folder + countryInput + "_paFC.shp")

#create array of existing roads layers
roadsList = [motorwayRoads, primaryRoads, trunkRoads]

for layer in roadsList:
    arcpy.analysis.Clip(layer, countrySelection, folder + countryInput + layer)
    
#create array of rasters for processing
rasterList = [bio70Rast, bio80Rast, bio90Rast]

# Check out the Spatial Analyst extension
arcpy.CheckOutExtension("Spatial") 

areasList = []
totalAreas = []
overlapAreas = []
LI_Overlap_KM = pd.DataFrame({'InfType':['Rail', 'Road', 'Transmission']})
LI_Overlap_Area = pd.DataFrame({'InfType':['Rail', 'Road', 'Transmission']})
LI_Overlap_Area_All = pd.DataFrame({'InfType':['All']})

#clip raster to country of interest, convert to polygon, add to new folder
for raster in rasterList:
    intRaster = Int(raster) #convert floating point raster to int raster (needed to polygonize)
    
    #convert each raster to polygon
    arcpy.conversion.RasterToPolygon(intRaster, "tempPolygon.shp", "NO_SIMPLIFY", "#" , "MULTIPLE_OUTER_PART") 
    
                                     #print("Key Bio Areas: " + str(arcpy.Describe("tempPolygon.shp").spatialReference.name))
    fileName = folder + countryInput + "_" + raster[:-4] + ".shp" # name for new shapefiles
    cutoffLevel = raster[-19:-4]
    #select single country from converted shapefile
    countryBiodiversity = arcpy.management.SelectLayerByAttribute("tempPolygon.shp", "NEW_SELECTION", countryWhereIndex)
    
    #create new feature layer of country, add to new folder
    arcpy.management.CopyFeatures(countryBiodiversity, fileName) 
    
    #add geometry (area) to each 
    arcpy.management.CalculateGeometryAttributes(fileName, [["Area_kmsq", "AREA"]], "#", "SQUARE_KILOMETERS")
    #delete temporary layers
    
    #Total area of each biodiversity layer
    outTableArea = r"in_memory\total_areastats"

    #Sum total area for each biodiversity layer
    arcpy.analysis.Statistics(fileName, outTableArea, [["Area_kmsq", "SUM"]])
    
    with arcpy.da.SearchCursor(outTableArea, ["SUM_Area_kmsq"]) as areaCursor:
        for row in areaCursor:
            totalAreas.append(row[0])
    del areaCursor
    
    #calculate overlap between PAs and biodiversity layers
    arcpy.analysis.Clip(fileName, folder + countryInput + "_paFC.shp", "PA_overlap.shp")
    arcpy.management.CalculateGeometryAttributes("PA_overlap.shp", [["OL_kmsq", "AREA"]], "#", "SQUARE_KILOMETERS")
    
    #Total area of each overlap areas
    outOLArea = r"in_memory\ol_areastats"

    #Sum total area for PA overlap layer
    arcpy.analysis.Statistics("PA_overlap.shp", outOLArea, [["OL_kmsq", "SUM"]])
    
    with arcpy.da.SearchCursor(outOLArea, ["SUM_OL_kmsq"]) as paCursor:
        for row in paCursor:
            overlapAreas.append(row[0])
    del paCursor
    
    #calculate overlap between LI and biodiversity layers
    arcpy.analysis.Clip(liPath, fileName, "LI_Km_Overlap.shp")
    
    arcpy.management.CalculateGeometryAttributes("LI_Km_Overlap.shp", [["LI_km", "LENGTH"]], "KILOMETERS")
    
    #Total length of each overlap areas
    LI_OL_length = r"in_memory\li_ol_length"
    
    #Sum total length for each biodiversity layer
    arcpy.analysis.Statistics("LI_Km_Overlap.shp", LI_OL_length, [["LI_km", "SUM"]], case_field = 'InfType')
        
    fieldNamesLI_OL = [i.name for i in arcpy.ListFields(LI_OL_length) if i.type != 'OID']
    # Open a cursor to extract results from stats table
        
    LI_OL_Cursor = arcpy.da.SearchCursor(LI_OL_length, fieldNamesLI_OL)
        
    # Create a pandas dataframe to hold results
    LI_OL_df = pd.DataFrame(data=[row for row in LI_OL_Cursor], columns=fieldNamesLI_OL)
        
    #rename length column to correspond w/ biodiversity cutoff
    LI_OL_df = LI_OL_df.rename(columns={"SUM_LI_km": cutoffLevel + "_km"})
        
    #drop frequency column
    LI_OL_df = LI_OL_df.drop(columns = ['FREQUENCY'])
    
    #add overlap numbers to data frame
    LI_Overlap_KM = LI_Overlap_KM.merge(LI_OL_df, how = 'outer', on ='InfType')
    
    #calculate overlap between LI buffer and biodiversity layers by mode
    arcpy.analysis.Buffer(liPath, "buffer_LI_mode.shp", "25 Kilometers", "FULL", "ROUND", "LIST", "InfType")
    arcpy.analysis.Clip("buffer_LI_mode.shp", fileName, "LI_Area_Overlap_Mode.shp")
    arcpy.management.CalculateGeometryAttributes("LI_Area_Overlap_Mode.shp", [["LI_kmsq", "AREA"]], "#", "SQUARE_KILOMETERS")
                                                 
    #Total area of each overlap areas
    LI_OL_area = r"in_memory\li_ol_area"

    #Sum total area for each biodiversity layer by mode
    arcpy.analysis.Statistics("LI_Area_Overlap_Mode.shp", LI_OL_area, [["LI_kmsq", "SUM"]], case_field = 'InfType')
    
    fieldNamesLI_OL_area = [i.name for i in arcpy.ListFields(LI_OL_area) if i.type != 'OID']
    # Open a cursor to extract results from stats table
    
    LI_OL_area_Cursor = arcpy.da.SearchCursor(LI_OL_area, fieldNamesLI_OL_area)
    
    # Create a pandas dataframe to hold results
    LI_OL_area_df = pd.DataFrame(data=[row for row in LI_OL_area_Cursor], columns=fieldNamesLI_OL_area)
    
    #rename length column to correspond w/ biodiversity cutoff
    LI_OL_area_df = LI_OL_area_df.rename(columns={"SUM_LI_kmsq": cutoffLevel + "_kmsq"})
    
    #drop frequency column
    LI_OL_area_df = LI_OL_area_df.drop(columns = ['FREQUENCY'])

    #add overlap numbers to data frame
    LI_Overlap_Area = LI_Overlap_Area.merge(LI_OL_area_df, how = 'outer', on ='InfType')
    
    arcpy.Delete_management("in_memory")
    
    #calculate overlap between LI buffer and biodiversity layers across all modes
    arcpy.analysis.Buffer(liPath, "buffer_LI_all.shp", "25 Kilometers", "FULL", "ROUND", "ALL")
    arcpy.analysis.Clip("buffer_LI_all.shp", fileName, "LI_Area_Overlap_All.shp")
    arcpy.management.CalculateGeometryAttributes("LI_Area_Overlap_All.shp", [["LI_kmsq", "AREA"]], "#", "SQUARE_KILOMETERS")                                             
    
    #Total area of each overlap areas
    LI_OL_area_all = r"in_memory\li_ol_area_all"

    #Sum total area for each biodiversity layer by mode
    arcpy.analysis.Statistics("LI_Area_Overlap_All.shp", LI_OL_area_all, [["LI_kmsq", "SUM"]])
    
    fieldNamesLI_OL_area_all = [i.name for i in arcpy.ListFields(LI_OL_area_all) if i.type != 'OID']
    
    # Open a cursor to extract results from stats table
    
    LI_OL_area_Cursor_all = arcpy.da.SearchCursor(LI_OL_area_all, fieldNamesLI_OL_area_all)
    
    # Create a pandas dataframe to hold results
    LI_OL_area_all_df = pd.DataFrame(data=[row for row in LI_OL_area_Cursor_all], columns=fieldNamesLI_OL_area_all)
    
    #rename length column to correspond w/ biodiversity cutoff
    LI_OL_area_all_df = LI_OL_area_all_df.rename(columns={"SUM_LI_kmsq": cutoffLevel + "_kmsq"})
    
    #drop frequency column
    LI_OL_area_all_df = LI_OL_area_all_df.drop(columns = ['FREQUENCY'])
    
    LI_OL_area_all_df['InfType'] = "All"


    #add overlap numbers to data frame
    LI_Overlap_Area_All = LI_Overlap_Area_All.merge(LI_OL_area_all_df, left_on=None)
    
    #print(LI_Overlap_Area_All)
    #clean up temp files
    arcpy.management.Delete("LI_Area_Overlap_mode.shp")
    arcpy.management.Delete("LI_KM_Overlap.shp")
    arcpy.management.Delete("temp_raster.tif", )
    arcpy.management.Delete("PA_overlap.shp")
    arcpy.management.Delete("buffer_LI_mode.shp")
    arcpy.management.Delete("buffer_LI_all.shp")
    arcpy.management.Delete("_LI.shp")
    arcpy.management.Delete("intRaster")
    arcpy.management.Delete("tempPolygon.shp")
    arcpy.management.Delete("LI_Area_Overlap_all.shp")

# Check in the Spatial Analyst extension
arcpy.CheckInExtension("Spatial")

#merge LI Overlap Area dfs
LI_Overlap_Area = pd.concat([LI_Overlap_Area, LI_Overlap_Area_All])
#print(LI_Overlap_Area)

# update areas list 
areasList.append(totalAreas) 
areasList.append(overlapAreas)  

# create data frame of biodiversity area and PA-biodiversity area overlap
areasDF = pd.DataFrame(areasList, index = ["Total_Area", "OL_PA_Area"], columns = ["70th Percentile", "80th Percentile", "90th Percentile"])

#  calculate percent of biodiversity areas protected, add to data frame
areasDF.loc['Percent_Protected'] = (areasDF.loc['OL_PA_Area']/ areasDF.loc['Total_Area']) * 100
#print(areasDF)

# Calculate total length of each LI type
outTableTL = r"in_memory\total_lengthstats"

arcpy.analysis.Statistics(liPath, outTableTL, [["Length_km", "SUM"]], case_field='InfType')

# Get field names of stats table
fieldNamesTL = [i.name for i in arcpy.ListFields(outTableTL) if i.type != 'OID']

# Open a cursor to extract results from stats table
tlCursor = arcpy.da.SearchCursor(outTableTL, fieldNamesTL)

# Create a pandas dataframe to hold results
total_LI_lengths_df = pd.DataFrame(data=[row for row in tlCursor],
                      columns=fieldNamesTL)

total_LI_lengths_df = total_LI_lengths_df.drop(columns = ['FREQUENCY'])

#export tables to CSV
areasDF.to_csv(folder + countryInput + "_Percent_Biodiversity_Protected.csv")
total_LI_lengths_df.to_csv(folder + countryInput + "_Total_LI_Lengths.csv")
LI_Overlap_KM.to_csv(folder + countryInput + "_LI_Overlap_by_Length.csv")
LI_Overlap_Area.to_csv(folder + countryInput + "_LI_Overlap_by_Area.csv")

#except:
   # print("An error occurred during processing.")

