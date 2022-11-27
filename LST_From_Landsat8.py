"""--------------------------------------------------------------------------
    Script Name: Land Surface Temperature from Landsat8 Bands
    Description: This script estimates the LST and the NDISI of a user's 
    inputted Landsat 8 Bands, with optional outputs of NDVI, MNDWI, and NDISI.
    It only works for Landsat 8 bands. It also will only work for a 
    Landsat Collection 2 Level-1 Product Bundle file. A Level-2 bundle
    will not work. The tool requires a full path to 
    a folder that contains the band's 3, 4, 5, 6, 10, 11 and the MTL 
    metadate file. The MTL metadata file associated with the bands is 
    required. The zip file of L8 data will contain the *MTL.txt file:
    (Example: LC08_L1TP_147047_20181110_20181127_01_T1_MTL)
    The script will scrape the metadata file for the necessary variables needed 
    for the equations within the script.
    Ouput Rasters Nomenclature: 'LST_184457GMT_20200403' 
    *Estimated Land Surface Temperature_Time Acquired in GMT_Date Acquired*
    The LST raster will be in celsius.

    For more documentation and methodology, please visit:
    https://ericsamson.com/projects/Python-LandSurfaceTemperature.html
    
    Created By:  Eric Samson.
    Date:        5/21/2020.
    Last Update: 11/15/2022.
-------------------------------------------------------------------------------"""

import os
import numpy
import arcpy

from arcpy.sa import *


def get_data_fromFolder(in_folder):
    data_dict = {}
    for x in os.listdir(in_folder):
        if x.endswith('B3.TIF'):
            B3_path = os.path.join(in_folder, x)
            data_dict['B3'] = B3_path
        elif x.endswith('B4.TIF'):
            B4_path = os.path.join(in_folder, x)
            data_dict['B4'] = B4_path
        elif x.endswith('B5.TIF'):
            B5_path = os.path.join(in_folder, x)
            data_dict['B5'] = B5_path
        elif x.endswith('B6.TIF'):
            B6_path = os.path.join(in_folder, x)
            data_dict['B6'] = B6_path
        elif x.endswith('B10.TIF'):
            B10_path = os.path.join(in_folder, x)
            data_dict['B10'] = B10_path
        elif x.endswith('B11.TIF'):
            B11_path = os.path.join(in_folder, x)
            data_dict['B11'] = B11_path
        elif x.endswith('MTL.txt'):
            metadata_path = os.path.join(in_folder, x)
            data_dict['metadata'] = metadata_path
    
    return data_dict


def mask_bands(in_mask_feature, out_gdb, in_bands_datadict):
    bands = ['B3', 'B4', 'B5', 'B6', 'B10', 'B11']
    band_masks = {}
    for band in bands:
        mask_name = f'{band}_Mask'
        mask_out = os.path.join(out_gdb, mask_name)
        mask_extract = arcpy.sa.ExtractByMask(in_bands_datadict[band], in_mask_feature)
        mask_extract.save(mask_out)
        band_masks[band] = mask_out
    
    return band_masks


def scrape_metadatafile(input_metadata, in_variables):
    scrape_lines = []
    with open(metadata, 'r') as metadata_file:
        for x in metadata_file:
            for variable in variable_name_list:
                if variable in x:
                    scrape_lines.append(x.rstrip('\n').strip())

    return [x.split('=')[1].strip() for x in scrape_lines]


def calculate_MNDWI(in_datadict, in_sun_elev, out_gdb, in_date_acquired, in_scene_center_time):
    """calculate green band and SWIR1 band, then create MNDWI based off of these rasters"""
    GREEN_REF = (((in_datadict['REFLECTANCE_MULT_BAND_3'] * Raster(B3)) 
                - in_datadict['REFLECTANCE_ADD_BAND_3'])
                /(in_sun_elev))

    NIR_REF = (((in_datadict['REFLECTANCE_MULT_BAND_5'] * Raster(B5)) 
                - in_datadict['REFLECTANCE_ADD_BAND_5'])
                /(in_sun_elev))

    SWIR1_REF = (((in_datadict['REFLECTANCE_MULT_BAND_6'] * Raster(B6)) 
                - in_datadict['REFLECTANCE_ADD_BAND_6'])
                /(in_sun_elev))

    MNDWI_REF = ((GREEN_REF - SWIR1_REF) 
                / (GREEN_REF + SWIR1_REF))

    MNDWI_PATH = os.path.join(gdb_path, 
                            f'MNDWI_{in_scene_center_time}GMT_{in_date_acquired}')
    MNDWI_REF.save(MNDWI_PATH)
    MNDWI = MNDWI_PATH

    return MNDWI, SWIR1_REF, NIR_REF


def calculate_NDISI(in_datadict, in_MNDWI, in_SWIR1_REF, in_NIR_REF, out_gdb, in_date_acquired, in_scene_center_time):
        BAND_10_RADIANCE = (((in_datadict['RADIANCE_MULT_BAND_10'] * Raster(B10)) 
                            + in_datadict['RADIANCE_ADD_BAND_10']))
        BAND10SATTEMP = (((in_datadict['K2_CONSTANT_BAND_10'] / 
                        Ln(((in_datadict['K1_CONSTANT_BAND_10'])/BAND_10_RADIANCE + 1))) 
                        -273.15))

        NDISI = ((BAND10SATTEMP - ((in_MNDWI + in_NIR_REF + in_SWIR1_REF)/3)) 
                / (BAND10SATTEMP + ((in_MNDWI + in_NIR_REF + in_SWIR1_REF)/3)))
        NDISI_PATH = os.path.join(out_gdb, 
                                f'NDISI_{in_scene_center_time}GMT_{in_date_acquired}')
        NDISI.save(NDISI_PATH)
        NDISI = NDISI_PATH

        return NDISI


def calculate_NDVI(in_datadict, in_NIR_REF, in_sun_elev, out_gdb, in_date_acquired, in_scene_center_time):
    """Calculate Red Band and NIR band, corrected with sun elevation. 
        Create NDVI based off of these rasters"""
    RED_REF = (((in_datadict['REFLECTANCE_MULT_BAND_4'] * Raster(B4)) 
                - in_datadict['REFLECTANCE_ADD_BAND_4']) 
                / (in_sun_elev))

    NDVI_REF = ((Float(in_NIR_REF - RED_REF)) 
                / (Float(in_NIR_REF + RED_REF)))

    NDVI_PATH = os.path.join(out_gdb, 
                            f'NDVI_{in_scene_center_time}GMT_{in_date_acquired}')
    NDVI_REF.save(NDVI_PATH)

    return NDVI_PATH


def get_NDVI_MinOrMax(in_NDVI, max=True):
        min_max = "MAXIMUM" if max else "MINIMUM"
        NDVI_PROP = arcpy.management.GetRasterProperties(in_NDVI, min_max, '')
        NDVI_VALUE = NDVI_PROP.getOutput(0)
        return float(NDVI_VALUE)


def calculate_sat_temp(in_datadict, in_b11):
        BAND_11_RADIANCE = (((in_datadict['RADIANCE_MULT_BAND_11'] * 
                            Raster(in_b11)) + in_datadict['RADIANCE_ADD_BAND_11']))
        return (in_datadict['K2_CONSTANT_BAND_11'] 
                / Ln((in_datadict['K1_CONSTANT_BAND_11'] / BAND_11_RADIANCE + 1)) 
                - 273.15)


def get_propveg(in_NDVI, in_NDVI_min, in_NDVI_max):
        return (Square(((Raster(in_NDVI)) - (in_NDVI_min)) 
                / ((in_NDVI_max - (in_NDVI_min)))))


def calculate_LSE(in_propveg):
        return (0.004 * in_propveg) + 0.986


def calculate_LST(in_B10_sat_temp, in_B11_sat_temp, in_LSE):
        BAND10LST = (in_B10_sat_temp / 
                    (1 + (10.895 * (in_B10_sat_temp/14380)) 
                    * (Ln(in_LSE))))
        BAND11LST = (in_B11_sat_temp / 
                    (1 + (12.005 * (in_B11_sat_temp/14380)) 
                    * (Ln(in_LSE))))

        return BAND10LST, BAND11LST


def add_to_map_delete_extra_data(in_prod_list):

        prod_dict = {'NDVI': NDVI, 'MNDWI': MNDWI, 'NDISI': NDISI, 'LST': LST}

        #Add products to map, or delete if not wanted
        for prod_str in in_prod_list:
            aprxMap.addDataFromPath(prod_dict[prod_str])
            if prod_str in prod_dict:
                prod_dict.pop(prod_str)

        for value in prod_dict.values():
            arcpy.Delete_management(value)


if __name__ == "__main__":
    arcpy.env.overwriteOutput = True
    arcpy.env.addOutputsToMap = False

    aprxMap = arcpy.mp.ArcGISProject('CURRENT').listMaps()[0]
    gdb_path = arcpy.env.workspace

    user_folder = arcpy.GetParameterAsText(0)
    products = arcpy.GetParameterAsText(1)
    products_list = products.split(';')
    mask_feature = arcpy.GetParameterAsText(2)
    average_b11 = arcpy.GetParameterAsText(3)

    bands_data_dict = get_data_fromFolder(user_folder)

    B3 = bands_data_dict['B3']
    B4 = bands_data_dict['B4']
    B5 = bands_data_dict['B5']
    B6 = bands_data_dict['B6']
    B10 = bands_data_dict['B10']
    B11 = bands_data_dict['B11']
    metadata = bands_data_dict['metadata']

    if mask_feature != '':
        bands_masked_datadict = mask_bands(mask_feature, gdb_path, bands_data_dict)
        B3 = bands_masked_datadict['B3']
        B4 = bands_masked_datadict['B4']
        B5 = bands_masked_datadict['B5']
        B6 = bands_masked_datadict['B6']
        B10 = bands_masked_datadict['B10']
        B11 = bands_masked_datadict['B11']

    variable_name_list = ['DATE_ACQUIRED', 'SCENE_CENTER_TIME', 'SUN_ELEVATION',
                            'RADIANCE_MULT_BAND_10', 'RADIANCE_MULT_BAND_11', 
                            'RADIANCE_ADD_BAND_10','RADIANCE_ADD_BAND_11',
                            'REFLECTANCE_MULT_BAND_3', 'REFLECTANCE_MULT_BAND_4', 
                            'REFLECTANCE_MULT_BAND_5', 'REFLECTANCE_MULT_BAND_6',
                            'REFLECTANCE_ADD_BAND_3','REFLECTANCE_ADD_BAND_4', 
                            'REFLECTANCE_ADD_BAND_5', 'REFLECTANCE_ADD_BAND_6', 
                            'K1_CONSTANT_BAND_10','K2_CONSTANT_BAND_10', 
                            'K1_CONSTANT_BAND_11', 'K2_CONSTANT_BAND_11']

    metadata_clean = scrape_metadatafile(metadata, variable_name_list)

    DATE_ACQUIRED = metadata_clean[0].replace('-', '')
    SCENE_CENTER_TIME = (metadata_clean[1][1:-1]
                        .split('.')[0]
                        .replace(':', ''))

    noDates_variable_name_list = variable_name_list[2:]
    noDates_scraped_data = metadata_clean[2:]
    floats_variable_list = [float(i) for i in noDates_scraped_data]

    variables_dict = dict(zip(noDates_variable_name_list, floats_variable_list))
    corrected_sun_elev = float(numpy.sin(numpy.deg2rad(variables_dict['SUN_ELEVATION'])))

    #calculate MNDWI
    MNDWI, SWIR1_REF, NIR_REF = calculate_MNDWI(variables_dict, corrected_sun_elev, 
                                                gdb_path, DATE_ACQUIRED, SCENE_CENTER_TIME)

    #Calculate NDISI
    NDISI = calculate_NDISI(variables_dict, MNDWI, SWIR1_REF, 
                            NIR_REF, gdb_path, DATE_ACQUIRED, 
                            SCENE_CENTER_TIME)

    #Calculate NDVI
    NDVI = calculate_NDVI(variables_dict, NIR_REF, corrected_sun_elev, 
                            gdb_path, DATE_ACQUIRED, SCENE_CENTER_TIME)

    #get min and max values
    NDVI_max = get_NDVI_MinOrMax(NDVI, max=True)
    NDVI_min = get_NDVI_MinOrMax(NDVI, max=False)

    # calculate brightness temp
    BAND10SATTEMP = calculate_sat_temp(variables_dict, B10)
    BAND11SATTEMP = calculate_sat_temp(variables_dict, B11)

    #propveg
    PROPVEG = get_propveg(NDVI, NDVI_min, NDVI_max)

    #calculate LSE
    LSE = calculate_LSE(PROPVEG)

    #calculate LST
    BAND10LST, BAND11LST = calculate_LST(BAND10SATTEMP, BAND11SATTEMP, LSE)

    LST = BAND10LST

    if average_b11 == 'true':
        #Find mean LST:
        LST = (BAND10LST + BAND11LST)/2

    LST_MEAN_PATH = os.path.join(gdb_path, f'LST_{SCENE_CENTER_TIME}GMT_{DATE_ACQUIRED}')
    LST.save(LST_MEAN_PATH)
    LST = LST_MEAN_PATH

    arcpy.AddMessage(products_list)
    add_to_map_delete_extra_data(products_list)
