import numpy as np

def mode_class(arr, axis = 0, num_classes = 4):
    """Fast mode finder using numpy. Designed to be compatible with xarray's reduce()
    functionality.

    Arguments:
    arr -- numpy array for which to take the mode. Values should be integers between 0 and num_classes-1.

    Keyword arguments:
    axis -- axis along which to take the mode, defaults to first axis of array
    num_classes -- defines the range of integers expected in arr.

    Returns:
    np.array of the modal value along the specified axis.

    This function ran about 1000x faster than scipy.stats.mode for determining the most common class
    for each pixel from the SAR wetlands tool for 5 observations of a 488x264 pixel image, so it is
    definitely worth using this method if your problem can be coerced to be compatible with it.

    """
    
    clarr = np.array([(arr == cla).sum(axis=axis) for cla in range(num_classes)])
    
    return np.argmax(clarr,axis=0)