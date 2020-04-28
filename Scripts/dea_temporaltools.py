## dea_temporaltools.py
'''
Description: This file contains a set of python functions for conducting 
temporal (time-domain) analyses on Digital Earth Australia data.

License: The code in this notebook is licensed under the Apache License, 
Version 2.0 (https://www.apache.org/licenses/LICENSE-2.0). Digital Earth 
Australia data is licensed under the Creative Commons by Attribution 4.0 
license (https://creativecommons.org/licenses/by/4.0/).

Contact: If you need assistance, please post a question on the Open Data 
Cube Slack channel (http://slack.opendatacube.org/) or on the GIS Stack 
Exchange (https://gis.stackexchange.com/questions/ask?tags=open-data-cube) 
using the `open-data-cube` tag (you can view previously asked questions 
here: https://gis.stackexchange.com/questions/tagged/open-data-cube). 

If you would like to report an issue with this script, file one on 
Github: https://github.com/GeoscienceAustralia/dea-notebooks/issues/new

Functions included:
    time_buffer

Last modified: April 2020

'''

# Import required packages
import pandas as pd

def time_buffer(chosen_date, buffer='30 days'):

    """
    Create a buffer of days around a time query. 
    Output is a string the correct format for a datacube query.

    Parameters
        ----------
        chosen_date : str, yyyy-mm-dd
        buffer : str, optional, default is 30 days, needs to be a number of days
        
            
    Returns
    -------
    early_buffer, late_buffer : str
        a tuple of strings to pass to the datacube query function
        e.g. ('2017-12-02', '2018-01-31') for input chosen_date ='2018-01-01' and buffer = '30 days'  
    """
    #use assertions to check we have the correct function input
    assert isinstance(chosen_date, str), "chosen date must be a string in quotes in 'yyyy-mm-dd' format"
    assert isinstance(buffer, str), "buffer must be a string in days e.g. '5 days'"
    
    buffer = pd.Timedelta(buffer)
    chosen_date =pd.to_datetime(chosen_date)
    early_buffer = chosen_date - buffer
    late_buffer = chosen_date + buffer
    #convert back to string
    early_buffer = str(early_buffer)[:10]
    late_buffer = str(late_buffer)[:10]
    return(early_buffer, late_buffer)