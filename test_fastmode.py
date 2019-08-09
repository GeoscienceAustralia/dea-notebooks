import pytest

import numpy as np
from scipy.stats import mode

from fastmode import mode_class

def test_mode_class():
    #test with 10 random arrays over a random choice of axis
    for _ in range(10):
        arr_in = np.random.randint(0,high=6,size=(10,11,12))
        axis = np.random.randint(0,high=3)
        
        scip_out = mode(arr_in,axis=axis)
        
        fast_out = mode_class(arr_in,axis=axis,num_classes=6)
    