## BandIndices.py
'''
This code allows for the quick calculation of remote sensing band indices.

Date: March 2018
Author: Claire Krause

'''

def calculate_indices(ds, index):
    '''
    Available indices are all calculated within the same function. If an
    index is requested that is not coded in the function, an error is
    raised.

    Try/except statements are used to account for the different band
    names for Landsat and Sentinel2 data.

    Available indices:
    - NDVI: Normalised Difference Vegetation Index
    - GNDVI: Green Normalised Difference Vegetation Index
    - NDWI: Normalised Difference Water Index
    - NDMI: Normalised Difference Moisture Index

    inputs:
    ds - dataset containing the bands needed for index calculation
    index - str of the index to be calculated

    outputs:
    indexout - result of the index calculation
    
    '''

    if index == 'NDWI':
        print('The formula we are using is (green - nir)/(green + nir)')
        try:
            indexout = ((ds.green - ds.nir)/(ds.green + ds.nir))
        except AttributeError:
            try:
                indexout = ((ds.green - ds.nir1)/(ds.green + ds.nir1))
            except:
                print('Error! NDWI requires green and nir bands')
    elif index == 'NDVI':
        print('The formula we are using is (nir - red)/(nir + red)')
        try:
            indexout = ((ds.nir - ds.red)/(ds.nir + ds.red))
        except AttributeError:
            try:
                indexout = ((ds.nir1 - ds.red)/(ds.nir1 + ds.red))
            except:
                print('Error! NDVI requires red and nir bands')  
    elif index == 'GNDVI':
        print('The formula we are using is (nir - green)/(nir + green)')
        try:
            indexout = ((ds.nir - ds.green)/(ds.nir + ds.green))
        except AttributeError:
            try:
                indexout = ((ds.nir1 - ds.green)/(ds.nir1 + ds.green))
            except:
                print('Error! GNDVI requires green and nir bands')
    elif index == 'NDMI':
        print('The formula we are using is (nir - swir1)/(nir + swir1)')
        try:
            indexout = ((ds.nir - ds.swir1)/(ds.nir + ds.swir1))
        except AttributeError:
            try:
                indexout = ((ds.nir1 - ds.swir1)/(ds.nir1 + ds.swir1))
            except:
                print('Error! NDVI requires swir1 and nir bands')  
    try:
        return indexout
    except:
        print('Hmmmmm. I don\'t recognise that index. '
              'Options I currently have are NDVI, GNDVI, NDMI and NDWI.')

def geological_indices(ds, index):
    '''
    Available indices are all calculated within the same function. If an
    index is requested that is not coded in the function, an error is
    raised.

    Try/except statements are used to account for the different band
    names for Landsat and Sentinel2 data.

    Available geological indices:
    - CMR: Clay Minerals Ratio
    - FMR: Ferrous Minerals Ratio
    - IOR: Iron Oxide Ratio

    inputs:
    ds - dataset containing the bands needed for index calculation
    index - str of the index to be calculated

    outputs:
    indexout - result of the index calculation

    Reference: http://www.harrisgeospatial.com/docs/BackgroundGeologyIndices.html
        '''

    if index == 'CMR':
        print('The formula we are using for Clay Minerals Ratio is (swir1 / swir2)')
        try:
            indexout = (ds.swir1 / ds.swir2)
        except AttributeError:
            print('Error! Clay Minerals Ratio requires swir1 and swir2 bands')
    elif index == 'FMR':
        print('The formula we are using for Ferrous Minerals Ratio is (swir1 / nir)')
        try:
            indexout = (ds.swir1 / ds.nir)
        except AttributeError:
            try:
                indexout = (ds.swir1 / ds.nir1)
            except:
                print('Error! Ferrous Minerals Ratio requires swir1 and nir bands')  
    elif index == 'IOR':
        print('The formula we are using for Iron Oxide Ratio is (red / blue)')
        try:
            indexout = (ds.red / ds.blue)
        except AttributeError:
            print('Error! Iron Oxide Ratio requires red and blue bands')
    try:
        return indexout
    except:
        print('Hmmmmm. I don\'t recognise that index. '
              'Options I currently have are CMR, FMR and IOR.')
