import numpy as np
import xarray as xr
from scipy import stats

def significance_tests(xarray_a, xarray_b, t_test=False, levene_test=False,
                       equal_variance = False, nan_policy= 'omit', mask_not_sig = False, 
                       level_of_sig = 0.05, center='mean'):
    """
    This function operates on a per-pixel basis and contains two types of significance tests:
    
    1.  A two-sided t-test for the null hypothesis that two independent samples have identical average (expected) values. 
        This test assumes that the populations have unequal variances by default (i.e. Welsh T-test), changing the 'equal_variance'
        variable will change this to an ordinary two-sided t-test. 
        See "scipy.stats.ttest_ind" for more info:
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html
    
    2. Levene statistic tests the null hypothesis that all input samples are from populations with equal variances.
       See "scipy.stats.levene" for more info:
       https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.stats.levene.html
    The user must specify which statistic to run, by default both tests are set to False. 
    Function will return two xarrrays, one conatining the statistic, and the other containing the p-values.
    The default is NOT to mask the pixels with p-values > the specified level of significance (default p-valies is 0.05).
    If conducting levene stats, be aware that large datasets could take a long time to compute.
    
    Inputs:
    xarray_a = an xarray dataArray containing observations from your first period of interest
    xarray_b = an xarray dataArray containing observations from your second period of interest
    t_test = Boolean. If True, conducts a per-pixel t-test
    levene_test = Boolean. If True, conducts a per-pixel levene-test
    mask_not_sig = Boolean. If True, mask out the values that don't achieve the desired level of significance
    level_of_sig = Float.  The level of confidence you wish to have if masking. Usually 0.05 (default) or 0.1
    equal_variance, nan_policy, center = see scipy.stats documentation
    
    Last modified: June 2018
    Author: Chad Burton
    """
    
    #convert into numpy ndarray arrays
    arr_1 = xarray_a.values
    arr_2 = xarray_b.values
    #Get coordinates from the original xarray
    lat  = xarray_a.coords['y']
    long = xarray_a.coords['x']
    
    if (t_test==False and levene_test==False):
        print('Please specificy which statistic you want to run by including either "t_test=True" or "levene_test=True" in your function call')
        
    if (t_test==True and levene_test==True):
        print('One statistical test at a time please!')
    
    if t_test:
        #run the t-test
        print('starting T-test')
        t_stat, p_values = stats.ttest_ind(arr_1, arr_2, equal_var = equal_variance, nan_policy = nan_policy)
        if mask_not_sig == True:
            t_stat[p_values>level_of_sig]=np.nan
        #Write arrays into a x-array
        t_stat_xr = xr.DataArray(t_stat, coords = [lat, long], dims = ['y', 'x'], name='t_stats')
        p_val_xr = xr.DataArray(p_values, coords = [lat, long], dims = ['y', 'x'], name='p_value') 
        print('finished T-test')
        return t_stat_xr, p_val_xr
            
    if levene_test:
        #create empty arrays to put the levene-stat results in
        t1, x1, y1 = arr_1.shape
        t2, x2, y2 = arr_2.shape
        assert x1 == x2 and y1 == y2
        levene_f = np.zeros((x1, y1))
        levene_p = np.zeros((x1, y1))
        #loop through each cell of arr1 and arr2 to conduct the levene test
        print('Starting for loop...this could take a while')
        for x in range(x1):
            for y in range(y1):
                arr_3 = arr_1[:, x, y] #for each x,y position, create a 1D array of the timeseries
                arr_4 = arr_2[:, x, y]
                arr_3 = arr_3[~np.isnan(arr_3)] #deal with the nans
                arr_4 = arr_4[~np.isnan(arr_4)]
                levene_f[x,y], levene_p[x,y] = stats.levene(arr_3, arr_4, center=center) #run the test     
        #Mask out values with insignificant trends (ie. p-value > 0.05) if user wants
        if mask_not_sig == True:   
            levene_f[levene_p>level_of_sig]=np.nan
        levene_stat_xr = xr.DataArray(levene_f, coords = [lat, long], dims = ['y', 'x'], name='levene_stats')
        p_val_levene_xr = xr.DataArray(levene_p, coords = [lat, long], dims = ['y', 'x'], name='p_value_levene') 
        print('finished levene test')
        return levene_stat_xr, p_val_levene_xr

# If the module is being run, not being imported! 
# to do this, do the following
# run {modulename}.py)

if __name__=='__main__':
#print that we are running the testing
    print('Testing..')
#import doctest to test our module for documentation
    import doctest
    doctest.testmod()
    print('Testing done')      
