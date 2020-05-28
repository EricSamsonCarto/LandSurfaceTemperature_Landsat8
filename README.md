[![LinkedIn][linkedin-shield]][linkedin-url]

<p align="center">
  <h3 align="center">Estimate Land Surface Temperature From Landsat 8 bands: Arcpy toolbox</h3>

  <p align="center">
    An ArcGIS Pro Arcpy toolbox that estimates land surface temperature using Landsat 8 bands.<br>
    Project Description page:<br>
  <a href='#'>Land Surface Temperature</a>
  </p>
</p>

<!-- ABOUT THE PROJECT -->
<div align="center">
  
<img src="https://s3-us-west-2.amazonaws.com/s.cdpn.io/3352342/tool.JPG" width="400px">
  
</div>

  Description: This script estimates the LST of a user's inputted 
  Landsat 8 Bands. It only works for Landsat 8 bands. The tool requires 
  path locations to band's 4, 5, 10, and 11. The MTL metadata file associated 
  with the bands is also required. The zip file of L8 data will contain 
  the *MTL.txt* file:
  (Example: LC08_L1TP_147047_20181110_20181127_01_T1_MTL)
  The script will scrap the metadata file for the neccesary variables needed 
  for the equations within the script. It outputs two rasters, a Land Surface
  Temperature (LST) raster and an NDVI raster. The NDVI raster is created 
  to calculate the Land Surface Emissivity (LSE), which is then used to 
  estimate the LST.
  
  Ouput Rasters Nomenclature: estLST_184457GMT_20200403 
                                         =
      *estimated Land Surface Temperature_Time Acquired in GMT_Date Acquired*

  The Temperature raster will be in Celsius.
  </div>

### How To Add the Tool to ArcGIS:
  <br>-Download the tool as a zip file, unzip to directory of choosing
  <br>-In catalog in ArcGIS Pro, open toolboxes
  <br>-Right click, add toolbox
  <br>-Navigate to the LST_FROMLANDSAT8 toolbox
  <br>-Click ok
  <br>-In the map pane, open geoprocessing, search for Land Surface Temperature
  <br>-Open Script
  <br>-Enter Workspace GDB
  <br>-Enter band paths (4,5,10,11)
  <br>-Enter Metadata file path, <b>MTL FILE (NOT ANG)</b>
  <br>-Clip rasters if desired

  THE SCRIPT WILL OUTPUT TWO RASTERS: 'estLST_TIMGMT_DATE' AND 'NDVI'

### Important Notes / Known Issues
-Make sure you use the MTL.txt metadata file and NOT the ANG.txt metadata file.

-ArcGIS Pro may not being able to see the MTL metadata text file, it will instead only be able to find the ANG metadata file within the directory. To fix this, change the MTL file's name. Just adding a _ somewhere in the file name will enable ArcGIS Pro to find it within the directory. This seems to happen the majority of the time, so this will need to be done before using the tool.

### Built With
* [Numpy](https://numpy.org/)
* [Arcpy](https://desktop.arcgis.com/en/arcmap/10.3/analyze/arcpy/a-quick-tour-of-arcpy.htm)
* [ArcGIS Pro](https://pro.arcgis.com/en/pro-app/get-started/get-started.htm)

<!-- CONTACT -->
## Contact
Eric Samson: [@MyTwitter](https://twitter.com/EricSamsonGIS) <br>
Email: ericsamsonwx@gmail.com <br>
Website: [EricSamson.com](https://ericsamson.com) <br>

Project Link: [https://github.com/EricSamsonCarto/LandSurfaceTemperature_FromLANDSAT8](https://github.com/EricSamsonCarto/LandSurfaceTemperature_FromLANDSAT8)

[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/iamericsamson
