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

ADD TOOL TO ARCGIS PRO PROJECT:

-Download the tool as a zip file, unzip to directory of choosing
-In catalog in ArcGIS Pro, open toolboxes
-RIGHT CLICK, ADD TOOLBOX
-NAVIGATE TO LST_FROMLANDSAT8 TOOLBOX
-CLICK OK
-OPEN GEOPROCESSING, SEARCH FOR LST FROM LANDSAT8
-OPEN SCRIPT
-ENTER WORKSPACE GDB
-ENTER BANDS (4,5,10,11)
-ENTER METADATA FILE, MTL FILE (NOT ANG)
-CLIP RASTERS IF DESIRED

  THE SCRIPT WILL OUTPUT TWO RASTERS: 'estLST_TIMGMT_DATE' AND 'NDVI'