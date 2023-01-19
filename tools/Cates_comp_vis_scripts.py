import os
import sys
import random
import datacube
import matplotlib.pyplot as plt
import numpy as np
import keras
import json
import pandas as pd
import xarray as xr

sys.path.insert(1, os.path.abspath("../Tools"))
from dea_tools.landcover import lc_colourmap
from dea_tools.plotting import display_map
import tensorflow as tf
from tensorflow.keras.layers.experimental import preprocessing
from tools.GEOC_utils import tile_array



def open_dict_into_partitions(ID_file_path, shuffle=True):

#     #open saved list of sample sites as dictionary
#     all_querys = coord_list = pd.read_csv(ID_file_path).to_dict(orient='index')
        
#     #get a list of test site keys    
#     list_of_keys = []
#     for keys in all_querys:
#         list_of_keys.append(keys)

    all_querys = list_of_files
        
    #in order to devide into train and test partitions count number od sites 
    number_of_samples = len(all_querys)
    list_of_samples = list(range(0,number_of_samples))


    #shuffle if true
    if shuffle==True:
        random.shuffle(list_of_samples)
    
    #define containers for storage of test and train partitions
    partition = {}
    train_list = []
    test_list = []
       
    #calculate the point at which we split test and train portions
    train_point = int(number_of_samples * 0.75)

    #list of each split, we are slicing the randomized list of samples
    train_split = list_of_samples[0 : train_point]
    test_split = list_of_samples[train_point : -1]
    
    
    #add indexed key to train split
    for i in train_split:
        train_list.append(list_of_keys[i])

    partition['train'] = train_list

    #add indexed key to tes split
    for i in test_split:
        test_list.append(list_of_keys[i])

    partition['validation'] = test_list
    return(partition)

def split_data_ID_list_into_partitions(ID_list, shuffle=True):
    """this one slits a list allready loaded into memory"""

    number_of_sample = len(ID_list)

    if shuffle == True:

        random.shuffle(ID_list)

    partition = {}

    train_list = []
    test_list = []
                                     
    train_split = int(number_of_sample * 0.75)
    test_splip = int(number_of_sample * 0.25)

    for i in range(0,train_split):
        train_list.append(ID_list[i].rstrip())

    partition['train'] = train_list

    for i in range(0,test_splip):
        test_list.append(ID_list[i].rstrip())

    partition['validation'] = test_list
    return(partition)


# def open_data_ID_txt_into_partitions(ID_file_path, shuffle=True):


#     with open(ID_file_path, "r") as txt_file:
#         ID_list = txt_file.readlines()

#     number_of_sample = len(ID_list)

#     if shuffle == True:

#         random.shuffle(ID_list)

#     partition = {}

#     train_list = []
#     test_list = []
                                     
#     train_split = int(number_of_sample * 0.75)
#     test_splip = int(number_of_sample * 0.25)

#     for i in range(0,train_split):
#         train_list.append(ID_list[i].rstrip())

#     partition['train'] = train_list

#     for i in range(0,test_splip):
#         test_list.append(ID_list[i].rstrip())

#     partition['validation'] = test_list
#     return(partition)

# class DataGenerator(keras.utils.all_utils.Sequence):
#     '''Generates data for Keras
#     for DC load'''
    
#     def __init__(self, list_IDs, data_sites_dict, batch_size=1, dim=(128,128), n_channels=3, #n_channels = bands
#                  n_classes=2, shuffle=True):
#         'Initialization'
#         self.dim = dim
#         self.batch_size = batch_size
#         self.list_IDs = list_IDs
#         self.data_sites_dict = data_sites_dict
#         self.n_channels = n_channels
#         self.n_classes = n_classes
#         self.shuffle = shuffle
#         self.on_epoch_end()

#     def __len__(self):
#         'Denotes the number of batches per epoch'
#         return int(np.floor(len(self.list_IDs) / self.batch_size))
    
#     def lc_process(self, data):
#         #do processing on landcover
#         #limit to urban class in level 3
#         artificial_y = xr.ones_like(data.level3).where(data.level3 == 215, 0)
#         artificial_y = artificial_y.astype('int16', casting='safe')
#         #change order of dementions to what the GEOC utils expect
#         artificial_y = artificial_y.transpose('y','x','time')

#         return artificial_y
    
#     def normalise(self, X):

#         X = X / 10000
#         #unsure this is correct normalisation
#         return X
    
#     def gm_process(self, data):
        
# #         data = data.isel(time=0)
#         #do processing on geomedian
#         data = self.normalise(data)
        
#         # make geomedian a neat array 
#         Geomedian_array = data.to_array()
#         #change order of dementions to what the GEOC utils expect
#         Geomedian_array = Geomedian_array.transpose('y','x','variable')
    
#         return Geomedian_array

#     def __getitem__(self, index):
#         'Generate one batch of data'
#         # Generate indexes of the batch
#         indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

#         # Find list of sites
        
#         list_sites_temp = [self.list_IDs[k] for k in indexes]

#         # Generate data
#         X, Y = self.__data_generation(list_sites_temp)

#         return X, Y
    
#     def tile_data(self, data):
#         #tile the urban classification layer
#         tiled_array = tile_array(data, xsize=128, ysize=128, overlap=0.5)
        
#         for i in range(0,tiled_array.shape[0]):
#             XorY = tiled_array[i]
        
#             return XorY
    

#     def on_epoch_end(self):
#         'Updates indexes after each epoch'
#         self.indexes = np.arange(len(self.list_IDs))
#         if self.shuffle == True:
#             np.random.shuffle(self.indexes)

#     def __data_generation(self, list_sites_temp):
#         'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
#         # Initialization
# #         X = np.empty((self.batch_size, *self.dim, self.n_channels))
# #         Y = np.empty((self.batch_size, *self.dim, 1))

#         dc = datacube.Datacube(app="urban_segmentation")
#         for sites in list_sites_temp:
#             query = self.data_sites_dict[sites]
           
#             #load sample
#             gm_x = self.gm_process(dc.load(
#                     product="ga_ls8c_nbart_gm_cyear_3",
#                     output_crs="EPSG:3577",
#                     measurements=["blue","green","red"],
#                     resolution=(-30, 30),
#                     **query
#                     ))
#             lc_y =  self.lc_process(dc.load(
#                     product="ga_ls_landcover_class_cyear_2",
#                     output_crs="EPSG:3577",
#                     measurements=["level3"],
#                     resolution=(-30, 30),
#                     **query
#                     ))

#             X= self.tile_data(gm_x)
#             Y= self.tile_data(lc_y)
            
#         return X,Y

