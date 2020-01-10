# -*- coding: utf-8 -*-
"""
Created on Wed May 22 10:53:07 2019

@author: u89076
"""

import unittest
import sys
import xarray as xr
import numpy as np
import os.path
from inspect import getfile, currentframe


class JupyterTest(unittest.TestCase):
    
    def setUp(self):

        cmd_folder = os.path.realpath(os.path.abspath(
                                      os.path.split(getfile(
                                                    currentframe()))[0]))

        self.testdata_folder = os.path.join(cmd_folder, 'test_data')

        parent = os.path.abspath(os.path.join(cmd_folder, os.pardir))

        if parent not in sys.path:
            sys.path.insert(0, parent)


    def test_only_return_whole_scene(self):
        
        from utilities.util import only_return_whole_scene
        
        blue_data = xr.DataArray([[[ 580.,  723.,  659.,  675.,  643.],
                                   [ 627.,  691.,  659.,  627.,  627.],
                                   [ np.nan, np.nan, np.nan, np.nan, np.nan],
                                   [ np.nan, np.nan, np.nan, np.nan, np.nan],
                                   [ np.nan, np.nan, np.nan, np.nan, np.nan]],

                                  [[ 597.,  615.,  684.,  598.,  615.],
                                   [ 562.,  615.,  666.,  545.,  598.],
                                   [ 597.,  580.,  580.,  545.,  580.],
                                   [ 544.,  544.,  544.,  527.,  527.],
                                   [ 579.,  544.,  510.,  510.,  545.]],                                  

                                  [[ 601.,  669.,  714.,  735.,  601.],
                                   [ 534.,  646.,  646.,  624.,  601.],
                                   [ 579.,  601.,  557.,  579.,  579.],
                                   [ 600.,  557.,  601.,  601.,  579.],
                                   [ 579.,  512.,  534.,  579.,  579.]]], 
                                 coords = {'time': ['2018-02-10', '2018-02-26', 
                                                    '2018-03-14']}, 
                                 dims=('time', 'x', 'y'))
    
        input_data = xr.Dataset({'blue': blue_data})

        expected_data = xr.DataArray([[[ 597.,  615.,  684.,  598.,  615.],
                                       [ 562.,  615.,  666.,  545.,  598.],
                                       [ 597.,  580.,  580.,  545.,  580.],
                                       [ 544.,  544.,  544.,  527.,  527.],
                                       [ 579.,  544.,  510.,  510.,  545.]],

                                      [[ 601.,  669.,  714.,  735.,  601.],
                                       [ 534.,  646.,  646.,  624.,  601.],
                                       [ 579.,  601.,  557.,  579.,  579.],
                                       [ 600.,  557.,  601.,  601.,  579.],
                                       [ 579.,  512.,  534.,  579.,  579.]]],
                                     coords = {'time': ['2018-02-26', 
                                                        '2018-03-14']}, 
                                     dims=('time', 'x', 'y'))

        expected_output = xr.Dataset({'blue': expected_data})
        
        out_data = only_return_whole_scene(input_data) 

        self.assertEqual(out_data, expected_output)
        
        
    def test_get_common_dates_data(self):
        
        from utilities.util import get_common_dates_data
        
        ard_data = xr.DataArray([[[ 580.,  723.,  659.,  675.,  643.],
                                  [ 627.,  691.,  659.,  627.,  627.],
                                  [ np.nan, np.nan, np.nan, np.nan, np.nan],
                                  [ np.nan, np.nan, np.nan, np.nan, np.nan],
                                  [ np.nan, np.nan, np.nan, np.nan, np.nan]],

                                 [[ 597.,  615.,  684.,  598.,  615.],
                                  [ 562.,  615.,  666.,  545.,  598.],
                                  [ 597.,  580.,  580.,  545.,  580.],
                                  [ 544.,  544.,  544.,  527.,  527.],
                                  [ 579.,  544.,  510.,  510.,  545.]],                                  

                                 [[ 601.,  669.,  714.,  735.,  601.],
                                  [ 534.,  646.,  646.,  624.,  601.],
                                  [ 579.,  601.,  557.,  579.,  579.],
                                  [ 600.,  557.,  601.,  601.,  579.],
                                  [ 579.,  512.,  534.,  579.,  579.]]], 
                                coords = {'time': [np.datetime64('2018-01-12T00:30:26.666831000'), 
                                                   np.datetime64('2018-01-28T00:30:17.574173000'), 
                                                   np.datetime64('2018-02-06T00:24:02.483995000')]}, 
                                dims=('time', 'x', 'y'))
                                        
        usgs_data = xr.DataArray([[[ 597.,  615.,  684.,  598.,  615.],
                                   [ 562.,  615.,  666.,  545.,  598.],
                                   [ 597.,  580.,  580.,  545.,  580.],
                                   [ 544.,  544.,  544.,  527.,  527.],
                                   [ 579.,  544.,  510.,  510.,  545.]],

                                  [[ 601.,  669.,  714.,  735.,  601.],
                                   [ 534.,  646.,  646.,  624.,  601.],
                                   [ 579.,  601.,  557.,  579.,  579.],
                                   [ 600.,  557.,  601.,  601.,  579.],
                                   [ 579.,  512.,  534.,  579.,  579.]]],
                                 coords = {'time': [np.datetime64('2018-01-12T00:30:26.701092000'), 
                                                    np.datetime64('2018-01-28T00:30:17.603166000')]}, 
                                 dims=('time', 'x', 'y'))
                                  
        xrd_ard_data = xr.Dataset({'blue': ard_data})
        xrd_usgs_data = xr.Dataset({'blue': usgs_data})
        input_data = [{'ls8_ard': {'data': xrd_ard_data}}, 
                      {'ls8_usgs_l2c1': {'data': xrd_usgs_data}}]         
               
        ard_data_expected = xr.DataArray([[[ 580.,  723.,  659.,  675.,  643.],
                                    [ 627.,  691.,  659.,  627.,  627.],
                                    [ np.nan, np.nan, np.nan, np.nan, np.nan],
                                    [ np.nan, np.nan, np.nan, np.nan, np.nan],
                                    [ np.nan, np.nan, np.nan, np.nan, np.nan]],

                                   [[ 597.,  615.,  684.,  598.,  615.],
                                    [ 562.,  615.,  666.,  545.,  598.],
                                    [ 597.,  580.,  580.,  545.,  580.],
                                    [ 544.,  544.,  544.,  527.,  527.],
                                    [ 579.,  544.,  510.,  510.,  545.]]],
                                  coords = {'time': [np.datetime64('2018-01-12T00:30:26.666831000'), 
                                                    np.datetime64('2018-01-28T00:30:17.574173000')]}, 
                                  dims=('time', 'x', 'y')) 
#                                 
        usgs_data_expected = xr.DataArray([[[597., 615., 684., 598., 615.],
                                            [562., 615., 666., 545., 598.],
                                            [597., 580., 580., 545., 580.],
                                            [544., 544., 544., 527., 527.],
                                            [579., 544., 510., 510., 545.]],
        
                                           [[601., 669., 714., 735., 601.],
                                            [534., 646., 646., 624., 601.],
                                            [579., 601., 557., 579., 579.],
                                            [600., 557., 601., 601., 579.],
                                            [579., 512., 534., 579., 579.]]],
                            coords = {'time': [np.datetime64('2018-01-12T00:30:26.701092000'), 
                                               np.datetime64('2018-01-28T00:30:17.603166000')]}, 
                            dims=('time', 'x', 'y'))                                

        expected_output = [{'ls8_ard': {'data': xr.Dataset({'blue': ard_data_expected})}}, 
                           {'ls8_usgs_l2c1': {'data':  xr.Dataset({'blue': usgs_data_expected})}}]
          

        out_data = get_common_dates_data(input_data)

        self.assertEqual(out_data, expected_output)
        
           
#suite = unittest.TestLoader().loadTestsFromTestCase(JupyterTest)
#unittest.TextTestRunner(verbosity=1, stream=sys.stdout).run(suite)

if __name__ == '__main__':
    unittest.main()