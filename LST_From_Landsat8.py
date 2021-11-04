import os
import numpy
import arcpy

from arcpy.sa import *

arcpy.env.overwriteOutput = True
arcpy.env.addOutputsToMap = False

"""----------------------------------------------------------------------
    Script Name: Land Surface Temperature from Landsat8 Bands

    Description: This script estimates the LST and the NDISI of a user's 
    inputted Landsat 8 Bands, with optional outputs of NDVI and MNDWI.
    It only works for Landsat 8 bands. The tool requires a full path to 
    a folder that contains the band's 3, 4, 5, 6, 10, and 11. The MTL metadata 
    file associated with the bands is also required. 
    The zip file of L8 data will contain the *MTL.txt file:
    (Example: LC08_L1TP_147047_20181110_20181127_01_T1_MTL)
    The script will scrap the metadata file for the necessary variables needed 
    for the equations within the script.
    Ouput Rasters Nomenclature: 'LST_184457GMT_20200403' 
    *Estimated Land Surface Temperature_Time Acquired in GMT_Date Acquired*
    The LST raster will be in celsius.

    For more documentation and methodology, please visit:
    https://ericsamson.com/Python/LandSurfaceTemp/LandSurfaceTemperature.html
    Created By:  Eric Samson.
    Date:        5/21/2020.
    Last Update: 11/03/2021.
------------------------------------------------------------------"""
aprx = arcpy.mp.ArcGISProject('CURRENT')
aprxMap = aprx.listMaps()[0]
gdb_path = aprx.defaultGeodatabase

in_folder = arcpy.GetParameterAsText(0)

band_noMasks = {}

for x in os.listdir(in_folder):
    if x.endswith('B3.TIF'):
        B3_path = os.path.join(in_folder, x)
        band_noMasks['B3'] = B3_path
    elif x.endswith('B4.TIF'):
        B4_path = os.path.join(in_folder, x)
        band_noMasks['B4'] = B4_path
    elif x.endswith('B5.TIF'):
        B5_path = os.path.join(in_folder, x)
        band_noMasks['B5'] = B5_path
    elif x.endswith('B6.TIF'):
        B6_path = os.path.join(in_folder, x)
        band_noMasks['B6'] = B6_path
    elif x.endswith('B10.TIF'):
        B10_path = os.path.join(in_folder, x)
        band_noMasks['B10'] = B10_path
    elif x.endswith('B11.TIF'):
        B11_path = os.path.join(in_folder, x)
        band_noMasks['B11'] = B11_path
    elif x.endswith('MTL.txt'):
        metadata_path = os.path.join(in_folder, x)
        band_noMasks['metadata'] = metadata_path

B3 = band_noMasks['B3']
B4 = band_noMasks['B4']
B5 = band_noMasks['B5']
B6 = band_noMasks['B6']
B10 = band_noMasks['B10']
B11 = band_noMasks['B11']
metadata = band_noMasks['metadata']

#Optional
products = arcpy.GetParameterAsText(1)
products_list = products.split(';')
Mask_Feature = arcpy.GetParameterAsText(2)
average_b11 = arcpy.GetParameterAsText(3)
arcpy.AddMessage(Mask_Feature)
#-------------------------------------------------------------------------------------
#Mask Bands
bands = ['B3', 'B4', 'B5', 'B6', 'B10', 'B11']
band_masks = {}

if Mask_Feature != '':
    for band in bands:
        mask_name = band + '_Mask'
        mask_output_loc = os.path.join(gdb_path,mask_name)
        mask_extract = arcpy.sa.ExtractByMask(band_noMasks[band], Mask_Feature); mask_extract.save(mask_output_loc)
        band_masks[band] = mask_output_loc

    B3 = band_masks['B3']
    B4 = band_masks['B4']
    B5 = band_masks['B5']
    B6 = band_masks['B6']
    B10 = band_masks['B10']
    B11 = band_masks['B11']

#-------------------------------------------------------------------------------------
#Scrap metadata for variables needed
variable_name_list = ['DATE_ACQUIRED', 'SCENE_CENTER_TIME', 'SUN_ELEVATION',
                        'RADIANCE_MULT_BAND_10', 'RADIANCE_MULT_BAND_11', 'RADIANCE_ADD_BAND_10',
                        'RADIANCE_ADD_BAND_11','REFLECTANCE_MULT_BAND_3', 'REFLECTANCE_MULT_BAND_4', 
                        'REFLECTANCE_MULT_BAND_5', 'REFLECTANCE_MULT_BAND_6','REFLECTANCE_ADD_BAND_3',
                        'REFLECTANCE_ADD_BAND_4', 'REFLECTANCE_ADD_BAND_5', 'REFLECTANCE_ADD_BAND_6', 
                        'K1_CONSTANT_BAND_10','K2_CONSTANT_BAND_10', 'K1_CONSTANT_BAND_11', 'K2_CONSTANT_BAND_11']

scrap_lines = []
with open(metadata, 'r') as list_file:
    for x in list_file:
        for variable in variable_name_list:
            if variable in x:
                scrap_lines.append(x.rstrip('\n').strip())

scrap_lines_clean = [x.split('=')[1].strip() for x in scrap_lines]

#Clean up the dates:
DATE_ACQUIRED = scrap_lines_clean[0].replace('-', '')
SCENE_CENTER_TIME1 = scrap_lines_clean[1][1:-1]
SCENE_CENTER_TIME = SCENE_CENTER_TIME1.split('.')[0].replace(':', '')

#remove time variables
noDates_variable_name_list = variable_name_list[2:]
noDates_scraped_data = scrap_lines_clean[2:]
floats_variable_list = [float(i) for i in noDates_scraped_data]

#create dictionary of variables
variables_dict = dict(zip(noDates_variable_name_list, floats_variable_list))
#Correct Sun Elevation
sin_sun_elev = numpy.sin(numpy.deg2rad(variables_dict['SUN_ELEVATION']))
corrected_sun_elev = float(sin_sun_elev)
#-------------------------------------------------------------------------------------
#Calculate MNDWI

#Calculate Green Band and SWIR1 band, corrected with sun elevation. Create MNDWI based off of these rasters
GREEN_REF = ((variables_dict['REFLECTANCE_MULT_BAND_3'] * Raster(B3)) - variables_dict['REFLECTANCE_ADD_BAND_3'])/(corrected_sun_elev)
NIR_REF = ((variables_dict['REFLECTANCE_MULT_BAND_5'] * Raster(B5)) - variables_dict['REFLECTANCE_ADD_BAND_5'])/(corrected_sun_elev)
SWIR1_REF = ((variables_dict['REFLECTANCE_MULT_BAND_6'] * Raster(B6)) - variables_dict['REFLECTANCE_ADD_BAND_6'])/(corrected_sun_elev)

MNDWI_REF = (GREEN_REF - SWIR1_REF) / (GREEN_REF + SWIR1_REF)
MNDWI_PATH = os.path.join(gdb_path, 'MNDWI_' + SCENE_CENTER_TIME + 'GMT_' + DATE_ACQUIRED)
MNDWI_REF.save(MNDWI_PATH)

MNDWI = MNDWI_PATH

#-------------------------------------------------------------------------------------
#Calculate NDISI

#Using band 10, calculate radiance and brightness temp:
BAND_10_RADIANCE = ((variables_dict['RADIANCE_MULT_BAND_10'] * Raster(B10)) + variables_dict['RADIANCE_ADD_BAND_10'])
BAND10SATTEMP = ((variables_dict['K2_CONSTANT_BAND_10'] / Ln(((variables_dict['K1_CONSTANT_BAND_10'])/BAND_10_RADIANCE + 1))) -273.15)

#Calculate NDISI:
NDISI = (BAND10SATTEMP - ((MNDWI + NIR_REF + SWIR1_REF)/3)) / (BAND10SATTEMP + ((MNDWI + NIR_REF + SWIR1_REF)/3))
NDISI_PATH = os.path.join(gdb_path, 'NDISI_' + SCENE_CENTER_TIME + 'GMT_' + DATE_ACQUIRED)
NDISI.save(NDISI_PATH)

NDISI = NDISI_PATH
#-------------------------------------------------------------------------------------
#Calculate NDVI

#Calculate Red Band and NIR band, corrected with sun elevation. Create NDVI based off of these rasters
RED_REF = ((variables_dict['REFLECTANCE_MULT_BAND_4'] * Raster(B4)) - variables_dict['REFLECTANCE_ADD_BAND_4']) / (corrected_sun_elev)

NDVI_REF = (Float(NIR_REF - RED_REF)) / (Float(NIR_REF + RED_REF))
NDVI_PATH = os.path.join(gdb_path,'NDVI_' + SCENE_CENTER_TIME + 'GMT_' + DATE_ACQUIRED)
NDVI_REF.save(NDVI_PATH)

NDVI = NDVI_PATH

#Create variables for the NDVI's max and min values:
NDVI_min_PROP = arcpy.management.GetRasterProperties(NDVI, "MINIMUM", '')
NDVI_min_VALUE = NDVI_min_PROP.getOutput(0)
NDVI_min = float(NDVI_min_VALUE)

NDVI_max_PROP = arcpy.management.GetRasterProperties(NDVI, "MAXIMUM", '')
NDVI_max_VALUE = NDVI_max_PROP.getOutput(0)
NDVI_max = float(NDVI_max_VALUE)


#-------------------------------------------------------------------------------------
#Calculate LST

#Using band 11, calculate radiance and brightness temp:
BAND_11_RADIANCE = ((variables_dict['RADIANCE_MULT_BAND_11'] * Raster(B11)) + variables_dict['RADIANCE_ADD_BAND_11'])
BAND11SATTEMP = ((variables_dict['K2_CONSTANT_BAND_11'] / Ln((variables_dict['K1_CONSTANT_BAND_11']/BAND_11_RADIANCE + 1)) - 273.15))

#Calculate Prop VEG using NDVI's min max, Use propveg to calculate the LSE:
PROPVEG = Square(((Raster(NDVI)) - (NDVI_min)) / ((NDVI_max - (NDVI_min))))

LSE = (0.004 * PROPVEG) + 0.986

#Use the LSE to estimate the LST of band 10, 11:
BAND10LST = (BAND10SATTEMP / (1 + (10.895 * (BAND10SATTEMP/14380)) * (Ln(LSE))))
BAND11LST = (BAND11SATTEMP / (1 + (12.005 * (BAND11SATTEMP/14380)) * (Ln(LSE))))

LST_CALC = BAND10LST

if average_b11 == 'true':
    #Find mean LST:
    LST_CALC = (BAND10LST + BAND11LST)/2

LST_MEAN_PATH = os.path.join(gdb_path,'LST_' + SCENE_CENTER_TIME + 'GMT_' + DATE_ACQUIRED)
LST_CALC.save(LST_MEAN_PATH)

LST = LST_MEAN_PATH

#Add NDVI and LST to map:
if 'NDVI' in products_list:
    aprxMap.addDataFromPath(NDVI)
if 'MNDWI' in products_list:
    aprxMap.addDataFromPath(MNDWI)
if 'NDISI' in products_list:
    aprxMap.addDataFromPath(NDISI)
if 'LST' in products_list:
    aprxMap.addDataFromPath(LST)
