import os
import arcgis
import arcpy
from arcpy import env
from arcpy.sa import *
import numpy

"""----------------------------------------------------------------------
  Script Name: Land Surface Temperature from Landsat8 Bands
  Description: This script estimates the LST of a user's inputted 
  Landsat 8 Bands. It only works for Landsat 8 bands. The tool requires 
  path locations to band's 4, 5, 10, and 11. The MTL metadata file associated 
  with the bands is also required. The zip file of L8 data will contain 
  the *MTL.txt file:
  (Example: LC08_L1TP_147047_20181110_20181127_01_T1_MTL)
  The script will scrap the metadata file for the neccesary variables needed 
  for the equations within the script. It outputs two rasters, a Land Surface
  Temperature (LST) raster and an NDVI raster. The NDVI raster is created 
  to calculate the Land Surface Emissivity (LSE), which is then used to 
  estimate the LST.
  
  Ouput Rasters Nomenclature: 'estLST_184457GMT_20200403' 
                                         |
      *estimated Land Surface Temperature_Time Acquired in GMT_Date Acquired*

  The Temperature raster will be in Celsius.

  For more information regarding this script, visit:
  !website!
  https://github.com/EricSamsonCarto/LandSurfaceTemperature_FromLANDSAT8

  Created By:  Eric Samson.
  Date:        5/21/2020.
------------------------------------------------------------------"""
def main():
	#Variables from User

	#workspace GDB
	inGDB = arcpy.GetParameterAsText(0)
	arcpy.env.workspace = inGDB
	arcpy.env.overwriteOutput = True
	arcpy.env.addOutputsToMap = False

	B4 = arcpy.GetParameterAsText(1)
	B5 = arcpy.GetParameterAsText(2)
	B10 = arcpy.GetParameterAsText(3)
	B11 = arcpy.GetParameterAsText(4)

	#metadata File
	metadata = arcpy.GetParameterAsText(5)

	#Optional
	clipOption = arcpy.GetParameterAsText(6)
	Clip_Feature = arcpy.GetParameterAsText(7)

#-------------------------------------------------------------------------------------

	#Clip Rasters if user requests

	if clipOption == 'true':
		B4_Clip = arcpy.sa.ExtractByMask(B4, Clip_Feature); B4_Clip.save(os.path.join(inGDB,'B4_Clip'))
		B4 = os.path.join(inGDB,'B4_Clip')
		B5_Clip = arcpy.sa.ExtractByMask(B5, Clip_Feature); B5_Clip.save(os.path.join(inGDB,'B5_Clip'))
		B5 = os.path.join(inGDB,'B5_Clip')
		B10_Clip = arcpy.sa.ExtractByMask(B10, Clip_Feature); B10_Clip.save(os.path.join(inGDB,'B10_Clip'))
		B10 = os.path.join(inGDB,'B10_Clip')
		B11_Clip = arcpy.sa.ExtractByMask(B11, Clip_Feature); B11_Clip.save(os.path.join(inGDB,'B11_Clip'))
		B11 = os.path.join(inGDB,'B11_Clip')


#-------------------------------------------------------------------------------------

	#Scrap metadata for variables needed
	scrap_lines = []

	with open(metadata, 'r') as list_file:
		for x in list_file:
			if 'DATE_ACQUIRED' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'SCENE_CENTER_TIME' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'SUN_ELEVATION' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'REFLECTANCE_MULT_BAND_4' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'REFLECTANCE_ADD_BAND_4' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'REFLECTANCE_MULT_BAND_5' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'REFLECTANCE_ADD_BAND_5' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'RADIANCE_MULT_BAND_10' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'RADIANCE_MULT_BAND_11' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'RADIANCE_ADD_BAND_10' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'RADIANCE_ADD_BAND_11' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'K1_CONSTANT_BAND_10' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'K2_CONSTANT_BAND_10' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'K1_CONSTANT_BAND_11' in x:
				scrap_lines.append(x.rstrip('\n').strip())
			if 'K2_CONSTANT_BAND_11' in x:
				scrap_lines.append(x.rstrip('\n').strip())

	scrap_lines_clean = []

	for x in scrap_lines:
		scrap_lines_clean.append(x.split('=')[1].strip())

	DATE_ACQUIRED = scrap_lines_clean[0].replace('-', '')
	SCENE_CENTER_TIME1 = scrap_lines_clean[1][1:-1]
	SCENE_CENTER_TIME = SCENE_CENTER_TIME1.split('.')[0].replace(':', '')
	SUN_ELEVATION = float(scrap_lines_clean[2])
	RADIANCE_MULT_BAND_10 = float(scrap_lines_clean[3])
	RADIANCE_MULT_BAND_11 = float(scrap_lines_clean[4])
	RADIANCE_ADD_BAND_10 = float(scrap_lines_clean[5])
	RADIANCE_ADD_BAND_11 = float(scrap_lines_clean[6])
	REFLECTANCE_MULT_BAND_4 = float(scrap_lines_clean[7])
	REFLECTANCE_MULT_BAND_5 = float(scrap_lines_clean[8])
	REFLECTANCE_ADD_BAND_4 = float(scrap_lines_clean[9])
	REFLECTANCE_ADD_BAND_5 = float(scrap_lines_clean[10])
	K1_CONSTANT_BAND_10 = float(scrap_lines_clean[11])
	K2_CONSTANT_BAND_10 = float(scrap_lines_clean[12])
	K1_CONSTANT_BAND_11 = float(scrap_lines_clean[13])
	K2_CONSTANT_BAND_11 = float(scrap_lines_clean[14])

	#Correct Sun Elevation
	sin_sun_elev = numpy.sin(numpy.deg2rad(SUN_ELEVATION))
	corrected_sun_elev = float(sin_sun_elev)
#-------------------------------------------------------------------------------------

	#Calculate NDVI

	#Calculate Red Band and NIR band, corrected with sun elevation. Create NDVI based off of these rasters
	RED_REF = ((REFLECTANCE_MULT_BAND_4 * Raster(B4)) - REFLECTANCE_ADD_BAND_4) / (corrected_sun_elev)
	NIR_REF = ((REFLECTANCE_MULT_BAND_5 * Raster(B5)) - REFLECTANCE_ADD_BAND_5) / (corrected_sun_elev)

	NDVI_REF = (Float(NIR_REF - RED_REF)) / (Float(NIR_REF + RED_REF))
	NDVI_PATH = os.path.join(inGDB,'NDVI')
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

	#Using band 10 and 11, calculate radiance and brightness temp:
	BAND_10_RADIANCE = ((RADIANCE_MULT_BAND_10 * Raster(B10)) + RADIANCE_ADD_BAND_10)
	BAND_11_RADIANCE = ((RADIANCE_MULT_BAND_11 * Raster(B11)) + RADIANCE_ADD_BAND_11)

	BAND10SATTEMP = ((K2_CONSTANT_BAND_10 / Ln((K1_CONSTANT_BAND_10/BAND_10_RADIANCE + 1)) - 272.15))
	BAND11SATTEMP = ((K2_CONSTANT_BAND_11 / Ln((K1_CONSTANT_BAND_11/BAND_11_RADIANCE + 1)) - 272.15))

	#Calculate Prop VEG using NDVI's min max, Use propveg to calculate the LSE:
	PROPVEG = Square(((Raster(NDVI)) - (NDVI_min)) / ((NDVI_max - (NDVI_min))))

	LSE = (0.004 * PROPVEG) + 0.986

	#Use the LSE to estimate the LST of band 10, 11:
	BAND10LST = (BAND10SATTEMP / 1) + (Raster(B10) * (BAND10SATTEMP/14380) * (Ln(LSE)))
	BAND11LST = (BAND11SATTEMP / 1) + (Raster(B11) * (BAND11SATTEMP/14380) *  (Ln(LSE)))

	#Find mean LST:
	LST_MEAN_11_10 = (BAND10LST + BAND11LST)/2

	LST_MEAN_PATH = os.path.join(inGDB,'estLST_' + SCENE_CENTER_TIME + 'GMT_' + DATE_ACQUIRED)
	LST_MEAN_11_10.save(LST_MEAN_PATH)

	#Add NDVI and LST to map:
	aprx = arcpy.mp.ArcGISProject("CURRENT")
	aprxMap = aprx.listMaps()[0]

	aprxMap.addDataFromPath(NDVI_PATH)
	aprxMap.addDataFromPath(LST_MEAN_PATH)
if __name__ == "__main__":
    main()